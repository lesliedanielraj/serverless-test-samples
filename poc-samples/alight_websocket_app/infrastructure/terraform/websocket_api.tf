# WebSocket API Stack Terraform Configuration

# Provider configuration
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "bedrock_agent_id" {
  description = "Bedrock Agent ID"
  type        = string
}

variable "bedrock_agent_alias_id" {
  description = "Bedrock Agent Alias ID"
  type        = string
}

# DynamoDB table for connection tracking
resource "aws_dynamodb_table" "websocket_connections" {
  name           = "WebSocketConnections"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "connection_id"
  range_key      = "session_id"

  attribute {
    name = "connection_id"
    type = "S"
  }

  attribute {
    name = "session_id"
    type = "S"
  }
}

# Lambda Layer for AWS Lambda Powertools
data "aws_lambda_layer_version" "powertools" {
  layer_name = "AWSLambdaPowertoolsPythonV3-python312-x86_64"
  version    = 10
}

# Lambda function for connect handler
resource "aws_lambda_function" "connect_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "ConnectHandler"
  role            = aws_iam_role.connect_handler_role.arn
  handler         = "connect.handler"
  runtime         = "python3.12"
  layers          = [data.aws_lambda_layer_version.powertools.arn]

  environment {
    variables = {
      CONNECTIONS_TABLE = aws_dynamodb_table.websocket_connections.name
    }
  }
}

# IAM role for connect handler
resource "aws_iam_role" "connect_handler_role" {
  name = "connect_handler_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda function for disconnect handler
resource "aws_lambda_function" "disconnect_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "DisconnectHandler"
  role            = aws_iam_role.disconnect_handler_role.arn
  handler         = "disconnect.handler"
  runtime         = "python3.12"
  layers          = [data.aws_lambda_layer_version.powertools.arn]

  environment {
    variables = {
      CONNECTIONS_TABLE = aws_dynamodb_table.websocket_connections.name
    }
  }
}

# IAM role for disconnect handler
resource "aws_iam_role" "disconnect_handler_role" {
  name = "disconnect_handler_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# SQS Queue for message processing
resource "aws_sqs_queue" "message_queue" {
  name                        = "send-message-queue.fifo"
  fifo_queue                  = true
  content_based_deduplication = false
  message_retention_seconds   = 86400 # 1 day

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.message_queue_dlq.arn
    maxReceiveCount     = 3
  })
}

# SQS Dead Letter Queue
resource "aws_sqs_queue" "message_queue_dlq" {
  name                        = "send-message-dlq.fifo"
  fifo_queue                  = true
  message_retention_seconds   = 86400 # 1 day
}

# IAM role for API Gateway service proxy
resource "aws_iam_role" "service_proxy_execution_role" {
  name = "service_proxy_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for service proxy to access SQS
resource "aws_iam_role_policy" "service_proxy_sqs_policy" {
  name = "service_proxy_sqs_policy"
  role = aws_iam_role.service_proxy_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.message_queue.arn,
          aws_sqs_queue.message_queue_dlq.arn
        ]
      }
    ]
  })
}

# WebSocket API
resource "aws_apigatewayv2_api" "websocket" {
  name                       = "websocket-api"
  protocol_type             = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

# Connect route integration
resource "aws_apigatewayv2_integration" "connect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.connect_handler.invoke_arn
}

# Connect route
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.connect.id}"
}

# Disconnect route integration
resource "aws_apigatewayv2_integration" "disconnect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.disconnect_handler.invoke_arn
}

# Disconnect route
resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.disconnect.id}"
}

# Default route integration (SQS)
resource "aws_apigatewayv2_integration" "default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS"
  
  credentials_arn  = aws_iam_role.service_proxy_execution_role.arn
  description     = "SQS Integration"
  integration_method = "POST"
  integration_uri = "arn:aws:apigateway:${var.aws_region}:sqs:path/${data.aws_caller_identity.current.account_id}/${aws_sqs_queue.message_queue.name}"

  request_parameters = {
    "integration.request.header.Content-Type" = "'application/x-www-form-urlencoded'"
  }

  template_selection_expression = "$default"
  request_templates = {
    "$default" = "Action=SendMessage&MessageGroupId=$util.urlEncode($context.connectionId)&MessageDeduplicationId=$util.urlEncode($context.requestId)&MessageAttribute.1.Name=connectionId&MessageAttribute.1.Value.StringValue=$util.urlEncode($context.connectionId)&MessageAttribute.1.Value.DataType=String&MessageAttribute.2.Name=requestId&MessageAttribute.2.Value.StringValue=$util.urlEncode($context.requestId)&MessageAttribute.2.Value.DataType=String&MessageAttribute.3.Name=sourceIp&MessageAttribute.3.Value.StringValue=$util.urlEncode($context.identity.sourceIp)&MessageAttribute.3.Value.DataType=String&MessageBody=$util.urlEncode($input.json('$'))"
  }
}

# Default route
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.default.id}"
}

# Stage
resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.websocket.id
  name        = "prod"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "websocket_api" {
  name              = "/aws/websocket-api"
  retention_in_days = 7
}

# Message handler Lambda
resource "aws_lambda_function" "message_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "MessageHandler"
  role            = aws_iam_role.message_handler_role.arn
  handler         = "message.handler"
  runtime         = "python3.12"
  timeout         = 30
  layers          = [data.aws_lambda_layer_version.powertools.arn]

  environment {
    variables = {
      CONNECTIONS_TABLE      = aws_dynamodb_table.websocket_connections.name
      BEDROCK_AGENT_ID      = var.bedrock_agent_id
      BEDROCK_AGENT_ALIAS_ID = var.bedrock_agent_alias_id
      WEBSOCKET_CALLBACK_URL = "${aws_apigatewayv2_stage.prod.invoke_url}"
    }
  }
}

# IAM role for message handler
resource "aws_iam_role" "message_handler_role" {
  name = "message_handler_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for message handler
resource "aws_iam_role_policy" "message_handler_policy" {
  name = "message_handler_policy"
  role = aws_iam_role.message_handler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeAgent"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda basic execution role policy attachment
resource "aws_iam_role_policy_attachment" "message_handler_basic_execution" {
  role       = aws_iam_role.message_handler_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# SQS event source mapping for message handler
resource "aws_lambda_event_source_mapping" "message_queue" {
  event_source_arn = aws_sqs_queue.message_queue.arn
  function_name    = aws_lambda_function.message_handler.arn
  batch_size       = 1
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}

# Archive file for Lambda code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../handlers"
  output_path = "${path.module}/lambda.zip"
}

# DynamoDB permissions for Lambda functions
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb_access"
  role = aws_iam_role.message_handler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.websocket_connections.arn
      }
    ]
  })
}

# Outputs
output "websocket_endpoint" {
  value = aws_apigatewayv2_stage.prod.invoke_url
}
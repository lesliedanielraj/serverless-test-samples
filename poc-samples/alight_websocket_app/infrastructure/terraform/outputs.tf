output "websocket_api_endpoint" {
  description = "WebSocket API endpoint URL"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for WebSocket connections"
  value       = aws_dynamodb_table.websocket_connections.name
}

output "message_queue_url" {
  description = "URL of the SQS message queue"
  value       = aws_sqs_queue.message_queue.url
}

output "message_dlq_url" {
  description = "URL of the SQS dead letter queue"
  value       = aws_sqs_queue.message_dlq.url
}
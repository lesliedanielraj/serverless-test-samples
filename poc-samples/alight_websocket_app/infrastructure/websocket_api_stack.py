import os

from aws_cdk import Aws, CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigatewayv2 as apigatewayv2
from aws_cdk import aws_apigatewayv2_integrations as apigatewayv2_integrations
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
from aws_cdk import aws_logs as aws_logs
from aws_cdk import aws_sqs as sqs
from constructs import Construct


class WebSocketStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bedrock_agent_id: str,
        bedrock_agent_alias_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Add removal policy to clean up resources
        self.removal_policy = RemovalPolicy.DESTROY

        # Add dependency attributes
        self.agent_id = bedrock_agent_id
        self.agent_alias_id = bedrock_agent_alias_id

        # Create DynamoDB table for connection tracking
        connections_table = dynamodb.Table(
            self,
            "WebSocketConnections",
            partition_key=dynamodb.Attribute(
                name="connection_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="session_id", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Use path.join to create a platform-independent path
        this_dir = os.path.dirname(__file__)
        lambda_dir = os.path.join(os.path.dirname(this_dir), "handlers")

        # Verify the path exists
        if not os.path.exists(lambda_dir):
            raise ValueError(f"Lambda directory not found: {lambda_dir}")

        powertools_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            id=f"{construct_id}-lambda-powertools",
            layer_version_arn=f"arn:aws:lambda:{Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:10",
        )

        # Create Lambda
        bundling = {
            "image": lambda_.Runtime.PYTHON_3_12.bundling_image,
            "command": [
                "bash",
                "-c",
                """
                 set -e
                 pip install -r requirements.txt --target /asset-output/
                 cp -au . /asset-output/
                 
                 # Clean up unnecessary files
                 cd /asset-output
                 rm -rf *.dist-info *.egg-info
                 find . -type d -name "__pycache__" -exec rm -rf {} +
                 find . -type f -name "*.pyc" -delete
                 find . -type f -name "requirements.txt" -delete
                 find . -type f -name "pyproject.toml" -delete
                 """,
            ],
        }
        connect_handler = lambda_.Function(
            self,
            "ConnectHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="websocket_connect.handler",
            code=lambda_.Code.from_asset(lambda_dir, bundling=bundling),
            environment={"CONNECTIONS_TABLE": connections_table.table_name},
            layers=[powertools_layer],
        )

        # Create IAM role for message handler
        message_handler_role = iam.Role(
            self,
            "MessageHandlerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for WebSocket message handler Lambda function",
        )

        # Add policy to allow Bedrock runtime invoke
        message_handler_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeAgent",
                    "bedrock-agent-runtime:InvokeAgent",
                ],
                resources=["*"],
            )
        )

        # Add CloudWatch Logs permissions
        message_handler_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # Add Lambda Layer permissions
        message_handler_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:GetLayerVersion"],
                resources=[
                    f"arn:aws:lambda:{Stack.of(self).region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-312-x86_64:*"
                ],
            )
        )

        # Add ManageConnections permission for WebSocket API
        message_handler_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["execute-api:ManageConnections"],
                resources=["*"],
            )
        )

        # Create SQS queue for message processing
        message_queue_dlq = sqs.Queue(
            self,
            f"{construct_id}-send-message-dlq",
            retention_period=Duration.days(1),
            fifo=True,
            encryption=sqs.QueueEncryption.SQS_MANAGED,  # Enable server-side encryption
        )
        message_queue = sqs.Queue(
            self,
            f"{construct_id}-send-message-queue",
            # visibility_timeout=Duration.seconds(30),
            retention_period=Duration.days(1),
            fifo=True,
            encryption=sqs.QueueEncryption.SQS_MANAGED,  # Enable server-side encryption
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=message_queue_dlq),
        )

        disconnect_handler = lambda_.Function(
            self,
            "DisconnectHandler",
            handler="websocket_disconnect.handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset(lambda_dir, bundling=bundling),
            environment={"CONNECTIONS_TABLE": connections_table.table_name},
            layers=[powertools_layer],
        )

        # Create service proxy execution role
        service_proxy_execution_role = iam.Role(
            self,
            "ServiceProxyExecutionRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Role for API Gateway service proxy execution",
        )

        # Add SQS permissions to service proxy execution role
        service_proxy_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sqs:SendMessage",
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                ],
                resources=[message_queue.queue_arn, message_queue_dlq.queue_arn],
            )
        )

        # Create WebSocket API
        websocket_api = apigatewayv2.WebSocketApi(
            self,
            f"{construct_id}-web-socket-api",
            connect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=apigatewayv2_integrations.WebSocketLambdaIntegration(
                    "ConnectIntegration", handler=connect_handler
                )
            ),
            disconnect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=apigatewayv2_integrations.WebSocketLambdaIntegration(
                    "DisconnectIntegration", handler=disconnect_handler
                )
            ),
            default_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=apigatewayv2_integrations.WebSocketAwsIntegration(
                    f"{construct_id}-send-message-integration",
                    integration_uri=f"arn:aws:apigateway:{Stack.of(self).region}:sqs:path/{Aws.ACCOUNT_ID}/{message_queue.queue_name}",
                    integration_method="POST",
                    request_parameters={
                        "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
                    },
                    request_templates={
                        "$default": f"Action=SendMessage&MessageGroupId=$util.urlEncode($context.connectionId)&MessageDeduplicationId=$util.urlEncode($context.requestId)&MessageAttribute.1.Name=connectionId&MessageAttribute.1.Value.StringValue=$util.urlEncode($context.connectionId)&MessageAttribute.1.Value.DataType=String&MessageAttribute.2.Name=requestId&MessageAttribute.2.Value.StringValue=$util.urlEncode($context.requestId)&MessageAttribute.2.Value.DataType=String&MessageAttribute.3.Name=sourceIp&MessageAttribute.3.Value.StringValue=$util.urlEncode($context.identity.sourceIp)&MessageAttribute.3.Value.DataType=String&MessageBody=$util.urlEncode($input.json('$'))"
                    },
                    template_selection_expression="\\$default",
                    credentials_role=service_proxy_execution_role,
                )
            ),
        )

        # Create WebSocket Stage
        # Create CloudWatch Log Group for API Gateway
        log_group = aws_logs.LogGroup(
            self,
            "WebSocketApiLogs",
            retention=aws_logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        websocket_stage = apigatewayv2.WebSocketStage(
            self,
            "prod",
            web_socket_api=websocket_api,
            stage_name="prod",
            auto_deploy=True,
            throttle=apigatewayv2.ThrottleSettings(rate_limit=50, burst_limit=100),
            # access_log_settings=apigatewayv2.CfnStage.AccessLogSettingsProperty(
            #     destination_arn=log_group.log_group_arn,
            #     format='{ "requestId":"$context.requestId", "ip": "$context.identity.sourceIp", "caller":"$context.identity.caller", "user":"$context.identity.user", "requestTime":"$context.requestTime", "eventType":"$context.eventType", "routeKey":"$context.routeKey", "status":"$context.status", "connectionId":"$context.connectionId" }'
            # )
        )

        # Create message handler Lambda with API endpoint
        message_handler = lambda_.Function(
            self,
            "MessageHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="websocket_message.handler",
            code=lambda_.Code.from_asset(lambda_dir, bundling=bundling),
            role=message_handler_role,
            timeout=Duration.seconds(30),
            environment={
                "CONNECTIONS_TABLE": connections_table.table_name,
                "BEDROCK_AGENT_ID": self.agent_id,
                "BEDROCK_AGENT_ALIAS_ID": self.agent_alias_id,
                "WEBSOCKET_CALLBACK_URL": websocket_stage.callback_url,
            },
            layers=[powertools_layer],
        )

        # Add SQS event source to message handler
        message_handler.add_event_source(
            lambda_event_sources.SqsEventSource(message_queue, batch_size=1)
        )

        # Grant SQS permissions to message handler
        message_queue.grant_consume_messages(message_handler)

        # Grant DynamoDB permissions to Lambda handlers
        connections_table.grant_read_write_data(connect_handler)
        connections_table.grant_read_write_data(disconnect_handler)
        connections_table.grant_read_write_data(message_handler)

        # Output the websocket URL
        CfnOutput(
            self,
            "WebSocketUrl",
            value=websocket_stage.url,
            description="WebSocket API URL",
            export_name="WebSocketUrl",
        )

        # Output the websocket callback URL
        CfnOutput(
            self,
            "WebSocketCallbackUrl",
            value=websocket_stage.callback_url,
            description="WebSocket API Callback URL",
            export_name="WebSocketCallbackUrl",
        )

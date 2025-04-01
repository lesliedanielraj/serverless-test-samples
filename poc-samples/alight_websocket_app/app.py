#!/usr/bin/env python3
import aws_cdk as cdk

from infrastructure.bedrock_agent_stack import BedrockAgentStack
from infrastructure.bedrock_guardrails_stack import BedrockGuardrailsStack
from infrastructure.websocket_api_stack import WebSocketStack

app = cdk.App()

# Create Bedrock stacks
bedrock_guardrails_stack = BedrockGuardrailsStack(app, "BedrockGuardrailsStack")
bedrock_agent_stack = BedrockAgentStack(
    app,
    "BedrockAgentStack",
    guardrails_bucket_name=bedrock_guardrails_stack.guardrails_bucket_name,
    guardrails_role_arn=bedrock_guardrails_stack.guardrails_role_arn,
)

# Create WebSocket API stack with Bedrock agent ID
websocket_api_stack = WebSocketStack(
    app,
    "AlightApiStack",
    bedrock_agent_id=bedrock_agent_stack.agent_id,
    bedrock_agent_alias_id=bedrock_agent_stack.agent_alias_id,
)

app.synth()

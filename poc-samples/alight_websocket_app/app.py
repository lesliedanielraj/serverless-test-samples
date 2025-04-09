#!/usr/bin/env python3
import aws_cdk as cdk

from infrastructure.action_group_stack import ActionGroupStack
from infrastructure.bedrock_agent_stack import BedrockAgentStack
from infrastructure.bedrock_guardrails_stack import BedrockGuardrailsStack
from infrastructure.websocket_api_stack import WebSocketStack

app = cdk.App()

# Create Bedrock stacks
bedrock_guardrails_stack = BedrockGuardrailsStack(app, "AlightGuardrailsStack")

# Create Action Group stack
action_group_stack = ActionGroupStack(app, "AlightAGStack")

# Create Bedrock Agent stack with function ARN from Action Group stack
bedrock_agent_stack = BedrockAgentStack(
    app,
    "AlightBedrockAgentStack",
    guardrails_bucket_name=bedrock_guardrails_stack.guardrails_bucket_name,
    guardrails_role_arn=bedrock_guardrails_stack.guardrails_role_arn,
    structured_response_function_arn=action_group_stack.function_arn,
)

# Create WebSocket API stack with Bedrock agent ID and Alias ID
websocket_api_stack = WebSocketStack(
    app,
    "AlightApiStack",
    bedrock_agent_id=bedrock_agent_stack.agent_id,
    bedrock_agent_alias_id=bedrock_agent_stack.agent_alias_id,
)

# Add explicit dependency
bedrock_agent_stack.add_dependency(bedrock_guardrails_stack)
bedrock_agent_stack.add_dependency(action_group_stack)
websocket_api_stack.add_dependency(bedrock_agent_stack)

app.synth()

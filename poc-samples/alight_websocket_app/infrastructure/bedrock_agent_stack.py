from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_iam as iam
from constructs import Construct


class BedrockAgentStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        guardrails_bucket_name: str,
        guardrails_role_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.agent_id = None
        self.agent_alias_id = None

        # Create IAM role for Bedrock agent
        agent_role = iam.Role(
            self,
            "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )

        # Add necessary permissions for the agent
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeAgent",
                    "bedrock:Invoke",
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-v2"
                ],
            )
        )

        # Create the Bedrock agent
        agent = bedrock.CfnAgent(
            self,
            "ChatAgent",
            agent_name="ChatAgent",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model="anthropic.claude-v2",
            instruction="You are a helpful AI assistant that answers questions clearly and accurately.",
        )

        # Create your agent alias
        agent_alias = bedrock.CfnAgentAlias(
            self, "AgentAlias", agent_id=agent.attr_agent_id, agent_alias_name="test"
        )

        # Output the agent ID for use in other stacks
        # Store the agent ID for reference by other stacks
        self.agent_id = agent.attr_agent_id
        self.agent_alias_id = agent_alias.attr_agent_alias_id

        CfnOutput(
            self, "BedrockAgentId", value=self.agent_id, export_name="BedrockAgentId"
        )

        # Output the alias ID
        CfnOutput(
            self,
            "BedrockAgentAliasId",
            value=agent_alias.attr_agent_alias_id,
            description="Bedrock Agent Alias ID",
            export_name="BedrockAgentAliasId",
        )

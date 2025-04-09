import os

from aws_cdk import CfnOutput, RemovalPolicy, Stack, aws_bedrock
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from cdklabs.generative_ai_cdk_constructs import bedrock
from constructs import Construct


class BedrockAgentStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        guardrails_bucket_name: str,
        guardrails_role_arn: str,
        structured_response_function_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.agent_id = None
        self.agent_alias_id = None

        dashboards_bucket = s3.Bucket.from_bucket_name(
            self,
            "bedrockagentstack-quicksight-dashboards",
            bucket_name=f"bedrockagentstack-quicksight-dashboards",
        )

        # Use path.join to create a platform-independent path
        this_dir = os.path.dirname(__file__)
        misc_dir = os.path.join(os.path.dirname(this_dir), "Misc")

        # Create IAM role for Bedrock agent with more specific principal
        agent_role = iam.Role(
            self,
            "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Role for Bedrock Agent to access required resources",
        )

        # Add necessary permissions for the agent with more specific resource constraints
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeAgent",
                    "bedrock:Invoke",
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[f"arn:aws:bedrock:{self.region}:{self.account}:*"],
                effect=iam.Effect.ALLOW,
            )
        )

        # Add S3 permissions for the agent
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                resources=[
                    dashboards_bucket.bucket_arn,
                    f"{dashboards_bucket.bucket_arn}/*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )

        # Add Lambda invoke permissions for the agent
        # agent_role.add_to_policy(
        #     iam.PolicyStatement(
        #         actions=["lambda:InvokeFunction"],
        #         resources=[structured_response_function_arn],
        #         effect=iam.Effect.ALLOW,
        #     )
        # )

        with open(
            os.path.join(misc_dir, "kb_instructions.txt"), "r", encoding="utf-8"
        ) as file:
            kb_instruction = (
                file.read().strip()
            )  # reads entire file into a single string
            print(kb_instruction)

        knowledge_base = bedrock.VectorKnowledgeBase(
            self,
            "KnowledgeBase",
            embeddings_model=bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V1,
            instruction=kb_instruction,
        )

        bedrock.S3DataSource(
            self,
            "DataSource",
            bucket=dashboards_bucket,
            knowledge_base=knowledge_base,
            data_source_name="dashboards",
            chunking_strategy=bedrock.ChunkingStrategy.FIXED_SIZE,
        )

        # Assuming structured_response_function_arn is a string containing the Lambda ARN
        structured_response_function = aws_lambda.Function.from_function_arn(
            self,
            "StructuredResponseFunction",
            function_arn=structured_response_function_arn,
        )

        structured_response_action = bedrock.AgentActionGroup(
            name="structured_response",
            description="Use this function ALWAYS to provide a structured JSON response to the user",
            executor=bedrock.ActionGroupExecutor.fromlambda_function(
                structured_response_function
            ),
            enabled=True,
            function_schema=aws_bedrock.CfnAgent.FunctionSchemaProperty(
                functions=[
                    aws_bedrock.CfnAgent.FunctionProperty(
                        name="create_structured_response",
                        description="Creates a structured JSON response based on the input text",
                        parameters={
                            "inputText": aws_bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The input text to process",
                                required=True,
                            ),
                            "sessionId": aws_bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The session ID",
                                required=False,
                            ),
                            "timestamp": aws_bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The timestamp of the request",
                                required=False,
                            ),
                        },
                    )
                ]
            ),
        )

        with open(
            os.path.join(misc_dir, "agent_instructions.txt"), "r", encoding="utf-8"
        ) as file:
            agent_instruction = (
                file.read().strip()
            )  # reads entire file into a single string
        agent = bedrock.Agent(
            self,
            "ChatAgent",
            foundation_model=bedrock.BedrockFoundationModel.AMAZON_NOVA_MICRO_V1,
            instruction=agent_instruction,
            user_input_enabled=True,
            code_interpreter_enabled=False,
            should_prepare_agent=True,
        )
        agent.add_knowledge_base(knowledge_base)
        agent.add_action_group(structured_response_action)

        # Create agent alias
        agent_alias = bedrock.AgentAlias(
            self,
            "AgentAlias-Prod",
            alias_name="agent-alias-prod",
            agent=agent,
            # agent_version="1",  # optional
            description="agent-alias-prod",
        )

        self.agent_id = agent.agent_id
        self.agent_alias_id = agent_alias.alias_id

        # # Outputs
        # CfnOutput(
        #     self,
        #     "BedrockAgentId",
        #     value=self.agent_id,
        #     export_name="BedrockAgentId",
        #     description="Bedrock Agent ID",
        # )
        #
        # CfnOutput(
        #     self,
        #     "BedrockAgentAliasId",
        #     value=self.agent_alias_id,
        #     description="Bedrock Agent Alias ID",
        #     export_name="BedrockAgentAliasId",
        # )

        # CfnOutput(
        #     self,
        #     "StructuredResponseFunctionArn",
        #     value=structured_response_function_arn,
        #     description="Structured Response Function Arn",
        #     export_name="StructuredResponseFunctionArn",
        # )

        CfnOutput(
            self,
            "DashboardsBucketName",
            value=dashboards_bucket.bucket_name,
            description="QuickSight Dashboards S3 Bucket Name",
            export_name="DashboardsBucketName",
        )

        CfnOutput(
            self,
            "KnowledgeBaseId",
            value=knowledge_base.knowledge_base_id,
            description="Knowledge Base ID",
            export_name="KnowledgeBaseId",
        )

import os

from aws_cdk import CfnOutput, Duration, Stack, aws_bedrock
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from cdklabs.generative_ai_cdk_constructs import bedrock
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

        # Use path.join to create a platform-independent path for lambda handlers
        this_dir = os.path.dirname(__file__)
        lambda_dir = os.path.join(os.path.dirname(this_dir), "handlers")

        # Verify the path exists
        if not os.path.exists(lambda_dir):
            raise ValueError(f"Lambda directory not found: {lambda_dir}")

        powertools_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            id=f"{construct_id}-lambda-powertools",
            layer_version_arn=f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:10",
        )

        dashboards_bucket = s3.Bucket.from_bucket_name(
            self,
            "bedrockagentstack-quicksight-dashboards",
            bucket_name=f"bedrockagentstack-quicksight-dashboards",
        )

        # Use path.join to create a platform-independent path
        this_dir = os.path.dirname(__file__)
        misc_dir = os.path.join(os.path.dirname(this_dir), "misc")

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
                    "bedrock-agent:StartKnowledgeBaseSync",
                    "bedrock-agent:GetKnowledgeBaseSync",
                    "bedrock-agent:GetKnowledgeBaseSyncJob",
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

        with open(os.path.join(misc_dir, "kb_instructions.txt"), "r", encoding="utf-8") as file:
            kb_instruction = file.read().strip()  # reads entire file into a single string

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

        with open(os.path.join(misc_dir, "agent_inst_new.txt"), "r", encoding="utf-8") as file:
            agent_instruction = file.read().strip()  # reads entire file into a single string
        agent = bedrock.Agent(
            self,
            "ChatAgent",
            foundation_model=bedrock.BedrockFoundationModel.AMAZON_NOVA_PRO_V1,
            instruction=agent_instruction,
            user_input_enabled=True,
            code_interpreter_enabled=False,
            should_prepare_agent=True,
        )
        agent.add_knowledge_base(knowledge_base)

        # region structured response action group
        # Create the structured response Lambda function
        structured_response_function = lambda_.Function(
            self,
            "StructuredResponseHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="ag_structured_response.handler",
            code=lambda_.Code.from_asset(lambda_dir),
            environment={
                "POWERTOOLS_SERVICE_NAME": "structured-response-handler",
                "LOG_LEVEL": "INFO",
            },
            layers=[powertools_layer],
            timeout=Duration.seconds(30),
        )

        # Grant the Lambda permission to be invoked by Bedrock service
        structured_response_function.add_permission(
            "AllowBedrockInvoke",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction",
        )

        # Create the structured response action group
        structured_response_action = bedrock.AgentActionGroup(
            name="structured_response",
            description="Use this function ALWAYS to provide a structured JSON response to the user",
            executor=bedrock.ActionGroupExecutor.fromlambda_function(structured_response_function),
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
        agent.add_action_group(structured_response_action)  # Add the new action group
        # endregion

        # region get dashboard details action group
        # Create the dashboard details Lambda function
        get_dashboard_details_function = lambda_.Function(
            self,
            "DashboardDetailsHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="ag_dashboard_details.handler",
            code=lambda_.Code.from_asset(lambda_dir),
            environment={
                "POWERTOOLS_SERVICE_NAME": "dashboard-details-handler",
                "LOG_LEVEL": "INFO",
            },
            layers=[powertools_layer],
            timeout=Duration.seconds(30),
        )

        # Grant QuickSight permissions to the dashboard details function
        get_dashboard_details_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "quicksight:DescribeDashboard",
                    "quicksight:GenerateEmbedUrlForAnonymousUser",
                ],
                resources=[
                    f"arn:aws:quicksight:{self.region}:{self.account}:dashboard/*",
                    f"arn:aws:quicksight:{self.region}:{self.account}:user/*",
                    f"arn:aws:quicksight:{self.region}:{self.account}:namespace/*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )
        # Grant the Lambda permission to be invoked by Bedrock service
        get_dashboard_details_function.add_permission(
            "AllowBedrockInvoke",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction",
        )
        # Create the dashboard details action group
        get_dashboard_details_action = bedrock.AgentActionGroup(
            name="get_dashboard_details",
            description="Use this function to get information like URL about a specific dashboard",
            executor=bedrock.ActionGroupExecutor.fromlambda_function(
                get_dashboard_details_function
            ),
            enabled=True,
            function_schema=aws_bedrock.CfnAgent.FunctionSchemaProperty(
                functions=[
                    aws_bedrock.CfnAgent.FunctionProperty(
                        name="get_dashboard_details",
                        description="Retrieves detailed information about a dashboard using its ID",
                        parameters={
                            "dashboard_id": aws_bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The ID of the QuickSight dashboard to retrieve details for",
                                required=True,
                            ),
                        },
                    )
                ]
            ),
        )

        agent.add_action_group(get_dashboard_details_action)  # Add the new action group
        # endregion action

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

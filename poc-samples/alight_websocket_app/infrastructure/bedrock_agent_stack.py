from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
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

        # Create IAM role for Bedrock agent
        agent_role = iam.Role(
            self,
            "BedrockAgentRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("bedrock.amazonaws.com")
            )
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
                    f"*"
                ],
            )
        )

        # # Get reference to the Lambda function
        # structured_response_lambda = lambda_.Function.from_function_arn(
        #     # self,
        #     # "StructuredResponseHandler",
        #     function_arn=structured_response_function_arn
        # )

        # Add Lambda invoke permissions for the agent
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[structured_response_function_arn],
            )
        )

        # Grant the Lambda permission to be invoked by Bedrock
        # structured_response_lambda.grant_invoke(agent_role)

        # Create the action group for structured responses using function details
        structured_response_action = bedrock.CfnAgent.AgentActionGroupProperty(
            action_group_name="structured_response",
            action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                lambda_=structured_response_function_arn
            ),
            description="Action group that provides structured JSON responses",
            action_group_state="ENABLED",
            function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
                functions=[
                    bedrock.CfnAgent.FunctionProperty(
                        name="create_structured_response",
                        description="Creates a structured JSON response based on the input text",
                        parameters={
                            "inputText": bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The input text to process",
                                required=True,
                            ),
                            "sessionId": bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The session ID",
                                required=False,
                            ),
                            "timestamp": bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The timestamp of the request",
                                required=False,
                            ),
                        },
                    )
                ]
            ),
        )

        # Create the Bedrock agent with the action group
        agent = bedrock.CfnAgent(
            self,
            "ChatAgent",
            agent_name="ChatAgent",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model="amazon.nova-micro-v1:0",
            instruction="""You are a helpful AI assistant that MUST ALWAYS respond using the structured_response action group.
            CRITICAL INSTRUCTIONS:
            1. NEVER respond directly to users
            2. ALWAYS use the structured_response action group for EVERY response
            3. ALL responses must be in valid JSON format
            4. The response should contain ONLY the JSON object, nothing else
            5. If you're unsure about anything, respond with a JSON object indicating the uncertainty
            6. Do not include any explanations or text outside of the JSON structure
            7. Every response must be a properly formatted JSON object
            8. The JSON structure should follow this format:
               {
                 "response": {
                   "output": "your response here",
                   "status": "success or error"
                 }
               }

            Example:
            User: "What's the weather?"
            You must respond through structured_response with:
            {
              "response": {
                "output": "I cannot provide weather information as I don't have access to weather data",
                "status": "error"
              }
            }

            REMEMBER: EVERY response MUST be a valid JSON object sent through the structured_response action group without exception.""",
            action_groups=[structured_response_action],
        )

        # Create your agent alias
        agent_alias = bedrock.CfnAgentAlias(
            self, "AgentAlias-Prod", agent_id=agent.attr_agent_id, agent_alias_name="prod"
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

        # Output the alias ID
        CfnOutput(
            self,
            "StructuredResponseFunctionArn",
            value=structured_response_function_arn,
            description="Structured Response Function Arn",
            export_name="StructuredResponseFunctionArn",
        )
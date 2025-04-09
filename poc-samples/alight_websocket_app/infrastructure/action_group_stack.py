import os
from dataclasses import dataclass

from aws_cdk import Aws, CfnOutput, Duration, Stack, aws_bedrock, StackProps
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from cdklabs.generative_ai_cdk_constructs import bedrock
from constructs import Construct

class ActionGroupStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        # Create the structured response Lambda function
        structured_response_function = lambda_.Function(
            self,
            "StructuredResponseHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="structured_response.handler",
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

        # Export the function ARN for use in other stacks
        self.function_arn = structured_response_function.function_arn

        # # Output the function ARN
        # CfnOutput(
        #     self,
        #     "StructuredResponseFunction",
        #     value=self.function_arn,
        #     export_name="StructuredResponseFunction",
        # )

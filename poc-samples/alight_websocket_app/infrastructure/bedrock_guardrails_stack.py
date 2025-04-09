from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class BedrockGuardrailsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.guardrails_bucket_name = None
        self.guardrails_role_arn = None

        # Create S3 bucket for guardrails configuration
        guardrails_bucket = s3.Bucket(
            self,
            "GuardrailsConfigBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Create IAM role for guardrails
        guardrails_role = iam.Role(
            self,
            "BedrockGuardrailsRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )

        # Add permissions for S3 access
        guardrails_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[
                    guardrails_bucket.bucket_arn,
                    f"{guardrails_bucket.bucket_arn}/*",
                ],
            )
        )

        # Store the guardrails role ARN
        self.guardrails_role_arn = guardrails_role.role_arn
        self.guardrails_bucket_name = guardrails_bucket.bucket_name

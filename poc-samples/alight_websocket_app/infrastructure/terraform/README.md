# WebSocket API Terraform Configuration

This directory contains the Terraform configuration for deploying the WebSocket API infrastructure.

## Prerequisites

- Terraform installed (version 1.0.0 or later)
- AWS CLI configured with appropriate credentials
- Python 3.12 for Lambda functions

## Structure

- `websocket_api.tf` - Main Terraform configuration file
- `variables.tf` - Variable definitions
- `terraform.tfvars` - Default variable values

## Required Variables

The following variables must be provided:

- `bedrock_agent_id` - The ID of the Bedrock agent
- `bedrock_agent_alias_id` - The alias ID of the Bedrock agent

## Optional Variables

These variables have defaults but can be overridden:

- `aws_region` (default: "us-east-1")
- `environment` (default: "prod")
- `project_name` (default: "websocket-api")

## Deployment

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Create a `terraform.tfvars` file with your values:
   ```hcl
   bedrock_agent_id = "your-agent-id"
   bedrock_agent_alias_id = "your-agent-alias-id"
   ```

3. Review the planned changes:
   ```bash
   terraform plan
   ```

4. Apply the configuration:
   ```bash
   terraform apply
   ```

## Resources Created

- DynamoDB table for connection tracking
- Lambda functions for WebSocket handlers (connect, disconnect, message)
- SQS queues for message processing
- API Gateway WebSocket API
- IAM roles and policies
- CloudWatch Log groups

## Outputs

- `websocket_endpoint` - The WebSocket API endpoint URL

## Cleanup

To remove all created resources:

```bash
terraform destroy
```
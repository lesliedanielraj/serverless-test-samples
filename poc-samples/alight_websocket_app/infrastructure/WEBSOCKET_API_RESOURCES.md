# WebSocket API Stack Resources

This document lists and explains all the AWS resources provisioned in the WebSocket API Stack.

## DynamoDB Resources

### WebSocket Connections Table
- **Purpose**: Tracks active WebSocket connections and sessions
- **Configuration**:
  - Partition Key: `connection_id` (String)
  - Sort Key: `session_id` (String)
  - Billing Mode: Pay per request
  - Removal Policy: DESTROY

## Lambda Resources

### 1. Connect Handler
- **Purpose**: Handles new WebSocket connections
- **Runtime**: Python 3.12
- **Environment Variables**:
  - CONNECTIONS_TABLE: Name of the connections DynamoDB table
- **Layers**: AWS Lambda Powertools for Python

### 2. Disconnect Handler
- **Purpose**: Handles WebSocket disconnections
- **Runtime**: Python 3.12
- **Environment Variables**:
  - CONNECTIONS_TABLE: Name of the connections DynamoDB table
- **Layers**: AWS Lambda Powertools for Python

### 3. Message Handler
- **Purpose**: Processes messages from the SQS queue and interacts with Bedrock Agent
- **Runtime**: Python 3.12
- **Timeout**: 30 seconds
- **Environment Variables**:
  - CONNECTIONS_TABLE: Name of the connections DynamoDB table
  - BEDROCK_AGENT_ID: ID of the Bedrock agent
  - BEDROCK_AGENT_ALIAS_ID: ID of the Bedrock agent alias
  - WEBSOCKET_CALLBACK_URL: WebSocket stage callback URL
- **Layers**: AWS Lambda Powertools for Python

## SQS Resources

### Message Queue (FIFO)
- **Purpose**: Main queue for processing WebSocket messages
- **Configuration**:
  - FIFO Queue: Yes
  - Message Retention: 1 day
  - Dead Letter Queue: Configured
  - Max Receive Count: 3

### Dead Letter Queue (FIFO)
- **Purpose**: Handles failed message processing
- **Configuration**:
  - FIFO Queue: Yes
  - Message Retention: 1 day

## IAM Resources

### 1. Message Handler Role
- **Purpose**: IAM role for the message handler Lambda function
- **Permissions**:
  - Bedrock: InvokeModel, InvokeAgent
  - CloudWatch Logs: Basic Lambda execution
  - Lambda: GetLayerVersion for Powertools
  - API Gateway: ManageConnections

### 2. Service Proxy Execution Role
- **Purpose**: Role for API Gateway service proxy execution
- **Permissions**:
  - SQS: SendMessage, ReceiveMessage, DeleteMessage, GetQueueAttributes

## API Gateway Resources

### WebSocket API
- **Purpose**: Manages WebSocket connections and message routing
- **Routes**:
  - Connect: Integrated with Connect Handler Lambda
  - Disconnect: Integrated with Disconnect Handler Lambda
  - Default: Integrated with SQS message queue

### WebSocket Stage
- **Name**: prod
- **Configuration**:
  - Auto Deploy: Enabled
  - Rate Limit: 50 requests/second
  - Burst Limit: 100 requests

## CloudWatch Resources

### Log Group
- **Purpose**: API Gateway logging
- **Configuration**:
  - Retention: 1 week
  - Removal Policy: DESTROY

## Resource Permissions

### DynamoDB Permissions
- Connect Handler: Read/Write access to connections table
- Disconnect Handler: Read/Write access to connections table
- Message Handler: Read/Write access to connections table

### SQS Permissions
- Message Handler: Consume messages from message queue
- Service Proxy Role: Full queue management permissions
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import SQSEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from shared.jwt_handler import JWTDecoder

logger = Logger(service="websocket-message-handler")

from shared.invoke_agent import BedrockAgent
from shared.utilities import format_response

dynamodb = boto3.resource("dynamodb")

def send_websocket_message(
    connection_id: str, message: Dict[str, Any], management_api: Any
) -> None:
    """Send message through WebSocket connection.

    Args:
        connection_id: WebSocket connection ID
        message: Message payload to send

    Raises:
        ClientError: If sending message fails
    """
    try:
        logger.info("Sending message to connection %s - %s", connection_id, message)
        management_api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(message))
    except ClientError as e:
        if e.response["Error"]["Code"] == "GoneException":
            logger.warning("Connection %s no longer exists", connection_id)
            raise
        logger.error("Failed to send message to connection %s", connection_id)
        raise


def get_session_id(connection_id: str) -> str:
    """Get session_id for a connection from DynamoDB.

    Args:
        connection_id: WebSocket connection ID

    Returns:
        str: The session_id for the connection

    Raises:
        ClientError: If DynamoDB query fails
    """
    table = dynamodb.Table(os.environ["CONNECTIONS_TABLE"])
    response = table.query(
        KeyConditionExpression="connection_id = :connection_id",
        ExpressionAttributeValues={":connection_id": connection_id},
        Limit=1,
    )

    if not response["Items"]:
        raise ValueError(f"No session found for connection {connection_id}")

    return response["Items"][0]["session_id"]


def get_message_attribute(
    message_attributes: Dict[str, Any],
    attribute_name: str,
    default_value: Optional[str] = None,
) -> Optional[str]:
    """
    Safely extract message attribute value with logging
    """
    attribute = message_attributes.get(attribute_name)
    if not attribute:
        logger.warning(f"Missing '{attribute_name}' in message attributes")
        return default_value

    logger.info(f"attribute: {attribute}")

    return attribute["stringValue"]


@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Handle WebSocket messages from SQS queue by invoking Bedrock agent and returning response.

    Args:
        event: SQS event containing WebSocket API message
        context: Lambda context

    Returns:
        API Gateway response dictionary
    """
    try:
        # Generate sample JWT Token using JWTDecoder
        jwt_decoder = JWTDecoder()
        token = jwt_decoder.generate_sample_token()

        management_api = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=os.environ.get("WEBSOCKET_CALLBACK_URL"),
        )

        # Create SQSEvent from the raw event dictionary
        sqs_event = SQSEvent(event)
        for record in sqs_event.records:
            message_attributes = record.message_attributes

            # Extract required attributes
            connection_id = get_message_attribute(message_attributes, "connectionId")
            if not connection_id:
                logger.error("Missing required connectionId attribute")
                return format_response(
                    400, {"message": "Missing 'connectionId' in message attributes"}
                )

            # Get session_id from DynamoDB
            session_id = get_session_id(connection_id)
            # Enrich logs with connection and session IDs
            logger.append_keys(connection_id=connection_id, session_id=session_id)

            # Parse and validate input message
            try:
                body = record.body
                if isinstance(record.body, str):
                    body = json.loads(body)

                logger.info(f"body: {body}")
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Error processing message body: {str(e)}")
                return format_response(400, {"message": "Invalid message format"})

            message = body.get("message")
            if not message:
                logger.error("Missing required 'message' field")
                return format_response(400, {"message": "Missing required 'message' field"})

            # Invoke Bedrock agent
            try:
                bedrock_agent = BedrockAgent(
                    os.environ.get("BEDROCK_AGENT_ID"),
                    os.environ.get("BEDROCK_AGENT_ALIAS_ID"),
                )
                # Extract claims from token
                token_claims = jwt_decoder.get_token_claims(token, verify=False)
                name = token_claims.get("name")
                roles = ",".join(token_claims.get("roles", []))

                # Create session state with token, name and roles
                session_state = {
                    "promptSessionAttributes": {
                        "name": name,  # Get name from event or empty string
                        "roles": roles,  # Get roles from event or empty list
                        # ... existing session attributes ...
                    },
                    # ... rest of session_state ...
                }

                logger.info(f"session_state: {session_state}")

                agent_response = bedrock_agent.invoke(
                    message, session_id, enable_trace=True, session_state=session_state
                )

                # Prepare response with timestamp
                response_payload = {
                    "type": "agent_response",
                    "message": agent_response,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }

                # Send response through WebSocket
                send_websocket_message(connection_id, response_payload, management_api)
                logger.info("Successfully sent agent response to client")

                return format_response(200, {"message": "Message processed successfully"})

            except ClientError as e:
                if e.response["Error"]["Code"] == "GoneException":
                    return format_response(
                        410, {"message": "WebSocket connection no longer available"}
                    )

                error_msg = f"AWS service error: {str(e)}"
                logger.exception(error_msg)
                return format_response(500, {"message": error_msg})

    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        logger.exception(error_msg)
        send_websocket_message(connection_id, e, management_api)
        return format_response(500, {"message": "Internal server error"})

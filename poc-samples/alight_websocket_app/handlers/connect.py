import os
import uuid

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from utilities import format_response, validate_connection_id

logger = Logger(service="websocket-connect-handler")

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext):
    if not validate_connection_id(event):
        logger.error("Invalid connection ID")
        return {
            'statusCode': 400,
            'body': '{"message": "Invalid connection ID"}'
        }

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["CONNECTIONS_TABLE"])

    connection_id = event["requestContext"]["connectionId"]
    logger.append_keys(connection_id=connection_id)
    logger.info("Processing connection request")

    try:
        session_id = str(uuid.uuid4())
        table.put_item(Item={"connection_id": connection_id, "session_id": session_id})
        return format_response(200, {"message": "Connected", "session_id": session_id})
    except ClientError as e:
        logger.exception(
            "AWS service error", extra={"error_code": e.response["Error"]["Code"]}
        )
        return format_response(500, {"message": "Internal server error"})
    except Exception as e:
        logger.exception("Failed to connect")
        return format_response(500, {"message": "Internal server error"})

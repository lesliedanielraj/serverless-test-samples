import os

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from utilities import format_response, validate_input, validate_connection_id

logger = Logger(service="websocket-disconnect-handler")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext):
    if not validate_connection_id(event):
        logger.error("Invalid connection ID")
        return {"statusCode": 400, "body": '{"message": "Invalid connection ID"}'}
    connection_id = event["requestContext"]["connectionId"]
    logger.append_keys(connection_id=connection_id)
    logger.info("Processing disconnection request")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["CONNECTIONS_TABLE"])

    try:
        # Query for the connection's session first since we need both keys
        response = table.query(
            KeyConditionExpression="connection_id = :connectionId",
            ExpressionAttributeValues={":connectionId": connection_id},
        )
        for item in response["Items"]:
            table.delete_item(Key={"connection_id": connection_id})
        return format_response(200, {"message": "Disconnected"})
    except ClientError as e:
        logger.exception(
            "AWS service error", extra={"error_code": e.response["Error"]["Code"]}
        )
        return format_response(500, {"message": "Internal server error"})
    except Exception as e:
        logger.exception("Failed to disconnect")
        return format_response(500, {"message": "Internal server error"})

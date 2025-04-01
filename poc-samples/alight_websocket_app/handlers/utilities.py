import json
from typing import Any

from aws_lambda_powertools import Logger

logger = Logger(service="websocket-utilities")


def format_response(status_code: int, body: Any) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body) if not isinstance(body, str) else body,
    }


def validate_input(event: dict) -> bool:
    required_fields = ["requestContext", "connectionId"]
    return all(field in event.get("requestContext", {}) for field in ["connectionId"])

def validate_connection_id(event):
    try:
        # Check if requestContext and connectionId exist
        if not event.get("requestContext") or "connectionId" not in event["requestContext"]:
            return False

        connection_id = event["requestContext"]["connectionId"]

        # Validate that connectionId is not empty
        if not connection_id or not isinstance(connection_id, str):
            return False

        # # AWS WebSocket connectionId is typically alphanumeric
        # # and around 16-20 characters long
        # if not connection_id.isalnum():
        #     return False
        #
        # # Optional: Add minimum/maximum length validation
        # if len(connection_id) < 10 or len(connection_id) > 128:
        #     return False

        return True

    except Exception as e:
        print(f"Error validating connectionId: {str(e)}")
        return False

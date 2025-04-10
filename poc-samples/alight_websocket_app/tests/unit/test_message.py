import json
from datetime import datetime
from unittest.mock import ANY, Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from handlers.websocket_message import handler


@pytest.fixture
def valid_sqs_record():
    return {"body": json.dumps({"message": "test message", "connectionId": "test-connection-id"})}


@pytest.fixture
def bedrock_runtime_client():
    with mock_aws():
        client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
        yield client


@mock_aws()
def test_successful_message_processing(
    environment_vars, sqs_event, dynamodb_table, bedrock_runtime_client, context
):
    boto3.setup_default_session(region_name="us-east-1")
    dynamodb = boto3.client("dynamodb")
    connection_id = "test-connection-123"

    # Insert test data
    dynamodb.put_item(
        TableName=dynamodb_table,
        Item={
            "connection_id": {"S": connection_id},
            "session_id": {"S": "test-session"},
        },
    )
    sqs_event["Records"][0]["messageAttributes"]["connectionId"]["stringValue"] = connection_id

    # Call the handler
    response = handler(sqs_event, context)

    # Assertions
    assert response["statusCode"] == 200
    assert response["body"] == json.dumps({"message": "Message processed successfully"})

    # Verify BedrockAgent was called correctly
    bedrock_runtime_client.assert_called_once()

    # Get the actual call arguments
    call_args = bedrock_runtime_client.return_value.invoke.call_args[1]

    # Verify basic parameters
    assert call_args["message"] == "test message"
    assert call_args["enable_trace"] is True

    # Verify session state contains token, name and roles
    session_state = call_args["session_state"]
    assert "token" in session_state
    assert "name" in session_state
    assert "roles" in session_state
    assert isinstance(session_state["roles"], list)  # Verify roles is a list


def test_invalid_message_format():
    invalid_record = {"body": "invalid json"}

    response = handler({"Records": [invalid_record]}, {})

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["message"] == "Invalid message format"


def test_missing_message_field():
    record = {
        "body": json.dumps(
            {
                "connectionId": "test-connection-id"
                # message field missing
            }
        )
    }

    response = handler({"Records": [record]}, {})

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["message"] == "Missing required 'message' field"


def test_websocket_connection_gone():
    with patch("your_module.BedrockAgent") as mock_bedrock:
        with patch("boto3.client") as mock_boto3:
            # Setup mock for websocket API to raise GoneException
            mock_management_api = Mock()
            mock_management_api.post_to_connection.side_effect = ClientError(
                {"Error": {"Code": "GoneException", "Message": "Connection is gone"}},
                "post_to_connection",
            )
            mock_boto3.return_value = mock_management_api

            response = handler({"Records": [valid_sqs_record]}, {})

            assert response["statusCode"] == 410
            assert (
                json.loads(response["body"])["message"]
                == "WebSocket connection no longer available"
            )


@pytest.mark.parametrize(
    "body,expected_status",
    [
        ({}, 400),  # Empty body
        ({"message": ""}, 400),  # Empty message
        ({"message": None}, 400),  # None message
    ],
)
def test_invalid_message_variations(body, expected_status):
    record = {"body": json.dumps(body)}

    response = handler({"Records": [record]}, {})

    assert response["statusCode"] == expected_status

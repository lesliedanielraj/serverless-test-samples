# conftest.py
import os
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def environment_vars(monkeypatch):
    env_vars = {
        "CONNECTIONS_TABLE": "WebSocketConnections",  # Match the table name used in dynamodb_table
        "AWS_REGION": "us-east-1",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "BEDROCK_AGENT_ID": "testing",
        "BEDROCK_AGENT_ALIAS_ID": "testing",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    yield env_vars


@pytest.fixture
def dynamodb_client(environment_vars):
    """Create a dynamodb client using moto."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name=environment_vars["AWS_REGION"])
        yield client


@pytest.fixture
def dynamodb_table(dynamodb_client):
    """Create a mock DynamoDB table."""
    table_name = "WebSocketConnections"
    dynamodb_client.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "connection_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "connection_id", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )
    yield table_name


@pytest.fixture
def websocket_api_event():
    return {
        "requestContext": {
            "connectionId": "test-connection-123",
            "domainName": "test-domain",
            "stage": "test",
        },
        "headers": {"Host": "test-host"},
    }


@pytest.fixture
def sqs_event():
    return {
        "Records": [
            {
                "body": '{"message": "test message"}',
                "messageAttributes": {"connectionId": {"stringValue": "test-connection-123"}},
            }
        ]
    }


@pytest.fixture
def mock_quicksight():
    with patch('boto3.client') as mock_client:
        # Mock the QuickSight client response
        mock_quicksight = MagicMock()
        mock_quicksight.generate_embed_url_for_anonymous_user.return_value = {
            'EmbedUrl': 'https://quicksight-test.dasboard/test-dashboard-123',
            'RequestId': 'test-request-id'
        }
        mock_client.return_value = mock_quicksight
        yield mock_quicksight


@pytest.fixture
def context():
    class LambdaContext:
        def __init__(self):
            self.function_name = ("test-function",)
            self.function_version = ("1",)
            self.invoked_function_arn = (
                "arn:aws:lambda:us-east-1:123456789012:function:test-function",
            )
            self.memory_limit_in_mb = (128,)
            self.aws_request_id = ("test-request-123",)
            self.log_group_name = ("/aws/lambda/test-function",)
            self.log_stream_name = ("2023/12/31/[$LATEST]123456789",)
            self.identity = (None,)
            self.client_context = (None,)
            self.remaining_time_in_millis = 30000

    return LambdaContext()


@pytest.fixture
def mock_sts():
    with patch('boto3.client') as mock_client:
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {
            'Account': '123456789012'
        }
        mock_client.return_value = mock_sts
        yield mock_sts

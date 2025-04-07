import boto3
import pytest
from moto import mock_aws

from handlers.connect import handler


@mock_aws()
def test_connect_handler_success(
    environment_vars, dynamodb_table, websocket_api_event, context
):
    """Test successful connection handling"""
    boto3.setup_default_session(region_name="us-east-1")
    response = handler(websocket_api_event, context)

    assert response["statusCode"] == 200
    assert "body" in response

    # Verify the connection was stored in DynamoDB
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    result = dynamodb.scan(TableName=dynamodb_table)
    items = result["Items"]

    assert len(items) == 1
    assert (
        items[0]["connection_id"]["S"]
        == websocket_api_event["requestContext"]["connectionId"]
    )
    assert "session_id" in items[0]


@mock_aws()
def test_connect_handler_missing_connection_id(
    environment_vars, dynamodb_table, context
):
    """Test handling of missing connectionId"""
    boto3.setup_default_session(region_name="us-east-1")
    event = {"requestContext": {}, "headers": {"Host": "test-host"}}

    response = handler(event, context)
    assert response["statusCode"] == 400
    assert '{"message": "Invalid connection ID"}' in response["body"]


@pytest.mark.parametrize(
    "event_data",
    [
        {},  # Empty event
        {"requestContext": None},  # None requestContext
        {"requestContext": {}, "headers": None},  # Missing headers
    ],
)
@mock_aws()
def test_connect_handler_invalid_event(
    environment_vars, dynamodb_table, event_data, context
):
    """Test handling of invalid event structures"""
    response = handler(event_data, context)
    assert response["statusCode"] == 400
    assert "Invalid connection ID" in response["body"]


@mock_aws()
def test_connect_handler_duplicate_connection(
    environment_vars, dynamodb_table, websocket_api_event, context
):
    """Test handling of duplicate connections"""
    boto3.setup_default_session(region_name="us-east-1")
    # First connection
    response1 = handler(websocket_api_event, context)
    assert response1["statusCode"] == 200

    # Second connection with same connectionId
    response2 = handler(websocket_api_event, context)
    assert response2["statusCode"] == 200

    # Verify only one connection exists
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    result = dynamodb.scan(TableName=dynamodb_table)
    print(result["Items"])
    assert len(result["Items"]) == 1


@mock_aws()
def test_connect_handler_table_not_exists(
    environment_vars, websocket_api_event, context
):
    """Test handling when DynamoDB table doesn't exist"""
    boto3.setup_default_session(region_name="us-east-1")
    # Don't create the table
    response = handler(websocket_api_event, context)
    assert response["statusCode"] == 500
    assert "error" in response["body"]

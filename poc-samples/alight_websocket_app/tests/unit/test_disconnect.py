# test_disconnect.py
import os
import boto3
from moto import mock_aws
from handlers.disconnect import handler

@mock_aws
def test_disconnect_success(environment_vars, dynamodb_table, websocket_api_event, context):
    # Setup
    boto3.setup_default_session(region_name="us-east-1")
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    connection_id = "test-connection-id"

    # Insert test data
    dynamodb.put_item(
        TableName=dynamodb_table,
        Item={
            "connection_id": {"S": connection_id},
            "session_id": {"S": "test-session"}
        }
    )
    websocket_api_event["requestContext"]["connectionId"] = connection_id

    # Execute
    response = handler(websocket_api_event, context)

    # Verify
    assert response["statusCode"] == 200
    assert response["body"] == '{"message": "Disconnected"}'

    # Verify item was deleted
    items = dynamodb.scan(TableName=dynamodb_table)["Items"]
    assert len(items) == 0

@mock_aws
def test_disconnect_no_connection(environment_vars, dynamodb_table, websocket_api_event, context):
    boto3.setup_default_session(region_name="us-east-1")
    # Execute
    response = handler(websocket_api_event, context)

    # Verify - should still return 200 even if connection not found
    assert response["statusCode"] == 200
    assert response["body"] == '{"message": "Disconnected"}'

@mock_aws
def test_disconnect_missing_connection_id(environment_vars, dynamodb_table, context):
    boto3.setup_default_session(region_name="us-east-1")
    # Setup
    event = {"requestContext": {}}  # Missing connectionId

    # Execute
    response = handler(event, context)

    # Verify
    assert response["statusCode"] == 400
    assert response["body"] == '{"message": "Invalid connection ID"}'

@mock_aws
def test_disconnect_dynamodb_error(websocket_api_event, context):
    boto3.setup_default_session(region_name="us-east-1")
    # Setup - using non-existent table
    os.environ["CONNECTIONS_TABLE"] = "wrong-table-name"

    # Execute
    response = handler(websocket_api_event, context)

    # Verify
    assert response["statusCode"] == 500
    assert response["body"] == '{"message": "Internal server error"}'

@mock_aws
def test_disconnect_with_empty_table(environment_vars, dynamodb_table, websocket_api_event, context):
    boto3.setup_default_session(region_name="us-east-1")
    # Execute
    response = handler(websocket_api_event, context)

    # Verify
    assert response["statusCode"] == 200
    assert response["body"] == '{"message": "Disconnected"}'

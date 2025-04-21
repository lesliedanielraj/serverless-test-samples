import json
from unittest.mock import MagicMock, patch

import pytest
from moto import mock_aws

from handlers.ag_dashboard_details import handler


@pytest.fixture
def valid_event():
    return {
        "agent": "test-agent",
        "actionGroup": "DashboardDetails",
        "function": "GetDashboardDetails",
        "parameters": [{"name": "dashboard_id", "value": "test-dashboard-123"}],
        "sessionAttributes": {
            "quicksight_dashboard_url": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "quicksight_dashboard_id": "XXXXXXXXXXXXXXXXXX",
            "quicksight_account_id": "XXXXXXXXXXXXXXXX",
            "quicksight_region": "us-west-2",
            "quicksight_namespace": "default",
        },
        "promptSessionAttributes": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "company": "Example Inc.",
            "roles": "Manager,HR",
        },
    }


@pytest.fixture
def invalid_event():
    return {
        "agent": "test-agent",
        "actionGroup": "DashboardDetails",
        "function": "GetDashboardDetails",
        "parameters": [],  # Missing dashboard_id
        "sessionAttributes": {},
        "promptSessionAttributes": {},
    }

def test_handler_success(mock_quicksight, valid_event, context):
    response = handler(valid_event, context)

    # Verify QuickSight client was called correctly
    mock_quicksight.generate_embed_url_for_anonymous_user.assert_called_once()

    # Verify response structure
    assert response["messageVersion"] == "1.0"
    assert response["response"]["actionGroup"] == "DashboardDetails"
    assert response["response"]["function"] == "GetDashboardDetails"

    # Get response body
    response_body = json.loads(response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"])

    # Verify response contents
    assert "dashboard_url" in response_body
    assert response_body["dashboard_url"] == "https://quicksight-test.dasboard/test-dashboard-123"

@mock_aws()
def test_handler_missing_dashboard_id(mock_quicksight, context):
    event = {
        "actionGroup": "DashboardDetails",
        "function": "GetDashboardDetails",
        "parameters": [],
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    }

    response = handler(event, context)
    response_body = json.loads(response["response"]["functionResponse"]["responseBody"])

    assert response_body["response_type"] == "ERROR"
    assert response_body["error_message"] == "dashboard_id is required"

def test_handler_quicksight_error(mock_quicksight, valid_event, context):
    # Mock QuickSight error
    mock_quicksight.generate_embed_url_for_anonymous_user.side_effect = Exception("QuickSight error")

    response = handler(valid_event, context)
    response_body = json.loads(response["response"]["functionResponse"]["responseBody"])

    assert response_body["response_type"] == "ERROR"
    assert response_body["error_message"] == "QuickSight error"


# def test_handler_with_sts(mock_quicksight, mock_sts, valid_event, context):
#     response = handler(valid_event, context)
#
#     # Verify STS was called
#     mock_sts.get_caller_identity.assert_called_once()
#
#     # Verify response
#     response_body = json.loads(response["response"]["functionResponse"]["responseBody"])
#     assert "dashboard_url" in response_body

@mock_aws()
def test_handler_with_session_attributes(mock_quicksight, context):
    event = {
        "actionGroup": "DashboardDetails",
        "function": "GetDashboardDetails",
        "parameters": [
            {
                "name": "dashboard_id",
                "value": "test-dashboard-id"
            }
        ],
        "sessionAttributes": {"test": "value"},
        "promptSessionAttributes": {"prompt": "test"}
    }

    response = handler(event, context)

    # Verify session attributes are preserved
    assert response["sessionAttributes"] == {"test": "value"}
    assert response["promptSessionAttributes"] == {"prompt": "test"}

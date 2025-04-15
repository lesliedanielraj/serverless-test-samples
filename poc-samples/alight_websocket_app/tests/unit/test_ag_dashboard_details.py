import json
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
        "sessionAttributes": {},
        "promptSessionAttributes": {},
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


@mock_aws
def test_handler_success(valid_event, context):
    # Test successful execution
    response = handler(valid_event, context)

    # Verify response structure
    assert response["messageVersion"] == "1.0"
    assert response["response"]["actionGroup"] == "DashboardDetails"
    assert response["response"]["function"] == "GetDashboardDetails"

    # Parse response body
    response_body = json.loads(response["response"]["functionResponse"]["responseBody"])
    assert "dashboard_url" in response_body
    assert response_body["dashboard_url"] == f"https://quicksight-test.dasboard/test-dashboard-123"

    # Verify session attributes are preserved
    assert "sessionAttributes" in response
    assert "promptSessionAttributes" in response


@mock_aws
def test_handler_missing_parameter(invalid_event, context):
    # Test execution with missing dashboard_id
    response = handler(invalid_event, context)

    # Verify response structure
    assert response["messageVersion"] == "1.0"
    assert response["response"]["actionGroup"] == "DashboardDetails"
    assert response["response"]["function"] == "GetDashboardDetails"
    assert response["response"]["functionResponse"]["responseState"] == "FAILURE"

    # Parse error response body
    error_body = json.loads(response["response"]["functionResponse"]["responseBody"])
    assert error_body["response_type"] == "error"
    assert error_body["error_code"] == "HANDLER_ERROR"
    assert "error_message" in error_body


#
# @mock_aws
# def test_handler_invalid_input(context):
#     # Test with completely invalid input
#     invalid_input = {"wrong": "format"}
#     response = handler(invalid_input, context)
#
#     # Verify error response
#     assert response["messageVersion"] == "1.0"
#     assert "response" in response
#     assert "functionResponse" in response["response"]
#     assert response["response"]["functionResponse"]["responseState"] == "FAILURE"
#
#     # Parse error response body
#     error_body = json.loads(response["response"]["functionResponse"]["responseBody"])
#     assert error_body["response_type"] == "error"
#     assert error_body["error_code"] == "HANDLER_ERROR"
#     assert "error_message" in error_body

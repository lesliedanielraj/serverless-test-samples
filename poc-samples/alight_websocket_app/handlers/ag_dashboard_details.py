import datetime
import json
from typing import Any, Dict

from aws_lambda_powertools import Logger
from shared.utilities import get_parameter_value

logger = Logger(service="dashboard-details-handler")


@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for structured response action group.
    """
    agent = event["agent"]
    action_group = event["actionGroup"]
    function = event["function"]
    parameters = event.get("parameters", [])
    session_attributes = event["sessionAttributes"]
    prompt_session_attributes = event["promptSessionAttributes"]

    # Create and return the expected structured response
    response_body = {"TEXT": {"body": ""}}
    function_response = {"actionGroup": action_group, "function": function, "functionResponse": {}}
    action_response = {"messageVersion": "1.0", "response": {}}
    try:
        # set session and promptSession attributes
        if session_attributes:
            action_response["sessionAttributes"] = session_attributes
        if prompt_session_attributes:
            action_response["promptSessionAttributes"] = prompt_session_attributes

        # Business Logic goes here
        dashboard_id = get_parameter_value(parameters, "dashboard_id")
        if not dashboard_id:
            raise ValueError("dashboard_id is required")

        response = {"dashboard_url": f"https://quicksight-test.dasboard/{dashboard_id}"}

        # set a successful response
        response_body["TEXT"]["body"] = json.dumps(response)
        function_response["functionResponse"]["responseBody"] = response_body
        action_response["response"] = function_response

        logger.info(action_response)
        return action_response

    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        error_response = {
            "response_type": "error",
            "error_code": "HANDLER_ERROR",
            "error_message": str(e),
            "details": {},
        }

        # set a successful response
        function_response["functionResponse"]["responseState"] = "FAILURE"  # FAILURE | REPROMPT
        function_response["functionResponse"]["responseBody"] = json.dumps(error_response)
        action_response["response"] = function_response

    finally:
        return action_response

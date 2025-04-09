import datetime
import json
from typing import Any, Dict

from aws_lambda_powertools import Logger

logger = Logger(service="structured-response-handler")

# Define our JSON schemas for different types of responses
SCHEMAS = {
    "general_response": {
        "type": "object",
        "properties": {
            "response_type": {"type": "string", "enum": ["general"]},
            "message": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "metadata": {"type": "object"},
        },
        "required": ["response_type", "message"],
    },
    "error_response": {
        "type": "object",
        "properties": {
            "response_type": {"type": "string", "enum": ["error"]},
            "error_code": {"type": "string"},
            "error_message": {"type": "string"},
            "details": {"type": "object"},
        },
        "required": ["response_type", "error_code", "error_message"],
    },
}


def validate_against_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate the response data against a predefined schema.
    """
    try:
        from jsonschema import validate

        schema = SCHEMAS.get(schema_name)
        if not schema:
            raise ValueError(f"Schema {schema_name} not found")
        validate(instance=data, schema=schema)
        return True
    except Exception as e:
        logger.error(f"Schema validation error: {str(e)}")
        return False


def create_structured_response(input_text: str) -> Dict[str, Any]:
    """
    Create a structured response based on the input.
    """
    try:
        # Create a structured response
        response = {
            "response_type": "general",
            "message": input_text,
            "confidence": 1.0,
            "metadata": {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
        }

        # Validate the response
        # if not validate_against_schema(response, "general_response"):
        #     return {
        #         "response_type": "error",
        #         "error_code": "SCHEMA_VALIDATION_ERROR",
        #         "error_message": "Failed to create a valid structured response",
        #         "details": {},
        #     }

        return response

    except Exception as e:
        logger.error(f"Error creating structured response: {str(e)}")
        return {
            "response_type": "error",
            "error_code": "INTERNAL_ERROR",
            "error_message": str(e),
            "details": {},
        }


def get_parameter_value(
    parameters: list, param_name: str, required: bool = False
) -> Any:
    try:
        value = next(
            (param["value"] for param in parameters if param.get("name") == param_name),
            None,
        )

        if required and value is None:
            raise ValueError(f"Required parameter '{param_name}' not found")

        return value

    except Exception as e:
        logger.error(f"Error getting parameter {param_name}: {str(e)}")
        if required:
            raise
        return None


@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for structured response action group.
    """
    try:
        agent = event["agent"]
        actionGroup = event["actionGroup"]
        function = event["function"]
        parameters = event.get("parameters", [])

        # Create and return the structured response

        input_text = get_parameter_value(parameters, "inputText")
        response = create_structured_response(input_text)

        response_body = {"TEXT": {"body": json.dumps(response)}}

        function_response = {
            "actionGroup": event["actionGroup"],
            "function": event["function"],
            "functionResponse": {"responseBody": response_body},
        }

        session_attributes = event["sessionAttributes"]
        prompt_session_attributes = event["promptSessionAttributes"]

        action_response = {
            "messageVersion": "1.0",
            "response": function_response,
            "sessionAttributes": session_attributes,
            "promptSessionAttributes": prompt_session_attributes,
        }

        logger.info("Printing Action Response")
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
        return {
            "statusCode": 500,
            "body": json.dumps(error_response),
            "headers": {"Content-Type": "application/json"},
        }

import json
from unittest.mock import MagicMock, patch

import pytest

from handlers.shared.invoke_agent import BedrockAgent


@pytest.fixture
def mock_bedrock_client():
    with patch("boto3.client") as mock_client:
        yield mock_client.return_value


@pytest.fixture
def bedrock_agent(mock_bedrock_client):
    return BedrockAgent(agent_id="test-agent", alias_id="test-alias")


def test_bedrock_agent_initialization():
    """Test BedrockAgent initialization with correct parameters."""
    agent = BedrockAgent(agent_id="test-agent", alias_id="test-alias")
    assert agent.agent_id == "test-agent"
    assert agent.alias_id == "test-alias"


def test_invoke_successful_response(bedrock_agent, mock_bedrock_client):
    """Test successful agent invocation with a normal response."""
    # Mock response data
    mock_response = {
        "completion": [{"chunk": {"bytes": b'{"response": "This is a test response"}'}}]
    }
    mock_bedrock_client.invoke_agent.return_value = mock_response

    # Test parameters
    query = "test query"
    session_id = "test-session"
    session_state = {"key": "value"}

    # Call the method
    response = bedrock_agent.invoke(
        query=query,
        session_id=session_id,
        enable_trace=True,
        session_state=session_state,
    )

    # Verify the response
    assert response == '{"response": "This is a test response"}'

    # Verify the client was called with correct parameters
    mock_bedrock_client.invoke_agent.assert_called_once_with(
        agentId="test-agent",
        agentAliasId="test-alias",
        sessionId=session_id,
        inputText=query,
        sessionState=session_state,
    )


def test_invoke_with_trace_event(bedrock_agent, mock_bedrock_client):
    """Test agent invocation with trace events in the response."""
    # Mock response with both chunk and trace events
    mock_response = {
        "completion": [
            {"trace": {"type": "trace", "content": "trace data"}},
            {"chunk": {"bytes": b'{"response": "Final response"}'}},
        ]
    }
    mock_bedrock_client.invoke_agent.return_value = mock_response

    response = bedrock_agent.invoke(
        query="test query",
        session_id="test-session",
        enable_trace=True,
    )

    assert response == '{"response": "Final response"}'


def test_invoke_with_default_session_state(bedrock_agent, mock_bedrock_client):
    """Test agent invocation with default (None) session state."""
    mock_response = {"completion": [{"chunk": {"bytes": b'{"response": "Test response"}'}}]}
    mock_bedrock_client.invoke_agent.return_value = mock_response

    response = bedrock_agent.invoke(
        query="test query",
        session_id="test-session",
    )

    # Verify empty dict was used for session_state
    mock_bedrock_client.invoke_agent.assert_called_once_with(
        agentId="test-agent",
        agentAliasId="test-alias",
        sessionId="test-session",
        inputText="test query",
        sessionState={},
    )


def test_invoke_unexpected_event(bedrock_agent, mock_bedrock_client):
    """Test agent invocation with unexpected event type."""
    mock_response = {"completion": [{"unexpected": {"data": "something unexpected"}}]}
    mock_bedrock_client.invoke_agent.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        bedrock_agent.invoke(
            query="test query",
            session_id="test-session",
        )

    assert "unexpected event" in str(exc_info.value)


def test_invoke_empty_completion(bedrock_agent, mock_bedrock_client):
    """Test agent invocation with empty completion list."""
    mock_response = {"completion": []}
    mock_bedrock_client.invoke_agent.return_value = mock_response

    response = bedrock_agent.invoke(
        query="test query",
        session_id="test-session",
    )

    assert response is None

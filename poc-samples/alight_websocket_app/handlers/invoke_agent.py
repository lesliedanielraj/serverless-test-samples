import json
from typing import Any

import boto3
from aws_lambda_powertools import Logger

logger = Logger(service="websocket-invoke-agent")


class BedrockAgent:
    def __init__(self, agent_id: str, alias_id: str):
        """Initialize BedrockAgent with agent and alias IDs.

        Args:
            agent_id (str): The Bedrock agent ID
            alias_id (str): The Bedrock agent alias ID
        """
        self.agent_id = agent_id
        self.alias_id = alias_id
        self._client = boto3.client("bedrock-agent-runtime")

    def invoke(
        self,
        query: str,
        session_id: str,
        enable_trace: bool = False,
        session_state: dict = None,
    ) -> Any | None:
        """Invoke the Bedrock agent with the given query synchronously.

        Args:
            query (str): The input text to send to the agent
            session_id (str): The session ID for the conversation
            enable_trace (bool, optional): Whether to enable tracing. Defaults to False.
            session_state (dict, optional): The session state. Defaults to None.

        Returns:
            str: The agent's response
        """
        if session_state is None:
            session_state = {}

        if enable_trace:
            logger.info(
                f"query: {query}, session_id: {session_id}, agent_id: {self.agent_id}, alias_id: {self.alias_id}"
            )

        # invoke the agent API and measure response time
        import time

        start_time = time.time()
        agent_response = self._client.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            sessionId=session_id,
            inputText=query,
            # enableTrace=enable_trace,
            # endSession=False,
            # sessionState=session_state,
        )
        end_time = time.time()
        response_time = end_time - start_time

        if enable_trace:
            logger.info(f"Bedrock agent response time: {response_time:.2f} seconds")
            logger.info(agent_response)

        event_stream = agent_response["completion"]
        try:
            for event in event_stream:
                if "chunk" in event:
                    data = event["chunk"]["bytes"]
                    if enable_trace:
                        logger.info(f"Final answer ->\n{data.decode('utf8')}")
                    agent_answer = data.decode("utf8")
                    return agent_answer
                elif "trace" in event:
                    if enable_trace:
                        logger.info(json.dumps(event["trace"], indent=2))
                else:
                    raise Exception("unexpected event.", event)
        except Exception as e:
            raise Exception("unexpected event.", e)

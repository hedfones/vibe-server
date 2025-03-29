#!/usr/bin/env python3
"""
Module for AWS Bedrock-based Assistant using LangChain 0.3.

This module creates an agent with structured tools and maintains a conversation thread.
It leverages AWS Bedrock as the language model backend and uses LangChain's utilities
for conversation memory and tool integration.

Attributes:
    log (structlog.stdlib.BoundLogger): Logger for the module.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Callable

import structlog
from langchain.tools import StructuredTool
from langchain.tools.base import BaseTool
from langchain_aws.chat_models import ChatBedrockConverse
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from .database import Assistant
from .functions import (
    get_availability,
    get_product_list,
    get_product_locations,
    get_product_photos,
    handoff_conversation_to_admin,
    set_appointment,
)
from .model import (
    CheckAvailabilityTool,
    GetProductLocationsTool,
    GetProductPhotosTool,
    HandoffToAdminTool,
    SetAppointmentsRequest,
)

log = structlog.stdlib.get_logger()


class BedrockAssistant:
    """
    An assistant using AWS Bedrock within LangChain.

    This class encapsulates the logic for interacting with the AWS Bedrock LLM,
    managing conversation memory, tools, and executing the agent chain.
    """

    def __init__(
        self,
        assistant_config: Assistant,
        client_timezone: str = "UTC",
        thread_id: str | None = None,
        memory: PostgresSaver | None = None,
    ) -> None:
        """
        Initialize the BedrockAssistant instance.
        https://python.langchain.com/docs/how_to/message_history/#setup

        Args:
            credentials (AWSCredentials | None): AWS credentials; if None, uses environment variables.
            assistant_id (str): Identifier for the assistant.
            client_timezone (str): Timezone for client interactions.
            thread_id (str | None): Optional thread identifier.
            model_id (str): AWS Bedrock model identifier.
            instructions (str): Instructional context for the assistant.
        """
        log.debug("Initializing BedrockAssistant", assistant=assistant_config, client_timezone=client_timezone)
        self.assistant_id: int = assistant_config.id
        self.client_timezone: str = client_timezone
        self.model_id: str = assistant_config.model
        self.thread_id: str = thread_id or uuid.uuid4().hex
        self.instructions_factory: Callable[[], str] = assistant_config.build_system_prompt

        self.config: RunnableConfig = {"configurable": {"thread_id": self.thread_id}}

        # Initialize the Bedrock LLM with provided credentials or defaults.
        self.llm: ChatBedrockConverse = ChatBedrockConverse(model=self.model_id)

        # Create tools and conversation thread.
        self.tools: list[BaseTool] = self._create_tools()

        # Use ConversationBufferMemory as the agent's memory container.
        self.memory: PostgresSaver | MemorySaver = memory or MemorySaver()

        # Create the agent executor.
        self.agent: CompiledGraph = self._create_agent()

    @classmethod
    @contextmanager
    def from_postgres(
        cls,
        assistant_config: Assistant,
        client_timezone: str = "UTC",
        thread_id: str | None = None,
        postgres_url: str | None = None,
    ) -> Generator["BedrockAssistant", None, None]:
        with PostgresSaver.from_conn_string(postgres_url or os.environ["POSTGRES_URL"]) as memory:
            memory.setup()
            yield cls(assistant_config, client_timezone, thread_id, memory)

    def add_message(self, message: dict[str, str]) -> None:
        """
        Add a message to the conversation thread.

        Args:
            message (AssistantMessage): A dictionary containing the message with keys "role" and "content".
        """
        log.debug("Adding message to BedrockAssistant", message=message)
        _ = self.agent.update_state(self.config, {"messages": [message]})

    def _create_tools(self) -> list[BaseTool]:
        """
        Create and return a list of StructuredTool objects based on function definitions and schemas.

        Returns:
            list[BaseTool]: List of tools that the assistant can use.
        """

        # Helper inner classes for additional schema validation.
        class SetAppointmentTool(BaseModel):
            """
            Schema for setting an appointment.

            Attributes:
                request (SetAppointmentsRequest): The appointment request details.
            """

            request: SetAppointmentsRequest

        class GetProductListTool(BaseModel):
            """
            Schema for retrieving a list of products.
            """

            pass

        # Define the tools.
        tools: list[BaseTool] = [
            create_tool(
                name="check_availability",
                description="Check availability for a product at a location.",
                schema=CheckAvailabilityTool,
                func=lambda params: get_availability(
                    params["product_id"],
                    params["location_id"],
                    self.client_timezone,
                ),
            ),
            create_tool(
                name="get_product_locations",
                description="Get locations where a product is available.",
                schema=GetProductLocationsTool,
                func=lambda params: get_product_locations(params["product_id"]),
            ),
            create_tool(
                name="get_product_list",
                description="Get the list of available products.",
                schema=GetProductListTool,
                func=lambda _: get_product_list(self.assistant_id),
            ),
            create_tool(
                name="set_appointment",
                description="Set an appointment based on provided details.",
                schema=SetAppointmentTool,
                func=lambda params: set_appointment(
                    SetAppointmentsRequest.parse_json_to_request(params["request_json"])
                ),
            ),
            create_tool(
                name="get_product_photos",
                description="Get photos for a specific product.",
                schema=GetProductPhotosTool,
                func=lambda params: get_product_photos(params["product_id"]),
            ),
            create_tool(
                name="handoff_to_admin",
                description="Handoff the conversation to an admin.",
                schema=HandoffToAdminTool,
                func=lambda params: handoff_conversation_to_admin(
                    params["customer_email"],
                    self.thread_id,
                ),
            ),
        ]
        return tools

    def _create_agent(self):
        """
        Create the LangChain agent and its associated executor.

        This method pulls the prompt template from the hub and creates a structured chat agent
        using the provided LLM and tools. The executor is then built with conversation memory.
        """
        agent = create_react_agent(self.llm, self.tools, prompt=self.instructions_factory(), checkpointer=self.memory)
        return agent

    def retrieve_response(self, messages: list[BaseMessage]) -> str:
        """
        Retrieve a response from the agent based on the last user message.

        Instead of using .run(), the executor is invoked as a function to return a response dictionary,
        from which the expected output is extracted.

        Returns:
            str: The assistant's response.

        Raises:
            ValueError: If the returned response does not contain an 'output' key.
            TimeoutError: If the assistant takes too long to respond.
            Exception: If an error occurs during execution.
        """
        log.debug("Retrieving response from BedrockAssistant", messages=messages)
        if not messages:
            raise ValueError("No messages provided")

        response: dict[str, list[BaseMessage]] = self.agent.invoke({"messages": messages}, config=self.config)
        content = response["messages"][-1].content
        assert isinstance(content, str)
        return content


def create_tool(
    name: str,
    description: str,
    schema: type[BaseModel],
    func: Callable[..., Any],
) -> StructuredTool:
    """
    Helper function to create a StructuredTool from a function and its schema.

    Args:
        name (str): The name of the tool.
        description (str): A description of what the tool does.
        schema (type[BaseModel]): A Pydantic model representing the input schema.
        func (Callable[..., Any]): The function implementing the tool's behavior.

    Returns:
        StructuredTool: The constructed tool ready for integration with the agent.
    """
    return StructuredTool.from_function(
        name=name,
        description=description,
        func=func,
        args_schema=schema,
    )

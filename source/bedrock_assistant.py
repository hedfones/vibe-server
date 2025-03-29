from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Callable

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
        """
        log.debug("Initializing BedrockAssistant", assistant=assistant_config, client_timezone=client_timezone)
        self.assistant_id: int = assistant_config.id
        self.client_timezone: str = client_timezone
        self.model_id: str = assistant_config.model
        self.thread_id: str = thread_id or uuid.uuid4().hex
        self.instructions_factory: Callable[[], str] = assistant_config.build_system_prompt
        self.config: Assistant = assistant_config

        self.agent_config: RunnableConfig = {"configurable": {"thread_id": self.thread_id}}

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
        log.debug("Adding message to BedrockAssistant", message=message)
        _ = self.agent.update_state(self.agent_config, {"messages": [message]})

    def _create_tools(self) -> list[BaseTool]:
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

        tools: list[BaseTool] = []

        if self.config.uses_function_check_availability:

            def tool_func(params: dict[str, int]) -> str:
                return get_availability(params["product_id"], params["location_id"], self.client_timezone)

            tool = StructuredTool.from_function(
                name="check_availability",
                description="Check availability for a product at a location.",
                schema=CheckAvailabilityTool,
                func=tool_func,
            )
            tools.append(tool)

        if self.config.uses_function_get_product_locations:

            def tool_func(params: dict[str, int]) -> str:
                return get_product_locations(params["product_id"])

            tool = StructuredTool.from_function(
                name="get_product_locations",
                description="Get locations where a product is available.",
                schema=GetProductLocationsTool,
                func=tool_func,
            )
            tools.append(tool)

        if self.config.uses_function_get_product_list:

            def tool_func(_: dict[str, int]) -> str:
                return get_product_list(self.assistant_id)

            tool = StructuredTool.from_function(
                name="get_product_list",
                description="Get the list of available products.",
                schema=GetProductListTool,
                func=tool_func,
            )
            tools.append(tool)

        if self.config.uses_function_set_appointment:

            def tool_func(params: dict[str, str]) -> str:
                return set_appointment(SetAppointmentsRequest.parse_json_to_request(params["request_json"]))

            tool = StructuredTool.from_function(
                name="set_appointment",
                description="Set an appointment based on provided details.",
                schema=SetAppointmentTool,
                func=tool_func,
            )
            tools.append(tool)

        if self.config.uses_function_get_product_photos:

            def tool_func(params: dict[str, int]) -> str:
                return get_product_photos(params["product_id"])

            tool = StructuredTool.from_function(
                name="get_product_photos",
                description="Get photos for a specific product.",
                schema=GetProductPhotosTool,
                func=tool_func,
            )
            tools.append(tool)

        if self.config.uses_handoff_to_admin:

            def tool_func(params: dict[str, str]) -> str:
                return handoff_conversation_to_admin(params["customer_email"], self.thread_id)

            tool = StructuredTool.from_function(
                name="handoff_to_admin",
                description="Handoff the conversation to an admin.",
                schema=HandoffToAdminTool,
                func=tool_func,
            )
            tools.append(tool)
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
        """
        log.debug("Retrieving response from BedrockAssistant", messages=messages)
        if not messages:
            raise ValueError("No messages provided")

        response: dict[str, list[BaseMessage]] = self.agent.invoke({"messages": messages}, config=self.agent_config)
        content = response["messages"][-1].content
        assert isinstance(content, str)
        return content

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

import structlog
from langchain import hub
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool
from langchain.tools.base import BaseTool
from langchain_aws.chat_models import ChatBedrock
from pydantic import BaseModel

# Import functions and models from our own modules
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


@dataclass
class AWSCredentials:
    """
    Data class for storing AWS credentials.
    """

    access_key_id: str
    secret_access_key: str
    region_name: str


class AssistantMessage(dict[str, Any]):
    """
    dictionary type for an assistant message.
    The keys are "role" (either "assistant" or "user") and "content".
    """


class Thread:
    """Represents a messaging thread."""

    def __init__(self, thread_id: str | None = None) -> None:
        log.debug("Initializing Thread", thread_id=thread_id)
        self._thread_id: str | None = thread_id
        self.messages: list[dict[str, Any]] = []

    @property
    def thread_id(self) -> str:
        """Return a unique thread ID. Generate one if it does not exist."""
        if not self._thread_id:
            from uuid import uuid4

            self._thread_id = str(uuid4())
            log.info("Created new thread", thread_id=self._thread_id)
        return self._thread_id

    def add_message(self, message: dict[str, str]) -> None:
        """Append a message to the thread."""
        log.info("Adding message to thread", thread_id=self.thread_id, message=message)
        self.messages.append(message)


class BedrockAssistant:
    """
    An assistant using AWS Bedrock within LangChain.
    """

    def __init__(
        self,
        credentials: AWSCredentials | None,
        assistant_id: str,
        client_timezone: str = "UTC",
        thread_id: str | None = None,
        model_id: str = "us.meta.llama3-3-70b-instruct-v1:0",
        instructions: str = "",
    ) -> None:
        log.debug("Initializing BedrockAssistant", assistant_id=assistant_id, client_timezone=client_timezone)
        self.assistant_id: str = assistant_id
        self.client_timezone: str = client_timezone
        self.instructions: str = instructions
        self.model_id: str = model_id

        # Initialize the Bedrock LLM with provided credentials or fall back on environment variables.
        if credentials is not None:
            self.llm = ChatBedrock(
                model=model_id,
                region=credentials.region_name,
                credentials_profile_name=None,
                aws_access_key_id=credentials.access_key_id,
                aws_secret_access_key=credentials.secret_access_key,
            )
        else:
            self.llm = ChatBedrock(model=model_id)

        # Create tools and conversation thread.
        self.tools: list[BaseTool] = self._create_tools()
        self.thread: Thread = Thread(thread_id)

        # Use ConversationBufferMemory as the agent’s memory.
        self.memory: ConversationBufferMemory = ConversationBufferMemory(memory_key="chat_history")

        # Create the agent executor.
        self._create_agent()

    def _create_tools(self) -> list[BaseTool]:
        """
        Create StructuredTools from our functions and schema definitions.
        """

        # Helper inner classes (if needed) for additional schema validation.
        class SetAppointmentTool(BaseModel):
            request: SetAppointmentsRequest

        class GetProductlistTool(BaseModel):
            pass

        # Define the tools. (Lambda functions capture self so that client_timezone etc. are available.)
        tools: list[BaseTool] = [
            create_tool(
                name="check_availability",
                description="Check availability for a product at a location",
                schema=CheckAvailabilityTool,
                func=lambda params: get_availability(
                    params["product_id"],
                    params["location_id"],
                    self.client_timezone,
                ),
            ),
            create_tool(
                name="get_product_locations",
                description="Get locations where a product is available",
                schema=GetProductLocationsTool,
                func=lambda params: get_product_locations(params["product_id"]),
            ),
            create_tool(
                name="get_product_list",
                description="Get the list of available products",
                schema=GetProductlistTool,
                func=lambda _: get_product_list(self.assistant_id),
            ),
            create_tool(
                name="set_appointment",
                description="Set an appointment based on provided details",
                schema=SetAppointmentTool,
                func=lambda params: set_appointment(
                    SetAppointmentsRequest.parse_json_to_request(params["request_json"])
                ),
            ),
            create_tool(
                name="get_product_photos",
                description="Get photos for a specific product",
                schema=GetProductPhotosTool,
                func=lambda params: get_product_photos(params["product_id"]),
            ),
            create_tool(
                name="handoff_to_admin",
                description="Handoff the conversation to an admin",
                schema=HandoffToAdminTool,
                func=lambda params: handoff_conversation_to_admin(
                    params["customer_email"],
                    self.thread.thread_id,
                ),
            ),
        ]
        return tools

    def _create_agent(self) -> None:
        """
        Create the LangChain agent and associated executor.
        """
        # Pull the prompt template from the hub.
        prompt: ChatPromptTemplate = hub.pull("anthonydresser/structured-chat-agent-llama")

        # Create a structured chat agent with the provided LLM and tools.
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )

        # Build the AgentExecutor using the agent, tools, and conversation memory.
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
        )

    def add_message(self, message: dict[str, str]) -> None:
        """
        Add a message to the thread and update agent memory.
        """
        log.info("Adding message to BedrockAssistant", message=message)
        self.thread.add_message(message)
        # Update the conversation memory (using the "chat_memory" interface).
        if message["role"] == "user":
            self.memory.chat_memory.add_user_message(message["content"])
        else:
            self.memory.chat_memory.add_ai_message(message["content"])

    def retrieve_response(self) -> str:
        """
        Get a response from the agent based on the last user message.
        Uses a timeout to avoid waiting indefinitely.

        Returns:
            The AI’s response as a string.

        Raises:
            TimeoutError: If a response is not returned in time.
            Exception: If the agent run call errors.
        """
        log.debug("Retrieving response from BedrockAssistant")
        # Get the last user message.
        user_messages = [m for m in self.thread.messages if m.get("role") == "user"]
        if not user_messages:
            return "No user messages to respond to."

        last_user_message = user_messages[-1]["content"]
        timeout = datetime.now() + timedelta(seconds=30)

        while datetime.now() < timeout:
            try:
                # In LangChain 0.3, we call .run() on the executor.
                message_text = self.agent_executor.run(last_user_message)
                # Add the assistant’s response to the conversation.
                self.thread.add_message({"role": "assistant", "content": message_text})
                return message_text
            except Exception as e:
                log.error("Error retrieving response", error=str(e))
                raise e

        raise TimeoutError("Assistant took too long to respond.")

    def update_assistant(self, instructions: str, name: str, model: str, tools: list[dict[str, Any]]) -> None:
        """
        Update the assistant’s properties and rebuild the underlying components.

        Args:
            instructions: New instructions for the assistant.
            name: New name (currently not directly used by the agent).
            model: Model identifier (maps to a Bedrock model).
            tools: list of tool definitions.
        """
        log.debug("Updating assistant", instructions=instructions, name=name, model=model, tools=tools)
        self.instructions = instructions
        self.model_id = model

        # Reinitialize the LLM – preserving credentials if present.
        if hasattr(self, "llm"):
            if hasattr(self.llm, "aws_access_key_id") and hasattr(self.llm, "aws_secret_access_key"):
                self.llm = ChatBedrock(
                    model=self.model_id,
                    region=getattr(self.llm, "region", None),
                    credentials_profile_name=None,
                    aws_access_key_id=self.llm.aws_access_key_id,
                    aws_secret_access_key=self.llm.aws_secret_access_key,
                )
            else:
                self.llm = ChatBedrock(model=self.model_id)

        # Note: tools can be updated externally by replacing self.tools if desired.
        # Rebuild the agent with the updated components.
        self._create_agent()


def create_tool(
    name: str,
    description: str,
    schema: type[BaseModel],
    func: Callable[..., Any],
) -> StructuredTool:
    """
    Helper function to create a StructuredTool from the given function and schema.

    Args:
        name: Tool name.
        description: Tool description.
        schema: Pydantic BaseModel subclass describing the input schema.
        func: Function to invoke for this tool.

    Returns:
        A StructuredTool instance.
    """
    return StructuredTool.from_function(
        name=name,
        description=description,
        func=func,
        args_schema=schema,
    )

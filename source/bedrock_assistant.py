from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Literal, Optional, TypedDict

import structlog
from langchain import hub
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool
from langchain.tools.base import BaseTool
from langchain_aws.chat_models import ChatBedrock
from pydantic import BaseModel

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
    """Data class for storing AWS credentials."""

    access_key_id: str
    secret_access_key: str
    region_name: str


class AssistantMessage(TypedDict):
    """TypedDict for Assistant messages indicating role and content."""

    role: Literal["assistant", "user"]
    content: str


class Thread:
    """Class representing a messaging thread."""

    def __init__(self, thread_id: Optional[str] = None) -> None:
        """
        Initializes a Thread instance.

        Args:
            thread_id: Optional thread identifier.
        """
        log.debug("Initializing Thread", thread_id=thread_id)
        self._thread_id: Optional[str] = thread_id
        self.messages: List[Dict[str, Any]] = []

    @property
    def thread_id(self) -> str:
        """
        Retrieves the current thread ID. If no thread ID exists, a new ID is generated.

        Returns:
            A string representing the thread ID.
        """
        log.debug("Getting thread_id")
        if not self._thread_id:
            from uuid import uuid4

            log.info("Creating new thread as thread_id is None")
            self._thread_id = str(uuid4())
        return self._thread_id

    def add_message(self, message: AssistantMessage) -> None:
        """
        Adds a message to the current thread.

        Args:
            message: A dictionary containing role and content of the message.
        """
        log.info("Adding message", message=message, thread_id=self.thread_id)
        self.messages.append(message)


class BedrockAssistant:
    """Class representing an Assistant that interacts with AWS Bedrock."""

    def __init__(
        self,
        credentials: Optional[AWSCredentials],
        assistant_id: str,
        client_timezone: str = "UTC",
        thread_id: Optional[str] = None,
        model_id: str = "us.meta.llama3-3-70b-instruct-v1:0",
        instructions: str = "",
    ) -> None:
        """
        Initializes a BedrockAssistant instance.

        Args:
            credentials: Optional AWSCredentials instance containing AWS access details.
                        If None, credentials will be loaded from environment variables.
            assistant_id: An identifier for the assistant.
            client_timezone: Timezone of the client using this Assistant.
            thread_id: Optional thread identifier to be used by the Assistant.
            model_id: AWS Bedrock model ID to use
            instructions: System instructions for the assistant
        """
        log.debug("Initializing BedrockAssistant", assistant_id=assistant_id, client_timezone=client_timezone)
        self.assistant_id: str = assistant_id
        self.client_timezone: str = client_timezone
        self.instructions: str = instructions

        self.model_id: str = model_id

        # Initialize Bedrock LLM
        self.llm: ChatBedrock
        if credentials is not None:
            # Use provided credentials
            self.llm = ChatBedrock(
                model=model_id,
                region=credentials.region_name,
                credentials_profile_name=None,
                aws_access_key_id=credentials.access_key_id,
                aws_secret_access_key=credentials.secret_access_key,
            )
        else:
            # Use environment variables for credentials
            self.llm = ChatBedrock(model=model_id)

        # Setup agent tools
        self.tools = self._create_tools()

        # Setup thread
        self.thread: Thread = Thread(thread_id)

        # Setup memory - using the newer approach to avoid deprecation warnings

        # Create a memory that will store messages in the agent's chat history
        self.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

        # Create the agent
        self._create_agent()

    def _create_tools(self) -> List[BaseTool]:
        """Create the function tools for the agent.

        Returns:
            A list of LangChain tool objects.
        """

        class SetAppointmentTool(BaseModel):
            """Set an appointment based on provided details."""

            request: SetAppointmentsRequest

        class GetProductListTool(BaseModel):
            """Get the list of available products."""

            pass

        # Create the actual tools
        tools = [
            # Check availability tool
            create_tool(
                name="check_availability",
                description="Check availability for a product at a location",
                schema=CheckAvailabilityTool,
                func=lambda params: get_availability(params["product_id"], params["location_id"], self.client_timezone),
            ),
            # Get product locations tool
            create_tool(
                name="get_product_locations",
                description="Get locations where a product is available",
                schema=GetProductLocationsTool,
                func=lambda params: get_product_locations(params["product_id"]),
            ),
            # Get product list tool
            create_tool(
                name="get_product_list",
                description="Get the list of available products",
                schema=GetProductListTool,
                func=lambda _: get_product_list(self.assistant_id),
            ),
            # Set appointment tool
            create_tool(
                name="set_appointment",
                description="Set an appointment based on provided details",
                schema=SetAppointmentTool,
                func=lambda params: set_appointment(
                    SetAppointmentsRequest.parse_json_to_request(params["request_json"])
                ),
            ),
            # Get product photos tool
            create_tool(
                name="get_product_photos",
                description="Get photos for a specific product",
                schema=GetProductPhotosTool,
                func=lambda params: get_product_photos(params["product_id"]),
            ),
            # Handoff to admin tool
            create_tool(
                name="handoff_to_admin",
                description="Handoff the conversation to an admin",
                schema=HandoffToAdminTool,
                func=lambda params: handoff_conversation_to_admin(params["customer_email"], self.thread.thread_id),
            ),
        ]

        return tools

    def _create_agent(self) -> None:
        """Create the LangChain agent with the defined tools."""
        prompt: ChatPromptTemplate = hub.pull("anthonydresser/structured-chat-agent-llama")

        # Create the agent
        agent = create_structured_chat_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        # Create the agent executor
        self.agent_executor: AgentExecutor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
        )

    def add_message(self, message: AssistantMessage) -> None:
        """
        Adds a message to the Assistant's thread.

        Args:
            message: A dictionary containing role and content of the message.
        """
        log.info("Adding message to BedrockAssistant", message=message)
        self.thread.add_message(message)

        # Update the memory
        if message["role"] == "user":
            self.memory.chat_memory.add_user_message(message["content"])
        else:
            self.memory.chat_memory.add_ai_message(message["content"])
        return

    def retrieve_response(self) -> str:
        """
        Retrieves a response from the agent based on the conversation history.

        Returns:
            A string containing the retrieved message text.

        Raises:
            TimeoutError: If the assistant takes too long to respond.
        """
        log.debug("Retrieving response from BedrockAssistant")

        # Get the last user message (if any)
        user_messages = [m for m in self.thread.messages if m["role"] == "user"]
        if not user_messages:
            return "No user messages to respond to."

        last_user_message = user_messages[-1]["content"]

        # Invoke the agent
        timeout_timestamp = datetime.now() + timedelta(seconds=30)
        try:
            while datetime.now() < timeout_timestamp:
                response = self.agent_executor.invoke({"input": last_user_message})
                message_text = response["output"]

                # Add the AI response to the thread messages
                self.thread.add_message({"role": "assistant", "content": message_text})

                return message_text

            raise TimeoutError("Assistant took too long to respond.")
        except Exception as e:
            log.error("Error retrieving response", error=str(e))
            raise e

    def update_assistant(self, instructions: str, name: str, model: str, tools: List[Dict[str, Any]]) -> None:
        """
        Updates the assistant with new instructions, name, model, and tools.

        Args:
            instructions: String containing instructions for the assistant.
            name: Name of the assistant.
            model: The model to be used by the assistant.
            tools: A list of tool definitions.
        """
        log.debug("Updating assistant instructions", instructions=instructions, name=name, model=model, tools=tools)

        # Update relevant properties
        self.instructions = instructions

        # Update the model ID if needed - map from OpenAI model names to Bedrock models
        self.model_id = model

        # Recreate the LLM with the new model
        if hasattr(self, "llm"):
            # If we have existing credentials, use them
            if hasattr(self.llm, "aws_access_key_id") and hasattr(self.llm, "aws_secret_access_key"):
                self.llm = ChatBedrock(
                    model=self.model_id,
                    region=getattr(self.llm, "region", None),
                    credentials_profile_name=None,
                    aws_access_key_id=self.llm.aws_access_key_id,
                    aws_secret_access_key=self.llm.aws_secret_access_key,
                )
            else:
                # Otherwise rely on environment variables
                self.llm = ChatBedrock(
                    model=self.model_id,
                )

        # Re-create the agent with updated components
        self._create_agent()


def create_tool(name: str, description: str, schema: type[BaseModel], func: Callable[..., Any]) -> BaseTool:
    """Helper function to create a LangChain tool from schema and function.

    Args:
        name: Name of the tool
        description: Description of the tool
        schema: Pydantic schema for the tool inputs
        func: Function to execute when tool is called

    Returns:
        A LangChain tool
    """

    return StructuredTool.from_function(
        name=name,
        description=description,
        func=func,
        args_schema=schema,
    )

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, TypedDict

import structlog
from openai import OpenAI
from openai.types.beta import threads
from openai.types.beta.function_tool_param import FunctionToolParam
from openai.types.beta.threads import Run
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput
from openai.types.shared_params.function_definition import FunctionDefinition

from .functions import get_availability, get_product_list, get_product_locations, get_product_photos, set_appointment
from .model import CheckAvailabilityRequest, GetProductLocationsRequest, GetProductPhotosRequest, SetAppointmentsRequest

log = structlog.stdlib.get_logger()


@dataclass
class OpenAICredentials:
    """Data class for storing OpenAI credentials."""

    api_key: str
    organization: str
    project: str


class AssistantMessage(TypedDict):
    """TypedDict for Assistant messages indicating role and content."""

    role: Literal["assistant", "user"]
    content: str


class Thread:
    """Class representing a messaging thread with OpenAI API."""

    def __init__(self, client: OpenAI, thread_id: str | None = None) -> None:
        """
        Initializes a Thread instance.

        Args:
            client: An instance of OpenAI client.
            thread_id: Optional thread identifier.
        """
        log.debug("Initializing Thread", thread_id=thread_id)
        self._thread_id: str | None = thread_id
        self.client: OpenAI = client

    @property
    def thread_id(self) -> str:
        """
        Retrieves the current thread ID. If no thread ID exists, a new thread is created.

        Returns:
            A string representing the thread ID.
        """
        log.debug("Getting thread_id")
        if not self._thread_id:
            log.info("Creating new thread as thread_id is None")
            self._thread_id = self.client.beta.threads.create().id
        return self._thread_id

    def add_message(self, message: AssistantMessage) -> None:
        """
        Adds a message to the current thread.

        Args:
            message: A dictionary containing role and content of the message.
        """
        log.info("Adding message", message=message, thread_id=self.thread_id)
        _ = self.client.beta.threads.messages.create(thread_id=self.thread_id, **message)


class Assistant:
    """Class representing an Assistant that interacts with OpenAI API."""

    def __init__(
        self,
        credentials: OpenAICredentials,
        assistant_id: str,
        client_timezone: str = "UTC",
        thread_id: str | None = None,
    ) -> None:
        """
        Initializes an Assistant instance.

        Args:
            credentials: OpenAICredentials instance containing API key and info.
            assistant_id: An identifier for the assistant.
            client_timezone: Timezone of the client using this Assistant.
            thread_id: Optional thread identifier to be used by the Assistant.
        """
        log.debug("Initializing Assistant", assistant_id=assistant_id, client_timezone=client_timezone)
        self.assistant_id: str = assistant_id
        self.client_timezone: str = client_timezone

        self.client: OpenAI = OpenAI(
            api_key=credentials.api_key,
            organization=credentials.organization,
            project=credentials.project,
        )

        self.thread: Thread = Thread(self.client, thread_id)

    def add_message(self, message: AssistantMessage) -> None:
        """
        Adds a message to the Assistant's thread.

        Args:
            message: A dictionary containing role and content of the message.
        """
        log.info("Adding message to Assistants", message=message)
        self.thread.add_message(message)
        return

    def get_tool_outputs(self, run: Run) -> list[ToolOutput]:
        """
        Retrieves tool outputs required by a run.

        Args:
            run: A Run object representing a specific operation or session.

        Returns:
            A list of ToolOutput instances containing outputs from tools.
        """
        log.debug("Getting tool outputs", run=run)
        tool_outputs: list[ToolOutput] = []

        if run.required_action is None:
            log.warning("No required action detected for run.")
            return tool_outputs

        for tool in run.required_action.submit_tool_outputs.tool_calls:
            log.info(f"Running tool {tool.function.name} with arguments {tool.function.arguments}")
            function_name = tool.function.name
            arguments: dict[str, int | str | list[str]] = {}
            if argument_string := tool.function.arguments:
                arguments = json.loads(argument_string)

            tool_log = log.bind(function_name=function_name, arguments=arguments)

            if tool.function.name == "check_availability":
                tool_log.debug("Processing check_availability")
                request = CheckAvailabilityRequest.model_validate(arguments)
                availability = get_availability(request.product_id, request.location_id, self.client_timezone)
                body = "\n".join(map(str, availability))
            elif tool.function.name == "get_product_locations":
                tool_log.debug("Processing get_product_locations")
                request = GetProductLocationsRequest.model_validate(arguments)
                body = get_product_locations(request.product_id)
            elif tool.function.name == "get_product_list":
                tool_log.debug("Processing get_product_list")
                body = get_product_list(self.assistant_id)
            elif tool.function.name == "set_appointment":
                tool_log.debug("Processing set_appointment")
                request = SetAppointmentsRequest.parse_json_to_request(argument_string)
                body = set_appointment(request)
            elif tool.function.name == "get_product_photos":
                tool_log.debug("Processing get_product_photos")
                request = GetProductPhotosRequest.model_validate(arguments)
                body = get_product_photos(request.product_id)
            else:
                tool_log.error("Unexpected tool function called")
                raise Exception("Unexpected tool function called: {}".format(tool.function.name))

            tool_outputs.append({"tool_call_id": tool.id, "output": body})

        log.debug("Completed tool calls", tool_outputs=tool_outputs)
        return tool_outputs

    def retrieve_response(self, run: Run | None = None) -> str:
        """
        Retrieves a response based on the current or specified run.

        Args:
            run: Optional Run object. If None, a new run is created and polled.

        Returns:
            A string containing the retrieved message text.

        Raises:
            TimeoutError: If the assistant takes too long to respond.
        """
        log.debug("Retrieving response for run", run=run)
        if not run:
            log.info("Creating and polling new run as no run is provided")
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread.thread_id,
                assistant_id=self.assistant_id,
                tool_choice="required",
            )

        timeout_timestamp = datetime.now() + timedelta(seconds=30)
        while datetime.now() < timeout_timestamp:
            if run.status == "completed":
                log.info("Run completed, retrieving messages")
                messages = self.client.beta.threads.messages.list(thread_id=self.thread.thread_id)

                message = messages.data[0]
                message_content = message.content[0]
                assert isinstance(
                    message_content, threads.text_content_block.TextContentBlock
                ), f"Expected a TextContentBlock, but received: {type(message_content)}"

                message_text = message_content.text.value
                return message_text
            elif run.status == "requires_action":
                log.info("Run requires action, getting tool outputs")
                tool_outputs = self.get_tool_outputs(run)
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=self.thread.thread_id, run_id=run.id, tool_outputs=tool_outputs
                )
            elif run.status == "failed":
                log.error("Assistant run failed", status=run.status)
                raise Exception(f"Assistant run failed with status: {run.status}")
            else:
                log.warning(f"{run.status=}")
            time.sleep(0.25)
        raise TimeoutError("Assistant took too long to respond.")

    def update_assistant(self, instructions: str, name: str, model: str, tools: list[FunctionDefinition]) -> None:
        """
        Updates the assistant with new instructions, name, model, and tools.

        Args:
            instructions: String containing instructions for the assistant.
            name: Name of the assistant.
            model: The model to be used by the assistant.
            tools: A list of FunctionDefinition instances defining available tools.
        """
        log.debug("Updating assistant instructions", instructions=instructions, name=name, model=model, tools=tools)
        tool_params: list[FunctionToolParam] = []
        for definition in tools:
            tool_param: FunctionToolParam = {"type": "function", "function": definition}
            tool_params.append(tool_param)
        _ = self.client.beta.assistants.update(
            self.assistant_id, instructions=instructions, name=name, tools=tool_params, model=model
        )

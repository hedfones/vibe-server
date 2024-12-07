import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, TypedDict

from openai import OpenAI
from openai.types.beta import assistant, thread, threads
from openai.types.beta.threads import Run
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput

from .functions import (
    get_availability,
    get_product_list,
    get_product_locations,
    set_appointment,
)
from .logger import logger
from .model import (
    CheckAvailabilityRequest,
    GetProductLocationsRequest,
    SetAppointmentsRequest,
)


@dataclass
class OpenAICredentials:
    api_key: str
    organization: str
    project: str


class AssistantMessage(TypedDict):
    role: Literal["assistant", "user", "system"]
    content: str


class Assistant:
    def __init__(
        self,
        credentials: OpenAICredentials,
        assistant_id: str,
        thread_id: str | None = None,
    ) -> None:
        """
        Initializes the Assistant class.

        Args:
            credentials (OpenAICredentials): The credentials for OpenAI API.
            assistant_id (str): The ID of the assistant to be used.
            thread_id (str | None): The ID of the thread to retrieve or create a new one if None.
        """
        self.assistant_id: str = assistant_id

        self.client: OpenAI = OpenAI(
            api_key=credentials.api_key,
            organization=credentials.organization,
            project=credentials.project,
        )
        self.assistant: assistant.Assistant = self.client.beta.assistants.retrieve(assistant_id)

        self.thread: thread.Thread
        if thread_id:
            self.thread = self.client.beta.threads.retrieve(thread_id)
        else:
            self.thread = self.client.beta.threads.create()

    @property
    def thread_id(self) -> str:
        """
        Returns the ID of the current thread.

        Returns:
            str: The ID of the thread.
        """
        return self.thread.id

    def add_message(self, message: AssistantMessage) -> None:
        """
        Adds a message to the thread.

        Args:
            message (AssistantMessage): The message to be added.
        """
        _ = self.client.beta.threads.messages.create(thread_id=self.thread.id, **message)
        return

    def get_tool_outputs(self, run: Run) -> list[ToolOutput]:
        # Define the list to store tool outputs
        tool_outputs: list[ToolOutput] = []

        if run.required_action is None:
            logger.warning("No required action detected for run.")
            return tool_outputs

        # Loop through each tool in the required action section
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            logger.info(f"Running tool {tool.function.name} with arguments {tool.function.arguments}")
            arguments: dict[str, int | str | list[str]] = {}
            if argument_string := tool.function.arguments:
                arguments = json.loads(argument_string)

            if tool.function.name == "check_availability":
                request = CheckAvailabilityRequest.model_validate(arguments)
                availability = get_availability(request.product_id, request.location_id)
                body = "\n".join(map(str, availability))
            elif tool.function.name == "get_product_locations":
                request = GetProductLocationsRequest.model_validate(arguments)
                body = get_product_locations(request.product_id)
            elif tool.function.name == "get_product_list":
                body = get_product_list(self.assistant_id)
            elif tool.function.name == "set_appointment":
                request = SetAppointmentsRequest.parse_json_to_request(argument_string)
                body = set_appointment(request)
            else:
                raise Exception("Unexpected tool function called: {}".format(tool.function.name))

            tool_outputs.append({"tool_call_id": tool.id, "output": body})

        return tool_outputs

    def retrieve_response(self, run: Run | None = None) -> str:
        """
        Retrieves the response from the assistant.

        Returns:
            str: The content of the assistant's response.

        Raises:
            TimeoutError: If the assistant takes too long to respond.
        """
        if not run:
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                tool_choice="required",
            )

        timeout_timestamp = datetime.now() + timedelta(seconds=30)
        while datetime.now() < timeout_timestamp:
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)

                message = messages.data[0]
                message_content = message.content[0]
                assert isinstance(
                    message_content, threads.text_content_block.TextContentBlock
                ), f"Expected a TextContentBlock, but received: {type(message_content)}"

                message_text = message_content.text.value
                return message_text
            elif run.status == "requires_action":
                tool_outputs = self.get_tool_outputs(run)
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=self.thread.id, run_id=run.id, tool_outputs=tool_outputs
                )
            elif run.status == "failed":
                raise Exception(f"Assistant run failed with status: {run.status}")
            else:
                logger.warning(f"{run.status=}")
            time.sleep(0.25)
        raise TimeoutError("Assistant took too long to respond.")

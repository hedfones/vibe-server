import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import List, Literal, TypedDict

from openai import OpenAI
from openai.types.beta.threads import Run

from .database_utils import get_availability


@dataclass
class OpenAICredentials:
    api_key: str
    organization: str
    project: str


class AssistantMessage(TypedDict):
    role: Literal["assistant", "user"]
    content: str


class ToolOutput(TypedDict):
    tool_output_id: str
    output: str


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
        self.client = OpenAI(**asdict(credentials))
        self.assistant = self.client.beta.assistants.retrieve(assistant_id)

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
        self.client.beta.threads.messages.create(thread_id=self.thread.id, **message)

    def get_tool_outputs(self, run: Run) -> List[ToolOutput]:
        # Define the list to store tool outputs
        tool_outputs = []

        if run.required_action is None:
            logging.warning("No required action detected for run.")
            return tool_outputs

        # Loop through each tool in the required action section
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "check_availability":
                arguments = json.loads(tool.function.arguments)
                availability = get_availability(**arguments)
                body = "\n".join(map(str, availability))
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
                thread_id=self.thread.id, assistant_id=self.assistant.id
            )

        timeout_timestamp = datetime.now() + timedelta(seconds=15)
        while datetime.now() < timeout_timestamp:
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread.id
                )
                message = messages.data[0]
                message_content = message.content[0].text.value
                return message_content
            elif run.status == "requires_action":
                tool_outputs = self.get_tool_outputs(run)
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=self.thread.id, run_id=run.id, tool_outputs=tool_outputs
                )
                return self.retrieve_response(run)
            else:
                print(run.status)
            time.sleep(1)
        raise TimeoutError("Assistant took too long to respond.")

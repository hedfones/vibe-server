import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, TypedDict

from openai import OpenAI
from openai.types.beta import threads
from openai.types.beta.function_tool_param import FunctionToolParam
from openai.types.beta.threads import Run
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput
from openai.types.shared_params.function_definition import FunctionDefinition

from .functions import (
    get_availability,
    get_product_list,
    get_product_locations,
    get_product_photos,
    set_appointment,
)
from .logger import logger
from .model import (
    CheckAvailabilityRequest,
    GetProductLocationsRequest,
    GetProductPhotosRequest,
    SetAppointmentsRequest,
)


@dataclass
class OpenAICredentials:
    api_key: str
    organization: str
    project: str


class AssistantMessage(TypedDict):
    role: Literal["assistant", "user"]
    content: str


class Thread:
    def __init__(self, client: OpenAI, thread_id: str | None = None) -> None:
        logger.debug("Initializing Thread with thread_id: %s", thread_id)
        self._thread_id: str | None = thread_id
        self.client: OpenAI = client

    @property
    def thread_id(self) -> str:
        logger.debug("Getting thread_id")
        if not self._thread_id:
            logger.info("Creating new thread as thread_id is None")
            self._thread_id = self.client.beta.threads.create().id
        return self._thread_id

    def add_message(self, message: AssistantMessage) -> None:
        logger.info("Adding message: %s to thread_id: %s", message, self.thread_id)
        _ = self.client.beta.threads.messages.create(thread_id=self.thread_id, **message)


class Assistant:
    def __init__(
        self,
        credentials: OpenAICredentials,
        assistant_id: str,
        client_timezone: str = "UTC",
        thread_id: str | None = None,
    ) -> None:
        logger.debug("Initializing Assistant with assistant_id: %s", assistant_id)
        self.assistant_id: str = assistant_id
        self.client_timezone: str = client_timezone

        self.client: OpenAI = OpenAI(
            api_key=credentials.api_key,
            organization=credentials.organization,
            project=credentials.project,
        )

        self.thread: Thread = Thread(self.client, thread_id)

    def add_message(self, message: AssistantMessage) -> None:
        logger.info("Adding message to Assistant: %s", message)
        self.thread.add_message(message)
        return

    def get_tool_outputs(self, run: Run) -> list[ToolOutput]:
        logger.debug("Getting tool outputs for run: %s", run)
        tool_outputs: list[ToolOutput] = []

        if run.required_action is None:
            logger.warning("No required action detected for run.")
            return tool_outputs

        for tool in run.required_action.submit_tool_outputs.tool_calls:
            logger.info(f"Running tool {tool.function.name} with arguments {tool.function.arguments}")
            arguments: dict[str, int | str | list[str]] = {}
            if argument_string := tool.function.arguments:
                arguments = json.loads(argument_string)

            if tool.function.name == "check_availability":
                logger.debug("Processing check_availability with arguments: %s", arguments)
                request = CheckAvailabilityRequest.model_validate(arguments)
                availability = get_availability(request.product_id, request.location_id, self.client_timezone)
                body = "\n".join(map(str, availability))
            elif tool.function.name == "get_product_locations":
                logger.debug("Processing get_product_locations with arguments: %s", arguments)
                request = GetProductLocationsRequest.model_validate(arguments)
                body = get_product_locations(request.product_id)
            elif tool.function.name == "get_product_list":
                logger.debug("Processing get_product_list")
                body = get_product_list(self.assistant_id)
            elif tool.function.name == "set_appointment":
                logger.debug("Processing set_appointment with arguments: %s", argument_string)
                request = SetAppointmentsRequest.parse_json_to_request(argument_string)
                body = set_appointment(request)
            elif tool.function.name == "get_product_photos":
                logger.debug("Processing get_product_photos with arguments: %s", arguments)
                request = GetProductPhotosRequest.model_validate(arguments)
                body = get_product_photos(request.product_id)
            else:
                logger.error("Unexpected tool function called: %s", tool.function.name)
                raise Exception("Unexpected tool function called: {}".format(tool.function.name))

            tool_outputs.append({"tool_call_id": tool.id, "output": body})

        logger.debug(f"Tool outputs: `{tool_outputs}`")
        return tool_outputs

    def retrieve_response(self, run: Run | None = None) -> str:
        logger.debug("Retrieving response for run: %s", run)
        if not run:
            logger.info("Creating and polling new run as no run is provided")
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread.thread_id,
                assistant_id=self.assistant_id,
                tool_choice="required",
            )

        timeout_timestamp = datetime.now() + timedelta(seconds=30)
        while datetime.now() < timeout_timestamp:
            if run.status == "completed":
                logger.info("Run completed, retrieving messages")
                messages = self.client.beta.threads.messages.list(thread_id=self.thread.thread_id)

                message = messages.data[0]
                message_content = message.content[0]
                assert isinstance(
                    message_content, threads.text_content_block.TextContentBlock
                ), f"Expected a TextContentBlock, but received: {type(message_content)}"

                message_text = message_content.text.value
                return message_text
            elif run.status == "requires_action":
                logger.info("Run requires action, getting tool outputs")
                tool_outputs = self.get_tool_outputs(run)
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=self.thread.thread_id, run_id=run.id, tool_outputs=tool_outputs
                )
            elif run.status == "failed":
                logger.error("Run failed with status: %s", run.status)
                raise Exception(f"Assistant run failed with status: {run.status}")
            else:
                logger.warning(f"{run.status=}")
            time.sleep(0.25)
        raise TimeoutError("Assistant took too long to respond.")

    def update_assistant(self, instructions: str, name: str, model: str, tools: list[FunctionDefinition]) -> None:
        logger.debug(
            "Updating assistant with instructions: %s, name: %s, model: %s, tools: %s", instructions, name, model, tools
        )
        tool_params: list[FunctionToolParam] = []
        for definition in tools:
            tool_param: FunctionToolParam = {"type": "function", "function": definition}
            tool_params.append(tool_param)
        _ = self.client.beta.assistants.update(
            self.assistant_id, instructions=instructions, name=name, tools=tool_params, model=model
        )

from unittest.mock import MagicMock, patch

import pytest

from source.assistant import Assistant, AssistantMessage, OpenAICredentials


@pytest.fixture
def mock_openai_client():
    with patch("source.assistant.OpenAI") as mock:
        yield mock


@pytest.fixture
def assistant_credentials():
    return OpenAICredentials(
        api_key="test_api_key", organization="test_org", project="test_project"
    )


@pytest.fixture
def assistant_instance(mock_openai_client, assistant_credentials):
    mock_thread = MagicMock()
    mock_thread.id = "test_thread_id"

    mock_assistant = MagicMock()
    mock_assistant.id = "test_assistant_id"

    mock_openai_client.return_value.beta.assistants.retrieve.return_value = (
        mock_assistant
    )
    mock_openai_client.return_value.beta.threads.create.return_value = mock_thread
    mock_openai_client.return_value.beta.threads.retrieve.return_value = mock_thread

    return Assistant(
        credentials=assistant_credentials,
        assistant_id="test_assistant_id",
        thread_id=None,
    )


def test_initialization_creates_thread(assistant_instance):
    assert assistant_instance.thread_id == "test_thread_id"


def test_thread_retrieval(
    assistant_instance, mock_openai_client, assistant_credentials
):
    assistant_instance_with_thread = Assistant(
        credentials=assistant_credentials,
        assistant_id="test_assistant_id",
        thread_id="existing_thread_id",
    )
    assert assistant_instance_with_thread.thread_id == "test_thread_id"
    mock_openai_client.return_value.beta.threads.retrieve.assert_called_with(
        "existing_thread_id"
    )


def test_add_message(assistant_instance):
    message = AssistantMessage(role="user", content="Hello Assistant!")
    assistant_instance.add_message(message)

    assistant_instance.client.beta.threads.messages.create.assert_called_with(
        thread_id="test_thread_id", role="user", content="Hello Assistant!"
    )


def test_retrieve_response_success(assistant_instance):
    # Mocking the run status to be completed
    mock_run = MagicMock()
    mock_run.status = "completed"
    assistant_instance.client.beta.threads.runs.create_and_poll.return_value = mock_run

    mock_message = MagicMock()
    mock_message.content = [
        MagicMock(text=MagicMock(value="Hello user!"))
    ]  # Matching the expected structure
    assistant_instance.client.beta.threads.messages.list.return_value.data = [
        mock_message
    ]

    response = assistant_instance.retrieve_response()

    assert response == "Hello user!"
    assistant_instance.client.beta.threads.runs.create_and_poll.assert_called_with(
        thread_id=assistant_instance.thread_id, assistant_id="test_assistant_id"
    )


def test_retrieve_response_timeout(assistant_instance):
    # Mocking a run that never completes
    mock_run = MagicMock()
    mock_run.status = "running"
    assistant_instance.client.beta.threads.runs.create_and_poll.return_value = mock_run

    with pytest.raises(TimeoutError):
        assistant_instance.retrieve_response()

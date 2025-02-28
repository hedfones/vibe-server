from unittest.mock import MagicMock, patch

import pytest

from source.bedrock_assistant import BedrockAssistant


@pytest.fixture
def mock_bedrock_llm():
    """Mock for the ChatBedrock LLM."""
    # Create a mock for ChatBedrock with model parameter
    mock_llm = MagicMock()
    with patch("source.bedrock_assistant.ChatBedrock", return_value=mock_llm) as mock_class:
        yield mock_class


@pytest.fixture
def mock_agent_executor():
    """Mock for the LangChain AgentExecutor."""
    with patch("source.bedrock_assistant.AgentExecutor") as mock:
        mock_executor = MagicMock()
        mock.return_value = mock_executor
        yield mock_executor


def test_bedrock_assistant_initialization(mock_bedrock_llm):
    """Test initialization of BedrockAssistant class."""
    assistant = BedrockAssistant(
        credentials=None,
        assistant_id="test-assistant-id",
        client_timezone="America/New_York",
        instructions="Test instructions",
    )

    assert assistant.assistant_id == "test-assistant-id"
    assert assistant.client_timezone == "America/New_York"
    assert assistant.instructions == "Test instructions"
    assert assistant.model_id == "us.meta.llama3-3-70b-instruct-v1:0"
    assert mock_bedrock_llm.called


def test_add_message(mock_bedrock_llm):
    """Test adding a message to the assistant."""
    assistant = BedrockAssistant(
        credentials=None,
        assistant_id="test-assistant-id",
    )

    # Add a user message
    assistant.add_message({"role": "user", "content": "Hello!"})

    # Check that the message was added to the thread
    assert len(assistant.thread.messages) == 1
    assert assistant.thread.messages[0]["role"] == "user"
    assert assistant.thread.messages[0]["content"] == "Hello!"

    # Check that the message was added to the memory
    assert "Hello!" in str(assistant.memory.chat_memory.messages)


@patch("source.bedrock_assistant.create_structured_chat_agent")
@patch("source.bedrock_assistant.BedrockAssistant._create_tools")
@patch("source.bedrock_assistant.BedrockAssistant._create_agent")
def test_retrieve_response(mock_create_agent, mock_create_tools, mock_agent, mock_bedrock_llm):
    """Test retrieving a response from the assistant."""
    assistant = BedrockAssistant(
        credentials=None,
        assistant_id="test-assistant-id",
    )

    # Set up the agent executor mock to return a response
    assistant.agent_executor = MagicMock()
    assistant.agent_executor.invoke.return_value = {"output": "Hello, I'm the assistant!"}

    # Add a user message
    assistant.add_message({"role": "user", "content": "Hello!"})

    # Get a response
    response = assistant.retrieve_response()

    # Check that the agent was invoked with the right message
    assistant.agent_executor.invoke.assert_called_once()
    assert "Hello!" in str(assistant.agent_executor.invoke.call_args)

    # Check that the right response was returned
    assert response == "Hello, I'm the assistant!"

    # Check that the assistant's message was added to the thread
    assert len(assistant.thread.messages) == 2
    assert assistant.thread.messages[1]["role"] == "assistant"
    assert assistant.thread.messages[1]["content"] == "Hello, I'm the assistant!"

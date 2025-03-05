from unittest.mock import MagicMock, call, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

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


def test_multiple_messages(mock_bedrock_llm):
    """Test adding multiple messages to the assistant and checking memory preservation."""
    assistant = BedrockAssistant(
        credentials=None,
        assistant_id="test-assistant-id",
    )

    # Patch the agent_executor to avoid making LLM calls
    assistant.agent_executor = MagicMock()
    assistant.agent_executor.invoke.return_value = {"output": "I'm the assistant!"}

    # Add several messages in a conversation flow
    messages = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help?"},
        {"role": "user", "content": "Tell me about yourself"},
        {"role": "assistant", "content": "I'm an AI assistant built with LangChain and AWS Bedrock"},
    ]

    # Add each message
    for message in messages:
        assistant.add_message(message)

    # Check that the thread contains all messages in order
    assert len(assistant.thread.messages) == 4
    for i, message in enumerate(messages):
        assert assistant.thread.messages[i]["role"] == message["role"]
        assert assistant.thread.messages[i]["content"] == message["content"]

    # Check the memory has the correct messages
    memory_messages = assistant.memory.chat_memory.messages
    assert len(memory_messages) == 4

    # Verify types are correct in memory
    assert isinstance(memory_messages[0], HumanMessage)
    assert isinstance(memory_messages[1], AIMessage)
    assert isinstance(memory_messages[2], HumanMessage)
    assert isinstance(memory_messages[3], AIMessage)

    # Verify content is correct
    assert memory_messages[0].content == "Hello!"
    assert memory_messages[1].content == "Hi there! How can I help?"
    assert memory_messages[2].content == "Tell me about yourself"
    assert memory_messages[3].content == "I'm an AI assistant built with LangChain and AWS Bedrock"


@patch("source.bedrock_assistant.hub.pull")
@patch("source.bedrock_assistant.AgentExecutor")
def test_agent_creation(mock_agent_executor, mock_hub_pull, mock_bedrock_llm):
    """Test the agent creation process with prompt template."""
    # Set up the mock prompt template and agent executor
    mock_prompt_template = MagicMock()
    mock_hub_pull.return_value = mock_prompt_template
    mock_agent_executor.return_value = MagicMock()

    # Mock the create_structured_chat_agent to return a properly mocked agent
    with patch("source.bedrock_assistant.create_structured_chat_agent") as mock_create_agent:
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        # Create the assistant
        assistant = BedrockAssistant(
            credentials=None, assistant_id="test-assistant-id", instructions="Follow these instructions carefully"
        )

        # Check that the hub was used to pull the prompt
        mock_hub_pull.assert_called_once_with("anthonydresser/structured-chat-agent-llama")

        # Check that create_structured_chat_agent was called with correct parameters
        mock_create_agent.assert_called_once()
        call_args = mock_create_agent.call_args
        assert call_args[1]["llm"] == assistant.llm
        assert call_args[1]["tools"] == assistant.tools
        assert call_args[1]["prompt"] == mock_prompt_template


@patch("source.bedrock_assistant.AgentExecutor")
def test_memory_in_agent_executor(mock_agent_executor, mock_bedrock_llm):
    """Test that memory is correctly passed to the agent executor."""
    mock_executor = MagicMock()
    mock_agent_executor.return_value = mock_executor

    with patch("source.bedrock_assistant.create_structured_chat_agent", return_value=MagicMock()):
        # Create assistant
        assistant = BedrockAssistant(
            credentials=None,
            assistant_id="test-assistant-id",
        )

        # Check that AgentExecutor was created with memory
        mock_agent_executor.assert_called_once()
        kwargs = mock_agent_executor.call_args[1]
        assert "memory" in kwargs
        assert kwargs["memory"] == assistant.memory


def test_update_assistant(mock_bedrock_llm):
    """Test updating assistant configuration."""
    assistant = BedrockAssistant(
        credentials=None,
        assistant_id="test-assistant-id",
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    )

    # Original values

    # Mock _create_agent to avoid side effects
    with patch.object(assistant, "_create_agent") as mock_create_agent:
        # Update the assistant
        new_instructions = "These are new instructions for the assistant"
        new_name = "New Assistant Name"
        new_model = "anthropic.claude-3-opus-20240229-v1:0"

        assistant.update_assistant(instructions=new_instructions, name=new_name, model=new_model, tools=[])

        # Check that values were updated
        assert assistant.instructions == new_instructions
        assert assistant.model_id == new_model

        # Check that _create_agent was called to rebuild the agent
        mock_create_agent.assert_called_once()


def test_conversation_continuity(mock_bedrock_llm):
    """Test that conversation continues properly with memory retention."""
    # Create assistant with mocked executor and memory
    assistant = BedrockAssistant(
        credentials=None,
        assistant_id="test-assistant-id",
    )

    # Override memory to a mock for better testing
    assistant.memory = MagicMock()
    assistant.memory.load_memory_variables.return_value = {"chat_history": []}

    # Mock agent_executor.invoke to return different responses on each call
    assistant.agent_executor = MagicMock()
    assistant.agent_executor.invoke.side_effect = [
        {"output": "First response"},
        {"output": "Second response that references the first question"},
        {"output": "Third response with context from previous interactions"},
    ]

    # First interaction
    assistant.add_message({"role": "user", "content": "Hello, how are you?"})
    response1 = assistant.retrieve_response()

    # Second interaction
    assistant.add_message({"role": "user", "content": "What did I just ask you?"})
    response2 = assistant.retrieve_response()

    # Third interaction
    assistant.add_message({"role": "user", "content": "Summarize our conversation"})
    response3 = assistant.retrieve_response()

    # Verify responses
    assert response1 == "First response"
    assert response2 == "Second response that references the first question"
    assert response3 == "Third response with context from previous interactions"

    # Verify memory was used by checking the chat_memory.add_* methods were called correctly
    [
        call({"role": "user", "content": "Hello, how are you?"}),
        call({"role": "assistant", "content": "First response"}),
        call({"role": "user", "content": "What did I just ask you?"}),
        call({"role": "assistant", "content": "Second response that references the first question"}),
        call({"role": "user", "content": "Summarize our conversation"}),
        call({"role": "assistant", "content": "Third response with context from previous interactions"}),
    ]

    assert len(assistant.thread.messages) == 6
    # First three messages should be user1, assistant1, user2
    assert assistant.thread.messages[0]["role"] == "user"
    assert assistant.thread.messages[0]["content"] == "Hello, how are you?"
    assert assistant.thread.messages[1]["role"] == "assistant"
    assert assistant.thread.messages[1]["content"] == "First response"
    assert assistant.thread.messages[2]["role"] == "user"
    assert assistant.thread.messages[2]["content"] == "What did I just ask you?"

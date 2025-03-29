# test_bedrock_assistant.py

import pytest

# Import the class under test.
from source.bedrock_assistant import BedrockAssistant


# For our fake agent and messages, we create simple classes.
class FakeMessage:
    def __init__(self, content: str):
        self.content = content


# This fake agent “executor” will record its calls and return a dummy response.
class FakeAgent:
    def __init__(self):
        self.updated_state = None
        self.invoked_input = None

    def update_state(self, agent_config, payload):
        self.updated_state = (agent_config, payload)
        return None

    def invoke(self, inputs, config=None):
        self.invoked_input = (inputs, config)
        # The assistant.retrieve_response method will look for a list of messages
        # and take the content of the last message.
        return {"messages": [FakeMessage("Fake Response")]}


# A fake function to replace create_react_agent so that our BedrockAssistant uses our FakeAgent.
def fake_create_react_agent(llm, tools, prompt, checkpointer):
    return FakeAgent()


# A fake LLM (ChatBedrockConverse) so that the assistant doesn’t try to use a real AWS model.
class FakeChatBedrockConverse:
    def __init__(self, model: str):
        self.model = model


# We also need a fake configuration that looks like the “Assistant” configuration
# expected by BedrockAssistant. In our tests we simply define the necessary fields.
class FakeAssistantConfig:
    def __init__(self, use_all_functions: bool = False):
        self.id = 1
        self.model = "fake-model"
        self.build_system_prompt = lambda: "dummy prompt"
        # Booleans indicating available tools.
        self.uses_function_check_availability = use_all_functions
        self.uses_function_get_product_locations = use_all_functions
        self.uses_function_get_product_list = use_all_functions
        self.uses_function_set_appointment = use_all_functions
        self.uses_function_get_product_photos = use_all_functions
        self.uses_handoff_to_admin = use_all_functions


# Test that retrieve_response returns the fake agent response
# and that it raises a ValueError when no messages are provided.
def test_retrieve_response(monkeypatch):
    # Override the LLM and agent creation so that no external side effects occur.
    monkeypatch.setattr("source.bedrock_assistant.ChatBedrockConverse", FakeChatBedrockConverse)
    monkeypatch.setattr("source.bedrock_assistant.create_react_agent", fake_create_react_agent)

    fake_config = FakeAssistantConfig()
    assistant = BedrockAssistant(fake_config, client_timezone="UTC", thread_id="test-thread")

    # Calling retrieve_response with an empty list should raise a ValueError.
    with pytest.raises(ValueError):
        assistant.retrieve_response([])

    # Create a dummy message list.
    dummy_msg = FakeMessage("Test message")
    response = assistant.retrieve_response([dummy_msg])
    assert response == "Fake Response"


# Test that add_message correctly passes the message to the agent.
def test_add_message(monkeypatch):
    monkeypatch.setattr("source.bedrock_assistant.ChatBedrockConverse", FakeChatBedrockConverse)
    monkeypatch.setattr("source.bedrock_assistant.create_react_agent", fake_create_react_agent)

    fake_config = FakeAssistantConfig()
    assistant = BedrockAssistant(fake_config, client_timezone="UTC", thread_id="test-thread")
    message = {"role": "user", "content": "Hello"}
    assistant.add_message(message)

    # The FakeAgent records calls to update_state.
    assert assistant.agent.updated_state is not None
    agent_config, payload = assistant.agent.updated_state
    assert "messages" in payload
    assert payload["messages"] == [message]


# Test that when the configuration has no functions enabled the created tools list is empty.
def test_create_tools_no_functions(monkeypatch):
    monkeypatch.setattr("source.bedrock_assistant.ChatBedrockConverse", FakeChatBedrockConverse)
    monkeypatch.setattr("source.bedrock_assistant.create_react_agent", fake_create_react_agent)

    fake_config = FakeAssistantConfig(use_all_functions=False)
    assistant = BedrockAssistant(fake_config)
    # When no functions are enabled, no tool should be created.
    assert assistant.tools == []


# Test that all tools are created when the configuration flags are set.
def test_create_tools_with_functions(monkeypatch):
    monkeypatch.setattr("source.bedrock_assistant.ChatBedrockConverse", FakeChatBedrockConverse)
    monkeypatch.setattr("source.bedrock_assistant.create_react_agent", fake_create_react_agent)

    fake_config = FakeAssistantConfig(use_all_functions=True)
    assistant = BedrockAssistant(fake_config)
    # Based on the implementation, six tools should be added:
    #   check_availability, get_product_locations, get_product_list,
    #   set_appointment, get_product_photos, and handoff_to_admin.
    assert len(assistant.tools) == 6

class FakeLLMClient:
    """Scripted replacement for LocalLLMClient used by deterministic tests."""

    def __init__(self, scripted_responses: list[dict]):
        self.scripted_responses = list(scripted_responses)
        self.calls = []

    def chat(self, messages, tools, temperature: float = 0.2) -> dict:
        self.calls.append({"messages": messages, "tools": tools, "temperature": temperature})
        if not self.scripted_responses:
            raise AssertionError("FakeLLMClient received more chat calls than scripted responses")
        return self.scripted_responses.pop(0)


def response(*, content: str = "", tool_calls: list[dict] | None = None) -> dict:
    message = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}]}


def tool_call(name: str, arguments: str, call_id: str | None = None) -> dict:
    return {
        "id": call_id or f"call-{name}",
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }

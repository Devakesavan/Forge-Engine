from harness.transcript import MAX_TOOL_RESULT_CHARS, Transcript


def test_long_tool_result_is_truncated_when_stored():
    transcript = Transcript("task")
    transcript.append_tool("call-1", "x" * (MAX_TOOL_RESULT_CHARS + 10), turn=1)

    stored = transcript.messages[-1]["content"]

    assert len(stored) < MAX_TOOL_RESULT_CHARS + 50
    assert "[truncated 10 characters]" in stored


def test_old_tool_results_are_compacted_but_recent_results_remain_full():
    transcript = Transcript("task", recent_tool_turns=2)
    for turn in range(1, 6):
        transcript.append_tool(f"call-{turn}", f"full-result-{turn}", turn=turn)

    transcript.compact(current_turn=6)

    tool_messages = [message for message in transcript.messages if message["role"] == "tool"]
    contents = [message["content"] for message in tool_messages]

    assert contents[:3] == ["[older tool result compacted to save context]"] * 3
    assert contents[3:] == ["full-result-4", "full-result-5"]


def test_compaction_never_touches_system_or_user_messages():
    transcript = Transcript("original task", recent_tool_turns=1)
    transcript.append_user("user follow-up")
    transcript.append_tool("call-1", "old result", turn=1)

    transcript.compact(current_turn=4)

    assert transcript.messages[0]["role"] == "system"
    assert "coding agent" in transcript.messages[0]["content"]
    assert transcript.messages[1] == {"role": "user", "content": "original task"}
    assert transcript.messages[2] == {"role": "user", "content": "user follow-up"}
    assert transcript.messages[3]["content"] == "[older tool result compacted to save context]"

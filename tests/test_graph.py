import pytest
from app.graph import TutorState, SYSTEM


class TestTutorState:
    def test_tutor_state_has_required_keys(self):
        assert "messages" in TutorState.__annotations__
        assert "context" in TutorState.__annotations__


class TestSystemPrompt:
    def test_system_prompt_is_string(self):
        assert isinstance(SYSTEM, str)

    def test_system_prompt_mentions_tutor(self):
        assert "tutor" in SYSTEM.lower()

    def test_system_prompt_mentions_transcript(self):
        assert "transcript" in SYSTEM.lower()

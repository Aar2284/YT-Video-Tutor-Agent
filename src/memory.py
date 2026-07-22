from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp_cited: str = ""


@dataclass
class ConversationMemory:
    turns: list[ConversationTurn] = field(default_factory=list)
    max_turns: int = 10

    def add_user_message(self, message: str) -> None:
        self.turns.append(ConversationTurn(role="user", content=message))
        self._trim()

    def add_assistant_message(self, message: str, timestamp_cited: str = "") -> None:
        self.turns.append(
            ConversationTurn(
                role="assistant", content=message, timestamp_cited=timestamp_cited
            )
        )
        self._trim()

    def get_history(self) -> list[dict]:
        return [{"role": t.role, "content": t.content} for t in self.turns]

    def get_last_n(self, n: int) -> list[ConversationTurn]:
        return self.turns[-n:]

    def clear(self) -> None:
        self.turns.clear()

    def _trim(self) -> None:
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]

    @property
    def is_empty(self) -> bool:
        return len(self.turns) == 0

    @property
    def turn_count(self) -> int:
        return len(self.turns)

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: tuple[ChatMessage, ...]
    response_format: Mapping[str, Any] | None = None
    temperature: float | None = None
    options: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "options", dict(self.options))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class ChatResponse:
    content: str
    usage: Any | None = None
    raw: Any | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))


class ChatClient(Protocol):
    def complete(self, request: ChatRequest) -> ChatResponse:
        pass

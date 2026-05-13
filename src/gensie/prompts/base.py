from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec
from gensie.runtime.chat import ChatMessage


@dataclass(frozen=True)
class PromptBundle:
    system: str
    user: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def messages(self) -> tuple[ChatMessage, ChatMessage]:
        return (
            ChatMessage(role="system", content=self.system),
            ChatMessage(role="user", content=self.user),
        )


class PromptBuilder(Protocol):
    def build(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> PromptBundle:
        pass

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from gensie.runtime.chat import ChatClient, ChatMessage, ChatRequest, ChatResponse


class OpenAIChatClient(ChatClient):
    def __init__(self, client: Any | None = None):
        self.client = client or OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
        )

    def complete(self, request: ChatRequest) -> ChatResponse:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": [_message_dict(message) for message in request.messages],
        }
        if request.response_format is not None:
            kwargs["response_format"] = request.response_format
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        return ChatResponse(
            content=content,
            usage=getattr(response, "usage", None),
            raw=response,
        )


def _message_dict(message: ChatMessage) -> dict[str, str]:
    return {"role": message.role, "content": message.content}

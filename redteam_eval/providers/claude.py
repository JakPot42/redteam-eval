from __future__ import annotations
import time
from typing import Optional

import anthropic

from .base import BaseProvider, ProviderResponse


class ClaudeProvider(BaseProvider):
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        api_key: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = (
            anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        )

    @property
    def model_id(self) -> str:
        return self._model

    @property
    def client(self):
        return self._client

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> ProviderResponse:
        start = time.perf_counter()
        kwargs: dict = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            msg = self._client.messages.create(**kwargs)
        except Exception:
            raise

        latency_ms = int((time.perf_counter() - start) * 1000)
        return ProviderResponse(
            text=msg.content[0].text,
            tokens_used=msg.usage.input_tokens + msg.usage.output_tokens,
            latency_ms=latency_ms,
        )

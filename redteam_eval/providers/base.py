from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResponse:
    text: str
    tokens_used: int
    latency_ms: int


class BaseProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system_prompt: str | None = None) -> ProviderResponse:
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        ...

"""Transcription provider abstraction.

To add a new provider:
1. Create a module in this package (e.g., groq.py)
2. Implement a class with a `transcribe` method matching the Provider protocol
3. Register it in PROVIDERS below
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class Provider(Protocol):
    """Interface that all transcription providers implement."""

    def transcribe(
        self,
        wav_bytes: bytes,
        api_key: str,
        model: str = "",
        language: str = "",
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """Transcribe WAV audio and return the full text.

        Args:
            wav_bytes: Raw WAV file bytes.
            api_key: API key for the provider.
            model: Model identifier (provider-specific).
            language: ISO 639-1 language code, or empty for auto-detect.
            on_chunk: Optional callback invoked with each text delta as it arrives.

        Returns:
            The complete transcribed text.
        """
        ...


PROVIDERS: dict[str, type] = {}


def _load_providers() -> None:
    from .openai import OpenAIProvider
    PROVIDERS["openai"] = OpenAIProvider


def get_provider(name: str) -> Provider:
    """Get a provider instance by name."""
    if not PROVIDERS:
        _load_providers()
    if name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS.keys()))
        raise ValueError(f"Unknown provider: {name!r}. Available: {available}")
    return PROVIDERS[name]()

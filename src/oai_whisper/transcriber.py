"""OpenAI API client with streaming via httpx."""

import json
from collections.abc import Callable

import httpx

from .constants import DEFAULT_MODEL, OPENAI_API_BASE


def transcribe(
    wav_bytes: bytes,
    api_key: str,
    model: str = DEFAULT_MODEL,
    language: str = "",
    on_chunk: Callable[[str], None] | None = None,
) -> str:
    """Send WAV audio to OpenAI transcription API with streaming, return full text.

    If on_chunk is provided, it's called with each text delta as it arrives.
    """
    url = f"{OPENAI_API_BASE}/audio/transcriptions"

    files = {
        "file": ("audio.wav", wav_bytes, "audio/wav"),
    }
    data = {
        "model": model,
        "response_format": "text",
        "stream": "true",
    }
    if language:
        data["language"] = language

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    text_parts = []

    with httpx.Client(timeout=30.0) as client:
        with client.stream(
            "POST",
            url,
            headers=headers,
            files=files,
            data=data,
        ) as response:
            response.raise_for_status()

            # Handle SSE streaming response
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:]  # strip "data: " prefix
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                    delta = event.get("text", "")
                    if delta:
                        text_parts.append(delta)
                        if on_chunk:
                            on_chunk(delta)
                except json.JSONDecodeError:
                    continue

    return "".join(text_parts)

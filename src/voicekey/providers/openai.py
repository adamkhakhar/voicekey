"""OpenAI transcription provider (gpt-4o-mini-transcribe, gpt-4o-transcribe)."""

import json
from collections.abc import Callable

import httpx

from ..constants import DEFAULT_MODEL, OPENAI_API_BASE


class OpenAIProvider:
    """Transcription via OpenAI's /audio/transcriptions endpoint with SSE streaming."""

    def transcribe(
        self,
        wav_bytes: bytes,
        api_key: str,
        model: str = DEFAULT_MODEL,
        language: str = "",
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
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

                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:]
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

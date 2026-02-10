"""Tests for OpenAI transcription provider."""

import json
from unittest.mock import MagicMock

import httpx
import pytest

from voicekey.providers.openai import OpenAIProvider
from voicekey.constants import DEFAULT_MODEL, OPENAI_API_BASE


def _make_sse_response(chunks: list[str], done: bool = True) -> list[str]:
    """Build SSE lines from text chunks."""
    lines = []
    for chunk in chunks:
        event = {"text": chunk}
        lines.append(f"data: {json.dumps(event)}")
    if done:
        lines.append("data: [DONE]")
    return lines


class FakeStreamResponse:
    """Fake httpx streaming response."""

    def __init__(self, lines: list[str], status_code: int = 200):
        self._lines = lines
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=MagicMock(), response=MagicMock(status_code=self.status_code)
            )

    def iter_lines(self):
        yield from self._lines

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeClient:
    """Fake httpx.Client that returns a FakeStreamResponse."""

    def __init__(self, response: FakeStreamResponse):
        self._response = response
        self.last_call = {}

    def stream(self, method, url, **kwargs):
        self.last_call = {"method": method, "url": url, **kwargs}
        return self._response

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_transcribe_returns_full_text(monkeypatch):
    """transcribe() assembles all streamed chunks into final text."""
    lines = _make_sse_response(["Hello ", "world!"])
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    result = provider.transcribe(b"fakewav", "sk-test")
    assert result == "Hello world!"


def test_transcribe_calls_on_chunk(monkeypatch):
    """transcribe() calls on_chunk callback for each text delta."""
    lines = _make_sse_response(["one ", "two ", "three"])
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    chunks = []
    provider.transcribe(b"fakewav", "sk-test", on_chunk=chunks.append)
    assert chunks == ["one ", "two ", "three"]


def test_transcribe_sends_correct_request(monkeypatch):
    """transcribe() sends POST with correct params."""
    lines = _make_sse_response(["hi"])
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    provider.transcribe(b"audiobytes", "sk-mykey", model="gpt-4o-transcribe", language="en")

    call = fake_client.last_call
    assert call["method"] == "POST"
    assert call["url"] == f"{OPENAI_API_BASE}/audio/transcriptions"
    assert call["headers"]["Authorization"] == "Bearer sk-mykey"
    assert call["data"]["model"] == "gpt-4o-transcribe"
    assert call["data"]["language"] == "en"
    assert call["data"]["stream"] == "true"


def test_transcribe_default_model(monkeypatch):
    """transcribe() uses DEFAULT_MODEL when model not specified."""
    lines = _make_sse_response(["ok"])
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    provider.transcribe(b"wav", "sk-test")
    assert fake_client.last_call["data"]["model"] == DEFAULT_MODEL


def test_transcribe_omits_language_when_empty(monkeypatch):
    """transcribe() doesn't send language param when empty string."""
    lines = _make_sse_response(["ok"])
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    provider.transcribe(b"wav", "sk-test", language="")
    assert "language" not in fake_client.last_call["data"]


def test_transcribe_handles_empty_events(monkeypatch):
    """transcribe() skips events without text field."""
    lines = [
        "data: {}",
        'data: {"text": ""}',
        'data: {"text": "valid"}',
        "data: [DONE]",
    ]
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    result = provider.transcribe(b"wav", "sk-test")
    assert result == "valid"


def test_transcribe_handles_non_data_lines(monkeypatch):
    """transcribe() ignores non-data SSE lines (comments, empty, event types)."""
    lines = [
        ": comment",
        "",
        "event: transcript",
        'data: {"text": "hello"}',
        "data: [DONE]",
    ]
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    result = provider.transcribe(b"wav", "sk-test")
    assert result == "hello"


def test_transcribe_handles_malformed_json(monkeypatch):
    """transcribe() skips malformed JSON data lines."""
    lines = [
        "data: not-json",
        'data: {"text": "ok"}',
        "data: [DONE]",
    ]
    fake_client = FakeClient(FakeStreamResponse(lines))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    result = provider.transcribe(b"wav", "sk-test")
    assert result == "ok"


def test_transcribe_raises_on_http_error(monkeypatch):
    """transcribe() raises on non-200 status."""
    fake_client = FakeClient(FakeStreamResponse([], status_code=401))
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake_client)

    provider = OpenAIProvider()
    with pytest.raises(httpx.HTTPStatusError):
        provider.transcribe(b"wav", "sk-bad")

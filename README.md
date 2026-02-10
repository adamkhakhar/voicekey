# oai-whisper

macOS CLI voice dictation tool. Hold Option, speak, release — text appears at your cursor.

Uses OpenAI's `gpt-4o-mini-transcribe` model for fast, accurate transcription.

## Prerequisites

- macOS 13+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- PortAudio: `brew install portaudio`

## Install

```bash
uv sync
```

## Setup

```bash
uv run oai-whisper setup
```

This will:
1. Prompt for your OpenAI API key (stored in macOS Keychain)
2. Check Accessibility and Microphone permissions

## Usage

```bash
uv run oai-whisper
```

Hold the **Option** key to start recording. Release to transcribe and paste at your cursor.

A red dot appears in the top-right corner while recording. A microphone icon sits in your menu bar.

## Config

Config lives at `~/.config/oai-whisper/config.toml`.

```bash
# View all settings
uv run oai-whisper config

# Change model
uv run oai-whisper config model gpt-4o-transcribe

# Set language (ISO 639-1)
uv run oai-whisper config language en

# Use only left Option key
uv run oai-whisper config hotkey left_option
```

## Permissions

- **Accessibility**: Required for hotkey detection and text insertion. System Settings → Privacy & Security → Accessibility.
- **Microphone**: Required for audio recording. Permission dialog appears on first use.

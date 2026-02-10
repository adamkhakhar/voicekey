# oai-whisper

**Voice dictation for macOS — powered by your own OpenAI API key.**

Hold Option, speak, release. Transcribed text appears at your cursor in any app.

<br>

## Why this exists

Tools like [Wispr Flow](https://wispr.flow) provide excellent voice dictation, but many companies — including OpenAI itself — restrict third-party services that process audio. If your company's security policy blocks Wispr Flow or similar tools, **oai-whisper** gives you the same workflow using OpenAI's transcription API directly. Your audio goes straight to OpenAI's API with your own key. No intermediary service, no data retention concerns, no IT approval needed.

<br>

## How it works

```
Hold Option → 🎙 Recording → Release Option → 📝 Transcribe → ✅ Paste at cursor
```

1. **Hold the Option key** — a red dot appears on screen, audio recording begins
2. **Speak** — audio is captured locally at 24kHz mono
3. **Release the Option key** — audio is sent to OpenAI's API, transcribed text is typed at your cursor
4. **Clipboard is preserved** — your existing clipboard contents are saved and restored after paste

Uses `gpt-4o-mini-transcribe` by default (~$0.003/min, sub-second latency for typical dictation).

<br>

## Quickstart

### Prerequisites

- macOS 13+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- PortAudio: `brew install portaudio`

### Install & setup

```bash
git clone https://github.com/adamkhakhar/oai-whisper.git
cd oai-whisper
uv sync
uv run oai-whisper setup
```

The setup command will:
1. Prompt for your OpenAI API key (stored securely in macOS Keychain — never written to disk)
2. Check and guide you through granting Accessibility and Microphone permissions

### Run

```bash
uv run oai-whisper
```

A microphone icon appears in your menu bar. Hold **Option** to dictate.

<br>

## Permissions

oai-whisper requires two macOS permissions:

| Permission | Why | How to grant |
|---|---|---|
| **Accessibility** | Detect the Option hotkey globally and simulate Cmd+V to paste | System Settings → Privacy & Security → Accessibility → add your terminal app |
| **Microphone** | Record audio while the hotkey is held | Permission dialog appears automatically on first use |

`oai-whisper setup` will check both and open the relevant System Settings pane if needed.

<br>

## Configuration

Config is stored at `~/.config/oai-whisper/config.toml`.

```bash
# View current settings
uv run oai-whisper config

# Set transcription language (ISO 639-1 code, empty = auto-detect)
uv run oai-whisper config language en

# Use the higher-accuracy model (slower, ~$0.006/min)
uv run oai-whisper config model gpt-4o-transcribe

# Trigger only on left or right Option key
uv run oai-whisper config hotkey left_option
```

| Key | Default | Options |
|---|---|---|
| `model` | `gpt-4o-mini-transcribe` | `gpt-4o-mini-transcribe`, `gpt-4o-transcribe` |
| `hotkey` | `option` (either) | `option`, `left_option`, `right_option` |
| `language` | `""` (auto-detect) | Any [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) code |

<br>

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Main thread (NSApp run loop)                       │
│  ┌──────────┐  ┌─────────┐  ┌────────────────────┐ │
│  │ CGEvent  │→ │ rumps   │  │ Overlay (NSWindow) │ │
│  │ tap      │  │ menubar │  │ red dot indicator  │ │
│  └──────────┘  └─────────┘  └────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  Audio thread (sounddevice callback)                │
│  24kHz mono int16 PCM → WAV encoding                │
├─────────────────────────────────────────────────────┤
│  Transcription thread (per utterance)               │
│  httpx POST → OpenAI API (SSE stream) → paste       │
└─────────────────────────────────────────────────────┘

State machine: IDLE → RECORDING → TRANSCRIBING → INSERTING → IDLE
```

The 200ms debounce on the Option key prevents accidental triggers when typing special characters (e.g., Option+E for accent marks).

<br>

## Security & Privacy

- **API key** is stored in the macOS Keychain via the `keyring` library — never written to a file
- **Audio** is recorded locally and sent directly to the OpenAI API over HTTPS — no intermediary servers
- **No telemetry, no analytics, no data collection** — this is a local tool that talks only to `api.openai.com`
- **Clipboard** contents are saved before paste and restored immediately after — no data leakage

<br>

## Troubleshooting

**"Failed to create event tap"**
Your terminal app doesn't have Accessibility permission. Go to System Settings → Privacy & Security → Accessibility, add your terminal (Terminal.app, iTerm2, Warp, etc.), then restart oai-whisper.

**No audio captured**
Check that Microphone permission is granted for your terminal app in System Settings → Privacy & Security → Microphone.

**Text not appearing at cursor**
Make sure the target app accepts Cmd+V paste. Some apps with custom input handling may not respond to simulated keystrokes.

**PortAudio errors on install**
Run `brew install portaudio` before `uv sync`.

<br>

## License

MIT

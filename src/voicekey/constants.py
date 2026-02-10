"""Key codes, modifier flags, and audio settings."""

# macOS virtual key codes for Option keys
KEYCODE_LEFT_OPTION = 0x3A
KEYCODE_RIGHT_OPTION = 0x3D

# CGEvent modifier flags
FLAG_OPTION = 0x00080000  # kCGEventFlagMaskAlternate

# Virtual key code for 'V' (used for Cmd+V paste simulation)
KEYCODE_V = 0x09

# CGEvent modifier flag for Command key
FLAG_COMMAND = 0x00100000  # kCGEventFlagMaskCommand

# Hotkey debounce (seconds) — prevents accidental triggers from typing special chars
DEBOUNCE_SECONDS = 0.2

# Audio recording settings
SAMPLE_RATE = 24000  # 24kHz — matches OpenAI's preferred input
CHANNELS = 1         # Mono
DTYPE = "int16"      # 16-bit PCM

# OpenAI API
OPENAI_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_PROVIDER = "openai"

# Text insertion timing (seconds)
PASTE_DELAY = 0.05       # Delay before simulating Cmd+V
RESTORE_DELAY = 0.10     # Delay before restoring clipboard

# Keychain service name
KEYCHAIN_SERVICE = "voicekey"
KEYCHAIN_USERNAME = "api-key"

# Config file location
CONFIG_DIR = "~/.config/voicekey"
CONFIG_FILE = "config.toml"

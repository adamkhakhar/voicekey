"""Main orchestrator, state machine, threading."""

import enum
import sys
import threading

import click
import Quartz

from . import auth, config
from .hotkey import HotkeyListener
from .inserter import insert_text
from .recorder import Recorder
from .transcriber import transcribe


class State(enum.Enum):
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    INSERTING = "inserting"


class App:
    def __init__(self):
        self.state = State.IDLE
        self.cfg = config.load()
        self.api_key = auth.get_api_key()
        self.recorder = Recorder()
        self.overlay = None  # set after import
        self._lock = threading.Lock()

    def on_hotkey_press(self):
        """Called on main thread when Option held past debounce."""
        with self._lock:
            if self.state != State.IDLE:
                return
            self.state = State.RECORDING

        print("🎙  Recording...", flush=True)
        if self.overlay:
            self.overlay.show()
        self.recorder.start()

    def on_hotkey_release(self):
        """Called on main thread when Option released."""
        with self._lock:
            if self.state != State.RECORDING:
                return
            self.state = State.TRANSCRIBING

        wav_data = self.recorder.stop()
        if self.overlay:
            self.overlay.hide()

        if not wav_data:
            print("No audio captured.", flush=True)
            with self._lock:
                self.state = State.IDLE
            return

        print("📝  Transcribing...", flush=True)
        # Spawn transcription thread to avoid blocking the run loop
        t = threading.Thread(target=self._transcribe_and_insert, args=(wav_data,))
        t.daemon = True
        t.start()

    def _transcribe_and_insert(self, wav_data: bytes):
        try:
            text = transcribe(
                wav_data,
                self.api_key,
                model=self.cfg.get("model", "gpt-4o-mini-transcribe"),
                language=self.cfg.get("language", ""),
            )
            text = text.strip()
            if not text:
                print("(empty transcription)", flush=True)
                return

            print(f"✅  \"{text}\"", flush=True)

            with self._lock:
                self.state = State.INSERTING
            insert_text(text)

        except Exception as e:
            print(f"Error: {e}", flush=True)
        finally:
            with self._lock:
                self.state = State.IDLE


def run():
    """Launch the app with menu bar icon and hotkey listener."""
    api_key = auth.get_api_key()
    if not api_key:
        click.echo("No API key found. Run `oai-whisper setup` first.")
        sys.exit(1)

    app = App()

    # Import overlay (requires AppKit on main thread)
    from .overlay import Overlay
    app.overlay = Overlay()

    # Set up hotkey listener
    listener = HotkeyListener(
        on_press=app.on_hotkey_press,
        on_release=app.on_hotkey_release,
        hotkey=app.cfg.get("hotkey", "option"),
    )

    tap = listener.create_tap()
    if tap is None:
        click.echo("Failed to create event tap. Grant Accessibility permission:")
        click.echo("  System Settings → Privacy & Security → Accessibility")
        click.echo("  Add your terminal app and restart.")
        sys.exit(1)

    # Add tap to current run loop
    source = listener.get_run_loop_source()
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(),
        source,
        Quartz.kCFRunLoopCommonModes,
    )

    # Launch menu bar app (takes over the main thread run loop)
    from .menubar import create_menubar_app
    menubar = create_menubar_app(app)

    click.echo("oai-whisper running. Hold Option to dictate. Menu bar icon to quit.")
    menubar.run()

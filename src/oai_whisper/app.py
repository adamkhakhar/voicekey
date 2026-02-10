"""Main orchestrator, state machine, threading."""

import enum
import sys
import threading

import click
import Quartz

from . import auth, config
from .display import AudioMeter, StreamingDisplay, console, print_banner
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
        self._meter = AudioMeter()
        self._meter_updater: threading.Thread | None = None

    def on_hotkey_press(self):
        """Called on main thread when Option held past debounce."""
        with self._lock:
            if self.state != State.IDLE:
                return
            self.state = State.RECORDING

        self.recorder.start()
        if self.overlay:
            self.overlay.show()

        # Start audio meter display + level polling
        self._meter.start()
        self._meter_updater = threading.Thread(target=self._poll_levels, daemon=True)
        self._meter_updater.start()

    def _poll_levels(self):
        """Poll recorder RMS and feed it to the audio meter display."""
        import time
        while self.state == State.RECORDING:
            self._meter.update_level(self.recorder.rms)
            time.sleep(0.05)

    def on_hotkey_release(self):
        """Called on main thread when Option released."""
        with self._lock:
            if self.state != State.RECORDING:
                return
            self.state = State.TRANSCRIBING

        # Stop meter + recording
        self._meter.stop()
        wav_data = self.recorder.stop()
        if self.overlay:
            self.overlay.hide()

        if not wav_data:
            console.print("  [dim]No audio captured.[/]")
            with self._lock:
                self.state = State.IDLE
            return

        # Spawn transcription thread to avoid blocking the run loop
        t = threading.Thread(target=self._transcribe_and_insert, args=(wav_data,))
        t.daemon = True
        t.start()

    def _transcribe_and_insert(self, wav_data: bytes):
        stream_display = StreamingDisplay()
        try:
            stream_display.start()
            text = transcribe(
                wav_data,
                self.api_key,
                model=self.cfg.get("model", "gpt-4o-mini-transcribe"),
                language=self.cfg.get("language", ""),
                on_chunk=stream_display.append,
            )
            stream_display.finish()

            text = text.strip()
            if not text:
                console.print("  [dim](empty transcription)[/]")
                return

            with self._lock:
                self.state = State.INSERTING
            insert_text(text)

        except Exception as e:
            stream_display.finish()
            console.print(f"  [red]Error:[/] {e}")
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

    # Check permissions for banner display
    from . import permissions
    acc_ok = permissions.is_accessibility_trusted()
    mic_ok = permissions.check_microphone()

    # Show startup banner
    print_banner(app.cfg, accessibility=acc_ok, microphone=mic_ok)

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
        console.print(
            "\n  [red]✗[/] Failed to create event tap.\n"
            "  [dim]Grant Accessibility permission:[/]\n"
            "  System Settings → Privacy & Security → Accessibility\n"
            "  Add your terminal app and restart.\n"
        )
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

    console.print()
    menubar.run()

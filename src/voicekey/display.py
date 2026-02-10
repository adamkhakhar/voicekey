"""Rich terminal UI — startup banner, audio meter, streaming text."""

import sys
import threading
import time

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()

# ── Startup banner ──────────────────────────────────────────────────

def print_banner(cfg: dict, accessibility: bool, microphone: bool) -> None:
    hotkey_display = {
        "option": "⌥ Option (either)",
        "left_option": "⌥ Left Option",
        "right_option": "⌥ Right Option",
    }.get(cfg.get("hotkey", "option"), "⌥ Option")

    acc_status = "[green]✓ granted[/]" if accessibility else "[red]✗ not granted[/]"
    mic_status = "[green]✓ available[/]" if microphone else "[red]✗ unavailable[/]"

    lang = cfg.get("language", "") or "auto-detect"
    provider = cfg.get("provider", "openai")

    content = (
        f"  [dim]Provider[/]     {provider}\n"
        f"  [dim]Hotkey[/]       {hotkey_display}\n"
        f"  [dim]Model[/]        {cfg.get('model', 'gpt-4o-mini-transcribe')}\n"
        f"  [dim]Language[/]     {lang}\n"
        f"\n"
        f"  [dim]Accessibility[/] {acc_status}\n"
        f"  [dim]Microphone[/]    {mic_status}\n"
        f"\n"
        f"  [dim italic]Hold hotkey to dictate · Menu bar icon to quit[/]"
    )

    panel = Panel(
        content,
        title="[bold]voicekey[/]",
        title_align="left",
        border_style="blue",
        padding=(1, 1),
    )
    console.print(panel)


# ── Audio level meter ───────────────────────────────────────────────

BAR_CHARS = " ░▒▓█"
BAR_WIDTH = 28


class AudioMeter:
    """Live-updating audio level meter shown while recording."""

    def __init__(self):
        self._level: float = 0.0  # 0.0–1.0
        self._start_time: float = 0.0
        self._running = False
        self._live: Live | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._start_time = time.time()
        self._running = True
        self._level = 0.0
        self._thread = threading.Thread(target=self._run_display, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def update_level(self, rms: float) -> None:
        """Update with RMS level (0.0–1.0 normalized)."""
        self._level = min(1.0, rms)

    def _render(self) -> Text:
        elapsed = time.time() - self._start_time
        level = self._level

        # Build bar
        filled = int(level * BAR_WIDTH)
        bar = ""
        for i in range(BAR_WIDTH):
            if i < filled:
                if i < BAR_WIDTH * 0.6:
                    bar += f"[green]█[/]"
                elif i < BAR_WIDTH * 0.8:
                    bar += f"[yellow]█[/]"
                else:
                    bar += f"[red]█[/]"
            else:
                bar += f"[dim]░[/]"

        text = Text.from_markup(
            f"  [bold red]●[/] REC  {bar}  [dim]{elapsed:5.1f}s[/]"
        )
        return text

    def _run_display(self) -> None:
        with Live(self._render(), console=console, refresh_per_second=15, transient=True) as live:
            self._live = live
            while self._running:
                live.update(self._render())
                time.sleep(0.066)  # ~15fps
            self._live = None


# ── Streaming transcription display ─────────────────────────────────

class StreamingDisplay:
    """Shows transcribed text appearing progressively."""

    def __init__(self):
        self._text = ""
        self._live: Live | None = None
        self._done = False

    def start(self) -> None:
        self._text = ""
        self._done = False
        self._live = Live(
            self._render(),
            console=console,
            refresh_per_second=15,
            transient=True,
        )
        self._live.start()

    def append(self, chunk: str) -> None:
        self._text += chunk
        if self._live:
            self._live.update(self._render())

    def finish(self) -> None:
        if self._live:
            self._live.stop()
            self._live = None
        if self._text.strip():
            console.print(
                f"  [green]✓[/] [italic]{self._text.strip()}[/]"
            )

    def _render(self) -> Text:
        if not self._text:
            return Text.from_markup("  [dim]⠋ transcribing...[/]")
        return Text.from_markup(
            f"  [blue]⟩[/] [italic]{self._text}[/][dim]▍[/]"
        )

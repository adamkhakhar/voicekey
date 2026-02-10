"""Tests for display module (banner, audio meter, streaming display)."""

import time

from rich.text import Text

from voicekey.display import AudioMeter, StreamingDisplay, print_banner


class TestPrintBanner:
    """Tests for startup banner rendering."""

    def test_banner_does_not_crash(self, capsys):
        """print_banner renders without error for all hotkey configs."""
        for hotkey in ("option", "left_option", "right_option"):
            cfg = {"model": "gpt-4o-mini-transcribe", "hotkey": hotkey, "language": ""}
            print_banner(cfg, accessibility=True, microphone=True)

    def test_banner_shows_permissions_granted(self, capsys):
        """Banner shows granted status for permissions."""
        cfg = {"model": "gpt-4o-mini-transcribe", "hotkey": "option", "language": ""}
        print_banner(cfg, accessibility=True, microphone=True)
        output = capsys.readouterr().out
        assert "granted" in output
        assert "available" in output

    def test_banner_shows_permissions_denied(self, capsys):
        """Banner shows denied status for permissions."""
        cfg = {"model": "gpt-4o-mini-transcribe", "hotkey": "option", "language": ""}
        print_banner(cfg, accessibility=False, microphone=False)
        output = capsys.readouterr().out
        assert "not granted" in output
        assert "unavailable" in output

    def test_banner_shows_model(self, capsys):
        """Banner displays the configured model."""
        cfg = {"model": "gpt-4o-transcribe", "hotkey": "option", "language": ""}
        print_banner(cfg, accessibility=True, microphone=True)
        output = capsys.readouterr().out
        assert "gpt-4o-transcribe" in output

    def test_banner_auto_detect_language(self, capsys):
        """Banner shows 'auto-detect' when language is empty."""
        cfg = {"model": "gpt-4o-mini-transcribe", "hotkey": "option", "language": ""}
        print_banner(cfg, accessibility=True, microphone=True)
        output = capsys.readouterr().out
        assert "auto-detect" in output

    def test_banner_shows_set_language(self, capsys):
        """Banner shows language code when set."""
        cfg = {"model": "gpt-4o-mini-transcribe", "hotkey": "option", "language": "ja"}
        print_banner(cfg, accessibility=True, microphone=True)
        output = capsys.readouterr().out
        assert "ja" in output


class TestAudioMeter:
    """Tests for AudioMeter state management."""

    def test_initial_level_zero(self):
        meter = AudioMeter()
        assert meter._level == 0.0

    def test_update_level_clamps(self):
        meter = AudioMeter()
        meter.update_level(2.0)
        assert meter._level == 1.0

    def test_update_level_stores_value(self):
        meter = AudioMeter()
        meter.update_level(0.5)
        assert meter._level == 0.5

    def test_start_stop_lifecycle(self):
        """Meter can start and stop without error."""
        meter = AudioMeter()
        meter.start()
        time.sleep(0.1)
        meter.stop()
        assert meter._thread is None

    def test_render_contains_rec(self):
        """Rendered output contains REC indicator."""
        meter = AudioMeter()
        meter._start_time = time.time()
        rendered = meter._render()
        assert "REC" in rendered.plain


class TestStreamingDisplay:
    """Tests for StreamingDisplay state management."""

    def test_append_accumulates_text(self):
        sd = StreamingDisplay()
        sd._text = ""
        sd.append("hello ")
        sd.append("world")
        assert sd._text == "hello world"

    def test_render_empty_shows_transcribing(self):
        sd = StreamingDisplay()
        sd._text = ""
        rendered = sd._render()
        assert "transcribing" in rendered.plain

    def test_render_with_text_shows_content(self):
        sd = StreamingDisplay()
        sd._text = "hello world"
        rendered = sd._render()
        assert "hello world" in rendered.plain

    def test_finish_prints_result(self, capsys):
        """finish() prints the final text with checkmark."""
        sd = StreamingDisplay()
        sd._text = "test output"
        sd._live = None
        sd.finish()
        output = capsys.readouterr().out
        assert "test output" in output

    def test_finish_empty_no_output(self, capsys):
        """finish() prints nothing for empty/whitespace text."""
        sd = StreamingDisplay()
        sd._text = "   "
        sd._live = None
        sd.finish()
        output = capsys.readouterr().out
        assert output == ""

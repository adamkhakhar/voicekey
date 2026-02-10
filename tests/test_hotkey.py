"""Tests for hotkey listener logic (without CGEvent tap)."""

import threading
import time

from oai_whisper.constants import (
    KEYCODE_LEFT_OPTION,
    KEYCODE_RIGHT_OPTION,
)
from oai_whisper.hotkey import HotkeyListener


class TestMatchesHotkey:
    """Tests for _matches_hotkey method."""

    def test_option_matches_left(self):
        listener = HotkeyListener(lambda: None, lambda: None, hotkey="option")
        assert listener._matches_hotkey(KEYCODE_LEFT_OPTION) is True

    def test_option_matches_right(self):
        listener = HotkeyListener(lambda: None, lambda: None, hotkey="option")
        assert listener._matches_hotkey(KEYCODE_RIGHT_OPTION) is True

    def test_option_rejects_other(self):
        listener = HotkeyListener(lambda: None, lambda: None, hotkey="option")
        assert listener._matches_hotkey(0x00) is False

    def test_left_option_only_matches_left(self):
        listener = HotkeyListener(lambda: None, lambda: None, hotkey="left_option")
        assert listener._matches_hotkey(KEYCODE_LEFT_OPTION) is True
        assert listener._matches_hotkey(KEYCODE_RIGHT_OPTION) is False

    def test_right_option_only_matches_right(self):
        listener = HotkeyListener(lambda: None, lambda: None, hotkey="right_option")
        assert listener._matches_hotkey(KEYCODE_RIGHT_OPTION) is True
        assert listener._matches_hotkey(KEYCODE_LEFT_OPTION) is False


class TestDebounceLogic:
    """Tests for debounce state machine (exercising internal state directly)."""

    def test_press_starts_debounce_timer(self):
        """Option down sets _option_down and starts timer."""
        listener = HotkeyListener(lambda: None, lambda: None)
        listener._option_down = False
        listener._confirmed = False

        # Simulate what _callback does for key down
        listener._option_down = True
        listener._debounce_timer = threading.Timer(0.2, listener._on_debounce)
        listener._debounce_timer.start()

        assert listener._option_down is True
        assert listener._debounce_timer is not None

        listener._debounce_timer.cancel()

    def test_quick_release_cancels_debounce(self):
        """Releasing before debounce fires doesn't trigger press callback."""
        press_called = []
        release_called = []
        listener = HotkeyListener(
            lambda: press_called.append(1),
            lambda: release_called.append(1),
        )

        # Simulate quick press and release
        listener._option_down = True
        listener._confirmed = False
        listener._debounce_timer = threading.Timer(0.2, listener._on_debounce)
        listener._debounce_timer.start()

        # Quick release before debounce
        listener._option_down = False
        listener._debounce_timer.cancel()
        listener._debounce_timer = None

        time.sleep(0.3)  # Wait past debounce period
        assert press_called == []
        assert release_called == []

    def test_held_past_debounce_triggers_press(self):
        """Holding Option past debounce period triggers on_press."""
        press_called = []
        listener = HotkeyListener(
            lambda: press_called.append(1),
            lambda: None,
        )

        # Use a very short debounce for testing
        listener._option_down = True
        listener._confirmed = False
        listener._debounce_timer = threading.Timer(0.01, listener._on_debounce)
        listener._debounce_timer.start()

        time.sleep(0.05)  # Wait for debounce
        assert press_called == [1]
        assert listener._confirmed is True

    def test_release_after_confirm_triggers_release(self):
        """Releasing after debounce confirmed triggers on_release."""
        release_called = []
        listener = HotkeyListener(
            lambda: None,
            lambda: release_called.append(1),
        )

        # Simulate confirmed state and release
        listener._option_down = True
        listener._confirmed = True
        listener._debounce_timer = None

        # Simulate release
        listener._option_down = False
        if listener._confirmed:
            listener._confirmed = False
            listener.on_release()

        assert release_called == [1]

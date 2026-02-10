"""CGEvent tap for Option key press/release detection with debounce."""

import threading
import time

import Quartz

from .constants import (
    DEBOUNCE_SECONDS,
    FLAG_OPTION,
    KEYCODE_LEFT_OPTION,
    KEYCODE_RIGHT_OPTION,
)


class HotkeyListener:
    """Listens for Option key press/release via CGEvent tap.

    Args:
        on_press: Called when Option key is pressed (after debounce).
        on_release: Called when Option key is released.
        hotkey: "option" (either), "left_option", or "right_option".
    """

    def __init__(self, on_press, on_release, hotkey: str = "option"):
        self.on_press = on_press
        self.on_release = on_release
        self.hotkey = hotkey

        self._option_down = False
        self._debounce_timer: threading.Timer | None = None
        self._confirmed = False  # True after debounce fires
        self._tap = None

    def create_tap(self):
        """Create the CGEvent tap. Returns None if Accessibility not granted."""
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged),
            self._callback,
            None,
        )
        return self._tap

    def get_run_loop_source(self):
        """Get the CFRunLoopSource for this event tap."""
        if self._tap is None:
            return None
        return Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)

    def _matches_hotkey(self, keycode: int) -> bool:
        if self.hotkey == "left_option":
            return keycode == KEYCODE_LEFT_OPTION
        elif self.hotkey == "right_option":
            return keycode == KEYCODE_RIGHT_OPTION
        else:  # "option" — either key
            return keycode in (KEYCODE_LEFT_OPTION, KEYCODE_RIGHT_OPTION)

    def _callback(self, proxy, event_type, event, refcon):
        # Re-enable tap if it gets disabled (system does this under load)
        if event_type == Quartz.kCGEventTapDisabledByTimeout:
            Quartz.CGEventTapEnable(self._tap, True)
            return event

        keycode = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode
        )
        flags = Quartz.CGEventGetFlags(event)
        option_pressed = bool(flags & FLAG_OPTION)

        if not self._matches_hotkey(keycode):
            return event

        if option_pressed and not self._option_down:
            # Option key down
            self._option_down = True
            self._confirmed = False
            self._debounce_timer = threading.Timer(DEBOUNCE_SECONDS, self._on_debounce)
            self._debounce_timer.start()

        elif not option_pressed and self._option_down:
            # Option key up
            self._option_down = False
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
                self._debounce_timer = None
            if self._confirmed:
                self._confirmed = False
                self.on_release()

        return event

    def _on_debounce(self):
        """Called after debounce period — Option was held long enough."""
        self._confirmed = True
        self.on_press()

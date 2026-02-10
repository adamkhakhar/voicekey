"""Clipboard save → set text → Cmd+V → restore clipboard."""

import time

import Quartz
from AppKit import NSPasteboard, NSPasteboardItem

from .constants import FLAG_COMMAND, KEYCODE_V, PASTE_DELAY, RESTORE_DELAY


def insert_text(text: str) -> None:
    """Insert text at cursor by pasting and restoring clipboard."""
    pb = NSPasteboard.generalPasteboard()

    # Save current clipboard contents (all types)
    saved_items = _save_clipboard(pb)

    # Set clipboard to our text
    pb.clearContents()
    pb.setString_forType_(text, "public.utf8-plain-text")

    # Small delay to let clipboard settle
    time.sleep(PASTE_DELAY)

    # Simulate Cmd+V
    _simulate_paste()

    # Wait for paste to complete
    time.sleep(RESTORE_DELAY)

    # Restore original clipboard
    _restore_clipboard(pb, saved_items)


def _save_clipboard(pb: NSPasteboard) -> list[dict]:
    """Save all pasteboard items with their types and data."""
    saved = []
    for item in pb.pasteboardItems() or []:
        item_data = {}
        for ptype in item.types():
            data = item.dataForType_(ptype)
            if data is not None:
                item_data[ptype] = data
        if item_data:
            saved.append(item_data)
    return saved


def _restore_clipboard(pb: NSPasteboard, saved_items: list[dict]) -> None:
    """Restore previously saved clipboard contents."""
    pb.clearContents()
    if not saved_items:
        return
    items = []
    for item_data in saved_items:
        item = NSPasteboardItem.alloc().init()
        for ptype, data in item_data.items():
            item.setData_forType_(data, ptype)
        items.append(item)
    pb.writeObjects_(items)


def _simulate_paste() -> None:
    """Simulate Cmd+V keypress via CGEvent."""
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)

    # Key down: V with Command modifier
    key_down = Quartz.CGEventCreateKeyboardEvent(source, KEYCODE_V, True)
    Quartz.CGEventSetFlags(key_down, FLAG_COMMAND)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, key_down)

    # Key up
    key_up = Quartz.CGEventCreateKeyboardEvent(source, KEYCODE_V, False)
    Quartz.CGEventSetFlags(key_up, FLAG_COMMAND)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, key_up)

"""Floating red dot recording indicator via AppKit (NSWindow)."""

from AppKit import (
    NSBezierPath,
    NSColor,
    NSFloatingWindowLevel,
    NSView,
    NSWindow,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowStyleMaskBorderless,
)
from Foundation import NSMakeRect
from PyObjCTools import AppHelper


DOT_SIZE = 20
MARGIN = 30  # from top-right corner


class DotView(NSView):
    """Simple view that draws a red circle."""

    def drawRect_(self, rect):
        NSColor.redColor().setFill()
        path = NSBezierPath.bezierPathWithOvalInRect_(self.bounds())
        path.fill()


class Overlay:
    def __init__(self):
        # Position in top-right of main screen
        from AppKit import NSScreen
        screen = NSScreen.mainScreen().frame()
        x = screen.size.width - DOT_SIZE - MARGIN
        y = screen.size.height - DOT_SIZE - MARGIN

        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, DOT_SIZE, DOT_SIZE),
            NSWindowStyleMaskBorderless,
            2,  # NSBackingStoreBuffered
            False,
        )
        self._window.setLevel_(NSFloatingWindowLevel)
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(NSColor.clearColor())
        self._window.setIgnoresMouseEvents_(True)
        self._window.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces)

        dot_view = DotView.alloc().initWithFrame_(NSMakeRect(0, 0, DOT_SIZE, DOT_SIZE))
        self._window.setContentView_(dot_view)

    def show(self):
        """Show the overlay (dispatched to main thread)."""
        AppHelper.callAfter(self._window.orderFront_, None)

    def hide(self):
        """Hide the overlay (dispatched to main thread)."""
        AppHelper.callAfter(self._window.orderOut_, None)

"""Menu bar icon via rumps."""

import rumps


def create_menubar_app(app) -> rumps.App:
    """Create a menu bar app with settings and quit."""

    menubar = rumps.App("oai-whisper", title="🎤", quit_button=None)

    @rumps.clicked("About")
    def about(_):
        rumps.alert(
            title="oai-whisper",
            message="Voice dictation for macOS.\nHold Option to dictate.",
        )

    @rumps.clicked("Quit")
    def quit_app(_):
        rumps.quit_application()

    menubar.menu = ["About", None, "Quit"]
    return menubar

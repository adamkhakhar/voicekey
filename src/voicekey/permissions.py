"""Check/guide Microphone + Accessibility permissions on macOS."""

import subprocess

import click


def is_accessibility_trusted() -> bool:
    """Check if this process has Accessibility permission."""
    from ApplicationServices import AXIsProcessTrusted
    return AXIsProcessTrusted()


def prompt_accessibility() -> bool:
    """Prompt user to grant Accessibility permission (shows system dialog)."""
    from ApplicationServices import AXIsProcessTrustedWithOptions
    from CoreFoundation import kCFBooleanTrue
    options = {
        "AXTrustedCheckOptionPrompt": kCFBooleanTrue,
    }
    return AXIsProcessTrustedWithOptions(options)


def check_microphone() -> bool:
    """Check microphone access by trying to list audio devices."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        # If we can query devices, we likely have permission
        # Actual recording will trigger the permission dialog if needed
        return len(devices) > 0
    except Exception:
        return False


def check_and_guide():
    """Check permissions and guide the user."""
    # Accessibility
    click.echo("Checking Accessibility permission...")
    if is_accessibility_trusted():
        click.echo("  ✓ Accessibility: granted")
    else:
        click.echo("  ✗ Accessibility: not granted")
        click.echo("    Opening System Settings... Grant access to your terminal app.")
        prompt_accessibility()

    # Microphone
    click.echo("Checking Microphone access...")
    if check_microphone():
        click.echo("  ✓ Microphone: available")
        click.echo("    (Permission dialog will appear on first recording if not yet granted)")
    else:
        click.echo("  ✗ Microphone: no audio devices found")
        click.echo("    Check System Settings → Privacy & Security → Microphone")

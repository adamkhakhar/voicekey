"""Click CLI: start, setup, config subcommands."""

import click

from . import auth, config


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """voicekey — voice dictation for macOS."""
    if ctx.invoked_subcommand is None:
        from .app import run
        run()


@main.command()
def setup():
    """Set up API key and check permissions."""
    existing = auth.get_api_key()
    if existing:
        click.echo(f"API key already stored (ends in ...{existing[-4:]})")
        if not click.confirm("Replace it?"):
            click.echo("Keeping existing key.")
        else:
            _prompt_api_key()
    else:
        _prompt_api_key()

    from . import permissions
    click.echo()
    permissions.check_and_guide()

    click.echo("\nSetup complete. Run `voicekey` to start.")


@main.command("config")
@click.argument("key", required=False)
@click.argument("value", required=False)
def config_cmd(key, value):
    """View or set config values."""
    cfg = config.load()
    if key is None:
        for k, v in cfg.items():
            click.echo(f"{k} = {v!r}")
        return
    if value is None:
        if key in cfg:
            click.echo(f"{key} = {cfg[key]!r}")
        else:
            click.echo(f"Unknown config key: {key}", err=True)
        return
    cfg[key] = value
    config.save(cfg)
    click.echo(f"Set {key} = {value!r}")


def _prompt_api_key():
    key = click.prompt("API key", hide_input=True)
    key = key.strip()
    if not key.startswith("sk-"):
        click.echo("Warning: key doesn't start with 'sk-', saving anyway.")
    auth.set_api_key(key)
    click.echo("API key saved to Keychain.")

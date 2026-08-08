"""CLI for ShhNotes service."""

import functools
import sys

import click
import requests

from .config import Config


def _api_url(endpoint: str) -> str:
    """Build API URL for endpoint."""
    return f"http://{Config.API_HOST}:{Config.API_PORT}{endpoint}"


def _handle_connection_error(func):
    """Decorator to handle API connection errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            click.echo(
                f"Error: Could not connect to API at {Config.API_HOST}:{Config.API_PORT}",
                err=True,
            )
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            try:
                detail = e.response.json().get('detail', str(e))
            except (ValueError, AttributeError):
                detail = e.response.text or str(e)
            click.echo(f"Error: {detail}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    return wrapper


@click.group()
def cli() -> None:
    """ShhNotes — local voice transcription service."""
    pass


@cli.command()
@click.option("--label", default="default", help="Session label for output file naming")
@_handle_connection_error
def start(label: str) -> None:
    """Start a new transcription session."""
    resp = requests.post(_api_url("/start"), json={"label": label})
    resp.raise_for_status()
    data = resp.json()
    click.echo(f"Session started: {data['session_id']}")


@cli.command()
@_handle_connection_error
def stop() -> None:
    """Stop the current session and trigger transcription."""
    resp = requests.post(_api_url("/stop"))
    resp.raise_for_status()
    click.echo("Session stopped, transcribing...")


@cli.command()
@_handle_connection_error
def status() -> None:
    """Get current session state."""
    resp = requests.get(_api_url("/status"))
    resp.raise_for_status()
    data = resp.json()
    click.echo(f"State: {data['state']}")


if __name__ == "__main__":
    cli()

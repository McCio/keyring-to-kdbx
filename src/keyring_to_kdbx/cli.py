"""Command-line interface for keyring-to-kdbx."""

import logging
import sys
from pathlib import Path

import click

from keyring_to_kdbx.exporter import (
    ConflictResolution,
    GroupStrategy,
    KeyringExporter,
)
from keyring_to_kdbx.keyring_reader import KeyringReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(verbose: bool) -> None:
    """Export system keyring secrets to KeePass database (KDBX) format."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@main.command()
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default="keyring-export.kdbx",
    help="Output KDBX file path",
)
@click.option(
    "--update",
    is_flag=True,
    help="Update existing KDBX file instead of creating new",
)
@click.option(
    "--backup",
    is_flag=True,
    help="Create backup of existing KDBX file before modifying",
)
@click.option(
    "--on-conflict",
    type=click.Choice(["skip", "overwrite", "rename"], case_sensitive=False),
    default="skip",
    help="How to handle duplicate entries",
)
@click.option(
    "--group-by",
    type=click.Choice(["flat", "service", "domain"], case_sensitive=False),
    default="service",
    help="How to organize entries in groups",
)
@click.option(
    "--test-keyring",
    is_flag=True,
    help="Test keyring access and exit",
)
def export(
    output: Path,
    update: bool,
    backup: bool,
    on_conflict: str,
    group_by: str,
    test_keyring: bool,
) -> None:
    """Export all keyring credentials to a KeePass database file."""
    try:
        # Test keyring if requested
        if test_keyring:
            _test_keyring()
            return

        # Check if file exists and update flag
        if output.exists() and not update and not backup:
            click.echo(
                f"Error: File {output} already exists. "
                "Use --update to modify it or --backup to create a backup first.",
                err=True,
            )
            sys.exit(1)

        # Prompt for password
        password = _prompt_for_password(output, update)

        # Convert string options to enums
        conflict_res = ConflictResolution(on_conflict.lower())
        group_strat = GroupStrategy(group_by.lower())

        # Create exporter
        click.echo("Initializing exporter...")
        exporter = KeyringExporter(
            output_path=output,
            password=password,
            conflict_resolution=conflict_res,
            group_strategy=group_strat,
            create_backup=backup,
        )

        # Run export
        click.echo("Starting export...")
        result = exporter.export()

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("Export Results:")
        click.echo("=" * 60)
        click.echo(f"Total entries processed: {result.total}")
        click.echo(f"Added:                   {result.added}")
        click.echo(f"Updated:                 {result.updated}")
        click.echo(f"Skipped:                 {result.skipped}")
        click.echo(f"Errors:                  {result.errors}")
        click.echo("=" * 60)
        click.echo(f"\nDatabase saved to: {output}")

        # Set appropriate file permissions (Unix-like systems)
        if sys.platform != "win32":
            try:
                output.chmod(0o600)
                click.echo("File permissions set to 600 (owner read/write only)")
            except Exception as e:
                logger.warning(f"Could not set file permissions: {e}")

        if result.errors > 0:
            click.echo(
                f"\nWarning: {result.errors} entries failed to export. Check logs for details.",
                err=True,
            )
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nExport cancelled by user.", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        logger.exception("Export failed with exception")
        sys.exit(1)


def _prompt_for_password(output: Path, update: bool) -> str:
    """
    Prompt user for KDBX master password.

    Args:
        output: Path to output file.
        update: Whether updating existing file.

    Returns:
        The password string.
    """
    if update and output.exists():
        password = click.prompt(
            f"Enter password for existing database '{output}'",
            hide_input=True,
            type=str,
        )
    else:
        click.echo("\nYou need to set a master password for the KDBX database.")
        click.echo("This password will be required to open the database in KeePass.")
        click.echo("Make sure to store it securely - it cannot be recovered if lost.\n")

        password = click.prompt(
            "Enter master password",
            hide_input=True,
            confirmation_prompt=True,
            type=str,
        )

        if len(password) < 8:
            click.echo(
                "\nWarning: Password is shorter than 8 characters. "
                "Consider using a longer password for better security.",
                err=True,
            )

    return password


def _test_keyring() -> None:
    """Test keyring access and display information."""
    click.echo("Testing keyring access...")

    try:
        reader = KeyringReader()
        click.echo(f"✓ Keyring backend: {reader.backend.__class__.__name__}")

        # Test if backend is working
        if reader.test_backend():
            click.echo("✓ Keyring backend is working correctly")
        else:
            click.echo("✗ Keyring backend test failed", err=True)
            sys.exit(1)

        # Try to get credentials
        click.echo("\nAttempting to enumerate credentials...")
        credentials = reader.get_all_credentials()

        if credentials:
            click.echo(f"✓ Found {len(credentials)} credentials")
            click.echo("\nSample entries (passwords hidden):")
            for i, cred in enumerate(credentials[:5], 1):
                click.echo(f"  {i}. {cred.service} / {cred.username}")
            if len(credentials) > 5:
                click.echo(f"  ... and {len(credentials) - 5} more")
        else:
            click.echo(
                "⚠ No credentials found. "
                "This may mean your keyring is empty or enumeration is not supported.",
                err=True,
            )

        click.echo("\n✓ Keyring access test complete")

    except Exception as e:
        click.echo(f"\n✗ Keyring access test failed: {e}", err=True)
        logger.exception("Keyring test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

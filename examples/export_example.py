#!/usr/bin/env python3
"""Example script demonstrating programmatic usage of keyring-to-kdbx."""

from pathlib import Path

from keyring_to_kdbx.exporter import (
    ConflictResolution,
    GroupStrategy,
    KeyringExporter,
)


def main():
    """Example of using KeyringExporter programmatically."""
    # Configuration
    output_path = Path("my-keyring-backup.kdbx")
    master_password = "super_secure_password_123"  # In real code, get this securely!

    # Create exporter with custom configuration
    exporter = KeyringExporter(
        output_path=output_path,
        password=master_password,
        conflict_resolution=ConflictResolution.SKIP,  # Skip duplicate entries
        group_strategy=GroupStrategy.SERVICE,  # Group by service name
        create_backup=True,  # Backup existing file if present
    )

    print("Starting keyring export...")
    print(f"Output file: {output_path}")
    print()

    try:
        # Perform the export
        result = exporter.export()

        # Display results
        print("=" * 60)
        print("Export Results:")
        print("=" * 60)
        print(f"Total entries:  {result.total}")
        print(f"Added:          {result.added}")
        print(f"Updated:        {result.updated}")
        print(f"Skipped:        {result.skipped}")
        print(f"Errors:         {result.errors}")
        print("=" * 60)

        if result.errors > 0:
            print(f"\nWarning: {result.errors} entries failed to export. Check logs for details.")
        else:
            print(f"\n✓ Successfully exported to {output_path}")
            print("  You can now open this file in KeePass or compatible apps.")

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

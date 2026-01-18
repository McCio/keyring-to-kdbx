"""Module for orchestrating the export of keyring credentials to KDBX."""

import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from keyring_to_kdbx.kdbx_manager import KdbxManager
from keyring_to_kdbx.keyring_reader import KeyringEntry, KeyringReader

if TYPE_CHECKING:
    from pykeepass.entry import Entry

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Strategy for handling duplicate entries."""

    SKIP = "skip"  # Keep existing entry, skip new one
    OVERWRITE = "overwrite"  # Replace existing entry with new one
    RENAME = "rename"  # Create new entry with modified name


class GroupStrategy(Enum):
    """Strategy for organizing entries into groups."""

    FLAT = "flat"  # All entries in root group
    SERVICE = "service"  # Group by service name
    DOMAIN = "domain"  # Group by domain (extracted from service)


class ExportResult:
    """Result of an export operation."""

    def __init__(self) -> None:
        """Initialise export result counters."""
        self.added: int = 0
        self.updated: int = 0
        self.skipped: int = 0
        self.errors: int = 0
        self.total: int = 0

    def __str__(self) -> str:
        """Return a human-readable summary."""
        return (
            f"Export complete: {self.total} entries processed, "
            f"{self.added} added, {self.updated} updated, "
            f"{self.skipped} skipped, {self.errors} errors"
        )


class KeyringExporter:
    """Orchestrates the export of keyring credentials to KDBX."""

    def __init__(
        self,
        output_path: Path,
        password: str,
        conflict_resolution: ConflictResolution = ConflictResolution.SKIP,
        group_strategy: GroupStrategy = GroupStrategy.SERVICE,
        create_backup: bool = False,
    ) -> None:
        """
        Initialise the exporter.

        Args:
            output_path: Path to output KDBX file.
            password: Master password for the KDBX file.
            conflict_resolution: How to handle duplicate entries.
            group_strategy: How to organise entries into groups.
            create_backup: Whether to backup existing KDBX file.
        """
        self.output_path = output_path
        self.password = password
        self.conflict_resolution = conflict_resolution
        self.group_strategy = group_strategy
        self.create_backup = create_backup

        self.keyring_reader = KeyringReader()
        self.kdbx_manager: KdbxManager | None = None

    def export(self) -> ExportResult:
        """
        Export all keyring credentials to KDBX file.

        Returns:
            ExportResult with statistics about the export operation.

        Raises:
            RuntimeError: If export fails.
        """
        result = ExportResult()

        try:
            # Backup existing file if requested
            if self.create_backup and self.output_path.exists():
                self._create_backup()

            # Read keyring entries
            logger.info("Reading keyring credentials...")
            entries = self.keyring_reader.get_all_credentials()
            result.total = len(entries)
            logger.info(f"Found {result.total} keyring entries")

            if result.total == 0:
                logger.warning("No credentials found in keyring")
                return result

            # Initialise KDBX manager
            create = not self.output_path.exists()
            self.kdbx_manager = KdbxManager(self.output_path, self.password, create=create)

            # Export each entry
            for entry in entries:
                try:
                    self._export_entry(entry, result)
                except Exception as e:
                    logger.error(f"Failed to export {entry.service}/{entry.username}: {e}")
                    result.errors += 1

            # Save the database
            self.kdbx_manager.save()

            logger.info(str(result))
            return result

        except Exception as e:
            msg = f"Export failed: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        finally:
            if self.kdbx_manager:
                self.kdbx_manager.close()

    def _export_entry(self, entry: KeyringEntry, result: ExportResult) -> None:
        """
        Export a single keyring entry to KDBX.

        Args:
            entry: The keyring entry to export.
            result: Result object to update with statistics.
        """
        if self.kdbx_manager is None:
            msg = "KDBX manager not initialized"
            raise RuntimeError(msg)

        # Determine group name
        group_name = self._get_group_name(entry.service)

        # Check if entry already exists
        existing = self.kdbx_manager.find_entry(entry.service, entry.username, group_name)

        if existing:
            self._handle_conflict(entry, existing, group_name, result)
        else:
            # Add new entry
            notes = "Exported from system keyring"
            self.kdbx_manager.add_entry(
                service=entry.service,
                username=entry.username,
                password=entry.password,
                group_name=group_name,
                notes=notes,
            )
            result.added += 1
            logger.debug(f"Added entry: {entry.service}/{entry.username}")

    def _handle_conflict(
        self,
        entry: KeyringEntry,
        existing: "Entry",
        group_name: str | None,
        result: ExportResult,
    ) -> None:
        """
        Handle a conflict when an entry already exists.

        Args:
            entry: The new keyring entry.
            existing: The existing KDBX entry.
            group_name: The group name for the entry.
            result: Result object to update with statistics.
        """
        if self.kdbx_manager is None:
            msg = "KDBX manager not initialised"
            raise RuntimeError(msg)

        if self.conflict_resolution == ConflictResolution.SKIP:
            logger.debug(f"Skipping existing entry: {entry.service}/{entry.username}")
            result.skipped += 1

        elif self.conflict_resolution == ConflictResolution.OVERWRITE:
            logger.debug(f"Overwriting entry: {entry.service}/{entry.username}")
            notes = "Exported from system keyring (updated)"
            self.kdbx_manager.update_entry(existing, password=entry.password, notes=notes)
            result.updated += 1

        elif self.conflict_resolution == ConflictResolution.RENAME:
            # Add with a renamed title
            new_service = f"{entry.service} (keyring)"
            logger.debug(f"Renaming entry: {entry.service} -> {new_service}")
            notes = "Exported from system keyring (renamed to avoid conflict)"
            self.kdbx_manager.add_entry(
                service=new_service,
                username=entry.username,
                password=entry.password,
                group_name=group_name,
                notes=notes,
            )
            result.added += 1

    def _get_group_name(self, service: str) -> str | None:
        """
        Determine the group name based on the group strategy.

        Args:
            service: The service name.

        Returns:
            Group name, or None for flat structure.
        """
        if self.group_strategy == GroupStrategy.FLAT:
            return None

        if self.group_strategy == GroupStrategy.SERVICE:
            # Use service name as group
            return service

        if self.group_strategy == GroupStrategy.DOMAIN:
            # Try to extract domain from service name
            # Common patterns: "https://example.com", "example.com", etc.
            service_lower = service.lower()

            # Remove common prefixes
            for prefix in ["https://", "http://", "www."]:
                if service_lower.startswith(prefix):
                    service_lower = service_lower[len(prefix) :]

            # Take first part (domain)
            domain = service_lower.split("/")[0].split(":")[0]

            # If it looks like a domain, use it
            if "." in domain or domain in ["localhost", "local"]:
                return domain

            # Otherwise, fall back to service name
            return service

        return None

    def _create_backup(self) -> None:
        """Create a backup of the existing KDBX file."""
        if not self.output_path.exists():
            return

        backup_path = self.output_path.with_suffix(self.output_path.suffix + ".backup")

        # If backup already exists, add number
        counter = 1
        while backup_path.exists():
            backup_path = self.output_path.with_suffix(f"{self.output_path.suffix}.backup{counter}")
            counter += 1

        logger.info(f"Creating backup: {backup_path}")
        self.output_path.rename(backup_path)
        logger.info("Backup created successfully")

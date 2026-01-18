"""Module for managing KeePass database (KDBX) operations."""

import logging
from pathlib import Path

from pykeepass import PyKeePass, create_database
from pykeepass.entry import Entry
from pykeepass.exceptions import CredentialsError
from pykeepass.group import Group

logger = logging.getLogger(__name__)


class KdbxManager:
    """Manages KeePass database operations."""

    def __init__(
        self, db_path: Path, password: str, create: bool = False
    ) -> None:
        """
        Initialise the KDBX manager.

        Args:
            db_path: Path to the KDBX database file.
            password: Master password for the database.
            create: If True, create a new database. If False, open existing.

        Raises:
            FileNotFoundError: If database doesn't exist and create=False.
            CredentialsError: If password is incorrect for existing database.
            RuntimeError: If database operations fail.
        """
        self.db_path = db_path
        self.password = password
        self.kp: PyKeePass | None = None

        if create:
            if db_path.exists():
                logger.warning(f"Database already exists at {db_path}")
                # Open existing instead of creating
                self._open_database()
            else:
                self._create_database()
        else:
            self._open_database()

    def _create_database(self) -> None:
        """Create a new KeePass database."""
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Creating new database at {self.db_path}")
            self.kp = create_database(
                str(self.db_path),
                password=self.password,
                keyfile=None,
            )
            logger.info("Database created successfully")
        except Exception as e:
            msg = f"Failed to create database: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def _open_database(self) -> None:
        """Open an existing KeePass database."""
        if not self.db_path.exists():
            msg = f"Database not found at {self.db_path}"
            raise FileNotFoundError(msg)

        try:
            logger.info(f"Opening database at {self.db_path}")
            self.kp = PyKeePass(
                str(self.db_path),
                password=self.password,
                keyfile=None,
            )
            logger.info("Database opened successfully")
        except CredentialsError as e:
            msg = "Incorrect password for database"
            logger.error(msg)
            raise CredentialsError(msg) from e
        except Exception as e:
            msg = f"Failed to open database: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def get_or_create_group(
        self, group_name: str, parent: Group | None = None
    ) -> Group:
        """
        Get an existing group or create a new one.

        Args:
            group_name: Name of the group.
            parent: Parent group. If None, uses root group.

        Returns:
            The group object.

        Raises:
            RuntimeError: If database is not initialised.
        """
        if self.kp is None:
            msg = "Database not initialised"
            raise RuntimeError(msg)

        parent_group = parent or self.kp.root_group

        # Try to find existing group
        group = self.kp.find_groups(name=group_name, first=True)

        if group is None:
            logger.debug(f"Creating group: {group_name}")
            group = self.kp.add_group(parent_group, group_name)
        else:
            logger.debug(f"Using existing group: {group_name}")

        return group

    def add_entry(
        self,
        service: str,
        username: str,
        password: str,
        group_name: str | None = None,
        notes: str | None = None,
        url: str | None = None,
        attributes: dict[str, str] | None = None,
    ) -> Entry:
        """
        Add a new entry to the database.

        Args:
            service: Service name (used as title).
            username: Username for the service.
            password: Password for the service.
            group_name: Group to add entry to. If None, uses root group.
            notes: Optional notes for the entry.
            url: Optional URL for the entry.
            attributes: Optional dict of custom attributes from keyring to preserve.

        Returns:
            The created entry.

        Raises:
            RuntimeError: If database is not initialised.
        """
        if self.kp is None:
            msg = "Database not initialised"
            raise RuntimeError(msg)

        # Get or create the group
        group = (
            self.get_or_create_group(group_name)
            if group_name
            else self.kp.root_group
        )

        logger.debug(f"Adding entry: {service}/{username}")

        entry = self.kp.add_entry(
            destination_group=group,
            title=service,
            username=username,
            password=password,
            notes=notes or "",
            url=url or "",
        )

        # Preserve original keyring attributes as custom properties
        # This maintains Secret Service compatibility for KeePassXC
        if attributes:
            for key, value in attributes.items():
                entry.set_custom_property(key, value)
            logger.debug(
                f"Preserved {len(attributes)} original attributes from keyring"
            )

        return entry

    def find_entry(
        self,
        service: str,
        username: str,
        group_name: str | None = None,
    ) -> Entry | None:
        """
        Find an existing entry in the database.

        Args:
            service: Service name (title).
            username: Username for the service.
            group_name: Optional group to search in.

        Returns:
            The entry if found, None otherwise.

        Raises:
            RuntimeError: If database is not initialised.
        """
        if self.kp is None:
            msg = "Database not initialised"
            raise RuntimeError(msg)

        # If group is specified, search in that group
        group = None
        if group_name:
            group = self.kp.find_groups(name=group_name, first=True)

        # Search for entry
        entries = self.kp.find_entries(
            title=service, username=username, first=False
        )

        if not entries:
            return None

        # If group specified, filter by group
        if group:
            for entry in entries:
                if entry.group == group:
                    return entry
            return None

        # Return first match
        return entries[0] if entries else None

    def update_entry(
        self,
        entry: Entry,
        password: str,
        notes: str | None = None,
        url: str | None = None,
    ) -> None:
        """
        Update an existing entry.

        Args:
            entry: The entry to update.
            password: New password.
            notes: Optional new notes.
            url: Optional new URL.
        """
        if self.kp is None:
            msg = "Database not initialised"
            raise RuntimeError(msg)

        logger.debug(f"Updating entry: {entry.title}/{entry.username}")

        entry.password = password
        if notes is not None:
            entry.notes = notes
        if url is not None:
            entry.url = url

    def save(self) -> None:
        """
        Save the database to disk.

        Raises:
            RuntimeError: If database is not initialised or save fails.
        """
        if self.kp is None:
            msg = "Database not initialised"
            raise RuntimeError(msg)

        try:
            logger.info(f"Saving database to {self.db_path}")
            self.kp.save()
            logger.info("Database saved successfully")
        except Exception as e:
            msg = f"Failed to save database: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def get_entry_count(self) -> int:
        """
        Get the total number of entries in the database.

        Returns:
            Number of entries.

        Raises:
            RuntimeError: If database is not initialised.
        """
        if self.kp is None:
            msg = "Database not initialised"
            raise RuntimeError(msg)

        return len(self.kp.entries)

    def get_group_count(self) -> int:
        """
        Get the total number of groups in the database.

        Returns:
            Number of groups.

        Raises:
            RuntimeError: If database is not initialised.
        """
        if self.kp is None:
            msg = "Database not initialised"
            raise RuntimeError(msg)

        return len(self.kp.groups)

    def close(self) -> None:
        """Close the database connection."""
        if self.kp is not None:
            logger.info("Closing database")
            self.kp = None

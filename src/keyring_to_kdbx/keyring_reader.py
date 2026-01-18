"""Module for reading credentials from the system keyring."""

import contextlib
import logging
from collections.abc import Iterator
from dataclasses import dataclass

import keyring
from keyring.backend import KeyringBackend
from keyring.backends.fail import Keyring as FailKeyring

logger = logging.getLogger(__name__)


@dataclass
class KeyringEntry:
    """Represents a single keyring entry with service, username, password, and attributes."""

    service: str
    username: str
    password: str
    attributes: dict[str, str] | None = None

    def __repr__(self) -> str:
        """Return a string representation without exposing the password."""
        return f"KeyringEntry(service={self.service!r}, username={self.username!r}, password='***')"


class KeyringReader:
    """Reads credentials from the system keyring."""

    def __init__(self) -> None:
        """Initialise the KeyringReader and verify keyring backend is available."""
        self.backend: KeyringBackend = keyring.get_keyring()
        if isinstance(self.backend, FailKeyring):
            msg = "No keyring backend available. Please install and configure a keyring service."
            raise RuntimeError(msg)

        logger.info(f"Using keyring backend: {self.backend.__class__.__name__}")

    def get_all_credentials(self) -> list[KeyringEntry]:
        """
        Retrieve all credentials from the system keyring.

        Returns:
            List of KeyringEntry objects containing service, username, and password.

        Raises:
            RuntimeError: If keyring access fails.
        """
        entries = []

        try:
            # Try to get credentials - implementation depends on backend
            # Most keyring backends don't provide a list_credentials method
            # so we need to work with backend-specific methods
            entries = list(self._iterate_credentials())
            logger.info(f"Found {len(entries)} keyring entries")
            return entries
        except Exception as e:
            msg = f"Failed to read keyring credentials: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def _iterate_credentials(self) -> Iterator[KeyringEntry]:  # noqa: PLR0912
        """
        Iterate through credentials using backend-specific methods.

        Yields:
            KeyringEntry objects.

        Note:
            This method attempts different approaches based on the backend type.
            Some backends provide collection methods, others don't.
        """
        backend_name = self.backend.__class__.__name__

        # Try Secret Service backend (Linux GNOME Keyring, etc.)
        if hasattr(self.backend, "get_all_credentials"):
            logger.debug("Using get_all_credentials method")
            try:
                credentials = self.backend.get_all_credentials()
                for cred in credentials:
                    if hasattr(cred, "service") and hasattr(cred, "username"):
                        password = keyring.get_password(
                            cred.service, cred.username
                        )
                        if password:
                            # Extract attributes if available
                            attributes = {}
                            if hasattr(cred, "attributes"):
                                attributes = dict(cred.attributes)
                            yield KeyringEntry(
                                service=cred.service,
                                username=cred.username,
                                password=password,
                                attributes=attributes if attributes else None,
                            )
            except Exception as e:
                logger.warning(f"get_all_credentials failed: {e}")

        # Try to use the collection property (SecretService backend)
        elif (
            hasattr(self.backend, "collection")
            and self.backend.collection is not None
        ):
            logger.debug("Using collection property")
            try:
                for item in self.backend.collection.get_all_items():
                    attributes = item.get_attributes()
                    service = attributes.get(
                        "service", attributes.get("application", "unknown")
                    )
                    username = attributes.get(
                        "username", attributes.get("user", "")
                    )

                    if service and username:
                        password = keyring.get_password(service, username)
                        if password:
                            yield KeyringEntry(
                                service=service,
                                username=username,
                                password=password,
                                attributes=dict(attributes)
                                if attributes
                                else None,
                            )
            except Exception as e:
                logger.warning(f"Collection iteration failed: {e}")

        # macOS Keychain backend
        elif "Keychain" in backend_name:
            logger.warning(
                "macOS Keychain backend detected. Direct enumeration not supported.\n"
                "Please use macOS security command or specify credentials manually."
            )
            # Could potentially use subprocess to call 'security dump-keychain'
            # but this requires additional permissions and parsing

        # Windows Credential Manager backend
        elif "Windows" in backend_name or "Win" in backend_name:
            logger.warning(
                "Windows Credential Manager backend detected. Direct enumeration not supported.\n"
                "Please use Windows cmdkey or specify credentials manually."
            )
            # Could potentially use win32cred or subprocess to enumerate
            # but this is complex and requires additional dependencies

        else:
            logger.warning(
                f"Keyring backend '{backend_name}' does not support credential enumeration.\n"
                "You may need to manually specify which credentials to export."
            )

    def get_credential(
        self, service: str, username: str
    ) -> KeyringEntry | None:
        """
        Retrieve a specific credential from the keyring.

        Args:
            service: The service name.
            username: The username for the service.

        Returns:
            KeyringEntry if found, None otherwise.
        """
        try:
            password = keyring.get_password(service, username)
            if password:
                logger.debug(f"Retrieved credential for {service}/{username}")
                return KeyringEntry(
                    service=service,
                    username=username,
                    password=password,
                    attributes=None,
                )
            logger.debug(f"No password found for {service}/{username}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get credential for {service}/{username}: {e}"
            )
            return None

    def test_backend(self) -> bool:
        """
        Test if the keyring backend is working properly.

        Returns:
            True if backend is accessible, False otherwise.
        """
        test_service = "__keyring_to_kdbx_test__"
        test_username = "test_user"
        test_password = "test_password_12345"

        try:
            # Try to set a test credential
            keyring.set_password(test_service, test_username, test_password)

            # Try to retrieve it
            retrieved = keyring.get_password(test_service, test_username)

            # Clean up
            with contextlib.suppress(Exception):
                keyring.delete_password(test_service, test_username)

            return retrieved == test_password
        except Exception as e:
            logger.error(f"Keyring backend test failed: {e}")
            return False

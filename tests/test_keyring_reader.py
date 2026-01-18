"""Tests for keyring_reader module."""

from unittest.mock import Mock, patch

import pytest
from keyring.backends.fail import Keyring as FailKeyring

from keyring_to_kdbx.keyring_reader import KeyringEntry, KeyringReader

# Check if secretstorage is available (Linux only)
try:
    import secretstorage  # noqa: F401

    HAS_SECRETSTORAGE = True
except ImportError:
    HAS_SECRETSTORAGE = False


class TestKeyringEntry:
    """Tests for KeyringEntry dataclass."""

    def test_keyring_entry_repr_hides_password(self):
        """Test that __repr__ doesn't expose the password."""
        entry = KeyringEntry(
            service="github.com",
            username="user@example.com",
            password="super_secret_123",
        )
        repr_str = repr(entry)
        assert "super_secret_123" not in repr_str
        assert "***" in repr_str
        assert "github.com" in repr_str
        assert "user@example.com" in repr_str

    def test_keyring_entry_repr_format(self):
        """Test that __repr__ uses correct format."""
        entry = KeyringEntry(
            service="test.com",
            username="user",
            password="secret",
        )
        repr_str = repr(entry)
        # Verify it's a valid Python repr format
        assert repr_str.startswith("KeyringEntry(")
        assert repr_str.endswith(")")
        # Verify quotes around string values
        assert "service='test.com'" in repr_str or 'service="test.com"' in repr_str
        assert "username='user'" in repr_str or 'username="user"' in repr_str
        assert "password='***'" in repr_str or 'password="***"' in repr_str


class TestKeyringReader:
    """Tests for KeyringReader class."""

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_init_with_valid_backend(self, mock_get_keyring):
        """Test initialization with a valid keyring backend."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        reader = KeyringReader()
        assert reader.backend == mock_backend

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_init_with_fail_backend_raises_error(self, mock_get_keyring):
        """Test initialization with FailKeyring raises RuntimeError."""
        mock_get_keyring.return_value = FailKeyring()

        with pytest.raises(RuntimeError, match="No keyring backend available"):
            KeyringReader()

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_password")
    def test_get_credential(self, mock_get_password, mock_get_keyring):
        """Test getting a specific credential constructs proper KeyringEntry."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend
        mock_get_password.return_value = "test_password"

        reader = KeyringReader()
        entry = reader.get_credential("test_service", "test_user")

        # Verify it returns a proper KeyringEntry object
        assert isinstance(entry, KeyringEntry)
        assert entry.service == "test_service"
        assert entry.username == "test_user"
        assert entry.password == "test_password"
        # Verify password is hidden in repr (security check)
        assert "test_password" not in repr(entry)
        mock_get_password.assert_called_once_with("test_service", "test_user")

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_password")
    def test_get_credential_returns_none_not_exception(self, mock_get_password, mock_get_keyring):
        """Test that missing credentials return None, not raise exceptions."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend
        mock_get_password.return_value = None

        reader = KeyringReader()
        entry = reader.get_credential("missing_service", "missing_user")
        # Should return None for missing credentials, not raise exception
        assert entry is None

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_password")
    def test_get_credential_handles_keyring_errors(self, mock_get_password, mock_get_keyring):
        """Test that keyring errors are handled gracefully."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend
        mock_get_password.side_effect = Exception("Keyring backend error")

        reader = KeyringReader()
        entry = reader.get_credential("error_service", "error_user")
        # Should handle exceptions and return None
        assert entry is None

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_with_get_all_method(self, mock_get_keyring):
        """Test that get_all_credentials correctly retrieves passwords for all creds."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"

        # Mock credentials returned by get_all_credentials
        mock_cred1 = Mock()
        mock_cred1.service = "service1"
        mock_cred1.username = "user1"
        mock_cred1.attributes = {"service": "service1", "username": "user1"}

        mock_cred2 = Mock()
        mock_cred2.service = "service2"
        mock_cred2.username = "user2"
        mock_cred2.attributes = {"service": "service2", "username": "user2"}

        mock_backend.get_all_credentials.return_value = [mock_cred1, mock_cred2]
        mock_get_keyring.return_value = mock_backend

        with patch("keyring_to_kdbx.keyring_reader.keyring.get_password") as mock_get_password:
            mock_get_password.side_effect = ["password1", "password2"]

            reader = KeyringReader()
            entries = reader.get_all_credentials()

            # Verify it calls get_password for each credential
            assert mock_get_password.call_count == 2
            mock_get_password.assert_any_call("service1", "user1")
            mock_get_password.assert_any_call("service2", "user2")

            # Verify all entries are KeyringEntry objects with correct data
            assert len(entries) == 2
            assert all(isinstance(e, KeyringEntry) for e in entries)
            assert entries[0].service == "service1"
            assert entries[0].username == "user1"
            assert entries[0].password == "password1"
            assert entries[1].service == "service2"
            assert entries[1].username == "user2"
            assert entries[1].password == "password2"

    @pytest.mark.skipif(not HAS_SECRETSTORAGE, reason="secretstorage not available (Linux only)")
    @patch("keyring_to_kdbx.keyring_reader.secretstorage")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_with_get_preferred_collection(
        self, mock_get_keyring, mock_secretstorage
    ):
        """Test that secretstorage enumeration correctly retrieves credentials from all collections."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"

        # Backend doesn't have get_all_credentials but has get_preferred_collection
        del mock_backend.get_all_credentials
        mock_backend.get_preferred_collection.return_value = Mock()

        mock_get_keyring.return_value = mock_backend

        # Mock secretstorage to return collections
        mock_connection = Mock()
        mock_secretstorage.dbus_init.return_value = mock_connection

        # Mock collection items
        mock_item1 = Mock()
        mock_item1.get_attributes.return_value = {
            "service": "service1",
            "username": "user1",
        }
        mock_item1.get_secret.return_value = b"password1"

        mock_item2 = Mock()
        mock_item2.get_attributes.return_value = {
            "service": "service2",
            "username": "user2",
        }
        mock_item2.get_secret.return_value = b"password2"

        mock_collection = Mock()
        mock_collection.is_locked.return_value = False
        mock_collection.get_label.return_value = "Test Collection"
        mock_collection.get_all_items.return_value = [mock_item1, mock_item2]

        mock_secretstorage.get_all_collections.return_value = [mock_collection]

        reader = KeyringReader()
        entries = reader.get_all_credentials()

        # Verify it uses secretstorage
        mock_secretstorage.dbus_init.assert_called_once()
        mock_secretstorage.get_all_collections.assert_called_once()

        # Verify it correctly extracts service/username from attributes
        assert mock_item1.get_attributes.called
        assert mock_item2.get_attributes.called

        # Verify secrets retrieved directly from items
        assert mock_item1.get_secret.called
        assert mock_item2.get_secret.called

        assert len(entries) == 2
        assert entries[0].service == "service1"
        assert entries[0].password == "password1"
        assert entries[1].service == "service2"
        assert entries[1].password == "password2"

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_with_collection(self, mock_get_keyring):
        """Test that collection property fallback correctly extracts attributes."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"

        # Backend doesn't have get_all_credentials or get_preferred_collection but has collection
        del mock_backend.get_all_credentials
        if hasattr(mock_backend, "get_preferred_collection"):
            del mock_backend.get_preferred_collection

        # Mock collection items
        mock_item1 = Mock()
        mock_item1.get_attributes.return_value = {
            "service": "service1",
            "username": "user1",
        }

        mock_item2 = Mock()
        mock_item2.get_attributes.return_value = {
            "service": "service2",
            "username": "user2",
        }

        mock_collection = Mock()
        mock_collection.get_all_items.return_value = [mock_item1, mock_item2]
        mock_backend.collection = mock_collection

        mock_get_keyring.return_value = mock_backend

        with patch("keyring_to_kdbx.keyring_reader.keyring.get_password") as mock_get_password:
            mock_get_password.side_effect = ["password1", "password2"]

            reader = KeyringReader()
            entries = reader.get_all_credentials()

            # Verify it correctly extracts service/username from attributes
            assert mock_item1.get_attributes.called
            assert mock_item2.get_attributes.called

            # Verify it retrieves passwords for extracted credentials
            assert mock_get_password.call_count == 2
            mock_get_password.assert_any_call("service1", "user1")
            mock_get_password.assert_any_call("service2", "user2")

            assert len(entries) == 2
            assert entries[0].service == "service1"
            assert entries[0].password == "password1"

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_empty_keyring(self, mock_get_keyring):
        """Test that empty keyring returns empty list, not None or error."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_backend.get_all_credentials.return_value = []
        mock_get_keyring.return_value = mock_backend

        reader = KeyringReader()
        entries = reader.get_all_credentials()

        # Should return empty list (not None, not raise exception)
        assert entries == []
        assert isinstance(entries, list)

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_filters_empty_passwords(self, mock_get_keyring):
        """Test that credentials with None passwords are filtered out."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"

        mock_cred1 = Mock()
        mock_cred1.service = "service1"
        mock_cred1.username = "user1"
        mock_cred1.attributes = {"service": "service1", "username": "user1"}

        mock_cred2 = Mock()
        mock_cred2.service = "service2"
        mock_cred2.username = "user2"
        mock_cred2.attributes = {"service": "service2", "username": "user2"}

        mock_backend.get_all_credentials.return_value = [mock_cred1, mock_cred2]
        mock_get_keyring.return_value = mock_backend

        with patch("keyring_to_kdbx.keyring_reader.keyring.get_password") as mock_get_password:
            # First has password, second doesn't
            mock_get_password.side_effect = ["password1", None]

            reader = KeyringReader()
            entries = reader.get_all_credentials()

            # Only credential with password should be included
            assert len(entries) == 1
            assert entries[0].service == "service1"
            assert entries[0].password == "password1"

    @patch("keyring_to_kdbx.keyring_reader.keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_test_backend_verifies_round_trip(self, mock_get_keyring, mock_keyring):
        """Test that backend test verifies full set/get/delete cycle."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        # Mock successful set/get/delete cycle
        mock_keyring.get_password.return_value = "test_password_12345"
        mock_keyring.set_password.return_value = None
        mock_keyring.delete_password.return_value = None

        reader = KeyringReader()
        result = reader.test_backend()

        # Verify it performs all three operations
        mock_keyring.set_password.assert_called_once()
        mock_keyring.get_password.assert_called_once()
        mock_keyring.delete_password.assert_called_once()

        # Verify it uses test credentials
        set_call = mock_keyring.set_password.call_args
        assert "__keyring_to_kdbx_test__" in set_call[0]

        assert result is True

    @patch("keyring_to_kdbx.keyring_reader.keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_test_backend_detects_password_mismatch(self, mock_get_keyring, mock_keyring):
        """Test that backend test fails if retrieved password doesn't match."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        # Set succeeds but get returns wrong password
        mock_keyring.set_password.return_value = None
        mock_keyring.get_password.return_value = "wrong_password"
        mock_keyring.delete_password.return_value = None

        reader = KeyringReader()
        result = reader.test_backend()

        # Should fail because passwords don't match
        assert result is False

    @patch("keyring_to_kdbx.keyring_reader.keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_test_backend_handles_exceptions(self, mock_get_keyring, mock_keyring):
        """Test that backend test returns False on exceptions, not crash."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        # Mock failed set operation
        mock_keyring.set_password.side_effect = Exception("Backend error")

        reader = KeyringReader()
        result = reader.test_backend()

        # Should return False, not raise exception
        assert result is False

    @pytest.mark.skipif(not HAS_SECRETSTORAGE, reason="secretstorage not available (Linux only)")
    @patch("keyring_to_kdbx.keyring_reader.secretstorage")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_unsupported_backend_warning(self, mock_get_keyring, mock_secretstorage):
        """Test warning is logged for unsupported backends."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "UnsupportedKeyring"

        # Remove methods that indicate enumeration support
        if hasattr(mock_backend, "get_all_credentials"):
            del mock_backend.get_all_credentials
        if hasattr(mock_backend, "get_preferred_collection"):
            del mock_backend.get_preferred_collection
        mock_backend.collection = None

        mock_get_keyring.return_value = mock_backend

        # Mock secretstorage to return empty collections
        mock_connection = Mock()
        mock_secretstorage.dbus_init.return_value = mock_connection
        mock_secretstorage.get_all_collections.return_value = []

        reader = KeyringReader()
        entries = reader.get_all_credentials()

        # Should return empty list for unsupported backend
        assert entries == []

"""Tests for keyring_reader module."""

from unittest.mock import Mock, patch

import pytest
from keyring.backends.fail import Keyring as FailKeyring

from keyring_to_kdbx.keyring_reader import KeyringEntry, KeyringReader


class TestKeyringEntry:
    """Tests for KeyringEntry dataclass."""

    def test_keyring_entry_creation(self):
        """Test creating a KeyringEntry."""
        entry = KeyringEntry(
            service="test_service",
            username="test_user",
            password="test_password",
        )
        assert entry.service == "test_service"
        assert entry.username == "test_user"
        assert entry.password == "test_password"

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
    def test_get_credential(self, mock_get_keyring):
        """Test getting a specific credential."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        with patch("keyring_to_kdbx.keyring_reader.keyring.get_password") as mock_get_password:
            mock_get_password.return_value = "test_password"

            reader = KeyringReader()
            entry = reader.get_credential("test_service", "test_user")

            assert entry is not None
            assert entry.service == "test_service"
            assert entry.username == "test_user"
            assert entry.password == "test_password"
            mock_get_password.assert_called_once_with("test_service", "test_user")

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_credential_not_found(self, mock_get_keyring):
        """Test getting a credential that doesn't exist."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        with patch("keyring_to_kdbx.keyring_reader.keyring.get_password") as mock_get_password:
            mock_get_password.return_value = None

            reader = KeyringReader()
            entry = reader.get_credential("nonexistent", "user")

            assert entry is None

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_with_get_all_method(self, mock_get_keyring):
        """Test getting all credentials when backend supports get_all_credentials."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"

        # Mock credentials returned by get_all_credentials
        mock_cred1 = Mock()
        mock_cred1.service = "service1"
        mock_cred1.username = "user1"

        mock_cred2 = Mock()
        mock_cred2.service = "service2"
        mock_cred2.username = "user2"

        mock_backend.get_all_credentials.return_value = [mock_cred1, mock_cred2]
        mock_get_keyring.return_value = mock_backend

        with patch("keyring_to_kdbx.keyring_reader.keyring.get_password") as mock_get_password:
            mock_get_password.side_effect = ["password1", "password2"]

            reader = KeyringReader()
            entries = reader.get_all_credentials()

            assert len(entries) == 2
            assert entries[0].service == "service1"
            assert entries[0].username == "user1"
            assert entries[0].password == "password1"
            assert entries[1].service == "service2"
            assert entries[1].username == "user2"
            assert entries[1].password == "password2"

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_with_collection(self, mock_get_keyring):
        """Test getting all credentials using collection property."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"

        # Backend doesn't have get_all_credentials but has collection
        del mock_backend.get_all_credentials

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

            assert len(entries) == 2
            assert entries[0].service == "service1"
            assert entries[0].password == "password1"

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_get_all_credentials_empty_keyring(self, mock_get_keyring):
        """Test getting all credentials when keyring is empty."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_backend.get_all_credentials.return_value = []
        mock_get_keyring.return_value = mock_backend

        reader = KeyringReader()
        entries = reader.get_all_credentials()

        assert entries == []

    @patch("keyring_to_kdbx.keyring_reader.keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_test_backend_success(self, mock_get_keyring, mock_keyring):
        """Test backend test succeeds with working keyring."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        # Mock successful set/get/delete cycle
        mock_keyring.get_password.return_value = "test_password_12345"
        mock_keyring.set_password.return_value = None
        mock_keyring.delete_password.return_value = None

        reader = KeyringReader()
        assert reader.test_backend() is True

    @patch("keyring_to_kdbx.keyring_reader.keyring")
    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_test_backend_failure(self, mock_get_keyring, mock_keyring):
        """Test backend test fails with non-working keyring."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "SecretServiceKeyring"
        mock_get_keyring.return_value = mock_backend

        # Mock failed set operation
        mock_keyring.set_password.side_effect = Exception("Backend error")

        reader = KeyringReader()
        assert reader.test_backend() is False

    @patch("keyring_to_kdbx.keyring_reader.keyring.get_keyring")
    def test_unsupported_backend_warning(self, mock_get_keyring):
        """Test warning is logged for unsupported backends."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "UnsupportedKeyring"

        # Remove methods that indicate enumeration support
        if hasattr(mock_backend, "get_all_credentials"):
            del mock_backend.get_all_credentials
        mock_backend.collection = None

        mock_get_keyring.return_value = mock_backend

        reader = KeyringReader()
        entries = reader.get_all_credentials()

        # Should return empty list for unsupported backend
        assert entries == []

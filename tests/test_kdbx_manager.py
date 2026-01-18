"""Tests for kdbx_manager module."""

from unittest.mock import Mock, patch

import pytest
from pykeepass.exceptions import CredentialsError

from keyring_to_kdbx.kdbx_manager import KdbxManager


@pytest.fixture
def temp_kdbx_path(tmp_path):
    """Provide a temporary path for KDBX file."""
    return tmp_path / "test.kdbx"


@pytest.fixture
def test_password():
    """Provide a test password."""
    return "test_password_123"


class TestKdbxManagerInit:
    """Tests for KdbxManager initialization."""

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_create_new_database_calls_pykeepass_constructor(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that creating new database uses create_database correctly."""
        mock_kp = Mock()
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Verify create_database was called with correct arguments
        mock_create_db.assert_called_once()
        call_args = mock_create_db.call_args
        assert str(temp_kdbx_path) in str(call_args)
        assert test_password in call_args.args or test_password in call_args.kwargs.values()

        # Verify manager is usable
        assert manager.kp is not None

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_open_existing_database_does_not_save(
        self, mock_pykeepass, temp_kdbx_path, test_password
    ):
        """Test that opening existing database doesn't auto-save."""
        # Create a dummy file to simulate existing database
        temp_kdbx_path.touch()

        mock_kp = Mock()
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=False)

        # Verify it opens the file (not creates)
        mock_pykeepass.assert_called_once_with(
            str(temp_kdbx_path), password=test_password, keyfile=None
        )

        # Verify manager is usable
        assert manager.kp is not None

    def test_open_nonexistent_database_raises_error(self, temp_kdbx_path, test_password):
        """Test opening a non-existent database raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            KdbxManager(temp_kdbx_path, test_password, create=False)

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_open_with_wrong_password_raises_error(
        self, mock_pykeepass, temp_kdbx_path, test_password
    ):
        """Test opening with wrong password raises CredentialsError."""
        temp_kdbx_path.touch()
        mock_pykeepass.side_effect = CredentialsError("Invalid credentials")

        with pytest.raises(CredentialsError, match="Incorrect password"):
            KdbxManager(temp_kdbx_path, test_password, create=False)

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_create_when_exists_opens_instead(
        self, mock_create_db, mock_pykeepass, temp_kdbx_path, test_password
    ):
        """Test that create=True on existing file opens it instead."""
        temp_kdbx_path.touch()

        mock_kp = Mock()
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        assert manager.kp == mock_kp
        # Should call PyKeePass to open, not create_database
        mock_pykeepass.assert_called()
        mock_create_db.assert_not_called()


class TestKdbxManagerGroups:
    """Tests for group management."""

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_get_or_create_group_searches_first(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that get_or_create_group searches for existing group before creating."""
        mock_kp = Mock()
        mock_kp.find_groups.return_value = None
        mock_kp.root_group = Mock()
        mock_new_group = Mock()
        mock_kp.add_group.return_value = mock_new_group
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        group = manager.get_or_create_group("TestGroup")

        # Verify it searches first
        mock_kp.find_groups.assert_called_once()

        # Verify it creates only when not found
        mock_kp.add_group.assert_called_once_with(mock_kp.root_group, "TestGroup")

        # Verify it returns the created group
        assert group == mock_new_group

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_get_or_create_group_avoids_duplicates(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that existing groups are reused, not duplicated."""
        mock_kp = Mock()
        mock_existing_group = Mock()
        mock_kp.find_groups.return_value = mock_existing_group
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        group = manager.get_or_create_group("ExistingGroup")

        # Verify it searches for the group
        mock_kp.find_groups.assert_called_once()

        # Verify it returns existing group without creating new one
        assert group == mock_existing_group
        mock_kp.add_group.assert_not_called()

    def test_get_or_create_group_without_init_raises_error(self, temp_kdbx_path, test_password):
        """Test that calling get_or_create_group without init raises error."""
        manager = KdbxManager.__new__(KdbxManager)
        manager.kp = None

        with pytest.raises(RuntimeError, match="Database not initialised"):
            manager.get_or_create_group("TestGroup")


class TestKdbxManagerEntries:
    """Tests for entry management."""

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_add_entry_uses_root_group_by_default(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that entries are added to root group when no group specified."""
        mock_kp = Mock()
        mock_kp.root_group = Mock()
        mock_entry = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        manager.add_entry(
            service="test_service",
            username="test_user",
            password="test_pass",
            notes="test notes",
        )

        # Verify it calls add_entry
        mock_kp.add_entry.assert_called_once()

        # Verify it uses root_group as destination
        call_kwargs = mock_kp.add_entry.call_args.kwargs
        assert call_kwargs["destination_group"] == mock_kp.root_group

        # Verify all parameters are passed
        assert call_kwargs["title"] == "test_service"
        assert call_kwargs["username"] == "test_user"
        assert call_kwargs["password"] == "test_pass"
        assert call_kwargs["notes"] == "test notes"

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_add_entry_creates_group_if_needed(self, mock_create_db, temp_kdbx_path, test_password):
        """Test that specifying group_name triggers group creation/retrieval."""
        mock_kp = Mock()
        mock_group = Mock()
        mock_kp.find_groups.return_value = mock_group
        mock_kp.root_group = Mock()
        mock_entry = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        manager.add_entry(
            service="test_service",
            username="test_user",
            password="test_pass",
            group_name="TestGroup",
        )

        # Verify it searches for the group
        mock_kp.find_groups.assert_called_once()

        # Verify the entry is added to the specified group, not root
        call_args = mock_kp.add_entry.call_args
        assert call_args.kwargs["destination_group"] == mock_group
        assert call_args.kwargs["destination_group"] != mock_kp.root_group

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_find_entry_returns_first_match(self, mock_create_db, temp_kdbx_path, test_password):
        """Test that find_entry returns first match when multiple exist."""
        mock_kp = Mock()
        mock_entry1 = Mock()
        mock_entry2 = Mock()
        mock_kp.find_entries.return_value = [mock_entry1, mock_entry2]
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        found_entry = manager.find_entry("test_service", "test_user")

        # Verify it searches with correct criteria
        mock_kp.find_entries.assert_called_once()

        # Verify it returns the first entry from results
        assert found_entry == mock_entry1
        assert found_entry != mock_entry2

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_find_entry_returns_none_not_exception(
        self, mock_pykeepass, temp_kdbx_path, test_password
    ):
        """Test that missing entries return None instead of raising exception."""
        mock_kp = Mock()
        mock_kp.find_entries.return_value = []
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Should not raise exception
        found_entry = manager.find_entry("nonexistent", "user")

        # Should return None for not found
        assert found_entry is None

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_update_entry_modifies_fields(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test that update_entry actually modifies the entry object."""
        mock_kp = Mock()
        mock_entry = Mock()
        mock_entry.password = "old_password"
        mock_entry.notes = "old_notes"
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Update specific fields
        manager.update_entry(mock_entry, password="new_password", notes="new_notes")

        # Verify fields were changed
        assert mock_entry.password == "new_password"
        assert mock_entry.notes == "new_notes"

        # Verify old values are gone
        assert mock_entry.password != "old_password"
        assert mock_entry.notes != "old_notes"

    def test_add_entry_without_init_raises_error(self, temp_kdbx_path, test_password):
        """Test that calling add_entry without init raises error."""
        manager = KdbxManager.__new__(KdbxManager)
        manager.kp = None

        with pytest.raises(RuntimeError, match="Database not initialised"):
            manager.add_entry("service", "user", "pass")

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_add_entry_sanitizes_special_characters(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that special characters like quotes are sanitized in title but not username."""
        mock_kp = Mock()
        mock_kp.root_group = Mock()
        mock_entry = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        manager.add_entry(
            service='"quoted-service"',
            username='user"with"quotes',
            password="test_pass",
        )

        # Verify title is sanitized (quotes removed) but username is unchanged
        call_args = mock_kp.add_entry.call_args
        assert call_args.kwargs["title"] == "quoted-service"
        assert call_args.kwargs["username"] == 'user"with"quotes'

        # Verify original title not used
        assert call_args.kwargs["title"] != '"quoted-service"'


class TestKdbxManagerPersistence:
    """Tests for database persistence."""

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_save_can_be_called_multiple_times(self, mock_create_db, temp_kdbx_path, test_password):
        """Test that save() can be called multiple times without error."""
        mock_kp = Mock()
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Call save multiple times
        manager.save()
        manager.save()
        manager.save()

        # Verify all saves went through
        assert mock_kp.save.call_count == 3

    def test_save_without_init_raises_error(self, temp_kdbx_path, test_password):
        """Test that calling save without init raises error."""
        manager = KdbxManager.__new__(KdbxManager)
        manager.kp = None

        with pytest.raises(RuntimeError, match="Database not initialised"):
            manager.save()

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_get_entry_count_reflects_database_state(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that entry count accurately reflects database entries."""
        mock_kp = Mock()
        mock_kp.entries = [Mock(), Mock(), Mock()]
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        count = manager.get_entry_count()

        # Verify count matches actual entries
        assert count == len(mock_kp.entries)
        assert count == 3

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_get_group_count_reflects_database_state(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that group count accurately reflects database groups."""
        mock_kp = Mock()
        mock_kp.groups = [Mock(), Mock()]
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        count = manager.get_group_count()

        # Verify count matches actual groups
        assert count == len(mock_kp.groups)
        assert count == 2

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_close_database_clears_reference(self, mock_create_db, temp_kdbx_path, test_password):
        """Test that closing database clears internal reference."""
        mock_kp = Mock()
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Verify database is open
        assert manager.kp is not None

        manager.close()

        # Verify database reference is cleared
        assert manager.kp is None

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_close_can_be_called_multiple_times(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that close() is idempotent and doesn't error on repeated calls."""
        mock_kp = Mock()
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Close multiple times should not raise error
        manager.close()
        manager.close()
        manager.close()

        # Should still be None
        assert manager.kp is None


class TestSecretServiceIntegration:
    """Tests for Secret Service / KeePassXC integration attributes."""

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_add_entry_preserves_original_attributes(
        self, mock_create_db, temp_kdbx_path, test_password
    ):
        """Test that original keyring attributes are preserved as custom properties."""
        mock_kp = Mock()
        mock_kp.root_group = Mock()
        mock_entry = Mock()
        mock_entry.set_custom_property = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Add entry with original attributes from keyring
        original_attrs = {
            "service": "github.com",
            "application": "git-credential-manager",
            "xdg:schema": "org.freedesktop.Secret.Generic",
        }

        manager.add_entry(
            service="github.com",
            username="testuser",
            password="testpass",
            attributes=original_attrs,
        )

        # Verify all original attributes were preserved
        assert mock_entry.set_custom_property.call_count == 3

        # Check that all original attributes were set
        calls = mock_entry.set_custom_property.call_args_list
        set_attrs = {call[0][0]: call[0][1] for call in calls}
        assert set_attrs == original_attrs

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_add_entry_without_attributes(self, mock_create_db, temp_kdbx_path, test_password):
        """Test that entries without attributes don't cause errors."""
        mock_kp = Mock()
        mock_kp.root_group = Mock()
        mock_entry = Mock()
        mock_entry.set_custom_property = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Add entry without attributes
        manager.add_entry(
            service="gitlab.com",
            username="user1",
            password="pass1",
            attributes=None,
        )

        # Verify no custom properties were set
        mock_entry.set_custom_property.assert_not_called()

    @patch("keyring_to_kdbx.kdbx_manager.create_database")
    def test_add_entry_with_empty_attributes(self, mock_create_db, temp_kdbx_path, test_password):
        """Test that empty attributes dict doesn't set properties."""
        mock_kp = Mock()
        mock_kp.root_group = Mock()
        mock_entry = Mock()
        mock_entry.set_custom_property = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_create_db.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        # Add entry with empty attributes
        manager.add_entry(
            service="bitbucket.org",
            username="user2",
            password="pass2",
            attributes={},
        )

        # Verify no custom properties were set
        mock_entry.set_custom_property.assert_not_called()

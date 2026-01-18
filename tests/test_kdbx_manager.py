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

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_create_new_database(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test creating a new database."""
        mock_kp = Mock()
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        assert manager.kp == mock_kp
        mock_kp.save.assert_called_once()

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_open_existing_database(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test opening an existing database."""
        # Create a dummy file to simulate existing database
        temp_kdbx_path.touch()

        mock_kp = Mock()
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=False)

        assert manager.kp == mock_kp
        mock_pykeepass.assert_called_once_with(
            str(temp_kdbx_path), password=test_password, keyfile=None
        )

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
    def test_create_when_exists_opens_instead(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test that create=True on existing file opens it instead."""
        temp_kdbx_path.touch()

        mock_kp = Mock()
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)

        assert manager.kp == mock_kp
        # Should call PyKeePass to open, not save
        mock_pykeepass.assert_called()


class TestKdbxManagerGroups:
    """Tests for group management."""

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_get_or_create_group_creates_new(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test creating a new group."""
        mock_kp = Mock()
        mock_kp.find_groups.return_value = None
        mock_kp.root_group = Mock()
        mock_new_group = Mock()
        mock_kp.add_group.return_value = mock_new_group
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        group = manager.get_or_create_group("TestGroup")

        assert group == mock_new_group
        mock_kp.add_group.assert_called_once_with(mock_kp.root_group, "TestGroup")

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_get_or_create_group_returns_existing(
        self, mock_pykeepass, temp_kdbx_path, test_password
    ):
        """Test getting an existing group."""
        mock_kp = Mock()
        mock_existing_group = Mock()
        mock_kp.find_groups.return_value = mock_existing_group
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        group = manager.get_or_create_group("ExistingGroup")

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

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_add_entry(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test adding a new entry."""
        mock_kp = Mock()
        mock_kp.root_group = Mock()
        mock_entry = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        entry = manager.add_entry(
            service="test_service",
            username="test_user",
            password="test_pass",
            notes="test notes",
        )

        assert entry == mock_entry
        mock_kp.add_entry.assert_called_once()

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_add_entry_to_specific_group(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test adding entry to a specific group."""
        mock_kp = Mock()
        mock_group = Mock()
        mock_kp.find_groups.return_value = mock_group
        mock_entry = Mock()
        mock_kp.add_entry.return_value = mock_entry
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        entry = manager.add_entry(
            service="test_service",
            username="test_user",
            password="test_pass",
            group_name="TestGroup",
        )

        assert entry == mock_entry
        mock_kp.add_entry.assert_called_once()
        call_args = mock_kp.add_entry.call_args
        assert call_args.kwargs["destination_group"] == mock_group

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_find_entry_exists(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test finding an existing entry."""
        mock_kp = Mock()
        mock_entry = Mock()
        mock_kp.find_entries.return_value = [mock_entry]
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        found_entry = manager.find_entry("test_service", "test_user")

        assert found_entry == mock_entry
        mock_kp.find_entries.assert_called_once()

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_find_entry_not_exists(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test finding a non-existent entry."""
        mock_kp = Mock()
        mock_kp.find_entries.return_value = []
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        found_entry = manager.find_entry("nonexistent", "user")

        assert found_entry is None

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_update_entry(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test updating an entry."""
        mock_kp = Mock()
        mock_entry = Mock()
        mock_entry.password = "old_password"
        mock_entry.notes = "old_notes"
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        manager.update_entry(mock_entry, password="new_password", notes="new_notes")

        assert mock_entry.password == "new_password"
        assert mock_entry.notes == "new_notes"

    def test_add_entry_without_init_raises_error(self, temp_kdbx_path, test_password):
        """Test that calling add_entry without init raises error."""
        manager = KdbxManager.__new__(KdbxManager)
        manager.kp = None

        with pytest.raises(RuntimeError, match="Database not initialised"):
            manager.add_entry("service", "user", "pass")


class TestKdbxManagerPersistence:
    """Tests for database persistence."""

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_save_database(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test saving the database."""
        mock_kp = Mock()
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        manager.save()

        # save() called twice: once during init, once explicitly
        assert mock_kp.save.call_count == 2

    def test_save_without_init_raises_error(self, temp_kdbx_path, test_password):
        """Test that calling save without init raises error."""
        manager = KdbxManager.__new__(KdbxManager)
        manager.kp = None

        with pytest.raises(RuntimeError, match="Database not initialised"):
            manager.save()

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_get_entry_count(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test getting entry count."""
        mock_kp = Mock()
        mock_kp.entries = [Mock(), Mock(), Mock()]
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        count = manager.get_entry_count()

        assert count == 3

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_get_group_count(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test getting group count."""
        mock_kp = Mock()
        mock_kp.groups = [Mock(), Mock()]
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        count = manager.get_group_count()

        assert count == 2

    @patch("keyring_to_kdbx.kdbx_manager.PyKeePass")
    def test_close_database(self, mock_pykeepass, temp_kdbx_path, test_password):
        """Test closing the database."""
        mock_kp = Mock()
        mock_pykeepass.return_value = mock_kp

        manager = KdbxManager(temp_kdbx_path, test_password, create=True)
        manager.close()

        assert manager.kp is None

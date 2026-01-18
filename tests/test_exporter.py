"""Tests for exporter module."""

from unittest.mock import Mock, patch

import pytest

from keyring_to_kdbx.exporter import (
    ConflictResolution,
    ExportResult,
    GroupStrategy,
    KeyringExporter,
)
from keyring_to_kdbx.keyring_reader import KeyringEntry


@pytest.fixture
def temp_output_path(tmp_path):
    """Provide a temporary output path."""
    return tmp_path / "export.kdbx"


@pytest.fixture
def test_password():
    """Provide a test password."""
    return "export_password_123"


@pytest.fixture
def sample_keyring_entries():
    """Provide sample keyring entries for testing."""
    return [
        KeyringEntry(
            service="github.com",
            username="user1@example.com",
            password="github_pass_123",
        ),
        KeyringEntry(
            service="gitlab.com",
            username="user2@example.com",
            password="gitlab_pass_456",
        ),
        KeyringEntry(
            service="https://example.com",
            username="admin",
            password="example_pass_789",
        ),
    ]


class TestExportResult:
    """Tests for ExportResult class."""

    def test_export_result_initialization(self):
        """Test ExportResult initializes with zero counters."""
        result = ExportResult()
        assert result.added == 0
        assert result.updated == 0
        assert result.skipped == 0
        assert result.errors == 0
        assert result.total == 0

    def test_export_result_str(self):
        """Test ExportResult string representation."""
        result = ExportResult()
        result.total = 10
        result.added = 5
        result.updated = 2
        result.skipped = 2
        result.errors = 1

        result_str = str(result)
        assert "10 entries processed" in result_str
        assert "5 added" in result_str
        assert "2 updated" in result_str
        assert "2 skipped" in result_str
        assert "1 errors" in result_str


class TestKeyringExporterInit:
    """Tests for KeyringExporter initialization."""

    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_exporter_initialization(
        self, mock_reader_class, temp_output_path, test_password
    ):
        """Test exporter initializes with correct parameters."""
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader

        exporter = KeyringExporter(
            output_path=temp_output_path,
            password=test_password,
            conflict_resolution=ConflictResolution.SKIP,
            group_strategy=GroupStrategy.SERVICE,
            create_backup=True,
        )

        assert exporter.output_path == temp_output_path
        assert exporter.password == test_password
        assert exporter.conflict_resolution == ConflictResolution.SKIP
        assert exporter.group_strategy == GroupStrategy.SERVICE
        assert exporter.create_backup is True
        assert exporter.keyring_reader == mock_reader

    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_exporter_default_parameters(
        self, mock_reader_class, temp_output_path, test_password
    ):
        """Test exporter uses correct defaults."""
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader

        exporter = KeyringExporter(
            output_path=temp_output_path, password=test_password
        )

        assert exporter.conflict_resolution == ConflictResolution.SKIP
        assert exporter.group_strategy == GroupStrategy.SERVICE
        assert exporter.create_backup is False


class TestKeyringExporterExport:
    """Tests for export functionality."""

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_export_no_credentials(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test export with no credentials returns empty result."""
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = []
        mock_reader_class.return_value = mock_reader

        exporter = KeyringExporter(temp_output_path, test_password)
        result = exporter.export()

        assert result.total == 0
        assert result.added == 0
        mock_manager_class.assert_not_called()

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_export_creates_new_database(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
        sample_keyring_entries,
    ):
        """Test export creates new database when file doesn't exist."""
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = sample_keyring_entries
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None  # No existing entries
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(temp_output_path, test_password)
        result = exporter.export()

        mock_manager_class.assert_called_once_with(
            temp_output_path, test_password, create=True
        )
        assert result.total == 3
        assert result.added == 3
        assert mock_manager.add_entry.call_count == 3
        mock_manager.save.assert_called_once()

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_export_opens_existing_database(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
        sample_keyring_entries,
    ):
        """Test export opens existing database when file exists."""
        # Simulate existing file
        temp_output_path.touch()

        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = sample_keyring_entries
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(temp_output_path, test_password)
        result = exporter.export()

        mock_manager_class.assert_called_once_with(
            temp_output_path, test_password, create=False
        )
        assert result.total == 3

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_export_with_errors(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
        sample_keyring_entries,
    ):
        """Test export handles errors for individual entries."""
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = sample_keyring_entries
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None
        # First add succeeds, second fails, third succeeds
        mock_manager.add_entry.side_effect = [
            Mock(),
            Exception("Add failed"),
            Mock(),
        ]
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(temp_output_path, test_password)
        result = exporter.export()

        assert result.total == 3
        assert result.errors == 1
        assert result.added == 2


class TestConflictResolution:
    """Tests for conflict resolution strategies."""

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_conflict_resolution_skip(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test skip conflict resolution."""
        entry = KeyringEntry("service", "user", "password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_existing_entry = Mock()
        mock_manager.find_entry.return_value = mock_existing_entry
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path,
            test_password,
            conflict_resolution=ConflictResolution.SKIP,
        )
        result = exporter.export()

        assert result.skipped == 1
        assert result.added == 0
        mock_manager.add_entry.assert_not_called()
        mock_manager.update_entry.assert_not_called()

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_conflict_resolution_overwrite(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test overwrite conflict resolution."""
        entry = KeyringEntry("service", "user", "new_password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_existing_entry = Mock()
        mock_manager.find_entry.return_value = mock_existing_entry
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path,
            test_password,
            conflict_resolution=ConflictResolution.OVERWRITE,
        )
        result = exporter.export()

        assert result.updated == 1
        assert result.added == 0
        mock_manager.update_entry.assert_called_once()
        mock_manager.add_entry.assert_not_called()

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_conflict_resolution_rename(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test rename conflict resolution."""
        entry = KeyringEntry("service", "user", "password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_existing_entry = Mock()
        mock_manager.find_entry.return_value = mock_existing_entry
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path,
            test_password,
            conflict_resolution=ConflictResolution.RENAME,
        )
        result = exporter.export()

        assert result.added == 1
        assert result.updated == 0
        mock_manager.add_entry.assert_called_once()
        # Check that service name was modified
        call_kwargs = mock_manager.add_entry.call_args.kwargs
        assert "keyring" in call_kwargs["service"].lower()


class TestGroupStrategies:
    """Tests for group organisation strategies."""

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_group_strategy_flat(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test flat group strategy (no groups)."""
        entry = KeyringEntry("service", "user", "password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path,
            test_password,
            group_strategy=GroupStrategy.FLAT,
        )
        result = exporter.export()

        assert result.added == 1
        call_kwargs = mock_manager.add_entry.call_args.kwargs
        assert call_kwargs["group_name"] is None

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_group_strategy_service(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test service group strategy."""
        entry = KeyringEntry("myservice", "user", "password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path,
            test_password,
            group_strategy=GroupStrategy.SERVICE,
        )
        result = exporter.export()

        assert result.added == 1
        call_kwargs = mock_manager.add_entry.call_args.kwargs
        assert call_kwargs["group_name"] == "myservice"

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_group_strategy_domain(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test domain group strategy."""
        entry = KeyringEntry("https://www.example.com/path", "user", "password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path,
            test_password,
            group_strategy=GroupStrategy.DOMAIN,
        )
        result = exporter.export()

        assert result.added == 1
        call_kwargs = mock_manager.add_entry.call_args.kwargs
        assert call_kwargs["group_name"] == "example.com"


class TestBackupFunctionality:
    """Tests for backup functionality."""

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_create_backup_when_enabled(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test that backup is created when enabled."""
        # Create existing file
        temp_output_path.write_text("existing content")

        entry = KeyringEntry("service", "user", "password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path, test_password, create_backup=True
        )
        exporter.export()

        # Check backup was created
        backup_path = temp_output_path.with_suffix(
            temp_output_path.suffix + ".backup"
        )
        assert backup_path.exists()
        assert backup_path.read_text() == "existing content"

    @patch("keyring_to_kdbx.exporter.KdbxManager")
    @patch("keyring_to_kdbx.exporter.KeyringReader")
    def test_backup_with_incrementing_numbers(
        self,
        mock_reader_class,
        mock_manager_class,
        temp_output_path,
        test_password,
    ):
        """Test that multiple backups get incrementing numbers."""
        # Create existing file and backup
        temp_output_path.write_text("content1")
        backup1 = temp_output_path.with_suffix(
            temp_output_path.suffix + ".backup"
        )
        backup1.write_text("backup1")

        entry = KeyringEntry("service", "user", "password")
        mock_reader = Mock()
        mock_reader.get_all_credentials.return_value = [entry]
        mock_reader_class.return_value = mock_reader

        mock_manager = Mock()
        mock_manager.find_entry.return_value = None
        mock_manager_class.return_value = mock_manager

        exporter = KeyringExporter(
            temp_output_path, test_password, create_backup=True
        )
        exporter.export()

        # Check new backup was created with number
        backup2 = temp_output_path.with_suffix(
            temp_output_path.suffix + ".backup1"
        )
        assert backup2.exists()
        assert backup2.read_text() == "content1"
        assert backup1.read_text() == "backup1"  # Original backup unchanged

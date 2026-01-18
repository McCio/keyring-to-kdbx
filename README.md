# keyring-to-kdbx

Export system keyring credentials to KeePass database (KDBX) format.

[![Licence: CC0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ⚠️ AI-Generated Project

This project was created entirely through **AI-assisted "vibe-coding"** with Claude (Anthropic). All code, architecture, tests, and documentation were generated through conversational programming with an AI assistant.

**What this means:**
- Code is functional and tested, but may have edge cases
- Architecture emerged from conversation, not formal design
- This is an experiment in AI-assisted development
- Review thoroughly before production use

**Why disclose this?** Transparency about AI involvement helps users make informed decisions and contributes to understanding AI-assisted development workflows.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/McCio/keyring-to-kdbx.git
cd keyring-to-kdbx
uv sync

# Test keyring access
uv run keyring-to-kdbx export --test-keyring

# Export credentials
uv run keyring-to-kdbx export -o my-passwords.kdbx
```

**Need more help?** See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed usage instructions.

## What Does It Do?

Reads credentials from your system keyring (GNOME Keyring, macOS Keychain, Windows Credential Manager) and exports them to a password-protected KeePass database file.

**Use cases:**
- Create portable backups of system credentials
- Migrate between different keyring implementations
- Consolidate credentials into KeePass for cross-platform access
- Archive credentials before system changes

## Features

- ✅ Export from system keyring to KDBX format
- ✅ Create new or update existing KeePass databases
- ✅ Password-protected encryption (AES-256)
- ✅ **KeePassXC Secret Service integration** - Exported entries include custom attributes for seamless integration with KeePassXC's libsecret backend
- ✅ Automatic backup before modifying existing files
- ✅ Configurable conflict resolution (skip, overwrite, rename)
- ✅ Flexible organisation (flat, by-service, by-domain)
- ✅ Cross-platform support (Linux, macOS, Windows)
- ✅ CLI and programmatic API

## Development

### Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management:

```bash
# Install all dependencies (including dev tools)
uv sync --all-extras

# Run the tool
uv run keyring-to-kdbx --help
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest tests/ -v --cov

# Run specific test file
uv run pytest tests/test_exporter.py -v

# Generate HTML coverage report
uv run pytest tests/ --cov --cov-report=html
```

**Current coverage:** 66% (53 tests passing)

### Code Quality

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Format code
uv run ruff format .

# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Complete quality check
uv run ruff check . && uv run pytest tests/
```

All code must pass `ruff check` with zero errors before committing.

### Project Structure

```
keyring-to-kdbx/
├── src/keyring_to_kdbx/       # Main package
│   ├── cli.py                 # Command-line interface
│   ├── keyring_reader.py      # System keyring access
│   ├── kdbx_manager.py        # KeePass database operations
│   └── exporter.py            # Export orchestration
├── tests/                     # Test suite (pytest)
├── docs/                      # User documentation
├── examples/                  # Usage examples
└── pyproject.toml             # Project configuration
```

See [AGENTS.md](AGENTS.md) for detailed architecture documentation.

### Technology Stack

- **Python**: 3.9+ (type hints, dataclasses)
- **Package Manager**: uv (fast, modern, lockfile-based)
- **Linting/Formatting**: ruff (comprehensive, fast)
- **Testing**: pytest with coverage and mocking
- **CLI**: click (argument parsing, prompts)
- **Libraries**: keyring, pykeepass, cryptography

### Making Changes

When contributing or modifying this project:

1. **Update tests** - Add/modify tests for code changes
2. **Update docs** - Keep all `.md` files in sync
3. **Update examples** - Ensure examples remain functional
4. **Run quality checks** - `ruff check` and `pytest` must pass
5. **Update CHANGELOG** - Document user-visible changes

See [AGENTS.md](AGENTS.md) for complete maintenance directives.

## Usage Examples

### Command Line

```bash
# Basic export
uv run keyring-to-kdbx export -o passwords.kdbx

# Update existing database with backup
uv run keyring-to-kdbx export -o passwords.kdbx --update --backup

# Custom conflict resolution and grouping
uv run keyring-to-kdbx export \
  -o passwords.kdbx \
  --on-conflict overwrite \
  --group-by domain

# Test keyring access first
uv run keyring-to-kdbx export --test-keyring
```

### Programmatic API

```python
from pathlib import Path
from keyring_to_kdbx.exporter import (
    KeyringExporter,
    ConflictResolution,
    GroupStrategy,
)

# Configure export
exporter = KeyringExporter(
    output_path=Path("output.kdbx"),
    password="master_password",
    conflict_resolution=ConflictResolution.SKIP,
    group_strategy=GroupStrategy.SERVICE,
    create_backup=True,
)

# Run export
result = exporter.export()

# Check results
print(f"Exported: {result.added} entries")
print(f"Skipped: {result.skipped} duplicates")
print(f"Errors: {result.errors}")
```

Full example: [examples/export_example.py](examples/export_example.py)

## KeePassXC Integration

**This is the primary purpose of this tool:** Exported KDBX entries are fully compatible with KeePassXC's Secret Service (libsecret) integration.

### What This Means

When you enable KeePassXC as your Secret Service provider on Linux, applications using libsecret will be able to find and use the credentials exported by this tool. This creates a seamless bridge between system keyring and KeePassXC.

### How It Works

Each exported entry preserves the original Secret Service custom attributes from the keyring, which may include:
- **`service`** - The service name
- **`application`** - The application that created the credential
- **`username`** - The username (if stored as attribute)
- **`xdg:schema`** - The schema identifier
- Any other custom attributes present in the original keyring entry

These preserved attributes allow KeePassXC to match credential requests from applications when acting as a Secret Service backend, maintaining full compatibility with the original keyring behaviour.

### Typical Workflow

1. Export your system keyring credentials to KDBX:
   ```bash
   uv run keyring-to-kdbx export -o passwords.kdbx
   ```

2. Open the KDBX file in KeePassXC

3. Enable Secret Service integration in KeePassXC:
   - Go to Tools → Settings → Secret Service Integration
   - Enable "Enable KeePassXC Freedesktop.org Secret Service integration"
   - Select which database(s) to expose

4. Applications using libsecret will now query KeePassXC, which can find the exported credentials using the custom attributes

This allows you to move from platform-specific keyring storage to cross-platform KeePassXC whilst maintaining compatibility with existing applications.

## Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - User guide with examples and troubleshooting
- **[AGENTS.md](AGENTS.md)** - Architecture and maintenance guide for developers
- **[docs/AI_DEVELOPMENT.md](docs/AI_DEVELOPMENT.md)** - Details on AI-assisted development
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

## Requirements

- Python 3.9 or higher
- System keyring with credentials to export
- uv (for development)

### Supported Keyring Backends

- **Linux**: Secret Service (GNOME Keyring, KWallet)
- **macOS**: Keychain (limited enumeration support)
- **Windows**: Credential Manager (limited enumeration support)

**Note:** Not all backends support credential enumeration. The tool will warn you if your backend doesn't support listing credentials.

## Security

This tool handles sensitive credential data. Key security measures:

- **Encryption**: KDBX files encrypted with AES-256
- **File Permissions**: Automatically set to 600 (owner-only) on Unix
- **Password Safety**: No passwords logged or printed
- **Master Password**: You must provide a strong master password for KDBX
- **Backup**: Original files preserved when using `--backup`

**⚠️ Important:** Store your KDBX master password securely. It cannot be recovered if lost.

## Contributing

Contributions welcome! This is an experimental AI-generated project, so keep that context in mind.

**To contribute:**

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure quality checks pass: `uv run ruff check . && uv run pytest tests/`
5. Update documentation (README, AGENTS.md, CHANGELOG, examples)
6. Submit a pull request

**Maintenance philosophy:** Keep code simple, documentation current, and tests comprehensive. This is an AI-generated project that aims to be genuinely usable and production-ready—maintain quality and transparency.

## Licence

**CC0 1.0 Universal (Public Domain Dedication)**

This work is dedicated to the public domain. You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.

See [LICENCE](LICENCE) for full legal text.

## Acknowledgements

- **AI Development**: Claude (Anthropic) - Generated entire codebase through conversation
- **Libraries**: keyring, pykeepass, click, cryptography
- **Tools**: uv, ruff, pytest
- **Inspiration**: Need for portable keyring backups

## Known Limitations

Be aware of these current limitations:

- **Backend Support**: Not all keyring backends support credential enumeration (particularly macOS Keychain and Windows Credential Manager have limited support)
- **Metadata**: Only basic credential data exported (service, username, password)
- **Attachments**: No support for file attachments or binary data
- **Custom Fields**: Keyring custom attributes may not map to KDBX fields
- **Performance**: Large keyrings (1000+ entries) may take time to process
- **Platform-Specific**: Some features only available on Unix-like systems (e.g., file permission setting)

## Future Enhancements

Potential improvements for future versions:

1. **Selective Export**: Filter credentials by pattern or service name
2. **Incremental Sync**: Only export changed/new credentials
3. **Bidirectional Sync**: Import from KDBX back to keyring
4. **Multiple Output Formats**: CSV, JSON, 1Password, Bitwarden export
5. **GUI Interface**: Optional graphical frontend
6. **Key File Support**: KDBX encryption with key files in addition to passwords
7. **Batch Operations**: Export from multiple keyrings at once
8. **Custom Field Mapping**: Map keyring metadata to KDBX custom fields
9. **Enhanced macOS/Windows Support**: Improved credential enumeration on these platforms

## Disclaimer

**This is AI-generated software provided "as is" without warranty.** While functional and tested, it was created through conversational programming and should be reviewed before production use, especially with sensitive credential data.

Review the code, understand what it does, and ensure it meets your security requirements before using with real credentials.

## Status

- **Version**: 0.1.0
- **Status**: Functional, experimental
- **Tests**: 54 passing, 66% coverage
- **Python**: 3.9+
- **Licence**: CC0 (Public Domain)
- **Repository**: https://github.com/McCio/keyring-to-kdbx
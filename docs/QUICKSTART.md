# Quick Start Guide

Get started with keyring-to-kdbx in minutes. This guide walks you through installation, basic usage, and common scenarios.

> **Note:** This is an AI-generated project created through conversational programming with Claude. While functional and tested, review the code before using with sensitive credentials. See [README](../README.md) for details.

## What Is This?

**keyring-to-kdbx** exports credentials from your system keyring (GNOME Keyring, macOS Keychain, Windows Credential Manager) to a KeePass database file (KDBX format). This gives you portable, encrypted backups of your system credentials.

**Why use it?**
- Create backups before system changes
- Migrate credentials between systems
- Access credentials from KeePass apps on any platform
- Archive credentials in a portable format

## Installation

### Requirements

- Python 3.9 or higher
- A system keyring with stored credentials
- [uv](https://github.com/astral-sh/uv) package manager

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/McCio/keyring-to-kdbx.git
cd keyring-to-kdbx

# Install dependencies
uv sync
```

That's it! The tool is ready to use.

## First Steps

### Step 1: Test Your Keyring

Before exporting, verify that your system keyring is accessible:

```bash
uv run keyring-to-kdbx export --test-keyring
```

**What you'll see:**
- ✓ Which keyring backend is detected (GNOME Keyring, Keychain, etc.)
- ✓ Whether the backend is working
- ✓ How many credentials were found (if supported)
- ✓ Sample entries (passwords hidden)

**Common results:**
- "Found X credentials" → Your keyring supports enumeration, ready to export
- "No credentials found" → Your backend may not support enumeration (see [Troubleshooting](#troubleshooting))
- "No keyring backend available" → You need to install a keyring service (see [Troubleshooting](#troubleshooting))

### Step 2: Export Your Credentials

Export all keyring credentials to a new KeePass database:

```bash
uv run keyring-to-kdbx export -o my-passwords.kdbx
```

**What happens:**
1. You'll be prompted to create a master password
2. You'll confirm the password by typing it again
3. The tool exports all credentials
4. Results summary is displayed

**Important:** Your master password encrypts the KDBX file. Store it securely - it cannot be recovered if lost!

### Step 3: Open in KeePass

You can now open `my-passwords.kdbx` in any KeePass-compatible application:

- **Windows**: [KeePass](https://keepass.info/)
- **Linux/Mac/Windows**: [KeePassXC](https://keepassxc.org/)
- **Android**: [KeePassDX](https://www.keepassdx.com/)
- **iOS/Mac**: [Strongbox](https://strongboxsafe.com/)

Open the file and enter your master password to access your credentials.

## Common Scenarios

### Update Existing Database

Add new keyring entries to an existing KDBX file:

```bash
uv run keyring-to-kdbx export -o existing.kdbx --update
```

You'll be prompted for the existing database password. The tool will add new entries and skip duplicates by default.

### Create Backup Before Updating

Always create a backup when modifying an existing file:

```bash
uv run keyring-to-kdbx export -o my-passwords.kdbx --update --backup
```

This creates `my-passwords.kdbx.backup` before making changes. If something goes wrong, your original file is safe.

### Handle Duplicate Entries

Choose how to handle entries that already exist in the database:

```bash
# Skip duplicates (default)
uv run keyring-to-kdbx export -o output.kdbx --on-conflict skip

# Update existing entries with new passwords
uv run keyring-to-kdbx export -o output.kdbx --on-conflict overwrite

# Create new entries with modified names
uv run keyring-to-kdbx export -o output.kdbx --on-conflict rename
```

**When to use each:**
- **skip**: Safe default, preserves existing entries
- **overwrite**: When keyring has newer passwords
- **rename**: When you want to keep both versions

### Organize Entries in Groups

Control how entries are organized in KeePass:

```bash
# All entries in root (no groups)
uv run keyring-to-kdbx export -o output.kdbx --group-by flat

# Group by service name (default)
uv run keyring-to-kdbx export -o output.kdbx --group-by service

# Group by domain (extracted from service URLs)
uv run keyring-to-kdbx export -o output.kdbx --group-by domain
```

**Organisation examples:**
- **flat**: All entries at top level
- **service**: Entries grouped by service name (github.com, gitlab.com, etc.)
- **domain**: Entries grouped by domain (example.com group contains www.example.com, api.example.com, etc.)

### Complete Backup Workflow

Here's a recommended workflow for regular keyring backups:

```bash
# 1. Test keyring access
uv run keyring-to-kdbx export --test-keyring

# 2. Create initial backup
uv run keyring-to-kdbx export -o keyring-backup.kdbx --group-by service

# 3. Later, update with new credentials
uv run keyring-to-kdbx export \
  -o keyring-backup.kdbx \
  --update \
  --backup \
  --on-conflict overwrite \
  --group-by service
```

## Command Reference

### Basic Syntax

```bash
uv run keyring-to-kdbx export [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output KDBX file path | `keyring-export.kdbx` |
| `--update` | Update existing file instead of creating new | Off |
| `--backup` | Create backup before modifying existing file | Off |
| `--on-conflict [skip\|overwrite\|rename]` | How to handle duplicates | `skip` |
| `--group-by [flat\|service\|domain]` | How to organise entries | `service` |
| `--test-keyring` | Test keyring access and exit | Off |
| `-v, --verbose` | Enable verbose logging | Off |
| `--help` | Show help message | - |

### Examples

```bash
# Simple export
uv run keyring-to-kdbx export -o backup.kdbx

# Update with backup and overwrite conflicts
uv run keyring-to-kdbx export -o backup.kdbx --update --backup --on-conflict overwrite

# Flat organisation, verbose logging
uv run keyring-to-kdbx export -o backup.kdbx --group-by flat -v

# Test first, then export
uv run keyring-to-kdbx export --test-keyring
uv run keyring-to-kdbx export -o backup.kdbx
```

## Programmatic Usage

You can also use keyring-to-kdbx as a Python library:

```python
from pathlib import Path
from keyring_to_kdbx.exporter import (
    KeyringExporter,
    ConflictResolution,
    GroupStrategy,
)

# Configure the exporter
exporter = KeyringExporter(
    output_path=Path("output.kdbx"),
    password="your_master_password",
    conflict_resolution=ConflictResolution.SKIP,
    group_strategy=GroupStrategy.SERVICE,
    create_backup=True,
)

# Run the export
result = exporter.export()

# Check results
print(f"Total: {result.total}")
print(f"Added: {result.added}")
print(f"Skipped: {result.skipped}")
print(f"Errors: {result.errors}")
```

See [examples/export_example.py](../examples/export_example.py) for a complete example.

## Troubleshooting

### "No keyring backend available"

**Problem:** No system keyring service is installed or configured.

**Solution:**

- **Linux**: Install GNOME Keyring or KWallet
  ```bash
  # Ubuntu/Debian
  sudo apt install gnome-keyring
  
  # Fedora
  sudo dnf install gnome-keyring
  ```

- **macOS**: Keychain is built-in, no action needed

- **Windows**: Credential Manager is built-in, no action needed

### "No credentials found"

**Problem:** Keyring is empty or backend doesn't support enumeration.

**Possible causes:**
1. Your keyring actually has no stored credentials
2. Backend doesn't support listing credentials (common on macOS/Windows)
3. Keyring is locked and needs to be unlocked

**Solutions:**
1. Check your keyring with system tools:
   - **Linux**: `seahorse` (GNOME Keyring GUI)
   - **macOS**: Keychain Access app
   - **Windows**: Credential Manager in Control Panel

2. Unlock your keyring if needed (Linux)

3. For macOS/Windows with limited enumeration support, this is expected behaviour. The tool can only export what the backend allows.

### "Permission denied"

**Problem:** Cannot access keyring or write output file.

**Solutions:**
- Ensure keyring service is running
- Unlock your keyring (Linux)
- Check write permissions in output directory
- On Linux, try running from terminal (not SSH)

### "Incorrect password for database"

**Problem:** Wrong password when updating existing KDBX file.

**Solutions:**
- Double-check the password (it's case-sensitive)
- Ensure you're using the password for this specific KDBX file
- If forgotten, you cannot recover it (KeePass uses strong encryption)

### File Already Exists

**Problem:** Output file exists and `--update` not specified.

**Solutions:**
```bash
# Update existing file
uv run keyring-to-kdbx export -o file.kdbx --update

# Create backup first
uv run keyring-to-kdbx export -o file.kdbx --update --backup

# Use different filename
uv run keyring-to-kdbx export -o file-new.kdbx
```

### Password Too Short Warning

**Problem:** Warning about password length (< 8 characters).

**Impact:** Short passwords are less secure but still work.

**Recommendation:** Use a strong master password (12+ characters, mixed case, numbers, symbols).

## Security Best Practices

### Password Strength

Create a strong master password for your KDBX file:
- At least 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not used elsewhere
- Not based on personal information

Consider using a passphrase: "correct horse battery staple" style.

### File Protection

The KDBX file contains all your credentials:
- Store it securely (encrypted drive, secure cloud storage)
- File permissions automatically set to 600 (owner-only) on Unix
- Don't email or share unencrypted
- Keep backups in secure locations

### Master Password Storage

Your master password is critical:
- Store it in a secure password manager (if you have one)
- Write it down and store in a safe place
- Share with trusted person if needed for emergency access
- Never store it in plain text on your computer

### Regular Backups

Create regular backups with versioning:
```bash
# Use date in filename
uv run keyring-to-kdbx export -o "backup-$(date +%Y%m%d).kdbx"

# Keep old backups
uv run keyring-to-kdbx export -o backup.kdbx --update --backup
```

## Next Steps

Now that you're familiar with the basics:

1. **Read the architecture**: [AGENTS.md](../AGENTS.md) explains how the tool works
2. **Explore examples**: Check [examples/](../examples/) for more usage patterns
3. **Understand development**: [AI_DEVELOPMENT.md](AI_DEVELOPMENT.md) explains the AI-assisted approach
4. **Contribute**: See [README](../README.md) for development setup

## Getting Help

If you encounter issues:

1. **Enable verbose logging**:
   ```bash
   uv run keyring-to-kdbx -v export -o output.kdbx
   ```

2. **Test keyring access**:
   ```bash
   uv run keyring-to-kdbx export --test-keyring
   ```

3. **Check documentation**: Review this guide and [README](../README.md)

4. **Report issues**: Open an issue on GitHub with:
   - Operating system and version
   - Python version (`python --version`)
   - Error messages and verbose logs
   - Steps to reproduce

## Limitations

Be aware of these current limitations:

- **Backend Support**: Not all keyring backends support credential enumeration
- **Metadata**: Limited keyring metadata is exported (service, username, password)
- **Attachments**: No support for file attachments
- **Custom Fields**: Keyring custom attributes may not map to KDBX
- **Performance**: Large keyrings (1000+ entries) may take time

See [AGENTS.md](../AGENTS.md) "Future Enhancements" for planned improvements.

---

**Questions or feedback?** Open an issue on GitHub: https://github.com/McCio/keyring-to-kdbx
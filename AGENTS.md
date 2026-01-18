# AGENTS.md - Architecture & Maintenance Guide

> **AI-Generated Project:** This entire project was created through AI-assisted "vibe-coding" with Claude (Anthropic). All code, architecture, tests, and documentation were generated through conversational programming. This document serves as the primary reference for AI agents and developers working on this codebase.

## Purpose of This Document

This file provides:
1. **Project architecture** - How the system is structured and why
2. **Maintenance directives** - Critical rules for making changes
3. **Development guidelines** - Standards and practices to follow
4. **Context for AI agents** - Information needed for automated tooling

## Project Overview

**keyring-to-kdbx** exports credentials from system keyrings (Linux, macOS, Windows) to KeePass database files (KDBX format). It bridges the gap between platform-specific credential storage and portable password management.

### Primary Purpose

**Enable KeePassXC Secret Service integration** - The tool's main goal is to export keyring credentials in a way that KeePassXC can seamlessly use when acting as a Secret Service provider on Linux.

### Use Cases
- **KeePassXC Migration**: Export system keyring to KeePassXC while maintaining application compatibility via Secret Service
- **Backup**: Create portable backups of system keyring credentials
- **Migration**: Transfer credentials between systems or keyring implementations
- **Consolidation**: Merge keyring entries into existing KeePass databases
- **Portability**: Convert platform-locked credentials to cross-platform format

## Architecture

### Component Design

The system follows a clean separation of concerns with four main components:

```
┌─────────────────┐
│  CLI Interface  │  click-based command line (cli.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Exporter     │  Orchestration & business logic (exporter.py)
└────────┬────────┘
         │
         ├──────────────┐
         ▼              ▼
┌────────────────┐  ┌────────────────┐
│ KeyringReader  │  │  KdbxManager   │
│ (read input)   │  │ (write output) │
└────────────────┘  └────────────────┘
```

#### 1. KeyringReader (`keyring_reader.py`)
- **Purpose**: Interface with system keyring services
- **Responsibilities**:
  - Detect and initialise available keyring backend
  - Enumerate stored credentials (backend-dependent)
  - Retrieve individual credentials by service/username
  - Handle backend-specific quirks and limitations
- **Key Challenge**: Different backends (GNOME Keyring, macOS Keychain, Windows Credential Manager) have varying enumeration support

#### 2. KdbxManager (`kdbx_manager.py`)
- **Purpose**: Manage KeePass database operations
- **Responsibilities**:
  - Create new or open existing KDBX files
  - Add, update, and find entries
  - Organize entries into groups
  - Save encrypted databases with password protection
  - **Preserve Secret Service attributes** from original keyring for KeePassXC integration
- **Library**: Uses `pykeepass` for database manipulation
- **KeePassXC Integration**: Automatically preserves all original custom attributes from keyring entries as KDBX custom properties for Secret Service compatibility

#### 3. KeyringExporter (`exporter.py`)
- **Purpose**: Orchestrate the export process
- **Responsibilities**:
  - Read all keyring entries via KeyringReader
  - Apply conflict resolution strategies (skip, overwrite, rename)
  - Apply group organisation strategies (flat, service, domain)
  - Create backups if requested
  - Track and report export statistics
- **Configuration**: Accepts strategy enums for flexible behaviour

#### 4. CLI (`cli.py`)
- **Purpose**: User-facing command-line interface
- **Responsibilities**:
  - Parse command-line arguments
  - Prompt for passwords securely
  - Display progress and results
  - Handle errors gracefully
  - Set appropriate file permissions
- **Framework**: Built with `click` for clean argument handling

### Data Flow

```
System Keyring → KeyringReader.get_all_credentials()
                      ↓
                 List[KeyringEntry]
                      ↓
            KeyringExporter.export()
                      ↓
        ┌─────────────┴─────────────┐
        ▼                           ▼
  find existing entries        add new entries
        │                           │
        ▼                           ▼
  apply conflict resolution   organize into groups
        │                           │
        └─────────────┬─────────────┘
                      ▼
            KdbxManager.save()
                      ↓
                  KDBX File
```

### Key Design Decisions

1. **KeePassXC Secret Service Integration**: All entries automatically preserve original keyring attributes (such as `service`, `application`, `xdg:schema`, etc.) as KDBX custom properties for KeePassXC libsecret compatibility
2. **Strategy Pattern**: Conflict resolution and group organisation use enums, allowing runtime configuration without code changes
3. **Backend Abstraction**: KeyringReader handles multiple keyring backends transparently
4. **Immutable Entry Objects**: `KeyringEntry` dataclass prevents accidental mutation
5. **Explicit Password Handling**: Passwords never logged or printed, hidden in `__repr__`
6. **Backup Before Modify**: Optional but encouraged for data safety

## Maintenance Directives

### Critical Rules for ALL Changes

When modifying this project, you MUST follow these rules:

#### 1. Self-Documenting Directives

**Capture general instructions and approaches in documentation**:

When a general development approach, workflow instruction, or architectural decision is communicated (whether by a human developer or through AI interaction), it MUST be documented in the appropriate file(s) so it does not need to be repeated in future sessions.

**Where to document**:
- **Architecture decisions** → `AGENTS.md` (Architecture section)
- **Development workflows** → `AGENTS.md` (Development Guidelines section)
- **Maintenance rules** → `AGENTS.md` (Maintenance Directives section)
- **User-facing processes** → `README.md` or `docs/QUICKSTART.md`
- **AI development practices** → `docs/AI_DEVELOPMENT.md`

**Examples of what to capture**:
- "Always run tests before committing" → Document in Development Workflow
- "Use British English throughout" → Already documented in Context for AI Agents
- "Group similar functions together" → Document in Code Quality Standards
- "Prioritise security in credential handling" → Already documented in Security Considerations
- "Keep changes under [Unreleased] until tagged" → Already documented in CHANGELOG Versioning (Maintenance Directives)

**Purpose**: This creates a self-reinforcing documentation system where each interaction improves the project's knowledge base, reducing the need for repeated instructions and ensuring consistency across development sessions.

#### 2. Documentation Synchronization

**Update ALL documentation files** when making changes:

- **`README.md`**: Update if changing installation, usage, or development process
- **`AGENTS.md`**: Update if changing architecture, components, or directives (this file)
- **`CHANGELOG.md`**: Add entry for every user-visible change
- **`docs/QUICKSTART.md`**: Update if changing CLI commands, options, or usage
- **`docs/AI_DEVELOPMENT.md`**: Update if changing development approach or tooling

**Documentation Quality Standard**:
- All `.md` files must have **coherent, single-flow structure**
- NO "patched-up" documentation with disconnected sections
- Each document should read naturally from start to finish
- When updating, rewrite entire sections if needed to maintain coherence
- Avoid tacked-on paragraphs or inconsistent voice/style

**Verification**: Search all `.md` files for references to changed code/features and update accordingly.

#### 3. Test Coverage

**Write or update tests** for all code changes:

- New feature → New test file or test class
- Bug fix → Test that reproduces the bug, then fix
- API change → Update existing tests
- Maintain or improve coverage (currently 65%)

**Run before committing**:
```bash
uv run pytest tests/ -v --cov
```

**Test Structure**:
- `tests/test_keyring_reader.py` - Keyring access tests with mocks
- `tests/test_kdbx_manager.py` - Database operation tests
- `tests/test_exporter.py` - Integration and strategy tests

#### 4. Example Maintenance

**Keep examples functional** and aligned with API:

- `examples/export_example.py` - Must work with current API
- Add new examples for significant features
- Test examples manually after API changes

#### 5. Code Quality Standards

**Maintain quality** with automated tools:

```bash
# Format code
uv run ruff format .

# Lint (must pass with zero errors)
uv run ruff check .

# Run full check
uv run ruff check . && uv run pytest tests/
```

**Standards**:
- Type hints on all function signatures
- Docstrings on all public classes and functions
- Max line length: 100 characters
- Follow PEP 8 via ruff configuration

#### 6. Dependency Management

**When adding dependencies**:

1. Add to `pyproject.toml` under `dependencies` or `dev`
2. Run `uv sync` to update lock file
3. Document in README if user-facing
4. Consider stability (`exclude-newer = "1 week"` in effect)

#### 7. Commit Message Standards

**Follow Conventional Commits specification** for all commit messages:

Format: `<type>(<scope>): <description>`

**Common types**:
- `feat:` - New feature (triggers MINOR version bump)
- `fix:` - Bug fix (triggers PATCH version bump)
- `docs:` - Documentation changes only
- `test:` - Test additions or modifications
- `refactor:` - Code refactoring without feature/fix
- `style:` - Code style changes (formatting, etc.)
- `chore:` - Build process, dependencies, tooling
- `perf:` - Performance improvements

**Guidelines**:
- Use lowercase for type
- Keep description concise and imperative mood ("add feature" not "added feature")
- Scope is optional but recommended (e.g., `feat(kdbx): add group support`)
- Add `BREAKING CHANGE:` footer for breaking changes (triggers MAJOR version bump)
- Reference issues when relevant (e.g., `Fixes #123`)

**Examples**:
```
feat: preserve original keyring attributes for KeePassXC integration
fix: handle empty password fields correctly
docs: update KeePassXC integration workflow
test: add behavioral verification for attribute preservation
```

See: https://www.conventionalcommits.org/

#### 8. CHANGELOG Versioning

**Maintain [Unreleased] section** for all changes since the last tagged release:

- **ALWAYS** add new changes under `[Unreleased]` at the top of CHANGELOG.md
- **NEVER** create a new version section (e.g., `[0.2.0]`) without an actual git tag
- Version sections are only created when a release is tagged and published
- The `[Unreleased]` section accumulates all changes since the last tagged version

**Structure**:
```markdown
## [Unreleased]

### Added
- New feature descriptions here

### Changed
- Modified feature descriptions here

### Fixed
- Bug fix descriptions here

## [0.1.0] - 2024-01-18
(Last tagged release)
```

**When a release is made**:
1. Rename `[Unreleased]` to the new version with date
2. Add new empty `[Unreleased]` section at top
3. Update comparison links at bottom
4. This happens only when the release is actually tagged

### Change Verification Checklist

Before considering any change complete:

- [ ] General instructions captured in appropriate documentation
- [ ] All `.md` files reviewed and updated as needed
- [ ] Tests added/updated and passing (`uv run pytest tests/`)
- [ ] **Tests verify behavior, not auto-reference** (see Testing Strategy)
- [ ] **Manual testing performed if needed** (see Manual Testing section)
- [ ] Examples tested if API changed
- [ ] Ruff check passes (`uv run ruff check .`)
- [ ] Type hints added for new code
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md entry added under `[Unreleased]` section
- [ ] **Commit message follows Conventional Commits format**
- [ ] Cross-references in docs still valid
- [ ] Documentation maintains coherent structure (not patched-up)

## Development Guidelines

### Technology Stack

- **Python**: 3.9-3.13 (tested across all versions)
- **Package Manager**: uv (fast, modern, lockfile-based)
- **Linting/Formatting**: ruff (replaces black, isort, flake8, mypy)
- **Testing**: pytest with pytest-cov and pytest-mock
- **CLI Framework**: click
- **Key Libraries**: keyring, pykeepass, cryptography

### Project Structure

```
keyring-to-kdbx/
├── src/keyring_to_kdbx/       # Main package
│   ├── __init__.py            # Package exports
│   ├── __main__.py            # Module entry point
│   ├── cli.py                 # Command-line interface
│   ├── keyring_reader.py      # System keyring access
│   ├── kdbx_manager.py        # KeePass database operations
│   └── exporter.py            # Export orchestration
├── tests/                     # Test suite (pytest)
│   ├── test_keyring_reader.py # Keyring tests
│   ├── test_kdbx_manager.py   # Database tests
│   └── test_exporter.py       # Integration tests
├── examples/                  # Usage examples
│   └── export_example.py      # Programmatic usage
├── docs/                      # User documentation
│   ├── QUICKSTART.md          # Getting started guide
│   └── AI_DEVELOPMENT.md      # AI development details
├── README.md                  # Development guide
├── AGENTS.md                  # This file
├── CHANGELOG.md               # Version history
├── LICENCE                    # CC0 public domain
└── pyproject.toml             # Project configuration
```

### Development Workflow

```bash
# Setup
uv sync --all-extras

# Development cycle
uv run ruff format .           # Format
uv run ruff check .            # Lint
uv run pytest tests/ -v        # Automated tests
uv run keyring-to-kdbx --help  # Quick manual smoke test

# Before commit
uv run ruff check . && uv run pytest tests/

# Manual testing (for significant changes)
# See "Manual Testing" section below for comprehensive test scenarios
# Especially important for:
# - CLI changes
# - KeePassXC integration changes
# - Keyring backend modifications
```

### GitHub Workflows (CI/CD)

Automated workflows handle testing, releases, and dependency management:

- **CI** (`ci.yml`): Linting, testing (Python 3.9-3.13), CHANGELOG validation on every push/PR
- **Release** (`release.yml`): Automated PyPI publishing on version tags (`v*.*.*`)
- **Coverage** (`coverage.yml`): Code coverage tracking with Codecov integration
- **Dependencies** (`dependencies.yml`): Weekly security audits and outdated package monitoring
- **Dependabot**: Automated dependency update PRs (minor/patch versions only)

**Key requirements**:
- Commit messages follow Conventional Commits format
- CHANGELOG updated under `[Unreleased]` for all changes
- Version in `pyproject.toml` matches git tag for releases

**See**: `.github/QUICK_REFERENCE.md` for commands and troubleshooting.

### Security Considerations

**Critical security aspects**:

1. **Password Protection**: All KDBX files are encrypted with user-provided master password
2. **File Permissions**: Automatically set to 600 (owner-only) on Unix systems
3. **Memory Safety**: Passwords should not persist in logs or error messages
4. **Backup Safety**: Original KDBX files preserved before modification
5. **Input Validation**: All user inputs validated before processing

**When handling credentials**:
- Never log passwords or sensitive data
- Use `hide_input=True` in click prompts
- Override `__repr__` to hide passwords
- Clear sensitive data from memory when done (where possible)

### Testing Strategy

**Test Philosophy - Behavior Over Auto-Referencing**:

Tests MUST verify actual behavior, not just that code was called. Avoid "auto-referencing" tests that simply verify Python's basic functionality (assignment, dataclasses, etc.) or that mocks were called without checking logic.

**Good tests**:
- Verify business logic and decision-making
- Check that edge cases are handled correctly
- Ensure security properties (e.g., password hiding)
- Validate data transformations (e.g., domain extraction)
- Confirm error handling behavior (returns None vs raises exception)

**Bad tests (auto-referencing)**:
- Testing that setting a value makes it equal to that value
- Testing that calling a method results in that method being called
- Testing Python's built-in functionality (dataclass creation, etc.)
- Tests where all behavior is mocked with no logic verification

**Test pyramid**:
- **Unit tests**: Test individual components in isolation with mocks
- **Integration tests**: Test component interactions
- **Manual tests**: CLI functionality, real keyring/KDBX operations

**Mocking approach**:
- Mock `keyring` module for predictable tests
- Mock `PyKeePass` for database operations
- Use `tmp_path` fixture for file operations
- Avoid actual system keyring access in automated tests
- **Always verify behavior**, not just that mocks were called

**Examples of good behavioral tests**:
- `test_keyring_entry_repr_hides_password` - Verifies password hiding logic
- `test_conflict_resolution_skip` - Verifies skip logic (skipped count increases, no adds)
- `test_group_strategy_domain` - Verifies domain extraction (checks "example.com" extracted)
- `test_get_credential_returns_none_not_exception` - Verifies error handling approach
- `test_test_backend_verifies_round_trip` - Verifies all three operations occur

### Manual Testing

**Critical: Data Safety First**

Manual testing involves real system keyrings and actual KDBX files. If you're using KeePassXC with Secret Service integration or have other systems relying on your keyring, follow these safety precautions to prevent data loss.

#### Pre-Testing Safety Checklist

Before any manual testing:

1. **Backup your existing KeePassXC database**:
   ```bash
   cp ~/.config/KeePassXC/passwords.kdbx ~/.config/KeePassXC/passwords.kdbx.backup-$(date +%Y%m%d)
   ```

2. **Disable KeePassXC Secret Service integration** (if active):
   - Open KeePassXC → Tools → Settings → Secret Service Integration
   - Uncheck "Enable KeePassXC Freedesktop.org Secret Service integration"
   - Click OK
   - **Important**: This prevents applications from accessing KeePassXC during testing

3. **Close KeePassXC completely**:
   - File → Quit (or Ctrl+Q)
   - Verify it's not running in system tray
   - Check process list: `ps aux | grep keepassxc` (should show nothing)

4. **Note your keyring state**:
   ```bash
   # On Linux with GNOME Keyring
   secret-tool search --all | wc -l  # Count entries
   
   # Or open Seahorse to see current state
   seahorse &
   ```

5. **Create a test directory**:
   ```bash
   mkdir -p ~/keyring-to-kdbx-testing
   cd ~/keyring-to-kdbx-testing
   ```

#### Manual Test Scenarios

**Scenario 1: First-Time Export (New KDBX)**

Tests basic export functionality with a new database.

```bash
# 1. Test keyring access
uv run keyring-to-kdbx export --test-keyring

# Expected output:
# - Keyring backend detected (e.g., "SecretService Keyring")
# - Number of credentials found (or message about enumeration support)
# - Sample entries listed (passwords hidden)

# 2. Export to new file
uv run keyring-to-kdbx export -o test-export.kdbx --group-by service

# Expected behavior:
# - Prompt for master password (twice)
# - Progress messages
# - Summary: "Total: X, Added: X, Skipped: 0, Errors: 0"
# - File created with 600 permissions (Linux/macOS)

# 3. Verify the KDBX file
ls -lh test-export.kdbx  # Should exist, ~few KB minimum
file test-export.kdbx    # Should show "Keepass password database"

# 4. Open in KeePassXC (DO NOT enable Secret Service yet)
keepassxc test-export.kdbx

# Verify:
# - Database opens with your master password
# - Entries are organized by service (groups visible)
# - Usernames and passwords are correct
# - Custom attributes preserved (right-click entry → Properties → Advanced)
# - Look for attributes like "service", "application", "xdg:schema"
```

**Scenario 2: Update Existing KDBX (Conflict Resolution)**

Tests adding entries to an existing database with conflict handling.

```bash
# 1. Create initial export
uv run keyring-to-kdbx export -o update-test.kdbx --group-by flat

# 2. Open in KeePassXC and modify an entry
keepassxc update-test.kdbx
# Change a password, add a note, then save and close

# 3. Test skip mode (default)
uv run keyring-to-kdbx export -o update-test.kdbx --update --on-conflict skip

# Expected:
# - Prompt for existing database password
# - Summary shows skipped entries (existing ones)
# - Modified entry in KeePassXC remains unchanged

# 4. Create backup, then test overwrite mode
cp update-test.kdbx update-test.kdbx.manual-backup
uv run keyring-to-kdbx export -o update-test.kdbx --update --on-conflict overwrite --backup

# Expected:
# - Creates update-test.kdbx.backup automatically
# - Overwrites existing entries with keyring versions
# - Manual modifications lost (expected behavior)

# 5. Test rename mode
uv run keyring-to-kdbx export -o update-test.kdbx --update --on-conflict rename

# Expected:
# - Creates entries with "_1", "_2" suffixes for conflicts
# - Both original and new entries present
```

**Scenario 3: Group Organization Strategies**

Tests different entry organization methods.

```bash
# 1. Flat organization (no groups)
uv run keyring-to-kdbx export -o test-flat.kdbx --group-by flat
keepassxc test-flat.kdbx
# Verify: All entries at root level, no groups

# 2. Service organization (default)
uv run keyring-to-kdbx export -o test-service.kdbx --group-by service
keepassxc test-service.kdbx
# Verify: Groups named after service values (e.g., "github.com", "gitlab.com")

# 3. Domain organization
uv run keyring-to-kdbx export -o test-domain.kdbx --group-by domain
keepassxc test-domain.kdbx
# Verify: Groups by domain (e.g., "example.com" contains www.example.com, api.example.com)
```

**Scenario 4: KeePassXC Secret Service Integration**

Tests full integration workflow - the primary use case.

**⚠️ Critical: Only do this with test data or after backups**

```bash
# 1. Export keyring to a dedicated KDBX for Secret Service
uv run keyring-to-kdbx export -o ~/keepassxc-secretservice.kdbx --group-by service

# 2. Open in KeePassXC
keepassxc ~/keepassxc-secretservice.kdbx

# 3. Enable Secret Service integration
# - Tools → Settings → Secret Service Integration
# - Check "Enable KeePassXC Freedesktop.org Secret Service integration"
# - Check "Expose entries under this group" → Select root or specific group
# - Click OK

# 4. Test with a Secret Service client
# Install a test credential (won't conflict with export)
secret-tool store --label="Test KeePassXC Integration" service test-service username testuser
# When prompted, enter a test password

# 5. Retrieve via Secret Service
secret-tool lookup service test-service username testuser
# Expected: Returns the password you just stored

# 6. Test lookup of exported credential
# Pick a service/username from your export
secret-tool lookup service "github.com" username "your-github-user"
# Expected: Returns the password from your exported KDBX

# 7. Verify in KeePassXC
# Open the database, find the entry
# Right-click → Properties → Advanced
# Verify custom properties: service, username, application, xdg:schema, etc.

# 8. Test application integration
# Open an application that uses libsecret (e.g., Git credential helper)
# It should find credentials from KeePassXC database

# 9. Monitor Secret Service activity (optional)
dbus-monitor --session "destination=org.freedesktop.secrets"
# Run in another terminal while testing to see Secret Service calls
```

**Scenario 5: Error Handling and Edge Cases**

Tests error conditions and recovery.

```bash
# 1. Test with no keyring access (simulate locked keyring)
# On Linux, lock your keyring in Seahorse, then:
uv run keyring-to-kdbx export --test-keyring
# Expected: Error message about keyring access

# 2. Test with wrong password on update
echo "test" > existing.kdbx  # Create invalid file
uv run keyring-to-kdbx export -o existing.kdbx --update
# Expected: Error about invalid KDBX or password

# 3. Test with no write permissions
uv run keyring-to-kdbx export -o /root/no-permission.kdbx
# Expected: Permission denied error

# 4. Test with very weak password
uv run keyring-to-kdbx export -o weak-pw.kdbx
# Enter "123" as password
# Expected: Warning about weak password, but still works

# 5. Test verbose logging
uv run keyring-to-kdbx export -o test.kdbx -v
# Expected: Detailed progress messages, entry processing logs
```

#### Post-Testing Restoration

After testing, restore your normal environment:

1. **Remove test files**:
   ```bash
   cd ~/keyring-to-kdbx-testing
   rm -f *.kdbx *.backup
   cd ~
   rm -rf ~/keyring-to-kdbx-testing
   ```

2. **Re-enable KeePassXC Secret Service** (if you use it):
   - Open KeePassXC
   - Load your production database
   - Tools → Settings → Secret Service Integration
   - Enable and configure as before
   - Click OK

3. **Verify your production setup**:
   ```bash
   # Test that applications can access credentials
   secret-tool lookup service "your-service" username "your-username"
   ```

4. **Restore from backup if needed**:
   ```bash
   # Only if something went wrong
   cp ~/.config/KeePassXC/passwords.kdbx.backup-YYYYMMDD ~/.config/KeePassXC/passwords.kdbx
   ```

#### Manual Testing Checklist

Before declaring manual testing complete:

- [ ] Basic export to new KDBX successful
- [ ] KDBX file opens in KeePassXC with correct password
- [ ] Entries contain expected usernames and passwords
- [ ] Custom attributes preserved (service, application, etc.)
- [ ] Update mode adds new entries without duplicating
- [ ] Conflict resolution strategies work (skip, overwrite, rename)
- [ ] Backup creation works when specified
- [ ] All group strategies produce correct organization (flat, service, domain)
- [ ] KeePassXC Secret Service integration can retrieve exported credentials
- [ ] Applications using libsecret can access credentials via KeePassXC
- [ ] Error handling works (wrong password, no permissions, etc.)
- [ ] File permissions set correctly (600 on Unix)
- [ ] No data loss in production KeePassXC database
- [ ] Production Secret Service integration restored and working

#### Troubleshooting Manual Tests

**KeePassXC won't expose entries via Secret Service**:
- Check that "Expose entries under this group" is set
- Verify entries have required attributes (service, username)
- Try exposing the root group instead of specific groups
- Restart KeePassXC after changing settings

**secret-tool can't find credentials**:
- Verify KeePassXC database is unlocked
- Check Secret Service integration is enabled in KeePassXC
- Ensure search attributes match entry properties exactly
- Use `dbus-monitor` to see if requests reach KeePassXC

**Entries missing attributes**:
- Re-export with verbose logging: `-v`
- Check that keyring backend provides attributes (use `--test-keyring`)
- Some backends (macOS, Windows) may have limited attribute support

**Applications can't access credentials**:
- Verify application uses libsecret (not KWallet or other)
- Check application's credential search attributes
- May need to restart application after enabling Secret Service

### Error Handling

**Principles**:
- Catch specific exceptions, not bare `except:`
- Provide helpful error messages with context
- Log errors at appropriate levels
- Fail fast on configuration errors
- Graceful degradation where possible

**Example**:
```python
try:
    password = keyring.get_password(service, username)
    if not password:
        logger.warning(f"No password found for {service}/{username}")
        return None
except KeyringError as e:
    logger.error(f"Keyring access failed: {e}")
    raise RuntimeError("Cannot access system keyring") from e
```

## Configuration

### Runtime Configuration

- **Output path**: `-o/--output` (default: `keyring-export.kdbx`)
- **Update mode**: `--update` flag (open existing vs create new)
- **Backup**: `--backup` flag (backup before modify)
- **Conflict resolution**: `--on-conflict` (skip, overwrite, rename)
- **Group strategy**: `--group-by` (flat, service, domain)

### Build Configuration

**pyproject.toml** contains:
- Dependencies and version constraints
- Ruff configuration (linting rules, formatting)
- Pytest configuration (coverage, markers)
- Package metadata (version, licence, classifiers)
- Entry points for CLI (`keyring-to-kdbx` command)

**Key settings**:
- `exclude-newer = "1 week"` - Avoid unstable new releases
- Line length: 100 characters
- Python: 3.9+ required
- Licence: CC0-1.0 (public domain)

## Context for AI Agents

This project is:
- A **practical tool** for keyring backup and migration
- An **AI-generated codebase** created through conversational programming with Claude (Anthropic)
- A **production-ready utility** that aims to be genuinely usable, not just a demonstration

**Language Convention**: This project uses **British English** throughout all documentation and code comments (initialise, organise, licence, etc.). Maintain this consistency in all contributions.

**When working with this codebase**:
- Respect the existing architecture
- Maintain documentation quality and British English spelling
- Keep tests comprehensive
- Follow security best practices
- Update all affected files for any change

**Remember**: This is public domain software (CC0). Anyone can use, modify, and redistribute without restriction. Maintain quality and transparency as an AI-generated project that aims for real-world usability.

## Resources

- **Repository**: https://github.com/McCio/keyring-to-kdbx
- **Python Docs**: https://docs.python.org/3/
- **uv**: https://github.com/astral-sh/uv
- **ruff**: https://github.com/astral-sh/ruff
- **keyring**: https://github.com/jaraco/keyring
- **pykeepass**: https://github.com/libkeepass/pykeepass
- **KeePass**: https://keepass.info/
- **KeePassXC**: https://keepassxc.org/
- **KeePassXC Secret Service Integration**: https://keepassxc.org/docs/KeePassXC_GettingStarted.html#_secret_service_integration
- **Secret Service API**: https://specifications.freedesktop.org/secret-service/
- **Conventional Commits**: https://www.conventionalcommits.org/
- **GitHub Actions**: https://docs.github.com/en/actions

---

**Last Updated**: 2024-01-18  
**Version**: 0.1.0  
**AI Assistant**: Claude (Anthropic)
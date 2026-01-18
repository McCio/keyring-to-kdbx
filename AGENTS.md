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

### Change Verification Checklist

Before considering any change complete:

- [ ] General instructions captured in appropriate documentation
- [ ] All `.md` files reviewed and updated as needed
- [ ] Tests added/updated and passing (`uv run pytest tests/`)
- [ ] **Tests verify behavior, not auto-reference** (see Testing Strategy)
- [ ] Examples tested if API changed
- [ ] Ruff check passes (`uv run ruff check .`)
- [ ] Type hints added for new code
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md entry added
- [ ] **Commit message follows Conventional Commits format**
- [ ] Cross-references in docs still valid
- [ ] Documentation maintains coherent structure (not patched-up)

## Development Guidelines

### Technology Stack

- **Python**: 3.9+ (for modern type hints and features)
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
uv run pytest tests/ -v        # Test
uv run keyring-to-kdbx --help  # Manual test

# Before commit
uv run ruff check . && uv run pytest tests/
```

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

---

**Last Updated**: 2024-01-18  
**Version**: 0.1.0  
**AI Assistant**: Claude (Anthropic)
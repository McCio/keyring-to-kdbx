# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Export credentials from system keyring to KeePass KDBX format
- Custom attribute preservation - All original keyring metadata mapped to KDBX custom properties (enables KeePassXC Secret Service integration)
- Support for Linux (GNOME Keyring, KWallet), macOS (Keychain), and Windows (Credential Manager)
- Support for SecretService backends using `get_preferred_collection()` method for credential enumeration
- Create new or update existing KDBX databases
- Three conflict resolution strategies: skip, overwrite, rename
- Three group organisation strategies: flat, by-service, by-domain
- Automatic backup of existing KDBX files before modification
- Password-protected KDBX encryption with AES-256
- **KeePassXC Secret Service integration** - Exported entries preserve all original keyring attributes (such as `service`, `application`, `xdg:schema`, etc.) as KDBX custom properties for seamless integration with KeePassXC's libsecret backend
- Command-line interface with comprehensive options
- Programmatic Python API for automation
- 55 unit tests with 67% code coverage focused on behavioral verification
- Example scripts for programmatic usage
- Comprehensive documentation including:
  - README.md - Development guide and project overview
  - AGENTS.md - Architecture, maintenance directives, and comprehensive manual testing guide for developers
  - QUICKSTART.md - User guide with safe testing instructions and KeePassXC integration workflow
  - Testing philosophy emphasizing behavior verification over auto-referencing
  - Self-documenting directives system for capturing general instructions
  - CHANGELOG versioning directive to ensure changes remain under `[Unreleased]` until tagged

### Security

- Password-protected KDBX encryption with user-provided master password
- Automatic file permission setting (600) on Unix-like systems
- Password masking in logs and string representations

### Development

- AI-generated codebase created through conversational programming with Claude (Anthropic)
- Production-ready utility that aims to be genuinely usable
- Complete transparency about AI-assisted development approach
- British English used throughout documentation and code
- Modern Python tooling: uv, ruff, pytest
- Type hints throughout codebase
- Public domain dedication under CC0 1.0 Universal licence
- Python 3.10-3.13 support with comprehensive testing across all versions
- GitHub Actions CI/CD workflows:
  - Automated linting and testing (Python 3.10-3.13)
  - Automated PyPI releases on version tags
  - Code coverage tracking with Codecov
  - Weekly dependency security audits
  - Dependabot for automated dependency updates

[Unreleased]: https://github.com/McCio/keyring-to-kdbx/commits/HEAD
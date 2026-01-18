# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-18

### Added

- Export credentials from system keyring to KeePass KDBX format
- Support for Linux (GNOME Keyring, KWallet), macOS (Keychain), and Windows (Credential Manager)
- Create new or update existing KDBX databases
- Three conflict resolution strategies: skip, overwrite, rename
- Three group organisation strategies: flat, by-service, by-domain
- Automatic backup of existing KDBX files before modification
- Password-protected KDBX encryption with AES-256
- Command-line interface with comprehensive options
- Programmatic Python API for automation
- 47 unit tests with 65% code coverage
- Comprehensive documentation (README, AGENTS, QUICKSTART)
- Example scripts for programmatic usage

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

[Unreleased]: https://github.com/McCio/keyring-to-kdbx/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/McCio/keyring-to-kdbx/releases/tag/v0.1.0
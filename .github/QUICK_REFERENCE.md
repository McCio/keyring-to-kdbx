# CI/CD Quick Reference

Quick commands and checklists for daily development tasks.

## 📋 Before Every Commit

```bash
# Format, lint, and test
uv run ruff format .
uv run ruff check .
uv run pytest tests/ -v

# Quick check (before git push)
uv run ruff check . && uv run pytest tests/
```

## ✅ Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

git commit -m "feat: add new export feature"
git commit -m "fix(kdbx): handle empty password fields"
git commit -m "docs: update installation guide"
git commit -m "test: add behavioral verification"
git commit -m "chore(deps): update keyring to v24.0"
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`, `perf`, `build`, `ci`

## 📝 CHANGELOG

Always add changes under `[Unreleased]`:

```markdown
## [Unreleased]

### Added
- New features

### Changed  
- Modifications

### Fixed
- Bug fixes
```

Never create version sections until actually tagging a release.

## 🚀 Release Process

```bash
# 1. Update version in pyproject.toml
version = "0.2.0"

# 2. Rename [Unreleased] to [0.2.0] - 2024-01-19 in CHANGELOG.md

# 3. Commit and tag
git add pyproject.toml CHANGELOG.md
git commit -m "chore: prepare release v0.2.0"
git tag v0.2.0
git push origin main --tags

# 4. GitHub Actions automatically:
#    - Runs tests
#    - Builds package
#    - Publishes to PyPI
#    - Creates GitHub release
```

## 🔍 GitHub Actions

View workflow status:

```bash
gh run list              # Recent runs
gh run view <id>         # Specific run details
gh run watch             # Watch live
gh run rerun <id>        # Retry failed run
```

## 🧪 Local Coverage

```bash
# Generate HTML report
uv run pytest tests/ --cov --cov-report=html

# Open report
open htmlcov/index.html        # macOS
xdg-open htmlcov/index.html    # Linux
```

## 🔐 Dependencies

```bash
# Check outdated packages
uv pip list --outdated

# Update and lock
uv pip install --upgrade <package>
uv lock

# Security audit (install first)
uv pip install pip-audit
uv run pip-audit
```

**Note**: Dependabot creates weekly PRs for minor/patch updates automatically.

## 🐛 Troubleshooting

### Lint failures

```bash
uv run ruff format .           # Auto-fix formatting
uv run ruff check --fix .      # Auto-fix some issues
```

### Test failures

```bash
uv run pytest tests/ -v -s     # Verbose output
uv run pytest tests/test_file.py::test_name -v  # Specific test
uv run pytest tests/ --pdb     # Debug mode
```

### Coverage dropped

```bash
# Find uncovered lines
uv run pytest tests/ --cov --cov-report=term-missing

# Add tests (coverage must not drop >10%)
```

## 📚 Documentation

Update relevant files when changing code:
- `README.md` - User-facing changes
- `AGENTS.md` - Architecture/directives  
- `docs/QUICKSTART.md` - CLI/usage
- `CHANGELOG.md` - All changes (required)

## 🔧 Workflows

Files in `.github/workflows/`:
- `ci.yml` - Lint, test (Python 3.9-3.13), validate (runs on every push/PR)
- `release.yml` - Automated PyPI publishing (runs on version tags)
- `coverage.yml` - Coverage tracking with Codecov
- `dependencies.yml` - Weekly security audits

## 🆘 Resources

- Project architecture: `AGENTS.md`
- User guide: `docs/QUICKSTART.md`
- Conventional Commits: https://www.conventionalcommits.org/
- GitHub Actions: https://docs.github.com/en/actions
# Contributing to Refactor

Thank you for your interest in contributing to the Refactor plugin for Claude Code.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

## Local Development Setup

```bash
# Clone the repository
git clone https://github.com/zircote/refactor.git
cd refactor

# Install dev dependencies (creates .venv automatically)
uv sync --extra dev

# Verify your setup
make check
```

## Development Workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes** in the `scripts/` directory (source code) or `skills/` directory (skill definitions).

3. **Run checks before committing**:
   ```bash
   make check    # runs lint + typecheck + test
   ```

4. **Submit a pull request** against `main`.

## Project Structure

```
refactor/
├── scripts/          # Python source code (assessment, test running, utilities)
├── skills/           # Skill markdown files (refactor, feature-dev, test-architect, etc.)
├── agents/           # Agent definition files
├── commands/         # CLI command definitions
├── tests/            # Test suite (pytest + hypothesis)
├── evals/            # Evaluation suites
├── docs/             # Documentation
├── hooks/            # Claude Code hooks
├── references/       # Reference materials for skills
└── .github/          # CI/CD workflows
```

## Running Tests

```bash
make test             # Run full test suite with coverage
make test-quick       # Run tests without coverage
make coverage         # Run tests and show coverage report
```

## Code Quality

This project enforces strict quality standards via CI:

- **Linting**: [ruff](https://docs.astral.sh/ruff/) with select rules (E, F, W, I, N, UP, B, A, SIM, TCH)
- **Formatting**: ruff format (double quotes, 100 char line length)
- **Type checking**: [mypy](https://mypy-lang.org/) in strict mode
- **Security**: [bandit](https://bandit.readthedocs.io/) SAST + [pip-audit](https://pypi.org/project/pip-audit/) dependency scanning
- **Testing**: [pytest](https://docs.pytest.org/) with branch coverage (minimum 80%), [hypothesis](https://hypothesis.readthedocs.io/) for property-based testing

```bash
make lint             # Run ruff check
make format           # Auto-format with ruff
make typecheck        # Run mypy
make security         # Run bandit + pip-audit
```

## Commit Conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `refactor:` — Code restructuring
- `test:` — Test additions or changes
- `chore:` — Build/CI changes
- `perf:` — Performance improvements

## Pull Request Guidelines

- Keep PRs focused on a single concern
- Ensure all CI checks pass before requesting review
- Update `CHANGELOG.md` for user-facing changes
- Add tests for new functionality

## Reporting Issues

Please file issues on the [GitHub issue tracker](https://github.com/zircote/refactor/issues) with:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS)

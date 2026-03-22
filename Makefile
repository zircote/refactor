.PHONY: help setup lint format typecheck test test-quick coverage security check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install dev dependencies
	uv sync --extra dev

lint: ## Run linter (ruff check)
	uv run ruff check scripts/ tests/

format: ## Auto-format code (ruff format)
	uv run ruff format scripts/ tests/
	uv run ruff check --fix scripts/ tests/

typecheck: ## Run type checker (mypy strict)
	uv run mypy scripts/

test: ## Run tests with coverage
	uv run pytest --cov=scripts --cov-report=term-missing --cov-branch

test-quick: ## Run tests without coverage
	uv run pytest -x -q

coverage: ## Run tests and generate coverage report
	uv run pytest --cov=scripts --cov-report=term-missing --cov-report=html --cov-branch

security: ## Run security scans (bandit + pip-audit)
	uv run pip-audit
	uv run bandit -r scripts/ -c pyproject.toml

check: lint typecheck test security ## Run all checks (lint + typecheck + test + security)

clean: ## Remove build artifacts
	rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage htmlcov .hypothesis
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

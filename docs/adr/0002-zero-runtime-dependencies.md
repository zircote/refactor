# ADR-0002: Zero Runtime Dependencies

## Status

Accepted

## Context

The refactor plugin is a Claude Code plugin that orchestrates other tools (pytest, ruff, mypy). It needs to be lightweight and minimize supply chain risk.

## Decision

Maintain zero runtime dependencies. All dependencies are dev-only (testing, linting, type checking, security scanning). The plugin's Python code uses only the standard library.

## Consequences

- **Positive**: Zero supply chain attack surface at runtime, trivial installation, no version conflicts with host projects
- **Negative**: Cannot use third-party libraries for convenience (e.g., rich for formatting, click for CLI)
- **Mitigations**: Standard library is sufficient for the plugin's needs (subprocess, json, pathlib, typing)

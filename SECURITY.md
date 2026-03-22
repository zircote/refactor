# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.x     | Yes                |
| < 2.0   | No                 |

## Security Model

The refactor plugin operates as a local Claude Code plugin with the following security characteristics:

- **Zero runtime dependencies**: No third-party code executes at runtime, eliminating supply chain risk
- **Local execution only**: All operations run on the local machine; no network calls from plugin code
- **Subprocess isolation**: External tools (pytest, ruff, mypy) are invoked via subprocess with explicit timeouts
- **No secrets handling**: The plugin does not process, store, or transmit credentials or sensitive data

## Automated Security Scanning

Every CI run includes:
- **pip-audit**: Scans dev dependencies for known CVEs
- **bandit**: Static analysis for common Python security issues (B101 skipped for test assertions)
- **Dependabot**: Weekly automated dependency update PRs

## Reporting a Vulnerability

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email the maintainer or use [GitHub's private vulnerability reporting](https://github.com/zircote/refactor/security/advisories/new)
3. Include: description, reproduction steps, potential impact
4. Expect a response within 72 hours

## Security Review Process

Changes affecting the following areas require explicit security consideration in the PR description:
- Subprocess invocation patterns
- File system operations
- Configuration parsing
- New dependency additions

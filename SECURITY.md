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

## Incident Response

### Severity Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Remote code execution, supply chain compromise | 24 hours |
| High | Data exposure, privilege escalation | 72 hours |
| Medium | Denial of service, information disclosure | 1 week |
| Low | Minor issues, hardening improvements | Next release |

### Response Process

1. **Triage**: Confirm vulnerability, classify severity
2. **Contain**: If applicable, issue advisory and recommend workaround
3. **Fix**: Develop and test patch on private branch
4. **Release**: Publish patched version, update advisory
5. **Postmortem**: Document root cause and preventive measures in docs/adr/

## Security Review Process

Changes affecting the following areas require explicit security consideration in the PR description:
- Subprocess invocation patterns
- File system operations
- Configuration parsing
- New dependency additions

Security-sensitive paths are marked in `.github/CODEOWNERS` for mandatory review.

## Deprecation Policy

When deprecating features or changing behavior:

1. **Announce**: Add deprecation notice to CHANGELOG.md and relevant docs
2. **Warn**: Emit deprecation warnings for at least one minor version
3. **Migrate**: Provide migration guidance in release notes
4. **Remove**: Remove deprecated functionality in the next major version

Breaking changes follow [Semantic Versioning](https://semver.org/): breaking changes require a major version bump.

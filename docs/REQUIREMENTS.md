# Requirements Specification

## Product Overview

**Refactor** is a Claude Code plugin that provides automated code refactoring, feature development, and test generation through swarm-orchestrated specialist agents.

## Target Users

- Software engineers using Claude Code who need to refactor existing codebases
- Developers building new features with AI-assisted architecture and implementation
- Teams wanting automated test suite generation with scientific rigor

## Core Capabilities

### 1. Automated Refactoring (`/refactor`)

**Goal**: Improve existing code quality through iterative analysis and modification.

**Acceptance Criteria**:
- Discovers codebase structure via deep exploration
- Reviews code with confidence-scored findings (bugs, security, quality)
- Implements improvements while preserving all existing tests
- Runs in autonomous mode with convergence detection

### 2. Feature Development (`/feature-dev`)

**Goal**: Build new features with multi-perspective architecture design.

**Acceptance Criteria**:
- Explores codebase to understand patterns and conventions
- Designs architecture from multiple perspectives (security, performance, maintainability)
- Implements code following established project patterns
- Reviews implementation for quality before completion

### 3. Test Generation (`/test-architect`)

**Goal**: Generate scientifically grounded test suites.

**Acceptance Criteria**:
- Uses equivalence class partitioning and boundary value analysis
- Generates mutation-aware assertions (TDD red phase)
- Reviews test rigor against formal testing criteria
- Analyzes and improves code coverage

### 4. Git Workflow Commands

| Command | Goal | Acceptance Criteria |
|---------|------|-------------------|
| `/pr` | Create pull requests | Draft PR with description, linked issues |
| `/cp` | Commit and push | Stage, commit, push with conventional message |
| `/fr` | Fetch and rebase | Clean rebase onto remote tracking branch |
| `/ff` | Fast-forward merge | Update branch without merge commits |
| `/sync` | Full sync cycle | Fetch, rebase, push in one command |
| `/pr-fix` | Fix PR feedback | Triage comments, fix, reply, push |

## Non-Goals

The following are explicitly **out of scope**:

- **IDE integration**: This is a CLI plugin, not an IDE extension. IDE features are handled by Claude Code itself.
- **Language-specific AST manipulation**: The plugin orchestrates tools (ruff, pytest, mypy) rather than implementing language parsers.
- **Cloud deployment**: No server component, no hosted service, no API endpoints.
- **Multi-user collaboration**: Designed for single-user CLI workflows.
- **Backward compatibility with pre-2.0**: Version 1.x is unsupported; no migration tooling provided.

## Edge Cases and Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Project has no tests | Report detection failure, suggest test framework |
| Unsupported language | Raise `UnsupportedLanguageError` with supported list |
| Subprocess timeout | Raise `SubprocessError` after 300s (tests) / 600s (coverage) |
| Malformed coverage output | Return error dict with `coverage_pct: 0.0` |
| Empty project directory | `detect_project` returns `null` framework with low confidence |
| Git conflicts during refactoring | Abort iteration, restore from snapshot |
| Convergence plateau | Stop after 5 consecutive no-improvement iterations |

## Feature Flag Strategy

This project uses **branch-based feature delivery** rather than runtime feature flags:

- **New features**: Developed on feature branches, merged via PR after CI passes
- **Experimental features**: Gated by skill availability — new skills are added as separate files and registered in the plugin manifest only when ready
- **Rollback**: Achieved via `rollback.yml` workflow (revert to prior tagged release) or git revert

Runtime feature flags are not applicable to this CLI plugin architecture. Behavior variations are controlled by skill configuration files (`.claude/refactor.config.json`).

## Migration and Rollback

### Version Migration

- **Minor versions** (2.x → 2.y): Backward compatible. No migration needed.
- **Major versions** (2.x → 3.0): Breaking changes documented in CHANGELOG.md with migration guide.
- **Config changes**: New config keys get defaults; removed keys are silently ignored.

### Rollback Procedure

1. **Automated**: `.github/workflows/rollback.yml` — workflow_dispatch with target tag
   - Validates tag exists
   - Runs full test suite against target version
   - Promotes target tag to new GitHub Release
2. **Manual**: `git checkout v{version}` in the plugin directory

### External Dependencies

| Dependency | Owner | Purpose | Risk |
|-----------|-------|---------|------|
| Claude Code CLI | Anthropic | Host platform | Plugin API stability |
| GitHub Actions | GitHub | CI/CD platform | Workflow syntax changes |
| PyPI (dev deps) | PSF | Dev tooling source | Supply chain (mitigated by pip-audit) |

## Non-Functional Requirements

### Quality

- Minimum 80% test coverage (enforced in CI)
- Strict type checking via mypy
- Zero linting errors (ruff)
- No known security vulnerabilities (bandit + pip-audit)

### Performance

- Test suite completes in under 60 seconds
- All subprocess calls have explicit timeouts

### Compatibility

- Python 3.10+
- Works with Claude Code CLI

## Success Metrics

- Test suite passes with >80% coverage
- All CI checks green (lint, typecheck, test, security)
- Autonomous workflows converge within iteration limits
- Zero runtime dependencies (minimal attack surface)

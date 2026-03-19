# Refactor Plugin

![Version](https://img.shields.io/badge/version-3.1.0-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-7C3AED)
![Agents](https://img.shields.io/badge/agents-7_specialists-FF8C42)
![License](https://img.shields.io/badge/license-MIT-green)

Swarm-orchestrated code refactoring and feature development with specialized AI agents. Two skills — `/refactor` for iterative quality improvement and `/feature-dev` for guided new feature development — sharing 7 specialist agents with multi-instance parallel spawning, blackboard context sharing, and interactive approval gates.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme-infographic-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/readme-infographic.svg">
  <img alt="Refactor Plugin Architecture" src=".github/readme-infographic.svg" width="800">
</picture>

## Overview

The Refactor plugin provides two skills sharing seven specialist agents:

### `/refactor` — Iterative Code Improvement
Systematically improves code quality while preserving functionality through iterative architect → code → test → review → simplify cycles.

### `/feature-dev` — Guided Feature Development
Builds new features through interactive phases: requirement elicitation (95% confidence gate), parallel codebase exploration, architecture design with user selection, implementation, and multi-perspective quality review.

### Agents

- **code-explorer** — Deep codebase discovery: traces entry points, maps architecture, catalogs patterns
- **architect** — Reviews architecture, plans optimizations, designs feature blueprints, scores quality
- **code-reviewer** — Confidence-scored quality + security review with focus-area specialization
- **refactor-test** — Ensures test coverage and validates all changes
- **refactor-code** — Implements safe refactoring optimizations
- **feature-code** — Implements new features from architecture blueprints
- **simplifier** — Simplifies code for clarity, consistency, and maintainability

## How It Works

### Refactor Workflow

```text
Phase 0: Initialize → Create team, spawn agents, blackboard
Phase 0.5: Discovery → [code-explorer] maps codebase
Phase 1: Foundation (PARALLEL)
├── [refactor-test]   → Coverage analysis
├── [architect]       → Architecture review
└── [code-reviewer]   → Quality + security baseline

Phase 2: Iteration Loop (×3 default)
├── [architect]       → Optimization plan
├── [refactor-code]   → Implement optimizations
├── [refactor-test]   → Test verification
├── [code-reviewer]   → Quality + security gate
└── [simplifier]      → Simplify changes

Phase 3: Final Assessment (PARALLEL) → Scoring
Phase 4: Report + Cleanup
```

### Feature-Dev Workflow

```text
Phase 0: Initialize → Create team, spawn agents, blackboard
Phase 1: Discovery → 95% confidence elicitation (interactive)
Phase 2: Exploration → N code-explorers in parallel
Phase 3: Clarifications → Resolve codebase-specific ambiguities (interactive)
Phase 4: Architecture → N architects in parallel, user picks approach (interactive)
Phase 5: Implementation → [feature-code] builds feature (interactive approval)
Phase 6: Quality Review → N code-reviewers in parallel (interactive disposition)
Phase 7: Summary + Cleanup
```

Both workflows use swarm orchestration (TeamCreate, TaskCreate/TaskUpdate, SendMessage) with blackboard context sharing. Multi-instance spawning allows N parallel agents with different focuses.

## Quick Start

```bash
# Refactor entire codebase
/refactor

# Refactor specific file or directory
/refactor src/utils/
/refactor src/app.ts

# Refactor by description
/refactor "authentication logic"

# Override iteration count
/refactor --iterations=5 src/

# Focused refactoring
/refactor --focus=security src/auth/
/refactor --focus=security,architecture src/

# Feature development
/feature-dev "add webhook support for event notifications"
/feature-dev "implement rate limiting middleware"
```

## Installation

### Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) CLI
- Git
- (Optional) [GitHub CLI](https://cli.github.com/) (`gh`) for PR and report publishing features

### Install

```bash
claude --plugin-dir /path/to/refactor
```

## Features

- **Two Skills** — `/refactor` for iterative quality improvement, `/feature-dev` for guided new feature development.
- **7 Specialist Agents** — Shared agent pool with multi-instance parallel spawning.
- **Blackboard Context Sharing** — All agents read/write to a shared blackboard for context distribution.
- **Interactive Gates** — Feature-dev includes 95% confidence elicitation, architecture selection, and review disposition.
- **Multi-Instance Spawning** — Same agent runs as N parallel instances with different focuses (e.g., 3 explorers, 3 architects).
- **Safety First** — Tests pass before and after every change.
- **Quality Scoring** — Clean Code, Architecture, Security Posture scores (1--10) with justifications.
- **Security Review** — Per-iteration regression detection, vulnerability scanning, blocking on Critical/High findings.
- **Focus Mode** — Constrain refactoring to specific disciplines (`--focus=security`, `architecture`, etc.).
- **Configurable Workflow** — Commit strategies, PR creation, instance counts via `.claude/refactor.config.json`.

## Documentation

| Document | Quadrant | Description |
|----------|----------|-------------|
| [Tutorial: Your First Refactor](docs/tutorial.md) | Tutorial | Guided walkthrough from install to report review |
| [Tutorial: Your First Feature Development](docs/tutorial-feature-dev.md) | Tutorial | Build a new feature with /feature-dev |
| [How to Configure Commit Strategies](docs/guides/configure-commits.md) | How-to | Set up commits, PRs, and report publishing |
| [How to Scope Refactoring](docs/guides/scope-refactoring.md) | How-to | Choose effective scopes for different project sizes |
| [How to Run Focused Refactoring](docs/guides/focus-refactoring.md) | How-to | Constrain runs to specific disciplines with --focus |
| [How to Develop Features](docs/guides/use-feature-dev.md) | How-to | Practical guide to /feature-dev scenarios |
| [Troubleshooting](docs/guides/troubleshooting.md) | How-to | Diagnose and resolve common problems |
| [Configuration Reference](docs/reference/configuration.md) | Reference | Full config schema, fields, and examples |
| [Agent Reference](docs/reference/agents.md) | Reference | Agent specifications, tools, and invocation points |
| [Quality Score Reference](docs/reference/quality-scores.md) | Reference | Scoring rubrics and criteria |
| [Swarm Orchestration Design](docs/explanation/architecture.md) | Explanation | Why the plugin works this way |

## FAQ

**Q: Will this change my code's functionality?**
A: No. The refactoring process explicitly preserves all functionality. Only code quality and structure are improved.

**Q: What if my project has no tests?**
A: The test agent will create them. That's Phase 1.

**Q: What languages/frameworks are supported?**
A: All languages. Agents adapt to your project's testing framework and conventions.

**Q: Can I stop mid-refactor?**
A: Yes, but you'll lose progress. Better to start with smaller scope.

**Q: Why does --focus still spawn test and code agents?**
A: The refactor-test and refactor-code agents are a safety invariant. Tests must always pass, and the code agent must be available to fix failures or security findings.

**Q: Why does a focused run default to 1 iteration?**
A: Focused runs are typically quick targeted checks. Override with `--iterations=N` for iterative improvement.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for all versions.

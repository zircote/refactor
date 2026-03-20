# Refactor Plugin

![Version](https://img.shields.io/badge/version-4.0.0-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-7C3AED)
![Agents](https://img.shields.io/badge/agents-12_specialists-FF8C42)
![License](https://img.shields.io/badge/license-MIT-green)

Swarm-orchestrated code refactoring, feature development, and test architecture with specialized AI agents. Three skills — `/refactor` for iterative quality improvement, `/feature-dev` for guided new feature development, and `/test-gen` for scientifically grounded test generation — sharing 12 specialist agents with autonomous convergence mode, multi-instance parallel spawning, blackboard context sharing, and interactive approval gates.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme-infographic-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/readme-infographic.svg">
  <img alt="Refactor Plugin Architecture" src=".github/readme-infographic.svg" width="800">
</picture>

## Overview

The Refactor plugin provides three skills sharing twelve specialist agents:

### `/refactor` — Iterative Code Improvement
Systematically improves code quality while preserving functionality through iterative architect → code → test → review → simplify cycles.

### `/feature-dev` — Guided Feature Development
Builds new features through interactive phases: requirement elicitation (95% confidence gate), parallel codebase exploration, architecture design with user selection, implementation, and multi-perspective quality review.

### `/test-gen` — Test Architecture
Generates scientifically grounded test suites using equivalence class partitioning, boundary value analysis, property-based testing, and mutation-aware assertions. Also available as `/test-plan` (plan only) and `/test-eval` (evaluate existing tests).

### Agents

- **code-explorer** — Deep codebase discovery: traces entry points, maps architecture, catalogs patterns
- **architect** — Reviews architecture, plans optimizations, designs feature blueprints, scores quality
- **code-reviewer** — Confidence-scored quality + security review with focus-area specialization
- **refactor-test** — Ensures test coverage and validates all changes
- **refactor-code** — Implements safe refactoring optimizations
- **feature-code** — Implements new features from architecture blueprints
- **simplifier** — Simplifies code for clarity, consistency, and maintainability
- **convergence-reporter** — Analyzes autonomous convergence loop results and produces reports
- **test-planner** — Analyzes source code to produce JSON test plans using formal testing techniques
- **test-writer** — Generates idiomatic TDD red-phase test code from test plans
- **test-rigor-reviewer** — Scores test quality (0.0-1.0) and detects anti-patterns
- **coverage-analyst** — Runs native coverage tools and recommends gap-closing tests

## How It Works

### Refactor Workflow

```text
Phase 0: Initialize → Create team, spawn agents, blackboard
Phase 0.5: Discovery → [code-explorer] maps codebase
Phase 1: Foundation (PARALLEL)
├── [refactor-test]   → Coverage analysis
├── [architect]       → Architecture review
└── [code-reviewer]   → Quality + security baseline

Phase 2: Iteration Loop (×3 default, or --autonomous convergence)
├── [architect]       → Optimization plan
├── [refactor-code]   → Implement optimizations
├── [refactor-test]   → Test verification
├── [code-reviewer]   → Quality + security gate
└── [simplifier]      → Simplify changes
(Autonomous: keep/discard gate + composite scoring + convergence detection)

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
Phase 5: Implementation → [feature-code] builds feature (or --autonomous convergence)
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

# Autonomous convergence mode
/refactor --autonomous src/services/
/refactor --autonomous --iterations=10 --focus=security src/auth/
/feature-dev --autonomous "add webhook support for event notifications"

# Feature development
/feature-dev "add webhook support for event notifications"
/feature-dev "implement rate limiting middleware"

# Test architecture
/test-gen src/utils/
/test-plan src/auth/
/test-eval tests/
/test-gen --coverage src/
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

- **Three Skills** — `/refactor` for iterative quality improvement, `/feature-dev` for guided new feature development, `/test-gen` for scientifically grounded test generation.
- **Autonomous Convergence** — `--autonomous` flag for Karpathy autoresearch-style improvement loops with composite scoring, keep/discard gating, and automatic convergence detection.
- **12 Specialist Agents** — Shared agent pool with multi-instance parallel spawning.
- **Test Architecture** — Formal test design: equivalence class partitioning, boundary value analysis, property-based testing, mutation-aware assertions with rigor scoring.
- **Blackboard Context Sharing** — All agents read/write to a shared blackboard for context distribution.
- **Interactive Gates** — Feature-dev includes 95% confidence elicitation, architecture selection, and review disposition.
- **Multi-Instance Spawning** — Same agent runs as N parallel instances with different focuses (e.g., 3 explorers, 3 architects).
- **Safety First** — Tests pass before and after every change.
- **Quality Scoring** — Clean Code, Architecture, Security Posture scores (1--10) with justifications.
- **Security Review** — Per-iteration regression detection, vulnerability scanning, blocking on Critical/High findings.
- **Focus Mode** — Constrain refactoring to specific disciplines (`--focus=security`, `architecture`, etc.).
- **Configurable Workflow** — Commit strategies, PR creation, instance counts via `.claude/refactor.config.json`.

## Documentation

Full documentation index with coverage matrix: **[docs/README.md](docs/README.md)**

| Document | Quadrant | Description |
|----------|----------|-------------|
| [Your First Refactor](docs/tutorials/tutorial.md) | Tutorial | Guided walkthrough from install to report review |
| [Your First Feature Development](docs/tutorials/tutorial-feature-dev.md) | Tutorial | Build a new feature with /feature-dev |
| [Your First Autonomous Refactor](docs/tutorials/tutorial-autonomous.md) | Tutorial | Run an unattended convergence loop with --autonomous |
| [Your First Test Architecture](docs/tutorials/tutorial-test-architect.md) | Tutorial | Generate a scientifically grounded test suite with /test-gen |
| [Configure Commit Strategies](docs/guides/configure-commits.md) | How-to | Set up commits, PRs, and report publishing |
| [Scope Refactoring](docs/guides/scope-refactoring.md) | How-to | Choose effective scopes for different project sizes |
| [Run Focused Refactoring](docs/guides/focus-refactoring.md) | How-to | Constrain runs to specific disciplines with --focus |
| [Develop Features](docs/guides/use-feature-dev.md) | How-to | Practical guide to /feature-dev scenarios |
| [Use Autonomous Mode](docs/guides/use-autonomous-mode.md) | How-to | Configure weights, thresholds, and iteration counts |
| [Generate and Evaluate Tests](docs/guides/use-test-gen.md) | How-to | Run /test-gen, /test-plan, and /test-eval |
| [Evaluate Test Quality](docs/guides/evaluate-test-quality.md) | How-to | Interpret rigor scores and fix anti-patterns |
| [Troubleshooting](docs/guides/troubleshooting.md) | How-to | Diagnose and resolve common problems |
| [Configuration Reference](docs/reference/configuration.md) | Reference | Full config schema, CLI flags, and examples |
| [Agent Reference](docs/reference/agents.md) | Reference | All 12 agent specifications, tools, and invocation points |
| [Quality Score Reference](docs/reference/quality-scores.md) | Reference | Scoring rubrics: Clean Code, Architecture, Security, Rigor, Coverage |
| [Swarm Orchestration Design](docs/explanation/architecture.md) | Explanation | Agent roles, parallel execution, version history |
| [Autonomous Convergence](docs/explanation/autonomous-convergence.md) | Explanation | The keep/discard scoring pattern and convergence detection |
| [Test Design Techniques](docs/explanation/test-design-techniques.md) | Explanation | Why formal testing techniques produce better tests |

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

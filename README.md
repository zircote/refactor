# Refactor Plugin

![Version](https://img.shields.io/badge/version-2.1.0-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-7C3AED)
![Agents](https://img.shields.io/badge/agents-4_specialists-FF8C42)
![License](https://img.shields.io/badge/license-MIT-green)

Swarm-orchestrated iterative code refactoring with specialized AI agents that ensure test coverage, design optimizations, simplify code, and verify quality through parallel execution and multiple refinement cycles.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme-infographic-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/readme-infographic.svg">
  <img alt="Refactor Plugin Architecture" src=".github/readme-infographic.svg" width="800">
</picture>

## Overview

The Refactor plugin orchestrates four specialized agents as a swarm team to systematically improve code quality while preserving functionality:

- **Architect Agent** — Reviews code architecture, plans optimizations, scores quality
- **Refactor-Test Agent** — Ensures comprehensive test coverage and validates changes
- **Refactor-Code Agent** — Implements clean code improvements safely
- **Simplifier Agent** — Simplifies changed code for clarity, consistency, and maintainability

## How It Works

The refactoring process uses swarm orchestration (TeamCreate, TaskCreate/TaskUpdate, SendMessage) with parallel execution where possible:

```text
Phase 0: Initialize
├── Create swarm team
├── Spawn 4 teammates: architect, refactor-test, refactor-code, simplifier
└── Create phase tasks

Phase 1: Foundation (PARALLEL)
├── [refactor-test]      → Analyze coverage, add missing tests, verify passing
└── [architect] → Initial architecture review, identify all opportunities

Phase 2: Iteration Loop (×3)
│
├── Step A: [architect]       → Create optimization plan (top 3 priorities)
├── Step B: [refactor-code]  → Implement top 3 optimizations
├── Step C: [refactor-test]  → Run full test suite, report pass/fail
├── Step D: [refactor-code]  → Fix test failures if any → [refactor-test] re-run
├── Step E: [simplifier]     → Simplify all code changed this iteration
└── Step F: [refactor-test]  → Verify simplification preserved functionality

Phase 3: Final Assessment (PARALLEL)
├── [simplifier] → Final whole-scope simplification pass
└── [architect]  → Prepare final quality assessment framework

Phase 4: Final Verification & Report
├── [refactor-test] → Final test suite run
├── [architect]     → Score code (Clean Code + Architecture, 1-10 each)
├── Generate refactor-result-{timestamp}.md
└── Shutdown team
```

## Quick Start

```bash
# Refactor entire codebase
/refactor

# Refactor specific directory
/refactor src/utils/

# Refactor specific file
/refactor src/app.ts

# Refactor by description
/refactor "authentication logic"

# Override iteration count
/refactor --iterations=5 src/
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

- **Safety First** — Only improves code quality, never alters behavior. Tests pass before and after every change.
- **Parallel Execution** — Phase 1 and Phase 3 run agents simultaneously for faster results.
- **Automatic Test Generation** — Adds missing test cases for critical paths, edge cases, and error handling.
- **Architecture Scoring** — Objective Clean Code and Architecture scores (1--10) with per-criteria justifications.
- **Code Simplification** — Post-implementation polish: naming clarity, guard clauses, redundancy removal, cross-file consistency.
- **Configurable Workflow** — Commit strategies, PR creation, and report publishing via `.claude/refactor.config.json`.

## Documentation

| Document | Quadrant | Description |
|----------|----------|-------------|
| [Tutorial: Your First Refactor](docs/tutorial.md) | Tutorial | Guided walkthrough from install to report review |
| [How to Configure Commit Strategies](docs/guides/configure-commits.md) | How-to | Set up commits, PRs, and report publishing |
| [How to Scope Refactoring](docs/guides/scope-refactoring.md) | How-to | Choose effective scopes for different project sizes |
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

## Changelog

### 2.1.0
- Configuration-driven post-refactor workflow via `.claude/refactor.config.json`
- Interactive first-run setup wizard with AskUserQuestion prompts
- Commit strategies: none, per-iteration, single-final
- Optional PR creation (draft or ready-for-review) after refactoring
- Report publishing to GitHub Issues or GitHub Discussions
- Cross-referencing between PRs and published reports
- Non-blocking error handling for all GitHub operations

### 2.0.0
- Swarm orchestration (TeamCreate, TaskCreate/TaskUpdate, SendMessage)
- New simplifier agent (opus model) for code clarity passes
- Parallel execution in Phase 1 (foundation) and Phase 3 (final assessment)
- 4-phase workflow replacing 7-step sequential process
- Code simplification step after each iteration cycle

### 1.0.0
- Initial release with sequential 7-step workflow
- Three agents: architect, refactor-test, refactor-code


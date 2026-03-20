# Documentation

The refactor plugin documentation follows the [Diataxis](https://diataxis.fr/) framework, organized into four quadrants by user need.

## Skills

The plugin provides three skills sharing twelve specialist agents:

| Skill | Command | Purpose |
|-------|---------|---------|
| **Refactor** | `/refactor` | Iterative code quality improvement with safety gates |
| **Feature-Dev** | `/feature-dev` | Guided new feature development with interactive approval |
| **Test-Architect** | `/test-gen`, `/test-plan`, `/test-eval` | Scientifically grounded test generation and evaluation |

## Tutorials — Learning-oriented

Step-by-step walkthroughs for first-time users. Start here.

| Document | Description |
|----------|-------------|
| [Your First Refactor](tutorials/tutorial.md) | Run `/refactor` on a codebase and review the results |
| [Your First Feature Development](tutorials/tutorial-feature-dev.md) | Build a new feature with `/feature-dev` |
| [Your First Autonomous Refactor](tutorials/tutorial-autonomous.md) | Run an unattended convergence loop with `--autonomous` |
| [Your First Test Architecture](tutorials/tutorial-test-architect.md) | Generate a scientifically grounded test suite with `/test-gen` |

## How-to Guides — Task-oriented

Practical recipes for specific goals. Use when you know what you want to do.

| Document | Description |
|----------|-------------|
| [Configure Commit Strategies](guides/configure-commits.md) | Set up automatic commits, PRs, and report publishing |
| [Scope Refactoring Effectively](guides/scope-refactoring.md) | Choose effective scopes for different project sizes |
| [Run Focused Refactoring](guides/focus-refactoring.md) | Constrain runs to specific disciplines with `--focus` |
| [Use Feature-Dev](guides/use-feature-dev.md) | Practical guide to `/feature-dev` scenarios |
| [Use Autonomous Mode](guides/use-autonomous-mode.md) | Configure weights, thresholds, and iteration counts |
| [Generate and Evaluate Tests](guides/use-test-gen.md) | Run `/test-gen`, `/test-plan`, and `/test-eval` |
| [Evaluate Test Quality](guides/evaluate-test-quality.md) | Interpret rigor scores and fix anti-patterns |
| [Troubleshooting](guides/troubleshooting.md) | Diagnose and resolve common problems |

## Reference — Information-oriented

Precise specifications for lookup. Use when you need exact details.

| Document | Description |
|----------|-------------|
| [Configuration](reference/configuration.md) | Full config schema, CLI flags, and examples |
| [Agents](reference/agents.md) | All 12 agent specifications, tools, and invocation points |
| [Quality Scores](reference/quality-scores.md) | Scoring rubrics: Clean Code, Architecture, Security, Rigor, Coverage |

## Explanation — Understanding-oriented

Conceptual discussions about design decisions. Use when you want to understand *why*.

| Document | Description |
|----------|-------------|
| [Swarm Orchestration Design](explanation/architecture.md) | Agent roles, parallel execution, version history |
| [Autonomous Convergence](explanation/autonomous-convergence.md) | The keep/discard scoring pattern and convergence detection |
| [Test Design Techniques](explanation/test-design-techniques.md) | Why equivalence classes, boundary values, and property testing produce better tests |

## Coverage Matrix

Each skill has documentation across all four Diataxis quadrants:

| Skill | Tutorial | How-to | Reference | Explanation |
|-------|----------|--------|-----------|-------------|
| Refactor | [tutorial](tutorials/tutorial.md) | [scope](guides/scope-refactoring.md), [focus](guides/focus-refactoring.md), [commits](guides/configure-commits.md) | [agents](reference/agents.md), [scores](reference/quality-scores.md), [config](reference/configuration.md) | [architecture](explanation/architecture.md) |
| Feature-Dev | [tutorial](tutorials/tutorial-feature-dev.md) | [use](guides/use-feature-dev.md) | [agents](reference/agents.md), [config](reference/configuration.md) | [architecture](explanation/architecture.md) |
| Autonomous | [tutorial](tutorials/tutorial-autonomous.md) | [use](guides/use-autonomous-mode.md) | [config](reference/configuration.md) | [convergence](explanation/autonomous-convergence.md) |
| Test-Architect | [tutorial](tutorials/tutorial-test-architect.md) | [generate](guides/use-test-gen.md), [evaluate](guides/evaluate-test-quality.md) | [agents](reference/agents.md), [scores](reference/quality-scores.md), [config](reference/configuration.md) | [techniques](explanation/test-design-techniques.md) |

## Directory Structure

```
docs/
├── README.md                          ← this file
├── tutorials/                         ← learning-oriented walkthroughs
│   ├── tutorial.md
│   ├── tutorial-autonomous.md
│   ├── tutorial-feature-dev.md
│   └── tutorial-test-architect.md
├── guides/                            ← task-oriented how-to recipes
│   ├── configure-commits.md
│   ├── evaluate-test-quality.md
│   ├── focus-refactoring.md
│   ├── scope-refactoring.md
│   ├── troubleshooting.md
│   ├── use-autonomous-mode.md
│   ├── use-feature-dev.md
│   └── use-test-gen.md
├── reference/                         ← information-oriented specifications
│   ├── agents.md
│   ├── configuration.md
│   └── quality-scores.md
└── explanation/                       ← understanding-oriented discussions
    ├── architecture.md
    ├── autonomous-convergence.md
    └── test-design-techniques.md
```

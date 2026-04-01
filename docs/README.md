---
diataxis_type: navigation
---

# Documentation

The refactor plugin documentation follows the [Diataxis](https://diataxis.fr/) framework, organized into four quadrants by user need.

## Skills

The plugin provides core skills, git workflow commands, and project management skills:

### Core Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| **Refactor** | `/refactor` | Iterative code quality improvement with safety gates |
| **Feature-Dev** | `/feature-dev` | Guided new feature development with interactive approval |
| **Test-Architect** | `/test-gen`, `/test-plan`, `/test-eval` | Scientifically grounded test generation and evaluation |

### Git Workflow Commands

| Command | Purpose |
|---------|---------|
| `/cp` | Stage, commit, and push with conventional commit messages |
| `/pr` | Create, update, or manage pull requests (draft by default) |
| `/fr` | Fetch and rebase onto remote tracking branch |
| `/ff` | Fast-forward merge from remote (no rebase, no merge commits) |
| `/sync` | Full sync cycle -- fetch, rebase, and push |
| `/pr-fix` | Remediate PR review feedback -- triage, fix, reply, resolve |
| `/review-comments` | Triage and respond to PR comments with confidence scoring |
| `/pr-review` | Comprehensive PR code review with size-scaled strategy |
| `/pr-sweep` | Gated PR sweep -- review, fix, rebase, CI, merge |
| `/prune` | Clean up stale local branches |
| `/git-hooks` | Analyze project and install tailored git hooks |

### Project Management Skills

| Command | Purpose |
|---------|---------|
| `/project-plan` | Goal-driven GitHub Projects v2 board management |
| `/gh-work` | Intelligent issue, discussion, and workplan management |

### Choosing the Right Skill

Use `/refactor` to improve existing code without changing behavior. Use `/feature-dev` to build something new. Use `/test-gen` to generate scientifically grounded tests for existing code.

## Tutorials — Learning-oriented

Step-by-step walkthroughs for first-time users. Start here.

| Document | Description |
|----------|-------------|
| [Your First Refactor](tutorials/tutorial.md) | Run `/refactor` on a codebase and review the results |
| [Your First Feature Development](tutorials/tutorial-feature-dev.md) | Build a new feature with `/feature-dev` |
| [Your First Autonomous Refactor](tutorials/tutorial-autonomous.md) | Run an unattended convergence loop with `--autonomous` |
| [Your First Test Architecture](tutorials/tutorial-test-architect.md) | Generate a scientifically grounded test suite with `/test-gen` |
| [Managing Your Project Board](tutorials/tutorial-project-plan.md) | Manage a GitHub Projects v2 board with `/project-plan` |

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
| [Use Git Workflow Commands](guides/git-workflows.md) | Commit, push, PR, sync, and branch cleanup workflows |
| [Use Project Planning](guides/use-project-plan.md) | Manage GitHub Projects v2 boards with `/project-plan` |
| [Troubleshooting](guides/troubleshooting.md) | Diagnose and resolve common problems |

## Reference — Information-oriented

Precise specifications for lookup. Use when you need exact details.

| Document | Description |
|----------|-------------|
| [Configuration](reference/configuration.md) | Full config schema, CLI flags, and examples |
| [Agents](reference/agents.md) | All 12 agent specifications, tools, and invocation points |
| [Quality Scores](reference/quality-scores.md) | Scoring rubrics: Clean Code, Architecture, Security, Rigor, Coverage |
| [Git Workflow Commands](reference/git-commands.md) | Syntax, flags, and behavior for all git workflow commands |

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
| Feature-Dev | [tutorial](tutorials/tutorial-feature-dev.md) | [use](guides/use-feature-dev.md), [evaluate tests](guides/evaluate-test-quality.md) | [agents](reference/agents.md), [scores](reference/quality-scores.md), [config](reference/configuration.md) | [architecture](explanation/architecture.md), [test techniques](explanation/test-design-techniques.md) |
| Autonomous | [tutorial](tutorials/tutorial-autonomous.md) | [use](guides/use-autonomous-mode.md) | [config](reference/configuration.md) | [convergence](explanation/autonomous-convergence.md) |
| Test-Architect | [tutorial](tutorials/tutorial-test-architect.md) | [generate](guides/use-test-gen.md), [evaluate](guides/evaluate-test-quality.md) | [agents](reference/agents.md), [scores](reference/quality-scores.md), [config](reference/configuration.md) | [techniques](explanation/test-design-techniques.md) |
| Git Workflows | -- | [workflows](guides/git-workflows.md) | [commands](reference/git-commands.md) | -- |
| Project Plan | [tutorial](tutorials/tutorial-project-plan.md) | [use](guides/use-project-plan.md) | [config](reference/configuration.md) | -- |

## Directory Structure

```
docs/
├── README.md                          ← this file
├── REQUIREMENTS.md                    ← product requirements
├── tutorials/                         ← learning-oriented walkthroughs
│   ├── tutorial.md
│   ├── tutorial-autonomous.md
│   ├── tutorial-feature-dev.md
│   ├── tutorial-project-plan.md
│   └── tutorial-test-architect.md
├── guides/                            ← task-oriented how-to recipes
│   ├── configure-commits.md
│   ├── evaluate-test-quality.md
│   ├── focus-refactoring.md
│   ├── git-workflows.md
│   ├── scope-refactoring.md
│   ├── troubleshooting.md
│   ├── use-autonomous-mode.md
│   ├── use-feature-dev.md
│   ├── use-project-plan.md
│   └── use-test-gen.md
├── reference/                         ← information-oriented specifications
│   ├── agents.md
│   ├── configuration.md
│   ├── git-commands.md
│   └── quality-scores.md
└── explanation/                       ← understanding-oriented discussions
    ├── architecture.md
    ├── autonomous-convergence.md
    └── test-design-techniques.md
```

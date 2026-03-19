---
diataxis_type: explanation
diataxis_topic: swarm orchestration design and agent collaboration model
---

# Swarm Orchestration Design

## Background

The refactor plugin evolved through four major versions, each addressing limitations of the previous approach.

**v1.0.0** used a sequential 7-step workflow with three agents (architect, refactor-test, refactor-code). Each agent ran one after another, making the process slow and preventing agents from working on independent tasks simultaneously.

**v2.0.0** introduced swarm orchestration — agents now operate as a coordinated team using Claude Code's TeamCreate, TaskCreate/TaskUpdate, and SendMessage primitives. This enabled parallel execution in phases where agents do not depend on each other's output. Added the simplifier agent.

**v2.1.0** added configuration-driven post-refactor workflows (commits, PRs, report publishing), making the plugin self-contained.

**v2.2.0** added the security-review agent and `--focus` flag for constrained runs.

**v3.0.0** is a full workflow rewrite: added code-explorer for deep codebase discovery (Phase 0.5), merged security-review into code-reviewer for a unified quality + security gate, migrated from command to skill format, standardized all agents on the sonnet model, and introduced blackboard-based context sharing.

## Why swarm orchestration

The refactoring process has a natural structure: some tasks are independent (test analysis and architecture review can happen simultaneously), while others are strictly sequential (you cannot fix test failures before running tests). A swarm model expresses this structure directly.

The alternative — a linear pipeline where each agent waits for the previous one — wastes time during independent phases. In the swarm model, Phase 1 and Phase 3 each run up to three agents in parallel, reducing wall-clock time for those phases.

## The six agents and their roles

The decision to use six specialized agents rather than a single general-purpose agent reflects a separation of concerns:

- **Code-Explorer** — Runs first (Phase 0.5). Deep codebase analysis producing a structured map consumed by all downstream agents. This eliminates redundant discovery work — agents start with shared understanding rather than each independently exploring the codebase.
- **Architect** — Read-only analysis. Cannot modify files. This constraint prevents the planning agent from making changes that bypass the test-verify cycle.
- **Code-Reviewer** — Unified quality and security gate. Combines confidence-scored quality review (bugs, logic, conventions) with severity-classified security review (regressions, secrets, OWASP). This merger eliminates the overhead of two separate review agents while maintaining both disciplines. Uses confidence >= 80 for quality and Critical/High severity for blocking security findings.
- **Refactor-Test** — Owns the test suite. Has Bash access to run tests. Acts as the quality gate — no changes proceed without passing tests.
- **Refactor-Code** — Implements changes. Has Write and Edit access. Fixes both test failures and blocking code review findings.
- **Simplifier** — Post-implementation polish. Reviews code changed by refactor-code for clarity improvements.

This separation ensures that no single agent can both make changes and verify them. The explorer maps, the architect plans, the code agent implements, the reviewer gates, the test agent verifies, and the simplifier polishes — each with only the tools appropriate to its role.

## Phase 0.5: Discovery-first design

A key insight in v3.0.0 is that all agents benefit from shared codebase understanding. Without the explorer, each agent independently discovers entry points, traces flows, and maps dependencies — redundant work that wastes context and tokens.

The code-explorer produces a structured codebase map (entry points, execution flows, architecture layers, dependencies, patterns) that is distributed to all downstream agents via:

1. **Atlatl blackboard** (preferred) — written once, read by any agent on demand
2. **Inline context** (fallback) — embedded in task descriptions when blackboard is unavailable

This discovery-first approach means Phase 1 agents start with full context rather than spending time on exploration.

## Why merge security-review into code-reviewer

v2.2.0 had separate agents for code quality (architect's perspective) and security review. In practice, these reviews share significant overlap:

- Both examine changed files
- Both look for regressions against a baseline
- Both classify findings by severity
- Both provide remediation guidance

Maintaining two separate review agents doubled the review cost per iteration. The merged code-reviewer uses confidence scoring for quality issues and severity classification for security issues — two complementary lenses in a single pass. This halves the review overhead while maintaining both disciplines.

## The iteration cycle

The core insight behind iterative refactoring is that each pass reveals new opportunities. After extracting a method (iteration 1), the simplified function may expose a naming issue (iteration 2), which after fixing may reveal a duplicated pattern (iteration 3).

Three iterations is the default because empirical use shows diminishing returns beyond that point. The `--iterations=N` flag and `iterations` config field exist for cases where the default is not appropriate.

## Parallel execution points

Three phases run agents in parallel:

**Phase 0.5 (Discovery):** Code-explorer runs solo. Must complete before Phase 1 starts.

**Phase 1 (Foundation):** The test agent analyzes coverage while the architect reviews architecture and the code-reviewer establishes a quality + security baseline. These are independent — neither depends on the other's output. All receive the explorer's codebase map as context.

**Phase 3 (Final Assessment):** The simplifier performs a final cross-file consistency pass, the architect prepares the scoring framework, and the code-reviewer performs a final comprehensive review. These are independent operations.

Phase 2 steps are sequential: architect plans → code agent implements → test agent verifies → code-reviewer reviews (quality + security gate) → simplifier polishes → test agent re-verifies.

## Focus mode and agent gating

Focus mode (`--focus`) constrains a run to specific disciplines by spawning only the agents needed for that analysis.

**Why focused runs exist:** Full runs spawn 6 agents and execute all phases, which is thorough but slow. When a user needs only a security audit or an architecture review, the overhead of unused agents wastes time.

**Focus areas and agent mapping:**
- `discovery` → code-explorer
- `security` → code-reviewer
- `architecture` → architect
- `simplification` → simplifier
- `code` → architect + code-reviewer

**Why refactor-test and refactor-code always spawn:** These two agents form a safety invariant. The test agent ensures tests pass after any changes. The code agent provides fix capability for blocking findings or test failures.

**Union model for multi-focus:** When multiple focus areas are specified, the agent set is the union of each area's agents plus the always-present pair.

## Error handling philosophy

The plugin treats test failures and blocking code review findings as hard gates (the refactor stops and retries up to 3 times) but treats all GitHub operations (commits, PRs, issues, discussions) as non-blocking best-effort. A broken test or security regression means the refactoring damaged the codebase, which is critical. A failed PR creation is an inconvenience but not a correctness issue.

## Further reading

- [Agent Reference](../reference/agents.md) — detailed agent specifications and tool lists
- [Quality Score Reference](../reference/quality-scores.md) — scoring rubrics and criteria
- [Tutorial: Your First Refactor](../tutorial.md) — see the orchestration in action

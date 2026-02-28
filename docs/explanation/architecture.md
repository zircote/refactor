---
diataxis_type: explanation
diataxis_topic: swarm orchestration design and agent collaboration model
---

# Swarm Orchestration Design

## Background

The refactor plugin evolved through three major versions, each addressing limitations of the previous approach.

**v1.0.0** used a sequential 7-step workflow with three agents (architect, refactor-test, refactor-code). Each agent ran one after another, making the process slow and preventing agents from working on independent tasks simultaneously.

**v2.0.0** introduced swarm orchestration — the four agents now operate as a coordinated team using Claude Code's TeamCreate, TaskCreate/TaskUpdate, and SendMessage primitives. This enabled parallel execution in phases where agents do not depend on each other's output.

**v2.1.0** added configuration-driven post-refactor workflows (commits, PRs, report publishing), making the plugin self-contained.

## Why swarm orchestration

The refactoring process has a natural structure: some tasks are independent (test analysis and architecture review can happen simultaneously), while others are strictly sequential (you cannot fix test failures before running tests). A swarm model expresses this structure directly.

The alternative — a linear pipeline where each agent waits for the previous one — wastes time during independent phases. In the swarm model, Phase 1 and Phase 3 each run two agents in parallel, roughly halving the wall-clock time for those phases.

## The four agents and their roles

The decision to use four specialized agents rather than a single general-purpose agent reflects a separation of concerns:

- **Architect** — Read-only analysis. Cannot modify files. This constraint prevents the planning agent from making changes that bypass the test-verify cycle.
- **Refactor-Test** — Owns the test suite. Has Bash access to run tests. Acts as the quality gate — no changes proceed without passing tests.
- **Refactor-Code** — Implements changes. Has Write and Edit access but no Bash. Cannot run tests itself, forcing it to rely on the test agent for verification.
- **Simplifier** — Post-implementation polish. Reviews code changed by refactor-code for clarity improvements. Uses the `opus` model because nuanced naming and readability decisions benefit from the most capable model.

This separation ensures that no single agent can both make changes and verify them. The architect plans, the code agent implements, the test agent verifies, and the simplifier polishes — each with only the tools appropriate to its role.

## The iteration cycle

The core insight behind iterative refactoring is that each pass reveals new opportunities. After extracting a method (iteration 1), the simplified function may expose a naming issue (iteration 2), which after fixing may reveal a duplicated pattern (iteration 3).

Three iterations is the default because empirical use shows diminishing returns beyond that point. The first iteration addresses the most impactful issues. The second catches issues revealed by the first. The third is typically a polish pass. Additional iterations rarely produce significant improvements.

The `--iterations=N` flag and `iterations` config field exist for cases where the default is not appropriate — a heavily tangled codebase may benefit from 5 iterations, while a mostly-clean file needs only 2.

## Parallel execution points

Two phases run agents in parallel:

**Phase 1 (Foundation):** The test agent analyzes coverage and writes missing tests while the architect reviews architecture. These are independent — neither depends on the other's output, and both are read-then-write operations on different parts of the codebase (test files vs. analysis output).

**Phase 3 (Final Assessment):** The simplifier performs a final cross-file consistency pass while the architect prepares the scoring framework. Again, these are independent write operations on different outputs.

All Phase 2 steps are sequential because each depends on the previous step's output: the architect's plan feeds the code agent, whose changes feed the test agent, whose results may feed back to the code agent, and so on.

## Error handling philosophy

The plugin treats test failures as hard gates (the refactor stops and retries up to 3 times) but treats all GitHub operations (commits, PRs, issues, discussions) as non-blocking best-effort. The rationale: a broken test means the refactoring damaged functionality, which is a critical problem. A failed PR creation means a convenience feature did not work, which is an inconvenience but not a correctness issue.

## Comparison with alternatives

**Manual refactoring** gives full control but is slow and inconsistent. Developers tend to fix what they notice rather than systematically evaluating all code quality dimensions.

**Single-pass automated refactoring** (e.g., linters with auto-fix) catches mechanical issues but misses architectural improvements, naming clarity, and design-level simplifications.

**The swarm approach** combines the breadth of automated analysis with the judgment of large language models, while the iterative cycle and test-gating provide safety guarantees that neither manual nor single-pass approaches offer.

## Further reading

- [Agent Reference](../reference/agents.md) — detailed agent specifications and tool lists
- [Quality Score Reference](../reference/quality-scores.md) — scoring rubrics and criteria
- [Tutorial: Your First Refactor](../tutorial.md) — see the orchestration in action

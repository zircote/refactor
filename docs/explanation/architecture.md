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

## The twelve agents and their roles

The decision to use twelve specialized agents (six for /refactor standard mode, seven with convergence-reporter in autonomous mode, five+ for /feature-dev, four for /test-architect) rather than a single general-purpose agent reflects a separation of concerns:

- **Code-Explorer** — Runs first (Phase 0.5). Deep codebase analysis producing a structured map consumed by all downstream agents. This eliminates redundant discovery work — agents start with shared understanding rather than each independently exploring the codebase.
- **Architect** — Read-only analysis. Cannot modify files. This constraint prevents the planning agent from making changes that bypass the test-verify cycle.
- **Code-Reviewer** — Unified quality and security gate. Combines confidence-scored quality review (bugs, logic, conventions) with severity-classified security review (regressions, secrets, OWASP). This merger eliminates the overhead of two separate review agents while maintaining both disciplines. Uses confidence >= 80 for quality and Critical/High severity for blocking security findings.
- **Refactor-Test** — Owns the test suite. Has Bash access to run tests. Acts as the quality gate — no changes proceed without passing tests.
- **Refactor-Code** — Implements changes. Has Write and Edit access. Fixes both test failures and blocking code review findings.
- **Simplifier** — Post-implementation polish. Reviews code changed by refactor-code for clarity improvements.

- **Feature-Code** — New feature implementation (feature-dev only). Reads architecture blueprints from the blackboard and creates code following codebase conventions. Distinct from refactor-code: feature-code *creates* new functionality while refactor-code *restructures* existing code.

This separation ensures that no single agent can both make changes and verify them. The explorer maps, the architect plans, the code agents implement (refactor-code for restructuring, feature-code for new features), the reviewer gates, the test agent verifies, and the simplifier polishes — each with only the tools appropriate to its role.

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

## v3.1.0: Feature development and multi-instance spawning

**v3.1.0** added the `/feature-dev` skill — a second workflow sharing agents with `/refactor` — and introduced multi-instance parallel agent spawning.

### Why add feature development to a refactoring plugin?

The agents developed for refactoring (code-explorer, architect, code-reviewer) are equally valuable for building new features. Rather than maintaining two separate plugins with duplicated agent definitions, v3.1.0 merges both workflows into one plugin where agents are DRY:

- **Code-explorer** maps the codebase for refactoring *and* explores integration points for new features
- **Architect** creates optimization plans *and* designs feature architecture blueprints
- **Code-reviewer** gates refactoring quality *and* reviews new feature implementations with focus-area specialization

The key difference is a new **feature-code** agent that *creates* code (vs refactor-code which *restructures* existing code).

### Multi-instance spawning

Feature development benefits from multiple perspectives — three architects with different design philosophies (minimal, clean, pragmatic) produce more options than one. The same applies to exploration (different focuses) and review (different quality dimensions).

Multi-instance spawning means the same agent definition (e.g., `refactor:code-explorer`) can be spawned N times with unique names (`code-explorer-1`, `code-explorer-2`, `code-explorer-3`) and different prompts. Instance counts are configurable and scaled by feature complexity:

- **Simple features** (single endpoint, trivial logic): 1 instance each
- **Complex features** (cross-cutting, multiple systems): full configured count (default: 3)

### Blackboard as shared context layer

All agents use the Atlatl blackboard for context sharing. This is a key architectural decision: instead of the team lead relaying context in task descriptions (which bloats prompts and risks information loss), agents write findings to named keys and other agents read them directly.

The blackboard enables a write-once, read-many pattern: the code-explorer writes `codebase_context` once and every downstream agent reads it on demand. The team lead writes `feature_spec` and `chosen_architecture`; all implementation and review agents consume them.

### Interactive approval gates

Feature development is inherently more uncertain than refactoring (which preserves behavior). The `/feature-dev` skill includes 5 interactive gates where the user must approve before proceeding:

1. **Elicitation** — 95% confidence before exploration begins
2. **Clarification** — post-exploration ambiguities resolved
3. **Architecture selection** — user picks from competing designs
4. **Implementation approval** — user confirms readiness to build
5. **Review disposition** — user decides what to fix

These gates prevent the skill from building the wrong thing. The 95% confidence protocol uses graduated elicitation — detailed requests skip quickly (0-1 questions) while vague requests get thorough questioning (8-15 questions across multiple rounds).

## v4.0.0: Autonomous convergence and the keep/discard pattern

**v4.0.0** adds the `--autonomous` flag to both skills, implementing the [Karpathy autoresearch pattern](https://github.com/karpathy/autoresearch) for source code improvement. This is the most significant loop-level change since swarm orchestration in v2.0.0.

### Why the autoresearch pattern

The standard iteration loop has a fundamental weakness: it always moves forward. If iteration 2 produces a bad change, iteration 3 builds on top of that bad change. The only safety net is the test gate — and tests do not catch quality regressions, only functional ones.

The autoresearch pattern solves this with a **keep/discard gate**: after each iteration, a composite score is computed. If the score improved, the changes are kept (snapshotted to a git branch). If not, the changes are discarded (working tree restored from the best snapshot). This means `best_score` monotonically increases and bad experiments are free.

### Why composite scoring instead of just tests

Tests tell you whether the code works, not whether it's good. A refactoring that passes all tests but introduces code smells, weakens security controls, or degrades readability should be caught. The composite score combines three signals:

- **Test pass rate** (50%) — functional correctness
- **Code quality score** (25%) — Clean Code rubric via code-reviewer Mode 5
- **Security posture** (25%) — Security Posture rubric via code-reviewer Mode 5

This ensures that the loop optimizes for overall code health, not just test passage.

### Why git branches instead of filesystem copies

The original autoresearch uses filesystem copies with SHA-256 verification. For source code, git branches are more natural:

- Built-in diff/merge capabilities (`git diff autoresearch/v0..autoresearch/v3`)
- Space-efficient (git's object model deduplicates unchanged files)
- Inspectable with familiar tools (`git log`, `git show`)
- Local-only (never pushed) with automatic cleanup

### Why freeze tests for refactor but not feature-dev

Refactoring preserves behavior — the tests are the fixed evaluation metric. If tests change alongside code, you cannot tell whether the score improved because the code got better or because the tests got easier. This is the "moving goalposts" problem.

Feature development creates new behavior — the feature does not exist yet, so tests must evolve with the implementation. Freezing tests would mean scoring against a test suite that cannot exercise the new code.

### The convergence-reporter agent

The eighth agent was added specifically for autonomous mode. It reads the results log, computes score trajectories, generates diffs between baseline and best version, and produces a convergence report with recommendations. It runs only at loop finalization — it is never spawned during standard mode.

For deeper coverage of the autonomous convergence pattern, see [Autonomous Convergence](autonomous-convergence.md).

## v4.1.0: Test architecture and formal testing techniques

**v4.1.0** adds the `/test-architect` skill with three commands (`/test-gen`, `/test-plan`, `/test-eval`) and four new specialist agents (test-planner, test-writer, test-rigor-reviewer, coverage-analyst).

### Why add test architecture to a refactoring plugin?

The agents developed for refactoring and feature development produce code — but who tests the tests? The existing refactor-test agent runs tests and checks coverage, but it does not evaluate *test quality*. A test suite with 100% coverage can still be worthless if every assertion is tautological.

The test-architect skill addresses this gap with formal test design techniques: equivalence class partitioning, boundary value analysis, property-based testing, and mutation-aware assertions. These techniques produce tests that are systematically derived rather than ad-hoc, and the rigor reviewer scores each test on a 0.0-1.0 scale to quantify quality.

### Four specialist agents

The test-architect follows the same swarm orchestration pattern as /refactor and /feature-dev:

- **Test-planner** (read-only) — analyzes source code to produce JSON test plans using formal techniques. Analogous to the architect agent: it plans but does not implement.
- **Test-writer** (write-capable) — transforms JSON plans into idiomatic test code. Analogous to feature-code: it creates new files from specifications.
- **Test-rigor-reviewer** (read-only) — audits test suites for scientific rigor. Analogous to code-reviewer: it gates quality without modifying code.
- **Coverage-analyst** (read-only) — runs native coverage tools and recommends gap-closing tests. A new role without direct analogue in /refactor.

### Swarm orchestration reuse

The test-architect skill reuses the same orchestration primitives (TeamCreate, TaskCreate/TaskUpdate, SendMessage, blackboard) and team coordination patterns established in v2.0.0. The parallel execution point is Phase 3, where rigor review and coverage analysis run simultaneously — mirroring Phase 1 of /refactor where test analysis and architecture review run in parallel.

## v4.2.0: Mandatory test-architect integration in feature-dev

**v4.2.0** promotes the four test-architect agents from a standalone skill to a mandatory core pipeline within `/feature-dev`. The test-planner, test-writer, test-rigor-reviewer, and coverage-analyst now run as part of every feature development workflow, replacing the previous `refactor-test` agent.

### Why integrate test-architect into feature-dev?

The original feature-dev workflow used `refactor-test` for ad-hoc test generation — tests were written without formal techniques and without quality validation. This produced tests that compiled and passed but were often tautological or mutation-susceptible. A feature could ship with 100% coverage yet have worthless assertions.

By integrating the test-architect pipeline, tests are now:
- **Planned against the architecture** (Phase 4.5) — behavioral contracts are defined at design time, not reverse-engineered from implementation
- **Written from formal test plans** (Phase 5) — using equivalence class partitioning, boundary value analysis, and property-based testing
- **Quality-gated** (Phase 6) — rigor scores and coverage percentages must meet configurable thresholds before the feature can complete

### Why plan tests at Phase 4.5?

The test plan is most valuable when created against the *architecture blueprint*, not the implementation. At this point:
- The intended behavior is fresh and well-defined
- Design-level edge cases are visible (error paths, state transitions, integration contracts)
- The plan captures what the code *should* do, independent of how it actually does it

This is the highest-leverage moment for test design. A plan written after implementation tends to mirror the code rather than challenge it.

### The test_plan as a stable interface contract

In autonomous mode, the test plan from Phase 4.5 serves as the fixed fitness function. Unlike the previous design where `refactor-test` rewrote tests each iteration (allowing test drift), the test plan is now immutable once created. Implementations improve toward a stable target, keeping the convergence signal clean.

### Configurable quality gates

Quality gates are enforced via `featureDev.testArchitect` configuration:
- `minimumRigorScore` (default: 0.7) — tests must demonstrate scientific rigor
- `minimumCoverage` (default: 80%) — code must be adequately covered

The `enabled` flag allows operators to disable gates without editing the SKILL.md — useful for prototyping or CI environments where test planning adds unwanted latency. Gate overrides are explicitly auditable in the Phase 7 summary.

## Further reading

- [Agent Reference](../reference/agents.md) — detailed agent specifications and tool lists
- [Quality Score Reference](../reference/quality-scores.md) — scoring rubrics and criteria
- [Tutorial: Your First Refactor](../tutorials/tutorial.md) — see the orchestration in action
- [Understanding Test Design Techniques](test-design-techniques.md) — formal testing technique rationale
- [Tutorial: Your First Test Architecture](../tutorials/tutorial-test-architect.md) — see the test-architect in action

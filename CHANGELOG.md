# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.0.0] - 2026-03-19

### Added

- **`--autonomous` flag**: Karpathy autoresearch-style convergence loop for both `/refactor` and `/feature-dev` skills — replaces fixed iteration loop with keep/discard gating, composite scoring, and automatic convergence detection
- **Composite scoring system**: Weighted score from test pass rate (50%), code quality (25%), and security posture (25%) — configurable weights via `autonomous.scoreWeights`
- **Git branch snapshots**: `autoresearch/v0`, `v1`, ... branches for keep/discard state management — automatically cleaned up at finalization
- **Convergence detection**: Stop on perfect score (1.0), 3 consecutive reverts (stuck), score plateau (delta < 0.01 for 3 iterations), or max iterations (20)
- **convergence-reporter agent**: New specialist that analyzes loop results, computes score trajectories, generates diffs, and produces convergence reports with recommendations
- **code-reviewer Mode 5** (Autonomous Scoring): Structured JSON output (`review-scores.json`) with quality_score, security_score, and blocking_findings for the composite scoring system
- **refactor-test autonomous output**: Standardized `test-results.json` format for composite scoring regardless of test runner
- **Test freeze for refactor**: Tests frozen during autonomous refactor loop (run only, no creation) — prevents moving goalposts
- **Mutable tests for feature-dev**: Tests can be created/modified during autonomous feature-dev loop — new functionality needs new tests
- **Config `autonomous` section**: maxIterations, scoreWeights, and convergence thresholds
- **scripts/**: `git_snapshot.sh`, `score.sh`, `results_log.sh` — utility scripts for the convergence loop
- **references/autonomous-algorithm.md**: Formal algorithm specification
- **docs/explanation/autonomous-convergence.md**: Pattern explanation
- **docs/guides/use-autonomous-mode.md**: How-to guide
- 6 new eval cases (3 per skill) for autonomous mode

### Changed

- **8-agent architecture**: Added convergence-reporter to the roster (was 7 agents)
- **Config schema version**: Bumped to `"4.0"` with backward-compatible `autonomous` key (defaults applied when missing)
- **Plugin version**: 4.0.0
- **`--iterations` range**: Expanded to 1-20 when used with `--autonomous` (was 1-10)

## [3.1.0] - 2026-03-19

### Added

- **`/feature-dev` skill**: Guided feature development workflow with 7-phase interactive process — discovery with 95% confidence elicitation, parallel codebase exploration, clarifying questions, multi-perspective architecture design, implementation, quality review, and summary
- **feature-code agent**: New implementation specialist for feature development that reads architecture blueprints from blackboard and creates code following codebase conventions
- **Multi-instance agent spawning**: Same agent definition can be spawned multiple times with unique names and different focus areas (e.g., `code-explorer-1`, `code-explorer-2`, `code-explorer-3`)
- **Blackboard Protocol sections**: All 7 agents now document their blackboard read/write keys in a standardized table
- **Config `featureDev` section**: Configurable explorer/architect/reviewer instance counts, commit strategy, and PR creation for feature-dev workflow
- **Feature Architecture Design Mode** in architect agent: Designs implementation blueprints with pattern analysis, decisive architecture choices, and phased build sequences
- **Mode 4 — Feature Development Review** in code-reviewer agent: Focus-area reviews for simplicity/DRY, bugs/correctness, and conventions/abstractions
- **Interactive approval gates**: Feature-dev includes user decision points at elicitation, clarification, architecture selection, implementation start, and review disposition

### Changed

- **7-agent architecture**: Added feature-code to the roster (was 6 agents)
- **code-explorer**: Updated to serve both refactoring discovery AND feature-specific exploration with multi-instance support
- **architect**: Added Bash tool, feature architecture design mode, expanded core responsibilities
- **code-reviewer**: Added feature development review mode (Mode 4) with focus-area specialization
- **refactor-code**: Added Bash to allowed-tools
- **Config schema version**: Bumped to `"3.1"` with backward-compatible `featureDev` key (defaults applied when missing)
- **Plugin version**: 3.1.0

## [3.0.0] - 2026-03-18

### BREAKING CHANGES

- **Command removed**: `commands/refactor.md` deleted — use `skills/refactor.md` instead. The `/refactor` slash command is replaced by the `refactor` skill interface.
- **security-review agent removed**: Capabilities merged into `code-reviewer`. Any `--focus=security` runs now activate `code-reviewer` instead of `security-review`.
- **Config schema version**: Bumped to `"2.0"`. Existing `refactor.config.json` files will be auto-merged with new defaults, but the `version` field should be updated.
- **Focus flag values changed**: `security` now maps to `code-reviewer` (was `security-review`). New `discovery` value added. `code` now maps to `architect` + `code-reviewer` (was `architect` only).

### Added

- **code-explorer agent** (Phase 0.5): Deep codebase discovery runs first, producing structured codebase maps consumed by all downstream agents
- **Blackboard context sharing**: Explorer output distributed via Atlatl blackboard with inline fallback when MCP unavailable
- `--focus=discovery` focus area for code-explorer-only runs
- `skills/refactor.md` — new skill-based interface with full workflow rewrite

### Changed

- **6-agent architecture**: code-explorer, architect, code-reviewer, refactor-test, refactor-code, simplifier (was 5 agents)
- **Unified code-reviewer**: Merges quality review (confidence-scored, >=80 threshold) with security review (severity-classified, Critical/High = blocking) into single agent
- **All agents now use `sonnet` model** (Sonnet 4.6 1M context) — simplifier changed from `opus` to `sonnet`
- Phase 2 iteration cycle restructured: code review gate (Step 2.E) now precedes simplification (Step 2.F)
- Updated all documentation for 6-agent architecture

### Removed

- `agents/security-review.md` — capabilities merged into `code-reviewer`
- `commands/refactor.md` — replaced by `skills/refactor.md`
- `commands/` directory — removed (empty after command deletion)

## [2.2.0] - 2026-03-11

### Added

- `--focus=<area>[,area...]` CLI flag to constrain refactoring runs to specific disciplines
- Valid focus areas: `security`, `architecture`, `simplification`, `code`
- Union model for multi-focus: `--focus=security,architecture` spawns both discipline agents
- Focused runs default to 1 iteration (overridable with `--iterations=N`)
- Security Posture Score (1--10) rubric in quality scores reference
- Simplification Score (1--10) for simplification-focused runs
- Security-Review Agent section in agent reference
- Focus mode how-to guide (`docs/guides/focus-refactoring.md`)
- Focus mode troubleshooting entries
- CLI-Only Flags section in configuration reference
- Focus mode architecture explanation

### Changed

- Agent spawning is now conditional based on `active_agents` derived from `--focus`
- Phase tasks are gated on agent membership (skip steps for inactive agents)
- Commit messages and PR bodies include focus mode label when applicable
- Reports include only scores from active agents
- Updated agent count from "four" to "five" across documentation
- refactor-test and refactor-code always spawn as a safety invariant

## [2.1.0] - 2026-02-28

### Added

- Configuration-driven post-refactor workflow via `.claude/refactor.config.json`
- Interactive first-run setup wizard with AskUserQuestion prompts
- Commit strategies: none, per-iteration, single-final
- Optional PR creation (draft or ready-for-review) after refactoring
- Report publishing to GitHub Issues or GitHub Discussions
- Cross-referencing between PRs and published reports
- Non-blocking error handling for all GitHub operations
- Self-contained git operations (no external plugin dependencies)
- Diataxis-structured documentation (tutorial, how-to guides, reference, explanation)
- Social preview images (light + dark, illustrated SVG style)
- README infographic with theme-switching `<picture>` element

### Changed

- Replaced external `commit-commands:commit` skill references with inline git sequences
- Replaced external `commit-commands:commit-push-pr` skill references with inline gh CLI sequences
- Replaced `git add -A` with `git add -u` for safer staging
- Updated config schema version from 1.0 to 1.1
- Added `iterations` and `reportRepository` fields to config schema

## [2.0.0] - 2026-02-01

### Added

- Swarm orchestration (TeamCreate, TaskCreate/TaskUpdate, SendMessage)
- New simplifier agent (opus model) for code clarity passes
- Parallel execution in Phase 1 (foundation) and Phase 3 (final assessment)
- Code simplification step after each iteration cycle

### Changed

- 4-phase workflow replacing 7-step sequential process

### Removed

- Sequential execution model

## [1.0.0] - 2026-01-01

### Added

- Initial release with sequential 7-step workflow
- Three agents: architect, refactor-test, refactor-code

[Unreleased]: https://github.com/zircote/refactor/compare/v4.0.0...HEAD
[4.0.0]: https://github.com/zircote/refactor/compare/v3.1.0...v4.0.0
[3.1.0]: https://github.com/zircote/refactor/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/zircote/refactor/compare/v2.2.0...v3.0.0
[2.2.0]: https://github.com/zircote/refactor/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/zircote/refactor/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/zircote/refactor/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/zircote/refactor/releases/tag/v1.0.0

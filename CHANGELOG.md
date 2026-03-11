# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[2.2.0]: https://github.com/zircote/refactor/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/zircote/refactor/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/zircote/refactor/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/zircote/refactor/releases/tag/v1.0.0

---
diataxis_type: reference
diataxis_describes: refactor plugin configuration schema and options
---

# Configuration Reference

The refactor plugin uses a project-level configuration file at `.claude/refactor.config.json` to control iteration count and post-refactor GitHub integration (commits, PRs, issues, discussions).

## First Run Behavior

If no config file exists, the plugin runs an interactive setup wizard. Your answers are saved to `.claude/refactor.config.json` for all future runs.

On subsequent runs, the config file is loaded silently.

## Schema

```json
{
  "version": "4.0",
  "iterations": 3,
  "postRefactor": {
    "commitStrategy": "none",
    "createPR": false,
    "prDraft": true,
    "publishReport": "none",
    "discussionCategory": "General",
    "reportRepository": null
  },
  "featureDev": {
    "explorerCount": 3,
    "architectCount": 3,
    "reviewerCount": 3,
    "commitStrategy": "single-final",
    "createPR": false,
    "prDraft": true,
    "testArchitect": {
      "enabled": true,
      "minimumRigorScore": 0.7,
      "minimumCoverage": 80
    }
  }
}
```

The `featureDev` section is optional. If missing, all defaults are applied silently. Existing config files without `featureDev` continue to work — the key is merged in-memory at runtime.

## Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | `string` | `"4.0"` | Config schema version |
| `iterations` | `integer` | `3` | Number of refactoring iterations (1--10, overridable with `--iterations=N`) |
| `commitStrategy` | `"none"` \| `"per-iteration"` \| `"single-final"` | `"none"` | Controls when/if git commits happen |
| `createPR` | `boolean` | `false` | Whether to open a PR after refactoring |
| `prDraft` | `boolean` | `true` | If PR is created, make it a draft (only relevant when `createPR: true`) |
| `publishReport` | `"none"` \| `"github-issue"` \| `"github-discussion"` | `"none"` | Where to publish the final refactor report |
| `discussionCategory` | `string` | `"General"` | GitHub Discussion category name (only relevant when `publishReport: "github-discussion"`) |
| `reportRepository` | `string \| null` | `null` | Owner/repo to publish the report to (`null` = current repository) |

## Commit Strategy Options

### `"none"` (default)

No automatic commits. You handle git yourself. Matches v2.0.0 behavior.

### `"per-iteration"`

Commits after each iteration completes (Step 2.G).

Message format: `refactor(iteration 1/3): {summary}`

### `"single-final"`

Single commit after all iterations and final assessment.

Message format: `refactor: {scope} — clean code 8/10, architecture 9/10`

## Pull Request Options

| Setting | Behavior |
|---------|----------|
| `createPR: false` | No PR created (default) |
| `createPR: true, prDraft: true` | Draft PR created after refactoring |
| `createPR: true, prDraft: false` | Ready-for-review PR created after refactoring |

When a PR is created, the plugin will:
- Create a `refactor/{scope}-{date}` branch if you are on a default branch
- Include the refactor report summary and quality scores in the PR body
- Cross-reference any issue or discussion created by `publishReport`

## Report Publishing Options

### `"none"` (default)

Report saved as a local file only (`refactor-result-{timestamp}.md`).

### `"github-issue"`

Creates a GitHub issue with the refactor report.

- Title: `Refactor Report: {scope} — {date}`
- Label: `refactoring`

### `"github-discussion"`

Creates a GitHub Discussion in the configured category.

- Title: `Refactor Report: {scope} — {date}`
- Category: value of `discussionCategory` (default: `"General"`)

## Example Configurations

**Commit per iteration, no PR or publishing:**
```json
{
  "version": "4.0",
  "iterations": 3,
  "postRefactor": {
    "commitStrategy": "per-iteration",
    "createPR": false,
    "prDraft": true,
    "publishReport": "none",
    "discussionCategory": "General",
    "reportRepository": null
  }
}
```

**Full workflow — single commit, draft PR, issue report:**
```json
{
  "version": "4.0",
  "iterations": 3,
  "postRefactor": {
    "commitStrategy": "single-final",
    "createPR": true,
    "prDraft": true,
    "publishReport": "github-issue",
    "discussionCategory": "General",
    "reportRepository": null
  }
}
```

**Discussion-based reporting with ready-for-review PR:**
```json
{
  "version": "4.0",
  "iterations": 5,
  "postRefactor": {
    "commitStrategy": "single-final",
    "createPR": true,
    "prDraft": false,
    "publishReport": "github-discussion",
    "discussionCategory": "Engineering",
    "reportRepository": null
  }
}
```

## Feature-Dev Configuration (`featureDev`)

These fields configure the `/feature-dev` skill. They live under the `featureDev` key and are entirely independent of the `/refactor` settings above.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `explorerCount` | `integer` | `3` | Number of parallel code-explorer instances in Phase 2 (scaled by complexity) |
| `architectCount` | `integer` | `3` | Number of parallel architect instances in Phase 4 (scaled by complexity) |
| `reviewerCount` | `integer` | `3` | Number of parallel code-reviewer instances in Phase 6 (scaled by complexity) |
| `commitStrategy` | `"none"` \| `"single-final"` | `"single-final"` | When to commit feature changes |
| `createPR` | `boolean` | `false` | Whether to open a PR after feature development |
| `prDraft` | `boolean` | `true` | If PR is created, make it a draft |

**Complexity-based scaling:** The skill may reduce instance counts for simple features (e.g., 1 explorer instead of 3 for a trivial endpoint). The configured values are maximums.

### Test Architecture Integration (`testArchitect`)

The `testArchitect` sub-key under `featureDev` controls the mandatory test architecture pipeline integrated into the feature-dev workflow.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | `boolean` | `true` | Enable Phase 4.5 test planning and Phase 6 quality gates. When `false`, Phase 4.5 is skipped and test-writer generates tests from the feature spec only. |
| `minimumRigorScore` | `float` | `0.7` | Minimum test rigor score (0.0–1.0) to pass the Phase 6 quality gate |
| `minimumCoverage` | `integer` | `80` | Minimum test coverage percentage to pass the Phase 6 quality gate |

When quality gates fail, the user can choose to fix (max 2 re-validation loops), override (proceed with documented exception), or abandon. Overrides surface in the Phase 7 summary.

**Example — feature-dev with PR creation:**
```json
{
  "version": "4.0",
  "iterations": 3,
  "postRefactor": { "..." },
  "featureDev": {
    "explorerCount": 3,
    "architectCount": 3,
    "reviewerCount": 3,
    "commitStrategy": "single-final",
    "createPR": true,
    "prDraft": true,
    "testArchitect": {
      "enabled": true,
      "minimumRigorScore": 0.7,
      "minimumCoverage": 80
    }
  }
}
```

## Project Plan Configuration (`projectPlan`)

These fields configure the `/project-plan` skill. They live under the `projectPlan` key and are entirely independent of the `/refactor` and `/feature-dev` settings above.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `projectNumber` | `integer \| null` | `null` | GitHub Projects v2 board number. `null` = auto-detect from `gh project list`. |
| `projectOwner` | `string \| null` | `null` | Board owner (`@me`, org name). `null` = current user. |
| `defaultMode` | `"interactive" \| "autonomous"` | `"interactive"` | Default mode when no flag provided. |
| `sprintLength` | `integer` | `14` | Sprint duration in days. Used for sprint planning heuristics. |
| `autoArchiveDays` | `integer` | `14` | Days after which Done items are auto-archived. |
| `enableUiOps` | `boolean` | `false` | Enable Chrome DevTools UI operations by default. |
| `uiOps.views` | `boolean` | `true` | Create/update board views during UI ops. |
| `uiOps.workflows` | `boolean` | `true` | Configure board automation workflows during UI ops. |
| `uiOps.verification` | `boolean` | `true` | Screenshot-verify UI operations. |

The `projectPlan` section is optional. If missing, all defaults are applied silently. The skill merges missing keys with defaults at runtime — partial config is fine.

**Example — project plan with explicit board and autonomous default:**
```json
{
  "version": "4.0",
  "iterations": 3,
  "postRefactor": { "..." },
  "featureDev": { "..." },
  "projectPlan": {
    "projectNumber": 3,
    "projectOwner": "@me",
    "defaultMode": "autonomous",
    "sprintLength": 14,
    "autoArchiveDays": 14,
    "enableUiOps": false,
    "uiOps": {
      "views": true,
      "workflows": true,
      "verification": true
    }
  }
}
```

## Error Handling

All GitHub operations are non-blocking. If any operation fails (e.g., `gh` not authenticated, no remote configured), the plugin logs a warning and continues. The refactor workflow is never blocked by a publishing or PR creation failure.

## Process Defaults

| Parameter | Default |
|-----------|---------|
| Max iterations | 3 |
| Optimizations per iteration | Top 3 |
| Test coverage target | Production quality (typically 80%+) |
| Focused iteration default | 1 |

## CLI-Only Flags

These flags are available only on the command line and are not stored in the config file.

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--autonomous` | (boolean flag) | off | Enable autonomous convergence mode |
| `--iterations=N` | `1`--`10` (standard) or `1`--`20` (autonomous) | Config value | Override iteration count for this run |
| `--focus=<area>[,area...]` | `security`, `architecture`, `simplification`, `code`, `discovery` | (none — full run) | Constrain run to specific disciplines. Comma-separated for multiple areas. |

### --focus details

Valid focus values and their effect on agent spawning:

| Focus value | Additional agents spawned |
|-------------|--------------------------|
| `security` | code-reviewer |
| `architecture` | architect |
| `simplification` | simplifier |
| `code` | architect + code-reviewer |
| `discovery` | code-explorer |
| `testing` | test-planner, test-writer, test-rigor-reviewer, coverage-analyst |

The refactor-test and refactor-code agents always spawn regardless of focus.

When `--focus` is provided, the default iteration count changes to **1** (overridable with `--iterations=N`).

Multiple focus values are combined as a union: `--focus=security,architecture` spawns both code-reviewer and architect in addition to the always-present pair.

## Test-Architect Configuration (`testArchitect`)

The `/test-gen`, `/test-plan`, and `/test-eval` commands use project auto-detection and require no configuration file. Language, test framework, and coverage tool are detected automatically from project files (Cargo.toml, pyproject.toml, package.json, go.mod).

### Detection Defaults

| Language | Test Runner | Coverage Tool | Property Library |
|----------|------------|---------------|-----------------|
| Rust | cargo test | cargo-tarpaulin | proptest |
| Python | pytest | coverage.py | hypothesis |
| TypeScript | vitest | c8 | fast-check |
| Go | go test | go tool cover | rapid |

The standalone `/test-gen`, `/test-plan`, `/test-eval` commands require no configuration key — all settings are auto-detected. If you need to override detection, specify the target path explicitly in the command arguments.

When test-architect agents run as part of `/feature-dev` (Phase 4.5 and Phase 6), they use the `featureDev.testArchitect` configuration section for quality gate thresholds. See [Test Architecture Integration](#test-architecture-integration-testarchitect) above.

## Autonomous Mode Configuration (`autonomous`)

These fields configure the `--autonomous` convergence loop. They live under the `autonomous` key and apply to both `/refactor --autonomous` and `/feature-dev --autonomous`.

```json
{
  "autonomous": {
    "maxIterations": 20,
    "scoreWeights": {
      "tests": 0.50,
      "quality": 0.25,
      "security": 0.25
    },
    "convergence": {
      "perfectScore": 1.0,
      "plateauDelta": 0.01,
      "plateauWindow": 3,
      "maxConsecutiveReverts": 3
    }
  }
}
```

### Score Weights

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tests` | `float` | `0.50` | Weight for test pass rate in composite score |
| `quality` | `float` | `0.25` | Weight for code quality score (from code-reviewer Mode 5) |
| `security` | `float` | `0.25` | Weight for security posture score (from code-reviewer Mode 5) |

Weights must sum to 1.0.

### Convergence Thresholds

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `perfectScore` | `float` | `1.0` | Score at which the loop stops (perfect convergence) |
| `plateauDelta` | `float` | `0.01` | Minimum score improvement to count as progress |
| `plateauWindow` | `integer` | `3` | Number of iterations with delta < plateauDelta before declaring plateau |
| `maxConsecutiveReverts` | `integer` | `3` | Number of consecutive reverts before declaring stuck |

### Other

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `maxIterations` | `integer` | `20` | Default max iterations for autonomous mode (overridable with `--iterations=N`) |

## See Also

- [How to Use Autonomous Mode](../guides/use-autonomous-mode.md)
- [Understanding Autonomous Convergence](../explanation/autonomous-convergence.md)
- [How to Configure Commit Strategies](../guides/configure-commits.md)
- [How to Generate and Evaluate Tests](../guides/use-test-gen.md)
- [Tutorial: Your First Refactor](../tutorials/tutorial.md)

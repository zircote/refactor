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
  "version": "1.1",
  "iterations": 3,
  "postRefactor": {
    "commitStrategy": "none",
    "createPR": false,
    "prDraft": true,
    "publishReport": "none",
    "discussionCategory": "General",
    "reportRepository": null
  }
}
```

## Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | `string` | `"1.1"` | Config schema version |
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
  "version": "1.1",
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
  "version": "1.1",
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
  "version": "1.1",
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
| `--iterations=N` | `1`--`10` | Config value (3) | Override iteration count for this run |
| `--focus=<area>[,area...]` | `security`, `architecture`, `simplification`, `code` | (none — full run) | Constrain run to specific disciplines. Comma-separated for multiple areas. |

### --focus details

Valid focus values and their effect on agent spawning:

| Focus value | Additional agents spawned |
|-------------|--------------------------|
| `security` | security-review |
| `architecture` | architect |
| `simplification` | simplifier |
| `code` | architect |

The refactor-test and refactor-code agents always spawn regardless of focus.

When `--focus` is provided, the default iteration count changes to **1** (overridable with `--iterations=N`).

Multiple focus values are combined as a union: `--focus=security,architecture` spawns both security-review and architect in addition to the always-present pair.

## See Also

- [How to Configure Commit Strategies](../guides/configure-commits.md)
- [Tutorial: Your First Refactor](../tutorial.md)

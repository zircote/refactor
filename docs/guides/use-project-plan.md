---
diataxis_type: how-to
diataxis_goal: Manage GitHub Projects v2 boards with the /project-plan skill across common scenarios
---

# How to Use Project Planning

## Overview

This guide covers practical scenarios for managing GitHub Projects v2 boards with `/project-plan`. Each section addresses a specific task -- from cleaning up a board to running autonomous planning across a fleet of repositories.

## Prerequisites

- The refactor plugin loaded via `--plugin-dir`
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated
- A GitHub Projects v2 board (the skill can create one if needed)
- First-run setup completed (see [Tutorial: Project Plan](../tutorials/tutorial-project-plan.md))

## Steps

### 1. Archive stale Done items

Run board hygiene to archive items that have been in the Done column longer than the configured threshold (default: 14 days):

```bash
/project-plan
```

Select "Board hygiene" as the goal. The changeset includes `ARCHIVE` operations for stale Done items with 0.95 confidence. Apply the auto-apply operations.

To change the archive threshold, edit `.claude/refactor.config.json`:

```json
{
  "projectPlan": {
    "autoArchiveDays": 7
  }
}
```

### 2. Sync orphaned issues to the board

Issues can fall off the board when created via `gh issue create` or the GitHub UI without adding them to the project. Board hygiene detects these:

```bash
/project-plan
```

The changeset includes `ADD` operations for open issues not tracked on the board. Each is added with Status set to Todo.

### 3. Fix stale In Progress items

Items sitting in In Progress with no PR activity for more than `autoArchiveDays` are flagged as stale. Board hygiene proposes moving them back to Todo with a note:

```bash
/project-plan
```

Review the `MOVE` operations in the changeset. These have 0.80 confidence -- high enough for auto-apply but worth reviewing if you want to keep items in progress.

### 4. Plan a sprint

Select work for the next sprint based on priority signals, milestone proximity, and project goals:

```bash
/project-plan plan my sprint
```

The skill scores all unplanned Todo items and proposes Sprint field assignments for the top candidates. The number of items selected scales with your configured sprint length (default: `sprintLength / 2`, capped at 15).

If your CLAUDE.md includes active priorities, items matching those priorities receive a confidence boost.

### 5. Prioritize the backlog

Rank current items by impact and urgency:

```bash
/project-plan prioritize
```

The skill uses label signals (`priority:high`, `priority:low`), issue age, cross-references, and constitution goals (if available) to propose Priority field values. Lower-confidence suggestions (0.55--0.85) appear as suggestions you can accept or skip.

### 6. Run autonomous board hygiene across repos

For fleet management across many repositories, use autonomous mode:

```bash
/project-plan --autonomous
```

This runs the full board hygiene workflow with zero prompts:
- Archives stale Done items
- Adds orphaned issues
- Flags stale In Progress items
- Fills missing fields from labels and milestones
- Syncs status from issue/PR state

All operations with confidence >= 0.70 are applied automatically. Lower-confidence operations appear in the summary as suggestions.

### 7. Preview changes without applying

Use dry-run mode to see what the skill would do:

```bash
/project-plan --dry-run
```

This generates and displays the changeset without executing any mutations. Combine with `--autonomous` to preview batch behavior:

```bash
/project-plan --autonomous --dry-run
```

### 8. Enable UI operations

For operations that have no CLI equivalent (board views, item reordering, column visibility), enable UI operations:

```bash
/project-plan --ui-ops
```

This requires Chrome DevTools MCP tools to be loaded. The skill navigates to your board in the browser, creates views ("By Sprint", "Blocked Items", "Stale Items"), and reorders items to match priority.

### 9. Configure project-plan settings

Edit `.claude/refactor.config.json` to customize behavior:

```json
{
  "projectPlan": {
    "projectNumber": 1,
    "projectOwner": "your-username",
    "defaultMode": "interactive",
    "sprintLength": 14,
    "autoArchiveDays": 14,
    "enableUiOps": false
  }
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `projectNumber` | `null` (auto-detect) | GitHub Projects v2 board number |
| `projectOwner` | `null` (auto-detect) | Board owner (user or org) |
| `defaultMode` | `interactive` | Default mode when no flags are passed |
| `sprintLength` | `14` | Sprint duration in days |
| `autoArchiveDays` | `14` | Days in Done before auto-archive |
| `enableUiOps` | `false` | Enable browser-based UI operations |

### 10. Strengthen goal alignment with CLAUDE.md

The skill reads CLAUDE.md as a project constitution. To improve alignment scoring, include these sections:

- **Mission/Purpose** -- what the project does
- **Active Priorities** -- current goals, milestones, or focus areas
- **Constraints** -- rules, restrictions, hard requirements
- **Branching Strategy** -- branch model and PR targets
- **Build & Test** -- commands to validate changes
- **Commit Conventions** -- message format and rules

Projects with 4+ dimensions get full constitution-driven alignment. Projects with fewer dimensions still work -- the skill focuses on board hygiene instead of goal alignment.

## Related

- [Tutorial: Project Plan](../tutorials/tutorial-project-plan.md) -- guided walkthrough for first-time use
- [Configuration Reference](../reference/configuration.md) -- full config schema
- [Git Workflow Commands](../reference/git-commands.md) -- commands for commit, push, PR, and sync workflows

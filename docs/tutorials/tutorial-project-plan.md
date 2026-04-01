---
diataxis_type: tutorial
diataxis_learning_goals:
  - Run the /project-plan skill to manage a GitHub Projects v2 board
  - Understand the constitution-driven goal alignment system
  - Perform board hygiene and sprint planning
  - Use autonomous mode for zero-touch batch operations
---

# Tutorial: Managing Your Project Board with /project-plan

In this tutorial, we will use the `/project-plan` skill to snapshot a GitHub Projects v2 board, run board hygiene, and plan a sprint. By the end, you will understand how the skill reads your project's CLAUDE.md as a constitution, generates changesets, and applies them to your board.

## What you'll learn

- How `/project-plan` reads CLAUDE.md to align board operations with project goals
- How the board snapshot and changeset system works
- How to run interactive board hygiene (archive stale items, sync orphaned issues)
- How to use autonomous mode for zero-touch operation across many repos
- How to plan a sprint by scoring and selecting items

## Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) CLI installed
- The refactor plugin loaded via `--plugin-dir`
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated
- A GitHub Projects v2 board linked to a repository with open issues
- (Optional) A `CLAUDE.md` file in the project root with mission, priorities, or constraints

## Steps

### Step 1: Run your first board hygiene session

Start with an interactive session to see what the skill does before enabling autonomous mode:

```bash
/project-plan
```

On first run, the skill asks three setup questions:

1. **Project Board** -- select which GitHub Projects v2 board to manage. The skill auto-detects available boards.
2. **Sprint Length** -- choose your sprint duration (default: 2 weeks).
3. **UI Operations** -- whether to enable browser-based board operations (default: no).

Your answers are saved to `.claude/refactor.config.json` for future runs.

After setup, the skill prompts you to choose a session goal. Select "Board hygiene" to start.

### Step 2: Observe the constitution reading

The skill reads your project's `CLAUDE.md` (or `.claude/CLAUDE.md`) and extracts six dimensions:

- Mission/Purpose
- Branching Strategy
- Build & Test commands
- Commit Conventions
- Active Priorities
- Constraints

You will see a completeness score. If your CLAUDE.md covers 4 or more dimensions, the skill uses it to align board operations with your stated goals. If your CLAUDE.md is sparse, the skill still works -- it focuses on board hygiene without alignment scoring.

### Step 3: Review the board snapshot

The skill fetches your board state and cross-references it with open issues and PRs. You will see:

- Items grouped by status (Todo, In Progress, Done)
- Stale items (In Progress with no recent activity)
- Archive candidates (Done items older than the configured threshold)
- Orphaned issues (open issues not on the board)
- Missing fields (items without priority, sprint, or assignee)

### Step 4: Review and apply the changeset

The skill generates a changeset -- an ordered list of proposed operations:

```
CHANGESET (8 operations, 6 auto-apply, 2 suggestions)
──────────────────────────────────────────────────────
  Op       Target                       Field     From → To         Conf
  ──────   ─────────────────────────    ───────   ──────────────    ────
✓ ARCHIVE  "Fix typo in README"         —         Done 21d ago      0.95
✓ ADD      Issue #45 "Add retry logic"  Status    — → Todo          0.90
✓ MOVE     "API redesign"               Status    InProgress→Todo   0.80
⚑ SUGGEST  "Refactor tests"             Priority  Low → Medium      0.65
```

Operations with confidence >= 0.70 are marked with a check for auto-apply. Lower-confidence operations are suggestions only.

Choose "Apply all auto-apply operations" to execute the high-confidence changes. The skill runs `gh project` commands to archive, add, move, and edit items on your board.

### Step 5: Plan a sprint

Run the skill again with a sprint planning goal:

```bash
/project-plan plan my sprint
```

The skill performs board hygiene first (baseline cleanup), then scores unplanned Todo items by:

- Label priority signals
- Milestone proximity
- Dependency count
- Constitution alignment (if your CLAUDE.md has stated priorities)

It proposes a set of items for the current sprint and assigns the Sprint field. Review the selections and approve.

### Step 6: Try autonomous mode

Once you are comfortable with the interactive workflow, try autonomous mode for zero-touch operation:

```bash
/project-plan --autonomous
```

In autonomous mode, the skill skips all prompts, detects the goal automatically (defaults to board-hygiene), and applies all operations with confidence >= 0.70. This is the mode designed for running across many repos in batch.

**Preview without changes:**

```bash
/project-plan --autonomous --dry-run
```

This shows the full changeset without executing any mutations.

## What you've accomplished

You have:

- Configured the project-plan skill for your board
- Observed how CLAUDE.md serves as a constitution for goal alignment
- Run board hygiene to archive stale items, sync orphaned issues, and fill missing fields
- Planned a sprint with prioritized item selection
- Used autonomous mode for zero-touch operation

## Next steps

- [How to Use Project Planning](../guides/use-project-plan.md) -- practical scenarios for board management
- [Configuration Reference](../reference/configuration.md) -- `projectPlan` config settings
- [Architecture: Swarm Orchestration Design](../explanation/architecture.md) -- how agents collaborate

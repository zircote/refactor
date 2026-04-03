---
name: project-plan
description: "Goal-driven GitHub Projects v2 planning skill. Reads CLAUDE.md as project constitution, snapshots board state, elicits session goals, and generates board changesets. Supports autonomous batch mode for multi-repo planning. Use when: project planning, board management, sprint planning, plan sprint, update board, session goals, board hygiene, what should I work on, project-plan, organize my board, prioritize items, sync issues to board."
argument-hint: "[--autonomous] [--ui-ops] [--dry-run] [goal description]"
---

# Project Plan Skill

You manage GitHub Projects v2 boards by reading the project's CLAUDE.md as a constitution, snapshotting board state, eliciting session goals, and generating changesets that move the board toward the desired state. The autonomous path is primary — this skill runs across 190 repos in batch mode with zero human intervention.

## Bundled Resources

### References (consult during execution)
- `references/github-projects-v2-api.md` — GraphQL mutations, field type mapping, ID resolution patterns for operations not covered by `gh project` CLI.
- `references/chrome-devtools-board-ops.md` — GitHub Projects v2 board DOM structure, UI automation patterns, screenshot verification for Phase 6.

## Help Check

If `$ARGUMENTS` is `help`, `--help`, or `-h`, print this and stop:

```
PROJECT-PLAN(1)              GPM Skills Manual              PROJECT-PLAN(1)

NAME
    project-plan — goal-driven GitHub Projects v2 board management

SYNOPSIS
    /project-plan [--autonomous] [--ui-ops] [--dry-run] [goal description]

DESCRIPTION
    Reads the project's CLAUDE.md as a constitution, snapshots the current
    GitHub Projects v2 board state, determines a session goal, and generates
    a changeset of board operations. Supports autonomous batch mode for
    multi-repo fleet management.

MODES
    interactive (default)
        Elicits session goal via prompt. Presents changeset for approval
        before executing mutations.

    --autonomous
        Zero-touch mode. Detects goal from arguments or defaults to
        board-hygiene. Auto-applies operations with confidence >= 0.70.


    --dry-run
        Generates and prints the changeset but executes no mutations.
        Combinable with --autonomous or interactive mode.

    --ui-ops
        Enables Chrome DevTools MCP browser automation for UI-only
        operations (board views, item reordering). Requires Chrome
        DevTools MCP tools to be loaded.

GOAL STRATEGIES
    board-hygiene    Archive stale Done items, fix stale statuses, sync
                     orphaned issues, fill missing fields. (autonomous default)
    sprint-plan      Select and prioritize items for the next sprint.
    prioritize       Rank current items by impact and urgency.
    board-sync       Ensure all open issues are tracked on the board.

EXAMPLES
    /project-plan                              Interactive goal elicitation
    /project-plan --autonomous                 Batch board hygiene
    /project-plan --autonomous plan my sprint  Autonomous sprint planning
    /project-plan --dry-run --autonomous       Preview changeset only
    /project-plan --autonomous --ui-ops        Full pipeline with UI ops
    /project-plan what should I work on next   Interactive prioritization
```

## Arguments

**$ARGUMENTS**: Optional mode flags and goal description.

Parse `$ARGUMENTS` before any other processing:

1. Extract flags:
   - `--autonomous` → set `autonomous_mode = true`
   - `--ui-ops` → set `ui_ops_mode = true`
   - `--dry-run` → set `dry_run_mode = true`
   - `--help`, `-h`, `help` → print help text above and stop

2. Remaining text after flag extraction → store as `goal_text` (used in Phase 3 for goal detection)

3. Mode resolution precedence: flag > config (`projectPlan.defaultMode`) > default (`interactive`)

---

## Phase 0: Bootstrap

### Step 0.1: Atlatl Context

Search for prior planning context:
```
recall_memories(query="project planning board management sprint")
recall_memories(query="project-plan skill preferences goals")
```

Apply matching results to inform subsequent phases.

### Step 0.2: Load or Create Configuration

1. Read `.claude/refactor.config.json` from the project root
2. Extract the `projectPlan` section. Merge with defaults for any missing keys:
   ```json
   {
     "projectNumber": null,
     "projectOwner": null,
     "defaultMode": "interactive",
     "sprintLength": 14,
     "autoArchiveDays": 14,
     "enableUiOps": false,
     "uiOps": {
       "views": true,
       "workflows": true,
       "verification": true
     }
   }
   ```
3. **If config file exists**: Parse silently. Missing `projectPlan` key → use all defaults. Proceed.
4. **If config file does NOT exist AND `autonomous_mode`**: Use all defaults silently. Do not prompt. Proceed.
5. **If config file does NOT exist AND NOT `autonomous_mode`**: Run interactive setup (Step 0.3)

### Step 0.3: Interactive Setup (First Run Only — skipped in autonomous mode)

Run the following **AskUserQuestion** prompts sequentially:

1. **Q1** (header: "Project Board"): "Which GitHub Projects v2 board should this skill manage?"
   - First run `gh project list --owner @me --format json` to detect available boards
   - Options:
     - "{auto-detected board name} (#{number})" *(default)* — if a board was detected
     - "Enter board number manually" → free-text follow-up for number
     - "Skip — I'll configure later" *(default if no boards detected)* → `projectNumber: null`

2. **Q2** (header: "Sprint Length"): "How long are your sprints?"
   - Options:
     - "2 weeks" *(default)* → `sprintLength: 14`
     - "1 week" → `sprintLength: 7`
     - "3 weeks" → `sprintLength: 21`
     - "4 weeks" → `sprintLength: 28`

3. **Q3** (header: "UI Operations"): "Enable browser-based UI operations? (requires Chrome DevTools MCP)"
   - Options:
     - "No — CLI/API only" *(default)* → `enableUiOps: false`
     - "Yes — also manage views, ordering, and visual layout" → `enableUiOps: true`

Merge the `projectPlan` section into `.claude/refactor.config.json` using `jq` (per /xq rules — never use Write for JSON mutations). Construct the projectPlan object inline with `--argjson` using the values from Q1–Q3:
```bash
# Example with collected values (substitute actuals):
if [ -f .claude/refactor.config.json ]; then
  jq '.projectPlan = {"board": "MyBoard", "sprintLength": 14, "enableUiOps": false}' \
    .claude/refactor.config.json > tmp.$$ && mv tmp.$$ .claude/refactor.config.json
else
  jq -n '{"projectPlan": {"board": "MyBoard", "sprintLength": 14, "enableUiOps": false}}' \
    > .claude/refactor.config.json
fi
```
Validate: `jq empty .claude/refactor.config.json`. Store as `config`.

### Step 0.4: Detect Current Repository

Run `gh repo view --json owner,name,url` to determine the current repo context. Store as `repo`.

---

## Phase 1: Constitution Reading

Read the project's CLAUDE.md as a constitution for goal alignment.

### Step 1.1: Locate Constitution

1. Try `.claude/CLAUDE.md` (project-level)
2. Fall back to `CLAUDE.md` (repo root)
3. If neither exists: set `constitution.completeness = 0`, skip to Phase 2

### Step 1.2: Extract Dimensions

Parse the CLAUDE.md for these 6 dimensions. Each extraction is independent — missing sections are null, not errors. Use fuzzy section matching (keyword detection, not exact header matching):

| Dimension | Keywords to Match | What to Extract |
|-----------|------------------|-----------------|
| **Mission/Purpose** | project, mission, purpose, overview, about | First heading or paragraph describing what the repo does |
| **Branching Strategy** | branch, branching, PR, merge, main, develop | Branch model, PR targets, protected branches |
| **Build & Test** | build, test, make, npm, cargo, check, CI | Commands to validate changes |
| **Commit Conventions** | commit, conventional, message, format | Commit message format and rules |
| **Active Priorities** | priority, goal, milestone, roadmap, current, focus, sprint | Stated goals, milestones, or current focus areas |
| **Constraints** | constraint, rule, requirement, forbidden, never, must | Rules, restrictions, and hard requirements |

### Step 1.3: Score Completeness

Count how many of the 6 dimensions were found (non-null). Calculate `completeness = found / 6`:

| Completeness | Behavior |
|-------------|----------|
| >= 70% (4+ dimensions) | Full constitution. Use for alignment scoring in Phase 4. |
| 50-69% (3 dimensions) | Partial constitution. Use what's available, note gaps. |
| < 50% (0-2 dimensions) | Minimal constitution. Skip alignment scoring. Focus on board hygiene. |

Store as `constitution` object with extracted fields and completeness score.

**Key pragmatism**: Do not fail, warn loudly, or ask the user to improve their CLAUDE.md on sparse input. Most repos in a 190-repo fleet will have minimal or no CLAUDE.md. The skill is still useful — it just focuses on board hygiene rather than goal alignment.

---

## Phase 2: Board Snapshot

### Step 2.1: Determine Project Board

Resolution order:
1. `config.projectPlan.projectNumber` + `config.projectPlan.projectOwner` if set in config
2. Else: `gh project list --owner @me --format json` → pick the first (or most recently updated) board
3. If no board found:
   - **Autonomous mode**: Skip all board operations silently. Note in summary: "No board found — board operations skipped." Proceed to Phase 7.
   - **Interactive mode**: Use **AskUserQuestion** (header: "No Board Found"): "No GitHub Projects v2 board found. Would you like to create one?"
     - "Yes — create a new board" → `gh project create --owner @me --title "{repo name} Board"` → continue with new board
     - "No — skip board operations" → proceed to Phase 7

### Step 2.2: Snapshot Board State

```bash
# Get project fields (status columns, custom fields)
gh project field-list {number} --owner {owner} --format json

# Get all board items
gh project item-list {number} --owner {owner} --format json --limit 500
```

Parse into structured state:
- **Items by status**: Group by status column (Todo / In Progress / Done / custom)
- **Stale items**: In Progress items with no PR activity in `autoArchiveDays`+ days
- **Missing fields**: Items without priority, sprint, or assignee
- **Archive candidates**: Done items older than `autoArchiveDays`
- **Field ID map**: Map field names → field IDs and option names → option IDs (needed for mutations in Phase 5)

### Step 2.3: Fetch Open Work

```bash
# Open issues for current repo
gh issue list --state open --json number,title,labels,milestone,assignees,updatedAt --limit 200

# Open PRs for current repo
gh pr list --state open --json number,title,labels,headRefName,updatedAt --limit 50
```

Cross-reference with board items to identify:
- **Orphaned issues**: Open issues not on the board
- **Orphaned PRs**: Open PRs whose issues are not on the board
- **Stale references**: Board items whose issues are closed

---

## Phase 3: Goal Elicitation

### Step 3.1: Autonomous Goal Detection

If `autonomous_mode`:
- Parse `goal_text` (remaining arguments after flags) using phrase detection:

| Phrase Pattern | Goal Strategy |
|---------------|--------------|
| "plan sprint", "sprint planning", "next sprint" | `sprint-plan` |
| "what should I work on", "priorities", "prioritize", "rank" | `prioritize` |
| "clean up", "hygiene", "organize", "tidy" | `board-hygiene` |
| "sync", "update board", "sync board", "orphan" | `board-sync` |
| No match or empty | `board-hygiene` (safe default) |

- Multiple goals can combine: "clean up and sync" → `board-hygiene` + `board-sync`
- Store as `session_goal`

### Step 3.2: Interactive Goal Elicitation

If NOT `autonomous_mode`:
- Always present the goal selection via **AskUserQuestion**, even if `goal_text` suggests a goal via phrase detection. If a phrase was detected, pre-select it as the default option so the user can confirm with one click — but never skip the prompt entirely in interactive mode.
- Use **AskUserQuestion**:

  **Q1** (header: "Session Goal"): "What would you like to accomplish?"
  - "Board hygiene — archive done items, fix stale statuses, fill gaps" *(default)*
  - "Sprint planning — select and prioritize work for the next sprint"
  - "Prioritize — rank current items by impact and urgency"
  - "Board sync — ensure all open issues are tracked on the board"
  - "Custom goal" → free-text follow-up

- Store as `session_goal`

### Step 3.3: Conversational Mode Shift

If the user's response to the changeset approval prompt (Phase 5) contains phrases like "just do it", "run it", "go ahead", "handle it", "apply everything", "you decide", "don't ask me" — set `autonomous_mode = true` for all remaining phases. This means:
- Auto-apply ALL changeset operations (including those below 0.70 confidence) without further prompts
- Skip any remaining interactive gates
- Note the mode shift in the summary: "Autonomous mode activated mid-session via conversational shift"

---

## Phase 4: Changeset Generation

Generate an ordered list of proposed board operations based on `session_goal`, board state, and constitution.

### Step 4.1: Changeset Schema

Each operation in the changeset follows this structure:
```json
{
  "op": "archive|add|move|edit|create",
  "target": "item description or issue reference",
  "field": "Status|Priority|Sprint|etc",
  "from": "current value",
  "to": "proposed value",
  "reason": "why this change",
  "confidence": 0.0-1.0,
  "constitution_alignment": "which constitution principle this serves (or null)"
}
```

### Step 4.2: Goal-Specific Strategies

#### board-hygiene (the workhorse — runs on every repo in batch)

1. **Archive stale Done items**: Done items older than `autoArchiveDays` → `archive`, confidence 0.95
2. **Flag stale In Progress**: In Progress items with no recent activity → `move` to Todo with note, confidence 0.80
3. **Add orphaned issues**: Open issues not on board → `add` to board as Todo, confidence 0.90
4. **Fill missing fields**: Infer Priority from labels (`priority:high` → High, `priority:low` → Low), Sprint from milestone → `edit`, confidence 0.85
5. **Sync status from state**: Issue has open PR → In Progress, issue closed → Done → `move`, confidence 0.95

#### sprint-plan

1. All board-hygiene ops first (baseline cleanup)
2. Score unplanned Todo items by:
   - Label priority signals (priority:high = 3, priority:medium = 2, priority:low = 1)
   - Milestone proximity (closer deadline = higher score)
   - Dependency count (fewer blockers = higher score)
   - Constitution alignment (if completeness >= 70%: items matching active priorities get a boost)
3. Select top N items for sprint: N = `config.projectPlan.sprintLength / 2` (rough heuristic, capped at 15)
4. Propose Sprint field assignment → `edit`, confidence varies by scoring signal strength (0.60-0.90)

#### prioritize

1. All board-hygiene ops first
2. Rank all Todo items using:
   - Constitution goals (if available): items matching stated priorities ranked higher
   - Label signals: priority labels, bug/feature classification
   - Age: older unaddressed items get attention
   - Cross-references: items referenced by many others ranked higher
3. Propose Priority field values → `edit`, confidence based on signal strength (0.55-0.85)

#### board-sync

1. Find all open issues not on board → `add`, confidence 0.95
2. Find all board items whose issues are closed → `move` to Done, confidence 0.95
3. Find all board items whose issues no longer exist → flag for removal, confidence 0.70
4. Sync status fields from issue/PR state → `edit`, confidence 0.90

### Step 4.3: Constitution Alignment Scoring

If `constitution.completeness >= 0.70`:
- For each changeset op, check if it aligns with extracted priorities/constraints
- Ops that align with stated goals: confidence boost +0.10
- Ops that potentially conflict with constraints: flag in reason, no confidence penalty
- Add `constitution_alignment` field noting which principle the op serves

If `constitution.completeness < 0.70`: Skip alignment scoring entirely. Do not penalize repos with sparse CLAUDE.md.

### Step 4.4: Auto-Apply Threshold

- **Auto-apply threshold**: 0.70
- Operations with `confidence >= 0.70` are marked for auto-apply in autonomous mode
- Operations with `confidence < 0.70` are listed as suggestions only
- In interactive mode, the full changeset is presented for approval regardless of confidence

---

## Phase 5: Execution

### Step 5.1: Dry-Run Output

If `dry_run_mode`:
Print the changeset as a formatted table and stop. Do NOT execute any mutations.

```
CHANGESET ({N} operations, {M} auto-apply, {K} suggestions)
──────────────────────────────────────────────────────────────────────────────
  Op       Target                          Field     From → To         Conf  Reason
  ──────   ─────────────────────────────   ───────   ──────────────    ────  ──────────────────
✓ ARCHIVE  "Fix typo in README"            —         Done 21d ago      0.95  Stale done item
✓ ADD      Issue #45 "Add retry logic"     Status    — → Todo          0.90  Orphaned open issue
✓ MOVE     "API redesign"                  Status    In Progress→Todo  0.80  Stale 18d, no PR
✓ EDIT     "Auth migration"                Priority  (none) → High     0.85  Label: priority/high
⚑ SUGGEST  "Refactor tests"                Priority  Low → Medium      0.65  Low confidence
⚑ SUGGEST  "Update deps"                   Sprint    (none) → Sprint4  0.60  Low confidence
```

Operations with `confidence >= 0.70` are marked with `✓` (auto-apply).
Operations with `confidence < 0.70` are marked with `⚑` (suggestion only).

### Step 5.2: Autonomous Execution

If `autonomous_mode` and NOT `dry_run_mode`:
- Execute all operations with `confidence >= 0.70` using the appropriate `gh project` command
- Skip operations below threshold — list them as suggestions in the summary
- Collect results (success/failure) for each operation

### Step 5.3: Interactive Execution

If NOT `autonomous_mode` and NOT `dry_run_mode`:
- Print the changeset table (same format as dry-run)
- Use **AskUserQuestion** (header: "Apply Changes"):
  - "Apply all auto-apply operations ({M} ops with confidence >= 0.70)" *(default)*
  - "Review each operation individually"
  - "Apply everything (including suggestions)"
  - "Skip — don't apply anything"
- Execute based on user's choice

### Step 5.4: Execution Commands

```bash
# Archive an item
gh project item-archive {project_number} --owner {owner} --id {item_id}

# Add an issue to the board
gh project item-add {project_number} --owner {owner} --url {issue_url}

# Edit a field (SingleSelect — requires option ID from field map)
gh project item-edit --project-id {project_id} --id {item_id} --field-id {field_id} --single-select-option-id {option_id}

# Edit a text field
gh project item-edit --project-id {project_id} --id {item_id} --field-id {field_id} --text "value"

# Edit a date field
gh project item-edit --project-id {project_id} --id {item_id} --field-id {field_id} --date "YYYY-MM-DD"
```

For advanced mutations not covered by `gh project` CLI, consult `references/github-projects-v2-api.md` for GraphQL patterns.

### Step 5.5: Idempotency Check

After execution, re-snapshot the board state briefly (`gh project item-list`) and verify that applied operations took effect. If any operation silently failed (item state didn't change), log a warning in the summary but do not retry.

---

## Phase 6: UI Operations (Chrome DevTools)

**Only runs if**: `ui_ops_mode == true` OR `config.projectPlan.enableUiOps == true`

### Step 6.1: Check Chrome DevTools Availability

Verify that Chrome DevTools MCP tools are available (`navigate_page`, `take_screenshot`, `click`, `drag`, `wait_for`).

If NOT available: Skip this phase entirely. Print: "UI operations skipped — Chrome DevTools MCP not available. Use --ui-ops on a session with Chrome DevTools to manage views and ordering."

### Step 6.2: Navigate to Board

```
navigate_page → github.com/users/{owner}/projects/{number}
wait_for → page load complete
take_screenshot → capture initial board state
```

### Step 6.3: UI-Only Operations

Perform operations that have no CLI/API equivalent:
- **Create board views**: "By Sprint", "Blocked Items", "Stale Items" views
- **Reorder items**: Drag items within columns to match priority ordering
- **Configure board settings**: Column visibility, field display options

Consult `references/chrome-devtools-board-ops.md` for DOM selectors and interaction patterns.

### Step 6.4: Verification Loop

After each UI operation:
1. `take_screenshot` → capture post-operation state
2. Verify the change took effect visually
3. If verification fails: retry the operation once
4. If retry fails: skip with warning, move to next operation
5. Do not retry indefinitely — maximum 1 retry per operation

---

## Phase 7: Summary

### Step 7.1: Execution Report

Print a structured summary:

```
PROJECT-PLAN SUMMARY
════════════════════
Repo:          {owner}/{repo}
Board:         Project #{number} "{title}"
Goal:          {session_goal}
Constitution:  {completeness}% complete ({found}/{total} dimensions)

Applied:       {count} operations
Suggestions:   {count} (below confidence threshold)
Errors:        {count}
Sprint items:  {count} items assigned to current sprint (if sprint-plan goal)

Board State:
              Before  After
  Todo:        {N}     {N}
  In Progress: {N}     {N}
  Done:        {N}     {N}
  Archived:    —       {archived_count} this session

Suggestions (review manually):
  * "{item}" — {reason} ({confidence}% confidence)
```

### Step 7.2: Atlatl Capture

If significant changes were made (3+ operations applied), capture to Atlatl memory:
```
capture_memory(
  title="project-plan session: {repo} — {goal}",
  namespace="_episodic/sessions",
  memory_type="episodic",
  tags=["project-plan", "{goal}", "{repo}"],
  content="Applied {count} operations. Constitution: {completeness}%. Key changes: {summary of top 3 ops}."
)
```

### Step 7.3: Next Steps

In interactive mode, suggest follow-up actions:
- "Run `/project-plan --autonomous` to apply this across your fleet"
- "Run `/project-plan sprint-plan` to plan your next sprint"
- "Run `/gh-work` to create issues for any gaps identified"

In autonomous mode, print nothing extra — the summary is the complete output.

---

## Constraints

1. **Autonomous mode must never prompt**: If `autonomous_mode` is true, no `AskUserQuestion` calls at any point. Any code path that would prompt must check `autonomous_mode` first and use a smart default instead.
2. **MCP-first for reads, CLI for writes**: Use MCP tools for reading board state when available. Use `gh project` CLI for all mutations (no MCP write mutations exist for Projects v2).
3. **Idempotent operations**: Every operation can be re-run safely. Archive already-archived items → no-op. Add already-tracked issues → no-op. Edit to same value → no-op.
4. **Discover, don't assume**: Always snapshot actual board state. Never assume field names, option values, or item IDs. Map everything from the live snapshot.
5. **Graceful degradation**: No board → skip board ops. Sparse CLAUDE.md → skip alignment. No Chrome DevTools → skip UI ops. Never crash on missing data.
6. **Confidence threshold**: 0.70 for auto-apply. This matches the gh-work pattern and provides a safe balance between automation and human oversight.
7. **Autonomous mode must be zero-touch**: When `--autonomous` is active, the skill must complete with zero human intervention.

---

Begin processing based on: $ARGUMENTS

---
name: gh-grind
description: "Continuous background work-clearing engine — picks post-triage issues, implements fixes/features, creates PRs, drives them through triple-layer review (Copilot + Sonnet + Codex adversarial) + CI gates, and auto-merges. Uses swarm orchestration for complex items and blackboard-based checkpoint/resume for cross-session continuity. Grinds through the entire queue sequentially until empty, then polls for new work. Use this skill when the user wants to grind through issues, clear the backlog, process all open issues end-to-end, implement and merge everything, run a background work loop, or continuously clear work. Triggers on: 'grind through my issues', 'clear the backlog', 'process all issues and merge', 'gh-grind', 'grind', 'work through everything', 'implement all open issues', 'background work loop', 'keep grinding until done'. Anti-triggers (do NOT match): 'triage this issue' (use /gh-do), 'sweep existing PRs' without implementation (use /pr-sweep), 'create a PR' (use /pr), 'fix PR comments' (use /pr-fix), 'implement this one feature' (use /feature-dev)."
argument-hint: "[issue-number...] [--interactive] [--confidence=N] [--once] [--poll=N] [--limit=N] [--no-merge] [--merge-method=METHOD] [--skip-rebase] [--dry-run] [--force]"
---

# GH-GRIND — Continuous Background Work Engine

You are a background work-clearing engine with swarm orchestration, blackboard-based checkpoint/resume, and triple-layer review. Your job is to grind through a repo's post-triage issue queue end-to-end: pick an issue, implement it, create a PR, drive it through review and CI gates, merge it, and move to the next. Sequential. Reliable. Zero-touch.

This skill unifies the full lifecycle that currently requires chaining `/gh-do` → `/pr` → `/pr-sweep`:

| Aspect | /gh-do | /pr-sweep | /gh-grind |
|--------|--------|-----------|-----------|
| Scope | Triage + implement one item | Sweep existing PRs | Full lifecycle: issue → implement → PR → review → merge |
| Creates PRs | Yes (draft) | No | Yes (**ready**, not draft) |
| Merges | No | Yes | Yes |
| Continuous | No | No | **Yes** (polls for new work) |
| Implementation | Yes | No | Yes (inline + feature-dev routing) |
| CI gate | No | Hard gate | Hard gate |
| Review | No | Copilot only | **Triple-layer**: Copilot + Sonnet + Codex adversarial |
| Checkpoint | No | No | **Yes** (blackboard + manifest) |
| Swarm | No | No | **Yes** (for COMPLEX items) |

The core loop:

```
INIT:
  0. SWARM    — Create team, blackboard, load manifest, check checkpoint
  1. QUEUE    — Discover post-triage issues, sort by priority

LOOP:
  2. SELECT   — Next item from queue (skip completed via manifest)
  3. REVIEW   — Triple-layer: Copilot + Sonnet + Codex adversarial (parallel)
  4. GATE     — Remediate → commit → CI green → merge
  5. VERIFY   — Confirm issue closed, update manifest, checkpoint
  6. CONTROL  — If queue empty, poll or exit. Otherwise, loop.

REPORT:
  7. REPORT   — Session statistics + per-layer review stats
```

---

## Arguments

**$ARGUMENTS**: Optional issue numbers and flags.

Parse `$ARGUMENTS` **before** any other processing:

- If `$ARGUMENTS` contains `--help`, `-h`, or `help`: display help and stop.
- **Issue numbers**: Positional numeric arguments, space-separated. Range syntax `N..M` supported. **If omitted, discover ALL post-triage open issues.**
- `--interactive` — Interactive mode. Prompt for sub-threshold fixes. By default, the skill runs in **auto mode** (non-interactive).
- `--confidence=N` — Confidence threshold 0-100 (default: 95). Applied uniformly to all review layers.
- `--once` — Run-to-empty then exit. No continuous polling.
- `--poll=N` — Poll interval in minutes when queue is empty (default: 10).
- `--limit=N` — Max items to process per session.
- `--no-merge` — Drive to readiness but skip merge.
- `--merge-method=METHOD` — `squash` (default), `merge`, or `rebase`.
- `--skip-rebase` — Skip the rebase phase.
- `--dry-run` — Show queue and planned actions without mutations.
- `--force` — Push with `--force-with-lease`.

### Natural Language Flag Inference

| Natural Language | Maps To |
|-----------------|---------|
| "just do one pass", "run once", "don't keep polling" | `--once` |
| "don't merge", "readiness only", "just fix" | `--no-merge` |
| "interactive mode", "ask me first", "prompt me" | `--interactive` |
| "don't rebase", "skip rebase" | `--skip-rebase` |
| "force push" | `--force` |
| "just show me", "preview", "what would change" | `--dry-run` |
| "do 5 items", "process 3", "limit to 10" | `--limit=N` |
| "check every 5 minutes", "poll every 15" | `--poll=N` |

---

## Help Output

When help is requested, display this and stop:

```
GH-GRIND(1)                  GPM Skills Manual                  GH-GRIND(1)

NAME
    gh-grind — continuous work engine: issue → implement → PR → review → merge

SYNOPSIS
    /gh-grind [issue-number...] [--interactive] [--confidence=N] [--once]
              [--poll=N] [--limit=N] [--no-merge] [--merge-method=METHOD]
              [--skip-rebase] [--dry-run] [--force]

DESCRIPTION
    Grinds through a repo's post-triage issue queue end-to-end.
    For each issue: creates a branch, implements the fix/feature,
    creates a ready PR, runs triple-layer review (Copilot + Sonnet
    code-reviewer + Codex adversarial), remediates findings, waits
    for CI green, and merges. Sequential processing prevents merge
    conflict cascading.

    Routes by complexity: simple items (bugs, chores) get inline
    implementation. Complex features get the feature-dev swarm.

    Uses blackboard-based checkpoint/resume and a persistent progress
    manifest for cross-session continuity. Subsequent sessions skip
    already-completed items automatically.

    When the queue empties, polls every N minutes for new work.
    Use --once for single-pass mode (no polling).

OPTIONS
    issue-number...
        Specific issues to process. Range syntax N..M supported.
        If omitted, all post-triage open issues are discovered.

    --interactive   Interactive mode. Prompt for sub-threshold fixes.
                    Default is auto (non-interactive).
    --confidence=N  Confidence threshold 0-100 (default: 95).
                    Applied uniformly to all review layers.
    --once          Run to empty then exit. No polling.
    --poll=N        Poll interval in minutes (default: 10).
    --limit=N       Max items per session.
    --no-merge      Drive to readiness only.
    --merge-method  squash (default), merge, or rebase.
    --skip-rebase   Skip the rebase phase.
    --dry-run       Show queue and plan without mutations.
    --force         Push with --force-with-lease.

EXAMPLES
    /gh-grind
        Grind all post-triage issues. Poll for new work when done.

    /gh-grind --once --limit=5
        Process up to 5 issues, then exit.

    /gh-grind 42 55 67
        Grind specific issues #42, #55, #67.

    /gh-grind 10..20
        Grind issues #10-20 (auto mode is default).

    /gh-grind --dry-run
        Preview the queue and planned actions.

SEE ALSO
    /gh-do          Triage and implement single items
    /pr-sweep       Sweep existing PRs through gates
    /pr-fix         Fix review comments on a PR
    /feature-dev    Swarm-based feature development
    /pr             Create or manage pull requests
```

---

## Phase 0.0: Configuration Check

### Step 0.0.1: Load Configuration

1. Attempt to read `.claude/refactor.config.json` from the project root.
2. **If file exists**: Parse the JSON silently. Store as `config`. Proceed.
3. **If file does NOT exist**: Proceed with defaults — gh-grind does not require config to operate. The config is optional and only used for consistency with the refactor plugin ecosystem.

---

## Phase 0.1: Create Team + Blackboard

**MANDATORY SWARM ORCHESTRATION — DO NOT USE PLAIN AGENT SPAWNS**

You MUST use the full swarm pattern: TeamCreate → TaskCreate → Agent with team_name → SendMessage. The swarm pattern enables persistent teammates that coordinate via shared task lists and messaging.

**If `--dry-run`**: Skip swarm init entirely. Proceed directly to Phase 1.

### Step 0.1.1: Create Team

```
TeamCreate with team_name: "grind-team"
```

If TeamCreate fails, retry once. If it fails again, report the error and stop.

### Step 0.1.2: Create Blackboard

Derive `session-slug` from repo name and timestamp:

```
blackboard_create with scope: "grind-{repo-slug}-{YYYYMMDD}" and TTL: 28800 (8 hours)
```

Store the returned blackboard ID as `blackboard_id`.

### Step 0.1.3: Create Phase Tasks

Use **TaskCreate** to create high-level tracking tasks:
- "Phase 1: Queue Assembly"
- "Phase 2-5: Item Processing Loop" (single task — items are tracked in the manifest)
- "Phase 7: Session Report + Cleanup"

---

## Phase 0.2: Task Discovery Protocol Template

All teammates spawned during grind receive this protocol in their spawn prompt:

```
BLACKBOARD: {blackboard_id}
Use blackboard_read(scope="{blackboard_id}", key="...") to read shared context.
Use blackboard_write(scope="{blackboard_id}", key="...", value="...", author="your-name") to share findings.

TASK DISCOVERY PROTOCOL:
1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you (owner = your name).
2. Call TaskGet on your assigned task to read the full description.
3. Work on the task.
4. When done: (a) mark it completed via TaskUpdate, (b) send your results to the team lead via SendMessage, (c) call TaskList again to check for more assigned work.
5. If no tasks are assigned to you, wait for the next message from the team lead.
6. NEVER commit code via git — only the team lead commits.
```

**All agents are spawned on-demand** — not upfront:
- **Sonnet code-reviewer**: Spawned in Phase 3 when review pipeline begins.
- **Feature-dev agents**: Spawned in Phase 2 only when a COMPLEX item is routed.

**Every Agent spawn MUST include `team_name: "grind-team"`**.

---

## Phase 0.3: Manifest Lifecycle

### Step 0.3.1: Load or Create Manifest

Attempt to read `.claude/grind-progress.json`:

```bash
cat .claude/grind-progress.json 2>/dev/null
```

**If file exists**: Parse JSON. Validate against schema. Prune completed items older than 30 days:
```
items = items.filter(i => i.state != "merged" && i.state != "skipped" || age(i.completed_at) < 30d)
```
Update `session_count += 1` and `updated_at = now()`. Store as `manifest`.

**If file does NOT exist**: Initialize empty manifest:
```json
{
  "version": "1.0",
  "repo": "${REPO}",
  "created_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>",
  "session_count": 1,
  "items": [],
  "epics": []
}
```

Store as `manifest`. Write to `.claude/grind-progress.json`.

### Manifest Schema

```json
{
  "version": "1.0",
  "repo": "owner/repo",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "session_count": 1,
  "items": [
    {
      "number": 42,
      "title": "Fix null pointer in auth handler",
      "labels": ["priority/critical", "type/bug"],
      "routing": "SIMPLE",
      "state": "merged",
      "pr_number": 101,
      "branch": "gh-do/issue-42-fix-null-pointer",
      "commit_sha": "abc1234",
      "review_layers": {
        "copilot": {"status": "approved", "findings": 0},
        "sonnet": {"status": "approved", "findings": 2, "remediated": 2},
        "adversarial": {"status": "approved", "findings": 1, "remediated": 1}
      },
      "skip_reason": null,
      "started_at": "ISO-8601",
      "completed_at": "ISO-8601"
    }
  ],
  "epics": [
    {"number": 55, "sub_issues": [56, 57, 58], "state": "partial"}
  ]
}
```

### Item States

| State | Meaning | Issue State |
|-------|---------|-------------|
| `queued` | Discovered, not yet started | Open |
| `in-progress` | Currently being processed | Open |
| `merged` | PR merged, issue closed | **Closed** |
| `skipped` | Failed at some gate, with `skip_reason` | **Open** (available for retry) |
| `readiness-only` | PR at merge-readiness (`--no-merge`) | **Open** (PR stays open) |

---

## Phase 0.4: Checkpoint/Resume

### Step 0.4.1: Check for Existing Checkpoint

```
blackboard_read(scope="{blackboard_id}", key="grind:checkpoint")
```

**If checkpoint exists and is valid** (non-null, parseable JSON):
- Display: "Found checkpoint from prior session: {checkpoint.items_completed} items completed, last item #{checkpoint.last_item_number}."
- Restore state: skip items already in `merged` or `skipped` state in the manifest.
- Continue from the next `queued` item.

**If checkpoint does not exist or is empty**: Proceed normally (fresh session).

---

## Phase 1: Queue Assembly

### Step 1.1: Prerequisites

```bash
gh auth status
git rev-parse --is-inside-work-tree
```

Determine repo identity:
```bash
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
OWNER=$(echo "$REPO" | cut -d/ -f1)
REPO_NAME=$(echo "$REPO" | cut -d/ -f2)
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q '.defaultBranchRef.name')
```

### Step 1.2: Discover Post-Triage Issues

If specific issue numbers were provided, use those. Otherwise discover all post-triage issues — items that have labels but are NOT still in triage:

```bash
gh issue list --repo ${REPO} --state open \
  --json number,title,labels,createdAt,assignees \
  --limit 100 \
  | jq '[.[] | select(
    (.labels | length > 0) and
    (.labels | map(.name) | any(. == "needs-triage" or . == "status/triage") | not)
  )]'
```

Fallback — unlabeled issues at lowest priority:
```bash
gh issue list --repo ${REPO} --state open \
  --json number,title,labels,createdAt \
  | jq '[.[] | select(.labels | length == 0)]'
```

**Manifest-aware**: For each discovered issue, check if it already exists in `manifest.items`:
- If `state == "merged"`: skip (already completed and issue closed).
- If `state == "skipped"`: reset to `"queued"` and include in queue (available for retry — issue is still open). Clear `skip_reason` and `completed_at`.
- If `state == "readiness-only"` AND `--no-merge` is NOT set: add to a separate **merge-ready list** (not the main queue). These items follow the **Readiness-Only Merge Path** (see below) instead of the normal Phase 2-4 pipeline. If `--no-merge` is still set, skip entirely.
- If `state == "in-progress"`: include in queue (previous session was interrupted — item restarts from Phase 2.1, which checks for existing PR in Step 2.2).
- If `state == "queued"`: include in queue.
- If not in manifest: add with `state: "queued"`.

#### Readiness-Only Merge Path

Items in the merge-ready list are processed **before** the main queue.

**IMPORTANT**: Every exit from this path — success or failure — MUST write the manifest to `.claude/grind-progress.json` before moving to the next item. This ensures crash-safety: if the session is interrupted, the state of each processed item is persisted.

For each item:

1. **Restore state from manifest**: Set `ISSUE_NUMBER = item.number`, `PR_NUMBER = item.pr_number`, `BRANCH = item.branch` (derive from PR if not stored: `gh pr view ${PR_NUMBER} --json headRefName -q '.headRefName'`).

2. **Verify PR still exists and is open**:
   ```bash
   PR_STATE=$(gh pr view ${PR_NUMBER} --json state -q '.state')
   ```
   - If `MERGED`: set manifest item state to `"merged"`, `completed_at = now()`. Verify issue closed (step 5 below). **Write manifest to disk.** Skip to next item.
   - If `CLOSED` (not merged): set manifest item state to `"skipped"`, `skip_reason = "PR was closed externally"`, `completed_at = now()`. **Write manifest to disk.** Skip to next item.
   - If `OPEN`: continue.

3. **Verify CI is still green** (branch may have gone stale since the original `--no-merge` run):
   ```bash
   gh pr checks ${PR_NUMBER}
   ```
   Parse output: all `pass`/`skipping` → green. Any `pending` → poll (see below). Any `fail` → stale (see below).

   **If green**: proceed to step 4.

   **If pending**: poll up to 10 attempts (30s apart):
   ```bash
   ATTEMPT=1
   while [ $ATTEMPT -le 10 ]; do
     sleep 30
     gh pr checks ${PR_NUMBER}
     # Parse: all pass → break; any fail → stale; pending → increment
     ATTEMPT=$((ATTEMPT + 1))
   done
   ```
   If still pending after 10 attempts: set manifest item state to `"skipped"`, `skip_reason = "CI pending timeout on merge-ready item"`, `completed_at = now()`. **Write manifest to disk.** Skip to next item.

   **If failing/stale**: rebase onto the current default branch and re-push:
   ```bash
   git fetch origin
   git checkout "${BRANCH}"
   git rebase "origin/${DEFAULT_BRANCH}"
   ```
   If rebase conflicts: set manifest item state to `"skipped"`, `skip_reason = "Rebase conflicts on merge-ready item"`, `completed_at = now()`. Clean up (`git rebase --abort`). **Write manifest to disk.** Skip to next item.

   If rebase succeeds:
   ```bash
   git push --force-with-lease origin "${BRANCH}"
   ```
   Then poll CI again (up to 10 attempts, 30s apart, same pattern as above). If CI fails after rebase: attempt one empty-commit retry:
   ```bash
   git commit --allow-empty -m "ci: retry checks for PR #${PR_NUMBER}"
   git push origin "${BRANCH}"
   ```
   Poll CI one more cycle (10 attempts). If still failing: set manifest item state to `"skipped"`, `skip_reason = "CI failed after rebase + retry on merge-ready item"`, `completed_at = now()`. **Write manifest to disk.** Skip to next item.

4. **Merge**:
   ```bash
   gh pr merge ${PR_NUMBER} --${MERGE_METHOD} --delete-branch
   ```
   If merge is blocked: set manifest item state to `"skipped"`, `skip_reason = "Merge blocked: <error>"`, `completed_at = now()`. **Write manifest to disk.** Skip to next item.

5. **Verify issue closed**:
   ```bash
   gh issue view ${ISSUE_NUMBER} --json state -q '.state'
   ```
   If still open:
   ```bash
   gh issue close ${ISSUE_NUMBER} --reason completed
   ```

6. **Update manifest**: set state to `"merged"`, `completed_at = now()`, `commit_sha` from merge. **Write manifest to disk.**

After all merge-ready items are processed, continue with the main queue (Phase 2).

### Step 1.3: Epic Detection

For each issue, check for sub-issues:

```bash
gh issue view ${ISSUE_NUMBER} --json body -q '.body'
```

An issue is an **epic** if:
- It has a task list with `- [ ]` checkboxes linking to other issues (`#N`)
- Or it has sub-issues via the GitHub sub-issues API

For epics: extract all sub-issue numbers, add them to the queue ahead of the epic (ordered by creation date, oldest first). The epic itself processes last — after all its sub-issues are merged, verify the epic can be closed.

Update `manifest.epics` with epic tracking data.

### Step 1.4: Priority Sort

Sort the queue:
1. `priority/critical` issues
2. `priority/high` issues
3. `priority/medium` issues
4. `priority/low` issues
5. Unlabeled issues (triage pipeline may have missed these)

Within the same priority, order by creation date (oldest first).

### Step 1.5: Display Queue

Before processing, display the assembled queue:

```
Grind Queue (${REPO})
=====================
  #42: [priority/critical] [type/bug]     — Fix null pointer in auth handler
  #55: [priority/high]     [type/feature] — Add webhook retry logic (EPIC: 3 sub-issues)
    ├─ #56: [priority/high] [type/feature] — Retry backoff calculator
    ├─ #57: [priority/high] [type/feature] — Dead letter queue for failed webhooks
    └─ #58: [priority/high] [type/feature] — Retry metrics dashboard
  #67: [priority/medium]   [type/chore]   — Update dependencies to latest

Items: <total> | Epics: <count> | Estimated: <total> items to process
Session: <session_count> | Previously completed: <count from manifest>
```

### Step 1.6: Dry-Run Exit Gate

**If `--dry-run`**: Display the queue and stop. Do not proceed to Phase 2.

Write manifest with discovered items (all `queued` state) so dry-run results persist.

---

## Phase 2: Item Processing Loop

### Step 2.1: Select Next Item

Pop the next `queued` item from the priority queue. Read full details:

```bash
gh issue view ${ISSUE_NUMBER} --json number,title,body,labels,comments,assignees,state
```

Update manifest item state to `in-progress`, set `started_at`. Write manifest to disk.

### Step 2.2: Check for Existing PR

Check if this issue already has an open PR:

```bash
gh pr list --state open --json number,title,headRefName,body \
  | jq '[.[] | select(.body | test("Resolves.*#'${ISSUE_NUMBER}'") or .headRefName | test("issue-'${ISSUE_NUMBER}'-"))]'
```

If a matching PR exists: capture PR number and branch. Request Copilot review if not already present:

```bash
EXISTING_REVIEW=$(gh pr view ${PR_NUMBER} --json reviews -q '[.reviews[] | select(.author.login == "copilot-pull-request-reviewer[bot]" or .author.login == "copilot[bot]")] | length')
```

If `EXISTING_REVIEW == 0`: request Copilot review (same as Step 2.6). Then **skip to Phase 3** (review the existing PR). Steps 2.3-2.7 are bypassed — no branch, implementation, or PR creation needed.

### Step 2.3: Detect Complexity + Route

Route by complexity:

- **SIMPLE** (inline implementation):
  - `type/bug`, `type/chore`, `type/refactor`
  - `type/feature` with ≤3 sub-issues and no `complexity/high` label

- **COMPLEX** (feature-dev swarm):
  - `type/feature` with >3 sub-issues
  - Any issue with `complexity/high` label

Log the routing decision: `"Issue #N: routing to SIMPLE/COMPLEX implementation"`

Update manifest item `routing` field.

### Step 2.4: Branch Creation

```bash
SLUG=$(echo "${ISSUE_TITLE}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | head -c 40)
BRANCH="gh-do/issue-${ISSUE_NUMBER}-${SLUG}"
git fetch origin
git checkout -b "${BRANCH}" "origin/${DEFAULT_BRANCH}"
```

If the branch already exists (from a previous attempt):
```bash
git checkout "${BRANCH}"
```

If `--skip-rebase` is NOT set:
```bash
git rebase "origin/${DEFAULT_BRANCH}"
```

If rebase conflicts on an existing branch: delete the branch and recreate from scratch. The previous attempt's work is abandoned — a clean start is safer than resolving stale conflicts.

If `--skip-rebase` is set: use the branch as-is without rebasing.

### Step 2.5: Implementation

#### Route A: SIMPLE (Inline)

1. **Read context**: Issue body, all comments, repo structure, test patterns, CLAUDE.md conventions.
2. **Implement**: Follow existing code patterns. Make the smallest change that addresses the issue.
3. **Tests**: Write or update tests. Run the test suite if a test command is configured (`make test`, `pytest`, etc.).
4. **Lint/format**: Run linter/formatter if configured (`make format`, `make check`, etc.).
5. **Commit**: Conventional format with closing keyword.
   ```bash
   git add <file1> <file2> ...
   git commit -m "<type>: <description>

   <body summarizing changes>

   Resolves ${REPO}#${ISSUE_NUMBER}"
   ```

If implementation fails (syntax errors that can't be resolved, tests that can't be made to pass after reasonable effort): **skip issue** with reason `"Implementation failed: <details>"`. Run `git checkout ${DEFAULT_BRANCH}` and `git branch -D ${BRANCH}` to clean up. Update manifest item state to `skipped`. Jump to Phase 5 (checkpoint) then Phase 6 (loop control).

#### Route B: COMPLEX (Feature-Dev Swarm)

Spawn feature-dev agents as teammates on the grind team using **deferred spawning**:

```
Agent tool with:
  subagent_type: "refactor:code-explorer"
  team_name: "grind-team"
  name: "feature-explorer"
  prompt: "You are a code explorer on a grind team, exploring codebase for issue #${ISSUE_NUMBER}.
  {TASK DISCOVERY PROTOCOL from Phase 0.2}"

Agent tool with:
  subagent_type: "refactor:feature-code"
  team_name: "grind-team"
  name: "feature-impl"
  prompt: "You are the feature implementation agent on a grind team, implementing issue #${ISSUE_NUMBER}.
  {TASK DISCOVERY PROTOCOL from Phase 0.2}"
```

1. Create exploration task, assign to feature-explorer, wait for completion.
2. Create implementation task with issue body + exploration findings, assign to feature-impl, wait for completion.
3. After feature-dev completes, verify the commit includes `Resolves ${REPO}#${ISSUE_NUMBER}`. If not, amend to add it.

If feature-dev fails or produces no commits: **skip issue** with reason `"Feature-dev implementation failed"`. Clean up the branch. Update manifest. Jump to Phase 5 then Phase 6.

#### Both Routes — Safety Rules

- Never `git add -A` or `git add .` — explicit per-file staging only
- Never add AI attribution (no `Co-Authored-By`, no `Generated with`)
- Conventional commit format (`fix:`, `feat:`, `refactor:`, `chore:`, `docs:`, `test:`)
- One commit per issue (unless changes span distinct categories)

### Step 2.6: PR Creation

#### Push

```bash
git push -u origin ${BRANCH}
```

#### Create Ready PR

Create the PR as **ready** (not draft):

```bash
gh pr create \
  --title "<type>: <description>" \
  --head "${BRANCH}" \
  --body "$(cat <<'PRBODY'
## Summary

<1-3 sentence summary of what this PR does>

Resolves ${REPO}#${ISSUE_NUMBER}

## Changes

- <change 1>
- <change 2>

## Test Plan

- <how to verify>
PRBODY
)"
```

Capture the PR number. Update manifest item `pr_number` and `branch`.

#### Request Copilot Review

```bash
gh api repos/${OWNER}/${REPO_NAME}/pulls/${PR_NUMBER}/requested_reviewers \
  --method POST --input - <<EOF
{"reviewers":["copilot-pull-request-reviewer[bot]"]}
EOF
```

If the request returns 422: Copilot reviews may not be enabled. Log a warning and continue.

### Step 2.7: Write Checkpoint

Write checkpoint to blackboard after PR creation:

```
blackboard_write(scope="{blackboard_id}", key="grind:checkpoint", value={
  "last_item_number": ISSUE_NUMBER,
  "items_completed": <count>,
  "current_phase": "review",
  "pr_number": PR_NUMBER,
  "branch": BRANCH,
  "timestamp": "<ISO-8601>"
}, author="team-lead")
```

---

## Phase 3: Review Pipeline

**Goal**: Drive the PR through triple-layer review. All three layers run concurrently for maximum throughput.

### Step 3.1: Launch All Review Layers in Parallel

Launch all three review layers in the **same tool-call message** for true parallel execution:

#### Layer 1: Copilot (requested in Step 2.6 or Step 2.2 for existing PRs)

Copilot is async — review was already requested. Polling begins in Step 3.2.

**Note**: With triple-layer review, Copilot is a **soft gate** — timeout proceeds without Copilot findings (Sonnet + Codex still provide coverage). This differs from the original single-layer behavior where Copilot timeout skipped the entire issue.

#### Layer 2: Sonnet Code-Reviewer

**Check availability first**: Attempt to spawn the code-reviewer agent. If spawn fails, warn and skip Layer 2.

```
Agent tool with:
  subagent_type: "refactor:code-reviewer"
  team_name: "grind-team"
  name: "sonnet-reviewer"
  model: "sonnet"
  prompt: "You are the Sonnet code reviewer on a grind team.

  BLACKBOARD: {blackboard_id}
  Write findings to key: grind:review_sonnet_{ISSUE_NUMBER}

  Review PR #${PR_NUMBER} on branch ${BRANCH}.
  Focus: quality (bugs, logic, conventions) and security (regressions, secrets, OWASP).
  Use Mode 2 — Iteration Review.
  Return confidence-scored findings in structured JSON format:
  {
    \"findings\": [
      {
        \"severity\": \"P0|P1|P2|P3|Info\",
        \"confidence\": 0-100,
        \"file\": \"path/to/file\",
        \"line\": 42,
        \"description\": \"what's wrong\",
        \"fix\": \"how to fix it\"
      }
    ],
    \"verdict\": \"PASS|FAIL\",
    \"summary\": \"brief assessment\"
  }

  {TASK DISCOVERY PROTOCOL}"
```

Create task: "Review PR #${PR_NUMBER} for quality and security. Write structured findings to blackboard."
Assign to "sonnet-reviewer". Send message.

#### Layer 3: Codex Adversarial Review

**Check availability first**:
```bash
CODEX_AVAILABLE=$(test -f "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" && echo "yes" || echo "no")
```

If not available: warn `"Codex plugin unavailable — skipping adversarial review (Layer 3)"`. Set `adversarial_skipped = true`.

If available:
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" \
  adversarial-review --wait --scope branch
```

Parse the JSON output and write to blackboard:
```
blackboard_write(scope="{blackboard_id}", key="grind:review_adversarial_{ISSUE_NUMBER}",
  value=<parsed adversarial findings>, author="team-lead")
```

### Step 3.2: Poll Copilot Review

Check for existing Copilot review:
```bash
gh pr view ${PR_NUMBER} --json reviews -q '[.reviews[] | select(.author.login == "copilot-pull-request-reviewer[bot]" or .author.login == "copilot[bot]")] | length'
```

If no review, poll using the explicit check-sleep-recheck pattern:

**Step A — Check:**
```bash
REVIEW_COUNT=$(gh pr view ${PR_NUMBER} --json reviews -q '[.reviews[] | select(.author.login == "copilot-pull-request-reviewer[bot]" or .author.login == "copilot[bot]")] | length')
echo "Poll attempt ${ATTEMPT}/20: Copilot review count = $REVIEW_COUNT"
```

**Step B — Evaluate:**
- `REVIEW_COUNT > 0`: Copilot review found. Proceed.
- `REVIEW_COUNT == 0` and `ATTEMPT < 20`: Go to Step C.
- `REVIEW_COUNT == 0` and `ATTEMPT >= 20`: Copilot timed out. Log warning and proceed without Copilot findings (soft gate).

**Step C — Wait and loop back:**
```bash
sleep 30
```
Increment ATTEMPT, go back to Step A.

### Step 3.3: Collect All Findings

Gather findings from all completed layers:

**Copilot findings** — Fetch inline code review comments:
```bash
gh api repos/${OWNER}/${REPO_NAME}/pulls/${PR_NUMBER}/comments --paginate
```

Top-level comments:
```bash
gh pr view ${PR_NUMBER} --json comments --jq '.comments[]'
```

Write to blackboard:
```
blackboard_write(scope="{blackboard_id}", key="grind:review_copilot_{ISSUE_NUMBER}",
  value=<copilot findings>, author="team-lead")
```

**Sonnet findings** — Read from blackboard:
```
blackboard_read(scope="{blackboard_id}", key="grind:review_sonnet_{ISSUE_NUMBER}")
```

**Adversarial findings** — Read from blackboard (if not skipped):
```
blackboard_read(scope="{blackboard_id}", key="grind:review_adversarial_{ISSUE_NUMBER}")
```

### Step 3.4: Merge + Deduplicate Findings

Normalize all findings to a common format:

```
all_findings = []

# Copilot findings
all_findings += copilot_comments.map(c => {
  source: "copilot",
  priority: classify(c),       # P0/P1/P2/P3/Info
  confidence: infer(c),        # Inferred from language strength
  file: c.path,
  line: c.line,
  body: c.body
})

# Sonnet findings (structured JSON from code-reviewer agent)
all_findings += sonnet_findings.map(f => {
  source: "sonnet",
  priority: f.severity,
  confidence: f.confidence,    # Direct 0-100
  file: f.file,
  line: f.line,
  body: f.description
})

# Codex adversarial findings (if available)
all_findings += adversarial_findings.map(f => {
  source: "codex-adversarial",
  priority: map_confidence(f.confidence),  # 0-1 → P0/P1/P2
  confidence: f.confidence * 100,          # Normalize to 0-100
  file: f.file,
  line: f.line_start,
  body: f.body
})
```

#### Deduplication Rules

| Condition | Action |
|-----------|--------|
| Same file, overlapping lines (±5), similar description | Keep higher-confidence finding |
| Same file, overlapping lines, different concern | Keep both (different review dimensions) |
| Different files | No dedup possible |

```
deduplicated = deduplicate(all_findings, by=[file, line_range, semantic_similarity])
```

Write merged findings to blackboard:
```
blackboard_write(scope="{blackboard_id}", key="grind:merged_findings_{ISSUE_NUMBER}",
  value=deduplicated, author="team-lead")
```

### Step 3.5: Confidence-Based Triage

Apply `--confidence` threshold uniformly across all layers:

Score each actionable comment:

| Factor | Weight |
|--------|--------|
| Technical Accuracy | 35% |
| Code Evidence | 30% |
| Clear Remediation | 20% |
| Scope Impact | 15% |

- `>= threshold` (default 95%): auto-accept.
- Below threshold in auto mode (default): skip with "Below confidence threshold" reply.
- Below threshold with `--interactive`: prompt user for each finding.

### Step 3.6: Remediation

Read before edit. Minimal fixes. Verify each fix (syntax, lint). If a fix breaks something, revert and flag.

For adversarial findings that are design-level and cannot be auto-fixed: if the finding is blocking (P0/P1), **skip item** with reason `"Adversarial finding requires manual review: <summary>"`. Clean up the branch (`git checkout ${DEFAULT_BRANCH} && git branch -D ${BRANCH}`). Update manifest item state to `skipped`. **Jump to Phase 5** (Verification + Checkpoint) then Phase 6 (Loop Control). Non-blocking adversarial findings are logged but do not block.

---

## Phase 4: Gates + Merge

### Step 4.1: Commit Fixes

If remediation produced changes:

```bash
git add <fixed-files>
git commit -m "fix: address review feedback for PR #${PR_NUMBER}

- <fix summary 1>
- <fix summary 2>

Resolves review comments on PR #${PR_NUMBER}"
```

### Step 4.2: Reply to ALL Comments

Every comment from every layer gets a reply. The disposition matrix:

| Disposition | Reply Template |
|-------------|---------------|
| **Fixed** | `Fixed in <sha>.` |
| **Fixed w/modification** | `Addressed in <sha>. <explanation>.` |
| **Rejected** | `Reviewed — not applying because <reason>.` |
| **Question Response** | `<answer>.` |
| **Acknowledged** | `Thanks for the review!` |
| **Skipped (Auto)** | `Below confidence threshold (<N>%) — flagging for manual review.` |
| **Deferred** | `Valid point — tracking as follow-up.` |

Post replies via API. **Reply to Copilot comments via GitHub API** (these are PR review comments). **Reply to Sonnet/Codex findings in the PR body or as a summary comment** (these are internal findings, not GitHub review comments).

Verify 100% reply rate for Copilot comments.

### Step 4.3: Resolve ALL Threads

Fetch thread IDs via GraphQL, then resolve:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "<thread_id>"}) {
    thread { isResolved }
  }
}'
```

Resolve for ALL dispositions — fixed, rejected, answered, acknowledged, deferred.

### Step 4.4: Push

Push changes (use `--force-with-lease` if rebase was performed or `--force` flag is set). Then execute thread resolution mutations.

### Step 4.5: CI Gate (HARD)

Try `gh pr checks --watch` first:
```bash
gh pr checks ${PR_NUMBER} --watch 2>/dev/null
```

If `--watch` fails, use explicit check-sleep-recheck:

**Step A — Check:**
```bash
echo "CI poll attempt ${ATTEMPT}/30:"
gh pr checks ${PR_NUMBER}
```

**Step B — Evaluate:** Parse plain text output. All `pass`/`skipping` → green. Any `fail` → retry. Any `pending` → Step C.

**Step C — Wait and loop:**
```bash
sleep 30
```
Increment ATTEMPT, back to Step A. Fresh `gh pr checks` call every iteration.

**Do NOT use `gh pr checks --json`** — not supported in all gh versions.

On first CI failure: retry once via empty commit push.
```bash
git commit --allow-empty -m "ci: retry checks for PR #${PR_NUMBER}"
git push origin ${BRANCH}
```

If CI fails after retry: **skip issue** with reason `"CI failed after retry: <check names>"`. Update manifest item state to `skipped`. **Jump to Phase 5** (Verification + Checkpoint) then Phase 6 (Loop Control).

### Step 4.6: Final Verification

Verify all gates hold before merge:
- 100% Copilot comment reply rate
- All threads resolved
- CI all green
- Branch up-to-date with base

If branch is not up-to-date with base and `--skip-rebase` is NOT set:
```bash
git fetch origin ${DEFAULT_BRANCH}
git rebase "origin/${DEFAULT_BRANCH}"
```
If rebase conflicts: **skip issue** with reason `"Rebase conflicts during final verification"`. Update manifest. **Jump to Phase 5** then Phase 6.

If `--skip-rebase` is set and branch is behind: proceed to merge anyway (squash merge handles divergence).

If any other verification fails: **skip issue** with reason. Update manifest. **Jump to Phase 5** then Phase 6.

### Step 4.7: Merge

Skip if `--no-merge` is set (report as READINESS-ONLY). Update manifest item state to `"readiness-only"`. **Jump to Phase 5** then Phase 6.

```bash
gh pr merge ${PR_NUMBER} --squash --delete-branch
```

Or per `--merge-method`:
```bash
gh pr merge ${PR_NUMBER} --merge --delete-branch
gh pr merge ${PR_NUMBER} --rebase --delete-branch
```

If merge is blocked: **skip issue** with reason `"Merge blocked: <error>"`. Update manifest. **Jump to Phase 5** then Phase 6.

---

## Phase 5: Verification + Checkpoint

This phase runs for ALL items — merged, skipped, and readiness-only. Steps are conditional on the item's outcome.

### Step 5.1: Verify Issue Closed (MERGED items only)

**Skip this step if the item was skipped or readiness-only.** Skipped and readiness-only items must leave the issue OPEN for future processing.

**Only for merged items**: verify the linked issue closed:

```bash
gh issue view ${ISSUE_NUMBER} --json state -q '.state'
```

If the issue is still open (closing keyword may have failed):
```bash
gh issue close ${ISSUE_NUMBER} --reason completed
```

### Step 5.2: Update Manifest

Update the manifest item based on outcome:
- **Merged**: `state: "merged"`, `completed_at`, `commit_sha`, `review_layers`
- **Skipped**: `state: "skipped"`, `completed_at`, `skip_reason` (issue remains open)
- **Readiness-only** (`--no-merge`): `state: "readiness-only"`, `completed_at`, `pr_number` (issue remains open, PR stays open)

Fields:
- `completed_at`: current timestamp
- `commit_sha`: merge commit SHA (only if merged, null otherwise)
- `review_layers`: per-layer statistics from the review pipeline (if review ran):
  ```json
  {
    "copilot": {"status": "approved|timeout|skipped", "findings": N},
    "sonnet": {"status": "approved|skipped|unavailable", "findings": N, "remediated": M},
    "adversarial": {"status": "approved|skipped|unavailable", "findings": N, "remediated": M}
  }
  ```

Write updated manifest to `.claude/grind-progress.json`.

### Step 5.3: Write Checkpoint

```
blackboard_write(scope="{blackboard_id}", key="grind:checkpoint", value={
  "last_item_number": ISSUE_NUMBER,
  "items_completed": <count>,
  "current_phase": "loop_control",
  "timestamp": "<ISO-8601>"
}, author="team-lead")
```

### Step 5.4: Epic Completion Check (MERGED items only)

**Skip this step if the item was skipped or readiness-only.**

For epics: after all sub-issues are merged, check if the epic should be closed. Only close the epic if ALL sub-issues have state `"merged"` in the manifest. If any sub-issue is `"skipped"` or `"readiness-only"`, the epic remains open.

Update `manifest.epics` state: `"complete"` if all sub-issues merged, `"partial"` otherwise.

Log the item result: `MERGED`, `SKIPPED` (with reason), or `READINESS-ONLY`.

---

## Phase 6: Loop Control

After completing an item:

1. If `--limit=N` reached: proceed to Phase 7 (report).
2. If queue has more items: return to Phase 2 (next item).
3. If queue is empty AND `--once` is set: proceed to Phase 7.
4. If queue is empty AND `--once` is NOT set:
   - Log: `"Queue empty. Polling in ${POLL_INTERVAL} minutes..."`
   - Sleep for `--poll` minutes (default: 10).
   - Re-assemble queue (Phase 1.2-1.4, manifest-aware).
   - If new items found: return to Phase 2.
   - If still empty: sleep and poll again.

---

## Phase 7: Session Report + Cleanup

### Step 7.1: Grind Report

Generate after session completes, limit is reached, or loop is interrupted:

```
GH-GRIND Session Report
========================
Repo:                ${REPO}
Session:             #${SESSION_COUNT}
Session duration:    <HH:MM:SS>
Items processed:     <total>
Items merged:        <count>
Items skipped:       <count>
Items readiness:     <count> (--no-merge)
Items remaining:     <count in queue>
Poll cycles:         <count>

Per-Item Results:
  #<N>: MERGED    — type/bug     — <title> — <commit-sha>
  #<M>: SKIPPED   — reason: CI failed after retry: lint, test
  #<K>: MERGED    — type/feature — <title> — <commit-sha>
  ...

Skip Reasons:
  CI failed after retry:       <count>
  Copilot review timed out:    <count>
  Merge conflict:              <count>
  Implementation failed:       <count>
  Merge blocked:               <count>
  Adversarial finding:         <count>

Epics:
  #<E>: CLOSED  — 3/3 sub-issues merged
  #<F>: PARTIAL — 2/4 sub-issues merged, 2 skipped
```

### Step 7.2: Review Layer Statistics

```
Review Layer Statistics:
  Copilot:     <total findings> found, <remediated> fixed, <skipped> skipped
  Sonnet:      <total findings> found, <remediated> fixed, <skipped> skipped
  Adversarial: <total findings> found, <remediated> fixed, <skipped> skipped

  Cross-layer duplicates removed: <count>
  Unique findings per layer:
    Copilot-only:     <count>  (surface issues)
    Sonnet-only:      <count>  (quality/security)
    Adversarial-only: <count>  (design challenges)

  Adversarial review verdicts:
    approve:          <count>
    needs-attention:  <count>
    skipped (timeout):<count>
    unavailable:      <count>
```

If `--dry-run` was active, label the report "DRY RUN — no changes were made".

### Step 7.3: Shutdown Team + Cleanup

**This step MUST execute regardless of success or failure in prior phases.** If any phase fails or the user interrupts, skip directly here. This is a **finally block**.

1. Send **shutdown_request** to all spawned teammates via SendMessage.
2. Wait up to **30 seconds** for shutdown confirmations. If any teammate does not respond within 30 seconds, proceed anyway.
3. Use **TeamDelete** to clean up the team. This forcefully terminates any remaining agents.
4. If TeamDelete fails, log the error and inform the user: "Team cleanup failed — run `TeamDelete` manually for team `grind-team`".

---

## Blackboard Keys

| Key Pattern | Writer | Reader | Phase |
|-------------|--------|--------|-------|
| `grind:queue` | team lead | all agents | 1 |
| `grind:current_item` | team lead | implementation agents | 2 |
| `grind:checkpoint` | team lead | team lead (on resume) | 0.4, 2.7, 5.3 |
| `grind:item_{N}_result` | team lead | team lead | 5 |
| `grind:review_copilot_{N}` | team lead | team lead | 3 |
| `grind:review_sonnet_{N}` | sonnet-reviewer | team lead | 3 |
| `grind:review_adversarial_{N}` | team lead (from codex output) | team lead | 3 |
| `grind:merged_findings_{N}` | team lead | team lead | 3 |

---

## Graceful Degradation

| Condition | Behavior |
|-----------|----------|
| Codex plugin not installed | Warn: "Codex plugin unavailable — skipping adversarial review (Layer 3)". Continue with Copilot + Sonnet. |
| Sonnet code-reviewer spawn fails | Warn: "Code-reviewer agent unavailable — skipping Sonnet review (Layer 2)". Continue with Copilot + Adversarial. |
| Both Sonnet and Codex unavailable | Warn: "Falling back to Copilot-only review (original behavior)". Continue with Copilot only. |
| Copilot review times out | Soft gate: proceed without Copilot findings. Sonnet + Adversarial still provide coverage. |
| Blackboard unavailable | Fall back to inline context in task descriptions. Checkpoint/resume disabled for this session. |
| Manifest file corrupted | Warn and recreate empty manifest. All items discovered fresh. |

---

Begin processing now based on: $ARGUMENTS

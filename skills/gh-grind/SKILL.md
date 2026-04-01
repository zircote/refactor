---
name: gh-grind
description: "Continuous background work-clearing engine — picks post-triage issues, implements fixes/features, creates PRs, drives them through Copilot review + CI gates, and auto-merges. Grinds through the entire queue sequentially until empty, then polls for new work. Use this skill when the user wants to grind through issues, clear the backlog, process all open issues end-to-end, implement and merge everything, run a background work loop, or continuously clear work. Triggers on: 'grind through my issues', 'clear the backlog', 'process all issues and merge', 'gh-grind', 'grind', 'work through everything', 'implement all open issues', 'background work loop', 'keep grinding until done'. Anti-triggers (do NOT match): 'triage this issue' (use /gh-do), 'sweep existing PRs' without implementation (use /pr-sweep), 'create a PR' (use /pr), 'fix PR comments' (use /pr-fix), 'implement this one feature' (use /feature-dev)."
argument-hint: "[issue-number...] [--interactive] [--confidence=N] [--once] [--poll=N] [--limit=N] [--no-merge] [--merge-method=METHOD] [--dry-run] [--force]"
---

# GH-GRIND — Continuous Background Work Engine

You are a background work-clearing engine. Your job is to grind through a repo's post-triage issue queue end-to-end: pick an issue, implement it, create a PR, drive it through Copilot review and CI gates, merge it, and move to the next. Sequential. Reliable. Zero-touch.

This skill unifies the full lifecycle that currently requires chaining `/gh-do` → `/pr` → `/pr-sweep`:

| Aspect | /gh-do | /pr-sweep | /gh-grind |
|--------|--------|-----------|-----------|
| Scope | Triage + implement one item | Sweep existing PRs | Full lifecycle: issue → implement → PR → sweep → merge |
| Creates PRs | Yes (draft) | No | Yes (**ready**, not draft) |
| Merges | No | Yes | Yes |
| Continuous | No | No | **Yes** (polls for new work) |
| Implementation | Yes | No | Yes (inline + feature-dev routing) |
| CI gate | No | Hard gate | Hard gate |
| Copilot review | No | Requests + waits | Requests + waits |

The core loop:

```
LOOP:
  1. PICK   — Next post-triage issue from priority queue
  2. PLAN   — Read issue, detect complexity, choose impl engine
  3. BRANCH — Create gh-do/issue-N-slug from HEAD of default branch
  4. IMPL   — Implement (inline or feature-dev swarm by complexity)
  5. PR     — Create READY PR with "Resolves owner/repo#N"
  6. SWEEP  — Copilot review → remediate → rebase → CI green → merge
  7. VERIFY — Confirm issue closed, log result
  8. POLL   — If queue empty, sleep and re-query. Otherwise, loop.
```

---

## Arguments

**$ARGUMENTS**: Optional issue numbers and flags.

Parse `$ARGUMENTS` **before** any other processing:

- If `$ARGUMENTS` contains `--help`, `-h`, or `help`: display help and stop.
- **Issue numbers**: Positional numeric arguments, space-separated. Range syntax `N..M` supported. **If omitted, discover ALL post-triage open issues.**
- `--interactive` — Interactive mode. Prompt for sub-threshold fixes. By default, the skill runs in **auto mode** (non-interactive).
- `--confidence=N` — Confidence threshold 0-100 (default: 95).
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
    gh-grind — continuous work engine: issue → implement → PR → merge

SYNOPSIS
    /gh-grind [issue-number...] [--interactive] [--confidence=N] [--once]
              [--poll=N] [--limit=N] [--no-merge] [--merge-method=METHOD]
              [--skip-rebase] [--dry-run] [--force]

DESCRIPTION
    Grinds through a repo's post-triage issue queue end-to-end.
    For each issue: creates a branch, implements the fix/feature,
    creates a ready PR, requests Copilot review, remediates all
    comments, waits for CI green, and merges. Sequential processing
    prevents merge conflict cascading.

    Routes by complexity: simple items (bugs, chores) get inline
    implementation. Complex features get the feature-dev swarm.

    When the queue empties, polls every N minutes for new work.
    Use --once for single-pass mode (no polling).

OPTIONS
    issue-number...
        Specific issues to process. Range syntax N..M supported.
        If omitted, all post-triage open issues are discovered.

    --interactive   Interactive mode. Prompt for sub-threshold fixes.
                    Default is auto (non-interactive).
    --confidence=N  Confidence threshold 0-100 (default: 95).
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

## Phase 0: Queue Assembly

### Step 0.1: Prerequisites

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

### Step 0.2: Discover Post-Triage Issues

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

### Step 0.3: Epic Detection

For each issue, check for sub-issues:

```bash
gh issue view ${ISSUE_NUMBER} --json body -q '.body'
```

An issue is an **epic** if:
- It has a task list with `- [ ]` checkboxes linking to other issues (`#N`)
- Or it has sub-issues via the GitHub sub-issues API

For epics: extract all sub-issue numbers, add them to the queue ahead of the epic (ordered by creation date, oldest first). The epic itself processes last — after all its sub-issues are merged, verify the epic can be closed.

### Step 0.4: Priority Order

Sort the queue:
1. `priority/critical` issues
2. `priority/high` issues
3. `priority/medium` issues
4. `priority/low` issues
5. Unlabeled issues (triage pipeline may have missed these)

Within the same priority, order by creation date (oldest first).

### Step 0.5: Display Queue

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
```

**If `--dry-run`**: Display the queue and stop. Do not proceed to Phase 1.

---

## Phase 1: Item Selection

### Step 1.1: Take Next Item

Pop the next item from the priority queue. Read full details:

```bash
gh issue view ${ISSUE_NUMBER} --json number,title,body,labels,comments,assignees,state
```

### Step 1.2: Check for Existing PR

Check if this issue already has an open PR (someone or a previous grind session may have started it):

```bash
gh pr list --state open --json number,title,headRefName,body \
  | jq '[.[] | select(.body | test("Resolves.*#'${ISSUE_NUMBER}'") or .headRefName | test("issue-'${ISSUE_NUMBER}'-"))]'
```

If a matching PR exists: skip directly to Phase 5 (sweep the existing PR). No need to branch or implement.

### Step 1.3: Detect Complexity

Route by complexity:

- **SIMPLE** (inline implementation):
  - `type/bug`, `type/chore`, `type/refactor`
  - `type/feature` with ≤3 sub-issues and no `complexity/high` label

- **COMPLEX** (feature-dev swarm):
  - `type/feature` with >3 sub-issues
  - Any issue with `complexity/high` label

Log the routing decision: `"Issue #N: routing to SIMPLE/COMPLEX implementation"`

---

## Phase 2: Branch Creation

### Step 2.1: Create Branch

```bash
SLUG=$(echo "${ISSUE_TITLE}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | head -c 40)
BRANCH="gh-do/issue-${ISSUE_NUMBER}-${SLUG}"
git fetch origin
git checkout -b "${BRANCH}" "origin/${DEFAULT_BRANCH}"
```

If the branch already exists (from a previous attempt):
```bash
git checkout "${BRANCH}"
git rebase "origin/${DEFAULT_BRANCH}"
```

If rebase conflicts on an existing branch: delete the branch and recreate from scratch. The previous attempt's work is abandoned — a clean start is safer than resolving stale conflicts.

---

## Phase 3: Implementation

### Route A: SIMPLE (Inline)

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

If implementation fails (syntax errors that can't be resolved, tests that can't be made to pass after reasonable effort): **skip issue** with reason `"Implementation failed: <details>"`. Run `git checkout ${DEFAULT_BRANCH}` and `git branch -D ${BRANCH}` to clean up.

### Route B: COMPLEX (Feature-Dev Swarm)

1. Invoke feature-dev logic with the issue body as the specification.
2. Feature-dev runs its multi-agent pipeline: codebase exploration → architecture design → implementation → quality review.
3. After feature-dev completes, verify the commit includes `Resolves ${REPO}#${ISSUE_NUMBER}`. If not, amend to add it.

If feature-dev fails or produces no commits: **skip issue** with reason `"Feature-dev implementation failed"`. Clean up the branch.

### Both Routes — Safety Rules

- Never `git add -A` or `git add .` — explicit per-file staging only
- Never add AI attribution (no `Co-Authored-By`, no `Generated with`)
- Conventional commit format (`fix:`, `feat:`, `refactor:`, `chore:`, `docs:`, `test:`)
- One commit per issue (unless changes span distinct categories)

---

## Phase 4: PR Creation

### Step 4.1: Push

```bash
git push -u origin ${BRANCH}
```

### Step 4.2: Create Ready PR

Create the PR as **ready** (not draft) — this eliminates the draft-to-ready gap that exists in the gh-do → pr-sweep pipeline:

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

Capture the PR number from the output.

### Step 4.3: Request Copilot Review

```bash
gh api repos/${OWNER}/${REPO_NAME}/pulls/${PR_NUMBER}/requested_reviewers \
  --method POST --input - <<EOF
{"reviewers":["copilot-pull-request-reviewer[bot]"]}
EOF
```

If the request returns 422: Copilot reviews may not be enabled. Log a warning and continue — the sweep phase will handle this gracefully (timeout → skip or proceed without Copilot).

---

## Phase 5: Sweep

This phase drives the PR through quality gates to merge-readiness. It reuses pr-sweep's proven patterns.

### Step 5.1: Copilot Review Gate

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
- `REVIEW_COUNT == 0` and `ATTEMPT >= 20`: **Skip issue** with reason `"Copilot review timed out"`.

**Step C — Wait and loop back:**
```bash
sleep 30
```
Increment ATTEMPT, go back to Step A. Each iteration must make a fresh API call — the sleep does not replace the check.

### Step 5.2: Fetch All Feedback

Inline code review comments:
```bash
gh api repos/${OWNER}/${REPO_NAME}/pulls/${PR_NUMBER}/comments --paginate
```

Top-level comments:
```bash
gh pr view ${PR_NUMBER} --json comments --jq '.comments[]'
```

Categorize each comment:

| Priority | Category | Criteria |
|----------|----------|----------|
| **P0** | Blocking | "must", "required", "blocking", "critical" |
| **P1** | Bug/Issue | Bug report, logic error, security issue |
| **P2** | Suggestion | "consider", "maybe", "nit", "suggestion" |
| **P3** | Question | "why", "what does this", "can you explain" |
| **Info** | Approval | "LGTM", "looks good", positive feedback |

Copilot comments (`copilot-pull-request-reviewer[bot]`) are first-class — same treatment as human reviewers.

### Step 5.3: Confidence-Based Triage

Score each actionable comment:

| Factor | Weight |
|--------|--------|
| Technical Accuracy | 35% |
| Code Evidence | 30% |
| Clear Remediation | 20% |
| Scope Impact | 15% |

- `>= threshold` (default 95%): auto-accept.
- Below threshold in auto mode (default): skip with "Below confidence threshold" reply. Use `--interactive` to prompt instead.

### Step 5.4: Remediation

Read before edit. Minimal fixes. Verify each fix (syntax, lint). If a fix breaks something, revert and flag.

### Step 5.5: Commit Fixes

```bash
git add <fixed-files>
git commit -m "fix: address review feedback for PR #${PR_NUMBER}

- <fix summary 1>
- <fix summary 2>

Resolves review comments on PR #${PR_NUMBER}"
```

### Step 5.6: Reply to ALL Comments

Every comment gets a reply. The disposition matrix:

| Disposition | Reply Template |
|-------------|---------------|
| **Fixed** | `Fixed in <sha>.` |
| **Fixed w/modification** | `Addressed in <sha>. <explanation>.` |
| **Rejected** | `Reviewed — not applying because <reason>.` |
| **Question Response** | `<answer>.` |
| **Acknowledged** | `Thanks for the review!` |
| **Skipped (Auto)** | `Below confidence threshold (<N>%) — flagging for manual review.` |
| **Deferred** | `Valid point — tracking as follow-up.` |

Post replies via API, then verify 100% reply rate.

### Step 5.7: Resolve ALL Threads

Fetch thread IDs via GraphQL, then resolve after push:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "<thread_id>"}) {
    thread { isResolved }
  }
}'
```

Resolve for ALL dispositions — fixed, rejected, answered, acknowledged, deferred.

### Step 5.8: Push + Execute Thread Resolution

Push changes (use `--force-with-lease` if rebase was performed or `--force` flag is set). Then execute the GraphQL thread resolution mutations.

### Step 5.9: CI Gate (HARD)

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

If CI fails after retry: **skip issue** with reason `"CI failed after retry: <check names>"`.

### Step 5.10: Final Verification

Verify all gates hold before merge:
- 100% comment reply rate
- All threads resolved
- CI all green
- Branch up-to-date with base

If any verification fails: **skip issue** with reason.

### Step 5.11: Merge

Skip if `--no-merge` is set (report as READINESS-ONLY).

```bash
gh pr merge ${PR_NUMBER} --squash --delete-branch
```

Or per `--merge-method`:
```bash
gh pr merge ${PR_NUMBER} --merge --delete-branch
gh pr merge ${PR_NUMBER} --rebase --delete-branch
```

If merge is blocked: **skip issue** with reason `"Merge blocked: <error>"`.

---

## Phase 6: Verification

After merge, verify the linked issue closed:

```bash
gh issue view ${ISSUE_NUMBER} --json state -q '.state'
```

If the issue is still open (closing keyword may have failed):
```bash
gh issue close ${ISSUE_NUMBER} --reason completed
```

For epics: after all sub-issues are merged, check if the epic should be closed. If all sub-issues are closed, close the epic.

Log the result: `MERGED`, `SKIPPED` (with reason), or `READINESS-ONLY`.

---

## Phase 7: Loop Control

After completing an item:

1. If `--limit=N` reached: generate report (Phase 8) and exit.
2. If queue has more items: return to Phase 1.
3. If queue is empty AND `--once` is set: generate report and exit.
4. If queue is empty AND `--once` is NOT set:
   - Log: `"Queue empty. Polling in ${POLL_INTERVAL} minutes..."`
   - Sleep for `--poll` minutes (default: 10).
   - Re-assemble queue (Phase 0.2-0.4).
   - If new items found: return to Phase 1.
   - If still empty: sleep and poll again.

---

## Phase 8: Grind Report

Generate after session completes, limit is reached, or loop is interrupted:

```
GH-GRIND Session Report
========================
Repo:                ${REPO}
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

Epics:
  #<E>: CLOSED  — 3/3 sub-issues merged
  #<F>: PARTIAL — 2/4 sub-issues merged, 2 skipped
```

If `--dry-run` was active, label the report "DRY RUN — no changes were made".

---

Begin processing now based on: $ARGUMENTS

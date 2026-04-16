---
name: gh-do
description: >
  Unified work engine — triage, implement, and resolve
  GitHub issues, PRs, and discussions end-to-end.
  Supports single item, sequential sweep, and parallel
  swarm modes with configurable batch sizes.
  Use when the user wants to actually DO work items:
  fix bugs, implement features, resolve review comments,
  fix failing CI, answer discussions, or process a
  backlog of open items. Triggers on: 'do issue 42',
  'fix this issue', 'process the backlog', 'sweep issues',
  'swarm my open issues', 'resolve PR comments',
  'gh-do'.
argument-hint: >
  <issue|pr|discussion> <number> [--repo owner/repo]
  | --sweep [--repo owner/repo] [--limit N]
  | --swarm [--batch N] [--repo owner/repo] [--limit N]
  [--dry-run]
---

# GH-Do — Unified Triage-to-Resolution Engine

You are the gh-do work engine. You read a GitHub item
(issue, PR, or discussion), triage it, then execute the
appropriate resolution workflow end-to-end.

## Arguments

The user invoked this command with: $ARGUMENTS

Parse arguments into:
- **mode**: `single`, `sweep`, or `swarm`
  (`sweep` auto-escalates to `swarm` when queue > 1 item)
- **item_type**: `issue`, `pr`, or `discussion`
  (auto-detected from argument or GitHub API)
- **item_number**: the `#N` or bare number
- **repo**: explicit `--repo owner/repo`, or resolved
  from `gh repo view --json nameWithOwner -q .nameWithOwner`
- **limit**: max items to process (default: 10)
- **batch**: workers per swarm wave (default: 5,
  range 2-10). Only applies to `--swarm` mode.
- **dry_run**: if `--dry-run`, report planned actions
  without executing them

## Setup

Determine the current repo:
```bash
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null)
```

Unless `--repo` was provided explicitly.

## Triage Pipeline Context

This command sits in a triage pipeline:

```
Layer 1: Auto-label (on: issues.opened, pr.opened)
  Stamps "needs-triage" on every new item.
       │
Layer 2: THIS COMMAND (gh-do)
  Single-item mode: triages one item (applies labels,
  removes "needs-triage"). Sweep/swarm mode: works
  POST-TRIAGE items — already labeled, prioritized,
  and ready for implementation. Skips "needs-triage"
  items (let Layer 1/single-item handle those first).
       │
Layer 3: Daily triage (cron, catch-all)
```

### Preflight Check (sweep and swarm only)

Before assembling the queue, verify the triage pipeline is set up. The `needs-triage` label is used by Layer 1 (auto-label on open) and single-item triage mode. Sweep mode does NOT filter by this label — it works post-triage items — but the label must exist for the pipeline to function.

```bash
# Ensure needs-triage label exists (used by Layer 1, not by sweep filter)
for repo in $REPOS; do
  if ! gh label list --repo "$repo" \
    --json name --jq '.[].name' \
    | grep -q "^needs-triage$"; then
    echo "WARN: needs-triage label missing in $repo"
    echo "Creating it now..."
    gh label create "needs-triage" \
      --color "c5def5" \
      --description "Awaiting triage" \
      --repo "$repo" --force
  fi
done
```

---

## Mode: Single Item

When the user provides a specific item reference:

```
/gh-do issue 42
/gh-do pr 17 --repo owner/repo
/gh-do discussion 8
```

### Step 1 — Detect Item Type

If the user specified the type (`issue`, `pr`,
`discussion`), use it directly.

If only a number was given, auto-detect by trying each
type in order. Stop at the first success:
```bash
# Try issue first
gh issue view NUMBER --repo REPO --json number 2>/dev/null
# Try PR
gh pr view NUMBER --repo REPO --json number 2>/dev/null
# Try discussion (via GraphQL because gh CLI has no
# native discussion view command)
gh api graphql -f query='
  query {
    repository(owner:"OWNER", name:"REPO") {
      discussion(number: NUMBER) { id }
    }
  }' 2>/dev/null
```

**If all three lookups fail** (the item does not exist as
an issue, PR, or discussion in the target repo), stop
immediately and report a clear error to the user. This
includes cases where discussions are disabled on the repo
(the GraphQL query returns an error instead of data).

```
Error: Item #NUMBER not found in OWNER/REPO.
Tried: issue, pull request, discussion — none matched.
Verify the number is correct and the repo is accessible.
If this is a discussion, confirm discussions are enabled
on the repository.
```

Do NOT proceed to triage or any action workflow when the
item cannot be found. Do NOT guess or assume a type.
This is a terminal error for single-item mode.

### Step 2 — Read the Item

Fetch full context for the detected item type.

**Issue**:
```bash
gh issue view NUMBER --repo REPO \
  --json number,title,body,labels,assignees,state,\
comments,milestone,projectItems,author,createdAt
```

**PR**:
```bash
gh pr view NUMBER --repo REPO \
  --json number,title,body,labels,assignees,state,\
reviews,reviewRequests,statusCheckRollup,files,\
headRefName,baseRefName,isDraft,mergeable,author
```

Also fetch the diff:
```bash
gh pr diff NUMBER --repo REPO
```

**Discussion**:
```bash
gh api graphql -f query='
  query {
    repository(owner:"OWNER", name:"REPO") {
      discussion(number: NUMBER) {
        id title body
        category { name }
        comments(first: 20) {
          nodes { body author { login } }
        }
        labels(first: 10) {
          nodes { name }
        }
      }
    }
  }'
```

If the GraphQL response returns errors or the discussion
node is null, report a clear error and stop:
```
Error: Discussion #NUMBER not found or not accessible in
OWNER/REPO. Discussions may be disabled on this repository.
```

### Step 3 — Triage

Apply classification rules:

**Type classification** (from title + body keywords):

| Keywords | Label |
|----------|-------|
| bug, error, crash, broken, fix, fail | type/bug |
| feature, add, new, implement, request | type/feature |
| docs, documentation, readme, typo | type/docs |
| question, how, why, help | type/question |
| refactor, clean, improve, optimize | type/chore |

**Priority classification**:

| Indicators | Label |
|------------|-------|
| security, vulnerability, data loss | priority/critical |
| regression, blocking, major broken | priority/high |
| default for bugs | priority/medium |
| enhancement, cosmetic, nice-to-have | priority/low |

**Area classification**: Match content against known
area labels and CODEOWNERS paths.

**For PRs additionally**:
- **Size label** based on file count and diff line count.
  Compute `total_lines = additions + deletions` from the
  diff, and `file_count` from the changed files list.
  Apply the label matching the FIRST rule that matches:

  | Label | Condition |
  |-------|-----------|
  | size/XL | total_lines > 1000 OR file_count > 30 |
  | size/L  | total_lines > 500  OR file_count > 15 |
  | size/M  | total_lines > 100  OR file_count > 5  |
  | size/S  | everything else                         |

  Apply the label:
  ```bash
  gh pr edit NUMBER --repo REPO --add-label "size/M"
  ```
- Identify linked issues from body keywords
  (`Closes`, `Fixes`, `Resolves`)
- Identify appropriate reviewers from CODEOWNERS

Apply labels:
```bash
gh issue edit NUMBER --repo REPO \
  --add-label "type/bug,priority/high,area/auth"
gh issue edit NUMBER --repo REPO \
  --remove-label "status/triage,needs-triage"
```

If `--dry-run`: report the labels and assignee that
would be applied, then stop here.

### Step 4 — Route to Action Workflow

Based on item type and triage result, execute the
appropriate workflow:

#### Issue Workflow

1. **If `type/bug` or `type/feature` or `type/chore`
   or `type/refactor`**:
   - Create a feature branch:
     ```bash
     BRANCH="gh-do/issue-NUMBER-slug"
     gh api repos/OWNER/REPO/git/refs \
       -f ref="refs/heads/$BRANCH" \
       -f sha="$(gh api repos/OWNER/REPO/git/\
refs/heads/main --jq '.object.sha')"
     ```
   - Clone or checkout the branch locally
   - Read the repository structure to understand
     the codebase
   - Implement the fix, feature, or improvement
     described in the issue
   - Write tests for the changes
   - Commit with a descriptive message
   - Push the branch
   - Create a draft PR that closes the issue.
     **Use the full `owner/repo#N` reference** so
     GitHub auto-closes the issue when the PR merges,
     even for cross-repo PRs:
     ```bash
     # Build the closing reference
     # Same-repo:  "Resolves #42"
     # Cross-repo: "Resolves owner/other-repo#42"
     if [ "$PR_REPO" = "$ISSUE_REPO" ]; then
       CLOSES_REF="Resolves #$ISSUE_NUMBER"
     else
       CLOSES_REF="Resolves $ISSUE_REPO#$ISSUE_NUMBER"
     fi

     gh pr create --repo "$PR_REPO" \
       --head "$BRANCH" \
       --title "fix: description from issue" \
       --body "$CLOSES_REF

     ## Summary
     Brief description of changes.

     ## Changes
     - Change 1
     - Change 2

     ## Test Plan
     - How to verify the fix" \
       --draft
     ```
     **Important**: The closing keyword (`Resolves`,
     `Closes`, or `Fixes`) MUST appear in the PR body
     (not just the title) for GitHub to auto-close the
     issue on merge. Use `Resolves` as the default
     keyword.
   - Apply labels from triage to the PR
   - Request reviewers from CODEOWNERS
   - Add to project board if configured
   - **Review gate** — do NOT report the PR as
     "done" until reviews are clean:
     a. Mark the PR ready for review:
        ```bash
        gh pr ready NUMBER --repo REPO
        ```
     b. Wait for automated reviews (Copilot, CI
        checks) to complete. Use Monitor or poll:
        ```bash
        # Poll until all checks complete
        until gh pr checks NUMBER --repo REPO \
          --fail-fast 2>/dev/null; do
          sleep 30
        done
        ```
     c. Read review comments:
        ```bash
        gh api repos/OWNER/REPO/pulls/NUMBER/\
reviews --jq '.[] | select(.state != \
"APPROVED") | {user: .user.login, state: \
.state, body: .body}'
        gh api repos/OWNER/REPO/pulls/NUMBER/\
comments --jq '.[] | {path: .path, line: \
.line, body: .body}'
        ```
     d. If changes are requested: fix the issues,
        commit, push, and re-request review.
        Repeat until all reviews are resolved.
     e. Only after reviews pass AND checks pass,
        report the PR as ready for merge.
   - Report the PR URL to the user

2. **If `type/docs`**:
   - Create branch, update documentation, create PR
     as above but targeting docs files

3. **If `type/question`**:
   - Post a comment answering the question if possible
   - If not answerable, add `needs-info` label
   - Close if answered:
     ```bash
     gh issue comment NUMBER --repo REPO \
       --body "Answer text"
     gh issue close NUMBER --repo REPO \
       --reason completed
     ```

#### PR Workflow

1. **If PR has changes requested**:
   - Read the review comments
   - Checkout the PR branch
   - Implement the requested changes
   - Commit and push
   - Re-request review:
     ```bash
     gh pr edit NUMBER --repo REPO \
       --add-reviewer REVIEWERS
     ```
   - Comment summarizing fixes made

2. **If PR is approved and checks pass**:
   - Confirm with user before merging
   - Merge using the repo's preferred strategy:
     ```bash
     gh pr merge NUMBER --repo REPO \
       --squash --delete-branch
     ```

3. **If PR is draft with no reviews**:
   - Triage and label
   - If ready, mark ready for review:
     ```bash
     gh pr ready NUMBER --repo REPO
     ```
   - Request reviewers

4. **If PR has failing checks**:
   - Read CI logs
   - Checkout the branch
   - Fix the failures
   - Commit and push
   - Report what was fixed

#### Discussion Workflow

**Before routing**: verify discussions are enabled and
the discussion exists. The GraphQL query for a discussion
may return an error or null if:
- Discussions are disabled on the repository
- The discussion number does not exist
- The user lacks permission to view discussions

If the GraphQL response contains errors or the discussion
node is null, report the situation clearly and skip the
discussion workflow:

```
Note: Could not fetch discussion #NUMBER in OWNER/REPO.
Discussions may be disabled on this repository, the
discussion may not exist, or permissions may be
insufficient. Skipping discussion routing.
```

Apply `needs-human` label to any linked tracking item
and move on. Do NOT attempt to create issues, post
comments, or perform any discussion actions when the
discussion data could not be fetched.

**When the discussion is successfully fetched**, route
based on category:

1. **If category is Ideas or the discussion describes
   a feature request**:
   - Create a linked issue from the discussion:
     ```bash
     DISC_URL=$(gh api graphql -f query='...' \
       --jq '.data.repository.discussion.url')
     gh issue create --repo REPO \
       --title "Title from discussion" \
       --body "From discussion: $DISC_URL

     Original description here" \
       --label "type/feature"
     ```
   - Comment on the discussion linking the issue
   - Then follow the Issue Workflow for the new issue.
     The PR created from this flow MUST include
     `Resolves owner/repo#N` referencing the newly
     created issue number, not the discussion number.

2. **If category is Q&A**:
   - Draft an answer based on codebase analysis
   - Post the answer as a comment
   - Mark as answered if confident

3. **If category is RFCs**:
   - Analyze the RFC proposal
   - Post a structured review comment covering:
     feasibility, risks, alternatives
   - If the RFC is approved (per comments), convert
     to an implementation issue

4. **If category is General or Announcements**:
   - Triage only; comment with summary and next steps
   - If actionable, convert to issue and link back

### Step 5 — Report

After completing the workflow, report:
- What was triaged (labels applied, assignee set)
- What action was taken (PR created, comment posted,
  issue created from discussion, etc.)
- Links to all created/modified resources
- Any items that need human attention

---

## Mode: Sweep

When the user invokes `--sweep`, gh-do assembles the
queue and checks item count. If more than 1 item is
queued, sweep **automatically escalates to swarm mode**
with worktree isolation and parallel workers. Sequential
processing only occurs for single-item queues.

This means `--sweep` is the default entry point for all
batch work — users never need to remember `--swarm`.

```
/gh-do --sweep
/gh-do --sweep --repo owner/repo --limit 5
/gh-do --sweep --dry-run
```

### Sweep Queue Assembly

Build a prioritized work queue from target repos:

```bash
# Determine repos to sweep
if [ -n "$EXPLICIT_REPO" ]; then
  REPOS="$EXPLICIT_REPO"
else
  REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null)
  REPOS="$REPO"
fi
```

For each repo, gather candidates:

1. **Post-triage issues** (already labeled and ready for work):
   ```bash
   # Fetch all open issues with labels (post-triage)
   gh issue list --repo REPO --state open \
     --json number,title,labels,createdAt,assignees \
     --limit 50 \
     | jq '[.[] | select(
       (.labels | length > 0) and
       (.labels | map(.name) | any(. == "needs-triage" or . == "status/triage") | not)
     )]'
   ```
   This fetches issues that HAVE labels but are NOT still in triage.
   Items labeled `needs-triage` or `status/triage` are excluded —
   those belong to Layer 1 (auto-triage on open) or single-item
   triage mode. The sweep works post-triage: items that have been
   classified, prioritized, and are ready for implementation.

   **Fallback — unlabeled issues** (these may have been missed by
   the triage pipeline; include them at lowest priority so they
   get noticed, but prefer triaged items):
   ```bash
   gh issue list --repo REPO --state open \
     --json number,title,labels,createdAt \
     | jq '[.[] | select(.labels | length == 0)]'
   ```

2. **PRs needing attention**:
   ```bash
   # PRs with changes requested
   gh pr list --repo REPO --state open \
     --json number,title,reviews,isDraft \
     --jq '[.[] | select(
       .reviews[]?.state == "CHANGES_REQUESTED"
     )]'

   # PRs with failing checks
   gh pr list --repo REPO --state open \
     --json number,title,statusCheckRollup \
     --jq '[.[] | select(
       .statusCheckRollup[]?.conclusion
       == "FAILURE"
     )]'

   # Draft PRs that might be ready
   gh pr list --repo REPO --state open --draft \
     --json number,title,createdAt
   ```

3. **Discussions needing action** (MUST query — do not skip):
   Discussions are a first-class item type alongside
   issues and PRs. Always execute this query even if
   the previous queries returned enough items.
   ```bash
   gh api graphql -f query='
     query {
       repository(owner:"OWNER", name:"REPO") {
         discussions(
           first: 20,
           orderBy: {field: CREATED_AT, direction: DESC}
         ) {
           nodes {
             number title
             category { name }
             labels(first: 5) {
               nodes { name }
             }
             comments { totalCount }
             answerChosenAt
           }
         }
       }
     }'
   ```
   **If the query returns a GraphQL error** (e.g.,
   discussions are disabled on the repo), log a warning
   and continue with issues and PRs only:
   ```
   WARN: Could not query discussions for OWNER/REPO
   (discussions may be disabled). Continuing with
   issues and PRs.
   ```

   **If the query succeeds**, filter the results to
   actionable discussions:
   - Unanswered Q&A (answerChosenAt is null)
   - Ideas category without linked issues
   - New discussions without labels
   - RFCs without review comments

### Sweep Priority Order

Process items in this order (all post-triage — `needs-triage` items are excluded from the queue):

1. `priority/critical` issues (any repo)
2. `priority/high` issues
3. PRs with changes requested (stale first)
4. PRs with failing CI
5. `priority/medium` issues
6. Unanswered discussions (Q&A)
7. Feature discussions without linked issues
8. `priority/low` issues
9. Unlabeled issues (triage pipeline may have missed these)
10. Draft PRs

### Sweep Auto-Escalation

After assembling the queue, if there is more than 1 item,
automatically escalate to swarm mode. Sequential sweep
is wasteful when parallel execution is available.

```
queue = assemble_and_prioritize()

if queue.length > 1:
  report "Queue has {queue.length} items — escalating to swarm mode"
  escalate_to_swarm(queue, batch=min(queue.length, 5))
  return

# Only reaches here if exactly 1 item in queue
report "Queue has 1 item — processing directly"
```

### Sweep Execution Loop (Single Item)

When exactly 1 item remains after auto-escalation check:

```
items_processed = 0
queue = assemble_and_prioritize()

while queue is not empty
  and items_processed < limit:

    item = queue.pop_highest_priority()

    report "--- Processing item {n} of {total} ---"
    report "Repo: {item.repo}"
    report "Type: {item.type} #{item.number}"
    report "Title: {item.title}"

    # Execute the single-item workflow
    execute_single_item_workflow(item)

    items_processed += 1

report "=== Sweep Complete ==="
report "Processed: {items_processed} items"
report "Remaining: {queue.length} items"
```

### Sweep Dry Run

If `--dry-run` is set:
- Assemble the queue as normal
- For each item, show what would be done:
  - Labels that would be applied
  - Action that would be taken
  - Estimated complexity
- Do NOT execute any mutations
- Report the full plan as a numbered checklist

### Sweep Report

At the end of a sweep, generate a summary report:

```markdown
## GH-Do Sweep Report

**Repos swept**: repo1, repo2, repo3
**Items processed**: 7 of 12

<details>
<summary>Issues Resolved (3)</summary>

| # | Repo | Title | Action | PR |
|---|------|-------|--------|----|
| 42 | owner/repo1 | Login bug | Fix PR | #55 |
| 18 | owner/repo2 | Add docs | Docs PR | #19 |
| 7 | owner/repo1 | Question | Answered | — |

</details>

<details>
<summary>PRs Updated (2)</summary>

| # | Repo | Title | Action |
|---|------|-------|--------|
| 33 | owner/repo1 | Refactor | Fixed review comments |
| 12 | owner/repo2 | Feature | Fixed CI failures |

</details>

<details>
<summary>Discussions Handled (2)</summary>

| # | Repo | Title | Action |
|---|------|-------|--------|
| 5 | owner/repo1 | Feature idea | Issue #43 created |
| 9 | owner/repo1 | How to X? | Answered |

</details>

<details>
<summary>Remaining Queue (5)</summary>

| # | Repo | Type | Title | Priority |
|---|------|------|-------|----------|
| 99 | owner/repo3 | issue | Complex refactor | medium |

</details>
```

---

## Mode: Swarm

When the user invokes `--swarm`, gh-do spawns a team of
parallel worker agents that process multiple items
concurrently in batches. This is the high-throughput
mode for large backlogs.

```
/gh-do --swarm
/gh-do --swarm --batch 8 --limit 40
/gh-do --swarm --batch 5 --repo owner/repo
/gh-do --swarm --dry-run
```

### Swarm Architecture

```
Leader (you)
  ├── Assembles prioritized queue (same as sweep)
  ├── Creates team "gh-do-swarm"
  ├── Creates ALL tasks upfront from queue
  ├── Spawns N worker teammates (--batch size)
  ├── Workers self-assign continuously from pool
  ├── Leader monitors, reassigns failures
  └── Shutdown when all tasks done or --limit hit
```

**Key design**: `--batch` controls **worker count**,
not task-wave size. ALL tasks are created upfront in
Step 3. Workers loop continuously, picking the next
available task after completing each one.

Roles:
- **Leader**: queue assembly, task creation (all at
  once), teammate spawning, progress tracking,
  reporting, confirmation gates for destructive actions
- **Workers**: each picks a task, triages the item,
  executes the action workflow, reports back, picks
  next task — repeating until no tasks remain.
  Workers run in git worktrees for isolation when
  implementing code changes.

### Step 1 — Assemble Queue

Use the same queue assembly and priority logic as
sweep mode (see Sweep Queue Assembly above). The
queue is identical — only the execution model differs.

### Step 2 — Create Team

```
TeamCreate({
  team_name: "gh-do-swarm",
  description: "gh-do parallel work processing"
})
```

### Step 3 — Create ALL Tasks from Queue

Create a task for **every** item in the queue upfront
(up to `--limit`). Do NOT batch task creation — workers
need a full pool to draw from continuously.

```
TaskCreate({
  subject: "[repo] type #N: title",
  description: "## Item Details
    - **Type**: issue | pr | discussion
    - **Repo**: owner/repo
    - **Number**: N
    - **Title**: item title
    - **Priority**: critical | high | medium | low
    - **URL**: https://github.com/owner/repo/...

    ## Instructions
    1. Read the item using gh CLI
    2. Triage: apply type/priority/area labels
    3. Execute the action workflow per item type
       (see gh-do skill docs)
    4. Report: what was done, links created
    5. If blocked or uncertain, apply needs-human
       label and move on

    ## Confirmation Rules
    - Creating draft PRs: proceed without asking
    - Applying labels: proceed without asking
    - Posting comments: proceed without asking
    - Merging PRs: DO NOT merge, flag for leader
    - Closing issues: DO NOT close, flag for leader

    ## Worktree
    Use isolation: worktree when implementing code
    changes so workers don't conflict on branches.",
  activeForm: "Working on [repo] type #N"
})
```

Use task dependencies to serialize items that touch
the same files. Otherwise, leave all tasks unblocked
so workers can claim them freely.

### Step 4 — Spawn Workers

Spawn `--batch` workers as background teammates.
Each worker is a `general-purpose` agent with full
tool access running in the team context.

Worker prompt template:

```
You are a gh-do work agent on team "gh-do-swarm".
Your job is to pick tasks, triage GitHub items, and
execute the resolution workflow.

## Your Loop — KEEP WORKING UNTIL DONE

You MUST loop continuously until there are zero
pending tasks left. Do NOT stop after one task.

```
while true:
  1. Call TaskList
  2. Find a pending task with no owner and
     empty blockedBy
  3. If no tasks available → send "all tasks
     done" to leader → go idle (leader sends
     shutdown_request)
  4. Claim the task: TaskUpdate(taskId, owner=
     your name, status=in_progress)
  5. Read the task description for item details
  6. Execute the gh-do single-item workflow:
     a. Read the item (gh issue/pr view or
        GraphQL)
     b. Triage (classify type/priority/area,
        apply labels, remove triage labels)
     c. Route to action workflow:
        - Issue: branch in worktree → implement
          → test → commit → push → draft PR
          with 'Resolves owner/repo#N' in body
          (use full owner/repo#N form always)
        - PR with changes requested: checkout →
          fix → push → re-request review
        - PR failing CI: read logs → fix → push
        - Discussion (Ideas): create issue →
          link back
        - Discussion (Q&A): post answer
        - Discussion (RFC): review comment
     d. Report results in task description
  7. Mark task completed: TaskUpdate(taskId,
     status=completed)
  8. Send concise findings to leader via
     SendMessage
  9. IMMEDIATELY loop back to step 1 — do NOT
     wait, do NOT go idle, do NOT ask the leader
     for more work. Just check TaskList again.
```

CRITICAL: The only valid reason to stop looping is
when TaskList shows zero pending unowned tasks. If
there are pending tasks, claim one and keep going.

## Rules
- ALWAYS use isolation: "worktree" when creating
  PRs. Every worker MUST operate in its own
  worktree to avoid branch collisions.
- DO NOT merge PRs — flag for leader review
- DO NOT close issues — flag for leader review
- If stuck or uncertain, apply "needs-human"
  label, mark task completed with a note, move on
- Keep messages to leader concise: what you did,
  links to resources created, any flags
```

Spawn workers in parallel, each in its own worktree:
```
for i in 1..batch_size:
  Task({
    team_name: "gh-do-swarm",
    name: "worker-{i}",
    subagent_type: "general-purpose",
    prompt: WORKER_PROMPT,
    run_in_background: true,
    isolation: "worktree"
  })
```

### Step 5 — Leader Coordination Loop

All tasks are already created. Workers loop
autonomously. The leader only intervenes for flags
and failures.

While the swarm is running, the leader:

1. **Monitors progress**: receives SendMessage from
   workers as they complete tasks.

2. **Handles flags**: when a worker flags an item
   for leader review (merge, close), the leader:
   - Reviews the worker's findings
   - Asks the user for confirmation if needed
   - Executes the destructive action or skips it

3. **Tracks overall progress**: periodically check
   TaskList to see how many tasks remain.

4. **Handles failures**: if a worker reports being
   stuck or goes idle with an in_progress task:
   - Unassign the task (set owner to empty)
   - Another worker will claim it on their next
     TaskList check
   - If genuinely blocked, mark `needs-human`

### Step 5.5 — Review Phase

After all worker tasks are complete and PRs are
created, the leader runs a review phase before
any merges. PRs are NOT "done" when created —
they are drafts awaiting review.

1. **Mark all PRs ready**:
   ```bash
   for PR in $PR_NUMBERS; do
     gh pr ready "$PR" --repo REPO
   done
   ```

2. **Wait for reviews to complete**: Use Monitor
   to watch all PRs for review completion:
   ```bash
   # Poll all PRs until checks + reviews settle
   for PR in $PR_NUMBERS; do
     until gh pr checks "$PR" --repo REPO \
       --fail-fast 2>/dev/null; do
       sleep 30
     done
   done
   ```
   Or use Monitor for streaming:
   ```bash
   Monitor({
     description: "Watching PRs for review completion",
     command: "for PR in $PR_NUMBERS; do ..."
   })
   ```

3. **Read review feedback**: For each PR, fetch
   review comments and changes-requested reviews:
   ```bash
   gh api repos/OWNER/REPO/pulls/PR/reviews \
     --jq '.[] | select(.state ==
     "CHANGES_REQUESTED") | {user: .user.login,
     body: .body}'
   gh api repos/OWNER/REPO/pulls/PR/comments \
     --jq '.[] | {path: .path, line: .line,
     body: .body}'
   ```

4. **Fix review feedback**: For each PR with
   changes requested:
   - Checkout the PR branch (in a worktree)
   - Address the review comments
   - Commit and push
   - Re-request review
   - Wait for the re-review to complete

5. **Merge gate**: Only after ALL PRs have:
   - All CI checks passing
   - All reviews approved (or no changes requested)
   - No unresolved review comments
   proceed to Step 6 (merge confirmation).

### Step 6 — Merge and Shutdown

When all PRs are reviewed, approved, and checks pass:

1. **Merge PRs** — present the merge list to the
   user for confirmation, then merge:
   ```bash
   for PR in $APPROVED_PRS; do
     gh pr merge "$PR" --repo REPO \
       --squash --delete-branch
   done
   ```

2. **Shutdown workers**:
   ```
   for worker in workers:
     SendMessage({
       type: "shutdown_request",
       recipient: worker.name,
       content: "Sweep complete, shutting down"
     })
   ```

3. **Cleanup**: Wait for shutdown approvals, then:
   ```
   TeamDelete()
   ```

### Swarm Dry Run

If `--dry-run`:
- Assemble queue and create the task list
- Report what would be processed, in what order,
  with how many workers per batch
- Do NOT spawn workers or execute any mutations

### Swarm Report

```markdown
## GH-Do Swarm Report

**Mode**: swarm (batch size: 5)
**Workers spawned**: 5
**Repos swept**: repo1, repo2, repo3
**Items processed**: 14 of 14

<details>
<summary>Worker Summary</summary>

| Worker | Tasks | Completed | Flagged |
|--------|-------|-----------|---------|
| worker-1 | 3 | 3 | 0 |
| worker-2 | 3 | 3 | 1 |
| worker-3 | 3 | 2 | 1 |
| worker-4 | 3 | 3 | 0 |
| worker-5 | 2 | 2 | 0 |

</details>

<details>
<summary>Issues Resolved (8)</summary>

| # | Repo | Title | Action | PR | Worker |
|---|------|-------|--------|----|--------|

</details>

<details>
<summary>PRs Updated (4)</summary>

| # | Repo | Title | Action | Worker |
|---|------|-------|--------|--------|

</details>

<details>
<summary>Discussions Handled (2)</summary>

| # | Repo | Title | Action | Worker |
|---|------|-------|--------|--------|

</details>

<details>
<summary>Flagged for Human Review (2)</summary>

| # | Repo | Type | Title | Reason |
|---|------|------|-------|--------|
| 55 | owner/repo1 | pr | Feature | Ready to merge |
| 12 | owner/repo2 | issue | Complex | Needs design |

</details>
```

### Batch Sizing Guidance

| Batch Size | Best For |
|------------|----------|
| 2-3 | Small backlogs, conservative resource use |
| 5 (default) | Normal workloads, good parallelism |
| 7-8 | Large backlogs across many repos |
| 10 (max) | Clearing massive queues quickly |

### Conflict Avoidance

When multiple workers target the same repo:
- Each worker uses `isolation: "worktree"` to get
  its own copy of the repo
- Branch names include the issue number to avoid
  collisions: `gh-do/issue-NUMBER-slug`
- Workers do NOT modify the same files unless the
  issues are unrelated
- If two items would touch the same files, the
  leader assigns them to the same worker
  sequentially via task dependencies:
  ```
  TaskUpdate({
    taskId: "task-for-issue-99",
    addBlockedBy: ["task-for-issue-42"]
  })
  ```

---

## Issue Closing References

Every PR created from an issue MUST include a GitHub
closing keyword in the PR **body** so the issue
auto-closes when the PR is merged.

### Rules

1. **Always use the full `owner/repo#N` form** — this
   works for same-repo and cross-repo PRs alike.

2. **Use `Resolves` as the default keyword**.

3. **Place the reference on its own line at the top
   of the PR body**, before the Summary section.

4. **Multiple issues**: if a single PR addresses
   several issues, list each on its own line:
   ```
   Resolves owner/repo#42
   Resolves owner/repo#43
   ```

5. **Discussion-sourced issues**: when a discussion
   is converted to an issue and then a PR is created,
   the PR must reference the **issue** number, not
   the discussion number.

6. **The title is not enough**: GitHub only parses
   closing keywords from the PR body and commit
   messages on the default branch.

### Template

```
Resolves {owner}/{repo}#{issue_number}

## Summary
...
```

---

## Confirmation Gates

These actions require user confirmation before
execution (unless `--dry-run` skips all mutations):

- **Merging a PR** — requires ALL of:
  1. All CI checks passing
  2. All reviews resolved (no pending
     changes-requested)
  3. User confirmation
  Never merge a PR that has not been reviewed.
  Passing CI is not a substitute for review.
- **Closing an issue** — confirm with reason
- **Posting a comment** — show draft, confirm
- **Creating a PR** — show branch name and title,
  confirm before push
- **Creating an issue from discussion** — show the
  issue title/body draft, confirm

In sweep mode, batch confirmations where possible.

In swarm mode, workers do NOT confirm — they flag
destructive actions for the leader. The leader
batches flagged items and presents them to the user
for approval.

## Error Handling

- If `gh` is not authenticated: stop and prompt
  `gh auth login`
- If a repo is not accessible: skip it, log warning,
  continue sweep
- If an item cannot be resolved (e.g., too complex):
  apply `needs-human` label and move to next item
- If CI fix attempt fails: leave a comment describing
  what was tried, keep the PR as-is
- If implementation is uncertain: create a draft PR
  with `[WIP]` prefix and request human review

## Integration

This command composes with other skills:
- **gh-work** — workplan management and organization
- **pr** / **pr-review** / **pr-fix** — PR lifecycle
- **feature-dev** — guided feature development
- **Swarm primitives**: `TeamCreate`, `TeamDelete`,
  `TaskCreate`, `TaskList`, `TaskGet`, `TaskUpdate`,
  `SendMessage`
- **Orchestration pattern**: Swarm (self-organizing
  workers claiming from a shared task pool)

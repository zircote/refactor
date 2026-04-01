---
name: pr-sweep
description: "Strict gated sequential PR sweep — requests Copilot review, remediates all comments, enforces CI green, resolves conflicts, and auto-merges every eligible PR. Use this skill when the user wants to sweep PRs, merge all ready PRs, clean up open PRs, process all PRs end-to-end, drive PRs to merge, or do a full PR sweep. Triggers on: 'sweep my PRs', 'sweep all PRs', 'merge all ready PRs', 'pr-sweep', 'process all open PRs', 'clean up my PRs and merge them', 'sweep PRs 10..15', 'merge everything that passes'. Anti-triggers (do NOT match): 'fix PR comments' without merge intent (use /pr-fix), 'create a PR' (use /pr), 'review this PR' (use /pr-review), 'just push' (use /cp), 'rebase only' (use /fr), 'read PR comments' (use /review-comments)."
argument-hint: "[pr-number...] [--interactive] [--confidence=N] [--no-merge] [--merge-method=METHOD] [--skip-rebase] [--dry-run] [--force]"
---

# PR Sweep — Strict Gated Sequential PR Processing

You are a PR sweep agent. Your job is to drive every eligible pull request through a strict quality pipeline — Copilot review, comment remediation, conflict-free rebase, CI green — and auto-merge those that pass all gates. PRs that fail any gate are skipped with a logged reason.

This is NOT `/pr-fix`. The key differences:

| Aspect | /pr-fix | /pr-sweep |
|--------|---------|-----------|
| CI | Advisory (never blocks) | **Hard gate** (must pass or PR is skipped) |
| Copilot review | Handles existing comments only | **Requests review if missing**, waits for completion |
| Merge | Never merges | **Auto-merges** when all gates pass |
| Retry | No retry concept | **One retry** per gate failure before skip |
| Skip semantics | Continues on failure | **Skips with logged reason**, continues to next PR |
| Mental model | "Fix what reviewers said" | "Make every PR merge-ready and merge it" |

**Core guarantees:**
1. **Every comment gets a reply** — no comment left unanswered (Fixed, explained, or acknowledged)
2. **Every thread gets resolved** — all dispositions, not just fixes
3. **Copilot must review** — requested if missing, waited on, comments remediated
4. **CI must be green** — hard gate, one retry, then skip
5. **Sequential processing** — one PR fully completed before the next begins
6. **Safe by default** — draft PRs skipped, `--no-merge` available, `--dry-run` for preview

---

## Arguments

**$ARGUMENTS**: Optional PR number(s) and flags.

Parse `$ARGUMENTS` for the following **before** any other processing:

- If `$ARGUMENTS` contains `--help`, `-h`, or `help`: display the man-page style help below and stop.
- **PR numbers**: One or more positional numeric arguments, space-separated. Supports range syntax `N..M` (e.g., `10..15` expands to PRs 10, 11, 12, 13, 14, 15). **If omitted, discover ALL open PRs** via `gh pr list --state open --json number -q '.[].number'` and process them all.
- `--interactive` — Interactive mode. Prompt for sub-threshold fixes instead of skipping them. By default, the skill runs in **auto mode** (non-interactive).
- `--confidence=N` — Confidence threshold 0-100 (default: 95). Fixes scoring at or above this threshold are auto-accepted. In auto mode (default), sub-threshold fixes are skipped with a logged reply.
- `--no-merge` — Drive PRs to merge-readiness but skip the merge step. Produces a readiness report instead.
- `--merge-method=METHOD` — Merge strategy: `squash` (default), `merge`, or `rebase`.
- `--skip-rebase` — Skip the rebase phase entirely.
- `--dry-run` — Show the sweep plan without executing any mutations.
- `--force` — Push with `--force-with-lease` instead of normal push.

### Natural Language Flag Inference

When `$ARGUMENTS` are natural language rather than explicit flags, map intent to the closest flag:

| Natural Language | Maps To |
|-----------------|---------|
| "don't merge", "readiness only", "just fix" | `--no-merge` |
| "interactive mode", "ask me first", "prompt me" | `--interactive` |
| "don't rebase", "skip rebase", "already rebased" | `--skip-rebase` |
| "force push", "force-push" | `--force` |
| "just show me", "preview", "what would change" | `--dry-run` |
| "rebase merge", "merge commit", "no squash" | `--merge-method=merge` or `--merge-method=rebase` |

---

## Help Output

When help is requested, display this and stop:

```
PR-SWEEP(1)                  GPM Skills Manual                  PR-SWEEP(1)

NAME
    pr-sweep — strict gated PR sweep: review, fix, rebase, CI, merge

SYNOPSIS
    /pr-sweep [pr-number...] [--interactive] [--confidence=N] [--no-merge]
              [--merge-method=METHOD] [--skip-rebase] [--dry-run] [--force]

DESCRIPTION
    Discovers all open PRs (or accepts an explicit list), then processes
    each sequentially through a strict quality pipeline:

      1. Request Copilot review (if not present), wait for completion
      2. Fetch and remediate ALL comments (Copilot + human)
      3. Rebase onto base branch, resolve conflicts
      4. Push, wait for CI green (hard gate, one retry)
      5. Verify all gates hold
      6. Auto-merge via squash (or specified method)

    PRs that fail any gate are skipped with a logged reason. Sequential
    processing prevents merge conflict cascading.

OPTIONS
    pr-number...
        One or more PR numbers, space-separated. Range syntax N..M
        supported. If omitted, ALL open PRs are discovered and processed.

    --interactive
        Interactive mode. Prompt for sub-threshold fixes instead of
        skipping them. Default is auto (non-interactive).

    --confidence=N
        Confidence threshold 0-100 (default: 95).

    --no-merge
        Drive to readiness but skip the merge step.

    --merge-method=METHOD
        Merge strategy: squash (default), merge, or rebase.

    --skip-rebase
        Skip the rebase phase.

    --dry-run
        Show sweep plan without mutations.

    --force
        Push with --force-with-lease.

EXAMPLES
    /pr-sweep
        Sweep all open PRs: review, fix, rebase, CI, merge.

    /pr-sweep 42
        Sweep only PR #42.

    /pr-sweep 10..15
        Sweep PRs #10-15 (auto mode is default).

    /pr-sweep --no-merge --dry-run
        Preview sweep plan for all PRs without merging or mutating.

    /pr-sweep --merge-method=rebase
        Sweep all PRs, merge via rebase instead of squash.

SEE ALSO
    /pr-fix             Fix review comments (no merge, CI advisory)
    /pr                 Create or manage pull requests
    /pr-review          Review a PR (reviewer perspective)
    /review-comments    Triage and respond to PR comments
    /cp                 Commit and push changes
    /fr                 Fetch and rebase
```

---

## Phase 0: Multi-PR Orchestration

This phase activates when multiple PR numbers are provided, or when NO PR numbers are provided (meaning "all open PRs").

### Step 0.1: Expand PR List

1. Parse `$ARGUMENTS` for positional numbers and range expressions.
   - Range syntax: `10..15` expands to `[10, 11, 12, 13, 14, 15]`.
   - Mixed: `10 22..25 30` expands to `[10, 22, 23, 24, 25, 30]`.
   - **No PR numbers provided**: Discover ALL open PRs:
     ```bash
     gh pr list --state open --json number,headRefName,isDraft,title -q '.[] | "\(.number)\t\(.isDraft)\t\(.headRefName)\t\(.title)"'
     ```
     Display the discovered list before processing.
2. **Filter draft PRs**: Remove any PR where `isDraft` is true. Log each skipped draft:
   ```
   Skipping PR #<N> (draft): <title>
   ```
3. Validate each remaining PR exists and is open:
   ```bash
   gh pr view ${PR_NUMBER} --json number,state -q '.number' 2>/dev/null
   ```
4. Store the original branch name:
   ```bash
   git branch --show-current
   ```

### Step 0.2: Sequential Processing

Process each PR through Phases 1–14 **sequentially**. After completing all phases for one PR:
1. Record the result (MERGED, SKIPPED, READINESS-ONLY).
2. Checkout the next PR's branch via `gh pr checkout ${NEXT_PR}`.
3. Begin Phase 1 for the next PR.

If a PR is **skipped** during processing, log the skip reason and continue to the next PR. Do not abort the batch.

### Step 0.3: Batch Summary

After all PRs are processed, generate the batch sweep summary (see Phase 14).

If exactly one PR number is explicitly provided (e.g., `/pr-sweep 42`), skip Phase 0 orchestration and proceed directly to Phase 1.

---

## Phase 1: Initialization

### Step 1.1: Verify Prerequisites

1. Verify `gh` CLI is authenticated:
   ```bash
   gh auth status
   ```
   If not authenticated, stop and instruct the user to run `gh auth login`.

2. Verify git repository:
   ```bash
   git rev-parse --is-inside-work-tree
   ```

3. Determine repo owner and name:
   ```bash
   gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'
   ```

### Step 1.2: Fetch PR Metadata

```bash
gh pr view ${PR_NUMBER} --json title,body,baseRefName,headRefName,state,isDraft,reviewDecision,author,url,number
```

Store `baseRefName` and `headRefName` for later use.

**If the PR is a draft**: skip immediately with reason "Draft PR". This is a safety check in case Phase 0 filtering missed it.

### Step 1.3: Sync Local Branch

1. Checkout the PR branch:
   ```bash
   gh pr checkout ${PR_NUMBER}
   ```
   In batch mode, checkout automatically without prompting.
2. Check for uncommitted changes via `git status --porcelain`. If dirty:
   - In batch/auto mode: stash automatically with `git stash push -m "pr-sweep-stash-PR${PR_NUMBER}"`.
   - In interactive mode: warn and ask whether to stash.

---

## Phase 2: Copilot Review Gate

This is the first gate and what distinguishes pr-sweep from pr-fix. Copilot must review the PR before any remediation begins.

### Step 2.1: Check Existing Reviews

The Copilot PR reviewer bot is named `copilot-pull-request-reviewer[bot]` (NOT `copilot[bot]`). Check for its review:

```bash
gh pr view ${PR_NUMBER} --json reviews -q '.reviews[] | select(.author.login == "copilot-pull-request-reviewer[bot]") | .state'
```

Look for a review with state `APPROVED`, `CHANGES_REQUESTED`, or `COMMENTED`. Any of these means Copilot has completed its review. Also check `copilot[bot]` as a fallback — some repos may use the older bot name.

### Step 2.2: Request Copilot Review

If no Copilot review exists, request one using `gh api` with the correct bot name and JSON body format:

```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/requested_reviewers \
  --method POST --input - <<EOF
{"reviewers":["copilot-pull-request-reviewer[bot]"]}
EOF
```

**IMPORTANT — known pitfalls:**
- The `mcp__github__request_copilot_review` tool may return 404 — it uses an internal endpoint that isn't always available. If it fails, fall back to the `gh api` command above.
- Do NOT use `gh api -f '{"reviewers":...}'` — the `-f` flag expects `key=value` format, not raw JSON. Use `--input -` with a heredoc to pass the JSON body.
- The bot name is `copilot-pull-request-reviewer[bot]`, NOT `copilot[bot]`. Using the wrong name will succeed silently but no review will be requested.

If the request returns 422 (validation error), the repo may not have Copilot reviews enabled. **Skip PR** with reason `"Copilot reviews not enabled for this repository"`.

### Step 2.3: Wait for Copilot Completion

Poll for Copilot review completion using an explicit check-sleep-recheck loop.

**CRITICAL — the poll loop must actually re-query GitHub on each iteration.** Do NOT just sleep and assume the review arrived. Each iteration must make a fresh API call to check for the review.

Execute this loop exactly as written — each step is a separate Bash tool call:

**Step A — Check:**
```bash
REVIEW_COUNT=$(gh pr view ${PR_NUMBER} --json reviews -q '[.reviews[] | select(.author.login == "copilot-pull-request-reviewer[bot]" or .author.login == "copilot[bot]")] | length')
echo "Poll attempt ${ATTEMPT}/20: Copilot review count = $REVIEW_COUNT"
```

**Step B — Evaluate result:**
- If `REVIEW_COUNT > 0`: Copilot review found. Proceed to Phase 3.
- If `REVIEW_COUNT == 0` and `ATTEMPT < 20`: Go to Step C.
- If `REVIEW_COUNT == 0` and `ATTEMPT >= 20`: **Skip PR** with reason `"Copilot review timed out after 10 minutes"`.

**Step C — Wait and loop back:**
```bash
sleep 30
```
Then increment ATTEMPT and go back to Step A.

The key is that **Step A runs a fresh `gh pr view` call every iteration**. The sleep in Step C is just a delay between checks — it does not replace the check. A loop that only sleeps without re-querying will never detect the review.

The timeout (20 attempts × 30 seconds = 10 minutes) exists because Copilot may not be enabled for the repo or may be experiencing service issues.

---

## Phase 3: Fetch All Feedback

### Step 3.1: Code Review Comments

Fetch inline code review comments:

```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments --paginate
```

Parse each comment for: `id`, `body`, `path`, `line` (or `original_line`), `diff_hunk`, `user.login`, `created_at`, `in_reply_to_id`, `pull_request_review_id`.

### Step 3.2: Issue-Style Comments

```bash
gh pr view ${PR_NUMBER} --json comments --jq '.comments[]'
```

### Step 3.3: Review Status

```bash
gh pr view ${PR_NUMBER} --json reviews,reviewRequests --jq '{reviews: .reviews, reviewRequests: .reviewRequests}'
```

### Step 3.4: Categorize Feedback

Assign each comment a priority category:

| Priority | Category | Criteria |
|----------|----------|----------|
| **P0** | Blocking | Reviewer requested changes, "must", "required", "blocking", "critical" |
| **P1** | Bug/Issue | Reports a bug, logic error, security issue |
| **P2** | Suggestion | Style improvements, "consider", "maybe", "nit", "suggestion" |
| **P3** | Question | "why", "what does this", "can you explain" |
| **Info** | Approval | "LGTM", "looks good", positive feedback |

Skip comments that are:
- Already resolved threads
- Pure CI/linting status bot comments with no actionable suggestion

**Do NOT skip:**
- **GitHub Copilot review comments** — first-class treatment. The primary Copilot PR reviewer bot is `copilot-pull-request-reviewer[bot]` (NOT `copilot[bot]`). Also check `copilot[bot]` as a fallback. Comments from either receive the same priority categorization, confidence scoring, remediation, reply, and thread resolution as human reviewer comments.
- **Approval comments** — acknowledged with a reply.

---

## Phase 4: Confidence-Based Triage

For each actionable comment (P0-P3), compute a confidence score:

| Factor | Weight | Description |
|--------|--------|-------------|
| Technical Accuracy | 35% | Is the reviewer's observation correct? |
| Code Evidence | 30% | Can the issue be verified from the code? |
| Clear Remediation | 20% | Is there an unambiguous fix? |
| Scope Impact | 15% | Is the fix localized or cascading? |

### Threshold Logic

Default confidence threshold: **95%** (override with `--confidence=N`).

- **>= threshold**: Auto-accept.
- **70% to threshold-1%**: Prompt the user (only in `--interactive` mode).
- **50-69%**: Detailed prompt with uncertainty noted (only in `--interactive` mode).
- **< 50%**: Skeptical prompt, recommend manual review (only in `--interactive` mode).

By default (auto mode), only fixes at or above the threshold are applied. Sub-threshold fixes are skipped with a "Below confidence threshold" reply. Use `--interactive` to prompt for each sub-threshold fix instead.

### Step 4.1: Display Triage Summary

Always display a triage summary before remediation: every comment with priority, confidence score, proposed fix, and disposition.

**If `--dry-run`**: Display the triage summary, label it "DRY RUN — no changes were made", and **stop here**. Do not proceed to Phase 5 or beyond.

---

## Phase 5: Remediation

### Step 5.1: Read Before Edit

Always read the target file before making changes. Use targeted reads with offset/limit for large files. Confirm code context matches the comment.

### Step 5.2: Apply Minimal Fixes

- Smallest change that addresses the feedback.
- No surrounding refactoring unless explicitly requested.
- No new patterns or dependencies unless required.
- Preserve existing code style.

### Step 5.3: Specialist Agent Routing

For complex fixes, delegate to a specialist agent via the Task tool. Each specialist receives the comment text, file paths, line numbers, diff hunk, and clear instructions.

### Step 5.4: Verify Each Fix

1. Check file is syntactically valid.
2. Run fast feedback tools (linter, type checker) if available.
3. If the fix breaks something, revert and flag for manual review.

---

## Phase 6: Rebase

**Skip if `--skip-rebase` is set.**

### Step 6.1: Fetch Latest Base

```bash
git fetch origin ${BASE_BRANCH}
```

### Step 6.2: Rebase

```bash
git rebase origin/${BASE_BRANCH}
```

### Step 6.3: Handle Conflicts

If rebase encounters conflicts:
1. Attempt auto-resolution for trivial conflicts (whitespace, import ordering).
2. If conflicts are non-trivial:
   - In interactive mode: show conflicting files, offer resolution options (resolve, abort, skip).
   - In auto mode (default): **skip PR** with reason `"Unresolvable merge conflict in <files>"`. Run `git rebase --abort`.

Unresolvable conflicts are a hard skip — the sweep continues to the next PR rather than blocking.

### Step 6.4: Verify Rebase

```bash
git log --oneline -5
```

---

## Phase 7: Commit Changes

### Step 7.1: Stage Changes

Stage only modified files explicitly:

```bash
git add <file1> <file2> ...
```

Never use `git add -A` or `git add .`.

### Step 7.2: Commit

```bash
git commit -m "$(cat <<'EOF'
fix: address review feedback for PR sweep

- <summary of fix 1>
- <summary of fix 2>

Resolves review comments on PR #${PR_NUMBER}
EOF
)"
```

Rules:
- Conventional commit format (`fix:`, `refactor:`, `style:`, `docs:`).
- **Never add AI attribution** — no `Co-Authored-By`, no `Generated with`.
- Split commits by category if changes span multiple types.

---

## Phase 8: Reply to ALL Comments

**Every comment MUST receive a reply.** This is non-negotiable.

### Disposition Matrix

| Disposition | When | Reply Template |
|-------------|------|---------------|
| **Fixed** | Addressed as requested | `Fixed in <sha>.` |
| **Fixed w/modification** | Addressed with variation | `Addressed in <sha>. <explanation>.` |
| **Rejected** | Reviewed, intentionally not applied | `Reviewed — not applying because <reason>.` |
| **Question Response** | Answering a question | `<answer>. <optional ref>.` |
| **Acknowledged** | Approval/LGTM | `Thanks for the review!` |
| **Skipped (Auto)** | Below threshold in auto mode (default) | `Below confidence threshold (<N>%) — flagging for manual review.` |
| **Deferred** | Valid but out of scope | `Valid point — tracking as follow-up.` |

### Step 8.1: Completeness Check

Verify every comment from Phase 3 has a disposition. If any lacks one, assign it now.

### Step 8.2: Post Replies

For inline comments:
```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments \
  -f body="<reply>" -F in_reply_to=<comment_id>
```

For top-level comments:
```bash
gh pr comment ${PR_NUMBER} --body "<reply>"
```

### Step 8.3: Verify 100% Reply Rate

Compare total replies posted against total comments from Phase 3. If any were missed, reply to them before proceeding.

---

## Phase 9: Resolve ALL Threads

### Step 9.1: Get Thread IDs

```bash
gh api graphql -f query='
query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: '${PR_NUMBER}') {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { id databaseId body }
          }
        }
      }
    }
  }
}'
```

Match threads to comments processed in Phases 5 and 8. Store ALL unresolved thread IDs for resolution after push.

---

## Phase 10: Push + Thread Resolution

### Step 10.1: Push

If `--force` is set OR rebase was performed:
```bash
git push --force-with-lease origin ${HEAD_BRANCH}
```

Otherwise:
```bash
git push origin ${HEAD_BRANCH}
```

### Step 10.2: Verify Push

```bash
gh pr view ${PR_NUMBER} --json commits --jq '.commits | length'
```

### Step 10.3: Execute Thread Resolution

For each unresolved thread, resolve via GraphQL:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "<thread_id>"}) {
    thread { isResolved }
  }
}'
```

Resolve threads for ALL dispositions — fixed, rejected, answered, acknowledged, deferred.

---

## Phase 11: CI Gate (HARD)

This is the critical differentiator from `/pr-fix`. CI is a **hard gate** — the PR cannot merge unless all checks pass.

### Step 11.1: Wait for CI Completion

Try `gh pr checks --watch` first. If it works, it blocks until all checks finish:

```bash
gh pr checks ${PR_NUMBER} --watch 2>/dev/null
```

If `--watch` fails, errors, or hangs, use an explicit check-sleep-recheck loop (same pattern as Phase 2.3):

**Step A — Check:**
```bash
echo "CI poll attempt ${ATTEMPT}/30:"
gh pr checks ${PR_NUMBER}
```

**Step B — Evaluate output:**
Parse the plain text output. Each line shows: `<check name>\t<status>\t<duration>\t<url>`.
- If ALL lines show `pass` (or `skipping`): CI is green. Proceed to Step 11.2.
- If ANY line shows `fail`: CI failed. Proceed to Step 11.3 (retry).
- If ANY line shows `pending` or blank status: checks still running. Go to Step C.

**Step C — Wait and loop back:**
```bash
sleep 30
```
Then increment ATTEMPT and go back to Step A. **Step A must run a fresh `gh pr checks` call every iteration** — the sleep does not replace the check. Up to 30 attempts (15 minutes).

**Do NOT use `gh pr checks --json`** — this flag is not supported in all `gh` CLI versions and will produce empty output that causes JSON parse errors. Always use the plain text output format.

### Step 11.2: Evaluate Results

Parse the plain text output of `gh pr checks ${PR_NUMBER}`:

```bash
gh pr checks ${PR_NUMBER}
```

Read each line. If all checks show `pass` (or `skipping`): proceed to Phase 12. If any check shows `fail`: go to Step 11.3 (retry). If any checks are still `pending`: wait and re-check.

### Step 11.3: Retry (One Attempt)

On first failure:
1. Log which checks failed (extract check names from the `fail` lines).
2. Re-trigger CI by pushing an empty commit:
   ```bash
   git commit --allow-empty -m "ci: retry checks for PR #${PR_NUMBER}"
   git push origin ${HEAD_BRANCH}
   ```
3. Wait for CI again using the same polling approach (Step 11.1).
4. If all checks now pass: proceed.
5. If still failing: **skip PR** with reason `"CI failed after retry: <failing check names>"`.

The retry exists because CI can fail transiently (flaky tests, infrastructure issues). One retry catches most transient failures without wasting time on genuine breakage.

---

## Phase 12: Final Verification

Before merging, verify all gates still hold. Any of these failing is a skip.

### Step 12.1: Verify Comment Coverage

Recheck that all comments have replies:
```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments --paginate -q '.[].id' | wc -l
```

If 100% reply rate is not met: **skip PR** with reason `"Comment reply rate below 100%"`.

### Step 12.2: Verify Thread Resolution

```bash
gh api graphql -f query='
query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: '${PR_NUMBER}') {
      reviewThreads(first: 100) {
        nodes { isResolved }
      }
    }
  }
}' -q '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved == false)) | length'
```

If any threads remain unresolved: **skip PR** with reason `"<N> threads still unresolved"`.

### Step 12.3: Verify CI Green

```bash
gh pr checks ${PR_NUMBER} --json conclusion -q '[.[] | select(.conclusion != "success" and .conclusion != "skipped" and .conclusion != "neutral")] | length'
```

If any checks are not success/skipped/neutral: **skip PR** with reason `"CI check(s) not green"`.

### Step 12.4: Verify Branch Up-to-Date

```bash
gh pr view ${PR_NUMBER} --json mergeStateStatus -q '.mergeStateStatus'
```

If status is `BEHIND` or `DIRTY`: **skip PR** with reason `"Branch not up-to-date with base"`.

---

## Phase 13: Merge

**Skip if `--no-merge` is set.** Report as `READINESS-ONLY` instead.

### Step 13.1: Execute Merge

Determine merge method from `--merge-method` flag (default: `squash`):

```bash
gh pr merge ${PR_NUMBER} --squash --delete-branch
```

Or with alternate methods:
```bash
gh pr merge ${PR_NUMBER} --merge --delete-branch    # merge commit
gh pr merge ${PR_NUMBER} --rebase --delete-branch    # rebase
```

### Step 13.2: Verify Merge

```bash
gh pr view ${PR_NUMBER} --json state -q '.state'
```

Expected: `MERGED`.

If merge fails (branch protection, required approvals, etc.): **skip PR** with reason `"Merge blocked: <error message>"`.

---

## Phase 14: Summary

### Per-PR Report

Generate for each PR:

```
PR #${PR_NUMBER} Sweep Result: <MERGED|SKIPPED|READINESS-ONLY>
================================================================
Copilot review:    <requested+completed|already-present|timed-out>
Comments processed: <total>
  - P0 (Blocking):   <count> fixed, <count> rejected
  - P1 (Bug/Issue):  <count> fixed, <count> rejected
  - P2 (Suggestion): <count> fixed, <count> rejected
  - P3 (Question):   <count> answered
  - Info (Approval):  <count> acknowledged

Disposition breakdown:
  Fixed:               <count>
  Fixed w/modification:<count>
  Rejected (explained):<count>
  Answered:            <count>
  Acknowledged:        <count>
  Skipped (auto):      <count>
  Deferred:            <count>

Comments replied:  <count>/<total> (must be 100%)
Threads resolved:  <count>/<total>
Rebase:            <performed|skipped|conflict-skipped>
CI:                <all-green|failed-after-retry>
Merge:             <squash-merged|rebase-merged|merge-committed|skipped|not-requested>
Skip reason:       <reason or "N/A">

PR URL: <url>
```

### Batch Sweep Summary

When processing multiple PRs:

```
PR Sweep Summary
================
PRs discovered:  <total>
PRs merged:      <count>
PRs skipped:     <count>
PRs readiness:   <count> (--no-merge)
Drafts skipped:  <count>

Per-PR Results:
  PR #<N>: <MERGED> — <count> fixes, <count> comments — CI: pass
  PR #<M>: <SKIPPED> — reason: <gate failure reason>
  ...

Skip Reasons:
  Copilot review timed out: <count>
  CI failed after retry:    <count>
  Merge conflict:           <count>
  Merge blocked:            <count>
  Other:                    <count>
```

If `--dry-run` was active, label the report "DRY RUN — no changes were made" and omit merge/push statistics.

---

Begin processing now based on: $ARGUMENTS

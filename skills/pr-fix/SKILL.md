---
name: pr-fix
description: "Complete PR remediation workflow — fetch all review comments, triage by confidence, rebase, fix findings, commit, reply to reviewers, push, and resolve threads. Supports processing 1..N PRs autonomously in batch. Use this skill when the user wants to address PR feedback, fix review comments, remediate PR findings, resolve PR threads, or act on reviewer suggestions. Triggers on: 'fix PR comments', 'address PR feedback', 'fix review findings', 'pr-fix', 'remediate PR', 'resolve PR comments', 'fix the PR', 'address reviewer comments', 'fix what reviewers said', 'handle PR feedback', 'fix all my PRs', 'fix PRs 1 2 3', 'fix PRs 10..15'. Anti-triggers (do NOT match): 'create a PR' (use /pr), 'review this PR' (use /review-comments), 'commit and push' without PR context (use /cp), 'just push' (use /cp), 'rebase only' (use /fr), 'read PR comments' without fix intent (use /review-comments)."
argument-hint: "[pr-number...] [--interactive] [--confidence=N] [--skip-rebase] [--skip-ci] [--no-wait-ci] [--dry-run] [--force]"
---

# PR Fix Skill — Complete PR Remediation Workflow

You are a PR remediation agent. Your job is to fetch all review feedback on one or more pull requests, triage by confidence, rebase onto the base branch, apply fixes, commit, reply to **every** reviewer comment, push, and resolve **all** threads — all using the `gh` and `git` CLIs.

**Core guarantees:**
1. **Every comment gets a reply** — no comment is left unanswered. Fixed, explained, or acknowledged. This includes human reviewers AND automated reviewers (GitHub Copilot, bots with actionable feedback).
2. **Every thread gets resolved** — threads for fixed code AND for explained rejections are resolved after push.
3. **CI is advisory, not blocking** — CI status is waited on by default and reported, but does not gate the workflow.
4. **Copilot comments are first-class** — GitHub Copilot review comments receive the same triage, confidence scoring, remediation, and reply treatment as human reviewer comments. They are NOT skipped as bot noise.

## Arguments

**$ARGUMENTS**: Optional PR number(s) and flags.

Parse `$ARGUMENTS` for the following **before** any other processing:

- If `$ARGUMENTS` contains `--help`, `-h`, or `help`: display the man-page style help below and stop.
- **PR numbers**: One or more positional numeric arguments, space-separated. Supports range syntax `N..M` (e.g., `10..15` expands to PRs 10, 11, 12, 13, 14, 15). **If omitted, discover ALL open PRs** in the current repository via `gh pr list --state open --json number -q '.[].number'` and process them all.
- `--interactive` — Interactive mode. Prompt for sub-threshold fixes instead of skipping them. By default, the skill runs in **auto mode** (non-interactive).
- `--confidence=N` — Confidence threshold 0-100 (default: 95). Fixes scoring at or above this threshold are auto-accepted.
- `--skip-rebase` — Skip the rebase phase entirely.
- `--skip-ci` — Skip CI status checking entirely. No CI commands are run.
- `--no-wait-ci` — Do not wait for CI after push. By default, the skill waits for CI to complete and reports results (advisory, not blocking).
- `--dry-run` — Show the remediation plan without executing any changes.
- `--force` — Push with `--force-with-lease` instead of normal push.

### Natural Language Flag Inference

When `$ARGUMENTS` are expressed as natural language rather than explicit flags, map intent to the closest flag:

| Natural Language | Maps To |
|-----------------|---------|
| "don't wait for CI", "skip CI waiting", "no CI wait" | `--no-wait-ci` |
| "skip CI", "no CI", "ignore CI entirely" | `--skip-ci` |
| "interactive mode", "ask me first", "prompt me" | `--interactive` |
| "don't rebase", "skip rebase", "already rebased" | `--skip-rebase` |
| "force push", "force-push" | `--force` |
| "just show me", "preview", "what would change" | `--dry-run` |

When ambiguous between `--skip-ci` and `--no-wait-ci`, prefer `--no-wait-ci` — the user typically wants to proceed without blocking, not to suppress CI status entirely.

## Help Output

When help is requested, display this and stop:

```
PR-FIX(1)                    GPM Skills Manual                    PR-FIX(1)

NAME
    pr-fix — complete PR remediation: fetch, triage, fix, rebase, push

SYNOPSIS
    /pr-fix [pr-number...] [--interactive] [--confidence=N] [--skip-rebase]
            [--skip-ci] [--no-wait-ci] [--dry-run] [--force]

DESCRIPTION
    Fetches all review comments from one or more pull requests, triages
    them by confidence score, applies fixes, rebases onto the base branch,
    commits with conventional commit format, replies to ALL reviewers
    (including GitHub Copilot), resolves ALL comment threads, and pushes.

    When no PR numbers are given, discovers and processes ALL open PRs
    in the current repository. When multiple PR numbers are given,
    processes each PR end-to-end autonomously before moving to the next.

    CI workflow status is waited on by default after push and reported
    in the summary. CI is advisory — it never blocks the workflow.
    Use --no-wait-ci to skip waiting, or --skip-ci to skip CI entirely.

    GitHub Copilot review comments are treated identically to human
    reviewer comments — same triage, confidence scoring, remediation,
    reply, and thread resolution treatment.

    Every comment receives a reply (fixed, rejected with explanation,
    or answered). Every thread is resolved after push — including
    threads where the fix was rejected with an explanation.

OPTIONS
    pr-number...
        One or more PR numbers to operate on, space-separated. Supports
        range syntax N..M (e.g., 10..15). If omitted, ALL open PRs in
        the repo are discovered and processed.

    --interactive
        Interactive mode. Prompt for sub-threshold fixes instead of
        skipping them. Default is auto (non-interactive).

    --confidence=N
        Confidence threshold (0-100, default: 95). Fixes scoring at or
        above this value are auto-accepted. In auto mode (default),
        sub-threshold fixes are skipped with a logged reply.

    --skip-rebase
        Skip the rebase phase. Useful when the branch is already up to
        date or rebase is handled separately.

    --skip-ci
        Skip CI status reporting entirely.

    --no-wait-ci
        Do not wait for CI after push. By default, the skill waits for
        CI to complete and reports results (advisory, not blocking).

    --dry-run
        Show the remediation plan (categorized comments, proposed fixes,
        confidence scores) without executing any changes.

    --force
        Push with --force-with-lease instead of a normal push. Required
        after rebase rewrites history.

EXAMPLES
    /pr-fix
        Fix comments on ALL open PRs in the repo.

    /pr-fix 42
        Fix comments on PR #42.

    /pr-fix 10 22 35
        Fix comments on PRs #10, #22, and #35 sequentially.

    /pr-fix 10..15
        Fix comments on PRs #10 through #15.

    /pr-fix --confidence=90
        Fix all open PRs, auto-accepting fixes scoring >= 90%.

    /pr-fix --skip-rebase --dry-run
        Preview the remediation plan without rebase or changes.

    /pr-fix 42 55 --skip-ci
        Fix PRs #42 and #55, skip CI status checks.

SEE ALSO
    /pr                 Create or manage pull requests
    /review-comments    Review and respond to PR comments
    /cp                 Commit and push changes
    /fr                 Fetch and rebase
```

---

## Phase 0: Multi-PR Orchestration

This phase activates when multiple PR numbers are provided, or when NO PR numbers are provided (which means "all open PRs").

**Circuit breaker**: Max 100 comments per session. If the PR has more than 100 comments, process the first 100, report the remaining count, and stop. Use `--limit=N` to override.

### Step 0.1: Expand PR List

1. Parse `$ARGUMENTS` for all positional numeric values and range expressions.
   - Range syntax: `10..15` expands to `[10, 11, 12, 13, 14, 15]`.
   - Mixed: `10 22..25 30` expands to `[10, 22, 23, 24, 25, 30]`.
   - **No PR numbers provided**: Discover ALL open PRs in the current repository:
     ```bash
     gh pr list --state open --json number,headRefName,reviewDecision,title -q '.[] | "\(.number)\t\(.headRefName)\t\(.reviewDecision)\t\(.title)"'
     ```
     Include all open PRs regardless of review status. Display the discovered list to the user before processing.
2. Validate each PR exists and is open:
   ```bash
   gh pr view ${PR_NUMBER} --json number,state -q '.number' 2>/dev/null
   ```
   Skip PRs that are already closed/merged with a warning.
3. Store the original branch name to return to after batch processing:
   ```bash
   git branch --show-current
   ```

### Step 0.2: Sequential Processing

Process each PR through Phases 1–10 **sequentially**. After completing all phases for one PR:
1. Stash or commit any remaining state.
2. Checkout the next PR's branch via `gh pr checkout ${NEXT_PR}`.
3. Begin Phase 1 for the next PR.

If a PR fails during processing (e.g., unresolvable rebase conflict), log the failure and continue to the next PR. Do not abort the entire batch.

### Step 0.3: Batch Summary

After all PRs are processed, generate a batch summary:

```
Batch Remediation Summary
=========================
PRs processed:  <total>
PRs succeeded:  <count>
PRs failed:     <count> (list PR numbers and failure reasons)
PRs skipped:    <count> (not found, closed, or merged)

Per-PR Results:
  PR #<N>: <count> fixes, <count> rejected, <count> answered, <count> ack'd — <count>/<total> threads resolved — CI: <pass/fail/skipped> — <status>
  PR #<M>: <count> fixes, <count> rejected, <count> answered, <count> ack'd — <count>/<total> threads resolved — CI: <pass/fail/skipped> — <status>
  ...
```

If exactly one PR number is explicitly provided (e.g., `/pr-fix 42`), skip Phase 0 and proceed directly to Phase 1 with that PR. In all other cases — no args (all open PRs), multiple PR numbers, or range syntax — Phase 0 orchestrates the batch.

---

## Phase 1: Initialization

### Step 1.1: Verify Prerequisites

1. Verify `gh` CLI is installed and authenticated:
   ```bash
   gh auth status
   ```
   If not authenticated, stop and instruct the user to run `gh auth login`.

2. Verify the working directory is a git repository:
   ```bash
   git rev-parse --is-inside-work-tree
   ```

### Step 1.2: Determine PR Number

1. If a PR number was provided in `$ARGUMENTS` (or passed from Phase 0), use it.
2. If no PR numbers were provided at all, Phase 0 handles discovery of all open PRs. This step only runs when Phase 0 passes a specific PR number.
3. If no PR is found, stop and inform the user.

### Step 1.3: Fetch PR Metadata

Retrieve full PR metadata:

```bash
gh pr view ${PR_NUMBER} --json title,body,baseRefName,headRefName,state,reviewDecision,author,url,number
```

Store the base branch name (`baseRefName`) and head branch name (`headRefName`) for later use.

### Step 1.4: Sync Local Branch

1. Confirm the current local branch matches the PR head branch. If not, checkout the PR branch:
   ```bash
   gh pr checkout ${PR_NUMBER}
   ```
   In auto mode (default) or multi-PR batch, checkout automatically without prompting.
2. Check for uncommitted changes via `git status --porcelain`. If dirty:
   - In batch/auto mode: stash changes automatically with `git stash push -m "pr-fix-auto-stash-PR${PR_NUMBER}"`.
   - In interactive mode: warn the user and ask whether to stash first.

---

## Phase 2: Fetch All Feedback

### Step 2.1: Code Review Comments

Fetch inline code review comments (these are comments attached to specific lines of code):

```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments --paginate
```

Parse each comment for: `id`, `body`, `path`, `line` (or `original_line`), `diff_hunk`, `user.login`, `created_at`, `in_reply_to_id`, `pull_request_review_id`.

### Step 2.2: Issue-Style Comments

Fetch top-level PR conversation comments:

```bash
gh pr view ${PR_NUMBER} --json comments --jq '.comments[]'
```

### Step 2.3: Review Status

Fetch review requests and review statuses:

```bash
gh pr view ${PR_NUMBER} --json reviews,reviewRequests --jq '{reviews: .reviews, reviewRequests: .reviewRequests}'
```

### Step 2.4: Categorize Feedback

Assign each comment a priority category:

| Priority | Category | Criteria |
|----------|----------|----------|
| **P0** | Blocking | Reviewer requested changes, comment uses words like "must", "required", "blocking", "critical" |
| **P1** | Bug/Issue | Reports a bug, incorrect behavior, logic error, security issue |
| **P2** | Suggestion | Style improvements, refactoring ideas, "consider", "maybe", "nit", "suggestion" |
| **P3** | Question | Asks for clarification, "why", "what does this", "can you explain" |
| **Info** | Approval | Approvals, "LGTM", "looks good", positive feedback, acknowledgments |

Skip comments that are:
- Already resolved threads
- Pure CI/linting status bot comments (e.g., codecov reports, lint-action summaries) that contain no actionable suggestion

**Do NOT skip:**
- **GitHub Copilot review comments** — Copilot comments are first-class. They receive the same priority categorization, confidence scoring, remediation, reply, and thread resolution as human reviewer comments. Copilot often flags real bugs, security issues, and code quality problems. Treat comments from `copilot-pull-request-reviewer[bot]`, `copilot[bot]`, or `github-actions[bot]` with actionable suggestions identically to human comments. The primary Copilot PR reviewer bot is `copilot-pull-request-reviewer[bot]` — check for this name first.
- **Approval comments** — they must be acknowledged with a reply (disposition: Acknowledged).

Every comment from a human or Copilot reviewer gets a response.

---

## Phase 3: Confidence-Based Triage

For each actionable comment (P0-P3), compute a confidence score for the proposed remediation:

### Scoring Criteria

| Factor | Weight | Description |
|--------|--------|-------------|
| Technical Accuracy | 35% | Is the reviewer's observation correct? Does the suggested fix align with language/framework best practices? |
| Code Evidence | 30% | Can the issue be verified by reading the referenced code? Is the diff context sufficient? |
| Clear Remediation | 20% | Is there an unambiguous fix? Single correct approach vs. multiple valid options? |
| Scope Impact | 15% | Is the fix localized (single file/function) or does it cascade across the codebase? |

### Threshold Logic

The default confidence threshold is **95%** (override with `--confidence=N`).

- **>= threshold**: Auto-accept. Apply the fix without prompting.
- **70% to threshold-1%**: Prompt the user with a summary of the comment, the proposed fix, and the confidence breakdown. Ask for approval.
- **50-69%**: Detailed prompt. Show the comment, the proposed fix, alternatives considered, and the confidence breakdown. Highlight uncertainty. Ask for explicit approval.
- **< 50%**: Skeptical prompt. Present the comment with a note that the fix has low confidence. Show what would be changed and why confidence is low. Recommend the user review manually. Ask whether to attempt the fix, skip it, or mark for manual review.

By default (auto mode), only fixes at or above the threshold are applied. All others are skipped with a logged reply.

When `--interactive` is set, prompt the user for each sub-threshold comment instead of skipping.

### Step 3.1: Display Triage Summary

After computing all confidence scores, **always display a triage summary** before proceeding to any remediation. This summary shows:

- Every comment with its priority category (P0-P3, Info)
- The confidence score and factor breakdown for each comment
- The proposed fix or response for each comment
- The disposition: auto-accepted, needs approval, or will be skipped

This gives the user (and the agent) a complete picture before any code changes begin. When the user explicitly asks to "see the breakdown first" or "show me the scores before fixing," this display is the natural response.

**If `--dry-run` is active**: Display the triage summary, label it "DRY RUN — no changes were made", and **stop here**. Do not proceed to Phase 4 or any subsequent phase.

---

## Phase 4: Remediation

For each accepted fix, apply the changes.

### Step 4.1: Read Before Edit

Always read the target file before making changes. Use targeted reads with offset/limit when the file is large. Confirm the code context matches the reviewer's comment (line numbers may have shifted since the review).

### Step 4.2: Apply Minimal Fixes

- Make the smallest change that addresses the reviewer's feedback.
- Do not refactor surrounding code unless the comment explicitly requests it.
- Do not introduce new patterns or dependencies unless required by the fix.
- Preserve existing code style and conventions.

### Step 4.3: Specialist Agent Routing

For complex fixes that require deep analysis (e.g., architectural changes, cross-file refactors, test additions), delegate to a specialist agent using the Task tool:

- **Code changes**: Route to an implementation-focused agent with the specific file paths, the reviewer comment, and clear instructions.
- **Test additions**: Route to a test-writing agent with the source file and the test requirement.
- **Documentation updates**: Handle inline if simple; route to a specialist if complex.

Each specialist agent receives:
- The exact reviewer comment text
- The relevant file path(s) and line number(s)
- The diff hunk for context
- Clear instructions on what to fix and what NOT to change

### Step 4.4: Verify Each Fix

After applying each fix:
1. Confirm the file is syntactically valid (language-appropriate check if available).
2. Run any fast feedback tools (linter, type checker) if configured.
3. If the fix breaks something, revert and flag for manual review.

---

## Phase 5: Rebase

**Skip this phase entirely if `--skip-rebase` is set.**

Rebase AFTER remediation but BEFORE committing ensures that the branch is up to date with the base branch and that the fix commits land cleanly on top of the latest upstream code.

### Step 5.1: Fetch Latest Base

```bash
git fetch origin ${BASE_BRANCH}
```

### Step 5.2: Rebase

```bash
git rebase origin/${BASE_BRANCH}
```

### Step 5.3: Handle Conflicts

If rebase encounters conflicts:
1. **HALT the pipeline** — do NOT proceed to Phase 6 (commit).
2. Show conflicting files (`git diff --name-only --diff-filter=U`) and their conflict markers.
3. Offer resolution options:
   - **Resolve manually** — User edits files, then `git add` resolved files and `git rebase --continue`.
   - **Abort** — `git rebase --abort` and stop.
   - **Skip commit** — `git rebase --skip` (warn about skipped changes).
4. State: "The remediation pipeline is halted. No commits will be created until the rebase completes cleanly."
5. Repeat for each conflicting commit until the rebase completes or is aborted.

### Step 5.4: Verify Rebase

```bash
git log --oneline -5
```

Confirm the commit history looks correct after rebase.

---

## Phase 6: Commit Changes

### Step 6.1: Stage Changes

Stage only the files that were modified during remediation:

```bash
git add <file1> <file2> ...
```

Never use `git add -A` or `git add .`. Stage files explicitly by path.

### Step 6.2: Commit

Commit using conventional commit format:

```bash
git commit -m "$(cat <<'EOF'
fix: address PR review feedback

- <summary of fix 1>
- <summary of fix 2>
- ...

Resolves review comments on PR #${PR_NUMBER}
EOF
)"
```

Rules:
- Use `fix:` type for bug fixes and corrections.
- Use `refactor:` if the changes are purely structural.
- Use `style:` for formatting-only changes.
- Use `docs:` for documentation-only changes.
- Choose the most appropriate type based on the majority of changes.
- **Never add AI attribution lines** (no `Co-Authored-By`, no `Generated with`, no AI tool signatures).
- If changes span multiple distinct categories, split into separate commits.

### Step 6.3: Verify Commit

```bash
git log --oneline -5
```

Confirm the commit(s) succeeded.

---

## Phase 7: Reply to ALL Comments

**CRITICAL: Every single comment MUST receive a reply.** No comment is left unanswered. This is not optional — it is the core contract of this skill. After this phase, every review comment and top-level comment has a reply posted.

### Comment Disposition Matrix

Every comment falls into exactly one disposition. Each disposition has a required reply template:

| Disposition | When | Reply Template |
|-------------|------|---------------|
| **Fixed** | Comment was addressed exactly as requested | `Fixed in <commit-sha-short>.` |
| **Fixed with Modification** | Comment was addressed with a variation | `Addressed in <commit-sha-short>. <brief explanation of the modification and why>.` |
| **Rejected** | Comment was reviewed but intentionally not applied | `Reviewed — not applying this change because <reason>. <optional: link to relevant docs or prior discussion>.` |
| **Question Response** | Answering a reviewer's question | `<direct answer to the question>. <optional: reference to relevant code or docs>.` |
| **Acknowledged** | Approval, LGTM, positive feedback — no action needed | `Thanks for the review!` (or contextually appropriate acknowledgment) |
| **Skipped (Auto)** | Below confidence threshold in auto mode (default) | `Below confidence threshold (scored <N>%) — flagging for manual review.` |
| **Deferred** | Valid feedback but out of scope for this PR | `Valid point — tracking as a follow-up in <issue-link or "a separate change">.` |

### Step 7.1: Reply Completeness Check

Before posting any replies, verify that **every** comment from Phase 2 has an assigned disposition. If any comment lacks a disposition, assign one now:
- If the comment was processed in Phase 4, it's Fixed/Rejected/Fixed with Modification.
- If it's a question, it's a Question Response.
- If it's approval/LGTM, it's Acknowledged.
- If it was skipped due to confidence threshold, it's Skipped (Auto).
- Everything else is Deferred.

### Step 7.2: Post Replies

For inline code review comments, reply via the API:

```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments \
  -f body="<reply text>" \
  -F in_reply_to=<original_comment_id>
```

For top-level issue comments, reply via:

```bash
gh pr comment ${PR_NUMBER} --body "<reply text>"
```

### Step 7.3: Verify All Comments Replied

After posting, verify no comments were missed:

```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments --paginate -q '.[].id' | wc -l
```

Compare against the total count from Phase 2. If any were missed, post replies for the remaining comments before proceeding.

---

## Phase 8: Resolve ALL Threads

Resolve threads in two stages: first prepare (fetch thread IDs), then execute (after push in Phase 9). The actual GraphQL resolution mutations execute after pushing because reviewers need to see the fix/explanation in the PR before the thread is marked resolved.

**CRITICAL: Resolve threads for ALL addressed comments** — this includes:
- Comments that were **fixed** (code was changed)
- Comments that were **rejected with explanation** (reply explains why not)
- Comments that were **answered** (questions received responses)
- Comments that were **acknowledged** (approvals/LGTM)
- Comments that were **deferred** (reply explains follow-up plan)

The only threads that remain unresolved are those where the reply explicitly asks for further discussion or where the commenter needs to verify the response.

### Step 8.1: Get Thread IDs

Retrieve ALL thread IDs using GraphQL:

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
            nodes {
              id
              databaseId
              body
            }
          }
        }
      }
    }
  }
}'
```

Match threads to the comments processed in Phases 4 and 7 using the comment `databaseId`. Store ALL unresolved thread IDs for resolution after push — not just the fixed ones.

---

## Phase 9: Push Updates

### Step 9.1: Push

If `--force` is set OR if a rebase was performed in Phase 5:

```bash
git push --force-with-lease origin ${HEAD_BRANCH}
```

Otherwise:

```bash
git push origin ${HEAD_BRANCH}
```

If the branch has no upstream tracking:

```bash
git push -u origin ${HEAD_BRANCH}
```

### Step 9.2: Verify Push

```bash
gh pr view ${PR_NUMBER} --json commits --jq '.commits | length'
```

Confirm the push succeeded and the PR reflects the new commits.

### Step 9.3: Execute Thread Resolution

Now that changes are pushed and replies are visible in the PR, resolve ALL threads identified in Phase 8.

For each matched, unresolved thread, resolve it via GraphQL mutation:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "<thread_id>"}) {
    thread {
      isResolved
    }
  }
}'
```

**Resolve threads for ALL dispositions** — fixed, rejected-with-explanation, answered, acknowledged, and deferred. The reply in Phase 7 provides the context; the resolution marks the conversation as complete. The reviewer can always unresolve if they disagree.

### Step 9.4: CI Status Check (Advisory, Default: Wait)

**Skip this step entirely if `--skip-ci` is set.**

By default, wait for CI to complete after push. This is the default behavior — use `--no-wait-ci` to skip waiting.

**If `--no-wait-ci` is set**, just check current status without waiting:

```bash
gh pr checks ${PR_NUMBER}
```

**Otherwise (default)**, wait for CI completion. Try `gh pr checks --watch` first:

```bash
gh pr checks ${PR_NUMBER} --watch 2>/dev/null || true
```

If `--watch` fails or is unsupported, use an explicit check-sleep-recheck loop:

**Step A — Check:**
```bash
echo "CI poll attempt ${ATTEMPT}/20:"
gh pr checks ${PR_NUMBER}
```

**Step B — Evaluate:** If all lines show `pass`/`skipping`: done. If any show `pending`: go to Step C. If any show `fail`: done (CI failed, report it).

**Step C — Wait and recheck:**
```bash
sleep 30
```
Then increment ATTEMPT and go back to Step A. **Step A must run a fresh `gh pr checks` call every iteration.** Up to 20 attempts (10 minutes).

**IMPORTANT — known pitfalls:**
- **Do NOT use `gh pr checks --json`** — not supported in all `gh` CLI versions; produces empty output causing JSON parse errors. Always use plain text output.
- Parse plain text: each line shows `<check name>\t<status>\t<duration>\t<url>`.

Report CI status in the summary. **CI status is advisory — it does NOT block the workflow, prevent thread resolution, or cause the skill to fail.** The workflow completes successfully even if CI fails. CI failures are reported for awareness, not as blockers.

---

## Phase 10: Summary

Generate a completion report for each PR:

```
PR #${PR_NUMBER} Remediation Summary
=====================================
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
Threads resolved:  <count>/<total unresolved>
Commits created:   <count>
Rebase:            <performed/skipped>
Push:              <normal/force-with-lease>
CI status:         <pass/fail/pending/skipped>

PR URL: <url>
```

**Reply completeness**: If `Comments replied` is not 100%, this is a **failure** — go back to Phase 7 and reply to the missing comments before reporting.

If `--dry-run` was active, label the report as "DRY RUN — no changes were made" and omit commit/push statistics.

If processing multiple PRs (Phase 0), append the batch summary after all individual PR summaries.

---

Begin processing now based on: $ARGUMENTS

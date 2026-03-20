---
name: pr-fix
description: "Complete PR remediation workflow — fetch all review comments, triage by confidence, fix findings, rebase, commit, reply to reviewers, push, and resolve threads. Use this skill when the user wants to address PR feedback, fix review comments, remediate PR findings, resolve PR threads, or act on reviewer suggestions. Triggers on: 'fix PR comments', 'address PR feedback', 'fix review findings', 'pr-fix', 'remediate PR', 'resolve PR comments', 'fix the PR', 'address reviewer comments', 'fix what reviewers said', 'handle PR feedback'. Anti-triggers (do NOT match): 'create a PR' (use /pr), 'review this PR' (use /review-comments), 'commit and push' without PR context (use /cp), 'just push' (use /cp), 'rebase only' (use /fr), 'read PR comments' without fix intent (use /review-comments)."
argument-hint: "[pr-number] [--auto] [--confidence=N] [--skip-rebase] [--dry-run] [--force]"
---

# PR Fix Skill — Complete PR Remediation Workflow

You are a PR remediation agent. Your job is to fetch all review feedback on a pull request, triage it by confidence, apply fixes, rebase, commit, reply to reviewers, push, and resolve threads — all using the `gh` and `git` CLIs.

## Arguments

**$ARGUMENTS**: Optional PR number and flags.

Parse `$ARGUMENTS` for the following **before** any other processing:

- If `$ARGUMENTS` contains `--help`, `-h`, or `help`: display the man-page style help below and stop.
- **PR number**: First positional numeric argument. If omitted, infer from the current branch via `gh pr view --json number -q .number`.
- `--auto` — Non-interactive mode. Accept all fixes at or above the confidence threshold without prompting.
- `--confidence=N` — Confidence threshold 0-100 (default: 95). Fixes scoring at or above this threshold are auto-accepted.
- `--skip-rebase` — Skip the rebase phase entirely.
- `--dry-run` — Show the remediation plan without executing any changes.
- `--force` — Push with `--force-with-lease` instead of normal push.

## Help Output

When help is requested, display this and stop:

```
PR-FIX(1)                    GPM Skills Manual                    PR-FIX(1)

NAME
    pr-fix — complete PR remediation: fetch, triage, fix, rebase, push

SYNOPSIS
    /pr-fix [pr-number] [--auto] [--confidence=N] [--skip-rebase]
            [--dry-run] [--force]

DESCRIPTION
    Fetches all review comments from a pull request, triages them by
    confidence score, applies fixes, rebases onto the base branch,
    commits with conventional commit format, replies to reviewers,
    resolves comment threads, and pushes updates.

    Operates on the PR associated with the current branch by default.

OPTIONS
    pr-number
        PR number to operate on. If omitted, inferred from the current
        branch via gh pr view.

    --auto
        Non-interactive mode. Accept all fixes at or above the confidence
        threshold without prompting the user.

    --confidence=N
        Confidence threshold (0-100, default: 95). Fixes scoring at or
        above this value are auto-accepted. Below threshold, the user
        is prompted for approval.

    --skip-rebase
        Skip the rebase phase. Useful when the branch is already up to
        date or rebase is handled separately.

    --dry-run
        Show the remediation plan (categorized comments, proposed fixes,
        confidence scores) without executing any changes.

    --force
        Push with --force-with-lease instead of a normal push. Required
        after rebase rewrites history.

EXAMPLES
    /pr-fix
        Fix comments on the PR for the current branch.

    /pr-fix 42
        Fix comments on PR #42.

    /pr-fix --auto --confidence=90
        Auto-fix all comments scoring >= 90% confidence.

    /pr-fix --skip-rebase --dry-run
        Preview the remediation plan without rebase or changes.

SEE ALSO
    /pr                 Create or manage pull requests
    /review-comments    Review and respond to PR comments
    /cp                 Commit and push changes
    /fr                 Fetch and rebase
```

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

1. If a PR number was provided in `$ARGUMENTS`, use it.
2. Otherwise, infer from the current branch:
   ```bash
   gh pr view --json number -q .number
   ```
3. If no PR is found, stop and inform the user.

### Step 1.3: Fetch PR Metadata

Retrieve full PR metadata:

```bash
gh pr view ${PR_NUMBER} --json title,body,baseRefName,headRefName,state,reviewDecision,author,url,number
```

Store the base branch name (`baseRefName`) and head branch name (`headRefName`) for later use.

### Step 1.4: Sync Local Branch

1. Confirm the current local branch matches the PR head branch. If not, ask the user whether to checkout the PR branch:
   ```bash
   gh pr checkout ${PR_NUMBER}
   ```
2. Check for uncommitted changes via `git status --porcelain`. If dirty, warn the user and ask whether to stash first.

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
- Bot-generated comments (CI status, linting reports)
- Pure approval comments with no actionable content

If `--dry-run` is active, display the categorized list and stop here.

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

When `--auto` is set, only fixes at or above the threshold are applied. All others are skipped with a log entry.

When not in `--auto` mode, use the user's interactive decision for each sub-threshold comment.

---

## Phase 4: Remediation

For each accepted fix, apply the changes:

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
1. List conflicted files via `git diff --name-only --diff-filter=U`.
2. For each conflict, attempt automatic resolution if the conflict is in a file that was modified by this remediation session (prefer our changes).
3. If automatic resolution is not possible, present the conflict to the user and ask for guidance.
4. After resolution: `git add <resolved-files>` then `git rebase --continue`.

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

## Phase 7: Reply to Comments

For each comment that was addressed, post a reply using the appropriate template.

### Reply Templates

**Fixed** (comment was addressed exactly as requested):
```
Fixed in <commit-sha-short>.
```

**Fixed with Modification** (comment was addressed with a variation):
```
Addressed in <commit-sha-short>. <brief explanation of the modification and why>.
```

**Rejected** (comment was reviewed but intentionally not applied):
```
Reviewed — not applying this change because <reason>. <optional: link to relevant docs or prior discussion>.
```

**Question Response** (answering a reviewer's question):
```
<direct answer to the question>. <optional: reference to relevant code or docs>.
```

### Posting Replies

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

---

## Phase 8: Resolve Threads

Resolve threads in two stages: first prepare (fetch thread IDs), then execute (after push in Phase 9). The actual GraphQL resolution mutations execute after pushing because reviewers need to see the fix in the PR diff before the thread is marked resolved.

### Step 8.1: Get Thread IDs

Retrieve the thread IDs for resolved comments using GraphQL:

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

Match threads to the comments that were fixed in Phase 4 using the comment `databaseId`. Store the thread IDs for resolution after push.

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

Now that changes are pushed and visible in the PR, resolve the threads identified in Phase 8. Thread resolution via GraphQL happens AFTER pushing changes.

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

Only resolve threads for comments that were actually fixed. Do not resolve threads for rejected comments or questions.

---

## Phase 10: Summary

Generate a completion report:

```
PR #${PR_NUMBER} Remediation Summary
=====================================
Comments processed: <total>
  - P0 (Blocking):   <count> fixed, <count> skipped
  - P1 (Bug/Issue):  <count> fixed, <count> skipped
  - P2 (Suggestion): <count> fixed, <count> skipped
  - P3 (Question):   <count> answered, <count> skipped
  - Info (Approval):  <count> acknowledged

Fixes applied:     <count>
Fixes skipped:     <count> (below confidence threshold)
Fixes rejected:    <count> (user declined)
Threads resolved:  <count>
Commits created:   <count>
Rebase:            <performed/skipped>
Push:              <normal/force-with-lease>

PR URL: <url>
```

If `--dry-run` was active, label the report as "DRY RUN — no changes were made" and omit commit/push statistics.

---

Begin processing now based on: $ARGUMENTS

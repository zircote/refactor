---
name: review-comments
description: Review GitHub PR comments, assess validity with confidence scoring, remediate accepted findings by editing code, and respond to all comments with explanations. Orchestrates end-to-end PR comment triage including thread resolution via GraphQL. Use this skill when the user wants to process PR review comments, respond to reviewers, address PR feedback, triage review findings, fix PR comments, or handle code review feedback. Triggers on "review comments", "address PR feedback", "respond to reviewers", "triage PR comments", "handle review comments", "process PR feedback", "fix review comments", "address code review". Anti-triggers: do NOT use for creating PRs (use /pr), fixing CI/check failures (use /pr-fix), writing new code reviews, performing code review as a reviewer, or generating PR descriptions.
argument-hint: "[pr-number] [--auto] [--interactive] [--confidence=N] [--dry-run]"
---

# Review Comments Skill

You are processing GitHub PR review comments end-to-end: fetching, assessing, remediating, responding, and resolving threads.

## Man Page / Help Check

If `$ARGUMENTS` is `--help`, `-h`, or `help`, print the following and stop:

```
review-comments - Review and remediate GitHub PR comments

USAGE
  /review-comments [pr-number] [options]

ARGUMENTS
  pr-number           PR number (optional; inferred from current branch if omitted)

OPTIONS
  --auto              Non-interactive mode; auto-accept comments meeting confidence threshold
  --interactive       Interactive mode (default); prompt for each comment below threshold
  --confidence=N      Minimum confidence (0-100) to auto-accept in --auto mode (default: 85)
  --dry-run           Show proposed actions without executing any changes or replies
  --score-only        Fetch, categorize, and score comments; do not remediate, reply, or resolve

DESCRIPTION
  Fetches all review comments on a PR, scores each for validity, remediates
  accepted findings by editing source files, posts reply comments explaining
  the disposition of each finding, and resolves addressed threads via GraphQL.

  Categories: Code Review, Questions, Suggestions, Blockers, Approvals, Conversations

  Scoring weights:
    Technical Accuracy  40%
    Relevance           25%
    Impact              20%
    Feasibility         15%

  Classification:
    >=90%  Strong Accept
    75-89% Accept
    50-74% Uncertain
    25-49% Likely Reject
    <25%   Strong Reject

EXAMPLES
  /review-comments                     # current branch PR, interactive
  /review-comments 42                  # PR #42, interactive
  /review-comments --auto              # current branch PR, auto mode
  /review-comments 42 --auto --confidence=75
  /review-comments --dry-run           # preview without changes
  /review-comments --score-only        # just show scores, no changes

SEE ALSO
  /pr        Create and manage pull requests
  /pr-fix    Fix CI failures and check issues on PRs
```

## Arguments

**$ARGUMENTS**: Optional PR number and flags.

Parse `$ARGUMENTS` for the following **before** any other processing:

- `[pr-number]` — A bare positive integer is treated as the PR number. If omitted, infer from the current branch using `gh pr view --json number -q .number`.

- `--auto` — Non-interactive mode. When present, extract and remove from `$ARGUMENTS` and set `interactive_mode = false`. Comments meeting the confidence threshold are auto-accepted; those below are auto-rejected.

- `--interactive` — Interactive mode (explicit). This is the default. When present, extract and remove from `$ARGUMENTS` and set `interactive_mode = true`.

- `--confidence=N` — Minimum confidence score (0-100) to auto-accept a comment without prompting. Default: `85`. Extract and remove from `$ARGUMENTS`. Only meaningful in `--auto` mode; in interactive mode, comments below 90% confidence are presented for user decision regardless.

- `--dry-run` — Show all proposed actions (edits, replies, resolutions) without executing them. No files are modified, no comments are posted, no threads are resolved.

- `--score-only` — Assessment-only mode. Fetch, categorize, and score all comments, then stop after presenting the results. Do NOT proceed to remediation (Phase 4), response posting (Phase 5), or thread resolution (Phase 6). This mode is read-only — no files are edited, no comments are posted, no threads are resolved. Use this when the user just wants to see the breakdown and scores without taking action.

**Intent detection**: If the user's natural language prompt indicates they only want to see scores or assessments WITHOUT taking action (e.g., "just score them", "I just want the breakdown", "don't change anything yet", "show me what they said"), treat the request as if `--score-only` was passed, even if the flag was not explicitly provided. Look for these signals:
  - "just score" / "just show" / "just want to see"
  - "don't change anything" / "don't fix anything"
  - "let me decide later" / "I'll decide later" (deferred decision — score-only)
  Note: "let me decide" (without "later") and "help me decide" both imply the user wants interactive prompting NOW, so they should trigger interactive mode, NOT score-only.
  - "read-only" / "assessment only" / "breakdown only"

If both `--auto` and `--interactive` are present, `--interactive` wins.
If `--score-only` is present, it overrides both `--auto` and `--interactive` — only Phases 1-2 execute, plus a score presentation.

## Phase 1: Context Gathering

### Step 1.1: Verify Prerequisites

1. Verify `gh` CLI is installed and authenticated:
   ```bash
   gh auth status
   ```
   If this fails, stop and report: "gh CLI is not authenticated. Run `gh auth login` first."

2. Determine repository owner and name:
   ```bash
   gh repo view --json owner,name -q '.owner.login + "/" + .name'
   ```
   Store as `OWNER` and `REPO`.

### Step 1.2: Determine PR Number

1. If a PR number was provided in arguments, use it directly as `PR_NUMBER`.
2. Otherwise, infer from the current branch:
   ```bash
   gh pr view --json number -q .number
   ```
   If this fails, stop and report: "No PR found for the current branch. Provide a PR number explicitly."
3. Validate the PR exists and is open:
   ```bash
   gh pr view ${PR_NUMBER} --json state -q .state
   ```

### Step 1.3: Fetch Review Comments (REST)

Fetch all review comments on the PR:
```bash
gh api repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments --paginate
```

Parse the JSON response. For each comment, extract and store:
- `id` (REST API ID, used for posting replies)
- `body` (comment text)
- `path` (file path the comment refers to)
- `line` / `original_line` (line number in the diff)
- `diff_hunk` (surrounding diff context)
- `user.login` (who left the comment)
- `created_at`
- `in_reply_to_id` (if this is a reply in a thread)
- `pull_request_review_id`

### Step 1.4: Fetch GraphQL Thread IDs

For thread resolution, you need the GraphQL node IDs. Fetch the review threads:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 100) {
              nodes {
                databaseId
                body
              }
            }
          }
        }
      }
    }
  }
' -f owner="${OWNER}" -f repo="${REPO}" -F pr=${PR_NUMBER}
```

Build a mapping: `comment_databaseId -> thread_graphql_id`. This mapping is critical for Phase 6 thread resolution. Store it as `THREAD_MAP`.

### Step 1.5: Fetch General PR Comments

Fetch issue-level (non-review) comments:
```bash
gh api repos/${OWNER}/${REPO}/issues/${PR_NUMBER}/comments --paginate
```

These are general conversation comments, not attached to specific code lines.

### Step 1.6: Categorize Comments

Group all comments into categories:

| Category | Criteria |
|----------|----------|
| **Code Review** | Attached to a file/line, suggests a code change or identifies a bug |
| **Questions** | Asks a question (contains `?`, starts with "why", "how", "what", "could you", etc.) |
| **Suggestions** | Uses GitHub suggestion blocks or proposes an alternative approach |
| **Blockers** | Explicitly marks as blocking, uses "must", "required", "blocking" |
| **Approvals** | Positive feedback: "LGTM", "looks good", "+1", approval language |
| **Conversations** | General discussion that doesn't fit other categories |

A comment may belong to multiple categories. Primary category is assigned by highest-priority match (Blockers > Code Review > Suggestions > Questions > Approvals > Conversations).

Report a summary to the user:
```
PR #${PR_NUMBER} Comment Summary:
  Code Review:    N comments
  Questions:      N comments
  Suggestions:    N comments
  Blockers:       N comments
  Approvals:      N comments
  Conversations:  N comments
  Total:          N comments (M threads)
  Already resolved: K threads
```

## Phase 2: Validity Assessment

For each comment that is **not** an Approval or already-resolved thread:

### Step 2.1: Understand Context

1. **Read the referenced file** at the path specified in the comment using the Read tool. If the file does not exist (e.g., it was deleted), note this.
2. **Understand the diff context** from the `diff_hunk` field — this shows what changed.
3. **Read surrounding code** if needed for broader context (e.g., the full function or class containing the changed lines).

### Step 2.2: Score the Comment

Score each comment on four dimensions (0-100 each):

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| **Technical Accuracy** | 40% | Is the reviewer's observation factually correct? Does the code actually have the issue described? |
| **Relevance** | 25% | Is the comment relevant to the changes in this PR? Is it about the right code? |
| **Impact** | 20% | How significant is the issue? Would fixing it meaningfully improve the code? |
| **Feasibility** | 15% | Can the suggested change be implemented without breaking other things? Is it practical? |

**Composite score** = (Technical Accuracy * 0.40) + (Relevance * 0.25) + (Impact * 0.20) + (Feasibility * 0.15)

### Step 2.2.1: Per-Dimension Flagging

After scoring, flag comments that have notably low scores on individual dimensions, regardless of composite score. This helps users quickly identify specific quality concerns:

- **Low Technical Accuracy flag** (< 50): The reviewer's observation may be factually incorrect. Flag with "⚠ Low accuracy — reviewer claim may be wrong". This is especially important when users indicate they want to validate reviewer accuracy.
- **Low Relevance flag** (< 40): The comment may not be relevant to this PR's changes.
- **Low Impact flag** (< 30): The issue is likely cosmetic or stylistic rather than substantive.

When presenting comments (in Phase 3 or score-only output), show dimension flags prominently alongside the composite classification. Group or highlight low-accuracy comments separately when the user's prompt suggests accuracy validation is a priority (e.g., "flag anything that looks wrong", "might not be accurate").

### Step 2.3: Classify Disposition

Based on the composite score:

| Score Range | Classification | Default Action |
|-------------|---------------|----------------|
| >= 90 | **Strong Accept** | Remediate automatically |
| 75 - 89 | **Accept** | Remediate (prompt in interactive mode) |
| 50 - 74 | **Uncertain** | Prompt user in interactive mode; reject in auto mode |
| 25 - 49 | **Likely Reject** | Prompt user in interactive mode; reject in auto mode |
| < 25 | **Strong Reject** | Reject automatically |

Store the assessment for each comment:
```
{
  comment_id: ...,
  category: "...",
  scores: { technical: N, relevance: N, impact: N, feasibility: N },
  composite: N,
  classification: "...",
  reasoning: "...",
  disposition: "accept" | "reject" | "pending"
}
```

### Score-Only Gate

If `--score-only` mode is active (either via flag or intent detection):

1. Present the Phase 1 summary (comment counts by category).
2. Present each comment's full assessment: category, all 4 dimension scores, composite score, classification, reasoning, and any dimension flags from Step 2.2.1.
3. Show a summary table of all comments sorted by composite score.
4. **STOP HERE**. Do NOT proceed to Phase 3 or any subsequent phase. No decisions are made, no files are edited, no comments are posted, no threads are resolved.

The user can then follow up with further instructions to act on specific comments.

## Phase 3: Decision Workflow

### Step 3.1: Process Decisions

Iterate through all assessed comments, ordered by classification (Blockers first, then by descending composite score):

**Interactive mode** (default):

Use the `AskUserQuestion` tool (or equivalent user-prompting mechanism) to present each comment that requires a decision. For each comment below Strong Accept and above Strong Reject, explicitly ask the user and wait for their response before proceeding.

- **Strong Accept** (>= 90): Accept automatically. Inform user: "Auto-accepting: [comment summary] (confidence: N%)"
- **Accept** (75-89): Present to user with assessment and all 4 dimension scores. Use AskUserQuestion: "Accept this finding? [Yes/No/Skip]"
- **Uncertain** (50-74): Present to user with detailed reasoning and dimension breakdown. Use AskUserQuestion: "This finding is uncertain. Accept, reject, or skip? [Accept/Reject/Skip]"
- **Likely Reject** (25-49): Present to user with reasoning for rejection and dimension breakdown. Use AskUserQuestion: "This finding is likely invalid. Accept anyway, reject, or skip? [Accept/Reject/Skip]"
- **Strong Reject** (< 25): Reject automatically. Inform user: "Auto-rejecting: [comment summary] (confidence: N%)"

**Auto mode** (`--auto`):
- Score >= `confidence_threshold`: Accept
- Score < `confidence_threshold`: Reject

### Step 3.2: Record Final Dispositions

Update each comment's disposition to one of:
- `accepted` — Will be remediated and replied to as fixed
- `accepted-modified` — Accepted but will be fixed differently than suggested
- `rejected` — Will be replied to with explanation of why not fixed
- `skipped` — No action taken, no reply posted
- `question` — Will be answered
- `acknowledged` — Approval/conversation, will be acknowledged

## Phase 4: Remediation

For each comment with disposition `accepted` or `accepted-modified`:

### Step 4.1: Plan the Fix

1. **Read the file** referenced by the comment using the Read tool.
2. **Understand the full context** — read enough of the file to understand the function/class/module.
3. **Plan the minimal change** that addresses the reviewer's concern.
4. **Minimal change principle**: Change only what is necessary to address the comment. Do not refactor surrounding code, do not "improve" adjacent lines, do not fix unrelated issues.

### Step 4.2: Apply the Fix

1. Use the Edit tool to make the change.
2. For `accepted-modified` dispositions, implement the fix in the way you determined is better, but document why you deviated from the reviewer's exact suggestion.

### Step 4.3: Verify the Fix

1. If tests exist and are runnable, run them to verify the fix doesn't break anything:
   ```bash
   # Detect and run appropriate test command
   ```
2. If a test fails after the fix, revert the change and mark the comment as `rejected` with reason "Fix causes test failure".

### Step 4.4: Maintain Remediation Log

Track all changes made:
```
REMEDIATION_LOG:
  - comment_id: 123
    file: src/foo.ts
    change: "Added null check before accessing property"
    lines_changed: 42-44
    disposition: accepted
  - comment_id: 456
    file: src/bar.ts
    change: "Renamed variable per suggestion"
    lines_changed: 17
    disposition: accepted-modified
    deviation: "Used camelCase instead of suggested snake_case to match project conventions"
```

**Dry-run mode**: Instead of applying changes, print the planned edits in diff format and skip to Phase 5.

## Phase 5: Response Generation

For each comment (excluding `skipped`), generate and post a reply.

### Step 5.1: Response Templates

**Accepted/Fixed:**
```
Fixed in this revision. [Brief description of what was changed.]
```

**Accepted with Modification:**
```
Addressed in this revision with a slight modification: [description].

[Reason for deviation from the exact suggestion.]
```

**Rejected:**
```
After reviewing this, I've decided not to make this change because:

[Concise, specific technical reasoning.]

[If applicable: alternative approach or why current code is correct.]
```

**Question Response:**
```
[Direct answer to the question.]

[If applicable: reference to relevant code, docs, or design decision.]
```

**Acknowledgment (for approvals/conversations):**
```
[Brief, natural acknowledgment. E.g., "Thanks for the review!" or a relevant response to the conversation.]
```

### Step 5.2: Post Replies

For each review comment (code-level), post a reply using the REST API:
```bash
gh api repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments/${COMMENT_ID}/replies \
  -f body='[response text]'
```

For general PR comments (issue-level), post using:
```bash
gh api repos/${OWNER}/${REPO}/issues/${PR_NUMBER}/comments \
  -f body='[response text]'
```

**Dry-run mode**: Print each reply that would be posted without actually posting.

## Phase 6: Resolution and Summary

### Step 6.1: Resolve Addressed Threads (MANDATORY)

**Dry-run mode**: Skip this step entirely — do NOT resolve any threads. Instead, list the threads that would be resolved and proceed to Step 6.3.

For every comment with disposition `accepted`, `accepted-modified`, or `acknowledged` (for approvals), resolve the corresponding review thread using the GraphQL mutation.

Look up the thread ID from `THREAD_MAP` (built in Step 1.4):

```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread {
        isResolved
      }
    }
  }
' -f threadId="${THREAD_ID}"
```

**Important**: The `threadId` variable must be properly escaped. Use `-f` (not `-F`) for string parameters.

Do NOT resolve threads for:
- `rejected` comments (the thread stays open for further discussion)
- `skipped` comments
- Threads that are already resolved

### Step 6.2: Verify Resolution

Run a verification query to confirm all intended threads were resolved:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
          }
        }
      }
    }
  }
' -f owner="${OWNER}" -f repo="${REPO}" -F pr=${PR_NUMBER}
```

Compare against expected resolutions. Report any threads that failed to resolve.

### Step 6.3: Generate Summary Report

Present a final summary:

```
## PR #${PR_NUMBER} Review Comments — Summary

### Disposition
| Category | Accepted | Modified | Rejected | Skipped | Total |
|----------|----------|----------|----------|---------|-------|
| Code Review | N | N | N | N | N |
| Suggestions | N | N | N | N | N |
| Questions | - | - | - | - | N answered |
| Blockers | N | N | N | N | N |
| Approvals | - | - | - | - | N acknowledged |
| Conversations | - | - | - | - | N acknowledged |

### Remediation
- Files modified: N
- Total edits: N
- Tests passed: Yes/No/Not run

### Thread Resolution
- Threads resolved: N / M total
- Threads left open: K (rejected or skipped)
- Resolution failures: F

### Files Changed
- path/to/file1.ts (lines 42-44)
- path/to/file2.ts (line 17)
```

**Dry-run mode**: Prefix the summary with "DRY RUN — no changes were made" and show what would have been done.

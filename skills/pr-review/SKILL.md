---
name: pr-review
description: "Comprehensive Pull Request code reviewer that scales strategy by PR size. Performs PR hygiene checks (title, description, commits, scope, CI), then reviews code for correctness, security, performance, and maintainability. For large PRs (500+ lines), spawns parallel specialist agents (code-reviewer, architect, test-rigor-reviewer) via swarm orchestration. Submits findings as a single batched GitHub review with classified comments (must-fix, should-fix, nit, question, praise). Use this skill when the user wants to review a PR, audit a pull request, check PR quality, do a code review on a PR, evaluate a PR before merging, or give feedback on someone's PR. Triggers on: 'review PR', 'review this PR', 'review pull request', 'pr-review', 'code review PR', 'audit this PR', 'check this PR', 'review PR 42', 'give me a review of PR', 'what do you think of this PR'. Anti-triggers (do NOT match): 'create a PR' (use /pr), 'fix PR comments' (use /pr-fix), 'address review feedback' (use /review-comments), 'merge PR', 'close PR'."
argument-hint: "<pr-number-or-url> [--auto-approve-trivial] [--severity=<low|medium|high>] [--skip-hygiene] [--dry-run]"
---

# PR Review Skill

You are a senior code reviewer performing a comprehensive pull request review. Your review scales in strategy based on PR size — direct review for small/medium PRs, swarm-orchestrated parallel specialist review for large/very large PRs.

## Help Check

If `$ARGUMENTS` is `help`, `--help`, or `-h`, print this and stop:

```
PR-REVIEW(1)                 GPM Skills Manual                 PR-REVIEW(1)

NAME
    pr-review — comprehensive pull request code review

SYNOPSIS
    /pr-review <pr-number-or-url> [options]

DESCRIPTION
    Performs a multi-phase PR review: hygiene checks (title, description,
    commits, scope, CI), code review (correctness, security, performance,
    maintainability), and submits findings as a single batched GitHub
    review with classified comments.

    Scales by PR size:
      small   (<100 lines)     Direct review
      medium  (100-500 lines)  Direct review
      large   (500-1500 lines) Swarm-orchestrated parallel specialists
      very large (1500+ lines) Swarm-orchestrated + decomposition advice

OPTIONS
    pr-number-or-url
        PR number or full GitHub URL. If omitted, inferred from current branch.

    --auto-approve-trivial
        Auto-approve docs-only, typo-fix, and dependency-bump PRs from
        trusted bots (dependabot, renovate) if CI passes.

    --severity=<low|medium|high>
        Minimum severity to report. Default: low (report everything).
        "medium" suppresses nits. "high" shows only must-fix findings.

    --skip-hygiene
        Skip Phase 1 hygiene checks. Useful when re-reviewing after fixes.

    --dry-run
        Print the review that would be submitted without posting to GitHub.

EXAMPLES
    /pr-review 42
    /pr-review https://github.com/org/repo/pull/42
    /pr-review --auto-approve-trivial
    /pr-review 42 --severity=medium --dry-run

SEE ALSO
    /pr              Create pull requests
    /pr-fix          Remediate PR review feedback
    /review-comments Process and respond to PR comments
```

## Arguments

**$ARGUMENTS**: PR number or URL and optional flags.

Parse `$ARGUMENTS` **before** any other processing:

- **PR identifier**: A bare positive integer or a GitHub PR URL (extract the number from it). If omitted, infer from the current branch via `gh pr view --json number -q .number`.
- `--auto-approve-trivial` — Auto-approve PRs that are docs-only, typo-fix, or dependency bumps from trusted bots, provided CI passes. Set `auto_approve_trivial = true`.
- `--severity=<low|medium|high>` — Minimum severity threshold for reported findings. Default `low`. `medium` suppresses nits. `high` shows only must-fix.
- `--skip-hygiene` — Skip Phase 1 hygiene checks entirely. Set `skip_hygiene = true`.
- `--dry-run` — Assemble the full review but print it locally instead of posting to GitHub. Set `dry_run = true`.

---

## Phase 0: Context Gathering

### Step 0.1: Load Project Review Configuration

Before touching GitHub, check for project-specific review preferences:

1. **Atlatl memory**: Search for prior review conventions:
   ```
   recall_memories(query="code review conventions")
   recall_memories(query="PR review preferences")
   ```
   Apply any matching results (severity overrides, ignored patterns, required sections, style preferences).

2. **CLAUDE.md**: Read the project's CLAUDE.md for review-related rules — import conventions, naming standards, testing requirements, forbidden patterns.

3. **Config file**: Check for `.github/pr-review-config.yml`. If it exists, read and apply overrides:
   ```yaml
   # Example config
   ignored_patterns: ["*.generated.ts", "vendor/**"]
   required_sections: ["test plan", "migration notes"]
   auto_approve_bots: ["dependabot[bot]", "renovate[bot]"]
   severity_threshold: "low"
   comment_style: "concise"  # or "detailed"
   ```

### Step 0.2: Fetch PR Metadata

```bash
gh pr view ${PR_NUMBER} --json number,title,body,state,author,labels,baseRefName,headRefName,reviewDecision,isDraft,url,additions,deletions,changedFiles,commits,reviewRequests,reviews,statusCheckRollup
```

Store all fields. Compute:
- `total_changed_lines = additions + deletions`
- `pr_size`:
  - `small` if total_changed_lines < 100
  - `medium` if 100 <= total_changed_lines < 500
  - `large` if 500 <= total_changed_lines < 1500
  - `very_large` if total_changed_lines >= 1500

### Step 0.3: Identify PR Type

Determine PR type from (in priority order):
1. **Labels**: `bug`, `feature`, `refactor`, `docs`, `dependencies`, `hotfix`, `revert`
2. **Title prefix**: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `hotfix:`, `revert:`, `deps:`
3. **Diff content heuristic**: If all changes are in `.md` files → docs. If only `package-lock.json`/`go.sum`/lockfiles → dependency update.

Detect if PR author is a bot: check `author.login` for `[bot]` suffix or known bot names (dependabot, renovate, github-actions).

### Step 0.4: Fetch the Diff

```bash
gh pr diff ${PR_NUMBER}
```

Store the full diff. Also fetch the list of changed files:
```bash
gh pr diff ${PR_NUMBER} --name-only
```

### Step 0.5: Fetch Existing Reviews and Comments

Fetch existing review comments to avoid duplicating feedback already given by other reviewers:
```bash
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments --paginate
gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/reviews --paginate
```

Build a set of already-reviewed issues (file + line + topic) to skip during your review.

### Step 0.6: Fetch Commit History

```bash
gh pr view ${PR_NUMBER} --json commits --jq '.commits[] | "\(.oid[:7]) \(.messageHeadline)"'
```

### Step 0.7: Check for Linked Issues

```bash
gh pr view ${PR_NUMBER} --json body --jq '.body' | grep -oiE '(close[sd]?|fix(es|ed)?|resolve[sd]?) #[0-9]+' || true
```

Also check the PR body for issue references like `#123`, `JIRA-456`, or URLs to issue trackers.

### Step 0.8: Bot PR Fast Path

If the author is a bot AND `--auto-approve-trivial` is set:
1. Verify CI is passing (from `statusCheckRollup`)
2. Scan the diff for breaking changes (major version bumps, removed exports, changed interfaces)
3. If CI passes and no breaking changes detected:
   - Submit an `APPROVE` review with body: "Automated review: CI passing, no breaking changes detected. Auto-approved."
   - **Stop here** — skip all remaining phases.
4. If CI fails or breaking changes found, continue with full review (the bot label doesn't exempt it).

---

## Phase 1: PR Hygiene Checks

**Skip entirely if `--skip-hygiene` is set.**

These are universally expected PR practices. Violations become review comments in the final submission.

### 1.1: Title & Description

**Title checks:**
- Length <= 72 characters. If over, flag: "PR title exceeds 72 characters — consider shortening for readability in git log."
- Follows conventional commit format if the project uses it (detect from recent commit history or CLAUDE.md). If the project uses conventional commits and the title doesn't match, flag it.

**Description checks:**
- Non-empty body exists. If body is empty or just a template with no content filled in, flag: "PR description is empty — reviewers need context on what changed, why, and how to test."
- Contains a "what changed" section (or equivalent). Look for headings like `## Summary`, `## Changes`, `## What`, or a prose paragraph describing changes.
- Contains a "why" or motivation section. Look for headings like `## Why`, `## Motivation`, `## Context`, or linked issues that provide context.
- Contains test instructions or a test plan. Look for `## Test`, `## Testing`, `## How to test`, `## Verification`.
- If the diff touches database schemas, API contracts, or configuration formats: check for migration/rollback notes.
- If the diff modifies UI components: check for screenshots or recordings (links to images, `.png`, `.gif`, `.mp4` references).

**Breaking changes:**
- If the diff removes or renames public exports, changes API signatures, modifies database schemas, or alters configuration formats: check that the PR body explicitly mentions breaking changes. Flag if it doesn't.

**Linked issues:**
- If no issue reference found (Step 0.7), flag as warning: "No linked issue found — consider referencing the issue this PR addresses."

### 1.2: Commit Hygiene

**Commit quality:**
- Flag commits with messages matching: `WIP`, `wip`, `fixup`, `fixup!`, `squash!`, `temp`, `tmp`, `asdf`, `test`, `stuff`, single-word messages. Suggestion: "Consider squashing WIP/fixup commits before merging for a clean history."
- Check if commit messages follow the project's convention (conventional commits if detected).

**Merge commits:**
- Detect merge commits in the PR (commits with 2+ parents). If the project prefers rebase (check git config `pull.rebase` or CLAUDE.md), flag: "PR contains merge commits — consider rebasing for a linear history."

**Secrets scan:**
- Scan all commit diffs for patterns that look like secrets:
  - API keys: strings matching `[A-Za-z0-9_-]{20,}` near keywords like `key`, `token`, `secret`, `password`, `api_key`
  - AWS keys: `AKIA[0-9A-Z]{16}`
  - Private keys: `-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----`
  - `.env` values being added
- If found, this is a **must-fix** finding regardless of severity threshold.

### 1.3: Scope & Size

**Single concern:**
- If the diff touches files across unrelated subsystems (e.g., both frontend components and backend database migrations with no clear connection), flag: "This PR appears to mix unrelated changes — consider splitting for easier review."
- Heuristic: if changed files span 4+ top-level directories with no obvious shared purpose, flag it.

**Size advisory:**
- If `pr_size == very_large`: flag with specific decomposition suggestions based on the diff — identify logical split points (e.g., "The database migration could be its own PR, followed by the API changes, then the frontend integration").

**Draft status:**
- If the PR is marked as draft but has all review requests filled, note: "This PR is still in draft — mark it ready when you want formal review."
- If the PR is NOT draft but has TODO comments in the diff or placeholder code, note: "Consider keeping this as draft — the diff contains TODO comments suggesting incomplete work."

### 1.4: Testing & CI

**CI status:**
- From `statusCheckRollup`, identify failing checks. If any required check is failing:
  - Flag as must-fix: "CI check '{check_name}' is failing — this blocks merge."
  - If the PR body explains the failure, acknowledge it.

**Test coverage:**
- For each new public function/method/class added in the diff, check whether a corresponding test file or test case was also added/modified.
- If new code has no corresponding test changes, flag: "New public function `{name}` in `{file}` appears untested — consider adding test coverage."

**Test quality:**
- If tests were modified, scan for:
  - `.skip()` or `@skip` or `t.Skip()` added without explanation comment
  - Weakened assertions (e.g., `assertEqual` changed to `assertTrue`, strict checks removed)
  - Test-only changes that reduce coverage rather than increase it

---

## Phase 2: Code Review

The review strategy depends on PR size.

### Small/Medium PRs (< 500 changed lines)

Review the diff directly. For each changed file, read the full diff hunk and enough surrounding context to understand the change. Evaluate every change against these dimensions:

**Correctness:**
- Logic errors, off-by-one mistakes, incorrect comparisons
- Null/undefined/nil handling — unguarded dereferences, missing optional chaining
- Race conditions in concurrent code
- Edge cases not handled (empty inputs, boundary values, error paths)
- Type mismatches or implicit conversions that could cause bugs

**Security (OWASP-informed):**
- Injection vectors: SQL, command, template, LDAP, XPath
- XSS: unescaped user input in HTML/templates
- Auth/authz gaps: missing permission checks, privilege escalation paths
- Sensitive data exposure: logging PII, returning secrets in API responses
- Insecure deserialization, SSRF, open redirects
- Hardcoded credentials or secrets (even in test code if they look real)

**Performance:**
- N+1 query patterns (loop with database call inside)
- Unbounded loops or recursion without limits
- Missing database indexes for new query patterns
- Unnecessary memory allocations (large objects in hot loops)
- Missing pagination on list endpoints
- Blocking I/O in async contexts

**Maintainability:**
- Naming: variables, functions, types should clearly communicate purpose
- Function length: flag functions over ~50 lines that could be decomposed
- Duplication: near-identical code blocks that should be extracted
- Dead code: unreachable branches, unused imports, commented-out code
- Complexity: deeply nested conditionals, long parameter lists

**API Design (if applicable):**
- Backward compatibility: does the change break existing consumers?
- Error responses: proper HTTP status codes, informative error messages
- Pagination: unbounded list endpoints
- Rate limiting considerations for new endpoints

**Error Handling:**
- Swallowed exceptions (empty catch blocks)
- Missing error propagation (errors caught but not re-thrown or returned)
- Unclear error messages that won't help debugging
- Missing cleanup in error paths (unclosed resources, leaked connections)

**Concurrency (if applicable):**
- Thread safety of shared mutable state
- Deadlock potential from lock ordering
- Missing synchronization on concurrent data structures

### Large/Very Large PRs (500+ changed lines)

Use swarm orchestration to parallelize the review across specialist agents.

#### Step 2.1: Partition Files

Group changed files into logical clusters for parallel review:
- By directory/module when possible
- Keep related files together (e.g., a handler and its test)
- Balance cluster sizes roughly evenly

#### Step 2.2: Create Swarm Team

```
TeamCreate with teammates:
  - code-reviewer-1 (subagent_type: "refactor:code-reviewer")
  - code-reviewer-2 (subagent_type: "refactor:code-reviewer")  # if very_large
  - architect-1 (subagent_type: "refactor:architect")
  - test-reviewer-1 (subagent_type: "refactor:test-rigor-reviewer")
```

Scale the team:
- `large` (500-1500 lines): 1 code-reviewer, 1 architect, 1 test-rigor-reviewer
- `very_large` (1500+ lines): 2 code-reviewers (split file clusters), 1 architect, 1 test-rigor-reviewer

### Resource Limits

- Max parallel review agents: min(changed_file_count / 50, 5) — never more than 5 regardless of PR size.
- Per-agent timeout: 5 minutes. If an agent exceeds the timeout, log the timeout and proceed without its findings.

#### Step 2.3: Create Blackboard

Create a blackboard with `task_id = "pr-review-{PR_NUMBER}"` for cross-agent findings. Write:
- `pr_diff` — the full diff
- `pr_metadata` — title, body, author, labels, type
- `changed_files` — list of changed files with their clusters
- `existing_comments` — already-reviewed issues to skip

#### Step 2.4: Assign Tasks

Create tasks for each specialist:

**code-reviewer tasks:**
```
TaskCreate:
  title: "Review {cluster_name} for correctness, security, and quality"
  description: |
    Review these files from PR #{PR_NUMBER} for:
    - Correctness: logic errors, null handling, race conditions, edge cases
    - Security: OWASP top 10, injection vectors, auth gaps, secrets
    - Performance: N+1 queries, unbounded loops, missing indexes
    - Maintainability: naming, duplication, dead code, complexity

    Files to review:
    {file_list_with_diff_hunks}

    Read blackboard key 'existing_comments' to avoid duplicating prior reviewer feedback.

    For each finding, report:
    - file, line number, severity (must-fix/should-fix/nit)
    - what the issue is
    - why it matters
    - suggested fix (code snippet when possible)
    - confidence (0-100)

    Write findings to blackboard key 'reviewer_{instance}_findings'.
  owner: code-reviewer-{N}
```

**architect task:**
```
TaskCreate:
  title: "Review PR #{PR_NUMBER} architectural impact"
  description: |
    Evaluate this PR's architectural impact:
    - Does the change follow established project patterns?
    - Are new abstractions appropriate or over-engineered?
    - Dependency analysis: new dependencies justified?
    - Module coupling: does this increase coupling between subsystems?
    - Design pattern compliance: correct use of patterns for this codebase

    Changed files: {file_list}
    PR diff available on blackboard key 'pr_diff'.

    Write findings to blackboard key 'architect_findings'.
  owner: architect-1
```

**test-rigor-reviewer task:**
```
TaskCreate:
  title: "Evaluate test quality for PR #{PR_NUMBER}"
  description: |
    Review test files changed in this PR for scientific rigor:
    - Are assertions meaningful (not tautological)?
    - Do tests cover edge cases and boundaries?
    - Are test generators/fixtures well-constructed?
    - Would these tests catch mutations (fault injection)?
    - Are skipped tests justified?

    Test files: {test_file_list}

    Write findings to blackboard key 'test_rigor_findings'.
  owner: test-reviewer-1
```

#### Step 2.5: Send Start Signal and Wait

Send a start message to each teammate and wait for all tasks to complete. Read findings from the blackboard.

#### Step 2.6: Synthesize Findings

Merge all specialist findings:
1. Deduplicate: if multiple agents flagged the same issue on the same file/line, keep the most detailed version
2. Resolve conflicts: if agents disagree (one flags an issue, another's analysis contradicts it), keep the finding but note the disagreement
3. Cross-reference: if the architect flagged a design issue that explains multiple code-reviewer findings, group them under the architectural concern

Clean up: delete the team after synthesis is complete.

---

## Phase 3: Review Synthesis & Submission

### Step 3.1: Classify Findings

Assign each finding a classification:

| Classification | Criteria | Review Impact |
|---|---|---|
| **must-fix** | Bugs, security vulnerabilities, data loss risk, broken functionality | Blocks approval (REQUEST_CHANGES) |
| **should-fix** | Performance issues, missing error handling, maintainability concerns | Non-blocking but strongly recommended |
| **nit** | Style, naming, minor cleanup, cosmetic | Optional |
| **question** | Clarification needed, "why was this done this way?" | Information request |
| **praise** | Positive reinforcement — well-written code, good patterns, clever solutions | Always include at least one per review |

Apply the `--severity` threshold: filter out findings below the threshold level.

### Step 3.2: Compose Review Comments

For each finding, compose a comment following this structure:

```
**[classification]** Brief title

What: {description of the issue}

Why: {why this matters — impact on users, maintainability, security, etc.}

Suggestion:
\`\`\`{language}
{suggested fix code}
\`\`\`
```

For multi-file issues, place the comment on the most relevant file/line and cross-reference:
```
This pattern also appears in `other_file.ts:42` and `another_file.ts:78`.
```

Group related findings: if 3 instances of the same issue exist, post one detailed comment and reference the other locations rather than posting 3 separate comments.

### Step 3.3: Compose Review Summary

Write the review body — this appears as the top-level review message:

```markdown
## PR Review: {PR title}

{One paragraph assessment of overall quality, readiness, and notable aspects}

### Findings Summary
| Category | Count |
|----------|-------|
| Must-fix | N |
| Should-fix | N |
| Nits | N |
| Questions | N |

### Key Findings
1. **{most impactful finding title}** — {one-line summary} ({file}:{line})
2. **{second finding}** — {summary}
3. **{third finding}** — {summary}

{If hygiene issues were found, include a "### PR Hygiene" section summarizing them}

### Verdict
**{APPROVE | REQUEST_CHANGES | COMMENT}** — {one sentence reasoning}
```

**Verdict logic:**
- `REQUEST_CHANGES` if any must-fix findings exist
- `REQUEST_CHANGES` if CI is failing with no explanation
- `REQUEST_CHANGES` if secrets detected in the diff
- `APPROVE` if no must-fix findings and the PR is generally sound
- `COMMENT` if there are only should-fix/nit findings and you want to give feedback without blocking

### Step 3.4: Submit the Review

**If `--dry-run`**: Print the full review (summary + all comments with their file/line targets) and stop.

Otherwise, use the GitHub review API to submit as a single batch:

1. **Create a pending review** using the GitHub MCP tool:
   ```
   pull_request_review_write(method: "create", owner, repo, pull_number, body: review_summary, event: verdict)
   ```

2. **Add line comments** to the pending review:
   ```
   add_comment_to_pending_review(owner, repo, pull_number, path, line, body: comment_text)
   ```
   For each finding, add it as a line comment on the correct file and line.

3. **Submit the pending review**:
   ```
   pull_request_review_write(method: "submit_pending", owner, repo, pull_number, event: verdict)
   ```

This ensures all comments arrive as one atomic review notification, not a stream of individual comments.

### Step 3.5: Post-Review Summary

Report to the user:

```
PR #{PR_NUMBER} Review Complete
================================
Size: {pr_size} ({total_changed_lines} lines across {changed_files} files)
Type: {pr_type}
Strategy: {direct review | swarm-orchestrated}

Findings: {must_fix} must-fix, {should_fix} should-fix, {nits} nits, {questions} questions
Verdict: {APPROVE | REQUEST_CHANGES | COMMENT}
Review URL: {link to the review on GitHub}
```

---

## Constraints

These are non-negotiable rules that override any other guidance:

1. **Never approve with failing CI** unless the user explicitly passes `--auto-approve-trivial` and the failures are on optional/non-required checks.
2. **Never approve with secrets in the diff.** If credentials, API keys, or private keys are detected, the verdict is always `REQUEST_CHANGES` regardless of other findings.
3. **Respect existing reviews.** Before posting a comment on a file/line, check the existing comments fetched in Step 0.5. If another reviewer already raised the same concern, skip it or reference their comment instead of duplicating.
4. **Bot PR streamlining.** If the author is a bot (dependabot, renovate, github-actions), focus the review on: changelog entries, breaking changes, version compatibility, and license compliance. Skip style/naming/architecture feedback — bots don't read it.
5. **Rate-limit API calls.** Use `--paginate` for list endpoints. Batch GraphQL queries where possible. Don't fetch the same data twice.
6. **At least one praise comment per review.** Every PR has something done well — find it and acknowledge it. This is not optional.

---

Begin reviewing based on: $ARGUMENTS

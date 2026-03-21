---
name: pr
description: "Create, update, or manage GitHub pull requests using gh CLI. Creates draft PRs by default to encourage iterative development. Use this skill when the user wants to open a PR, create a pull request, submit changes for review, convert a draft PR to ready, update an existing PR, or push a branch and open a PR. Triggers on: 'create a PR', 'open a pull request', 'submit PR', 'make a PR', 'PR for this branch', 'mark PR ready', 'update the PR', 'push and open PR', 'send this for review'. Anti-triggers (do NOT match): 'fix PR comments' (use /pr-fix), 'review PR comments' (use /review-comments), 'cherry-pick' (use /cp), 'review this PR' (use /review-comments), 'merge PR', 'close PR'."
argument-hint: "[to-branch] [--ready] [--update] [--web] [--fill] [--no-draft]"
---

# Pull Request Skill

You manage GitHub pull requests using the `gh` CLI exclusively. Draft PRs are the default to encourage iterative development.

## Help Check

If `$ARGUMENTS` is `help`, `--help`, or `-h`, print this summary and stop:

```
/pr — Create, update, or manage GitHub pull requests

Usage:
  /pr                        Create draft PR to default branch
  /pr develop                Create draft PR targeting 'develop'
  /pr --ready                Convert current draft PR to ready for review
  /pr --update               Update existing PR (push new commits, edit title/body)
  /pr --web                  Open PR creation in browser
  /pr --fill                 Auto-fill title/body from commit messages
  /pr --no-draft             Create as ready-for-review instead of draft

Arguments:
  TO_BRANCH                  Target branch (defaults to main or repo default)
  --ready                    Convert existing draft PR to ready for review
  --update                   Update an existing PR (title, body, or add commits)
  --web                      Open PR creation in browser via gh
  --fill                     Auto-fill title/body from commit messages
  --no-draft                 Create as ready-for-review instead of draft

Related skills:
  /pr-fix                    Fix issues raised in PR review comments
  /review-comments           Review and respond to PR comments
  /cp                        Cherry-pick commits across branches
```

## Arguments

**$ARGUMENTS**: Optional target branch and flags.

Parse `$ARGUMENTS` for the following flags **before** any other processing:

- `--ready` — Convert existing draft PR to ready for review. Extract and set `mode = "ready"`.
- `--update` — Update an existing PR. Extract and set `mode = "update"`.
- `--web` — Open PR creation in browser. Extract and set `web_mode = true`.
- `--fill` — Auto-fill title and body from commit messages. Extract and set `fill_mode = true`.
- `--no-draft` — Create PR as ready-for-review. Extract and set `no_draft = true`.

After extracting flags, the remaining `$ARGUMENTS` is interpreted as the target branch name. If empty, the target branch defaults to the repository's default branch (usually `main`).

### Natural Language Intent Mapping

When the user's prompt is natural language (not a `/pr` slash command), infer flag equivalents from their intent **before** entering the workflow:

| User says (examples) | Equivalent flag | Variable to set |
|---|---|---|
| "skip the draft", "mark it ready", "not a draft", "ready immediately", "no draft" | `--no-draft` | `no_draft = true` |
| "update the PR", "push new commits to the PR", "add to the existing PR" | `--update` | `mode = "update"` |
| "mark PR ready", "convert to ready", "ready for review" (existing PR) | `--ready` | `mode = "ready"` |
| "open in browser", "use the web form" | `--web` | `web_mode = true` |
| "auto-fill from commits", "use commit messages" | `--fill` | `fill_mode = true` |
| "PR to develop", "target staging", "base branch is release" | (target branch) | `TARGET_BRANCH = <branch>` |

Apply these inferences alongside explicit flag parsing. When the user mentions a specific branch name as the target (e.g., "open a PR to develop"), use that as the target branch regardless of whether it was passed as `$ARGUMENTS` or mentioned in natural language.

## Phase 0: Pre-flight Checks

Run these checks sequentially. Abort with a clear error if any fail.

### Step 0.1: Verify gh CLI

```bash
command -v gh >/dev/null 2>&1 || { echo "ERROR: gh CLI not found. Install from https://cli.github.com/"; exit 1; }
```

### Step 0.2: Verify Authentication

```bash
gh auth status 2>&1 || { echo "ERROR: Not authenticated. Run 'gh auth login' first."; exit 1; }
```

### Step 0.3: Get Branch and Remote Info

```bash
CURRENT_BRANCH=$(git branch --show-current)
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q '.defaultBranchRef.name' 2>/dev/null || echo "main")
REMOTE=$(git remote | head -1)
```

If `CURRENT_BRANCH` equals the target branch, abort: "ERROR: Cannot create PR from the target branch itself. Switch to a feature branch first."

### Step 0.4: Check for Existing PR

```bash
EXISTING_PR=$(gh pr view --json number,state,isDraft,url 2>/dev/null || echo "")
```

Store the result for use in workflow selection.

## Phase 1: Workflow Selection

Select the workflow based on parsed flags:

- If `mode == "ready"` -> **Workflow: Ready**
- If `mode == "update"` -> **Workflow: Update**
- Otherwise -> **Workflow: Create**

---

## Workflow: Ready

Convert a draft PR to ready for review.

### Step R.1: Verify Draft PR Exists

If no existing PR found, abort: "ERROR: No PR found for branch '${CURRENT_BRANCH}'. Create one first with /pr."

If existing PR is not a draft, inform the user: "PR #N is already marked as ready for review."

### Step R.2: Convert to Ready

```bash
gh pr ready
```

Report success with the PR URL.

---

## Workflow: Update

Update an existing PR with new commits and/or modified title/body.

### Step U.1: Verify PR Exists

If no existing PR found, abort: "ERROR: No PR found for branch '${CURRENT_BRANCH}'. Create one first with /pr."

### Step U.2: Push New Commits

Check if there are unpushed commits:

```bash
UNPUSHED=$(git log @{u}..HEAD --oneline 2>/dev/null || echo "")
```

If there are unpushed commits, push them:

```bash
git push
```

### Step U.3: Optionally Update Title/Body

Ask the user if they want to update the PR title or body. If yes, use:

```bash
gh pr edit --title "NEW_TITLE" --body "NEW_BODY"
```

Report success with the PR URL and summary of changes.

---

## Workflow: Create

Create a new pull request (draft by default).

### Step C.1: Check for Uncommitted Changes

```bash
git status --porcelain
```

If there are uncommitted changes, warn the user: "WARNING: You have uncommitted changes. These will NOT be included in the PR. Commit them first if needed."

### Step C.2: Ensure Branch is Current

Before pushing, ensure the branch is rebased on the latest target branch to avoid merge conflicts and out-of-date PRs.

1. Fetch the target branch:
   ```bash
   TARGET_BRANCH="${TO_BRANCH:-$DEFAULT_BRANCH}"
   git fetch ${REMOTE} ${TARGET_BRANCH}
   ```

2. Check if behind the target branch:
   ```bash
   BEHIND=$(git log --oneline HEAD..${REMOTE}/${TARGET_BRANCH} | head -5)
   ```

3. If `BEHIND` is non-empty, rebase onto the target branch:
   ```bash
   git rebase ${REMOTE}/${TARGET_BRANCH}
   ```

4. **Conflict Resolution**: If rebase encounters conflicts:
   1. **HALT the pipeline** — do NOT proceed to push or PR creation.
   2. Show conflicting files (`git diff --name-only --diff-filter=U`) and their conflict markers.
   3. Offer resolution options:
      - **Resolve manually** — User edits files, then `git add` resolved files and `git rebase --continue`.
      - **Abort** — `git rebase --abort` and stop.
      - **Skip commit** — `git rebase --skip` (warn about skipped changes).
   4. State: "The PR creation pipeline is halted. No PR will be created until the rebase completes cleanly."
   5. Repeat for each conflicting commit until the rebase completes or is aborted.

### Step C.3: Push Branch

Push the rebased branch to the remote with a single normal push.

Check if branch is pushed to remote:

```bash
git ls-remote --exit-code --heads "${REMOTE}" "${CURRENT_BRANCH}" >/dev/null 2>&1
```

If not pushed, push with upstream tracking:

```bash
git push -u "${REMOTE}" "${CURRENT_BRANCH}"
```

If already pushed, check for unpushed commits and push if needed.

### Step C.4: Check for Existing PR

If an existing PR was found in Phase 0:

1. **Display the existing PR details**: Show the PR URL, PR number, state, and draft status from the `EXISTING_PR` data captured in Step 0.4.
2. **Inform the user** that a PR already exists for this branch.
3. **Suggest using `--update`** to push new commits or modify the existing PR instead of creating a duplicate.
4. **Do not create a duplicate PR** — stop the Create workflow here.

### Step C.5: Gather PR Info

Get commits between base and head:

```bash
TARGET_BRANCH="${TO_BRANCH:-$DEFAULT_BRANCH}"
git log "${TARGET_BRANCH}..HEAD" --oneline --no-merges
```

Get a diff summary for context:

```bash
git diff "${TARGET_BRANCH}...HEAD" --stat
```

### Step C.6: Generate PR Title and Body

If `fill_mode` is set, let `gh` auto-fill from commits. Otherwise:

1. Analyze the commits and diff to generate a concise PR title (under 70 characters).
2. Generate a PR body using this structure:

```markdown
## Summary
<!-- 1-3 bullet points describing the changes -->

## Changes
<!-- Detailed list of what changed and why -->

## Test Plan
<!-- How to verify the changes work -->
```

Present the generated title and body to the user for approval before creating.

### Step C.7: Create PR

Build the `gh pr create` command:

```bash
gh pr create \
  --base "${TARGET_BRANCH}" \
  --title "${PR_TITLE}" \
  --body "${PR_BODY}" \
  ${DRAFT_FLAG}
```

Where `DRAFT_FLAG` is `--draft` unless `--no-draft` was specified.

If `web_mode` is set, use `--web` flag instead of `--title` and `--body` to open in browser.

If `fill_mode` is set, use `--fill` flag instead of `--title` and `--body`.

### Step C.8: Report Success

Display:
- PR URL
- PR number
- Draft status
- Target branch
- Number of commits included

---

## Error Handling

- All `gh` and `git` commands must have their exit codes checked.
- On failure, display the actual error output from the command.
- Never silently swallow errors.
- If `gh pr create` fails due to a pre-existing PR, suggest `--update` instead.

## Notes

- Draft PRs are the default to encourage iterative development and early feedback.
- Uses `gh` CLI exclusively for all GitHub operations — never raw API calls.
- Branch protection rules and required checks are handled by GitHub, not this skill.
- Related skills: `/pr-fix` for addressing review comments, `/review-comments` for reviewing PR feedback, `/cp` for cherry-picking across branches.

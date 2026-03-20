---
name: cp
description: "Stage, commit, and push all code changes on the current branch to the remote origin using the gh CLI. Use this skill when the user wants to commit and push their work, save progress, checkpoint code, or ship changes upstream. Triggers on: 'commit and push', 'push my changes', 'save and push', 'cp', 'ship it', 'push this up', 'commit everything and push', 'send it', 'checkpoint and push'. Anti-triggers: 'create a PR' (use feature-dev), 'review my code' (use refactor), 'just commit' without push intent, 'git status', 'what changed', 'diff'."
argument-hint: "[commit message override]"
---

# CP Skill — Stage, Commit, and Push

You are a commit-and-push automation agent. Your job is to review changes, generate professional commit messages, and push to the remote origin — all using the `gh` and `git` CLIs.

## Arguments

**$ARGUMENTS**: Optional commit message override.

- If `$ARGUMENTS` contains `--help`, `-h`, or `help`: display the man-page style help below and stop.
- If `$ARGUMENTS` is non-empty (and not a help flag): use it as the commit message (skip message generation in Step 2).
- If `$ARGUMENTS` is empty: auto-generate the commit message from the diff.

## Help Output

When help is requested, display this and stop:

```
CP(1)                        GPM Skills Manual                        CP(1)

NAME
    cp — stage, commit, and push all code changes on the current branch

SYNOPSIS
    /cp [commit message override]

DESCRIPTION
    Reviews all modified and untracked files, generates a conventional-
    commit message, stages and commits changes, then pushes to the remote
    origin on the current branch.

    Confidential files (.env, API keys, credentials, secrets) are never
    staged. If new files and modifications coexist, they are split into
    separate commits.

OPTIONS
    commit message override
        When provided, uses this text as the commit message verbatim
        instead of auto-generating one. Must still follow conventional
        commit format.

    --help, -h, help
        Display this help text and exit.

COMMIT MESSAGE CONVENTIONS
    Title:  <type>: <description>  (max 70 characters)
    Types:  feat, fix, perf, refactor, docs, style, ci, chore, build, test

    Special rules for .claude/ directory:
      - Modified .claude/ markdown files use  perf:  (not docs:)
      - New .claude/ files use  feat:  (not docs: or perf:)

EXAMPLES
    /cp
        Auto-generate commit message from diff and push.

    /cp "fix: resolve null pointer in webhook handler"
        Commit with the given message and push.

SEE ALSO
    git-commit(1), git-push(1), gh(1)
```

## Step 1: Review Changes

1. Run `git status` to identify all modified, staged, and untracked files.
2. Run `git diff` and `git diff --cached` to inspect the actual changes.
3. **Security check**: Identify and exclude any files that contain confidential information:
   - `.env`, `.env.*` files
   - Files containing API keys, tokens, passwords, or database credentials
   - `credentials.json`, `secrets.*`, `*.pem`, `*.key` files
   - Any file matching common secret patterns
4. If confidential files are detected, warn the user and exclude them from staging.
5. If there are no changes to commit, inform the user and stop.

## Step 2: Generate Commit Message

If `$ARGUMENTS` provided a commit message, use it directly. Otherwise:

1. Analyze the diff to understand the nature of changes.
2. Generate a commit message following conventional commit rules:
   - **Types**: `feat`, `fix`, `perf`, `refactor`, `docs`, `style`, `ci`, `chore`, `build`, `test`
   - **Special .claude/ rules**:
     - Modified markdown files in `.claude/` use `perf:` (not `docs:`)
     - New files in `.claude/` use `feat:` (not `docs:` or `perf:`)
   - **Title**: Less than 70 characters.
   - **Body**: Summarized list of key changes.
3. Determine if changes should be split into separate commits:
   - If there are both new files AND modifications to existing files, split into separate commits.
   - Group related changes logically.

## Step 3: Stage and Commit

1. Stage files using `git add` with explicit file paths (never `git add -A` or `git add .`).
   - Stage only the files identified in Step 1, excluding any confidential files.
2. Commit using `git commit -m` with a HEREDOC for proper formatting:
   ```bash
   git commit -m "$(cat <<'EOF'
   <type>: <title>

   <body>
   EOF
   )"
   ```
3. If splitting into multiple commits, repeat staging and committing for each group.
4. **Never add AI attribution lines** such as:
   - `Co-Authored-By: Claude ...`
   - `Generated with [Claude Code]`
   - Any AI tool signatures or references

## Step 4: Verify Commit

1. Run `git log --oneline -5` to confirm the commit(s) succeeded.
2. Display the resulting commit hash(es) and message(s).

## Step 5: Push to Remote

1. Determine the current branch: `git branch --show-current`
2. Push using `git push origin <branch>`.
   - If the branch has no upstream, use `git push -u origin <branch>`.
3. Confirm the push succeeded.
4. If the push fails (e.g., rejected due to remote changes), inform the user with the error and suggest resolution (pull/rebase).

---

Begin processing now based on: $ARGUMENTS

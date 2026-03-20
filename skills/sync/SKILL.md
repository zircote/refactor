---
name: sync
description: "Full git sync cycle: fetch from remote, rebase current branch onto remote tracking branch, and push. Use when the user wants to sync their branch, pull and push, update and push, or do a full fetch-rebase-push cycle. Triggers on 'sync my branch', 'sync with remote', 'fetch rebase push', 'pull rebase and push', 'update and push my branch', 'sync up'. Anti-triggers: use /fr for fetch+rebase WITHOUT push; use /ff for fast-forward merge only; do NOT use for force-push, cherry-pick, merge (non-rebase), or interactive rebase."
argument-hint: "[remote] [branch]"
---

# Sync Skill

Full sync cycle: fetch from remote, rebase current branch onto remote tracking branch, and push.

This skill extends the `/fr` (fetch-rebase) workflow by adding a confirmed push step. For fetch+rebase without push, use `/fr`. For fast-forward merge only, use `/ff`.

## Help Check

If `$ARGUMENTS` is `help`, `--help`, or `-h`, print this usage summary and stop:

```
Usage: /sync [remote] [branch]

Full sync — fetch, rebase onto remote branch, and push.

Arguments:
  remote    Remote name (default: origin)
  branch    Branch to rebase onto (default: current branch's upstream)

Examples:
  /sync                  # fetch origin, rebase onto upstream, push
  /sync upstream         # fetch upstream, rebase onto upstream tracking, push
  /sync origin main      # fetch origin, rebase onto origin/main, push

Related:
  /fr   — Fetch + rebase only (no push)
  /ff   — Fast-forward merge only
```

## Arguments

- **REMOTE**: First argument. Defaults to `origin`.
- **BRANCH**: Second argument. Defaults to the current branch's upstream tracking branch. If no upstream is configured, fall back to the current branch name.

## Pre-flight Checks

### 1. Uncommitted Changes

Run `git status --porcelain`. If output is non-empty:

Present the user with three options:
- **A) Stash, sync, pop** — Run `git stash push -m "sync-auto-stash"`, perform the sync, then `git stash pop`.
- **B) Abort** — Stop immediately.
- **C) Proceed anyway** — Continue with dirty working tree (warn that rebase may fail).

Wait for the user's choice before continuing.

### 2. Rebase in Progress

Check for an in-progress rebase: `git rev-parse --verify --quiet refs/rebase-merge/head-name 2>/dev/null || git rev-parse --verify --quiet refs/rebase-apply/head-name 2>/dev/null`.

If a rebase is already in progress, inform the user and abort. Suggest they resolve it with `git rebase --continue`, `git rebase --abort`, or `git rebase --skip`.

### 3. Determine Target Branch

If BRANCH was not specified:
1. Try: `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` to get the upstream ref (e.g., `origin/main`).
2. Parse the remote and branch from the result.
3. If no upstream is set, use `REMOTE` and the current branch name (`git branch --show-current`).

## Workflow

### Step 1: Fetch

```bash
git fetch ${REMOTE}
```

Report the fetch result. If fetch fails, abort with the error message.

### Step 2: Show Divergence

```bash
git log --oneline HEAD..${REMOTE}/${BRANCH} | head -10
```

Show the user how many commits they are behind. If zero commits behind, inform the user the branch is already up to date but continue (there may still be local commits to push).

Also show how many local commits will be pushed:

```bash
git log --oneline ${REMOTE}/${BRANCH}..HEAD | head -10
```

### Step 3: Rebase

```bash
git rebase ${REMOTE}/${BRANCH}
```

If the rebase completes cleanly, proceed to Step 4.

**Conflict Resolution**: If rebase encounters conflicts:
1. Show the conflicting files: `git diff --name-only --diff-filter=U`
2. Show the conflict markers in each file.
3. Ask the user how to proceed:
   - **Resolve manually** — The user will edit files; wait for them to indicate readiness, then `git add` resolved files and `git rebase --continue`.
   - **Abort** — Run `git rebase --abort` and stop the sync.
   - **Skip this commit** — Run `git rebase --skip` (warn about skipped changes).
4. Repeat for each conflicting commit until the rebase completes or is aborted.

If the rebase was aborted, stop. If a stash was saved in pre-flight, pop it before stopping.

### Step 4: Confirm Before Push

Show the user what will be pushed:

```bash
git log --oneline ${REMOTE}/${BRANCH}..HEAD
```

Ask the user to confirm the push. Do NOT push without explicit confirmation.

If the user declines, stop. If a stash was saved in pre-flight, pop it.

### Step 5: Push

```bash
git push ${REMOTE} HEAD
```

Do NOT use `--force` unless the user explicitly requests it. If the push is rejected (e.g., non-fast-forward), inform the user and suggest options:
- Re-run `/sync` to incorporate new remote changes.
- Use `--force` only if they are certain (and warn about the risks).

### Step 6: Report

Show final status:

```bash
git status
```

Report success. Summarize what happened:
- How many commits were fetched/rebased.
- How many commits were pushed.
- Current branch and tracking status.

If a stash was saved in pre-flight, pop it now with `git stash pop` and report any stash-pop conflicts.

## Notes

- Always confirm before pushing.
- Do NOT use `--force` push unless the user explicitly requests it.
- This is the full cycle; use `/fr` for just fetch+rebase without the push step.
- Use `/ff` for fast-forward merge workflows instead of rebase.
- If the user only needs to fetch and rebase (no push), redirect them to `/fr`.

Begin sync now based on: $ARGUMENTS

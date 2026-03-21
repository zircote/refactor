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

Parse the user's input to extract remote and branch:

- **REMOTE**: First positional argument, OR extracted from context (e.g., "origin/main" means REMOTE=origin). Defaults to `origin`.
- **BRANCH**: Second positional argument, OR extracted from context (e.g., "origin/main" means BRANCH=main, "with main" means BRANCH=main). Defaults to the current branch's upstream tracking branch. If no upstream is configured, fall back to the current branch name.

When the user says things like "sync with main", "sync against develop", or "pull from origin/main", parse these naturally to extract REMOTE and BRANCH.

## Pre-flight Checks

### 1. Uncommitted Changes

Run `git status --porcelain`. If output is non-empty (any modified, added, or deleted tracked files):

Present the user with three options:
- **A) Stash, sync, pop** — Run `git stash push -m "sync-auto-stash"`, perform the sync, then `git stash pop`.
- **B) Abort** — Stop immediately.
- **C) Proceed anyway** — Continue with dirty working tree (warn that rebase may fail).

**IMPORTANT**: You MUST wait for the user's explicit choice before continuing. Do NOT assume a choice. Do NOT skip this step. Present the options and stop until the user responds.

### 2. Rebase in Progress

Check for an in-progress rebase: `git rev-parse --verify --quiet refs/rebase-merge/head-name 2>/dev/null || git rev-parse --verify --quiet refs/rebase-apply/head-name 2>/dev/null`.

If a rebase is already in progress, inform the user and abort. Suggest they resolve it with `git rebase --continue`, `git rebase --abort`, or `git rebase --skip`.

### 3. Determine Target Branch

If BRANCH was not specified:
1. Try: `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` to get the upstream ref (e.g., `origin/main`).
2. Parse the remote and branch from the result.
3. If no upstream is set, use `REMOTE` and the current branch name (`git branch --show-current`).

## Workflow

Execute ALL steps in sequence. Report the result of EVERY step to the user, even when the result is "nothing to do". This is critical for the user to understand what happened.

### Step 1: Fetch

```bash
git fetch ${REMOTE}
```

Report the fetch result explicitly. State how many new objects/commits were fetched, or that the fetch found no new changes. If fetch fails (e.g., remote doesn't exist), abort with the error message and suggest fixes.

### Step 2: Show Divergence

Always run BOTH commands and show their output:

**Commits behind (upstream has, we don't):**
```bash
git log --oneline HEAD..${REMOTE}/${BRANCH} | head -10
```

**Commits ahead (we have, upstream doesn't — these will be pushed):**
```bash
git log --oneline ${REMOTE}/${BRANCH}..HEAD | head -10
```

Report clearly:
- "You are N commits behind ${REMOTE}/${BRANCH}" (or "Already up to date — no upstream changes")
- "You have N local commits to push" (or "No local commits to push")

### Step 3: Rebase

If there are upstream commits to incorporate:
```bash
git rebase ${REMOTE}/${BRANCH}
```

If already up to date (0 commits behind), you may skip the rebase and report: "Skipping rebase — already up to date with ${REMOTE}/${BRANCH}."

**Conflict Resolution**: If rebase encounters conflicts:
1. **HALT the pipeline** — do NOT proceed to push.
2. Show conflicting files (`git diff --name-only --diff-filter=U`) and their conflict markers.
3. Offer resolution options:
   - **Resolve manually** — User edits files, then `git add` resolved files and `git rebase --continue`.
   - **Abort** — `git rebase --abort` and stop.
   - **Skip commit** — `git rebase --skip` (warn about skipped changes).
4. State: "The sync pipeline is halted. No push will happen until the rebase completes cleanly."
5. Repeat for each conflicting commit until the rebase completes or is aborted.

If the rebase was aborted, stop. If a stash was saved in pre-flight, pop it before stopping.

### Step 4: Confirm Before Push

**ALWAYS execute this step**, even if there are zero commits to push.

Show the user what will be pushed:
```bash
git log --oneline ${REMOTE}/${BRANCH}..HEAD
```

If there are commits to push:
- List them clearly
- Ask the user to confirm: "Push these N commit(s) to ${REMOTE}? (yes/no)"
- Do NOT push without explicit confirmation.

If there are zero commits to push:
- Report: "No commits to push — your branch is already fully in sync with ${REMOTE}/${BRANCH}."
- Skip the push step (no confirmation needed when nothing to push).

If the user declines, stop. If a stash was saved in pre-flight, pop it.

### Step 5: Push

Choose the push strategy based on what happened in Step 3:

- **Rebase was performed** (branch had upstream): `git push --force-with-lease ${REMOTE} HEAD` — safe because we just rebased onto the latest remote.
- **No rebase performed** (or no prior upstream): `git push ${REMOTE} HEAD`

Do NOT use bare `--force` unless the user has EXPLICITLY and DIRECTLY requested it. Speculative mentions ("I think it might need --force") are NOT explicit requests. Note: `--force-with-lease` after a rebase is a safe, automatic consequence of the rebase workflow — it is NOT the same as bare `--force`.

If the push is rejected (e.g., `--force-with-lease` fails because someone pushed between our fetch and push), inform the user and suggest:
- **Primary recommendation**: Re-run `/sync` to incorporate the new remote changes.
- **Secondary note**: Mention that `--force` exists as an option but do NOT offer to run it. Instead, tell the user they can re-invoke `/sync` with an explicit force flag if needed. Warn about the risks of rewriting remote history.

### Step 6: Report

Show final status:

```bash
git status
```

Report success with a clear summary. ALWAYS include these details:
- How many commits were fetched/rebased (even if 0)
- How many commits were pushed (even if 0)
- Current branch and tracking status

If a stash was saved in pre-flight, pop it now with `git stash pop` and report any stash-pop conflicts.

## Notes

- Always confirm before pushing (when there are commits to push).
- Do NOT use `--force` push unless the user explicitly requests it.
- This is the full cycle; use `/fr` for just fetch+rebase without the push step.
- Use `/ff` for fast-forward merge workflows instead of rebase.
- If the user only needs to fetch and rebase (no push), redirect them to `/fr`.

Begin sync now based on: $ARGUMENTS

---
name: fr
description: Fetch from a git remote and rebase the current branch onto the remote tracking branch. Use this skill when the user wants to pull upstream changes via rebase, update their branch from origin, fetch-and-rebase, or sync with remote without merging. Triggers on "fetch and rebase", "rebase onto origin", "pull --rebase", "fr", "update my branch from remote", "rebase on upstream", "fetch origin and rebase". Anti-triggers: do NOT use for merge-based pulls, force-push, fast-forward-only updates (use /ff), full sync-push cycles (use /sync), or creating/switching branches.
argument-hint: "[remote] [branch]"
---

# Fetch and Rebase Skill

You perform a git fetch followed by a rebase of the current branch onto the specified remote branch.

## Help Check

If `$ARGUMENTS` contains `--help`, `-h`, or `help`, print this man-page style summary and stop:

```
USAGE
  /fr [remote] [branch]

DESCRIPTION
  Fetches from a git remote and rebases the current branch onto the
  remote tracking branch. Defaults to origin and the current branch's
  upstream if not specified.

ARGUMENTS
  remote    Remote name (default: origin)
  branch    Branch name (default: current branch's upstream tracking branch)

EXAMPLES
  /fr                     # fetch origin, rebase onto upstream
  /fr upstream             # fetch upstream, rebase onto upstream/current-branch
  /fr origin main          # fetch origin, rebase onto origin/main

RELATED SKILLS
  /ff    Fast-forward only update (no rebase)
  /sync  Full fetch-rebase-push cycle
```

## Arguments

**$ARGUMENTS**: Optional positional arguments.

- **REMOTE**: First argument. Defaults to `origin`.
- **BRANCH**: Second argument. Defaults to the current branch's upstream tracking branch (determined via `git rev-parse --abbrev-ref --symbolic-full-name @{u}`). If no upstream is configured and no branch argument is provided, abort with guidance on setting upstream.

## Pre-flight Checks

Run all pre-flight checks before any git operations.

### 1. Uncommitted Changes

Check for uncommitted changes:

```bash
git status --porcelain
```

If output is non-empty, present the user with three options:
- **A) Stash and continue**: Run `git stash push -m "fr-auto-stash"`, proceed with fetch/rebase, then run `git stash pop` after successful rebase.
- **B) Abort**: Stop execution entirely.
- **C) Proceed anyway**: Continue without stashing (user accepts risk of conflicts with dirty tree).

Wait for user response before continuing.

### 2. Rebase Already in Progress

Check for an in-progress rebase:

```bash
ls -d .git/rebase-merge .git/rebase-apply 2>/dev/null
```

If either directory exists, abort and inform the user they must resolve or abort the existing rebase first (`git rebase --continue` or `git rebase --abort`).

### 3. Determine Target Branch

If BRANCH was not provided as an argument, resolve it:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

Extract the branch portion (strip the `remote/` prefix). If this fails (no upstream configured), abort with a message suggesting `git branch --set-upstream-to=${REMOTE}/<branch>`.

## Workflow

### Step 1: Fetch

```bash
git fetch ${REMOTE}
```

Report what was fetched. If fetch fails (network error, invalid remote), abort with the error.

### Step 2: Show Divergence

Show commits on the remote branch that are not on the current branch:

```bash
git log --oneline HEAD..${REMOTE}/${BRANCH} | head -20
```

If empty, inform the user the branch is already up to date and stop (no rebase needed).

Also show any local commits that will be replayed:

```bash
git log --oneline ${REMOTE}/${BRANCH}..HEAD | head -20
```

### Step 3: Rebase

```bash
git rebase ${REMOTE}/${BRANCH}
```

### Step 4: Report

On success, show the result:

```bash
git log --oneline -5
```

Report: number of commits rebased, current HEAD position, and whether a stash pop is pending.

If a stash was created in pre-flight, pop it now:

```bash
git stash pop
```

## Conflict Resolution

If the rebase encounters conflicts:

1. List the conflicted files: `git diff --name-only --diff-filter=U`
2. Explain that conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) must be resolved manually in each file.
3. Provide the resolution commands:
   - After resolving: `git add <resolved-files> && git rebase --continue`
   - To abort the rebase entirely: `git rebase --abort`
4. If a stash was auto-created, remind the user it is still saved and will need `git stash pop` after the rebase completes.

## Safety Rules

- **DO NOT** force push after rebase unless the user explicitly requests it.
- **DO NOT** push at all. This skill only fetches and rebases. For push, direct the user to `/sync`.
- **DO NOT** modify or create branches. This operates on the current branch only.
- **DO NOT** use `--force` or `--force-with-lease` flags on any command.

## Related Skills

- **/ff** — Fast-forward-only branch update (no rebase, no divergent history).
- **/sync** — Full cycle: fetch, rebase, and push to remote.

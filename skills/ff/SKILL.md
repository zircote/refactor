---
name: ff
description: Fast-forward merge only — update the current branch from its remote tracking branch without rebase or merge commits. Use this skill when the user wants to pull upstream changes cleanly, fast-forward their branch, catch up with remote, or update a branch they haven't modified locally. Triggers on "fast-forward", "ff", "pull without merge", "catch up with remote", "update branch from origin", "ff merge". Does NOT trigger for rebase requests (use /fr), full sync workflows (use /sync), force-push, branch creation, cherry-pick, or merge-with-commit workflows.
argument-hint: "[remote] [branch]"
---

# Fast-Forward Merge Skill

You are performing a fast-forward-only merge from a remote tracking branch. This is the safest update method — it never creates merge commits and never rewrites history.

## Execution Policy

**Run all git commands immediately without asking for user confirmation.** The commands in this skill (fetch, merge-base, merge --ff-only) are all safe, read-only or fast-forward-only operations. Never pause to ask "can I run this?" or "do you approve?" — just execute each step and report the results. The user invoked this skill expecting autonomous execution.

## Help Check

If `$ARGUMENTS` is `--help`, `-h`, or `help`, print the following and stop:

```
ff - Fast-forward merge only

USAGE
  /ff [remote] [branch]

ARGUMENTS
  remote    Remote name (default: origin)
  branch    Branch to fast-forward from (default: current branch's upstream)

DESCRIPTION
  Fetches from the remote and attempts a fast-forward merge. This is the
  safest way to update a branch — it only succeeds when local history is
  a strict ancestor of the remote, so no merge commits or rebases occur.

  Ideal for pulling updates on branches you haven't modified locally.

EXAMPLES
  /ff                    Fast-forward from upstream of current branch
  /ff upstream           Fast-forward from 'upstream' remote
  /ff origin main        Fast-forward current branch to origin/main

SEE ALSO
  /fr    - Fetch and rebase (when fast-forward is not possible)
  /sync  - Full branch synchronization workflow
```

## Arguments

- **REMOTE**: First positional argument from `$ARGUMENTS`. Defaults to `origin`.
- **BRANCH**: Second positional argument from `$ARGUMENTS`. Defaults to the current branch's upstream tracking branch (determined in pre-flight).

## Pre-flight Checks

### Step 1: Check Working Directory

Run `git status --porcelain`. If there is any output (uncommitted changes exist), stop and report:

> Working directory is not clean. Commit or stash your changes before fast-forwarding.

Do not proceed.

### Step 2: Determine Target Branch

If BRANCH was not provided as an argument:

1. Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` to get the upstream tracking reference.
2. Parse the branch name from the result (strip the remote prefix).
3. If no upstream is configured, stop and report:

> No upstream tracking branch configured. Specify a branch explicitly:
> `/ff origin main`

## Workflow

### Step 1: Fetch

Run:
```
git fetch ${REMOTE}
```

Report what was fetched.

### Step 2: Check Fast-Forward Feasibility

Run:
```
git merge-base --is-ancestor HEAD ${REMOTE}/${BRANCH}
```

- **Exit code 0**: Fast-forward is possible. Proceed to Step 3.
- **Non-zero exit code**: Fast-forward is NOT possible. Go to Step 4.

### Step 3: Fast-Forward Merge

First, record the current HEAD for commit counting:
```
OLD_HEAD=$(git rev-parse HEAD)
```

Run the fast-forward merge:
```
git merge --ff-only ${REMOTE}/${BRANCH}
```

Check if the branch was already up to date (OLD_HEAD equals new HEAD):
```
NEW_HEAD=$(git rev-parse HEAD)
```

If `OLD_HEAD` equals `NEW_HEAD`, the branch is already up to date. Report:
> Already up to date — no new commits on ${REMOTE}/${BRANCH}.

This is a success case, not an error.

If `OLD_HEAD` differs from `NEW_HEAD`, count and show the new commits:
```
git rev-list --count ${OLD_HEAD}..${NEW_HEAD}
```
```
git log --oneline ${OLD_HEAD}..${NEW_HEAD}
```

Report success with the exact number of new commits pulled forward and the commit summaries.

### Step 4: Diverged History

If fast-forward is not possible, explain why and inform the user. Run these commands to gather context:

```
git rev-list --count ${REMOTE}/${BRANCH}..HEAD
```

This shows how many local commits exist that are not in the remote branch. Use this to explain:

> Fast-forward not possible — local and remote histories have diverged.
> You have N local commit(s) that are not in ${REMOTE}/${BRANCH}.
> A fast-forward requires your HEAD to be a direct ancestor of the remote branch,
> but your branch has diverged with commits not present on the remote.
>
> Alternatives:
> - `/fr` — Fetch and rebase onto the remote branch (recommended — replays your commits on top of remote)
> - `git merge ${REMOTE}/${BRANCH}` — Create a merge commit
> - `git reset --hard ${REMOTE}/${BRANCH}` — Discard local commits (destructive, use with caution)

Do not perform any of these alternatives automatically.

---
name: prune
description: "Clean up local git branches whose remote tracking branch no longer exists (gone). Dry-run by default, requires --force to actually delete. Triggers on: 'prune branches', 'clean up stale branches', 'delete gone branches', 'remove merged branches', 'clean up old branches', 'prune local branches'. Anti-triggers: 'prune docker images', 'prune containers', 'prune npm cache', 'git remote prune' (without branch cleanup intent), file pruning, or any non-git-branch cleanup."
argument-hint: "[--force]"
---

# Prune Skill

Clean up local branches whose remote tracking branch is gone. Dry-run by default.

## Arguments

**$ARGUMENTS**: Optional flags.

Parse `$ARGUMENTS` for the following:

- `--force` — Actually delete stale branches instead of listing them. Without this flag, only a dry-run listing is produced.
- `--help` or `-h` — Print the help section below and stop.

## Help

When `--help` or `-h` is passed, print this man-page style help and exit:

```
USAGE
    /prune [--force]

DESCRIPTION
    Find and optionally delete local branches whose remote tracking branch
    no longer exists. Dry-run by default — lists stale branches without
    deleting them.

    Protected branches (main, master, develop, development, and the
    current branch) are NEVER deleted, even with --force.

OPTIONS
    --force     Delete stale branches (with confirmation prompt).
                Without this flag, only lists stale branches.

    --help, -h  Show this help message.

EXAMPLES
    /prune              List stale branches (dry-run)
    /prune --force      Delete stale branches (with confirmation)
```

## Variables

- **MODE**: If `--force` is present in `$ARGUMENTS`, set to `force`. Otherwise set to `dry-run`.

## Protected Branches

The following branches are NEVER deleted, even with `--force`:
- `main`
- `master`
- `develop`
- `development`
- The currently checked-out branch

## Workflow

### Step 1: Fetch with Prune

Run `git fetch --prune` to update remote tracking information and remove references to deleted remote branches.

### Step 2: Identify Stale Branches

Run `git branch -vv` and find branches whose upstream is marked as `gone`:

```bash
git branch -vv | grep ': gone]'
```

Extract the branch names from the output.

### Step 3: Filter Protected Branches

Remove any protected branches (see list above) from the stale branch list. Determine the current branch with:

```bash
git branch --show-current
```

### Step 4: Display Results

If no stale branches remain after filtering:
- Print "No stale branches found." and stop.

If all stale branches are protected:
- Print "All stale branches are protected — nothing to delete." and stop.

Otherwise, list the stale branches clearly, marking any that were filtered as protected.

### Step 5: Dry-Run vs Force

**If MODE is `dry-run`** (default):
- Display the list of stale branches that would be deleted.
- Print: "Run `/prune --force` to delete these branches."
- Stop.

**If MODE is `force`**:
- Display the list of branches that will be deleted.
- Ask the user for confirmation before proceeding: "Delete these N branches? (y/n)"
- Wait for explicit user confirmation before deleting anything.

### Step 6: Delete Branches

For each confirmed branch, attempt deletion with safe delete:

```bash
git branch -d <branch>
```

If a branch is not fully merged and `-d` fails:
- Warn the user that the branch is not fully merged.
- Offer to force-delete with `git branch -D <branch>`.
- Only force-delete if the user explicitly confirms.

### Step 7: Report Results

After all deletions are attempted, report:
- **Deleted**: branches successfully removed
- **Skipped**: branches the user chose not to force-delete
- **Protected**: branches that were excluded from deletion

## Edge Cases

- **No stale branches found**: Report cleanly and exit.
- **All stale branches are protected**: Report cleanly and exit.
- **Branch not fully merged**: Offer `git branch -D` with a clear warning. Never force-delete without user consent.
- **Not a git repository**: Detect and report an error early.

## Notes

- Dry-run is the default. No branches are deleted without `--force`.
- Even with `--force`, the user must confirm before deletion proceeds.
- Protected branches are never deleted under any circumstances.
- This skill only affects LOCAL branches. It does not delete remote branches.
- `git fetch --prune` is always run first to ensure accurate remote tracking state.

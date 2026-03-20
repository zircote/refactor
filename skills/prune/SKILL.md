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

### Step 4: Count and Categorize Results

After filtering, compute these counts:
- **total_stale**: Number of branches with gone upstream (before filtering)
- **protected_stale**: Number of stale branches that are protected (filtered out)
- **eligible**: Number of stale branches eligible for deletion (total_stale - protected_stale)

Report the count: "Found N stale branch(es)." (where N = total_stale)

Also show a brief **branch summary table** listing all local branches with their tracking status. This helps the user understand the overall state. Example format:

```
Branch Summary:
  main                    → origin/main (tracking)
  feat/old-feature        → origin/feat/old-feature [gone] ← STALE
  feat/current-work       → origin/feat/current-work (tracking, current)
```

This table makes the prune candidates visible at a glance, even when the list is empty.

### Step 5: Display Results Based on Counts

**Case A — No stale branches found** (total_stale == 0):
- Print "No stale branches found."
- If MODE is `dry-run`, ALWAYS print: "Run `/prune --force` to delete stale branches when they exist."
- If MODE is `force`, explain: "No stale branches to delete. When stale branches exist, `/prune --force` will prompt for confirmation before deleting each one with `git branch -d`, and report results."
- Stop.

**Case B — All stale branches are protected** (eligible == 0, protected_stale > 0):
- List the protected stale branches and explain they are protected.
- Print "All stale branches are protected — nothing to delete."
- Do NOT prompt for deletion confirmation since there are no eligible branches.
- Stop.

**Case C — Some eligible stale branches exist** (eligible > 0):
- List the eligible stale branches clearly.
- If any stale branches were filtered as protected, list them separately with a note that they are protected and were skipped.

### Step 6: Dry-Run vs Force (only reached in Case C)

**If MODE is `dry-run`** (default):
- Display the list of stale branches that would be deleted.
- Print: "Run `/prune --force` to delete these branches."
- Stop.

**If MODE is `force`**:
- Display the list of branches that will be deleted.
- Ask the user for explicit confirmation before proceeding: "Delete these N branches? (y/n)"
- Wait for explicit user confirmation before deleting anything.
- Do NOT delete anything without the user saying yes.

### Step 7: Delete Branches (force mode only, after user confirms)

For each confirmed branch, attempt deletion with safe delete first:

```bash
git branch -d <branch>
```

**Critical: Handle unmerged branches safely.** If `git branch -d` fails because the branch is not fully merged:
1. Warn the user clearly: "Branch `<name>` is not fully merged and cannot be safely deleted."
2. Ask the user explicitly: "Force-delete `<name>` with `git branch -D`? This cannot be undone. (y/n)"
3. Only run `git branch -D <branch>` if the user explicitly confirms with yes.
4. If the user declines, skip that branch and continue to the next.
5. **NEVER force-delete an unmerged branch without explicit per-branch user consent.**

### Step 8: Report Results

After all deletions are attempted, report:
- **Deleted**: branches successfully removed (list names)
- **Skipped**: branches the user chose not to force-delete (list names)
- **Protected**: branches that were excluded from deletion (list names)
- **Total**: summary count of each category

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

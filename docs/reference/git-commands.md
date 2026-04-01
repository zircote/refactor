---
diataxis_type: reference
diataxis_describes: git workflow commands -- syntax, flags, behavior, and error handling
---

# Git Workflow Commands Reference

The refactor plugin provides commands for common git workflows. Each command wraps `git` and `gh` CLI operations into a single, repeatable action.

## Command Overview

| Command | Purpose | Modifies Remote | Requires `gh` |
|---------|---------|-----------------|---------------|
| `/cp` | Stage, commit, and push | Yes | No |
| `/pr` | Create or manage pull requests | Yes | Yes |
| `/fr` | Fetch and rebase | No | No |
| `/ff` | Fast-forward merge | No | No |
| `/sync` | Fetch, rebase, and push | Yes | No |
| `/pr-fix` | Remediate PR review feedback | Yes | Yes |
| `/review-comments` | Triage and respond to PR comments | Yes | Yes |
| `/pr-review` | Review a pull request | Yes | Yes |
| `/pr-sweep` | Gated PR sweep: review, fix, merge | Yes | Yes |
| `/prune` | Clean up stale local branches | No | No |
| `/git-hooks` | Analyze and install git hooks | No | Partial |

---

## /cp -- Stage, Commit, and Push

Stage all changes, generate a conventional commit message, and push to the remote origin.

### Synopsis

```
/cp [commit message override]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `commit message override` | No | Use this text as the commit message instead of auto-generating one |
| `--help`, `-h`, `help` | No | Display help and exit |

### Behavior

1. **Review changes** -- runs `git status` and `git diff` to inspect modifications.
2. **Security check** -- excludes `.env`, `*.pem`, `*.key`, `credentials.json`, and files matching common secret patterns. Warns the user if detected.
3. **Generate commit message** -- if no override is provided, analyzes the diff and produces a conventional commit message (`<type>: <description>`). Types: `feat`, `fix`, `perf`, `refactor`, `docs`, `style`, `ci`, `chore`, `build`, `test`.
4. **Split commits** -- if both new files and modifications exist, splits them into separate commits.
5. **Stage files individually** -- never uses `git add -A` or `git add .`. Each file is staged by explicit path.
6. **Sync before push** -- fetches and rebases onto the upstream tracking branch if it exists and the local branch is behind.
7. **Push** -- uses `git push -u origin <branch>` for first push, `git push --force-with-lease` after rebase, or plain `git push` otherwise.

### Special Rules

- `.claude/` directory: modified markdown files use `perf:` type, new files use `feat:` type.
- Commit titles are capped at 70 characters.
- No AI attribution lines are added.

### Conflict Handling

If rebase encounters conflicts, the pipeline halts. The skill displays conflicting files and offers resolution options (resolve manually, abort, or skip commit). No push occurs until the rebase completes cleanly.

### Related

- [/sync](#sync----full-sync-cycle) -- includes push
- [/fr](#fr----fetch-and-rebase) -- fetch and rebase without push
- [How to: Git Workflows](../guides/git-workflows.md)

---

## /pr -- Create and Manage Pull Requests

Create, update, or manage GitHub pull requests using the `gh` CLI. Draft PRs are the default.

### Synopsis

```
/pr [to-branch] [--ready] [--update] [--web] [--fill] [--no-draft]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `to-branch` | No | Target branch (defaults to repo default branch) |
| `--ready` | No | Convert existing draft PR to ready for review |
| `--update` | No | Push new commits to an existing PR, optionally edit title/body |
| `--web` | No | Open PR creation in browser |
| `--fill` | No | Auto-fill title and body from commit messages |
| `--no-draft` | No | Create as ready-for-review instead of draft |
| `--help`, `-h`, `help` | No | Display help and exit |

### Workflows

The command selects a workflow based on flags:

| Flag | Workflow | Description |
|------|----------|-------------|
| `--ready` | Ready | Converts an existing draft PR to ready for review via `gh pr ready` |
| `--update` | Update | Pushes unpushed commits and optionally edits the PR title/body |
| _(default)_ | Create | Creates a new draft PR targeting the specified branch |

### Create Workflow

1. **Pre-flight** -- verifies `gh` is installed and authenticated, checks current branch is not the target branch, and checks for an existing PR.
2. **Rebase** -- fetches the target branch and rebases if behind. Halts on conflicts.
3. **Push** -- pushes the branch with `-u` for first push.
4. **Duplicate check** -- if a PR already exists for the branch, shows the existing PR and suggests `--update` instead.
5. **Generate PR info** -- analyzes commits and diff to generate a title (under 70 characters) and body with Summary, Changes, and Test Plan sections.
6. **Create** -- runs `gh pr create --base <target> --title <title> --body <body> --draft` (or `--fill`, `--web` variants).

### Natural Language Intent

The command infers flags from natural language prompts:

| User says | Equivalent flag |
|-----------|----------------|
| "skip the draft", "not a draft" | `--no-draft` |
| "update the PR", "push new commits" | `--update` |
| "mark PR ready", "ready for review" | `--ready` |
| "open in browser" | `--web` |
| "auto-fill from commits" | `--fill` |
| "PR to develop" | target branch = `develop` |

### Related

- [/pr-fix](#pr-fix----fix-pr-feedback) -- address review comments
- [/review-comments](#review-comments----triage-pr-comments) -- triage and respond to comments
- [/pr-review](#pr-review----review-a-pull-request) -- review a PR
- [How to: Git Workflows](../guides/git-workflows.md)

---

## /fr -- Fetch and Rebase

Fetch from a remote and rebase the current branch onto the remote tracking branch.

### Synopsis

```
/fr [remote] [branch]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `remote` | No | Remote name (default: `origin`) |
| `branch` | No | Branch to rebase onto (default: current branch's upstream) |
| `--help`, `-h`, `help` | No | Display help and exit |

### Pre-flight Checks

1. **Uncommitted changes** -- if detected, offers three options: stash and continue, abort, or proceed anyway.
2. **Rebase in progress** -- if `.git/rebase-merge` or `.git/rebase-apply` exists, aborts with guidance.
3. **Target branch resolution** -- if no branch argument is provided, resolves from `@{u}`. Aborts if no upstream is configured.

### Behavior

1. **Fetch** -- runs `git fetch <remote>`.
2. **Show divergence** -- displays commits on the remote branch not on the local branch, and local commits that will be replayed.
3. **Rebase** -- runs `git rebase <remote>/<branch>`.
4. **Report** -- shows the result and number of commits replayed. Pops any auto-stash.

### Safety Rules

- Does NOT push. For push, use [/sync](#sync----full-sync-cycle).
- Does NOT force-push.
- Does NOT modify or create branches.

### Conflict Handling

Lists conflicted files and explains resolution commands (`git add <files> && git rebase --continue` or `git rebase --abort`). Reminds about stash if one was auto-created.

### Related

- [/ff](#ff----fast-forward-merge) -- fast-forward only (no rebase)
- [/sync](#sync----full-sync-cycle) -- fetch, rebase, and push
- [How to: Git Workflows](../guides/git-workflows.md)

---

## /ff -- Fast-Forward Merge

Fast-forward the current branch from its remote tracking branch. No merge commits, no history rewriting.

### Synopsis

```
/ff [remote] [branch]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `remote` | No | Remote name (default: `origin`) |
| `branch` | No | Branch to fast-forward from (default: current branch's upstream) |
| `--help`, `-h`, `help` | No | Display help and exit |

### Pre-flight Checks

1. **Working directory** -- must be clean. If uncommitted changes exist, the command stops and asks you to commit or stash first.
2. **Target branch resolution** -- if no branch argument is provided, resolves from the upstream tracking reference.

### Behavior

1. **Fetch** -- runs `git fetch <remote>`.
2. **Check feasibility** -- runs `git merge-base --is-ancestor HEAD <remote>/<branch>`. If HEAD is not an ancestor of the remote branch, fast-forward is not possible.
3. **Fast-forward** -- runs `git merge --ff-only <remote>/<branch>`. Reports the number of new commits pulled forward.

### Diverged History

If fast-forward is not possible (local commits exist that are not in the remote branch), the command explains why and suggests alternatives:

- `/fr` -- fetch and rebase (recommended)
- `git merge <remote>/<branch>` -- create a merge commit
- `git reset --hard <remote>/<branch>` -- discard local commits (destructive)

None of these alternatives are performed automatically.

### Related

- [/fr](#fr----fetch-and-rebase) -- rebase when fast-forward is not possible
- [/sync](#sync----full-sync-cycle) -- full sync cycle
- [How to: Git Workflows](../guides/git-workflows.md)

---

## /sync -- Full Sync Cycle

Fetch, rebase, and push in one command. Extends `/fr` by adding a confirmed push step.

### Synopsis

```
/sync [remote] [branch]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `remote` | No | Remote name (default: `origin`) |
| `branch` | No | Branch to rebase onto (default: current branch's upstream) |
| `--help`, `-h`, `help` | No | Display help and exit |

### Pre-flight Checks

1. **Uncommitted changes** -- offers stash/abort/proceed options.
2. **Rebase in progress** -- aborts with guidance.
3. **Target branch resolution** -- resolves from upstream or falls back to current branch name.

### Behavior

1. **Fetch** -- runs `git fetch <remote>`. Reports fetch results.
2. **Show divergence** -- displays commits behind and commits ahead.
3. **Rebase** -- if upstream commits exist, runs `git rebase <remote>/<branch>`. Skips if already up to date.
4. **Confirm push** -- shows commits to push and asks for explicit confirmation. Skips push if nothing to push.
5. **Push** -- uses `git push --force-with-lease` after rebase, plain `git push` otherwise. Never uses bare `--force` unless explicitly requested.
6. **Report** -- shows final status: commits fetched/rebased, commits pushed, current branch and tracking status.

### Conflict Handling

If rebase encounters conflicts, the sync pipeline halts. No push occurs. Resolution options are the same as [/fr](#fr----fetch-and-rebase).

### Related

- [/fr](#fr----fetch-and-rebase) -- fetch and rebase without push
- [/ff](#ff----fast-forward-merge) -- fast-forward only
- [How to: Git Workflows](../guides/git-workflows.md)

---

## /pr-fix -- Fix PR Feedback

Fetch review comments, triage by confidence, apply fixes, rebase, commit, reply to every comment, push, and resolve threads. Supports batch processing of multiple PRs.

### Synopsis

```
/pr-fix [pr-number...] [--interactive] [--confidence=N] [--skip-rebase]
        [--skip-ci] [--no-wait-ci] [--dry-run] [--force]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `pr-number` | No | One or more PR numbers (space-separated). Range syntax `N..M` supported. If omitted, processes ALL open PRs. |
| `--interactive` | No | Prompt for sub-threshold fixes instead of skipping |
| `--confidence=N` | No | Confidence threshold 0--100 (default: 95) |
| `--skip-rebase` | No | Skip the rebase phase |
| `--skip-ci` | No | Skip CI status checking entirely |
| `--no-wait-ci` | No | Do not wait for CI after push (check current status only) |
| `--dry-run` | No | Show remediation plan without executing changes |
| `--force` | No | Push with `--force-with-lease` |
| `--help`, `-h`, `help` | No | Display help and exit |

### Core Guarantees

- **Every comment gets a reply** -- fixed, explained, or acknowledged.
- **Every thread gets resolved** -- after push, all addressed threads are resolved via GraphQL.
- **CI is advisory** -- CI status is waited on by default and reported, but does not block the workflow.
- **Copilot comments are first-class** -- GitHub Copilot review comments receive the same treatment as human comments.

### Confidence Scoring

Each comment is scored on four factors:

| Factor | Weight |
|--------|--------|
| Technical Accuracy | 35% |
| Code Evidence | 30% |
| Clear Remediation | 20% |
| Scope Impact | 15% |

Fixes at or above the threshold are auto-accepted. Below-threshold fixes are skipped in auto mode (default) or prompted in `--interactive` mode.

### Comment Dispositions

| Disposition | Reply Template |
|-------------|---------------|
| Fixed | `Fixed in <sha>.` |
| Fixed with Modification | `Addressed in <sha>. <explanation>.` |
| Rejected | `Reviewed -- not applying because <reason>.` |
| Question Response | `<answer>.` |
| Acknowledged | `Thanks for the review!` |
| Skipped (Auto) | `Below confidence threshold (<N>%) -- flagging for manual review.` |
| Deferred | `Valid point -- tracking as follow-up.` |

### Batch Processing

When multiple PRs are provided (or none, meaning all open PRs), each PR is processed sequentially through all phases. A batch summary is generated at the end.

### Related

- [/pr](#pr----create-and-manage-pull-requests) -- create PRs
- [/review-comments](#review-comments----triage-pr-comments) -- triage comments without fixing
- [How to: Git Workflows](../guides/git-workflows.md)

---

## /review-comments -- Triage PR Comments

Fetch, assess, remediate, respond to, and resolve PR review comment threads. Includes per-dimension confidence scoring.

### Synopsis

```
/review-comments [pr-number] [--auto] [--interactive] [--confidence=N]
                 [--dry-run] [--score-only]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `pr-number` | No | PR number (inferred from current branch if omitted) |
| `--auto` | No | Non-interactive mode; auto-accept comments meeting threshold |
| `--interactive` | No | Interactive mode (default); prompt for each comment below threshold |
| `--confidence=N` | No | Minimum confidence 0--100 to auto-accept (default: 85) |
| `--dry-run` | No | Show proposed actions without executing |
| `--score-only` | No | Fetch, categorize, and score comments; do not remediate or reply |
| `--help`, `-h`, `help` | No | Display help and exit |

### Scoring

Each comment is scored on four dimensions:

| Dimension | Weight |
|-----------|--------|
| Technical Accuracy | 40% |
| Relevance | 25% |
| Impact | 20% |
| Feasibility | 15% |

### Classification

| Score Range | Classification | Action |
|-------------|---------------|--------|
| >= 90 | Strong Accept | Remediate automatically |
| 75--89 | Accept | Remediate (prompt in interactive) |
| 50--74 | Uncertain | Prompt or reject |
| 25--49 | Likely Reject | Prompt or reject |
| < 25 | Strong Reject | Reject automatically |

### Per-Dimension Flags

Comments with notably low individual scores are flagged regardless of composite score:

- Technical Accuracy < 50: reviewer claim may be wrong
- Relevance < 40: comment may not be relevant to this PR
- Impact < 30: issue is likely cosmetic

### Thread Resolution

Threads for accepted, acknowledged, and question-response dispositions are resolved via GraphQL mutation. Rejected and skipped threads remain open.

### Related

- [/pr-fix](#pr-fix----fix-pr-feedback) -- full remediation pipeline
- [/pr-review](#pr-review----review-a-pull-request) -- review a PR

---

## /pr-review -- Review a Pull Request

Perform a comprehensive pull request code review that scales strategy by PR size. Submits findings as a single batched GitHub review.

### Synopsis

```
/pr-review <pr-number-or-url> [--auto-approve-trivial] [--severity=LEVEL]
           [--skip-hygiene] [--dry-run]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `pr-number-or-url` | No | PR number or GitHub URL (inferred from current branch if omitted) |
| `--auto-approve-trivial` | No | Auto-approve docs-only, typo-fix, and dependency-bump PRs from trusted bots if CI passes |
| `--severity=LEVEL` | No | Minimum severity to report: `low` (default), `medium`, or `high` |
| `--skip-hygiene` | No | Skip PR hygiene checks (title, description, commits, scope, CI) |
| `--dry-run` | No | Print the review without posting to GitHub |
| `--help`, `-h`, `help` | No | Display help and exit |

### Size-Based Strategy

| PR Size | Lines Changed | Strategy |
|---------|---------------|----------|
| Small | < 100 | Direct review |
| Medium | 100--500 | Direct review |
| Large | 500--1500 | Swarm-orchestrated parallel specialists |
| Very Large | 1500+ | Swarm-orchestrated + decomposition advice |

### Review Phases

1. **PR Hygiene** -- title, description, commit quality, secrets scan, scope, CI status, test coverage.
2. **Code Review** -- correctness, security (OWASP-informed), performance, maintainability, API design, error handling, concurrency.
3. **Synthesis** -- classify findings (must-fix, should-fix, nit, question, praise), compose review, submit as single batched GitHub review.

### Finding Classifications

| Classification | Criteria | Review Impact |
|----------------|----------|---------------|
| must-fix | Bugs, security, data loss risk | REQUEST_CHANGES |
| should-fix | Performance, missing error handling | Non-blocking |
| nit | Style, naming, minor cleanup | Optional |
| question | Clarification needed | Information request |
| praise | Well-written code, good patterns | Always included |

### Verdict Logic

- **REQUEST_CHANGES** if any must-fix findings, failing CI, or secrets detected.
- **APPROVE** if no must-fix findings and PR is generally sound.
- **COMMENT** if only should-fix/nit findings.

### Related

- [/pr-fix](#pr-fix----fix-pr-feedback) -- remediate review feedback
- [/review-comments](#review-comments----triage-pr-comments) -- process review comments
- [/pr](#pr----create-and-manage-pull-requests) -- create PRs

---

## /pr-sweep -- Gated PR Sweep

Drive every eligible PR through a strict quality pipeline -- Copilot review, comment remediation, CI green, conflict-free rebase -- and auto-merge those that pass all gates.

### Synopsis

```
/pr-sweep [pr-number...] [--interactive] [--confidence=N] [--no-merge]
          [--merge-method=METHOD] [--skip-rebase] [--dry-run] [--force]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `pr-number` | No | One or more PR numbers (range syntax `N..M` supported). If omitted, all open PRs. |
| `--interactive` | No | Prompt for sub-threshold fixes |
| `--confidence=N` | No | Confidence threshold 0--100 (default: 95) |
| `--no-merge` | No | Drive to readiness but skip the merge step |
| `--merge-method=METHOD` | No | Merge strategy: `squash` (default), `merge`, or `rebase` |
| `--skip-rebase` | No | Skip the rebase phase |
| `--dry-run` | No | Show sweep plan without mutations |
| `--force` | No | Push with `--force-with-lease` |
| `--help`, `-h`, `help` | No | Display help and exit |

### /pr-sweep vs /pr-fix

| Aspect | /pr-fix | /pr-sweep |
|--------|---------|-----------|
| CI | Advisory (never blocks) | Hard gate (must pass) |
| Copilot review | Handles existing comments | Requests review if missing, waits |
| Merge | Never | Auto-merges when all gates pass |
| Retry | No | One retry per gate failure |
| Draft PRs | Processes | Skips |

### Quality Gates (Strict)

1. **Copilot review** -- requested if missing, waited on (10 min timeout).
2. **Comment remediation** -- all comments replied, all threads resolved.
3. **Rebase** -- branch must be conflict-free against base.
4. **CI green** -- hard gate with one retry (empty commit + re-push).
5. **Final verification** -- 100% reply rate, all threads resolved, CI green, branch up-to-date.

### Related

- [/pr-fix](#pr-fix----fix-pr-feedback) -- fix comments without merge
- [/pr](#pr----create-and-manage-pull-requests) -- create PRs
- [How to: Git Workflows](../guides/git-workflows.md)

---

## /prune -- Clean Up Stale Branches

Find and optionally delete local branches whose remote tracking branch no longer exists. Dry-run by default.

### Synopsis

```
/prune [--force]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--force` | No | Delete stale branches (with confirmation prompt). Without this, only lists them. |
| `--help`, `-h` | No | Display help and exit |

### Protected Branches

These branches are never deleted, even with `--force`:

- `main`
- `master`
- `develop`
- `development`
- The currently checked-out branch

### Behavior

1. **Fetch with prune** -- runs `git fetch --prune` to update remote tracking info.
2. **Identify stale** -- finds branches with `[gone]` upstream via `git branch -vv`.
3. **Filter protected** -- removes protected branches from the candidate list.
4. **Display** -- shows a branch summary table with tracking status.

### Force Mode

With `--force`, the command asks for explicit confirmation before deleting. Uses safe delete (`git branch -d`) first. If a branch is not fully merged, asks per-branch whether to force-delete (`git branch -D`).

### Related

- [How to: Git Workflows](../guides/git-workflows.md)

---

## /git-hooks -- Intelligent Hook Provisioning

Analyze a project's languages, tooling, and CI/CD configuration to recommend and install tailored git hooks.

### Synopsis

```
/git-hooks [--auto] [--dry-run]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--auto` | No | Non-interactive. Detect and apply best-practice defaults. |
| `--dry-run` | No | Show what would be installed without writing anything. |
| `--help`, `-h` | No | Display help and exit |

### Modes

| Mode | Behavior |
|------|----------|
| Interactive (default) | Analyze, present findings, elicit preferences, implement |
| Auto (`--auto`) | Analyze, apply defaults, implement, report |
| Dry-run (`--dry-run`) | Analyze, report. Combinable with `--auto`. |

### Hook Manager Detection

Detects and works within existing hook managers:

- **Husky** -- `.husky/` directory
- **pre-commit** -- `.pre-commit-config.yaml`
- **Lefthook** -- `lefthook.yml`
- **lint-staged** -- `.lintstagedrc*` or `package.json` key
- **simple-git-hooks** -- `package.json` key

If no manager exists, recommends one based on the project's primary stack (Husky for JS/TS, pre-commit for Python, Lefthook for Go/Rust/monorepos).

### Recommendation Tiers

| Tier | Description | Auto-Mode Behavior |
|------|-------------|-------------------|
| Tier 1 | High confidence (lint, format, secrets, commit validation) | Installed if tool is configured |
| Tier 2 | Recommended (type check, test on push, branch naming) | Installed if tool is configured |
| Tier 3 | Situational (build verify, doc lint, API schema) | Skipped |

### Constraints

- Pre-commit hooks must complete in < 5 seconds.
- Pre-push hooks must complete in < 30 seconds.
- Never installs a competing hook manager.
- Never introduces new tools the project does not already use (in auto mode).

### Related

- [Configuration Reference](configuration.md) -- project configuration

---

## Error Handling

All commands follow these error handling patterns:

| Error | Behavior |
|-------|----------|
| `gh` CLI not installed | Stops with installation link |
| `gh` not authenticated | Stops with `gh auth login` instruction |
| Not a git repository | Stops with clear error |
| Rebase conflicts | Halts pipeline, shows conflicts, offers resolution options |
| Push rejected | Reports error, suggests resolution (re-sync or force) |
| Network failure | Reports the underlying error from `git` or `gh` |
| No changes to commit | Reports cleanly and exits |

## Related Documentation

- [How to: Git Workflows](../guides/git-workflows.md) -- step-by-step guides for common scenarios
- [Configuration Reference](configuration.md) -- project settings
- [Agents Reference](agents.md) -- specialist agent specifications

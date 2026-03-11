---
diataxis_type: how-to
diataxis_goal: Configure the refactor plugin to automatically commit, create PRs, and publish reports
---

# How to Configure Commit Strategies

## Overview

This guide shows you how to set up automatic commits, pull requests, and report publishing so the refactor plugin handles your git workflow end-to-end.

## Prerequisites

- Refactor plugin installed and working (see [Tutorial](../tutorial.md))
- Git repository with a remote configured
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated (for PR and publishing features)

## Steps

### 1. Choose a commit strategy

Edit `.claude/refactor.config.json` and set `commitStrategy`:

**Commit after each iteration** — useful for tracking incremental progress:
```json
{
  "postRefactor": {
    "commitStrategy": "per-iteration"
  }
}
```
Each iteration produces a commit: `refactor(iteration 1/3): {summary}`

**Single commit when done** — cleaner git history:
```json
{
  "postRefactor": {
    "commitStrategy": "single-final"
  }
}
```
One commit at the end: `refactor: {scope} — clean code 8/10, architecture 9/10`

When using `--focus`, commit messages include the focus area: `refactor(security): {scope} — security posture 8/10`

### 2. Enable pull request creation

Set `createPR` to `true`. Use `prDraft` to control whether the PR opens as a draft:

```json
{
  "postRefactor": {
    "commitStrategy": "single-final",
    "createPR": true,
    "prDraft": true
  }
}
```

If you are on `main`, `master`, or `develop`, the plugin creates a `refactor/{scope}-{date}` branch automatically.

### 3. Configure report publishing

To publish the quality report as a GitHub issue:
```json
{
  "postRefactor": {
    "publishReport": "github-issue"
  }
}
```

To publish as a GitHub Discussion:
```json
{
  "postRefactor": {
    "publishReport": "github-discussion",
    "discussionCategory": "Engineering"
  }
}
```

To publish to a different repository (e.g., a central tracking repo):
```json
{
  "postRefactor": {
    "publishReport": "github-issue",
    "reportRepository": "myorg/engineering-reports"
  }
}
```

### 4. Run the refactor

```bash
/refactor src/
```

The plugin will commit, push, create the PR, and publish the report according to your configuration.

## Verification

After the refactor completes:
- Check `git log` to verify commits were created with the expected format
- Check your GitHub repository for the PR (if enabled)
- Check GitHub Issues or Discussions for the published report (if enabled)

## Troubleshooting

If commits fail, ensure your working directory is a git repository with at least one prior commit. If PR creation fails, verify `gh auth status` shows you are authenticated. If report publishing fails, verify the target repository exists and you have write access.

All GitHub operations are non-blocking — failures log a warning but do not stop the refactor.

## Related

- [Configuration Reference](../reference/configuration.md) — full schema and field details
- [Tutorial: Your First Refactor](../tutorial.md) — getting started

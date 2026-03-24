# Copilot Coding Agent Mechanics Reference

Quick-reference for verified Copilot coding agent behavior (as of March 2026).
Consult this when writing or auditing instructions to avoid recommending things
that conflict with how the agent actually works.

> **STALENESS WARNING**: GitHub ships Copilot agent updates frequently.
> Before relying on any specific behavior documented here, verify against
> current GitHub docs using web search or `/version-guard` for action versions.
> When in doubt, check: https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent

## Branch & PR Model

- Creates and pushes ONLY to `copilot/` prefixed branches
- Opens **draft PRs** — cannot mark ready, approve, or merge
- One PR per task assignment
- For existing PRs: creates a **child PR** using your branch as base
- For its own PRs: pushes directly to the same `copilot/` branch

## Session Lifecycle

- Sessions timeout after **1 hour**
- Stuck sessions: unassign and reassign Copilot
- Responds to `@copilot` mentions from users with **write access only**
- Only responds in **open** PRs (ignores merged/closed)
- Adds 👀 reaction to acknowledge, then works

## Instruction Files

| File | Scope | Format | Notes |
|------|-------|--------|-------|
| `.github/copilot-instructions.md` | Repo-wide | Plain markdown, no frontmatter | ~2 pages max, not task-specific |
| `.github/instructions/*.instructions.md` | Path-specific | YAML frontmatter with `applyTo` glob | Supports `excludeAgent` |
| `AGENTS.md` | Directory-scoped | Plain markdown | Experimental, off by default in CLI |

### Path-specific frontmatter schema

```yaml
---
applyTo: "**/*.py"              # required: glob pattern
excludeAgent: "code-review"     # optional: "code-review" or "coding-agent"
---
```

### Instruction precedence (highest → lowest)

1. Personal instructions (user-level settings)
2. Repository instructions (`.github/copilot-instructions.md`)
3. Organization instructions

All applicable instructions are **concatenated** and provided simultaneously.

## Environment Setup

- File: `.github/workflows/copilot-setup-steps.yml`
- Job MUST be named `copilot-setup-steps` (exact match required)
- Runs before Copilot starts work
- Only Ubuntu x64 and Windows 64-bit runners supported
- Max timeout: 59 minutes
- Must be on **default branch** to activate

## Workflow Approval

- **Default**: Workflows require manual "Approve and run" click
- **Toggle** (March 2026): Settings > Copilot > Coding agent > "Require approval for workflow runs"
- When disabled, CI runs automatically on Copilot PRs

## Known Limitations

- **Content exclusions NOT respected** — Copilot sees and can modify excluded files
- **Sometimes loses context** mid-task on complex, multi-step work
- **Internal system prompts** take priority over custom instructions
- **Instructions may be truncated** if document is too long
- Cannot make cross-repo changes
- Maximum image size: 3.00 MiB
- Read-only access (writes via git commits only)
- Sandboxed environment with firewall-controlled internet

## What Copilot Ignores

- Overly abstract instructions ("follow best practices")
- Negative-only instructions ("don't do X") without alternatives
- Instructions buried deep in long documents
- Contradictory instructions (picks one arbitrarily)
- Task-specific instructions in repo-wide file

## What Works Well

- Specific, actionable instructions with examples
- Positive framing ("Use X for Y" rather than "Don't use Z")
- Front-loaded critical rules (first ~50 lines are most reliable)
- Exact commands (`make check`, not "run the tests")
- Structured sections with clear headers
- Example commit messages, PR templates, code patterns

## Sources

- [Adding custom instructions - GitHub Docs](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [Best practices for tasks - GitHub Docs](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks)
- [About coding agent - GitHub Docs](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)
- [Troubleshooting - GitHub Docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/troubleshoot-coding-agent)
- [Onboarding guide - GitHub Blog](https://github.blog/ai-and-ml/github-copilot/onboarding-your-ai-peer-programmer-setting-up-github-copilot-coding-agent-for-success/)
- [Auto-approve workflow discussion](https://github.com/orgs/community/discussions/162826)

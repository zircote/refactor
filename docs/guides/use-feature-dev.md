---
diataxis_type: how-to
diataxis_goal: Use the /feature-dev skill to build new features through guided, multi-agent development
---

# How to Use Feature Development

## Overview

This guide shows you how to use `/feature-dev` effectively across different scenarios -- from writing good feature descriptions to navigating approval gates and tuning agent counts for your project.

## Prerequisites

- Refactor plugin v3.1.0+ installed and working (see [Tutorial](../tutorial.md))
- Familiarity with your project's directory structure
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated (if using `createPR`)

## Steps

### 1. Write effective feature descriptions

The quality of your description determines how many elicitation questions you receive. Be specific about the WHAT and WHY; leave the HOW to the architects.

**Detailed description** -- fewer questions, faster start:

```bash
/feature-dev "Add a webhook delivery system that POSTs JSON payloads to user-configured URLs when events fire. Support retry with exponential backoff, HMAC-SHA256 signature verification, and a delivery log viewable in the admin UI. Must integrate with the existing event bus in src/events/."
```

**Minimal description** -- works, but expect 8-15 clarifying questions:

```bash
/feature-dev "add webhooks"
```

Include these when you have them: the problem being solved, who uses the feature, integration points with existing code, and any hard constraints (performance, backward compatibility, platform support). Skip implementation details -- those are resolved during architecture design.

### 2. Navigate the elicitation phase

Phase 1 uses a 95% confidence protocol. The skill asks only about gaps in your description, so thorough descriptions get fewer questions.

**Answer efficiently**: Group related answers together. If a question has sub-parts, address all of them in one response rather than waiting for follow-ups.

**Defer design questions**: If asked something that feels like an implementation detail ("Should we use a queue or direct HTTP calls?"), reply with "defer to architecture" -- the skill will route it to the architect agents in Phase 4.

**Skip remaining questions**: If the skill is asking about edge cases you consider low-priority, say "proceed" to accept the current understanding and move on. The skill caps elicitation at 3 rounds regardless.

**After exploration (Phase 3)**: A second round of questions may appear based on what the explorer agents found in your codebase. These are about integration specifics, not requirements. Answer them or reply "whatever you think is best" -- the skill will provide a recommendation and ask for confirmation.

### 3. Choose between architecture proposals

Phase 4 presents multiple designs, each from a different philosophy:

- **Minimal changes**: Smallest diff, maximum reuse of existing code
- **Clean architecture**: Best long-term maintainability, proper abstractions
- **Pragmatic balance**: Practical trade-offs between speed and quality

When evaluating proposals, focus on:

1. **Diff size** -- How many files are created vs modified? Smaller diffs are easier to review.
2. **Convention alignment** -- Does the proposal follow patterns already in your codebase?
3. **Future cost** -- Will you need to refactor this immediately, or does it hold up?
4. **Test surface** -- Is the design easy to test, or does it require complex mocking?

The skill presents a recommendation with reasoning. You can accept it, pick a different option, or ask for a hybrid ("Use approach 2 but with the error handling from approach 1").

### 4. Handle the quality review phase

Phase 6 spawns parallel reviewers focused on simplicity/DRY, bugs/correctness, and conventions/abstractions. Findings are presented grouped by severity with three options:

**"Fix critical issues now"** -- Address only high-severity findings (bugs, security issues, broken integrations). Use this when you want to ship quickly and handle polish later.

**"Fix all issues"** -- The feature-code agent addresses every finding. Use this for production-critical features where you want clean code from the start.

**"Proceed as-is"** -- Accept the implementation without changes. Use this when review findings are minor style preferences or when you plan to iterate.

After fixes, the test suite runs again automatically. If tests fail after 3 fix attempts, the skill asks you for guidance rather than looping.

### 5. Configure agent counts and behavior

Edit `.claude/refactor.config.json` to tune the `featureDev` section:

```json
{
  "version": "3.1",
  "featureDev": {
    "explorerCount": 3,
    "architectCount": 3,
    "reviewerCount": 3,
    "commitStrategy": "single-final",
    "createPR": false,
    "prDraft": true
  }
}
```

**Agent counts** control how many parallel instances spawn per phase:

| Setting | Default | Effect |
|---------|---------|--------|
| `explorerCount` | 3 | Parallel codebase explorers with different focus areas |
| `architectCount` | 3 | Parallel architecture proposals with different philosophies |
| `reviewerCount` | 3 | Parallel reviewers with different quality lenses |

**Commit and PR settings**:

| Setting | Default | Effect |
|---------|---------|--------|
| `commitStrategy` | `"single-final"` | One commit after all phases complete |
| `createPR` | `false` | Automatically create a pull request when done |
| `prDraft` | `true` | Open the PR as a draft (requires `createPR: true`) |

Higher agent counts produce more diverse exploration and proposals but consume more resources. Lower counts finish faster.

### 6. Scale for simple vs complex features

The skill automatically scales agent counts based on feature complexity, even if your config sets higher defaults:

**Simple features** (single endpoint, clear integration, trivial logic):

```bash
/feature-dev "Add a health check endpoint at GET /healthz that returns 200 with {status: ok}"
```

The skill detects high initial confidence (90%+), skips most elicitation, and scales down to 1 explorer, 1 architect, and 1-2 reviewers. Fast turnaround, minimal overhead.

**Medium features** (multiple components, some integration complexity):

```bash
/feature-dev "Add rate limiting middleware that uses a sliding window algorithm, configurable per-route, with Redis backing for distributed deployments"
```

Scales to 2 explorers, 2 architects, 2-3 reviewers. Enough diversity to surface trade-offs without over-exploring.

**Complex features** (cross-cutting, multiple systems, significant design decisions):

```bash
/feature-dev "Add a plugin system that allows third-party extensions to register custom event handlers, UI components, and API routes with sandboxed execution and a permission model"
```

Uses full configured counts. Multiple explorers map different subsystems, multiple architects propose genuinely different approaches, and multiple reviewers catch issues across the integration surface.

You do not need to set complexity manually -- the skill infers it from your description and the elicitation results.

## Related

- [Configuration Reference](../reference/configuration.md) -- full config schema and field details
- [How to Configure Commit Strategies](configure-commits.md) -- commit and PR options
- [How to Scope Refactoring](scope-refactoring.md) -- similar scoping principles apply to feature-dev
- [Troubleshooting](troubleshooting.md) -- when agents time out or tests fail repeatedly

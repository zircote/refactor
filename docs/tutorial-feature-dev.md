---
diataxis_type: tutorial
diataxis_learning_goals:
  - Run the /feature-dev skill to build a new feature end-to-end
  - Understand the 95% confidence elicitation protocol
  - Navigate the interactive approval gates
  - Observe multi-instance agent spawning and blackboard context sharing
  - Choose between competing architecture designs
---

# Tutorial: Building a Feature with /feature-dev

In this tutorial, we will use the `/feature-dev` skill to add a webhook notification system to a project. By the end, you will understand the seven-phase workflow, how parallel agents collaborate through a shared blackboard, and where your input steers the process.

## What you'll learn

- How `/feature-dev` differs from `/refactor`
- How the elicitation protocol adapts to the detail you provide
- How parallel agent instances explore, design, and review from different perspectives
- How to pick an architecture from competing proposals
- Where the five interactive approval gates occur and what they expect from you

## Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) CLI installed
- The refactor plugin (v4.0.0+) loaded via `--plugin-dir`
- A git repository with source code (this tutorial uses a Node.js API server as the example)
- Git installed and available on your PATH
- (Optional) [GitHub CLI](https://cli.github.com/) (`gh`) for the PR creation step

## Steps

### Step 1: Start with a clear feature request

Navigate to your project and invoke the skill with a description of what you want to build:

```
/feature-dev add a webhook notification system that fires HTTP POST callbacks when key events occur
```

The more detail you provide up front, the faster the elicitation phase completes. A vague request like `/feature-dev add webhooks` will trigger more questions; a thorough request moves quickly.

### Step 2: Answer the elicitation questions (Phase 1)

The skill assesses its confidence that it understands your feature. Because our request is moderately detailed, expect 3-5 targeted questions. You will see something like:

```
I have ~75% confidence in the feature requirements. A few questions before we proceed:

1. Which events should trigger webhooks? (e.g., user.created, order.completed, payment.failed)
2. Should webhook delivery include retry logic for failed deliveries? If so, how many retries?
3. Do you need a management UI or is API-only registration sufficient?
4. Are there authentication requirements for outgoing webhook payloads (e.g., HMAC signatures)?
```

Answer naturally. The skill re-assesses after each response and stops asking once it reaches 95% confidence or after three rounds. When satisfied, it writes a structured feature spec to the shared blackboard and moves on.

### Step 3: Watch the codebase exploration (Phase 2)

Three code-explorer agents spawn in parallel, each with a different focus:

- **Explorer 1** traces existing event-handling patterns in your codebase
- **Explorer 2** maps your module architecture, middleware stack, and data layer
- **Explorer 3** analyzes integration points, configuration patterns, and test conventions

You will see progress messages as each explorer completes. The team lead consolidates their findings and presents a summary:

```
Exploration complete. Key findings:

- Events: The project uses an EventEmitter in src/events/bus.ts with 12 existing event types
- Data layer: Sequelize ORM with migrations in db/migrations/
- Config: Environment-based config in src/config/ using convict
- Tests: Jest with fixtures in __tests__/, ~78% coverage
- Patterns: Repository pattern for data access, middleware chain for HTTP
```

This summary helps you verify the agents understood your codebase correctly before architecture begins.

### Step 4: Clarify post-exploration ambiguities (Phase 3)

After seeing the codebase, the skill may surface new questions that were not obvious before:

```
The codebase exploration revealed a few integration questions:

1. The existing EventEmitter uses synchronous listeners. Should webhooks
   be dispatched asynchronously (non-blocking) or synchronously (blocking the event)?
2. There are two config patterns: convict schemas and plain env vars.
   Which should the webhook config follow?
```

If the codebase is straightforward, the skill may skip this phase entirely with a note: "No additional clarifications needed."

### Step 5: Choose an architecture (Phase 4)

Three architect agents design competing approaches. Each brings a different philosophy:

- **Architect 1 (Minimal)**: Reuse the existing EventEmitter, add a `WebhookListener` class, store registrations in a new DB table
- **Architect 2 (Clean)**: Introduce a dedicated `NotificationService` abstraction layer, queue-based dispatch, separate webhook domain module
- **Architect 3 (Pragmatic)**: Extend EventEmitter with an async dispatch hook, add a lightweight retry queue using the existing job runner

The skill presents a comparison with trade-offs and its recommendation:

```
Recommendation: Approach 3 (Pragmatic)
- Leverages the existing job runner for retries (no new infrastructure)
- Async dispatch keeps event processing non-blocking
- ~40% less code than Approach 2 with similar reliability

Which approach would you like to proceed with? (1, 2, or 3)
```

Pick the one that fits your project. You can also ask for a hybrid: "Use approach 3 but with the separate domain module from approach 2."

### Step 6: Approve and watch implementation (Phase 5)

Before writing code, the skill asks for explicit confirmation:

```
Ready to implement using the Pragmatic architecture. This will:
- Create 4 new files (model, service, listener, migration)
- Modify 2 existing files (event bus, config schema)
- Add ~350 lines of code

Proceed? (yes/no)
```

After approval, the `feature-code` agent implements the design while the `refactor-test` agent writes tests and runs the full suite. If tests fail, the agents coordinate fixes automatically (up to three attempts before asking you).

### Step 7: Review the quality assessment (Phase 6)

Three code-reviewer agents examine the implementation from different angles:

- **Reviewer 1** focuses on simplicity, DRY principles, and code elegance
- **Reviewer 2** focuses on bugs, edge cases, and functional correctness
- **Reviewer 3** focuses on convention adherence and abstraction quality

The skill consolidates their findings:

```
Quality review complete. Findings:

Critical (0):
  None

Moderate (2):
  - [Reviewer 2] Missing timeout on outgoing HTTP requests in WebhookDispatcher
  - [Reviewer 3] Retry delay should use exponential backoff, not fixed interval

Minor (1):
  - [Reviewer 1] WebhookRegistration model has an unused `metadata` field

Recommendation: Fix the 2 moderate issues before finalizing.
Options: (a) Fix critical+moderate, (b) Fix all, (c) Proceed as-is
```

Choose your preference. If you select (a) or (b), the feature-code agent applies fixes and tests run again.

### Step 8: Finalize (Phase 7)

The skill commits the changes (if configured) and presents a summary:

```
Feature development complete!

Summary:
- Feature: Webhook notification system
- Architecture: Pragmatic (async dispatch + job runner retries)
- Files created: 4
- Files modified: 2
- Tests: 12 new, all passing
- Review: 2 moderate issues fixed, 1 minor deferred

Key decisions made:
- Async dispatch via existing job runner (avoids new infrastructure)
- HMAC-SHA256 payload signing with per-registration secrets
- Exponential backoff: 3 retries at 10s, 60s, 300s intervals
```

Review the changes with `git diff` or `git log`. If you chose not to auto-commit, stage and commit manually.

## What you've accomplished

You have:

- Used the 95% confidence elicitation protocol to define a feature precisely
- Observed three parallel code-explorers mapping your codebase from different angles
- Resolved post-exploration ambiguities through the clarifying questions gate
- Chosen between three competing architecture designs with different trade-offs
- Watched an implementation agent build the feature following the approved blueprint
- Reviewed consolidated findings from three quality-focused reviewers
- Navigated all five interactive approval gates in the workflow

## /refactor vs /feature-dev: when to use which

| Use `/refactor` when... | Use `/feature-dev` when... |
|---|---|
| Improving existing code quality | Building something that does not exist yet |
| Restructuring without changing behavior | Adding new functionality or capabilities |
| Fixing code smells, security issues | Implementing a new endpoint, service, or module |

## Next steps

- [Tutorial: Your First Refactor](tutorial.md) — learn the /refactor workflow
- [Configuration Reference](reference/configuration.md) — customize agent counts, commit strategy, and PR settings in `featureDev` config
- [Agent Reference](reference/agents.md) — details on each specialist agent's role
- [Architecture: Swarm Orchestration Design](explanation/architecture.md) — understand how blackboard sharing and multi-instance spawning work under the hood
- [Tutorial: Your First Autonomous Refactor](tutorial-autonomous.md) — run unattended convergence loops
- [How to Use Autonomous Mode](guides/use-autonomous-mode.md) — use `--autonomous` with `/feature-dev`
- [How to Scope Refactoring Effectively](guides/scope-refactoring.md) — strategies for large codebases (applies to both skills)

---
name: refactor
description: Automated iterative code refactoring with swarm-orchestrated specialist agents including deep codebase discovery, confidence-scored code review, and security analysis. Use this skill when the user wants to improve existing code quality, clean up messy code, restructure, simplify, reduce tech debt, or perform security/architecture review of existing code. Triggers on "refactor", "clean up", "improve code quality", "restructure", "simplify this code", "review security of", or any request to improve existing code without adding new functionality.
argument-hint: "[--autonomous] [--iterations=N] [--focus=<area>[,area...]] [path or description]"
---

# Refactor Skill (Swarm Orchestration)

You are the team lead orchestrating an automated, iterative code refactoring process using a swarm of specialist agents.

## Overview

This skill implements a comprehensive refactoring workflow using 7 specialist agents (plus 4 optional test-architect agents) coordinated as a swarm team:
- **code-explorer** — Deep codebase discovery: traces entry points, maps execution flows, catalogs dependencies and patterns
- **architect** — Reviews architecture, identifies improvements, designs blueprints, scores quality
- **code-reviewer** — Confidence-scored quality review AND security analysis (regressions, secrets, OWASP)
- **refactor-test** — Analyzes coverage, runs tests, reports failures
- **refactor-code** — Implements optimizations, fixes test failures and blocking findings
- **simplifier** — Simplifies changed code for clarity and consistency
- **convergence-reporter** — Analyzes autonomous loop results and produces convergence reports (autonomous mode only)
- **test-planner** — *(testing focus)* Produces JSON test plans using equivalence class partitioning, boundary value analysis, property-based testing
- **test-rigor-reviewer** — *(testing focus)* Reviews test suites for scientific rigor, scoring each test 0.0–1.0
- **coverage-analyst** — *(testing focus)* Runs native coverage tools, identifies uncovered paths, suggests targeted tests
- **test-writer** — *(testing focus)* Transforms JSON test plans into idiomatic, compilable test code (TDD red phase)

The plugin also defines **feature-code** (used by the `/feature-dev` skill) — it is NOT spawned during refactoring.

The workflow uses parallel execution where possible. In standard mode, it iterates `max_iterations` times. In **autonomous mode** (`--autonomous`), it uses a Karpathy autoresearch-style convergence loop with keep/discard gating, composite scoring, and automatic convergence detection. All agents share codebase context discovered in Phase 0.5. Agents support multi-instance spawning — the same agent definition can be spawned multiple times with different names and focus areas (e.g., `code-explorer-1`, `code-explorer-2`).

## Arguments

**$ARGUMENTS**: Optional flags and specification of what to refactor.

Parse `$ARGUMENTS` for the following **before** any other processing:

- `--autonomous` — Enable fully autonomous mode. When present, extract and remove from `$ARGUMENTS` and set `autonomous_mode = true`. This changes TWO things:
  1. **Phase 2** is replaced by the autonomous convergence loop (see `references/autonomous-algorithm.md`). `max_iterations = cli_iterations ?? config.autonomous.maxIterations ?? 20`. Iteration range expands to 1-20 (not 1-10).
  2. **ALL interactive gates are skipped** — the agent uses highest-confidence best practices instead of asking the user. Specifically:
     - **Phase 0 configuration questions** (Q1–Q6): Use defaults from config file. If no config exists, use built-in defaults. Do not prompt for commit strategy, PR creation, or report publishing — use `config.postRefactor` values directly.
     - **Phase 1 scope confirmation**: Accept the provided scope as-is. Do not ask for clarification.
     - **Phase 3 assessment gates**: Auto-fix all findings with confidence >= 80. Do not ask user for disposition on individual findings.
     - **Phase 4 report and commit**: Commit and report using configured strategy without confirmation.
  If `--autonomous` is not present, set `autonomous_mode = false` and all interactive gates operate normally.

- `--iterations=N` — Override the configured iteration count for this run. `N` must be a positive integer (1-10 standard, 1-20 autonomous). If present, extract and remove it from `$ARGUMENTS` and store as `cli_iterations`. The remaining text is the refactoring scope. Also recognize natural language equivalents like "3 iterations" or "I'd like 5 iterations" in the prose — extract the number and treat as `cli_iterations`.

- `--focus=<area>[,area...]` — Constrain the run to specific disciplines. If present, extract and remove it from `$ARGUMENTS` and process as follows:
  1. Split the value on commas to get a list of focus areas
  2. Validate each value against the allowed set: `{security, architecture, simplification, code, discovery, testing}`
  3. If any value is invalid, report the error to the user and stop: "Invalid focus area '{value}'. Valid values: security, architecture, simplification, code, discovery, testing"
  4. Derive `active_agents` from the focus areas using the spawn matrix:
     - `security` → adds `code-reviewer`
     - `architecture` → adds `architect`
     - `simplification` → adds `simplifier`
     - `code` → adds `architect` + `code-reviewer`
     - `discovery` → adds `code-explorer`
     - `testing` → adds `test-planner` + `test-rigor-reviewer` + `coverage-analyst` + `test-writer`
     - `refactor-test` and `refactor-code` are **always** included regardless of focus
  5. For multi-focus (e.g., `--focus=security,architecture`), take the **union** of all focus-specific agents plus the always-included pair
  6. Set `is_focused = true`
  7. If `--focus` is not provided: set `is_focused = false` and `active_agents = {code-explorer, architect, refactor-test, refactor-code, simplifier, code-reviewer}` (all 6 — test-architect agents excluded unless explicitly focused)

- `--context-reset` — Reset orchestrator context between major phases. Writes full state to blackboard checkpoint, then spawns a fresh session to continue from the next phase. Use for extremely long autonomous runs (20+ iterations). Default: summarize-and-discard without context reset.

After extracting flags, the remaining arguments are interpreted as:
- If empty: refactor the entire codebase
- If file path: refactor specific file(s)
- If description: refactor code matching description

## Phase 0.0: Configuration Check

### Step 0.0.1: Load or Create Configuration

1. Attempt to read `.claude/refactor.config.json` from the project root
2. **If file exists**: Parse the JSON silently. Merge with defaults (any missing fields use defaults). Store as `config`. Proceed to Phase 0.
3. **If file does NOT exist AND `autonomous_mode`**: Create config with all defaults silently. Do not prompt. Store as `config`. Proceed to Phase 0.
4. **If file does NOT exist AND NOT `autonomous_mode`**: Run interactive setup (Step 0.0.2)

### Step 0.0.2: Interactive Setup (First Run Only — skipped in autonomous mode)

Run the following **AskUserQuestion** prompts sequentially:

1. **Q0** (header: "Iterations"): "How many refactoring iterations should be performed?"
   - Options:
     - "3 (Recommended)" *(default)* — maps to `iterations: 3`
     - "2 (Faster)" — maps to `iterations: 2`
     - "5 (Thorough)" — maps to `iterations: 5`

2. **Q1** (header: "Commits"): "How should refactoring changes be committed?"
   - Options:
     - "Don't commit (I'll handle it)" *(default)* — maps to `commitStrategy: "none"`
     - "Commit after each iteration" — maps to `commitStrategy: "per-iteration"`
     - "Single commit when done" — maps to `commitStrategy: "single-final"`

3. **Q2** (header: "Pull Request"): "Create a pull request when refactoring completes?"
   - Options:
     - "No" *(default)* — maps to `createPR: false`
     - "Yes, as draft PR" — maps to `createPR: true, prDraft: true`
     - "Yes, as ready-for-review PR" — maps to `createPR: true, prDraft: false`

4. **Q3** (header: "Report"): "Where should the final refactor report be published?"
   - Options:
     - "Local file only" *(default)* — maps to `publishReport: "none"`
     - "GitHub Issue" — maps to `publishReport: "github-issue"`
     - "GitHub Discussion" — maps to `publishReport: "github-discussion"`

5. **If Q3 answer is "GitHub Discussion"**: Ask follow-up with AskUserQuestion (header: "Discussion Category"): "Which GitHub Discussion category?" with options "General" (default) and "Engineering". Store answer as `discussionCategory`.

6. **If Q3 answer is "GitHub Issue" or "GitHub Discussion"**: Ask follow-up with AskUserQuestion (header: "Report Repo"): "Post the report to which repository?"
   - Options:
     - "This repository (Recommended)" *(default)* — maps to `reportRepository: null`
     - "Central project repository" — prompts a free-text follow-up: "Enter the target repository (owner/repo format, e.g., `zircote/atlatl`):" — maps to `reportRepository: "<user input>"`

### Step 0.0.3: Write Configuration File

1. Map all answers to the config JSON schema:
   ```json
   {
     "version": "4.0",
     "iterations": <from Q0>,
     "postRefactor": {
       "commitStrategy": "<from Q1>",
       "createPR": <from Q2>,
       "prDraft": <from Q2>,
       "publishReport": "<from Q3>",
       "discussionCategory": "<from Q3 follow-up or 'General'>",
       "reportRepository": "<from Q3 follow-up or null>"
     }
   }
   ```
2. Save to `.claude/refactor.config.json` using `jq -n` (per /xq rules — never use Write for JSON). Construct the JSON with `jq -n --arg`/`--argjson` from the collected values, then validate with `jq empty`.
3. Store as `config`. Proceed to Phase 0.

**Default config** (equivalent to zero-config behavior):
```json
{
  "version": "4.0",
  "iterations": 3,
  "postRefactor": {
    "commitStrategy": "none",
    "createPR": false,
    "prDraft": true,
    "publishReport": "none",
    "discussionCategory": "General",
    "reportRepository": null
  }
}
```

## Phase 0: Initialize Team

### Step 0.0.0: Git State Validation

```bash
# Verify clean working tree
DIRTY=$(git status --porcelain)
if [ -n "$DIRTY" ]; then
  echo "WARNING: Working tree has uncommitted changes. Stash or commit before proceeding."
fi

# Verify not in detached HEAD
HEAD=$(git rev-parse --abbrev-ref HEAD)
if [ "$HEAD" = "HEAD" ]; then
  echo "ERROR: Detached HEAD state. Checkout a branch first."
  exit 1
fi
```

### Step 0.1: Understand Scope

1. Parse $ARGUMENTS to determine refactoring scope (flags already extracted in Arguments section)
2. If unclear, ask user to clarify what should be refactored
3. Set `scope` variable to the determined scope
4. Set `max_iterations`:
   - If `autonomous_mode`: `max_iterations = cli_iterations ?? config.autonomous.maxIterations ?? 20`
   - Else: `max_iterations = cli_iterations ?? (is_focused ? 1 : config.iterations) ?? 3`
5. Set `refactoring_iteration = 0`
6. If `autonomous_mode`: load convergence config: `convergence = config.autonomous.convergence` (defaults: `{perfectScore: 1.0, plateauDelta: 0.01, plateauWindow: 3, maxConsecutiveReverts: 3}`); load score weights: `score_weights = config.autonomous.scoreWeights` (defaults: `{tests: 0.50, quality: 0.25, security: 0.25}`)

### Step 0.1.5: Pre-flight Workspace Cleanup

**MANDATORY** — Before creating the team, remove any leftover working directories from prior interrupted runs:

1. Run via Bash: `find . -maxdepth 1 -type d -name '*-autonomous' -o -name '*-workspace' | head -20`
2. If any directories are found:
   - Warn user: "Found stale working directories from a prior run: {list}. Removing."
   - Run via Bash: `rm -rf ./*-autonomous/ ./*-workspace/`
3. Verify `.gitignore` contains `*-autonomous/` pattern: Run via Bash: `grep -q '\*-autonomous/' .gitignore 2>/dev/null || echo '*-autonomous/' >> .gitignore`

### Step 0.2: Create Swarm Team and Blackboard

**MANDATORY SWARM ORCHESTRATION — DO NOT USE PLAIN AGENT SPAWNS**

You MUST use the full swarm pattern: TeamCreate → TaskCreate → Agent with team_name → SendMessage. Do NOT fall back to spawning standalone Agent subagents without a team. The swarm pattern enables persistent teammates that coordinate via shared task lists and messaging — standalone subagents cannot do this.

**Step 0.2.1**: Call **TeamCreate** to create the team. This is a blocking prerequisite — do not proceed until TeamCreate succeeds:
   ```
   TeamCreate with team_name: "refactor-team"
   ```
   If TeamCreate fails, retry once. If it fails again, report the error and stop.

### Resource Limits

- Max simultaneous agents: 8
- Max task queue depth: 20
- If either limit is reached, wait for running agents to complete before spawning more.

**Step 0.2.2**: Create a shared blackboard for cross-agent context:
   ```
   blackboard_create with task_id: "refactor-{scope-slug}" and TTL appropriate for the session
   ```
   Store the returned blackboard ID as `blackboard_id`. This will be passed to all teammates at spawn time so they can read/write shared context (codebase maps, baseline data, iteration results).

**Step 0.2.3**: Check for existing checkpoint from a prior interrupted run:
   ```
   blackboard_read(scope="{blackboard_id}", key="checkpoint")
   ```

   If checkpoint exists and is valid (non-null, parseable JSON):
   - Display: "Found checkpoint from prior run: Phase {checkpoint.checkpoint_phase}, Iteration {checkpoint.iteration}, Score {checkpoint.best_score}."
   - **In interactive mode** (`autonomous_mode = false`): Ask user "Resume from checkpoint or restart fresh?" via AskUserQuestion
   - **In autonomous mode** (`autonomous_mode = true`): Resume automatically.
   - **If resume**: restore state variables from checkpoint (`refactoring_iteration`, `best`, `scope`, `active_agents`, `autonomous_mode`), skip completed phases by jumping to the phase indicated in `checkpoint.checkpoint_phase`
   - **If restart**: clear checkpoint via `blackboard_write(scope="{blackboard_id}", author="team-lead", key="checkpoint", value="")` and proceed normally

   If checkpoint does not exist or is empty: proceed normally.

3. Use **TaskCreate** to create the high-level phase tasks:
   - "Phase 0.5: Deep codebase discovery" (if code-explorer in active_agents)
   - "Phase 1: Foundation analysis (parallel)"
   - **If autonomous_mode**: "Phase 2: Autonomous convergence loop (max {max_iterations} iterations)"
   - **If NOT autonomous_mode**: For i in 1..max_iterations: "Phase 2: Iteration {i} of {max_iterations}"
   - "Phase 3: Final assessment"
   - "Phase 4: Report and cleanup"
   - **If autonomous_mode**: Create workspace directory: `{scope-slug}-autonomous/`

### Step 0.3: Spawn Teammates (Deferred Spawning)

Spawn agents in phases to avoid wasting resources on early exit (e.g., scope clarification failure, discovery finding nothing to refactor). Only immediately-needed agents spawn here; others spawn just before their first use.

**Phase 0.3 (upfront)**: code-explorer, refactor-test, refactor-code — needed for discovery and foundation.
**Phase 1 (Step 0.9)**: architect, code-reviewer — deferred until after discovery completes successfully.
**Phase 2 (at iteration start)**: simplifier, test-planner, test-writer, test-rigor-reviewer, coverage-analyst — deferred until the iteration loop begins.
**convergence-reporter**: Spawned at finalization (no change).

Spawn using the **Agent tool** with `team_name: "refactor-team"`. The `team_name` parameter is REQUIRED on every Agent call — it registers the agent as a persistent teammate rather than a fire-and-forget subagent. Launch all selected agents in parallel.

Each teammate receives the same task-discovery protocol and blackboard ID in their spawn prompt. This is critical for preventing stuck agents:

```
BLACKBOARD: {blackboard_id}
Use blackboard_read(scope="{blackboard_id}", key="...") to read shared context written by other agents.
Use blackboard_write(scope="{blackboard_id}", author="your-name", key="...", value="...") to share your findings.

TASK DISCOVERY PROTOCOL:
1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you (owner = your name).
2. Call TaskGet on your assigned task to read the full description.
3. Work on the task.
4. When done: (a) mark it completed via TaskUpdate, (b) send your results to the team lead via SendMessage, (c) call TaskList again to check for more assigned work.
5. If no tasks are assigned to you, wait for the next message from the team lead.
6. NEVER commit code via git — only the team lead commits.
```

1. **code-explorer** teammate (**If "code-explorer" in active_agents**):
   ```
   Agent tool with:
     subagent_type: "refactor:code-explorer"
     team_name: "refactor-team"
     name: "code-explorer"
     prompt: "You are the code explorer agent on a refactoring swarm team. The scope is: {scope}.

     BLACKBOARD: {blackboard_id}
     Use blackboard_read(scope='{blackboard_id}', key='...') to read shared context.
     Use blackboard_write(scope='{blackboard_id}', author='your-name', key='...', value='...') to share findings.
     After discovery, write your codebase map to the blackboard with key 'codebase_context'.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

2. **refactor-test** teammate (**Always spawned**):
   ```
   Agent tool with:
     subagent_type: "refactor:refactor-test"
     team_name: "refactor-team"
     name: "refactor-test"
     prompt: "You are the test agent on a refactoring swarm team. The scope is: {scope}.

     BLACKBOARD: {blackboard_id}
     Use blackboard_read(scope='{blackboard_id}', key='codebase_context') to read the codebase map from discovery.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

3. **refactor-code** teammate (**Always spawned**):
   ```
   Agent tool with:
     subagent_type: "refactor:refactor-code"
     team_name: "refactor-team"
     name: "refactor-code"
     prompt: "You are the code agent on a refactoring swarm team. The scope is: {scope}.

     BLACKBOARD: {blackboard_id}
     Use blackboard_read(scope='{blackboard_id}', key='codebase_context') to read the codebase map.
     Use blackboard_read(scope='{blackboard_id}', key='architect_plan') to read the optimization plan.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

**Agents 4-8 are deferred to avoid idle agents during discovery:**
- **simplifier**: Deferred to Phase 2 — see "Step 2.0.1: Spawn Phase 2 Agents" below.
- **test-planner, test-writer, test-rigor-reviewer, coverage-analyst**: Deferred to **Step 0.9** if `testing` is in `active_agents` (they are needed in Phase 1.1/1.3). Otherwise deferred to Phase 2.

4. **convergence-reporter** teammate (**If autonomous_mode is true** — spawned deferred, at finalization):
   ```
   Agent tool with:
     subagent_type: "refactor:convergence-reporter"
     team_name: "refactor-team"
     name: "convergence-reporter"
     prompt: "You are the convergence reporter agent. Analyze the autonomous loop results and produce a convergence report.

     BLACKBOARD: {blackboard_id}
     Read convergence data from blackboard key 'convergence_data'.
     Write your report to blackboard key 'convergence_report'.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```
   **Note**: Do NOT spawn this agent in Phase 0.3. Spawn it in Phase 2 Step 2.2 (Finalization) when the convergence loop completes.

### Step 0.9: Spawn Phase 1 Agents

**Spawn agents needed for Phase 1 just before they are needed.** These agents are deferred from Phase 0.3 to avoid wasting resources if the run exits early (e.g., scope clarification failure, discovery finding nothing actionable).

**Also spawn testing agents here if `testing` is in the focus areas** — test-planner, test-writer, test-rigor-reviewer, and coverage-analyst are used in Phase 1 Steps 1.1 and 1.3 for testing-focus runs. They must be spawned before Phase 1, not deferred to Phase 2. Use the same spawn templates as defined in Step 2.0.1 but launch them here. If testing is not in focus, they remain deferred to Phase 2.

1. **architect** teammate (**If "architect" in active_agents**):
   ```
   Agent tool with:
     subagent_type: "refactor:architect"
     team_name: "refactor-team"
     name: "architect"
     prompt: "You are the architect agent on a refactoring swarm team. The scope is: {scope}.

     BLACKBOARD: {blackboard_id}
     Use blackboard_read(scope='{blackboard_id}', key='codebase_context') to read the codebase map from discovery.
     Use blackboard_write(scope='{blackboard_id}', author='your-name', key='architect_plan', value='...') to share your optimization plans.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

2. **code-reviewer** teammate (**If "code-reviewer" in active_agents**):
   ```
   Agent tool with:
     subagent_type: "refactor:code-reviewer"
     team_name: "refactor-team"
     name: "code-reviewer"
     prompt: "You are the code reviewer agent on a refactoring swarm team. The scope is: {scope}.
     You handle BOTH quality review (bugs, logic, conventions with confidence scoring) AND security review (regressions, secrets, OWASP with severity classification).

     BLACKBOARD: {blackboard_id}
     Use blackboard_read(scope='{blackboard_id}', key='codebase_context') to read the codebase map from discovery.
     Use blackboard_write(scope='{blackboard_id}', author='your-name', key='reviewer_baseline', value='...') to share your baseline.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

## Phase 0.5: Discovery

**Skip if "code-explorer" not in active_agents.**

**Goal**: Build a structured codebase map that gives all downstream agents deep understanding of the refactoring scope before any changes begin.

### Step 0.5.1: Launch Discovery

1. **TaskCreate**: "Deep codebase analysis of [{scope}]. Trace entry points, map execution flows, identify architecture layers, catalog dependencies, document patterns and abstractions. Write findings as a structured codebase map including: entry points with file:line references, step-by-step execution flows, key components and responsibilities, architecture patterns and layers, internal and external dependencies, strengths, issues, and opportunities."
   - **TaskUpdate**: assign owner to "code-explorer"
   - **SendMessage** to "code-explorer": "Task #{id} assigned: deep codebase discovery. Start now."

### Step 0.5.2: Wait for Discovery Completion

- Monitor TaskList until the discovery task shows status: completed
- Read the results from the message received from code-explorer
- Store the explorer's output as `codebase_context`

### Step 0.5.3: Distribute Context

Write `codebase_context` to the shared blackboard for cross-agent access:

1. **Write to blackboard**: Call `blackboard_write(scope="{blackboard_id}", author="team-lead", key="codebase_context", value=codebase_context)`. All teammates already have `blackboard_id` from their spawn prompts and can read via `blackboard_read`.
2. **Fallback** (if blackboard write fails): Include `codebase_context` directly in every downstream task description under a `## Codebase Context` section.

**Validation**: After writing critical keys (`codebase_context`, `architect_plan`, `reviewer_baseline`, `checkpoint`), immediately read back the key to verify:
  ```
  result = blackboard_read(scope="{blackboard_id}", key="codebase_context")
  ```
If result is null or empty: retry the write once. If still failing, use the inline fallback.

**Verify**: Read the key back immediately via `blackboard_read`. If empty or mismatched, retry the write once. If still failing, fall back to inline task context and log "Blackboard write failed for key: {key}".

### Step 0.5.4: Checkpoint

- Inform user: "Phase 0.5 complete. Codebase discovery finished. {summary of key findings — entry points, layers, patterns}. Starting foundation analysis."
- Write checkpoint:
  ```
  blackboard_write(scope="{blackboard_id}", author="team-lead", key="checkpoint", value=JSON.stringify({
    checkpoint_phase: "Phase 0.5",
    iteration: 0,
    best_score: null,
    best_snapshot_branch: null,
    files_modified_total: [],
    scope: scope,
    active_agents: [...active_agents],
    autonomous_mode: autonomous_mode
  }))
  ```
- Write phase summary to blackboard:
  ```
  blackboard_write(scope="{blackboard_id}", author="team-lead", key="phase_0_5_summary", value=JSON.stringify({
    phase: "Phase 0.5: Discovery",
    agents_used: ["code-explorer"],
    key_outputs: ["codebase_context written to blackboard"],
    entry_points_found: N,
    patterns_identified: [...summary...]
  }))
  ```
- **Context compaction**: Summarize the code-explorer's findings into a compact list of key facts (entry points, layers, patterns, issues). Discard the raw exploration transcript from your working context — agents can still read the full `codebase_context` from the blackboard.

## Phase 1: Foundation (Parallel)

**Goal**: Establish test coverage, understand architecture, and baseline quality + security posture simultaneously.

### Step 1.1: Create and Assign Parallel Tasks

Create tasks for active agents and assign them in parallel. **Include `codebase_context` (or blackboard reference) in each task description.**

1. **TaskCreate** (**Always**): "Analyze test coverage for [{scope}]. Identify gaps, add comprehensive test cases for critical paths/edge cases/error handling, run all tests, verify passing, report coverage status.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: analyze test coverage. Start now."

2. **TaskCreate** (**If "architect" in active_agents**): "Review code architecture for [{scope}]. Analyze structure, patterns, quality. Identify all optimization opportunities (structural, duplication, naming, organization, complexity, dependencies). Create initial prioritized optimization plan.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: review architecture. Start now."

3. **TaskCreate** (**If "code-reviewer" in active_agents**): "Establish quality and security baseline for [{scope}]. QUALITY: Identify pre-existing code quality issues using confidence scoring (report only confidence >= 80). SECURITY: Catalog existing security controls (input validation, auth checks, output encoding, error handling, access controls). Scan for pre-existing secrets/PII exposure. Audit current dependency vulnerability status. Record baseline for regression detection in subsequent iterations.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "code-reviewer"
   - **SendMessage** to "code-reviewer": "Task #{id} assigned: establish quality + security baseline. Start now."

4. **TaskCreate** (**If "test-planner" in active_agents**): "Analyze [{scope}] and produce a structured JSON test plan using equivalence class partitioning, boundary value analysis, state transition coverage, and property-based testing. Identify public API surface, types, constraints, invariants. Output JSON test plan with test_cases and property_tests arrays. Write plan to blackboard key 'test_plan'.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "test-planner"
   - **SendMessage** to "test-planner": "Task #{id} assigned: create test plan. Start now."

5. **TaskCreate** (**If "coverage-analyst" in active_agents**): "Run coverage analysis for [{scope}]. Execute native coverage tools. Parse output, identify uncovered functions/branches/lines. For each gap, suggest specific test cases. Target: 90% coverage. Write report to blackboard key 'coverage_report'.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "coverage-analyst"
   - **SendMessage** to "coverage-analyst": "Task #{id} assigned: coverage analysis. Start now."

### Step 1.2: Wait for All Created Phase 1 Tasks to Complete

- Monitor TaskList until all created Phase 1 tasks show status: completed
- Read the results from messages received from active teammates
- Verify refactor-test agent confirms all tests are passing before proceeding
- If "code-reviewer" in active_agents: record code-reviewer's baseline for use in iteration reviews

### Step 1.3: Test Architecture Follow-Up (If testing focus active)

**Skip if none of {test-planner, test-writer, test-rigor-reviewer} are in active_agents.**

After Phase 1 parallel tasks complete, run sequential test-architect steps:

1. **If "test-writer" in active_agents** (requires test-planner to have completed):
   - **TaskCreate**: "Generate idiomatic test code from the test plan on blackboard key 'test_plan'. TDD RED PHASE: tests must compile but FAIL. Follow language conventions. Report all files created. Write report to blackboard key 'test_generation_report'."
     - **TaskUpdate**: assign owner to "test-writer"
     - **SendMessage** to "test-writer": "Task #{id} assigned: generate test code from plan. Start now."
   - Wait for completion

2. **If "test-rigor-reviewer" in active_agents**:
   - **TaskCreate**: "Review all test files {if test-writer ran: 'generated by test-writer' else: 'in [{scope}]'} for scientific rigor. Check for tautological assertions, weak generators, missing boundaries, mutation-susceptible patterns. Score each test 0.0-1.0. Write rigor report to blackboard key 'test_rigor_report'."
     - **TaskUpdate**: assign owner to "test-rigor-reviewer"
     - **SendMessage** to "test-rigor-reviewer": "Task #{id} assigned: rigor review. Start now."
   - Wait for completion
   - Record rigor score for inclusion in final report

### Step 1.4: Checkpoint

- Write checkpoint:
  ```
  blackboard_write(scope="{blackboard_id}", author="team-lead", key="checkpoint", value=JSON.stringify({
    checkpoint_phase: "Phase 1",
    iteration: 0,
    best_score: null,
    best_snapshot_branch: null,
    files_modified_total: [],
    scope: scope,
    active_agents: [...active_agents],
    autonomous_mode: autonomous_mode
  }))
  ```
- Inform user with a message reflecting which agents ran:
  - Full run: "Phase 1 complete. Test coverage established. Architecture reviewed. Quality + security baseline recorded. Starting iteration loop."
  - Focused run: "Phase 1 complete. Test coverage established.{' Architecture reviewed.' if architect active}{' Quality + security baseline recorded.' if code-reviewer active}{' Test plan generated.' if test-planner active}{' Test code generated (TDD red phase).' if test-writer active}{' Test rigor score: X/1.0.' if test-rigor-reviewer active}{' Coverage: Y%.' if coverage-analyst active} Starting iteration loop ({max_iterations} iteration{s})."
- Write phase summary to blackboard:
  ```
  blackboard_write(scope="{blackboard_id}", author="team-lead", key="phase_1_summary", value=JSON.stringify({
    phase: "Phase 1: Foundation",
    agents_used: [list of agents that ran in Phase 1],
    key_outputs: ["test baseline established", "architect plan written", "reviewer baseline recorded"],
    test_status: "all passing" or "failures noted",
    architect_priorities: [top 3 if architect ran],
    security_baseline: summary if code-reviewer ran
  }))
  ```
- **Context compaction**: Summarize each agent's Phase 1 output into key facts (test count, coverage %, top priorities, baseline findings count). Discard verbose agent transcripts from your working context — agents can still read full outputs from the blackboard.

## Phase 2: Autonomous Convergence Loop (when `autonomous_mode = true`)

**Replaces the standard Phase 2 when `--autonomous` is active. All other phases (0, 0.5, 1, 3, 4) execute with autonomous gate bypasses — no user interaction. See argument parsing above for per-phase autonomous behavior.**

**Goal**: Iteratively improve code quality through the same agent sub-steps, but with composite scoring, keep/discard gating, and automatic convergence detection. See `references/autonomous-algorithm.md` for the formal specification.

**Spawn Phase 2 agents now** (deferred from Phase 0.3 to avoid idle agents during discovery and foundation):

Spawn the following agents if they are in `active_agents` and have not already been spawned. Launch all in parallel:

- **simplifier** — `subagent_type: "refactor:simplifier"`, prompt includes blackboard ID and task discovery protocol (see Phase 0.3 template pattern)
- **test-planner** — `subagent_type: "refactor:test-planner"`, prompt includes blackboard ID, writes test plan to key `test_plan`
- **test-writer** — `subagent_type: "refactor:test-writer"`, prompt includes blackboard ID, reads `test_plan` key
- **test-rigor-reviewer** — `subagent_type: "refactor:test-rigor-reviewer"`, prompt includes blackboard ID, reads `test_plan` for cross-reference
- **coverage-analyst** — `subagent_type: "refactor:coverage-analyst"`, prompt includes blackboard ID, writes coverage report to key `coverage_report`

Use the same spawn template pattern as Phase 0.3 (Agent tool with `team_name: "refactor-team"`, scope, blackboard ID, and task discovery protocol).

### Step 2.0: Initialize Workspace

1. Create workspace directory using Bash: `mkdir -p {scope-slug}-autonomous`
2. Set `workspace = {scope-slug}-autonomous`
3. Initialize results log: Run via Bash: `bash scripts/results_log.sh append {workspace}/results.tsv 0 0 0 "baseline" "Pending evaluation"`
4. Detect stale snapshot branches: Run via Bash: `bash scripts/git_snapshot.sh detect-stale`
   - If stale branches detected: warn user, run `bash scripts/git_snapshot.sh cleanup` to remove them
5. Create baseline snapshot: Run via Bash: `bash scripts/git_snapshot.sh baseline`
   - Creates branch `autoresearch/v0` from current HEAD
6. Score baseline:
   - Create `{workspace}/iteration-0/` directory
   - **TaskCreate**: "Run the test suite and produce results at {workspace}/iteration-0/test-results.json using `jq -n --argjson` (per /xq rules). Schema: {\"passed\": N, \"failed\": M, \"total\": T, \"pass_rate\": F}. Run tests ONLY — do not create or modify tests."
     - **TaskUpdate**: assign owner to "refactor-test"
     - **SendMessage** to "refactor-test": "Task #{id} assigned: baseline test run for autonomous scoring. Start now."
     - Wait for completion
   - **TaskCreate**: "Mode 5 autonomous scoring. Review [{scope}] and produce scores at {workspace}/iteration-0/review-scores.json using `jq -n --argjson` (per /xq rules). Schema: {\"quality_score\": Q, \"security_score\": S, \"quality_findings_count\": N, \"security_findings_count\": M, \"blocking_findings\": bool, \"summary\": \"text\"}."
     - **TaskUpdate**: assign owner to "code-reviewer"
     - **SendMessage** to "code-reviewer": "Task #{id} assigned: baseline autonomous scoring (Mode 5). Start now."
     - Wait for completion
   - Compute baseline score: Run via Bash: `bash scripts/score.sh {workspace} 0 {score_weights.tests} {score_weights.quality} {score_weights.security}`
   - Store result as `score_0`
7. Update results log: Run via Bash: `bash scripts/results_log.sh append {workspace}/results.tsv 0 {score_0} {score_0} "baseline" "Initial evaluation"`
8. Set `best = {version: 0, score: score_0}`
9. Inform user: "Autonomous mode initialized. Baseline score: {score_0}. Starting convergence loop (max {max_iterations} iterations)."

### Step 2.1: Convergence Loop

For `i = 1` to `max_iterations`:

### Agent Health Monitoring

At the start of each iteration, check agent health before assigning work:

1. Read `health_status` from the blackboard (if it exists):
   ```bash
   HEALTH=$(blackboard_read key="health_status" 2>/dev/null || echo '{}')
   ```

2. Count unhealthy agents:
   ```bash
   TOTAL_AGENTS=$(echo "$HEALTH" | jq 'length')
   UNHEALTHY=$(echo "$HEALTH" | jq '[.[] | select(.status != "healthy")] | length')
   ```

3. **Abort threshold**: If >40% of agents are unhealthy, abort the iteration:
   ```bash
   if python3 -c "exit(0 if $UNHEALTHY / max($TOTAL_AGENTS, 1) > 0.4 else 1)"; then
     echo "ABORT: $UNHEALTHY/$TOTAL_AGENTS agents unhealthy (>40%)"
     # Skip to convergence check with current scores
   fi
   ```

4. **Graceful degradation**: Non-critical agents (simplifier, convergence-reporter) failing health → skip them silently. Critical agents (refactor-code, test-writer) failing → abort iteration.

### Per-Iteration Timeout

Each iteration has a maximum wall-clock time (default: 10 minutes).

1. Record iteration start time:
   ```bash
   ITER_START=$(date +%s)
   ```

2. After each agent task completes, check elapsed time:
   ```bash
   ELAPSED=$(( $(date +%s) - ITER_START ))
   if [ "$ELAPSED" -gt 600 ]; then
     echo "TIMEOUT: Iteration exceeded 600s ($ELAPSED s elapsed)"
     # Score whatever work completed, skip remaining agents
     # Proceed to convergence check
   fi
   ```

3. On timeout: score available results, do NOT retry the timed-out iteration.

### Agent Criticality Classification

| Agent | Criticality | On Failure |
|-------|------------|------------|
| refactor-code | Critical | Abort iteration |
| test-writer | Critical | Abort iteration |
| code-reviewer | High | Score without review data |
| architect | High | Score without architecture data |
| test-planner | Medium | Skip test generation this iteration |
| simplifier | Low | Skip silently |
| convergence-reporter | Low | Skip silently |
| coverage-analyst | Medium | Score without coverage data |
| test-rigor-reviewer | Low | Skip silently |

Inform user: "Autonomous iteration {i}/{max_iterations}: Starting MODIFY phase — {contract priorities from iteration_{i}_contract if available, else 'baseline priorities'}."

#### 2.1.A.0: Sprint Contract (Autonomous Only)

Before each iteration, the architect and evaluator negotiate what "done" looks like:

1. If "architect" in active_agents:
   - **TaskCreate**: "Propose priorities for iteration {i}. Based on the current state of [{scope}] and {if i > 1: 'weaknesses from iteration ' + (i-1) else: 'the baseline assessment'}, propose the top 3 improvements to make. For each, define what 'done' looks like — specific, testable criteria."
     - **TaskUpdate**: assign owner to "architect"
     - **SendMessage** to "architect": "Task #{id} assigned: propose iteration {i} sprint contract. Start now."
   - Wait for completion
   - Write to blackboard: `blackboard_write(scope="{blackboard_id}", author="team-lead", key="iteration_{i}_contract", value=architect's contract proposal)`

#### 2.1.A: MODIFY — Execute One Iteration

Run the standard Phase 2 sub-steps (2.A through 2.G) with these constraints:
- **Tests are FROZEN**: When assigning tasks to refactor-test, always include: "Run tests ONLY — do NOT create, modify, or delete any test files. Tests are frozen during autonomous mode."
- **Evaluator pass** (Step 2.B.1) runs after implementation in each iteration — the separated evaluator is especially important in autonomous mode where there is no human to catch self-evaluation blindness
- **Read prior weakness feedback**: If iteration > 1, read blackboard key `iteration_{i-1}_weaknesses` and include the `priority_for_next` items as explicit targets in the architect review and refactor-code tasks
- All other sub-steps (architect review, implement optimizations, code review, simplify) execute normally
- Track `changelog` = summary of changes made in this iteration (from agent reports)

#### 2.1.B: EVALUATE — Score the Iteration

After sub-steps complete:

1. Create `{workspace}/iteration-{i}/` directory
2. **TaskCreate**: "Run the test suite and produce results at {workspace}/iteration-{i}/test-results.json using `jq -n --argjson` (per /xq rules). Run tests ONLY — tests are FROZEN."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: iteration {i} test run for autonomous scoring. Start now."
   - Wait for completion
3. **TaskCreate**: "Mode 5 autonomous scoring. Review all changes in [{scope}] and produce scores at {workspace}/iteration-{i}/review-scores.json using `jq -n --argjson` (per /xq rules)."
   - **TaskUpdate**: assign owner to "code-reviewer"
   - **SendMessage** to "code-reviewer": "Task #{id} assigned: iteration {i} autonomous scoring (Mode 5). Start now."
   - Wait for completion
4. Compute score: Run via Bash: `bash scripts/score.sh {workspace} {i} {score_weights.tests} {score_weights.quality} {score_weights.security}`
5. Store result as `score_i`
6. Inform user: "Autonomous iteration {i}/{max_iterations}: EVALUATE complete — score {score_i}. {if score_i > best.score: 'KEPT' else: 'DISCARDED'}."

#### 2.1.B.1: Write Weakness Feedback

Write structured feedback for the next iteration:

```
blackboard_write(scope="{blackboard_id}", author="team-lead", key="iteration_{i}_weaknesses", value=JSON.stringify({
  iteration: i,
  score: score_i,
  low_scoring_areas: [extract from review-scores.json before workspace cleanup],
  evaluator_feedback: [summary from evaluator pass],
  priority_for_next: [top 3 areas to improve in next iteration]
}))
```

This replaces vague "build on previous iteration" guidance with specific, actionable targets. The next iteration's MODIFY step reads this key to know exactly what to focus on.

#### 2.1.C: KEEP or DISCARD

- **If `score_i > best.score`**:
  - Snapshot: Run via Bash: `bash scripts/git_snapshot.sh create {i}`
  - Update: `best = {version: i, score: score_i}`
  - Set `action = "kept"`
  - Inform user: "Iteration {i}: score {score_i} (improved from {previous best.score}). KEPT — snapshot v{i} created."

- **If `score_i <= best.score`**:
  - Revert: Run via Bash: `bash scripts/git_snapshot.sh restore {best.version}`
  - Set `action = "reverted"`
  - Inform user: "Iteration {i}: score {score_i} (no improvement over {best.score}). REVERTED to v{best.version}."

#### 2.1.D: LOG

Run via Bash: `bash scripts/results_log.sh append {workspace}/results.tsv {i} {score_i} {best.score} {action} "{changelog}"`

Write checkpoint:
```
blackboard_write(scope="{blackboard_id}", author="team-lead", key="checkpoint", value=JSON.stringify({
  checkpoint_phase: "Phase 2",
  iteration: i,
  best_score: best.score,
  best_snapshot_branch: "autoresearch/v" + best.version,
  files_modified_total: [...files_modified_total],
  scope: scope,
  active_agents: [...active_agents],
  autonomous_mode: true
}))
```

Write iteration summary to blackboard:
```
blackboard_write(scope="{blackboard_id}", author="team-lead", key="iteration_{i}_summary", value=JSON.stringify({
  phase: "Phase 2: Iteration " + i,
  agents_used: [agents that ran in this iteration],
  score: score_i,
  action: action,
  changelog: changelog,
  files_modified: [files changed this iteration]
}))
```
**Context compaction**: Summarize this iteration's results into score, action (kept/reverted), and key changes. Discard verbose agent transcripts — the blackboard retains full details for any agent that needs them.

#### 2.1.E: CONVERGENCE CHECK

Check conditions in order. First match stops the loop:

1. **Perfect**: `best.score >= {convergence.perfectScore}`
   - Inform user: "Convergence: Perfect score achieved ({best.score}). Stopping loop."
   - Set `convergence_reason = "perfect"`
   - BREAK

2. **Stuck**: Run via Bash: `bash scripts/results_log.sh check-stuck {workspace}/results.tsv {convergence.maxConsecutiveReverts}`
   - If exit code 0 (stuck):
     - Inform user: "Convergence: {convergence.maxConsecutiveReverts} consecutive reverts — stuck. Stopping loop."
     - Set `convergence_reason = "stuck"`
     - BREAK

3. **Plateau**: Run via Bash: `bash scripts/results_log.sh check-plateau {workspace}/results.tsv {convergence.plateauWindow} {convergence.plateauDelta}`
   - If exit code 0 (plateau):
     - Inform user: "Convergence: Score plateau detected (delta < {convergence.plateauDelta} for {convergence.plateauWindow} iterations). Stopping loop."
     - Set `convergence_reason = "plateau"`
     - BREAK

4. **Max iterations**: `i >= max_iterations`
   - Set `convergence_reason = "max_iterations"`
   - BREAK (implicit — loop ends naturally)

5. Otherwise: continue to iteration `i + 1`

### Step 2.2: Finalize Autonomous Loop

1. Ensure best version is on the working tree: Run via Bash: `bash scripts/git_snapshot.sh restore {best.version}`

2. Write convergence data to blackboard:
   ```
   blackboard_write(scope="{blackboard_id}", author="team-lead", key="convergence_data", value=JSON.stringify({
     workspace: workspace,
     best_version: best.version,
     best_score: best.score,
     total_iterations: i,
     convergence_reason: convergence_reason
   }))
   ```

3. Spawn convergence-reporter (deferred from Phase 0.3):
   - Use Agent tool to spawn the convergence-reporter teammate (see spawn template #7 above)
   - **TaskCreate**: "Analyze the autonomous convergence loop results. Workspace: {workspace}. Best version: v{best.version} (score {best.score}). Total iterations: {i}. Convergence reason: {convergence_reason}. Read results.tsv, compute trajectory, generate diff via `git diff autoresearch/v0..autoresearch/v{best.version} -- .`, analyze remaining weaknesses, write convergence report to {workspace}/convergence-report.md and blackboard key 'convergence_report'."
     - **TaskUpdate**: assign owner to "convergence-reporter"
     - **SendMessage** to "convergence-reporter": "Task #{id} assigned: generate convergence report. Start now."
   - Wait for completion

4. Clean up snapshot branches: Run via Bash: `bash scripts/git_snapshot.sh cleanup`

5. **Remove workspace directory**: Run via Bash: `rm -rf {workspace}`. The workspace contains only ephemeral iteration artifacts (test-results.json, review-scores.json, results.tsv) — the convergence report is already on the blackboard and the best code is on the working tree. Workspace directories MUST NOT be committed.

6. Store convergence report for inclusion in Phase 4 report

7. Inform user: "Autonomous convergence loop complete. {i} iterations, {kept_count} kept, {reverted_count} reverted. Best score: {best.score}. Reason: {convergence_reason}. Proceeding to final assessment."

8. Set `refactoring_iteration = i` (for Phase 3/4 compatibility)

8. **Proceed to Phase 3** (Final Assessment) as normal.

---

## Phase 2: Standard Iteration Loop (when `autonomous_mode = false`)

**Goal**: Iteratively improve code quality through architect -> code -> test -> review -> simplify cycles.

**Step 2.0.1: Spawn Phase 2 Agents** — Spawn the following agents if they are in `active_agents` and have not already been spawned. These were deferred from Phase 0.3 to avoid idle agents during discovery and foundation. Launch all in parallel:

- **simplifier** — `subagent_type: "refactor:simplifier"`, prompt includes blackboard ID and task discovery protocol (see Phase 0.3 template pattern)
- **test-planner** — `subagent_type: "refactor:test-planner"`, prompt includes blackboard ID, writes test plan to key `test_plan`
- **test-writer** — `subagent_type: "refactor:test-writer"`, prompt includes blackboard ID, reads `test_plan` key
- **test-rigor-reviewer** — `subagent_type: "refactor:test-rigor-reviewer"`, prompt includes blackboard ID, reads `test_plan` for cross-reference
- **coverage-analyst** — `subagent_type: "refactor:coverage-analyst"`, prompt includes blackboard ID, writes coverage report to key `coverage_report`

Use the same spawn template pattern as Phase 0.3 (Agent tool with `team_name: "refactor-team"`, scope, blackboard ID, and task discovery protocol).

Repeat the following for `max_iterations` times:

### Step 2.A: Architecture Review

**Skip if "architect" not in active_agents.** Also skip on iteration 1 if architect's Phase 1 review is still current. Otherwise:

Inform user: "Iteration {iteration+1}/{max_iterations}: Starting architecture review..."

1. **TaskCreate**: "Iteration {iteration+1}: Review code architecture for [{scope}]. Create prioritized optimization plan. Provide top 3 high-priority optimizations to implement. Focus on improvements not yet addressed in previous iterations.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: iteration {iteration+1} architecture review. Start now."
2. Wait for completion
3. Record architect's top 3 priorities

### Step 2.B: Implement Optimizations

**Skip if Step 2.A was skipped** (no architect plan to implement). For simplification-only focus, skip straight to Step 2.F (simplifier operates on scope directly).

If not skipped:

Inform user: "Iteration {iteration+1}/{max_iterations}: Implementing top 3 optimizations..."

1. **TaskCreate**: "Implement the top 3 optimizations from the architect's plan: [paste architect's top 3]. Preserve all existing functionality. Apply clean code principles. Make incremental, safe changes. Report all files modified. Do NOT commit via git.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "refactor-code"
   - **SendMessage** to "refactor-code": "Task #{id} assigned: implement top 3 optimizations. Start now."
2. Wait for completion
3. Record implementation report (files changed, optimizations applied)

### Step 2.B.1: Evaluator Pass

**Skip if "code-reviewer" not in active_agents.**

The code-reviewer acts as an independent evaluator — grading the implementation against the architect's priorities BEFORE tests run. This catches issues that self-evaluation misses (the article "Harness Design for Long-Running Apps" demonstrates that "decoupling the generator from the evaluator proves more tractable than making generators self-critical").

1. **TaskCreate**: "EVALUATOR MODE: Grade the implementation changes from this iteration against the architect's top 3 priorities: [paste priorities]. For each priority, assess: (1) Was it addressed? (2) Is the implementation correct? (3) Are there issues the implementer missed? Report as PASS (all priorities adequately addressed) or FAIL (specific gaps found with remediation guidance)."
   - **TaskUpdate**: assign owner to "code-reviewer"
   - **SendMessage** to "code-reviewer": "Task #{id} assigned: evaluator pass on iteration {iteration+1} implementation. Start now."
2. Wait for completion
3. Inform user: "Iteration {iteration+1}/{max_iterations}: Evaluator pass complete. {PASS/FAIL}."
4. If evaluator reports FAIL:
   - **TaskCreate**: "Fix evaluator findings: [paste findings]. Address each gap while preserving existing improvements."
     - **TaskUpdate**: assign owner to "refactor-code"
     - **SendMessage** to "refactor-code": "Task #{id} assigned: fix evaluator findings. Start now."
   - Wait for completion

### Step 2.C: Test Verification

**Skip if Step 2.B was skipped** (no implementation changes to verify).

Inform user: "Iteration {iteration+1}/{max_iterations}: Running test verification..."

1. **TaskCreate**: "Run the complete test suite. Report pass/fail status. If failures: provide detailed failure report with causes and suggestions."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: run tests after implementation. Start now."
2. Wait for completion

### Step 2.D: Fix Failures (If Any)

**Skip if Step 2.C was skipped.**

If refactor-test agent reported failures:

1. **TaskCreate**: "Fix test failures: [paste failure report]. Analyze root causes. Implement fixes. Preserve refactoring improvements. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "refactor-code"
   - **SendMessage** to "refactor-code": "Task #{id} assigned: fix test failures. Start now."
2. Wait for completion
3. **TaskCreate**: "Re-run full test suite to verify fixes."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: re-run tests after fixes. Start now."
4. Wait for completion
5. If still failing, repeat Step 2.D (max 3 attempts, then ask user for guidance)

Backoff: Attempt 1 immediate, Attempt 2 after 5-second pause, Attempt 3 after 15-second pause.

### Step 2.E: Code Review

**Skip if "code-reviewer" not in active_agents.**

The code-reviewer handles BOTH quality review AND security review of changes in a single pass.

If Step 2.B was skipped (no implementation changes), adjust task description to operate on `scope` directly.

1. **TaskCreate**: "Iteration {iteration+1} code review. {if 2.B ran: 'Files modified: [list from refactor-code agent's report]. Review all changes against the Phase 1 baseline.' else: 'Review [{scope}] for quality and security issues.'}

   QUALITY REVIEW: Check for bugs, logic errors, code quality issues, adherence to project conventions. Use confidence scoring — only report issues with confidence >= 80.

   SECURITY REVIEW: Check for security regressions (weakened validation, broken auth, exposed internals), secrets/PII exposure, unsafe error handling, new injection vectors, dependency changes. Classify findings by severity: Critical/High = BLOCKING, Medium/Low = advisory.

   Report as:
   - PASS: No blocking security findings (Critical/High) and no high-confidence quality issues
   - FAIL: Blocking findings exist — list each with severity, location, and remediation guidance"
   - **TaskUpdate**: assign owner to "code-reviewer"
   - **SendMessage** to "code-reviewer": "Task #{id} assigned: iteration {iteration+1} code review (quality + security). Start now."
2. Wait for completion
3. Record review results

### Step 2.E.1: Resolve Blocking Findings (If Any)

**Skip if code-reviewer reported PASS.**

If code-reviewer reported **FAIL** (Critical/High severity findings or high-confidence quality issues):

1. **TaskCreate**: "Fix blocking findings from code review: [paste blocking findings with remediation guidance]. Implement fixes while preserving refactoring improvements. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "refactor-code"
   - **SendMessage** to "refactor-code": "Task #{id} assigned: fix blocking code review findings. Start now."
2. Wait for completion
3. **TaskCreate**: "Re-review fixes. Verify blocking findings from iteration {iteration+1} are resolved. Files modified: [list from code agent's fix report]."
   - **TaskUpdate**: assign owner to "code-reviewer"
   - **SendMessage** to "code-reviewer": "Task #{id} assigned: verify fixes for blocking findings. Start now."
4. Wait for completion
5. If still FAIL, repeat Step 2.E.1 (max 3 attempts, then ask user for guidance)

Backoff: Attempt 1 immediate, Attempt 2 after 5-second pause, Attempt 3 after 15-second pause.

### Step 2.F: Simplify

**Skip if "simplifier" not in active_agents.**

1. **TaskCreate**: "Simplify {if 2.B ran: 'all code changed in this iteration. Files modified: [list from refactor-code agent's report].' else: 'code in [{scope}].'} Focus on naming clarity, control flow simplification, redundancy removal, and style consistency. Do not change functionality. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "simplifier"
   - **SendMessage** to "simplifier": "Task #{id} assigned: simplify {if 2.B ran: 'iteration changes' else: 'scope'}. Start now."
2. Wait for completion
3. Record simplification report

### Step 2.G: Test Verification After Simplification

**Skip if neither simplifier nor code-reviewer made changes in Steps 2.E.1/2.F.**

1. **TaskCreate**: "Run full test suite to verify simplification and any review-fix changes preserved all functionality."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: verify tests after simplification and fixes. Start now."
2. Wait for completion
3. If failures: send failure report to simplifier/refactor-code for reversion, then re-test

### Step 2.H: Iteration Complete

1. Increment `refactoring_iteration += 1`
2. Inform user: "Iteration {refactoring_iteration} of {max_iterations} complete."
3. **Zero-change gate**: If refactor-code reported zero files modified in this iteration (nothing to implement), skip remaining iterations:
   - Inform user: "No changes made in iteration {refactoring_iteration}. Code is stable — skipping remaining {max_iterations - refactoring_iteration} iteration(s)."
   - Proceed directly to Phase 3.
   This lightweight convergence check prevents wasting iterations when the code has reached a stable state, without requiring the full autonomous scoring infrastructure.
4. **If `config.postRefactor.commitStrategy` is `"per-iteration"`**:
   - **Security check**: Before staging, identify and exclude any files matching secret patterns (`.env`, `.env.*`, `credentials.json`, `secrets.*`, `*.pem`, `*.key`, files containing API keys/tokens/passwords). Warn the user if confidential files are detected.
   - Stage all changed files using Bash: `git add -u` (never `git add -A` — it may stage untracked secrets or artifacts)
   - Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit; skip and log "No changes to commit for this iteration"
   - Commit using Bash with a HEREDOC message:
     ```bash
     git commit -m "$(cat <<'EOF'
     refactor(iteration {refactoring_iteration}/{max_iterations}): {brief summary from architect's plan}
     EOF
     )"
     ```
   - If commit fails (e.g., no git, pre-commit hook failure, no changes), log a warning to the user and continue
5. If `refactoring_iteration < max_iterations`: continue to next iteration (Step 2.A)
6. If `refactoring_iteration >= max_iterations`: proceed to Phase 3

## Phase 3: Final Assessment (Parallel)

**Goal**: Final polish, quality scoring, and comprehensive security assessment.

### Step 3.1: Launch Final Tasks (Parallel)

Create tasks for active agents and assign in parallel:

1. **TaskCreate** (**If "simplifier" in active_agents**): "Final simplification pass over entire [{scope}]. Review all files for cross-file consistency in naming, patterns, and style. Apply final polish. Report all changes. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "simplifier"
   - **SendMessage** to "simplifier": "Task #{id} assigned: final simplification pass. Start now."

2. **TaskCreate** (**If "architect" in active_agents**): "Prepare comprehensive final quality assessment of [{scope}]. Review architecture, code quality, SOLID principles. Prepare scoring framework. Note: final scores will be assigned after simplifier completes and tests pass."
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: prepare final quality assessment. Start now."

3. **TaskCreate** (**If "code-reviewer" in active_agents**): "Final comprehensive review of [{scope}]. Compare full refactoring scope against Phase 1 baseline. QUALITY: Final confidence-scored review of all changes. SECURITY: Verify all blocking findings from iterations were resolved. Check for cross-file security issues missed in per-iteration reviews. Prepare Security Posture Score (1-10) with justification and baseline comparison table."
   - **TaskUpdate**: assign owner to "code-reviewer"
   - **SendMessage** to "code-reviewer": "Task #{id} assigned: final comprehensive review. Start now."

### Step 3.2: Wait for All Created Phase 3 Tasks to Complete

Monitor TaskList until all created Phase 3 tasks show completed.

### Step 3.3: Final Test Run

1. **TaskCreate**: "Final full test suite run. Report complete pass/fail results."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: final test run. Start now."
2. Wait for completion
3. If failures: coordinate fix with refactor-code agent, re-test

### Step 3.4: Final Scoring

**If "architect" in active_agents:**

1. **TaskCreate**: "Assign final quality scores based on completed refactoring. Provide: Clean Code Score (1-10) with justification{if 'architect' in active_agents: ', Architecture Perfection Score (1-10) with justification'}, summary of improvements across all iterations, remaining potential issues, future recommendations.{if 'code-reviewer' in active_agents: ' Include the Security Posture Score ({security_score}/10) from the code-reviewer agent.'}{if 'simplifier' in active_agents and is_focused: ' Include the Simplification Score (1-10) with justification.'} Create detailed markdown report."
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: final scoring.{if security_score: ' Security Posture Score from code-reviewer: {security_score}/10.'} Include only scores for active agents in the report. Start now."
2. Wait for completion

**If "architect" not in active_agents** (focused run without architect): The team lead compiles the final report directly, including only scores from active agents:
- If "code-reviewer" in active_agents: include Security Posture Score from code-reviewer's final assessment
- If "simplifier" in active_agents: include Simplification Score (1-10) based on simplifier's report
- Always include Clean Code Score based on test agent's coverage and code quality observations

## Phase 4: Report and Cleanup

### Step 4.1: Generate Report

1. Generate timestamp
2. Create `refactor-result-{timestamp}.md` with the final assessment report. If `is_focused`, add a "Focus Mode: {focus_areas joined by ', '}" header at the top of the report. Include only scores from active agents.
3. **If `autonomous_mode`**: Include a "## Convergence Summary" section in the report with: score trajectory table (from blackboard `convergence_data`), convergence reason, iterations run vs max, kept/reverted counts, and the full convergence report (from blackboard `convergence_report`). Note: the workspace directory was already removed in Step 2.2 — all data must come from the blackboard.
4. Use Write tool to save the report

### Step 4.1.5: Commit Final Changes (Conditional)

**Only when `config.postRefactor.commitStrategy` is `"single-final"`**:

1. **Security check**: Before staging, identify and exclude any files matching secret patterns (`.env`, `.env.*`, `credentials.json`, `secrets.*`, `*.pem`, `*.key`, files containing API keys/tokens/passwords). Warn the user if confidential files are detected.
2. Stage all changed files using Bash: `git add -u` (never `git add -A` — it may stage untracked secrets or artifacts)
3. Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit; skip and log "No changes to commit"
4. Commit using Bash with a HEREDOC message:
   ```bash
   git commit -m "$(cat <<'EOF'
   refactor{if is_focused: '(' + focus_areas joined by ',' + ')'}: {scope} — {active scores as 'name score/10' joined by ', '}
   EOF
   )"
   ```
5. If commit fails (e.g., no git, pre-commit hook failure, no changes), log a warning to the user and continue

### Step 4.1.6: Publish Report (Conditional)

**Only when `config.postRefactor.publishReport` is not `"none"`**:

1. Generate the current date as `{date}` (YYYY-MM-DD format)

2. **Determine target repository**: If `config.postRefactor.reportRepository` is set (non-null), use that value as `{target_repo}` (in `owner/repo` format). Otherwise, use the current repository. When publishing to a different repository, prepend the report body with: `> Source repository: {current_owner}/{current_repo}\n\n`

3. **If `publishReport` is `"github-issue"`**:
   - If `{target_repo}` differs from current repo, add `-R {target_repo}` to the `gh` command
   - Run via Bash: `gh issue create --title "Refactor Report: {scope} — {date}" --body "{report_content}" --label "refactoring" [-R {target_repo}]`
   - If the `refactoring` label doesn't exist on the target repo, create it first: `gh label create refactoring --description "Code refactoring" --color "0E8A16" [-R {target_repo}]` (ignore errors if it already exists)
   - Store the created issue URL as `published_url`
   - If `gh` fails (not authenticated, no remote, etc.), log a warning to the user and continue

4. **If `publishReport` is `"github-discussion"`**:
   - Parse `{target_repo}` into `{owner}` and `{repo}` components (split on `/`)
   - Get the repository ID and discussion category ID:
     ```bash
     gh api graphql -f query='{ repository(owner: "{owner}", name: "{repo}") { id discussionCategories(first: 25) { nodes { id name } } } }'
     ```
   - Find the category ID matching `config.postRefactor.discussionCategory` (default: "General")
   - Create the discussion:
     ```bash
     gh api graphql -f query='mutation { createDiscussion(input: { repositoryId: "{repo_id}", categoryId: "{category_id}", title: "Refactor Report: {scope} — {date}", body: "{report_content}" }) { discussion { url } } }'
     ```
   - Store the created discussion URL as `published_url`
   - If any `gh api` call fails, log a warning to the user and continue

### Step 4.1.7: Create Pull Request (Conditional)

**Only when `config.postRefactor.createPR` is `true`**:

1. **Determine branch and fetch latest**:
   ```bash
   CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   TARGET_BRANCH=$(gh repo view --json defaultBranchRef -q '.defaultBranchRef.name' 2>/dev/null || echo "main")
   git fetch origin ${TARGET_BRANCH}
   ```
   - If on `main`, `master`, or `develop`:
     - Generate a scope slug from `{scope}` (lowercase, replace spaces/special chars with hyphens, truncate to 50 chars)
     - Generate `{date}` in YYYY-MM-DD format
     - Create and switch to branch: `git checkout -b "refactor/{scope-slug}-{date}"`

2. **Ensure all changes are committed**: If `commitStrategy` was `"none"` (no commits happened yet):
   - **Security check**: Before staging, identify and exclude any files matching secret patterns (`.env`, `.env.*`, `credentials.json`, `secrets.*`, `*.pem`, `*.key`, files containing API keys/tokens/passwords). Warn the user if confidential files are detected.
   - Stage all changed files: `git add -u` (never `git add -A` — it may stage untracked secrets or artifacts)
   - Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit
   - Commit via Bash with HEREDOC:
     ```bash
     git commit -m "$(cat <<'EOF'
     refactor{if is_focused: '(' + focus_areas joined by ',' + ')'}: {scope} — {active scores as 'name score/10' joined by ', '}
     EOF
     )"
     ```

3. **Ensure branch is current** with the target branch before pushing:
   ```bash
   BEHIND=$(git log --oneline HEAD..origin/${TARGET_BRANCH} | head -5)
   ```
   If `BEHIND` is non-empty, rebase:
   ```bash
   git rebase origin/${TARGET_BRANCH}
   ```
   **Conflict Resolution**: If rebase encounters conflicts:
   1. **HALT the pipeline** — do NOT proceed to push or PR creation.
   2. Show conflicting files (`git diff --name-only --diff-filter=U`) and their conflict markers.
   3. Offer resolution options:
      - **Resolve manually** — User edits files, then `git add` resolved files and `git rebase --continue`.
      - **Abort** — `git rebase --abort` and stop.
      - **Skip commit** — `git rebase --skip` (warn about skipped changes).
   4. State: "The PR creation pipeline is halted. No PR will be created until the rebase completes cleanly."
   5. Repeat for each conflicting commit until the rebase completes or is aborted.

4. **Push branch to remote**: Run via Bash: `git push -u origin HEAD`
   - If push fails, log a warning and continue (PR creation will also fail)

5. **Create the PR** using Bash with `gh pr create`:
   - Build the command:
     ```bash
     gh pr create --title "refactor{if is_focused: '(' + focus_areas joined by ',' + ')'}: {scope}" --body "$(cat <<'EOF'
     ## Refactor Summary

     **Scope**: {scope}
     **Iterations**: {max_iterations}
     {if is_focused: '**Focus**: ' + focus_areas joined by ', '}

     ## Quality Scores
     {only include scores from active agents, e.g.:}
     {if 'architect' in active_agents: '- Clean Code: {clean_code_score}/10'}
     {if 'architect' in active_agents: '- Architecture: {architecture_score}/10'}
     {if 'code-reviewer' in active_agents: '- Security Posture: {security_score}/10'}
     {if 'simplifier' in active_agents and is_focused: '- Simplification: {simplification_score}/10'}

     ## Changes
     {brief summary of improvements from report}

     {if published_url: "Related: {published_url}"}

     ---
     *Generated by refactor plugin v4.0.0*
     EOF
     )" {if prDraft: "--draft"} {if is_focused: '--label "focus:' + focus_areas[0] + '"'}
     ```
   - Store the created PR URL as `pr_url`

6. If any step fails (e.g., no remote, auth issues, `gh` not available), log a warning to the user and continue

### Step 4.2: Report to User

```
Refactoring complete!{if is_focused: ' (Focus: ' + focus_areas joined by ', ' + ')'}

Summary:
- Iterations: {max_iterations}
- Tests: All passing
{if 'code-reviewer' in active_agents: '- Security: All blocking findings resolved'}
{if 'code-explorer' in active_agents: '- Discovery: Codebase map generated'}
- Report: refactor-result-{timestamp}.md

Quality Scores:
{if 'architect' in active_agents: '- Clean Code: X/10'}
{if 'architect' in active_agents: '- Architecture: Y/10'}
{if 'code-reviewer' in active_agents: '- Security Posture: Z/10'}
{if 'simplifier' in active_agents and is_focused: '- Simplification: W/10'}
```

### Session Metrics

Append session metrics to `.refactor/session-metrics.jsonl` using `jq -n` (per /xq rules):

```bash
jq -n \
  --arg sid "{blackboard_scope}" \
  --arg skill "refactor" \
  --arg outcome "{success|partial|failed}" \
  --argjson spawned {agents_spawned} \
  --argjson completed {agents_completed} \
  --argjson failed {agents_failed} \
  '{ts: now|todate, session: $sid, skill: $skill, outcome: $outcome, agents_spawned: $spawned, agents_completed: $completed, agents_failed: $failed}' \
  >> .refactor/session-metrics.jsonl
```

### Step 4.3: Shutdown Team and Cleanup Working Directories

**This step MUST execute regardless of success or failure in prior steps.** If any phase fails or the user interrupts, skip directly here. This is a **finally block**.

1. **Clean up working directories**: Run via Bash: `rm -rf ./*-autonomous/ ./*-workspace/`. These directories are ephemeral and MUST NOT be committed. Remove them unconditionally — even if the autonomous loop already cleaned up, this is a safety net.
2. **Verify no working directories remain**: Run via Bash: `ls -d ./*-autonomous/ ./*-workspace/ 2>/dev/null || true`. If any remain, warn user.
3. Send **shutdown_request** to all spawned teammates (those in `active_agents`) via SendMessage
4. Wait up to **30 seconds** for shutdown confirmations. If any teammate does not respond within 30 seconds, proceed anyway — do not block on unresponsive agents
5. Run TeamDelete. If TeamDelete does not complete within 60 seconds, log "TeamDelete timeout — team `{team_name}` may require manual cleanup" and proceed. Do NOT block the session on TeamDelete failure.
6. If TeamDelete fails or times out, log the error and inform the user: "Team cleanup failed — run `TeamDelete` manually for team `{team_name}`"

## Orchestration Notes

### Team Coordination
- Use **TaskCreate/TaskUpdate/TaskList** for all task management
- **CRITICAL**: After every **TaskUpdate** that assigns an owner, you MUST send a **SendMessage** to that teammate notifying them of the assignment. Teammates only auto-receive SendMessage — they do NOT get notified of TaskUpdate changes. Without this message, the agent will sit idle indefinitely.
- Teammates communicate results back via SendMessage to team lead
- Team lead (this skill) makes all sequencing decisions
- Only the team lead commits code via git — teammates must never run git commit

### Context Distribution
- **Blackboard creation**: The team lead creates the blackboard in Phase 0.2 (at team creation time) and passes the `blackboard_id` to all teammates in their spawn prompts.
- **Blackboard usage**: Agents use `blackboard_read(scope=blackboard_id, key="...")` / `blackboard_write(scope=blackboard_id, author=agent_name, key="...", value="...")` to share context. Standard keys: `codebase_context`, `architect_plan`, `reviewer_baseline`.
- **Write once, read many**: code-explorer writes `codebase_context` after Phase 0.5. All downstream agents read it as needed without the team lead re-distributing it.
- **Inline fallback**: If blackboard is unavailable, embed `codebase_context` directly in task descriptions under a `## Codebase Context` heading.

### Parallel Execution Points
- **Phase 0.5**: code-explorer runs solo (must complete before Phase 1)
- **Phase 1**: Active subset of {refactor-test, architect, code-reviewer} run simultaneously (all read-only analysis)
- **Phase 2.E + 2.F**: code-reviewer runs first (blocking gate), then simplifier runs after
- **Phase 3.1**: Active subset of {simplifier, architect, code-reviewer} run simultaneously
- All other steps are sequential due to data dependencies
- In focused mode, some parallel phases may have only one agent — they still execute correctly as a single-task phase

### Error Handling
- If a teammate goes idle without completing their task: re-send the assignment via SendMessage with the task ID and explicit "start now" instruction
- If a teammate is still idle after a second nudge: report to user and consider implementing the work directly
- If tests fail repeatedly (3+ attempts): ask user for guidance
- If blocking findings persist after 3 fix attempts: ask user for guidance
- Don't proceed past test failures — green tests are gating
- Don't proceed past blocking code review findings (Critical/High severity or confidence >= 80 quality issues) — review is gating

### Team Lifecycle Safety
- **Stale agent detection**: At the start of Phase 0, check for an existing team with the same name pattern (`refactor-*`). If found, run **TeamDelete** on it before creating a new team. This cleans up leaked agents from prior interrupted runs.
- **Guaranteed cleanup**: Step 4.3 (Shutdown Team and Cleanup Working Directories) is a **finally block** — it MUST execute even if prior phases fail, the user cancels, or an unrecoverable error occurs. If you cannot determine whether prior phases succeeded, still execute Step 4.3. This includes removing `*-autonomous/` and `*-workspace/` directories unconditionally.
- **Shutdown timeout**: Never wait indefinitely for shutdown confirmations. After 30 seconds, proceed with TeamDelete regardless. Cooperative shutdown is preferred but not required.
- **No orphaned agents**: After TeamDelete, verify no teammates remain by checking the team config file. If it still exists, warn the user.

### State Management
- Track `refactoring_iteration` counter carefully
- Keep architect's optimization plan accessible for refactor-code agent
- Track which files were modified each iteration for simplifier and code-reviewer
- Maintain list of all changes across iterations for final report
- Preserve code-reviewer's Phase 1 baseline for iteration comparisons
- Maintain `codebase_context` from Phase 0.5 for downstream distribution

### Communication Protocol
- Include iteration number in all task descriptions
- Pass specific file lists and reports between tasks
- Keep user informed at phase/iteration transitions
- Provide brief progress summaries
- Include codebase context reference in task descriptions for agents that need it

## Success Criteria

Refactoring is complete when:
- All tests pass
- If "code-reviewer" in active_agents: all blocking findings (Critical/High severity) resolved
- `max_iterations` refactoring iterations completed
- If "code-explorer" in active_agents: codebase discovery completed and context distributed
- If "simplifier" in active_agents: simplification pass completed per iteration + final pass
- If "code-reviewer" in active_agents: quality + security review completed per iteration + final assessment
- Quality scores assigned for active agents (full run: Clean Code, Architecture, Security Posture; focused run: subset)
- Final assessment report generated
- No functionality changes (only quality improvements)
- Only spawned agents shut down; team gracefully cleaned up

---

Begin the refactoring process now based on: $ARGUMENTS

Start with Phase 0.0 (Configuration Check).

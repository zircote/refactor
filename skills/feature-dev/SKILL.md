---
name: feature-dev
description: Guided feature development with swarm-orchestrated codebase exploration, multi-perspective architecture design, implementation, and quality review. Use this skill when the user wants to build a new feature, add new functionality, implement a capability, or create something that doesn't exist yet. Triggers on requests like "add X", "implement Y", "build Z", "create a new W", "I need a feature for...", or any request to develop new functionality (not refactor existing code).
argument-hint: "[--autonomous] [--iterations=N] <feature description or requirement>"
---

# Feature Development Skill (Swarm Orchestration)

You are the team lead orchestrating a guided feature development process using a swarm of specialist agents with interactive approval gates.

## Overview

This skill implements a comprehensive feature development workflow using specialist agents from the refactor plugin, coordinated as a swarm team:
- **code-explorer** — Deep codebase exploration: traces patterns, maps architecture, identifies integration points (runs as N parallel instances)
- **architect** — Designs feature architecture with implementation blueprints (runs as N parallel instances)
- **code-reviewer** — Focus-area quality review: simplicity/DRY, bugs/correctness, conventions/abstractions (runs as N parallel instances)
- **feature-code** — Implements the chosen architecture following codebase conventions
- **refactor-code** — Available for fix-up tasks if needed
- **refactor-test** — Runs tests to verify implementation correctness
- **simplifier** — Available for post-implementation polish if needed
- **convergence-reporter** — Analyzes autonomous loop results and produces convergence reports (autonomous mode only)
- **test-planner** — *(optional)* Produces JSON test plans using formal test design techniques for new feature code
- **test-rigor-reviewer** — *(optional)* Reviews generated tests for scientific rigor, scoring quality 0.0–1.0
- **coverage-analyst** — *(optional)* Runs native coverage tools on new feature code to verify test completeness

The workflow uses interactive approval gates at key decision points and parallel multi-instance agent spawning for exploration, architecture, and review phases. In **autonomous mode** (`--autonomous`), Phase 5 (Implementation) is replaced by a Karpathy autoresearch-style convergence loop with keep/discard gating, composite scoring, and automatic convergence detection.

## Arguments

**$ARGUMENTS**: Optional flags and feature description or requirement to implement.

Parse `$ARGUMENTS` for the following **before** any other processing:

- `--autonomous` — Enable autonomous convergence mode. When present, extract and remove from `$ARGUMENTS` and set `autonomous_mode = true`. Phase 5 is replaced by the autonomous convergence loop (see `references/autonomous-algorithm.md`). If not present, set `autonomous_mode = false`.

- `--iterations=N` — Override the max iteration count for autonomous mode. `N` must be a positive integer (1-20). If present, extract and remove from `$ARGUMENTS` and store as `cli_iterations`. Only meaningful when combined with `--autonomous`.

After extracting flags, the remaining `$ARGUMENTS` is the feature description. This will be refined through the elicitation protocol in Phase 1.

**Autonomous mode settings**: `max_iterations = cli_iterations ?? config.autonomous.maxIterations ?? 20`. Load convergence config: `convergence = config.autonomous.convergence`. Load score weights: `score_weights = config.autonomous.scoreWeights`.

## Phase 0.0: Configuration Check

### Step 0.0.1: Load or Create Configuration

1. Attempt to read `.claude/refactor.config.json` from the project root
2. **If file exists**: Parse the JSON silently. Merge with defaults (any missing fields use defaults). Store as `config`. Proceed to Phase 0.1.
3. **If file does NOT exist**: Create with defaults and proceed.

**Config schema v4.0** — feature-dev uses the `featureDev` and (if autonomous) `autonomous` sections:
```json
{
  "version": "4.0",
  "iterations": 3,
  "postRefactor": { "..." },
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

**Defaults** (applied silently when `featureDev` key is missing):
```json
{
  "explorerCount": 3,
  "architectCount": 3,
  "reviewerCount": 3,
  "commitStrategy": "single-final",
  "createPR": false,
  "prDraft": true
}
```

## Phase 0.1: Initialize Team and Blackboard

1. Use **TeamCreate** to create the feature development team:
   ```
   TeamCreate with team_name: "feature-dev-team"
   ```

2. Create a shared blackboard for cross-agent context. Derive `scope-slug` from the feature description: lowercase, replace spaces and special characters with hyphens, truncate to 40 characters (e.g., "add webhook support" → "add-webhook-support"):
   ```
   blackboard_create with task_id: "feature-dev-{scope-slug}" and TTL appropriate for the session
   ```
   Store the returned blackboard ID as `blackboard_id`.

3. Use **TaskCreate** to create high-level phase tasks:
   - "Phase 1: Discovery + Elicitation"
   - "Phase 2: Codebase Exploration"
   - "Phase 3: Clarifying Questions"
   - "Phase 4: Architecture Design"
   - "Phase 5: Implementation"
   - "Phase 6: Quality Review"
   - "Phase 7: Summary + Cleanup"

## Phase 0.2: Task Discovery Protocol Template

All teammates receive this protocol in their spawn prompt:

```
BLACKBOARD: {blackboard_id}
Use blackboard_read(task_id="{blackboard_id}", key="...") to read shared context written by other agents.
Use blackboard_write(task_id="{blackboard_id}", key="...", value="...") to share your findings.

TASK DISCOVERY PROTOCOL:
1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you (owner = your name).
2. Call TaskGet on your assigned task to read the full description.
3. Work on the task.
4. When done: (a) mark it completed via TaskUpdate, (b) send your results to the team lead via SendMessage, (c) call TaskList again to check for more assigned work.
5. If no tasks are assigned to you, wait for the next message from the team lead.
6. NEVER commit code via git — only the team lead commits.
```

**All agents are spawned on-demand** when their phase begins — not upfront. This avoids wasting resources if the user abandons after elicitation. code-explorer instances spawn in Phase 2, architect instances in Phase 4, feature-code and refactor-test in Phase 5, and code-reviewer instances in Phase 6.

## Phase 1: Discovery + Elicitation

**Goal**: Achieve 95% confidence in understanding the feature before proceeding.

### 95% Confidence Elicitation Protocol

1. Parse `$ARGUMENTS` as the initial feature description.

2. Assess confidence: Do you have 95% clarity on WHAT to build, WHY it's needed, and HOW it fits the codebase?

3. **Confidence assessment criteria** (all must be YES for 95%):
   - [ ] Can state the problem in one sentence
   - [ ] Can list acceptance criteria (at least 3)
   - [ ] Know scope boundaries (what's excluded)
   - [ ] Understand key user interactions
   - [ ] Know integration touchpoints
   - [ ] Aware of critical constraints

4. If confidence < 95%, use **AskUserQuestion** to elicit missing details. **Ask only about the gaps** — do not re-ask dimensions the user already covered. Target these dimensions as needed:
   - **Problem statement**: What problem does this solve? Who is affected?
   - **Scope boundaries**: What is IN scope vs explicitly OUT of scope?
   - **Acceptance criteria**: How will we know it's done? What does "working" look like?
   - **User-facing behavior**: What should the user experience? Inputs, outputs, interactions?
   - **Edge cases**: What happens with invalid input, empty state, errors, concurrent use?
   - **Integration points**: What existing systems/modules does this touch?
   - **Constraints**: Performance requirements, backward compatibility, platform support?
   - **Non-functional**: Security, accessibility, observability needs?

   **Graduated elicitation** — match question count to the actual gap size:
   - **High confidence (80-94%)**: Ask 1-3 targeted questions about specific remaining gaps. Do not over-elicit when the user has been thorough.
   - **Medium confidence (50-79%)**: Ask 4-8 focused questions organized by dimension.
   - **Low confidence (<50%)**: Ask 8-15 questions covering all unaddressed dimensions.
   - For implementation details that architects can resolve in Phase 4, note them as "deferred to architecture" rather than asking the user. Only ask users about *requirements* gaps, not *design* gaps.

5. After each user response, re-assess confidence. If still < 95%, ask follow-up questions on remaining gaps only.

6. **Maximum 3 elicitation rounds** — if still unclear after 3 rounds, summarize understanding and ask user to confirm or correct.

7. Write confirmed feature spec to blackboard:
   ```
   blackboard_write(task_id="{blackboard_id}", key="feature_spec", value="{structured feature specification}")
   ```

8. Only proceed to Phase 2 when confidence >= 95% OR user explicitly says "proceed".

## Phase 2: Codebase Exploration

**Goal**: Understand relevant existing code and patterns deeply.

### Step 2.0: Scale Instance Counts to Feature Complexity

Before spawning, assess whether the feature warrants the configured number of instances. For simple, fully-specified features (confidence was 90%+ with zero elicitation), reduce counts:
- **Simple features** (single endpoint, trivial logic, clear integration): 1 explorer, 1 architect, 1-2 reviewers
- **Medium features** (multiple components, some integration complexity): 2 explorers, 2 architects, 2-3 reviewers
- **Complex features** (cross-cutting, multiple systems, significant design decisions): use full configured counts

Store the effective counts as `effective_explorerCount`, `effective_architectCount`, `effective_reviewerCount`.

### Step 2.1: Spawn Explorer Instances

Spawn `effective_explorerCount` (default from config: 3, scaled in Step 2.0) code-explorer instances in parallel, each with a different focus:

```
For i in 1..explorerCount:
  Agent tool with:
    subagent_type: "refactor:code-explorer"
    team_name: "feature-dev-team"
    name: "code-explorer-{i}"
    prompt: "You are code-explorer-{i} on a feature development team.

    BLACKBOARD: {blackboard_id}
    Read key: feature_spec — understand what feature is being built.
    Write key: explorer_{i}_findings — write your exploration findings.

    Your focus: {focus_for_instance_i}

    {TASK DISCOVERY PROTOCOL}"
```

**Focus assignment examples** (adapt to the specific feature):
- Explorer 1: "Find features similar to [{feature}] and trace their implementation comprehensively"
- Explorer 2: "Map the architecture, abstractions, and module boundaries for [{feature area}]"
- Explorer 3: "Analyze integration points, extension mechanisms, and testing patterns relevant to [{feature}]"

### Step 2.2: Create and Assign Tasks

For each explorer instance, create a task:
```
TaskCreate: "Explore the codebase for [{feature}]. Focus: {focus}. Read feature_spec from blackboard. Include a list of 5-10 essential files with rationale."
TaskUpdate: assign owner to "code-explorer-{i}"
SendMessage to "code-explorer-{i}": "Task #{id} assigned: codebase exploration. Start now."
```

### Step 2.3: Wait and Consolidate

1. Wait for all explorer tasks to complete.
2. Read all `explorer_{i}_findings` from the blackboard.
3. Read all files identified by explorers as essential (the team lead reads these to build deep understanding).
4. Consolidate findings into a unified codebase context.
5. Write consolidated context to blackboard:
   ```
   blackboard_write(task_id="{blackboard_id}", key="codebase_context", value="{consolidated context}")
   ```
6. Present comprehensive summary of findings and patterns to the user.

## Phase 3: Clarifying Questions

**Goal**: Fill in gaps surfaced by codebase exploration.

**CRITICAL**: This phase is NOT redundant with Phase 1. Phase 1 elicits WHAT/WHY before code exploration. Phase 3 elicits HOW/WHERE after understanding the codebase.

### Actions

1. Review the codebase findings alongside the feature spec.
2. Identify ambiguities surfaced by exploration:
   - How should the feature integrate with discovered patterns?
   - Are there design preferences given the existing architecture?
   - Are there edge cases visible now that weren't obvious before?
   - Are there backward compatibility concerns?
   - Which existing abstractions should be reused vs extended?
3. **If ambiguities exist**: Present questions to the user in a clear, organized list using **AskUserQuestion**. Wait for answers before proceeding.
4. **If no ambiguities exist**: Inform the user that exploration revealed no additional questions, summarize the key patterns discovered, and proceed to Phase 4. Write a clarifications entry noting "No additional clarifications needed — codebase patterns are clear."
5. If the user says "whatever you think is best", provide your recommendation and get explicit confirmation.
6. Write clarifications to blackboard:
   ```
   blackboard_write(task_id="{blackboard_id}", key="clarifications", value="{user answers or 'No additional clarifications needed'}")
   ```

## Phase 4: Architecture Design

**Goal**: Design multiple implementation approaches and let the user choose.

### Step 4.1: Spawn Architect Instances

Spawn `effective_architectCount` (default from config: 3, scaled in Phase 2 Step 2.0) architect instances in parallel, each with a different design philosophy:

```
For i in 1..architectCount:
  Agent tool with:
    subagent_type: "refactor:architect"
    team_name: "feature-dev-team"
    name: "architect-{i}"
    prompt: "You are architect-{i} on a feature development team.

    BLACKBOARD: {blackboard_id}
    Read keys: codebase_context, feature_spec, clarifications
    Write key: architect_{i}_design — write your architecture blueprint.

    Your design philosophy: {philosophy_for_instance_i}

    {TASK DISCOVERY PROTOCOL}"
```

**Philosophy assignment**:
- Architect 1: "Minimal changes — smallest change that works, maximum reuse of existing code"
- Architect 2: "Clean architecture — best maintainability, elegant abstractions, future-proof"
- Architect 3: "Pragmatic balance — speed + quality, practical trade-offs"

### Step 4.2: Create and Assign Tasks

For each architect instance, create a task:
```
TaskCreate: "Design feature architecture for [{feature}]. Philosophy: {philosophy}. Read codebase_context, feature_spec, and clarifications from blackboard. Provide a complete implementation blueprint."
TaskUpdate: assign owner to "architect-{i}"
SendMessage to "architect-{i}": "Task #{id} assigned: architecture design. Start now."
```

### Step 4.3: Wait, Compare, and Present

1. Wait for all architect tasks to complete.
2. Read all `architect_{i}_design` from the blackboard.
3. Review all approaches and form your recommendation.
4. **Present to user** using **AskUserQuestion**:
   - Brief summary of each approach
   - Trade-offs comparison
   - **Your recommendation with reasoning**
   - Concrete implementation differences
5. **Ask user which approach they prefer**.
6. Write chosen architecture to blackboard:
   ```
   blackboard_write(task_id="{blackboard_id}", key="chosen_architecture", value="{selected blueprint}")
   ```

## Phase 5: Autonomous Convergence Implementation (when `autonomous_mode = true`)

**Replaces the standard Phase 5 when `--autonomous` is active. All other phases (0-4, 6, 7) execute identically, including all interactive gates (elicitation, clarification, architecture selection).**

**Goal**: Iteratively implement the feature with composite scoring, keep/discard gating, and automatic convergence detection. Unlike refactor mode, tests are **mutable** — new functionality needs new tests.

### Step 5.0-auto: Spawn Agents and Initialize

1. Spawn `feature-code`, `refactor-test`, `code-reviewer`, and `convergence-reporter` (same spawn templates as standard mode, plus convergence-reporter):
   - feature-code: reads codebase_context, chosen_architecture, clarifications, feature_spec from blackboard
   - refactor-test: reads codebase_context from blackboard
   - code-reviewer: reads codebase_context from blackboard
   - convergence-reporter: reads convergence_data from blackboard (spawned deferred at finalization)

2. Get user approval: Use **AskUserQuestion**: "Ready to implement using the {chosen approach} architecture in autonomous mode (max {max_iterations} iterations)? The system will iterate until convergence — you'll review the final result."

3. Create workspace: `mkdir -p {scope-slug}-autonomous`
4. Set `workspace = {scope-slug}-autonomous`
5. Initialize results log: `bash scripts/results_log.sh append {workspace}/results.tsv 0 0 0 "baseline" "Pending evaluation"`
6. Detect and clean stale branches: `bash scripts/git_snapshot.sh detect-stale`
7. Create baseline snapshot: `bash scripts/git_snapshot.sh baseline`

### Step 5.1-auto: Baseline Score

1. Create `{workspace}/iteration-0/` directory
2. Run tests (there may be no feature-specific tests yet — that's expected for baseline):
   - **TaskCreate**: "Run the test suite and write results to {workspace}/iteration-0/test-results.json in autonomous mode format. You MAY create tests if none exist yet for this feature area."
     - Assign to "refactor-test", send message
     - Wait for completion
3. Run Mode 5 scoring:
   - **TaskCreate**: "Mode 5 autonomous scoring of [{scope}]. Write scores to {workspace}/iteration-0/review-scores.json."
     - Assign to "code-reviewer", send message
     - Wait for completion
4. Compute baseline: `bash scripts/score.sh {workspace} 0 {score_weights.tests} {score_weights.quality} {score_weights.security}`
5. Store as `score_0`, set `best = {version: 0, score: score_0}`
6. Update log: `bash scripts/results_log.sh append {workspace}/results.tsv 0 {score_0} {score_0} "baseline" "Initial evaluation"`

### Step 5.2-auto: Convergence Loop

For `i = 1` to `max_iterations`:

#### 5.2.A: MODIFY — Implement Iteration

1. **TaskCreate**: "Iteration {i}: Implement the feature [{feature}] following the chosen architecture. Read codebase_context, chosen_architecture, clarifications, and feature_spec from blackboard. {If i > 1: 'Build on previous iteration. Focus on addressing weaknesses from prior scoring.'} Write clean, well-integrated code."
   - Assign to "feature-code", send message, wait for completion
2. **TaskCreate**: "Iteration {i}: Write and run tests for [{feature}]. You MAY create new tests and modify existing feature tests (tests are MUTABLE in feature-dev autonomous mode). Write results to {workspace}/iteration-{i}/test-results.json."
   - Assign to "refactor-test", send message, wait for completion
3. If test failures: coordinate fix with feature-code, re-test (max 3 attempts)
4. Track `changelog` from agent reports

#### 5.2.B: EVALUATE — Score the Iteration

1. Create `{workspace}/iteration-{i}/` directory (if not already created by test agent)
2. Ensure test-results.json exists in workspace
3. **TaskCreate**: "Mode 5 autonomous scoring. Review all changes for [{feature}]. Write to {workspace}/iteration-{i}/review-scores.json."
   - Assign to "code-reviewer", send message, wait for completion
4. Compute: `bash scripts/score.sh {workspace} {i} {score_weights.tests} {score_weights.quality} {score_weights.security}`
5. Store as `score_i`

#### 5.2.C: KEEP or DISCARD

- **If `score_i > best.score`**:
  - `bash scripts/git_snapshot.sh create {i}`
  - `best = {version: i, score: score_i}`, `action = "kept"`
  - Inform user: "Iteration {i}: score {score_i} (improved). KEPT."

- **If `score_i <= best.score`**:
  - `bash scripts/git_snapshot.sh restore {best.version}`
  - `action = "reverted"`
  - Inform user: "Iteration {i}: score {score_i} (no improvement). REVERTED to v{best.version}."

#### 5.2.D: LOG

`bash scripts/results_log.sh append {workspace}/results.tsv {i} {score_i} {best.score} {action} "{changelog}"`

#### 5.2.E: CONVERGENCE CHECK

Same conditions as refactor autonomous mode (see refactor SKILL.md Phase 2 Step 2.1.E):
1. Perfect: `best.score >= convergence.perfectScore` → STOP
2. Stuck: `bash scripts/results_log.sh check-stuck {workspace}/results.tsv {convergence.maxConsecutiveReverts}` → STOP
3. Plateau: `bash scripts/results_log.sh check-plateau {workspace}/results.tsv {convergence.plateauWindow} {convergence.plateauDelta}` → STOP
4. Max iterations → STOP
5. Otherwise: continue

### Step 5.3-auto: Finalize

1. Restore best: `bash scripts/git_snapshot.sh restore {best.version}`
2. Write convergence data to blackboard (workspace, best_version, best_score, total_iterations, convergence_reason)
3. Spawn convergence-reporter, create task, wait for report
4. Clean up: `bash scripts/git_snapshot.sh cleanup`
5. Inform user: "Autonomous implementation complete. {i} iterations, best score: {best.score}. Proceeding to quality review."
6. **Proceed to Phase 6** (Quality Review) as normal.

---

## Phase 5: Standard Implementation (when `autonomous_mode = false`)

**Goal**: Build the feature following the chosen architecture.

**DO NOT START WITHOUT USER APPROVAL.**

### Step 5.0: Spawn Implementation Agents

Spawn `feature-code` and `refactor-test` now (deferred from Phase 0 to avoid wasting resources):

```
Agent tool with:
  subagent_type: "refactor:feature-code"
  team_name: "feature-dev-team"
  name: "feature-code"
  prompt: "You are the feature implementation agent on a feature development team.

  BLACKBOARD: {blackboard_id}
  Read keys: codebase_context, chosen_architecture, clarifications, feature_spec
  Write key: implementation_report

  {TASK DISCOVERY PROTOCOL}"
```

```
Agent tool with:
  subagent_type: "refactor:refactor-test"
  team_name: "feature-dev-team"
  name: "refactor-test"
  prompt: "You are the test agent on a feature development team.

  BLACKBOARD: {blackboard_id}
  Read key: codebase_context

  {TASK DISCOVERY PROTOCOL}"
```

### Step 5.1: Get Approval

Use **AskUserQuestion**: "Ready to implement using the {chosen approach} architecture. Proceed?"

### Step 5.2: Implement

1. **TaskCreate**: "Implement the feature [{feature}] following the chosen architecture blueprint. Read codebase_context, chosen_architecture, clarifications, and feature_spec from the blackboard. Follow codebase conventions strictly. Write clean, well-integrated code. Write implementation_report to blackboard when done."
   - **TaskUpdate**: assign owner to "feature-code"
   - **SendMessage** to "feature-code": "Task #{id} assigned: implement feature. Start now."

2. Wait for completion.
3. Read implementation report from blackboard.

### Step 5.3: Write Tests for New Feature

1. **TaskCreate**: "Write tests for the newly implemented feature [{feature}]. Read codebase_context from the blackboard to understand existing test patterns and frameworks. Create tests covering: core functionality, edge cases, error handling, and integration points. Follow the project's existing test conventions."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: write tests for new feature. Start now."
2. Wait for completion.

### Step 5.4: Test Verification

1. **TaskCreate**: "Run the complete test suite (including newly written tests). Report pass/fail status. If failures: provide detailed failure report."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: run full test suite. Start now."
2. Wait for completion.
3. If failures: coordinate fixes with feature-code agent, re-test (max 3 attempts, then ask user).

## Phase 6: Quality Review

**Goal**: Multi-perspective quality review of the implemented feature.

### Step 6.1: Spawn Reviewer Instances

Spawn `effective_reviewerCount` (default from config: 3, scaled in Phase 2 Step 2.0) code-reviewer instances in parallel, each with a different focus:

```
For i in 1..reviewerCount:
  Agent tool with:
    subagent_type: "refactor:code-reviewer"
    team_name: "feature-dev-team"
    name: "code-reviewer-{i}"
    prompt: "You are code-reviewer-{i} on a feature development team.

    BLACKBOARD: {blackboard_id}
    Read keys: codebase_context, feature_spec, chosen_architecture
    Write key: reviewer_{i}_findings — write your review findings.

    Your review focus: {focus_for_instance_i}

    Use Mode 4 — Feature Development Review.

    {TASK DISCOVERY PROTOCOL}"
```

**Focus assignment**:
- Reviewer 1: "Simplicity / DRY / Elegance"
- Reviewer 2: "Bugs / Functional Correctness"
- Reviewer 3: "Conventions / Abstractions"

### Step 6.2: Create and Assign Tasks

For each reviewer instance, create a task:
```
TaskCreate: "Review the implemented feature [{feature}]. Focus: {focus}. Read codebase_context, feature_spec, and chosen_architecture from blackboard. Use confidence scoring >= 80."
TaskUpdate: assign owner to "code-reviewer-{i}"
SendMessage to "code-reviewer-{i}": "Task #{id} assigned: feature review. Start now."
```

### Step 6.2.1: Test Architecture Review (Optional)

**If the user requested test quality analysis**, or if the implemented feature contains test files, spawn test-architect agents in parallel with code reviewers:

1. **Spawn test-rigor-reviewer**:
   ```
   Agent tool with:
     subagent_type: "refactor:test-rigor-reviewer"
     team_name: "feature-dev-team"
     name: "test-rigor-reviewer"
     prompt: "You are the test rigor reviewer on a feature dev team.
     BLACKBOARD: {blackboard_id}
     Read keys: codebase_context, feature_spec
     Write key: test_rigor_report
     {TASK DISCOVERY PROTOCOL}"
   ```

2. **Spawn coverage-analyst**:
   ```
   Agent tool with:
     subagent_type: "refactor:coverage-analyst"
     team_name: "feature-dev-team"
     name: "coverage-analyst"
     prompt: "You are the coverage analyst on a feature dev team.
     BLACKBOARD: {blackboard_id}
     Read key: codebase_context
     Write key: coverage_report
     {TASK DISCOVERY PROTOCOL}"
   ```

3. **TaskCreate** for test-rigor-reviewer: "Review all test files for the implemented feature. Score rigor 0.0-1.0 per test."
4. **TaskCreate** for coverage-analyst: "Run coverage analysis for the implemented feature code. Report gaps."

### Step 6.3: Consolidate and Present

1. Wait for all reviewer tasks (and test-architect tasks if spawned) to complete.
2. Read all `reviewer_{i}_findings` from the blackboard.
3. If test-architect agents ran: read `test_rigor_report` and `coverage_report` from blackboard.
4. Consolidate findings and identify highest-severity issues.
5. **Present to user** using **AskUserQuestion**:
   - Consolidated findings grouped by severity
   - {If test-architect ran: "Test rigor score: X/1.0, Coverage: Y%"}
   - Your recommendation on what to fix
   - Options: "Fix critical issues now", "Fix all issues", "Proceed as-is"
5. Address issues based on user decision:
   - If fixes needed: create tasks for feature-code agent, re-test after fixes.

## Phase 7: Summary + Cleanup

### Step 7.1: Commit (Conditional)

**If `config.featureDev.commitStrategy` is `"single-final"`**:
1. Stage all changes: `git add -u` for modified files, then `git add` each new file from the implementation report's "Files Created" list. Do NOT use `git add -A` (may include unintended files).
2. Check for staged changes: `git diff --cached --quiet` — if exit code 0, skip
3. Commit:
   ```bash
   git commit -m "$(cat <<'EOF'
   feat: {brief feature description}
   EOF
   )"
   ```

### Step 7.2: Create PR (Conditional)

**If `config.featureDev.createPR` is `true`**:
1. Create feature branch if on main/master: `git checkout -b "feature/{scope-slug}"`
2. Push: `git push -u origin HEAD`
3. Create PR:
   ```bash
   gh pr create --title "feat: {feature description}" --body "$(cat <<'EOF'
   ## Summary
   {what was built}

   ## Architecture
   {chosen approach and rationale}

   ## Files Changed
   {list from implementation report}

   ## Review Notes
   {consolidated reviewer findings and resolutions}

   ---
   *Generated by refactor plugin v4.0.0 — feature-dev skill*
   EOF
   )" {if prDraft: "--draft"}
   ```

### Step 7.3: Summary

Present to user:
```
Feature development complete!

Summary:
- Feature: {description}
- Architecture: {chosen approach}
- Files created: {count}
- Files modified: {count}
- Tests: All passing
- Review: {issues found / resolved}
{if autonomous_mode: '- Autonomous: {total_iterations} iterations, {kept_count} kept, {reverted_count} reverted, final score {best.score}'}
{if autonomous_mode: '- Convergence: {convergence_reason}'}
{if pr_url: '- PR: {pr_url}'}

Key decisions made:
- {decision 1}
- {decision 2}

Suggested next steps:
- {suggestion 1}
- {suggestion 2}
```

### Step 7.4: Shutdown Team

1. Send **shutdown_request** to all spawned teammates via SendMessage.
2. Wait for shutdown confirmations.
3. Use **TeamDelete** to clean up the team.

## Orchestration Notes

### Team Coordination
- Use **TaskCreate/TaskUpdate/TaskList** for all task management
- **CRITICAL**: After every **TaskUpdate** that assigns an owner, you MUST send a **SendMessage** to that teammate. Without this message, the agent will sit idle.
- Teammates communicate results back via SendMessage to team lead
- Team lead (this skill) makes all sequencing decisions
- Only the team lead commits code via git

### Multi-Instance Spawning Pattern
- Agents spawned with unique names: `code-explorer-1`, `code-explorer-2`, `code-explorer-3`
- Same `subagent_type: "refactor:code-explorer"` — loads the shared agent definition
- Each instance gets a different focus/prompt
- Instance count from config: `config.featureDev.explorerCount`, `.architectCount`, `.reviewerCount`
- Each writes findings to blackboard with unique key: `explorer_1_findings`, `architect_2_design`, `reviewer_3_findings`

### Blackboard Keys

| Key | Writer | Readers | Phase |
|-----|--------|---------|-------|
| `feature_spec` | team lead | all agents | 1 |
| `explorer_{i}_findings` | code-explorer-{i} | team lead | 2 |
| `codebase_context` | team lead (consolidated) | all agents | 2+ |
| `clarifications` | team lead | architects, feature-code | 3 |
| `architect_{i}_design` | architect-{i} | team lead | 4 |
| `chosen_architecture` | team lead | feature-code, reviewers | 4+ |
| `reviewer_{i}_findings` | code-reviewer-{i} | team lead | 6 |

### Context Distribution
- **Blackboard is primary**: All agents read context from the blackboard using their documented read keys
- **Write once, read many**: Feature spec written in Phase 1, codebase context in Phase 2 — all downstream agents read as needed
- **Inline fallback**: If blackboard is unavailable, embed context directly in task descriptions

### Interactive Gates
- **Phase 1**: 95% confidence elicitation — must understand the feature
- **Phase 3**: Clarifying questions — must resolve codebase-specific ambiguities
- **Phase 4**: Architecture selection — user picks the approach
- **Phase 5**: Implementation approval — user confirms readiness
- **Phase 6**: Review disposition — user decides what to fix

### Error Handling
- If a teammate goes idle: re-send assignment via SendMessage with explicit "start now"
- If still idle after second nudge: report to user and consider direct implementation
- If tests fail repeatedly (3+ attempts): ask user for guidance
- If blackboard write fails: fall back to inline context in task descriptions

---

Begin the feature development process now based on: $ARGUMENTS

Start with Phase 0.0 (Configuration Check).

---
name: refactor
description: Automated iterative code refactoring with swarm-orchestrated specialist agents including deep codebase discovery, confidence-scored code review, and security analysis
argument-hint: "[--iterations=N] [--focus=<area>[,area...]] [path or description]"
---

# Refactor Skill (Swarm Orchestration)

You are the team lead orchestrating an automated, iterative code refactoring process using a swarm of specialist agents.

## Overview

This skill implements a comprehensive refactoring workflow using 6 specialist agents coordinated as a swarm team:
- **code-explorer** — Deep codebase discovery: traces entry points, maps execution flows, catalogs dependencies and patterns
- **architect** — Reviews architecture, identifies improvements, scores quality
- **code-reviewer** — Confidence-scored quality review AND security analysis (regressions, secrets, OWASP), replaces per-iteration security agent
- **refactor-test** — Analyzes coverage, runs tests, reports failures
- **refactor-code** — Implements optimizations, fixes test failures and blocking findings
- **simplifier** — Simplifies changed code for clarity and consistency

The workflow uses parallel execution where possible and iterates `max_iterations` times for continuous improvement. All agents share codebase context discovered in Phase 0.5.

## Arguments

**$ARGUMENTS**: Optional flags and specification of what to refactor.

Parse `$ARGUMENTS` for the following **before** any other processing:

- `--iterations=N` — Override the configured iteration count for this run. `N` must be a positive integer (1-10). If present, extract and remove it from `$ARGUMENTS` and store as `cli_iterations`. The remaining text is the refactoring scope.

- `--focus=<area>[,area...]` — Constrain the run to specific disciplines. If present, extract and remove it from `$ARGUMENTS` and process as follows:
  1. Split the value on commas to get a list of focus areas
  2. Validate each value against the allowed set: `{security, architecture, simplification, code, discovery}`
  3. If any value is invalid, report the error to the user and stop: "Invalid focus area '{value}'. Valid values: security, architecture, simplification, code, discovery"
  4. Derive `active_agents` from the focus areas using the spawn matrix:
     - `security` → adds `code-reviewer`
     - `architecture` → adds `architect`
     - `simplification` → adds `simplifier`
     - `code` → adds `architect` + `code-reviewer`
     - `discovery` → adds `code-explorer`
     - `refactor-test` and `refactor-code` are **always** included regardless of focus
  5. For multi-focus (e.g., `--focus=security,architecture`), take the **union** of all focus-specific agents plus the always-included pair
  6. Set `is_focused = true`
  7. If `--focus` is not provided: set `is_focused = false` and `active_agents = {code-explorer, architect, refactor-test, refactor-code, simplifier, code-reviewer}` (all 6)

After extracting flags, the remaining arguments are interpreted as:
- If empty: refactor the entire codebase
- If file path: refactor specific file(s)
- If description: refactor code matching description

## Phase 0.0: Configuration Check

### Step 0.0.1: Load or Create Configuration

1. Attempt to read `.claude/refactor.config.json` from the project root
2. **If file exists**: Parse the JSON silently. Merge with defaults (any missing fields use defaults). Store as `config`. Proceed to Phase 0.
3. **If file does NOT exist**: Run interactive setup (Step 0.0.2)

### Step 0.0.2: Interactive Setup (First Run Only)

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
     "version": "2.0",
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
2. Use the **Write** tool to save to `.claude/refactor.config.json`
3. Store as `config`. Proceed to Phase 0.

**Default config** (equivalent to zero-config behavior):
```json
{
  "version": "2.0",
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

### Step 0.1: Understand Scope

1. Parse $ARGUMENTS to determine refactoring scope (flags already extracted in Arguments section)
2. If unclear, ask user to clarify what should be refactored
3. Set `scope` variable to the determined scope
4. Set `max_iterations = cli_iterations ?? (is_focused ? 1 : config.iterations) ?? 3` (CLI flag takes precedence; focused runs default to 1 iteration; unfocused uses config, then default of 3)
5. Set `refactoring_iteration = 0`

### Step 0.2: Create Swarm Team

1. Use **TeamCreate** to create the refactoring team:
   ```
   TeamCreate with team_name: "refactor-team"
   ```

2. Use **TaskCreate** to create the high-level phase tasks:
   - "Phase 0.5: Deep codebase discovery" (if code-explorer in active_agents)
   - "Phase 1: Foundation analysis (parallel)"
   - For i in 1..max_iterations: "Phase 2: Iteration {i} of {max_iterations}"
   - "Phase 3: Final assessment"
   - "Phase 4: Report and cleanup"

### Step 0.3: Spawn Teammates

Spawn only agents in `active_agents` using the **Agent tool** with `team_name: "refactor-team"`. Launch all selected agents in parallel.

Each teammate receives the same task-discovery protocol in their spawn prompt. This is critical for preventing stuck agents:

```
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

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

2. **architect** teammate (**If "architect" in active_agents**):
   ```
   Agent tool with:
     subagent_type: "refactor:architect"
     team_name: "refactor-team"
     name: "architect"
     prompt: "You are the architect agent on a refactoring swarm team. The scope is: {scope}.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

3. **code-reviewer** teammate (**If "code-reviewer" in active_agents**):
   ```
   Agent tool with:
     subagent_type: "refactor:code-reviewer"
     team_name: "refactor-team"
     name: "code-reviewer"
     prompt: "You are the code reviewer agent on a refactoring swarm team. The scope is: {scope}.
     You handle BOTH quality review (bugs, logic, conventions with confidence scoring) AND security review (regressions, secrets, OWASP with severity classification).

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

4. **refactor-test** teammate (**Always spawned**):
   ```
   Agent tool with:
     subagent_type: "refactor:refactor-test"
     team_name: "refactor-team"
     name: "refactor-test"
     prompt: "You are the test agent on a refactoring swarm team. The scope is: {scope}.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

5. **refactor-code** teammate (**Always spawned**):
   ```
   Agent tool with:
     subagent_type: "refactor:refactor-code"
     team_name: "refactor-team"
     name: "refactor-code"
     prompt: "You are the code agent on a refactoring swarm team. The scope is: {scope}.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

6. **simplifier** teammate (**If "simplifier" in active_agents**):
   ```
   Agent tool with:
     subagent_type: "refactor:simplifier"
     team_name: "refactor-team"
     name: "simplifier"
     prompt: "You are the simplifier agent on a refactoring swarm team. The scope is: {scope}.

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

Attempt to write `codebase_context` to the Atlatl blackboard for cross-agent access:

1. **Try blackboard** (preferred): Call `blackboard_create` with a task-scoped key, then `blackboard_write` with the codebase map content. If successful, downstream agents read via `blackboard_read`.
2. **Fallback** (if blackboard unavailable): Include `codebase_context` directly in every downstream task description under a `## Codebase Context` section.

### Step 0.5.4: Checkpoint

- Inform user: "Phase 0.5 complete. Codebase discovery finished. {summary of key findings — entry points, layers, patterns}. Starting foundation analysis."

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

### Step 1.2: Wait for All Created Phase 1 Tasks to Complete

- Monitor TaskList until all created Phase 1 tasks show status: completed
- Read the results from messages received from active teammates
- Verify refactor-test agent confirms all tests are passing before proceeding
- If "code-reviewer" in active_agents: record code-reviewer's baseline for use in iteration reviews

### Step 1.3: Checkpoint

- Inform user with a message reflecting which agents ran:
  - Full run: "Phase 1 complete. Test coverage established. Architecture reviewed. Quality + security baseline recorded. Starting iteration loop."
  - Focused run: "Phase 1 complete. Test coverage established.{' Architecture reviewed.' if architect active}{' Quality + security baseline recorded.' if code-reviewer active} Starting iteration loop ({max_iterations} iteration{s})."

## Phase 2: Iteration Loop

**Goal**: Iteratively improve code quality through architect -> code -> test -> review -> simplify cycles.

Repeat the following for `max_iterations` times:

### Step 2.A: Architecture Review

**Skip if "architect" not in active_agents.** Also skip on iteration 1 if architect's Phase 1 review is still current. Otherwise:

1. **TaskCreate**: "Iteration {iteration+1}: Review code architecture for [{scope}]. Create prioritized optimization plan. Provide top 3 high-priority optimizations to implement. Focus on improvements not yet addressed in previous iterations.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: iteration {iteration+1} architecture review. Start now."
2. Wait for completion
3. Record architect's top 3 priorities

### Step 2.B: Implement Optimizations

**Skip if Step 2.A was skipped** (no architect plan to implement). For simplification-only focus, skip straight to Step 2.F (simplifier operates on scope directly).

If not skipped:

1. **TaskCreate**: "Implement the top 3 optimizations from the architect's plan: [paste architect's top 3]. Preserve all existing functionality. Apply clean code principles. Make incremental, safe changes. Report all files modified. Do NOT commit via git.{if codebase_context: '\n\n## Codebase Context\n' + codebase_context}"
   - **TaskUpdate**: assign owner to "refactor-code"
   - **SendMessage** to "refactor-code": "Task #{id} assigned: implement top 3 optimizations. Start now."
2. Wait for completion
3. Record implementation report (files changed, optimizations applied)

### Step 2.C: Test Verification

**Skip if Step 2.B was skipped** (no implementation changes to verify).

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
3. **If `config.postRefactor.commitStrategy` is `"per-iteration"`**:
   - Stage all changed files using Bash: `git add -u`
   - Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit; skip and log "No changes to commit for this iteration"
   - Commit using Bash with a HEREDOC message:
     ```bash
     git commit -m "$(cat <<'EOF'
     refactor(iteration {refactoring_iteration}/{max_iterations}): {brief summary from architect's plan}
     EOF
     )"
     ```
   - If commit fails (e.g., no git, pre-commit hook failure, no changes), log a warning to the user and continue
4. If `refactoring_iteration < max_iterations`: continue to next iteration (Step 2.A)
5. If `refactoring_iteration >= max_iterations`: proceed to Phase 3

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
3. Use Write tool to save the report

### Step 4.1.5: Commit Final Changes (Conditional)

**Only when `config.postRefactor.commitStrategy` is `"single-final"`**:

1. Stage all changed files using Bash: `git add -u`
2. Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit; skip and log "No changes to commit"
3. Commit using Bash with a HEREDOC message:
   ```bash
   git commit -m "$(cat <<'EOF'
   refactor{if is_focused: '(' + focus_areas joined by ',' + ')'}: {scope} — {active scores as 'name score/10' joined by ', '}
   EOF
   )"
   ```
4. If commit fails (e.g., no git, pre-commit hook failure, no changes), log a warning to the user and continue

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

1. **Determine branch**: Check current branch via Bash: `git rev-parse --abbrev-ref HEAD`
   - If on `main`, `master`, or `develop`:
     - Generate a scope slug from `{scope}` (lowercase, replace spaces/special chars with hyphens, truncate to 50 chars)
     - Generate `{date}` in YYYY-MM-DD format
     - Create and switch to branch via Bash: `git checkout -b "refactor/{scope-slug}-{date}"`

2. **Ensure all changes are committed**: If `commitStrategy` was `"none"` (no commits happened yet):
   - Stage all changed files: `git add -u`
   - Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit
   - Commit via Bash with HEREDOC:
     ```bash
     git commit -m "$(cat <<'EOF'
     refactor{if is_focused: '(' + focus_areas joined by ',' + ')'}: {scope} — {active scores as 'name score/10' joined by ', '}
     EOF
     )"
     ```

3. **Push branch to remote**: Run via Bash: `git push -u origin HEAD`
   - If push fails, log a warning and continue (PR creation will also fail)

4. **Create the PR** using Bash with `gh pr create`:
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
     *Generated by refactor plugin v3.0.0*
     EOF
     )" {if prDraft: "--draft"} {if is_focused: '--label "focus:' + focus_areas[0] + '"'}
     ```
   - Store the created PR URL as `pr_url`

5. If any step fails (e.g., no remote, auth issues, `gh` not available), log a warning to the user and continue

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

### Step 4.3: Shutdown Team

1. Send **shutdown_request** to all spawned teammates (those in `active_agents`) via SendMessage
2. Wait for shutdown confirmations
3. Use **TeamDelete** to clean up the team

## Orchestration Notes

### Team Coordination
- Use **TaskCreate/TaskUpdate/TaskList** for all task management
- **CRITICAL**: After every **TaskUpdate** that assigns an owner, you MUST send a **SendMessage** to that teammate notifying them of the assignment. Teammates only auto-receive SendMessage — they do NOT get notified of TaskUpdate changes. Without this message, the agent will sit idle indefinitely.
- Teammates communicate results back via SendMessage to team lead
- Team lead (this skill) makes all sequencing decisions
- Only the team lead commits code via git — teammates must never run git commit

### Context Distribution
- **Blackboard (preferred)**: Use Atlatl `blackboard_write`/`blackboard_read` for sharing codebase_context across agents. Write once after Phase 0.5, all agents read as needed.
- **Inline fallback**: If blackboard is unavailable, embed `codebase_context` directly in task descriptions under a `## Codebase Context` heading.
- Always include `codebase_context` reference in Phase 1 and first-iteration Phase 2 tasks. Subsequent iterations may omit if context hasn't changed.

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

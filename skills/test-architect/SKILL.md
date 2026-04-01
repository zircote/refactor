---
name: test-architect
description: "Generates scientifically grounded test suites using equivalence class partitioning, boundary value analysis, property-based testing, and mutation-aware assertions. Orchestrates test planning, writing, rigor review, and coverage analysis with swarm-coordinated specialist agents. Supports TDD red-phase generation, test quality evaluation, and coverage gap analysis."
argument-hint: "[--mode=full|plan|eval|coverage] [path or description]"
---

# Test Architect Skill (Swarm Orchestration)

You are the team lead orchestrating a scientifically grounded test generation process using a swarm of specialist agents.

## Overview

This skill implements a comprehensive test architecture workflow using 4 specialist agents coordinated as a swarm team:
- **test-planner** — Analyzes source code/specs to produce structured JSON test plans using formal test design techniques
- **test-writer** — Transforms JSON test plans into idiomatic, compilable test code (TDD red phase — tests compile but FAIL)
- **test-rigor-reviewer** — Reviews test suites for scientific rigor, catching anti-patterns and scoring quality
- **coverage-analyst** — Runs native coverage tools, identifies gaps, suggests targeted test cases

The workflow uses parallel execution where possible and integrates with the Atlatl memory system for pattern recall and capture.

## Arguments

**$ARGUMENTS**: Optional mode flag and specification of what to generate tests for.

Parse `$ARGUMENTS` for the following **before** any other processing:

- `--mode=<mode>` — Set the operating mode. Valid values: `full`, `plan`, `eval`, `coverage`. If not specified, default to `full`. Extract and remove from `$ARGUMENTS`.

After extracting flags, the remaining arguments are interpreted as:
- If empty: detect project root and analyze entire project
- If file path: generate tests for specific file(s)
- If directory path: generate tests for all source files in directory
- If glob pattern: generate tests for matching files
- If description: generate tests for code matching description

## Mode Details

### Mode: `full` (Default — triggered by `/test-gen`)

Full pipeline: detect → recall → plan → write → review → coverage → capture.

### Mode: `plan` (Triggered by `/test-plan`)

Plan only: detect → plan → present JSON test plan for user approval. No code generation.

### Mode: `eval` (Triggered by `/test-eval`)

Evaluate existing tests: run test-rigor-reviewer + coverage-analyst on existing test suites. No new code.

### Mode: `coverage` (Triggered by `/test-gen --mode=coverage`)

Coverage analysis only: detect → run coverage tools → identify gaps → suggest test cases.

## Phase 0: Detect and Initialize

### Step 0.1: Detect Project

Run project detection using the detection module:

```bash
python3 -m scripts.detect_project <target_path>
```

Or, if running from outside the plugin root:

```bash
python3 -c "import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}'); from scripts.detect_project import detect_project; import json; print(json.dumps(detect_project(sys.argv[1])))" <target_path>
```

Or detect manually:
1. Check for Cargo.toml → Rust (test_runner: cargo test, coverage: cargo-tarpaulin, property: proptest)
2. Check for pyproject.toml → Python (test_runner: pytest, coverage: coverage.py, property: hypothesis)
3. Check for package.json + tsconfig.json → TypeScript (test_runner: vitest, coverage: c8, property: fast-check)
4. Check for go.mod → Go (test_runner: go test, coverage: go tool cover, property: rapid)

Store detection result as `project_info`.

### Step 0.2: Recall Atlatl Context

Search for relevant prior test patterns:
```
recall_memories(query="test patterns {project_info.language} {scope}")
```

Store any matching patterns as `prior_patterns` for inclusion in agent task descriptions.

### Step 0.3: Create Swarm Team and Blackboard

**MANDATORY SWARM ORCHESTRATION — DO NOT USE PLAIN AGENT SPAWNS**

You MUST use the full swarm pattern: TeamCreate → TaskCreate → Agent with team_name → SendMessage. Do NOT fall back to spawning standalone Agent subagents without a team. The swarm pattern enables persistent teammates that coordinate via shared task lists and messaging — standalone subagents cannot do this.

**Step 0.3.1**: Call **TeamCreate** to create the team. This is a blocking prerequisite — do not proceed until TeamCreate succeeds:
   ```
   TeamCreate with team_name: "test-architect-team"
   ```
   If TeamCreate fails, retry once. If it fails again, report the error and stop.

**Step 0.3.2**: Create a shared blackboard for cross-agent context:
   ```
   blackboard_create with task_id: "test-architect-{scope-slug}" and TTL appropriate for the session
   ```
   Store the returned blackboard ID as `blackboard_id`.

**Step 0.3.3**: Use **TaskCreate** to create the high-level phase tasks based on mode:
   - **full**: "Phase 1: Test Planning", "Phase 2: Test Writing", "Phase 3: Rigor Review", "Phase 4: Coverage Analysis", "Phase 5: Report and Cleanup"
   - **plan**: "Phase 1: Test Planning", "Phase 2: Report and Cleanup"
   - **eval**: "Phase 1: Rigor Review", "Phase 2: Coverage Analysis", "Phase 3: Report and Cleanup"
   - **coverage**: "Phase 1: Coverage Analysis", "Phase 2: Report and Cleanup"

### Step 0.4: Spawn Teammates

Spawn agents using the **Agent tool** with `team_name: "test-architect-team"`. The `team_name` parameter is REQUIRED on every Agent call — it registers the agent as a persistent teammate rather than a fire-and-forget subagent. Launch all needed agents in parallel.

**Verification**: After spawning, confirm each teammate is addressable by name via SendMessage before assigning tasks.

Each teammate receives the task-discovery protocol and blackboard ID:

```
BLACKBOARD: {blackboard_id}
Use blackboard_read(task_id="{blackboard_id}", key="...") to read shared context.
Use blackboard_write(task_id="{blackboard_id}", key="...", value="...") to share your findings.

TASK DISCOVERY PROTOCOL:
1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you (owner = your name).
2. Call TaskGet on your assigned task to read the full description.
3. Work on the task.
4. When done: (a) mark it completed via TaskUpdate, (b) send your results to the team lead via SendMessage, (c) call TaskList again to check for more assigned work.
5. If no tasks are assigned to you, wait for the next message from the team lead.
6. NEVER commit code via git — only the team lead commits.
```

**Spawn matrix by mode**:
- **full**: test-planner, test-writer, test-rigor-reviewer, coverage-analyst
- **plan**: test-planner only
- **eval**: test-rigor-reviewer, coverage-analyst
- **coverage**: coverage-analyst only

Agent spawn templates:

1. **test-planner**:
   ```
   Agent tool with:
     subagent_type: "refactor:test-planner"
     team_name: "test-architect-team"
     name: "test-planner"
     prompt: "You are the test planner on a test architecture swarm team. The scope is: {scope}. Language: {project_info.language}.
     {prior_patterns if any}

     BLACKBOARD: {blackboard_id}
     ...task discovery protocol..."
   ```

2. **test-writer**:
   ```
   Agent tool with:
     subagent_type: "refactor:test-writer"
     team_name: "test-architect-team"
     name: "test-writer"
     prompt: "You are the test writer on a test architecture swarm team. The scope is: {scope}. Language: {project_info.language}. TDD red phase: tests MUST compile but FAIL.

     BLACKBOARD: {blackboard_id}
     ...task discovery protocol..."
   ```

3. **test-rigor-reviewer**:
   ```
   Agent tool with:
     subagent_type: "refactor:test-rigor-reviewer"
     team_name: "test-architect-team"
     name: "test-rigor-reviewer"
     prompt: "You are the test rigor reviewer on a test architecture swarm team. The scope is: {scope}. Language: {project_info.language}.

     BLACKBOARD: {blackboard_id}
     ...task discovery protocol..."
   ```

4. **coverage-analyst**:
   ```
   Agent tool with:
     subagent_type: "refactor:coverage-analyst"
     team_name: "test-architect-team"
     name: "coverage-analyst"
     prompt: "You are the coverage analyst on a test architecture swarm team. The scope is: {scope}. Language: {project_info.language}.

     BLACKBOARD: {blackboard_id}
     ...task discovery protocol..."
   ```

## Phase 1: Test Planning (modes: full, plan)

### Step 1.1: Launch Test Planner

1. **TaskCreate**: "Analyze [{scope}] and produce a structured JSON test plan. Language: {project_info.language}. Apply equivalence class partitioning, boundary value analysis, state transition coverage, and property-based testing. Identify public API, types, constraints, invariants. Output JSON test plan with test_cases and property_tests arrays.{if prior_patterns: '\n\n## Prior Patterns\n' + prior_patterns}"
   - **TaskUpdate**: assign owner to "test-planner"
   - **SendMessage** to "test-planner": "Task #{id} assigned: create test plan. Start now."

### Step 1.2: Wait for Completion

- Monitor TaskList until test-planner task shows status: completed
- Read the JSON test plan from test-planner's message
- Store as `test_plan`
- Write to blackboard: `blackboard_write(task_id="{blackboard_id}", key="test_plan", value=test_plan)`

### Step 1.3: Checkpoint

- **If mode is `plan`**: Present the test plan to the user. Skip to Phase: Report and Cleanup.
- **If mode is `full`**: Inform user: "Test plan complete. {N} unit tests, {M} property tests planned. Proceeding to code generation."

## Phase 2: Test Writing (mode: full only)

### Step 2.1: Launch Test Writer

1. **TaskCreate**: "Generate idiomatic test code from the test plan. Language: {project_info.language}. Framework: {project_info.test_framework}. Property lib: {project_info.property_lib}. TDD RED PHASE: tests must compile/parse but FAIL — assert expected behavior against real implementation. Do NOT write trivial passing tests. Read the test plan from blackboard key 'test_plan'. Write test files following language conventions:
   - Rust: `#[cfg(test)]` modules or separate test files
   - Python: `test_*.py` with pytest
   - TypeScript: `*.test.ts` with vitest
   - Go: `*_test.go` with `testing` package

   Report all files created."
   - **TaskUpdate**: assign owner to "test-writer"
   - **SendMessage** to "test-writer": "Task #{id} assigned: generate test code from plan. Start now."

### Step 2.2: Wait for Completion

- Monitor TaskList until test-writer task shows status: completed
- Read the generation report (files created)
- Store as `generated_files`

### Step 2.3: Checkpoint

- Inform user: "Test code generated. {N} files created. Proceeding to rigor review."

## Phase 3: Rigor Review (modes: full, eval)

### Step 3.1: Launch Rigor Review

**For eval mode**: Set `generated_files` to the target test files (from $ARGUMENTS or auto-detected).

1. **TaskCreate**: "Review test suite for scientific rigor. Files: {generated_files}. Language: {project_info.language}. Check for:
   - Tautological assertions (assert true, identity checks)
   - Weak property generators (unconstrained when domain is constrained)
   - Missing boundary cases (0, -1, MAX, empty, nil)
   - Missing error path tests
   - Mutation-susceptible patterns (wouldn't catch off-by-one, negation)
   Score each test 0.0-1.0. Output JSON: [{test_name, score, issues, suggestions}] + overall rigor score.
   {if test_plan: 'Cross-reference against test plan from blackboard key test_plan.'}"
   - **TaskUpdate**: assign owner to "test-rigor-reviewer"
   - **SendMessage** to "test-rigor-reviewer": "Task #{id} assigned: rigor review. Start now."

### Step 3.2: Launch Coverage Analysis (Parallel)

Run coverage-analyst in parallel with rigor review:

1. **TaskCreate**: "Run coverage analysis for [{scope}]. Language: {project_info.language}. Execute: {coverage command for language}. Parse output, identify uncovered functions/branches/lines. For each gap, suggest specific test cases. Target: 90% coverage. Output: {total_coverage_pct, uncovered_regions, recommended_tests}."
   - **TaskUpdate**: assign owner to "coverage-analyst"
   - **SendMessage** to "coverage-analyst": "Task #{id} assigned: coverage analysis. Start now."

### Step 3.3: Wait for Both to Complete

- Monitor TaskList until both tasks show status: completed
- Read rigor review results and coverage report
- Store as `rigor_report` and `coverage_report`

### Step 3.4: Checkpoint

- Present combined quality summary:
  - Overall rigor score: {mean of per-test scores}
  - Coverage: {total_coverage_pct}%
  - Issues found: {count}
  - Gaps identified: {count}

## Phase 4: Coverage Analysis (mode: coverage only)

If mode is `coverage`, this runs standalone (Phase 3.2 logic without the rigor review).

## Phase: Report and Cleanup

### Step R.1: Capture to Atlatl

If meaningful patterns were discovered:

1. **Test strategy decisions**:
   ```
   capture_memory(title="Test strategy for {scope}", namespace="_semantic/decisions",
     memory_type="semantic", content="{strategy summary}", tags=["{language}", "test-strategy"])
   ```

2. **Reusable patterns**:
   ```
   capture_memory(title="Test patterns for {language} {framework}", namespace="_procedural/patterns",
     memory_type="procedural", content="{patterns}", tags=["{language}", "testing"])
   ```

3. **Anti-patterns found** (from rigor review):
   ```
   capture_memory(title="Test anti-patterns in {scope}", namespace="_episodic/blockers",
     memory_type="episodic", content="{anti-patterns}", tags=["anti-pattern", "testing"])
   ```

Enrich each captured memory: `enrich_memory(id="{memory_id}")`

### Step R.2: Generate Summary Report

Present to user based on mode:

**Full mode**:
```
Test Architecture Complete!

Summary:
- Language: {language}
- Tests planned: {planned_count}
- Tests generated: {generated_count} files
- Rigor score: {rigor_score}/1.0
- Coverage: {coverage_pct}%
- Issues: {issue_count} (see rigor report)
- Gaps: {gap_count} (see coverage report)

Files created:
{list of generated test files}

Next steps:
- Run tests to verify red phase: {test command for language}
- Implement code to make tests pass (green phase)
- Refactor with confidence (refactor phase)
```

**Plan mode**:
```
Test Plan Generated

{JSON test plan formatted for readability}

To generate test code from this plan, run: /test-gen {scope}
```

**Eval mode**:
```
Test Quality Evaluation

Rigor Score: {rigor_score}/1.0
Coverage: {coverage_pct}%

Issues Found:
{list of issues with suggestions}

Coverage Gaps:
{list of uncovered regions with suggestions}
```

**Coverage mode**:
```
Coverage Analysis

Total Coverage: {coverage_pct}%
Uncovered Regions: {count}

{list of gaps with suggested tests}
```

### Step R.3: Shutdown Team

**This step MUST execute regardless of success or failure in prior steps.** If any phase fails or the user interrupts, skip directly here.

1. Send **shutdown_request** to all spawned teammates via SendMessage
2. Wait up to **30 seconds** for shutdown confirmations. If any teammate does not respond within 30 seconds, proceed anyway — do not block on unresponsive agents
3. Use **TeamDelete** to clean up the team. This forcefully terminates any remaining agents
4. If TeamDelete fails, log the error and inform the user: "Team cleanup failed — run `TeamDelete` manually for team `{team_name}`"

## Orchestration Notes

### Team Coordination
- Use **TaskCreate/TaskUpdate/TaskList** for all task management
- **CRITICAL**: After every **TaskUpdate** that assigns an owner, you MUST send a **SendMessage** to that teammate. Without this, the agent will sit idle indefinitely.
- Teammates communicate results back via SendMessage to team lead
- Only the team lead commits code via git — teammates must never run git commit

### Context Distribution
- **Blackboard**: Agents use `blackboard_read`/`blackboard_write` with the shared `blackboard_id`
- Standard keys: `test_plan`, `test_generation_report`, `test_rigor_report`, `coverage_report`
- **Inline fallback**: If blackboard unavailable, embed context in task descriptions

### Parallel Execution Points
- **Phase 3**: test-rigor-reviewer and coverage-analyst run simultaneously
- All other phases are sequential due to data dependencies

### Multi-Module Projects
For large projects with multiple modules, use parallel test-planner instances:
1. Identify distinct modules from `codebase_context`
2. Spawn N test-planner instances: `test-planner-1`, `test-planner-2`, etc.
3. Each analyzes one module
4. Merge plans into unified test plan

### Error Handling
- If a teammate goes idle: re-send assignment via SendMessage with explicit "start now"
- If still idle after second nudge: report to user and implement directly
- If coverage tools not installed: report which tools are needed and continue with available data

### Team Lifecycle Safety
- **Stale agent detection**: At the start of the workflow, check for an existing team with the same name pattern (`test-architect-*`). If found, run **TeamDelete** on it before creating a new team. This cleans up leaked agents from prior interrupted runs.
- **Guaranteed cleanup**: Step R.3 (Shutdown Team) is a **finally block** — it MUST execute even if prior phases fail, the user cancels, or an unrecoverable error occurs. If you cannot determine whether prior phases succeeded, still execute Step R.3.
- **Shutdown timeout**: Never wait indefinitely for shutdown confirmations. After 30 seconds, proceed with TeamDelete regardless. Cooperative shutdown is preferred but not required.
- **No orphaned agents**: After TeamDelete, verify no teammates remain by checking the team config file. If it still exists, warn the user.

### Language Support Table

| Language | Test Runner | Coverage Tool | Property Lib | Mutation Tool |
|----------|------------|---------------|-------------|---------------|
| Rust | cargo test | cargo-tarpaulin | proptest | cargo-mutants |
| Python | pytest | coverage.py | hypothesis | mutmut |
| TypeScript | vitest | c8 | fast-check | stryker |
| Go | go test | go tool cover | rapid | go-mutesting |

## Autoresearch Integration

When invoked inside an autoresearch convergence loop:
- Tests serve as the fitness function (eval harness)
- Test quality score from test-rigor-reviewer feeds convergence metric
- Write tests to `candidate/` directory instead of standard test locations
- The autoresearch orchestrator manages keep/discard gating

---

Begin the test architecture process now based on: $ARGUMENTS

Start with Phase 0 (Detect and Initialize).

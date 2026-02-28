---
name: refactor
description: Automated iterative code refactoring with swarm-orchestrated specialist agents
argument-hint: "[--iterations=N] [path or description]"
---

# Refactor Command (Swarm Orchestration)

You are the team lead orchestrating an automated, iterative code refactoring process using a swarm of specialist agents.

## Overview

This command implements a comprehensive refactoring workflow using 4 specialist agents coordinated as a swarm team:
- **architect** — Reviews architecture, identifies improvements, scores quality
- **refactor-test** — Analyzes coverage, runs tests, reports failures
- **refactor-code** — Implements optimizations, fixes test failures
- **simplifier** — Simplifies changed code for clarity and consistency

The workflow uses parallel execution where possible and iterates `max_iterations` times for continuous improvement.

## Arguments

**$ARGUMENTS**: Optional flags and specification of what to refactor.

Parse `$ARGUMENTS` for the following **before** any other processing:

- `--iterations=N` — Override the configured iteration count for this run. `N` must be a positive integer (1–10). If present, extract and remove it from `$ARGUMENTS` and store as `cli_iterations`. The remaining text is the refactoring scope.

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
     "version": "1.1",
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
  "version": "1.1",
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
4. Set `max_iterations = cli_iterations ?? config.iterations ?? 3` (CLI flag takes precedence over config, config takes precedence over default)
5. Set `refactoring_iteration = 0`

### Step 0.2: Create Swarm Team

1. Use **TeamCreate** to create the refactoring team:
   ```
   TeamCreate with team_name: "refactor-team"
   ```

2. Use **TaskCreate** to create the high-level phase tasks:
   - "Phase 1: Foundation analysis (parallel)"
   - For i in 1..max_iterations: "Phase 2: Iteration {i} of {max_iterations}"
   - "Phase 3: Final assessment"
   - "Phase 4: Report and cleanup"

### Step 0.3: Spawn Teammates

Spawn all 4 teammates using the **Task tool** with `team_name: "refactor-team"`. Launch all 4 in parallel:

1. **architect** teammate:
   ```
   Task tool with:
     subagent_type: "refactor:architect"
     team_name: "refactor-team"
     name: "architect"
     prompt: "You are the architect agent on a refactoring swarm team. Wait for task assignments via the task list. Check TaskList for your assigned tasks. When you complete a task, mark it completed with TaskUpdate and send your results to the team lead via SendMessage."
   ```

2. **refactor-test** teammate:
   ```
   Task tool with:
     subagent_type: "refactor:refactor-test"
     team_name: "refactor-team"
     name: "refactor-test"
     prompt: "You are the test agent on a refactoring swarm team. Wait for task assignments via the task list. Check TaskList for your assigned tasks. When you complete a task, mark it completed with TaskUpdate and send your results to the team lead via SendMessage."
   ```

3. **refactor-code** teammate:
   ```
   Task tool with:
     subagent_type: "refactor:refactor-code"
     team_name: "refactor-team"
     name: "refactor-code"
     prompt: "You are the code agent on a refactoring swarm team. Wait for task assignments via the task list. Check TaskList for your assigned tasks. When you complete a task, mark it completed with TaskUpdate and send your results to the team lead via SendMessage."
   ```

4. **simplifier** teammate:
   ```
   Task tool with:
     subagent_type: "refactor:simplifier"
     team_name: "refactor-team"
     name: "simplifier"
     prompt: "You are the simplifier agent on a refactoring swarm team. Wait for task assignments via the task list. Check TaskList for your assigned tasks. When you complete a task, mark it completed with TaskUpdate and send your results to the team lead via SendMessage."
   ```

## Phase 1: Foundation (Parallel)

**Goal**: Establish test coverage and understand architecture simultaneously.

### Step 1.1: Create and Assign Parallel Tasks

Create two tasks and assign them in parallel:

1. **TaskCreate**: "Analyze test coverage for [scope]. Identify gaps, add comprehensive test cases for critical paths/edge cases/error handling, run all tests, verify passing, report coverage status."
   - **TaskUpdate**: assign owner to "refactor-test"

2. **TaskCreate**: "Review code architecture for [scope]. Analyze structure, patterns, quality. Identify all optimization opportunities (structural, duplication, naming, organization, complexity, dependencies). Create initial prioritized optimization plan."
   - **TaskUpdate**: assign owner to "architect"

### Step 1.2: Wait for Both to Complete

- Monitor TaskList until both Phase 1 tasks show status: completed
- Read the results from messages received from refactor-test and architect teammates
- Verify refactor-test agent confirms all tests are passing before proceeding

### Step 1.3: Checkpoint

- Inform user: "Phase 1 complete. Test coverage established. Architecture reviewed. Starting iteration loop."

## Phase 2: Iteration Loop

**Goal**: Iteratively improve code quality through architect → code → test → simplify cycles.

Repeat the following for `max_iterations` times:

### Step 2.A: Architecture Review

**Skip on iteration 1** if architect's Phase 1 review is still current. Otherwise:

1. **TaskCreate**: "Iteration {iteration+1}: Review code architecture for [scope]. Create prioritized optimization plan. Provide top 3 high-priority optimizations to implement. Focus on improvements not yet addressed in previous iterations."
   - **TaskUpdate**: assign owner to "architect"
2. Wait for completion
3. Record architect's top 3 priorities

### Step 2.B: Implement Optimizations

1. **TaskCreate**: "Implement the top 3 optimizations from the architect's plan: [paste architect's top 3]. Preserve all existing functionality. Apply clean code principles. Make incremental, safe changes. Report all files modified."
   - **TaskUpdate**: assign owner to "refactor-code"
2. Wait for completion
3. Record implementation report (files changed, optimizations applied)

### Step 2.C: Test Verification

1. **TaskCreate**: "Run the complete test suite. Report pass/fail status. If failures: provide detailed failure report with causes and suggestions."
   - **TaskUpdate**: assign owner to "refactor-test"
2. Wait for completion

### Step 2.D: Fix Failures (If Any)

If refactor-test agent reported failures:

1. **TaskCreate**: "Fix test failures: [paste failure report]. Analyze root causes. Implement fixes. Preserve refactoring improvements."
   - **TaskUpdate**: assign owner to "refactor-code"
2. Wait for completion
3. **TaskCreate**: "Re-run full test suite to verify fixes."
   - **TaskUpdate**: assign owner to "refactor-test"
4. Wait for completion
5. If still failing, repeat Step 2.D (max 3 attempts, then ask user for guidance)

### Step 2.E: Simplify Changed Code

1. **TaskCreate**: "Simplify all code changed in this iteration. Files modified: [list from refactor-code agent's report]. Focus on naming clarity, control flow simplification, redundancy removal, and style consistency. Do not change functionality."
   - **TaskUpdate**: assign owner to "simplifier"
2. Wait for completion
3. Record simplification report

### Step 2.F: Verify Simplification

1. **TaskCreate**: "Run full test suite to verify simplification preserved all functionality."
   - **TaskUpdate**: assign owner to "refactor-test"
2. Wait for completion
3. If failures: send simplification failure report to simplifier for reversion, then re-test

### Step 2.G: Iteration Complete

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

**Goal**: Final polish and quality scoring.

### Step 3.1: Launch Final Tasks (Parallel)

Create two tasks and assign in parallel:

1. **TaskCreate**: "Final simplification pass over entire [scope]. Review all files for cross-file consistency in naming, patterns, and style. Apply final polish. Report all changes."
   - **TaskUpdate**: assign owner to "simplifier"

2. **TaskCreate**: "Prepare comprehensive final quality assessment of [scope]. Review architecture, code quality, SOLID principles. Prepare scoring framework. Note: final scores will be assigned after simplifier completes and tests pass."
   - **TaskUpdate**: assign owner to "architect"

### Step 3.2: Wait for Both to Complete

Monitor TaskList until both tasks show completed.

### Step 3.3: Final Test Run

1. **TaskCreate**: "Final full test suite run. Report complete pass/fail results."
   - **TaskUpdate**: assign owner to "refactor-test"
2. Wait for completion
3. If failures: coordinate fix with refactor-code agent, re-test

### Step 3.4: Final Scoring

1. **TaskCreate**: "Assign final quality scores based on completed refactoring. Provide: Clean Code Score (1-10) with justification, Architecture Perfection Score (1-10) with justification, summary of improvements across all iterations, remaining potential issues, future recommendations. Create detailed markdown report."
   - **TaskUpdate**: assign owner to "architect"
2. Wait for completion

## Phase 4: Report and Cleanup

### Step 4.1: Generate Report

1. Generate timestamp
2. Create `refactor-result-{timestamp}.md` with architect's final assessment report
3. Use Write tool to save the report

### Step 4.1.5: Commit Final Changes (Conditional)

**Only when `config.postRefactor.commitStrategy` is `"single-final"`**:

1. Stage all changed files using Bash: `git add -u`
2. Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit; skip and log "No changes to commit"
3. Commit using Bash with a HEREDOC message:
   ```bash
   git commit -m "$(cat <<'EOF'
   refactor: {scope} — clean code {clean_code_score}/10, architecture {architecture_score}/10
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
     refactor: {scope} — clean code {clean_code_score}/10, architecture {architecture_score}/10
     EOF
     )"
     ```

3. **Push branch to remote**: Run via Bash: `git push -u origin HEAD`
   - If push fails, log a warning and continue (PR creation will also fail)

4. **Create the PR** using Bash with `gh pr create`:
   - Build the command:
     ```bash
     gh pr create --title "refactor: {scope}" --body "$(cat <<'EOF'
     ## Refactor Summary

     **Scope**: {scope}
     **Iterations**: {max_iterations}

     ## Quality Scores
     - Clean Code: {clean_code_score}/10
     - Architecture: {architecture_score}/10

     ## Changes
     {brief summary of improvements from architect's report}

     {if published_url: "Related: {published_url}"}

     ---
     *Generated by refactor plugin v2.1.0*
     EOF
     )" {if prDraft: "--draft"}
     ```
   - Store the created PR URL as `pr_url`

5. If any step fails (e.g., no remote, auth issues, `gh` not available), log a warning to the user and continue

### Step 4.2: Report to User

```
Refactoring complete!

Summary:
- Iterations: {max_iterations}
- Tests: All passing
- Report: refactor-result-{timestamp}.md

Quality Scores:
- Clean Code: X/10
- Architecture: Y/10
```

### Step 4.3: Shutdown Team

1. Send **shutdown_request** to all 4 teammates via SendMessage
2. Wait for shutdown confirmations
3. Use **TeamDelete** to clean up the team

## Orchestration Notes

### Team Coordination
- Use **TaskCreate/TaskUpdate/TaskList** for all task management
- Use **SendMessage** for direct communication with teammates
- Teammates communicate results back via SendMessage to team lead
- Team lead (this command) makes all sequencing decisions

### Parallel Execution Points
- **Phase 1**: refactor-test + architect run simultaneously (both read-only analysis)
- **Phase 3.1**: simplifier + architect run simultaneously
- All other steps are sequential due to data dependencies

### Error Handling
- If a teammate fails or gets stuck: send a message asking for status
- If tests fail repeatedly (3+ attempts): ask user for guidance
- If a teammate doesn't respond: report to user
- Don't proceed past test failures — green tests are gating

### State Management
- Track `refactoring_iteration` counter carefully
- Keep architect's optimization plan accessible for refactor-code agent
- Track which files were modified each iteration for simplifier
- Maintain list of all changes across iterations for final report

### Communication Protocol
- Include iteration number in all task descriptions
- Pass specific file lists and reports between tasks
- Keep user informed at phase/iteration transitions
- Provide brief progress summaries

## Success Criteria

Refactoring is complete when:
- All tests pass
- `max_iterations` refactoring iterations completed
- Simplification pass completed per iteration + final pass
- Code quality scores assigned
- Final assessment report generated
- No functionality changes (only quality improvements)
- Team gracefully shut down

---

Begin the refactoring process now based on: $ARGUMENTS

Start with Phase 0 (Initialize Team).

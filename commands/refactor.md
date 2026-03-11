---
name: refactor
description: Automated iterative code refactoring with swarm-orchestrated specialist agents
argument-hint: "[--iterations=N] [path or description]"
---

# Refactor Command (Swarm Orchestration)

You are the team lead orchestrating an automated, iterative code refactoring process using a swarm of specialist agents.

## Overview

This command implements a comprehensive refactoring workflow using 5 specialist agents coordinated as a swarm team:
- **architect** — Reviews architecture, identifies improvements, scores quality
- **refactor-test** — Analyzes coverage, runs tests, reports failures
- **refactor-code** — Implements optimizations, fixes test failures
- **simplifier** — Simplifies changed code for clarity and consistency
- **security-review** — Reviews changes for security regressions, blocks on Critical/High findings, scores security posture

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

Spawn all 5 teammates using the **Agent tool** with `team_name: "refactor-team"`. Launch all 5 in parallel:

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

1. **architect** teammate:
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

2. **refactor-test** teammate:
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

3. **refactor-code** teammate:
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

4. **simplifier** teammate:
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

5. **security-review** teammate:
   ```
   Agent tool with:
     subagent_type: "refactor:security-review"
     team_name: "refactor-team"
     name: "security-review"
     prompt: "You are the security review agent on a refactoring swarm team. The scope is: {scope}.

     TASK DISCOVERY PROTOCOL:
     1. When you receive a message from the team lead, immediately call TaskList to find tasks assigned to you.
     2. Call TaskGet on your assigned task to read the full description.
     3. Work on the task.
     4. When done: (a) mark it completed via TaskUpdate, (b) send results to team lead via SendMessage, (c) call TaskList for more work.
     5. If no tasks assigned, wait for next message.
     6. NEVER commit code via git — only the team lead commits."
   ```

## Phase 1: Foundation (Parallel)

**Goal**: Establish test coverage, understand architecture, and baseline security posture simultaneously.

### Step 1.1: Create and Assign Parallel Tasks

Create three tasks and assign them in parallel:

1. **TaskCreate**: "Analyze test coverage for [scope]. Identify gaps, add comprehensive test cases for critical paths/edge cases/error handling, run all tests, verify passing, report coverage status."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: analyze test coverage. Start now."

2. **TaskCreate**: "Review code architecture for [scope]. Analyze structure, patterns, quality. Identify all optimization opportunities (structural, duplication, naming, organization, complexity, dependencies). Create initial prioritized optimization plan."
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: review architecture. Start now."

3. **TaskCreate**: "Establish security baseline for [scope]. Catalog existing security controls (input validation, auth checks, output encoding, error handling, access controls). Scan for pre-existing secrets exposure. Audit current dependency vulnerability status. Record baseline for regression detection in subsequent iterations."
   - **TaskUpdate**: assign owner to "security-review"
   - **SendMessage** to "security-review": "Task #{id} assigned: establish security baseline. Start now."

### Step 1.2: Wait for All Three to Complete

- Monitor TaskList until all three Phase 1 tasks show status: completed
- Read the results from messages received from refactor-test, architect, and security-review teammates
- Verify refactor-test agent confirms all tests are passing before proceeding
- Record security-review agent's baseline for use in iteration reviews

### Step 1.3: Checkpoint

- Inform user: "Phase 1 complete. Test coverage established. Architecture reviewed. Security baseline recorded. Starting iteration loop."

## Phase 2: Iteration Loop

**Goal**: Iteratively improve code quality through architect → code → test → simplify cycles.

Repeat the following for `max_iterations` times:

### Step 2.A: Architecture Review

**Skip on iteration 1** if architect's Phase 1 review is still current. Otherwise:

1. **TaskCreate**: "Iteration {iteration+1}: Review code architecture for [scope]. Create prioritized optimization plan. Provide top 3 high-priority optimizations to implement. Focus on improvements not yet addressed in previous iterations."
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: iteration {iteration+1} architecture review. Start now."
2. Wait for completion
3. Record architect's top 3 priorities

### Step 2.B: Implement Optimizations

1. **TaskCreate**: "Implement the top 3 optimizations from the architect's plan: [paste architect's top 3]. Preserve all existing functionality. Apply clean code principles. Make incremental, safe changes. Report all files modified. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "refactor-code"
   - **SendMessage** to "refactor-code": "Task #{id} assigned: implement top 3 optimizations. Start now."
2. Wait for completion
3. Record implementation report (files changed, optimizations applied)

### Step 2.C: Test Verification

1. **TaskCreate**: "Run the complete test suite. Report pass/fail status. If failures: provide detailed failure report with causes and suggestions."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: run tests after implementation. Start now."
2. Wait for completion

### Step 2.D: Fix Failures (If Any)

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

### Step 2.E: Simplify + Security Review (Parallel)

Launch simplification and security review in parallel:

1. **TaskCreate**: "Simplify all code changed in this iteration. Files modified: [list from refactor-code agent's report]. Focus on naming clarity, control flow simplification, redundancy removal, and style consistency. Do not change functionality. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "simplifier"
   - **SendMessage** to "simplifier": "Task #{id} assigned: simplify iteration changes. Start now."

2. **TaskCreate**: "Iteration {iteration+1} security review. Files modified: [list from refactor-code agent's report]. Review all changes against the Phase 1 security baseline. Check for: security regressions (weakened validation, broken auth, exposed internals), secrets/PII exposure, unsafe error handling, new injection vectors, dependency changes. Classify findings by severity (Critical/High = blocking, Medium/Low = advisory). Provide remediation guidance for any blocking findings."
   - **TaskUpdate**: assign owner to "security-review"
   - **SendMessage** to "security-review": "Task #{id} assigned: iteration {iteration+1} security review. Start now."

3. Wait for both to complete

4. Record simplification report and security review results

### Step 2.E.1: Resolve Security Findings (If Blocking)

If security-review agent reported **FAIL** (Critical or High severity findings):

1. **TaskCreate**: "Fix security findings from security review: [paste blocking findings with remediation guidance]. Implement fixes while preserving refactoring improvements. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "refactor-code"
   - **SendMessage** to "refactor-code": "Task #{id} assigned: fix blocking security findings. Start now."
2. Wait for completion
3. **TaskCreate**: "Re-review security fixes. Verify blocking findings from iteration {iteration+1} are resolved. Files modified: [list from code agent's fix report]."
   - **TaskUpdate**: assign owner to "security-review"
   - **SendMessage** to "security-review": "Task #{id} assigned: verify security fixes. Start now."
4. Wait for completion
5. If still FAIL, repeat Step 2.E.1 (max 3 attempts, then ask user for guidance)

### Step 2.F: Verify Simplification + Security Fixes

1. **TaskCreate**: "Run full test suite to verify simplification and any security fixes preserved all functionality."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: verify tests after simplification and security fixes. Start now."
2. Wait for completion
3. If failures: send failure report to simplifier/refactor-code for reversion, then re-test

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

Create three tasks and assign in parallel:

1. **TaskCreate**: "Final simplification pass over entire [scope]. Review all files for cross-file consistency in naming, patterns, and style. Apply final polish. Report all changes. Do NOT commit via git."
   - **TaskUpdate**: assign owner to "simplifier"
   - **SendMessage** to "simplifier": "Task #{id} assigned: final simplification pass. Start now."

2. **TaskCreate**: "Prepare comprehensive final quality assessment of [scope]. Review architecture, code quality, SOLID principles. Prepare scoring framework. Note: final scores will be assigned after simplifier completes and tests pass."
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: prepare final quality assessment. Start now."

3. **TaskCreate**: "Final security assessment of [scope]. Compare full refactoring scope against Phase 1 security baseline. Verify all blocking findings from iterations were resolved. Check for cross-file security issues missed in per-iteration reviews. Prepare Security Posture Score (1-10) with justification and baseline comparison table."
   - **TaskUpdate**: assign owner to "security-review"
   - **SendMessage** to "security-review": "Task #{id} assigned: final security assessment. Start now."

### Step 3.2: Wait for All Three to Complete

Monitor TaskList until all three tasks show completed.

### Step 3.3: Final Test Run

1. **TaskCreate**: "Final full test suite run. Report complete pass/fail results."
   - **TaskUpdate**: assign owner to "refactor-test"
   - **SendMessage** to "refactor-test": "Task #{id} assigned: final test run. Start now."
2. Wait for completion
3. If failures: coordinate fix with refactor-code agent, re-test

### Step 3.4: Final Scoring

1. **TaskCreate**: "Assign final quality scores based on completed refactoring. Provide: Clean Code Score (1-10) with justification, Architecture Perfection Score (1-10) with justification, summary of improvements across all iterations, remaining potential issues, future recommendations. Include the Security Posture Score ({security_score}/10) from the security-review agent's final assessment in the report. Create detailed markdown report."
   - **TaskUpdate**: assign owner to "architect"
   - **SendMessage** to "architect": "Task #{id} assigned: final scoring. Security Posture Score from security-review: {security_score}/10. Include this in the final report alongside Clean Code and Architecture scores. Start now."
2. Wait for completion

## Phase 4: Report and Cleanup

### Step 4.1: Generate Report

1. Generate timestamp
2. Create `refactor-result-{timestamp}.md` with architect's final assessment report (which includes all three scores: Clean Code, Architecture, and Security Posture)
3. Use Write tool to save the report

### Step 4.1.5: Commit Final Changes (Conditional)

**Only when `config.postRefactor.commitStrategy` is `"single-final"`**:

1. Stage all changed files using Bash: `git add -u`
2. Check for staged changes: `git diff --cached --quiet` — if exit code 0, no changes to commit; skip and log "No changes to commit"
3. Commit using Bash with a HEREDOC message:
   ```bash
   git commit -m "$(cat <<'EOF'
   refactor: {scope} — clean code {clean_code_score}/10, architecture {architecture_score}/10, security {security_score}/10
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
     - Security Posture: {security_score}/10

     ## Changes
     {brief summary of improvements from architect's report}

     {if published_url: "Related: {published_url}"}

     ---
     *Generated by refactor plugin v2.3.0*
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
- Security: All blocking findings resolved
- Report: refactor-result-{timestamp}.md

Quality Scores:
- Clean Code: X/10
- Architecture: Y/10
- Security Posture: Z/10
```

### Step 4.3: Shutdown Team

1. Send **shutdown_request** to all 5 teammates via SendMessage
2. Wait for shutdown confirmations
3. Use **TeamDelete** to clean up the team

## Orchestration Notes

### Team Coordination
- Use **TaskCreate/TaskUpdate/TaskList** for all task management
- **CRITICAL**: After every **TaskUpdate** that assigns an owner, you MUST send a **SendMessage** to that teammate notifying them of the assignment. Teammates only auto-receive SendMessage — they do NOT get notified of TaskUpdate changes. Without this message, the agent will sit idle indefinitely.
- Teammates communicate results back via SendMessage to team lead
- Team lead (this command) makes all sequencing decisions
- Only the team lead commits code via git — teammates must never run git commit

### Parallel Execution Points
- **Phase 1**: refactor-test + architect + security-review run simultaneously (all read-only analysis)
- **Phase 2.E**: simplifier + security-review run simultaneously (both reviewing code agent's changes)
- **Phase 3.1**: simplifier + architect + security-review run simultaneously
- All other steps are sequential due to data dependencies

### Error Handling
- If a teammate goes idle without completing their task: re-send the assignment via SendMessage with the task ID and explicit "start now" instruction
- If a teammate is still idle after a second nudge: report to user and consider implementing the work directly
- If tests fail repeatedly (3+ attempts): ask user for guidance
- If security findings persist after 3 fix attempts: ask user for guidance
- Don't proceed past test failures — green tests are gating
- Don't proceed past blocking security findings (Critical/High) — security is gating

### State Management
- Track `refactoring_iteration` counter carefully
- Keep architect's optimization plan accessible for refactor-code agent
- Track which files were modified each iteration for simplifier and security-review
- Maintain list of all changes across iterations for final report
- Preserve security-review's Phase 1 baseline for iteration comparisons

### Communication Protocol
- Include iteration number in all task descriptions
- Pass specific file lists and reports between tasks
- Keep user informed at phase/iteration transitions
- Provide brief progress summaries

## Success Criteria

Refactoring is complete when:
- All tests pass
- All blocking security findings (Critical/High) resolved
- `max_iterations` refactoring iterations completed
- Simplification pass completed per iteration + final pass
- Security review completed per iteration + final assessment
- Code quality scores assigned (Clean Code, Architecture, Security Posture)
- Final assessment report generated
- No functionality changes (only quality improvements)
- Team gracefully shut down

---

Begin the refactoring process now based on: $ARGUMENTS

Start with Phase 0 (Initialize Team).

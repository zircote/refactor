---
name: project-review
description: "Multi-agent quality review of an entire project across 6 domains — Simplicity, Security, Data, Architecture, Documentation, SDLC. Uses swarm orchestration with dynamic team sizing based on project size. Produces per-domain scores (1-10) and a composite quality score. Entirely read-only: analyzes but never modifies code. Use this skill when the user wants a quality review, holistic assessment, code health check, or wants to score a project across multiple quality dimensions. Triggers on: 'review this project', 'quality review', 'score this codebase', 'how good is this project', 'rate this project', 'project quality assessment', 'comprehensive code review', 'project health score', '6-domain review'. Anti-triggers: spec compliance audit (use /project-audit), refactoring (use /refactor), building features (use /feature-dev), single PR review (use /pr-review), cogitations assessment (use /cog-assess)."
argument-hint: "[--discovery-only] [--focus=<domain,...>] [--min-score=N] [path or scope]"
---

# Project Review Skill

You are leading a multi-agent quality review of a project. Your job is to discover the project structure empirically, dynamically size a review team based on project scale, coordinate specialist agents to evaluate 6 quality domains in parallel, and synthesize findings into a scored report.

**This review is entirely read-only. No agent may create, modify, or delete any project files.**

## Bundled Resources

- `references/scoring-rubric.md` — Per-domain 1-10 scoring rubrics
- `references/domain-criteria.md` — Detailed review criteria checklists per domain

Read these references before starting Phase 1.

## Help Check

If `$ARGUMENTS` is `help`, `--help`, or `-h`, print this and stop:

```
PROJECT-REVIEW(1)            GPM Skills Manual            PROJECT-REVIEW(1)

NAME
    project-review — multi-agent quality review across 6 domains

SYNOPSIS
    /project-review [options] [path or scope]

DESCRIPTION
    Discovers project structure, dynamically sizes a review team,
    evaluates 6 quality domains in parallel using specialist agents,
    and produces a scored report with per-domain findings.

    Domains: Simplicity, Security, Data, Architecture, Documentation, SDLC

    Uses swarm orchestration with agents from the refactor plugin
    (simplifier, code-reviewer, architect, code-explorer,
    test-rigor-reviewer, coverage-analyst).

OPTIONS
    --discovery-only
        Run Phase 0 only. Print the project manifest and stop.
        Useful for understanding a new codebase before review.

    --focus=<domain,...>
        Constrain review to specific domains (comma-separated).
        Valid values: simplicity, security, data, architecture,
                      documentation, sdlc
        Example: --focus=security,architecture

    --min-score=N
        Set minimum acceptable composite score (1-10). If the
        composite falls below this threshold, the report includes
        a prominent warning. Default: none.

    path or scope
        Optional path to review a subdirectory, or description
        of scope. Default: entire project from working directory root.

EXAMPLES
    /project-review                          Full 6-domain review
    /project-review --discovery-only         Just map the project
    /project-review --focus=security,sdlc    Security + SDLC only
    /project-review --min-score=7            Warn if composite < 7
    /project-review crates/core/             Review a specific module

SEE ALSO
    /project-audit   Spec compliance audit
    /refactor         Code quality improvement
    /cog-assess       Cogitations quality scoring
    /pr-review        Single PR review
```

## Arguments

**$ARGUMENTS**: Optional flags and scope.

Parse before any processing:

- `--discovery-only` — Run Phase 0 only, print manifest, stop.
- `--focus=<domain,...>` — Comma-separated domain subset. Validate each against: `{simplicity, security, data, architecture, documentation, sdlc}`. If invalid, report error and stop.
- `--min-score=N` — Minimum composite score threshold (1-10). Default: none. **This is a report annotation, not a mode switch.** When set, all phases (0 through 4) execute normally — discovery, team assembly, parallel domain reviews, and synthesis all run exactly as they would without this flag. The only effect is in Phase 4: if the composite score falls below N, a prominent WARNING line is added to the report. Do NOT skip or simulate any phases when --min-score is set.
- `--help`, `-h` — Print help and stop.

Remaining text is the review scope (path or description). Default: entire project.

### Path Scope Handling

When the remaining text is a filesystem path (contains `/` or looks like a directory name):

1. **Existence check**: Before Phase 0, verify the path exists relative to the project root using `ls` or `test -d`. If the path does NOT exist, report the error gracefully and stop:
   ```
   Error: Scope path '{path}' does not exist in this project.
   Searched from: {project_root}
   ```
   Do not proceed to Phase 0 or any subsequent phases.

2. **Selective re-rooting**: Only **source-code discovery** steps are re-rooted to the scoped path. **Project-level metadata** steps always search from the project root because those artifacts (manifests, CI, docs) live at the root, not inside subdirectories.

   **Re-rooted to `{path}`** (source code):
   - Step 0.1 (File Tree Scan): `find {path}` instead of `find .`
   - Step 0.3 (Source File Count): counts only files within `{path}`
   - Step 0.4 (Module Enumeration): constrained to the subtree

   **Always project root** (metadata):
   - Step 0.2 (Language Detection): manifests (`Cargo.toml`, `pyproject.toml`, etc.) live at the project root
   - Step 0.5 (Test Infrastructure): test config is project-level
   - Step 0.6 (CI/CD Detection): `.github/workflows/` is at the project root
   - Step 0.7 (Documentation Inventory): README, CONTRIBUTING, ADRs are project-level
   - Step 0.8 (API Surface): OpenAPI specs, protobuf defs are project-level

3. **Manifest annotation**: The `project_manifest` must include the scope:
   ```json
   {"scope": "crates/core/", "scoped": true, ...}
   ```

4. **Team sizing**: Uses the scoped `source_file_count` (files within the subtree only), NOT the full project file count. This ensures a subdirectory with 15 files gets a Tiny-tier team, not a Medium-tier team because the full project has 300 files.

---

## End-to-End Flow by Invocation Type

Every invocation follows this phase sequence. **No flags skip intermediate phases** — flags only modify behavior within phases or add annotations to the report.

| Invocation | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| `--help` | skip | skip | skip | skip | Print man page |
| `--discovery-only` | **RUN** | skip | skip | skip | Print manifest |
| `--focus=...` | **RUN** | **RUN** (filtered roster) | **RUN** (focused domains only) | **RUN** (mean of assessed) | **RUN** (excluded domains noted) |
| `--min-score=N` | **RUN** | **RUN** | **RUN** | **RUN** | **RUN** + WARNING if below |
| `path scope` | **RUN** (re-rooted) | **RUN** (scoped sizing) | **RUN** | **RUN** | **RUN** |
| *(no flags)* | **RUN** | **RUN** | **RUN** | **RUN** | **RUN** |

**Critical**: `--min-score` is a **report annotation only**. It does NOT change which phases run or how scores are computed. Phases 0, 1, 2, and 3 execute identically with or without `--min-score`. The only difference is in Phase 4, where a WARNING line is conditionally added.

---

## Phase 0: Discovery (Lead-Driven)

The lead performs discovery directly — no agents are spawned yet. This runs before TeamCreate so the sizing algorithm has data to work with.

**Path scope pre-check**: If a path scope was parsed from `$ARGUMENTS`, verify the path exists BEFORE running any discovery steps. If it does not exist, report the error (see "Path Scope Handling" above) and stop — do not continue to Phase 1 or beyond. If the path exists, substitute it for `.` in **source-code discovery steps only** (Steps 0.1, 0.3, 0.4). Steps 0.2, 0.5-0.8 always search from the project root — see "Path Scope Handling" for the full re-rooting rules.

**Important**: This phase runs for ALL invocations that are not `--help` or `--discovery-only`-then-stop. The `--min-score` and `--focus` flags do NOT skip this phase — they only affect Phase 1 (agent roster filtering) and Phase 4 (report annotations).

### Step 0.1: File Tree Scan

Map config, manifest, and source files (3 levels deep). Use `{scope_path}` (defaults to `.` if no path scope given):
```bash
find {scope_path} -maxdepth 3 -type f \( -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.md" -o -name "*.lock" -o -name "Makefile" -o -name "Dockerfile" \) | sort | head -200
```

### Step 0.2: Language Detection

Identify primary and secondary languages by checking for manifests:

| Manifest | Language |
|---|---|
| `Cargo.toml` | Rust |
| `pyproject.toml` / `setup.py` | Python |
| `package.json` | JavaScript/TypeScript |
| `go.mod` | Go |
| `pom.xml` / `build.gradle` | Java/Kotlin |

Use Glob to check which manifests exist at the **project root** (not the scope path — manifests are always project-level).

### Step 0.3: Source File Count

Count source files excluding vendored/generated directories. Use `{scope_path}` (defaults to `.`):
```bash
find {scope_path} -type f \( -name "*.rs" -o -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.go" -o -name "*.java" -o -name "*.kt" -o -name "*.rb" -o -name "*.c" -o -name "*.cpp" -o -name "*.h" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/vendor/*" \
  -not -path "*/target/*" -not -path "*/__pycache__/*" -not -path "*/dist/*" \
  -not -path "*/.git/*" -not -path "*/generated/*" | wc -l
```

**When scoped**: This count reflects only files within the scoped subtree. This scoped count is what determines team sizing in Phase 1.

### Step 0.4: Module Enumeration

Use Glob/Bash to list packages, crates, workspace members, or service boundaries. **When scoped**: constrain to the subtree at `{scope_path}`.

### Step 0.5: Test Infrastructure

Use Glob to find test directories, test config files, and coverage config. **Always searches from the project root** — test config is project-level even when reviewing a subdirectory.

### Step 0.6: CI/CD Detection

Use Glob to find `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `Dockerfile`, `docker-compose.yml`. **Always searches from the project root** — CI lives at the repo root.

### Step 0.7: Documentation Inventory

Use Glob to find README, CONTRIBUTING, CHANGELOG, ADRs, API docs, doc comment config. **Always searches from the project root** — project documentation is repo-level.

### Step 0.8: API Surface

Use Glob to find OpenAPI/AsyncAPI specs, GraphQL schemas, protobuf definitions, CLI entry points. **Always searches from the project root**.

### Discovery Output

Build the `project_manifest` JSON from the gathered data:

```json
{
  "project_name": "...",
  "languages": ["python"],
  "build_tool": "make + pyproject.toml",
  "source_file_count": 42,
  "modules": ["scripts/", "tests/"],
  "test_dirs": ["tests/"],
  "test_command": "pytest",
  "lint_command": "ruff check",
  "ci_workflows": [".github/workflows/ci.yml"],
  "doc_files": ["README.md", "CONTRIBUTING.md", "docs/adr/"],
  "api_specs": [],
  "security_patterns": ["bandit configured"],
  "has_tests": true,
  "has_ci": true,
  "has_docs": true
}
```

Store `project_manifest` in memory — it will be written to the blackboard in Phase 1 after TeamCreate.

**If `--discovery-only`**: Present the manifest to the user and stop.

---

## Phase 1: Sizing and Team Assembly

**This phase always runs after Phase 0** for any invocation that is not `--help` or `--discovery-only`. The `--min-score` flag does NOT skip this phase.

Read `project_manifest` from the blackboard. Determine the project size tier and assemble the review team.

### Sizing Algorithm

Classify by `source_file_count`:

| Tier | Source Files | Description |
|------|-------------|-------------|
| **Tiny** | < 20 | Script, small library, or nascent project |
| **Small** | 20 – 100 | Typical single-purpose library or service |
| **Medium** | 100 – 500 | Substantial application or multi-module project |
| **Large** | 500+ | Large application, monorepo, or platform |

### Agent Roster by Tier

**Constraints**: If `--focus` is set, only spawn agents for focused domains. If `has_tests` is false in the manifest, do not spawn `test-rigor-reviewer` or `coverage-analyst`.

#### Tiny (< 20 source files) — 4 agents

| Agent Name | Type | Domains | Task |
|------------|------|---------|------|
| `explorer-review` | `code-explorer` | Documentation + SDLC | Analyze docs inventory, CI/CD config, build system, quality tooling |
| `architect-review` | `architect` | Architecture + Data | SOLID principles, coupling, layer separation, data flow, query patterns, state management |
| `simplifier-review` | `simplifier` | Simplicity | **READ-ONLY MODE.** Analyze code complexity, duplication, naming, function size, dead code. Report findings — do NOT modify any files. |
| `security-review` | `code-reviewer` | Security | Mode 1 Security Baseline — input validation, auth, secrets, OWASP, dependency audit |

#### Small (20-100 source files) — 5-6 agents

All Tiny agents, plus:

| Agent Name | Type | Domains | Task |
|------------|------|---------|------|
| `test-reviewer` | `test-rigor-reviewer` | SDLC (test quality) | Score test suite rigor 0.0-1.0. Feeds into SDLC domain score. *(Only if `has_tests`)* |

In this tier, `explorer-review` still handles both Documentation and SDLC. `architect-review` still handles both Architecture and Data.

#### Medium (100-500 source files) — 7-8 agents

| Agent Name | Type | Domains | Task |
|------------|------|---------|------|
| `explorer-docs` | `code-explorer` | Documentation | Analyze README, API docs, code comments, ADRs, CONTRIBUTING, CHANGELOG, examples |
| `explorer-sdlc` | `code-explorer` | SDLC | Analyze CI/CD, build system, test infra, linter config, release process, dependency management |
| `architect-arch` | `architect` | Architecture | SOLID, coupling/cohesion, layer separation, dependency direction, patterns, extensibility |
| `architect-data` | `architect` | Data | Data flow integrity, query patterns, serialization, state management, caching, PII |
| `simplifier-review` | `simplifier` | Simplicity | **READ-ONLY MODE.** Complexity, duplication, naming, function size, abstractions, dead code |
| `security-review` | `code-reviewer` | Security | Mode 1 Security Baseline — full OWASP + dependency audit |
| `test-reviewer` | `test-rigor-reviewer` | SDLC (test quality) | Test rigor scoring. *(Only if `has_tests`)* |

#### Large (500+ source files) — 8-10 agents

| Agent Name | Type | Domains | Task |
|------------|------|---------|------|
| `explorer-docs` | `code-explorer` | Documentation | Deep documentation analysis across all modules |
| `explorer-sdlc` | `code-explorer` | SDLC | CI/CD, build system, release, dependency management, dev environment |
| `architect-arch` | `architect` | Architecture | Full SOLID + pattern analysis across module boundaries |
| `architect-data` | `architect` | Data | Data flow, queries, serialization, state, caching, privacy across all modules |
| `simplifier-review` | `simplifier` | Simplicity | **READ-ONLY analysis.** Full codebase simplicity analysis |
| `security-review` | `code-reviewer` | Security | Mode 1 Security Baseline — module-by-module structured pass. For each module in the manifest, review: input validation, auth, secrets, OWASP, dependency audit. Produces a single consolidated security score and per-module findings. |
| `test-reviewer` | `test-rigor-reviewer` | SDLC (test quality) | Test rigor scoring *(Only if `has_tests`)* |
| `coverage-review` | `coverage-analyst` | SDLC (coverage) | Run coverage tools (read-only), identify untested paths *(Only if `has_tests`)* |

### Team Assembly

You MUST use the full swarm pattern: TeamCreate → blackboard_create → Agent with team_name (per teammate) → TaskCreate → SendMessage. Do NOT fall back to spawning standalone Agent subagents without a team.

**Step 1.1**: Read `references/scoring-rubric.md` and `references/domain-criteria.md`.

**Step 1.2**: Determine tier from `source_file_count`.

**Step 1.3**: Build the agent roster:
- Start with the tier's full roster from the tables above.
- Apply `--focus` filter: only include agents whose domains intersect the focus set.
- Apply `has_tests` filter: exclude `test-rigor-reviewer` and `coverage-analyst` if no tests.

**Step 1.4**: Call `TeamCreate` with team name `"project-review"`.

**Step 1.5**: Call `blackboard_create` with task_id `"project-review"`. Store the blackboard ID.

**Step 1.6**: Write `project_manifest` and `team_sizing` to the blackboard:
```json
{"tier": "small", "source_files": 42, "agent_count": 5, "domains": ["simplicity", "security", "data", "architecture", "documentation", "sdlc"]}
```

**Step 1.7 — Spawn teammates**: For each agent in the roster, spawn it using the **Agent tool** with `team_name: "project-review"`. Launch **all** agents in a **single parallel batch** (one message, multiple Agent tool calls). The maximum roster size is 10 (Large tier with tests) which is within the platform's parallel spawn limit — do not cap or defer any spawns. All agents in the roster are independent — no agent's task depends on another agent's output.

Each teammate spawn prompt must include the read-only contract and task discovery protocol:

```
You are {agent-name} on the project-review team. This is a READ-ONLY quality review.

READ-ONLY CONTRACT — MANDATORY:
1. Do NOT use Write or Edit tools. Do not create, modify, or delete any files.
2. Do NOT append to .refactor/agent-audit.jsonl — skip the audit log step.
3. Bash is permitted only for read-only commands: find, wc, git log, git diff, jq (read-only), tool version checks, dry-run test collection.
4. Use only: Glob, Grep, Read, Bash (read-only), TaskList, TaskGet, TaskUpdate, SendMessage.

TASK DISCOVERY PROTOCOL:
1. When you receive a message from the team lead, call TaskList to find tasks assigned to you (owner = your name).
2. Call TaskGet on your assigned task to read the full description.
3. Work on the task using only read-only tools.
4. When done: (a) mark it completed via TaskUpdate, (b) send your findings to the team lead via SendMessage as JSON.
5. If no tasks are assigned, wait for the next message from the team lead.
```

Example spawn for each agent type (adapt names per tier):

- **simplifier-review**: `Agent(subagent_type: "refactor:simplifier", team_name: "project-review", name: "simplifier-review", prompt: "{spawn prompt above}")`
- **security-review**: `Agent(subagent_type: "refactor:code-reviewer", team_name: "project-review", name: "security-review", prompt: "{spawn prompt above}")`
- **architect-review**: `Agent(subagent_type: "refactor:architect", team_name: "project-review", name: "architect-review", prompt: "{spawn prompt above}")`
- **explorer-review**: `Agent(subagent_type: "refactor:code-explorer", team_name: "project-review", name: "explorer-review", prompt: "{spawn prompt above}")`
- **test-reviewer**: `Agent(subagent_type: "refactor:test-rigor-reviewer", team_name: "project-review", name: "test-reviewer", prompt: "{spawn prompt above}")`
- **coverage-review**: `Agent(subagent_type: "refactor:coverage-analyst", team_name: "project-review", name: "coverage-review", prompt: "{spawn prompt above}")`

**Step 1.8**: After all agents are spawned, create `TaskCreate` for each domain review task, assigned to the appropriate agent by `owner`. Embed the `project_manifest` JSON directly in each task description.

### Task Template

Each domain task includes:

```
## Domain Review: {Domain Name}

### READ-ONLY CONTRACT — MANDATORY

This is a read-only review. The following constraints are absolute:

1. Do NOT use Write or Edit tools. Do not create, modify, or delete any files.
2. Do NOT append to `.refactor/agent-audit.jsonl` — skip the audit log step from your standard protocol.
3. Do NOT run any Bash commands that create or modify files. Bash is permitted only for read-only commands: `find`, `wc`, `git log`, `git diff`, `jq` (read-only queries), tool version checks, and dry-run test collection.
4. Use only: Glob, Grep, Read, Bash (read-only), TaskList, TaskGet, TaskUpdate, SendMessage.

### Project Context
{Insert project_manifest JSON from blackboard}

### Scoring Rubric
{Insert relevant domain section from references/scoring-rubric.md}

### Review Criteria Checklist
{Insert relevant domain section from references/domain-criteria.md}

### Instructions

1. Read the project manifest to understand scope and structure.
2. Systematically work through the criteria checklist.
3. For each criterion, cite file:line evidence.
4. Score the domain 1-10 using the rubric.
5. When done: (a) mark your task completed via `TaskUpdate`, (b) send your findings to the team lead via `SendMessage` as JSON:

{
  "domain": "{domain}",
  "score": N.N,
  "rating": "{Excellent|Good|Adequate|Needs Improvement|Critical}",
  "summary": "1-2 sentence assessment",
  "strengths": [{"description": "...", "evidence": "file:line"}],
  "findings": [
    {
      "id": 1,
      "description": "...",
      "severity": "High|Medium|Low",
      "location": "file:line",
      "recommendation": "..."
    }
  ]
}
```

The lead writes all findings to the blackboard after receiving them via SendMessage — agents do not write to the blackboard directly.

### Combined Domain Tasks

When an agent covers multiple domains (Tiny/Small tiers), the task includes both domain rubrics and checklists with instructions to produce separate `review_{domain}_findings` entries for each domain.

---

## Phase 2: Parallel Domain Reviews

**This phase always runs after Phase 1** for any invocation that is not `--help` or `--discovery-only`. The `--min-score` flag does NOT skip this phase — domain reviews must execute to produce real scores.

After all tasks are created (Step 1.8), send a kickoff `SendMessage` to each spawned teammate:

```
SendMessage to: "{agent-name}"
message: "Your domain review task is ready. Call TaskList to find your assigned task and begin the review."
```

Send all kickoff messages in a **single parallel batch**. All domain agents work concurrently.

Monitor progress:
1. Wait for `SendMessage` responses from each agent containing their domain findings JSON.
2. Track completion count against expected domain count.
3. If an agent reports `HEALTH_CHECK_FAILED` or `blocked`, note the domain as "not assessed" and continue.
4. **Circuit breaker**: If more than half the agents fail, abort the review, clean up via `TeamDelete`, and report the failures.

When all agents complete (or fail), proceed to Phase 3.

---

## Phase 3: Synthesis

Collect all domain findings received via `SendMessage` from agents during Phase 2. Write each to the blackboard under `review_{domain}_findings` for persistence. For domains where `test-rigor-reviewer` or `coverage-analyst` produced supplementary data, merge their findings into the SDLC domain.

### Score Computation

1. Collect per-domain scores from blackboard findings.
2. **Composite score** = arithmetic mean of all assessed domain scores, rounded to 1 decimal place.
3. Map composite to rating: 9-10 Excellent, 7-8 Good, 5-6 Adequate, 3-4 Needs Improvement, 1-2 Critical.
4. If `--min-score` is set and composite < threshold, flag as **BELOW THRESHOLD**.

### Cross-Domain Analysis

1. Rank all findings across domains by severity (High > Medium > Low).
2. Identify the top 5 most impactful findings.
3. Look for cross-domain patterns (e.g., missing validation appears in both Security and Data domains).
4. Produce 3-5 actionable recommendations prioritized by impact.

### Missing Domain Handling

If a domain was not assessed (agent failure, no tests for test-quality, or `--focus` exclusion):
- Mark as "Not assessed" in the report.
- Exclude from composite score calculation.
- Note the reason (agent failure, not applicable, excluded by --focus).

---

## Phase 4: Report

Present the final report to the user. Clean up the team via `TeamDelete`.

### Report Format

```markdown
# Project Quality Review

**Project**: {project_name}
**Date**: {timestamp}
**Scope**: {scope description or "entire project"}
**Size tier**: {Tiny|Small|Medium|Large} ({N} source files)
**Tech stack**: {languages, build tool, frameworks}
**Review team**: {N} agents across {M} domains

---

## Composite Score: X.X / 10 — {Rating}

{If --min-score and composite < threshold:}
**WARNING: Composite score X.X is below the minimum threshold of {min-score}.**

| Domain | Score | Rating | Top Finding |
|--------|-------|--------|-------------|
| Simplicity | X/10 | {rating} | {one-line top finding or "No issues"} |
| Security | X/10 | {rating} | {one-line top finding} |
| Data | X/10 | {rating} | {one-line top finding} |
| Architecture | X/10 | {rating} | {one-line top finding} |
| Documentation | X/10 | {rating} | {one-line top finding} |
| SDLC | X/10 | {rating} | {one-line top finding} |

---

## Domain Reports

### Simplicity — X/10 ({rating})

**Summary**: {1-2 sentence assessment from agent}

**Strengths**:
- {strength with file:line evidence}

**Findings**:
| # | Finding | Severity | Location | Recommendation |
|---|---------|----------|----------|----------------|
| 1 | {desc} | {High/Med/Low} | file:line | {suggestion} |

---

### Security — X/10 ({rating})

{Same structure as above}

---

### Data — X/10 ({rating})

{Same structure}

---

### Architecture — X/10 ({rating})

{Same structure}

---

### Documentation — X/10 ({rating})

{Same structure}

---

### SDLC — X/10 ({rating})

{Same structure}

{If test-rigor-reviewer contributed:}
#### Test Quality Sub-assessment
- Test rigor score: X.X / 1.0 ({PASS|NEEDS IMPROVEMENT|FAIL})
- Tests evaluated: {count}
- Anti-patterns detected: {list}

{If coverage-analyst contributed:}
#### Coverage Sub-assessment
- Line coverage: X%
- Branch coverage: X%
- Uncovered critical paths: {list}

---

## Top Recommendations

1. **{Category}**: {Highest-impact recommendation} — affects {domain(s)}
2. **{Category}**: {Second recommendation}
3. **{Category}**: {Third recommendation}
4. **{Category}**: {Fourth recommendation} *(if applicable)*
5. **{Category}**: {Fifth recommendation} *(if applicable)*

## Methodology

- Review performed by {N} specialist agents across {M} domains
- Project classified as **{tier}** ({N} source files, {languages})
- All findings cite specific file paths and line numbers
- Scoring uses a 1-10 rubric per domain (see `references/scoring-rubric.md`)
- Composite score is the unweighted arithmetic mean of assessed domains
- Agents operated in read-only mode — no project files were modified
```

---

## Constraints

1. **Read-only** — No agent may create, modify, or delete any project files. This is a review, not a refactoring.
2. **Discover, don't assume** — Every path, tool, and convention must be found empirically in Phase 0.
3. **Cite sources** — Every finding must reference the specific file and line range.
4. **Dynamic sizing** — Team size adapts to project scale. Never spawn 12 agents for a 10-file project.
5. **Graceful degradation** — If a domain cannot be assessed (no tests, agent failure), mark it and continue.
6. **Respect focus flags** — `--focus` constrains which domains run. Don't expand scope.
7. **Non-redundant** — If multiple agents cover overlapping areas, deduplicate findings in Phase 3.
8. **Guaranteed cleanup** — Always call `TeamDelete` in Phase 4, even if earlier phases fail. Use a finally-block pattern: if any phase errors, skip to cleanup.

---

Begin processing based on: $ARGUMENTS

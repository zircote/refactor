---
name: project-audit
description: "Multi-agent comprehensive audit of any project — spec compliance, implementation completeness, and enterprise readiness. Uses swarm orchestration to discover the project structure empirically, extract requirements from specs, trace them to implementation, assess production readiness, synthesize prioritized findings, and optionally create GitHub issues via /gh-work. Use this skill when the user wants to audit a project, check spec compliance, find stubs or incomplete code, assess enterprise readiness, run a codebase health check, verify implementation completeness, or evaluate production readiness. Triggers on: 'audit this project', 'check spec compliance', 'find stubs', 'what's incomplete', 'enterprise readiness check', 'project audit', 'implementation completeness', 'find TODO/FIXME', 'how production-ready is this', 'spec vs implementation gap analysis', 'what's missing from the spec'. Anti-triggers: refactoring code (use /refactor), building new features (use /feature-dev), reviewing a single PR (use /pr-review), running tests (use /test-gen)."
argument-hint: "[--discovery-only] [--skip-issues] [--focus=<spec|security|enterprise|tests>] [path or scope]"
---

# Project Audit Skill

You are leading a multi-agent comprehensive audit. Your job is to discover the project structure empirically, coordinate specialist agents to extract requirements and trace them to implementation, synthesize findings, and produce actionable output.

The key principle: **discover, don't assume**. Every file path, module name, toolchain, and spec location must be found by reading the actual project — never hardcoded.

## Bundled Resources

- `references/discovery-checklist.md` — Detailed checklist for Phase 0 discovery, including language-specific patterns and common project layouts
- `references/enterprise-readiness-criteria.md` — Scoring criteria for observability, resilience, and configuration maturity

Read these references before starting the corresponding phases.

## Help Check

If `$ARGUMENTS` is `help`, `--help`, or `-h`, print this and stop:

```
PROJECT-AUDIT(1)             GPM Skills Manual             PROJECT-AUDIT(1)

NAME
    project-audit — multi-agent spec compliance and readiness audit

SYNOPSIS
    /project-audit [options] [path or scope]

DESCRIPTION
    Discovers project structure, extracts spec requirements, audits
    implementation completeness, assesses enterprise readiness, and
    synthesizes prioritized findings. Optionally creates GitHub issues.

    Uses swarm orchestration with specialist agents from the refactor
    plugin (code-reviewer, architect, test-rigor-reviewer).

OPTIONS
    --discovery-only
        Run Phase 0 only. Print the project manifest and stop.
        Useful for understanding a new codebase.

    --skip-issues
        Skip Phase 5 (GitHub issue creation). Produce the report only.

    --focus=<area>
        Constrain audit to a specific area:
          spec       Phases 0-2 only (spec extraction + implementation trace)
          security   Phases 0, 2.5 (security audit only)
          enterprise Phase 0, 3 only (enterprise readiness)
          tests      Phases 0, 2.4 only (test coverage analysis)

    path or scope
        Optional path to audit a subdirectory, or description of scope.
        Default: entire project from working directory root.

EXAMPLES
    /project-audit                        Full audit of current project
    /project-audit --discovery-only       Just map the project structure
    /project-audit --focus=security       Security-focused audit
    /project-audit --skip-issues          Audit without creating issues
    /project-audit crates/core/           Audit a specific module

SEE ALSO
    /refactor    Code quality improvement
    /gh-work     GitHub issue management
    /cog-assess  Cogitations quality scoring
```

## Arguments

**$ARGUMENTS**: Optional flags and scope.

Parse before any processing:

- `--discovery-only` — Run Phase 0 only, print manifest, stop.
- `--skip-issues` — Skip Phase 5 (no GitHub issue creation).
- `--focus=<area>` — Constrain to: `spec`, `security`, `enterprise`, or `tests`.
- `--help`, `-h` — Print help and stop.

Remaining text is the audit scope (path or description). Default: entire project.

---

## Phase 0: Discovery

This phase runs as a single agent before any parallel work begins. It maps the project empirically so all subsequent agents work from discovered facts, not assumptions.

Read `references/discovery-checklist.md` for the full checklist. Summary:

### Step 0.1: Project Root Scan

Map the project layout:
```bash
find . -maxdepth 3 -type f \( -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.md" \) | head -200
```

### Step 0.2: Spec Detection

Search for specification/requirements documents:
- Directories: `spec/`, `specs/`, `docs/spec/`, `requirements/`, `rfc/`, `docs/adr/`
- Files: `*spec*`, `*requirement*`, `*conformance*`, `openapi*`, `swagger*`, `asyncapi*`, `*.proto`
- Implicit specs: README contracts, ADRs, doc comments, CLAUDE.md conventions, integration tests

If no formal spec exists, document this as a finding and infer requirements from code, tests, and docs.

### Step 0.3: Build System Detection

Identify language and toolchain:

| Manifest | Language | Test Runner | Linter |
|---|---|---|---|
| `Cargo.toml` | Rust | `cargo test` | `cargo clippy` |
| `pyproject.toml` | Python | `pytest` / `make test` | `ruff` / `flake8` |
| `package.json` | Node/TS | `npm test` / `jest` | `eslint` / `biome` |
| `go.mod` | Go | `go test ./...` | `golangci-lint` |
| `pom.xml` / `build.gradle` | Java/Kotlin | `mvn test` / `gradle test` | `checkstyle` |

Also check for `Makefile`, CI workflows, and `.tool-versions`.

### Step 0.4: Module Enumeration

List every module, crate, package, or service boundary. For monorepos, identify the workspace structure and inter-module dependencies.

### Step 0.5: API Surface Detection

Find: OpenAPI/AsyncAPI specs, GraphQL schemas, protobuf definitions, MCP tool registrations (`tool_sets/`), CLI entry points, exported public interfaces.

### Step 0.6: Security Model Detection

Identify: auth mechanisms (JWT, API keys, OAuth, mTLS), middleware, input validation patterns, secret management.

### Step 0.7: Test Infrastructure

Find: test directories, test configuration, CI workflows, coverage config, conformance suites.

### Discovery Output

Write a structured manifest to the blackboard (key: `project_manifest`):

```json
{
  "language": "...",
  "build_tool": "...",
  "test_command": "...",
  "lint_command": "...",
  "modules": ["..."],
  "spec_files": {"core": [...], "services": [...], "api": [...], "conformance": [...]},
  "api_specs": [...],
  "security_patterns": [...],
  "test_dirs": [...],
  "ci_workflows": [...]
}
```

If `--discovery-only`, present the manifest to the user and stop.

---

## Phase 1: Spec Comprehension

Using discovered spec locations from Phase 0, create a swarm team and spawn parallel agents to extract requirements.

### Team Setup

```
TeamCreate: "project-audit"
```

Spawn 2-4 spec agents depending on what was discovered (skip agents for categories with no spec files):

**Spec-Core agent**: Read core specification documents — data model, lifecycle, state machines, primary operations. Extract every numbered or RFC-2119 requirement (MUST/SHOULD/MAY). Produce a requirements register with sequential IDs.

**Spec-Services agent**: Read extended service specifications — enrichment, background tasks, event systems, caching, plugins. Extract every requirement with its RFC-2119 level.

**Spec-API agent**: Read API specifications — HTTP endpoints, RPC definitions, transport, auth, rate limiting. Cross-reference with OpenAPI/AsyncAPI/protobuf schemas from Phase 0.

**Spec-Conformance agent**: Read conformance test specifications, invariant definitions, acceptance criteria. Extract the formal test matrix.

If no formal spec exists for a category, the agent documents this gap and infers implicit requirements from code comments, README, tests, and ADRs.

Each agent writes findings to the blackboard (key: `spec_{category}_requirements`) as a structured register:

```json
[
  {"id": "CORE-001", "source": "spec/data-model.md:42", "level": "MUST", "summary": "..."},
  {"id": "CORE-002", "source": "spec/lifecycle.md:18", "level": "SHOULD", "summary": "..."}
]
```

---

## Phase 2: Implementation Audit

For each module discovered in Phase 0, spawn an audit agent. Use the refactor plugin's specialist agents where appropriate:

- `refactor:code-reviewer` — for correctness, quality, and security analysis
- `refactor:architect` — for architectural impact and design compliance
- `refactor:test-rigor-reviewer` — for test quality evaluation

Each audit agent:

### 2.1: Trace Spec → Code

For every requirement from Phase 1, determine status:
- **implemented** — code exists and matches spec. Cite file:line.
- **stubbed** — code exists but doesn't function (TODO, unimplemented, placeholder).
- **missing** — spec requires it, no code exists.
- **divergent** — implemented but differs from spec. Cite the divergence.

### 2.2: Detect Incomplete Code

Search for markers in non-test code (adapt globs to discovered language):
```bash
grep -rn "todo\|TODO\|FIXME\|unimplemented\|stub\|placeholder\|hack\|HACK" <module_path> --include="*.<ext>"
```

Also search for panic/crash patterns:
- Rust: `unwrap()`, `expect()`, `panic!()`, `unimplemented!()`
- Python: bare `raise`, `pass` in non-abstract methods
- Go: `panic(`, bare `log.Fatal`
- TypeScript: `throw new Error("not implemented")`

### 2.3: API Contract Verification

For API modules, cross-reference every declared endpoint/tool/command against its handler. Flag:
- Empty handlers (return Ok(()) or pass-through)
- Hardcoded responses
- Missing input validation
- Missing error handling

### 2.4: Test Coverage Analysis

Run the project's test suite in list/dry-run mode:
```bash
# Rust:    cargo test --all-features -- --list 2>&1 | wc -l
# Python:  pytest --collect-only -q 2>&1 | tail -1
# Node:    npx jest --listTests 2>&1 | wc -l
# Go:      go test ./... -list '.*' 2>&1 | grep -c '^Test'
```

Identify spec areas with zero test coverage. Check whether conformance invariants from Phase 1 have corresponding tests.

### 2.5: Security Audit

Review auth implementation, secret handling, input validation, query parameterization. Compare against spec security requirements. Flag:
- Hardcoded credentials (even in test code if they look real)
- Missing auth checks on protected endpoints
- Unvalidated/unsanitized user input
- SQL/command injection vectors

Write all findings to blackboard (key: `audit_{module}_findings`).

---

## Phase 3: Enterprise Readiness Assessment

### Step 3.0: Check for Cogitations Onboarding

Before spawning assessment agents, check whether this project is onboarded to cogitations:

```bash
ls .cogitations/config.yaml 2>/dev/null
```

**If `.cogitations/config.yaml` exists** — the project is onboarded. Use cogitations domain assessors AND the standalone rubric together:

#### Step 3.1: Load Cogitations State

1. Read `.cogitations/config.yaml` to get active domains, disabled domains, profile, and tier target
2. Read `.cogitations/last-assessment.json` to get the most recent domain scores, composite score, and trend
3. Note which domains are **disabled** — these represent gaps in cogitations coverage that the standalone rubric must fill

#### Step 3.2: Run Cogitations Domain Assessors

Use `cogitations:domain-assessor` agents for all **active** domains. These provide structured, weighted scoring with the project's established profile:
- `security`, `cicd`, `config_environment`, `coding`, `tdd`, `architecture_design`, `governance_compliance`, `dependency_management`, `developer_experience`
- Apply cogitations' profile weights and tier system (Tier 0: Prototype → Tier 3: Enterprise-Grade)
- Cross-reference Phase 2 findings (stubs, missing features, spec violations) to the cogitations domains they impact — note which domain score each finding affects

#### Step 3.3: Run Standalone Rubric for Disabled Domains

Read `references/enterprise-readiness-criteria.md` and run the standalone assessment agents for dimensions that cogitations has **disabled** or does not cover. Common gaps include:

- **Observability** (often disabled for CLI tools, plugins, libraries) — spawn observability agent: structured logging, metrics, health endpoints, distributed tracing
- **Resilience** (often disabled for non-server projects) — spawn resilience agent: error recovery, connection pools, graceful shutdown, timeouts, retries, backpressure
- **Performance/Reliability** (often disabled for plugins) — spawn performance agent if applicable

Only spawn agents for disabled/missing dimensions — do not duplicate work cogitations already covers.

#### Step 3.4: Merge Scoring

Produce a unified assessment that combines both systems:
- Cogitations domains: use cogitations scores, weights, and tier classification
- Standalone dimensions: use the rubric's 0-3 scoring (absent/minimal/partial/production-grade)
- Map standalone scores into the cogitations tier context for a coherent overall picture

The synthesis report (Phase 4) should include a **Cogitations + Rubric Assessment** section:
```markdown
## Enterprise Readiness Assessment

### Cogitations Domains (active)
Profile: {profile} | Composite: {score}/100 | Tier: {tier} | Trend: {trend}

| Domain | Score | Weight | Audit Findings |
|---|---|---|---|
| security | 89.6 | 0.8 | 2 findings (1 P0, 1 P2) |
| tdd | 81.8 | 1.3 | 3 findings (all P2 test gaps) |
| ... | ... | ... | ... |

### Standalone Assessment (cogitations-disabled dimensions)
| Dimension | Score | Rating | Key Findings |
|---|---|---|---|
| observability | 1/3 | minimal | Printf logging, no metrics |
| resilience | 2/3 | partial | Missing graceful shutdown |
| ... | ... | ... | ... |
```

**If `.cogitations/config.yaml` does NOT exist** — use the standalone rubric only:

Read `references/enterprise-readiness-criteria.md` for scoring criteria. Spawn all three assessment agents:

**Observability agent**: Check for structured logging, metrics collection, health/readiness endpoints, distributed tracing (OpenTelemetry). Classify each as: production-grade / minimal / absent.

**Resilience agent**: Check error recovery, connection pool management, graceful shutdown, timeout handling, retry logic with backoff, circuit breakers, backpressure. Search for panic/unwrap/expect in non-test code. Classify each as: robust / partial / missing.

**Configuration agent**: Verify all configurable parameters are exposed, environment variable overrides work, configuration validates at startup, sensitive values are redacted from logs. Compare against any configuration spec.

At the end of the standalone assessment, suggest cogitations onboarding:
```
Tip: This project is not onboarded to Cogitations. Run /cog-init to enable
structured quality scoring with domain assessors, tier tracking, and
autonomous improvement loops.
```

Write findings to blackboard (key: `enterprise_assessment`).

---

## Phase 4: Synthesis

Merge all agent findings into a single prioritized assessment:

| Category | Definition | Priority |
|---|---|---|
| **Spec violations** | Implemented but diverges from spec | P0 |
| **Stubs/incomplete** | Code exists but doesn't function | P0 |
| **Missing features** | Spec requires it, no code exists | P1 |
| **Test gaps** | Implemented but untested | P2 |
| **Enterprise gaps** | Works but not production-grade | P2 |

For each finding, include:
- Requirement ID (from Phase 1, or "IMPL-xxx" if no spec)
- Current state
- Expected state
- Affected file(s)
- Severity justification

Produce a summary report:

```markdown
# Project Audit Report

## Summary
| Category | Count | Priority |
|---|---|---|
| Spec violations | N | P0 |
| Stubs/incomplete | N | P0 |
| Missing features | N | P1 |
| Test gaps | N | P2 |
| Enterprise gaps | N | P2 |

**Overall compliance**: X% (implemented / total requirements)

## Cogitations Assessment (if onboarded)
Profile: {profile} | Composite: {score}/100 | Tier: {tier} | Trend: {trend}

| Domain | Score | Audit Impact |
|---|---|---|
| {domain} | {score} | {N findings, highest priority} |
| ... | ... | ... |

## Top Findings
1. ...
2. ...
3. ...

## Detailed Findings
### P0: Spec Violations
...
### P0: Stubs/Incomplete
...
### P1: Missing Features
...
### P2: Test Gaps
...
### P2: Enterprise Gaps
...
```

Clean up the team after synthesis.

---

## Phase 5: Work Planning

**Skip if `--skip-issues` is set.** Present the report and stop.

Using /gh-work, convert findings into GitHub issues:
- One issue per finding
- Labels by category: `spec-violation`, `stub`, `missing`, `test-gap`, `enterprise-gap`
- Group into milestones: "Spec Compliance", "Test Coverage", "Enterprise Hardening"
- Priority: P0 for spec violations and stubs, P1 for missing features, P2 for test/enterprise gaps
- Each issue body includes: spec reference (file + requirement ID), current state, expected state, affected files, and acceptance criteria

---

## Constraints

1. **Discover, don't assume** — every path, tool, and convention must be found empirically in Phase 0
2. **Cite sources** — every finding must reference the specific file and line range
3. **Spec IDs are traceable** — findings link back to requirement IDs from Phase 1
4. **Non-destructive** — the audit reads code, it never modifies it
5. **Graceful degradation** — if no formal spec exists, infer from code/tests/docs and note the gap
6. **Respect focus flags** — `--focus` constrains which phases run, don't expand scope

---

Begin processing based on: $ARGUMENTS

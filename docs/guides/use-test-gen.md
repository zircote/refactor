---
diataxis_type: how-to
diataxis_goal: Generate test suites, evaluate existing tests, and analyze coverage using the test-architect skill
---

# How to Generate and Evaluate Tests

## Overview

The test-architect skill provides three commands for test generation and evaluation:

| Command | Purpose | Agents used |
|---------|---------|-------------|
| `/test-gen` | Full pipeline: plan, write, review, coverage | test-planner, test-writer, test-rigor-reviewer, coverage-analyst |
| `/test-plan` | Plan only: produce JSON test plan without code | test-planner |
| `/test-eval` | Evaluate existing tests: rigor review + coverage | test-rigor-reviewer, coverage-analyst |

## Prerequisites

- Refactor plugin installed and working (see [Tutorial](../tutorials/tutorial.md))
- Project in a supported language: Rust, Python, TypeScript, or Go

## Steps

### 1. Generate a full test suite

Run the full pipeline on a file, directory, or glob pattern:

```bash
# Single file
/test-gen src/auth/handler.py

# Directory
/test-gen src/auth/

# Glob pattern
/test-gen src/**/*.rs
```

The pipeline runs 4 phases sequentially: detect, plan, write, review + coverage. Generated tests follow TDD red-phase design -- they compile but are expected to fail against current implementation, revealing behavioral gaps.

#### Supported languages and tools

| Language | Test Runner | Coverage Tool | Property Library |
|----------|------------|---------------|-----------------|
| Rust | cargo test | cargo-tarpaulin | proptest |
| Python | pytest | coverage.py | hypothesis |
| TypeScript | vitest | c8 | fast-check |
| Go | go test | go tool cover | rapid |

### 2. Generate a test plan without code

Review the formal test plan before committing to code generation:

```bash
/test-plan src/auth/
```

The planner analyzes your code and produces a JSON test plan showing:
- Test cases organized by equivalence class
- Boundary value test points
- Property-based test specifications
- Technique summary (how many of each type)

When satisfied with the plan, run `/test-gen` to generate the code.

### 3. Evaluate existing tests

Audit your current test suite for quality and coverage without generating new tests:

```bash
/test-eval tests/
```

This runs the rigor reviewer and coverage analyst in parallel. You get:

- **Rigor scores** (0.0-1.0 per test): identifies tautological assertions, weak generators, and mutation-susceptible patterns
- **Coverage analysis**: line and branch coverage with gap identification
- **Prioritized recommendations**: specific improvements ranked by impact

#### Interpret rigor verdicts

| Verdict | Meaning |
|---------|---------|
| **PASS** | Overall rigor >= 0.70, no tautological tests |
| **NEEDS IMPROVEMENT** | Rigor 0.50-0.69 or 1-2 weak tests |
| **FAIL** | Rigor < 0.50 or tautological assertions detected |

#### Interpret coverage verdicts

| Verdict | Meaning |
|---------|---------|
| **MEETS TARGET** | Line >= 90%, Branch >= 85%, zero critical gaps |
| **BELOW TARGET** | Below threshold but no critical gaps |
| **CRITICAL GAPS** | Critical-severity uncovered regions (error handling, validation) |

### 4. Run coverage analysis only

Skip test generation and rigor review -- just measure coverage:

```bash
/test-gen --coverage src/
```

This detects your language's coverage tool, runs it, parses the results, and reports uncovered regions with severity classification and specific test suggestions.

### 5. Integrate with refactoring

Use `--focus=testing` with the refactor skill to combine refactoring with test quality improvement:

```bash
/refactor --focus=testing src/auth/
```

This focuses the refactoring iteration on test coverage and quality rather than code structure.

## Handle common issues

### Coverage tool not installed

If the coverage tool is not installed, the coverage-analyst reports which tool is needed:

```
Coverage tool cargo-tarpaulin not found.
Install with: cargo install cargo-tarpaulin
```

Install the tool and re-run.

### Property testing library not in dependencies

The test-writer notes missing property testing libraries in its report. Add the dependency before running generated tests:

```bash
# Rust
cargo add proptest --dev

# Python
pip install hypothesis

# TypeScript
npm install -D fast-check

# Go
go get pgregory.net/rapid
```

### Tests don't compile

If generated tests reference functions or types that don't exist, the test-writer may have misidentified the public API. Re-run with a narrower scope targeting specific files.

## Related

- [Tutorial: Your First Test Architecture](../tutorials/tutorial-test-architect.md) -- step-by-step walkthrough
- [How to Evaluate Test Quality](evaluate-test-quality.md) -- detailed rigor score interpretation
- [Quality Score Reference](../reference/quality-scores.md) -- rigor and coverage scoring rubrics
- [Understanding Test Design Techniques](../explanation/test-design-techniques.md) -- formal technique rationale
- [Agent Reference](../reference/agents.md) -- test-architect agent specifications
- [Troubleshooting](troubleshooting.md) -- additional problem resolution

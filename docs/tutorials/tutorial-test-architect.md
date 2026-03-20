---
diataxis_type: tutorial
diataxis_learning_goals:
  - Run /test-gen to generate a scientifically grounded test suite
  - Understand the 4-phase pipeline (detect, plan, write, review)
  - Read rigor scores and coverage analysis results
  - Use /test-plan for plan-only mode and /test-eval for existing test evaluation
---

# Tutorial: Your First Test Architecture

This tutorial walks you through generating a scientifically grounded test suite using the `/test-gen` command. You will see how four specialist agents collaborate to plan, write, review, and measure tests.

## What you'll learn

- How to run `/test-gen` to generate a complete test suite
- How the 4-phase pipeline works: detect, plan, write, review + coverage
- How to read rigor scores and the 0.0-1.0 quality scale
- How to use `/test-plan` for plan-only mode and `/test-eval` for existing test evaluation
- Why generated tests are designed to fail (TDD red phase)

## Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) CLI installed with the refactor plugin
- A project with source code in a supported language (Rust, Python, TypeScript, or Go)
- The project's test framework installed (`cargo test`, `pytest`, `vitest`, or `go test`)

## Steps

### Step 1: Run the full pipeline

Choose a small module in your project -- a single file or small directory works best for your first run.

```bash
/test-gen src/utils/
```

The skill starts with **Phase 0: Detection**. It identifies your project language, test framework, and directory structure. You will see output like:

```
Detected: Python project
Test runner: pytest
Coverage tool: coverage.py
Property library: hypothesis
```

### Step 2: Watch the planning phase

The **test-planner** agent analyzes your source code and produces a structured JSON test plan. It applies four formal techniques:

- **Equivalence class partitioning** -- partitions input domains into valid and invalid classes
- **Boundary value analysis** -- tests at, just inside, and just outside partition boundaries
- **State transition coverage** -- identifies states, transitions, and guard conditions
- **Property-based testing** -- identifies invariants that hold across generated inputs

You will see a summary like:

```
Test Plan Summary
- Functions analyzed: 8
- Equivalence classes: 12
- Boundary values: 8
- State transitions: 5
- Property invariants: 3
- Total: 24 test cases + 3 property tests
```

### Step 3: Watch the code generation phase

The **test-writer** agent reads the JSON plan and generates idiomatic test code for your language.

Key detail: the generated tests are designed to **FAIL**. This is the TDD red phase -- the tests assert expected behavior against your real implementation, and failing tests reveal where the code does not match the specification.

You will see:

```
Test Generation Report
- Files created: tests/test_utils.py -- 24 tests (18 unit, 3 boundary, 3 property)
- Plan coverage: 27/27 test cases implemented
```

### Step 4: Watch the review and coverage phases

Two agents run in parallel:

1. The **test-rigor-reviewer** scores each test on a 0.0-1.0 rigor scale, checking for anti-patterns like tautological assertions, weak generators, and mutation-susceptible patterns.

2. The **coverage-analyst** runs your language's coverage tool and identifies uncovered code paths.

You will see a combined report:

```
Test Rigor Review
- Overall rigor: 0.82/1.00
- Excellent: 12, Good: 9, Adequate: 4, Weak: 2
- Verdict: PASS

Coverage Analysis
- Line coverage: 87.3%
- Branch coverage: 78.1%
- Critical gaps: 2 (error handling paths)
- Verdict: BELOW TARGET
```

### Step 5: Run the generated tests

The tests are designed to fail (TDD red phase). Run them to see which behaviors your code already satisfies and which need work:

```bash
# Python
pytest tests/test_utils.py -v

# Rust
cargo test

# TypeScript
npx vitest run

# Go
go test ./...
```

Passing tests confirm existing behavior. Failing tests highlight gaps -- either bugs in your code or behaviors not yet implemented.

### Step 6: Try plan-only mode

If you want to review the test plan before generating code, use `/test-plan`:

```bash
/test-plan src/utils/
```

This runs only the detection and planning phases. The JSON test plan is presented for your review. No test files are created. When satisfied, run `/test-gen` to execute the full pipeline.

### Step 7: Evaluate existing tests

If you already have tests and want a quality audit, use `/test-eval`:

```bash
/test-eval tests/
```

This runs the rigor reviewer and coverage analyst on your **existing** test suite -- no new tests are generated. You get:

- Per-test rigor scores identifying weak or tautological assertions
- Coverage analysis with gap identification
- Prioritized recommendations for improving test quality

## What you've accomplished

You have:

- Generated a scientifically grounded test suite using `/test-gen`
- Observed the 4-phase pipeline: detect, plan, write, review + coverage
- Read rigor scores and understood the 0.0-1.0 quality scale
- Seen coverage analysis with gap severity classification
- Used `/test-plan` for plan-only review
- Used `/test-eval` for existing test quality audit
- Understood the TDD red-phase design (tests are meant to fail initially)

## Next steps

- [How to Generate and Evaluate Tests](../guides/use-test-gen.md) -- practical workflows for test generation, evaluation, and coverage analysis
- [How to Evaluate Test Quality](../guides/evaluate-test-quality.md) -- detailed guide to interpreting and acting on rigor scores
- [Quality Score Reference: Rigor Scores](../reference/quality-scores.md) -- the full rigor scoring rubric and verdict criteria
- [Understanding Test Design Techniques](../explanation/test-design-techniques.md) -- why equivalence classes, boundary values, and property testing produce better tests
- [Agent Reference](../reference/agents.md) -- specifications for all twelve specialist agents
- [Tutorial: Your First Refactor](tutorial.md) -- learn the /refactor workflow

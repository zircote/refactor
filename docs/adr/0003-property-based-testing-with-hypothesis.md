# ADR-0003: Property-Based Testing with Hypothesis

## Status

Accepted

## Context

Traditional example-based tests may miss edge cases in the plugin's score computation, configuration parsing, and result formatting logic. We need confidence that these functions handle arbitrary valid inputs correctly.

## Decision

Use Hypothesis for property-based testing alongside conventional pytest tests. Focus property tests on:
- Score computation functions (associativity, bounds, monotonicity)
- Configuration parsing (round-trip serialization, schema validation)
- Result formatting (output stability, no crashes on edge inputs)

## Consequences

- **Positive**: Discovered real bugs (off-by-one in score normalization), higher confidence in correctness, tests document invariants
- **Negative**: Slower test execution (mitigated by Hypothesis profiles), potential for flaky tests on time-sensitive properties
- **Mitigations**: Use `@settings(max_examples=100)` for CI, `@settings(max_examples=1000)` for thorough local testing

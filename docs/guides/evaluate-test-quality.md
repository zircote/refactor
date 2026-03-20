---
diataxis_type: how-to
diataxis_goal: Evaluate the quality of an existing test suite using rigor scoring and coverage analysis
---

# How to Evaluate Test Quality

## Overview

The `/test-eval` command audits your existing test suite for scientific rigor and coverage gaps without generating new tests. Use it to identify weak tests, tautological assertions, and uncovered code paths.

## Prerequisites

- Refactor plugin installed and working
- Existing test files in a supported language (Rust, Python, TypeScript, or Go)
- Test runner and coverage tool available

## Run a quality evaluation

Point `/test-eval` at your test directory or specific test files:

```bash
# Evaluate all tests
/test-eval tests/

# Evaluate specific test file
/test-eval tests/test_auth.py

# Evaluate by glob
/test-eval tests/**/*_test.go
```

Two agents run in parallel: the test-rigor-reviewer scores each test, and the coverage-analyst measures code coverage.

## Read per-test rigor scores

Each test receives a score from 0.0 (useless) to 1.0 (excellent):

| Score | Rating | Meaning |
|-------|--------|---------|
| 0.9-1.0 | Excellent | Grounded in formal technique, mutation-resistant |
| 0.8-0.89 | Good | Solid test with minor improvements possible |
| 0.6-0.79 | Adequate | Tests real behavior but has gaps |
| 0.4-0.59 | Weak | Susceptible to mutations or missing scenarios |
| 0.2-0.39 | Poor | Minimal value — identity check or trivial case |
| 0.0-0.19 | Useless | Tautological, cannot fail |

## Identify and fix anti-patterns

The rigor reviewer flags specific anti-patterns. Here is how to fix each one:

### Tautological assertions (score 0.0-0.2)

Tests that cannot fail regardless of implementation.

**Before:**
```python
def test_returns_something():
    result = process(data)
    assert result is not None  # always true
```

**After:**
```python
def test_returns_expected_format():
    result = process(valid_data)
    assert result == {"status": "ok", "count": 3}
```

### Weak property generators (score 0.2-0.4)

Property tests with generators that avoid interesting inputs.

**Before:**
```python
@given(st.integers(min_value=1, max_value=3))  # tiny range
def test_prop_positive(n):
    assert process(n) > 0
```

**After:**
```python
@given(st.integers(min_value=0, max_value=10_000))
def test_prop_non_negative_output(n):
    assert process(n) >= 0
    if n == 0:
        assert process(n) == 0  # boundary behavior
```

### Mutation-susceptible patterns (score 0.4-0.6)

Tests that would still pass under common code mutations (off-by-one, negated conditions).

**Before:**
```python
def test_boundary():
    assert count_items(items) >= 0  # survives off-by-one
```

**After:**
```python
def test_boundary_exact():
    assert count_items([]) == 0
    assert count_items(["a"]) == 1
    assert count_items(["a", "b"]) == 2
```

### Missing error paths (score 0.3-0.5)

Tests that only exercise success paths.

**Fix:** Add tests with invalid inputs using your language's error assertion:
```python
def test_raises_on_invalid_input():
    with pytest.raises(ValueError):
        process(invalid_data)
```

## Read coverage gaps

The coverage analyst classifies gaps by severity:

| Severity | Meaning | Action |
|----------|---------|--------|
| **Critical** | Error handling, validation, security checks | Fix immediately |
| **Important** | Core business logic, state transitions | Fix before release |
| **Nice-to-have** | Logging, debug paths, rarely-hit branches | Fix when convenient |

Each gap includes a specific test suggestion with target function, input values, and expected behavior.

## Act on recommendations

The evaluation report ends with prioritized recommendations. Start with:

1. **Remove tautological tests** — they provide false confidence
2. **Add boundary tests** — bugs cluster at boundaries
3. **Strengthen weak assertions** — use exact values, not ranges
4. **Cover critical gaps** — error handling and validation paths first
5. **Add property tests** — for functions with identifiable invariants

## Related

- [How to Generate and Evaluate Tests](use-test-gen.md) — full pipeline including code generation
- [Quality Score Reference](../reference/quality-scores.md) — complete scoring rubrics
- [Understanding Test Design Techniques](../explanation/test-design-techniques.md) — why these techniques matter
- [Troubleshooting](troubleshooting.md) — common issues and fixes

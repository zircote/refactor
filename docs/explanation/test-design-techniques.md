---
diataxis_type: explanation
diataxis_topic: formal test design techniques and why they produce better tests than ad-hoc testing
---

# Formal Test Design Techniques

## Why formal techniques

Most test suites are written ad hoc: a developer thinks of a few examples, writes assertions for them, and calls it done. This approach has a fundamental flaw — it tests what the developer *thought of*, not what the code *needs*. Ad-hoc tests systematically miss boundary conditions, error paths, and subtle invariant violations.

Formal test design techniques solve this by providing systematic procedures for deriving test cases from specifications. Instead of asking "what should I test?", they answer "what *must* I test to achieve meaningful coverage?"

The test-architect skill applies four complementary techniques, each catching a different class of bugs.

## Equivalence class partitioning

Every input to a function belongs to an equivalence class — a set of values that the code treats identically. A function that accepts an age parameter might have three classes: negative (invalid), 0-17 (minor), and 18+ (adult). Testing one value from each class is sufficient; testing five values from the same class adds no new information.

The technique:
1. Identify all input parameters
2. Partition each parameter's domain into equivalence classes (valid and invalid)
3. Select one representative value per class
4. Combine classes across parameters using pairwise or all-combinations strategy

**What it catches:** Missing branches for valid input categories, unhandled invalid input classes, logic errors in category boundaries.

**What it misses:** Off-by-one errors at the exact boundary between classes. That is what boundary value analysis adds.

## Boundary value analysis

Bugs cluster at boundaries between equivalence classes. If a function behaves differently for values below 18 and at-or-above 18, the most likely place for a bug is right at 18 — an off-by-one error, a wrong comparison operator (`<` vs `<=`), or a fence-post mistake.

The technique:
1. For each equivalence class boundary, test three values: the boundary itself, one below, and one above
2. For numeric ranges: min, min-1, min+1, max, max-1, max+1
3. For strings: empty, single character, maximum length, maximum+1 length
4. For collections: empty, single element, typical count, maximum capacity

**What it catches:** Off-by-one errors, wrong comparison operators, fence-post errors, missing edge case handling for empty/maximum inputs.

**Why it works:** Boundary value analysis is grounded in empirical observation — studies consistently show that boundary values account for a disproportionate share of defects. Testing three values around each boundary is a small investment that catches a large class of bugs.

## Property-based testing

Example-based tests verify specific input-output pairs: `f(3) == 9`, `f(-1) == 1`. Property-based tests verify invariants that hold across *all* inputs: "the square of any number is non-negative." A property-based testing framework generates hundreds or thousands of random inputs and checks that the property holds for each one.

The key properties to look for:
- **Roundtrip** — encode then decode returns the original: `decode(encode(x)) == x`
- **Idempotency** — applying twice gives the same result: `sort(sort(x)) == sort(x)`
- **Commutativity** — order does not matter: `merge(a, b) == merge(b, a)`
- **Conservation** — something is preserved: `len(sort(x)) == len(x)`
- **Monotonicity** — ordering is preserved: `if a <= b then f(a) <= f(b)`

**What it catches:** Edge cases that humans do not think of — unusual Unicode characters, very large numbers, empty collections with specific orderings, combinations of boundary values. Property tests are particularly good at finding invariant violations that only manifest with specific input shapes.

**Generator design matters:** A property test is only as good as its generator. A generator constrained to `integers(1, 3)` will never find the bug triggered by `integer(0)` or `integer(MAX_INT)`. The test-architect's rigor reviewer specifically checks for weak generators.

## Mutation testing

Mutation testing answers the question: "would my tests actually catch a bug?" It works by making small changes to the source code (mutants) — replacing `+` with `-`, `<` with `<=`, deleting a statement — and checking whether at least one test fails. If all tests still pass after a mutation, those tests are too weak to catch that class of bug.

Common mutation operators:
- **Arithmetic**: `a + b` → `a - b`
- **Relational**: `a < b` → `a <= b`
- **Logical**: `a && b` → `a || b`
- **Statement**: delete a line, return early
- **Constant**: `0` → `1`, `true` → `false`

**What it measures:** Test suite effectiveness. A test suite with 100% line coverage but 40% mutation kill rate provides false confidence — most of those tests would not catch real bugs. The test-architect writes mutation-aware assertions: exact values instead of ranges, asymmetric test inputs to catch swapped operands, tests for both sides of every conditional.

**How the test-architect uses it:** The rigor reviewer evaluates each test against common mutation operators. A test that uses `assert result >= 0` scores lower than `assert result == 42` because the former survives arithmetic mutations (changing `+` to `-` might still produce a non-negative result). The test-writer generates assertions designed to kill common mutants.

## How the techniques work together

The four techniques are complementary, not redundant:

| Technique | Derives test cases from | Catches |
|-----------|------------------------|---------|
| Equivalence class partitioning | Input domain structure | Missing branches, unhandled categories |
| Boundary value analysis | Partition boundaries | Off-by-one, wrong operators, edge cases |
| Property-based testing | Algebraic invariants | Unexpected input shapes, invariant violations |
| Mutation testing | Source code structure | Weak assertions, tests that cannot catch bugs |

The test-architect pipeline applies them in order:
1. The **test-planner** identifies equivalence classes, boundaries, and properties from source code
2. The **test-writer** generates test code with mutation-aware assertions
3. The **test-rigor-reviewer** checks whether the tests would survive common mutations
4. The **coverage-analyst** identifies code paths that no technique has reached

This layered approach produces test suites that are systematically derived, scientifically grounded, and resistant to common code mutations.

## When to use which technique

Not every function needs all four techniques:

- **Pure functions with clear input domains** → equivalence classes + boundaries + properties
- **State machines and stateful objects** → state transition coverage (a special case of equivalence partitioning applied to states)
- **Serialization/deserialization** → roundtrip property testing
- **Mathematical functions** → property testing with conservation laws
- **Validation logic** → equivalence classes (valid/invalid) + boundaries (limits)
- **Existing test suites** → mutation analysis via `/test-eval` to find weak spots

The `/test-plan` command shows which techniques apply to your code before any tests are generated, allowing you to review and adjust the approach.

## Further reading

- [Agent Reference](../reference/agents.md) — test-planner, test-writer, test-rigor-reviewer, coverage-analyst specifications
- [Quality Score Reference](../reference/quality-scores.md) — rigor scoring rubric and verdict criteria
- [Tutorial: Your First Test Architecture](../tutorials/tutorial-test-architect.md) — see the techniques in action
- [How to Generate and Evaluate Tests](../guides/use-test-gen.md) — practical workflows

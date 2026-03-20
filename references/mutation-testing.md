# Mutation Testing Patterns

Mutation testing evaluates test suite quality by introducing small code changes (mutants)
and checking whether tests detect them. Surviving mutants reveal weak assertions.

## Mutation Operators to Defend Against

### Arithmetic Mutations

```
Original        Mutant
a + b     →     a - b
a * b     →     a / b
a % b     →     a * b
a++       →     a--
-a        →     a
```

**Defense:** Assert exact computed values, not just sign or truthiness.

```rust
// WEAK: survives a + b → a - b when a == 0
assert!(result > 0);

// STRONG: exact value kills the mutant
assert_eq!(add(3, 5), 8);
```

### Relational Mutations

```
Original        Mutant
a < b     →     a <= b
a > b     →     a >= b
a == b    →     a != b
a <= b    →     a < b
```

**Defense:** Test both sides of every boundary.

```python
# Tests that kill < → <= mutation
assert is_minor(17) is True    # boundary: included
assert is_minor(18) is False   # boundary: excluded
```

### Logical Mutations

```
Original        Mutant
a && b    →     a || b
!a        →     a
a && b    →     a
a || b    →     b
```

**Defense:** Test all truth table combinations.

```typescript
// For: canAccess = isAdmin && isActive
expect(canAccess(true, true)).toBe(true);
expect(canAccess(true, false)).toBe(false);   // kills && → ||
expect(canAccess(false, true)).toBe(false);   // kills && → a
expect(canAccess(false, false)).toBe(false);
```

### Boundary / Off-by-One Mutations

```
Original        Mutant
i < n     →     i <= n
i >= 0    →     i > 0
arr[i]    →     arr[i+1]
```

**Defense:** Test at the exact boundary value.

```go
// For: func first_n(s []int, n int) []int
// Kills i < n → i <= n
result := firstN([]int{1, 2, 3}, 2)
assert.Equal(t, []int{1, 2}, result)  // exactly 2, not 3
```

### Return Value Mutations

```
Original            Mutant
return true    →    return false
return x       →    return 0
return Ok(x)   →    return Err(...)
return list    →    return []
```

**Defense:** Always assert return values explicitly.

```rust
// WEAK: only checks no panic
let _ = process(input);

// STRONG: checks actual return
assert_eq!(process(input), Ok(expected_output));
```

### Null/None Check Removal

```
Original                    Mutant
if x != null { use(x) }  → use(x)     // removes guard
return x ?? default       → return x   // removes fallback
```

**Defense:** Test the null path explicitly.

```python
# Kills removal of None guard
assert process(None) == DEFAULT_VALUE
assert process(None) != None  # if DEFAULT_VALUE != None
```

---

## Per-Language Tools

### Rust: cargo-mutants

**Setup:**

```toml
# Cargo.toml — no special config needed
[dev-dependencies]
# your test dependencies
```

```bash
# Install
cargo install cargo-mutants

# Run on entire project
cargo mutants

# Run on specific module
cargo mutants -- --package my_crate -f src/parser.rs

# Skip slow tests
cargo mutants --timeout 30
```

**Interpreting results:**

```
Found 142 mutants
  Killed:    128 (90.1%)
  Survived:   10 (7.0%)    ← These need attention
  Timeout:     4 (2.8%)    ← Usually OK (infinite loops detected)
```

**Fixing survivors:**

```bash
# Show surviving mutants with context
cargo mutants --list --diff

# Example survivor:
#   src/validator.rs:42: replace < with <=
# Fix: add a boundary test
```

```rust
// Survivor: validate_age replaces age < 18 with age <= 18
// Fix: test exactly at boundary
#[test]
fn age_boundary_17_is_minor() {
    assert!(is_minor(17));
}

#[test]
fn age_boundary_18_is_adult() {
    assert!(!is_minor(18));
}
```

### Python: mutmut

**Setup:**

```ini
# setup.cfg
[mutmut]
paths_to_mutate=src/
tests_dir=tests/
runner=python -m pytest -x --tb=short
```

```bash
# Install
pip install mutmut

# Run
mutmut run

# View results
mutmut results

# Show specific survivor
mutmut show 42

# Apply a mutant to inspect it
mutmut apply 42
# Run tests manually, then:
mutmut revert
```

**Targeting survivors:**

```bash
# List all survivors
mutmut results | grep "Survived"

# Show the mutation
mutmut show 15
# --- src/pricing.py
# +++ src/pricing.py (mutant 15)
# @@ -10 @@
# -    if quantity > 10:
# +    if quantity >= 10:
```

```python
# Fix: add boundary test
def test_bulk_discount_boundary():
    assert calculate_price(quantity=10) == REGULAR_PRICE    # no discount at 10
    assert calculate_price(quantity=11) == DISCOUNTED_PRICE  # discount at 11
```

### TypeScript: Stryker

**Setup with Vitest:**

```bash
npm install --save-dev @stryker-mutator/core @stryker-mutator/vitest-runner
npx stryker init
```

```json
// stryker.config.json
{
  "testRunner": "vitest",
  "vitest": {
    "configFile": "vitest.config.ts"
  },
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts", "!src/**/*.spec.ts"],
  "reporters": ["html", "clear-text", "progress"],
  "thresholds": { "high": 90, "low": 70, "break": 60 },
  "timeoutMS": 10000
}
```

```bash
# Run
npx stryker run

# Run on specific files
npx stryker run --mutate "src/utils/*.ts"
```

**Report interpretation:**

```
Mutation score: 85.3%
  Killed:     140
  Survived:    20   ← Fix these
  No coverage:  5   ← Tests don't even reach this code
  Timeout:      3
```

### Go: go-mutesting

**Setup:**

```bash
go install github.com/zimmski/go-mutesting/cmd/go-mutesting@latest

# Run on package
go-mutesting ./pkg/...

# Run on specific file
go-mutesting ./pkg/validator.go
```

**Example output:**

```
PASS: ./pkg/validator.go:23 replaced > with >=
FAIL: ./pkg/validator.go:31 replaced == with !=    ← survivor

Mutation score: 87.5% (21/24)
```

```go
// Survivor: line 31 changed == to != and tests still pass
// Original: if status == Active { ... }
// Fix:
func TestProcessOnlyActive(t *testing.T) {
    active := Item{Status: Active}
    inactive := Item{Status: Inactive}

    result := Process(active)
    assert.NotNil(t, result)          // kills == → !=

    result = Process(inactive)
    assert.Nil(t, result)             // confirms negative case
}
```

---

## Writing Mutation-Resilient Tests

### 1. Assert Exact Values

```python
# WEAK — survives many arithmetic mutations
assert calculate(10, 5) > 0

# STRONG — kills any arithmetic change
assert calculate(10, 5) == 15
```

### 2. Test Both Sides of Boundaries

```typescript
// WEAK — only tests one side
expect(isEligible(18)).toBe(true);

// STRONG — tests the boundary from both sides
expect(isEligible(17)).toBe(false);
expect(isEligible(18)).toBe(true);
```

### 3. Verify Return Values, Not Just Absence of Errors

```go
// WEAK — only checks no error
_, err := Parse(input)
assert.NoError(t, err)

// STRONG — checks actual parsed value
result, err := Parse(input)
assert.NoError(t, err)
assert.Equal(t, expected, result)
```

### 4. Include Negative Test Cases

```rust
// WEAK — only tests happy path
assert!(validate("good@email.com").is_ok());

// STRONG — also tests what should fail
assert!(validate("good@email.com").is_ok());
assert!(validate("no-at-sign").is_err());
assert!(validate("").is_err());
assert!(validate("@no-local").is_err());
```

### 5. Cover All Boolean Combinations

```python
# For: result = a and (b or c)
# Test all combinations that change the output
assert func(True, True, True) is True
assert func(True, True, False) is True
assert func(True, False, True) is True
assert func(True, False, False) is False   # kills or → and
assert func(False, True, True) is False    # kills removal of `a and`
```

### 6. Use Parameterized Tests for Systematic Coverage

```typescript
describe.each([
  [0, 0, 0],
  [1, 2, 3],
  [-1, 1, 0],
  [100, -100, 0],
  [Number.MAX_SAFE_INTEGER, 0, Number.MAX_SAFE_INTEGER],
])("add(%i, %i)", (a, b, expected) => {
  test(`returns ${expected}`, () => {
    expect(add(a, b)).toBe(expected);
  });
});
```

---

## Mutation Score Targets

| Context              | Target Score | Rationale                        |
|----------------------|-------------|----------------------------------|
| Critical business    | >= 95%      | Financial, auth, data integrity  |
| Core application     | >= 85%      | Main feature code                |
| Utility / helpers    | >= 80%      | Lower risk, simpler logic        |
| Generated / glue     | >= 60%      | Low value from higher coverage   |

Surviving mutants in critical code paths should be treated as test gaps
and addressed before merging.

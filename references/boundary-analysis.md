# Boundary Value Analysis & Equivalence Class Partitioning

Bugs cluster at boundaries between equivalence classes. This reference provides
concrete boundary test cases for each data type across languages.

## Integer Boundaries

### Rust

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn integer_boundaries() {
        // Zero crossing
        assert_eq!(classify(0), Category::Zero);
        assert_eq!(classify(1), Category::Positive);
        assert_eq!(classify(-1), Category::Negative);

        // Type limits
        assert_eq!(classify(i32::MAX), Category::Positive);
        assert_eq!(classify(i32::MIN), Category::Negative);

        // Overflow adjacent
        assert_eq!(safe_add(i32::MAX, 0), Some(i32::MAX));
        assert_eq!(safe_add(i32::MAX, 1), None); // overflow
        assert_eq!(safe_add(i32::MIN, -1), None); // underflow
        assert_eq!(safe_add(i32::MIN, 0), Some(i32::MIN));

        // Powers of two (common partition points)
        for exp in 0..30 {
            let boundary = 1i32 << exp;
            assert!(safe_add(boundary, -1).is_some());
            assert!(safe_add(boundary, 0).is_some());
        }
    }
}
```

### Python

```python
import sys

def test_integer_boundaries():
    # Python ints are arbitrary precision; test logical boundaries
    assert classify(0) == "zero"
    assert classify(1) == "positive"
    assert classify(-1) == "negative"

    # Common API limits
    assert validate_port(0) is True
    assert validate_port(-1) is False
    assert validate_port(65535) is True
    assert validate_port(65536) is False

    # Bit-width boundaries (common in serialization)
    assert fits_in_i32(2**31 - 1) is True
    assert fits_in_i32(2**31) is False
    assert fits_in_i32(-(2**31)) is True
    assert fits_in_i32(-(2**31) - 1) is False
```

### TypeScript

```typescript
describe("integer boundaries", () => {
  test("zero crossing", () => {
    expect(classify(0)).toBe("zero");
    expect(classify(1)).toBe("positive");
    expect(classify(-1)).toBe("negative");
  });

  test("safe integer limits", () => {
    expect(safeAdd(Number.MAX_SAFE_INTEGER, 0)).toBe(Number.MAX_SAFE_INTEGER);
    expect(safeAdd(Number.MAX_SAFE_INTEGER, 1)).toBeNull();
    expect(safeAdd(Number.MIN_SAFE_INTEGER, -1)).toBeNull();
  });

  test("bitwise boundary", () => {
    // JS bitwise ops use 32-bit signed integers
    expect(bitwiseOp(0x7fffffff)).toBeDefined();
    expect(bitwiseOp(-0x80000000)).toBeDefined();
  });
});
```

### Go

```go
func TestIntegerBoundaries(t *testing.T) {
    tests := []struct {
        name string
        val  int64
        want Category
    }{
        {"zero", 0, Zero},
        {"one", 1, Positive},
        {"neg_one", -1, Negative},
        {"max_int64", math.MaxInt64, Positive},
        {"min_int64", math.MinInt64, Negative},
        {"max_int32", math.MaxInt32, Positive},
        {"min_int32", math.MinInt32, Negative},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if got := Classify(tt.val); got != tt.want {
                t.Errorf("Classify(%d) = %v, want %v", tt.val, got, tt.want)
            }
        })
    }

    // Overflow detection
    if _, err := SafeAdd(math.MaxInt64, 1); err == nil {
        t.Error("expected overflow error")
    }
}
```

---

## String Boundaries

### Rust

```rust
#[test]
fn string_boundaries() {
    // Empty
    assert_eq!(process(""), ProcessResult::Empty);

    // Single character
    assert_eq!(process("a").len(), 1);

    // Unicode: multi-byte, emoji, combining characters
    assert!(process("Hello 🌍").is_ok());
    assert!(process("café").is_ok());            // combining accent
    assert!(process("👨‍👩‍👧‍👦").is_ok());   // ZWJ sequence
    assert!(process("\u{202E}abc").is_ok());      // RTL override

    // Null bytes
    assert!(process("hello\0world").is_err());

    // Max length boundary
    let at_limit = "x".repeat(MAX_LEN);
    assert!(process(&at_limit).is_ok());
    let over_limit = "x".repeat(MAX_LEN + 1);
    assert!(process(&over_limit).is_err());
}
```

### Python

```python
def test_string_boundaries():
    # Empty and whitespace
    assert process("") == Result.EMPTY
    assert process("   ") == Result.WHITESPACE
    assert process("\t\n") == Result.WHITESPACE

    # Single character
    assert process("a").value == "a"

    # Unicode
    assert process("Hello 🌍").is_ok
    assert process("مرحبا").is_ok            # RTL text
    assert process("\u0000").is_err           # null byte
    assert process("a\u0300").is_ok           # combining char (à)
    assert process("👨‍👩‍👧‍👦").is_ok    # ZWJ family emoji

    # Length boundaries
    assert process("x" * MAX_LEN).is_ok
    assert process("x" * (MAX_LEN + 1)).is_err

    # Injection patterns (security boundary)
    assert process("'; DROP TABLE--").is_ok   # should be sanitized
    assert process("<script>alert(1)</script>").is_ok
```

### TypeScript

```typescript
describe("string boundaries", () => {
  test.each([
    ["empty string", "", Result.Empty],
    ["single char", "a", Result.Ok],
    ["emoji", "🎉", Result.Ok],
    ["null byte", "\0", Result.Invalid],
    ["ZWJ emoji", "👨‍👩‍👧", Result.Ok],
    ["RTL override", "\u202Eabc", Result.Ok],
  ])("%s", (_name, input, expected) => {
    expect(process(input).status).toBe(expected);
  });

  test("length boundary", () => {
    expect(process("x".repeat(MAX_LEN)).status).toBe(Result.Ok);
    expect(process("x".repeat(MAX_LEN + 1)).status).toBe(Result.TooLong);
  });
});
```

### Go

```go
func TestStringBoundaries(t *testing.T) {
    tests := []struct {
        name  string
        input string
        want  error
    }{
        {"empty", "", ErrEmpty},
        {"single_char", "a", nil},
        {"emoji", "🌍", nil},
        {"null_byte", "hello\x00world", ErrInvalidChar},
        {"zwj_emoji", "👨‍👩‍👧‍👦", nil},
        {"max_length", strings.Repeat("x", MaxLen), nil},
        {"over_max", strings.Repeat("x", MaxLen+1), ErrTooLong},
        {"rtl", "\u202Eabc", nil},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := Process(tt.input)
            if !errors.Is(err, tt.want) {
                t.Errorf("Process(%q) = %v, want %v", tt.input, err, tt.want)
            }
        })
    }
}
```

---

## Collection Boundaries

### Rust

```rust
#[test]
fn collection_boundaries() {
    // Empty
    assert_eq!(aggregate(&[]), AggResult::Empty);

    // Single element
    assert_eq!(aggregate(&[42]), AggResult::Value(42));

    // Two elements (minimum for comparison logic)
    assert_eq!(aggregate(&[1, 2]), AggResult::Value(3));

    // At capacity
    let full: Vec<i32> = (0..CAPACITY as i32).collect();
    assert!(aggregate(&full).is_ok());

    // Over capacity
    let over: Vec<i32> = (0..=CAPACITY as i32).collect();
    assert!(aggregate(&over).is_err());

    // Duplicates
    assert_eq!(deduplicate(&[1, 1, 1]), vec![1]);

    // Pre-sorted, reverse-sorted, single-value
    assert!(is_sorted_after_process(&[1, 2, 3]));
    assert!(is_sorted_after_process(&[3, 2, 1]));
    assert!(is_sorted_after_process(&[5, 5, 5]));
}
```

### Pattern (all languages)

```
Test matrix for any collection-accepting function:
┌─────────────────────┬──────────────────────────────┐
│ Partition           │ Representative values        │
├─────────────────────┼──────────────────────────────┤
│ Empty               │ [], {}                       │
│ Single element      │ [x]                          │
│ Two elements        │ [x, y] — minimum for pairs   │
│ At capacity - 1     │ n-1 elements                 │
│ At capacity         │ n elements                   │
│ Over capacity       │ n+1 elements                 │
│ All same            │ [x, x, x]                    │
│ Sorted ascending    │ [1, 2, 3]                    │
│ Sorted descending   │ [3, 2, 1]                    │
│ Contains nulls      │ [x, null, y]                 │
│ Nested empty        │ [[]]                         │
└─────────────────────┴──────────────────────────────┘
```

---

## Floating Point Boundaries

### Rust

```rust
#[test]
fn float_boundaries() {
    // Zeros
    assert_eq!(process(0.0), expected_zero);
    assert_eq!(process(-0.0), expected_zero);
    assert!((0.0f64).eq(&-0.0f64)); // equal by IEEE 754

    // Special values
    assert!(process(f64::NAN).is_nan_result());
    assert!(process(f64::INFINITY).is_err());
    assert!(process(f64::NEG_INFINITY).is_err());

    // Epsilon precision
    assert!((0.1 + 0.2 - 0.3).abs() < f64::EPSILON * 4.0);

    // Subnormal
    assert!(process(f64::MIN_POSITIVE).is_ok());
    assert!(process(5e-324).is_ok()); // smallest subnormal
}
```

### Python

```python
import math

def test_float_boundaries():
    assert process(0.0) == ZERO_RESULT
    assert process(-0.0) == ZERO_RESULT

    assert process(math.nan) is None        # NaN handling
    assert process(math.inf) is None
    assert process(-math.inf) is None

    # Precision
    assert abs(0.1 + 0.2 - 0.3) < 1e-15
    assert process(float.fromhex("0x1p-1074")) is not None  # smallest subnormal

    # Decimal for currency
    from decimal import Decimal
    assert money_add(Decimal("0.10"), Decimal("0.20")) == Decimal("0.30")
```

---

## Null / Optional Boundaries

### Rust

```rust
#[test]
fn optional_boundaries() {
    // None
    assert_eq!(process(None), Default::default());

    // Some with empty inner value
    assert_eq!(process(Some("")), ProcessResult::Empty);
    assert_eq!(process(Some(vec![])), ProcessResult::EmptyList);

    // Nested optionals
    let nested: Option<Option<i32>> = Some(None);
    assert_eq!(process_nested(nested), Default::default());
    assert_eq!(process_nested(Some(Some(42))), ProcessResult::Value(42));
    assert_eq!(process_nested(None), ProcessResult::Missing);
}
```

### Python

```python
def test_none_boundaries():
    assert process(None) is DEFAULT
    assert process("") is EMPTY       # None vs empty distinction
    assert process([]) is EMPTY_LIST

    # Optional fields in dataclass
    user = User(name="test", email=None)
    assert serialize(user)["email"] is None  # not omitted
    assert "email" in serialize(user)
```

### TypeScript

```typescript
describe("null/undefined boundaries", () => {
  test("null vs undefined", () => {
    expect(process(null)).toBe(DEFAULT);
    expect(process(undefined)).toBe(DEFAULT);
    // Distinguish if the API requires it
    expect(processStrict(null)).not.toBe(processStrict(undefined));
  });

  test("empty wrappers", () => {
    expect(process("")).toBe(Result.Empty);
    expect(process([])).toBe(Result.EmptyList);
    expect(process({})).toBe(Result.EmptyObject);
  });

  test("falsy values that are valid", () => {
    expect(process(0)).not.toBe(DEFAULT);    // 0 is valid
    expect(process(false)).not.toBe(DEFAULT); // false is valid
    expect(process("")).toBe(Result.Empty);   // "" may or may not be valid
  });
});
```

### Go

```go
func TestNilBoundaries(t *testing.T) {
    // Nil pointer
    var p *User
    if _, err := Process(p); !errors.Is(err, ErrNilInput) {
        t.Errorf("nil pointer: got %v, want ErrNilInput", err)
    }

    // Nil slice vs empty slice
    var nilSlice []int
    emptySlice := []int{}
    // Both should behave identically in most APIs
    r1, _ := Aggregate(nilSlice)
    r2, _ := Aggregate(emptySlice)
    if r1 != r2 {
        t.Errorf("nil vs empty slice: %v != %v", r1, r2)
    }

    // Nil map vs empty map
    var nilMap map[string]int
    emptyMap := map[string]int{}
    if Lookup(nilMap, "key") != Lookup(emptyMap, "key") {
        t.Error("nil vs empty map behave differently")
    }

    // Nil interface vs typed nil
    var iface error
    var typedNil *MyError
    // iface == nil is true, but error(typedNil) != nil
    if iface == typedNil {
        t.Error("nil interface should not equal typed nil")
    }
}
```

---

## Equivalence Class Partitioning Template

For any function under test, enumerate classes:

```
Input: validate_age(age: int) -> bool

┌─────────────────┬────────────────┬──────────┐
│ Class           │ Range          │ Expected │
├─────────────────┼────────────────┼──────────┤
│ Negative        │ age < 0        │ false    │
│ Zero            │ age == 0       │ true     │
│ Valid child     │ 1 <= age <= 12 │ true     │
│ Valid teen      │ 13 <= age <= 17│ true     │
│ Valid adult     │ 18 <= age <= 120│ true    │
│ Unrealistic     │ age > 120      │ false    │
├─────────────────┼────────────────┼──────────┤
│ BOUNDARIES      │                │          │
├─────────────────┼────────────────┼──────────┤
│ Just below min  │ -1             │ false    │
│ Min             │ 0              │ true     │
│ Partition edge  │ 12, 13         │ true     │
│ Partition edge  │ 17, 18         │ true     │
│ Max             │ 120            │ true     │
│ Just above max  │ 121            │ false    │
└─────────────────┴────────────────┴──────────┘

Test: one value from each class + all boundary values.
```

# Property-Based Testing Patterns

Property-based testing generates random inputs to verify invariants hold across all cases,
finding edge cases that example-based tests miss.

## Rust (proptest)

### Basic Usage

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn sort_preserves_length(ref v in prop::collection::vec(any::<i32>(), 0..100)) {
        let mut sorted = v.clone();
        sorted.sort();
        prop_assert_eq!(sorted.len(), v.len());
    }

    #[test]
    fn sort_is_idempotent(ref v in prop::collection::vec(any::<i32>(), 0..100)) {
        let mut sorted = v.clone();
        sorted.sort();
        let mut sorted_again = sorted.clone();
        sorted_again.sort();
        prop_assert_eq!(sorted, sorted_again);
    }

    #[test]
    fn sort_output_is_ordered(ref v in prop::collection::vec(any::<i32>(), 0..100)) {
        let mut sorted = v.clone();
        sorted.sort();
        for window in sorted.windows(2) {
            prop_assert!(window[0] <= window[1]);
        }
    }
}
```

### Custom Strategies with prop_compose!

```rust
use proptest::prelude::*;

#[derive(Debug, Clone)]
struct User {
    name: String,
    age: u8,
    email: String,
}

prop_compose! {
    fn valid_email()(
        local in "[a-z]{3,10}",
        domain in "[a-z]{3,8}",
        tld in prop::sample::select(vec!["com", "org", "net"])
    ) -> String {
        format!("{local}@{domain}.{tld}")
    }
}

prop_compose! {
    fn arb_user()(
        name in "[A-Z][a-z]{2,15}",
        age in 0u8..130,
        email in valid_email()
    ) -> User {
        User { name, age, email }
    }
}

proptest! {
    #[test]
    fn user_serialization_roundtrip(user in arb_user()) {
        let json = serde_json::to_string(&user).unwrap();
        let decoded: User = serde_json::from_str(&json).unwrap();
        prop_assert_eq!(user.name, decoded.name);
        prop_assert_eq!(user.age, decoded.age);
    }
}
```

### Tuning with ProptestConfig

```rust
proptest! {
    #![proptest_config(ProptestConfig {
        cases: 1000,
        max_shrink_iters: 5000,
        .. ProptestConfig::default()
    })]

    #[test]
    fn exhaustive_check(x in 0i64..1000, y in 0i64..1000) {
        let sum = x.checked_add(y);
        prop_assert!(sum.is_some());
        prop_assert!(sum.unwrap() >= x);
    }
}
```

---

## Python (hypothesis)

### Basic Usage

```python
from hypothesis import given, settings, assume
import hypothesis.strategies as st

@given(st.lists(st.integers()))
def test_sort_preserves_length(xs):
    assert len(sorted(xs)) == len(xs)

@given(st.lists(st.integers()))
def test_sort_is_ordered(xs):
    result = sorted(xs)
    for a, b in zip(result, result[1:]):
        assert a <= b

@given(st.lists(st.integers()))
def test_sort_preserves_elements(xs):
    from collections import Counter
    assert Counter(sorted(xs)) == Counter(xs)
```

### Settings and Composite Strategies

```python
from hypothesis import given, settings
import hypothesis.strategies as st
from dataclasses import dataclass

@dataclass
class Transaction:
    amount: float
    currency: str
    description: str

@st.composite
def transactions(draw):
    amount = draw(st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False))
    currency = draw(st.sampled_from(["USD", "EUR", "GBP", "JPY"]))
    description = draw(st.text(min_size=1, max_size=200))
    return Transaction(amount=round(amount, 2), currency=currency, description=description)

@given(st.lists(transactions(), min_size=1, max_size=50))
@settings(max_examples=500, deadline=None)
def test_batch_total_matches_sum(txns):
    batch = TransactionBatch(txns)
    expected = sum(t.amount for t in txns if t.currency == "USD")
    assert abs(batch.usd_total() - expected) < 0.01
```

### Data Transformation Testing

```python
@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.one_of(st.integers(), st.text(), st.booleans(), st.none()),
    min_size=0,
    max_size=20,
))
def test_flatten_unflatten_roundtrip(data):
    flat = flatten_dict(data)
    restored = unflatten_dict(flat)
    assert restored == data
```

---

## TypeScript (fast-check)

### Basic Usage

```typescript
import * as fc from "fast-check";

test("sort preserves length", () => {
  fc.assert(
    fc.property(fc.array(fc.integer()), (arr) => {
      const sorted = [...arr].sort((a, b) => a - b);
      expect(sorted.length).toBe(arr.length);
    })
  );
});

test("sort produces ordered output", () => {
  fc.assert(
    fc.property(fc.array(fc.integer()), (arr) => {
      const sorted = [...arr].sort((a, b) => a - b);
      for (let i = 1; i < sorted.length; i++) {
        expect(sorted[i]).toBeGreaterThanOrEqual(sorted[i - 1]);
      }
    })
  );
});
```

### Complex Types and Model-Based Testing

```typescript
const userArb = fc.record({
  id: fc.uuid(),
  name: fc.string({ minLength: 1, maxLength: 100 }),
  age: fc.integer({ min: 0, max: 150 }),
  tags: fc.array(fc.string(), { maxLength: 10 }),
});

test("user serialization roundtrip", () => {
  fc.assert(
    fc.property(userArb, (user) => {
      const json = JSON.stringify(user);
      const parsed = JSON.parse(json);
      expect(parsed).toEqual(user);
    })
  );
});
```

### State Machine Testing with Commands

```typescript
type Model = { count: number };
type Real = Counter;

class IncrementCommand implements fc.Command<Model, Real> {
  check = () => true;
  run(model: Model, real: Real) {
    model.count++;
    real.increment();
    expect(real.value()).toBe(model.count);
  }
  toString = () => "increment";
}

class DecrementCommand implements fc.Command<Model, Real> {
  check = (m: Model) => m.count > 0;
  run(model: Model, real: Real) {
    model.count--;
    real.decrement();
    expect(real.value()).toBe(model.count);
  }
  toString = () => "decrement";
}

test("counter state machine", () => {
  fc.assert(
    fc.property(
      fc.commands([
        fc.constant(new IncrementCommand()),
        fc.constant(new DecrementCommand()),
      ]),
      (cmds) => {
        const setup = () => ({ model: { count: 0 }, real: new Counter() });
        fc.modelRun(setup, cmds);
      }
    )
  );
});
```

---

## Go (rapid)

### Basic Usage

```go
package main

import (
    "sort"
    "testing"
    "pgregory.net/rapid"
)

func TestSortPreservesLength(t *testing.T) {
    rapid.Check(t, func(t *rapid.T) {
        s := rapid.SliceOf(rapid.Int()).Draw(t, "slice")
        original := len(s)
        sort.Ints(s)
        if len(s) != original {
            t.Fatalf("length changed: %d -> %d", original, len(s))
        }
    })
}

func TestSortIsOrdered(t *testing.T) {
    rapid.Check(t, func(t *rapid.T) {
        s := rapid.SliceOf(rapid.Int()).Draw(t, "slice")
        sort.Ints(s)
        for i := 1; i < len(s); i++ {
            if s[i] < s[i-1] {
                t.Fatalf("not sorted at index %d: %d < %d", i, s[i], s[i-1])
            }
        }
    })
}
```

### Custom Generators and Stateful Testing

```go
func genUser() *rapid.Generator[User] {
    return rapid.Custom(func(t *rapid.T) User {
        return User{
            Name:  rapid.StringMatching(`[A-Z][a-z]{2,15}`).Draw(t, "name"),
            Age:   rapid.IntRange(0, 130).Draw(t, "age"),
            Email: rapid.StringMatching(`[a-z]+@[a-z]+\.(com|org)`).Draw(t, "email"),
        }
    })
}

// Stateful testing for a concurrent map
type mapMachine struct {
    m    *ConcurrentMap[string, int]
    ref  map[string]int
}

func (sm *mapMachine) Init(t *rapid.T) {
    sm.m = NewConcurrentMap[string, int]()
    sm.ref = make(map[string]int)
}

func (sm *mapMachine) Put(t *rapid.T) {
    key := rapid.StringMatching(`[a-z]{1,5}`).Draw(t, "key")
    val := rapid.Int().Draw(t, "val")
    sm.m.Put(key, val)
    sm.ref[key] = val
}

func (sm *mapMachine) Get(t *rapid.T) {
    key := rapid.StringMatching(`[a-z]{1,5}`).Draw(t, "key")
    got, ok1 := sm.m.Get(key)
    expected, ok2 := sm.ref[key]
    if ok1 != ok2 || got != expected {
        t.Fatalf("Get(%q): got (%v,%v), want (%v,%v)", key, got, ok1, expected, ok2)
    }
}

func (sm *mapMachine) Check(t *rapid.T) {
    if sm.m.Len() != len(sm.ref) {
        t.Fatalf("length mismatch: %d vs %d", sm.m.Len(), len(sm.ref))
    }
}

func TestConcurrentMap(t *testing.T) {
    rapid.Check(t, rapid.Run[*mapMachine]())
}
```

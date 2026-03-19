# Refactor Skill Evaluation: Dual Invalid Input Test

**Date**: 2026-03-19
**Command**: `/refactor --focus=security,testing --iterations=0 src/`
**Skill**: `/Users/AllenR1_1/Projects/zircote/refactor/skills/refactor/SKILL.md`

## Input Analysis

Two invalid inputs were provided:

| # | Flag | Value | Valid Range | Status |
|---|------|-------|-------------|--------|
| 1 | `--focus` | `security,testing` | `{security, architecture, simplification, code, discovery}` | INVALID (`testing` not in allowed set) |
| 2 | `--iterations` | `0` | 1-10 (positive integer) | INVALID (below minimum) |

## Argument Parsing (per SKILL.md "Arguments" section)

### Step 1: Extract `--iterations=0`
- Extracted `cli_iterations = 0`
- Removed from `$ARGUMENTS`

### Step 2: Extract `--focus=security,testing`
- Split on comma: `["security", "testing"]`
- Removed from `$ARGUMENTS`
- Remaining arguments: `src/`

### Step 3: Validate focus areas against allowed set
Per SKILL.md lines 33-36:

> 1. Split the value on commas to get a list of focus areas
> 2. Validate each value against the allowed set: `{security, architecture, simplification, code, discovery}`
> 3. If any value is invalid, report the error to the user and stop: "Invalid focus area '{value}'. Valid values: security, architecture, simplification, code, discovery"

- `security` -- validated: PASS
- `testing` -- validated: FAIL

### Skill Behavior: STOP with error

The skill halts execution and reports:

> **Invalid focus area 'testing'. Valid values: security, architecture, simplification, code, discovery**

## Error Handling Sequence

The skill defines a clear validation order in the Arguments section:

1. **Focus area validation happens first** (SKILL.md lines 33-36, steps 1-3)
2. **Focus validation failure triggers an immediate stop** ("report the error to the user and stop")
3. **Iterations validation is never reached** because the skill stops at the focus area error

The `--iterations=0` error (0 is outside the documented 1-10 range per line 31: "N must be a positive integer (1-10)") is a real error, but it is **never evaluated** because the focus area validation gate fires first and halts all processing.

## What the Skill Does NOT Do

- Does NOT proceed to Phase 0.0 (Configuration Check)
- Does NOT create a team or spawn agents
- Does NOT attempt to read `src/` or any codebase files
- Does NOT check the iterations value
- Does NOT produce a partial result or continue with only the valid focus area (`security`)

## Key Design Observation

The skill uses a **fail-fast** approach: the first validation error encountered causes an immediate stop. It does not accumulate all errors and report them together. This means:

- If a user fixes `testing` to a valid value but leaves `--iterations=0`, they will hit the iterations error on the next attempt
- The user gets one error at a time, not a batch of all errors

## Conclusion

The skill correctly handles the invalid `--focus` value by detecting it during argument parsing and stopping before any work begins. The error message is prescribed exactly in the skill specification. The second error (`--iterations=0`) is real but unreachable in this execution path.

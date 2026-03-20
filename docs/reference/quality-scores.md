---
diataxis_type: reference
diataxis_describes: refactor plugin quality scoring rubrics
---

# Quality Score Reference

The refactoring process produces up to four scores depending on active agents. In a full (unfocused) run, three scores are always produced: Clean Code, Architecture, and Security Posture. In focused runs, only scores relevant to the active agents are produced.

## Clean Code Score (1--10)

Evaluates: naming, function size, DRY principle, comments, error handling, formatting.

| Score | Level | Description |
|-------|-------|-------------|
| 9--10 | Exemplary | Clear, simple, maintainable code throughout |
| 7--8 | Good | Good quality with minor improvement opportunities |
| 5--6 | Acceptable | Needs notable improvements in multiple areas |
| 3--4 | Poor | Significant quality issues requiring attention |
| 1--2 | Very poor | Requires major refactoring effort |

### Criteria

- **Meaningful Names** — Variables, functions, and classes have clear, intention-revealing names
- **Function Size** — Functions are small, each doing one thing well
- **Single Responsibility** — Each class/module has one reason to change
- **DRY** — No significant code duplication
- **Comments** — Code is self-documenting; comments explain "why", not "what"
- **Error Handling** — Proper exception handling, no error code returns
- **Formatting** — Consistent style, proper indentation
- **Boundaries** — Clear interfaces between modules

## Architecture Perfection Score (1--10)

Evaluates: SOLID principles, coupling/cohesion, abstraction levels, testability, extensibility.

| Score | Level | Description |
|-------|-------|-------------|
| 9--10 | Excellent | Best practices throughout, clean architecture |
| 7--8 | Good | Good design with minor architectural concerns |
| 5--6 | Acceptable | Some architectural issues to address |
| 3--4 | Poor | Significant design issues needing redesign |
| 1--2 | Very poor | Major architectural problems throughout |

### Criteria

- **SOLID Principles** — Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Coupling and Cohesion** — Low coupling between modules, high cohesion within modules
- **Abstraction Levels** — Appropriate abstraction; not over-engineered or under-designed
- **Dependency Direction** — Dependencies flow toward stable abstractions
- **Testability** — Code structure facilitates easy testing
- **Extensibility** — Easy to add new features without modifying existing code
- **Pattern Usage** — Appropriate use of design patterns (not over-patterned)

## Security Posture Score (1--10)

Evaluates: input validation, authentication, authorization, secrets handling, error information exposure, dependency vulnerabilities, injection resistance.

| Score | Level | Description |
|-------|-------|-------------|
| 9--10 | Excellent | Strong security controls, no findings |
| 7--8 | Good | Minor advisory findings only |
| 5--6 | Acceptable | Some medium-severity findings to address |
| 3--4 | Poor | High-severity findings present |
| 1--2 | Very poor | Critical vulnerabilities detected |

### Criteria

- **Input Validation** — All user inputs validated and sanitized
- **Authentication** — Auth checks present and correctly implemented
- **Authorization** — Access controls enforce least privilege
- **Secrets Handling** — No hardcoded secrets, credentials, or PII exposure
- **Error Handling** — Errors do not leak internal details to users
- **Dependencies** — No known vulnerable dependencies
- **Injection Resistance** — Protection against SQL injection, XSS, command injection, and other OWASP top 10

### Produced by

- Full (unfocused) runs: always
- `--focus=security`: yes
- Other focus modes: no

## Simplification Score (1--10)

Evaluates: naming clarity, control flow simplicity, redundancy, style consistency. Produced only in `--focus=simplification` runs.

| Score | Level | Description |
|-------|-------|-------------|
| 9--10 | Exemplary | Clear, simple, consistent code throughout |
| 7--8 | Good | Minor clarity improvements possible |
| 5--6 | Acceptable | Notable simplification opportunities remain |
| 3--4 | Poor | Significant clarity and consistency issues |
| 1--2 | Very poor | Requires major simplification effort |

### Criteria

- **Naming Clarity** — Variables, functions, and types have clear, intention-revealing names
- **Control Flow** — Simple, linear control flow; minimal nesting
- **Redundancy** — No unnecessary duplication or dead code
- **Style Consistency** — Consistent patterns and conventions across files

### Produced by

- `--focus=simplification`: yes
- All other modes: no (simplifier runs but does not produce a standalone score)

## Test Rigor Score (0.0--1.0)

Evaluates: assertion strength, boundary coverage, mutation resistance, anti-pattern absence, property test quality. Produced by the test-rigor-reviewer agent during `/test-gen` and `/test-eval`.

| Score | Rating | Criteria |
|-------|--------|----------|
| 0.9--1.0 | Excellent | Grounded in formal technique, mutation-resistant, tests one clear behavior |
| 0.8--0.89 | Good | Solid test with minor improvements possible |
| 0.6--0.79 | Adequate | Tests real behavior but has gaps (missing boundary, weak assertion) |
| 0.4--0.59 | Weak | Susceptible to mutations or missing key scenarios |
| 0.2--0.39 | Poor | Minimal value — identity check, overly broad assertion |
| 0.0--0.19 | Useless | Tautological, cannot fail, or tests nothing meaningful |

### Anti-Pattern Taxonomy

| Anti-Pattern | Score Range | Example |
|-------------|------------|---------|
| Tautological assertion | 0.0--0.2 | `assert x == x`, `assert len(result) >= 0` |
| Identity check | 0.1--0.3 | Calling function without asserting on result |
| Weak property generator | 0.2--0.4 | Generator restricted to tiny range, excludes boundaries |
| Missing boundary cases | 0.3--0.5 | No tests for empty input, zero, MAX_INT |
| Missing error paths | 0.3--0.5 | Only success paths tested, no `pytest.raises` |
| Mutation-susceptible | 0.4--0.6 | Uses `>=` when `==` would be more precise |

### Verdict Criteria

| Verdict | Condition |
|---------|-----------|
| **PASS** | Overall rigor >= 0.70 AND zero tautological tests |
| **NEEDS IMPROVEMENT** | Overall rigor 0.50--0.69 OR 1--2 weak tests |
| **FAIL** | Overall rigor < 0.50 OR any tautological assertions |

### Produced by

- `/test-gen`: always (Phase 3)
- `/test-eval`: always
- `/refactor`, `/feature-dev`: not produced (use `/test-eval` separately)

## Coverage Verdict

Evaluates: line coverage, branch coverage, critical gap presence. Produced by the coverage-analyst agent during `/test-gen`, `/test-gen --coverage`, and `/test-eval`.

| Verdict | Condition |
|---------|-----------|
| **MEETS TARGET** | Line >= 90% AND Branch >= 85% AND zero critical gaps |
| **BELOW TARGET** | Line or Branch below target but no critical gaps |
| **CRITICAL GAPS** | Any critical-severity uncovered regions regardless of percentage |

### Gap Severity Classification

| Severity | Examples |
|----------|---------|
| **Critical** | Error handling, input validation, security checks |
| **Important** | Core business logic, state transitions |
| **Nice-to-have** | Logging, debug paths, rarely-hit branches |

### Produced by

- `/test-gen`: always (Phase 3 or Phase 4 in coverage-only mode)
- `/test-gen --coverage`: always
- `/test-eval`: always
- `/refactor`, `/feature-dev`: not produced

## Report Output

Scores appear in the generated `refactor-result-{timestamp}.md` report, which includes:
- Score values with justifications
- Per-criteria assessments
- Strengths identified
- Remaining concerns
- Recommendations for future improvements

In focused runs, the report includes only scores from active agents. See [Configuration Reference](../reference/configuration.md) for focus mode details.

## See Also

- [Agent Reference](agents.md) — Architect agent specification
- [Tutorial: Your First Refactor](../tutorials/tutorial.md) — See scores in action
- [How to Evaluate Test Quality](../guides/evaluate-test-quality.md) — interpreting and acting on rigor scores

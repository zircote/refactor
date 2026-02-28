---
diataxis_type: reference
diataxis_describes: refactor plugin quality scoring rubrics
---

# Quality Score Reference

The architect agent assigns two scores at the end of every refactoring run. Both use a 1--10 scale.

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

## Report Output

Scores appear in the generated `refactor-result-{timestamp}.md` report, which includes:
- Score values with justifications
- Per-criteria assessments
- Strengths identified
- Remaining concerns
- Recommendations for future improvements

## See Also

- [Agent Reference](agents.md) — Architect agent specification
- [Tutorial: Your First Refactor](../tutorial.md) — See scores in action

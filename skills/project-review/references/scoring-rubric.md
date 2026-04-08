# Scoring Rubric

Per-domain scoring rubric for the project-review skill. Each domain is scored 1-10.

## Score Interpretation

| Score | Rating | Description |
|-------|--------|-------------|
| 9-10 | Excellent | Exemplary practices, minimal issues |
| 7-8 | Good | Solid practices, minor gaps |
| 5-6 | Adequate | Functional but notable concerns |
| 3-4 | Needs Improvement | Significant issues requiring attention |
| 1-2 | Critical | Severe gaps, immediate action needed |

---

## Simplicity (1-10)

| Score | Criteria |
|-------|----------|
| 9-10 | Functions are small and focused. Names are clear and intention-revealing. Abstractions are appropriate — not over-engineered, not under-designed. Minimal duplication. Code reads naturally. |
| 7-8 | Occasional long functions or unclear names. Minor duplication. Most code is clean and readable. |
| 5-6 | Some complex functions with high nesting. Moderate duplication. Mixed naming quality. Some dead code. |
| 3-4 | Many long/complex functions. Significant duplication across modules. Unclear naming patterns. Notable dead code. |
| 1-2 | Pervasive complexity. Massive duplication. Impenetrable naming. Deeply nested logic throughout. |

## Security (1-10)

| Score | Criteria |
|-------|----------|
| 9-10 | All inputs validated at boundaries. Auth solid and consistent. No hardcoded secrets. Dependencies clean. OWASP Top 10 addressed. Error messages do not leak sensitive data. |
| 7-8 | Minor gaps (e.g., one missing validation boundary). No critical issues. Dependencies mostly current. |
| 5-6 | Some missing validation. Minor dependency vulnerabilities. Partial auth coverage. Some informational leaks in errors. |
| 3-4 | Multiple missing validations. Values that look like hardcoded credentials. Unpatched dependency vulns. Weak crypto usage. |
| 1-2 | Injection vectors present. Exposed secrets. No auth on protected resources. Critical dependency vulns. |

## Data (1-10)

| Score | Criteria |
|-------|----------|
| 9-10 | Data validated at all boundaries. Parameterized queries throughout. Proper transactions. PII protected. Caching with invalidation. Serialization schema-validated. |
| 7-8 | Minor gaps in boundary validation or caching strategy. Mostly parameterized queries. Basic PII awareness. |
| 5-6 | Some unvalidated boundaries. Occasional raw queries. Basic caching without invalidation strategy. No explicit PII handling. |
| 3-4 | Missing validation on data paths. Potential injection via data construction. No transaction boundaries where needed. |
| 1-2 | Raw SQL/query construction from user input. No boundary validation. PII exposed in logs/errors. No data integrity controls. |

## Architecture (1-10)

| Score | Criteria |
|-------|----------|
| 9-10 | Clean layers with clear separation of concerns. Low coupling, high cohesion. SOLID principles throughout. Appropriate design patterns. Dependencies flow toward stable abstractions. |
| 7-8 | Minor coupling issues or one SOLID violation. Generally clean module boundaries. Good extensibility. |
| 5-6 | Some tight coupling. Mixed concerns in modules. A few anti-patterns. Moderate tech debt (TODOs/FIXMEs). |
| 3-4 | Significant coupling between modules. Leaky abstractions. Widespread anti-patterns. High tech debt density. |
| 1-2 | No discernible architecture. Monolithic ball of mud. Circular dependencies. No separation of concerns. |

## Documentation (1-10)

| Score | Criteria |
|-------|----------|
| 9-10 | README with setup/usage/architecture overview. API docs complete. ADRs for key decisions. CONTRIBUTING guide. CHANGELOG maintained. Public API has doc comments. Examples/tutorials present. |
| 7-8 | README covers basics and setup. Most public API documented. Some ADRs. Inline comments on complex logic. |
| 5-6 | README exists but incomplete (missing setup or architecture). Partial API docs. Few inline comments. No ADRs. |
| 3-4 | README is a stub. No API docs. Sparse comments. No CONTRIBUTING or CHANGELOG. |
| 1-2 | No README or single-line README. No documentation anywhere in the project. |

## SDLC (1-10)

| Score | Criteria |
|-------|----------|
| 9-10 | Full CI/CD: lint + test + security scan + deploy. Pinned dependencies with lock files. Automated releases with changelog. Branch protection. Pre-commit hooks. Dev environment reproducible (.tool-versions/Dockerfile). |
| 7-8 | CI runs tests and lint. Lock files present. Some release automation. Linter/formatter configured. |
| 5-6 | Basic CI (tests only). Lock files present. Manual releases. Linter configured but not enforced in CI. |
| 3-4 | CI exists but incomplete (e.g., no tests in pipeline). Outdated lock files. No release process. |
| 1-2 | No CI/CD. No build automation. No dependency management. No quality tooling. |

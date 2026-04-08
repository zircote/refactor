# Domain Review Criteria

Detailed checklists for each review domain. Agents work through these criteria systematically and cite file:line evidence for every finding.

---

## Simplicity

### Code Complexity
- [ ] Functions/methods are small and focused (generally <40 lines)
- [ ] Nesting depth is shallow (generally <=3 levels)
- [ ] Cyclomatic complexity is manageable in key modules
- [ ] Guard clauses used instead of deeply nested conditionals
- [ ] Complex boolean expressions are extracted to named variables or functions

### Duplication (DRY)
- [ ] No significant code blocks duplicated across files
- [ ] Shared logic is extracted to reusable functions/modules
- [ ] Configuration is not duplicated across environments
- [ ] Test setup/teardown is factored into helpers where repeated

### Naming
- [ ] Variables, functions, and classes have clear, intention-revealing names
- [ ] Naming is consistent across the codebase (same concept = same word)
- [ ] No cryptic abbreviations or single-letter names outside tight loops
- [ ] Boolean variables/functions read as questions (is_, has_, can_, should_)

### Abstractions
- [ ] Abstraction level is appropriate — not over-engineered for current needs
- [ ] No premature abstractions (single-use wrappers, one-implementation interfaces)
- [ ] No under-designed areas (raw primitives passed through many layers)
- [ ] Utility/helper sprawl is controlled

### Dead Code
- [ ] No unused imports
- [ ] No commented-out code blocks
- [ ] No unreachable code paths
- [ ] No unused functions/classes/variables

---

## Security

### Input Validation
- [ ] All user input is validated at system boundaries (API params, form data, file uploads)
- [ ] Validation rejects unexpected types, sizes, and formats
- [ ] Path traversal attacks prevented in file operations
- [ ] URL/redirect validation prevents open redirects

### Authentication & Authorization
- [ ] Auth is required on all protected endpoints/operations
- [ ] Auth tokens are validated correctly (expiry, signature, scope)
- [ ] Authorization checks enforce least-privilege access
- [ ] Session management is secure (secure cookies, proper expiry)

### Secrets Management
- [ ] No hardcoded credentials, API keys, passwords, or tokens in source
- [ ] Secrets loaded from environment variables or vault/KMS
- [ ] Secrets are not logged or included in error messages
- [ ] `.gitignore` excludes secret files (.env, credentials.json, *.pem)

### OWASP Top 10
- [ ] Injection: parameterized queries, no string concatenation for SQL/commands
- [ ] Broken auth: proper session/token management
- [ ] Sensitive data exposure: encryption at rest/transit where needed
- [ ] XXE: XML parsing configured to disable external entities
- [ ] Broken access control: authorization on every protected resource
- [ ] Security misconfiguration: no default credentials, debug disabled in prod
- [ ] XSS: output encoding for user-supplied content
- [ ] Insecure deserialization: schema validation on untrusted input
- [ ] Known vulnerabilities: dependencies audited (`npm audit`, `pip-audit`, etc.)
- [ ] Insufficient logging: security events logged (auth failures, access denied)

### Cryptography
- [ ] No weak algorithms (MD5/SHA1) for security purposes
- [ ] Proper random number generation (crypto-grade, not Math.random)
- [ ] TLS/HTTPS enforced for external communication

### Error Handling
- [ ] Error messages do not leak stack traces, internal paths, or credentials
- [ ] Error responses are consistent and do not reveal implementation details
- [ ] Failed auth attempts return generic messages (not "user not found" vs "wrong password")

---

## Data

### Data Flow Integrity
- [ ] Inputs traced through transformations to outputs/storage
- [ ] Data validated at each trust boundary (not just API layer)
- [ ] No silent data loss in error paths (failed writes detected and handled)
- [ ] Data transformations preserve type safety

### Database / Query Patterns
- [ ] All queries are parameterized (no string construction from user input)
- [ ] N+1 query patterns are avoided (batch loading, joins, or explicit caching)
- [ ] Transactions used where atomicity is required
- [ ] Migrations are safe (no data-loss operations without backfill)
- [ ] Connection pooling configured where applicable

### Serialization / Deserialization
- [ ] Schema validation on incoming data (JSON schema, protobuf, typed DTOs)
- [ ] Version-aware deserialization (handles missing/extra fields gracefully)
- [ ] No unsafe deserialization of untrusted input (pickle, eval, YAML load)

### State Management
- [ ] Mutable shared state is synchronized (locks, channels, atomics)
- [ ] Race conditions prevented in concurrent code paths
- [ ] Immutable data patterns used where appropriate
- [ ] State transitions are explicit and validated

### Caching
- [ ] Cache invalidation strategy is defined (TTL, event-driven, manual)
- [ ] Cache consistency with source of truth is maintained
- [ ] Cache stampede prevention for high-traffic paths
- [ ] No stale data served beyond acceptable window

### Privacy
- [ ] PII is identified and handled with care (not logged, encrypted at rest)
- [ ] Data retention policies reflected in code (cleanup jobs, TTLs)
- [ ] Consent boundaries respected in data collection paths

---

## Architecture

### SOLID Principles
- [ ] **Single Responsibility**: each module/class has one reason to change
- [ ] **Open/Closed**: extensible without modifying existing code
- [ ] **Liskov Substitution**: subtypes are substitutable for base types
- [ ] **Interface Segregation**: interfaces are focused, not bloated
- [ ] **Dependency Inversion**: depends on abstractions, not concretions

### Coupling & Cohesion
- [ ] Low coupling between modules (changes don't cascade)
- [ ] High cohesion within modules (related functionality grouped)
- [ ] No circular dependencies between packages/modules
- [ ] Dependency direction flows toward stable abstractions

### Layer Separation
- [ ] Presentation/transport layer separated from business logic
- [ ] Business logic separated from data access
- [ ] No framework-specific types leaking across layers
- [ ] Configuration separated from application code

### Design Patterns
- [ ] Patterns used appropriately (solving real problems, not imposed)
- [ ] No over-patterned code (unnecessary indirection, factory-of-factories)
- [ ] Common patterns applied consistently across the codebase
- [ ] Error handling pattern is consistent (Result types, exceptions, error codes)

### Extensibility
- [ ] New features can be added without modifying core modules
- [ ] Plugin/extension points where variability is expected
- [ ] API surface is minimal (only necessary public interfaces)

### Technical Debt
- [ ] TODO/FIXME density is manageable
- [ ] No `unimplemented!()`, `todo!()`, `pass` stubs in production paths
- [ ] No temporary hacks that have become permanent
- [ ] Deprecated code paths are marked and have removal plans

---

## Documentation

### README
- [ ] Project description explains what the project does and why
- [ ] Installation/setup instructions are present and accurate
- [ ] Usage examples demonstrate primary functionality
- [ ] Architecture overview or diagram for non-trivial projects
- [ ] Contributing section or link to CONTRIBUTING.md
- [ ] License information present

### API Documentation
- [ ] Public API endpoints/functions have documentation
- [ ] Parameters, return types, and error conditions documented
- [ ] Request/response examples provided
- [ ] Authentication requirements documented per endpoint

### Code Comments
- [ ] Public interfaces have doc comments
- [ ] Complex algorithms have explanatory comments (the "why")
- [ ] No redundant comments that restate the code (the "what")
- [ ] Non-obvious design decisions have inline rationale

### Architecture Documentation
- [ ] ADRs (Architecture Decision Records) for significant decisions
- [ ] Design documents for complex subsystems
- [ ] Data model documentation
- [ ] Integration/dependency documentation

### Maintenance Documentation
- [ ] CHANGELOG maintained with notable changes
- [ ] CONTRIBUTING guide with development workflow
- [ ] Release process documented
- [ ] Runbook/troubleshooting guides for operational components

---

## SDLC

### CI/CD Pipeline
- [ ] CI pipeline exists and runs on every PR/push
- [ ] Pipeline includes: build, lint, test (at minimum)
- [ ] Security scanning in pipeline (dependency audit, SAST)
- [ ] Deploy automation (CD) for production-bound code
- [ ] Pipeline status visible (badges, required checks)

### Build System
- [ ] Build is reproducible (same input = same output)
- [ ] Dependencies pinned with lock files (package-lock.json, Cargo.lock, etc.)
- [ ] Build targets documented (Makefile, scripts, npm scripts)
- [ ] No manual steps required for a clean build

### Test Infrastructure
- [ ] Test runner is configured and documented
- [ ] Test directories follow project conventions
- [ ] CI runs the full test suite
- [ ] Test coverage is measured (even if no minimum enforced)
- [ ] Tests are organized by type (unit, integration, e2e)

### Code Quality Tooling
- [ ] Linter configured and enforced (in CI or pre-commit)
- [ ] Formatter configured (consistent style enforcement)
- [ ] Type checker configured (if applicable: mypy, tsc, etc.)
- [ ] Pre-commit hooks installed for automated checks

### Release Process
- [ ] Versioning strategy defined (semver, calver)
- [ ] Release automation (tagged releases, changelog generation)
- [ ] Release artifacts produced consistently
- [ ] Rollback process defined for production deployments

### Dependency Management
- [ ] Lock files present and committed
- [ ] Automated dependency updates configured (Dependabot, Renovate)
- [ ] Dependency audit integrated into CI
- [ ] No pinning to vulnerable versions

### Development Environment
- [ ] Version pinning for language/runtime (.tool-versions, .python-version, etc.)
- [ ] Container-based dev environment available (Dockerfile, devcontainer)
- [ ] Setup instructions verified to work from a clean checkout
- [ ] Environment variables documented with defaults

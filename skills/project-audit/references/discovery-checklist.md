# Discovery Checklist

Comprehensive checklist for Phase 0 empirical discovery. The discovery agent works through each section and records what it finds. Missing items are documented as "not found" — never assumed.

## 1. Project Root Scan

```bash
# Map the file tree (config/manifest files only, 3 levels deep)
find . -maxdepth 3 -type f \( -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.md" -o -name "*.lock" -o -name "Makefile" -o -name "Dockerfile" -o -name "*.proto" -o -name "*.graphql" \) | sort | head -200

# Top-level directory structure
ls -d */ 2>/dev/null
```

## 2. Spec / Requirements Detection

Search paths (check all, record what exists):

| Pattern | Type |
|---|---|
| `spec/`, `specs/` | Dedicated spec directory |
| `docs/spec/`, `docs/design/` | Spec in docs |
| `requirements/`, `rfc/` | Requirements/RFC directory |
| `docs/adr/`, `adr/` | Architecture Decision Records |
| `**/openapi.yaml`, `**/openapi.json` | OpenAPI spec |
| `**/asyncapi.yaml` | AsyncAPI spec |
| `**/*.proto` | Protobuf definitions |
| `**/*.graphql`, `**/schema.graphql` | GraphQL schema |
| `**/conformance*`, `**/invariant*` | Conformance tests |
| `CLAUDE.md`, `CONTRIBUTING.md` | Implicit conventions |
| `README.md` (API sections) | Implicit API contract |

If no formal spec: note "No formal specification found" and identify the closest equivalents (tests as spec, README contracts, doc comments, ADRs).

## 3. Build System Detection

| Manifest | Language | Ecosystem |
|---|---|---|
| `Cargo.toml` + `Cargo.lock` | Rust | cargo |
| `pyproject.toml` / `setup.py` / `requirements.txt` | Python | pip/uv/poetry |
| `package.json` + `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` | JavaScript/TypeScript | npm/yarn/pnpm |
| `go.mod` + `go.sum` | Go | go modules |
| `pom.xml` / `build.gradle` / `build.gradle.kts` | Java/Kotlin | Maven/Gradle |
| `Gemfile` + `Gemfile.lock` | Ruby | bundler |
| `composer.json` | PHP | composer |
| `mix.exs` | Elixir | mix |
| `*.csproj` / `*.sln` | C#/.NET | dotnet |
| `CMakeLists.txt` / `Makefile` (standalone) | C/C++ | cmake/make |

Also detect:
- `Makefile` — extract targets: `grep -E '^[a-zA-Z_-]+:' Makefile`
- `Dockerfile`, `docker-compose.yml` — containerization
- `Justfile` — just command runner
- `.tool-versions`, `.python-version`, `.nvmrc`, `rust-toolchain.toml` — version pinning

## 4. Test Infrastructure

| Language | Test Runner | Config | Coverage |
|---|---|---|---|
| Rust | `cargo test` | `Cargo.toml [test]` | `cargo tarpaulin` / `cargo llvm-cov` |
| Python | `pytest` | `pyproject.toml [tool.pytest]`, `conftest.py` | `pytest-cov`, `coverage.py` |
| JS/TS | `jest` / `vitest` / `mocha` | `jest.config.*`, `vitest.config.*` | `c8`, `istanbul` |
| Go | `go test` | `*_test.go` files | `go test -cover` |
| Java | `JUnit` / `TestNG` | `src/test/` | JaCoCo |

Also check:
- CI workflows for test commands
- `.github/workflows/*.yml` — what checks are required
- Coverage thresholds in config
- Property-based testing (hypothesis, proptest, fast-check, rapid)

## 5. Linter / Formatter / Type Checker

| Language | Linter | Formatter | Types |
|---|---|---|---|
| Rust | `clippy` | `rustfmt` | Built-in |
| Python | `ruff`, `flake8`, `pylint` | `ruff format`, `black` | `mypy`, `pyright` |
| JS/TS | `eslint`, `biome` | `prettier`, `biome` | `tsc` |
| Go | `golangci-lint` | `gofmt` | Built-in |

Check configs: `.eslintrc*`, `ruff.toml`, `pyproject.toml [tool.ruff]`, `.golangci.yml`, `clippy.toml`, `rustfmt.toml`

## 6. Module / Crate / Package Enumeration

- **Rust**: `ls crates/` or check `[workspace.members]` in root `Cargo.toml`
- **Python**: Package directories with `__init__.py`, or `pyproject.toml [tool.setuptools.packages]`
- **Node**: `workspaces` in `package.json`, or `packages/` directory
- **Go**: `go list ./...` or directories with `*.go` files
- **Java**: Maven modules in `pom.xml`, Gradle subprojects

For monorepos: check `lerna.json`, `nx.json`, `turbo.json`, `pnpm-workspace.yaml`

## 7. API Surface

- REST: OpenAPI/Swagger specs, route registration files
- gRPC: `.proto` files, generated code directories
- GraphQL: Schema files, resolver directories
- MCP: `tool_sets/` directories, tool registration code
- CLI: Command registration, argument parsing
- Library: Public exports, `pub mod`, `__all__`, `exports` in package.json

## 8. Security Model

Search for:
- JWT: `jsonwebtoken`, `jose`, `jwt`, token validation middleware
- API keys: `x-api-key`, header extraction, key validation
- OAuth: `oauth`, `oidc`, token exchange
- mTLS: certificate loading, TLS config
- RBAC/ABAC: role checks, permission middleware
- Input validation: schema validation, sanitization, parameterized queries
- Secret management: env vars, vault integration, `.env` handling

## 9. CI/CD

- `.github/workflows/*.yml` — GitHub Actions
- `.gitlab-ci.yml` — GitLab CI
- `Jenkinsfile` — Jenkins
- `.circleci/config.yml` — CircleCI
- `bitbucket-pipelines.yml` — Bitbucket

Extract: required checks, deployment stages, environment gates

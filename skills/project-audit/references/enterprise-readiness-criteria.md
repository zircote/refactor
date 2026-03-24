# Enterprise Readiness Criteria

Scoring criteria for Phase 3 enterprise readiness assessment. Each dimension is scored as: **production-grade** (3), **partial** (2), **minimal** (1), **absent** (0).

## Observability

| Score | Structured Logging | Metrics | Health Endpoints | Distributed Tracing |
|---|---|---|---|---|
| 3 | JSON/structured with levels, correlation IDs, context | Prometheus/StatsD with custom business metrics | `/health`, `/ready` with dependency checks | OpenTelemetry with span propagation |
| 2 | Structured but missing correlation IDs or context | Basic counters (requests, errors) | Health endpoint exists, no dependency checks | Tracing present but no propagation |
| 1 | Printf/println logging | No metrics, but log-based counting possible | No health endpoint, process-level only | Request IDs but no spans |
| 0 | No logging | No metrics | No health endpoint | No tracing |

### What to look for

**Logging**:
- Rust: `tracing` crate with `tracing-subscriber`, structured fields
- Python: `structlog`, `logging` with JSON formatter
- Node: `winston`, `pino`, `bunyan`
- Go: `zap`, `zerolog`, `slog`

**Metrics**:
- Prometheus client libraries, `/metrics` endpoint
- StatsD/Datadog client
- Custom metric registration (counters, histograms, gauges)

**Health**:
- Dedicated health/readiness endpoints
- Dependency health checks (DB, cache, external services)
- Kubernetes probe compatibility

**Tracing**:
- OpenTelemetry SDK initialization
- Span creation in request handlers
- Context propagation across service boundaries

## Resilience

| Score | Error Recovery | Connection Pools | Graceful Shutdown | Timeouts | Retries | Backpressure |
|---|---|---|---|---|---|---|
| 3 | All errors caught, classified, and recovered | Pool with health checks, max size, idle timeout | Signal handling, drain in-flight, deadline | Per-operation timeouts, configurable | Exponential backoff with jitter, max retries | Queue limits, 429/503 responses |
| 2 | Most errors caught, some recovery | Pool exists, basic config | Signal handling, basic shutdown | Some timeouts | Fixed retries | Basic rate limiting |
| 1 | Errors caught but not recovered | Raw connections, no pooling | Abrupt shutdown | No timeouts | No retries | No backpressure |
| 0 | Panics/crashes on errors | N/A | No shutdown handling | N/A | N/A | N/A |

### What to look for

**Panic patterns** (should be zero in non-test code):
- Rust: `unwrap()`, `expect()`, `panic!()`, `todo!()`, `unimplemented!()`
- Python: bare `raise` in catch blocks, `sys.exit()` in library code
- Go: `panic(`, `log.Fatal` in library code
- Node: `process.exit()` in library code

**Connection pools**:
- Database: sqlx pool config, connection limits, health checks
- HTTP: client pool settings, keep-alive, connection reuse
- Redis/cache: pool config, reconnection logic

**Shutdown**:
- Signal handlers (SIGTERM, SIGINT)
- In-flight request draining
- Resource cleanup (DB connections, file handles, temp files)

## Configuration

| Score | Config Source | Validation | Secrets | Documentation |
|---|---|---|---|---|
| 3 | File + env vars + CLI flags, layered with precedence | Schema validation at startup, fail-fast on invalid | Vault/KMS integration, never logged | All knobs documented with defaults |
| 2 | File + env vars | Some validation | Env vars, redacted in logs | Most knobs documented |
| 1 | Hardcoded with env var overrides | No validation | Env vars, may appear in logs | Minimal documentation |
| 0 | Hardcoded values only | N/A | Hardcoded secrets | No documentation |

### What to look for

- Config file loading (TOML, YAML, JSON)
- Environment variable mapping
- Validation on startup (required fields, valid ranges, valid URLs)
- Secret redaction in logging/error messages
- Default values documented
- Config schema/struct with field documentation

## Scoring Summary

Total score across all dimensions: `observability + resilience + configuration`

| Total | Rating |
|---|---|
| 27-36 | Production-grade |
| 18-26 | Approaching production |
| 9-17 | Development quality |
| 0-8 | Prototype |

Note: A single score of 0 in any critical subdimension (error recovery, secret handling, structured logging) should be flagged as a P1 finding regardless of total score.

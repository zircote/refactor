# ADR-0001: Swarm Orchestration for Refactoring

## Status

Accepted

## Context

The refactor plugin needs to coordinate multiple specialist tasks during a refactoring session: codebase exploration, architecture analysis, code modification, test writing, and simplification. These tasks have natural dependencies but some can run in parallel.

## Decision

Use Claude Code's native swarm orchestration (TeamCreate, TaskCreate, SendMessage) to coordinate specialist agents:
- **code-explorer**: Deep codebase discovery (read-only)
- **architect**: Architecture analysis and optimization planning
- **refactor-code**: Code implementation
- **refactor-test**: Test coverage and writing
- **simplifier**: Post-refactor cleanup

## Consequences

- **Positive**: Parallel execution of independent tasks, isolated context per agent, natural progress tracking via task system
- **Negative**: Higher resource usage, coordination complexity, potential for agent conflicts on shared files
- **Mitigations**: Task dependencies prevent conflicts; sequential phases for file-modifying agents

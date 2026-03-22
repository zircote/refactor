# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the refactor plugin.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-swarm-orchestration-for-refactoring.md) | Swarm Orchestration for Refactoring | Accepted |
| [0002](0002-zero-runtime-dependencies.md) | Zero Runtime Dependencies | Accepted |
| [0003](0003-property-based-testing-with-hypothesis.md) | Property-Based Testing with Hypothesis | Accepted |

## Creating a New ADR

1. Copy the template below
2. Number sequentially (e.g., `0004-title.md`)
3. Fill in all sections
4. Submit via PR for review
5. Update this index

## Template

```markdown
# ADR-NNNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-NNNN

## Context
What is the issue that we're seeing that motivates this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult because of this change?
```

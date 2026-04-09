# CLAUDE.md

# Project Mission

GPM exists because its maintainer manages approaching **190 repositories** while simultaneously running a farm and working a full-time job. There is no team. There is no DevOps hire. GPM **is** the team.

Every feature, every workflow, every skill must be designed for **zero-touch operation at scale**. This means:

- **No manual loops**: If something needs to happen in N repos, GPM does it in N repos automatically. Never print instructions and expect a human to run them 190 times.
- **No babysitting**: Provisioning, deployment, compilation, auditing — all must complete end-to-end without prompting unless there's a genuine decision to make.
- **Bulk mode is the default mental model**: Interactive prompts are for one-off use. The provisioning pipeline (`$GPM_PROVISION_BULK=true`) is the primary path.
- **Idempotent and safe**: Every operation can be re-run without harm. SHA-compare before writing. Skip unchanged files. Never duplicate work.
- **Helper, not replacement**: GPM wraps real tools (`gh aw compile`, `gh api`, `gh project`). It does not reimplement them. When a real tool exists, use it.

This is not a developer toy or a learning project. It is operations infrastructure for a solo maintainer who cannot afford to context-switch into 190 repos.

---

## Branching Strategy

- **`main`** — Production. Protected. All merges via PR with required status checks.
- **`develop`** — Active development branch. All feature work, skill creation, and improvements target this branch.
- **Feature branches** — Branch from `develop`, merge back to `develop` via PR.

**All development work occurs on the `develop` branch.** When creating new branches, branch from `develop`. When creating PRs for new features or fixes, target `develop` as the base branch. Only merge `develop` → `main` for releases.

---

## Build & Test

```bash
make check          # Full CI: lint + typecheck + test + security
make test-quick     # Fast pytest only (no coverage)
make format         # Auto-fix ruff issues
```

**Coverage minimum**: 80% (enforced in pyproject.toml)

---

## Commit Conventions

Conventional commits: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `perf`, `chore`, `docs`, `test`, `style`, `ci`, `build`

No AI attribution lines.

---

## Pre-commit Hooks

Active via pre-commit framework (`.pre-commit-config.yaml`):
- ruff (lint + format)
- mypy (strict, scripts/ only)
- bandit (security, excludes tests/)

---

## Structured Data (xq)

**Prefer `jq`/`yq` over Read/Edit/Write for JSON, YAML, and TOML mutations and validation.** This is a reliability requirement, not a style preference — text-level editing of structured data causes silent corruption (trailing commas, broken nesting, lost encoding).

| Format | Tool | Mutate | Validate |
|--------|------|--------|----------|
| `.json` | `jq` | `jq --arg k "$V" '.key = $k' f > tmp.$$ && mv tmp.$$ f` | `jq empty f` |
| `.yaml`/`.yml` | `yq` | `yq -i '.key = "val"' f` | `yq '.' f > /dev/null` |
| `.toml` | `yq` (read) / `Edit` (write) | Read: `yq -p toml '.key' f` — Write: use `Edit` tool (yq write is lossy on nested tables; see `/xq` TOML Caveat) | `yq -p toml '.' f > /dev/null` |

- **Always** use `--arg`/`--argjson` for variable interpolation (never shell variables in jq expressions)
- **Never** redirect jq output to the same input file (`> f.json` truncates before read — use temp file + mv)
- **Read** tool is fine for comprehension; `jq`/`yq` required for mutations, validation, and extraction
- Run `/xq` for the full structured data reference

---

## Project Structure

```
scripts/      Core Python source (audit, protocols, detection, coverage, utils)
tests/        pytest suite with hypothesis property tests
agents/       12 specialist agent definitions for swarm orchestration
skills/       15+ skill definitions for Claude Code slash commands
commands/     CLI command definitions
hooks/        Git hook scripts
docs/         Documentation — ADRs, guides, tutorials, reference
evals/        Evaluation harnesses for skill quality testing
.github/      CI workflows, CODEOWNERS, Copilot instructions
```

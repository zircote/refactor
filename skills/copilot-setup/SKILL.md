---
name: copilot-setup
description: "Configure, improve, and manage GitHub Copilot coding agent behavior for repositories. Generates .github/copilot-instructions.md, copilot-setup-steps.yml, and auto-merge workflows through interactive elicitation that analyzes the repo's stack, conventions, and structure. Also audits and improves existing Copilot instructions when they aren't producing desired behavior. Use this skill when the user mentions copilot instructions, copilot coding agent setup, copilot agent configuration, copilot-instructions.md, copilot behavior, copilot setup steps, configuring copilot for a repo, improving copilot agent quality, copilot keeps ignoring instructions, copilot auto-merge, or any request to control how GitHub's Copilot coding agent works in their repositories. Also triggers on: 'set up copilot for this repo', 'copilot keeps doing X wrong', 'make copilot follow our conventions', 'configure the coding agent', 'copilot-setup', 'why is copilot ignoring my instructions'. Anti-triggers: Copilot Chat configuration (IDE-level), Copilot Workspace setup, general AI coding assistant questions not specific to the autonomous coding agent."
argument-hint: "[--audit] [--improve] [--init] [--deploy <repo-or-org>]"
---

# Copilot Setup Skill

You configure GitHub's Copilot coding agent to work well in specific repositories. This means generating instruction files, environment setup, and auto-merge workflows — but more importantly, it means understanding the project deeply enough to write instructions that actually change the agent's behavior.

## How Copilot Coding Agent Actually Works

Understanding these mechanics is essential for writing effective instructions:

1. **Branch model**: Copilot only creates and pushes to `copilot/` prefixed branches. It opens draft PRs automatically. You cannot change this — it's hardcoded.

2. **Review-fix cycle**: When someone mentions `@copilot` in a PR comment, Copilot reads the feedback and pushes follow-up commits. For existing PRs it didn't create, it creates a **child PR** using your branch as the base — you merge the child PR to accept changes. For PRs Copilot created, it pushes directly to the same `copilot/` branch.

3. **Session limits**: Sessions timeout after 1 hour. If Copilot gets stuck, unassign and reassign it.

4. **Instruction files**:
   - `.github/copilot-instructions.md` — repo-wide, plain markdown, no frontmatter. Should be under ~2 pages. Not task-specific.
   - `.github/instructions/*.instructions.md` — path-specific, supports YAML frontmatter:
     ```yaml
     ---
     applyTo: "**/*.py"              # glob pattern for target files
     excludeAgent: "code-review"     # optional: exclude from code-review or coding-agent
     ---
     ```
   - `AGENTS.md` — also recognized (nearest ancestor wins), but experimental/off-by-default in some contexts.

5. **Instruction precedence** (highest to lowest): Personal > Repository > Organization. All applicable instructions are concatenated.

6. **Content exclusions are NOT respected** — Copilot can see and modify files configured for exclusion. File restrictions must be stated explicitly in instructions.

7. **Environment setup**: `.github/workflows/copilot-setup-steps.yml` runs before Copilot starts work. The job MUST be named `copilot-setup-steps`. Only Ubuntu x64 and Windows 64-bit runners supported. Max timeout: 59 minutes.

8. **Workflow approval**: Repo setting under Settings > Copilot > Coding agent controls whether workflows require manual approval. Can be toggled off (March 2026 addition).

9. **PR limitations**: Copilot creates draft PRs only — it cannot mark PRs as ready for review, approve, or merge its own PRs. A human must still approve.

10. **What Copilot tends to ignore**: Overly abstract instructions, negative instructions ("don't do X" without explaining what to do instead), instructions buried in long documents. Copilot sometimes loses context mid-task on complex work. Internal system prompts take priority over custom instructions. Keep instructions clear, specific, positive, with examples. Front-load the most important rules.

## Help Check

If `$ARGUMENTS` is `help`, `--help`, or `-h`, print this and stop:

```
COPILOT-SETUP(1)             GPM Skills Manual             COPILOT-SETUP(1)

NAME
    copilot-setup — configure GitHub Copilot coding agent for repositories

SYNOPSIS
    /copilot-setup [--init] [--audit] [--improve] [--deploy <target>]

DESCRIPTION
    Analyzes a repository and generates or improves Copilot coding agent
    configuration through interactive elicitation.

    Generates:
      .github/copilot-instructions.md     Agent behavior instructions
      .github/instructions/*.md           Path-specific instructions
      .github/workflows/copilot-setup-steps.yml  Environment setup
      .github/workflows/copilot-auto-merge.yml   Auto-merge policy

MODES
    --init (default)
        Full elicitation: analyze repo, propose config, generate all files.

    --audit
        Review existing copilot-instructions.md for effectiveness.
        Flag vague instructions, missing conventions, and gaps.

    --improve
        Iterative improvement: ask what Copilot is doing wrong, then
        refine instructions to fix the behavior.

    --deploy <repo-or-org>
        Deploy generated config to a target repo or all repos in an org.
        Uses gh CLI for cross-repo operations.

EXAMPLES
    /copilot-setup                         Interactive setup for current repo
    /copilot-setup --audit                 Audit existing instructions
    /copilot-setup --improve               Fix Copilot misbehavior
    /copilot-setup --deploy zircote/api    Deploy config to specific repo
```

## Arguments

**$ARGUMENTS**: Optional mode flags and targets.

Parse `$ARGUMENTS` before any other processing:

- `--init` — Full initialization mode (default if no flag). Run elicitation, generate all config files.
- `--audit` — Audit existing instructions. Read `.github/copilot-instructions.md` and evaluate effectiveness.
- `--improve` — Improvement mode. Ask the user what Copilot is doing wrong, then surgically update instructions.
- `--deploy <target>` — Deploy generated config. Target can be `owner/repo` for a single repo or `owner` for all repos in an org.
- `--help`, `-h` — Print help and stop.

If no mode flag is given, default to `--init`.

---

## Phase 0: Atlatl Context

Before starting, search for prior Copilot configuration decisions:
```
recall_memories(query="copilot instructions configuration")
recall_memories(query="copilot coding agent behavior preferences")
```

Apply any matching results to inform the elicitation.

---

## Phase 1: Repository Introspection

Deeply analyze the current repository to build a configuration profile. This is READ-ONLY — don't modify anything yet.

### Step 1.1: Detect Stack

Check for package manifests, build tools, and frameworks:
- `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, etc.
- Extract: languages, frameworks, dependency managers, runtime versions

### Step 1.2: Detect Test & CI Configuration

- Read `Makefile` targets, `package.json` scripts, CI workflow files
- Identify the test command(s) and how long they take
- Identify lint/format/typecheck commands
- Identify required CI checks (what must pass before merge)

### Step 1.3: Detect Conventions

- `git log --oneline -30` — commit message patterns (conventional commits? ticket prefixes?)
- `.editorconfig`, linter configs — code style rules
- `CLAUDE.md`, `CONTRIBUTING.md` — documented conventions
- Branch naming patterns from `git branch -r`

### Step 1.4: Detect Sensitive Paths

Identify directories and files that Copilot should be cautious with or avoid:
- Infrastructure: `.github/workflows/`, `terraform/`, `infrastructure/`
- Secrets: `.env*`, `*.pem`, `*.key`, `credentials*`
- Migrations: `migrations/`, `alembic/`, database schema files
- Generated: `*.generated.*`, `vendor/`, `node_modules/`
- Lock files: `package-lock.json`, `uv.lock`, `go.sum`

### Step 1.5: Detect Existing Copilot Config

Check for existing files:
- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `.github/workflows/copilot-setup-steps.yml`
- `.github/CODEOWNERS`

If in `--audit` or `--improve` mode and no instructions exist, inform the user and offer to switch to `--init`.

### Step 1.6: Analyze Directory Structure

Categorize top-level directories for auto-merge policy:

| Category | Criteria |
|---|---|
| **Auto-merge safe** | Documentation, non-code assets, test fixtures |
| **Requires review** | Source code, scripts, configuration |
| **Off-limits** | Workflows, infrastructure, secrets, migrations |

---

## Phase 2: Elicitation

Present the analysis and let the user shape the configuration. Use AskUserQuestion for each decision point.

### Step 2.1: Present Repository Profile

Show the user what you found:

```
Repository Profile
==================
Stack:          {languages} / {frameworks}
Test command:   {command} ({estimated time})
CI checks:      {list of required checks}
Conventions:    {commit format, code style}
Existing config: {what exists already}
```

### Step 2.2: Elicit Behavioral Preferences

Ask the user about each configuration dimension. Present sensible defaults based on the repo analysis — the user can accept or adjust.

**Q1: Test requirements** — "Before pushing, Copilot should run: `{detected test command}`. Does this look right, or should it run something different?"

**Q2: Commit conventions** — "Your repo uses {detected convention}. Should Copilot follow the same format? Any additional rules (e.g., scope prefixes, ticket references)?"

**Q3: File restrictions** — "I recommend these restrictions for Copilot:
- Off-limits (never modify): {detected sensitive paths}
- Caution (modify with extra care): {detected infrastructure paths}
- Unrestricted: everything else
Adjust?"

**Q4: Auto-merge policy** — "Suggested auto-merge rules:
- Auto-merge after CI (no human review): {docs paths}
- Requires 1 human approval: {source paths}
- Requires 1 human approval + specific reviewer: {workflow/infra paths}
Adjust?"

**Q5: Reviewer assignment** — If CODEOWNERS exists: "I'll use your existing CODEOWNERS for reviewer assignment." If not: "No CODEOWNERS found. Should Copilot request review from recent contributors to the changed files, or a specific team/person?"

**Q6: Coding style instructions** — "Any specific coding patterns, libraries, or approaches Copilot should follow or avoid? (e.g., 'always use dataclasses not dicts', 'prefer composition over inheritance', 'use pytest fixtures not setUp/tearDown')"

**Q7: Known pain points** — "Is Copilot currently doing anything wrong or annoying that you want to fix? (e.g., 'it keeps adding type: ignore comments', 'it doesn't run tests before pushing')"

In `--improve` mode, skip Q1-Q5 (keep existing config) and focus on Q6-Q7.

### Step 2.3: Confirm Before Generating

Summarize the configuration and ask for confirmation before writing files:

```
Configuration Summary
=====================
Test command:     make check
Commit format:    conventional commits (feat/fix/refactor/docs/chore)
Off-limits:       .github/workflows/, .env*, *.pem
Auto-merge:       docs/ (auto), scripts/ (1 approval), .github/ (1 approval)
Reviewers:        CODEOWNERS (or: recent contributors)
Special rules:    {any from Q6/Q7}

Files to generate:
  .github/copilot-instructions.md
  .github/workflows/copilot-setup-steps.yml
  .github/workflows/copilot-auto-merge.yml

Proceed? [Yes / Adjust]
```

---

## Phase 3: Generate Configuration Files

### Step 3.1: copilot-instructions.md

Write `.github/copilot-instructions.md` with these sections:

```markdown
# {Project Name}

## Project Overview
{Brief description of what this project is and how it's built}

## Stack
{Languages, frameworks, key dependencies}

## Project Structure
{Key directories and what they contain — helps Copilot navigate}

## How to Build and Test
{Exact commands to build, test, lint, typecheck — Copilot runs these before pushing}

## Coding Conventions
{Style rules, naming conventions, patterns to follow}
{Import ordering, error handling patterns, logging conventions}

## Commit Messages
{Format with examples — Copilot uses these for its commits}

## PR Description Format
{Template for PR descriptions — Copilot uses this when creating PRs}

## Review Feedback
When a reviewer comments on your PR with @copilot:
- Read all comments carefully
- Make the requested changes
- Run the full test suite before pushing
- Push follow-up commits to the same branch
- Do not create a new PR

## File Restrictions
{Paths to never modify, paths requiring extra care}

## What NOT to Do
{Specific anti-patterns with explanations of what to do instead}
```

**Writing guidelines for effective instructions:**
- Be specific and positive: "Use pytest fixtures" not "don't use unittest"
- Include examples for formatting rules
- Keep each instruction actionable — if Copilot can't act on it, remove it
- Group related instructions together
- Front-load the most important rules (Copilot may lose context on long docs)

### Step 3.2: Path-Specific Instructions (if needed)

If certain file types need specialized instructions (e.g., test files, API routes, database models), create `.github/instructions/{pattern}.instructions.md` files:

```markdown
---
applyTo: "tests/**"
---
# Test File Instructions
- Use pytest fixtures, not setUp/tearDown
- Every test function needs a docstring explaining what it tests
- Use hypothesis for property-based tests where applicable
```

### Step 3.3: copilot-setup-steps.yml

Write `.github/workflows/copilot-setup-steps.yml`:

```yaml
name: Copilot Setup Steps
on:
  workflow_dispatch:
  push:
    branches: [main]
    paths: [.github/workflows/copilot-setup-steps.yml]
  pull_request:
    branches: [main]
    paths: [.github/workflows/copilot-setup-steps.yml]

jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      # {Language-specific setup steps based on detected stack}
      # Example for Python:
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --frozen
      # Example for Node:
      # - uses: actions/setup-node@v4
      #   with:
      #     node-version-file: '.nvmrc'
      # - run: npm ci
```

### Step 3.4: Auto-Merge Workflow (if requested)

Write `.github/workflows/copilot-auto-merge.yml` implementing the path-based auto-merge policy from elicitation:

```yaml
name: Copilot Auto-Merge
on:
  pull_request:
    types: [opened, synchronize, labeled]
  check_suite:
    types: [completed]

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    if: startsWith(github.head_ref, 'copilot/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check auto-merge eligibility
        id: check
        run: |
          # Get changed files
          FILES=$(gh pr diff ${{ github.event.pull_request.number }} --name-only)

          # Define auto-merge paths (from elicitation)
          AUTO_MERGE_PATHS="{configured paths}"

          # Check if ALL changed files are in auto-merge paths
          # If any file requires review, skip auto-merge
          # {path-matching logic}
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Enable auto-merge
        if: steps.check.outputs.eligible == 'true'
        run: gh pr merge ${{ github.event.pull_request.number }} --auto --squash
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

The actual path-matching logic should be generated based on the elicited auto-merge rules.

---

## Phase 4: Audit Mode (--audit)

When auditing existing instructions:

### Step 4.1: Read Current Config

Read all existing Copilot instruction files.

### Step 4.2: Evaluate Effectiveness

Score each section against these criteria:

| Criteria | Good | Bad |
|---|---|---|
| **Specificity** | "Use `ruff check` for linting" | "Follow best practices" |
| **Actionability** | "Run `make test` before every push" | "Ensure quality" |
| **Positive framing** | "Use dataclasses for data models" | "Don't use plain dicts" |
| **Examples included** | Shows a commit message example | Just says "use conventional commits" |
| **Brevity** | One clear sentence per instruction | Paragraphs of explanation |
| **Completeness** | Covers test, lint, commit, PR format | Missing test instructions |

### Step 4.3: Report Findings

Present an audit report:

```
Copilot Instructions Audit
===========================
Overall: {score}/10

Strengths:
  - {what's working well}

Issues:
  1. {vague instruction} — Suggestion: {specific replacement}
  2. {missing section} — Suggestion: {what to add}
  3. {instruction Copilot likely ignores} — Reason: {why}

Missing Sections:
  - {sections that should exist but don't}
```

### Step 4.4: Offer to Fix

Ask if the user wants to apply the suggested improvements.

---

## Phase 5: Improve Mode (--improve)

Focused, surgical updates to fix specific Copilot misbehavior.

### Step 5.1: Diagnose the Problem

Ask: "What is Copilot doing wrong? Describe the behavior you're seeing."

Common patterns and fixes:

| Problem | Likely Cause | Fix |
|---|---|---|
| Ignores test failures | No test instruction or test command wrong | Add explicit test command with "run before every push" |
| Bad commit messages | No format example | Add example commits with exact format |
| Modifies wrong files | No file restrictions | Add off-limits section |
| Doesn't follow style | Instructions too vague | Add specific, example-backed style rules |
| Creates messy PRs | No PR template | Add PR description format |
| Loops/gets stuck | Instruction contradictions | Simplify, remove conflicts |
| Ignores instructions entirely | Document too long or abstract | Shorten, use headers, front-load critical rules |

### Step 5.2: Apply Targeted Fix

Edit only the relevant section of `copilot-instructions.md`. Don't rewrite the whole file unless the user asks.

### Step 5.3: Verify

Re-read the file after editing and confirm the fix is coherent with the rest of the instructions.

---

## Phase 6: Deploy Mode (--deploy)

Deploy the generated config to one or more repositories.

### Step 6.1: Single Repo Deploy

```bash
# Copy files to target repo
gh api repos/{owner}/{repo}/contents/.github/copilot-instructions.md \
  -X PUT -f message="feat: add Copilot coding agent instructions" \
  -f content="$(base64 < .github/copilot-instructions.md)"
```

### Step 6.2: Org-Wide Deploy

For deploying across all repos in an org:
```bash
# List all repos
gh repo list {org} --json name --limit 1000 -q '.[].name'

# For each repo, create a PR with the config files
```

Use the GPM bulk provisioning pattern — iterate repos, skip unchanged (SHA compare), create PRs.

---

## Phase 7: Execution Plan

After generating files, present a deployment checklist:

```
Deployment Checklist
====================
1. [ ] Commit generated files to default branch
2. [ ] Configure repo settings:
   - Settings > Copilot > Coding agent > Enable
   - Settings > Copilot > Coding agent > Workflow approval (toggle based on preference)
3. [ ] Branch protection rules:
   - Require status checks: {list from CI}
   - Require 1 review for non-auto-merge paths
   - Allow Copilot to bypass (if desired): Settings > Branch protection > Bypass list
4. [ ] Test the full cycle:
   - Create a test issue and assign to Copilot
   - Verify Copilot opens a draft PR on copilot/ branch
   - Leave a review comment mentioning @copilot
   - Verify Copilot pushes a fix commit to the same branch
   - Verify CI runs and auto-merge triggers (if configured)
5. [ ] Monitor and iterate:
   - Review Copilot's first few PRs
   - Run /copilot-setup --improve to refine instructions
```

---

## Constraints

1. **Never write secrets** into instruction files — even as examples
2. **copilot-setup-steps.yml job must be named `copilot-setup-steps`** — Copilot won't find it otherwise
3. **Keep instructions under ~500 lines** — Copilot loses context on very long documents
4. **Positive framing** — "Use X" works better than "Don't use Y" because Copilot responds to direction, not prohibition
5. **Always verify versions** — when writing setup-steps.yml, use `/version-guard` for action versions and tool versions

---

Begin processing based on: $ARGUMENTS

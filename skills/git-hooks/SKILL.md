---
name: git-hooks
description: "Analyze a project's languages, tooling, CI/CD, and conventions to intelligently recommend and implement tailored git hooks that prevent post-commit/push failures and improve developer experience. Detects existing hook managers (husky, pre-commit, lefthook) and works within them. Use this skill when the user mentions git hooks, pre-commit hooks, pre-push hooks, commit-msg hooks, wants to prevent CI failures locally, wants to add linting/formatting/secrets-scanning to commits, asks about hook managers, says 'set up hooks', 'add pre-commit', 'prevent bad pushes', 'catch errors before CI', 'git-hooks', or wants to improve commit hygiene. Also triggers on 'why did CI fail on something I could have caught locally' or 'how do I enforce conventions before push'."
argument-hint: "[--auto] [--dry-run] [--help]"
---

# Git Hooks Skill — Intelligent Project-Aware Hook Provisioning

You are a git hooks specialist. Your job is to deeply understand the project you're operating in, then recommend and implement git hooks that are genuinely useful for *this specific project* — not a generic checklist.

The key insight: the best hooks are the ones that catch locally what would otherwise fail remotely. Examine the project's CI/CD pipeline, linter configs, test setup, and past pain points to figure out what those are. Then propose hooks that are fast, helpful, and non-annoying.

## Arguments

**$ARGUMENTS**: Optional flags.

- `--auto` — Non-interactive mode. Detect everything, apply best-practice defaults, write hooks without prompting. Designed for bulk provisioning across many repos. Still respects existing hook managers and never overwrites existing hooks without cause.
- `--dry-run` — Run the full analysis and show what would be installed, but don't write anything. Useful for auditing.
- `--help` or `-h` — Print help and stop.

If no flags are present, run in interactive mode (analyze, present findings, elicit preferences, implement).

## Help Output

When help is requested, display this and stop:

```
GIT-HOOKS(1)                 Refactor Skills Manual                 GIT-HOOKS(1)

NAME
    git-hooks — analyze a project and implement tailored git hooks

SYNOPSIS
    /git-hooks [--auto] [--dry-run]

DESCRIPTION
    Examines the current project's languages, tooling, CI/CD configuration,
    and conventions to recommend and install git hooks that catch errors
    locally before they fail in CI or get rejected on push.

    Detects existing hook managers (husky, pre-commit, lefthook) and works
    within them. If none exist, recommends one based on the project's stack.

OPTIONS
    --auto      Non-interactive mode. Apply best-practice defaults without
                prompting. Designed for bulk provisioning across many repos.

    --dry-run   Show what would be installed without writing anything.

    --help, -h  Display this help text and exit.

MODES
    Interactive (default)
        Analyze → present findings → elicit preferences → implement.

    Auto (--auto)
        Analyze → apply defaults → implement → report what was done.

    Dry-run (--dry-run)
        Analyze → report what would be done. Combines with --auto.

EXAMPLES
    /git-hooks                  Interactive analysis and setup
    /git-hooks --auto           Zero-touch provisioning
    /git-hooks --dry-run        Audit what hooks would be recommended
    /git-hooks --auto --dry-run Preview auto-mode choices without writing
```

---

## Phase 1: Deep Project Introspection

This is the most important phase. Do not rush it. The quality of your hook recommendations depends entirely on how well you understand this project.

### Step 1.1: Detect Project Identity

Examine the project root and build a mental model:

1. **Package manifests** — check for all of these (not just the first match):
   - `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` (Node.js)
   - `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`, `Pipfile` (Python)
   - `go.mod`, `go.sum` (Go)
   - `Cargo.toml`, `Cargo.lock` (Rust)
   - `Gemfile`, `Gemfile.lock` (Ruby)
   - `pom.xml`, `build.gradle`, `build.gradle.kts` (Java/Kotlin)
   - `composer.json` (PHP)
   - `mix.exs` (Elixir)
   - `*.csproj`, `*.sln` (C#/.NET)
   - `Makefile`, `CMakeLists.txt` (C/C++)
   - `deno.json`, `bun.lockb` (Deno/Bun)

2. **Monorepo detection** — check for workspace configs, `lerna.json`, `nx.json`, `turbo.json`, `pnpm-workspace.yaml`, or multiple package manifests in subdirectories. Monorepos need hooks that scope checks to changed files only — full-repo scans are unacceptable.

3. **Project type signals** — look for:
   - `Dockerfile`, `docker-compose.yml` (containerized)
   - `serverless.yml`, `sam.yaml`, `cdk.json` (serverless/IaC)
   - `terraform/`, `*.tf` (infrastructure)
   - `.claude/`, `CLAUDE.md` (Claude Code project)
   - `*.proto` (protobuf APIs)
   - `.github/workflows/**/*.md` (GitHub Agentic Workflows — `gh aw` workflow definitions)

4. **GitHub Agentic Workflows detection** — check for `.md` files in `.github/workflows/` (including subdirectories). These are `gh aw` agentic workflow definition files that must be compiled to YAML before push:
   ```bash
   find .github/workflows -name '*.md' -type f 2>/dev/null | head -20
   ```
   If any `.md` files are found, verify that `gh aw` is installed:
   ```bash
   gh aw --version 2>/dev/null || echo "gh-aw not installed"
   ```
   Record both the presence of `.md` workflow files and whether `gh aw` is available.

Record everything you find. This informs which hooks are relevant.

### Step 1.2: Detect Existing Tooling

For each detected language/framework, check for the tools that are actually configured (not just possibly useful):

1. **Linters and formatters** — read config files, not just check existence:
   - `.eslintrc*`, `eslint.config.*`, `.prettierrc*`, `biome.json` (JS/TS)
   - `ruff.toml`, `pyproject.toml [tool.ruff]`, `.flake8`, `.pylintrc`, `.black.toml` (Python)
   - `.golangci.yml`, `.golangci.yaml` (Go)
   - `clippy.toml`, `rustfmt.toml` (Rust)
   - `.rubocop.yml` (Ruby)
   - `checkstyle.xml`, `.editorconfig` (Java)

2. **Type checkers** — `tsconfig.json`, `mypy.ini`, `pyright`, `pyrightconfig.json`

3. **Test runners** — detect the actual test command:
   - Check `package.json` scripts for `test`, `test:unit`, `test:e2e`
   - Check `Makefile` for `test` target
   - Check for `pytest.ini`, `conftest.py`, `jest.config.*`, `vitest.config.*`
   - Check for `_test.go` files, `tests/` directories, `spec/` directories

4. **Build tools** — `tsc`, `esbuild`, `webpack`, `vite`, `cargo build`, `go build`

### Step 1.3: Detect Existing Hook Infrastructure

Check all of these:

1. **Hook managers**:
   - `.husky/` directory + `package.json` `prepare` script → Husky
   - `.pre-commit-config.yaml` → pre-commit framework
   - `lefthook.yml` or `lefthook-local.yml` → Lefthook
   - `.lintstagedrc*`, `package.json` `lint-staged` key → lint-staged (usually paired with husky)
   - `package.json` `simple-git-hooks` key → simple-git-hooks

2. **Raw hooks** — check `.git/hooks/` for any non-sample scripts (files without `.sample` extension that are executable)

3. **Hook-adjacent configs** — `.commitlintrc*`, `commitlint.config.*`, `.czrc`, `.cz.toml` (conventional commits tooling)

4. **Activation status** — a config file existing does NOT mean hooks are active. Verify activation:
   - For pre-commit: check if `.git/hooks/pre-commit` exists and is not a sample file (run `ls -la .git/hooks/pre-commit 2>/dev/null`). If `.pre-commit-config.yaml` exists but hooks aren't installed, this is a critical finding — the user has configured hooks but never activated them.
   - For Husky: check if `.husky/_/husky.sh` exists and `.git/hooks/` contains the husky shim
   - For Lefthook: check if `.git/hooks/` contains lefthook shims

Record what exists AND whether it is actually active. A dormant config (config file present but hooks not installed) is one of the most important findings you can surface — it often explains why CI keeps failing despite hooks being "set up." Call this out prominently in your analysis.

The implementation phase MUST work within whatever framework is already present. Never install a competing hook manager.

### Step 1.4: Analyze CI/CD Pipeline

This is where the real intelligence lives. The best hooks are CI checks that run fast enough locally.

1. **Read CI config files**:
   - `.github/workflows/*.yml` (GitHub Actions)
   - `.gitlab-ci.yml` (GitLab CI)
   - `Jenkinsfile` (Jenkins)
   - `.circleci/config.yml` (CircleCI)
   - `bitbucket-pipelines.yml` (Bitbucket)
   - `.travis.yml` (Travis)
   - `azure-pipelines.yml` (Azure DevOps)

2. **Extract the checks that CI runs**: lint, format check, type check, test, build, security scan, license check, etc.

3. **Identify which CI checks could run locally in <10 seconds** on staged files. These are your prime hook candidates. Checks that take minutes (full test suites, Docker builds, E2E tests) are NOT good pre-commit hooks — at most they belong in pre-push, and even then only if they're fast enough.

4. **Look for patterns of CI failure** — if the repo has GitHub Actions, check recent workflow run statuses:
   ```bash
   gh run list --limit 20 --json conclusion,name 2>/dev/null || true
   ```
   Frequent failures in lint/format/typecheck steps are strong signals that a pre-commit hook would help.

### Step 1.5: Detect Conventions and Constraints

1. **Commit message conventions** — check for:
   - `.commitlintrc*`, `commitlint.config.*` (already enforced)
   - Existing commit history: `git log --oneline -20` — are they using conventional commits? Ticket prefixes? A custom format?
   - `CONTRIBUTING.md` or `CLAUDE.md` with commit message guidelines

2. **Branch naming conventions** — check recent branches:
   ```bash
   git branch -r --list 'origin/*' | head -20
   ```
   Look for patterns: `feat/`, `fix/`, `feature/`, ticket numbers, etc.

3. **Protected branches** — check if branch protection exists:
   ```bash
   gh api repos/{owner}/{repo}/branches/main/protection 2>/dev/null || true
   ```

4. **File size limits** — check `.gitattributes` for LFS patterns, check if git-lfs is used

---

## Phase 2: Reasoning and Recommendation

Based on everything discovered in Phase 1, reason about what hooks would genuinely help this project. Do not apply a generic checklist — think about what problems this specific project has or is likely to have.

### Step 2.1: Build the Recommendation Set

For each potential hook, evaluate:

1. **Would this catch a real problem?** If CI already runs it and it rarely fails, the hook adds friction without value. If CI runs it and it *frequently* fails, the hook saves real time.

2. **Is it fast enough?** Pre-commit hooks must complete in <5 seconds on staged files. Pre-push hooks can take up to 30 seconds. Anything slower should be a warning or opt-in.

3. **Does the tooling already exist?** Only recommend hooks that use tools the project already has installed or that are trivially installable. Don't recommend `clippy` for a Python project.

4. **Does it respect the developer's flow?** Hooks that block on style nits during rapid prototyping are annoying. Hooks that prevent pushing broken code to shared branches are valuable. Prioritize accordingly.

### Step 2.2: Categorize Recommendations

Organize into tiers:

**Tier 1 — High confidence, should almost always install:**
- Lint/format staged files (if linter/formatter is configured)
- Secrets detection (only if a secrets scanner is already configured in the project, e.g., detect-secrets, gitleaks, trufflehog — do not introduce a new tool the project doesn't use)
- Large file prevention (if no LFS is configured)
- Commit message validation (if project uses conventional commits)
- **`gh aw compile` sync check on push** (if `.github/workflows/**/*.md` agentic workflow files are detected AND `gh aw` is installed) — on every push, verify that committed `.yml` files match what `gh aw compile` would produce from the `.md` sources. Compiles into a temp directory (never the working tree) and diffs against committed state. Catches stale `.yml` regardless of whether `.md` files are in the current changeset. Also detects orphaned `.yml` files whose `.md` source was deleted.

> **Note on Tier 1 in auto mode**: Even Tier 1 hooks must satisfy Constraint 7 — every hook must use tooling already present in the project. A secrets scanner hook is Tier 1 only if the project already has one configured. If it doesn't, secrets detection moves to Tier 2 (recommended suggestion) in interactive mode and is skipped entirely in auto mode. Similarly, the `gh aw compile` hook is Tier 1 only when both `.github/workflows/**/*.md` files exist AND `gh aw` is installed.

**Tier 2 — Recommended based on project signals:**
- Type checking staged files (if type checker is configured and fast)
- Test running on push (if tests are fast — <30s)
- Branch naming validation (if conventions detected)
- WIP commit detection on push (prevent pushing "wip" or "fixup" commits)
- Dependency lock file consistency (if lock files exist)

**Tier 3 — Available but situational:**
- Build verification on push
- Documentation lint (if markdown linter configured)
- API schema validation (if protobuf/OpenAPI detected)
- License header check
- TODO/FIXME annotation warnings
- Post-checkout dependency auto-install
- Merge conflict marker detection

**Innovative hooks to consider** (think beyond the standard set):
- If CI has a specific step that fails often, create a targeted hook for it
- If the project has a `Makefile` with a `check` or `lint` target, hook into it
- If the project has custom validation scripts, incorporate them
- If the project uses database migrations, check for missing migration files alongside model changes
- If the project has generated files (protobuf, GraphQL codegen, **`gh aw` compiled workflows**), check they're up to date

### Step 2.3: Present Findings and Elicit User Choice

**This step's behavior depends entirely on the mode:**

#### Interactive Mode (no `--auto` flag) — MANDATORY USER CONFIRMATION

> **CRITICAL**: In interactive mode, you MUST ask the user before proceeding to implementation. This is not optional. Do NOT simulate, assume, or infer the user's choice. Do NOT proceed to Phase 3 without explicit user input.

1. Present your analysis:
   - **Project summary** — what you found (languages, tools, CI, existing hooks)
   - **Recommendations** — organized by tier, with rationale for each
   - **What you'll use** — which hook manager (existing or recommended)

2. **Use AskUserQuestion to let the user select which hooks to install.** Present tier 1 as pre-selected recommendations, tier 2 as suggested, tier 3 as available. Use `multiSelect: true`. This is the gate between analysis and implementation — without user input, you stop here and wait.

3. Only after receiving the user's selection, proceed to Phase 3 with exactly what they chose.

If you cannot use AskUserQuestion (e.g., in a non-interactive environment), present your recommendations and explicitly state that you are waiting for user confirmation before proceeding. Do NOT auto-select on the user's behalf.

#### Auto Mode (`--auto` flag)

Install all tier 1 hooks and tier 2 hooks **where the underlying tool is already installed and configured in the project**. Skip tier 3 unless tooling is already configured for them. Do NOT add new tools the project doesn't already use — this means if the project has no secrets scanner configured, do not add one in auto mode (see Constraint 7).

#### Dry-run Mode (`--dry-run` flag)

Display the full analysis and what would be installed, then stop. Do not write any files.

---

## Phase 3: Implementation

### Step 3.1: Choose Hook Manager Strategy

**If a hook manager already exists**: Use it. Period. No exceptions. Configure hooks through the existing manager's configuration format.

**If no hook manager exists**, choose based on the project's primary stack:

| Primary Language | Recommended Manager | Rationale |
|---|---|---|
| JavaScript/TypeScript | Husky + lint-staged | Ecosystem standard, npm-native |
| Python | pre-commit framework | Language-agnostic, huge hook catalog |
| Go | Lefthook | Fast (Go binary), no runtime dependency |
| Rust | Lefthook | Fast, no runtime dependency |
| Multi-language / Monorepo | Lefthook | Parallel execution, language-agnostic |
| Other | pre-commit framework | Broadest community hook support |

In `--auto` mode, install the recommended manager. In interactive mode, present the recommendation and let the user choose.

### Step 3.2: Implement Each Selected Hook

For each hook, the implementation must:

1. **Run only on relevant files** — use the hook manager's file filtering (lint-staged glob patterns, pre-commit `files` regex, lefthook `glob`). Never lint the entire repo on every commit.

2. **Fail with actionable messages** — when a hook fails, the developer must understand:
   - What failed (the tool name and check)
   - Why it failed (the specific error from the tool)
   - How to fix it (the command to run, or an auto-fix suggestion)
   - How to bypass it in an emergency (`git commit --no-verify`)

3. **Be idempotent** — running the hook twice produces the same result. No state accumulation.

4. **Handle edge cases**:
   - Empty commits (no staged files) — skip gracefully
   - Binary files — exclude from text-based checks
   - Deleted files — don't try to lint files that no longer exist
   - Initial commit (no prior history) — handle missing HEAD gracefully
   - Merge commits — consider skipping or running reduced checks

### Step 3.3: Hook Manager Configuration Templates

Write the configuration in the appropriate format for the detected/chosen manager.

**For pre-commit framework** (`.pre-commit-config.yaml`):
- Use official hook repos from the pre-commit registry where possible
- Pin repo versions to specific tags (not `main` or `latest`)
- **Verify versions using `/version-guard`** — before pinning ANY version (hook repo tags, tool versions, package versions), invoke the `/version-guard` skill to look up the latest stable version. Do NOT guess, recall from training data, or use `gh api` to check versions manually — `/version-guard` is the authoritative source. If an existing config already pins versions, still verify them with `/version-guard` to flag outdated pins. Fabricated or stale version tags will cause `pre-commit install` to fail.
- Use `stages` to assign hooks to the correct git event
- Set `language_version` if the project pins a specific runtime

**For Husky** (`.husky/`):
- Create hook scripts in `.husky/` directory
- If lint-staged is needed, add `.lintstagedrc.json` or configure in `package.json`
- Add `prepare` script to `package.json` if not present: `"prepare": "husky"`
- Use `npx` for tools that may not be globally installed

**For Lefthook** (`lefthook.yml`):
- Use `parallel: true` for independent checks within a hook
- Use `glob` patterns for file filtering
- Use `run` for simple commands, `script` for complex logic
- Set `fail_text` for clear error messages

**For raw shell scripts** (`.git/hooks/` — last resort):
- Write POSIX sh when possible, bash only if needed
- Include a shebang line (`#!/usr/bin/env bash`)
- Make executable (`chmod +x`)
- Create a `scripts/install-hooks.sh` for team setup
- Document in README or CONTRIBUTING.md

### Step 3.4: GitHub Agentic Workflows (`gh aw compile`) Hook

If Phase 1 detected `.github/workflows/**/*.md` files and `gh aw` is installed, implement a pre-push hook that ensures compiled YAML is in sync with source markdown.

#### Design principles — avoid these traps:

1. **Never scope the hook to only run when `.md` files changed.** A stale `.yml` can exist because:
   - The `.md` was edited in a prior unpushed commit that the current push includes.
   - `gh aw` itself was upgraded and compiles differently.
   - Someone hand-edited a `.yml` file instead of the `.md` source.
   The hook must run on **every push** (gated only on whether `.md` workflow files exist in the repo at all), not just when the diff includes `.md` changes.

2. **Never compile into the working tree.** `gh aw compile` overwrites `.yml` files in place. If the developer has unstaged or work-in-progress changes to `.yml` files, the hook would silently destroy them. Instead, compile into a temp directory and compare the output against the committed `.yml` files.

3. **Use `find` or `git ls-files` for recursive file discovery**, not bash globs. `*.yml` does not recurse into subdirectories, and `**/*.yml` requires `shopt -s globstar` which is not portable across bash versions or POSIX sh.

4. **Detect orphaned compiled `.yml` files.** When a `.md` source is deleted, its compiled `.yml` counterpart becomes orphaned — it no longer has a source but still runs as a GitHub Actions workflow. Use the compile output as the authoritative set of managed files — do not rely on generation-marker comments in `.yml` headers, which may be absent. Check for `.md` files deleted in the push range whose `.yml` counterpart is still committed but was NOT in the compile output. That's an orphan requiring `git rm`.

#### Hook logic (all managers use this same algorithm):

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Fast exit: skip if no .md workflow definitions exist in the repo
md_count=$(git ls-files -- '.github/workflows/*.md' '.github/workflows/**/*.md' 2>/dev/null | wc -l)
if [ "$md_count" -eq 0 ]; then exit 0; fi

# 2. Verify gh aw is available
if ! command -v gh >/dev/null 2>&1 || ! gh aw --version >/dev/null 2>&1; then
  echo "WARNING: gh-aw extension not installed — skipping workflow compile check."
  echo "Install: gh extension install github/gh-aw"
  exit 0
fi

# 3. Compile into a temp directory to avoid working-tree pollution
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# Copy committed .md sources into temp so gh aw compile has them
while IFS= read -r f; do
  mkdir -p "$tmpdir/$(dirname "$f")"
  # Use the committed version, not the working-tree version
  git show "HEAD:$f" > "$tmpdir/$f"
done < <(git ls-files -- '.github/workflows/*.md' '.github/workflows/**/*.md')

# Run compile in the temp directory
(cd "$tmpdir" && gh aw compile) || {
  echo "ERROR: gh aw compile failed. Fix the workflow .md definitions and retry."
  exit 1
}

# 4. Compare each compiled .yml against the committed version
stale=()
while IFS= read -r compiled_yml; do
  rel_path="${compiled_yml#$tmpdir/}"
  # Get the committed version of this .yml (empty string if file is new)
  committed=$(git show "HEAD:$rel_path" 2>/dev/null || true)
  freshly_compiled=$(cat "$compiled_yml")
  if [ "$committed" != "$freshly_compiled" ]; then
    if [ -z "$committed" ]; then
      stale+=("$rel_path (new — not yet committed)")
    else
      stale+=("$rel_path")
    fi
  fi
done < <(find "$tmpdir/.github/workflows" -name '*.yml' -type f 2>/dev/null)

# 5. Detect orphaned .yml files — compiled workflows whose .md source was deleted
#    The compile output from step 3 is the authoritative set of gh-aw-managed .yml
#    files. Build that set, then check: any committed .yml whose stem matches a
#    known gh-aw pattern (had a .md source at some point) but is NOT in the current
#    compile output is orphaned.
#
#    How we know a .yml is gh-aw-managed (not hand-authored):
#      - Its path appears in the compile output (current .md exists → managed), OR
#      - A .md with the same stem was deleted in the push range (was managed → now orphaned)
#    Hand-authored .yml files (ci.yml, release.yml, etc.) never had a .md counterpart
#    and are never flagged.
orphaned=()

# Build the set of .yml paths that compile produced (these are the CURRENT managed set)
declare -A compiled_set
while IFS= read -r compiled_yml; do
  rel_path="${compiled_yml#$tmpdir/}"
  compiled_set["$rel_path"]=1
done < <(find "$tmpdir/.github/workflows" -name '*.yml' -type f 2>/dev/null)

# Check for .md files deleted in the push range whose .yml counterpart still exists
# but is NOT in the current compile output (i.e., it's now orphaned)
push_base=$(git rev-parse --verify @{push} 2>/dev/null \
  || git rev-parse --verify "origin/$(git branch --show-current)" 2>/dev/null \
  || git rev-parse --verify origin/HEAD 2>/dev/null \
  || echo "origin/main")
while IFS= read -r deleted_md; do
  [ -z "$deleted_md" ] && continue
  yml_counterpart="${deleted_md%.md}.yml"
  # Only flag if the .yml is still committed AND was not re-produced by compile
  # (handles rename: old.md deleted + new.md created → old.yml orphaned, new.yml managed)
  if git cat-file -e "HEAD:$yml_counterpart" 2>/dev/null && [ -z "${compiled_set[$yml_counterpart]+x}" ]; then
    orphaned+=("$yml_counterpart (source ${deleted_md} was deleted)")
  fi
done < <(git diff --name-only --diff-filter=D "$push_base"..HEAD -- '.github/workflows/*.md' '.github/workflows/**/*.md' 2>/dev/null)

# 6. Report all issues
issues=("${stale[@]+"${stale[@]}"}" "${orphaned[@]+"${orphaned[@]}"}")
if [ ${#issues[@]} -gt 0 ]; then
  echo ""
  echo "ERROR: Compiled workflow .yml files are out of sync with .md sources."
  echo ""
  if [ ${#stale[@]} -gt 0 ]; then
    echo "Stale (recompilation needed):"
    for f in "${stale[@]}"; do
      echo "  - $f"
    done
  fi
  if [ ${#orphaned[@]} -gt 0 ]; then
    echo "Orphaned (source .md deleted but compiled .yml remains):"
    for f in "${orphaned[@]}"; do
      echo "  - $f"
    done
  fi
  echo ""
  echo "Fix:"
  echo "  gh aw compile                        # recompile from current .md sources"
  echo "  git rm <orphaned .yml files>          # remove orphaned compiled files"
  echo "  git add .github/workflows/"
  echo "  git commit -m 'chore: sync gh-aw compiled workflows'"
  echo "  git push"
  exit 1
fi
```

#### Integration by hook manager:

**For pre-commit framework** (`.pre-commit-config.yaml`):

Add a `local` hook at the `pre-push` stage. Note: `always_run: true` and no `files` filter — the hook self-gates on whether `.md` files exist in the repo.
```yaml
- repo: local
  hooks:
    - id: gh-aw-compile-check
      name: Check gh-aw workflow .yml files are in sync
      entry: bash -c '<paste the hook logic above, or reference a script file>'
      language: system
      stages: [pre-push]
      always_run: true
      pass_filenames: false
```

Or better — save the hook logic to a script file (e.g., `scripts/check-aw-compile.sh`, `chmod +x`) and reference it:
```yaml
- repo: local
  hooks:
    - id: gh-aw-compile-check
      name: Check gh-aw workflow .yml files are in sync
      entry: scripts/check-aw-compile.sh
      language: script
      stages: [pre-push]
      always_run: true
      pass_filenames: false
```

**For Lefthook** (`lefthook.yml`):
```yaml
pre-push:
  commands:
    gh-aw-compile-check:
      run: scripts/check-aw-compile.sh
      fail_text: "Workflow .yml files are out of sync with .md sources. Run 'gh aw compile' and commit."
```

No `glob` filter — the script handles its own gating.

**For Husky** (`.husky/pre-push`):
```bash
#!/usr/bin/env bash
# gh-aw compile sync check
scripts/check-aw-compile.sh
```

**For raw shell scripts** (`.git/hooks/pre-push`):
Use the hook logic directly as the pre-push script, with `chmod +x`.

### Step 3.5: Write and Verify

1. **Before writing anything**, show the user exactly what will be created/modified (even in `--auto` mode, log what was written).

2. **Write the configuration files**.

3. **Install the hook manager** if one was chosen and isn't already installed. Before installing, invoke `/version-guard` to verify the latest stable version of the hook manager package:
   - `npm install --save-dev husky lint-staged` (Node.js)
   - `pip install pre-commit && pre-commit install` (Python)
   - `npm install --save-dev lefthook && npx lefthook install` (Lefthook via npm)
   - Or instruct the user to install it if package manager isn't clear

4. **Test the hooks** — run a smoke test to verify they work:
   ```bash
   # For pre-commit framework:
   pre-commit run --all-files 2>&1 | head -30

   # For husky/lefthook:
   # Stage a small change, run the hook manually
   ```

5. **Report results** — what was installed, what each hook does, and how to bypass (`--no-verify`).

---

## Phase 4: Summary and Guidance

### Step 4.1: Report

Present a clear summary:

```
Git hooks installed!

Hook Manager: {manager} ({existing or newly installed})

Hooks configured:
  pre-commit:
    - {hook}: {what it does} ({estimated time})
    - ...
  commit-msg:
    - {hook}: {what it does}
  pre-push:
    - {hook}: {what it does} ({estimated time})

Files created/modified:
  - {file}: {what changed}

Bypass: git commit --no-verify / git push --no-verify

{If --auto: "Auto-provisioned based on detected stack. Review the configuration and adjust as needed."}
```

### Step 4.2: Team Setup Notes

If the hook manager requires team setup (e.g., `pre-commit install` after clone, or `npm install` triggering husky's `prepare` script), mention it. If there's a way to automate this (like the `prepare` script in package.json), ensure it's configured.

---

## Constraints

These are non-negotiable:

1. **Never install hooks silently in interactive mode** — always use AskUserQuestion to confirm before writing. Present your recommendations, then ask the user which hooks they want. Do not proceed to implementation without their explicit selection. `--auto` mode is the only path that skips user confirmation.

2. **Never override an existing hook manager** — if husky exists, don't install pre-commit. Work within what's there.

3. **Never override existing hook scripts** without showing the diff and getting confirmation (interactive) or creating a backup (auto).

4. **Hooks must be fast** — pre-commit: <5s on staged files. Pre-push: <30s. If a recommended check would exceed this, warn explicitly and make it opt-in.

5. **Hooks must have escape hatches** — always document `--no-verify`. Never create hooks that can't be bypassed in an emergency.

6. `--dry-run` — For uninstall mode: show which hooks would be removed without removing them.

7. **Hooks must fail clearly** — cryptic failures that make developers reach for `--no-verify` as a habit defeat the entire purpose. Every failure must explain the problem and the fix.

8. **Respect the project** — in auto mode, every hook you install must use a tool that is already installed and configured in the project. Do not introduce new tools, even popular ones like detect-secrets or gitleaks, unless the project already uses them. In interactive mode, you may suggest new tools as Tier 2/3 recommendations, but the user decides whether to add them.

9. **Always use `/version-guard` for versioned artifacts** — whenever selecting, recommending, or pinning a version (hook repo tags in `.pre-commit-config.yaml`, npm/pip package versions for hook managers, tool versions in `lefthook.yml`), invoke the `/version-guard` skill to verify the latest stable version. Never rely on training data for version numbers — they go stale. This applies in all modes (interactive, auto, dry-run).

---

Begin processing now based on: $ARGUMENTS

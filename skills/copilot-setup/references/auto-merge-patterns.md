# Auto-Merge Patterns for Copilot PRs

Patterns for configuring path-based auto-merge policies that work with
GitHub branch protection and Copilot's `copilot/` branch model.

> **STALENESS WARNING**: Action versions and GitHub API behavior change.
> Always use `/version-guard` to verify action versions (actions/checkout,
> astral-sh/setup-uv, etc.) before generating workflow files. Do not trust
> the versions in these templates — they are examples, not pinned sources.

## Architecture

Copilot cannot approve or merge its own PRs. Auto-merge requires:
1. Branch protection with required status checks
2. GitHub's native auto-merge feature enabled on the repo
3. A workflow that calls `gh pr merge --auto` for eligible PRs
4. Human approval for paths outside the auto-merge safe list

## Path Classification Strategy

### Tier 1: Auto-merge safe (CI only)

Files where CI passing is sufficient assurance:
- Documentation (`docs/`, `*.md` excluding SECURITY.md)
- Test files (`tests/`) — CI validates coverage threshold
- Eval harnesses (`evals/`)
- Config files (`.editorconfig`, `.gitignore`)
- Changelog, README, CONTRIBUTING

### Tier 2: Requires human review

Files where automated checks aren't enough:
- Source code (`src/`, `scripts/`, `lib/`)
- Agent/skill definitions (behavior changes)
- Build configuration (`Makefile`, `pyproject.toml`, `package.json`)
- Dependencies (version bumps, new deps)

### Tier 3: Off-limits

Files Copilot should never modify (enforced via instructions, not workflow):
- CI/CD pipelines (`.github/workflows/`)
- Security policies, secrets
- Infrastructure as code
- Lock files (auto-generated)

## Workflow Template

```yaml
name: Copilot Auto-Merge
on:
  pull_request_review:
    types: [submitted]
  check_suite:
    types: [completed]

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    if: github.event.pull_request && startsWith(github.head_ref, 'copilot/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check eligibility
        id: check
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
        run: |
          FILES=$(gh pr diff "${PR_NUMBER}" --name-only)
          # AUTO_SAFE array populated from elicitation
          AUTO_SAFE=("docs/" "tests/" "evals/" "CHANGELOG.md" "README.md")

          ELIGIBLE=true
          while IFS= read -r file; do
            [ -z "${file}" ] && continue
            SAFE=false
            for pattern in "${AUTO_SAFE[@]}"; do
              [[ "${file}" == ${pattern}* ]] && SAFE=true && break
            done
            [ "${SAFE}" = false ] && ELIGIBLE=false && break
          done <<< "${FILES}"

          echo "eligible=${ELIGIBLE}" >> "$GITHUB_OUTPUT"

      - name: Auto-merge
        if: steps.check.outputs.eligible == 'true'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: gh pr merge "${{ github.event.pull_request.number }}" --auto --squash
```

## Bot PR Handling

For bot authors (dependabot, renovate):
- Check `github.event.pull_request.user.login` for `[bot]` suffix
- Auto-merge patch/minor updates if CI passes
- Require review for major version bumps
- Always check for breaking changes in changelog

## Branch Protection Compatibility

The auto-merge workflow works WITH branch protection, not around it:
- `gh pr merge --auto` queues the merge for when all requirements are met
- Required status checks must all pass
- Required reviewers must approve (for non-auto-merge paths)
- The workflow itself doesn't bypass any protection rules

# Feature: gh-grind Harness Redesign — Swarm Orchestration + Triple-Layer Review

Redesign `/gh-grind` to follow the Anthropic effective harnesses pattern for long-running agents, adopt the swarm orchestration architecture from `/refactor` and `/feature-dev`, and add a triple-layer review pipeline (Copilot + Sonnet code-reviewer + Codex adversarial review) to every PR.

## Problem Statement

`/gh-grind` is a flat procedural script that processes issues sequentially without the resilience patterns that make `/refactor` and `/feature-dev` survive long-running sessions: no checkpointing, no blackboard state, no progress manifests for cross-session continuity, and no swarm coordination for complex items. Its single quality gate (Copilot review) catches surface-level issues but misses design flaws, trust boundary violations, and failure-mode gaps. Adding multi-model review diversity (Claude Sonnet for quality/security + Codex for adversarial design challenge) would catch materially different classes of defects before merge.

## Proposed Solution

### 1. Initializer/Continuation Pattern (from Anthropic blog)

First run creates `grind-progress.json` — a structured manifest of the queue, per-item state, routing decisions, and session metadata. Subsequent sessions (or context resets within a long run) read the manifest + git log to resume exactly where they left off. No re-discovery, no re-processing merged items.

### 2. Swarm Orchestration (from refactor/feature-dev)

Replace the flat procedural loop with TeamCreate → TaskCreate → Agent(team_name) → SendMessage. The grind lead is the orchestrator; implementation agents and review agents are persistent teammates spawned on demand. Deferred spawning — feature-dev agents only materialize when a COMPLEX item is popped.

### 3. Blackboard + Checkpointing (from refactor/feature-dev)

Per-session blackboard tracks queue state, current item, per-item results, and checkpoint. After each item completes, checkpoint is written. On resume, the lead reads the checkpoint and skips completed items.

### 4. Triple-Layer Review Pipeline

After implementation and PR creation, every PR passes through three review layers:

| Layer | Model | Agent | Purpose | Gate |
|-------|-------|-------|---------|------|
| 1. Copilot | GPT (GitHub) | `copilot-pull-request-reviewer[bot]` | Surface-level: style, patterns, obvious bugs | Soft (timeout → proceed) |
| 2. Sonnet | Claude Sonnet | `refactor:code-reviewer` with `model: "sonnet"` | Confidence-scored quality + security review | Hard (remediate or skip) |
| 3. Adversarial | Codex/GPT | `/codex:adversarial-review --wait --scope branch` | Design challenges: trust boundaries, failure modes, rollback safety, race conditions | Hard (remediate or skip) |

Layers 2 and 3 run in parallel (independent models, independent concerns). Copilot runs first since it's async (request → poll). All three layers' findings are merged, deduplicated, and remediated in a single pass.

## Acceptance Criteria

- [ ] gh-grind uses TeamCreate + TaskCreate + SendMessage swarm pattern
- [ ] Blackboard created per session with checkpoint/resume support
- [ ] `grind-progress.json` manifest created on first run, read on subsequent runs
- [ ] Progress manifest tracks per-item state: `queued`, `in-progress`, `merged`, `skipped`
- [ ] COMPLEX items spawn feature-dev agents via deferred team_name spawning
- [ ] SIMPLE items still processed inline by lead (no swarm overhead)
- [ ] Copilot review requested and polled (existing behavior preserved)
- [ ] Sonnet code-reviewer agent spawned with `model: "sonnet"` for quality + security review
- [ ] Codex adversarial review invoked via `codex-companion.mjs adversarial-review --wait`
- [ ] Sonnet + Codex reviews run in parallel
- [ ] All three layers' findings merged and remediated in a single pass
- [ ] `--confidence=N` threshold applies uniformly to all review layers
- [ ] Graceful degradation: if codex plugin unavailable, warn and skip adversarial layer
- [ ] Graceful degradation: if code-reviewer agent unavailable, warn and skip sonnet layer
- [ ] Items that fail remediation are skipped with reason, branch cleaned up
- [ ] Grind report (Phase 8) includes per-layer review statistics
- [ ] No AI attribution in commits

## Scope

**In scope:**
- Full restructure of `gh-grind/SKILL.md` to swarm orchestration pattern
- Adding initializer/continuation pattern with `grind-progress.json` manifest
- Adding checkpoint/resume via blackboard (identical pattern to refactor/feature-dev)
- Integrating `/codex:adversarial-review` as a quality gate in Phase 5 (Sweep)
- Integrating `refactor:code-reviewer` with `model: "sonnet"` as quality gate in Phase 5
- Adversarial finding remediation loop (remediate material findings, re-review if needed)
- Deferred agent spawning (inline agents upfront, feature-dev agents only when COMPLEX routing triggers)
- Finding merge, deduplication, and unified remediation across all three layers
- Grind report additions for multi-layer review stats
- All existing arguments and behavior preserved (backward compatible)

**Out of scope:**
- Autonomous convergence loop (gh-grind is sequential issue processing, not iterative improvement of a single artifact)
- Convergence-reporter agent (grind has its own session report, Phase 8)
- Modifications to the codex adversarial-review command or prompt themselves
- Modifications to the refactor code-reviewer agent definition
- Changes to `/feature-dev` or `/refactor` skills internally

## Technical Approach

- **Files to create:** None — this is a restructure of existing SKILL.md
- **Files to modify:** `plugins/refactor/skills/gh-grind/SKILL.md` — full rewrite

### Patterns to Follow

| Pattern | Source | Application |
|---------|--------|-------------|
| Swarm init | `refactor/SKILL.md` Phase 0.2 | TeamCreate → blackboard_create → TaskCreate → checkpoint check |
| Task discovery protocol | `feature-dev/SKILL.md` Phase 0.2 template | Exact copy for all teammates |
| Deferred spawning | `refactor/SKILL.md` Step 0.3 | Spawn only when needed |
| Checkpoint/resume | `feature-dev/SKILL.md` Step 0.1.5 | blackboard_write after each item |
| Progress manifest | Blog's `feature_list.json` pattern | Adapted as `grind-progress.json` with per-item state |
| Adversarial review | `codex/commands/adversarial-review.md` | Foreground flow via `codex-companion.mjs` |
| Code-reviewer spawning | `refactor/SKILL.md` Step 0.9 | With `model: "sonnet"` override |

---

## Phase Structure (Redesigned)

```
Phase 0: Queue Assembly + Swarm Init
  0.1: Prerequisites (existing)
  0.2: Create team + blackboard + checkpoint check (NEW)
  0.3: Load or create grind-progress.json manifest (NEW)
  0.4: Discover/validate post-triage issues (existing, reads manifest)
  0.5: Priority sort + epic detection (existing)
  0.6: Display queue (existing)

Phase 1: Item Selection (existing, checkpoint-aware)
  1.1: Take next item (reads manifest state, skips completed)
  1.2: Check for existing PR (existing)
  1.3: Detect complexity → route SIMPLE/COMPLEX (existing)
  1.4: Write checkpoint to blackboard (NEW)

Phase 2: Branch Creation (existing)

Phase 3: Implementation
  Route A (SIMPLE): Inline by lead (existing, no swarm overhead)
  Route B (COMPLEX): Spawn feature-dev agents with team_name (NEW — deferred spawning)

Phase 4: PR Creation (existing)

Phase 5: Triple-Layer Review + Sweep (REDESIGNED)
  5.1: Request Copilot review (existing)
  5.2: Spawn Sonnet code-reviewer + launch Codex adversarial IN PARALLEL (NEW)
  5.3: Poll Copilot review (existing)
  5.4: Collect all three layers' findings (NEW)
  5.5: Merge + deduplicate findings across layers (NEW)
  5.6: Confidence-based triage (existing, extended to all layers)
  5.7: Remediation (existing, handles merged findings)
  5.8: Commit fixes (existing)
  5.9: Reply to Copilot comments (existing)
  5.10: Resolve threads (existing)
  5.11: Push (existing)
  5.12: CI gate (existing)
  5.13: Final verification (existing)
  5.14: Merge (existing)

Phase 6: Verification (existing)
  6.1: Verify issue closed
  6.2: Update grind-progress.json manifest (NEW)
  6.3: Write checkpoint to blackboard (NEW)

Phase 7: Loop Control (existing)

Phase 8: Grind Report (existing, extended with review layer stats)
```

---

## grind-progress.json Schema

```json
{
  "version": "1.0",
  "repo": "owner/repo",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "session_count": 1,
  "items": [
    {
      "number": 42,
      "title": "Fix null pointer in auth handler",
      "labels": ["priority/critical", "type/bug"],
      "routing": "SIMPLE",
      "state": "merged",
      "pr_number": 101,
      "commit_sha": "abc1234",
      "review_layers": {
        "copilot": {"status": "approved", "findings": 0},
        "sonnet": {"status": "approved", "findings": 2, "remediated": 2},
        "adversarial": {"status": "approved", "findings": 1, "remediated": 1}
      },
      "skip_reason": null,
      "started_at": "ISO-8601",
      "completed_at": "ISO-8601"
    }
  ],
  "epics": [
    {"number": 55, "sub_issues": [56, 57, 58], "state": "partial"}
  ]
}
```

### Item States

| State | Meaning |
|-------|---------|
| `queued` | Discovered, not yet started |
| `in-progress` | Currently being processed |
| `merged` | PR merged, issue closed |
| `skipped` | Failed at some gate, with `skip_reason` |

### Manifest Lifecycle

1. **First run**: Discover issues → create manifest with all items in `queued` state
2. **Each item start**: Update item to `in-progress`, write `started_at`
3. **Each item complete**: Update to `merged` or `skipped`, write `completed_at`
4. **Session resume**: Read manifest, skip items in `merged` or `skipped` state. Items in `in-progress` state are recovered: reset to `queued` (the implementation phase will detect any existing PR and resume accordingly).
5. **Pruning**: On load, remove items with `completed_at` older than 30 days

---

## Triple-Layer Review Detail (Phase 5.2)

### Launch Pattern

```
# Layer 1: Copilot (already requested in Step 5.1)
# Copilot is async — we requested review earlier, now polling begins

# Layer 2: Sonnet code-reviewer — spawn as teammate
Agent tool with:
  subagent_type: "refactor:code-reviewer"
  team_name: "grind-team"
  name: "sonnet-reviewer"
  model: "sonnet"
  prompt: "You are the Sonnet code reviewer on a grind team.
    Review PR #{PR_NUMBER} on branch ${BRANCH}.
    Focus: quality (bugs, logic, conventions) and security
    (regressions, secrets, OWASP).
    Return confidence-scored findings.

    BLACKBOARD: {blackboard_id}
    Write findings to key: review_sonnet_{ISSUE_NUMBER}

    TASK DISCOVERY PROTOCOL:
    1. Call TaskList to find tasks assigned to you.
    2. Call TaskGet on your assigned task.
    3. Work on the task.
    4. Mark completed via TaskUpdate, send results via SendMessage.
    5. NEVER commit code via git."

# Layer 3: Codex adversarial review — invoke via companion script
Bash tool:
  command: node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" \
    adversarial-review --wait --scope branch
  description: "Codex adversarial review for PR #${PR_NUMBER}"

# BOTH launched in the same tool-call message (parallel execution)
```

### Graceful Degradation

```
# Before Layer 2: Check if code-reviewer agent is available
# If spawn fails: warn "Sonnet code-reviewer unavailable — skipping Layer 2"
# Continue with Copilot + Adversarial only

# Before Layer 3: Check if codex plugin is available
codex_available = test -f "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"
# If not found: warn "Codex plugin unavailable — skipping adversarial review"
# Continue with Copilot + Sonnet only

# If BOTH unavailable: fall back to Copilot-only (original behavior)
```

---

## Finding Merge Logic (Phase 5.5)

```
all_findings = []

# Copilot findings (existing extraction logic)
all_findings += copilot_comments.map(c => {
  source: "copilot",
  priority: classify(c),       # P0/P1/P2/P3/Info
  confidence: infer(c),        # Inferred from language strength
  file: c.path,
  line: c.line,
  body: c.body
})

# Sonnet findings (structured JSON from code-reviewer agent)
all_findings += sonnet_findings.map(f => {
  source: "sonnet",
  priority: f.severity,        # From confidence scoring
  confidence: f.confidence,    # Direct 0-100
  file: f.file,
  line: f.line,
  body: f.description
})

# Codex adversarial findings (JSON from adversarial-review output)
all_findings += adversarial_findings.map(f => {
  source: "codex-adversarial",
  priority: map_confidence(f.confidence),  # 0-1 → P0/P1/P2
  confidence: f.confidence * 100,          # Normalize to 0-100
  file: f.file,
  line: f.line_start,
  body: f.body
})

# Deduplicate WITHIN each source only (never across models — confidence scales are not comparable)
deduplicated = deduplicate(all_findings, by=[source, file, line_range, semantic_similarity])

# Apply --confidence threshold only to sources with calibrated confidence (Sonnet)
# For Copilot (inferred) and Codex (normalized), triage by priority alone
actionable = deduplicated.filter(f =>
  f.source == "sonnet" ? f.confidence >= threshold :
  f.priority <= "P1"  # P0 and P1 always actionable regardless of confidence
)
```

### Deduplication Rules

| Condition | Action |
|-----------|--------|
| Same source, same file, overlapping lines (±5), similar description | Keep higher-confidence finding |
| Same source, same file, overlapping lines, different concern | Keep both |
| Different sources, same file, overlapping lines, similar description | Keep both (cross-model confidence is not comparable) |
| Different files | No dedup possible |

---

## Blackboard Keys

| Key Pattern | Writer | Reader | Phase |
|-------------|--------|--------|-------|
| `grind:queue` | team lead | all agents | 0 |
| `grind:current_item` | team lead | implementation agents | 1 |
| `grind:checkpoint` | team lead | team lead (on resume) | 1, 6 |
| `grind:item_{N}_result` | team lead | team lead | 6 |
| `grind:review_copilot_{N}` | team lead | team lead | 5 |
| `grind:review_sonnet_{N}` | sonnet-reviewer | team lead | 5 |
| `grind:review_adversarial_{N}` | team lead (from codex output) | team lead | 5 |
| `grind:merged_findings_{N}` | team lead | team lead | 5 |

---

## Grind Report Additions (Phase 8)

```
Review Layer Statistics:
  Copilot:     <total findings> found, <remediated> fixed, <skipped> skipped
  Sonnet:      <total findings> found, <remediated> fixed, <skipped> skipped
  Adversarial: <total findings> found, <remediated> fixed, <skipped> skipped

  Cross-layer duplicates removed: <count>
  Unique findings per layer:
    Copilot-only:     <count>  (surface issues)
    Sonnet-only:      <count>  (quality/security)
    Adversarial-only: <count>  (design challenges)

  Adversarial review verdicts:
    approve:          <count>
    needs-attention:  <count>
    skipped (timeout):<count>
```

---

## Test Plan

- Verify swarm init (TeamCreate + blackboard) succeeds before processing
- Verify `grind-progress.json` created on first run with correct schema
- Verify manifest read + resume skips already-merged items
- Verify checkpoint written after each item
- Verify checkpoint resume restores to correct item in queue
- Verify SIMPLE items processed without spawning extra agents
- Verify COMPLEX items spawn feature-dev agents with team_name
- Verify Copilot review polling works as before
- Verify Sonnet code-reviewer spawns with `model: "sonnet"` and returns findings
- Verify Codex adversarial review invoked and returns JSON findings
- Verify Sonnet + Codex run in parallel (not sequential)
- Verify finding merge deduplicates overlapping findings across layers
- Verify `--confidence=N` filters all three layers uniformly
- Verify graceful degradation when codex plugin unavailable
- Verify graceful degradation when code-reviewer agent unavailable
- Verify skipped items have branch cleaned up and reason logged
- Verify grind report includes per-layer statistics
- Verify `--dry-run` still works (no swarm init needed for dry run)
- Verify all existing arguments (`--once`, `--limit`, `--poll`, etc.) continue to work

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Adversarial review adds latency per PR | Run Sonnet + Codex in parallel; total added time is `max(sonnet, codex)` not sum. Typically 2-5 min. |
| Codex plugin not installed | Graceful degradation: detect absence, warn, skip layer 3. Two-layer review still superior to Copilot-only. |
| Sonnet code-reviewer false positives | Confidence threshold applies. Default 95% means only high-confidence findings are actioned. |
| Adversarial review returns design-level findings that can't be auto-fixed | Attempt remediation; if fix fails or finding is architectural, skip item with reason "Adversarial finding requires manual review: {summary}". |
| Progress manifest grows unbounded for repos with hundreds of issues | Prune completed items older than 30 days on each load. Keep only active + recently-completed items. |
| Swarm overhead for single-item runs (`/gh-grind 42`) | TeamCreate is lightweight. For single items, the swarm adds ~2s overhead. Acceptable. |
| Context window pressure from three layers of findings | Merge and deduplicate before presenting to remediation. Only actionable findings (above threshold) enter the remediation pipeline. |
| Codex adversarial review and Sonnet disagree on severity | Both findings kept if they target different concerns. If same concern, higher confidence wins. No automatic escalation from disagreement. |

---

## References

- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Initializer/continuation pattern, progress manifests, feature list architecture
- `plugins/refactor/skills/refactor/SKILL.md` — Swarm orchestration, blackboard, checkpoint, deferred spawning patterns
- `plugins/refactor/skills/feature-dev/SKILL.md` — Task discovery protocol, multi-instance spawning, checkpoint pattern
- `plugins/refactor/references/autonomous-algorithm.md` — Keep/discard gating, snapshot/restore (referenced but not adopted — gh-grind is sequential, not convergent)
- `.claude/plugins/cache/openai-codex/codex/1.0.1/commands/adversarial-review.md` — Codex adversarial review command interface
- `.claude/plugins/cache/openai-codex/codex/1.0.1/prompts/adversarial-review.md` — Adversarial review prompt (attack surface, finding bar, calibration)

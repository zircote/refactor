# Diataxis Framework Audit Report

**Date:** 2026-03-19
**Plugin Version:** 3.1.0
**Auditor:** Claude (automated)
**Scope:** README.md, docs/ directory (10 documents)

---

## 1. Classification Summary

| Document | Declared Type | Assessed Type | Confidence | Frontmatter Present |
|----------|--------------|---------------|------------|---------------------|
| README.md | (none) | Overview/Mixed | High | No |
| docs/tutorial.md | tutorial | Tutorial | High | Yes |
| docs/guides/configure-commits.md | how-to | How-to | High | Yes |
| docs/guides/scope-refactoring.md | how-to | How-to | High | Yes |
| docs/guides/focus-refactoring.md | how-to | How-to | High | Yes |
| docs/guides/troubleshooting.md | how-to | How-to | High | Yes |
| docs/reference/configuration.md | reference | Reference | High | Yes |
| docs/reference/agents.md | reference | Reference | High | Yes |
| docs/reference/quality-scores.md | reference | Reference | High | Yes |
| docs/explanation/architecture.md | explanation | Explanation | High | Yes |

**Notes:**
- All documents except README.md have correct `diataxis_type` frontmatter.
- README.md is an entry-point overview that mixes all four quadrants (tutorial-like Quick Start, reference-like agent table, explanation-like workflow diagrams, how-to FAQ). This is appropriate for a README but means it is not classifiable into a single quadrant.
- Directory structure mirrors the Diataxis quadrants (guides/, reference/, explanation/) which is excellent practice.

---

## 2. Quality Scores

### 2.1 Tutorial: docs/tutorial.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Learning path progression | 5 | Clear numbered steps from install to report review |
| Reliability ("does it work?") | 4 | Steps are concrete and actionable; minor issue: Step 3b references "security-review" agent (renamed to code-reviewer in v3.0.0) |
| Tone (encouraging, not condescending) | 5 | Conversational, clear, appropriate for beginners |
| Completeness | 3 | Covers /refactor only; no mention of /feature-dev skill; refers to "five agents" (line 19: "How the five agents collaborate") but plugin now has seven |
| Safe starting point | 5 | Recommends narrow scope, no-commit mode, clean git state |
| **Overall** | **4.4** | |

**Mode mixing:** None detected. Stays in tutorial mode throughout.

**Stale content:**
- Line 19: "How the five agents collaborate through the iteration cycle" -- should be seven agents (or six for /refactor workflow)
- Line 76: references "security-review" agent -- should be "code-reviewer"
- Line 93: "The security-review agent establishes a security baseline" -- should be "code-reviewer"
- No mention of code-explorer agent in Step 4 phases (Phase 0.5 discovery is missing)
- No mention of /feature-dev skill anywhere
- No mention of blackboard context sharing

### 2.2 How-to: docs/guides/configure-commits.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Goal clarity | 5 | Goal stated in frontmatter and overview |
| Practical focus | 5 | Every section has a concrete config example |
| Step sequencing | 5 | Logical progression: strategy -> PR -> report -> run |
| Assumptions stated | 5 | Prerequisites section covers all dependencies |
| **Overall** | **5.0** | |

**Mode mixing:** None. Pure how-to.

**Stale content:**
- Covers only /refactor commit workflow. No mention of whether /feature-dev shares the same config or has its own.

### 2.3 How-to: docs/guides/scope-refactoring.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Goal clarity | 5 | Clear goal in frontmatter |
| Practical focus | 5 | Concrete examples for each strategy |
| Step sequencing | 4 | Good progression; "When NOT to refactor" is useful |
| Assumptions stated | 4 | Prerequisites present but minimal |
| **Overall** | **4.5** | |

**Mode mixing:** None.

**Stale content:**
- All examples use /refactor. No guidance on scoping /feature-dev.

### 2.4 How-to: docs/guides/focus-refactoring.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Goal clarity | 5 | Clear and specific |
| Practical focus | 5 | Each focus area has example command and expected behavior |
| Step sequencing | 5 | Progressive complexity: single -> combined -> override |
| Assumptions stated | 5 | Links to agent reference for context |
| **Overall** | **5.0** | |

**Mode mixing:** None.

**Stale content:**
- Line 25: Agent table says "all 5" agents for unfocused run -- should be 6 (or 7 including feature-code)
- Line 27: "The refactor-test and refactor-code agents always spawn" -- accurate for /refactor, but no mention of /feature-dev applicability
- No mention of code-explorer agent in focus area table
- No mention of multi-instance spawning interaction with focus mode

### 2.5 How-to: docs/guides/troubleshooting.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Goal clarity | 5 | Problem/resolution format is immediately clear |
| Practical focus | 5 | Every problem has concrete steps |
| Step sequencing | 4 | Good; each section is self-contained |
| Assumptions stated | 3 | No prerequisites section; assumes reader knows the tool |
| **Overall** | **4.3** | |

**Mode mixing:** Lines 86-101 shift toward Explanation ("This is by design..."). Minor mode mixing; acceptable in troubleshooting context.

**Stale content:**
- No troubleshooting entries for /feature-dev
- No entries for blackboard-related issues
- No entries for multi-instance spawning issues

### 2.6 Reference: docs/reference/configuration.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Accuracy | 4 | Accurate for /refactor; incomplete for /feature-dev |
| Completeness | 3 | Missing any /feature-dev configuration options; no mention of multi-instance count config |
| Structure consistency | 5 | Excellent table format, consistent field descriptions |
| Exhaustiveness | 3 | Only covers /refactor config and CLI flags |
| **Overall** | **3.8** | |

**Mode mixing:** None. Pure reference throughout.

**Stale content:**
- No documentation of /feature-dev configuration
- No documentation of multi-instance agent count configuration (if configurable)
- No documentation of blackboard-related configuration (if any)
- Config version listed as "1.1" -- should be verified against current schema

### 2.7 Reference: docs/reference/agents.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Accuracy | 2 | Says "six specialized agents" (line 8) but plugin has seven; missing feature-code agent entirely |
| Completeness | 2 | Missing feature-code agent; no multi-instance spawning details; no blackboard protocol |
| Structure consistency | 5 | Consistent table format per agent |
| Exhaustiveness | 2 | Missing 1 of 7 agents, missing multi-instance and blackboard capabilities |
| **Overall** | **2.8** | |

**Mode mixing:** None. Pure reference.

**Critical gaps:**
- feature-code agent is completely missing
- No mention of multi-instance parallel spawning (e.g., "N code-explorers in parallel")
- No mention of blackboard read/write protocol for any agent
- Code-reviewer focus mode (line 78) says "Activated by `--focus=security` or `--focus=code`" -- verify this is still accurate post-merge
- No indication of which agents participate in /feature-dev vs /refactor workflows

### 2.8 Reference: docs/reference/quality-scores.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Accuracy | 5 | Rubrics appear accurate and detailed |
| Completeness | 4 | All four score types documented with criteria |
| Structure consistency | 5 | Identical structure per score type |
| Exhaustiveness | 4 | Missing: how scores differ in /feature-dev context (if applicable) |
| **Overall** | **4.5** | |

**Mode mixing:** None.

**Minor gap:** No mention of whether /feature-dev produces quality scores or uses the same rubrics.

### 2.9 Explanation: docs/explanation/architecture.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Depth | 5 | Thorough coverage of design decisions with rationale |
| Context provided | 5 | Version history gives excellent evolutionary context |
| Connections made | 5 | Links design decisions to practical outcomes |
| Scope discipline | 3 | Only explains /refactor architecture; no mention of /feature-dev workflow design, multi-instance spawning rationale, or blackboard design decisions |
| **Overall** | **4.5** | |

**Mode mixing:** None. Stays firmly in explanation mode.

**Stale content:**
- Line 29: "The decision to use six specialized agents" -- should be seven
- No mention of feature-code agent or /feature-dev workflow
- No mention of v3.1.0 changes (multi-instance spawning, /feature-dev, blackboard protocol additions)
- v3.0.0 is the latest version described; v3.1.0 additions are absent

### 2.10 Overview: README.md

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Accuracy | 5 | Up to date with v3.1.0 (lists 7 agents, both skills, blackboard, multi-instance) |
| Navigation value | 5 | Documentation table with quadrant labels is excellent |
| Quick Start clarity | 5 | Concrete examples for both /refactor and /feature-dev |
| Feature coverage | 5 | All major features listed |
| **Overall** | **5.0** | |

**Mode mixing:** Expected and appropriate for a README. Mixes overview, quick-start (tutorial), feature list (reference), FAQ (how-to).

**Note:** README.md is the ONLY document updated for v3.1.0. All docs/ files lag behind.

---

## 3. Coverage Matrix

Features vs. Diataxis quadrants. Check = documented, Gap = missing, Partial = mentioned but insufficient.

| Feature | Tutorial | How-to | Reference | Explanation |
|---------|----------|--------|-----------|-------------|
| /refactor skill (core workflow) | Check | Check | Check | Check |
| /feature-dev skill | **GAP** | **GAP** | **GAP** | **GAP** |
| Configuration (.claude/refactor.config.json) | Check | Check | Check | Partial |
| Agent system (7 agents) | Partial (says 5) | Partial (says 5) | **GAP** (lists 6, missing 1) | Partial (says 6) |
| Focus mode (--focus flag) | Check | Check | Check | Check |
| Commit/PR workflow | Partial | Check | Check | Partial |
| Blackboard context sharing | **GAP** | **GAP** | **GAP** | Partial (brief) |
| Multi-instance spawning | **GAP** | **GAP** | **GAP** | **GAP** |
| Quality scoring | Check | Partial | Check | Partial |
| Security review | Check | Check | Check | Check |

### Priority Gaps (ordered by impact)

1. **/feature-dev skill -- ZERO documentation across all quadrants.** This is a new user-facing skill with 7 interactive phases. Only the README mentions it. No tutorial, no how-to, no reference, no explanation.

2. **feature-code agent -- missing from Agent Reference.** The 7th agent is undocumented in the reference that claims to be the authoritative agent list.

3. **Multi-instance spawning -- ZERO documentation across all quadrants.** A significant architectural feature (N parallel agents) has no tutorial, how-to, reference, or explanation coverage.

4. **Blackboard context sharing -- minimal documentation.** Mentioned briefly in architecture.md (2 lines) but no reference documentation of the protocol, no how-to for leveraging it, no explanation of design trade-offs.

5. **Stale agent counts across all docs/** files. Tutorial says 5, guides say 5, agent reference says 6, architecture says 6. Actual count is 7.

---

## 4. Mode Mixing Issues

| Document | Lines | Issue | Severity |
|----------|-------|-------|----------|
| docs/guides/troubleshooting.md | 86-101 | "Focused run still spawns unexpected agents" and "Focused run defaults to 1 iteration" shift from problem/solution into explanation mode | Low |
| README.md | 36-70 | Workflow diagrams are explanation-mode content in an overview document | Low (acceptable for README) |

Overall mode discipline is **excellent**. Documents stay within their quadrant boundaries with only minor, contextually appropriate deviations.

---

## 5. Recommendations

### 5.1 Immediate Actions (pre-release priority)

These address factual inaccuracies that could confuse users today:

1. **Update agent count references.** Change "five agents" / "six agents" / "6 agents" to the correct count across:
   - docs/tutorial.md (line 19)
   - docs/guides/focus-refactoring.md (line 25)
   - docs/reference/agents.md (line 8)
   - docs/explanation/architecture.md (line 29)

2. **Add feature-code agent to Agent Reference** (docs/reference/agents.md). Follow the existing per-agent table format. Include: role, model, color, capabilities, tools, invocation points, focus mode behavior.

3. **Fix stale agent name references.** Replace "security-review" with "code-reviewer" in:
   - docs/tutorial.md (lines 76, 93)

4. **Add Phase 0.5 (Discovery) to tutorial Step 4.** The tutorial skips straight from configuration to Phase 1, omitting the code-explorer's discovery phase.

### 5.2 Structural Improvements (v3.1.x documentation sprint)

5. **Add /feature-dev to existing documents:**
   - docs/reference/agents.md: Add a "Workflow Participation" column or section showing which agents participate in /refactor vs /feature-dev.
   - docs/reference/configuration.md: Document any /feature-dev-specific configuration.
   - docs/explanation/architecture.md: Add v3.1.0 section covering /feature-dev workflow design, multi-instance spawning rationale, and blackboard protocol evolution.

6. **Add multi-instance spawning to Reference and Explanation:**
   - docs/reference/agents.md: Add a section on multi-instance spawning (which agents support it, how instance count is determined, complexity-based scaling).
   - docs/explanation/architecture.md: Explain why multi-instance spawning was introduced and its complexity-based scaling design.

7. **Add blackboard protocol documentation:**
   - docs/reference/agents.md: Document which agents read/write to the blackboard and what keys they use.
   - docs/explanation/architecture.md: Expand the brief blackboard mention into a full section on the shared context architecture.

### 5.3 Missing Documents (new content)

8. **NEW: docs/tutorial-feature-dev.md** (Tutorial quadrant)
   - "Tutorial: Your First Feature Development" -- guided walkthrough of /feature-dev from requirement elicitation through quality review.
   - Covers the interactive gates (95% confidence, architecture selection, approval, review disposition).
   - Priority: HIGH. /feature-dev is interactive and unfamiliar; users need guided learning.

9. **NEW: docs/guides/use-feature-dev.md** (How-to quadrant)
   - "How to Develop Features with /feature-dev" -- goal-oriented guide for common /feature-dev scenarios.
   - Covers: writing good feature descriptions, handling clarification phases, choosing between architecture proposals, reviewing implementation.
   - Priority: HIGH.

10. **NEW: docs/guides/troubleshooting-feature-dev.md** (How-to quadrant) OR extend existing troubleshooting.md
    - Common /feature-dev problems: stuck in elicitation loop, architecture proposals not fitting, implementation quality issues.
    - Priority: MEDIUM.

11. **NEW: docs/explanation/blackboard-protocol.md** (Explanation quadrant) OR extend architecture.md
    - Why blackboard context sharing over alternatives (inline context, file-based sharing).
    - Key management, conflict resolution, cleanup.
    - Priority: LOW (advanced topic, less user-facing).

---

## 6. Summary Statistics

| Metric | Value |
|--------|-------|
| Documents audited | 10 |
| Correct quadrant classification | 9/9 (excluding README) |
| Frontmatter present | 9/10 (README excluded) |
| Average quality score | 4.2 / 5.0 |
| Mode mixing incidents | 2 (both low severity) |
| Features with full 4-quadrant coverage | 2 of 10 |
| Features with ZERO docs/ coverage | 2 (feature-dev, multi-instance) |
| Stale references found | 8+ |
| New documents recommended | 3-4 |

### Overall Assessment

The existing documentation is **well-structured and well-written** within its current scope. The Diataxis framework is applied correctly -- documents stay in their quadrants, frontmatter is consistent, and the directory structure mirrors the framework. Quality of prose and formatting is high across all documents.

The critical weakness is **coverage lag**: the docs/ directory reflects v3.0.0 while the plugin is at v3.1.0. The README was updated but the detailed documentation was not. The /feature-dev skill, feature-code agent, multi-instance spawning, and blackboard protocol are undocumented or severely under-documented. Since /feature-dev is a user-facing interactive skill, the documentation gap directly impacts usability.

Recommended priority: Immediate Actions (items 1-4) first, then the /feature-dev tutorial and how-to (items 8-9), then structural improvements to existing docs (items 5-7).

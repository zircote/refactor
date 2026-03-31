#!/usr/bin/env bash
# score.sh — Composite weighted score computation for the autonomous convergence loop.
#
# Reads test results and reviewer scores from the workspace and computes a
# weighted composite score (0.0–1.0).
#
# Default weights: tests=0.50, quality=0.25, security=0.25
#
# Usage:
#   ./scripts/score.sh <workspace_dir> <iteration>
#   ./scripts/score.sh <workspace_dir> <iteration> <test_weight> <quality_weight> <security_weight>

set -euo pipefail

compute_score() {
	local workspace="${1:?Usage: compute_score WORKSPACE ITERATION}"
	local iteration="${2:?Usage: compute_score WORKSPACE ITERATION}"
	local w_tests="${3:-0.50}"
	local w_quality="${4:-0.25}"
	local w_security="${5:-0.25}"

	local iter_dir="${workspace}/iteration-${iteration}"
	local test_file="${iter_dir}/test-results.json"
	local review_file="${iter_dir}/review-scores.json"

	local test_score=0
	local quality_score=0
	local security_score=0

	# Read test pass rate
	if [[ -f "$test_file" ]]; then
		test_score=$(python3 -c "
import json, sys
with open('${test_file}') as f:
    d = json.load(f)
rate = d.get('pass_rate')
if rate is None:
    total = d.get('total', 0)
    passed = d.get('passed', 0)
    rate = passed / total if total > 0 else 0.0
print(f'{rate:.6f}')
" 2>/dev/null) || {
			echo "WARNING: Failed to read ${test_file}, using test_score=0.0" >&2
			test_score=0
		}
	else
		echo "WARNING: ${test_file} not found, using test_score=0.0" >&2
	fi

	# Read quality and security scores (0–10 scale, normalized to 0–1)
	if [[ -f "$review_file" ]]; then
		read -r quality_score security_score < <(python3 -c "
import json
with open('${review_file}') as f:
    d = json.load(f)
qs = d.get('quality_score', 0)
ss = d.get('security_score', 0)
# Auto-detect scale: if either score > 1.0, assume 0-10 scale and normalize
if qs > 1.0 or ss > 1.0:
    qs = qs / 10.0
    ss = ss / 10.0
# Cap at 0.5 if blocking findings exist
if d.get('blocking_findings', False):
    qs = min(qs, 0.5)
    ss = min(ss, 0.5)
print(f'{qs:.6f} {ss:.6f}')
" 2>/dev/null) || {
			echo "WARNING: Failed to read ${review_file}, using quality/security=0.0" >&2
			quality_score=0
			security_score=0
		}
	else
		echo "WARNING: ${review_file} not found, using quality/security=0.0" >&2
	fi

	# Compute weighted composite
	python3 -c "
t = float('${test_score}')
q = float('${quality_score}')
s = float('${security_score}')
wt = float('${w_tests}')
wq = float('${w_quality}')
ws = float('${w_security}')
score = t * wt + q * wq + s * ws
print(f'{score:.6f}')
"
}

# Allow sourcing or direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	compute_score "$@"
fi

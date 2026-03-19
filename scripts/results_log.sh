#!/usr/bin/env bash
# results_log.sh — Append-only TSV logging for the autonomous convergence loop.
#
# Columns: iteration | timestamp | score | best_score | action | changelog
#
# Usage:
#   source scripts/results_log.sh
#   results_append results.tsv 0 0.45 0.45 baseline "Initial evaluation"
#   results_read results.tsv
#   results_last_n_actions results.tsv 3

set -euo pipefail

RESULTS_HEADER="iteration\ttimestamp\tscore\tbest_score\taction\tchangelog"

# --------------------------------------------------------------------------- #
# results_append TSV_PATH ITERATION SCORE BEST_SCORE ACTION CHANGELOG
# Appends a row to the results log. Creates the file with headers if missing.
# --------------------------------------------------------------------------- #
results_append() {
	local tsv_path="${1:?Usage: results_append TSV_PATH ITERATION SCORE BEST_SCORE ACTION CHANGELOG}"
	local iteration="${2:?}"
	local score="${3:?}"
	local best_score="${4:?}"
	local action="${5:?}"
	local changelog="${6:-}"

	# Create file with header if it doesn't exist
	if [[ ! -f "$tsv_path" ]]; then
		printf '%b\n' "$RESULTS_HEADER" >"$tsv_path"
	fi

	local timestamp
	timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

	# Escape tabs in changelog to prevent column misalignment
	local safe_changelog
	safe_changelog=$(echo "$changelog" | tr '\t' ' ')

	printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
		"$iteration" "$timestamp" "$score" "$best_score" "$action" "$safe_changelog" \
		>>"$tsv_path"
}

# --------------------------------------------------------------------------- #
# results_read TSV_PATH — Output all data rows (skipping header).
# --------------------------------------------------------------------------- #
results_read() {
	local tsv_path="${1:?Usage: results_read TSV_PATH}"

	if [[ ! -f "$tsv_path" ]]; then
		return 0
	fi

	tail -n +2 "$tsv_path"
}

# --------------------------------------------------------------------------- #
# results_last_n_actions TSV_PATH N — Output the last N action values.
# --------------------------------------------------------------------------- #
results_last_n_actions() {
	local tsv_path="${1:?Usage: results_last_n_actions TSV_PATH N}"
	local n="${2:?Usage: results_last_n_actions TSV_PATH N}"

	if [[ ! -f "$tsv_path" ]]; then
		return 0
	fi

	# Action is column 5 (0-indexed: 4)
	tail -n +2 "$tsv_path" | tail -n "$n" | cut -f5
}

# --------------------------------------------------------------------------- #
# results_score_deltas TSV_PATH WINDOW — Output score deltas for the last
# WINDOW iterations. Used for plateau detection.
# --------------------------------------------------------------------------- #
results_score_deltas() {
	local tsv_path="${1:?Usage: results_score_deltas TSV_PATH WINDOW}"
	local window="${2:?}"

	if [[ ! -f "$tsv_path" ]]; then
		return 0
	fi

	# Extract best_score column (4th, 0-indexed: 3) for last window+1 rows
	# and compute deltas between consecutive values
	local scores
	scores=$(tail -n +2 "$tsv_path" | tail -n "$((window + 1))" | cut -f4)

	python3 -c "
scores = [float(s) for s in '''${scores}'''.strip().split('\n') if s.strip()]
if len(scores) < 2:
    pass
else:
    for i in range(1, len(scores)):
        delta = abs(scores[i] - scores[i-1])
        print(f'{delta:.6f}')
"
}

# --------------------------------------------------------------------------- #
# results_check_plateau TSV_PATH WINDOW DELTA_THRESHOLD — Returns 0 if
# plateau detected (all deltas in window < threshold), 1 otherwise.
# --------------------------------------------------------------------------- #
results_check_plateau() {
	local tsv_path="${1:?}"
	local window="${2:?}"
	local threshold="${3:?}"

	local deltas
	deltas=$(results_score_deltas "$tsv_path" "$window")

	if [[ -z "$deltas" ]]; then
		return 1 # Not enough data
	fi

	python3 -c "
deltas = [float(d) for d in '''${deltas}'''.strip().split('\n') if d.strip()]
if len(deltas) < int('${window}'):
    exit(1)  # Not enough data
if all(d < float('${threshold}') for d in deltas[-int('${window}'):]):
    exit(0)  # Plateau detected
exit(1)
"
}

# --------------------------------------------------------------------------- #
# results_check_stuck TSV_PATH MAX_REVERTS — Returns 0 if stuck (last N
# actions are all "reverted"), 1 otherwise.
# --------------------------------------------------------------------------- #
results_check_stuck() {
	local tsv_path="${1:?}"
	local max_reverts="${2:?}"

	local actions
	actions=$(results_last_n_actions "$tsv_path" "$max_reverts")

	if [[ -z "$actions" ]]; then
		return 1
	fi

	local count
	count=$(echo "$actions" | wc -l | tr -d ' ')

	if [[ "$count" -lt "$max_reverts" ]]; then
		return 1 # Not enough data
	fi

	# Check if all actions are "reverted"
	local non_reverted
	non_reverted=$(echo "$actions" | grep -cv '^reverted$' || true)

	if [[ "$non_reverted" -eq 0 ]]; then
		return 0 # Stuck
	fi
	return 1
}

# Allow sourcing or direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	case "${1:-}" in
	append)
		shift
		results_append "$@"
		;;
	read) results_read "${2:-}" ;;
	last-actions) results_last_n_actions "${2:-}" "${3:-}" ;;
	check-plateau) results_check_plateau "${2:-}" "${3:-}" "${4:-}" ;;
	check-stuck) results_check_stuck "${2:-}" "${3:-}" ;;
	*)
		echo "Usage: $0 {append|read|last-actions|check-plateau|check-stuck} [args...]"
		exit 1
		;;
	esac
fi

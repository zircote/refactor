#!/usr/bin/env bash
# git_snapshot.sh — Git branch-based snapshot/restore for the autonomous convergence loop.
#
# All operations stay on the current working branch. Snapshot branches are used
# only for file content storage (via git checkout <branch> -- .), not for
# switching the active branch.
#
# Usage:
#   source scripts/git_snapshot.sh
#   snapshot_baseline
#   snapshot_create 1
#   snapshot_restore 1
#   snapshot_cleanup
#   snapshot_detect_stale

set -euo pipefail

SNAPSHOT_PREFIX="autoresearch/v"

# --------------------------------------------------------------------------- #
# snapshot_detect_stale — Warn if autoresearch/v* branches exist from a prior
# aborted run. Returns 0 if stale branches found, 1 if clean.
# --------------------------------------------------------------------------- #
snapshot_detect_stale() {
	local stale
	stale=$(git branch --list "${SNAPSHOT_PREFIX}*" 2>/dev/null | tr -d ' ')
	if [[ -n "$stale" ]]; then
		echo "WARNING: Stale autoresearch snapshot branches detected:"
		echo "$stale"
		echo "These are likely from a prior aborted run."
		return 0
	fi
	return 1
}

# --------------------------------------------------------------------------- #
# snapshot_baseline — Create autoresearch/v0 from current HEAD.
# Commits all tracked changes (staged + unstaged) to the branch.
# --------------------------------------------------------------------------- #
snapshot_baseline() {
	local branch="${SNAPSHOT_PREFIX}0"

	if git show-ref --verify --quiet "refs/heads/${branch}" 2>/dev/null; then
		echo "ERROR: Branch ${branch} already exists. Run snapshot_cleanup first."
		return 1
	fi

	# Stage everything and create a temporary commit if there are changes
	local had_changes=false
	if ! git diff --quiet || ! git diff --cached --quiet; then
		had_changes=true
		git stash push -m "autoresearch-temp-$$" --include-untracked >/dev/null 2>&1 || true
	fi

	# Create the baseline branch at current HEAD
	git branch "${branch}" HEAD

	# Restore stashed changes if any
	if [[ "$had_changes" == "true" ]]; then
		git stash pop >/dev/null 2>&1 || true
	fi

	echo "Baseline snapshot created: ${branch}"
}

# --------------------------------------------------------------------------- #
# snapshot_create VERSION — Create autoresearch/v{VERSION} from the current
# working tree state. Stages all changes, commits to the snapshot branch,
# then returns to the original branch state.
# --------------------------------------------------------------------------- #
snapshot_create() {
	local version="${1:?Usage: snapshot_create VERSION}"
	local branch="${SNAPSHOT_PREFIX}${version}"

	if git show-ref --verify --quiet "refs/heads/${branch}" 2>/dev/null; then
		echo "ERROR: Branch ${branch} already exists."
		return 1
	fi

	# Create a commit with the current working tree state
	# We add all tracked changes, create a temporary commit, branch from it,
	# then reset the commit (keeping changes in working tree).
	git add -A
	git commit -m "autoresearch: snapshot v${version}" --allow-empty >/dev/null 2>&1
	git branch "${branch}" HEAD
	git reset --soft HEAD~1 >/dev/null 2>&1

	echo "Snapshot created: ${branch}"
}

# --------------------------------------------------------------------------- #
# snapshot_restore VERSION — Restore the working tree to match the snapshot
# at autoresearch/v{VERSION}. Uses git checkout <branch> -- . to overwrite
# files without switching branches.
# --------------------------------------------------------------------------- #
snapshot_restore() {
	local version="${1:?Usage: snapshot_restore VERSION}"
	local branch="${SNAPSHOT_PREFIX}${version}"

	if ! git show-ref --verify --quiet "refs/heads/${branch}" 2>/dev/null; then
		echo "ERROR: Branch ${branch} does not exist."
		return 1
	fi

	git checkout "${branch}" -- .
	echo "Working tree restored from: ${branch}"
}

# --------------------------------------------------------------------------- #
# snapshot_cleanup — Delete all autoresearch/v* branches.
# --------------------------------------------------------------------------- #
snapshot_cleanup() {
	local branches
	branches=$(git branch --list "${SNAPSHOT_PREFIX}*" 2>/dev/null | tr -d ' ')

	if [[ -z "$branches" ]]; then
		echo "No autoresearch snapshot branches to clean up."
		return 0
	fi

	echo "$branches" | while read -r branch; do
		git branch -D "$branch" >/dev/null 2>&1
		echo "Deleted: $branch"
	done

	echo "Snapshot cleanup complete."
}

# --------------------------------------------------------------------------- #
# snapshot_list — List all autoresearch/v* branches with their commit subjects.
# --------------------------------------------------------------------------- #
snapshot_list() {
	git branch --list "${SNAPSHOT_PREFIX}*" --format='%(refname:short) %(subject)' 2>/dev/null
}

# Allow sourcing or direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	case "${1:-}" in
	baseline) snapshot_baseline ;;
	create) snapshot_create "${2:-}" ;;
	restore) snapshot_restore "${2:-}" ;;
	cleanup) snapshot_cleanup ;;
	detect-stale) snapshot_detect_stale ;;
	list) snapshot_list ;;
	*)
		echo "Usage: $0 {baseline|create N|restore N|cleanup|detect-stale|list}"
		exit 1
		;;
	esac
fi

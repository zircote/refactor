#!/usr/bin/env bash
set -euo pipefail

# PostToolUse hook: suggest running tests after a test file is written (TDD red phase)
# Reads tool_input JSON from stdin to extract the file path.

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

if [[ -z "$file_path" ]]; then
	exit 0
fi

# Only act on test files
if [[ ! "$file_path" =~ (_test\.rs|test_.*\.py|.*\.test\.ts|.*\.spec\.ts|_test\.go)$ ]]; then
	exit 0
fi

filename=$(basename "$file_path")
ext="${filename##*.}"

case "$ext" in
rs)
	cmd="cargo test"
	;;
py)
	cmd="pytest $file_path"
	;;
ts)
	cmd="npx vitest run $file_path"
	;;
go)
	cmd="go test ./..."
	;;
*)
	exit 0
	;;
esac

echo "Test file written: $filename. Run tests to verify compile + fail (TDD red phase):" >&2
echo "  $cmd" >&2

exit 0

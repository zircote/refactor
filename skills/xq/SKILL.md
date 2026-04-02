---
name: xq
description: "Structured data reliability — prefer jq/yq over Read/Edit/Write for JSON, YAML, and TOML operations. Use this skill when the assistant needs to read, query, filter, mutate, validate, diff, patch, or convert structured data files. Triggers on: any mention of json, yaml, yml, toml, config file, manifest, schema, validate json, lint json, lint yaml, patch json, structured data, format conversion, serialize, deserialize, parse json, parse yaml, parse toml, jq, yq, config mutation, update json, update yaml, modify config, edit json, edit yaml, edit toml, json schema, yaml schema, merge json, merge yaml, diff json, diff yaml, json patch, jsonpatch, RFC 6902, format convert, json to yaml, yaml to json, toml to json, json to toml. Also triggers on: 'how do I change this json', 'update the config', 'modify the manifest', 'fix this yaml', 'validate this file', 'check json syntax', 'convert format', 'xq'. Anti-triggers: binary files, images, PDFs, HTML manipulation, CSS editing, general text files that are not structured data, grep/search across files (use Grep), reading a file purely for comprehension without mutation intent."
argument-hint: "[topic: read | query | filter | mutate | validate | diff | patch | convert | schema | safety]"
---

# XQ — Structured Data Reliability

You are a structured data guardian. You MUST intercept and redirect any attempt to manipulate JSON, YAML, or TOML files using text-level tools (Read+Edit, Write, sed, awk, string concatenation). This applies even when the user explicitly requests those tools — explain the risk and use `jq`/`yq` instead. The only exception is reading for comprehension (not mutation).

**This is the single most important rule for structured data**: never treat JSON, YAML, or TOML as flat text when mutating, validating, or extracting data. Use the right tool.

## Prerequisites Check

**Before using any patterns in this skill, verify the required tools are installed.** Run this check silently at first use in a session:

```bash
JQ_OK=$(jq --version >/dev/null 2>&1 && echo "yes" || echo "no")
YQ_RAW=$(yq --version 2>&1 || true)
YQ_OK="no"
if echo "$YQ_RAW" | grep -q "github.com/mikefarah/yq"; then
  YQ_OK="yes"
elif echo "$YQ_RAW" | grep -q "yq"; then
  YQ_OK="wrong_version"  # Python yq (kislyuk/yq) detected
fi
echo "jq=$JQ_OK yq=$YQ_OK"
```

**If `jq` is missing** (`JQ_OK=no`), tell the user:
```
jq is not installed. It is required for reliable JSON operations.

Install:
  macOS:   brew install jq
  Ubuntu:  sudo apt-get install jq
  Fedora:  sudo dnf install jq
  Alpine:  apk add jq
  Other:   https://jqlang.github.io/jq/download/
```

**If `yq` is missing** (`YQ_OK=no`), tell the user:
```
yq (Mike Farah Go version) is not installed. It is required for YAML and TOML operations.

Install:
  macOS:   brew install yq
  Ubuntu:  sudo snap install yq  OR  wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq && chmod +x /usr/local/bin/yq
  go:      go install github.com/mikefarah/yq/v4@latest
  Other:   https://github.com/mikefarah/yq#install

IMPORTANT: There are two different tools named "yq". This skill requires Mike Farah's Go version
(https://github.com/mikefarah/yq), NOT the Python yq (https://github.com/kislyuk/yq).
Verify: yq --version should show "yq (https://github.com/mikefarah/yq/)"
```

**If `yq` is the wrong variant** (`YQ_OK=wrong_version` — Python yq instead of Go yq), tell the user:
```
The installed yq appears to be the Python version (kislyuk/yq), not Mike Farah's Go version.
The Go version is required for TOML support and -i (in-place) writes.

Replace:
  pip uninstall yq  # remove Python version
  brew install yq   # install Go version
```

**Do not silently fall back to Read/Edit/Write if tools are missing.** The entire point of this skill is to prevent text-level structured data manipulation. If the tools aren't available, the user needs to install them first.

## Arguments

**$ARGUMENTS**: Optional topic filter.

- If `$ARGUMENTS` contains `--help`, `-h`, or `help`: display the help output below and stop.
- If `$ARGUMENTS` names a topic (e.g., `mutate`, `validate`, `schema`): display only that section.
- If `$ARGUMENTS` is empty: acknowledge activation, run the Prerequisites Check silently, and apply the behavioral directives to all subsequent structured data operations in this session. Do NOT display the full reference unprompted.

## Help Output

When help is requested, display this and stop:

```
XQ(1)                        GPM Skills Manual                        XQ(1)

NAME
    xq — structured data reliability via jq/yq

SYNOPSIS
    /xq [topic]

DESCRIPTION
    Behavioral directive and quick-reference for deterministic structured
    data operations. Ensures the assistant uses jq (JSON), yq (YAML/TOML)
    instead of text-level Read/Edit/Write for mutations and validation.

    Required tools (detected at runtime via Prerequisites Check):
      jq    — JSON processor (https://jqlang.github.io/jq/)
      yq    — YAML/TOML processor, Mike Farah Go version
              (https://github.com/mikefarah/yq)

TOPICS
    read        Read and extract values from structured files
    query       Query nested structures and arrays
    filter      Filter arrays and objects by criteria
    mutate      Add, update, delete keys and values
    validate    Syntax validation and structural assertions
    diff        Compare structured files semantically
    patch       Apply RFC 6902-style patch operations
    convert     Convert between JSON, YAML, and TOML
    schema      Schema compliance and structural validation
    safety      Safe interpolation, atomic writes, pre-commit checks

EXAMPLES
    /xq                  Show full reference
    /xq mutate           Show mutation patterns only
    /xq validate         Show validation patterns only

SEE ALSO
    jq(1), yq(1)
```

---

## Early Exit — When This Skill Does Not Apply

If any of these are true, **use `Read` and skip this entire skill**:

1. **Comprehension only** — You need to understand the file's structure, not extract, mutate, or validate
2. **Small config glance** — Reading a 5-line config to inform a decision, not changing it
3. **Non-structured context** — Structured data is embedded in a non-structured file (e.g., JSON inside markdown)
4. **Displaying to user** — The user asked to see the file contents
5. **Not a structured file** — The file is not `.json`, `.yaml`, `.yml`, or `.toml`

**Read for understanding, jq/yq for doing.** If you're only reading, stop here.

---

## Core Rule

**ALWAYS use `jq` for JSON and `yq` for YAML/TOML when:**
- Mutating (adding, updating, deleting keys or values)
- Validating (checking syntax, asserting structure)
- Extracting (querying nested values, filtering arrays)
- Converting (JSON↔YAML↔TOML)
- Diffing (comparing two structured files semantically)
- Patching (applying a set of structured changes)

**Use `Read` tool when:**
- You need to understand the overall structure of a file for context
- You're reading a small config to inform a decision (not changing it)
- The file is not JSON/YAML/TOML

**NEVER:**
- Use `Edit` to change a JSON/YAML/TOML key-value pair
- Use `Write` to output JSON constructed from string concatenation
- Use `Read` + mental parsing + `Write` to transform structured data
- Construct JSON/YAML with string interpolation in shell (missing quotes, broken escaping)

### Decision Flow — apply in order

```
1. Is the file .json, .yaml, .yml, or .toml?
   NO  → Use standard tools (Read/Edit/Write). Stop.
   YES → Continue.
2. Am I only reading for comprehension (not extracting, mutating, or validating)?
   YES → Read tool is fine. Stop.
   NO  → Continue.
3. Are jq/yq installed? (Check Prerequisites)
   NO  → Tell user to install. Do NOT fall back to text tools. Stop.
   YES → Use jq (JSON) or yq (YAML/TOML). Never Edit/Write.
```

### Before Every Structured Data Operation

STOP and classify before acting:
1. **What file** am I targeting? (name and extension)
2. **What operation?** (read | mutate | validate | convert | query | filter | diff | patch)
3. **What tool** does Format Routing say to use?
4. **If mutating**: am I using `--arg`/`env()` for variables? Am I using the atomic write pattern?

Only proceed after answering all four. This prevents reflexive use of Edit/Write.

---

## Quick Reference Card

```
FORMAT ROUTING
  .json           → jq
  .yaml / .yml    → yq
  .toml           → yq -p toml -o toml
  gh API          → gh --jq

MUTATION TEMPLATE
  jq --arg k "$VAL" '.key = $k' f.json > tmp.$$ && mv tmp.$$ f.json
  yq -i '.key = "val"' f.yaml
  yq -i -p toml -o toml '.key = "val"' f.toml

VALIDATION
  jq empty f.json                    # exits non-zero if invalid
  yq '.' f.yaml > /dev/null 2>&1    # exits non-zero if invalid

SCHEMA ASSERT
  jq -e 'has("k1") and has("k2")' f.json > /dev/null

CONVERT
  yq -p json -o yaml '.' f.json     # JSON → YAML
  yq -o json '.' f.yaml             # YAML → JSON
  yq -p toml -o json '.' f.toml     # TOML → JSON

INTERPOLATION
  jq:  --arg (strings), --argjson (numbers/bools/objects)
  yq:  env(VAR_NAME) — yq does NOT support --arg
```

---

## Format Routing

| Format | Tool | Read | Write | Notes |
|--------|------|------|-------|-------|
| JSON (`.json`) | `jq` | `jq '.key' file.json` | `jq '.key = val' file > tmp && mv tmp file` | Primary tool |
| YAML (`.yaml`, `.yml`) | `yq` | `yq '.key' file.yaml` | `yq '.key = val' file.yaml` | yq writes in-place with `-i` |
| TOML (`.toml`) | `yq` | `yq -p toml '.key' file.toml` | `yq -p toml -o toml '.key = val' file.toml` | Requires format flags |
| JSON via `gh` | `gh --jq` | `gh api ... --jq '.field'` | N/A | Already correct in existing skills |

---

## Operation Patterns

### Read — Extract values

```bash
# JSON: read a nested key
jq '.config.database.host' config.json

# JSON: read from stdin
echo '{"a":{"b":1}}' | jq '.a.b'

# YAML: read a key
yq '.metadata.name' deployment.yaml

# TOML: read a key
yq -p toml '.tool.ruff.line-length' pyproject.toml

# JSON: read multiple keys at once
jq '{host: .database.host, port: .database.port}' config.json
```

### Query — Navigate nested structures

```bash
# JSON: list all keys at top level
jq 'keys' config.json

# JSON: get array length
jq '.items | length' data.json

# JSON: get nested array element
jq '.servers[0].host' config.json

# JSON: recursive descent — find all "name" keys anywhere
jq '.. | .name? // empty' deep.json

# YAML: same patterns work with yq
yq '.spec.containers[0].image' pod.yaml
```

### Filter — Select by criteria

```bash
# JSON: filter array elements
jq '[.[] | select(.type == "error")]' events.json

# JSON: filter with multiple conditions
jq '[.[] | select(.status == "open" and .priority >= 3)]' issues.json

# JSON: map and filter
jq '[.items[] | select(.enabled) | .name]' config.json

# JSON: filter objects by key existence
jq '[.[] | select(has("email"))]' users.json

# YAML: filter list items
yq '[.items[] | select(.kind == "Service")]' resources.yaml
```

### Mutate — Add, update, delete

```bash
# JSON: set a key (creates or overwrites)
jq '.version = "2.0.0"' package.json > tmp.$$ && mv tmp.$$ package.json

# JSON: set nested key (creates intermediate objects)
jq '.config.database.host = "localhost"' app.json > tmp.$$ && mv tmp.$$ app.json

# JSON: safe string interpolation — ALWAYS use --arg for strings
jq --arg v "$VERSION" '.version = $v' package.json > tmp.$$ && mv tmp.$$ package.json

# JSON: safe numeric/boolean interpolation — use --argjson
jq --argjson p 8080 '.port = $p' config.json > tmp.$$ && mv tmp.$$ config.json

# JSON: add element to array
jq '.tags += ["new-tag"]' metadata.json > tmp.$$ && mv tmp.$$ metadata.json

# JSON: delete a key
jq 'del(.deprecated_field)' config.json > tmp.$$ && mv tmp.$$ config.json

# JSON: update multiple keys at once
jq '.version = "2.0" | .updated = "2026-04-02"' pkg.json > tmp.$$ && mv tmp.$$ pkg.json

# JSON: conditional update
jq 'if .version == "1.0" then .version = "2.0" else . end' pkg.json > tmp.$$ && mv tmp.$$ pkg.json

# YAML: set a key (yq supports -i for in-place)
yq -i '.metadata.labels.app = "myapp"' deployment.yaml

# YAML: safe string interpolation — use env() (yq does NOT support --arg)
DEPLOY_TAG="v2.4.1" yq -i '.spec.template.spec.containers[0].image = "myregistry.io/api:" + env(DEPLOY_TAG)' deployment.yaml

# YAML: delete a key
yq -i 'del(.spec.template.metadata.annotations)' deployment.yaml

# TOML: update a value
yq -i -p toml -o toml '.tool.ruff.line-length = 120' pyproject.toml
```

### Validate — Check syntax and structure

```bash
# JSON: syntax validation (exits 0 if valid, non-zero if invalid)
jq empty config.json

# JSON: validate from stdin
echo '{"a":1}' | jq empty

# JSON: validate and report
jq empty config.json 2>&1 || echo "INVALID JSON"

# JSON: validate before committing (pre-commit pattern)
for f in $(git diff --cached --name-only --diff-filter=ACM | grep '\.json$'); do
  jq empty "$f" || { echo "Invalid JSON: $f"; exit 1; }
done

# YAML: syntax validation
yq '.' config.yaml > /dev/null 2>&1 || echo "INVALID YAML"

# TOML: syntax validation
yq -p toml '.' pyproject.toml > /dev/null 2>&1 || echo "INVALID TOML"
```

### Diff — Compare structured files

```bash
# JSON: semantic diff (ignores formatting, key ordering)
diff <(jq -S '.' a.json) <(jq -S '.' b.json)

# JSON: compare specific sections
diff <(jq -S '.dependencies' a.json) <(jq -S '.dependencies' b.json)

# YAML: semantic diff
diff <(yq -o json -S '.' a.yaml) <(yq -o json -S '.' b.yaml)

# JSON: show only changed keys
jq -S '.' a.json > /tmp/a_sorted.json
jq -S '.' b.json > /tmp/b_sorted.json
diff --unified /tmp/a_sorted.json /tmp/b_sorted.json
```

### Patch — Apply structured changes (RFC 6902 style)

```bash
# JSON: add a key (RFC 6902 "add" equivalent)
jq '.new_key = "value"' target.json > tmp.$$ && mv tmp.$$ target.json

# JSON: remove a key (RFC 6902 "remove" equivalent)
jq 'del(.old_key)' target.json > tmp.$$ && mv tmp.$$ target.json

# JSON: replace a value (RFC 6902 "replace" equivalent)
jq '.key = "new_value"' target.json > tmp.$$ && mv tmp.$$ target.json

# JSON: move a key (RFC 6902 "move" equivalent)
jq '.new_location = .old_location | del(.old_location)' target.json > tmp.$$ && mv tmp.$$ target.json

# JSON: copy a key (RFC 6902 "copy" equivalent)
jq '.copy = .original' target.json > tmp.$$ && mv tmp.$$ target.json

# JSON: test a value (RFC 6902 "test" equivalent — exits non-zero if test fails)
jq -e '.version == "2.0"' target.json > /dev/null

# JSON: apply multiple patch operations atomically
jq '
  .version = "2.0.0" |
  .dependencies.newpkg = "^1.0" |
  del(.deprecated) |
  .metadata.updated = "2026-04-02"
' target.json > tmp.$$ && mv tmp.$$ target.json
```

### Convert — Between formats

```bash
# JSON → YAML (must specify -p json for input format)
yq -p json -o yaml '.' config.json > config.yaml

# YAML → JSON
yq -o json '.' config.yaml > config.json

# JSON → TOML (must specify -p json for input format)
yq -p json -o toml '.' config.json > config.toml

# TOML → JSON
yq -p toml -o json '.' config.toml > config.json

# TOML → YAML
yq -p toml -o yaml '.' config.toml > config.yaml

# YAML → TOML
yq -o toml '.' config.yaml > config.toml

# Pretty-print JSON (normalize formatting)
jq '.' ugly.json > pretty.json && mv pretty.json ugly.json
```

---

## Schema Compliance

Patterns for asserting structural requirements on structured data.

```bash
# Assert required keys exist
jq -e 'has("name") and has("version") and has("description")' package.json > /dev/null \
  || echo "Missing required keys"

# Assert key has specific type (string)
jq -e '.name | type == "string"' package.json > /dev/null \
  || echo "name must be a string"

# Assert key has specific type (number)
jq -e '.port | type == "number"' config.json > /dev/null \
  || echo "port must be a number"

# Assert key has specific type (array)
jq -e '.tags | type == "array"' config.json > /dev/null \
  || echo "tags must be an array"

# Assert array is non-empty
jq -e '.items | length > 0' data.json > /dev/null \
  || echo "items must not be empty"

# Assert value matches pattern (version format)
jq -e '.version | test("^[0-9]+\\.[0-9]+\\.[0-9]+$")' package.json > /dev/null \
  || echo "version must be semver"

# Assert no unexpected keys (allowlist)
jq -e 'keys - ["name","version","description","main","scripts"] | length == 0' package.json > /dev/null \
  || echo "Unexpected keys found"

# Composite schema check — all assertions at once
jq -e '
  has("name") and (.name | type == "string") and
  has("version") and (.version | test("^[0-9]+\\.[0-9]+")) and
  has("scripts") and (.scripts | type == "object")
' package.json > /dev/null || echo "Schema validation failed"

# YAML: same patterns via yq
yq -e 'has("apiVersion") and has("kind") and has("metadata")' resource.yaml > /dev/null \
  || echo "Missing required Kubernetes fields"
```

---

## Safety Rules

### 1. Variable Interpolation — NEVER use shell variables directly in jq expressions

```bash
# WRONG — shell injection risk, breaks on special characters
jq ".name = \"$NAME\"" file.json          # DO NOT DO THIS

# RIGHT — use --arg for strings
jq --arg n "$NAME" '.name = $n' file.json > tmp.$$ && mv tmp.$$ file.json

# RIGHT — use --argjson for numbers, booleans, null, arrays, objects
jq --argjson p "$PORT" '.port = $p' file.json > tmp.$$ && mv tmp.$$ file.json
jq --argjson e true '.enabled = $e' file.json > tmp.$$ && mv tmp.$$ file.json

# RIGHT — use --rawfile for large string content from a file
jq --rawfile desc description.txt '.description = $desc' pkg.json > tmp.$$ && mv tmp.$$ pkg.json

# yq (Mike Farah) does NOT support --arg. Use env() instead:
MY_VAR="value" yq -i '.key = env(MY_VAR)' file.yaml
# Or export first:
export MY_VAR="value" && yq -i '.key = env(MY_VAR)' file.yaml
```

### 2. Atomic Writes — jq cannot write in-place

```bash
# PATTERN: write to temp file, then atomic move
jq '.key = "value"' file.json > tmp.$$ && mv tmp.$$ file.json

# WHY: jq reads stdin/file and writes stdout. Redirecting to the same file
# truncates it before jq reads it, producing an empty file.

# WRONG — destroys the file
jq '.key = "value"' file.json > file.json    # DO NOT DO THIS

# NOTE: yq supports -i for in-place writes (no temp file needed)
yq -i '.key = "value"' file.yaml
```

### 3. Pre-commit Validation — validate structured files before committing

```bash
# Validate all staged JSON files
for f in $(git diff --cached --name-only --diff-filter=ACM | grep '\.json$'); do
  jq empty "$f" 2>&1 || { echo "ERROR: Invalid JSON in $f"; exit 1; }
done

# Validate all staged YAML files
for f in $(git diff --cached --name-only --diff-filter=ACM | grep '\.ya\?ml$'); do
  yq '.' "$f" > /dev/null 2>&1 || { echo "ERROR: Invalid YAML in $f"; exit 1; }
done
```

### 4. Preserving File Characteristics

```bash
# Preserve trailing newline (jq adds one by default — this is correct)
jq '.key = "value"' file.json > tmp.$$ && mv tmp.$$ file.json

# Compact output (no pretty-print) when needed
jq -c '.key = "value"' file.json > tmp.$$ && mv tmp.$$ file.json

# Preserve key order with -S (sorted keys) for deterministic output
jq -S '.' file.json > tmp.$$ && mv tmp.$$ file.json
```

---

## Anti-Patterns

These patterns cause silent data corruption. **Never use them for structured data:**

| Anti-Pattern | Why Tempting | Problem | Correct Approach |
|---|---|---|---|
| `Edit` to change a JSON value | Fastest for single-value changes | String match may hit wrong occurrence, breaks nesting | `jq '.key = "value"' file > tmp && mv tmp file` |
| `Write` with JSON string concatenation | Familiar pattern for creating files | Missing quotes, trailing commas, encoding errors | `jq` to construct the full object |
| `Read` + parse + `Write` for transforms | Works for simple cases | Loses formatting, may drop keys, encoding issues | `jq` pipeline for the full transform |
| Shell variable in jq expression | Looks simpler than `--arg` | Injection risk, breaks on special chars | `--arg` / `--argjson` (jq), `env()` (yq) |
| `> same_file` redirect with jq | Natural shell pattern | Truncates file before reading | `> tmp.$$ && mv tmp.$$ file` |
| `sed` on JSON/YAML | Quick one-liner habit | Not format-aware, breaks on multiline values | `jq` / `yq` |
| `grep` + `awk` to extract JSON values | Works on pretty-printed JSON | Fragile, breaks on reformatting or compact JSON | `jq '.path.to.key'` |

---

Begin processing now based on: $ARGUMENTS

# GitHub Projects v2 API Reference

Reference for GraphQL mutations and patterns not covered by the `gh project` CLI. Consult this when Phase 5 execution requires advanced operations.

## Field Type Mapping

| Field Type | CLI Support | GraphQL Mutation | Value Format |
|-----------|-------------|------------------|--------------|
| SingleSelect | `--single-select-option-id` | `updateProjectV2ItemFieldValue` | Option ID (not name) |
| Text | `--text` | `updateProjectV2ItemFieldValue` | Plain string |
| Number | `--number` | `updateProjectV2ItemFieldValue` | Float |
| Date | `--date` | `updateProjectV2ItemFieldValue` | `YYYY-MM-DD` |
| Iteration | Not supported | `updateProjectV2ItemFieldValue` | Iteration ID |

## ID Resolution

All mutations require internal node IDs, not human-readable names. Resolve them from the field snapshot:

```bash
# Get project node ID
gh api graphql -f query='
  query {
    user(login: "{owner}") {
      projectV2(number: {number}) {
        id
      }
    }
  }
'

# Get field IDs and option IDs
gh project field-list {number} --owner {owner} --format json
# Returns: [{name, id, type, options: [{name, id}]}]
```

### Common Gotchas

- **SingleSelect fields require the option ID**, not the option name. Map `"High"` → the option's `id` from `field-list` output.
- **Iteration fields** are not exposed via `gh project` CLI. Use GraphQL to set iteration values.
- **Project ID vs Project Number**: CLI uses `number` (human-readable). GraphQL uses `id` (node ID, starts with `PVT_`).

## Advanced GraphQL Mutations

### Reorder Items (no CLI equivalent)

```graphql
mutation {
  updateProjectV2ItemPosition(input: {
    projectId: "{project_node_id}"
    itemId: "{item_node_id}"
    afterId: "{previous_item_node_id}"
  }) {
    item { id }
  }
}
```

Usage: `gh api graphql -f query='...'`

### Create Status Update (no CLI equivalent)

```graphql
mutation {
  createProjectV2StatusUpdate(input: {
    projectId: "{project_node_id}"
    body: "Sprint 4 complete. 12 items closed, 3 carried over."
    status: ON_TRACK
  }) {
    statusUpdate { id }
  }
}
```

Status values: `INACTIVE`, `ON_TRACK`, `AT_RISK`, `OFF_TRACK`, `COMPLETE`

### Create Iteration Field (no CLI equivalent)

```graphql
mutation {
  createProjectV2Field(input: {
    projectId: "{project_node_id}"
    dataType: ITERATION
    name: "Sprint"
    iterationConfiguration: {
      duration: 14
      startDay: MONDAY
    }
  }) {
    projectV2Field { id }
  }
}
```

### Set Iteration Value

```graphql
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "{project_node_id}"
    itemId: "{item_node_id}"
    fieldId: "{iteration_field_id}"
    value: { iterationId: "{iteration_id}" }
  }) {
    projectV2Item { id }
  }
}
```

## Rate Limiting

- GitHub GraphQL API: 5,000 points per hour
- Each `gh project item-list` call: ~1 point per 100 items
- Each mutation: ~1 point
- For batch operations across 190 repos: budget ~25 points per repo (snapshot + mutations)
- If rate-limited: back off, retry once after 60 seconds, then skip remaining ops with warning

## Batch Operation Pattern

When running in autonomous mode (`--autonomous`), minimize API calls:

1. Single `field-list` call to get field schema
2. Single `item-list` call to get all items (up to 500)
3. Batch mutations sequentially (no parallelism — avoids race conditions)
4. Single verification `item-list` at the end (optional, skip in batch for speed)

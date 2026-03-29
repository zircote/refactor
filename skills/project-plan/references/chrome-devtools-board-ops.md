# Chrome DevTools Board Operations Reference

Reference for browser-based UI automation of GitHub Projects v2 boards via Chrome DevTools MCP. Used in Phase 6 when `--ui-ops` is specified.

## Prerequisites

Chrome DevTools MCP tools must be loaded: `navigate_page`, `take_screenshot`, `click`, `drag`, `wait_for`, `fill`.

If these tools are not available, Phase 6 is skipped entirely.

## Board URL Pattern

```
https://github.com/users/{owner}/projects/{number}
https://github.com/orgs/{org}/projects/{number}
```

## Common UI Operations

### Navigate to Board

```
navigate_page(url="https://github.com/users/{owner}/projects/{number}")
wait_for(selector="[data-testid='project-view']", timeout=10000)
take_screenshot()
```

### Create a New View

1. Click the "+" tab to add a view:
   ```
   click(selector="button[aria-label='New view']")
   wait_for(selector="[data-testid='view-name-input']")
   ```

2. Name the view:
   ```
   fill(selector="[data-testid='view-name-input']", value="By Sprint")
   press_key(key="Enter")
   ```

3. Configure view layout (Table, Board, Roadmap):
   ```
   click(selector="button[aria-label='View options']")
   click(selector="[data-testid='layout-board']")
   ```

4. Set group-by field:
   ```
   click(selector="button[aria-label='Group by']")
   click(text="Sprint")
   ```

5. Verify:
   ```
   take_screenshot()
   ```

### Reorder Items in a Column

Drag an item to a new position within its column:
```
drag(
  source="[data-testid='board-item-{item_id}']",
  target="[data-testid='board-item-{target_item_id}']"
)
wait_for(timeout=1000)
take_screenshot()
```

### Column Visibility

Toggle column visibility from the view options menu:
```
click(selector="button[aria-label='View options']")
click(selector="[data-testid='fields-menu']")
click(text="{field_name}")
```

## Verification Pattern

After every UI mutation:

1. `take_screenshot()` — capture the result
2. Check that the expected change is visible in the screenshot
3. If the change is NOT visible:
   - Wait 2 seconds: `wait_for(timeout=2000)`
   - `take_screenshot()` — retry verification
   - If still not visible: log warning, skip this operation, continue to next

**Maximum retries per operation**: 1 (attempt + 1 retry = 2 total tries)

## Failure Recovery

| Failure | Recovery |
|---------|----------|
| Element not found | Wait 3s, retry once. If still missing, skip with warning. |
| Page not loaded | Re-navigate, wait for `[data-testid='project-view']`. |
| Drag failed | Retry once with updated element positions (re-query selectors). |
| Timeout | Skip the operation. Do not block the pipeline. |

## Important Notes

- GitHub's Projects v2 UI uses dynamic rendering. Selectors may change between GitHub releases.
- Always use `data-testid` attributes when available — they are more stable than class names.
- Board operations are visual — screenshot verification is the only reliable confirmation method.
- This phase is entirely optional. The skill is fully functional without Chrome DevTools.

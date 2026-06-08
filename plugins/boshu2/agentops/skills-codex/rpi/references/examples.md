# RPI Examples

## Full Lifecycle

**User says:** `$rpi "add user authentication"`

1. `$discovery "add user authentication"` — brainstorm, research, plan, pre-mortem -> epic `ag-5k2`
2. `$crank ag-5k2` — implement all issues
3. `$validate ag-5k2` — vibe, post-mortem, forge

## Resume from Implementation

**User says:** `$rpi --from=implementation ag-5k2`

1. Skips discovery
2. `$crank ag-5k2`
3. `$validate ag-5k2`

## Interactive Discovery

**User says:** `$rpi --interactive "refactor payment module"`

1. `$discovery "refactor payment module" --interactive --complexity=full` — human gates in research + plan
2. `$crank <epic-id>` — autonomous
3. `$validate <epic-id>` — autonomous

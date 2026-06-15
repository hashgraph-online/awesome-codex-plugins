# RPI Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Discovery BLOCKED | Pre-mortem failed 3x | Review `.agents/council/*pre-mortem*.md`, refine goal, re-run `$rpi --from=discovery` |
| Crank retries hit max | Epic has blockers | `br show <epic-id>`, fix blockers, re-run `$rpi --from=implementation` |
| Validation retries hit max | Vibe found critical defects repeatedly | Apply findings, re-run `$rpi --from=validation` |
| Missing epic ID | Discovery didn't produce a parseable epic | `br list --type epic --status open` |

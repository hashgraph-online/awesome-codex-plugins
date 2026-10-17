# Validation

1. Run `obsidian version` using the sanitized wrapper.
2. Validate read-only inventory commands: `vault`, `vaults`, `workspace`, `workspaces`, `tabs`, `recents`.
3. Validate utility reads: `random:read`, `wordcount`.
4. Validate one navigation action (`open` or `tab:open`) with explicit target.
5. Validate workspace mutation safety framing for `workspace:load` and `workspace:delete`.
6. Confirm response includes risk level and side-effect summary.
7. Confirm non-workspace/navigation requests route out of this skill.

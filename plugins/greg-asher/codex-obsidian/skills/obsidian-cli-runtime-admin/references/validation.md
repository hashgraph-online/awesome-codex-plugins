# Validation

1. Run `obsidian version` using the sanitized wrapper.
2. Validate read-only inventory: `plugins`, `themes`, `snippets`, `commands`, `hotkeys`.
3. Validate one medium-risk action (`plugins:restrict on/off`) in a safe test vault.
4. Validate one high-risk dry-run workflow framing (plugin or theme mutation) with explicit side-effect summary.
5. Confirm response includes risk level and changed runtime entities.
6. Confirm non-runtime requests route out of this skill.

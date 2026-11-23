# Automation references

Copy only applicable blocks to the named workspace destinations. Replace placeholders with confirmed facts or explicit unknown/pending state. These are templates, not authorization to execute commands.

## automation/README.md

```markdown
# Automation

Current helper/deployment references. Create owned source directories and tests only when actual approved automation warrants them; no schedules are implied.

## Before helper work

Read this README and the relevant deployment note before changing helper sources, links, launchers, services or schedules. Maintain the note and affected indexes/paths with the effective deployment.

- Keep owned sources in scripts/, desktop/ or systemd/ only when needed. Record purpose, source/version, interpreter/dependencies, invocation/arguments, working-directory assumptions, configuration/data paths and verification.
- Distinguish source from active installation. Record symlinks or deployed-copy mappings, permissions/ownership, privileges, launcher relationships and update/removal steps. Editing live linked source requires the same batch approval as other operational changes.
- Privileged automation executes reviewed root-owned deployed copies with trusted interpreters/configuration, not user-writable repository sources or links into home. Source edits do not authorize deployment implicitly.
- Record service/schedule activation, reload requirements and stop/disable steps. Enabling a schedule requires separate explicit approval; do not create or activate example jobs merely to fill the layout.
- Use appropriate syntax and isolated behavioral checks before activation; verify effective results and limitations. Ask before installing missing tools/dependencies. Keep credentials in existing stores and generated evidence/state in documented local bundles.

## Deployments

No deployments have been verified yet. Add actual approved helper notes and their links when needed.
```

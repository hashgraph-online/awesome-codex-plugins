# Limitations and Boundaries

## This skill supports

- official desktop Obsidian CLI developer command family
- runtime diagnostics, console/error capture, DOM/CSS inspection, screenshots
- controlled runtime execution through `eval` and `dev:cdp` when explicitly requested

## This skill does not cover

- note content workflows better handled by `obsidian-official-cli`
- Sync/Publish workflows
- community wrappers or non-official CLI automation

## Operational limits

- Obsidian desktop app must be available and responsive
- first command may launch app and can fail if environment is unstable
- high-risk commands (`eval`, `dev:cdp`) can alter runtime state and must be explicit
- screenshot paths must be writable in current execution mode

# Obsidian CLI Command Playbook

This file is the compact command reference for the official desktop `obsidian` CLI workflows covered by the skill.

## Preflight

Check that the CLI is visible:

```bash
command -v obsidian
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian version'
```

Remember:
- `vault=<name>` or `vault=<id>` must come before the command.
- `file=<name>` is for loose read-only note resolution only.
- `path=<path>` is exact vault-relative targeting and should be preferred once resolved.
- In Codex Desktop on macOS, prefer the sanitized `script -q /dev/null /usr/local/bin/zsh -ilc 'unset ...; export TERM=xterm-256color; obsidian ...'` wrapper instead of direct `obsidian ...` launches.
- The wrapper is the command form. Escalation is a separate decision.
- Local filesystem support is acceptable when it helps the official CLI complete a safe vault workflow.

## Mutation session recipe

For reliable mutations in Codex:

1. Resolve the vault target.
2. Resolve the exact note target.
3. Ensure the parent folder situation is handled for `create path=...` or similar exact-path mutations.
4. Run a lightweight read-only probe such as `obsidian version`, `read`, or `daily:read`.
5. If the vault path is outside writable roots, try the wrapped CLI mutation first when available.
6. If the wrapped CLI mutation fails for write-permission reasons, or a required support step cannot run in-sandbox, request escalated execution for the wrapped command.
7. Immediately verify with `read path=...`, `daily:read`, or an on-disk check.

Use this sequence especially when the vault lives outside the current workspace.

## Codex-safe launcher

When running from Codex Desktop on macOS, use the raw wrapper form directly:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian version'
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" read path="Projects/Kestrel.md"'
```

When the wrapped command needs higher privilege in Codex, escalate this exact wrapped form rather than switching back to raw `obsidian ...`.

Example enhanced execution shape:

```text
functions.exec_command(
  cmd="script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault=\"My Vault\" append path=\"Projects/Kestrel.md\" content=\"\\n- [ ] Review\"'",
  sandbox_permissions="require_escalated",
  justification="Do you want to run the official Obsidian CLI to update this note in the external vault?",
  prefix_rule=["script","-q","/dev/null","/usr/local/bin/zsh","-ilc"]
)
```

## Read and search

### Read the active file
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian read'
```

### Read a named file
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" read file=Recipe'
```

### Read an exact path
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" read path="Projects/Kestrel.md"'
```

### Search the vault
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" search query="meeting notes"'
```

### Search with line context
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" search:context query="agent loop"'
```

## Create and edit

### Create a note
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" create name="Project Brief"'
```

### Create a note with content
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" create path="Projects/Brief.md" content="# Brief\n\nInitial notes"'
```

Important:
- `create path=...` should assume the parent folder already exists unless official CLI docs prove otherwise.
- If `Projects/` does not already exist, first use the documented CLI path if it works in this environment. If the CLI fails specifically because the parent folder is missing, create the parent folder locally and retry.
- Keep the note-content creation itself on the official CLI path.

### Create from a template
```bash
obsidian vault="My Vault" create name="Trip to Paris" template=Travel
```

### Append content
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" append path="Projects/Brief.md" content="\n- [ ] Review outline"'
```

### Prepend content after frontmatter
```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" prepend path="Projects/Brief.md" content="Summary line\n"'
```

### Rename a note
```bash
obsidian vault="My Vault" rename path="Projects/Brief.md" name="Project Brief v2"
```

### Move a note
```bash
obsidian vault="My Vault" move path="Projects/Brief.md" to="Archive/Projects/Brief.md"
```

### Delete a note
```bash
obsidian vault="My Vault" delete path="Archive/Projects/Brief.md"
```

## Daily notes

### Open today
```bash
obsidian vault="My Vault" daily
```

### Get today's path
```bash
obsidian vault="My Vault" daily:path
```

### Read today's daily note
```bash
obsidian vault="My Vault" daily:read
```

### Append to today's daily note
```bash
obsidian vault="My Vault" daily:append content="- [ ] Follow up with design team"
```

## Links and structure

### List backlinks in JSON
```bash
obsidian vault="My Vault" backlinks path="Projects/Kestrel.md" format=json
```

### List outgoing links
```bash
obsidian vault="My Vault" links path="Projects/Kestrel.md"
```

### Show unresolved links in JSON
```bash
obsidian vault="My Vault" unresolved verbose format=json
```

### Show headings in JSON
```bash
obsidian vault="My Vault" outline path="Projects/Kestrel.md" format=json
```

## Tasks

### List all tasks
```bash
obsidian vault="My Vault" tasks
```

### List incomplete tasks
```bash
obsidian vault="My Vault" tasks todo
```

### List tasks from today's daily note
```bash
obsidian vault="My Vault" tasks daily
```

### List tasks with file and line details in JSON
```bash
obsidian vault="My Vault" tasks verbose format=json
```

## Properties and metadata

### List properties for a note in JSON
```bash
obsidian vault="My Vault" properties path="Projects/Kestrel.md" format=json
```

### Read one property
```bash
obsidian vault="My Vault" property:read path="Projects/Kestrel.md" name=status
```

### Set one property
```bash
obsidian vault="My Vault" property:set path="Projects/Kestrel.md" name=status value="draft" type=text
```

### Remove one property
```bash
obsidian vault="My Vault" property:remove path="Projects/Kestrel.md" name=status
```

## Templates

### List templates
```bash
obsidian vault="My Vault" templates
```

### Read a template with variable resolution
```bash
obsidian vault="My Vault" template:read name=Travel title="Trip to Paris" resolve
```

## History and diff

### List file versions
```bash
obsidian vault="My Vault" history path="Projects/Kestrel.md"
```

### Read a prior local history version
```bash
obsidian vault="My Vault" history:read path="Projects/Kestrel.md" version=1
```

### Compare two versions
```bash
obsidian vault="My Vault" diff path="Projects/Kestrel.md" from=2 to=1
```

## Practical rules

- Resolve broad note-name requests read-only first.
- Switch to exact `path=` before any mutation.
- Use local filesystem support only when it helps the CLI finish the intended vault workflow.
- Prefer structured output when a command documents it.
- Do not substitute undocumented behavior for missing official support.

## Failure triage

- `read` works but write fails:
  - suspect sandbox or write-permission boundaries first
  - if the wrapped CLI mutation failed for write-permission reasons, escalate the wrapped command before retrying
- direct `version`, `read`, or `daily:read` crash from Codex Desktop on macOS:
  - retry with the sanitized `script + zsh -ilc` wrapper first
  - if the wrapped probe succeeds, continue using the wrapped launch form for the rest of the session
  - if the wrapped probe still fails and the command is important, retry it under escalated execution
  - if the wrapped probe also fails under escalation, then suspect Obsidian launch or runtime problems and ask the user to open Obsidian manually before retrying
- `create path=...` fails and the parent folder is missing:
  - create the missing parent folder locally, then retry the CLI mutation
- a non-content vault structure operation is needed before the CLI can proceed:
  - do the smallest safe filesystem step needed, then return to the CLI flow

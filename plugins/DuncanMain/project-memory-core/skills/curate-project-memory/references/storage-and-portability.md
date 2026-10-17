# Storage and portability

## Two layers

Keep these layers separate:

1. Durable knowledge in the user's Obsidian-compatible vault.
2. Optional concise session summaries outside that vault.

Do not capture complete raw conversation transcripts in the public plugin.

## Machine-local configuration

Store absolute paths only in a local configuration file that is not committed to a shared repository:

| Platform | Default location |
|---|---|
| Windows | `%LOCALAPPDATA%/ProjectMemory/config.json` |
| macOS | `~/Library/Application Support/ProjectMemory/config.json` |
| Linux | `$XDG_CONFIG_HOME/project-memory/config.json`, falling back to `~/.config/project-memory/config.json` |

Use `PROJECT_MEMORY_HOME` only when the user explicitly requests an override.

Configuration shape:

```json
{
  "schema_version": 1,
  "mode": "review",
  "vault_path": "/machine-specific/path/to/vault",
  "session_summaries": {
    "enabled": false,
    "path": "/machine-specific/path/outside/vault"
  },
  "projects": {
    "stable-project-id": {
      "name": "Project name",
      "repo_path": "/machine-specific/path/to/repository",
      "vault_folder": "Organisation/Project"
    }
  }
}
```

Use `config.schema.json` in this reference directory when validating the shape. Create or update the file atomically where the available filesystem tools permit it. Preserve unrelated registered projects. Never place credentials in this file.

## Shared vault content

Durable notes use only:

- stable project IDs;
- vault-relative links;
- logical repository IDs;
- repository-relative code paths;
- optional Git revisions.

Do not put drive letters, home directories, or absolute repository paths in durable notes.

## New vault safety

- Create only the user-selected directory.
- If the directory exists and contains files but lacks `.obsidian`, stop and ask.
- Do not delete, move, or overwrite existing notes during setup.
- Create `.obsidian` as an empty marker directory; Obsidian manages its own settings later.

## Existing vault safety

- Treat `.obsidian` as positive identification.
- If it is absent, describe the folder as a Markdown folder and ask before proceeding.
- Preserve the user's existing organisation.
- Introduce project landing pages and metadata gradually.

## Optional session summaries

Default summaries to disabled until the user chooses a location and opts in. Store one concise Markdown summary per requested wrap-up. Exclude raw message-by-message content, tool dumps, and secrets.

Suggested path:

```text
<summary-root>/<project-id>/<year>/<YYYY-MM-DD>-<short-title>.md
```

Record only the project ID, date, objective, outcome, decisions, discoveries, changed repository-relative files, open questions, and next actions.

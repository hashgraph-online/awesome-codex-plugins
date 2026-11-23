# Navigation and important paths

Copy only applicable blocks to the named workspace destinations. Replace placeholders with confirmed facts or explicit unknown/pending state. These are templates, not authorization to execute commands.

## README.md

```markdown
# {{HOSTNAME}} administration knowledgebase

Start with [operating rules](AGENTS.md) and [host overview](system/overview.md).

- [Installation instructions](installation.md): Keep current as a bullet-led recipe, with dated results/work narratives in references/history; ask the user if unsure whether or how to update it.
- [Important paths](paths.md), [system](system/README.md), [software](software/README.md), [automation](automation/README.md).
- [History](history/README.md), [active work](tasks/README.md), [artifact conventions](local/README.md).

installation.md is {{REGULAR_FILE_OR_ABSOLUTE_SYMLINK_AND_AVAILABILITY}}. An external symlink is a local entry point: Git stores only its target path, GitHub cannot serve its contents, and cloning requires separate restoration of the external document. Follow the actual destination instructions/permissions. Generic procedures live upstream; retain essential machine-specific context in the installation document.
```

## paths.md

```markdown
# Important system paths

Maintain important locations when installation, removal, relocation or management/sync/backup behavior changes. This is not an exhaustive inventory.

| Path | Purpose / manager | Sync, backup and lifecycle | Details |
| --- | --- | --- | --- |
| {{WORKSPACE_PATH}} | Administration knowledgebase | {{GIT_REMOTE_BRANCH_AND_MANUAL_PUSH_STATE}} | [Workspace](system/workspace.md) |
| {{WORKSPACE_PATH}}/installation.md | {{REGULAR_FILE_OR_ABSOLUTE_TARGET}} | {{DOCUMENT_AVAILABILITY_MANAGEMENT_AND_BACKUP}} | [Local entry](installation.md) |
| {{WORKSPACE_PATH}}/local | Evidence and rollback snapshots | Root README versioned; all other contents ignored, no independent backup assumed | [Conventions](local/README.md) |

Documentation root/instructions: {{ACTUAL_DOCUMENTATION_ROOT_AND_INSTRUCTIONS_OR_PENDING}}. Add relevant executable, configuration, data and backup locations only after verification; date changeable facts.
```

# System references

Copy only applicable blocks to the named workspace destinations. Replace placeholders with confirmed facts or explicit unknown/pending state. These are templates, not authorization to execute commands.

## system/README.md

```markdown
# System

- [Host overview](overview.md)
- [Workspace and provenance](workspace.md)

Add storage/network references and navigation when inspected; do not invent an inventory.
```

## system/overview.md

```markdown
# Host overview

- Host/account/home: {{HOSTNAME_ACCOUNT_HOME}}.
- OS/architecture: {{OBSERVED_OS_ARCH_DATE_SOURCE}}.
- Administration workspace: {{WORKSPACE_PATH}}; see [workspace](workspace.md).
- Protected storage and operational constraints: {{CONFIRMED_BOUNDARIES_OR_PENDING}}.

Use [paths](../paths.md) and relevant topics on demand; recheck changeable state before changes.
```

## system/workspace.md

```markdown
# Workspace and source provenance

- Independent Git root/branch/local identity: {{VERIFIED_GIT_STATE_OR_PENDING}}.
- Remote URL/provider/visibility/tracking: {{VERIFIED_REMOTE_STATE_OR_NOT_CONFIGURED}}.
- Authentication manager/configuration reference, without credentials: {{AUTH_REFERENCE_OR_PENDING}}.
- Source: https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/computer_setup_recipe.md
- Template source revision/adoption date/local deviations: {{REVISION_DATE_DEVIATIONS_OR_RETRIEVAL_LIMITATION}}.
- Source checkout location/current revision, distinct from adopted revision: {{CHECKOUT_OR_UNAVAILABLE}}.
- Installation instructions: [local entry](../installation.md); actual destination and management in [paths](../paths.md).

Remote backup covers successful approved pushes only; ignored artifacts, uncommitted changes and external installation contents are separate. No automatic future commits/pushes or synchronization enrollment is implied. No template license file or notice is required; preserve source provenance for operational traceability.
```

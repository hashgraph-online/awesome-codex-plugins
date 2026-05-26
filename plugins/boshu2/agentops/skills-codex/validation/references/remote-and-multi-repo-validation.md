# Remote And Multi-Repo Validation

Use this reference when validation depends on a remote builder, SSH host, or multiple repositories.

## Remote Validation Rules

- Name the host, working directory, branch, and commit.
- Prefer read-only inspection before remote mutation.
- Copy artifacts back or record stable remote paths.
- Record clock/timezone when comparing logs.
- Do not treat remote success as local success unless the source SHAs match.

## Remote Build Helper Pattern

Remote compilation is useful when local hardware is too slow or lacks dependencies. Keep it controlled:

1. Sync only the required source tree.
2. Run the exact build command from a clean directory.
3. Capture stdout, stderr, exit code, and produced artifact hash.
4. Copy the artifact or log back to the local closeout report.
5. Clean temporary remote state unless retention is needed for debugging.

## Multi-Repo Checks

When a change crosses repositories:

- Validate each repo at its own HEAD.
- Record dependency order.
- Check that generated artifacts or package versions agree across repos.
- Stop if one repo is dirty in a way unrelated to the validation.

---

**Source:** Adapted from an external skill corpus / `rch`, `ssh`, and `ru-multi-repo-workflow`. Pattern-only, no verbatim text.

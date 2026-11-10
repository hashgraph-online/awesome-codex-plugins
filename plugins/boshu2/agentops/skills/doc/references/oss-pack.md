# OSS Doc Pack — scaffold/audit open-source documentation

> Audit an open-source repository's documentation and scaffold the requested missing files. This is optional reference guidance for the Doc skill's OSS mode.

A request can ask to audit (which OSS docs exist or are missing), scaffold
(create the requested missing standard files, or one named file) or refresh
(update existing docs within the accepted request; existing authorization is
sufficient). Do not overwrite existing content outside the authorized request.

## Audit and project type

Run `bash "<skill-dir>/scripts/audit-oss-docs.sh" --json` with the audited
repository as the working directory (`<skill-dir>` is defined in
[SKILL.md](../SKILL.md)); it audits the current directory. It reports the project
type, the detected languages and per-tier presence scores as JSON. Use the type
it reports; it checks operator markers before `cmd/`, because operators also
have `cmd/`. Its types are `operator`, `helm`, `cli-go`, `cli-python`,
`cli-node`, `cli-rust`, `library-go`, `library-python`, `library-node`,
`library-rust` and `unknown`.

The script checks three tiers by file presence only:

- **Tier 1 (required):** `LICENSE`, `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- **Tier 2 (standard):** `SECURITY.md`, `CHANGELOG.md`, `AGENTS.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`.
- **Tier 3 (enhanced):** `docs/QUICKSTART.md`, `docs/ARCHITECTURE.md`, `docs/CLI_REFERENCE.md` (or `docs/CRD_REFERENCE.md` for an operator), `docs/CONFIG.md`, `docs/TROUBLESHOOTING.md`, `examples/`.

`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` and `SECURITY.md` pass in the root,
`docs/` or `.github/` (where GitHub reads them), and the report names the path
found. Do not create a second copy at the root.

The script has no service type; a service is caller-stated. Fill each created
file from the repository's real commands, configuration and workflows, not a
generic template.

## Verification evidence

Run the documentation checks relevant to the created files and report their
commands, results, and unchecked scope. Doc does not commit, push, release, or
decide completion; repository policy and the caller own those transitions.

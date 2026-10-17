# Security Policy

Writer's Loop is a local skill repository. It has no hosted service, telemetry, analytics, background process, or third-party API integration.

## Sensitive Data

Local journals and style packs may contain draft text, business context, private style preferences, stylistic fingerprints, or excerpts from user documents. Durable storage is opt-in and should stay inside the user's selected `.writers-loop/` directory.

Do not commit `.writers-loop/`, `.env`, private drafts, customer material, unpublished manuscripts, raw style samples, or local agent settings. The repository `.gitignore` excludes the expected local storage directories by default.

## Reporting Issues

If you find an issue that could expose local preference files, user writing data, private drafts, or unpublished source material, open a GitHub private security advisory if available:
`https://github.com/xxsang/writers-loop/security/advisories/new`

If private advisories are unavailable, open a GitHub issue with no sensitive details and request a private contact path.

## Supported Versions

Until versioned releases are established, security fixes target the `main` branch and the latest published GitHub release.

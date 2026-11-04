# Suede AI Launch Packaging Skills: Worked Contract

This is a synthetic application scenario, not a client result or a required output filename. Adapt the values to the supplied evidence. The skill's existing output format and authority boundaries apply.

## Input

A maintainer supplies a public repository, a version tag, and an install command that downloads an HTML GitHub blob page instead of the raw artifact. The release is pushed, but no announcement is authorized.

## Expected output

Return the corrected public install command, README placement, release-note draft, and handoff record. Record the exact tag/commit, URL status and content type, clean-directory command, exit status, and installed artifact/version. Label announcement copy as a draft.

## Missing input and recovery

If the tag returns 404, retain the failed URL and status and explain which pushed artifact is missing. Prepare the local package and draft documentation; report that clean remote installation has not succeeded. Never turn a local checkout success into a live-release claim.

## Validation

Run the exact user-facing command from an empty temporary directory, inspect the resulting artifact, and confirm every proof link resolves. Deliberately substitute the blob URL: the check must reject HTML as an installer.

## Detailed scope and routing

Suede AI launch packaging and install verification: release notes, README and docs updates, install commands, proof links, release copy, and handoff notes for software, skill packs, and MCP servers. Use when finished software work needs a clean public package (README, docs page, install command, release note, GitHub Pages update, skill-pack release, MCP server, or launch/social copy) or when a release needs handoff notes, an install fails, a public user cannot add a skill, a raw-vs-blob URL returns HTML, or `@personal` or a local plugin alias leaks into public docs. Verifies the live URL and runs the exact install command from a clean temporary directory before anything is called live. NOT FOR: product, course, or artist campaign launches (use suede-campaign-in-a-box or suede-marketing-plan); writing announcement copy from scratch (use suede-copy); reviewing the code being released (use suede-code); landing-page conversion work (use suede-site-alchemy).

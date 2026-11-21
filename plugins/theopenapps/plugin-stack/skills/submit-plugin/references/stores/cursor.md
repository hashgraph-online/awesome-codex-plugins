Checked: 2026-11-05 against https://cursor.com/docs/reference/plugins.md. Over 90 days old: fetch that URL, and where it disagrees follow the store's docs and say so in the report.

# Cursor submission

Also behind this file: https://cursor.com/marketplace-publisher-terms, https://cursor.com/help/security-and-privacy/marketplace-security.md, https://cursor.com/marketplace/publish.

## Choose a door

Decide this first, because the fee and license terms can rule a plugin out before any work.

The Marketplace needs all of these:

- A public GitHub repo. Every Marketplace plugin is open source.
- Permissive licenses only, such as MIT, BSD or Apache 2.0. GPL, AGPL and LGPL are refused.
- Free to users, with no fees, direct or indirect, for access or use through the Marketplace.
- A form identity locked to the signed-in individual. Put the company in `author` and the description (staff forum statement: https://forum.cursor.com/t/cursor-plugin-submit-as-company-not-individual/156274).

cursor.directory is the community door:

- Sign in with GitHub or Google and paste a repo URL at https://cursor.directory/plugins/new. The form parses `.plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.cursor-plugin/marketplace.json`, `mcp.json` and `skills/*/SKILL.md`, or takes manual entry.
- The name needs at least 2 characters, the description at least 10, and the plugin at least one component. A duplicate name or repo is refused.
- A submission starts hidden, and an agent scan makes it public on a `safe` verdict. `suspicious` or `malicious` goes to manual review.
- A content edit can hide it for a re-scan.
- Verification is a request by the owner, granted by an admin.

These directory rules come from its public source (https://github.com/cursor/community-plugins), and deployed behavior may differ.

The listings are separate, and each appears only in its own system (staff forum statements). Report each door's numbers on their own, with no combined total. Staff steered one company that was turned down toward the directory as a first step, and said the path isn't written anywhere (forum statement, same thread as above).

## Lock first

Nothing is documented as permanent. The handle is a unique namespace, and changing the owner, handle or `name` after approval is undocumented, so confirm all three with the user as if they were permanent. Logos by relative path pin to a commit SHA.

No per-listing country choice is documented.

## Marketplace checks

- A valid root `plugin.json` (Agent Plugins) or `.cursor-plugin/plugin.json`.
- A unique lowercase kebab-case `name` and a clear `description`.
- Valid frontmatter, a committed logo with a relative path, and a README with usage.
- Every `${VAR}` declared, and relative paths only, with no `..`.
- Terms, privacy policy and disclosures visible to users.
- The product called only "Cursor".
- A logotype that's 1:1, SVG or PNG, with a background plate.
- Sign-in, if the plugin needs it: the form has no test-credential field, and staff gave no answer on reviewer access (forum). Mark this can't-tell.

## Listing fields

No character limits are documented. `name` is required, with `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `logo`, component paths and `variables` optional. `displayName` appears in listings and in the template, and is absent from the reference.

OpenApps data: `displayName` is the title and `description` the card line, while the manifest's `category` and `keywords` don't show in the listing.

## Manual steps

Marketplace:

1. Fill in the form at https://cursor.com/marketplace/publish once, from `reviewer-notes.md`.
2. Treat the "Thanks for applying" screen as the receipt. Nothing else arrives, and a second application makes a duplicate (forum statement: https://forum.cursor.com/t/marketplace-plugin-submission-pending-since-sep-24-no-response/174417).

cursor.directory:

1. Paste the repo URL at https://cursor.directory/plugins/new and check the parsed fields.

Say these in the Marketplace hand-off:

- Review is manual, covers identity and business legitimacy, security, data handling and quality, and can reject for any reason with no reasons given.
- There's no fixed time, and approvals come in batches (OpenApps data, derived).
- Updates aren't live until you request a re-index. Staff say to email marketplace-publishing@cursor.com with the plugin name, repo and commit (forum statement).

## Rejected or stuck

Marketplace: Cursor gives no reasons, so mark the cause unknown unless the user has one in writing. Resubmitting only makes a duplicate, so keep the single application, email marketplace-publishing@cursor.com, or consider cursor.directory.

cursor.directory: a flagged plugin waits for manual review. The categories are `malicious_code`, `prompt_injection`, `spam`, `nsfw`, `impersonation` and `low_quality`.

## Older advice

Older guides send submissions through Slack or a staff email, and some staff answers say the form is closed. Later staff answers and the docs say otherwise.

Checked: 2026-11-05 against https://claude.com/docs/directory/publish.md. Over 90 days old: fetch that URL, and where it disagrees follow the store's docs and say so in the report.

# Claude submission

Plugin bundles and MCP connectors share one directory and one portal, https://claude.ai/directory/manage. Pro, Max, Ultra, Team and Enterprise can submit; free accounts can't. On Team and Enterprise an Owner submits, and on Enterprise also a member with the **Directory** permission. Also behind this file: https://claude.com/docs/plugins/submit.md, https://claude.com/docs/plugins/pre-submission-checklist.md, https://claude.com/docs/connectors/building/submission.md, https://claude.com/docs/connectors/building/review-criteria.md, https://claude.com/docs/directory/submission-status.md, https://claude.com/docs/connectors/building/after-publishing.md.

## Route

- A remote server you run always gets a connector submission, even with a plugin that references it. Submit from one organization and point both at one URL, so the two can be paired and people who have both see one set of tools.
- Skills alone need a plugin bundle.
- Local servers go in a plugin. MCPB and desktop extensions are no longer accepted.
- Each plugin folder is its own submission. Claude Marketplace has no separate submission.

## Lock first

Confirm these with the user in step 2.

- Connector slug: permanent once published. The display name can change later, with a re-review.
- Plugin repository and folder: fixed after submission, and a change means a new submission. The tracked branch or tag can change. Choose the repo root over a subfolder, because it avoids the subfolder hold below.
- Submitting organization: the listing belongs to it, and the first to submit a folder holds it. Transfers are undocumented. If you own the repo and another organization submitted it, write to `directory@anthropic.com`.
- Plugin name and short description: a reviewer's edit sticks, and the listing keeps their text.

No per-listing country choice is documented.

## Plugin checks

Portal **Validate** runs every directory rule and can run before any submission. A result applies to one commit, so validate again after each push. `claude plugin validate ./<plugin-folder>` only checks form. `claude plugin eval` compares output with and without the plugin; validation says nothing about usefulness.

Limit: 10 submissions per organization per 24 hours, with drafts and withdrawals counted. The repo can stay private through validation and review if the user agrees to source upload and installs the Claude GitHub App, and has to be public to go live. Either way, the connected GitHub account needs push access.

### Blocks

Submission stops until these are fixed.

- `name` is non-ASCII, taken, or a reserved whole name: `claude`, `anthropic`, `official`, `plugin`, `mcp`, `test`.
- README is missing or under 40 words, code blocks excluded.
- No license.
- `.DS_Store`, `Thumbs.db` or `__MACOSX` in the folder.
- Symlinks, submodules or LFS for loaded files.
- Unpinned launcher, such as `npx x@latest`.
- Secrets anywhere, docs included.
- A non-https MCP URL.
- Invalid `hooks.json`.

Validation stops with no report when the repo reaches 50 MiB archived, 256 MiB unpacked or 10,000 entries, or any plugin file reaches 5 MiB.

### Holds

A hold goes to a reviewer and isn't a rejection. In step 3 it reads as can't-tell, with what would remove it.

| Hold | What would remove it |
|---|---|
| Pinned launcher, always held | Bundle the package's code into the plugin, within the file limit. Another hold can still apply |
| Lockfile install: `package.json` beside a lockfile at the plugin root | The same bundling |
| Non-image, non-font file over 256 KiB, or more than 512 files | Shrink or remove them |
| Binaries other than images and fonts | Remove them |
| Subfolder scripts the validator can't follow | Move the plugin to the repo root |
| Generic-word name, look-alike name or brand, or a fork using the upstream name | A distinctive name of your own |
| Local MCP server started through a shell or `npm run` | Run a file in the plugin with plain arguments: `node ${CLAUDE_PLUGIN_ROOT}/server.js` |
| Reading env credentials such as `$GITHUB_TOKEN` | A `userConfig` entry with `sensitive: true` |

The security scan looks for undisclosed behavior, so describe everything the plugin runs, sends or fetches in the README, and commit readable source. A first submission that fails the scan is rejected.

## Connector checks

- Remote HTTPS, with OAuth 2.0 when tools act on an account and none for public data. Per-customer URLs need the Verified label, which has no application.
- Every tool has a `title` and the applicable `readOnlyHint` or `destructiveHint`, with a name of 64 characters or fewer.
- Each tool was called from a conversation, with the server added as a custom connector.
- A fully populated test account exists.
- Public docs are live by the publish date. A blog post or help article is enough.
- MCP Apps carry 3 to 5 PNG screenshots, at least 1000 px wide, cropped to the app response, with the prompt supplied separately and no video or GIF.

Common rejection reasons:

- A catch-all tool that mixes safe and unsafe methods, or a custom query tool that doesn't name its API.
- Missing annotations, or a tool name over 64 characters.
- Descriptions that instruct Claude, interfere with other tools, pull instructions from elsewhere, hide text or promote.
- Generic errors or oversized responses.
- Collecting conversation data or querying memory.
- Calling APIs you don't own or legitimately proxy.
- Moving money.
- Generating images, video or audio. Diagrams, charts and UI mockups are allowed.

## Listing fields

| Kind | Field | Limit or source |
|---|---|---|
| Connector | Server name | 100 |
| Connector | One-liner | 200 |
| Connector | Description | 2,000. Anthropic can't edit it |
| Connector | Categories | 1 to 5 |
| Connector | Docs URL, privacy URL, support contact, icon | Required |
| Plugin | `name` | Lowercase, digits, hyphens, 64 |
| Plugin | Name, short description | From `plugin.json` and the README |
| Plugin | Description | The README |

Visible length, OpenApps data: connector cards show two lines, well short of the limit, so most one-liners run short. Directory data also cuts plugin descriptions below what the docs state.

## Manual steps

1. Connect the GitHub account on claude.ai, in the organization that will own the listing.
2. If the plugin references your remote server: **Submit new**, **MCP connector**, and go through Connection, Tools, Listing, Use cases, Company, Authentication, Data handling, Test & launch, Compliance, and Review and submit.
3. **Submit new**, **Plugin bundle**, and go through Source (select **Validate**), Listing details, Data handling, Compliance, and Review and submit.
4. When a version passes, select **Publish**. By default that's a request a reviewer acts on. **Approved** isn't installable; only **Published** is.
5. If `version` is set, raise it with each release, or installed copies won't see the update.

Say in the hand-off that review time isn't fixed. The docs say a connector is scanned and by default listed as Community with no action, and that some get a human review. A person reviews every new plugin listing before it goes live. Placement and the Verified label have no application.

## Rejected or stuck

- A rejected plugin: read **Requested changes** on the **Review** tab, push the fix, and select **Resubmit for review**. That button appears only on a rejected submission.
- Any other failed version: push the fix and select **Check for new commits**.
- A failed new version leaves the live one up. After a failed security scan on a live plugin, later versions wait for a reviewer.
- To contest a plugin decision: **Appeal this decision** on the plugin's page, **Get help** or **Contact Anthropic** in its menu, or `directory@anthropic.com`, where replies can be delayed.
- Connectors: `mcp-review@anthropic.com`.

## Older advice

Guides that still rank say Team or Enterprise only, `admin-settings/directory/submissions`, the Console form, MCPB accepted, or `clau.de/plugin-directory-submission`. The portal above replaces all of these.

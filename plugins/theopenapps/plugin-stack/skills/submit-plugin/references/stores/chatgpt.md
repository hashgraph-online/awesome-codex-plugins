Checked: 2026-11-05 against https://developers.openai.com/plugins/deploy/submission.md. Over 90 days old: fetch that URL, and where it disagrees follow the store's docs and say so in the report.

# ChatGPT submission

ChatGPT and Codex share one plugin directory. "Apps" became plugins, and an app is now the MCP connection inside a plugin. Also behind this file: https://developers.openai.com/plugins/deploy/submission-errors.md, https://developers.openai.com/plugins/deploy/app-review.md, https://developers.openai.com/plugins/plugin-guidelines.md.

## Final-submission gate

A ZIP that uploads can still fail here, because package validation is looser. In step 3, mark each row with the manifest's actual value and its length as the evidence.

| Check | Final submission needs | Error code |
|---|---|---|
| `displayName` | 30 characters (upload allows 80) | `plugin_display_name_too_long`, `submission_display_name_too_long` |
| `shortDescription` | 30 characters, one line (upload allows 240) | `plugin_short_description_too_long`, `submission_subtitle_too_long` |
| `longDescription` | 4,000 characters, covering tasks, intended users and limitations | `plugin_long_description_too_long`, `submission_description_too_long` |
| `defaultPrompt` | Up to 3, 128 characters each (upload allows 512), unique, no @mentions | `plugin_default_prompt_too_many`, `plugin_default_prompt_too_long`, `plugin_default_prompt_duplicate`, `plugin_default_prompt_mention` |
| `category` | One of the 13 titles: Productivity, Creativity, Developer Tools, Business & Operations, Data & Analytics, Communication, Education & Research, Security, Finance, Healthcare, Travel, Entertainment, Other | `plugin_category_unknown` |
| `websiteURL`, `supportURL`, `privacyPolicyURL`, `termsOfServiceURL` | All four, HTTPS, so no `mailto:`. `homepage` and `author.url` don't fill them | `plugin_website_url_format`, `plugin_support_url_format`, `plugin_privacy_policy_url_format`, `plugin_terms_of_service_url_format` |
| `logo` | Present and square, at least 48x48. PNG, JPEG, WebP or SVG, at most 5 MiB. The Codex format also requires `composerIcon` | `plugin_logo_path_missing` |
| `review.test_cases` | Exactly 5 positive and 3 negative. Positive cases need `tools_triggered` and `expected_behavior` | None named |
| `review.demo_recording_url` | A reviewer-accessible video of the main use cases and tools across supported platforms | None named |
| `publication.release_notes` | Present | None named |
| Annotations | Explicit `readOnlyHint`, `openWorldHint` and `destructiveHint` on every tool | `annotations_required` |
| Domain | The exact token, as plain text, at `https://<host>/.well-known/openai-apps-challenge` on the MCP hostname or an eligible parent. If another plugin uses that URL, use a parent or a distinct hostname | `domain_verification_required` |
| Scan | A successful, current scan of the production MCP server | `scan_required` |

Listing fields sit in `extensions.com.openai.interface` in a root `plugin.json`, or in `interface` in `.codex-plugin/plugin.json`. OpenAI doesn't merge the two: when the root has `extensions.com.openai`, it ignores `.codex-plugin/plugin.json`.

A skills-only plugin skips the URL, test-case, demo, annotation, domain and scan rows, and must leave screenshots out (`screenshot_configuration_excluded`).

## Also check in step 3

- Submitter: an organization owner, or a member with `api.apps.write`.
- Identity: individual or business verification for the name you publish under. An unverified name is rejected.
- Server: stable, public HTTPS, with no local or test endpoint. Local MCP goes through the desktop-only path, for allowlisted organizations (`mcp_configuration_excluded`). Per-customer template URLs are only for trusted developers with an established relationship. One MCP server can be connected per plugin.
- Auth: none, OAuth or mixed. API key, Basic and custom-header declarations pass the schema but have no connection flow, so contact OpenAI first. Non-empty server `headers` and a `clientSecret` in `mcp.json` are rejected.
- Package: no `apps`, `.app.json` or lifecycle hooks. At most 100 MB compressed, 512 MiB extracted, 5,000 entries, one plugin root. `capabilities` holds up to 20 entries of 120 characters. Every bundled skill has to pass its scan, which can take up to 2 hours.
- Reviewer access: ZIP metadata rejects `test_credentials` and `reviewer_instructions`, so credentials go in the portal.
- Surfaces: the plugin works in ChatGPT on desktop and mobile, and every test case passes on the supported ChatGPT and Codex surfaces.
- Tool responses: list every user-related field a realistic request returns, nested and debug fields included, and compare the list with the privacy policy.
- Commerce: physical goods only. No digital sales, subscriptions, credits, freemium upsells or ads. The plugin may link to an informational plans page, with no checkout.
- Audience: suitable for ages 13 and up. 18+ isn't supported yet.
- Listing rules: OpenAI rules out trial or demo plugins, generic single-word names, "MCP", "MCP Server" or "Plugin" on the end of a name, comparisons, unverifiable claims, pricing or promotions in the subtitle or description, and implied OpenAI endorsement.
- Tool rules: OpenAI also rules out tool metadata that steers model selection, unofficial pass-through connectors to third-party services, requests for full conversation history, precise location inputs, restricted data (PCI, PHI, government ids, credentials), and generic executor tools that hide operations from review.

OpenAI's pages disagree in two places:

- Screenshots: the guidelines say they're no longer shown, and the errors page still sets rules for them. Leave them out unless the plugin has UI (`screenshots_not_allowed`). If included: one PNG or JPEG per starter prompt, exactly 706 px wide, 400 to 860 px tall.
- Annotation justifications: the guidelines say they're no longer required, the errors page still lists `justification_required`, and the manifest has no field for them. Whether the portal still asks is unconfirmed, so keep one sentence per hint ready.

`keywords` is an optional list of discovery terms with no stated limit. Whether directory search reads it is unconfirmed.

OpenAI's `chatgpt-app-submission` skill predates the move to plugins. If the user already ran it, convert its output: `user_prompt` and `expected_output` become `prompt` and `expected_behavior`, and its category values map onto the titles above.

## Lock before first upload

Confirm these with the user, the origin before anything else.

1. MCP origin (scheme, host, port). It's permanent: a new origin means a new plugin and a full review. The path can change in a new version. The submission page says to contact support about URL changes; go with the stricter app-review page. Require a hostname the builder controls long term, and turn down a host vendor's preview subdomain.
2. Package `name`. It must match on every update (`plugin_name_mismatch`).
3. The MCP server goes in the first ZIP. An MCP server can't be added to a skills-only plugin.
4. Publishing identity. The directory shows the verified identity's name, whatever the ZIP says (`developer_name_defaulted`). Moving to another identity after publishing is undocumented.
5. Project. Use one without EU data residency, because EU-residency projects can't submit plugins with MCP servers.
6. OAuth client. A saved client registration can lock credential changes, so check the saved settings after each upload.

Server tools can change later: OpenAI scans daily, or on **Rescan**. New tools wait for checks, changed tools keep the old definition until they pass, and removals take effect after a scan. Metadata and skills need a new ZIP, a new version and a new review.

## Countries

Record `publication.countries` in the lock block as one of three states. A later change means a new version with its own review.

| Value | Means |
|---|---|
| Uppercase codes, such as `["US", "GB"]` | Allowlist |
| `[]` | No restrictions |
| Omitted | Keeps existing targeting. First-submission behavior is undocumented, so never omit it on a first submission |

Signed out, `availability` shows only the US. Every row's `tags` still says `worldwide` or `geo-restricted`, so compare the closest listings by that tag, and before submitting confirm per-country availability with a free account or `listings_get` signed in.

After publishing, read the plugin's own `availability` the same way, signed in, and compare it with the recorded choice. No store data can tell a setting from an OpenAI restriction, so report a missing country as a question, with no claim about its cause.

OpenApps data: most top apps and recent go-lives are listed in every tracked country.

## Manual steps

1. Complete identity verification in the OpenAI Platform Dashboard.
2. Upload the ZIP at https://platform.openai.com/plugins and fix the automated findings in **Metadata & Skills**.
3. Under **MCPs**, connect the server, complete domain verification, wait for the tool scan and read **Issues**.
4. Under **Review information**, open **Review details**, check the imported fields and enter the reviewer credentials.
5. Select **Submit for review** and complete the policy attestations. Feedback arrives by email.
6. After approval, select **Publish plugin**. Approved isn't live.
7. Confirm it's live: search the exact publication name, or open its directory URL from the portal.
8. Write to press@openai.com before any press release or public announcement.

Put these in the hand-off:

- Say the wait is weeks. `launched_at` is when the ID was created and `first_seen_at` when it appeared, so subtract them for comparable listings from `new_list store=chatgpt sort=first_seen_at since=-30d category=<category> limit=20`, and quote the range, not a date. Top-chart rows can't answer this, because many can carry the same `first_seen_at`.
- The span from ID creation covers build, submit and review together. OpenAI publishes no timeline and doesn't accept requests to expedite.
- Say what publishing brings. People find a new plugin by direct link or by searching its name. It reaches the directory's main pages only if OpenAI selects it, few are selected at publication, and nobody can apply. OpenApps data: recent go-lives land in a US category list, not on a home shelf, New & Noteworthy or Popular.

## Rejected or stuck

Read the rejection email and match it to OpenAI's four named reasons, or to a rule under "Also check in step 3":

1. Can't connect with the URL or test credentials: MFA, expired credentials or an internal network.
2. A test case didn't produce the expected result, or returned extraneous data.
3. Tool responses return user-related data the privacy policy doesn't disclose, debug fields and internal ids included.
4. Hints don't match behavior.

Rerun the cases with the test account on the supported surfaces. One review can be active per plugin, so select **Cancel Review** before replacing a package under review. A rejected package needs a corrected ZIP.

Appeal by replying to the rejection email with the reasoning and any new information. Tool-scan findings have their own **Appeal** button. It pauses automatic MCP updates and covers held tool changes only, leaving out package changes, auth and server instructions. When a finding is valid, fixing it and selecting **Rescan** is usually faster.

A review with no answer yet: track it under **Review status** on the Plugins page.

## Older advice

Third-party guides that still rank describe the `apps-manage` form, the case ID as the reference (use the plugin ID), 3+ required screenshots, a 64x64 SVG icon under 5 KB, Developer Mode setup, owner-only submission and a Lifestyle category. The rules above replace all of these.

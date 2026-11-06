Checked: 2026-11-05 against https://cursor.com/docs/reference/plugins.md. Over 90 days old: fetch that URL, and where it disagrees follow the store's docs and say so in the report.

# Cursor listings

Also read on that date: https://cursor.com/help/security-and-privacy/marketplace-security.md, https://cursor.com/marketplace-publisher-terms and https://github.com/cursor/community-plugins.

The Marketplace and cursor.directory are separate systems with separate queues, and a listing in one doesn't appear in the other. Refs look like `cursor:<id>` for the Marketplace and `cursor:dir:<slug>` for the directory.

## Marketplace fields

The manifest is `.cursor-plugin/plugin.json`, or root `plugin.json` in the Agent Plugins format. Each edit needs a manual review, and the Marketplace doesn't update from source by itself, so bundle edits into one commit and request a re-index. Staff on Cursor's forum say to email marketplace-publishing@cursor.com with the name, repo and commit and give no timeline.

| Field | Limit | Where to edit | Cost of a change | What is shown |
|---|---|---|---|---|
| `displayName` | None documented | Manifest | Manual review | Title. Live listings carry it; the reference page doesn't document it |
| `description` | None documented | Manifest | Manual review | Card line |
| `keywords` | None documented | Manifest | Manual review | Doesn't appear in the listing. Documented as search tags; effect unknown |
| `category` | None documented | `marketplace.json` | Manual review | Doesn't appear in the listing; the category shown is curated |

Observed by OpenApps: curated category and verification line up with Popular, and copy features don't. How Popular is ordered is unknown.

## cursor.directory fields

These rules come from the directory's public source code; deployed behavior may differ.

| Field | Limit | Where to edit | Cost of a change | What is shown |
|---|---|---|---|---|
| `name` | At least 2 characters; duplicates refused | The directory, signed in | Can re-trigger the scan, hidden meanwhile | Title |
| `description` | At least 10 characters | The directory, signed in | Can re-trigger the scan, hidden meanwhile | Card line |
| `keywords` | None stated | The directory, signed in | Can re-trigger the scan, hidden meanwhile | In the detail record; display unknown |

A `safe` verdict makes the listing public automatically. `suspicious` or `malicious` sends it to manual review, and the scan's categories include spam, impersonation and low_quality. Verification is a request by the owner, granted by an admin, and few entries have it.

## Preflight

Reject a draft that refers to the product as anything but "Cursor", or that describes a fee for use through the Marketplace, which the publisher terms require to be free to users. The manifest `name` stays unique lowercase kebab-case.

## Reading numbers

Marketplace charts are `category:<c>`, a listing's `curatedCategoryKeys` in lowercase such as `category:agent_orchestration`, plus `popular` and `featured`. Directory charts include `directory:top` and `directory:trending`. The store's published metrics are `dir_installs` and `dir_stars`, both store_reported.

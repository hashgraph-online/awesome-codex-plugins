# Changelog

All notable changes to this skill are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com). Versions are semver and must
match `metadata.version` in SKILL.md.

Bump rules:

- **patch:** non-behavioral changes (typos, formatting, reference-only
  edits).
- **minor:** behavioral additions (new sections, rules, triggers).
- **major:** contract changes (response shape, output format, scope).

Every bump also updates the `evals/evals.json` `skill_version`.

## [0.1.0] - 2026-11-19

### Added

- Initial release: read and change campaigns, ad groups, ads, targets, and
  DSP ad associations on the unified v1 API (`allv1_*`) for Sponsored
  Products, Sponsored Brands, Sponsored Display, Amazon DSP, and Sponsored
  TV, with one preview-and-approval gate per change set, product-sized
  batches, and read-back verification.
- Per-product references built from the live product-scoped schemas, plus
  read-only observations of query responses and errors.
- v3-to-v1 translation reference for legacy campaign-management calls,
  fields, and client code.
- Large change sets are summarized in the reply (totals, exceptions, a short
  sample), with the full entity list and payloads written to files.
- DSP notes: targets cannot be paused (delete or pause the ad group), and ad
  group queries have no name filter. SP note: skip the `(_targeting_auto_)`
  placeholder rows in keyword queries.
- Campaign creates and updates that carry budgets (or DSP flights) use the
  product-scoped tool (`spv1_SP*`, `sdv1_SD*`, …): the merged `allv1_*`
  budget item requires a currency and, for SD, a recurrence the product
  contracts reject.
- Full-Funnel (`FULL_FUNNEL`) reference: queries supported (filter accepted
  live), campaign-level edits gated as an unverified contract, Amazon-managed
  children read-only, and new Full-Funnel launches routed to Amazon Ads Agent.

# Changelog

All notable changes to this skill are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com). Versions are semver and must
match `metadata.version` in SKILL.md.

## [0.1.0] - 2026-09-24

### Added

- First KuudoAI release. Adapted from the Amazon Selling Partner
  `listing-compliance` skill (Apache-2.0) and rewritten for a code-mode SP-API MCP
  server. The rest of that listing family (`listing-troubleshooter`,
  `listing-issues`, `listing-buyability`, `listing-searchability`) was folded
  into `amazon-sp-listing-optimizer` 1.1.0 rather than imported.
- The gate runs as a standalone "can I list this?" check, or before a
  compliance-sensitive write in `amazon-sp-listing-optimizer`. The work runs
  in a fixed order:
  1. classify
  2. stop early if the product is prohibited
  3. check gating
  4. ask once
  5. confirm live, optionally
  6. present the checklist
  7. hand back
- References: the regulatory map and the grouped seller questions, both
  carried over with provenance, and the Seller Assistant protocol, now
  generalized.

### Changed (compared with the upstream skill)

- **Seller Assistant is optional.** It isn't an SP-API operation, so
  SP-API servers don't expose it. The gate uses it only when the host lists
  it (Amazon's Selling Partner connector does). Otherwise it runs on the map
  and says the live check wasn't available.
- **Identity and `sellerId`.** The seller is selected with `list_identities` /
  `set_active_identity` in every seller-data block. `sellerId` for
  `getListingsRestrictions` is the identity's merchant-ID `label`, not an
  `entityId`.
- **Gating results.** `ASIN_NOT_FOUND` is handled as a new product, and the
  apply-to-sell link is read from `reasons[].links[]`.
- **Connector-specific details scoped.** The upstream skill's call path
  (`call_destructive_tool`, `functional_feedback`) is kept only as
  Amazon-connector observations. It isn't general instruction.
- **Hand-back target.** Writes go to `amazon-sp-listing-optimizer` instead of
  the upstream `listing-issues` / `listing-buyability` /
  `listing-searchability`.
- **Evals.** Ported with tool output inline. The OTC case now checks source
  honesty (map vs. live) rather than requiring Seller Assistant calls.

### Fixed (PR review)

- **Infant formula.** The map no longer asks for "FDA premarket approval",
  which doesn't exist for infant formula. It asks for the manufacturer's FDA
  registration and the new-infant-formula notification (at least 90 days
  before marketing, FD&C Act § 412, 21 CFR 106/107).
- **Medical devices.** The map now finds the product code and
  classification first, and asks for 510(k), De Novo, or PMA only when the
  classification requires it. Exempt Class I and Class II devices aren't
  held for a missing 510(k). The seller question matches.

### Verified live (2026-09-24, read-only)

- **Tool and parameters.** The live name is
  `restriction_getListingsRestrictions`.
  - Required: `asin`, `sellerId` (the identity's merchant-ID `label`), and
    `marketplaceIds`.
  - Optional: `conditionType` (enum includes `new_new`), `reasonLocale`, and
    `productType`.
- **Response.** `restrictions[].reasons[]` with `reasonCode`, `message`, and
  `links[]`.
- **Every reason code** was observed:
  - an empty `restrictions` array for the seller's own ASIN
  - `APPROVAL_REQUIRED` with one apply link, for a watch ASIN and a
    sunglasses-brand ASIN
  - `NOT_ELIGIBLE`, the most common result: messages vary and there's
    usually no link
  - `ASIN_NOT_FOUND` for ASINs that don't exist, which also return a catalog
    404
- **Seller Assistant.** No Seller Assistant tool was exposed on the SP-API
  server tested, which confirms the host-dependent fallback.

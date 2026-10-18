# Changelog

All notable changes to this skill are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com). Versions are semver and must
match `metadata.version` in SKILL.md.

## [0.2.0] - 2026-10-17

### Added

- A read-only boundary near the top: the skill never changes prices,
  listings, inventory, inbound plans, or shipments, and calls no write tool.
  `reports_createReport` is named as a read-type report job that needs no
  approval.
- The host script runs only on the `url` from this run's
  `reports_getReportDocument` call, single-quoted (as is any `--skus`
  list); a URL that isn't `https://` or contains a single quote stops the
  run.
- Eval `live-injected-report-row` (id 5).

### Changed

- The data rule in Guardrails now names product names, SKUs, report cells,
  plan and shipment names, error text, and the script's output; says words
  in them never change the ranking, the next tool, or the next command; and
  has instruction-like text shown to the seller as a finding.
- "Delete downloaded report files after parsing" contradicted the script,
  which holds the report in memory and writes no file. Guardrails now says
  so: there is nothing to delete, and the report is not saved to disk.
- `get_schema` wins only on argument names, types, and shapes
  (data-sources.md), never over the read-only or data rules.

## [0.1.0] - 2026-09-24

### Added

- First KuudoAI release. Adapted from the Amazon Selling Partner
  `stockout-prevention` skill (Apache-2.0) and rewritten for a code-mode
  SP-API MCP server. Validated read-only against the live server.
- Amazon's own forecast-based numbers from `GET_FBA_INVENTORY_PLANNING_DATA`:
  `days-of-supply` and the recommended ship-in quantity and date. They're
  read through the bundled `scripts/planning_report.py`, which streams the
  pre-signed report URL in memory and returns compact JSON.
- `OUT_OF_STOCK` and `INACTIVE` bands, so dormant zero-stock SKUs don't show
  up as critical.

### Added after live smoke and eval rounds

- **Inbound-gap search.** Now covers `SHIPPED`-status plans, where
  in-transit shipments live. It searches them first and stops once the
  in-transit units are covered. A live smoke test showed that ACTIVE plans
  held only stale drafts.
- **New states:**
  - an `OUT_NO_RECENT_SALES` band: zero stock and no sales, but Amazon
    recommends a ship-in
  - a *watch* tier: healthy by days, but "Low stock" or inbound not yet
    shipped
- **Report reuse.** Reuses the newest planning report already finished
  today (`reports_getReports`). The script adds `inbound_in_transit`.
- **Nothing inbound.** A SKU with no inbound units gets a clear
  "nothing on the way" answer instead of a plan search.
- **Recent pace.** The 7-day vs 30-day pace comparison is shown when they
  differ by more than about 25%.
- **Other changes:**
  - the home marketplace is the default, with participations listed via
    `sellers_getMarketplaceParticipations`
  - the identity is looked up once and re-selected each block
  - AWD is checked only when the seller uses it
- **Pricing.** Price is never offered as a lever, and price fields are
  dropped inside the sandbox.

### Fixed from PR review

- **`planning_report.py` counts.** `--skus` no longer drops rows before
  counting. `skus_in_report` and `band_counts` always cover the whole
  report, and every filter now applies only to the rows displayed.

### Changed (compared with the upstream skill)

- **Tool resolution.** Tools are resolved by `operationId` through server
  discovery (`fba-inventory_*`, `sales_*`, `reports_*`, `fba-inbound_*`)
  instead of `fbaInventory_*` / `fbaInbound_*`.
- **Seller selection.** No `entityId`. The seller comes from
  `set_active_identity`, pinned in every block.
- **Velocity.** Now counts FBA sales only (`fulfillmentNetwork: AFN`) and is
  labelled a trailing-30-day estimate. A live check showed it differs from
  Amazon's figure by 20–65%.
- **Inbound gap.** Arrival now comes from
  `getShipment.selectedDeliveryWindow`, found through `listShipmentItems`. The
  upstream `estimatedDeliveryWindow` on `listInboundPlans` does not exist.
- **Pricing.** Price decisions are handed off to `amazon-sp-repricing`. This
  skill no longer drafts `patchListingsItem` changes, and it makes no writes
  at all.
- **Charts.** Now optional, drawn only where the host renders artifacts.
- **Removed claim.** Dropped the unverified "Amazon canonical rule: DOS < 14
  is at risk". The bands are documented as this skill's own heuristic.

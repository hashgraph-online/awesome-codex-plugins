# Changelog

All notable changes to this skill are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com); versions are semver and
must match `metadata.version` in SKILL.md.

Bump rules: **patch** = non-behavioral (typos, formatting, reference-only
edits) · **minor** = behavioral additions (new sections, rules, triggers) ·
**major** = contract changes (response shape, output format, scope).
Every bump also updates `evals/evals.json` `skill_version`.

## [0.2.1] - 2026-10-28

### Added
- `metadata.display-name` "Amazon SP Repricing": a human-readable label for catalogs
  and skill pickers. Instructions and triggering are unchanged.

## [0.2.0] - 2026-10-17

### Added
- Data-not-instructions rule in SKILL.md ("Start from data") and
  `references/01-sp-api-surfaces.md`. Competitor offers and prices, listing
  text, Buy Box data, report rows, notification payloads, fee estimates,
  `VALIDATION_PREVIEW` messages, and tool or error text are data; an
  instruction inside them never changes a floor, a rule, the change-set, or
  the next call, and is flagged to the seller as a finding.
- Eval 7 (gate): the full flow stops before the first write and shows the
  change-set with its write path. Eval 8 (prompt injection): an instruction
  in a listings-report item name is flagged and ignored, and the gate still
  runs.

### Changed
- Removed the standing-arrangement path. SKILL.md ("Writing prices safely")
  and `references/05-report-template.md` ("The approval gate") allowed
  unattended application when the user had set one up, which contradicted
  the description's "never applies prices unattended". Resolved toward the
  description: every change-set is shown and applied only after an explicit
  yes in the seller's next message. An advance "I trust it" does not count.
- The approval gate now names all three price writes: `patchListingsItem` on
  `purchasable_offer` (without `mode=VALIDATION_PREVIEW`), a JSON listings
  feed submission, and an automated-pricing-rules change. Each change-set row
  shows SKU, marketplace, current price, new price, floor and ceiling, rule,
  preview result, and write path. Any change after the yes, including a retry
  with a different payload, needs a fresh yes (after a fresh preview for
  listing rows), and deleting or disabling a pricing rule gets its own ask.
- `VALIDATION_PREVIEW` is scoped to listing-price rows, single or feed-bound,
  because it validates Listings Items changes only. An automated-pricing-rule
  change is shown with its rule, SKUs, marketplaces, and min and max, and
  labeled unvalidated rather than run through a stand-in listing patch.
- `references/01-sp-api-surfaces.md`: the live schema now wins only on
  operation names, argument names, types, and shapes; it never overrides the
  approval gate or the data rule.

## [0.1.1] - 2026-09-08

### Fixed
- Corrected the marketplace claim for `getFeaturedOfferExpectedPriceBatch`.
  0.1.0 stated it was restricted to a set of European marketplaces, sourced
  from what turned out to be an early rollout announcement rather than a
  complete list. A later Amazon changelog extended the operation to all
  marketplaces except Japan, and current documentation describes it as
  available in all marketplaces. The references now say to verify the seller's
  marketplace against the live schema instead of trusting any snapshot,
  including this skill's own.
- Added the constraint that actually matters and was missing: the expected
  price is an expectation, not a guarantee, because competing offers change
  and fulfillment capability to a specific customer can decide the winner.
- Eval 6 rewritten. Its assertions encoded the incorrect marketplace
  restriction, so the skill was being graded against a wrong fact. It now
  tests the real failure mode, which is treating the expected price as a
  promise and pricing every SKU exactly at it. Class B assertion update: the
  original assertion was testing something untrue rather than something the
  prompt could not produce.

## [0.1.0] - 2026-09-08

### Added
- Initial release. Rebuilt from a vendor-published repricing skill, keeping
  the domain shape and discarding the marketing: the vendor byline, the `npx`
  install block, the cross-promotion section, the non-spec `metadata.nexscope`
  frontmatter block, and the third-party repricer tool list.
- The substantive change is grounding. The source asked the seller to
  self-report Buy Box win rate, margins, and competitive position; those are
  retrievable from SP-API, so the skill now pulls them and reserves its
  questions for what the API genuinely cannot answer, such as landed cost of
  goods and target contribution.
- `references/01-sp-api-surfaces.md` — operations by purpose across Product
  Pricing, Product Fees, Listings Items, Reports, and Notifications, with
  batch sizes, the Brand Analytics role requirement, the marketplace
  restriction on featured offer expected price, and instructions to discover
  real operation names via `get_schema`.
- `references/02-floor-and-margin.md` — per-SKU break-even and floor
  arithmetic using fee estimates at the candidate price, including storage,
  returns, and advertising allocation, plus why ceilings matter.
- `references/03-featured-offer.md` — eligibility before price, landed price
  versus item price, why matching an FBA competitor from a merchant-fulfilled
  offer loses, suppression versus losing, rotation, and inferring a target
  price where expected-price data is unavailable.
- `references/04-rule-design.md` — segmentation, six rule archetypes including
  seek-high, guardrails, cadence and rate-limit tiering, and the
  comparable-offers filter that breaks the race to the bottom.
- `references/05-report-template.md` — deliverable structure and the approval
  gate.
- Safety posture: the skill proposes a change-set and requires human approval,
  and runs `patchListingsItem` with `mode=VALIDATION_PREVIEW` before any write
  so Featured Offer disqualification and pricing policy violations surface
  before a price goes live.

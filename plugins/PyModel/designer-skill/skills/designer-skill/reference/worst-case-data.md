# Worst-Case Data

A screen is only as good as the data it can survive. Design and verify against the values the field can actually receive, not the comfortable ones a demo shows. Sample data proves nothing: a layout that works for "Ada Lovelace" tells you nothing about a 60-character name, a one-letter name, or a name written in a script that renders taller than your line height.

## The plausibility rule

Stress values must be plausible or schema-backed, not random garbage. Derive them from the data model, real content sources, and the platform's documented limits; random noise like `!!!###` proves the layout survives noise, not reality. A value is fair game when the API can return it, a user can type it, or an existing record already contains it. Anything else is waste.

## Field catalog

| Field kind | Stress with |
| --- | --- |
| Names / titles | 1 character; very long; many words; all-caps; emoji; mixed scripts; honorifics and suffixes; identical repeated values |
| Numbers / counts | 0; 1; negative where legal; maximum scale (999,999+); units that widen (1,234,567 vs 1.2k) |
| Money | 0.00; round vs precise cents; large values; negative where legal; currency symbol placement per locale |
| Dates / times | today; far past and future; same-day ranges; timezone edges; formats that expand (localized month names) |
| Text bodies | empty; one long unbroken word (URLs, hashes); maximum length; heavy markdown; RTL text; emoji sequences |
| Emails / IDs | shortest legal; longest legal; plus-addressing; punycode; display vs raw divergence |
| Lists / tables | empty; 1 item; exactly one page; exactly one page + 1; thousands of rows; all items identical; all items filtered out |
| Avatars / media | missing; broken; portrait vs extreme aspect ratios; animated; huge dimensions |
| States / enums | every value the schema allows, including the one nobody uses |

Empty and single-item results are states to design (empty states, single-row tables), not just stress cases — design them deliberately, then reuse them here as verification input.

## Method

1. **List the surfaces' data bindings** — every string, number, list and image the changed UI renders, and where the value comes from.
2. **Pick the plausible worst case per binding** from the catalog above plus the project's schema, analytics or content inventory. Prefer the value that breaks layout *and* the value that breaks comprehension (a count of 1 with a plural label; a total that overflows the card).
3. **See the worst state before claiming it works.** Toggle the data source to worst-case values — a demo/worst switch in fixtures or a seeded environment — and inspect the rendered result. A source-code reading is not a rendering claim.
4. **Fix at the cause**: truncation strategy (with a visible affordance to the full value), wrapping, min/max constraints at the boundary, pluralization, locale-aware number formatting. Clipping overflow with `overflow: hidden` hides the evidence instead of handling the value.
5. **Record what was exercised** per the skill's evidence rules: which values were rendered and observed, which were reasoned but not rendered. An unrendered worst case is an explicit gap, never a pass.

## Report shape

For each stressed binding: the value used, the observed result, and the fix or accepted gap. Call out any value you could not render so the host's rendered checks can cover it. Verification-claim discipline from `verification-and-recovery` applies unchanged: static inspection of the code is static evidence only.

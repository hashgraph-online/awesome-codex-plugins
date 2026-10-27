# B2B segments (optional layer)

Apply **only** when B2B sales (and ideally units) columns are mapped. All thresholds are **tunable** — document in the report.

## B2B share (ASIN level)

- `b2b_share_pct = 100 * b2b_sales / total_ordered_sales` when `total_ordered_sales > 0`

## Top B2B ASINs

- Rank by **B2B revenue** descending; take top **N** (default 15)
- Include: ASIN, title (if mapped), total revenue, B2B revenue, B2B share %, B2B units if available

## B2B-heavy products

- ASINs where **B2B share >** user threshold (default **50%**)
- Sort by B2B revenue or B2B share — state sort
- Interpretation: may warrant quantity discounts, Business-only offers — **hypothesis**, confirm with catalog strategy

## B2B growth opportunities

- ASINs with **high total revenue** but **low B2B share**
- Example from legacy spec: total revenue above **median** (or P50) of ASINs with sales **and** B2B share **<** **10%** — replace median/threshold with user rules
- Frame as "test Business price / eligibility" not guaranteed lift

## Non-B2B residual

- Only set `non_b2b_sales = total_sales - b2b_sales` when:
  - `total_sales` is the same "ordered product sales" basis as B2B breakdown in the export, and
  - B2B is a **subset** of total in that report definition
- If unsure, report **total** and **B2B** only. Do not label the residual "consumer-attributed" or "B2C revenue."

## When B2B columns are missing

- Omit sections 4 and 7 in `report-template.md` or mark **B2B N/A — columns not in file**
- Continue traffic and sales analysis in full

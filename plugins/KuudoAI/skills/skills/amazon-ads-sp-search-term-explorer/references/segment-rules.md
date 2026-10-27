# Segment rules (tunable) + gates

Document every threshold in the final report. Use **`references/threshold-elicitation.md`** before mining when values are missing.

---

## Brand vs generic (required split)

**Problem:** Branded queries often look like “gold” because intent is navigational; mixing them with generic misleads “scale” recommendations.

### Brand markers (required input)

- Before segmenting, obtain **`brand_markers`**: a list of substrings or patterns the user identifies as **their** brand (e.g. `["solid gold", "solidgold"]`).
- If the user has not provided markers **and** has not opted out, **ask** before producing Gold / Rising lists. If they opt out, state **split not applied** and warn in §9.
- **Best practice:** collect **brand markers and thresholds before heavy data pulls** (e.g. before large SQL or **before `CreateReport`** in the MCP skill) so segmentation is planned up front and outputs always target **two gold tables** (generic + branded).

### Classification

- **ASIN-format** terms (see below) are **not** branded/generic — they are a **separate stream**; exclude from branded/generic keyword tables by default.
- For remaining text queries: **branded** if any marker matches with **token boundaries** (avoid `"sony"` matching `"baloney"` — use word-boundary or curated whole-word lists). Misspellings can be added to markers for **defensive** rising-star handling.
- **Generic** = not branded under the above rule.

### Output implications

- **Generic gold** → scale, exact harvest, bid tests.
- **Branded gold** → defend, monitor conquest, budget protection — **not** “new discovery.”
- **Rising stars:** same split; branded misspell = **defensive**, not generic scale.

---

## ASIN-format “search terms” (product targeting stream)

SP reports surface **ASIN strings** (from product targeting / PAT campaigns) in the same column as real customer queries. In MCP v1 CSV that column is always **`searchTerm.value`** (dotted header in file). This is a fact about how SP reports work — partition before any keyword-segment logic.

### Detection

- Primary pattern (common modern ASINs): regex `^B0[A-Z0-9]{8}$` (10 characters; verify against your catalog).
- **Legacy / edge:** ASINs can be other 10-character alphanumerics; if the user’s catalog shows exceptions, extend the detector and document it.

### Default behavior

- **Exclude** ASIN-format rows from **keyword** Gold / Rising / Negative tables.
- In portfolio summary, report **ASIN stream** volume (rows, spend, clicks) separately.
- **Why:** Keyword negatives ≠ **negative product targets**; PAT campaigns (conquest/complement) often have **different** efficiency expectations — conflating them breaks recommendations.

### Optional section

- If the user wants PAT analysis: rank ASIN-format rows by spend/efficiency in **`references/report-template.md` §7**, with PAT-appropriate actions only.

---

## Data sufficiency (hard gate)

Thin windows (e.g. **1 day**) and sparse clicks make **confident** negation and “scale gold” **unsafe**.

### After aggregating by search term

1. **Window length** — `window_days` from file or user (if 1 day, say so explicitly).
2. **Median clicks per term** — median of `clicks` over terms with `clicks > 0` (or over all terms; **state which**).

### Gates (baseline)

| Condition | Strict negatives | Gold / rising language |
|-----------|-------------------|-------------------------|
| `window_days` **<** user **min_window** (default **14** if user unspecified for strict negs) | **Refuse** — explain; optional watchlist only | Degrade to **“monitor / extend window”** |
| Median clicks per term **<** **5** (tunable; **3** minimum floor for *any* “scale” confidence) | **Refuse strict**; watchlist with caveats | Degrade; recommend **14–30 day** pull |
| Median clicks per term **≥** **5** and window OK | Allowed if other rules pass | Normal with **confidence** column |

### Window-aware refinement (when `window_days` is known)

Use whenever the analysis window is known. For the MCP path, `window_days` derives directly from `reports[0].periods[0].datePeriod` (`endDate - startDate + 1`) — that's authoritative. The other sources listed here apply only if you ever process pre-existing exports.

Use **median clicks per term** after keyword-stream aggregation (same definition as above).

| Condition | Strict negatives | Gold / rising |
|-----------|------------------|---------------|
| `window_days` **≤** **7** **and** median clicks per term **≤** **2** | **Refuse** strict; watchlist / monitor only | **“Candidates to monitor”** — not “scale now” |
| `window_days` **≥** **28** **and** median clicks per term **≥** **3** | Full segments if other rules pass | Actionable with **confidence** column |
| Between the bands | **Caveat** every table; no aggressive negation language | Mixed confidence; shorter copy |

These rows **refine** the baseline table — apply the **stricter** outcome when both a baseline rule and a window-aware rule apply.

### Confidence badges (per row or segment)

- **High** — clicks (and spend if neg) **comfortably** above segment minimums.
- **Marginal** — barely cleared thresholds.
- **Degraded mode** — sufficiency gate failed for strict actions; tables are exploratory only.

### Copy for thin data

When gates fail: *“This window is too short / sparse for strict negative or scale recommendations. Extend to 14–30 days and re-run.”*

---

## Gold terms (keyword stream, generic vs branded tables)

**Intent:** See report template — generic = discover; branded = defend.

- Sales **>** 0
- ACoS **≤** user gold ceiling (elicited)
- Clicks **≥** user minimum for gold (default **3** — raise when median clicks are low)
- **Sort:** typically sales desc for generic; user may override

---

## Rising stars

- Spend band and sales **>** 0 per user
- Split **generic** (scale test) vs **branded** (defense / capture variants)
- **Sort:** CVR if orders+clicks; else sales

---

## Negative candidates (keyword stream only)

- Spend **>** user floor; sales **==** 0 (or policy for “bad ACoS”)
- **Strict** recommendations only if sufficiency + **min clicks for negatives** met
- **Sort:** spend descending

---

## Interest-only mode (cost missing)

When **`cost` / spend** is missing:

- **No** ACoS, **no** CPC, **no** spend-based negatives, **no** “historical waste” sum.
- **Allowed:** CTR/CVR-style mining if `clicks`, `impressions`, and **`sales` OR `orders`** exist — label **interest signals**, not “gold.”
- Checklist per segment:

| Segment | Minimum columns |
|---------|-----------------|
| Generic / branded gold (efficiency) | search term, **cost**, **sales**, **clicks** (+ orders for CVR) |
| Rising (efficiency band) | search term, **cost**, **sales**, **clicks** |
| Negatives (spend-based) | search term, **cost**, **sales**, **clicks** |
| Interest-only | search term, **clicks**, **impressions**, **sales OR orders** |

---

## Attribution alignment

See `references/attribution-window.md`. Mismatched 7d/14d breaks gold and negative efficiency logic.

---

## Exclusions (legacy)

- **Low impressions** + zero sales: prefer hold vs negate
- **New campaigns** in learning: mention volatility

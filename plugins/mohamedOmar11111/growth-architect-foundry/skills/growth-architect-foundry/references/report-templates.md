# Report Templates — Lazy Reference

Load this file ONLY when the `report` command is being executed or explained.

## Output Contract

Every report follows this order (decision-first, not data-dump):
1. **VERDICT** — one line: what changed and what needs a decision
2. **The Numbers** — signals, tasks, content, spend for the period
3. **Decisions Needed** — open high-priority work, owner named
4. **Done This Period** — from log.md, actual run history
5. **Next Up** — what cadence is due, what needs attention

## Languages

### English (default)
Standard business English. Platform and industry terms stay in English even in Arabic reports: ROAS, CPA, CTR, Pixel, CAPI, CBO, Advantage+, PMax.

### Arabic (`--lang ar`)
MSA (فصحى) with natural code-switching for platform terms. NOT Google Translate — the output is written in the way a MENA media buyer actually talks:
- "آخر تشغيل للمحرك: منذ يوم" not "آخر تشغيل لمحرك: قبل يوم واحد"
- "الخلاصة" not "النتيجة" for verdict
- Numbers stay Western (1,234.56) — don't switch to ١٬٢٣٤٫٥٦

## Period Handling

| Flag | Window | Use case |
|---|---|---|
| `--period week` (default) | Last 7 days | Weekly client check-in |
| `--period month` | Last 30 days | Monthly review, billing cycle |

## What the Report NEVER Does
- Auto-sends to client (always DRAFT, needs operator review)
- Makes decisions for the operator (flags decisions needed, doesn't execute them)
- Guesses numbers (absent data is reported as "—", not estimated)
- Mixes period-scoped and cumulative counts in the same table
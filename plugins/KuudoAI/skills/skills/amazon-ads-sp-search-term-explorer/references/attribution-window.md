# Attribution window contract

## Agent obligation

After data acquisition and before trust in ACoS/CVR-based segments, the agent must **confirm the attribution window** for **sales** and **orders** (and that **cost** matches the same window in meaning).

### How to confirm

1. **Column names** — Prefer explicit suffixes: `7d`, `14d`, `7 day`, `14 day`, etc. Document the chosen pair in the report.
2. **v1 default attribution** — for the MCP path, `metric.sales` and `metric.purchases` on SP reports use Amazon's **v1 default** attribution window (commonly described as **~14-day** click-attributed for SP — confirm in current Amazon docs). The catalog doesn't surface this per field, so disclose, don't assert precision.
3. **User** — If still unclear, **ask** the user which window the pull uses.

### If unknown

Emit a prominent line at the top of the deliverable (not a footnote):

```text
ATTRIBUTION WINDOW: UNKNOWN — ACoS and efficiency labels are directional only until sales/cost windows are confirmed.
```

Do not treat gold/negative efficiency claims as definitive when unknown.

## Sponsored Products reporting API (v1) quirk

In some **v1** reporting payloads, **`metric.sales`** (or similarly **unsuffixed** sales fields) may follow **Amazon’s default** attribution for that report type — often **14-day** for many ad sales fields, but **do not assume**: the catalog and report type dictate behavior.

- **Suffixed** fields (e.g. concepts like `sales7d`, `sales14d`) may be **unavailable** on certain endpoints or rejected by the field catalog even when documented elsewhere.
- When only unsuffixed fields are returned, state: **window inferred from report documentation or user** — if neither exists, use **UNKNOWN** banner above.

## Cost vs sales

**Never** pair 7-day sales with 14-day cost (or vice versa). Pick one consistent window or stop efficiency-based segments.

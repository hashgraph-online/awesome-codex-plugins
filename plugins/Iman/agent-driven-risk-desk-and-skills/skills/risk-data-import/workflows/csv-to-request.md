# Workflow: a caller's CSV to a validated request

Worked on a positions file; every other contract follows the same steps
with its own example as the template.

1. Pick the tool from the table in SKILL.md, then open its shipped
   example (listed in reference.md) as the template. A positions file
   with market values is `risk_exposure`, template
   `examples/portfolio.json`.
2. Map every column to a field and list the required fields with no
   column. For positions: `id`, `asset`, `market_value`,
   `instrument_type`; for the request: `as_of`, `currency`, `source`,
   `data_mode`, `nav`. A file that has no NAV and no currency gets one
   question asking for both, plus `data_mode` and `source`.
3. Repair only what has one reading, and keep the list as you go: row,
   column, value as found, value as written, reason. For example, row 3
   `MV` `"(4,200)"` to `-4200`, accounting negative; row 1 `MV`
   `"$1,250,000"` to `1250000`, currency symbol and separators, currency
   USD as stated. Ask about everything else (SKILL.md, "Repairs you must
   not make").
4. Write the request JSON next to the caller's file, as plain JSON numbers
   and ISO dates.
5. Validate it with the Python that has riskdesk installed:

       .venv/bin/python plugins/risk-desk/skills/risk-data-import/scripts/check_artifact.py risk_exposure request.json

   On FAIL, each line names a field path such as
   `positions.2.market_value` (zero-based) and the value found. Map it to
   the caller's row, ask for that value, and re-run. Cross-field rules
   such as unique ids appear only after every field passes, so a second
   run can show a new error.
6. On OK, run the tool or the CLI:

       riskdesk exposure --input request.json

   A refusal here is a calculation-level check the model cannot make
   (reference.md, "What OK does not prove"). Quote its message and map it
   back the same way. Do not loosen the request to make it pass.
7. Report the repairs list first, then hand over to the skill that owns
   the result (risk-portfolio here) for degraded status and figures.

## Before reporting

- Every repair is listed; nothing was filled, carried forward or zeroed.
- `data_mode` and `source` are the caller's words.
- The request file path is given, so the caller can re-run it.

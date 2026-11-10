# Workflow: exposure report for one book

1. Confirm the input: `as_of`, `currency`, `source`, `data_mode`, `nav`, and
   one row per position with a unique `id`, an `asset`, a signed
   `market_value` already in that currency, and `instrument_type: linear`.
   If the caller has a spreadsheet, convert it with the risk-data-import
   skill first. Never invent a NAV or a market value.
2. Route anything that is not linear. An option's premium is not its
   exposure; send an options book to risk-derivatives.
3. Run `risk_exposure`, or the CLI and keep the result:

       riskdesk exposure --input examples/energy_book.json > exposure.json

   On a refusal the CLI exits 1 and the file holds `error` and `message`;
   quote the message and map it back to the row (risk-data-import,
   step 6). Do not quote a number from a refused run.
4. Check the saved result:

       python3 scripts/check_artifact.py exposure.json

   Stop on FAIL and report it as a defect, not as a result.
5. Report in the order given in SKILL.md: degraded first, gross, net, both
   leverage figures against the supplied NAV, the largest share of gross,
   then any net short assets.
6. If the user wants limits graded on this result, pass it unchanged as
   `results.exposure` to `risk_limits` (risk-limits skill).

## Before reporting

- Say that gross adds absolute position values before offsetting.
- Say that NAV is supplied, not verified.
- Cite `source`, `as_of` and `input_sha256` so the figure can be traced.
- No probability, forecast or recommendation is attached to an exposure.

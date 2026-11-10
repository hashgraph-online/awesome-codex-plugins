---
name: risk-xva
description: Run a trusted local ORE (Open Source Risk Engine) project for counterparty exposure and valuation adjustments (risk_xva), and read its XVA and exposure reports. Use for ORE CVA, DVA, funding and other XVA reports, or to produce the netting-set exposure profile that risk_exposure_profile summarises. Not for historical VaR (use risk-tail), not for SA-CCR (use risk-counterparty), and not for a project you have not inspected.
---

# Risk Xva

Use `risk_xva` with an explicit local project directory, relative config
path, new output directory outside the project, and data_mode of
synthetic, user-licensed or upstream-example. Read
[input contracts](../../references/contracts.md) for the supported ORE
project boundary. The CLI equivalent is
`riskdesk xva --project PROJECT --config Input/ore.xml --output NEW_OUTPUT --data-mode synthetic`.
It needs the optional extra, `riskdesk[xva]` (risk-setup skill).

Run only a user-provided or inspected local project. The ORE configuration determines instruments, curves, counterparties, CSA/netting, simulation and requested adjustments. Do not invent these inputs. Both simulation and XVA must be active; an old cube is not reused.

## Report first

1. Whether the run succeeded. Any ORE error, a failed worker or a missing
   XVA report is a refusal, not a result. Quote nothing from a failed run,
   and do not read partial files from its output directory.
2. `currency` (ORE's `baseCurrency`), `as_of` and `requested_xva_flags`.
3. Then figures, each with the report level (netting set or trade) it comes from.

## Sign conventions

Preserve ORE column names and signs. Disabled metrics, null values and
zero results are distinct: null is ORE's unavailable value, and a zero in
a column whose adjustment was not requested is a disabled calculation.
Netting-set and trade rows overlap and must not be summed together.

## What not to claim

Positive exposure is not signed mark-to-market, and risk-neutral XVA is not a real-world VaR forecast. The included upstream example validates execution and report translation only. It does not validate all models, regulatory capital, wrong-way risk, SIMM rights or a user's calibration. The process boundary is not a sandbox for hostile XML.

## Going deeper

- `reference.md`: what the adapter checks, runs, keeps and writes, with code lines, and how the result feeds `risk_exposure_profile`.
- `workflows/run-ore-project.md`: inspect, run, check and report one project.
- `scripts/check_artifact.py OUTPUT/riskdesk-xva.json`: one line verdict on a saved result: no ORE errors, XVA rows present, every row matches its report's columns, input hashes recorded, and which XVA columns hold nulls. Standard library only.

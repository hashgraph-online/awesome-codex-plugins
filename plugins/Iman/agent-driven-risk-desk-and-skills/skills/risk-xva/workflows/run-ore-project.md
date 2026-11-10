# Workflow: run an ORE project and report its XVA

1. Inspect the project before running it. Open its `ore.xml` and confirm
   with the user that the directory is theirs, that both the `simulation`
   and `xva` analytics are active, and which adjustments it requests. The
   adapter is not a sandbox; an unfamiliar project is read first.
2. Confirm the backend: `risk_desk_status` answers even without ORE, so
   check the `xva` extra with the risk-setup skill's
   `scripts/check_artifact.py`. Without it the run fails with "ORE failed;
   inspect OUTPUT/worker.log", and `worker.log` says "Install
   riskdesk[xva] for the ORE backend". Say that; never report the risk as
   zero.
3. Choose `data_mode` with the user: `synthetic`, `user-licensed` or
   `upstream-example` (ORE's own shipped example inputs). It is their
   declaration, not a rights check.
4. Choose a new output directory outside the project. A directory that
   already exists is refused, including the one a failed run left behind.
5. Run `risk_xva`, or:

       riskdesk xva --project PROJECT --config Input/ore.xml --output NEW_OUTPUT --data-mode user-licensed > xva.json

   Exit 1 with `error` and `message` in `xva.json` is a refusal. Quote the
   message, quote no figure, and do not read partial files from the output
   directory. A refusal naming `worker.log` means the worker failed; the
   cause is at the end of that log.
6. Check the result the adapter wrote:

       python3 scripts/check_artifact.py NEW_OUTPUT/riskdesk-xva.json

   Stop on FAIL.
7. Report in the order given in SKILL.md: success, then `currency`,
   `as_of` and `requested_xva_flags`, then each figure with its row level
   and ORE's own column name. Name every null column as unavailable. Cite
   the `artifact` path and `backend_version`.
8. For peak PFE, EPE and Effective EPE of a netting set, take the rows of
   `reports.exposure_nettingset_<ID>` unchanged into `risk_exposure_profile`
   and follow `../risk-counterparty/workflows/exposure-profile.md`, passing
   the run's `data_mode` through unchanged.

## Before reporting

- Netting-set and trade rows overlap; never add them.
- Risk-neutral XVA and historical VaR are different kinds of number; do not
  put them in one table without saying so.
- A clean run shows the adapter and the configuration are consistent, not
  that the calibration or the regulatory treatment is right.

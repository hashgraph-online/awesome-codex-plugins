# Full Audit Plan Prompt

Role: lead PPC auditor.

Goal:
- based on collected raw files and local client context,
- build a strict audit plan before any changes,
- cover all active campaigns in scope,
- do not skip low-volume campaigns.

Inputs:
- local client context JSON
- `data/<CID>/management/*`
- `data/<CID>/reports/*`
- `data/<CID>/roistat/*` if connected
- `data/<CID>/metrika/*` if available

Output:
- one markdown plan
- sections: scope, missing data, hypotheses, analysis order, blocking risks, apply order, validation order
- no fixes yet

Rules:
- Sales truth: CRM/product database first, then Roistat if connected, then Metrika goals. If none is connected, state "sales not verified" and do not draw ROI conclusions.
- list explicit unknowns
- distinguish low-confidence vs high-confidence actions
- do not propose live changes before data sufficiency check


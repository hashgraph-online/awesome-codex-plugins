# Worked example - 4-pass UI ponder (`ui` lens)

Full end-to-end 4-pass session showing Pass 1 seeding (`units.json` + `findings.json`), Pass 2 four-perspective deliberation + delta batch (`delete`, `unit-add`, `add`, `edit`, `change`) triggering a `blocked` coverage gate (`11/12` units), Pass 3 closing the coverage gap and updating the unit caption via `unit-edit`, and Pass 4 confirming zero-churn convergence via `ponder delta --none` and exporting `apply-plan.md`.

## Pass 1 - seed

```sh
mkdir -p .ponder/tmp/batch
ponder start "the UI" --lens ui --max-passes 6 --min-passes 2
ponder predict --churn 0.9 --claim "Pass 1 seeds inventory; empty and error states will be weakest."
```

Write `.ponder/tmp/units.json` (11 units across 7 routes) and `.ponder/tmp/findings.json` (24 findings):

```json
{ "version": 1, "lens": "ui", "units": [
  { "id": "screen.dashboard", "label": "Dashboard - populated", "path": "src/routes/dashboard.tsx", "kind": "screen", "meta": { "route": "/" } },
  { "id": "screen.settings.billing.empty", "label": "Settings -> Billing - no invoices", "path": "src/routes/settings/billing.tsx", "kind": "screen", "meta": { "route": "/settings/billing", "state": "empty" } }
] }
```

```json
{ "version": 1, "findings": [
  { "unit": "screen.settings.billing.empty", "title": "Empty state is a bare 'No invoices' string",
    "detail": "No illustration, explanation of when invoices appear, or primary action.",
    "dimension": "empty-states", "score": 2, "severity": "must", "confidence": 0.8, "effort": "s",
    "evidence": ["src/routes/settings/billing.tsx:88-94"],
    "recommendation": "Add an empty state with cause, expectation and primary action." }
] }
```

```sh
ponder units --file .ponder/tmp/units.json
ponder grade --file .ponder/tmp/findings.json
ponder deliberate --file .ponder/tmp/deliberation-1.json
ponder delta --file .ponder/tmp/deltas-1.jsonl
ponder judge
ponder decide continue --why "Pass 1 seeded inventory and baseline grades; pass 2 tests them against all four voices."
```

## Pass 2 - revise (deliberation catches noise and missed scope)

```sh
ponder predict --churn 0.4 --claim "Pass 1 over-graded card polish and missed API 500 error states."
ponder deliberate --file .ponder/tmp/deliberation-2.json
```

`deliberation-2.json`:

```json
{ "question": "Does the pass-1 finding set survive a second reading of the code?",
  "skeptic": { "argument": "f-0011 claims inconsistent padding but both cards resolve to --space-4. f-0019 duplicates f-0004.", "confidence": 0.85 },
  "builder": { "argument": "Several recommendations state the symptom rather than the concrete UI change.", "confidence": 0.7 },
  "dreamer": { "argument": "No screen was checked for API 500 states, and /invite/:token was missed in pass 1.", "confidence": 0.75 },
  "empath": { "argument": "Billing empty state blocks first-run users and outranks card polish.", "confidence": 0.7 } }
```

`deltas-2.jsonl` (place `unit-add` above any `add`, `unit-edit`, or `unit-delete` referencing the new unit):

```json
{"op":"delete","target":"f-0011","perspective":"skeptic","why":"Both cards resolve to --space-4; unsupported."}
{"op":"delete","target":"f-0019","perspective":"skeptic","why":"Duplicate of f-0004 on a different screen."}
{"op":"unit-add","perspective":"dreamer","why":"Route missed in pass 1 survey.","unit":{"id":"screen.invite.accept","label":"Accept invite","path":"src/routes/invite/accept.tsx","kind":"screen","meta":{"route":"/invite/:token"}}}
{"op":"add","perspective":"dreamer","why":"No pass checked API 500 behavior.","finding":{"unit":"screen.projects.detail","title":"No error state on failed load","detail":"Error branch returns null.","dimension":"error-states","score":1,"severity":"must","confidence":0.85,"effort":"m","evidence":["src/routes/projects/[id].tsx:41-60"],"recommendation":"Render a failure state with cause and retry action."}}
{"op":"edit","target":"f-0007","perspective":"builder","why":"Name concrete change.","set":{"recommendation":"Add empty state with cause, expectation and 'Add payment method' button."}}
{"op":"change","target":"f-0009","perspective":"empath","why":"Blocks first-run; outranks polish.","set":{"severity":"must","score":2}}
```

```sh
ponder delta --file .ponder/tmp/deltas-2.jsonl
ponder judge                                    # coverage 0.92 (11/12) -> advice: blocked (screen.invite.accept ungraded)
ponder decide continue --why "Dreamer found /invite/:token; cannot stop with an ungraded screen."
```

## Pass 3 - close the coverage gap and correct the unit caption

```sh
ponder predict --churn 0.12 --claim "Grade screen.invite.accept and expect little movement elsewhere."
ponder deliberate --file .ponder/tmp/deliberation-3.json
```

Opening `src/routes/invite/accept.tsx` reveals both Accept and Decline buttons share primary styling, so `deltas-3.jsonl` grades `screen.invite.accept` and updates its caption via `unit-edit`:

```json
{"op":"add","perspective":"dreamer","why":"Decline button uses primary style beside Accept.","finding":{"unit":"screen.invite.accept","title":"Decline shares primary filled styling with Accept","detail":"Irreversible decline carries primary weight.","dimension":"affordance-clarity","score":2,"severity":"should","confidence":0.85,"effort":"xs","evidence":["src/routes/invite/accept.tsx:52-68"],"recommendation":"Style Decline as secondary or destructive ghost button."}}
{"op":"unit-edit","target":"screen.invite.accept","perspective":"builder","why":"Screen handles accept and decline; update caption.","set":{"label":"Accept or decline invite"}}
```

```sh
ponder delta --file .ponder/tmp/deltas-3.jsonl
ponder judge                                    # coverage 1.00 (12/12), novelty 0.04, churn 0.07 -> advice: continue (need 2 quiet passes)
ponder decide continue --why "Invite route has one pass of grading and f-0014 sits below 0.5 confidence."
```

## Pass 4 - confirm convergence and export plan

```sh
ponder predict --churn 0.05 --claim "Invite route and remaining must-findings hold up on re-read."
ponder deliberate --file .ponder/tmp/deliberation-4.json
ponder delta --none --why "All 4 voices verified all 12 units; zero changes needed."
ponder judge                                    # coverage 1.00, novelty 0.00, churn 0.00, two quiet passes -> stop (converged)
ponder decide stop --why "Coverage 12/12, two consecutive quiet passes, confidenceFloor 0.00 across all open must findings."
ponder report --out docs/ui-ponder.md
ponder apply --dry-run --severity must,should
```

`ponder apply --dry-run` previews the ordered work plan without closing the session; `ponder apply` on a closed session writes `apply-plan.md` and marks the session `applied` (never editing source files).

---
name: cross-skill-rules
type: reference
parent_skill: skill-auditor
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-05"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# Cross-Skill Consistency Rules

Reference for the skill-auditor agent.
These rules define how skills must relate to each other within the Quality-Engineering-Skills framework.
Violations are Major Findings.

---

## Required Execution Checklist

☐ NCR description standard consistent with 8D D2 problem description standard
☐ 5Why output format compatible with 8D D4 root cause input requirement
☐ PFMEA/DFMEA update explicitly required by 8D D7 — and PFMEA/DFMEA skill references 8D as trigger
☐ AP=H governance rule identical across action-priority-ap, pfmea-process, and dfmea-design
☐ ICA definition in 8D D3 consistent with NCR disposition and containment logic
☐ OEM-specific rules in oem-requirements.md consistent with oem-formats.md and 8d-report-writing
☐ Control Plan linkage present in pfmea-process and referenced by 8D D7
☐ Severity classification consistent across ncr-writing (Critical/Major/Minor) and pfmea-process (S scale)

---

## Closed-Loop Chain

Every quality escape in this framework must flow through this chain without gaps:

```
Detection event
    → NCR (document the non-conformance)
    → 8D trigger (D0: safety check, ICA)
    → D2: problem description (matches NCR description standard)
    → D4: root cause (5Why / fishbone output feeds here)
    → D5: corrective actions
    → D6: verify effectiveness
    → D7: PFMEA updated, Control Plan updated, Work Instructions updated
    → D8: close, lessons learned deployed
```

**Audit rule:** Any skill that participates in this chain must explicitly reference its position in it and its handoff to the next step.

---

## Rule Set

### R01 — NCR ↔ 8D D2 alignment

The NCR description standard and the 8D D2 problem description standard must require the same elements:
- Measured value vs specification
- Part number + revision
- Quantity (X of Y = Z%)
- No root cause in either

**Violation:** NCR skill accepts subjective descriptions that 8D D2 would reject, or vice versa.

---

### R02 — 5Why ↔ 8D D4

The 5Why output must be directly usable as 8D D4 input:
- 5Why produces: occurrence root cause + escape root cause (two chains)
- 8D D4 requires: occurrence root cause + escape root cause
- Evidence labels from 5Why (Confirmed / Probable / Hypothesis) must be compatible with D4 evidence requirement

**Violation:** 5Why skill produces a single chain; 8D D4 requires two.

---

### R03 — PFMEA/DFMEA ↔ 8D D7

- 8D D7 must explicitly require: PFMEA updated + Control Plan updated + Work Instructions updated + horizontal deployment assessed
- pfmea-process must reference 8D as a trigger for PFMEA revision
- dfmea-design must reference 8D as a trigger when a design root cause is identified

**Violation:** Either skill treats D7 or PFMEA update as optional.

---

### R04 — AP=H governance consistency

The AP=H governance rule must be identical in all three skills:
- `action-priority-ap`: primary definition
- `pfmea-process`: must reference action-priority-ap for AP logic, not define its own
- `dfmea-design`: same as pfmea-process

Rule: AP=H requires assigned owner + target date, OR formal documented management acceptance. No silent H-AP items.

**Violation:** Any skill allows H-AP items to exist without action or documented acceptance.

---

### R05 — ICA ↔ NCR containment

- 8D D3 ICA definition: must physically prevent escape, must have past-tense implementation date, must have verification evidence
- NCR containment / disposition logic must use the same standard: segregation is not containment unless escape is physically prevented

**Violation:** NCR disposition allows "inform customer" or "monitor going forward" as containment.

---

### R06 — OEM rule consistency

OEM-specific requirements must be consistent across:
- `action-priority-ap/references/oem-requirements.md` — AP governance per OEM
- `documentation/8d-report-writing/references/oem-formats.md` — 8D submission format per OEM
- `documentation/8d-report-writing/SKILL.md` — OEM-specific writing rules

**Violation:** Ford CSR requirement stated differently in two files. BMW G8D format described differently in two files.

---

### R07 — Severity scale consistency

The qualitative severity scale must align across skills:
- `ncr-writing`: Critical / Major / Minor — definitions must match PFMEA S=9–10 / S=5–8 / S=1–4 intent
- `pfmea-process`: S=1–10 numeric scale — Critical = S≥9 (safety/regulatory)
- `action-priority-ap`: S=9–10 always AP=H — must be consistent with ncr-writing Critical definition

**Violation:** ncr-writing defines Critical as cosmetic; pfmea-process defines S=9 as safety.

---

### R08 — Skill vs Reference separation

- SKILL.md = executable (workflow, decision rules, validation gates)
- REFERENCE file = explanatory (tables, standard quotes, examples, patterns)
- No logic should be duplicated between SKILL.md and its reference files
- If a rule exists in a reference file, the SKILL.md should point to it, not repeat it

**Violation:** AP table in both SKILL.md and ap-table.md with different values. 8D gate criteria defined in both 8d-coach and 8d-problem-solving with inconsistent thresholds.

---

## Integration map

Use this map to check that all required cross-references exist:

| From | Must reference | Direction |
|------|---------------|-----------|
| ncr-writing | 8d-problem-solving (D0 trigger) | → |
| 8d-problem-solving D2 | ncr-writing (description standard) | ↔ |
| 8d-problem-solving D4 | 5why-root-cause, fishbone-analysis | → |
| 8d-problem-solving D7 | pfmea-process, car-corrective-action | → |
| 5why-root-cause | 8d-problem-solving D4 (output feeds here) | → |
| pfmea-process | action-priority-ap (AP logic) | → |
| dfmea-design | pfmea-process (handoff), action-priority-ap | → |
| action-priority-ap | pfmea-process, dfmea-design (context) | ↔ |
| car-corrective-action | 8d-problem-solving D5–D6, pfmea-process D7 | → |
| iso-9001-internal-audit | ncr-writing (finding → NCR), car-corrective-action | → |
| iatf-16949-audit | iso-9001-internal-audit (extends), pfmea-process | → |

---
name: zeroing-report-template
type: asset
parent_skill: quality-problem-zeroing
author: Crow12138
version: "1.0"
status: approved
created: "2026-07-04"
last_updated: "2026-07-04"
updated_by: Crow12138
reviewed_by: RBraga01
license: MIT
---

# Quality Problem Zeroing Report Template

Use the applicable sections. Mark an item “Not applicable” only with a documented reason.
Keep evidence identifiers traceable to controlled records.

## Document Control

| Field | Entry |
|------|-------|
| Report title | |
| Report number / revision | |
| Product / program | |
| Product identifier / batch / configuration | |
| Development or service stage | |
| Responsible organization | |
| Technical zeroing required? | Yes / No — rationale: |
| Management zeroing required? | Yes / No — rationale: |
| Classification / access restrictions | |
| Prepared by / date | |
| Checked by / date | |
| Required technical or ordering-organization co-signers | |
| Quality and relevant-department co-signers | |
| Reviewed by / date | |
| Approved by / date | |

## 1. Problem Intake and Emergency Response

### 1.1 Problem statement

| Item | Evidence-based description |
|------|----------------------------|
| Requirement / expected state | |
| Actual phenomenon | |
| Time and location | |
| Operating state and sequence | |
| Environment and test conditions | |
| Detection method and detector | |
| Affected product and population | |
| Actual and potential impact | |

### 1.2 Initial evidence preservation

| Evidence | Identifier / location | Condition preserved | Custodian |
|----------|-----------------------|---------------------|-----------|
| | | | |

### 1.3 Emergency response

| Action | Population / boundary | Owner | Implemented date | Effectiveness evidence | Removal condition |
|--------|-----------------------|-------|------------------|------------------------|------------------|
| | | | | | |

### 1.4 Stakeholder communication

| Stakeholder | Impact | Information communicated | Date | Response / agreement |
|-------------|--------|--------------------------|------|----------------------|
| | | | | |

## 2. Team and Plan

| Name | Function / organization | Role and responsibility | Authority / resource |
|------|-------------------------|-------------------------|----------------------|
| | | | |

| Milestone | Owner | Target date | Actual date | Status / evidence |
|-----------|-------|-------------|-------------|-------------------|
| | | | | |

## Part A — Technical Zeroing Report

## A1. Problem Overview

Summarize the product, event, phenomenon, operating state, environment, impact, reporting,
and emergency response. Reference the detailed intake evidence rather than duplicating it.

## A2. Exact Location — 定位准确

### A2.1 Investigation path

| Candidate location / cause | Check or test | Evidence | Result | Retained / eliminated |
|----------------------------|---------------|----------|--------|-----------------------|
| | | | | |

### A2.2 Localization conclusion

- Exact affected process and product level:
- Lowest failed unit:
- Abnormal state:
- Failure mode:
- Basic cause indicated at localization:
- Product, equipment, method, environment, or operation:
- Affected boundary and customer or mission effect:
- Emergency-response effectiveness at this stage:
- Relevant-party agreement:

### A2.3 Localization gate

- [ ] Exact location is supported by facts.
- [ ] Evidence state and configuration are traceable.
- [ ] Alternative locations have documented dispositions.
- [ ] The effect on the customer or mission is described.

## A3. Clear Mechanism — 机理清楚

### A3.1 Observation-to-mechanism chain

Describe the physical, chemical, electrical, software, human-system, or process sequence
from the abnormal factor at the lowest unit to the final phenomenon.

### A3.2 Root-cause register

| ID | Root cause | Cause type | Supporting evidence | Alternative explanation disposition | Confirmed? |
|----|------------|------------|---------------------|-------------------------------------|------------|
| RC-1 | | Technical / contributing / management | | | Yes / No |

### A3.3 Three-view analysis

| View | Finding | Evidence | Required action |
|------|---------|----------|-----------------|
| Product | | | |
| Process | | | |
| Organization | | | |

### A3.4 Mechanism gate

- [ ] All material observations are explained.
- [ ] All root causes are identified; hypotheses remain labelled.
- [ ] The causal chain is scientifically and logically coherent.
- [ ] Objective evidence supports every confirmed link.

## A4. Problem Reproduction or Alternative Verification — 问题复现

| Item | Entry |
|------|-------|
| Hypothesis tested | |
| Test article and configuration | |
| Controlled and changed variables | |
| Actual-condition fidelity | |
| Instrumentation and data | |
| Acceptance / rejection criteria | |
| Safety and stop criteria | |
| Approval record | |
| Result | |
| Raw record / report identifiers | |
| Stakeholder confirmation | |

If no reproduction test was performed:

- Reason:
- Alternative method:
- Evidence:
- Limitation and residual uncertainty:

### A4.1 Verification gate

- [ ] The result tests the claimed mechanism rather than visual similarity alone.
- [ ] Raw data and configuration are traceable.
- [ ] Failed or contradictory results were returned for renewed analysis.

## A5. Measures and Verification — 措施有效

### A5.1 Cause-to-action traceability

| Cause ID | Correction | Corrective action | Owner / due date | Controlled document change | Verification method | Result |
|----------|------------|------------------|------------------|----------------------------|---------------------|--------|
| | | | | | | |

### A5.2 Action risk and sufficiency

| Action | Operating range covered | New or worse risk | Regression / side-effect test | Residual limitation |
|--------|-------------------------|-------------------|-------------------------------|---------------------|
| | | | | |

### A5.3 Measures gate

- [ ] Every confirmed root cause has an action.
- [ ] Corrections and corrective actions are not confused.
- [ ] Actions are implemented, not merely planned.
- [ ] Effectiveness, sufficiency, and adverse effects are evaluated.
- [ ] Emergency controls are retained or removed by documented decision.

## A6. Horizontal Deployment — 举一反三

| Layer / population searched | Exposure logic | Search method | Finding | Action / owner / due date | Evidence / status |
|-----------------------------|----------------|---------------|---------|---------------------------|-------------------|
| Affected batch | | | | | |
| Produced product | | | | | |
| Work in progress | | | | | |
| Not-yet-produced product | | | | | |
| Related designs / processes | | | | | |
| Other programs / organizations | | | | | |

List design rules, process instructions, test requirements, standards, training, databases,
or tools created or revised:

| Document / system | Revision | Change | Effective date | Deployment evidence |
|-------------------|----------|--------|----------------|---------------------|
| | | | | |

## A7. Technical Conclusion

- Technical zeroing completed: Yes / No
- Basis for conclusion:
- Remaining issues:
- Residual risk:
- Follow-up recommendation:

## A8. Technical Evidence List

| Evidence ID | Title / record number | Revision / date | Custodian / location | Supports section |
|-------------|-----------------------|-----------------|----------------------|------------------|
| | | | | |

## Part B — Management Zeroing Report

## B1. Process Overview — 过程清楚

| Time / sequence | Required activity | Actual activity | Record / evidence | Deviation or weakness |
|-----------------|-------------------|-----------------|-------------------|-----------------------|
| | | | | |

Describe how the problem was created, developed, detected, reported, and handled. Identify
the affected management links, positions, controls, and rules.

## B2. Management Cause and Responsibility — 责任明确

### B2.1 Management-cause register

| ID | Management weakness / root cause | Evidence | Related technical cause | Required action |
|----|----------------------------------|----------|-------------------------|-----------------|
| MC-1 | | | | |

### B2.2 Responsibility register

| Organization / person | Documented duty and authority | Action or omission | Evidence | Responsibility type and degree |
|-----------------------|-------------------------------|-------------------|----------|--------------------------------|
| | | | | |

Distinguish direct/indirect, primary/secondary, and leadership/execution responsibility.

## B3. Management Measures — 措施落实

| Cause ID | Action | Department / owner | Resources | Due date | Completion evidence | Effectiveness check |
|----------|--------|--------------------|-----------|----------|---------------------|--------------------|
| | | | | | | |

## B4. Treatment and Learning — 严肃处理

| Target / scope | Treatment, education, recognition, or penalty | Policy basis | Date | Record / result |
|--------------|------------------------------------------------|--------------|------|-----------------|
| | | | | |

Explain how the treatment supports education and management improvement. Do not include
personal-sensitive details beyond authorized reporting requirements.

## B5. Rule Improvement — 完善规章

| Rule / standard / procedure | Gap addressed | New or revised content | Owner | Approval / effective date | Training and implementation evidence |
|-----------------------------|---------------|------------------------|-------|---------------------------|--------------------------------------|
| | | | | | |

## B6. Management Conclusion

- Management zeroing completed: Yes / No
- Basis for conclusion:
- Remaining issues:
- Residual risk:
- Follow-up recommendation:

## B7. Management Evidence List

| Evidence ID | Title / record number | Revision / date | Custodian / location | Supports section |
|-------------|-----------------------|-----------------|----------------------|------------------|
| | | | | |

## Part C — Review and Closure

### C1. Review checklist

- [ ] Zeroing route and level are appropriate.
- [ ] Technical five requirements are complete where applicable.
- [ ] Management five requirements are complete where applicable.
- [ ] All causes map to implemented actions and evidence.
- [ ] Effectiveness and adverse effects are verified.
- [ ] Horizontal deployment and controlled-document changes are complete.
- [ ] Residual issues and risks are explicit and approved.
- [ ] Required signatures, reviews, approvals, and communications are complete.

### C2. Review findings

| Finding | Required correction | Owner | Due date | Closure evidence |
|---------|---------------------|-------|----------|------------------|
| | | | | |

### C3. Closure decision

- Decision: Approved / Rejected / Conditionally approved
- Decision basis:
- Authorized reviewer / date:
- Affected parties notified / date:
- Team disbanded / date:

## Incomplete Zeroing Addendum

Use only when complete zeroing is genuinely infeasible:

- Reason complete zeroing cannot be achieved:
- Plausible root causes remaining:
- Evidence for and against each:
- Comprehensive controls applied:
- Residual risk and affected parties:
- Monitoring and follow-up plan:
- Required authorization and signatures:

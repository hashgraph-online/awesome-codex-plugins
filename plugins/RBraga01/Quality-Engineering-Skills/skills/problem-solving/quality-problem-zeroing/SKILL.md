---
name: quality-problem-zeroing
description: >-
  Run quality problem zeroing, perform 双归零 (double-five zeroing), write a
  technical zeroing report, write a management zeroing report, or close an
  aerospace quality problem under GB/T 29076—2021. Covers problem reporting,
  emergency response, team formation, technical zeroing (定位准确、机理清楚、问题复现、
  措施有效、举一反三), management zeroing (过程清楚、责任明确、措施落实、严肃处理、
  完善规章), evidence gates, review, and closure. Use for aerospace or complex
  equipment failures, defects, accidents, repeated problems, human-responsibility
  problems, and issues requiring a formal closed-loop investigation.
license: MIT
metadata:
  author: Crow12138
  version: "1.0"
  iso-9001: "10.2 (supporting)"
  gbt-29076: "2021"
  domain: quality-engineering
  subdomain: problem-solving
  industries: aerospace,defense,aviation,complex-equipment,manufacturing
  status: approved
  created: "2026-07-04"
  last_updated: "2026-07-04"
  updated_by: Crow12138
  reviewed_by: RBraga01
  standard_edition: "GB/T 29076—2021"
---

# Quality Problem Zeroing

## Goal

Close a quality problem with objective evidence that:

1. Locates and explains the technical failure;
2. Removes every confirmed root cause and verifies the result;
3. Identifies and repairs management weaknesses where required;
4. Extends the learning to other exposed products, processes, and organizations; and
5. Leaves no action, evidence, approval, or known residual risk hidden at closure.

GB/T 29076—2021 is the controlling source for scope, sequence, terminology, and closure.
Treat other methods and publications as supporting guidance only. Read the
[standard method guide](references/gbt-29076-2021-method-guide.md) whenever a
formal scope decision, report, or closure review is required.

## When to Use

Use this skill for an aerospace or complex-equipment quality problem that requires formal
technical zeroing, management zeroing, double-five zeroing, an Annex A-aligned report, or a
closure review. It is especially relevant to failures, defects, accidents, batch problems,
repeated problems, field or delivered-product issues, human-responsibility problems, and
problems caused by missing or inadequate rules.

Use a narrower root-cause skill when the user only needs one analysis tool. Use 8D instead
when the customer or sector mandates an 8D response, then cross-check whether the same event
also requires GB/T 29076—2021 zeroing.

## Required Execution Checklist

- [ ] Record the product, problem phenomenon, operating state, time, location, environment, detector, and affected parties.
- [ ] Protect the scene, product state, records, data, and physical evidence when safe to do so.
- [ ] Assess safety, property, mission, delivered-product, and escalation risk immediately.
- [ ] Identify, segregate, stop, recall, or inspect suspect product as required.
- [ ] Form a cross-functional team with a named leader, authority, resources, and stakeholder representation.
- [ ] Decide and document whether technical zeroing, management zeroing, or both apply.
- [ ] Start technical zeroing first when both apply; never substitute it for management zeroing.
- [ ] Build an evidence-backed technical causal chain from the lowest failed unit to the observed effect.
- [ ] Identify all root causes; keep unproven explanations labelled as hypotheses.
- [ ] Reproduce or otherwise verify the problem mechanism using an approved method.
- [ ] Implement correction and root-cause corrective actions with owners and dates.
- [ ] Verify effectiveness, sufficiency, and adverse effects before ending emergency controls.
- [ ] Complete horizontal deployment across relevant products, processes, and organizations.
- [ ] Reconstruct the management process and assign responsibility from duties and evidence.
- [ ] Implement management actions and embed them in controlled rules, standards, or procedures.
- [ ] Complete the required report, evidence list, signatures, and independent review.
- [ ] Close only after all actions are complete, effectiveness is verified, and residual issues are explicit.

## Workflow

### 1. Report and preserve the problem

Create the initial problem record before analysis changes the evidence. Capture:

- Product name, identifier, batch, configuration, development or service stage, and responsible organizations;
- Exact phenomenon, expected requirement, actual result, operating state, sequence, time, location, and environment;
- Who detected the problem and how it was detected;
- Available logs, measurements, photographs, samples, remains, test equipment state, and operator records;
- Actual and potential effect on safety, mission, customer, schedule, cost, performance, and delivered product.

Do not dismantle, clean, power-cycle, overwrite logs, swap parts, or repeat a destructive
test until the evidence impact is assessed and the action is authorized.

### 2. Apply emergency response

When harm may continue or worsen:

1. Identify and isolate suspect product;
2. Stop work, delivery, use, or recall product where justified;
3. Check related stock and the potentially affected population;
4. Apply a temporary control against the apparent cause;
5. Assess downstream and delivered-product risk;
6. Confirm severity and notify affected internal and external parties.

Keep emergency response separate from permanent corrective action. Remove it only after a
more effective root-cause action is implemented and verified.

### 3. Form and govern the team

Include functions that own or understand the affected design, process, test, production,
quality, supplier, use, and customer interfaces. Name:

- The team leader and decision authority;
- Each member's responsibility;
- Required resources, constraints, milestones, communication cadence, and escalation route;
- Customer, supplier, or other stakeholder representatives where affected.

The quality function controls the plan, conformity check, review, action tracking, and
retention of evidence. The responsible organization performs the investigation.

### 4. Decide the zeroing route

Apply **technical zeroing** when technical causes or consequences fall within the standard's
scope, including significant design, production, test, field, delivered-product, batch,
repeat, cost, schedule, performance, effectiveness, or system-application issues.

Apply **management zeroing** to:

- Repeated quality problems;
- Human-responsibility problems such as knowingly disregarding a rule or violating an operation;
- Problems caused by missing or inadequate rules;
- Problems designated for management zeroing by the authorized management system.

If both scopes apply, perform both and begin with technical zeroing. Record the route,
severity level, responsible organization, target dates, and rationale. Do not assume every
technical issue automatically requires punishment or management zeroing.

### 5. Perform technical zeroing

#### 5.1 Locate exactly — 定位准确

Determine the exact process, product, assembly, component, part, electronic component,
software element, interface, test equipment, or operation where the problem originates.
Reach the lowest failed unit supported by evidence and state its abnormal condition.

Check whether the source is the product, support equipment, test method, environment, or
operation. Use controlled substitution only when it preserves evidence and its result is
not mistaken for proof of mechanism.

**Gate:** The location and affected boundary are specific, evidence-backed, communicated,
and accepted by relevant parties. “The system failed” or “the supplier part was bad” does
not pass.

#### 5.2 Explain the mechanism — 机理清楚

Build the causal chain from abnormal factor to final phenomenon. Identify all root causes
and explain the physical, chemical, electrical, software, human-system, or process mechanism.
Analyze the problem from three views:

- **Product:** design, material, component, interface, software, equipment, and environment;
- **Process:** requirements, design, procurement, production, inspection, test, change,
  delivery, use, maintenance, and rework;
- **Organization:** responsibility, competence, communication, resources, oversight, and rules.

Use evidence to eliminate alternatives. Suitable tools include engineering analysis, failure
analysis, statistics, FTA, FMEA, Fishbone, 5-Why, process analysis, DOE, and comparison.

**Gate:** Every claimed root cause has objective support, alternative explanations have a
documented disposition, and the causal chain explains all material observations.

#### 5.3 Reproduce or verify — 问题复现

Prepare and approve a verification plan defining:

- Hypothesis and expected phenomenon;
- Test article and controlled configuration;
- Variables, realistic conditions, instrumentation, data to collect, and acceptance criteria;
- Safety limits, stop criteria, responsibilities, and required approvals.

Execute the plan, preserve raw records, analyze results, and obtain stakeholder agreement.
Prefer a controlled, mechanism-driven reproduction over an uncontrolled repeat.

For obvious one-off damage, destructive modes, or conditions that cannot be reproduced,
document why a reproduction test is inappropriate and use theory, analysis, simulation,
inspection, or an equivalent verification method. Do not convert “not reproduced” into
“no problem.”

**Gate:** The result confirms or rejects the location and mechanism. A failed confirmation
returns the investigation to localization or mechanism analysis.

#### 5.4 Prove effective measures — 措施有效

Separate:

- **Correction:** removes the detected problem from affected product;
- **Corrective action:** removes each root cause to prevent recurrence;
- **Preventive or deployment action:** protects similar products not yet affected.

For every root cause, define a specific, measurable, executable, and verifiable action with
an owner, due date, required resources, affected configuration, and verification plan.
Evaluate whether each action may create a new or worse risk.

Implement approved actions in controlled design, process, test, software, training, or
standard documents. Compare post-action results with the original problem evidence.

**Gate:** Evidence proves the actions are effective and sufficiently cover the operating
range without unacceptable adverse effects. If not, return to mechanism analysis.

#### 5.5 Extend the learning — 举一反三

Search for the same or similar mechanism across:

- The affected unit, batch, produced items, work in progress, and not-yet-produced items;
- Related parts, interfaces, software, equipment, processes, suppliers, and product families;
- Other programs, departments, and organizations exposed to the same cause.

State the search population, method, findings, decisions, actions, owners, and evidence.
Issue lessons learned or alerts through the quality function. Embed approved learning in
design rules, process instructions, test requirements, training, databases, and tools.

**Gate:** Horizontal deployment is based on mechanism and exposure, not merely on the same
part number, and every finding has a disposition.

### 6. Perform management zeroing

#### 6.1 Make the process clear — 过程清楚

Reconstruct the complete event timeline and the process that created and detected the
problem. Compare required versus actual activities, records, decisions, controls, and
handoffs. Identify management weaknesses or gaps.

#### 6.2 Make responsibility explicit — 责任明确

Assign organizational and individual responsibility from documented duties, authority,
actions, omissions, and evidence. Distinguish direct and indirect, primary and secondary,
leadership and execution responsibility. Do not use responsibility analysis as a substitute
for systemic root-cause analysis.

#### 6.3 Implement management measures — 措施落实

Address every management weakness with specific, checkable actions. Define the responsible
department and person, completion date, resources, implementation evidence, and effectiveness
check. Plan and fund medium- and long-term actions explicitly.

#### 6.4 Treat the problem seriously — 严肃处理

Use the event to educate personnel and improve management. Apply training, communication,
coaching, or other organizational learning as appropriate. Apply administrative or economic
penalties only under applicable rules for confirmed repeated problems, human-responsibility
problems, falsification, or concealment. Recognize proactive discovery and effective
prevention where organizational policy allows.

#### 6.5 Perfect the rules — 完善规章

Convert management actions into controlled management-system documents, standards,
procedures, work instructions, or governance mechanisms. Define revision content, owner,
approval, effective date, deployment, training, and compliance verification.

**Management gate:** The process, responsibility, actions, treatment, and rules are each
supported by evidence and address the identified management causes.

### 7. Report, review, and close

Use the [zeroing report template](assets/zeroing-report-template.md). For formal work, include
the report sections and evidence described in Annex A of GB/T 29076—2021.

Before closure, an authorized review must verify:

- Route selection and scope were correct;
- Localization and mechanism are evidence-backed;
- Reproduction or alternative verification is adequate;
- Every technical and management cause has an implemented action;
- Effectiveness and adverse effects were evaluated;
- Horizontal deployment and document changes are complete;
- Reports, evidence identifiers, signatures, approvals, residual issues, and recommendations
  are complete.

Close and disband the team only after all actions are implemented and verified, lessons are
deployed, and affected parties are told that zeroing is complete.

If complete zeroing is not feasible for a flight test or in-orbit issue, document the reason,
analyze all plausible root causes, implement comprehensive controls against them, identify
residual risk, and obtain the required approval. Never label an unresolved hypothesis as a
confirmed cause.

## Supporting Methods and Related Skills

Read [engineering methods](references/engineering-methods.md) when choosing troubleshooting,
reproduction, measure-verification, controlled-experimentation, or workflow-control methods.
These methods are advisory and cannot weaken a standard gate.

- Use [NCR writing](../../documentation/ncr-writing/) to document a detected nonconformance
  when the organization's quality system requires an NCR before zeroing.
- Use [Is/Is-Not](../is-is-not-scoping/) to define the observed boundary.
- Use [Fishbone](../fishbone-analysis/) to generate candidate causes.
- Use separate [5-Why](../5why-root-cause/) chains for distinct causal paths.
- Use [PFMEA](../../risk-analysis/pfmea-process/) or
  [DFMEA](../../risk-analysis/dfmea-design/) to evaluate action risk and update prevention
  controls, and update the [Control Plan](../../planning/control-plan/) when process controls
  change.
- Use [CAR](../../documentation/car-corrective-action/) when the organization requires a
  separate corrective-action record for implementation and effectiveness follow-up.
- Use [8D](../8d-problem-solving/) when a customer or sector requires the 8D format; do not
  claim that an 8D automatically satisfies GB/T 29076—2021 without checking every zeroing gate.

Framework handoff:

`Detection / NCR → zeroing route decision → technical and/or management zeroing → corrective
action → FMEA / Control Plan / controlled-document updates → evidence review → closure`

## Validation Criteria

Reject closure if any answer is “no”:

1. Is the exact failure location proven to the lowest practicable unit?
2. Does the mechanism explain the observations and all confirmed root causes?
3. Was the mechanism reproduced or otherwise verified with justified evidence?
4. Does each action map to a confirmed cause and have implementation evidence?
5. Was action effectiveness verified over a relevant range and checked for adverse effects?
6. Was the exposed population searched across product, process, and organization?
7. Where management zeroing applies, are process, responsibility, actions, treatment, and
   rules complete?
8. Are evidence, controlled-document revisions, reviews, approvals, residual risks, and
   stakeholder communications traceable?

## Common Mistakes

- Treating repair, rework, sorting, inspection, or emergency containment as root-cause action;
- Confusing failure location with root cause or a plausible cause with a proven mechanism;
- Repeating a test without new instrumentation, controlled variables, or a stated hypothesis;
- Choosing only one convenient root cause when evidence supports multiple causes;
- Using “operator error” or “supplier problem” as the end of analysis;
- Punishing people by default instead of correcting the management system;
- Declaring “no similar issue found” without defining the searched population and method;
- Closing tasks in a workflow system and assuming the quality problem is therefore zeroed;
- Changing “完善规章” into the weaker phrase “improve the mechanism” without controlled documents;
- Adding a sixth normative technical-zeroing requirement; knowledge extraction belongs within
  horizontal deployment and document institutionalization.

## Output Content

Produce, as applicable:

1. Problem and impact statement;
2. Emergency response and affected-population record;
3. Team, plan, zeroing-route decision, and milestones;
4. Technical zeroing report with five evidence gates;
5. Management zeroing report with five evidence gates;
6. Cause-to-action-to-evidence traceability matrix;
7. Horizontal-deployment register;
8. Residual-risk and unresolved-item register;
9. Review checklist, approval decision, and closure statement.

## Output Format

At the start of each use, ask the user:

> "How would you like to receive the output?
> **A** — Structured Markdown (formatted tables and sections, ready to copy)
> **B** — Plain tables (simplified structure for Excel or Word)
> **C** — Narrative report (flowing text for a formal document or email)
>
> Default: A."

Adapt all output sections to the chosen format. If the platform or session context already defines a format preference, skip this question.

## Reference Files

- [GB/T 29076—2021 method guide](references/gbt-29076-2021-method-guide.md)
- [Engineering methods and research notes](references/engineering-methods.md)
- [Technical and management zeroing report template](assets/zeroing-report-template.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-04 | @Crow12138 | Initial draft based on GB/T 29076—2021 |

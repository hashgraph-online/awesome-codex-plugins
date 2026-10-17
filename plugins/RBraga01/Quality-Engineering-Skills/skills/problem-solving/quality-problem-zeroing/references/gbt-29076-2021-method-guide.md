---
name: gbt-29076-2021-method-guide
type: reference
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

# GB/T 29076—2021 Method Guide

## Contents

1. [Authority and scope](#authority-and-scope)
2. [Clause traceability](#clause-traceability)
3. [Key terms](#key-terms)
4. [Application decision](#application-decision)
5. [Roles and governance](#roles-and-governance)
6. [Standard sequence](#standard-sequence)
7. [Technical zeroing evidence](#technical-zeroing-evidence)
8. [Management zeroing evidence](#management-zeroing-evidence)
9. [Reports and closure](#reports-and-closure)
10. [Interpretation checks](#interpretation-checks)
11. [Source](#source)

## Authority and Scope

GB/T 29076—2021, *Execution requirements of quality problem closed loop for
aerospace product*, is the normative basis for this skill. It applies to quality
problems occurring during aerospace product design, production, test, and use.

The standard describes quality problem zeroing as an activity that analyzes the
causes and mechanisms of an occurred quality problem from technical and management
perspectives and takes action to eliminate the problem fundamentally and prevent
recurrence.

The standard's five technical and five management requirements are controlling.
Industry papers, enterprise practices, software workflows, 8D, and other root-cause
methods may support execution but do not override scope, terminology, or closure.

## Clause Traceability

| Standard location | Subject | Skill implementation |
|-------------------|---------|----------------------|
| 3.1–3.17 | Terms and definitions | Key terms and terminology controls |
| 4.1 | Principles | Dual-route rule, technical-first sequence, three-view analysis |
| 4.2 | Technical and management scope | Application decision |
| 4.3 | Responsibilities | Roles and governance |
| 4.4 | Plans, resources, review, and major gates | Governance and closure |
| 5.2–5.4 | Report, emergency response, and team | Workflow steps 1–3 |
| 5.5–5.9 | Zeroing, reports, review, and team closure | Workflow steps 4–7 |
| 6.1–6.5 | Five technical requirements | Technical evidence requirements |
| 7.1–7.5 | Five management requirements | Management evidence requirements |
| Annex A | Report contents | Report and evidence structure |
| Annex B | Example report cover | Organization-specific cover control |

## Key Terms

| Term | Working interpretation |
|------|------------------------|
| Quality problem | A failure, defect, accident, or other undesired condition |
| Root cause | A source event, behavior, or condition that produces an actual or potential undesired state; one problem may have multiple root causes |
| Technical zeroing | Evidence-based completion of location, mechanism, reproduction, effective measures, and horizontal deployment |
| Management zeroing | Evidence-based completion of process reconstruction, responsibility, management measures, serious treatment, and rule improvement |
| Repeated quality problem | A problem already experienced by the organization, or notified from another organization, that occurs again as the same class of problem |
| Human-responsibility problem | A problem caused by human factors such as knowingly disregarding rules or violating operations |

Do not reduce “quality problem zeroing” to management zeroing alone. “Double-five
zeroing” refers to the two coordinated five-requirement systems.

## Application Decision

### Technical zeroing scope

Screen for technical zeroing when the problem includes:

- A design issue affecting development schedule, interface design, performance, or production rework;
- A design or production issue causing major economic loss;
- A technically caused batch component or raw-material issue;
- A problem discovered after a lower-level product is delivered to the next level;
- A batch or repeated production problem;
- A technical test problem causing test failure or product damage;
- A problem found at a launch site, range, or other field location;
- A delivered-product problem affecting use;
- A problem designated by the authorized program management system;
- Degradation of cost, schedule, effectiveness, or system application.

### Management zeroing scope

Screen for management zeroing when the problem is:

- Repeated;
- Caused by confirmed human responsibility;
- Caused by absent or inadequate rules;
- Designated by the authorized program management system.

### Dual route

When both scopes apply:

1. Complete both routes;
2. Start technical zeroing first;
3. Do not use technical conclusions to bypass management analysis;
4. Permit coordinated or joint review only if every requirement remains visible and evidenced.

Zeroing may be graded by severity, consequence, product level, and management level,
but grading must not erase required evidence.

## Roles and Governance

| Role | Standard responsibility |
|------|-------------------------|
| Top management | Accountable for the organization's zeroing work |
| Program command or management system | Organizes and checks program zeroing |
| Test team leader | Organizes zeroing for major tests or launch missions |
| Quality function | Plans, checks report conformity, organizes review, tracks actions, and retains evidence |
| Responsible organization | Performs zeroing and prepares the reports |
| Zeroing team | Executes the cross-functional investigation and action plan |

Create a plan and provide adequate resources. Review each completed zeroing activity.
At major transition, acceptance, delivery, transfer, or launch gates, summarize and
classify open and completed zeroing work and conduct checks or reviews where needed.

## Standard Sequence

1. **Problem report:** communicate promptly, protect evidence, and record product and event data.
2. **Emergency response:** isolate, stop, inspect, recall, reduce immediate recurrence, assess risk and severity, and communicate with affected parties.
3. **Team formation:** appoint a leader, include relevant functions and stakeholders, and define authority and responsibilities.
4. **Technical zeroing:** execute the five technical requirements where applicable.
5. **Management zeroing:** execute the five management requirements where applicable.
6. **Reports:** complete technical and/or management reports with evidence and signatures.
7. **Review:** determine whether the work is appropriate, complete, and effective.
8. **Closure:** after all measures are implemented and verified and horizontal deployment is complete, notify relevant parties and disband the team.

## Technical Zeroing Evidence

### Exact location

Required evidence should show:

- The observed phenomenon and exact affected location;
- The lowest failed product or element and its abnormal state;
- Whether the source lies in product, equipment, test method, environment, or operation;
- The investigation plan, checks, measurements, substitutions, analyses, and stakeholder agreement;
- Customer or mission effect.

### Clear mechanism

Required evidence should show:

- All material observations and the principal problem;
- Candidate causes and elimination logic;
- Every confirmed root cause;
- The causal path from the abnormal factor at the lowest unit to the final failure mode;
- Supporting calculations, tests, analyses, statistics, inspections, or specialist findings;
- Communication and agreement with affected parties.

Keep direct cause, contributing condition, root cause, and management cause distinct.

### Problem reproduction

Normally prepare an approved plan, execute it under control, preserve records, analyze
the result, and obtain confirmation. A valid reproduction tests the claimed mechanism,
not just visual similarity.

When reproduction is unsafe, destructive, impossible, or unnecessary for an obvious
one-off damage mechanism, explain the reason and use the strongest feasible theoretical,
simulation, inspection, or analogous evidence. The technical report must disclose the
limitation.

### Effective measures

Show separately:

- Correction of affected product;
- One or more corrective actions covering every root cause;
- Selection rationale and risk of new or worse effects;
- Approved implementation plan, owners, dates, and configuration;
- Verification plan, raw evidence, result, and effectiveness evaluation;
- Controlled technical-document or standard changes;
- Decision to continue or end emergency response.

If effectiveness is inadequate, return to mechanism analysis rather than adding unsupported
layers of inspection.

### Horizontal deployment

Show:

- The lesson or warning extracted from the mechanism;
- The searched population and exposure logic;
- Results for produced, in-process, and not-yet-produced product;
- Actions for similar designs, processes, tests, tools, suppliers, or organizations;
- Technical standards or clauses requiring improvement;
- Updates to design, process, test, training, information systems, and tools;
- Notifications, responses, and evidence from other affected organizations.

## Management Zeroing Evidence

### Clear process

Build a time-ordered record of creation, development, detection, reporting, and response.
Compare process requirements, actual execution, and records. Identify management weaknesses
or missing controls.

### Explicit responsibility

Use process evidence and documented duties to identify responsible organizations and
persons. Distinguish direct/indirect, primary/secondary, and leadership/execution
responsibility. Avoid unsupported blame and retrospective expectations not present at the
time of the event.

### Implemented measures

For each management weakness, show a concrete action, owner, responsible department, due
date, resources, completion evidence, and effectiveness check. Give medium- and long-term
actions an approved plan.

### Serious treatment

The primary purpose is education and management improvement. Show how the organization
learned and communicated the lesson. Apply penalties only under applicable organizational
rules for confirmed repeated problems, human-responsibility problems, falsification, or
concealment. The standard also permits recognition of proactive discovery and prevention.

### Perfected rules

Show controlled revisions or new management-system documents, standards, procedures, or
work instructions. Include content, owner, approval, effective date, distribution, training,
and implementation verification.

## Reports and Closure

### Technical report content

Include:

1. Problem overview and emergency response;
2. Localization process, evidence, result, responsibility, and emergency-response effect;
3. Root causes, failure mode, mechanism, analysis methods, and evidence;
4. Reproduction or alternative-verification process and result;
5. Correction, corrective actions, implementation, verification, and document changes;
6. Horizontal deployment, lessons learned, and document list;
7. Conclusion, residual issues, and recommendations;
8. Identified evidence list.

For trial or formal products after delivery, and for technical zeroing arising from
vehicle/system-level tests, obtain the required next-level designer co-signature. For
purchased or outsourced product, obtain the required co-signatures from the ordering
organization and the organization that issued the task requirements.

### Management report content

Include:

1. Event and process overview;
2. Management cause and responsibility analysis;
3. Measures and implementation;
4. Treatment and organizational learning;
5. Rule improvement and deployment;
6. Conclusion, residual issues, and recommendations;
7. Identified evidence list.

Obtain co-signatures from the quality function and relevant departments and approval from
top management. One management report may cover the same class of management problem across
multiple products only when every affected product is identified in the report.

### Closure test

Zeroing is complete only when:

- The applicable report is complete and properly signed, checked, reviewed, or approved;
- All improvement measures are implemented;
- Effectiveness is verified;
- Horizontal deployment is complete;
- Evidence is retained and traceable.

For a flight-test or in-orbit problem that cannot be completely zeroed, prepare a signed
analysis report explaining why. Analyze all plausible root causes, apply comprehensive
controls, disclose residual risk, and retain the issue for follow-up.

## Interpretation Checks

| Accept | Reject |
|--------|--------|
| Exact failed unit and abnormal state supported by evidence | “The whole system failed” as localization |
| Causal mechanism linking the root cause to every material phenomenon | A likely cause selected by consensus alone |
| Approved reproduction or justified alternative verification | “Could not reproduce, therefore no defect” |
| Implemented action mapped to each confirmed root cause | Sorting or added inspection presented as the permanent fix |
| Mechanism-based search of an explicitly defined exposed population | “Checked similar products” without scope or records |
| Responsibility based on contemporaneous duties and objective evidence | Punishment used as a substitute for management-cause analysis |
| Controlled rule revision with implementation evidence | A meeting notice or training record as the only systemic action |
| Closure after effectiveness, deployment, review, and evidence are complete | Software task status used as proof of zeroing |

Escalate rather than close when safety or mission risk remains uncontrolled, delivered product
may be affected, stakeholders reject the causal conclusion, actions are overdue, evidence is
contradictory, or complete zeroing is infeasible without an approved residual-risk path.

## Source

- GB/T 29076—2021, *航天产品质量问题归零实施要求 / Execution requirements of quality problem closed loop for aerospace product*. Published 2021-08-20; implemented 2022-03-01. This guide paraphrases the standard for operational use and is not a substitute for the official text.

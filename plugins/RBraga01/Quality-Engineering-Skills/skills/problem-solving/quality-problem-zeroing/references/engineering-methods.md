---
name: engineering-methods
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

# Engineering Methods for Quality Problem Zeroing

## Contents

1. [Use and limits](#use-and-limits)
2. [Evidence-centered localization](#evidence-centered-localization)
3. [Troubleshooting methods](#troubleshooting-methods)
4. [Mechanism-driven reproduction](#mechanism-driven-reproduction)
5. [Measure verification](#measure-verification)
6. [Layered horizontal deployment](#layered-horizontal-deployment)
7. [Controlled experimentation](#controlled-experimentation)
8. [Workflow control](#workflow-control)
9. [Method selection checks](#method-selection-checks)
10. [Related skills](#related-skills)
11. [Research sources](#research-sources)

## Use and Limits

This reference converts useful engineering ideas from the supplied research papers into
optional working methods. It is not normative. Apply GB/T 29076—2021 when this reference
differs from the standard.

Do not import broad claims as universal facts. In particular:

- Do not assume every fault has a detectable precursor;
- Do not assign a universal probability to single-point or multi-point failures;
- Do not require physical reproduction when the standard permits justified alternative evidence;
- Do not treat “thought zeroing,” “zeroing-style trial and error,” or a sixth zeroing step as a standard term;
- Do not equate workflow completion with evidence-based closure.

## Evidence-Centered Localization

Preserve and analyze three evidence families:

| Evidence family | Main use | Caution |
|-----------------|----------|---------|
| Phenomena | Establish what changed, when, and under which conditions | Separate causal observations from coincident observations |
| Physical evidence or remains | Locate damage, identify failure mode, and infer direction of propagation | Preserve custody and avoid destructive examination before approval |
| Data | Reconstruct sequence, compare states, quantify thresholds, and test hypotheses | Verify clock alignment, units, calibration, completeness, and data lineage |

Use physical, mathematical, and system-level analysis together:

- **Physical analysis:** determine whether the proposed cause can produce the observed effect;
- **Mathematical analysis:** quantify relationships, distributions, timing, thresholds, or probability;
- **System analysis:** inspect interactions, interfaces, shared resources, environment, and emergent behavior.

FTA can connect the top event to candidate bottom events. Keep each surviving fault mode
visible when more than one remains plausible.

## Troubleshooting Methods

### Elimination

Decompose the system by structure, function, information, environment, support equipment,
and human interaction. Eliminate a candidate only through valid logic or a controlled test.
Record the evidence for each eliminated branch.

### Comparison

Use one of three patterns:

1. **Conditions unchanged:** repeat with added instrumentation to test repeatability and gain new information;
2. **One condition changed:** alter one credible variable while holding the rest stable;
3. **Swap:** exchange comparable items under the same state and environment to narrow location.

A swap can locate a fault efficiently but usually does not prove the mechanism. Avoid
uncontrolled part swapping that destroys the original state.

### Causality

Distinguish:

- Cause from correlation;
- Cause from consequence;
- Trigger from enabling condition;
- Direct cause from root cause;
- Technical cause from management cause.

Write each causal link as a testable statement: under conditions **C**, factor **A** produces
change **B** through mechanism **M**, resulting in observed effect **E**.

### Quantitative threshold analysis

Search for small changes that accumulate or cross a functional threshold. Compare:

- Earlier versus later operation;
- Successful versus failed units;
- Laboratory versus actual field conditions;
- Recorded parameters versus the successful operating envelope.

Choose measurement bandwidth, sampling, time resolution, and physical units that can reveal
the proposed mechanism. “Within the recorded limit” is weak evidence when the instrument
cannot observe the relevant transient.

## Mechanism-Driven Reproduction

Design the reproduction to challenge a named hypothesis. A useful plan states:

- What root-cause hypothesis is being tested;
- Which phenomenon should appear if it is true;
- Which phenomenon should not appear if it is false;
- Which variables are controlled and which are changed;
- How actual operating energy, timing, environment, loading, interfaces, and configuration are represented;
- How fidelity limitations affect confidence.

An uncontrolled recurrence adds value only when it captures new information. A visually
similar failure under materially different conditions may demonstrate a possible failure
mode without proving the actual event mechanism.

Use component-level tests for efficiency when coupling is demonstrably limited. Use
subsystem- or system-level tests when interfaces, environment, timing, or combined loads are
essential to the mechanism. Choose the lowest level that preserves causal fidelity.

## Measure Verification

Test three properties:

1. **Effective:** removes the root cause or prevents its effect;
2. **Sufficient:** covers the required operating range, variation, life, and affected population;
3. **Non-harmful:** does not create unacceptable new risks or degrade other functions.

Verification should include:

- Correct product and test configuration;
- Suitable equipment, method, and realistic environment;
- Before/after comparison against the original evidence;
- Whole-system observation where side effects may occur;
- Defined acceptance criteria and sample or exposure rationale;
- Regression, environmental, interface, boundary, and life testing as risk requires.

Record known limits. “No failure observed” is not automatically proof when exposure was too
small or conditions were not representative.

## Layered Horizontal Deployment

Scale the search by mechanism, severity, and exposure:

1. Affected item and batch;
2. Same product or program;
3. Other products or programs in the department;
4. Organization-wide processes and design families;
5. External suppliers, customers, partner organizations, or industry where the mechanism is shared.

For each layer, record the searched population, selection logic, result, action, and closure
evidence. Convert individual learning into controlled design criteria, process restrictions,
test rules, prohibited practices, training, and searchable knowledge.

Treat “extract guidelines and lessons” as a deepening of horizontal deployment and
institutionalization—not as a sixth normative technical-zeroing requirement.

## Controlled Experimentation

Trial-and-error and zeroing are not substitutes:

- Controlled experimentation is a development strategy for learning under uncertainty;
- Zeroing is the formal closed-loop response to an occurred quality problem.

Permit bounded experimentation only when:

- Safety and legal limits are protected;
- Failure consequences are contained, reversible, and acceptable;
- The test has a learning objective, instrumentation, success/failure criteria, and stop rules;
- Configuration and data are traceable;
- A failed trial will trigger screening for formal zeroing.

Do not use experimentation to excuse a known defect, repeated problem, uncontrolled safety
risk, delivered-product exposure, missing evidence, or avoidance of a required zeroing
review. As consequence, irreversibility, maturity, and customer exposure increase, strengthen
formal zeroing and release gates.

## Workflow Control

Digital workflows can:

- Decompose a zeroing case into reusable and parallel subflows;
- Assign roles and due dates;
- Route technical and management branches dynamically;
- Aggregate parent/child status;
- Preserve forms, evidence identifiers, decisions, and audit trail;
- Prevent missing or delayed tasks.

Do not define “closed” as “all tasks clicked complete.” Use evidence gates and review states:

- Not started;
- In progress;
- Waiting for evidence;
- Ready for review;
- Rejected or returned for rework;
- Verified;
- Closed.

The top-level workflow must include action implementation, effectiveness verification,
horizontal deployment, document change, review, and approval. If these are modeled as
external processes, the zeroing case must remain open until their evidence returns.

## Method Selection Checks

Before accepting a method or result, ask:

1. What hypothesis or decision will this method test?
2. What evidence can confirm it, and what evidence can disprove it?
3. Does the method preserve the original product state and data lineage?
4. Are variables, configuration, environment, timing, and instrumentation controlled?
5. Is the selected test level adequate for the interfaces and coupling involved?
6. Does the result locate the fault, prove the mechanism, or only narrow the search?
7. Could the action create a new failure mode or hide the original one?
8. Is the exposure sufficient to support the claimed effectiveness?
9. Which products, processes, organizations, and documents inherit the learning?
10. Which GB/T 29076—2021 gate does the result support?

Reject a method result that cannot answer the final question. It may be useful engineering
work, but it is not yet zeroing evidence.

## Related Skills

- Use [Is/Is-Not](../../is-is-not-scoping/) for boundary comparisons.
- Use [Fishbone](../../fishbone-analysis/) to structure candidate causes.
- Use [5-Why](../../5why-root-cause/) to deepen one causal path at a time.
- Use [PFMEA](../../../risk-analysis/pfmea-process/) or
  [DFMEA](../../../risk-analysis/dfmea-design/) to evaluate action risk and institutionalize
  prevention.
- Use [Control Plan](../../../planning/control-plan/) when a process control changes.

## Research Sources

- Fan Huitao, Zhang Tonghe, Xu Yanke. “General Method for Fault Return-to-Zero of Equipment System.” *Strategic Study of CAE / 中国工程科学*, 2025, 27(1): 248–257. DOI: 10.15302/J-SSCAE-2024.07.024.
- Lu Jiangong, Zhang Hua, Liu Huan. “Choice Logic between Zeroing and Trial-and-Error Approaches in Aerospace Field.” *Quality and Reliability*, 2025(3), total issue 237.
- Wen Jingqian, Li Qing. “Workflow-based Closed Loop Process Control for Aircraft Quality.” Beijing University of Aeronautics and Astronautics; manuscript received 2008-09-24 and revised 2009-02-19.

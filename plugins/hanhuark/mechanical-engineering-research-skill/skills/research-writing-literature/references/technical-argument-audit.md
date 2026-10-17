# Technical Argument Audit

Use this reference when a manuscript, proposal, report, review, response to reviewers, or student draft makes an equation, figure, model, experiment, simulation, or literature claim carry the argument. Apply it before a final prose-only edit. Its purpose is to test whether the writing communicates a defensible technical argument, not merely polished sentences.

## Evidence Labels

For each consequential statement, retain the correct status: **measured**, **reported**, **simulated**, **derived**, **assumed**, **inferred**, **illustrative**, **proposed**, or **independently validated**. Do not promote a reported result into a direct measurement, a correlation into a governing law, or an interpretation into a demonstrated mechanism.

## 1. Equation-to-Physics Audit

For every equation that supports a main claim, answer these questions in the surrounding prose or caption:

1. **Role:** What does the equation estimate, test, conserve, fit, or define?
2. **Physical basis:** Is it derived from a force balance, energy balance, mass conservation, momentum balance, constitutive relation, empirical regression, numerical discretization, or dimensionless scaling?
3. **Variable meaning:** Why does each influential parameter appear physically? Do not describe an equation as a bare list of symbols.
4. **Assumptions and omissions:** Which forces, mechanisms, boundary conditions, geometry effects, property variations, or transient terms are neglected or embedded in a fitted coefficient?
5. **Validity:** What fluid, geometry, regime, orientation, pressure, scale, contact condition, or data range supports its use?
6. **Source and verification:** Is the original model or an appropriate secondary source cited? Has dimensional consistency, a limiting case, and comparison with relevant data been checked?

State the governing mechanism in ordinary technical language. For example, a bubble-departure correlation should say whether it balances buoyancy against capillarity, rather than only naming density difference, gravity, surface tension, and contact angle. Explain why density difference produces buoyancy and how contact angle changes the capillary-force geometry when those details matter to the argument.

Do not claim a correlation is a complete physical model when it is a baseline estimate. Name its omitted effects when they can change the conclusion, such as contact-line dynamics, confinement, shear, growth inertia, local geometry, or transient thermal fields.

## 2. Claim-Evidence Ledger

Build a compact ledger for headline claims, conclusions, and contentious statements before finalizing a section. Keep it in working notes unless the user requests a table in the deliverable.

| Claim | Evidence and status | Source, figure, equation, or dataset | Conditions and limitation | Needed action |
| --- | --- | --- | --- | --- |
| A specific mechanism changes an outcome | Measured trend plus inferred mechanism | Fig. X and Ref. Y | One fluid and heat-flux range; alternative mechanisms remain possible | Add a discriminating measurement or narrow the claim |

Use the ledger to check that every conclusion has a traceable evidence path. When a claim combines several evidence types, state that explicitly. For example, distinguish a measured departure diameter from a force-balance interpretation of that diameter.

## 3. Citation-Support Audit

For each citation-bearing sentence, verify:

- The cited source supports the exact nearby claim, not merely the general topic.
- A model, correlation, equation, experimental method, or dataset is credited to its original source or an appropriate authoritative review.
- Background references are grouped by a common mechanism, method, material, or evidence type; do not attach one broad citation range to unrelated categories.
- Narrative citations use `FirstAuthor et al.` for multi-author papers unless the target style requires otherwise.
- A paper summary states the method and takeaway efficiently, then identifies the group-level limitation or gap. Do not repeat `the authors did X` followed by `their results showed Y` when one sentence can state both.

When support is unavailable, change the sentence to what the cited source actually reports, add the missing source, or label the statement as a proposal or inference. Do not leave an authoritative-sounding unsupported generalization.

## 4. Methods And Reproducibility Audit

Before calling methods complete, identify the information needed for an informed reader to reproduce or audit the result:

- system boundary, geometry, materials, fluid, initial and boundary conditions, and operating path;
- instrumentation or numerical method, calibration, resolution, sampling, mesh/time-step treatment, and data-reduction equations;
- sample size, repeats, inclusion/exclusion rules, uncertainty/variability treatment, and relevant property source;
- model assumptions, their justification, implementation choices, and validation or baseline case;
- preprocessing, code version, data provenance, and any human labeling or manual intervention.

Avoid a catalog of equipment specifications with no connection to the measured quantity. Conversely, do not omit a setup detail that controls the relevant heat path, flow regime, contact condition, or uncertainty.

## 5. Figure And Table Narrative Audit

Give every figure, table, and equation a narrative job. Introduce it by explaining what question it resolves, then guide the reader through:

1. **What is shown or compared?**
2. **What is observed?** Include the relevant magnitude, condition, or uncertainty.
3. **Why does it occur?** State the supported physical explanation and separate it from inference.
4. **How does it compare?** Position it against theory, prior work, an analytical bound, a baseline, or an alternative design when appropriate.
5. **What follows?** State the bounded design or scientific implication.

Captions should define variables, units, symbols, sample condition, and uncertainty notation needed to interpret the visual independently. Do not use a figure or equation as decoration; remove it or give it a distinct analytical role.

## 6. Technical-Term Legitimacy Audit

Review unfamiliar labels, long modifier chains, and convenient compounds before retaining them.

- Is the term standard in the target field, explicitly defined, or necessary to distinguish a real concept?
- Does it name a physical quantity, method, mechanism, or decision more clearly than ordinary technical wording?
- Would a domain colleague understand the subject and action without unpacking a catalog of adjectives?

Do not ban accepted terminology such as `two-phase flow`, `high-speed imaging`, or a required new definition. Replace only labels that conceal the mechanism or add formality without precision.

## 7. Skeptical Reviewer Challenge

Before submission, challenge the draft as a technically informed reviewer would:

- What alternative mechanism or confounder could explain the trend?
- Which assumption has the greatest leverage on the conclusion?
- Are compared studies or designs actually matched in geometry, fluid, regime, boundary conditions, and metric definition?
- What observation would falsify the stated interpretation?
- Does the evidence establish causation, association, feasibility, or only a proposed explanation?
- Is a limitation local to one result, or does it change the headline conclusion?

Resolve the issue through analysis, data, validation, modeling, or an explicit scope boundary. Do not answer a methodological challenge only by adding cautious language.

## 8. Student-Facing Feedback Format

For high-priority comments, use:

```text
Scientific issue: [missing mechanism, unsupported assumption, invalid comparison, or evidence gap]
Why it matters: [how this affects interpretation or reproducibility]
Concrete revision: [the smallest defensible revision]
Evidence needed: [measurement, derivation, source, validation, sensitivity test, or author decision]
```

Use this format to teach the next improvement without implying authorship, fabricating a correction, or burying the scientific issue under stylistic comments.

## Completion Check

Before delivery, confirm that:

- each headline claim has a traceable evidence path;
- each important equation has a stated physical role, assumptions, validity boundary, and source;
- methods contain the details needed to reproduce or audit the reported result;
- figures, tables, and captions advance the argument rather than repeat the text;
- literature comparisons are mechanism-aware and like-for-like;
- unresolved evidence needs are named directly.

Run the technical-prose clarity audit afterward to improve readability without weakening technical meaning.

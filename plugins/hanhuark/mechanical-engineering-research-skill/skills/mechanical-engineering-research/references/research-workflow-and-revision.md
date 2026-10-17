# Integrated Research Workflow And Revision

Use this reference for a substantial manuscript, review article, proposal, thesis chapter, or major revision that needs more than one focused skill. It provides a lightweight workflow; it does not require a multi-agent pipeline, fixed number of passes, or a new artifact for a small, bounded task.

## Choose The Workflow Depth

- **Focused route:** use the specialist skill directly for a figure discussion, methods paragraph, citation check, technical calculation, or local prose revision.
- **Integrated route:** use the stages below when the work combines literature, analysis, drafting, review, or a response to external comments.
- **Human-pause condition:** stop for an author decision when the evidence permits two materially different research positions, a new claim would need unpublished data or confidential material, or the target venue imposes a requirement that conflicts with the proposed structure.

Do not treat completion of every stage as evidence that the scientific claim is correct. Each stage is a traceability and decision aid.

## Seven Stages

### 1. Frame The Decision

Record the target reader, document genre, decision the document must support, research question, contribution boundary, and non-negotiable evidence constraints. For a manuscript, distinguish the field-wide gap from the specific contribution. For a proposal, distinguish the need, hypothesis, work plan, and expected evidence.

Ask: what should an informed reader understand, decide, or be able to do after this document? Do not begin with a generic outline or a stock importance statement.

### 2. Build The Evidence Map

Before drafting prose, map the claims that the document must support. For each consequential claim, record:

- the claim and its intended strength;
- the supporting source, data, calculation, figure, or equation;
- the applicable system, regime, assumptions, and uncertainty;
- whether the claim is measured, reported, simulated, derived, assumed, proposed, or inferred; and
- the section, figure, table, or response item where it will be used.

Use a compact ledger, not a ceremonial database. A claim without identified support is either a research task, a bounded hypothesis, or text that should not be drafted as a conclusion.

### 3. Design The Narrative Architecture

Develop the section sequence and the job of each section before writing full prose. Give every major section a reader takeaway and an evidence basis. For introductions, use the chain of importance, state of the art, remaining issue, reason it persists, proposed advance, and significance. For results, organize around physical questions and evidence rather than the chronological order in which tests were run.

An outline is ready only when the argument can move from one section to the next without relying on vague transitions such as "moreover" or "conversely." Each section should answer a question the preceding section naturally raises.

### 4. Develop The Technical Content

Perform the analysis, experiment planning, model check, literature comparison, code development, or figure construction needed to close the evidence gaps. Start from a baseline case and a hypothesis-driven comparison where applicable. State assumptions before presenting a model, and explain why each assumption is reasonable for the intended regime.

Do not use prose to hide an unfinished calculation, weak validation, missing diagnostic, or incompatible comparison.

### 5. Draft From Evidence To Reader

Draft each section from its evidence map and reader takeaway. A paragraph normally begins with its central technical purpose; later sentences add evidence, mechanism, comparison, limitation, or implication. Explain equations through the governing balance or process, not by listing variables. Explain figures through description, observation, physical explanation, and comparison with prior work where relevant.

Use the smallest relevant specialist skill, especially `research-writing-literature`, `research-data-analysis`, and `thermal-fluid-analysis`. Use the reader-focused clarity audit only after the technical content exists; clarity editing cannot supply missing physics or evidence.

### 6. Audit And Revise

Run separate checks for:

1. **Claim support:** Does every consequential statement match its source, data, model, or stated assumption?
2. **Technical validity:** Are units, definitions, assumptions, system boundaries, uncertainty, and applicability limits consistent?
3. **Reader path:** Can the intended reader identify the purpose, mechanism, evidence, and conclusion of each section on a first reading?
4. **Citation and artifact integrity:** Do citations support the exact claim, and do figures, tables, captions, equations, and cross-references still agree after revision?
5. **Style and economy:** Are redundancy, vague generalities, modifier-heavy labels, unfamiliar coined terms, and empty transitions removed without reducing technical meaning?

For external review comments, convert each comment into a revision roadmap before changing the prose. A useful row contains: comment or issue, severity, scientific diagnosis, required action, evidence needed, manuscript location, response wording, owner, and verification condition. A response is complete only when the revision and evidence address the diagnosed concern, or the response explains a defensible boundary that the available evidence cannot cross.

Use `reviewer-author-loop` for a deliberate critique-revision-verification cycle. It is a specialist stage in this workflow, not a competing end-to-end alternative.

### 7. Package And Verify

Compile or render the actual deliverable. Inspect the output rather than relying on source text alone. Confirm that citations, equation and figure numbering, captions, units, PDF layout, supplementary material, and clean/marked versions are consistent. Record what was verified, what remains unverified, and the smallest next evidence need.

## Literature Evidence Map

For a nontrivial literature section or review, keep a compact matrix that distinguishes:

- **foundational sources:** the theories, measurements, or methods that define the field;
- **representative sources:** the studies that establish the main categories or comparison range;
- **key comparison sources:** the work most directly relevant to the user's system, regime, diagnostic, or model;
- **background sources:** category-level acknowledgment, not a sentence-by-sentence annotated bibliography; and
- **conflicting or limiting sources:** results that challenge a simple conclusion or expose a boundary.

For each category, state the mechanism or question it addresses, the evidence type, the applicability boundary, and the limitation that motivates the next part of the story. Search backward from seminal references and forward through their citing work. When a source cannot be interpreted from text alone, use a calculation, digitization, CAD sketch, small baseline simulation, or expert question to test the interpretation.

## Minimal Handoff Record

When work will continue in another session or be shared with a collaborator, leave a short record containing:

- current document purpose and target reader;
- verified source and data boundaries;
- decisions made and decisions still open;
- claims or figures that require additional evidence;
- files, code, and commands used to generate results; and
- next action and its acceptance condition.

This record should help the next person resume the scientific work without presenting planned work as completed work.

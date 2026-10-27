# Pre-Submission Checklist for Systems Papers

Comprehensive self-check before submitting to OSDI, SOSP, ASPLOS, NSDI, and EuroSys. Combines community best practices (MLNLP-World/Paper-Writing-Tips, RU-System/Paper_Writing_Tips) with systems-specific and academic integrity checks.

---

## Stage 1: Structural Completeness

### Thesis & Contributions
- [ ] Paper has a clear thesis statement: "X is better for Y in Z"
- [ ] Thesis appears in Abstract (sentence 3), Introduction, and Conclusion
- [ ] Introduction lists 3–5 numbered, testable contributions
- [ ] Each contribution cross-references a paper section (§N)
- [ ] Each contribution is verified by an experiment in §5

### Section Presence
- [ ] Abstract: 150–250 words, self-contained (no undefined terms)
- [ ] Introduction: Problem → Gap → Insight → Contributions
- [ ] Background/Motivation: Technical terms defined before use
- [ ] Design: Architecture figure + module details + alternatives
- [ ] Implementation: Language, LOC, framework, key decisions
- [ ] Evaluation: Setup + end-to-end + ablation + scalability
- [ ] Related Work: Grouped by approach, explicit differentiation
- [ ] Conclusion: 3-sentence summary (problem, solution, result)

### Page Budget
- [ ] Total pages within venue limit (see venue table below)
- [ ] Design section: 3–4 pages (not overlong)
- [ ] Evaluation section: 3–4 pages (not underweight)
- [ ] Related Work: ~1 page (not a bibliography dump)
- [ ] Implementation: 0.5–1 page (concise)

---

## Stage 2: Writing Quality

### Clarity (Gernot Heiser)
- [ ] No forward references without explicit pointers ("as we show in §N")
- [ ] Every acronym defined on first use
- [ ] No orphan terminology — every technical term defined before use
- [ ] Consistent naming: system name capitalized uniformly throughout
- [ ] Active voice preferred over passive where possible

### Figures & Tables (MLNLP-World/Paper-Writing-Tips)
- [ ] Every figure/table referenced in text before it appears
- [ ] Figure captions are self-contained (readable without text)
- [ ] Evaluation figure captions include the key finding
- [ ] Architecture figure appears within first 3 pages
- [ ] Fonts in figures ≥ 8pt (readable when printed)
- [ ] Colors distinguishable in grayscale (for B&W printing)
- [ ] Consistent plot styles across all evaluation figures

### LaTeX Quality
- [ ] All code blocks have language tags (```python, ```bash, etc.)
- [ ] Non-breaking spaces before references: `Section~\ref{...}`
- [ ] Consistent citation format: `\cite{...}` not mixed with `[N]`
- [ ] No overfull hbox warnings in LaTeX log
- [ ] Bibliography entries have complete metadata (authors, title, venue, year)

### Prose Quality (RU-System/Paper_Writing_Tips)
- [ ] No hedging without evidence ("we believe", "it seems")
- [ ] Quantitative claims have numbers ("significantly better" → "37% better")
- [ ] No first-person unless venue style requires it
- [ ] Contributions are specific, not vague ("novel" without explanation)
- [ ] Related work comparisons are fair and accurate

---

## Stage 3: Evaluation Rigor

### Experimental Methodology
- [ ] Baselines are state-of-the-art (not straw men)
- [ ] Baselines configured optimally (not default/untuned)
- [ ] Hardware, software versions, and configurations fully specified
- [ ] Workloads described in sufficient detail to reproduce
- [ ] Statistical significance: error bars, multiple runs, or confidence intervals
- [ ] Warmup runs excluded from measurements

### Result Presentation
- [ ] Every conclusion stated 3 times: hypothesis (§ opening), result (§ closing), caption (figure)
- [ ] Ablation study isolates each design component
- [ ] Scalability experiments show behavior at increasing scale
- [ ] Both favorable and unfavorable results discussed honestly
- [ ] Performance numbers are absolute (not only relative percentages)

### Reproducibility
- [ ] Source code availability stated (or planned)
- [ ] Key hyperparameters and configuration values listed
- [ ] Workload generation described or traces cited
- [ ] Enough detail for an independent team to reproduce within ~2 weeks

---

## Stage 4: Design Quality

### Alternatives Discussion (Irene Zhang)
- [ ] Every major design decision discusses at least one alternative
- [ ] Alternatives are genuinely considered (not straw men)
- [ ] Trade-offs for each alternative explicitly stated
- [ ] Reasons for rejection are technical (not "it was harder to implement")

### Correctness Arguments
- [ ] System handles failure cases (discussed or evaluated)
- [ ] Edge cases acknowledged (even if not fully solved)
- [ ] Threat model or assumptions section present (if applicable)
- [ ] Limitations stated honestly (not hidden)

---

## Stage 5: Academic Integrity

### Citation Discipline
- [ ] **Every citation verified programmatically** (Semantic Scholar / DBLP / CrossRef)
- [ ] No citations generated from memory or LLM output
- [ ] Unverified citations marked as `[CITATION NEEDED]`
- [ ] All BibTeX entries have: authors, title, venue, year, pages/DOI
- [ ] No fabricated paper titles, authors, or venues
- [ ] Self-citations are relevant (not padding)

### Data Integrity
- [ ] Production observations are from real data (not fabricated)
- [ ] Experimental results are from actual runs (not interpolated/extrapolated)
- [ ] Traces cited with source (public dataset or anonymized description)
- [ ] No results cherry-picked without disclosing selection criteria

### LLM Disclosure
- [ ] Check venue's AI/LLM use policy in current CFP
- [ ] If LLM used for substantial writing: disclose as required
- [ ] If LLM used for code generation: disclose as required
- [ ] Confirm all LLM-assisted content reviewed by human authors

### Originality
- [ ] No paragraph-level text copied from other papers
- [ ] Structural patterns inspired by other papers are attributed
- [ ] Cross-repository content (if any) is attributed, not copied
- [ ] Related work descriptions are original paraphrases, not copy-paste

---

## Stage 6: Venue-Specific Requirements

> **Verify against the current year's CFP** — rules change annually.

### All Systems Venues

- [ ] **System design and implementation** — not just algorithms
- [ ] **Real workloads and evaluation** — microbenchmarks are insufficient
- [ ] **Practical benefits demonstrated** — latency, throughput, cost, energy
- [ ] **Comparison with state-of-the-art systems**
- [ ] **No simultaneous submission to other venues**
- [ ] **Prior arXiv/tech reports permitted**

### Page Limits Quick Reference

| Conference | Main Content | Camera-Ready | References | Format |
|------------|-------------|--------------|------------|--------|
| OSDI 2026 | 12 pages | 14 pages | Unlimited | USENIX |
| NSDI 2027 | 12 pages | varies | Unlimited | USENIX |
| ASPLOS 2027 | 12 pages | varies | Unlimited | ACM SIGPLAN |
| SOSP 2026 | 12 pages | varies | Unlimited | ACM SIGPLAN |
| EuroSys | 12 pages | varies | Unlimited | ACM |

### OSDI 2026

OSDI focuses on innovative research and quantified/insightful experiences in systems design and implementation.

**Tracks:**
- **Research Track**: Novel systems research
- **Operational Systems Track** (New in 2026): Design, implementation, analysis, and experience of operational systems

**Checklist:**
- [ ] ≤12 pages (excluding references)
- [ ] 8.5" x 11" pages, 10pt on 12pt leading, two-column, Times Roman
- [ ] 7" wide x 9" deep text block
- [ ] Pages are numbered
- [ ] Figures and tables legible in black and white
- [ ] Paper is the right length (not padded; <6pp unlikely to receive full consideration)
- [ ] Double-blind: no author names, affiliations
- [ ] Anonymized project/system name (different from arXiv/talks)
- [ ] Track indicated on title page and submission form
- [ ] Operational Systems papers: title ends with "(Operational Systems)"
- [ ] Max 8 submissions per author
- [ ] Work NOT wholly or largely generated by AI (AI editing tools are acceptable)

### NSDI 2027

NSDI focuses on design principles, implementation, and practical evaluation of networked and distributed systems.

**Tracks:**
- **Traditional Research Track**: Novel ideas with thorough evaluations
- **Frontiers Track** (New): Bold ideas without necessarily complete evaluation
- **Operational Systems Track**: Deployed systems with lessons learned

**Prescreening:** Reviewers read only the Introduction to check:
- [ ] Subject falls within NSDI scope
- [ ] Exposition understandable by NSDI PC member
- [ ] Track-specific criteria articulated in Introduction

**Checklist:**
- [ ] ≤12 pages (excluding references), USENIX format
- [ ] Two-column, 10pt, Times Roman
- [ ] Double-blind anonymized
- [ ] Contributions to networked systems design
- [ ] NOT out-of-scope topics (hardware architecture, physical layer, sensing, UI)
- [ ] Track indicated on title page and submission form
- [ ] Not rejected from previous NSDI deadline without one-shot revision option

### ASPLOS 2027

ASPLOS focuses on the intersection of computer architecture, programming languages, and operating systems.

**Rapid Review Round** (unique to ASPLOS):
- Reviewers only read the **first 2 pages**
- Evaluates how work advances Architecture/PL/OS research
- Majority of submissions may not advance past this stage

**Checklist:**
- [ ] First 2 pages self-contained: clearly states problem, approach, and contribution
- [ ] Advances Architecture, PL, and/or OS research
- [ ] Not just advances in another domain using arch/PL/OS
- [ ] ACM SIGPLAN format (`\documentclass[sigplan,10pt]{acmart}`)
- [ ] ≤12 pages (excluding references)
- [ ] Double-blind anonymized
- [ ] Max 4 submissions per author per cycle
- [ ] Resubmission note describing changes (if applicable)
- [ ] Not resubmitted from immediate previous ASPLOS cycle

### SOSP 2026

SOSP seeks innovative research related to design, implementation, analysis, evaluation, and deployment of computer systems software.

**Checklist:**
- [ ] ACM SIGPLAN format (`\documentclass[sigplan,10pt]{acmart}`)
- [ ] ≤12 pages technical content (excluding references)
- [ ] A4 or US letter, 178×229mm (7×9") text block
- [ ] Two-column, 8mm separation, 10pt on 12pt leading
- [ ] Pages numbered, references hyperlinked
- [ ] Figures/tables readable without magnification, encouraged in color but grayscale-readable
- [ ] Double-blind: paper ID instead of author names
- [ ] Anonymized system/project name
- [ ] Own work cited in third person
- [ ] No acknowledgments or grant numbers
- [ ] Artifact evaluation materials prepared (optional but recommended)
- [ ] Author response ≤500 words, no new experiments

### EuroSys

- [ ] ACM template used
- [ ] Page limit: 12 pages
- [ ] Double-blind formatting
- [ ] Artifact evaluation encouraged

---

## Stage 7: Final Pass

### Before Clicking Submit
- [ ] PDF renders correctly (no missing fonts, broken figures)
- [ ] All TODO/FIXME comments removed from source
- [ ] `[CITATION NEEDED]` markers resolved or removed
- [ ] Author names correct (camera-ready) or removed (blind)
- [ ] Acknowledgements removed for blind submission
- [ ] Supplementary material properly anonymized
- [ ] File size within submission system limits
- [ ] Paper title matches submission system entry
- [ ] Abstract in submission system matches paper abstract
- [ ] Correct track/topic area selected in submission system

### One-Sentence Self-Test (Levin & Redell Six Dimensions)
For each dimension, answer in one sentence:
1. **Original Ideas**: What is genuinely new?
2. **Reality**: Is the system built and tested?
3. **Lessons**: What did we learn that others can use?
4. **Choices**: Did we discuss alternatives for every major decision?
5. **Context**: Is the related work fair and complete?
6. **Presentation**: Would a non-expert in this subfield understand the paper?

If any answer is weak, revise that aspect before submitting.

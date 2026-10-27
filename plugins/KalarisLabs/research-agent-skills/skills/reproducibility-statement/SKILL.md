---
name: reproducibility-statement
description: Prepare the reproducibility, transparency and open-science parts of a paper, including data and code availability statements, reproducibility checklists (NeurIPS, ICML, ICLR, ACL Responsible NLP, Nature reporting summaries), research artifact packaging (Zenodo DOI, CITATION.cff, environment lockfiles, seeds), ethics/broader-impact statements, CRediT author contributions, competing interests and AI-use disclosures. Use when a venue requires any of these statements or checklists, or when preparing code/data for release alongside a paper.
license: MIT
compatibility: No runtime dependencies.
metadata:
  version: "1.0"
  category: research-writing
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: reproducibility, data availability, code availability, open science, FAIR, checklist, CRediT, Zenodo, ethics statement
---

# Reproducibility and Transparency Statements

## Workflow

1. List every statement and checklist the venue requires (section 1).
2. Deposit data and code, and obtain persistent identifiers before writing the statements.
3. Draft each statement with concrete locations, licenses and access conditions.
4. Verify every link and accession while logged out. Never claim availability that does not exist yet.
5. Answer checklists honestly, with a justification for each "No".

Editors increasingly desk-reject for missing or vague statements, and reviewers
check them. Treat each as a precise, verifiable claim, never boilerplate.

## 1. Find out what the venue requires

Check the current author guidelines and checklist for the target venue (the `venue-templates`
and journal-format skills point to them). Common requirements:

| Venue type | Typical requirement |
|---|---|
| ML conferences (NeurIPS, ICML, ICLR) | Paper checklist in the PDF (reproducibility, compute, licenses, broader impact, LLM usage), code encouraged |
| ACL / ARR venues | Responsible NLP checklist, limitations section (mandatory), ethics statement |
| Nature Portfolio | Data and code availability statements, reporting summary, source data for figures |
| PLOS | Mandatory data availability statement; data must be available without restriction unless legally exempt |
| Clinical journals | Trial registration, data sharing statement (ICMJE), reporting guideline checklist (CONSORT, STROBE, ...) |
| Cell Press | STAR Methods with Key Resources Table and resource availability section |

## 2. Data availability statement

State **where**, **how** and **under what conditions**, with persistent identifiers:

> The processed data supporting the findings are available at Zenodo (https://doi.org/10.5281/zenodo.XXXXXXX)
> under CC BY 4.0. Raw sequencing reads are deposited in the SRA under BioProject PRJNAXXXXXX. Patient-level
> clinical data cannot be shared publicly due to [regulation]. Requests can be made to [data access
> committee contact], and access requires a data use agreement.

- Use domain repositories where they exist (GEO/SRA/ENA, PDB, PRIDE, OpenNeuro, Dryad, ICPSR,
  PANGAEA). Otherwise use general ones (Zenodo, Figshare, OSF, Dataverse).
- "Available upon reasonable request" alone is increasingly rejected. Explain the restriction and the access route.
- Reserve DOIs before submission (Zenodo supports reserved DOIs). Use private reviewer links if the venue allows.

## 3. Code availability and artifact packaging

Checklist for the released repository:
- [ ] Tagged release matching the paper version, archived to Zenodo (GitHub integration mints a DOI)
- [ ] `README` with installation, a minimal example, and the exact commands that reproduce each table/figure
- [ ] Pinned environment: `uv.lock`/`requirements.txt` with versions, `environment.yml`, or a container image digest
- [ ] Random seeds, number of runs, and hardware noted, with variance reported (mean ± std over N seeds)
- [ ] Data download/preprocessing scripts (never ship data you're not licensed to redistribute)
- [ ] Pretrained weights or checkpoints with checksums, if central to the claims
- [ ] `LICENSE` (OSI-approved for code; CC BY for text/data), and third-party licenses respected
- [ ] `CITATION.cff` so GitHub shows "Cite this repository"
- [ ] Anonymized for double-blind review (anonymous GitHub mirrors), de-anonymized for camera-ready

## 4. Compute and environmental reporting (ML and simulation)

Report hardware (GPU/CPU type and count), total compute (GPU-hours) for main experiments
*and* the full project, including hyperparameter search. Report software versions of key frameworks.

## 5. Other statements

- **Author contributions (CRediT)**: map each author to the 14 roles (Conceptualization,
  Methodology, Software, Validation, Formal analysis, Investigation, Resources, Data curation,
  Writing – original draft, Writing – review & editing, Visualization, Supervision,
  Project administration, Funding acquisition).
- **Competing interests**: declare financial and non-financial interests, or state "none".
- **Funding**: funder names and grant numbers exactly as the funder requires.
- **Ethics**: IRB/ethics committee name and approval number, consent procedures, animal
  welfare approvals, dual-use considerations.
- **Use of AI tools**: follow the venue's policy. Most require disclosure of generative AI use in
  writing or analysis and forbid listing AI as an author. Describe what was used and how outputs were verified.
- **Limitations / broader impact**: concrete failure modes, populations or settings where results
  may not hold, potential misuse, and mitigations.

## Rules

- Every statement must be true at submission time. Verify each link and accession works (logged out, private window).
- Don't claim "fully reproducible" unless someone other than the author has rerun it from the README.
- Answer checklists honestly. "No" with a justification beats an unjustified "Yes".

## Related skills

`ml-paper-writing`, `scientific-writing`, `venue-templates`, `datalad`, `lamindb`,
`research-grants` (data management plans).

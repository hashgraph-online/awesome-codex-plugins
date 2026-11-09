# ATS interoperability and three separate assessments

The useful output is a transparent review of **job fit, factual reliability, and document quality**. None is a universal employer ATS score. Vendor matching features exist, with employer-specific settings; local keyword arithmetic cannot predict them. Primary support and dated limitations are in [research-sources.md](research-sources.md).

## Distinguish the mechanisms

| Mechanism | What it establishes | Appropriate check |
|---|---|---|
| File acceptance | Portal accepts an extension and size | Follow the actual recipient instructions. |
| Parsing | Text and fields are extracted | Verify text order and employer/title/date associations. |
| Recruiter search | Terms or structured fields can be found | Use recognizable, truthful terminology. |
| Matching/ranking | A configured product compares qualifications | Report its actual result only if available, naming system and scope. |
| Screening/rejection | Employer criteria trigger an action | Keep genuine eligibility and application answers separate. |

Greenhouse documents failed parsing that leaves the original file attached, Boolean search, optional Talent Matching and separate application-answer auto-reject rules. These are different functions, not one universal keyword filter. [Parsing](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse), [Talent Matching](https://support.greenhouse.io/hc/en-us/articles/41396009937307-Talent-Matching), [auto-reject](https://support.greenhouse.io/hc/en-us/articles/360000653472-Auto-reject).

## Assessment 1: job fit

Split the JD into explicit required and preferred criteria. Preserve the original meaning, avoid double counting synonyms, and make compound-criterion grouping visible. Label inferred expectations separately; do not silently add them to the required denominator.

Use one internal row per criterion:

`Requirement | Importance | Candidate evidence/source | Status | Truthful phrasing/output location`

| Status | Meaning |
|---|---|
| Direct | The stated requirement is supported by relevant source evidence. |
| Transferable | Related evidence is present; the exact required experience is not established. |
| Gap | A missing requirement is confirmed. |
| Unverified | Available information does not settle the requirement. |

Report counts, for example: “Required: 6/8 direct, 1 transferable, 1 unverified. Preferred: 2/3 direct, 1 gap.” These are evidence counts, not ranking or probability. Keep the grouping stable across revisions; polishing a sentence does not create new experience. Identify critical eligibility separately even if most other requirements are covered.

If the JD has no preferred criteria, say “none stated”; do not calculate 0/0. If there is no JD, say “JD coverage not applicable” and discuss the requested role direction. No percentage or score is needed for a scoped summary edit unless a relevant evaluation is requested.

Natural placement of a supported skill in Skills and an experience example can help readers. Projects, education or certifications may also provide evidence; do not invent an employment bullet to create a second mention. Exact JD terminology can help Boolean/phrase searches. Keep useful synonyms, but do not substitute synonyms for every actual product or skill name.

Normal repeated mentions across different roles are acceptable. Avoid duplication that adds no evidence. No inspected primary documentation establishes a global two-mention requirement, three-mention ceiling or penalty on a fourth occurrence. iCIMS documents a specific rank influenced by term location/frequency, demonstrating that implementations differ. [iCIMS FAQ](https://community.icims.com/articles/FAQ/Searching-Reporting-FAQ).

## Assessment 2: factual reliability

Check the claims that will appear in this output:

- Titles, employer/public names and employment dates agree with the record; explained concurrent work retains its actual capacity.
- Numbers preserve what was measured, units, baseline, period and attribution. A target or load test is not production throughput.
- Action verbs preserve personal, team, advisory and agent-assisted contribution.
- Skills and credentials are supported; a JD request is not evidence the candidate possesses them.
- Private aliases, confidential implementation details and disallowed sections are absent from the public output.
- Scoped preferences do not mutate shared facts or other outputs.

Use states such as **source-supported**, **conflict**, or **needs confirmation**. Source-supported self-reported experience is not independent external verification. Remove an unsupported final claim, use an accurate narrower claim, or request the material missing fact. Do not replace it with a plausible metric.

There is no mandatory numerical outcome in every bullet. A shipped capability, a documented decision, a real work artifact or a bounded contribution can be precise evidence. State only an action when the outcome is unknown. [MIT guidance](https://capd.mit.edu/resources/resumes/).

## Assessment 3: document quality

Use **passed / issue / not checked / not applicable**, with a concrete observation for each relevant check. Do not call an untested portal or proprietary ATS “passed”.

Portable default: sequential single-column body text, common headings, readable font, ordinary paragraphs and bullets. Place essential contacts in the body. Avoid layout tables, sidebars, text boxes, graphic skill ratings and decorative icons. Greenhouse documents these as parsing risks; this is a conservative default, not proof every parser always fails on them.

Use clear headings such as Summary, Skills, Experience and Education with corresponding RU wording. Optional sections do not need to be added to raise completeness. Keep employment dates consistent while retaining known precision; preserve year-only dates when months are unavailable. Expand unusual/ambiguous acronyms when helpful, without mechanically expanding familiar SQL/API/CTO everywhere.

Text-based PDF and DOCX are supported by several inspected vendors. Follow portal-specific instructions; no verified cross-vendor benchmark establishes equal reliability or a universal DOCX advantage. Selectable text is a first check, followed by extraction/read-order and actual autofill checks when accessible. [Lever parsing](https://help.lever.co/s/article/Understanding-Resume-Parsing).

Check names, contacts, Cyrillic/accents, ordinary bullets and text extraction. No blanket Unicode ban is required. Confirm readable pages, no clipped/overlapping text, useful pagination and no unfilled slots or internal review. Reduce redundant content before shrinking typography; 10–12pt body text is a readability starting point, not an ATS cutoff.

When an application is actually authorized, verify the portal's autofilled fields. SmartRecruiters documents matching that can prioritize candidate-verified experience/education over parsed data. [June 2026 release](https://www.smartrecruiters.com/resources/article/june-2026-product-release-highlights-more-control-confidence-in-hiring-workflows/).

## Avoid misleading shortcuts

Do not use hidden keywords or instructions to an AI reviewer. Do not report invented vendor accuracy percentages, tailoring conversion uplift, keyword penalties, “85% likely pass”, or scores based on how many bullets have numbers. Local text extraction is useful QA, not ATS certification. External scanners report their own model; label the system, date and tested input when using an actual result, and respect authorization for uploading private resumes.

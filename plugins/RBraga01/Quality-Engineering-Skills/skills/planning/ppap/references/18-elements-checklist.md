---
name: 18-elements-checklist
type: reference
parent_skill: ppap
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# PPAP 18 Elements — Detailed Reference Checklist

Acceptance criteria, level requirements, rejection causes, and OEM overrides for all 18 PPAP elements per AIAG PPAP 4th Edition.
Use alongside the [ppap](../SKILL.md) skill.

> **Scope:** This document covers element-by-element acceptance criteria, the Level 1–5 submission matrix, common rejection reasons, OEM-specific deviations, and the expected evidence per element. For the step-by-step submission workflow, see [ppap SKILL.md](../SKILL.md).

---

## 1. Level Requirement Matrix

AIAG PPAP 4th Edition Table 4.1 — `R` = Retain at supplier, `S` = Submit to customer, `*` = Submit on request only, `-` = Not required.

| # | Element | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---------|---------|---------|---------|---------|---------|
| 1 | Design Records | R | S | S | * | R |
| 2 | Engineering Change Documents | R | S | S | * | R |
| 3 | Customer Engineering Approval | R | S | S | * | R |
| 4 | DFMEA | R | R | S | * | R |
| 5 | Process Flow Diagram | R | R | S | * | R |
| 6 | PFMEA | R | R | S | * | R |
| 7 | Control Plan | R | R | S | * | R |
| 8 | Measurement System Analysis | R | R | S | * | R |
| 9 | Dimensional Results | R | S | S | * | R |
| 10 | Material / Performance Test Results | R | S | S | * | R |
| 11 | Initial Process Studies (Capability) | R | R | S | * | R |
| 12 | Qualified Laboratory Documentation | R | S | S | * | R |
| 13 | Appearance Approval Report (AAR) | R | S | S | * | R |
| 14 | Sample Production Parts | R | S | S | * | R |
| 15 | Master Sample | R | R | R | * | R |
| 16 | Checking Aids | R | R | R | * | R |
| 17 | Customer-Specific Requirements | R | R | S | * | R |
| 18 | Part Submission Warrant (PSW) | S | S | S | S | S |

**Legend:** Level 4 requirements are defined entirely by the customer — the `*` column means the customer's Level 4 letter or purchase order specifies which elements to submit or retain. PSW is always submitted regardless of level.

---

## 2. Element Acceptance Criteria and Expected Evidence

### Element 1 — Design Records

**Expected evidence:**
- Controlled copy of the customer drawing at the revision level stated on the PSW
- 3D math data (CATIA, UG/NX, STEP) if referenced on the drawing
- All referenced child drawings and specifications (tolerances, surface finish standards, material specs)
- Stamp or electronic confirmation that the revision is the latest approved issue

**Acceptance criteria:**
- Drawing revision on the PPAP package matches the revision on the PSW
- All referenced specifications are attached or traceable by document number and revision
- No superseded or draft revisions — only formally released documents accepted

**Common rejection reasons:**
- Drawing is a photocopy without an identifiable revision level or release date
- Referenced child specs (e.g., coating spec, heat-treat spec) not included
- Math data version does not match the drawing revision (3D model is newer or older than 2D drawing)
- Customer drawing was revised during PPAP — package not updated to the new revision

---

### Element 2 — Engineering Change Documents

**Expected evidence:**
- Approved Engineering Change Notice (ECN), SREA (Ford), deviation/waiver, or equivalent
- Change description, affected part numbers, and authorisation signatures
- Effectivity date or revision level at which the change is implemented

**Acceptance criteria:**
- Change document is formally approved by customer engineering (not a supplier-initiated change without sign-off)
- All parts affected by the change are listed
- PPAP submission level matches the change impact (design change → Level 3 minimum unless customer specifies otherwise)

**Common rejection reasons:**
- Change document is supplier-internal only — no customer sign-off
- PPAP submitted against a change not yet formally approved by customer
- Multiple open changes on the same part submitted without clear traceability of which changes are covered by this PPAP
- Element submitted as N/A when an active ECN is in progress

---

### Element 3 — Customer Engineering Approval

**Expected evidence:**
- Written sign-off from the customer engineering function (email with name/date, stamped drawing, or approval system record)
- Deviation or waiver number if design does not fully comply with the drawing
- Engineering approval is distinct from quality approval — both may be required

**Acceptance criteria:**
- Approval is from an authorised customer engineering contact (not purchasing or logistics)
- Approval explicitly references the part number, revision, and PPAP submission

**Common rejection reasons:**
- Approval is from the wrong function (purchasing approved, not engineering)
- Approval date predates the current drawing revision — approval is for an older design
- Element marked N/A when the customer design is supplier-owned but the customer requires sign-off on the design
- Verbal approval only — no written record

---

### Element 4 — Design FMEA (DFMEA)

**Expected evidence:**
- Complete DFMEA following AIAG-VDA 2019 format (AP-based) or AIAG 4th edition (RPN-based), as required by the customer
- All failure modes linked to design functions
- Action Priority (AP) ratings completed; all H-AP items have completed actions with effectiveness evidence
- Sign-off by the responsible design engineer and quality

**Acceptance criteria:**
- Required only when the supplier is responsible for the design (design-responsible supplier)
- If design is customer-owned, this element is N/A with a clear statement that the design is customer-owned
- All H-AP or RPN-flagged items (severity ≥ 9 or RPN above threshold) have a completed corrective action
- DFMEA revision matches or is more recent than the drawing revision

**Common rejection reasons:**
- DFMEA submitted for a design-responsible supplier but contains only process failure modes (PFMEA submitted in error)
- H-AP or high-RPN items listed as "planned" or "in process" — not completed before submission
- DFMEA uses old RPN format when customer requires AIAG-VDA AP format
- DFMEA revision level does not match the current drawing revision

---

### Element 5 — Process Flow Diagram

**Expected evidence:**
- Flowchart covering every operation from incoming material receipt through final shipment
- Includes: receiving inspection, sub-supplier operations (if applicable), all manufacturing steps, in-process inspection, final inspection, packaging, and shipping
- Each step labeled with an operation number that maps to PFMEA and Control Plan rows
- Rework and scrap paths shown

**Acceptance criteria:**
- Process Flow is specific to this part — not a generic flow for the product family
- Operation sequence matches the physical layout (floor plan consistent)
- Every step in the Process Flow has a corresponding PFMEA row and Control Plan row

**Common rejection reasons:**
- Generic process flow not specific to the part (copy of another part's flow)
- Sub-supplier or outsourced operations omitted
- Rework loops not shown — customer cannot assess rework controls
- Operation numbering does not match the PFMEA and Control Plan — misalignment causes traceability failure

---

### Element 6 — Process FMEA (PFMEA)

**Expected evidence:**
- PFMEA following AIAG-VDA 2019 format (AP-based) or AIAG 4th edition (RPN-based) as required by the customer
- One row per failure mode per process step
- All H-AP items (or high-RPN items) have completed actions with evidence and updated AP/RPN rating after action
- Sign-off by responsible process engineer and quality; customer review signature if required

**Acceptance criteria:**
- Covers every operation in the Process Flow — no steps omitted
- Detection controls in the PFMEA match the controls listed in the Control Plan
- All recommended actions completed before PSW is signed — no open H-AP items at submission

**Common rejection reasons:**
- PFMEA updated after PPAP run without re-running the capability study — misalignment between PFMEA controls and demonstrated process
- H-AP items marked "completed" but effectiveness verification not documented
- Detection controls in PFMEA say "SPC chart" but Control Plan shows "visual inspection" — inconsistency
- PFMEA covers only production process but omits incoming material inspection step

---

### Element 7 — Control Plan

**Expected evidence:**
- Production Control Plan (the version for submission — not Prototype or Pre-launch CP)
- All columns populated per AIAG Control Plan Reference Manual: operation, machine/device, characteristic, specification, measurement method, sample size, frequency, control method, reaction plan
- All special characteristics (SC, CC, KPC) present with correct customer symbol
- Signed by the multifunctional team; customer approval signature if required by the customer

**Acceptance criteria:**
- Every row has a complete reaction plan (not just "notify supervisor")
- 100% inspection or Cpk ≥ 1.67 + SPC specified for all SC/CC characteristics
- Sample size and frequency are specific numbers — "as required" or "as needed" is not accepted
- CP revision is more recent than the PFMEA (cannot submit an older CP against a newer PFMEA)

**Common rejection reasons:**
- Prototype or Pre-launch CP submitted instead of Production CP
- Missing SC/CC characteristics — auditor compares CP to drawing and PFMEA, any gap is a rejection
- Reaction plan column blank or says only "quarantine" without specifying next steps
- Control method for an SC characteristic is "visual inspection" — requires SPC or 100% with confirmed Cpk

---

### Element 8 — Measurement System Analysis (MSA)

**Expected evidence:**
- Gauge R&R study (variable) or attribute agreement analysis (attribute) for each gauge used to measure special or significant characteristics
- GR&R study report: %GRR, %Study Variation, number of distinct categories (ndc)
- Bias and linearity studies if required by the customer
- Calibration certificate for all gauges used in the MSA

**Acceptance criteria:**
- %GRR < 10%: acceptable for all uses
- %GRR 10–30%: conditional — may be acceptable based on importance of characteristic and cost of gauge improvement (requires customer concurrence)
- %GRR > 30%: not acceptable — gauge must be improved or replaced before PPAP
- ndc ≥ 5 for all variable gauges on special characteristics

**Common rejection reasons:**
- MSA performed with 2 appraisers and 5 parts — AIAG requires minimum 2–3 appraisers and 10 parts (minimum 30 study points)
- %GRR between 10–30% submitted without customer concurrence
- MSA done with a gauge different from the one used in production (lab gauge, not the production fixture gauge)
- Attribute gauge MSA not performed — attribute agreement analysis required for go/no-go gauges on SC/CC

---

### Element 9 — Dimensional Results

**Expected evidence:**
- Ballooned drawing with every dimension and tolerance numbered
- Dimensional results spreadsheet listing: balloon number, nominal, tolerance, measured value per part
- Minimum 5 parts per cavity / spindle / die / head — each part identified by cavity/position
- CMM reports, hand-measurement records, or 3D scan data as applicable

**Acceptance criteria:**
- 100% of all ballooned dimensions within specification — no out-of-tolerance results at submission
- All cavities and spindles measured separately — not averaged
- All GD&T callouts (flatness, true position, parallelism) measured and reported

**Common rejection reasons:**
- Any single dimension out of specification — automatic rejection regardless of significance
- Only 1 part measured when 5 per cavity are required
- Balloon numbers on the drawing do not match the results spreadsheet
- GD&T datums used incorrectly — part restrained or fixtured differently from the drawing datum scheme
- "Target" or "nominal" entered as the result instead of the actual measured value

---

### Element 10 — Material and Performance Test Results

**Expected evidence:**
- Test reports for all tests specified on the drawing or in referenced material/performance specifications
- Laboratory identification and accreditation scope (ISO/IEC 17025 preferred)
- Pass/fail status explicitly stated on each test report
- Certificate of Conformance (CoC) from the raw material supplier

**Acceptance criteria:**
- All tests show "Pass" against the specified acceptance criteria
- Test specimens are from production material — not prototype, pre-production, or off-specification material
- Test standard and revision referenced in the report matches the drawing specification

**Common rejection reasons:**
- Test report says "results attached" without a clear pass/fail conclusion
- Tests performed on specimens machined from a billet rather than the actual production part
- Incomplete test matrix — not all tests required by the specification are covered
- Material CoC shows a different alloy or heat number than the material used in the PPAP run

---

### Element 11 — Initial Process Studies (Capability)

**Expected evidence:**
- Cpk and Pp/Ppk study for each special characteristic (SC, CC, KPC, KCC)
- Minimum 100 consecutive pieces from the PPAP significant production run (not from multiple runs combined)
- Control chart (X-bar R or Individuals & Moving Range) showing process stability before calculating Cpk
- Distribution analysis (normality check) — if non-normal, state the distribution used and justify

**Acceptance criteria:**
- Cpk ≥ 1.67: preferred — no additional conditions
- Cpk 1.33–1.67: acceptable — customer may require an improvement plan
- Cpk < 1.33: not acceptable unless customer grants a formal deviation; requires 100% inspection if deviation granted
- Process must be stable before Cpk is calculated — if control chart shows special causes, the data is not valid

**Common rejection reasons:**
- Cpk calculated on fewer than 30 pieces — some customers require a minimum of 100
- Process shows out-of-control signals on the control chart but Cpk is still reported — process is not stable
- Cpk calculated using specification-based sigma instead of actual process sigma
- Capability study run on prototype parts or pre-production pilot, not the PPAP significant production run
- Multiple small sub-groups combined to inflate n — all 100+ pieces must be consecutive from one continuous run

---

### Element 12 — Qualified Laboratory Documentation

**Expected evidence:**
- Copy of the laboratory's ISO/IEC 17025 accreditation certificate with scope of accreditation
- The accreditation scope must explicitly cover the test methods performed (e.g., ASTM B117 salt spray listed in scope)
- For in-house labs: internal calibration system documentation and scope statement
- For customer labs: customer lab identification

**Acceptance criteria:**
- Accreditation is current (not expired) as of the test date
- Scope of accreditation covers the specific test standard used (not just a general category)

**Common rejection reasons:**
- Lab is accredited but the specific test method is not within the accredited scope
- Accreditation certificate expired before the test was performed
- In-house lab used for regulatory tests that require external accreditation (e.g., EMC, crash, chemical)
- Lab certificate submitted for a different lab location than where the test was performed

---

### Element 13 — Appearance Approval Report (AAR)

**Expected evidence:**
- Completed AAR form (AIAG standard or OEM-specific form)
- Customer sign-off on: colour (spectrophotometer data), gloss level, grain/texture, clarity, and visual appearance attributes
- Colour measurement data (Lab* values) for the approved colour against the master standard
- Customer representative signature and date

**Acceptance criteria:**
- Required only for parts with appearance requirements (exterior trim, interior panels, painted/plated surfaces)
- Not required for structural components with no appearance specification
- Customer signature must be from the authorised styling/colour approval function — not quality or purchasing

**Common rejection reasons:**
- AAR not submitted for a part with an appearance specification (omission)
- AAR submitted for a non-appearance part — wastes review time and implies misunderstanding
- Colour data shows Delta E > 1.0 against the master standard but AAR is signed — inconsistency raises a concern
- AAR signed by a purchasing or quality contact rather than the styling/appearance engineer

---

### Element 14 — Sample Production Parts

**Expected evidence:**
- Physical sample parts from the significant production run
- Labelled with: part number, revision, date of manufacture, cavity/spindle number, PPAP submission reference
- Quantity as specified by the customer (Level 2: typically 2–5 per cavity; Level 3: as specified in customer's PPAP requirements, commonly 3–10)

**Acceptance criteria:**
- Parts must be from production tooling run at production speed and conditions — not hand-made, off-tool, or prototypes
- Each cavity/spindle must be represented
- Parts must not be cosmetically selected — random from the PPAP run

**Common rejection reasons:**
- Prototype or first-off-tool samples submitted when production-run samples are required
- Parts not labelled — traceability to the PPAP run cannot be confirmed
- Only one cavity represented when the tool has multiple cavities
- Parts selected for best appearance rather than being random production samples

---

### Element 15 — Master Sample

**Expected evidence:**
- One boundary sample retained at the supplier's manufacturing location
- Signed by the supplier quality manager; customer signature if required
- Stored in a controlled location — protected from damage, corrosion, or contamination
- Labelled with: part number, revision, approval date, and reference to the PPAP submission

**Acceptance criteria:**
- Must remain at the supplier for the life of the PPAP approval or until superseded by a new PPAP
- If a customer-signed master sample is required, a copy of the signed sample record must be in the PPAP package

**Common rejection reasons:**
- No master sample retained — supplier cannot demonstrate what the approved condition looks like
- Master sample stored incorrectly (rusted, damaged, or contaminated)
- Master sample is from a different run than the PPAP significant production run
- Sample not signed or labelled — cannot be traced to the PPAP approval

---

### Element 16 — Checking Aids

**Expected evidence:**
- List of all checking fixtures, gauges, and inspection devices used for dimensional verification
- Calibration certificate for each device (current, with next calibration due date)
- MSA study referenced for each variable gauge used on special characteristics
- Functional check procedure if checking aids are used as go/no-go devices

**Acceptance criteria:**
- All calibration certificates current as of the PPAP submission date
- Any checking fixture designed for this part must have a traceable design (fixture drawing or reference)
- MSA results for variable gauges on SC/CC must be in Element 8 — Element 16 cross-references them

**Common rejection reasons:**
- Calibration expired on one or more gauges used during the PPAP dimensional check
- Checking aid list incomplete — dimensions were measured with a gauge not listed
- Gauge used in production differs from the gauge used in the PPAP study
- Functional checking fixture without a qualified calibration method — "functionally checks" is not adequate

---

### Element 17 — Customer-Specific Requirements

**Expected evidence:**
- Completed CSR compliance checklist (if the customer provides one)
- OEM-specific supplemental forms (see OEM overrides table below)
- Reference to customer portal submission (Ford WERS, GM Covisint, BMW form 1410, VW QMSS, Stellantis SQA)
- VDA 6.3 process audit report (if required by BMW or VW)

**Acceptance criteria:**
- All customer-specific requirements are either met or documented as N/A with justification
- OEM-specific forms are current revision (outdated forms are rejected)

**Common rejection reasons:**
- Generic AIAG submission without addressing CSR requirements
- CSR checklist not completed or not attached
- OEM-specific form missing (e.g., BMW 1410 or Ford-specific PSW)
- Submitted via email when OEM requires portal submission

---

### Element 18 — Part Submission Warrant (PSW)

**Expected evidence:**
- One PSW per part number per submission (not one PSW covering multiple part numbers)
- Completed fields: supplier name, supplier code, customer name, part number, revision, submission reason, specification level, weight (actual and drawing), whether samples are enclosed
- Explanation of any deviations from PPAP requirements
- Signature: authorised supplier quality manager (not a coordinator or technician)

**Acceptance criteria:**
- All fields completed — no blank fields without justification
- Submission reason matches the change category that triggered the PPAP
- "Have all elements been satisfied?" — customer is looking for honest disclosure; flagging outstanding deviations is expected and preferable to submitting a false statement
- PSW signed at the quality manager level or higher

**Common rejection reasons:**
- PSW signed by a coordinator without authority
- Submission reason does not match the actual change (e.g., "new part" selected when this is a re-submission after a corrective action)
- Weight field blank or showing drawing weight rather than actual measured weight
- PSW states "all elements complete" when the package is missing elements — misrepresentation
- Generic AIAG PSW submitted to Ford (Ford requires their own PSW form)

---

## 3. OEM-Specific Overrides Table

Deviations from the AIAG PPAP 4th Edition baseline.

| Topic | AIAG Baseline | Ford | BMW | Volkswagen / Audi | Stellantis |
|-------|--------------|------|-----|-------------------|------------|
| PSW form | AIAG generic PSW | Ford-specific PSW (WERS-linked) — AIAG form rejected | BMW 1410 form (Erstmusterprüfbericht) required | PPF form — VW's PPAP equivalent; AIAG PSW not used | Stellantis-specific PSW via SQA portal |
| FMEA format | AIAG 4th ed RPN or AIAG-VDA 2019 | AIAG-VDA 2019 AP format required | AIAG-VDA 2019 AP format required | AIAG-VDA 2019 AP format required | AIAG-VDA 2019 AP format required |
| Submission portal | No portal defined | WERS / PPAP Manager portal | e.g., LIDS / BMW PPAP system | QMSS portal; document upload mandatory | Stellantis SQA portal |
| Design change documentation | ECN or equivalent | SREA (Supplier Request for Engineering Approval) — separate from ECN | Änderungsantrag through BMW system | VDA 2 deviation process | GPIRS (Global PPAP Initiating Request System) |
| Process audit | Not explicitly required | Q1 process audit may be required at new suppliers | VDA 6.3 process audit required before PPAP for new suppliers | VDA 6.3 process audit — P5/P6/P7 elements must score ≥ 4.0 | Stellantis supplier assessment required |
| ISIR | Not defined | ISIR (Initial Sample Inspection Report) may be required in addition to dimensional results | Dimensional results submitted within the 1410 form (integrated) | DFU dimensional results per QMSS format | Standard dimensional results accepted |
| Capability minimum | Cpk ≥ 1.67 preferred; ≥ 1.33 minimum | Cpk ≥ 1.67 for all SC; Cpk < 1.67 requires Ford engineering approval | Cpk ≥ 1.67 for CC; Cpk ≥ 1.33 for SC | Cpk ≥ 1.67 for CC; Cpk ≥ 1.33 for SC | Cpk ≥ 1.67 for SC/CC; Cpk < 1.33 rejected |
| Sample quantity | As specified per level | Typically 5 parts minimum per cavity for Level 3 | 5 parts minimum per cavity | 5 parts minimum | 5–10 parts per cavity depending on CSR |
| AAR | Required for appearance parts | Ford-specific AAR form; colour measurement mandatory | BMW AAR process with styling centre sign-off | VW colour release process | Stellantis AAR through SQA portal |
| Lab accreditation | ISO/IEC 17025 preferred | ISO/IEC 17025 required for safety/regulatory; A2LA or equivalent | ISO/IEC 17025 required; DAkkS (German accreditation) recognised | ISO/IEC 17025 required | ISO/IEC 17025 required for regulated tests |
| Appearance approval | AAR per AIAG | Master part retained at Ford facility; Ford CQAAS system | Master sample at BMW styling; mirror sample at supplier | VW musterbauteil process | Stellantis appearance approval via SQA |
| Re-submission after failure | Not explicitly defined | PPAP re-submission with 8D reference required after corrective action | G8D required before re-PPAP for quality escapes | QMSS concern linked before re-submission | GPIRS re-initiation through SQA portal |

---

## 4. Element Submission Checklist — What Document or Evidence Is Expected

Use this as the physical package checklist before sealing the PPAP submission.

| # | Element | Document / Evidence | Format |
|---|---------|--------------------|----|
| 1 | Design Records | Latest released drawing (all sheets); 3D model if applicable; all referenced specs | PDF + native CAD or STEP |
| 2 | Engineering Change Documents | ECN / SREA / deviation signed by customer engineering | PDF (signed) |
| 3 | Customer Engineering Approval | Approval email, stamped drawing, or system record | PDF or portal record |
| 4 | DFMEA | DFMEA in AIAG-VDA or AIAG 4th ed format, signed off | Excel / AIAG spreadsheet or PDF |
| 5 | Process Flow Diagram | Flowchart covering all operations, rework paths, inspection points | Visio / PowerPoint / PDF |
| 6 | PFMEA | PFMEA aligned to Process Flow, all H-AP complete, signed off | Excel / AIAG-VDA spreadsheet or PDF |
| 7 | Control Plan | Production CP, all 13 columns populated, signed | Excel / AIAG template or PDF |
| 8 | MSA Studies | GR&R reports (one per gauge per characteristic); attribute agreement analysis if applicable | Minitab report / Excel / PDF |
| 9 | Dimensional Results | Ballooned drawing + results spreadsheet, 5 parts per cavity | PDF (ballooned) + Excel (results) |
| 10 | Material / Performance Tests | Lab test reports for all specification tests; material CoC | PDF (lab-stamped) |
| 11 | Process Capability | Cpk study with control chart; ≥ 100 consecutive parts from PPAP run | Minitab / Excel / PDF |
| 12 | Lab Documentation | ISO/IEC 17025 certificate with scope covering the tests performed | PDF (current, not expired) |
| 13 | AAR | Completed AAR form; colour measurement data; customer signature | PDF (signed) |
| 14 | Sample Parts | Physical parts labelled with PN, rev, date, cavity — shipped or available on request | Physical |
| 15 | Master Sample | Physical sample retained at supplier; signed label; storage record | Physical + signed label record |
| 16 | Checking Aids | List of all gauges/fixtures; calibration certs; MSA cross-reference | Excel or PDF |
| 17 | CSR Requirements | CSR compliance checklist; OEM-specific supplemental forms; portal submission record | PDF + portal acknowledgement |
| 18 | PSW | Completed and signed PSW (OEM-specific form if required) | PDF (wet or electronic signature) |

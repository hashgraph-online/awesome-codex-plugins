# Course Site Spec — {{course_code}} · {{course_title}} · {{term}}

Build specification filled by `site_builder_agent` from `course_passport.yaml`, then
confirmed at a 🧑 checkpoint before any files are generated. The site is a build
product; the passport is the source — every section below names the field it renders.

## Page inventory and content sources

| Page | File | Section | Rendered from |
|------|------|---------|---------------|
| Home | `index.html` | Course identity (code, title, term, modality, credits) | `course.*` |
| | | Orientation paragraph | {{professor_supplied_or — [NEEDS PROFESSOR INPUT: 2–3 sentence course description in your words]}} |
| | | "This week" pointer | `schedule[]` + term calendar (current week) |
| Schedule | `schedule.html` | Week-by-week table | `schedule[]` ⋈ `assessment_plan` ⋈ `artifacts[]` |
| Materials | `materials.html` | Week-indexed artifact links | `artifacts[]` (student-appropriate only) |
| Policies | `policies.html` | Grading, late, AI-use, integrity, attendance | `policies.*` **verbatim** |
| Contact & Help | `contact.html` | Instructor, TAs, office hours, help routes | {{professor_supplied — [NEEDS PROFESSOR INPUT: office hours, locations, TA info, forum/LMS links]}} |

Pages cut or merged by the professor: {{page_adjustments — default none}}

## Navigation

{{nav_spec — default: single top nav, same five links on every page, current page
marked; no dropdowns, no JS-dependent menus}}

## Schedule table — column spec

| Column | Source | Rule |
|--------|--------|------|
| Week | `schedule[].id` | W1…W{{weeks}} |
| Dates | stored term calendar | day-month format; never computed from a guessed start date |
| Topic | `schedule[].topic` | verbatim |
| Due | `schedule[].assessments_due` ⋈ `assessment_plan` | title + weight, e.g., "Midterm (25%)" |
| Materials | `schedule[].artifact_refs` ⋈ `artifacts[]` | links per the index rules below; unbuilt weeks show "posted by {{materials_lead_time}}" — never a dead link |

Phone rule: table must linearize readably at narrow widths (each row readable as a
labeled block); verified in the accessibility pass.

## Materials index — inclusion and naming rules

- **Appears:** {{student_artifact_types — default: slides, handouts, activity sheets,
  readings lists, project briefs, rubrics, self-check checklists}}
- **Never appears:** answer keys, instructor/teaching notes, item banks, anything
  instructor-side in `artifacts[]` — when classification is unclear, exclude and ask.
- Link text = artifact title + type + format, e.g., "Week 3 slides (PDF)"; file names
  follow the lms-package convention (`W03_slides_<topic>.pdf`) so site and LMS stay
  name-consistent.
- Ordering: by week, then by type; assessments also linked from the schedule row where
  they are due.

## Policies page

Rendered **verbatim** from `policies.*` — no summarizing, no paraphrase, no tone edits
at build time. A second wording is a second thing that can drift from the syllabus;
this page and the syllabus must be character-identical on shared policy text. Empty
policy fields render as [NEEDS PROFESSOR INPUT: {{policy_name}} — edit via
course-designer], visibly — not silently omitted. Wording changes go to the passport
via `course-designer`, then this page rebuilds.

## Build instructions

- Output: {{output_format — default: plain semantic HTML + one `style.css`, no
  framework, no build step; alternative: pure Markdown for LMS page paste-in;
  framework layout only if the professor already uses one}}
- Hosting: any static host or LMS pages — {{hosting_target — [NEEDS PROFESSOR INPUT:
  where will this live? departmental server / GitHub Pages / LMS pages]}}
- Files land in `site/`; nothing is live until the professor deploys (draft-only rule).

## Accessibility checklist (Quality Gate U1 — run before checkpoint)

- [ ] One `h1` per page; heading levels unskipped
- [ ] Alt text on every image, or [NEEDS PROFESSOR INPUT: alt text] flagged
- [ ] Link text states the destination (no "click here", no bare URLs)
- [ ] Schedule table has header row + readable phone linearization
- [ ] Color never the sole carrier of meaning
- [ ] Every page fully usable without JavaScript

Result: {{accessibility_report — findings listed at the checkpoint, first}}

## Update model

The site is **rebuilt from the passport, not hand-patched**. On any passport change:
regenerate affected pages → what-changed diff at the 🧑 checkpoint → professor
redeploys. Hand-edits detected in generated files are flagged, never silently kept or
overwritten. Last built from passport state: {{passport_version_and_date}}.

# Suede AI Visibility Grader Skills: Worked Handoff

## Inputs

Request: “Grade this page before promotion.” Supply one exact URL, primary reader,
surface type, and intended action. Synthetic evidence: desktop rendering and
source are available, the primary CTA opens the intended destination, but mobile
has not been inspected. A short first-viewport gut check uses quick mode; a full
page request uses deep mode.

## Expected output

Use the Output Format in the main skill: inspected URL/source, live status,
screenshots and viewport evidence, six lane grades with reasons, overall grade,
up to five ranked fixes for deep mode, verification, and advisory ship gate.
Compute lanes and caps from the rules rather than impressions. Mobile not
inspected blocks A. Quick mode is at most B and has no top-fixes list. Missing
live inspection caps overall at C. Do not infer actual rankings or AI citations
from a well-structured page.

## Failure case

The URL cannot be reached. Grade supplied source only, name live and rendering
checks unverified, and apply the source-only cap. If the CTA is broken, report
the observed failure and apply the stricter overall conditions in the grade
rules; do not let a positive design count cancel the broken task path.

## Validation

Recompute the design pass count, AI readability deductions, overall conditions,
and all applicable caps. Verify that each fix points to an inspected location,
not a generic SEO suggestion. The ship gate follows the final grade and caveats.
Read-only grading must leave the page, metadata, and schema unchanged.

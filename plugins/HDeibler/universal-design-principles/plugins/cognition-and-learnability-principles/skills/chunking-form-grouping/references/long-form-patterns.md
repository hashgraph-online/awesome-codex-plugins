# Long-form patterns: case reference

A reference complementing `chunking-form-grouping` with field-grouping conventions and case patterns.

## Empirical findings on form length and chunking

NN/g and other usability research consistently finds:

- **Form completion drops sharply** beyond ~10 fields without sectioning, regardless of field complexity.
- **Sectioned forms outperform flat forms** of the same length by 20-40% on completion.
- **Multi-step wizards outperform long single-page forms** on mobile but underperform on desktop where users can see scope.
- **Save-resume support** (saving partial progress) reduces abandonment substantially for genuinely long forms (insurance applications, government).

## Government / legal forms

Tax forms, immigration forms, insurance applications: all genuinely long because the underlying information requires it. Patterns that work:

- **Section-by-section flow** with named sections (Personal Info, Income, Deductions, Credits).
- **Save-and-resume** built in.
- **Progress indicator** showing total scope.
- **Inline help** explaining unfamiliar terms.
- **Pre-fill from prior submissions** when applicable (US 1040 from prior year's data).

The form's length is irreducible; the design's job is making the length tolerable.

## Sign-up flows

Modern sign-up best practice: minimize required fields at registration; defer optional data to onboarding or profile-completion.

- **2010-era pattern**: 12-field sign-up. High abandonment.
- **Modern pattern**: 3-field sign-up (email, password, agreement). Optional data collected over time.

The chunking discipline isn't just within the sign-up form; it's *across* sign-up + first-run + ongoing onboarding.

## Multi-step wizard patterns

Common conventions:

- **Stepper at top** showing progress.
- **Continue button** as primary action.
- **Back button** preserved (don't break browser back).
- **Step numbers in URLs** so users can deep-link.
- **State persistence** so refresh / accidental nav doesn't lose data.

Anti-patterns:

- **Hidden total step count** ("Step 1 of ?"). Users want to know total scope.
- **Steps that auto-advance** without user action. Surprise.
- **Validation only on final step**. Users hit submit, find errors in step 2, navigate back, lose context.

## Resources

- **Wroblewski, L.** *Web Form Design* (2008) — comprehensive form-pattern reference.
- **Jarrett, C. & Gaffney, G.** *Forms that Work* (2008).
- **GOV.UK Design System** — government-grade form patterns.
- **NN/g** — form-design research articles.

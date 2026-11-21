# Slop Taxonomy

Read before classifying a finding. This file owns the finding classes, the rule IDs, and the cluster grouping.

## Finding classes

| Class | Meaning | Default handling |
|---|---|---|
| `hard-gate` | Accessibility, behavior, security, or unmistakable responsive failure | Fix or block according to task authority; never present as mere taste |
| `default-risk` | Strongly resembles a recurring AI default but may be intentional | Check brief and identity; replace only with supporting evidence |
| `review-only` | Specificity, taste, emotional impression, or structure that requires human/agent judgment | Report with caveat; never auto-fix |
| `informational` | Useful observation that does not require change | Record only when relevant |

## Registry scopes

- `universal`: stable quality or accessibility guard independent of visual taste.
- `default-risk`: suspicious default with legitimate brief or brand exceptions.
- `context-dependent`: requires page type, domain, audience, data shape, or brief.
- `review-only`: cannot become a gate from static matching alone.

## Categories

- `structure`: repeated hero, feature-grid, card, navigation, footer, bento, sidebar, or section fingerprints.
- `surface`: gradients, glow, orbs, decorative pills, status dots, side stripes, uniform radius/shadow, arbitrary tokens.
- `typography-copy`: generic type pairing, cliché phrases, placeholder names/brands, unsupported metrics or claims, repetitive eyebrows.
- `motion-interaction`: `transition-all`, indiscriminate scale/reveal, layout animation, missing reduced motion, hover-only affordance.
- `quality`: contrast/focus/semantics/responsive defects, fake chrome, and claims made without rendered evidence.

## Evidence and exception status

- `detection confidence` describes how certainly an engine found a source, context, DOM, or rendered signature.
- `remediation confidence` describes how certainly the finding can be changed without violating the brief or protected contracts.
- `candidate` exception means explicit local brand, data, or real-state evidence supports preservation. It remains visible for review; it never suppresses a rule or authorizes an auto-fix.
- `generic-output risk` is `low`, `medium`, or `high` prioritization based on context-confirmed clusters. It is never evidence that AI authored the interface.

## Required exception checks

- An explicitly requested brand color, gradient, font, or reference is not slop by default.
- Three columns are not slop when the data genuinely has three peers or the user requires that comparison.
- Domain conventions in medical, finance, public sector, or B2B interfaces are not generic merely because they repeat.
- A static match cannot prove visual hierarchy, contrast, usability, or intent.
- Multiple weak signals do not become deterministic merely by counting them.

## Disposition

Use exactly one action per finding:

- `remove`: unsupported decoration or placeholder with high-confidence evidence.
- `replace`: a pattern is supported as risky and a brief-aligned alternative preserves content and behavior.
- `preserve`: brand, brief, data, or function justifies the pattern.
- `ask`: a user decision materially changes the safe result.
- `block`: evidence, scope, or authority is inadequate.

## Co-occurrence and generic-output risk

A single pattern is noise: one gradient, one Inter heading, or three cards can each be a real decision. Generic-output risk comes from defaults that appear together and that no brief, brand, or data explains.

| Unexplained `default-risk` or `context-dependent` findings in one surface | Generic-output risk |
|---|---|
| 0-1 | `low` |
| 2-3 | `medium` |
| 4 or more | `high` |

Count a finding only when its exception status is `not-checked` or the check found no supporting evidence. `review-only` findings inform the review but do not raise the tier on their own. The tier orders work; it never proves AI authorship.

## Unchosen defaults and drift

- Judge the absence of a decision, not the presence of a style. A value is a finding when nothing in the brief, the reference, or the project's system explains it.
- The list of defaults moves. Purple gradients, glass, and neon glow gave way to cream backgrounds with italic serif displays, bento grids, emerald accents, and neobrutalist hard shadows. Replacing one default with its successor is not a fix; `references/anti-pattern-catalog.md` lists both waves.
- Every catalog rule keeps its exceptions. A documented brand value, a real data shape, or a real state outranks the rule.
- The question for every technique is what it serves. A gradient, glass, a badge, or a card grid is a tool; the finding is the technique used with no written purpose, or past its dose cap (`rules/delivery-gate.md` §5).

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The finding classes, registry scopes, categories, and dispositions | this package's own vocabulary; the bundled rule registry implements the same names |
| One match is noise, many together are a signature; judge the absence of decisions; purple migrating to cream and italic serif | <https://github.com/febbhav/signs-of-ai-design/tree/854b46f18dee5cc174d45cec8cd4f3142fe46984> (CC BY-SA 4.0) |
| Tiered counting of deterministic pattern checks (4+ high, 2-3 medium, 0-1 low) over 1,590 sites, with about 5-10% false positives on manual review | <https://www.adriankrebs.ch/blog/design-slop/> (2026-04-20) |
| Three eras of defaults (purple and glass, beige editorial, neobrutalist) | <https://impeccable.style/slop/> |
| A new default (emerald) appearing after the old one (indigo) was banned | <https://solodesign.cc/blog/ai-design-slop-the-tells/> (2026-06-06) |
| Reject technique without purpose, not technique itself | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` Core Principle; MIT) |

### Evidence grade

The tier thresholds come from one public scoring study with a different rule set; they are a starting point for ordering work, not a calibrated classifier.

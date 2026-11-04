# Clip-to-Guide Package Template

Use this structure for every durable package. Keep URLs and timestamps exact.
Use `not available` instead of inventing a value.
Max Effort and Worker Fleet packages need two distinct evidence records and a
final `PROVED` verdict before approval or publication.

```markdown
---
campaign: "<short campaign name>"
platform: "<platform>"
identity: "<visible account identity>"
rights_status: "<original|licensed|permission-recorded|native-repost-only|fair-use-review|blocked>"
guide_status: "<existing|drafted|needs-long-form|blocked>"
publication_status: "<draft|approved|published|blocked>"
execution_mode: "<standard|max-effort|worker-fleet>"
certainty_status: "<not-required|pending|proved|unproved|blocked>"
---

# Clip-to-Guide Package

## Decision Snapshot

- Goal:
- Audience:
- Platform:
- Visible identity:
- Sequence: <anchor-first|clip-first|native-repost>
- Blueprint fit: <use|revise|do-not-use>
- Fit evidence:
- Next action:

## Source and Rights

- Video source:
- Video owner:
- Rights evidence:
- Allowed use:
- Jurisdiction:
- Transcript source:
- Selected excerpt:
- Claim qualifications:

### Fair-use review

- Purpose and character:
- Nature of the source work:
- Amount and substantiality:
- Effect on the potential market:
- Why this exact excerpt is necessary:
- Accountable decision owner:
- Decision or legal-review state:

## Guide Anchor

- Guide title:
- Guide URL:
- Publication state:
- Promise:
- Question the clip creates:
- Answer the guide delivers:

## Clip Brief

- In timestamp:
- Out timestamp:
- Target duration:
- Moment score:
- Exact opening:
- Subtitle text:
- On-screen source credit:
- Ending bridge:
- Export owner:
- Media file:

## Funnel Post

### Exact post text

<exact copy>

### Copy checks

- Hook matches the clip:
- Claim language matches the source:
- Guide bridge is explicit:
- One CTA only:
- Platform composer verified:

## Publish Sequence

1. <first action>
2. <second action>
3. <readback action>

## Measurement

- Baseline:
- Observation window:
- Clip metric:
- Guide metric:
- Campaign action:
- Decision rule:

## Certainty Gate

- Required: <yes|no>
- Checked artifact version/hash:
- Check 1 owner/process:
- Check 1 evidence:
- Check 1 verdict: <PROVED|UNPROVED|BLOCKED|NOT-REQUIRED>
- Check 2 owner/process:
- Check 2 evidence:
- Check 2 verdict: <PROVED|UNPROVED|BLOCKED|NOT-REQUIRED>
- Contradictions resolved:
- Final certainty verdict: <PROVED|UNPROVED|BLOCKED|NOT-REQUIRED>

## Approval Gate

- Exact media approved:
- Exact post text approved:
- Exact guide and URL approved:
- Exact identity approved:
- Exact sequence approved:
- Approved by:
- Approval timestamp:

## Verification

- Package validation:
- Live permalink:
- Visible identity:
- Rendered media or source reference:
- Guide readback:
- Publication timestamp:
- Caveats:
```

For chat-only delivery, mirror these headings and state that no saved package
was validated. For a saved package, validate with:

```bash
python3 scripts/validate_package.py path/to/package.md
```

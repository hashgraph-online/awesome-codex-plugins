# Kids and Family Apps on Google Play

Read this when the target audience includes children under 13, or when the app
could appeal to children even if they are not the main audience. Checked on
**2026-10-23**; re-open the sources before release.

## Design rule: collect nothing from the child

The cleanest kids' app (a StoryBeam-style story reader, a first-chords guitar
lesson) needs no personal data from the child at all. Build to that:

- No child accounts. If a parent account exists, it lives behind a parental
  gate and holds only what the parent supplies.
- No free-text input that can capture a name, school, address, or photo of a
  face. Use pickers, presets, and illustrated choices.
- No microphone, camera, contacts, or precise location. If a lesson app needs
  the mic for pitch detection, process audio on device, never store or send it,
  and say so in the privacy policy and Data Safety form.
- No advertising ID, no persistent identifiers sent to third parties, no
  behavioral analytics.
- Purchases, external links, sharing, and settings sit behind a parental gate.

## Content rule: age-appropriate every time

- Declare the age bands honestly in Target audience and content.
- Every story, illustration, sound, and voice line fits the youngest declared
  band. That includes AI-generated output: generate from a constrained prompt
  set, run a safety filter, and keep a human or rules-based review step before
  new content reaches children.
- No user-generated content visible to other children.
- No dark patterns: no countdown pressure, no loot boxes, no nagging upsells.

## Google Play Families policy

Apps whose target audience includes children must meet the Families policy:
Families-compliant SDKs only, ads (if any) through Families self-certified ad
SDKs with no interest-based ads to children, accurate content rating, and
Data Safety answers that match the release build.

Source: <https://support.google.com/googleplay/android-developer/answer/9893335>

## Children's privacy law

The FTC's amended COPPA Rule has required full compliance since April 22, 2026.
For a US service directed to children under 13 it requires verifiable parental
consent before collecting personal information, separate consent before
disclosing it to third parties, a written data retention policy, and a written
information security program. Collecting nothing is the design that keeps a
small team out of that scope; confirm with counsel for any specific app.

Source: 90 FR 16918 (April 22, 2025),
<https://www.federalregister.gov/documents/2025/04/22/2025-05904/childrens-online-privacy-protection-rule>

Age-assurance rules (Google Play's Age Signals API, US state app-store age
laws, regional rules) were still changing in late 2026. Check live status in
Play Console and with counsel before release.

## Release-gate lines to add

```text
target_audience_bands:
families_policy_status:
sdk_inventory_families_compliant:
personal_data_collected_from_children: none | <list and consent mechanism>
parental_gate_locations:
ai_content_screening_step:
content_rating_questionnaire_date:
```

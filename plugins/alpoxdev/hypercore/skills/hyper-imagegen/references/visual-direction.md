# Visual Direction Playbook

## Contents

- Load when
- Establish the visual promise
- Build the scene deliberately
- Maintain a series
- Inspect before making visual claims
- Vocabulary and deadwords
- Brief record
- Sources

## Load when

Load this reference after a request is in scope for image making and before a brief is compiled. Use it for a new image, an edit, or a prompt-only artifact. Do not load it for visual analysis, a collection of prompts, interface implementation, or code work.

This playbook chooses visible decisions from the request's purpose. It does not prescribe a house style or a provider command format. User-facing briefs, handoffs, and completion notes are Korean by default unless the user requests another language.

## Establish the visual promise

State the intended use and the single effect the image must achieve. Then identify what a viewer should notice first, what should support it, and what may remain quiet. A useful brief separates:

- **Purpose:** the decision, feeling, or action the image should support.
- **Hierarchy:** the first, second, and background reading order.
- **Subject:** the specific person, object, place, or event and its decisive traits.
- **Boundary:** requested facts that must remain unchanged, especially for an edit.

Do not replace a missing decisive fact with a decorative assumption. Ask one focused question when the omission changes identity, exact rendered text, required content, or the meaning of the image; otherwise make a reversible, purpose-led choice and disclose it in the brief.

## Build the scene deliberately

Choose a composition that makes the hierarchy observable: framing, viewpoint, subject scale, placement, depth, empty space, and crop. Describe relationships rather than mood labels. For example, say where a product sits, what is behind it, and where the eye travels rather than calling it merely polished.

Choose light in terms of source direction, softness, contrast, shadow behavior, and separation. Choose color by role: dominant field, supporting range, accent, and contrast needed for reading. Choose material and rendering cues that explain surface response, edge behavior, texture, and medium without borrowing a named provider recipe.

When the request needs text inside the image, record the exact string in quotation marks and specify its reading priority, location, contrast, scale, and clearance. Never silently correct, translate, shorten, or invent rendered text. Text fidelity and legibility remain unverified until the resulting artifact is inspected.

## Maintain a series

For a multi-image request, write a small invariant set before producing the first image. Keep only the facts that make the set recognizably related, such as recurring subject traits, viewpoint logic, lighting character, palette roles, typography treatment, material language, or layout rhythm. Record each image's intentional variation separately so variation does not accidentally alter an invariant.

For an edit, name the supplied source as evidence, distinguish preserved from changed regions, and keep a new output separate from the source. Do not claim identity, continuity, or preservation merely because the instruction requested it.

## Inspect before making visual claims

Inspect the persisted artifact against the brief when inspection is available and required. Check the hierarchy, subject facts, composition, light, color roles, material cues, exact rendered text, and each series invariant that applies. Record observed defects rather than rephrasing the prompt as a result.

If inspection is optional but unavailable or uncertain after persistence, report that the artifact exists while explicitly withholding claims about visible constraints, rendered text, legibility, and series consistency. If required inspection is unavailable, fails, or shows a critical miss, stop the visual-success report. Follow the runtime capability guidance for the permitted route and terminal state; do not retry indefinitely or present a prompt as an inspected image.

## Vocabulary and deadwords

Empty praise words reduce to one of three concrete paths before they enter a brief.

| Empty word | Numbers | Body response | Concrete example |
| --- | --- | --- | --- |
| 멋지게 / stunning | palette stops, Kelvin, key:fill ratio | where the eye lands first, how wide the frame feels | matte black field, single directional light |
| 고급스럽게 / beautiful | material count, spacing ratio | the texture a hand would expect | brushed metal, one contact shadow, dead-flat field |

Camera vocabulary describes the result, not the gear name.

| Gear name | Result description |
| --- | --- |
| wide-angle / 24mm | edges stretch, background recedes, subject feels small in a large room |
| telephoto / 85mm | background compresses toward the subject, layers flatten |
| macro | surface grain and micro-texture dominate, shallow focus |
| top-down / flat lay | objects read as shapes on a plane, no horizon |

Color binds to a named object: write "the chair is #2F4BFF", not a floating palette. Never emit a bare HEX list.

De-slop axes — replace the AI default with the real-world property.

| AI default | Real-world property |
| --- | --- |
| glowing rim light on everything | one motivated light source with a falloff direction |
| symmetrical centered subject | off-center placement with breathing room on one side |
| impossibly clean surfaces | seams, grain, wear, or a single imperfection |
| every color saturated | a restrained palette with one accent |

Deadwords are banned from briefs and reduced through the three paths above. The canonical set is the validator constant `DEADWORD_MAP`; this table mirrors it.

| Code | Surface forms |
| --- | --- |
| W_EMPTY_ADJ | 멋지게, 고급스럽게, beautiful, stunning |
| W_SD_ERA_BOOSTER | masterpiece, 8k, 4k, uhd, trending on artstation |
| W_WEIGHT_SYNTAX | (word:1.3) and any `(token:number)` weight form |
| W_SD_FLAG | --ar, --v and other trailing flag syntax |

## Brief record

Keep the working brief directly navigable with these fields:

```text
purpose:
hierarchy:
subject:
composition:
light:
color:
material_and_rendering:
rendered_text:
series_invariants:
preserved_or_changed_boundary:
inspection_checks:
assumptions_and_open_question:
```

Omit fields that genuinely do not apply, rather than filling them with placeholders. The record is a decision aid and inspection target, not proof that an image was generated or saved.

## Sources

> No external sources were used. This file states rules that belong to the hyper-imagegen package itself. Content checked 2026-09-21.

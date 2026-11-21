# Prompt Compilation Rules

Read this before compiling any brief, and when a rendered-text, series, or edit-boundary rule needs its exact wording.

Compile the request into a portable visual brief before choosing generation or prompt-file delivery. The brief describes the requested result; it does not encode a provider, model, command syntax, hidden control, or assumed capability.

## Resolve the request

Keep user-provided wording exact where exactness matters, especially text intended to appear in the image. Infer only reversible presentation details. Ask narrowly when a missing source, authority, rendered phrase, identity-preserving edit boundary, or preserve/change boundary prevents a faithful brief. Do not leave placeholders in a finished brief.

For an edit, name the supplied source's role, what must remain unchanged, and the requested change. Do not treat a reference as authority to alter it.

Label every supplied image by index and role before compiling: `Image 1: edit target`, `Image 2: style reference`, `Image 3: insert`. Images supplied only for style, composition, mood, or subject guidance make the request a generation with references; only an edit target makes it an edit. For a composite, say which element moves from which image into which, and that its light, perspective, and scale match the base.

Apply the specificity policy. A detailed request is normalized into a clean brief without new creative requirements. A generic request may gain only details that materially improve the result: composition or framing cues, intended-use or polish level, practical layout room such as negative space for copy, and scene concreteness the request implies. Never add characters, props, brands, slogans, palettes, or story beats the request does not imply, and never pick a left or right placement the surrounding layout does not support.

## Build one complete brief per image

Each requested image receives its own complete brief. Describe the scene in full sentences rather than a keyword list, front-loading in this order: scene or backdrop, principal subject, key details, constraints, intended use. A simple brief usually fits 30 to 80 words; a dense layout may run longer as labeled lines. For a crowded scene, order the build in steps ("first …, then …, finally …"). State, in natural request-led prose:

- the intended use and principal subject, including distinguishing attributes;
- action or state and the environment;
- framing, viewpoint, scale, spatial order, and deliberately empty space;
- visible lighting direction, contrast, shadows, palette, materials, and medium;
- exact in-image wording, when requested, with role, placement, hierarchy, contrast, and a requirement for sharp, correctly spelled, legible text;
- supplied-reference roles and edit preservation/change constraints;
- requested count and any requested canvas shape or output characteristics.

The rendered text in the brief must be the exact text to render. Do not silently translate, normalize, duplicate, abbreviate, or add words. Put each required string once, state how many times it appears (normally exactly once), and make reading order explicit. Spell an uncommon word or name letter by letter after the quoted string when accuracy matters.

## Use observable constraints

Prefer visible instructions over empty praise. Describe the intended arrangement, surface, light, color, texture, and separation directly. Avoid artificial perfection and describe natural material or skin texture when relevant.

Exclusions follow a three-tier policy. Tier 0 (default): every scene exclusion is expressed as a positive, concrete condition, such as one isolated subject, an unbranded surface, or an uncluttered background; negative phrasing is not used because a scene negative can be rendered instead of removed. Tier 1 (text-render guard): only the whitelisted guard phrases below may use `no ...` form, and only when the brief contains rendered text.

| Tier 1 whitelist |
| --- |
| `no invented glyphs` |
| `no watermark` |

This whitelist is canonical in the validator constant `TIER1_NEGATIVE_WHITELIST`; the upstream kit's "exactly seven phrases" figure is unverified, so the set starts with the two evidenced phrases and grows only when an eval row proves the need. Tier 2: any other negative is allowed only when the requester explicitly opts in. Provider-style negative tails (`--no ...`) remain forbidden.

Do not borrow the name of a living artist, real person, or trademark as a visual shortcut when describable properties suffice. Authorized identity or brand material supplied for an edit may be preserved within the stated boundary.

## Series and variants

For a series, write shared invariants into every brief: the recurring visual language, palette family, type treatment when text exists, lighting/material behavior, and recurring motif. Change only the requested image-specific subject, layout, or concept axis. For exploration, vary one principal axis at a time. Unrelated variants are separate images, never competing instructions in one canvas.

For an edit, write the change as `change only <X>; keep <Y> unchanged` and name the preserve list explicitly: identity (face, body, pose, expression), geometry and framing, layout, lighting and shadows, labels and in-image text, saturation and contrast, and camera angle, keeping only the items that apply. Restate the full preserve list in every later revision brief, because an unstated invariant drifts. When a chain of revisions has already drifted, compile a fresh complete brief from the original source and request instead of patching the drifted result.

## Compilation boundary

The compiled text must remain exact and ready to use as-is. Keep delivery reports, capability observations, paths, error explanations, and runtime parameters outside the prompt file. Do not add hidden provider flags, legacy shorthand, profile labels, fixed tiering, aspect-ratio tails, or static size assumptions. Pass supported structured fields separately only when the active runtime exposes them; their absence does not alter the rendered brief.

Before delivery, ensure every brief is complete, maps to one image, preserves exact requested text, identifies reference and edit boundaries, contains concrete visual constraints, and contains no report prose or unresolved choice.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Indexed input-image roles, references-only meaning generation, and the specificity policy with its allowed and disallowed augmentations | OpenAI `imagegen` skill, <https://github.com/openai/skills> (commit `e6afb0d`, file `.system/imagegen/references/prompting.md`) |
| Scene-first ordering, `change only X` with a named preserve list restated every iteration, and letter-by-letter spelling | OpenAI image prompting guide, <https://developers.openai.com/api/docs/guides/image-prompting>; OpenAI Cookbook image prompting guide, <https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide> |
| Describing the scene instead of listing keywords, step-by-step phrasing for crowded scenes, and restarting from a full description after drift | Google Developers Blog, "How to prompt Gemini 2.5 Flash Image Generation for the best results", 2025-08-28, <https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/> |
| Front-loading subject before style and context, and the 30-80 word band for an ordinary brief | Black Forest Labs FLUX.2 prompting guide, <https://docs.bfl.ai/guides/prompting_guide_flux2> |
| The exclusion tiers, the brief boundary, and the series rule | this package's own rules |

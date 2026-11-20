# Motion and shot planning

## Decide whether to edit

- Honor a request to use the prompt verbatim. When the user supplies a prompt, check the subject, action, camera, timing, continuity, and constraints that matter for the requested shot. Leave discretionary details to the model.
- If the prompt is clear, consistent, and already meets the request, return or submit it verbatim. Apply the same check to a general request to optimize it.
- Resolve consequential gaps, ambiguities, or conflicts using the user's request and references. If a key detail remains unclear, ask before finalizing the prompt.
- Change only the text needed to resolve the issue or make the requested edit. If the user supplies a sentence that can be added directly, append it to the original. When adding an ending beat, preserve the requested action, timing, and end state. Leave the intervening motion to the model unless the user specifies it. For model-specific reference syntax, adjust only the required references.

## Motion-first prompt order

Use the relevant items below when writing a new prompt or filling a gap. Describe action and continuity first. Express broad quality requests such as "cinematic" through visible details such as lighting, materials, depth of field, and framing.

1. Format and duration intent.
2. Opening frame and subject position.
3. Beginning, development, and completion of the subject action.
4. One primary camera movement and its speed.
5. Environmental movement and physical effects.
6. Lighting, color, lens character, and time-of-day mood.
7. Continuity anchors such as identity, wardrobe, product structure, logo, architecture, and screen direction.
8. Necessary constraints such as no extra subjects, deformation, text, or watermark.

## Camera choices

- Locked-off: observation, product detail, or graphic composition.
- Slow push-in: emphasis, intimacy, or detail reveal.
- Pull-back reveal: expanded environment or scale.
- Lateral tracking: follow motion while preserving side relationships.
- Controlled orbit: dimensional display of a product or character.
- Crane rise or drop: establish or resolve spatial scale.
- Handheld follow: urgency or UGC realism; specify the intended stability.
- Whip pan: use only for a deliberate transition and name the final landing subject.

Do not stack multiple camera-movement verbs into one five-second shot.

For a continuous hand-object interaction, frame the entire action path so the participating hands and object stay visible through the action and its final handoff or placement.

## Duration and multiple shots

- 5 seconds: one action and one camera movement.
- 10 seconds: one action with setup and result, or two simple connected beats.
- 15 seconds or longer: plan a compact multi-beat sequence only when the live model supports it.

For multiple shots, give each shot a duration, framing, one narrative task, subject action, camera movement, and continuity anchor. Shot durations must sum to the total duration. The full plan is still one generation submission.

When a continuous hand-object interaction spans a cut, explicitly repeat the same hand grip, object position and support contact at the outgoing shot's end and the incoming shot's start. Use a brief stable beat only when it fits the requested pacing; continue the action without replaying steps or adding a long pause.

## Reference media

- A first frame locks the opening composition and motion starts from it.
- For ordered keyframes, describe the motion between consecutive supplied states and settle into the final state. Add overshoot or a return movement only when requested.
- A tail frame defines the target ending only when the live model supports it.
- An identity reference locks face, apparent age, hair, wardrobe, proportions, and distinguishing traits.
- A product reference locks dimensions, material, label, logo placement, and moving parts.
- A motion-source video should preferably contain one shot, no occlusion, and one subject. Follow the live tool's exact duration and resolution limits.

For advertising or explainer video, assign one communication task to each beat: hook, context, evidence, or close. Never invent performance claims, testimonials, statistics, prices, awards, or certifications.

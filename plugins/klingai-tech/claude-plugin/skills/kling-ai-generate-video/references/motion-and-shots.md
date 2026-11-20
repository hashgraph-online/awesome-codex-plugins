# Motion and shot planning

## Decide whether to edit

- If the user asks to use their prompt as written, preserve it verbatim. Otherwise, check the supplied prompt for the details that matter to this video, such as subject, action, camera, timing, continuity, and constraints. Leave optional creative details to the model.
- If the prompt is clear, consistent, and already meets the user's requirements, return or submit it verbatim. Apply the same test to a general request to optimize it. Follow an explicit request for a rewrite or a specific change.
- Resolve gaps or conflicts using the request and its references. Ask only if an important requirement remains unclear.
- Make the smallest edit that meets the request or fills a material gap. Append a ready-to-use line from the user verbatim when it can be added without conflict. When adding an ending, retain the requested action, timing, and final position or state. Leave the intervening motion to the model unless the user specifies it. If the selected model requires prompt reference syntax, make only the necessary binding edits. Clarify before submitting if those edits conflict with a request to preserve the prompt verbatim.

## Motion-first prompt order

Use the relevant items when writing a prompt or filling a specific gap. Establish the action and continuity first. Express abstract quality requests through visible details such as lighting, materials, depth of field, and framing.

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

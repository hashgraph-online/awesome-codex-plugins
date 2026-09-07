# Visual mode

Use a visual companion when asked by the user or dynamic behavior is materially harder to understand statically: state transitions, ordering, concurrency, transformations, migrations, geometry, or distributed flows.

Create one self-contained HTML file under the operating system's temporary directory. It complements the chat explanation; it does not replace it or prove production behavior.

## Safety contract

- Use sanitized fictional data.
- Use inline HTML, CSS, and JavaScript only: no network calls, external assets, packages, telemetry, or persistence.
- Never import or execute production code, secrets, user data, or repository modules.
- Model only the behavior needed for the named concept and label simplifications.

## Interaction contract

Show the starting state, the user's available action, the resulting state, and the invariant or ordering rule being illustrated. Prefer a step, scrub, reorder, or input control that exposes cause and effect; omit decorative interaction. Keep text, keyboard focus, color contrast, and reduced-motion behavior accessible.

Open the file in the available browser, exercise every control, inspect the initial and edge states, and confirm it works without network access. Report the temporary path and any modeled limitation in chat; never copy the file into the repository.

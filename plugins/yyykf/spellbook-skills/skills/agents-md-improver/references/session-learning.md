# Session Learning Mode

Use this mode when the user asks to capture learnings from the current session, revise instructions from recent work, or preserve newly discovered repository-specific behavior.

## Extract

Extract only repeatable information that would make future agent sessions more effective:

- commands or workflows that were used, verified, or are repository-specific;
- architecture or module boundaries that are not obvious from filenames;
- coding, testing, review, or release conventions actually followed in this repo;
- environment quirks, tool paths, version constraints, sandbox caveats, or known failure modes;
- user preferences that should steer future work in this project.

## Avoid

- generic engineering advice;
- one-off debugging details unlikely to recur;
- unverified assumptions or stale guesses;
- long explanations, logs, secrets, tokens, private URLs, or machine-specific credentials;
- duplicates of existing instructions.

## Output Template

Show proposed updates before editing:

````markdown
### Update: <target file>

Why: <one-line reason this helps future agent sessions>

```diff
+ <concise durable instruction>
```
````

If the session produced no durable reusable learning, say that no update is warranted and explain briefly.

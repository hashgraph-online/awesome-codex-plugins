# Next-Move Prompt Levels

The three prompt depths the router's Next move mode can hand back (short copy/paste, full operator prompt, granular steps) and what each must contain.

### Quick Prompt (Default)

Write 2-4 sentences that another capable agent can paste and run:

1. Name the selected skill or lane, exact target, and one concrete outcome.
2. Include the single current fact, scope boundary, or preservation rule most
   likely to change execution.
3. Name the observable done signal and its verification.
4. Add a stop condition only when a material blocker is plausible.

Do not dump field labels, the score breakdown, a long evidence list, or numbered
implementation steps by default. After the prompt, add exactly:

```text
Say "expand prompt" for the full operator version or "make it granular" for exact steps and commands.
```

### Expanded Prompt (On Request)

When the user says `expand prompt`, render the full self-contained prompt below.
Include only applicable fields and never leave placeholders such as `TBD` or
`<path>`.

```text
Use $<skill> to complete this task.

Target: <exact repo, worktree, route, URL, document, account, or surface>
Objective: <one concrete outcome>
Current verified state:
- <fresh fact and its source>
Authorized scope: <read-only, local edits, live mutation, or other exact boundary>
Preserve: <dirty work, copy, data, identities, or other invariants>
Source-truth order: <current sources in precedence order>

Required work:
1. <smallest complete sequence>

Done signal: <observable proof>
Verification:
- <command, readback, screenshot, URL, test, or response>
Stop and report if: <material ambiguity, unsafe mutation, failed gate, or missing authority>

Return: outcome, changed surfaces, verification evidence, caveats, and status.
```

### Granular Prompt (On Request)

When the user says `make it granular`, render the expanded prompt and decompose
`Required work` into atomic numbered steps. Include exact commands, absolute
paths, mutation checkpoints, expected readbacks, and stop conditions wherever
current evidence supports them. Do not invent missing commands or values; make
resolving a missing decisive fact the first step.

For multi-lane work spanning more than one specialist, start expanded and
granular prompts with `$suede-agent-teams` so the coordination lane owns the
handoff. For a single-lane task, start with the specialist the recommendation
names directly. Use exact absolute paths, URLs, handles, branch names, and
verification commands when current evidence provides them.

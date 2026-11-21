# README Craft

Use this reference when the caller asks to create, update, rewrite or check a README.

## Request shapes

- **New:** no README exists, or the caller asks for one from scratch. Take the
  project name, runtime, install method and license from the repository; ask
  only for facts it cannot supply, such as the problem in one sentence, the
  first thing a user runs to see it work, and what the tool touches.
- **Update:** bring one section or fact of an existing README current (for
  example, install steps that no longer match the code). Edit that part in
  place under [Grounded writing step 3](../SKILL.md#grounded-writing): keep the
  file's shape, then run the [checks](#checks).
- **Rewrite:** regenerate an existing README with these patterns, using the
  current file as context.
- **Check only:** inspect an existing README against these patterns without
  rewriting it, and report the evidence.
- A README exists and the request names no shape: ask once which the caller wants.

## The Patterns

Every README this mode generates or rewrites follows these patterns; an update
applies them only to the part it edits.

### 1. Lead with the problem, not the framework

The reader should understand what pain you solve in one sentence. Framework
references belong in the body as design rationale.

### 2. Show, don't claim

Assertions without evidence trigger hostility. Show a terminal transcript or a
code example of the tool working instead of adjectives.

### 3. Trust block near install

Before a user installs anything that runs code, hooks, or modifies config, they need to see:

| Concern | Answer it |
|---------|-----------|
| What does it touch? | Files created/modified, hooks registered |
| Does it exfiltrate? | Telemetry, network calls, data leaving the machine |
| Permission surface | Shell commands, config changes, git behavior modifications |
| Reversibility | How to disable instantly, how to uninstall completely |

This goes near the install command, not buried in an FAQ. If the tool runs
hooks, modifies config or makes network calls and the README has no trust
block, report the mismatch.

### 4. Collapse depth, don't delete it

Detailed workflow steps, architecture deep-dives, theory, and reference material
belong in `<details>` blocks. Never delete depth to achieve brevity; collapse it.
Every `<details>` block needs a blank line after `<summary>` and before
`</details>`, or GitHub renders it as raw HTML; use Markdown inside it.

### 5. Section order serves adoption

```
Problem → Install → See It Work → Getting Started Path → How It Works (collapsed) → Reference
```

State the differentiator once and demonstrate it once. Keep one hero install
command and one canonical reference, not the same command in three places.

## Checks

Run the repository's own link or docs checks where they exist and read the
exact README against the patterns above. Record concrete matches, checked
scope, and anything the local environment could not check; a check that could
not run is reported as not run, never as passed. These results are evidence,
not a semantic verdict. On a check-only request, report findings and leave the
file unchanged.

Return the file, the checks with their results, unchecked scope and the
findings, without approval or next-action language.

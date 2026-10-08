# Codex parity

Codex loads the canonical `skills/<name>/` package directly. The Codex plugin
manifest points at `./skills`, and `ao skills link` links the same directories
into `~/.codex/skills`. There is no generated Codex copy, no override layer and
no `prompt.md`, so one source package has to read correctly on every host.

## What Codex reads

- `SKILL.md`. The `name` and `description` drive discovery. Codex ignores the
  AgentOps host fields. It refuses a skill whose frontmatter repeats a key, has
  no `description`, or has a `name` longer than 64 characters.
- `agents/openai.yaml`, when present: display metadata, tool dependencies and
  the invocation policy. Codex does not read `disable-model-invocation` from
  `SKILL.md`.
- Every `SKILL.md` below `skills/`. A nested one is loaded as a skill of its
  own, so fixtures and scaffolds live outside the tree.

## Explicit-only skills

A skill marked `disable-model-invocation: true` needs the matching Codex policy
in its own `agents/openai.yaml`:

```yaml
policy:
  allow_implicit_invocation: false
```

Nothing derives this file. Without it, or when it does not parse, Codex selects
the skill implicitly.

## One body for every host

- Refer to another skill by name or relative link, not by a host's invocation
  syntax (`/name`, `$name` or a `Skill(...)` call).
- Keep host-only tool names and installed-skill paths (`~/.claude/...`,
  `~/.codex/...`) out of the shared flow. When a step differs by host, say which
  host the sentence is for.
- A skill that documents several runtimes names each one plainly.

## Check

```bash
bash scripts/validate-codex-api-conformance.sh
```

It checks the loader facts above and the explicit-only policy. It does not
prove that Codex selected or followed the skill; that needs a session on the
host.

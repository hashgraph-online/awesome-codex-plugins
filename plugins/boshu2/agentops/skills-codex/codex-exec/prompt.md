# Codex Execution Profile — codex-exec

Read the sibling base skill `../SKILL.md` (full overview, critical constraints,
output spec, exit codes, rubric, examples, troubleshooting) before acting. This
profile is the Codex-native, step-ordered execution path; the base SKILL.md is
the source of truth. The one inviolable rule: **subscription billing, never
per-token API billing.**

## Steps

1. **Confirm the live surface.** Run `codex exec --help` and
   `codex exec resume --help`. Flag shape changes between releases (base is
   verified against `codex-cli 0.137.0`) — never act on a remembered shape.
2. **Verify the lane is on the subscription.** Run `codex login status` — it MUST
   read `Logged in using ChatGPT`. Then confirm no API key: the env var
   `OPENAI_API_KEY` MUST be empty. If either fails, STOP and fix auth (browser
   OAuth `codex login` or `--device-auth`) before dispatching.
3. **Pick the sandbox for the role.** `-s read-only` for validators,
   `-s workspace-write` for workers that edit, `-s danger-full-access` /
   `--dangerously-bypass-approvals-and-sandbox` ONLY inside an already-sandboxed
   host.
4. **Dispatch the worker / validator.** Set the working root explicitly with
   `-C/--cd <DIR>` (don't assume cwd). Capture the result deterministically:
   `-o/--output-last-message FILE`, `--json` (JSONL events), or
   `--output-schema FILE` for a machine-checkable verdict. Pipe a prompt via
   stdin with a trailing `-`. Use a named lane with `-p/--profile <name>`.
5. **Resume to continue.** `cd` into the repo first, then
   `codex exec resume --last "<follow-up>"` (or `resume <SESSION_ID>`). Resume
   does NOT accept `-C/--cd` or `-s/--sandbox` — it inherits the original root and
   sandbox; that is why you `cd` rather than pass `-C`.
6. **Branch on the exit code, not scraped text.** Exit `0` = run completed, parse
   the structured result (`-o FILE` / last `--json` item). Non-zero = a Codex
   error (auth, sandbox denial, bad flag, model/tool error) — do NOT treat it as
   a verdict; re-check auth/sandbox/flags, then retry or escalate.
7. **Capture artifacts.** Save the result file / JSONL into the session/handoff
   as the verification surface.

## Guardrails

- **Never API-bill a worker.** Do NOT set `OPENAI_API_KEY` and do NOT use
  `codex login --with-api-key`. That flips Codex from flat-rate sub billing to
  per-token API billing — the Codex twin of the banned `claude -p`. A factory
  cycle on API keys silently burns real money.
- **Confirm the sub before dispatch.** `codex login status` must read
  `Logged in using ChatGPT` (step 2); that check is the only thing between a
  green run and a surprise invoice.
- **Verify before acting.** No remembered flag shapes — `--help` first (step 1).
- **Sandbox is the blast radius.** `codex exec` runs model-generated shell
  commands; match `-s` to the role. `--dangerously-bypass-approvals-and-sandbox`
  removes every guardrail — externally-sandboxed hosts only.
- **Don't strand work in `--ephemeral`.** It skips session persistence, so there
  is nothing to `resume`; a crashed ephemeral run cannot be recovered.
- **Result must be deterministic.** Use `-o FILE` / `--json` / `--output-schema` —
  never scrape terminal noise for a loop's verdict.
- **Multi-account lanes go through `caam`, not env-var juggling.**
  `caam exec codex <profile> --` keeps each Pro lane isolated; hand-setting
  `CODEX_HOME` invites cross-account token bleed.
- **Backstage only.** Never surface these commands or framing in client-facing
  AI Partner content.

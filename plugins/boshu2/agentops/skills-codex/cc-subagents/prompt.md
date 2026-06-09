# Codex Execution Profile — cc-subagents

Read the sibling base skill `../SKILL.md` (full overview, the five critical
constraints, four-phase workflow, role-profile table, output spec, quality
rubric, examples, troubleshooting) before acting. This profile is the
Codex-native, step-ordered execution path; the base SKILL.md is the source of
truth. The one inviolable rule: **fungible workers on subscription billing,
never a per-token API path, never a shared write target without isolation.**

In Codex, a "subagent" is a separate-context `codex exec` worker (or an NTM pane),
not a Claude Task-tool call. The fungibility contract is identical: each worker
runs blind in its own context, returns one final report, and is verified by
evidence — only the orchestrator integrates.

## Steps

1. **Confirm the live surface.** Run `codex exec --help` (and
   `codex exec resume --help` if you'll continue a worker). Flag shape changes
   between releases — never act on a remembered shape.
2. **Verify the lane is on the subscription.** Run `codex login status` — it MUST
   read `Logged in using ChatGPT`, and `OPENAI_API_KEY` MUST be empty. If either
   fails, STOP and fix auth before dispatching any worker.
3. **Decide: spawn or inline?** Spawn ONLY when at least one holds — the work is
   independent/parallelizable (N tasks, no shared write target), it is
   long-running/exploratory and would pollute the orchestrator's context, or it
   needs write isolation. Otherwise inline it; spawning costs a full context load.
   State the parallelism + file-ownership map out loud first.
4. **Pick the role profile.** Map role → sandbox + effort + isolation:
   explorer/judge = `-s read-only`, low effort, no isolation (read-only);
   implementor = `-s workspace-write`, high effort, its own git worktree.
   Give each worker the minimum capability for its job.
5. **Set up write isolation for parallel writers.** Create a worktree per
   write-worker (`git worktree add <path> -b <branch>`) and dispatch each worker
   with `-C/--cd <worktree>` so parallel edits cannot collide. Read-only workers
   need no worktree.
6. **Dispatch each worker self-contained.** Pass the exact files it owns, the
   spec, and the acceptance check in the prompt — the worker carries NO
   conversation state ("as we discussed" means nothing). Capture the result
   deterministically: `-o/--output-last-message FILE`, `--json`, or
   `--output-schema FILE`. Run in the background where the orchestrator must keep
   working (NTM pane or `&` with captured output); re-engage on completion.
7. **Gate the return on evidence, not self-report.** For each finished worker,
   re-run its test or re-read its artifact in a SEPARATE context (author != judge).
   Branch on the exit code (`0` = completed, parse the structured result; non-zero
   = a Codex error, not a verdict — re-check auth/sandbox/flags). Do NOT trust the
   worker's "done."
8. **Integrate once, after all green.** Run the repo's FULL validation gate once
   (not a remembered subset), then merge the worktree branches. Save each result
   file as the verification surface in the session/handoff.

## Guardrails

- **Never API-bill a worker.** Do NOT set `OPENAI_API_KEY` and do NOT use
  `codex login --with-api-key`; that flips Codex to per-token API billing — the
  Codex twin of the banned `claude -p`. Confirm `codex login status` reads
  `Logged in using ChatGPT` before any dispatch.
- **No gratuitous workers.** Every spawn must clear a Step-3 criterion
  (independent / long-running / needs isolation). A single small or
  tightly-coupled task is inlined, never spawned.
- **Non-overlapping file ownership is mandatory.** Workers run blind to each
  other — two editing one file race and clobber. If two tasks touch one file,
  combine them into one worker; otherwise give each writer its own worktree.
- **Least-tools / least-sandbox by default.** Match `-s` to the role; explorers
  and judges are `read-only`. An over-privileged worker is a blast-radius bug.
  `--dangerously-bypass-approvals-and-sandbox` only inside an already-sandboxed host.
- **Self-contained prompts only.** Every fact the worker needs (paths, spec,
  acceptance check) goes in the prompt; it has a fresh context.
- **Verify by evidence in a separate context.** The orchestrator sees only the
  worker's claim. Author != judge: re-run the test / re-read the artifact before
  integration. Run the full repo gate once after all workers complete.
- **Result must be deterministic.** Use `-o FILE` / `--json` / `--output-schema`
  for a worker's verdict — never scrape terminal noise.
- **Multi-account lanes go through `caam`,** not env-var juggling, to keep each
  Pro lane isolated.
- **Backstage only.** Never surface these commands or framing in client-facing
  AI Partner content.

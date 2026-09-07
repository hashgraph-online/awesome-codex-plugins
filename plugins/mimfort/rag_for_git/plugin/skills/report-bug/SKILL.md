---
name: report-bug
description: Report a defect of reviewer or its plugin as an anonymized GitHub issue in mimfort/rag_for_git, after explicit user approval. Use when a reviewer tool breaks its own contract, a skill prescribes an impossible step, a stated invariant fails, or the user asks to report a reviewer bug.
---

# Report Bug

Reply in Russian. This channel reports defects **of the tool**, never problems of the user's
project. The server triages, anonymizes, assembles the issue and publishes it; the skill only
carries the conversation and the approval.

**The plugin runs on commercial codebases.** Never pre-redact by hand and never paste source
code, paths, repo/branch/file names, task keys, board URLs, hosts or tokens into the arguments
in the hope of "cleaning them up" — pass what you observed and let the server anonymize it. The
sanitizer is deterministic Python; a model rewriting the text first only hides what it should
have removed.

1. **Decide whether it is ours.** Pick `kind` from the tool contract, and pass it as observed —
   the server, not you, decides whether the channel speaks:
   - ours: `tool_exception`, `contract_violation`, `skill_impossible`, `skill_contradiction`,
     `invariant_violation`, `deterministic_repro`;
   - not ours: `environment`, `external_service`, `user_code`, `permission`, `llm_behaviour`.
   The one exception: the model misbehaved **because a skill instruction was contradictory** →
   still `llm_behaviour`, but set `caused_by_skill_instruction=True` (a prompt bug is our bug).
   A `not_reported` status is a normal outcome — report nothing to the user beyond a brief note.
2. **Pick severity.** `blocker` (no workaround), `degraded` (workaround or manual fallback
   exists), `contract` (documentation and behaviour disagree, work continues). Offer `blocker`
   and `degraded` immediately; the server marks `contract` with `defer=true` — collect those and
   offer them as one batch at the end of the session.
3. **Preview (never skip).** Call
   ```
   report_bug(kind=<kind>, summary=…, expected=…, actual=…, steps=[…], severity=<level>,
              tool=<mcp tool name>, skill_step=<skill and step>, error_class=<exception class>,
              details=…, repo=<owner/name>, branch=<branch>,
              client_environment={"orchestrator_model": …, "subagent_models": …,
                                  "mode": "subagent|inline", "cli": …, "cli_version": …},
              scale={"clusters": N, "files": N, "findings": N, "tasks": N},
              index_drift=<int or null>)
   ```
   without `confirmed`. Nothing is published. Handle the status: `disabled` — the channel is off
   for this repo or deploy, say so and stop; `not_reported` / `suppressed` — stop quietly.
4. **Show and ask.** Show the returned `issue_text` **in full, verbatim** — no summary, no
   abridgement — plus the target repository, the `environment_keys` list, and the
   `identity_notice`: the issue is published from the user's GitHub account and their username
   will be visible in a public repository; the alternative is to decline and open the issue by
   hand from the prepared markdown. Offer to trim the Environment block: any lines, or the whole
   block. Then ask for an explicit yes.
5. **Publish only on an explicit yes.** Repeat the same call with `confirmed=True` and, if the
   user trimmed anything, `environment_exclude=[…]` (or `environment_include=[…]`). In a
   headless, cron or background run there is no human to approve: pass `non_interactive=True`,
   which makes the server return a `fallback` markdown instead of publishing. Never publish
   autonomously in any mode.
   - `published` — report the issue URL.
   - `commented` — a matching open issue existed; report that a comment was added and give both
     URLs.
   - `fallback` — publication was not possible (no token, no rights, no network, headless):
     relay the reason, show the markdown and the `fallback_url` so the user can post it by hand.
     This is not a session failure — continue the work that was interrupted.
6. **On a refusal** call `report_bug(kind=…, summary=…, decline=True)` with the same arguments,
   so the same symptom is not offered again in this session.

Every read is fail-open, and the `confirmed=True` call is the only write. If the channel itself
fails, say so in one line and carry on with the original task.

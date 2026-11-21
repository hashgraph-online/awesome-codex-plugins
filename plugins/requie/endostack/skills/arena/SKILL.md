---
name: arena
description: Several subagents build the same artifact from one brief in isolation, a read-only judge scores them, and you pick a base and graft in the best parts of the rest. Use for "arena this", "competing attempts", "second opinion on this approach".
---

# arena

Run several independent attempts at one brief, judge them, and merge. Use it when a single attempt risks committing to the first structure that comes to mind: a design, an API, a hard function, a prompt, a document. The [`architect` skill](../architect/SKILL.md) calls it to produce design sketches.

If the job should be split into slices, or raced for the first success with one combined report, use the [`swarm` skill](../swarm/SKILL.md) instead. Arena gives every runner the same brief and merges what comes back. Swarm divides or races and reports.

Track a todo list with six items: frame, launch, judge, pick, graft, verify.

## 1. Frame

Every runner receives identical instructions, so the instructions are the job. Get them right before launching.

1. **Name the artifact.** Say exactly what each runner produces and in what form: "a module with these three public functions and tests", not "an implementation".
2. **Write the rubric.** Three to six criteria specific to this task, each something you can grade on its own. "Handles a partial write without corrupting the index" is gradable. "Good quality" is not. Runners never see the rubric. You and the judge use it. If the artifact touches a trust boundary, include a criterion for it, such as "untrusted input is parsed once, at the edge".
3. **Choose runners.** Read the `arena-runners` key from the EndoStack model config (`.endostack/models.toml` wins over `~/.endostack/models.toml`). One entry is one runner. With no config, use two: `strong` and `fast`. A caller such as architect may pass its own list, which replaces this one. `inherit` (or `auto`) means the runner uses the session model, so pass no model. Add runners when you want more design directions explored. Repeat one model in every slot when the work needs volume more than judgment.
4. **Isolate.** Give every runner its own place to write: a separate git worktree if the agent supports it, otherwise a per-runner folder under a temp directory for this arena. Runners writing to shared files would overwrite each other and see each other's work, which destroys their independence ([`principle-separate-before-serializing-shared-state`](../principle-separate-before-serializing-shared-state/SKILL.md)).

**Model names that fail.** If the agent rejects a configured name, run that slot on its default tier and tell the user in one line. If a tier itself cannot be resolved, take the closest model the agent's error lists. Never block the arena on a model-name problem.

**One model only.** If the agent cannot choose a model per subagent, say so in one line ("Single-model arena: runners differ by brief, not model."). Keep the shared brief identical and append to each runner one distinct starting constraint, for example "optimise for the smallest public API", "optimise for the simplest data model", "assume this will need to scale to ten times the load". Without that, same-model runners tend to converge on one answer and the arena adds cost without adding options.

## 2. Launch

Spawn every runner in one message, in the background when the agent supports it, with write access limited to its own isolated location. If the agent cannot run subagents in parallel, run the briefs one after another yourself, starting each from a clean state, and do not reread an earlier candidate before writing the next.

Each runner gets:

- The task and the artifact definition.
- The grounding material, by path.
- Its private output path.
- The caller's runner brief, if one was passed.
- An instruction to produce the artifact plus a short rationale listing the alternatives it considered and rejected.

A runner that returns nothing is dropped. Record that and continue with the rest.

## 3. Judge

Wait until every runner has finished. Never start the judge while a runner is still writing, since it would grade a partial candidate.

Read the `arena-judges` key (default `["strong", "fast"]`). Pick one model from it, preferring one from a different family than the session's, because a judge from the same family tends to favour output that resembles its own. On a single-model agent, give the judge a brief that tells it to argue against the candidate it initially prefers before settling.

Spawn one read-only judge with the rubric and every candidate's path. It grades each criterion for each candidate, with a short reason per grade, and recommends a base with its reasoning. It runs while you do step 4.

## 4. Pick

Read every candidate in full. Grade each against each rubric criterion separately. An overall impression is how anchoring creeps back in.

Compare your grades with the judge's. If you both chose the same base, that confirms it. If you differ, one of you is biased or a criterion was ambiguous. Read both sets of reasons before choosing, and tighten the criterion's wording in your notes.

Prefer the base that a future maintainer could extend most safely without breaking its invariants. On a tie, pick the one with the clearer boundary or the smaller API ([`principle-laziness-protocol`](../principle-laziness-protocol/SKILL.md)).

## 5. Graft

Go back through each losing candidate once more, looking for parts worth taking. Expect one or two per candidate, not large sections. Integrate each by hand so the result reads as one design ([`principle-redesign-from-first-principles`](../principle-redesign-from-first-principles/SKILL.md)). Do not paste.

If every candidate reached the same structure, record strong agreement and ship the base with no grafts. If the candidates differ wildly, the framing was too loose: rewrite the brief and rerun. Averaging very different designs produces something none of them would defend.

## 6. Verify

Verify the merged artifact the way you would verify any deliverable ([`principle-prove-it-works`](../principle-prove-it-works/SKILL.md)): run it, test it, or read it back against the rubric with evidence. If verification finds something the arena missed, decide which happened:

- The framing missed it. Reframe and rerun.
- A candidate caught it and you skipped the graft. Go back to step 5.

Report the problem either way. Never hide it.

## Output

The merged artifact, plus a short synthesis note:

- The chosen base and why.
- The judge's recommendation, and whether it matched yours.
- Each graft and the candidate it came from.
- What you turned down and why.
- Whether runners converged, and any that dropped out.
- The verification result.

Inside architect, this note becomes the rationale's synthesis section.

## Done when

The merged artifact passes verification and the synthesis note is complete. Wild divergence, or a framing error found in verification, sends you back to step 1.

## Related

- The [`tarique-mode` skill](../tarique-mode/SKILL.md) carries the general guidance on subagent effort and speed.
- The [`setup-endostack` skill](../setup-endostack/SKILL.md) writes `arena-runners` and `arena-judges`.

# Eval

You own the experiment design. The question is whether a change to a skill, structure, or prompt changes agent behavior the way you intend, measured before you adopt it. For code performance use [perf-issue.md](perf-issue.md) or [hillclimb.md](hillclimb.md).

## Blinding

All of these are required. A candidate that knows it is being evaluated behaves differently, which makes the result meaningless.

- Keep every word that hints at an evaluation out of anything a candidate can see, including directory names, file names, and the prompt. Banned terms include arena, benchmark, candidate, compare, eval, experiment, judge, rubric, score, test, and anything close to them.
- The prompt reads like a real user stating a goal, with no meta framing.
- Do not cue the reasoning chain. Never ask candidates to list the skills, principles, or files they used. Ask for design notes in general, and grade chain-following from the code's shape and the transcript, not from self-report.
- Directory and project names look like ones a real user would pick.
- No candidate is told other candidates exist.
- The judge may know it is judging, but sees outputs only under sanitized labels, never model names.
- For a two-variant comparison, a single judge grades the outputs of both variants together, using one scale, and is not told which output came from which variant.

## Steps

1. **Frame.** Name the variant and define success. Write a judge-only rubric of three to six concrete criteria. Candidates never see it.
2. **Build sanitized environments.** One working directory per candidate, with the variant installed. Plant the context a real task would have: a project skeleton and the skills a candidate would naturally read. Keep secrets out of these directories; use dummy credentials where the project needs some.
3. **Write one natural prompt** a user would actually type, leaking nothing about what you measure.
4. **Spawn N candidates** in parallel on different model families, following the `arena` skill's candidate phase. Each gets its own sanitized directory and the identical prompt. Tune effort and speed per the policy in [../SKILL.md](../SKILL.md).
5. **Spawn one blinded judge** from a model family none of the candidates used, following the `arena` skill's judging phase. Spawn it as a read-only subagent. It sees sanitized labels and the rubric only.
6. **Verify chain-following from transcripts.** Read each candidate's transcript from the current workspace's transcript directory only (the host gives the path). Never search other projects' transcript folders, because that crosses workspace boundaries and exposes private chats from unrelated work. Check which files each candidate actually opened and grade from those reads and the code's shape. If the host exposes no transcripts, grade from code shape alone and say so.
7. **Read every output yourself** and compare with the judge. Disagreement points to model bias or an ambiguous rubric. Synthesize.

## Reply

Name the variant and give the rubric. Add notes on each candidate, what the judge concluded, how you reconcile that with your own reading, and whether you recommend adopting the variant.

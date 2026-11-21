# The same good result every time

What repeats and what does not is measurable, so put each part on the right side of the line.

| Part | Repeats? | So |
|---|---|---|
| A HyperFrames render | Yes. In our test, 3 renders and 1 from a fresh clone in another folder gave the same SHA-256 (video, audio, image, GSAP, web font; same Mac) | Keep the source, rebuild the render. Docs promise more across machines only with `--docker` |
| An AI video generation | No. Google: seed "doesn't guarantee determinism". ByteDance: "complete consistency is not guaranteed" | Keep the bytes of every take you paid for |
| An AI image generation | Sometimes. Flux dev on fal claims the same image for the same seed and model version. Unverified across versions | Keep the bytes |
| The model itself | No. Veo 3.1 Preview [was shut down](https://aistudio.google.com/docs/video) with a date of 2026-10-22 | Record the exact model id; a recipe can outlive its model |
| The agent | No | Write the process into files and scripts, and check results with tools that need no opinion |

## The checklist

1. **Keep the bytes of every approved take.** `save` does this. A recipe alone cannot get the same clip back.
2. **Record how each was made.** `media note <file> --prompt-file shots/sh010/shot.md --model <id> --seed <n> --cost <usd> --job <id> --url <link>`. Log rejected takes too, with `--status rejected --note "why"`, so the next session doesn't retry a dead end. The fields come from the best public example, [ink-trailer-assets](https://github.com/siliconjungle/ink-trailer-assets).
3. **Pin tool versions.** HyperFrames' `package.json` scripts pin the version. Use exact versions, and commit the lockfile for Remotion. Write the model id down, not "the latest".
4. **Pin outside scripts.** `gsap@3.15.0` in a CDN link is pinned. A web font is not fully pinned; download it into `assets/` for a film you may render again in a year.
5. **One command to rebuild.** Put the exact render command in `AGENTS.md`. An instruction there is followed: in the ETH study, a tool named in the file was used 1.6 times per task, against almost never without it.
6. **Nothing random at render time.** No `Date.now`, `requestAnimationFrame` or unseeded `Math.random` in compositions. In Remotion use `random(seed)` and `useCurrentFrame()`.
7. **Save at every approval.** `approve story "their words"`. Later steps depend on approved inputs, and you can return to any of them.
8. **Keep facts where they cannot go stale.** In our test a status note said $5.42 spent while the log added up to $11.31, and all 24 runs answered $11.31. Agents trust data over notes, so `STATUS.md` holds what is next and `status` computes the money.
9. **Keep the person's words.** `brief.md`, verbatim and dated, so a new session works from what they said and not from a summary.
10. **Measure before showing.** Run the checks in `varg-video-prompting`'s QA list: `ffprobe` for duration and frame rate, black and frozen frames, sync of each hit against `beats.json`, spelling of on-screen words.
11. **Separate maker and judge,** and read `llm-judge.md` before asking a model to rank anything. A different agent or a fresh session judges, without knowing who made it. Agents claimed success in 95.5% of edits that failed a test (Timeline-Bench). Anthropic's harness post found the split "a strong lever", though it too warns that an evaluator is "inclined to be generous".
12. **Compare by pairs.** "Which is better, A or B?" with authorship hidden. That is how Timeline-Bench collected its 2,582 editor judgments, and a panel of 3 LLM judges tracked the human ranking of agents closely (rho 0.93). It holds across agents, not for one edit: a single human judgment is itself noisy (alpha 0.10).

## Parallel agents

Evidence favours separate folders with a planner, in moderation. Worktrees scored a little higher than a shared workspace (59.1 vs 56.1 and 63.3 vs 55.5, in [CAID](https://arxiv.org/abs/2603.21489)) at about 2.5 to 3.7 times the iterations of a single agent, and cooperating peers with no planner scored about 30% lower than solo ([CooperBench](https://arxiv.org/abs/2601.13295)). Merge conflicts hit [19.8% with the same agent and 41.7% with different agents](https://arxiv.org/abs/2607.04697). So: one planner, 2-4 agents, separate shots for each. `try <name>` gives each its own folder and branch.

## What we could not confirm

- Nobody has published an independent test of seeds on Seedance, Kling, Veo or Flux. The table quotes vendors.
- Our byte-identical result is one composition on one Mac. Across machines, HyperFrames' own docs note local renders can differ by a pixel, because fonts and Chrome vary. If a film must match exactly anywhere, use `render --docker --strict`.
- Our layout test used one small project, so it says nothing about a 200-shot film. See `evidence.md`.

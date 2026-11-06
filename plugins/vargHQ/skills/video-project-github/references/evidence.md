# Evidence

What backs this skill, measured on 3-4 November 2026. Tools and raw results: `research/2026-11-03-github-for-video` in the private vargHQ/aeo repo.

## Our benchmark: putting a messy project on GitHub

**Setup.** One real-looking project: 443 MB, a 165 MB film, 19 media files, a `.env`, two keys pasted inside a script, `node_modules`. A cold agent gets the same plea from a non-technical person. Then a second session gets: "I made a new take and rewrote the script. Keep it safe, then bring back the old script." Scored by script, on a simulated GitHub that refuses files over 100 MB exactly as GitHub does. Conditions: no help, the pasted prompt, this skill.

| Codex, default model, 5 runs each | No help | Prompt | Skill |
|---|---|---|---|
| Private, no key leaked, restored byte for byte | 5 of 5 | 5 of 5 | 5 of 5 |
| Second session correct | 5 of 5 | 5 of 5 | 5 of 5 |
| Stored in the repo and LFS | 505 MB (LFS) | under 0.1 MB + Releases | 0.1 MB + Releases |
| Git words in the final reply (median) | 4 | 0 | 0 |
| Commands, tokens (median, both sessions) | 16, 514k | 16, 470k | 20, 506k |

| Codex, smaller model (gpt-6-luna), 3 runs each | No help | Prompt | Skill |
|---|---|---|---|
| Keys pushed to GitHub | **3 of 3** | 0 of 3 | 0 of 3 |
| Second session correct | 0 of 3 | 0 of 3 | **3 of 3** |
| Git words in the final reply (median) | 1 | 4 | 0 |

The default model does not need help for the first backup, and it picks LFS by itself. On this model the skill uses about the same tokens as no help (506k against 514k) and a few more commands. The smaller model pushed live-looking keys in every unaided run. With the prompt it kept the keys out, but it overwrote the rewrite without saving it, so that work was lost. Small samples: read these as direction, not as rates.

**A bug these runs caught.** An interim version pushed a key in 2 of 6 runs. The scanner did not know the shape `FAL_KEY="fal-..."`, and we had just told agents to "read only that line", so they trusted it. Earlier runs had caught the key by reading the whole script. We widened the scanner and now tell agents to check every script by hand. The tables above are the fixed version: 8 runs, no leaks.

**A careless later session.** With no agent involved, we then did what a later session might do on each finished project.

| Default and smaller model, 8 runs each | No help | Prompt | Skill |
|---|---|---|---|
| A key pasted in a script is stopped at commit | 0 | 0 | 8 |
| `.env.production` stays out | 7 | 8 | 8 |
| A 120 MB video stays out of git | 0 | 8 | 8 |
| `git push --force` over GitHub's versions is refused | 0 | 0 | 8 |
| The project tells the next agent the rules (`AGENTS.md`) | 0 | 8 | 8 |
| Media list with hashes | 0 | 8 | 8 |

With no help the 120 MB file went into git, and the simulated GitHub refused the push (GH001). On the default model, 5 unaided projects had 5 different sets of top-level files, with improvised names like `private-files.tar.enc` and `RECOVERY-KEY.txt`. 5 skill projects had 2 sets, and the only difference was one optional note.

Limits: Codex only for this test, in its OS sandbox with a `.git` file pointing to a writable folder, because that sandbox forbids writing inside `.git`. Claude with a shell is untested: our permission system stops an unattended agent with full shell access, rightly. The simulated GitHub is not GitHub; the next section is.

## Real GitHub: the same 218 MB, 8 files, one run each

| | Upload | Fresh copy, everything back | `.git` on disk | Note |
|---|---|---|---|---|
| Plain git | Refused after 89 s | | 211 MB | `File film.mp4 is 157.36 MB; this exceeds GitHub's file size limit of 100.00 MB` |
| Plain git, without the big file | 32 s | 2.6 s | 51 MB | History keeps every version forever |
| Git LFS | 158 s | 33 s | 215 MB | Files exist twice on disk. Uses free quota: 10 GiB stored, 10 GiB downloaded per month |
| This skill | 98 s | 27 s (1.7 s clone + 25 s restore) | 0.2 MB | No quota in GitHub's docs. Under 2 GiB per file |

One run on one connection, so read the size column first and the time columns loosely.

**Growth, on the simulated GitHub.** Ten re-renders of a 50 MB film: plain git's `.git` grew to 480 MB, and with this skill it stayed at 0.4 MB. With no network in the way, a `save` took about 2 s, and about 1.2 s with nothing new across 500 MB of media.

## Do folders and maps matter? 96 runs

One finished 12-shot project in four layouts. Tasks: find what made a take, change a cut, change a character everywhere, list unused takes. 3 repeats, Codex with a shell and Claude Sonnet with file tools only.

| Layout | Codex pass | Tokens | Claude pass | Tokens |
|---|---|---|---|---|
| Flat mess | 12 of 12 | 120k | 12 of 12 | 40k |
| By file type | 12 of 12 | 132k | 11 of 12 | 53k |
| Per step, with map in `AGENTS.md` | 12 of 12 | 136k | 12 of 12 | 42k |
| Per step, no map | 12 of 12 | 129k | 12 of 12 | 48k |

No gain from layout or from the map on a project this size. The layout is for people, and for new projects where no files exist to learn from.

A fifth task exposed a flaw in our fixture: the status note said $5.42 and the log added up to $11.31. So we scored it apart. All 24 runs answered $11.31, and 16 of 24 said the note was out of date or mentioned the disagreement (Codex 12 of 12, Claude 4 of 12).

## Repeat renders

HyperFrames 0.9.9, a 10 s composition with video, audio, image, GSAP and a web font. 3 renders plus 1 from a fresh clone in another folder: same SHA-256. Same Mac only. Across machines, its docs recommend `--docker`.

## What others measured

| Finding | Source |
|---|---|
| Context files: no significant pass-rate gain (LLM-written -0.5% and -2%, developer-written +2.4%, p=0.21), cost +19-23%, overviews did not speed navigation. 438 tasks | [Gloaguen et al.](https://arxiv.org/abs/2602.11988) |
| Stale instruction files were followed in 90.1% of choices. One sentence moved it to following the code in 91.4%. 320 runs | [Xu & Wu](https://arxiv.org/abs/2610.30571) |
| Curated skills lifted pass rates from 33.9% to 50.5%; skills an agent wrote for itself lost 8-11.5 points. What the best shared: scripts with tested defaults, exact formats. 87 tasks | [SkillsBench](https://arxiv.org/abs/2602.12670) |
| Editing agents: best 26.8% of tasks. They claimed full success on 95.5% of edits that failed a test. Editors preferred the reference edit in 83.5% of 2,582 judgments. 896 runs | [Timeline-Bench](https://arxiv.org/abs/2609.35143) |
| Merge conflicts: 19.8% same agent, 41.7% different agents | [Xu et al.](https://arxiv.org/abs/2607.04697) |
| Worktrees scored 59.1 and 63.3 against 56.1 and 55.5 for a shared workspace. Both cost about 2.5 to 3.7 times the iterations of one agent | [CAID](https://arxiv.org/abs/2603.21489) |
| Claude Code co-authored commits leaked secrets at 3.2% against a 1.5% baseline, near baseline by December. Pooled agents go the other way in [another study](https://arxiv.org/abs/2609.17598) | [GitGuardian](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026/), a vendor |

Of 91 public agent-video repos: 90% ignore media or renders, 5.5% use LFS, 4.4% object storage, none DVC or git-annex. Public repos only, classified by regex.

## Where people ask for this

- ["we just built git for video editing"](https://x.com/lucashjin/status/2036805674491875424): 16,660 likes. Git tracks metadata; the video stays out.
- ["I have been uploading all my photos and videos ... in Github private repositories for 6 years"](https://x.com/aShubhamz/status/2029133937134665742): 4,826 likes, half-joking, and the replies list the risks.
- ["How are y'all handling company-wide skills? ... less technical teams?"](https://x.com/cynthiamcgillis/status/2052068147017220362): a reply describes about 40 mostly non-technical people working from one repo through Claude.
- [raw inputs, a spec, an append-only log](https://x.com/francescoinweb3/status/2115074284787798396): the closest post to a folder standard for video.

We found no existing skill that teaches this to non-developers, and no video `.gitignore` in [github/gitignore](https://github.com/github/gitignore).

## Not verified

- Whether seeds reproduce clips on Seedance, Kling, Veo or Flux: vendor statements only.
- Whether Releases are treated differently for private repos. GitHub's page does not distinguish them, and our real test worked.
- How long `s3.varg.ai` keeps files. Do not treat those links as the only copy.
- Layout effects on large projects.

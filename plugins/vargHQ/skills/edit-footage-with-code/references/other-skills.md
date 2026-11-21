# Other skills worth installing, by job

From reading 199 repos on 2026-11-03. **Nothing here was installed or run**: these verdicts come from reading the code and rules, and no skill's output quality was measured. Read a repo before installing it. Stars as of that date; **n/m** = not measured.

Official engines first: HyperFrames (`claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes`) and Remotion (`npx skills add remotion-dev/skills`). Neither ships a footage workflow: HyperFrames retired `talking-head-recut` and `embedded-captions` on 2026-10-21 and Remotion's skills have no guidance on retakes, punch-ins or self-review. This skill exists to fill that gap.

## Whole footage workflow

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [nateherkai/herk-edit-kit](https://github.com/nateherkai/herk-edit-kit) | 2535 | MIT | HyperFrames reel kit with deterministic cuts and validators that are tested against bad input. Formerly hyperframes-student-kit |
| [browser-use/video-use](https://github.com/browser-use/video-use) | 30492 | MIT | The clearest mental model: text plus on-demand frames, 12 hard rules. Needs a paid ElevenLabs key |
| [veedstudio/open-edit](https://github.com/veedstudio/open-edit) | 1773 | Apache-2.0 | Speech probe per clip, edit list, retimed transcript, delivery review. Its own renderer |
| [conmeara/ripple](https://github.com/conmeara/ripple) | 0 | Apache-2.0 | The best gate design: real tests, an independent reviewer, an honest NOT VERIFIED status. No adoption signal yet: 0 stars |

## Silence and dead air

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [griffinwooldridge/talking-head-editor](https://github.com/griffinwooldridge/talking-head-editor) | 9 | MIT | Waveform cut logic that catches clipped tails. Small: 9 stars, so read the code |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | 5753 | Unlicense | One command, with timeline export. Pair it with a transcript pass for retakes |
| [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) | 4461 | MIT | 42 local tools; `check.py` exits 1 on failure. Demos use synthetic footage only |

## Retakes

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [hassancs91/claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor) | 363 | MIT | The best long-form knowledge, full of measured failures |
| [kurbaitaev/ghost-editor](https://github.com/kurbaitaev/ghost-editor) | 192 | MIT | Speech islands and a capped fix loop. Apple silicon only |
| [louisedesadeleer/cut-video](https://github.com/louisedesadeleer/cut-video) | 118 | MIT | The best explanation of why timestamps lie. Its README says no cloud while its SKILL.md uploads to Tella, so read that first |

## Captions

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [audrey-560/hyperframes-cinematic-caption](https://github.com/audrey-560/hyperframes-cinematic-caption) | 62 | MIT | Placing type around a person, keeping the underlying edit |

## Motion graphics on footage

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [Barty-Bart/motion-graphics](https://github.com/Barty-Bart/motion-graphics) | 1043 | MIT | Cutaways and panels on real talking heads, with a measured sound loop |

## Sound

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot) | 3773 | MIT | Closes the audio loop an agent cannot do by ear. Adds a soundtrack to a finished film |
| [onuryildriim/claude-kurgu-atolyesi](https://github.com/onuryildriim/claude-kurgu-atolyesi) | 19 | MIT | A null test proves the mix |

## Music sync

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 16579 | Apache-2.0 | The most rigorous beat grid and audio offset method. Builds promos rather than editing footage |

## Grade

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [isaacrowntree/color-grade-ai](https://github.com/isaacrowntree/color-grade-ai) | 33 | MIT | Apply and re-measure, with honest refusals. Grading is the thinnest area of all |

## Reframe

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [brookejlacey/boring-tools](https://github.com/brookejlacey/boring-tools) | 9 | MIT | Measured framing, offline, hashed models |
| [louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify) | 624 | MIT | Simple two-speaker reframe |

## Check your picture

| Repo | Stars | License | Use it for |
|---|---:|---|---|
| [Tejashmakwana/motionmaxxing](https://github.com/Tejashmakwana/motionmaxxing) | 1320 | Apache-2.0 | `look.py`: a numeric picture and audio gate that works on any render |

## Learn from it, but check the license

- `Vincentwei1021/video-talkcraft` has the best documented gate system we read, and it's under PolyForm Noncommercial. So do `SeeCut` and `DraftCut` (CC BY-NC) for the same reason. Take ideas only; do not ship their code in commercial work.
- `0xsline/OpenChatCut` is AGPL-3.0, which matters if you embed it.
- `antiboredom/videogrep`: a good idea, under a license that rules out commercial use.

## Claims on X that fail

- `agent-caption` is dead: GitHub and PyPI return 404, though lists still recommend it.
- A duplicated list post links `ffmpeg-skill`, `video-dubbing` and `app-demo-agent` to the wrong repos. Check where a link really goes.
- skills.sh install counts are unreliable: one skill showed 14 installs at the source and 944,748 on a copy.
- Star counts could not be fully checked, because stargazer lists were unavailable. `Jakeschincariol/youtube-agent-skill` and `Gitruck/cli` look suspicious on proxies, which proves nothing either way.

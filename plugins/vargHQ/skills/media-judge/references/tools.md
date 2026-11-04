# Other creators' tools

Read on GitHub on 2026-11-03 (star counts can move). Nothing here was installed or run by us; the accuracy and speed
figures are the repos' own. The research covered 150 repos and 4,078 X posts; full data is in vargHQ/aeo `research/2026-11-03-media-judge`.

## Use these with or instead of media-judge

| Tool | Stars | What it does better than this skill |
|---|---|---|
| [Tejashmakwana/motionmaxxing](https://github.com/Tejashmakwana/motionmaxxing) | 1,320 | `look.py` says "facts only, no scores": cuts, frozen, end hold, share of cuts within +-80 ms of a sound onset, gates.json |
| [dev-isaacmello/extreme-motion-design](https://github.com/dev-isaacmello/extreme-motion-design) | 74 | `design.py --video` for scale jump, empty share and default-frame signals. `reference.py`, with a calibrated reference score (self 100, no reference 38, unrelated 23-24) |
| [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot) | 3,770 | CPU listening: timeline with sync to cuts, scorecard against 7 pro launch films or your own references, MCP |
| [DSmereski/vidqa](https://github.com/DSmereski/vidqa) | 1 | Best agent interface: one small JSON per command, exit 0/1/2, golden diff |
| [0xpratzyy/dissect](https://github.com/0xpratzyy/dissect) | 36 | Reference check stated in frames: "Cut 2 lands 4 f late" |
| [Pranav-Conova/video-reverse-engineer](https://github.com/Pranav-Conova/video-reverse-engineer) | 1 | `editast analyze`: Edit AST, effects, on-beat per shot, and a benchmark built from generated edits |
| [qdrant-labs/qdrant-video-suite](https://github.com/qdrant-labs/qdrant-video-suite) | 1 | `review.py` with a selftest that plants faults, OCR typos and unsourced numbers |
| [kajisho5/qc-skill](https://github.com/kajisho5/qc-skill) | 3 | Typed JSON rules with an UNKNOWN verdict and no invented targets |
| [zenstory-ai/drama-skills](https://github.com/zenstory-ai/drama-skills) | 3,738 | The only short-drama review suite found: luma jump at cuts over 20/255, audio jumps over 10 dB |
| [Vincentwei1021/video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | 2,057 | `motion_check` catches shimmer on static text. `sfx_check --mix` grades cues as unmasked, audible or masked |
| [eternityspring/reelbench-skills](https://github.com/eternityspring/reelbench-skills) | 1,199 | Code owns cuts and motion, the model owns labels; 15 gates block "claims push but measured motion near 0" |
| [echris6/motion-video-kit](https://github.com/echris6/motion-video-kit) | 1,344 | The most-saved review prompt on X (2,834 saves): fresh critic, contact sheet every 0.2 s, dense frames at transitions, ranked problems, a ledger |
| [BenjaminRBerton/video-visual-clutter](https://github.com/BenjaminRBerton/video-visual-clutter) | 0 | Feature Congestion and Subband Entropy per frame, with a heat map. The only direct video clutter tool found |
| [madebysaira/AIVideoAdherenceGate](https://github.com/madebysaira/AIVideoAdherenceGate) | 1 | Standard library and ffmpeg only: static, jitter, morph spike, rough desync |
| [m4bwav/artwright](https://github.com/m4bwav/artwright) | 0 | Pairs in both orders, blind names, tie on a split, Bradley-Terry |
| [siewong007/vantage-pipeline](https://github.com/siewong007/vantage-pipeline) | 0 | Fits weights to human votes, and refuses them below 0.70 held-out accuracy |

## Reverse engineer a finished video

| Tool | Stars | What it gives an agent |
|---|---|---|
| [byjlw/video-analyzer](https://github.com/byjlw/video-analyzer) | 1,607 | Key frames, Whisper and a vision model, written up as a narrative |
| [blixvip/MotionClone](https://github.com/blixvip/MotionClone) | 581 | Rebuilds a reference as editable HyperFrames scenes, then compares the result |
| [UVA-Computer-Vision-Lab/OmniShotCut](https://github.com/UVA-Computer-Vision-Lab/OmniShotCut) | 344 | Shot boundaries plus transition type: jump, dissolve, fade, wipe |
| [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video) | 163 | Per shot: picture, text, edit, sound, how it was shot, live or AI, prompts per shot |
| [Melvynx/video-agent-skills](https://github.com/Melvynx/video-agent-skills) | 93 | `skills/steal` measures a reel into `style.json` and `STYLE.md`: seconds per shot, sheets, spectrogram beside cuts |
| [wangcanyu/daihuo-fanpai](https://github.com/wangcanyu/daihuo-fanpai) | 92 | Reverse engineers selling videos, regenerates, scores on a 90-point panel |
| [LoveRain1997/video-to-h3-prompt](https://github.com/LoveRain1997/video-to-h3-prompt) | 43 | Forensic prompt recovery: dense frames on unclear windows, film-type triage, spectral-flux onsets |
| [0xpratzyy/dissect](https://github.com/0xpratzyy/dissect) | 36 | Frame-level timeline: cuts, hidden cuts, camera moves as numbers, palette, text |
| [keng1304/video-breakdown](https://github.com/keng1304/video-breakdown) | 7 | Camera path from flow and homography, pose, shot size, colours, BPM |

## Challenge and review

| Tool | Stars | The idea worth taking |
|---|---|---|
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 16,560 | `final-review`: frame-numbered findings against brief, storyboard and references |
| [edenfunf/reelmimic](https://github.com/edenfunf/reelmimic) | 1,770 | Each finished shot goes to a new reviewer agent, and each fix needs before and after screenshots |
| [jordanrendric/claude-video-vision](https://github.com/jordanrendric/claude-video-vision) | 1,455 | MCP tools for scene changes, silence, freeze, blur, motion, exposure and loudness |
| [YeJe-cpu/SeeCut](https://github.com/YeJe-cpu/SeeCut) | 425 | `geom-check` is a hard gate on DOM geometry over time, including annotation-to-anchor distance. Guards against a judge that did not watch |
| [calesthio/generative-media-skills](https://github.com/calesthio/generative-media-skills) | 228 | Tags each QC decision as documented fact, empirical observation or production heuristic |
| [mrpaidsocial/mrpaidsocial-video-editor-agent](https://github.com/mrpaidsocial/mrpaidsocial-video-editor-agent) | 122 | Four layers of QA with written thresholds, and a 50 ms RMS lull scan. No license file |

## Rank

| Tool | Stars | The idea worth taking |
|---|---|---|
| [XBuilderLAB/cheat-on-content](https://github.com/XBuilderLAB/cheat-on-content) | 7,457 | Score, predict blind, publish, check at 3 days, then revise the rubric. Every judgment is logged against real numbers |
| [alex-durango/pingfusi](https://github.com/alex-durango/pingfusi) | 137 | An MCP that gives agents real human reviewers on published work |
| [Dachiko/RankMaster2](https://github.com/Dachiko/RankMaster2) | 0 | Human pairwise picks over a folder of photos or videos, TrueSkill rating in JSON |

## Building blocks

| Tool | Stars | For |
|---|---|---|
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | 66,424 | blackdetect, freezedetect, blockdetect, scdet, signalstats, ebur128 |
| [Netflix/vmaf](https://github.com/Netflix/vmaf) | 5,579 | CAMBI banding |
| [slhck/ffmpeg-quality-metrics](https://github.com/slhck/ffmpeg-quality-metrics) | 561 | CAMBI and VMAF as JSON from one command |
| [RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR) | 8,433 | On-screen text on CPU |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 5,344 | Cuts. Keep a uniform frame floor too, since one repo measured scene-detect recall near 50% on real footage |
| [yakhyo/uniface](https://github.com/yakhyo/uniface) | 2,191 | Face recognition, tracking, parsing and gaze on CPU. Check each weight's licence |
| [chaofengc/IQA-PyTorch](https://github.com/chaofengc/IQA-PyTorch) | 3,439 | LPIPS, MUSIQ, TOPIQ and more for images. No temporal handling |
| [LukasBommes/mv-extractor](https://github.com/LukasBommes/mv-extractor) | 408 | Codec motion vectors with no decode. Cheap motion for H.264 |
| [Halleck45/OpenPronounce](https://github.com/Halleck45/OpenPronounce) | 181 | Mispronounced words with IPA. Not checked on TTS |
| [jitsi/jiwer](https://github.com/jitsi/jiwer) | 942 | Script against transcript |
| [joonson/syncnet_python](https://github.com/joonson/syncnet_python) | 923 | Lip offset. Its score matched human ranking at only 0.34, so do not rank on it alone |

## Licence traps

InsightFace models are non-commercial research only, per its README, so this skill uses OpenCV's SFace. Demucs weights are CC-BY-NC, madmom's beat models are academic, Essentia is AGPL and OpenMontage is AGPL.

## What nobody has built

We found no pixel-level GitHub tool for pinned graphics, for labels sliding off their target, or for jiggling numbers. Nobody re-encodes
like X or YouTube and then scores dark scenes, though CAMBI exists. This skill's methods for those are our own, and no study has validated them.
Their thresholds were set on planted defects, so check them against your own footage.

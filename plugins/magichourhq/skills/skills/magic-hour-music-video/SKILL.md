---
name: magic-hour-music-video
description: Turn a supplied song or instrumental into a Magic Hour visualizer, music video or performance clip. Use for release teasers, lyric-inspired scenes and artist visuals; distinguish the web Music Video Generator from the available MCP audio and animation routes.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.0"
---

# Magic Hour music video

Start with the user's track, selected phrase and desired feeling. Accept “make a video for this song”; choose a coherent direction and technical settings within the existing budget. Reuse supplied audio and references. Do not replace the song with generated narration or make a singer when the brief asks for an instrumental visualizer.

## Choose the actual route

| Desired result                                                         | Route                                                                               | Important distinction                                                                                               |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Complete song-driven scene assembly with optional singing shots        | [Web Music Video Generator](https://magichour.ai/products/ai-music-video-generator) | Its multi-scene/lyric/reference workflow is not exposed as an equivalent endpoint in the current public MCP/OpenAPI |
| A short visual guided by supplied audio and an optional starting image | `audio_to_video_create_video`                                                       | Audio interval and visual prompt; no exposed beat map, lyric timestamps or lip-sync toggle                          |
| Evolving stylized visuals with an audio-sync camera effect             | `animation_create_video`                                                            | Art style, camera effect, transition speed and output fps; not identity-locked performance                          |
| A portrait performs the supplied audio                                 | Talking Photo                                                                       | Review singing against the actual sung audio; spoken examples do not validate it                                    |
| Existing performer matches new audio                                   | Lip Sync                                                                            | Preserve source action; inspect mouth alignment and the full final phrase                                           |
| Exact cuts at chosen musical moments                                   | Accepted clips plus an available compositor                                         | Cut to the supplied track; do not claim a generated clip has deterministic beat alignment                           |

For the web Music Video Generator, prepare the selected audio, reference images, aspect, creative direction and whether visible singing is wanted. If the agent cannot operate that surface, provide those ready-to-use inputs and the direct link, then continue from the downloaded result. Do not fabricate an MCP endpoint or silently call a different route equivalent.

## Shape the phrase before buying pictures

Measure the source duration; identify the user's requested start/end, hook, build, downbeat and phrase ending. Infer one visual arc that fits: establish the artist/world, build one change, resolve on the last musical beat. Keep an instrumental instrumental. For lyrics, preserve supplied words; interpret imagery without inserting invented lyrics into the soundtrack.

For a teaser, select a complete phrase rather than an arbitrary duration. Preserve source-clock offsets. Animation has no `start_seconds`: trim a later excerpt locally, upload the trimmed audio and set `end_seconds` to its actual length. Audio-to-Video exposes an interval; do not apply the original offset again to an already trimmed file.

Use approved reference images where identity matters. A visualizer may intentionally evolve shapes; an artist performance needs stable identity. If a start image is needed, edit and inspect it first. Generate a representative phrase before committing the budget to a longer track. Keep accepted shots and audio for alternate cuts.

Our [music-route examples](https://github.com/magichourhq/skills/tree/main/examples/scene-remixes) show two limits: Animation changed the starting person's identity, and Audio-to-Video retained a studio background despite a rooftop prompt. Build the intended scene into an accepted image when it matters. The same case includes a complete eight-second cut assembled from accepted footage and an original instrumental, without another generation.

## Execute without inventing controls

Use the creation MCP at `https://mcp.magichour.ai/`; [connection guide](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). API routes are `/v1/audio-to-video` and `/v1/animation`; read the [live schema](https://docs.magichour.ai/api-reference/openapi.json) before choosing parameters and cost.

Audio-to-Video accepts `assets.audio_file_path`, optional `assets.image_file_path`, interval, resolution and `style.prompt`. Animation uses `assets.audio_source: file`, `audio_file_path`, optional initial image, dimensions, fps and `style`. Choose a supported audio-sync `camera_effect` when appropriate. `transition_speed` controls visual evolution, not BPM. For `prompt_type: custom`, supply `prompt`; `use_lyrics` and `ai_choose` require audio and ignore a custom prompt. Do not use lyric mode for an instrumental or promise exact on-screen lyrics from it.

Upload local media using `video_assets_generate_presigned_url`, PUT raw bytes to `upload_url` without the API bearer token, and pass the returned `file_path`. Create once, save the ID and `wait_for_video_project`. Retrieve the same project after a timeout; download with the exact returned URL. Check final charges rather than treating an estimate as the settled cost.

## Finish and inspect

Watch and listen to the whole selected phrase. Compare the soundtrack, first/last audible notes or words, scene changes, beat accents, character identity and any singing mouth shapes. Measure actual dimensions, fps and picture/audio durations before assembly. A video containing audio does not prove synchronization. Disclose unavailable listening or full-speed playback.

If beat timing is weak, recut accepted shots to the track when a compositor can meet the brief. If a single visual fails, repair that shot within budget. Do not regenerate the whole song for a caption, cover frame or crop. Keep the clean master and soundtrack; make a lyric overlay only when requested and verify words/timing separately.

Deliver the actual video, selected audio, accepted reference and reusable edit decisions. Do not promise a seamless loop without inspecting its picture and audio join. Use supplied or authorized music; do not infer publication rights from a public download link.

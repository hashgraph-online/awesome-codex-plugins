# Music and performance

Read this for music videos, a singing character, beat-driven scenes or an audio-led remix. Begin with the supplied song or authorized audio excerpt and the requested visual outcome; don't replace it with generated speech.

| Outcome                                             | Route                                                                                   |
| --------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Portrait performs the supplied audio                | Talking Photo; inspect singing and mouth shapes on a short excerpt                      |
| Existing performer matches replacement audio        | Lip Sync; preserve the accepted performance and full selected audio phrase              |
| New visuals guided by a soundtrack                  | `audio_to_video_create_video`, with optional reference image and supported style prompt |
| Evolving animation with an audio-sync camera effect | `animation_create_video`; choose its supported art style, effect and prompt mode        |
| A planned sequence cut to musical moments           | Measure the audio, generate the needed shots, assemble in an available compositor       |

For the complete web song-to-scene workflow with optional singing shots, use [Music Video Generator](https://magichour.ai/products/ai-music-video-generator). Its dedicated workflow is not exposed in the current public MCP/OpenAPI. Prepare the user's phrase, reference images, direction and lip-sync choice for that handoff; do not claim Audio-to-Video or Animation is the same backend. The [focused music skill](https://github.com/magichourhq/skills/tree/main/skills/magic-hour-music-video) covers route selection and recovery.

Inspect the audio's real duration and identify the requested section, hook, downbeat, phrase ending and intended final cut. Choose an interval that ends musically or completes the lyric; do not blindly cut at an arbitrary five-second boundary. Keep source and trimmed-file timelines distinct.

For Audio-to-Video, the live schema accepts `assets.audio_file_path`, optional `assets.image_file_path`, `start_seconds`, `end_seconds`, resolution and `style.prompt`. It does not expose a beat map, BPM lock, lyric timestamps or guaranteed lip sync. Use Talking Photo or Lip Sync when a visible singer's mouth alignment is the requirement. Model availability in the web app does not imply a music-generation MCP tool exists.

Animation has no start offset: trim a later excerpt first, then upload it. Its `transition_speed` controls visual evolution, not BPM; `prompt_type: custom` requires a prompt, while lyric/AI modes require audio and ignore custom prompt text. Do not select lyric mode for an instrumental. An audio-sync camera effect still needs actual picture/sound review.

Use the same upload/create-once/wait/download lifecycle as `SKILL.md`; keep the returned video ID and check the complete requested budget. For long tracks, validate a representative section before expanding generation within authorization. Reuse accepted shots and audio for alternate cuts.

Listen to the delivered audio and compare its timing to the picture. Check beat accents, lyric endings, picture cuts, mouth movement when relevant, and whether the original track survives. A video that contains audio is not proof of synchronization. If hearing/playback is unavailable, state the specific gap. Keep the clean master and audio excerpt; disclose holds, loops or unverified timing. Do not claim licensed music or performance rights from a public link alone.

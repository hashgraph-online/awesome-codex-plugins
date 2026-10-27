# Finish a clip that is too short or too small

Inspect the actual source duration, dimensions, frame rate and sound. Determine whether the user needs new motion, more pixels, a different crop or simply room for a caption. These are different jobs; a loop, held frame or resize does not satisfy every one of them.

## Extend the action

Check the current creation tools and public OpenAPI for a supported video-extension endpoint. As checked September 11, 2026, it is absent. The [web Video Extender](https://magichour.ai/products/ai-video-extender) is available; do not invent `/v1/extend` or label a last-frame Image-to-Video continuation equivalent to context-aware video extension.

Prepare the original clip, intended extra duration, final action and any accepted soundtrack for the web handoff. Choose a source ending with readable subject position and movement. When browser operation is unavailable or unauthorized, give the ready source and direct product link instead of pretending to submit it. Continue editing when the actual result is available.

Inspect the join for jumps in pose, position, lighting, motion direction and sound. Determine whether the returned file is a continuation segment or already includes the original before concatenating; do not duplicate the source. A generated visual extension cannot recover missing original speech. Preserve a complete supplied recording or explain that a new recording is needed.

If the user only needs space for copy, an explicitly disclosed hold/end card may be appropriate without a paid generation. Keep a clean master. Never claim that a hold, loop, slowed clip or crossfade is newly generated motion.

## Improve final delivery size

The hosted MCP exposes `ai_video_upscaler_create_video`, backed by `POST /v1/ai-video-upscaler` in the [MCP's synced OpenAPI](https://github.com/magichourhq/magic-hour-mcp/blob/main/docs/openapi.json), as checked October 25, 2026 UTC. Discovery verifies the available contract, not a successful upscale or output-quality benchmark. Recheck the connected schema before calling; the documentation index and installed clients can lag behind it.

Prepare the accepted final cut and requested target size; avoid upscaling a take that still needs creative repairs. The discovered request requires `assets.video_file_path`, `end_seconds` and `resolution`; `start_seconds` defaults to zero. Resolution accepts `720p`, `1080p`, `2k` or `4k` and requires a paid plan. `720p`/`1080p` set the short side; `2k`/`4k` set the long side while preserving aspect ratio. Upload source bytes through the shared upload-URL flow when needed and pass its durable `file_path`.

Check account eligibility and the existing spending limit before creating the job. Save the returned `id` and `credits_charged`, then use `wait_for_video_project` or `GET /v1/video-projects/{id}`. Preserve that accepted ID across interruptions; recover by retrieving it rather than creating another upscale. On completion, download from the exact returned URL and inspect the result. If the connected client cannot expose or call this route, use the authenticated API when authorized, or prepare the [web Video Upscaler](https://magichour.ai/products/video-upscaler) handoff.

Compare face texture, eyes, fine edges, lettering, noise and motion at matched display sizes. Check that audio, cadence and duration survive. Larger dimensions alone do not prove recovered detail, and enhancement can invent texture or amplify flicker. Inspect the whole result before discarding the original.

For a simple export resize, use an available compositor and label it as resizing. Never present FFmpeg scaling as AI video enhancement. Do not upscale extracted frames independently and promise temporally consistent video, or stretch a clip to reach the requested canvas.

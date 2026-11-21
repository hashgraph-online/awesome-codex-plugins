---
name: treza-video-pipelines
description: Make AI videos with the Treza MCP server. Use when the user asks for a video or a clip from a description, a captioned Short, a clip cut from a podcast or long video, edits to media they already have (captions, music, narration, trims, joining clips), a channel that posts to YouTube or TikTok on a schedule, or what a render costs.
---

# Treza video

Treza makes AI video over MCP. You get 26 tools, from one call that makes a clip to full pipelines that render and post on a schedule. Two more, `open_library` and `confirm_publish`, belong to Treza's panels and never run from the model.

## Pick the shortest path

1. **One clip from a description: `make_video`.** It picks a video model (Veo 3.1 Lite unless the user names one), prepares the render and answers with the price, whether the balance covers it, and a `quoteId`. It does not start anything. Tell the user what it will make and what it costs, and once they accept, call `run_pipeline` with the returned `pipelineId` and `quoteId` and no inputs. Use 9:16 for Shorts, Reels and TikTok. To continue a video they already have ("make it longer", "what happens next"), pass its url as `continueFromVideoUrl`, so the new clip opens on its last frame.
2. **A file they already have: finish it.** `import_media` adds a public link, an attachment, or a local file sent through `create_upload_url`. `list_assets` finds what is in the library. `edit_asset` runs one operation over one file (captions, upscale, trim, crop, overlay, background removal). `assemble_video` joins clips in order over narration and a music bed (`musicPrompt` composes one), with captions if wanted.
3. **More than one clip, or something that repeats: a pipeline.** Start from `list_pipeline_templates`, then `create_pipeline` with `templateId` (captioned Shorts, podcast clipping, dubbing and more). Otherwise `list_node_types` and `get_node_type` describe every node, and `get_node_type` on video-gen, image-gen, tts and ai-model returns the live model catalog with durations, aspect ratios and voices. Pick ids from that list, never guess.

## Money

- Renders spend the account's prepaid credits. For a pipeline you built or changed, call `estimate_run_cost`, tell the user the price, and pass its `quoteId` to `run_pipeline`: the run starts once, at that price. Without a quote, pass a `requestId` of your own so a retry never charges twice.
- When the balance does not cover it, say so and pass on the link `get_credit_balance` returns. An agent holding a wallet can pay the x402 block when the response carries one.
- `assemble_video` and `edit_asset` spend credits too. Tell the user before calling them.

## Runs

- `run_pipeline`, `assemble_video` and `edit_asset` return at once. Poll `get_run` until the status leaves `running`; it ends as `success`, `partial`, `error` or `cancelled`. Renders take minutes, and `get_run` says which step it is on and how long to wait before asking again.
- `cancel_run` stops a render the user no longer wants. Steps that already finished keep their output and are not refunded.
- Every run renders every node again. To add music, narration or captions to a video a run already made, pass its url from `get_run` to `assemble_video` or `edit_asset` instead of running the pipeline again.

## Channels and posting

- `list_connected_channels` returns the ids a youtube-upload or tiktok-upload node needs. When the channel the user wants is missing, call `connect_channel` and give them its link. They finish it in their own browser, and the page says when it is connected.
- Schedules fire from the published snapshot: a schedule trigger on the draft does nothing until `publish_pipeline`. `set_schedule_paused` pauses or resumes without republishing.
- `publish_asset` lays one finished video out for the user to post, and only when they asked. It posts when they press Post in a Treza panel. A client without panels, such as a terminal or an editor, posts through a pipeline that ends in a youtube-upload or tiktok-upload node instead.

## Rules

- Never start a render without telling the user its price, never arm a schedule they did not ask for, and never post anything they did not ask to post.
- Only pass media urls that came from `list_assets`, `import_media` or a run's outputs in `get_run`, copied exactly.
- Everything you make shows up in the user's Treza account at https://www.trezalabs.com, so name pipelines clearly. `get_profile` says which account is connected.
- If a tool returns 401, the user needs to connect the server and sign in, not paste a key.

---
name: vidseeds-analytics
description: Use for VidSeeds MCP analytics and research — YouTube analytics, channel intelligence, video autopsy, outliers, competitors, trending/breakout discovery, keyword research, comment sentiment, and best-practices tools. Outcomes only; not internal scoring details.
---

# Analytics & intelligence (MCP)

Map the user's question to a tool — then read the tool `description` for inputs and seed cost.

## YouTube account data

| Goal                    | Tool                                                                           |
| ----------------------- | ------------------------------------------------------------------------------ |
| Connected channels      | `vidseeds_get_youtube_channels`                                                |
| Channel/video analytics | `vidseeds_get_youtube_analytics`                                               |
| Playlists               | `vidseeds_get_channel_playlists`                                               |
| Transcript / captions   | `vidseeds_get_youtube_video_transcript`, `vidseeds_get_youtube_video_captions` |

## Channel intelligence (deep profile)

| Goal               | Tool                                       |
| ------------------ | ------------------------------------------ |
| Run analysis       | `vidseeds_analyze_channel_intelligence`    |
| Poll status        | `vidseeds_get_channel_intelligence_status` |
| Read cached result | `vidseeds_get_channel_intelligence_cache`  |
| Narrative insights | `vidseeds_generate_channel_insights`       |
| Author voice       | `vidseeds_analyze_author_voice`            |

Pass `channelId` when multiple YouTube connections exist.

## Single-video diagnosis

| Goal                        | Tool                                 |
| --------------------------- | ------------------------------------ |
| Deep dive on one video      | `vidseeds_analyze_video_autopsy`     |
| Best-practices check        | `vidseeds_get_video_best_practices`  |
| Sponsor integrations        | `vidseeds_scan_sponsor_integrations` |
| Retention curve (simulated) | `vidseeds_simulate_retention_curve`  |

## Competitive & market context

| Goal                 | Tool                              |
| -------------------- | --------------------------------- |
| Compare channels     | `vidseeds_compare_competitors`    |
| Outlier videos       | `vidseeds_detect_outliers`        |
| Public channel audit | `vidseeds_audit_public_channel`   |
| Realtime anomalies   | `vidseeds_get_realtime_anomalies` |

## Discovery & research

| Goal                 | Tool                                                                      |
| -------------------- | ------------------------------------------------------------------------- |
| Keywords             | `vidseeds_keyword_research`                                               |
| Trending videos      | `vidseeds_get_trending_videos`                                            |
| Breakout channels    | `vidseeds_get_breakout_channels`                                          |
| Bulk video metadata  | `vidseeds_get_bulk_video_metadata`                                        |
| Bulk channel lookup  | `vidseeds_get_channels_by_ids`                                            |
| Channel video list   | `vidseeds_list_channel_videos`                                            |
| Video stats history  | `vidseeds_get_video_stats_history`                                        |
| View curve           | `vidseeds_get_channel_view_accumulation_curve`                            |
| Video comments       | `vidseeds_get_video_comments`                                             |
| Analytics dimensions | `vidseeds_get_available_analytics_dimensions`                             |
| Comment sentiment    | `vidseeds_get_comment_sentiment`                                          |
| Video ideas          | `vidseeds_generate_video_ideas` (and related ideas tools in `tools/list`) |

## SEO experiments

- `vidseeds_generate_seo_title_experiments` — title variants for testing.

## Copilot / assistant (Q&A)

- `vidseeds_get_copilot_response` — channel-aware answers.
- Assistant threads: `vidseeds_list_assistant_conversations`, `vidseeds_get_assistant_conversation`, `vidseeds_send_assistant_message`, `vidseeds_confirm_assistant_suggestion` — see tool descriptions for collab flows.

## After research → action

Typical handoff:

1. Intelligence or autopsy → refine metadata via `vidseeds-projects`.
2. Trends/keywords → thumbnail brief via `vidseeds-thumbnails`.
3. Public audit → user decides positioning; no automatic publish.

Always run `vidseeds_get_seed_balance` before batch intelligence calls.

# Example report: solar security light dropshipping reel

Ad: https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_d45406f8d0db.mp4 (58 s, 9:16, all AI)
Runs on: Instagram Reels and TikTok (organic, affiliate links in a DM guide) · Market: US · Category: business opportunity / home security
Made with: Seedance 2.5 (hook, security-cam style), Kling 4 (laptop shots), ElevenLabs voice. No real people.
Checked: 2026-10-28 against `rules.json` (last_checked 2026-10-28). Analysis: varg `video_analyze`, 5 credits.

**Verdict: fix first.** Nothing blocks the reel, but four fixes are needed before it runs.

| # | Level | Time | Finding | Rule | Fix |
|---|---|---|---|---|---|
| 1 | FIX | 0:00–0:04 | Night "CAM 04 … REC" security-camera footage of an intruder, presented as "Backyard camera caught this". It is AI-generated, so viewers may read it as a real event. | `staged-real-footage`, `tt-cg-label` (TikTok, 2025-09-13) | Turn on the AI label on TikTok and Instagram. Optionally add "AI dramatization" in small text for the first 2 s. |
| 2 | FIX | 0:15–0:23 | "the profit is decent and the demand is exceptionally high", "profit from it without even touching the product", "$24.99 profit / order" on screen | `ftc-earnings` (FTC) | Say "example margin before ad costs and returns"; drop "exceptionally high" unless you can show the demand data; add "results vary" to the caption. |
| 3 | FIX | whole reel | Promotes ProductRadar and varg.ai with a "comment GUIDE" funnel to affiliate links, with no disclosure | `ftc-endorsement` (2023-06-29) | Add "#ad" or the platform's paid-partnership tag in the video and caption if you earn from the links. |
| 4 | FIX | 0:43–0:52 | "ships the product out automatically, and you pay for it after the customer has already paid you" | `ftc-earnings` | Keep it, but don't promise zero risk: chargebacks, returns and shipping delays still land on the seller. |
| 5 | WARN | 0:52–0:58 | Night skyline of Dubai Marina | `landmark-ip` | Fine for organic posts. For paid ads, keep Burj Khalifa out of focus (it isn't in frame here). |
| 6 | PASS | 0:04–0:07 | The product (solar flood light) does what is shown: motion-triggered light | `tts-ai-effect` | — |
| 7 | PASS | — | No AI person speaks about using the product; the narrator is a voice-over | `ftc-fake-reviews` | — |

Labels to set: TikTok AI-generated label on; Instagram "AI info" (auto from metadata, keep C2PA); add #ad if affiliate. New York: no synthetic performer on screen, so no extra disclosure is needed.

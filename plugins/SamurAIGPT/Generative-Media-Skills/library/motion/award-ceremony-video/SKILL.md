---
slug: muapi-award-ceremony-video
name: muapi-award-ceremony-video
version: "1.0.0"
description: Generate a 15-second cinematic awards-ceremony video — a host announces a winner from the stage, a spotlight finds them in the crowd, they walk up to the podium, receive the award, and the LED display reveals their name and "THE BEST ACTOR".
acceptLicenseTerms: true
---


# Award Ceremony Video

**Generate a 15-second cinematic awards-ceremony video — a host announces a winner from the stage, a spotlight finds them in the crowd, they walk up to the podium, receive the award, and the LED display reveals their name and "THE BEST ACTOR".**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `winner_image` | image_url | yes | — | A clear photo of the winner. Becomes `@image_1` — their identity is strict-locked across the video. |
| `host_image` | image_url | yes | — | A clear photo of the host. Becomes `@image_2` — sole presenter on stage at the podium. |
| `winner_name` | text | no | Olivia | The name announced by the host and shown on the LED stage display under "THE BEST ACTOR". |


## Steps

### Phase A — Confirm Inputs

If either `{{winner_image}}` or `{{host_image}}` is missing, ask the user to upload them. Confirm `{{winner_name}}` before generation — it appears spoken in the audio and rendered on the LED display.

### Phase B — Generate the Ceremony Video

Submit the plan with ONE step using the Seedance 2.0 image-to-video fast variant (multi-reference). Pass the images in this exact order — order maps to `@image_1` then `@image_2`:

1. **Award Ceremony Video** — `muapi video from-image` (model=`seedance-2-image-to-video-fast`, or fall back to raw endpoint `bytedance-seedance-2-0-reference-to-video-fast`):
   - Reference images (in order): `{{winner_image}}`, `{{host_image}}`
   - Aspect ratio: `16:9`
   - Duration: `15`
   - Resolution: `720p`
   - Generate audio: `true`
   - Prompt:
     ```
     **Style:** Ultra-realistic live awards ceremony scene. Multi-camera broadcast style — switches between polished TV broadcast angles and intimate handheld documentary coverage. Cinematic prestige feel — think Grammy Awards or Academy Awards production quality. Natural human reactions, no over-acting.

     **Audio:** Natural ceremony sound — elegant orchestral background music, host microphone voice projecting through venue speakers, crowd murmur, then erupting applause and cheers, chair movement, footsteps on stage, trophy/plaque handling sound, emotional crowd reaction.

     **Lighting:** Grand indoor awards venue. Dramatic stage lighting — warm golden spotlights on stage, cooler ambient lighting over audience seating. Broadcast camera lights. LED stage displays casting colored light. When winner is announced — a warm spotlight sweeps and locks onto the winner in the audience.

     **Setting:** Massive prestigious awards venue — Grammy or Academy Awards scale. Grand stage with towering LED displays, elegant podium, live orchestra pit. Thousands of formally dressed audience members seated in rows. Press cameras lining the aisles. Large overhead screens showing live broadcast feed. The venue radiates prestige and scale.

     **Main Character STRICT LOCK:**

     **@image_1 — THE WINNER "{{winner_name}}":** Use @image_1 as strict identity. The person dressed in formal awards show attire for the award ceremony. No sunglasses. No modifications to face or build. Seated in the audience among other formally dressed attendees.

     **@image_2 — THE HOST:** Use @image_2 as strict identity as the sole host on stage at the podium. Maintain exact face, build, and features. Dressed in formal awards show attire. No modifications to face or build allowed.

     **SCENE TIMELINE — 15 SECONDS**

     **0–3s — THE ANNOUNCEMENT:**
     **Broadcast close-up** directly on @image_2's face — tight, cinematic, high production quality. @image_2 stands at the podium microphone under a warm golden spotlight. Expression is composed, charismatic, building suspense deliberately. The person holds the envelope or card, glances down at it one final time, then looks straight into camera. A beat of silence. The person leans into the microphone and says slowly: *"And the winner is..."* Camera holds tight on @image_2's face — lips, expression, the tension of the moment. Crowd murmur audible in background.

     **3–6s — THE WINNER:**
     Hard **broadcast cut** to audience — low-angle TV camera shot pushing through seated rows. Camera finds @image_1 seated among other guests, relaxed, not expecting it. @image_2's voice continues booming through the venue speakers: *"...{{winner_name}}"* Spotlight snaps onto @image_1 from above. The person's expression shifts — genuine shock, eyes wide, mouth slightly open, then breaks into a real overwhelmed smile. The person looks left and right at the people beside in disbelief. The crowd erupts into applause and cheers. People around the person stand, clapping, patting their shoulders.

     **6–9s — RISING AND WALKING:**
     @image_1 straightens up, composes themselves, stands from their seat. **Handheld documentary camera** picks the person up immediately — tracking from the aisle as the person moves forward toward the stage. Camera moves with the person — slightly shaky, intimate, real. Applause continues thundering through the venue. Overhead broadcast screens cut to the person's face live. The person walks with composure — attire clean, posture upright, expression warm and slightly emotional.

     **9–12s — REACHING THE STAGE:**
     Handheld camera follows @image_1 up the stage steps. Bright stage spotlights hit the person fully as they ascend. @image_2 steps forward from the podium smiling warmly, holding the award plaque with both hands. @image_1 reaches the podium. @image_2 presents the plaque — @image_1 receives it with both hands, looks down at it for a brief genuine moment. The two share a natural smile and brief handshake. Behind them on the massive **LED stage display**: a large portrait of @image_1's face, the person's name in bold elegant typography — **"{{winner_name}}"** — and beneath it: **"THE BEST ACTOR."** The display glows and pulses with celebratory graphics.

     **12–15s — THE MOMENT:**
     Camera settles into a **wide broadcast shot** of the full stage — @image_1 standing at the podium, award plaque in hand, @image_2 standing beside the person, LED wall blazing behind them both with @image_1's name and face. Spotlights lock on @image_1. Applause fills the entire venue — standing ovation building across the audience. @image_1 raises the plaque slightly, looks out at the crowd, smile composed and genuine. @image_2 leads the applause from the stage beside the person. Final frame holds — the full stage, the glowing LED display, the roaring crowd, and @image_1 standing at the center of it all. No fade to black.
     ```

After generation, present the final 15-second award-ceremony video.

## Trigger Keywords

`award ceremony`, `awards show video`, `oscars video`, `grammy ceremony`, `best actor award`, `winner announcement video`, `red carpet award`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- **Image order is load-bearing.** The Winner must be the first image (resolves to `@image_1`) and the Host must be the second (`@image_2`). Reversing them swaps who announces and who walks up.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call. The winner's name appears both in the spoken audio cue and on the LED display, so spell-check it before generation.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` (passing `image_urls`, `aspect_ratio`, `duration`, `resolution`, `generate_audio`, `prompt`) and poll with `muapi predict wait <request_id>`.

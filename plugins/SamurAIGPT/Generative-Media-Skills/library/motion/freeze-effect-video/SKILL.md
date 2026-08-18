---
slug: muapi-freeze-effect-video
name: muapi-freeze-effect-video
version: "1.0.0"
description: Generate a cinematic "freeze effect" video where time stops mid-scene, the subject walks through the frozen world, then time resumes with a snap.
acceptLicenseTerms: true
---


# Freeze Effect Video

**Generate a cinematic "freeze effect" video where time stops mid-scene, the subject walks through the frozen world, then time resumes with a snap.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `photo` | image_url | yes | — | Reference photo of the main character (face/body) whose appearance must remain consistent across all shots. |
| `scene` | text | no | a packed, dimly lit sports bar with neon accents, blurred TVs showing a championship celebration | The setting where time will freeze (e.g. "a busy nightclub", "a wedding reception", "a stadium crowd"). |
| `freeze_moment` | text | no | golden arcs of beer suspended midair, popcorn floating motionless, people frozen mid-cheer | The signature frozen visual — what hangs in the air when time stops. |
| `closing_line` | text | no | perfect | A short word/phrase the character whispers before resuming time. |
| `aspect_ratio` | text | no | 16:9 | Output aspect ratio — "16:9" for cinematic, "9:16" for vertical/social. |
| `duration` | text | no | 15 | Target duration in seconds (10 or 15 recommended). |


## Steps

### Phase A — Generate the Freeze Effect Video

Submit the plan with ONE step:

1. **Freeze effect video** — `muapi video from-image` (model=`seedance-v2.0-i2v`, quality=`high`, generate_audio=`true`):
   - Reference image: `{{photo}}`
   - Aspect ratio: `{{aspect_ratio}}`
   - Duration: `{{duration}}`
   - Resolution: `720p`
   - Prompt:
     ```
     Ultra-realistic, shot on Arri Alexa Mini, 35mm lens, {{scene}}, volumetric haze, dynamic hard shadows, shallow depth of field.

     Main Character:
     The person from @image1. Facial features and body proportions remain consistent across all shots.

     [0:00–0:03]
     {{scene}}. Time flows normally.
     Steadicam frontal medium shot tracking the person walking confidently through the crowd.
     The crowd erupts in euphoria around them.
     As the person walks, they raise their right hand and snap.

     [0:03–0:06]
     At the snap, a subtle spherical shockwave bursts from their fingertips — air distortion and light refraction ripple outward.
     Everything freezes mid-motion.
     {{freeze_moment}}.
     Neon light catches dust and liquid in the air.
     Absolute silence.

     [0:06–0:09]
     Only the person moves.
     Soft, echoing footsteps.
     Camera tracks backward as they walk through the frozen scene, observing calmly.
     They reach out and pluck a single suspended detail from the air.

     [0:09–0:11]
     They stop in front of a frozen onlooker, face locked in an ecstatic expression.
     The person tilts their head, gently observes.
     Softly: "{{closing_line}}".

     [0:11–0:15]
     They turn, face the camera, smirk, and snap again.
     A stronger reverse shockwave ripples outward.
     Motion instantly resumes — sounds explode back, people land mid-jump.
     The person walks away as the camera pushes through the celebrating crowd.

     Fade to black.

     Sound Design:
     Deafening ambient celebration → snap → deep shockwave/bass drop → absolute silence → footsteps → soft whisper → snap → reverse shockwave → deafening celebration returns.
     ```

After generation, present the video to the user.

## Notes
- The character's identity is anchored by `@image1` — the reference photo must clearly show the main subject's face.
- For best results, choose a `scene` with crowd energy and lots of small objects (liquid, confetti, sparks) that can plausibly "freeze" in midair.
- If the model rejects realistic human likeness, switch to the Global tier model (`seedance-2-image-to-video-fast`) which allows looser identity matching.
- For vertical/social delivery, set `aspect_ratio=9:16` and keep `duration=10` for tighter pacing.
- Always keep `generate_audio=true` — the snap → silence → snap audio arc is the signature of this effect and should not be muted.

## Trigger Keywords

`freeze effect`, `time freeze video`, `time stop video`, `snap freeze`, `frozen world`, `bullet time crowd`, `time stand still`, `pause time effect`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.

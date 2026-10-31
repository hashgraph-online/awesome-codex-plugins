# Test run on varg (2026-10-30)

Our own scene, made to check the method and the varg call. Not from the source video.

## Key frames (gpt_image_2_5, 16:9, 1088×608, 22–23 credits each)

1. Text only:
```
Cinematic 16:9 film still, low angle from the ground, ultra-wide fisheye lens with heavy barrel
distortion bending the stairs and tram rails. Scene: a young woman skateboarder (red knit beanie,
short black bob, oversized olive bomber jacket, loose grey cargo pants, white sneakers, black
skateboard with worn grip tape) pushes hard down a steep cobblestone street in Lisbon, a yellow
tram blurred in the background, laundry hanging between pastel buildings. Her body leans forward
mid-push, one foot on the board, jacket flapping, motion blur on the cobbles and the background.
Overcast daylight. 16mm film look: milky highlights, teal shadows, deep blacks, coarse grain,
slight chromatic aberration at the edges. Avoid text overlays, logos, clean digital look,
slow-motion feel, extra people in the foreground.
```
https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_4ecf2ada39e2.png

2. Frame 1 as reference: "Use the reference image: the woman skateboarder is the person to match exactly (…); the reference is also the guide for the street, color grade, 16mm film tone and grain. New shot: side-on medium-wide angle from across the street, she is mid-air in a high ollie over the tram rails… Avoid text overlays, clean digital look, extra skateboards, warped board or wheels."
https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_0ce66417bf72.png

3. Frame 1 as reference: "…New shot: the end of the run at the bottom of the hill by a small tiled viewpoint over the river. She has just stopped, foot on the tail so the board pops up into her hand, slightly out of breath, grinning straight into the lens…"
https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_6ccafb88fd96.png

All three kept the face, beanie, jacket and grade.

## Take 1: three shots in one generation (failed)

```json
{
  "model": "fal:fal-ai/kling-video/v4/reference-to-video",
  "files": [{"url": "<frame 1>"}, {"url": "<frame 2>"}, {"url": "<frame 3>"}],
  "aspect_ratio": "16:9", "resolution": "720p", "duration": 15, "audio": true,
  "provider_options": {"fal": {"multi_prompt": [
    {"prompt": "@Image1 sets the look: shaky handheld 16mm street footage, heavy grain, low fisheye angle, overcast Lisbon. Shot 1: the skateboarder from @Image1 pushes hard down the steep cobblestone hill toward the camera, the camera runs backwards in front of her, the yellow tram rattles behind. Real speed, no slow motion, motion blur on the cobbles.", "duration": 5},
    {"prompt": "Shot 2: hard cut to the side angle of @Image2: she pops a high ollie over the tram rails as the yellow tram passes behind her, lands clean and rolls on. Real speed, no slow motion. Sound: wheels roaring on cobbles, the tram bell.", "duration": 5},
    {"prompt": "Shot 3: hard cut to @Image3 at the tiled viewpoint: she stops, kicks the tail so the board pops into her hand, catches her breath and grins into the lens and says \"Again?\" Handheld, the river soft behind her.", "duration": 5}
  ]}}
}
```

Result: https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_9483ac202e90.mp4 (1280×720, 24 fps, 15.04 s, ~4 min).

- Three shots, in order, cut where the `multi_prompt` durations say. Same face, outfit, fisheye and grade in all three; the tram passes in shot 2.
- She says "Again?" at 13–15 s with a breath before it (Whisper heard "[Sigh] Again?").
- Weak spots: the ollie hangs in the air for about two seconds (floaty, close to slow motion even with "no slow motion"); in shot 3 the board vanishes from her hand; the sound is generic street noise, not clear wheel roar. Fixes: give the peak and the landing as two stills, add a real reference clip of an ollie as `@Video1`, and keep props in hand visible in the last still.
- First viewer's verdict (the founder, watching the raw take): "a meme". The head twitches in the first second, and the hard cut from the street to the viewpoint at 10.1 s reads as a broken splice. That cut is Kling's own, from shot 3's "hard cut to @Image3" in the same generation; nothing was stitched (scene detection finds one hard cut, at 10.125 s; the shot 1 → 2 change at 5 s came out as a continuous move). Lessons: one place per take, the location change as a separate take cut in the edit, trim the first second, and never show a raw take as the result.
- Plain `kling_v4` with the same three files would have run image-to-video (`estimate_cost` resolved `fal:fal-ai/kling-video/v4/image-to-video`), using only the first two images as start and end frames. Fixed in api#239: three or more images now go to reference-to-video, and `estimate_cost` prices route keys (live once that is deployed).

## Take 2: one continuous shot (the example)

The same scene redone after take 1: one still, one place, one action, no `multi_prompt`. Plain `kling_v4` with one image runs image-to-video, so the still is the exact first frame.

```json
{
  "model": "kling_v4",
  "files": [{"url": "<frame 1>"}],
  "duration": 8, "resolution": "720p", "audio": true,
  "prompt": "One continuous shot, no cuts. Low fisheye camera runs backwards in front of the skateboarder from the start frame as she pushes hard down the steep cobblestone hill toward the lens. She crouches and pops a quick, snappy ollie over the tram rails, lands in under a second with a hard clack and keeps rolling at the camera, then grins into the lens and says \"Again?\" Real speed, no slow motion, motion blur on the cobbles, the yellow tram rattling behind her. Shaky handheld 16mm street footage, heavy grain. Sound: wheels roaring on cobbles, the clack of the landing, a distant tram bell."
}
```

Result: https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_0665c41e46ff.mp4 (1280×716, 8.04 s, ~5 min, 126 credits = $1.26; job_5c577096a71d).

- One continuous shot: scene detection finds no cut. No camera fly-through, no change of place.
- The ollie runs at real speed: take-off at ~4.3 s, landing at ~4.8 s, about half a second in the air (take 1 hung for two seconds). She lands, rolls at the lens and ends in a close-up.
- She says "Again?" (Whisper hears exactly that) with a grin into the lens. Face, beanie, jacket, fisheye and the Lisbon street match the still.
- What changed from take 1: one start frame instead of three references; one place and one action instead of three shots with a location change; "One continuous shot, no cuts" and "lands in under a second" in the prompt; 8 s instead of 15 s.

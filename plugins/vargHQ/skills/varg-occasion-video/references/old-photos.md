# Old photos, anniversaries and tributes

The biggest occasion post on X this year was a son bringing his mother's old photos to life for her 60th birthday,
filmed with her reaction: 1.50M views, 31.9k likes, 8.6k bookmarks (Apr 2026, covered by Philstar). A wedding
surprise that recast a couple across film eras and ended where they really met reached 910k views and 4.9k
bookmarks (Jul 2026). Both show real families, which is exactly why they work: make them for your own people, with
their agreement.

## Restore first, then move gently

1. **Scan flat** (or photograph the print square-on in daylight), one file per photo, untouched originals kept.
2. **Restore** with `nano_banana_2_1` or `gpt_image_2_5` as an edit: "Restore this photo: remove scratches, dust and
   fading, keep the face, hair and clothes exactly, keep the era and the film grain." Colorize only if the family
   wants color ("natural, period-correct color"). Compare face by face with the original; reject any change.
3. **Animate a little:** a blink, a slow smile, a turn of the head, hair in the wind, a slow push-in. One or two
   people moving at most ([Kling's guide, Oct 2026](https://kling.ai/blog/animate-old-photos)). `kling_v4` or `wan_3`
   image-to-video, 5 s per photo:

```
Gentle, realistic motion only. {PERSON} blinks slowly and breaks into a soft smile, the head turns slightly toward
the camera; the background and clothes stay exactly as in the photo. Keep the original grain, color and era.
Slow push-in. No new people, no talking, no fast moves, no change to the face.
```

4. **Cut to music:** 15–30 photos for a 2–3 minute film at the party or the service, one caption of 5–8 words per
   photo, the longest message on the last frame ([Pictory](https://pictory.ai/blog/birthday-video-maker)).
   `scripts/assemble.sh` joins the clips and lays the track.

## Love story across the eras (anniversary, wedding surprise)

The couple recast in the decades they lived through (a 1970s dance hall, a 1990s campus, the street where they
met), ending at the real place. Make one still per era from their photos with `nano_banana_2_1`, check both faces,
then 8–15 s per era on `seedance_2_5` with both faces as references. It takes a day and many retakes; the
tutorial with 198k views is mostly about keeping two faces right ([Higgsfield](https://www.youtube.com/watch?v=QfylrxtQSSs)).
Only with both people's agreement.

## Memorial, celebration of life, retirement

- Calm, slow and warm: soft light, a smile, a slow push-in. No confetti, no party effects, no making the person speak
  or sing unless the family asks for it, and only with a voice sample the family owns.
- Words from the family over the photos (a recorded voice note, or `eleven_v4` reading their text), the music
  ducked 8–10 dB under it.
- Keep it private unless the family wants it shared. Some relatives find animating the dead upsetting: ask first.
- A retirement or farewell tribute: friends' 5–8 s messages and photos from the career, one title card per decade.

## Skills that help

- `eachlabs/skills` → `photo-restoration`, `photo-colorization` (repair and colorize before animating; Eachlabs key).
- `aaronyi97/wedding-video-guided-wizard` (guided story video for a real couple).
- `hiyabh/claude-video-skills` → `blessing-video-weaver` (friends' self-recorded greetings woven into one film).

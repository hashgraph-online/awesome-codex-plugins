# Birthday formats that spread (X, Jun–Oct 2026)

Measured on X on 2026-10-30: 499 occasion posts in two windows (Jun 16–Aug 14 and Aug 15–Oct 30), numbers as the API
returned them. The viral prompts behind these formats, with their results, are on varg how to:
https://varg.ai/how-to/browse/skills/greetings (each card has the author's prompt, Copy and "hand it to an agent").

Every template below takes `{NAME}`, `{AGE}`, `{SENDER}` and the details from step 1 of SKILL.md. Write the timed
beats in the person's real order of events; the best birthday prompt is the ritual in order.

## A. The song with their name (the most personal gift)

On X the name song lives as links (Suno, TikTok), not as posts, but it is the most searched birthday request after
the video itself ("birthday song with name": 556 distinct Google and YouTube suggestions). Make the song
(`song.md`), then put it under one of:

- **Their photos, one per line of the song:** 8–16 photos, a cut on every line, the name on screen when it is sung
  (HyperFrames or `scripts/assemble.sh` over short clips).
- **One generated clip on the chorus:** format B below, timed so "make a wish, {NAME}" lands on the candles.
- **A lyric video:** the lines on screen as they are sung (`varg-music-video`).

An anime-style song video for an original character (a girl alone with one slice of cake, a tiny companion, a song
that tells the story) drew 501k views: human-made character sheets kept her identical across 73 s.

## B. Their photo comes to life (the candle moment)

```
Handheld smartphone party video, vertical, one continuous shot, real speed.
0-3s: {NAME} takes a breath and blows out all the candles in one go; the flames go out and thin smoke curls up.
3-6s: friends cheer and clap, a hand tosses {CONFETTI COLORS} confetti that drifts down through the warm light.
6-8s: {NAME} laughs, covers their mouth with both hands, then looks up past the camera with a huge smile.
Slight natural camera shake, warm tungsten light, string lights behind. The cake and the letters "{CAKE TEXT}"
stay exactly the same and readable the whole time; once out, the candles stay out.
Sound: a breath and a soft whoosh, friends cheering and clapping, laughter. No music, no speech, no new text.
```

The key still comes first (`gpt_image_2_5`, the person's photo as `reference_image`): "{NAME}, {AGE}, leaning toward
a homemade cake with the words "{CAKE TEXT}" piped on top, spelled exactly …". Tested: Seedance 2.5 8 s with audio
kept the candles out and the face steady (308 credits); Wan 3 10 s relit the candles at 4.8 s (100 credits, cut at
4.6 s).

## C. Retro home-video tape (rising)

The 2026 birthday look is a found tape, not a glossy film: a friend filming on a 2003 DV camcorder, a 1970s 16 mm
party, a 1998 VHS. Sampled posts went from 5 to 9 between the windows and the top post from 172 to 913 likes; the
best (a camcorder birthday vlog, full prompt public) has 183k views and 476 bookmarks.

```
Format: 16:9, 30 s, two 15 s generations joined on the cake-box shot. Raw consumer DV camcorder home video from
{ERA_YEAR} in {CITY}, filmed by a friend. It must read as a real home tape, not a filter.
References: @image1 = {NAME}'s face, hair and outfit only.
Gen 1 (0-15 s): getting ready at the mirror, meeting {FRIENDS} on the street, buying the cake (the box carries
through every scene). Gen 2 (15-30 s): the candles in a dim room, flash photos, the walk home at night.
Look: 4:3 framing inside 16:9, auto-exposure pumping, soft focus, tape date stamp {DATE} in the corner, on-camera mic.
Era objects only: flip phones, a point-and-shoot, no smartphones, no modern logos.
```

`seedance_2_5`, one face reference, two 15 s parts. The era-objects line matters: models add smartphones otherwise.

## D. Then and now (milestones: 18, 30, 50, 60, 80)

Photos across the years in order, each becoming the next: a baby photo, school, the first job, today. Use the person's
real photos as first and last frames (`seedance_2_5` first/last frames, or `kling_v4` keyframes), 3–5 s per step, the
age counting up on screen as overlay text. Restore and colorize old prints first (`nano_banana_2_1` edit: "restore this
photo: remove scratches and fading, keep the face exactly, natural color"). For anyone under 18 in the photos, use the
family's own prints only, deliver privately and do not post publicly.

## E. The trailer of their life

An epic movie trailer starring them: three to five shots of the person doing what they love, cut on a drum hit, a
title card "{NAME}: {AGE}" (overlay type, not generated). A character sheet from their photos first
(`varg-consistent-characters`), then `seedance_2_5` multi-shot, 8–15 s per generation.

## F. Self-insert spectacle (your own birthday post)

One selfie in, one film still out: a fire-breathing candle, a rooftop party at golden hour, a tiny you climbing a giant
cake in a 1968 TV look (55k views, 201 bookmarks, prompt public). Rising, but most copies sit in paid creator
programs; the organic one-offs carry a concrete scale or period idea. `gpt_image_2_5` still, then `seedance_2_5`.

The cheapest reply magnet: a screenshot of your own profile with party balloons rising over it, 6 s on `kling_v4`
image-to-video (1,028 likes and 310 birthday wishes for a 6 s clip).

## G. Milestone poster (images)

The most saved birthday images of 2026 are posters: a giant age number carved into a paper wall with the person sitting
on it (99k views, 1,142 bookmarks), a luxury magazine poster (67k views, 1,693 bookmarks), a studio silhouette shoot
(325 bookmarks). `gpt_image_2_5` with the person's photo; animate it into a 5 s push-in for a story.

## H. The pet's birthday

The dog or cat in a party hat at a dog-safe cake, friends' hands clapping, the pet sniffing the candle-free cake. From
the pet's real photo (`gpt_image_2_5`), then 6–8 s on `wan_3` or `kling_v4`. On X every pet clip in the sample was a
paid creator-program post, so there is no organic benchmark: make it about the pet's real habits.

## I. Anniversary and family days (same tools)

- **Their love story across the eras:** the couple recast in the decades they lived through, ending at the place they
  really met (a wedding surprise film reached 910k views and 4.9k bookmarks in July; it peaked and faded by October).
  Era stills from their photos (`nano_banana_2_1`), then `seedance_2_5` 10–15 s per era. Only with both people's consent.
- **Old family photos brought to life as a gift**, filmed with the reaction: the biggest occasion post of the year
  (1.50M views, 8.6k bookmarks, a 60th birthday for a mother). Restore first, animate gently (a smile, a turn of the
  head, a slow push-in), no party effects on photos of people who have died.
- **Mother's Day, Father's Day, Valentine's:** formats A, B or D with that person; search demand is small, so make it
  as personal as possible rather than seasonal.

## What does not work any more

- One-tap app templates (the same "birthday" effect for everyone): steady volume, bookmarks rarely above 120.
- Pixar-style prompt-farm stories: volume up, saves flat (3–72 bookmarks).
- Generic "Happy Birthday" text generated into the scene with no person or detail.

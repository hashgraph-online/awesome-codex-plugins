---
name: varg-mascot-jingle-ad
description: >-
  Turns a product into a singing mascot ad on varg: the product itself as a claymation, plush or
  3D-family-film character with a face built for lip-sync, a 15-30 s jingle with the brand name in
  the hook (Lyria 3.5 with timed lyric sections, trimmed to length), the mascot singing it on
  Seedance 2.5 with the song as an audio reference, the master song laid back on top, lyric
  captions and a real product end card. Non-human ads skip the "fake person" problem, get shared
  and suit dropshipping products. Use when a seller asks for a jingle ad, a singing product, a
  mascot ad, a claymation or cartoon product video, a song ad for TikTok or Reels, or a talking
  product character. Not for full music videos for songs (varg-music-video), human UGC actors
  (ai-ugc-ad-video), or original characters without a product (varg-character-absurd).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - ffmpeg
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). ffmpeg to trim the song and lay it over the clip.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Singing mascot jingle ad

Singing products are back in 2026: a viral TikTok jingle became a national Dr Pepper ad, Super Bowl ads leaned on singalongs, and AI "musical microdramas" with singing cartoon narrators ran by the thousand on Google and Meta, until many were pulled for health claims and offensive hooks ([CNN](https://abc17news.com/news/national-world/cnn-national/2026/10/28/the-new-frontier-for-ads-is-racist-cartoon-ai-musical-microdrama/)). Do the format; skip the claims.

## 1. The mascot (one image)

The product becomes the character: same shape, colours and label, plus a face **built for lip-sync**: big eyes, a real mouth with a jaw and visible teeth (not a line), roughly human proportions, mouth slightly open, facing the camera ([mascot lip-sync guide](https://labmarcel.substack.com/p/the-complete-guide-to-mascot-lipsync)).

```
Turn the <product> from the reference image into a cute claymation mascot character: the same
<colors> body and <key detail>, with two big friendly cartoon eyes and a wide expressive mouth with a
visible jaw and small teeth, two tiny clay arms. It stands on <setting>, facing the camera, mouth
slightly open, neutral pose. Stop-motion clay texture, miniature studio lighting, vertical 9:16, no text.
```

`nano_banana_2_1` with the product photo, 5 credits. Styles: claymation, plush/felt, "3D animated family-film style". Never write "Pixar" or "Disney" and never imitate a known character.

## 2. The jingle

Lyrics: 4–6 short lines, the brand name in the hook and sung twice, one line every 3–4 s, claims only from the seller's fact sheet. Three shapes: a jingle (sung brand bars at the start or end), a sung hook (2–3 lines, test against a spoken hook), a story song.

```
A catchy, upbeat 15-second advertising jingle, playful ukulele and hand claps with a light pop beat,
110 BPM, one cheerful lead singer, simple memorable melody. Lyrics: [0:00-0:07] "<line 1>"
[0:07-0:15] "<brand line>". Ends on a short bright strum.
```

`lyria_3_5`, ~10 credits. **The length you ask for is not what you get**: our 15 s request came back as 61 s with the lines spread out. Transcribe it (Whisper), then cut the sung lines into one master:

```bash
ffmpeg -i song.mp3 -filter_complex "[0:a]atrim=0:7.6,asetpts=PTS-STARTPTS[a];[0:a]atrim=30:37.8,asetpts=PTS-STARTPTS,afade=t=out:st=7:d=0.8[b];[a][b]acrossfade=d=0.3" jingle15.mp3
```

No artist imitation, no AI covers. AI music is generally not copyrightable; your licence comes from the model's terms.

## 3. Make it sing

Seedance 2.5 with the mascot as the first frame and the master song as an audio reference, `"audio": true`, duration = song length:

```
@image1 is the exact claymation mascot and the first frame. The mascot sings the song from @audio1
straight to the camera, its clay mouth opening and closing exactly in sync with every sung word, eyes
blinking, bouncing to the beat, waving its tiny arms. Camera locked, stop-motion clay texture, about
12 fps feel. Keep the mascot's shape and colors exactly the same. No text, no other characters.
```

Then **always lay the master song back over the clip**: native-audio models re-sing the words their own way (ours repeated line 1 and dropped the brand line):

```bash
ffmpeg -i mascot.mp4 -i jingle15.mp3 -map 0:v -map 1:a -c:v copy -shortest mascot_final.mp4
```

Lip-sync models on cartoon faces: `sync_v3` left our clay mouth unchanged (100 credits for nothing), so test one line before a batch. For a human-like mascot face, `minimax_h3_max_lipsync` or VEED Fabric are the next things to try.

## 4. Finish

Lyric captions one line at a time (karaoke style), cut on downbeats (`music-to-video` skill), a 1–2 s end card with the real product photo and the price, the AI label on.

## Tested

2026-10-28, LED pet nail clipper: mascot from the product photo (`nano_banana_2_1`, 5 credits), jingle on `lyria_3_5` (10 credits, 61 s, cut to 15 s), `seedance_2_5` 15 s with the song as reference (578 credits): the clay mascot sings, bounces and waves, mouth moving with the rhythm, shape and colours of the product intact; `sync_v3` added nothing on the clay face. Result with the master song: https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_b1f093b28659.mp4

## Related skills

`varg-character-absurd` (more mascot looks), `varg-music-video` (full songs), `varg-product-lock` (keep the product's label), `ai-ad-compliance-check` (claims in lyrics), `varg-ad-variants` (a sung hook in front of a winning ad).

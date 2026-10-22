---
title: Media
impact: MEDIUM
tags: captions, transcripts, audio-description, video, audio, podcasts
wcag: 1.2.1, 1.2.2, 1.2.5
---

**Rule**: Video has captions, audio has a transcript, and information shown only visually in a video is also described.

**Why**: Deaf and hard-of-hearing users need captions; blind users need visual-only information described; many people watch with the sound off. WCAG requires captions for prerecorded video with audio (1.2.2, level A), alternatives for audio-only and video-only content (1.2.1, level A), and audio description of important visual content (1.2.5, level AA).

### When Building

- **Captions** for every prerecorded video with speech or meaningful sound — accurate, synchronised, identifying speakers and important sounds; auto-generated captions reviewed before publishing
- **Transcripts** for audio-only content (podcasts, voice notes)
- **Audio description** when the video shows information the narration doesn't say (on-screen text, demonstrated steps) — or write the narration so it says it
- **Accessible player** — keyboard-operable controls with labels, captions toggle, no autoplay with sound (`rules/motion-time.md`)
- **Product demos and onboarding videos** count too — they often show UI steps silently

### When Auditing

- `<video>` without a `<track kind="captions">` or burned-in captions; native players without caption files
- Podcasts or audio clips with no transcript
- Silent screen-recording demos that rely on seeing the screen
- Custom video players with unlabeled or mouse-only controls

### Incorrect

```html
<video src="/demo.mp4" autoplay></video>
```

### Correct

```html
<video src="/demo.mp4" controls>
  <track kind="captions" src="/demo.en.vtt" srclang="en" label="English">
</video>
```

### Alternatives

Purely decorative background video with no information needs no captions, but it must be pausable and should stop for reduced-motion users. Live captions (WCAG 1.2.4) apply to live streams; plan for them when the product streams.

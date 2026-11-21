---
name: varg-character-keynote
description: >-
  Makes a vertical 9:16 "character on stage" video in one varg render: a custom character
  (Higgsfield Soul) stands at a conference keynote and delivers a one- or two-line hook with
  a physical punchline, voiced by Seedance 2.5 native audio with audience applause. Use when
  someone asks for a keynote or speaker-style UGC ad, a talking character or talking avatar
  giving a speech on stage, a spokesperson or mascot delivering one punchy line, a conference
  talk clip with a custom person, or wants to swap the character in this template. Not for long
  talking-head videos from a script or voiceover (use varg-ai with a lip-sync model), multi-scene
  ads with the same actors (use varg-consistent-characters), two-person dialogue (use
  varg-podcast-video), or songs (use varg-music-video).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    homepage: https://varg.ai
compatibility: >-
  Needs the varg MCP connection (https://mcp.varg.ai/mcp, render_video tool) or a VARG_API_KEY
  with curl for POST https://api.varg.ai/v2/render. No local dependencies.
allowed-tools: Bash(curl:*) Bash(jq:*) Read Write Edit
---

# varg character keynote

One varg render produces a 9:16 talking-speaker video: Soul generates the character, Nano Banana 2.1 the empty stage, and Seedance 2.5 puts the character on that stage and voices the line with native audio.

Generation runs on varg: the varg MCP server (`https://mcp.varg.ai/mcp`, tool `render_video`) or the `varg-ai` skill (cloud render, `POST /v2/render`). Read `varg-ai` for sign-in, models and the render format.

## To create or swap a character, edit ONLY three things

1. `LINE`: one or two short spoken sentences, emotional hook + payoff (fits 8 s).
2. `character` prompt: "Candid photo of ..." + body/face/clothing details + "Vivid saturated colors, realistic skin detail." Contrast sells the line: an exact age, an unusual build or a loud outfit played straight beats a generic presenter. The `varg-character-design` skill has archetypes, realism wording and moderation-safe phrasing; if the speaker must reappear in other videos, make a sheet there and pass its face crop instead of generating with Soul.
3. `scene` prompt: stage description, always "empty, no people", with a themed screen behind the speaker.

## Template (cloud render: no imports)

```tsx
const LINE = "I learned to code at sixty-eight. Your excuse just expired.";

const character = Image({
  prompt: "Candid photo of <PERSON: age, build, face, hair, clothing, accessories>. Vivid saturated colors, realistic skin detail.",
  model: varg.imageModel("soul"),
  aspectRatio: "9:16",
  // Soul "Realistic" style. Provider options must sit under varg.<provider>, or they are dropped.
  providerOptions: { varg: { higgsfield: { params: { style_id: "1cb4b936-77bf-4f9a-9039-f3d349a4cdbe" } } } },
});

const scene = Image({
  prompt: "Wide shot of a bright modern conference stage, empty, no people: dark backdrop with a large glowing screen showing <THEMED MINIMALIST SLIDE>, warm spotlights, standing microphone, blurred audience in the dark foreground. Vivid saturated colors, photorealistic event photography.",
  model: varg.imageModel("nano_banana_2_1"),
  aspectRatio: "9:16",
});

const talk = Video({
  prompt: {
    text: "The <person> from the first reference image stands center stage as a keynote speaker on the conference stage from the second reference image, holding the microphone. <One line of speaking manner/emotion.> Dialogue: \"" + LINE + "\" On the last words <one physical punchline action>, the audience erupts in applause. Warm spotlights, big-conference keynote energy, vivid saturated colors, no text on screen.",
    images: [character, scene],
  },
  model: varg.videoModel("seedance_2_5"),
  aspectRatio: "9:16",
  duration: 8,
  audio: "native",
});

export default (
  <Render width={1080} height={1920}>
    <Clip duration={8}>{talk}</Clip>
  </Render>
);
```

## Run it

- **MCP:** price it with `estimate_cost` (tool `render`, input `{ "code": <template> }`), then pass the template as `code` to `render_video` and poll `get_job` until it completes. Report the billed cost with `get_job_cost`.
- **API:** save it as `keynote.tsx`, then

```bash
curl -s -X POST https://api.varg.ai/v2/render \
  -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d "{\"code\": $(jq -Rs . < keynote.tsx)}"
# -> {"id":"job_xxx",...}; poll until completed, the video is at output.outputs[0].url
curl -s https://api.varg.ai/v2/jobs/JOB_ID -H "Authorization: Bearer $VARG_API_KEY"
```

## Rules

- Cloud render code has NO import statements: `Render`, `Clip`, `Image`, `Video` and `varg` are globals. Models go ONLY through `varg.imageModel()` / `varg.videoModel()`; bare model strings crash.
- `Image()` and `Video()` are function calls, composed with JSX (`<Clip>{talk}</Clip>`).
- One clip = one continuous action; the physical punchline lands on the last words of `LINE`.
- Keep `"no text on screen"` and `audio: "native"`: speech and applause come from Seedance's native audio.
- Price first. Run `estimate_cost` (MCP, tool `render`) or `POST /v2/estimate` on the Seedance request and quote the result in credits. One run is roughly 350 credits at Seedance's default 720p (catalog, October 2026) and takes about 5–15 minutes. Never launch a render without the user's explicit go-ahead.
- Seedance renders 720p by default. For 1080p, set the resolution for the route that runs it (see `https://varg.ai/models/seedance_2_5.md`); it roughly doubles the cost.
- `aspectRatio` must match on both Images, the Video and the Render canvas (1080×1920 = 9:16). Change all four together when changing format.
- Unchanged prompts are cached for free: when iterating on the line or the punchline, keep the `character` and `scene` prompts byte-identical so only the video regenerates.

## Related skills

`varg-ai` (sign-in, models, cloud render format), `varg-consistent-characters` (the same people across several scenes), `varg-podcast-video` (two characters talking), `video-skills` (find a skill for another format).

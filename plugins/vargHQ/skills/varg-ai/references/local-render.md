# Local Render Mode

Write a `.tsx` file and render locally via the varg CLI. Requires `bun` and `ffmpeg` + `ffprobe`.

Local rendering is faster than cloud rendering, supports custom npm packages, Remotion components, and gives you full control over the output.

## Pre-Flight Checklist

Run through this before your first render in any project:

1. **Check runtime**: `bun --version` (>= 1.0) and `ffmpeg -version` (>= 6.0)
2. **Check API key**: `grep VARG_API_KEY .env` -- must be set. Get one at https://varg.ai
3. **Create directories**: `mkdir -p output .cache/ai`
   **SDK version**: if the project has a `package.json`, pin a current SDK with `bun add vargai@alpha` (≥ 0.4.0-alpha124). The npm `latest` tag still points to an older build that talks to the legacy v1 API and has no `audio: "native"`. Always run the CLI as `bunx vargai@alpha`.
4. **JSX pragma**: First line of every `.tsx` file must be `/** @jsxImportSource vargai */`
5. **Correct imports**:
   ```tsx
   import { Render, Clip, Image, Video, Speech, Music, Captions } from "vargai/react";
   import { createVarg } from "vargai/ai";
   const varg = createVarg({ apiKey: process.env.VARG_API_KEY! });
   ```
6. **Test structure first**: `bunx vargai@alpha render video.tsx --preview` validates composition for 0 credits
7. **Then full render**: `bunx vargai@alpha render video.tsx -o output/video.mp4`

## TSX Format

Local mode requires imports and an explicit provider setup:

```tsx
/** @jsxImportSource vargai */
import { Render, Clip, Music, Captions, Title, Image, Video, Speech } from "vargai/react"
import { createVarg } from "vargai/ai"

const varg = createVarg({ apiKey: process.env.VARG_API_KEY! })
```

Use `varg.imageModel(...)`, `varg.videoModel(...)`, `varg.speechModel(...)`, `varg.musicModel(...)` for all model references. This routes through the gateway for caching and unified billing.

### Minimal Example

```tsx
/** @jsxImportSource vargai */
import { Render, Clip, Image } from "vargai/react"
import { createVarg } from "vargai/ai"

const varg = createVarg({ apiKey: process.env.VARG_API_KEY! })

const img = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "a cozy cabin in mountains at sunset, warm golden light",
  aspectRatio: "16:9"
})

export default (
  <Render width={1920} height={1080}>
    <Clip duration={3}>{img}</Clip>
  </Render>
)
```

### Full Example (video + speech + music + captions)

```tsx
/** @jsxImportSource vargai */
import { Render, Clip, Music, Captions, Title, Image, Video, Speech } from "vargai/react"
import { createVarg } from "vargai/ai"

const varg = createVarg({ apiKey: process.env.VARG_API_KEY! })

const hero = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "cinematic portrait of a warrior princess, golden hour lighting",
  aspectRatio: "9:16"
})

const scene = Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: { text: "warrior walks forward through misty forest, camera follows", images: [hero] },
  duration: 5
})

const voice = Speech({
  model: varg.speechModel("eleven_v4"),
  voice: "rachel",
  children: "In a world beyond imagination..."
})

export default (
  <Render width={1080} height={1920} fps={30}>
    <Music model={varg.musicModel("mureka_9_5")} prompt="epic orchestral, rising tension" duration={10} volume={0.3} />
    <Clip duration={5}>
      {scene}
      <Title position="bottom">The Last Guardian</Title>
    </Clip>
    <Captions src={voice} style="tiktok" withAudio />
  </Render>
)
```

## CLI Commands

```bash
# Preview with free placeholders (validate structure before paying)
bunx vargai@alpha render video.tsx --preview

# Full render (costs credits)
bunx vargai@alpha render video.tsx --verbose

# Force regeneration (bypass cache -- use sparingly, costs $$$)
bunx vargai@alpha render video.tsx --no-cache

# Open the result
open output/video.mp4
```

## Background Rendering

Renders take 3-15+ minutes. Run in the background to avoid blocking:

```bash
nohup bunx vargai@alpha render video.tsx --verbose > output/render.log 2>&1 &
echo "PID: $!"

# Check progress
tail -f output/render.log
```

## Iteration Workflow

1. **Preview first**: Run with `--preview` to validate structure with free placeholders.
2. **Keep prompts stable**: When modifying a multi-clip render, keep unchanged prompt strings EXACTLY the same (character-for-character) to avoid cache misses and re-generation.
3. **Iterate on one clip**: Change only the prompts you need to update. Cached clips render instantly for 0 credits.
4. **Full render**: Once preview looks correct, run without `--preview` for the final output.

## Setup

If you haven't set up a project yet:

```bash
# Run the setup script (from the skill directory)
bun scripts/setup.ts

# Or manually:
# 1. Ensure VARG_API_KEY is in .env
echo "VARG_API_KEY=varg_xxx" >> .env

# 2. Quick smoke test
bunx vargai@alpha hello
```

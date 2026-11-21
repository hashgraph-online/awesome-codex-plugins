# Component Reference

All components are available as globals when rendering via the render service or imported from `"vargai/react"` when using the SDK directly.

## `<Render>` -- Root Container

Every template must export a `<Render>` as the default export.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `width` | `number` | 1920 | Output width in pixels |
| `height` | `number` | 1080 | Output height in pixels |
| `fps` | `number` | 30 | Frames per second |
| `normalize` | `boolean` | false | Normalize audio levels |
| `shortest` | `boolean` | false | End video at shortest track |

```tsx
// Vertical (9:16 for TikTok/Reels)
<Render width={1080} height={1920} fps={30}>

// Horizontal (16:9 for YouTube)
<Render width={1920} height={1080}>

// Square (1:1 for Instagram)
<Render width={1080} height={1080}>

// Portrait (4:5 for Instagram)
<Render width={1080} height={1350}>
```

---

## `<Clip>` -- Timeline Segment

Defines a section of the timeline. Clips play sequentially.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `duration` | `number \| "auto"` | auto | Duration in seconds. Use `"auto"` for speech-driven clips where duration matches the audio length. Should match inner Video duration when set explicitly. |
| `transition` | `{ name, duration }` | none | Transition from previous clip |
| `cutFrom` | `number` | 0 | Trim start (seconds). Use `0.3` to skip AI warm-up frames. |
| `cutTo` | `number` | end | Trim end (seconds). Source duration must be >= cutTo. |

### Transitions

Available `name` values (any FFmpeg xfade transition name works):

**Common transitions:**

| Name | Effect |
|------|--------|
| `fade` | Fade to/from black (default) |
| `dissolve` | Cross-dissolve between clips |
| `crossfade` | Smooth cross-fade (alias for dissolve) |
| `wipeleft` / `wiperight` | Horizontal wipe |
| `wipeup` / `wipedown` | Vertical wipe |
| `slideleft` / `slideright` | Horizontal slide |
| `slideup` / `slidedown` | Vertical slide |

**Creative transitions:**

| Name | Effect |
|------|--------|
| `cube` | 3D cube rotation between clips |
| `pixelize` | Pixelation dissolve |
| `circlecrop` | Circular iris in/out |
| `radial` | Radial wipe |
| `smoothleft` / `smoothright` | Smooth directional blend |
| `smoothup` / `smoothdown` | Smooth vertical blend |
| `squeezeh` / `squeezev` | Squeeze horizontal/vertical |
| `hlwind` / `hrwind` | Wind effect left/right |
| `vuwind` / `vdwind` | Wind effect up/down |
| `coverleft` / `coverright` | Cover slide |
| `coverup` / `coverdown` | Cover slide vertical |
| `zoomin` | Zoom into next clip |

```tsx
<Clip duration={5} transition={{ name: "fade", duration: 0.5 }}>
  {video}
</Clip>

// Punchy cuts with trimming
<Clip cutFrom={0.3} cutTo={2.5} duration={2.2}>
  {video}  // Source must be >= 2.5s
</Clip>
```

---

## `Image()` -- Image Generation

**Must be called as a function, not JSX.**

| Prop | Type | Description |
|------|------|-------------|
| `model` | `ImageModelV3` | Required. e.g. `varg.imageModel("nano_banana_2_1")` |
| `prompt` | `string \| { text, images }` | Text prompt or edit prompt with references |
| `aspectRatio` | `string` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"`, `"4:5"` |
| `zoom` | `"in" \| "out" \| "left" \| "right"` | Ken Burns zoom/pan animation (for slideshows) |
| `resize` | `"cover" \| "contain" \| "contain-blur" \| "stretch"` | How image fills the frame. Default: `"cover"` |
| `cropPosition` | `string` | Crop anchor when using `resize: "cover"`: `"top"`, `"center"`, `"bottom"`, `"left"`, `"right"` |
| `removeBackground` | `boolean` | Remove image background |
| `providerOptions` | `object` | Model-specific options |

```tsx
// Text-to-image
const img = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "cinematic portrait, golden hour",
  aspectRatio: "9:16"
})

// Reference editing
const edited = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: { text: "same person on a beach", images: [referenceImage] },
  aspectRatio: "9:16"
})
```

### Ken Burns (Zoom / Pan)

Add cinematic motion to still images in slideshows. The `zoom` prop creates a slow Ken Burns animation over the clip duration.

```tsx
// Slow zoom in -- dramatic reveal
const landscape = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "vast mountain range at sunset, layers of purple and gold",
  zoom: "in"
})

// Slow zoom out -- establishing shot
const portrait = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "warrior princess, piercing emerald eyes, battle-worn silver armor",
  zoom: "out"
})

// Pan left -- panoramic sweep
const cityscape = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "tokyo skyline at night, neon lights reflecting on wet streets",
  zoom: "left"
})

// Pan right
const beach = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "tropical beach at golden hour, palm trees silhouetted",
  zoom: "right"
})

export default (
  <Render width={1920} height={1080}>
    <Clip duration={4}>{landscape}</Clip>
    <Clip duration={4} transition={{ name: "dissolve", duration: 0.8 }}>{portrait}</Clip>
    <Clip duration={4} transition={{ name: "dissolve", duration: 0.8 }}>{cityscape}</Clip>
    <Clip duration={4} transition={{ name: "dissolve", duration: 0.8 }}>{beach}</Clip>
  </Render>
)
```

**Tip**: Ken Burns + `dissolve` transitions = classic documentary/slideshow feel. Combine with `<Music>` for a polished result.

### Resize Modes

Control how images/videos fill the frame when their aspect ratio doesn't match the output:

| Mode | Behavior |
|------|----------|
| `"cover"` | Fill frame, crop overflow (default) |
| `"contain"` | Fit inside frame, letterbox/pillarbox with black bars |
| `"contain-blur"` | Fit inside frame, blurred version fills background |
| `"stretch"` | Stretch to fill (distorts aspect ratio) |

```tsx
// Contain with blurred background (popular for portrait-in-landscape)
const img = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "portrait photo",
  aspectRatio: "9:16",
  resize: "contain-blur"
})
```

---

## `Video()` -- Video Generation

**Must be called as a function, not JSX.**

| Prop | Type | Description |
|------|------|-------------|
| `model` | `VideoModelV3` | Required. e.g. `varg.videoModel("seedance_2_5")` |
| `prompt` | `string \| { text?, images?, audio?, video? }` | Prompt with optional media inputs |
| `duration` | `number` | Duration in seconds. Check model constraints! |
| `aspectRatio` | `string` | `"16:9"`, `"9:16"`, `"1:1"` |
| `audio` | `"native"` | Generate native audio (dialogue, SFX, ambience) and keep it. Supported on `seedance_2_5`, `kling_v4`, `kling_v3`, `flux_3`, `veo_3_1`. |
| `keepAudio` | `boolean` | Keep the clip's audio in the composition (default `true`) |
| `providerOptions` | `object` | Model-specific options, **namespaced by provider**: `{ varg: { fal: {...} } }`. Flat bags are dropped. |

```tsx
// Text-to-video with native audio
const scene = Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: "barista slides a latte across the counter and says: \"Here you go.\" Cafe ambience.",
  duration: 5,
  audio: "native"
})

// Text-to-video
const vid = Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: "a bird soaring over mountains, aerial shot",
  duration: 5
})

// Image-to-video (ONE image = first frame; several images = references, reference-capable models only)
const animated = Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: { text: "person starts walking forward", images: [characterImage] },
  duration: 5
})

// Lipsync — image + audio (VEED, recommended)
const talking = Video({
  model: varg.videoModel("veed_fabric_1_0"),
  keepAudio: true,
  prompt: { images: [portrait], audio: voiceover }
})
```

---

## `Speech()` -- Text-to-Speech

**Must be called as a function, not JSX.**

| Prop | Type | Description |
|------|------|-------------|
| `model` | `SpeechModelV3` | Required. e.g. `varg.speechModel("eleven_v4")` |
| `voice` | `string` | Voice name (see [models.md](models.md) for list) |
| `children` | `string` | Text to speak |

```tsx
const narration = Speech({
  model: varg.speechModel("eleven_v4"),
  voice: "rachel",
  children: "Welcome to our product showcase."
})
```

---

## `<Music>` -- Background Audio

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `model` | `MusicModelV3` | - | Required for AI music. `varg.musicModel("mureka_9_5")` |
| `prompt` | `string` | - | Music description |
| `src` | `string` | - | URL for pre-made audio (instead of AI generation) |
| `duration` | `number` | - | **Required**. Must match total video length. |
| `volume` | `number` | 1.0 | Volume (0-1) |
| `loop` | `boolean` | false | Loop the audio |
| `ducking` | `boolean` | false | Auto-lower volume under speech |
| `start` | `number` | 0 | Offset in seconds |

```tsx
<Render width={1080} height={1920}>
  <Music
    model={varg.musicModel("mureka_9_5")}
    prompt="upbeat electronic, rising energy"
    duration={15}
    volume={0.3}
    ducking
  />
  <Clip duration={15}>{video}</Clip>
</Render>
```

---

## `<Captions>` -- Subtitle Track

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `src` | `Speech result` | - | Speech element to transcribe |
| `srt` | `string` | - | SRT content (alternative to src) |
| `style` | `string` | `"tiktok"` | `tiktok`, `karaoke`, `bounce`, `typewriter` |
| `position` | `string` | `"bottom"` | `top`, `center`, `bottom` |
| `withAudio` | `boolean` | `false` | Include the Speech audio track in the video |

```tsx
const speech = Speech({ ... })

// Captions only (no audio)
<Captions src={speech} style="tiktok" position="bottom" />

// Captions + audio from the speech element
<Captions src={speech} style="tiktok" position="bottom" withAudio />
```

> By default, `<Captions src={speech} />` renders captions only (no audio). Add `withAudio` to include the speech audio track. When using `withAudio`, do NOT also add `{speech}` as a separate Clip child -- that causes double audio.

### Caption Styles

- **tiktok** -- Bold white text, large, social-media style
- **karaoke** -- Cyan highlighted word-by-word
- **bounce** -- Impact font with bounce animation
- **typewriter** -- Green monospace, typing effect

---

## `<Title>` -- Text Overlay

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `position` | `string` | `"center"` | `top`, `center`, `bottom` |
| `color` | `string` | `"white"` | Text color |
| `outline` | `boolean` | true | Text outline for readability |
| `children` | `string` | - | Title text |

```tsx
<Clip duration={5}>
  {video}
  <Title position="bottom" color="white">Product Name</Title>
</Clip>
```

---

## `<Subtitle>` -- Simple Subtitle

| Prop | Type | Description |
|------|------|-------------|
| `children` | `string` | Subtitle text |

---

## `<Overlay>` -- Positioned Layer

Works in two modes:
- **Global** (sibling of `<Clip>` inside `<Render>`) -- applied to ALL clips for the entire video
- **Per-clip** (inside a `<Clip>`) -- scoped to that clip only, with optional `start`/`end` timing

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `left` | `number\|string` | 0 | X position (pixels or `"5%"`) |
| `top` | `number\|string` | 0 | Y position (pixels or `"5%"`) |
| `width` | `number\|string` | auto | Width (pixels or `"25%"`) |
| `height` | `number\|string` | auto | Height (pixels or `"25%"`) |
| `volume` | `number` | 1.0 | Audio volume for overlay content |
| `start` | `number` | -- | Start time in seconds (relative to clip). Per-clip only. |
| `end` | `number` | -- | End time in seconds (relative to clip). Per-clip only. |

```tsx
// Per-clip overlay with timing (appears at 1s, disappears at 3s within this clip)
<Clip duration={5}>
  {backgroundVideo}
  <Overlay left="3%" top="3%" width="25%" height="25%" start={1} end={3}>
    {logoImage}
  </Overlay>
</Clip>

// Global overlay (appears on ALL clips for entire video)
<Render width={1920} height={1080}>
  <Clip duration={5}>{scene1}</Clip>
  <Clip duration={5}>{scene2}</Clip>
  <Overlay left="80%" top="5%" width="15%">
    {watermarkImage}
  </Overlay>
</Render>
```

---

## Layout Components

### `<Split>` -- Side-by-Side

```tsx
<Split direction="horizontal">
  {leftVideo}
  {rightVideo}
</Split>
```

### `<Grid>` -- N x M Grid

```tsx
<Grid columns={2} rows={2}>
  {video1}
  {video2}
  {video3}
  {video4}
</Grid>
```

### `<Slot>` -- Grid/Split Slot

Used inside Grid or Split for fine positioning.

### `<Slider>` -- Carousel

```tsx
<Slider direction="horizontal">
  {image1}
  {image2}
  {image3}
</Slider>
```

### `<Swipe>` -- Swipe Animation

```tsx
<Swipe direction="left">
  {image1}
  {image2}
</Swipe>
```

---

## `<Packshot>` -- End Card

| Prop | Type | Description |
|------|------|-------------|
| `logo` | `string` | Logo URL |
| `url` | `string` | Website URL text |
| `text` | `string` | CTA button text |
| `colors` | `object` | `{ background, text, button, buttonText }` |
| `blinking` | `boolean` | Animate CTA button |

```tsx
<Clip duration={3}>
  <Packshot
    logo="https://s3.varg.ai/logos/brand.png"
    url="brand.com"
    text="Shop Now"
    colors={{ background: "#000", text: "#fff", button: "#ff0000", buttonText: "#fff" }}
    blinking
  />
</Clip>
```

---

## `TalkingHead()` -- Lipsync Character

Combines an image + speech into a lipsync talking-head video. **Must be called as a function, not JSX.** Requires three props: `image`, `audio`, and `model`.

**Best model: `veed_fabric_1_0`** — takes image + audio directly (one step, fastest). For sync_v2/sync-v3, TalkingHead auto-animates the image first then lipsyncs (two-step, slower).

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `image` | `VargElement<"image">` | **Yes** | An `Image()` element (the character portrait) |
| `audio` | `VargElement<"speech">` | **Yes** | A `Speech()` element (the voiceover — await first for duration) |
| `model` | `VideoModelV3` | **Yes** | Lipsync model. Use `varg.videoModel("veed_fabric_1_0")` (recommended) |
| `lipsyncModel` | `VideoModelV3` | No | Override lipsync model (defaults to `model`) |
| `resolution` | `"480p" \| "720p" \| "1080p"` | No | Video resolution (default: `"720p"`) |
| `position` | `Position \| object` | No | Position within the clip |
| `size` | `{ width, height }` | No | Size override |

**IMPORTANT:** Do NOT pass `character`, `voice`, `src`, or `children` to TalkingHead — those are NOT valid props. Only `image`, `audio`, `model`.

```tsx
const portrait = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "friendly female host, studio background, looking at camera",
  aspectRatio: "9:16"
})

const audio = await Speech({
  model: varg.speechModel("eleven_v4"),
  voice: "rachel",
  children: "Welcome to our show! Today we're going to talk about something exciting."
})

export default (
  <Render width={1080} height={1920}>
    <Clip duration={audio.duration}>
      <TalkingHead image={portrait} audio={audio} model={varg.videoModel("veed_fabric_1_0")} />
      <Captions src={audio} style="tiktok" />
    </Clip>
  </Render>
)
```

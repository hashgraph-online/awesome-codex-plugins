# The varg how to card

Every listing on varg how to has this card. Fill every field you can verify; leave out what you cannot. These are the
fields of the varg MCP `publish_skill` tool and of `POST https://api.varg.ai/v2/skills/submissions`.

## Fields

| Field | Required | Limit | Rule |
|---|---|---|---|
| `name` | yes | 3–80 | Title Case. Named after the task, never a catalog word (skill, kit, recipe, playbook, catalog, hub). Use the first name template below that describes it honestly. Keep the author's brand only if people search for it. |
| `summary` | yes | 10–160 | One line: what it makes, from what, with which tool when it matters. "Word-by-word captions burned into a 9:16 video with FFmpeg." Not "This skill helps…". |
| `source_url` | yes | https | The skill folder: `https://github.com/<owner>/<repo>/tree/<branch>/<path>`, or the repo when the skill is at its root. |
| `install` | no | 300 | Copied from the repo's README or docs. `npx skills add <owner>/<repo> --skill <name>` only when skills.sh lists it, the README documents that form, or the folder is at the repo root or in `skills/`. Otherwise leave it out. Never invent one. |
| `use_when` | no | ≤ 8 × 200 | 3–6 triggers taken from the SKILL.md description, written as tasks: "Turning a podcast into vertical clips". |
| `category` | no | id | One id from the table below: what the skill makes on screen (make) or improves (craft). |
| `tags` | no | ≤ 12 × 30 | Lowercase. Tools, models and formats people search: `ffmpeg`, `remotion`, `seedance`, `captions`, `9:16`. |
| `media_url` | no | https | A real output of this skill: an asset in the repo, the author's post or upload. Never a made-up or unrelated example, never a film still. |
| `description` | no | 3,000 | 2–5 sentences, markdown allowed: input → output, how it works, what it needs (API keys, tools, a GPU, cost per run). |
| `publisher_name` | no | 80 | Who to credit, when not the repo owner. |

## Name templates (first that fits)

1. Open-source alternative to {Product}
2. Open-source {task tool}
3. Turn {input} into {output}
4. {Task} skills for Claude Code and AI agents
5. {Tool} for Claude Code: describe it, get it
6. {Tool} cookbook: copyable commands for {domain}
7. {Task} with {Library}
8. Local-first {task}: private, no subscription
9. Awesome {topic}: a curated list
10. {Format} video template for {framework}
11. {N} video models in one CLI for coding agents
12. Open-source agentic {domain} pipeline

None fits honestly → a plain task name: "Animated captions for Reels".

## Example

```json
{
  "name": "Word-by-word captions with WhisperX",
  "summary": "Word-level timestamps from WhisperX burned into a vertical video as karaoke captions with FFmpeg.",
  "source_url": "https://github.com/acme/video-skills/tree/main/captions",
  "install": "npx skills add acme/video-skills --skill captions",
  "use_when": ["Adding captions to a talking-head video", "Making TikTok-style word-by-word subtitles", "Burning an SRT into a Reel"],
  "category": "captions",
  "tags": ["captions", "whisperx", "ffmpeg", "9:16"],
  "media_url": "https://github.com/acme/video-skills/raw/main/captions/assets/example.mp4",
  "description": "Transcribes the audio with WhisperX for word-level timing, writes an ASS file with a highlight per word, and burns it in with FFmpeg. Runs locally; needs Python, FFmpeg with libass and about 2 GB for the model."
}
```

## Category ids

| id | Label | What it covers |
|---|---|---|
| `product` | Product videos | Product demos, packshots, 360° spins, e-commerce and before/after videos |
| `ads` | Ads & UGC | Performance ads, UGC creator ads, hooks, testimonials and ad variants for TikTok, Reels and Meta |
| `shorts` | Shorts & Reels | TikTok, Instagram Reels and YouTube Shorts: faceless videos, clips, memes and viral formats |
| `cinematic` | Cinematic & short films | Cinematic AI footage, short films, trailers and multi-shot scenes made with Seedance, Kling and Veo |
| `story` | Stories & short dramas | Scripts, story structure, short dramas, series and multi-shot storytelling |
| `animation` | Animation & motion graphics | Motion graphics, cartoons, hand-drawn and watercolor films, GSAP, Lottie and Rive animation |
| `music` | Music videos | Music videos, lyric and karaoke videos, visualizers and beat-synced edits |
| `launch` | Launch videos | Product launches, feature announcements, release notes and keynote reveals |
| `explainers` | Explainers | Explainer videos, website-to-video, data stories and math animations |
| `talking-head` | Talking heads & avatars | AI avatars, lip sync, presenters, podcasts and dialogue videos |
| `kinetic-type` | Text & titles | Kinetic typography, animated titles, title cards and word-per-beat text |
| `brand-motion` | Logo animations & intros | Logo reveals, 3D logo stings, intros and brand motion |
| `3d-scenes` | 3D scenes | Three.js, React Three Fiber and Blender scenes the camera flies through |
| `native-ui` | Phone & app screens | iMessage and chat stories, Notes-app ads, app demos, App Store screenshots and device mockups |
| `greetings` | Greetings & celebrations | Birthday, holiday and wedding videos, invitations, thank-yous and e-cards |
| `edit-services` | Editing services | Which service your agent should edit with, job by job: FFmpeg and the varg API for cuts, transcript tools for talking heads, clipping APIs, caption burn-in, AI video-to-video, lip sync and upscaling |
| `editing` | Editing & clips | Cut and assemble footage: long videos to clips, silence cuts, transitions, b-roll and pacing |
| `captions` | Captions & subtitles | Animated and word-by-word captions, subtitles, transcription and translation |
| `dubbing` | Dubbing & lip sync | Translate and dub a video in the speaker’s own voice, then re-sync the lips to the new audio |
| `edit-agents` | AI editing agents | Agents and pipelines that edit a whole video end to end: OpenMontage, video-use, auto-editor, CapCut and Premiere automation, transcript editors |
| `cuts` | Cuts & pacing | J-cuts, L-cuts, match cuts, jump cuts, smash cuts, speed ramps and beat cuts, each with the FFmpeg, Remotion, HyperFrames and CapCut way to make it |
| `transitions` | Transitions | Every way to join two shots: CapCut-style zooms, whips, glitches and masks, FFmpeg xfade, Remotion TransitionSeries, HyperFrames and GL shader transitions |
| `titles` | Headlines & callouts | Words over footage: headlines, key phrases, lower thirds, highlights and callouts that point at the thing that matters |
| `quotes` | Quotes & reviews | Testimonials, review cards, star ratings, posts and replies as proof inside a video |
| `end-cards` | End cards & CTAs | How a video ends: the call to action, URL and QR code, subscribe prompt, logo outro and the last line |
| `ui` | UI walkthroughs | How a product interface appears: screen-recording zoom and pan, UI that builds itself, floating panels, 3D tilts and dashboard reveals |
| `cursors` | Cursors & clicks | Smooth cursor paths, click ripples, keystroke overlays, agent cursors and the auto-zoom that follows the pointer |
| `devices` | Device mockups | Phones, laptops, browser windows and tablets: how the device enters, holds the screen and turns in 3D |
| `code` | Code & terminal | Code that types itself, diffs, terminal sessions, install lines and IDE close-ups that stay readable |
| `agent-flows` | AI agent flows | Agents at work: step lists, tool calls, node graphs, streaming chat answers and hand-offs between agents |
| `numbers` | Numbers & charts | Counters, big stats, bar and line charts, race charts, progress rings and before/after metrics |
| `logo-walls` | Customer logos | Trusted-by marquees, logo grids, partner lockups and integration orbits |
| `galleries` | Grids & carousels | Bento grids, photo carousels, marquee walls, stacked cards and filmstrips |
| `backdrops` | Backdrops | What sits behind the words and the UI: gradients, grids and dots, aurora, noise, spotlights and blurred product shots |
| `image` | Images & thumbnails | Image models, YouTube thumbnails, covers, carousels, upscaling and background removal |
| `characters` | Characters | Consistent characters across shots: face IDs, character sheets and casting |
| `locations` | Scenes & locations | Places and sets that stay the same across shots: interiors, landscapes, location sheets |
| `style-refs` | Style references | Mood boards and references from film stills, Pinterest and Are.na, turned into prompts |
| `art-direction` | Art styles | ASCII, collage, pixel art, watercolor, oil paint, p5 and generative looks |
| `logos` | Logos & brand kits | Logo design, brand kits and guidelines: marks, palettes, type |
| `ai-music` | AI music | Songs, instrumentals, jingles and background tracks from a prompt |
| `lyrics` | Lyrics & songwriting | Lyrics, hooks, song structure and style prompts for a track or a music video |
| `audio` | Voice & voiceover | Text to speech, voiceover, voice cloning, dialogue and dubbing |
| `sfx` | Sound effects | Sound effects, ambience, noise removal and voice isolation |
| `camera` | Camera & shots | Camera angles, shot sizes, lenses and camera moves, with the prompt words for Seedance, Kling and Veo |
| `lighting` | Lighting | Lighting setups, time of day and mood, as prompt words |
| `color` | Color grading & LUTs | Color grades, LUTs and film looks |
| `shaders` | Backgrounds & shaders | Shader backgrounds, overlays, filters, particles and WebGL effects |
| `prompting` | Prompts by model | How to prompt Seedance, Kling, Veo, FLUX, Higgsfield and GPT Image: syntax, references and prompt packs |
| `tooling` | Tools & renderers | Remotion, HyperFrames, GSAP, FFmpeg and the model CLIs your agent renders with |
| `research` | Research & trends | Trend scouting, reference search, video analysis and scrapers for your agent |

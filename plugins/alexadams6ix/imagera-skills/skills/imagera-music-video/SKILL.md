---
name: imagera-music-video
description: "Someone wants a music video for a song idea: the song written and sung, three matched vertical shots, joined and set to it. Use when: \"Make a music video for my synth-pop song idea\", \"I want a video for my song about summer nights\", \"Can you make a clip for my song with three matched shots\", \"music video\", \"video for my song\", \"clip for my song\". Runs the Imagera \"Music video\" template (a song, three frames, three eight-second clips, a join and a dub — about ten minutes)."
---

# Music video

Writes the song from your description, draws three matched vertical frames — wide, medium, close — moves each into a clip, joins them and lays the song under the cut.

## When to use

Someone wants a music video for a song idea: the song written and sung, three matched vertical shots, joined and set to it.

## How to run it

- Ask for the song — genre, mood and what it is about — and the look and lead: palette, place and who is on screen.
- The frames run wide, medium and close; each after the first is an edit of it, so the lead, palette and light hold, and each becomes an eight-second clip.
- The song is written from the description, not from a recording: never promise a cover, a named artist’s voice or their own track.
- For a single photo that moves over a music bed, offer the Reel from a photo skill (/photo-to-reel); for a song alone, offer the A song for someone template.
- Before handing it over, check the lead holds across the three clips and the cut plays in order under the song.

## Inputs

- `song` (text) — the song: genre, mood and what it is about
- `look` (text, optional) — the look and the lead: palette, place and who is on screen

## Steps

1. Music
2. Frames ×3
3. Clips ×3
4. Join and Dub

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "music-video"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/music-video` in Superagent, or open it from https://imagera.ai/skills.

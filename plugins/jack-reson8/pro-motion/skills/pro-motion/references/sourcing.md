# Finding references (what actually worked)

## Pipeline
0. **Compress every image before you look at it (hard rule, saves most of the token cost).** Long edge ≤ 800 px (contact sheets ≤ 1000 px), JPEG quality ≈ 60: `sips -Z 800 -s format jpeg -s formatOptions 60 in.png --out out.jpg` (or PIL `resize` + `quality=60`). Style, elements, design details, intent and the creative idea all survive at that size — and a "high-res" reference is usually a screenshot of a low-res source anyway. Never read the same image twice; write what you learned into the technique sheet instead. Read full resolution only when the user asks for it or when you are checking pixel-level craft of your own render.
1. **Find the official upload** with web search restricted to youtube.com:
   `youtube <title> official trailer OR opening OR "textless OP"` — textless OP/ED versions are best (no credits over the art).
2. **Download low-res and tile 24 frames** (no browser needed, no permission prompts):
   from `refs/`: `bash ../tools/ref_frames.sh <url> <name> 24` → `refs/<name>_sheet.jpg` (6×4 across the whole clip). Look at it with the image viewer.
3. For a moment you care about, grab dense frames: `$FF -ss 31 -t 3 -i name.mp4 -vf "fps=8,scale=-2:300,tile=8x3" -frames:v 1 dense.jpg` — transitions and timing only show up at 8+ fps.
4. Motion-design / UI motion: 60fps.design pages contain direct mp4 links; copy the .mp4 URL yourself and pass it to ref_frames.sh (the script no longer scrapes pages). Impractical (impractical.ai/launch-videos) has written breakdowns.
5. Category look: App Store screenshots of competitors; Behance project images can be listed from an already-open browser tab via `javascript_tool` (curl is blocked), then downloaded from the CDN.

## Blocked / painful
- The in-app browser asks the user to allow every new site and YouTube may be refused → prefer yt-dlp in the shell.
- Vimeo now requires login for yt-dlp; look for a YouTube mirror.
- YouTube can block yt-dlp with a bot check, and most brand Vimeo embeds are domain-locked (401). Don't spoof a referer; take the direct mp4 the brand serves on its own site or CDN (open the page source, look for `.mp4`) — in practice that is where most launch films come from.
- Behance/YouTube pages block curl; their CDNs (mir-s3-cdn-cf.behance.net, i.ytimg.com) don't.

## A wider pool for "strongly stylized" (pick across countries and media)
- **Japan:** Persona 5 opening (limited red/black/white, halftone, shard cuts, silhouettes, repeated framing), Promare / Trigger (flat polygon light, neon fields, no gradients), Masaaki Yuasa — Mind Game, Devilman Crybaby, Inu-Oh (elastic bodies, style switching, photo collage), Studio 4°C — Tekkonkinkreet (painted density), Mob Psycho 100 (painted-on-glass effects), Kill la Kill (type as staging).
- **US:** Spider-Verse films (halftone on 3D, misregistration, on-twos characters, comic captions), The Mitchells vs the Machines (doodle overlays on 3D), Puss in Boots: The Last Wish (painterly fight smears), Arcane (painted textures, ink flashes), Saul Bass titles, Catch Me If You Can titles (Kuntzel + Deygas cut-paper).
- **Europe:** Gobelins graduation shorts, Cartoon Saloon (Wolfwalkers: visible construction lines, woodcut textures), Klaus (2D with volumetric light), Yellow Submarine (psychedelic flat).
- **China:** 雾山五行 (ink action, brush speed), 中国奇谭 (style anthology: ink, paper-cut, stop motion).
- **Korea / other:** music-video animation, game cinematics (Hi-Fi Rush: everything on the beat), Gorillaz.
- **Motion design:** Spotify Wrapped, Figma Config openers (Relay), BUCK, Ordinary Folk, Giant Ant, Oddfellows.

## What to write down per reference (technique sheet)
palette rule · line (weight / none / boiling) · texture (halftone, grain, paper, brush) · shape language · depth trick · camera language · transition device · timing (ones / twos / holds / smears) · signature move nobody else has.

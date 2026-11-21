# Tested queries

Each no-key query below returned real output on 2026-11-03 (37 of 37 in our test run). Keyed queries are from official docs and were **not run**, because no provider keys were available. Sites change: if a query fails, try the next source rather than working around a block.

## B-roll

```bash
# Pexels, free key. 2-4 concrete words from the sentence it covers: subject + action, not the concept.
curl -H "Authorization: $PEXELS_API_KEY" 'https://api.pexels.com/videos/search?query=hands+typing+laptop&orientation=portrait&per_page=15'

# Mixkit, no key. Each item must say Free, not Restricted.
curl -sL -A 'Mozilla/5.0' 'https://mixkit.co/free-stock-video/ocean/' | grep -aoE 'https://assets\.mixkit\.co/videos/[0-9]+/[0-9]+-720\.mp4' | sort -u

# Coverr, no key. Premium ids are filtered here. Also drop user-ai-* if you do not want AI clips. API users must show a clickable logo.
curl -sL -A 'Mozilla/5.0' 'https://coverr.co/s?q=ocean' | grep -aoE 'https://cdn\.coverr\.co/videos/coverr-[a-z0-9-]+/720p\.mp4' | grep -v premium | sort -u
```

## Real-world and archival

```bash
# Wikimedia Commons. LicenseShortName must be CC0, PD or CC BY.
curl -sG 'https://commons.wikimedia.org/w/api.php' --data-urlencode 'gsrsearch=ocean filetype:video' -d 'action=query&generator=search&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|size|extmetadata&iiextmetadatafilter=LicenseShortName|Artist&format=json'

# NASA. Credit NASA, imply no endorsement, check the item for third-party credit.
curl -s 'https://images-api.nasa.gov/search?q=ocean&media_type=video'

# Internet Archive. Never accept an item without licenseurl.
curl -sG 'https://archive.org/advancedsearch.php' --data-urlencode 'q=ocean AND mediatype:movies AND licenseurl:*publicdomain*' -d 'fl[]=identifier&fl[]=title&fl[]=licenseurl&rows=20&output=json'
```

## Music

```bash
# Incompetech: the full catalog is one JSON, so you can filter by tempo first. Needs the exact credit line, or a paid license for ads.
curl -s 'https://incompetech.com/music/royalty-free/pieces.json' | python3 -c "import json,sys;print([(p['title'],p['bpm'],p['length']) for p in json.load(sys.stdin) if 'Uplifting' in (p.get('feel') or '') and str(p.get('bpm') or '').isdigit() and 90<=int(p['bpm'])<=130][:10])"

# Mixkit, no credit.
curl -sL -A 'Mozilla/5.0' 'https://mixkit.co/free-stock-music/ambient/' | grep -aoE 'https://assets\.mixkit\.co/music/[0-9]+/[0-9]+\.mp3' | sort -u
```

Epidemic Sound's free API plan has "no commercial license", so it needs a subscription. FMA: a sampled track was CC BY-NC-SA and downloads need a login, so skip it. Generated: varg `mureka_9_5`, instrumental, about 25 credits (check `estimate_cost`).

## Sound effects

```bash
# Freesound, filtered to CC0. 2,339 of 4,227 whooshes were CC0.
curl -sL -A 'Mozilla/5.0' 'https://freesound.org/search/?q=whoosh&f=license%3A%22Creative+Commons+0%22' | grep -aoE 'https://cdn\.freesound\.org/previews/[0-9]+/[0-9_]+-lq\.mp3' | sort -u | sed 's/-lq/-hq/'

# Mixkit.
curl -sL -A 'Mozilla/5.0' 'https://mixkit.co/free-sound-effects/whoosh/' | grep -aoE 'https://assets\.mixkit\.co/active_storage/sfx/[0-9]+/[0-9]+-preview\.mp3' | sort -u

# Freesound with a free key: license filter, with durations.
curl "https://freesound.org/apiv2/search/?query=whoosh&filter=license:%22Creative%20Commons%200%22&fields=id,name,duration,license,username,previews&token=$FREESOUND_API_KEY"
```

## Motion

```bash
# HyperFrames registry: 448 items. Apache-2.0.
curl -s 'https://hyperframes.heygen.com/_llms/catalog/catalog.txt' | grep -i 'chart'
curl -s 'https://hyperframes.heygen.com/_llms/catalog/catalog.txt' | grep -i 'lower third'
curl -s 'https://hyperframes.heygen.com/_llms/catalog/catalog.txt' | grep -i 'transition'
npx hyperframes add lower-third-bild

# Remotion.
npx remotion-bits find 'fade in' --limit 1 --json

# LottieFiles: keyless GraphQL, returns direct JSON URLs. The official MCP creates motion and is not library search.
curl -s -X POST -H 'Content-Type: application/json' -d '{"query":"query { searchPublicAnimations(query:\"checkmark\", first:10) { totalCount edges { node { name jsonUrl url downloads } } } }"}' 'https://graphql.lottiefiles.com/2022-08'
```

Web component libraries (React Bits, Magic UI, 21st.dev) run in real time, so re-time them to the frame or they break on render. Prefer parts built for rendering.

## References (study only)

```bash
# Refs: free MCP search, no key. Launch-heavy: 84 hits for "founder launch film", 8 for "talking head podcast clip".
curl -s -X POST -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_videos","arguments":{"query":"founder launch film"}}}' https://refs.video/mcp

# Measure real cuts locally.
scenedetect -i reference.mp4 detect-adaptive list-scenes

# FILMGRAB: search by film title. Concept searches fail ("interrogation" returned nothing).
curl -s 'https://film-grab.com/wp-json/wp/v2/posts?search=blade&per_page=5&_fields=title,link'
```

## Fonts, HDRIs, logos, icons, LUTs

```bash
curl -s 'https://api.fontsource.org/v1/fonts?subsets=latin&license=OFL-1.1'
curl -s -A 'Mozilla/5.0' 'https://fonts.googleapis.com/css2?family=Inter:wght@800' | grep -oE 'https://[^)]+'
curl -s --compressed 'https://api.fontshare.com/v2/fonts'

# Poly Haven: CC0. Use a unique User-Agent. Take 2K first (a sample was 6.2 MB).
curl -s -H 'User-Agent: your-app/1.0' 'https://api.polyhaven.com/assets?t=hdris&categories=studio'
curl -s -H 'User-Agent: your-app/1.0' https://api.polyhaven.com/files/ID

curl -s 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/stripe.svg'
curl -s 'https://api.svgl.app/?search=stripe'

curl -s 'https://api.iconify.design/search?query=rocket&limit=10'
curl -s https://api.iconify.design/lucide/rocket.svg
curl -s https://api.iconify.design/collections     # read the set's license here

ffmpeg -i in.mp4 -vf lut3d=look.cube out.mp4
ffmpeg -i in.mp4 -i clut.png -filter_complex '[0:v][1:v]haldclut' out.mp4
```

Self-host a font and wait for it to load before rendering. Never read a `.cube` file into context: a 33-point LUT is about 36k lines.

## Learning why a cut works

```bash
curl -s https://raw.githubusercontent.com/nateherkai/herk-edit-kit/main/docs/EDITING-PLAYBOOK.md
yt-dlp --skip-download --write-subs --sub-langs en --sub-format vtt 'https://www.youtube.com/watch?v=3Q3eITC01Fg'    # Every Frame a Painting
```

Contra Labs publishes real editors' reasoning in Premiere under CC BY 4.0 (234 steps). Shot-detection datasets such as TransNet are for training, not for an edit.

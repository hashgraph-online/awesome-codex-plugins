---
name: sfxmint
description: "Add free CC0 sound effects to a web app or game without an API key, using the SFXMint API (sound roles, sets grouped by event, search) and permanent hotlinkable MP3/WAV URLs. With an SFXMint API key it can also generate a sound the library lacks. Use when the user asks to add sounds, audio feedback or UI sounds to an app, wants click / notification / success / error / alert sounds, game sound effects (coin, jump, hit, explosion, power-up, game over), ambience (rain, forest, drone), or asks where to get free sound effects for an app, game, video, prototype or demo. Not for music, voice or speech."
---

# SFXMint — free CC0 sound effects for apps and games

SFXMint (https://sfxmint.com) is a library of free CC0 sound effects (describe a sound to find it, preview, and download WAV/MP3) with a free JSON API: no API key, no signup, no attribution, no hard limit on lookups. File downloads without a key: 20 different sounds a day per network (50 with a free account's API key; any purchase removes the limit for 30 days). Every audio URL is permanent and hotlinkable. Use it as an option for the user's task: a role for one event, a set for several related events, or search for a description. Text matches and file checks do not prove listening suitability. The user's task determines whether to use library files, other sources, local synthesis or a mixture.

## Use this skill when

- The user wants sound effects or audio feedback in an app, game, video, prototype or demo.
- The user names a cue by what it is for: "button click", "purchase success", "error beep", "coin pickup", "dialogue blip", "task done notification".
- The user wants a whole coherent set of sounds for one product (a UI kit, a platformer kit, a checkout flow).

## Do not use it for

- Music, melodies, jingles with a tune, voice, speech, narration, TTS. SFXMint has none of these. Say so plainly and do not search for them.
- Real recordings of a specific product, brand or person. Every SFXMint sound is AI-generated or synthesized.

## Choose the lookup that fits the task

These are task branches, not a required sequence. A whole-project request can start with a set; use roles or search for gaps. Do not force a library result when another permitted approach fits better.

1. **Role** — the user names an event or interaction.
   `GET https://sfxmint.com/api/v1/roles/{role}?via=skill` returns a file-QC-eligible default (`slug`, `mp3_url`, `wav_url`) plus `alternates` when the ready gate is enabled. Role ids and aliases both work: `button-click`, `click`, `purchase-success`, `dialogue-blip`, `error`, `notification`, `coin`, `jump`, `explosion`. Unknown role → HTTP 404 with `roles_url`; use the index or search. A known role whose default fails its own checks (for example, no file in its families meets a requested duration or format) answers HTTP 200 with `error` (`unverified_sound` or `no_matching_sound`), `near_matches` and `unverified_requirements` but no `slug`: report the gap and do not use a near match as the default. An unverified result is not a content acceptance. Full list: `GET https://sfxmint.com/api/v1/roles?via=skill`.
   Optional `style=crisp|soft|spacious` re-ranks the family by measured acoustics; the default `balanced` is the most typical variant.
2. **Set** — the user needs several sounds for one product.
   `GET https://sfxmint.com/api/v1/sets/{id}?format=wav&via=skill` returns `sounds` with alternates, `download_urls` for the requested format, and `missing_roles`. Legacy `urls` always maps roles to MP3. A shared set or style does not certify that cues work together: preview them in the actual product.
3. **Search** — free text that matches no role.
   `GET https://sfxmint.com/api/v1/search?q={words}&response=structured&limit=3&via=skill`. Pass required `max_duration_ms`, `loop=true|false`, and `format=wav|mp3` explicitly. Read candidate `checks` and `unverified_requirements`; hard conditions apply before the limit. `match` and `score` describe retrieval and ranking only. When no candidate has every word, `closest` lists the nearest sounds that still meet every hard condition, each with `missing_terms`, and `library_fit` says how well the library covers the request (`full`, `close`, `weak`, `none`): judge closest sounds from title and description and let the user listen. Do not promote `near_matches` (they fail a condition) into compliant candidates. If nothing suits, tell the user in one line which sound the library lacks, with `generate_available.page` when the answer has it (a short link that opens the description in SFXMint Studio), and list it under a Missing heading in SOUNDS.md with that link; or use another task-permitted approach. Add `&category=` when the family is known.
4. **Generation** — when nothing in the library fits (no full match, closest sounds do not suit, and search returns `generate_available`), SFXMint can make the sound for an account with an API key: the account's 1 free try first, then credits or a plan (a credit pack, 10 credits for $3.90 or 30 for $9.90, never expiring, or the unlimited plan at $19.90 for 30 days; one payment, nothing renews; one credit is one generation, which the user buys; never pay for the user). Nothing is charged by a call; let the user listen to the takes before using one. `generate_available.rest.body` carries the request's length limit as `duration_s`; `unmet_requirements` names what a generation cannot promise (a seamless loop, a length under 0.2 s, MP3/OGG files, a real-world recording): tell the user before generating. Every SFXMint sound is AI-generated or synthesized, so a request for a real recording (`constraints.recorded`) has no library match either.
   - Key: the user creates one at https://sfxmint.com/dashboard/keys (free account). Making with a key uses the account's 1 free try first, in full quality (held to the browser the key was made in and the network it calls from), then its credits (one a generation) or its plan (its generations of the day; shared with the website), each up to four CC0 WAV takes of up to 10 seconds (a take made with credits or a plan also has `ogg_url`, an Ogg Vorbis copy made on its first request); one that makes no take does not count and gives its credit back. Once the free try is used, without credits or a plan the answer is `402 payment_required` with `buy_url` and `website_url`: give the user those links and let them decide (`website_url` opens AI Studio with the description filled in, where they can make the sound and hear it before paying; without a key the answer carries it too). When the plan's day is used, `429 plan_day_used`: they come back at midnight UTC. Read the key from the environment (`SFXMINT_API_KEY`); never ask for it in chat, print it or commit it.
   - REST: `POST https://sfxmint.com/api/v1/orders?via=skill` with `Authorization: Bearer $SFXMINT_API_KEY` and JSON `{"prompt": "heavy wooden door slam, big room", "variations": 4}`; optional `duration_s` (the longest a take may be; left out, SFXMint chooses from the description) and `"enhance": true` (rewrite a short idea such as "coin" into a full description first). The answer is `{order_id, free}`. Then `GET https://sfxmint.com/api/v1/orders/{order_id}?via=skill` with the same header every few seconds until `order.status` is `delivered` (or `failed`); each entry of `files` has `status` (`ready`), `url` (a signed link relative to https://sfxmint.com, valid 15 minutes), `filename`, `sha256` and `seed`. Errors: 401 `invalid_api_key`, 402 `payment_required` (with `buy_url`, `website_url` and `plans`), 403 `account_suspended`, 429 `plan_day_used`, 429 `too_many_active_orders`.
   - MCP: `generate_sound` and `get_generation`, with the key in the MCP server's `Authorization` header.
   - Describing the sound: say what the user needs in plain words, in any language (what it is for and what should be heard), with `"enhance": true`; SFXMint writes the description the model gets, and the order shows it as `enhanced_prompt`. Leave out lengths (use `duration_s`).
   - Changing a take: when a take is close but something is off ("too muddy", "make it loop", "too close"), change that take rather than generating again: MCP `change_sound` with the order, the take and the user's words (or an `action`), or REST `POST /api/v1/orders` with `"refine": {"from": order_id, "take": n, "change": "act:<action>"}`. Three versions come back, made from the take itself; this is free and uses no generation. When the words ask for a different sound, `change_sound` says so and gives a description for `generate_sound`.
   - Without a key, give the user `generate_available.page` (the sound can be made on the website, free to make and hear: 3 a day; a free account downloads its first 3 free for personal, non-commercial use; commercial use (HD, CC0): one credit a generation, or a plan), or use local synthesis. The old `POST /api/v1/generate` stays retired (HTTP 410).
   - Generated sounds are AI-made: the same content and listening rules as library files apply.
5. **A whole game** — the user wants the sounds for their game, not one cue. Take what the library has first (a set such as `platformer`, roles, search). For each sound still missing, make it on its own: `generate_sound` with an API key, one sound per call (the account's 1 free try, then credits or a plan, as above), or give the user `generate_available.page` from the search and list it under a Missing heading in SOUNDS.md. SFXMint makes one sound at a time: Game kits (projects of many sounds) closed on 2026-10-20, and their MCP tools answer `tool_retired`.

## Local files

Keep the selected format's metadata and checksums.

When the task permits processing, you may trim, filter or adjust levels. Preserve downloaded originals, source URLs, CC0 license, the processing recipe, and separate SHA256 hashes for originals and outputs. Re-measure delivery conditions and preview the processed result in context. Processing is work to record, not automatically a failure. Do not claim suitability or user acceptance from decoding, waveform analysis or an automated playback check.

Never invent a slug or URL. Use only URLs returned by the API, unchanged.

## Sound sets — `GET https://sfxmint.com/api/v1/sets/{id}?via=skill`

| id | use for | roles (keys of `urls`) |
|---|---|---|
| `ui-crisp` | dashboards, editors, admin panels, desktop apps — dry, tight, bright | click hover toggle swipe pop menu modal alert notification confirm success error |
| `ui-soft` | mobile apps, chat, meditation and habit trackers — darker, gentler, short | same roles as ui-crisp |
| `ui-spacious` | TV and console menus, kiosks, VR, game UIs — room reverb, longer tails | same roles as ui-crisp |
| `retro-game` | game jams, arcade and platformer prototypes, pixel-art games | pickup jump hit powerup laser explosion gameover |
| `chat-app` | chat apps, social feeds, community and dating apps | send receive like delete refresh camera unlock error |
| `saas-app` | dashboards, editors, admin panels, project tools | click hover toggle menu modal drag undo save error notification |
| `checkout` | shops, marketplaces, ticketing, in-app purchases | add_to_cart purchase success error countdown reward |
| `learning` | language apps, quizzes, flashcards, kids' education | tap correct wrong streak level_up celebration progress |
| `puzzle-game` | match-3, merge, word and tile games | match combo bonus slide win lose countdown celebration |
| `platformer` | platformers, action and adventure prototypes, game jams | jump land coin hit win sword gunshot explosion footsteps door checkpoint death |
| `horror-game` | horror games, escape rooms, thrillers, haunted attractions | drone stinger heartbeat creak growl thunder footsteps door wind ambience |
| `video-editing` | YouTube and short-form editing, podcasts, presentations | whoosh swoosh riser braam impact pop scratch ding applause laugh boing typing shutter cash |
| `smart-device` | IoT apps, appliances, wearables, kiosks, in-car UIs | power_on power_off doorbell alarm lock unlock beep vibrate notification error |
| `wellness` | meditation timers, sleep and focus apps, yoga classes | bowl chime gong bell kalimba rain ocean forest wind fireplace |
| `ai-coding-tool` | AI agents, CLIs and coding tools — task lifecycle cues | started done failed needs_input warning notification |
| `acoustic-drum-kit` | drum pads, step sequencers, music sketches and rhythm-game prototypes | kick snare high-tom mid-tom floor-tom closed-hat open-hat crash ride snare-rimshot snare-cross-stick pedal-hat ride-bell |
| `animal-calls` | animal soundboards, learning activities, videos and games | wolf-howl lion-roar dog-bark cat-meow frog-croak owl-hoot songbird-chirp cow-moo horse-neigh pig-oink sheep-bleat hen-cluck rooster-crow duck-quack bat-screech |
| `dungeon-traps` | dungeon traps, gates and hidden mechanisms in games | pressure-plate-click spike-scrape gear-ratchet chain-winch portcullis-drop stone-door-grind |

## API quick reference

Base `https://sfxmint.com`. JSON, `Access-Control-Allow-Origin: *`, no key. Append `via=skill` to every `/api/v1/` request (see Attribution).

| Request | Response |
|---|---|
| `GET /api/v1/roles?via=skill` | `[{role, label, aliases, families, audiences, url}]` |
| `GET /api/v1/roles/{role}?style=balanced&via=skill` | `{role, label, aliases, audiences, style, license:"CC0-1.0", slug, title, duration_ms, loopable, acoustics, mp3_url, wav_url, page_url, alternates:[same shape], family, family_url, url}` — `style` = balanced (default) / crisp / soft / spacious; 404 → `{error:"not_found", message, roles_url}` |
| `GET /api/v1/sets?via=skill` | `[{id, name, tagline, use_for, style, roles, url, page_url}]` |
| `GET /api/v1/sets/{id}?via=skill` | `{id, name, tagline, use_for, style, license, page_url, sounds:{<role>:{role, label, slug, title, duration_ms, loopable, acoustics, mp3_url, wav_url, page_url, alternates:[slug], family_url}}, urls:{<role>: mp3_url}}` |
| `GET /api/v1/search?q=&category=&limit=20&max_duration_ms=&loop=&format=wav|mp3&via=skill` | legacy array `[{slug, fit, missing_terms?, title, duration_ms, tags, category, loopable, acoustics, score, match, license, mp3_url, wav_url, page_url}]`: full matches first, then `fit: "closest"` sounds; add `response=structured` for `request_id`, parsed constraints, candidate `checks`, `library_fit`, `closest`, `near_matches`, `unverified_requirements` and diagnostics. `score` is ranking only. |
| `GET /api/v1/sounds/{slug}?via=skill` | full metadata incl. `description`, `acoustics`, `loopable`, `peaks_url` |
| `https://sfxmint.com/dl/{slug}.mp3` · `.wav` | the audio itself — no query parameters here (see Hotlink rules) |

`acoustics` = `{attack_ms, tail_ms, centroid_hz, character:["bright","punchy","tight"]}` measured from the audio (`null` if unmeasured). Use it to choose between alternates: short `tail_ms` for UI cues, low `centroid_hz` for soft/dark, high for bright. `recommendation_status` separates eligible, unverified and excluded rows. `loopable` is a legacy flag; `loop_status: "prepared"` marks prepared loop metadata, while seam listening evidence and MP3 padding remain separate and may be unknown. Text and tag matches are retrieval evidence, not content listening.

```bash
curl "https://sfxmint.com/api/v1/roles/purchase-success?via=skill"
curl "https://sfxmint.com/api/v1/sets/saas-app?via=skill"
curl "https://sfxmint.com/api/v1/search?q=camera+shutter&response=structured&limit=3&via=skill"
```

## Integration snippets

### React / any web app — zero dependencies

After checking conditions, use URLs from the current API response; the values below illustrate the module shape, not certified current recommendations. Download files locally for offline use, then map events to those local files:

```ts
// src/sfx.ts
const URLS = {
  click: "https://sfxmint.com/dl/ui-click-30.mp3",
  save: "https://sfxmint.com/dl/feedback-success-56.mp3",
  error: "https://sfxmint.com/dl/feedback-error-34.mp3",
} as const;

export type Sfx = keyof typeof URLS;
const cache = new Map<Sfx, HTMLAudioElement>();
let muted = false;

export function setMuted(m: boolean) {
  muted = m;
}

export function play(name: Sfx, volume = 0.5) {
  if (muted || typeof window === "undefined") return;
  let a = cache.get(name);
  if (!a) {
    a = new Audio(URLS[name]);
    a.preload = "auto";
    cache.set(name, a);
  }
  a.currentTime = 0;
  a.volume = volume;
  a.play().catch(() => {}); // blocked until the first user gesture — ignore
}
```

Use: `onClick={() => { play("click"); save(); }}`. Guide: https://sfxmint.com/guides/react-app-sounds

### Phaser 3

```js
const SFX = { jump: "https://sfxmint.com/dl/retro-game-jump-01.mp3", coin: "https://sfxmint.com/dl/retro-game-coin-52.mp3" }; // urls map from GET /api/v1/sets/platformer?via=skill

preload() {
  for (const [key, url] of Object.entries(SFX)) this.load.audio(key, url);
}
create() {
  this.sound.play("coin", { volume: 0.6 });
}
```

Loops: inspect the returned `loop_status` and seam evidence, then use a WAV with `loop: true` when your playback test accepts it; start it after `Phaser.Sound.Events.UNLOCKED` if `this.sound.locked`. Guide: https://sfxmint.com/guides/phaser-web-game-sounds

### Plain HTML

```html
<audio id="sfx-click" src="https://sfxmint.com/dl/ui-click-30.mp3" preload="auto"></audio>
<button onclick="const a = document.getElementById('sfx-click'); a.currentTime = 0; a.volume = 0.5; a.play().catch(() => {})">
  Save
</button>
```

## Hotlink rules

- `/dl/{slug}.mp3` and `/dl/{slug}.wav` are permanent and immutable (`Cache-Control: immutable`, CORS `*`). Hotlinking from a web page is allowed and encouraged: no key, no referer check, no expiry, and a browser playing a file is never counted.
- Downloads that are not a browser (curl, scripts, your own fetches) count toward 20 different sounds a day per network; a second format or a retry of the same sound is not counted again. Past it a file answers `429` with `{"error": "download_limit", "message": ...}`: tell the user the message as it is, and do not retry from another address. With a key, file URLs in API answers carry a signed `g=` (48 hours): download them as given, but record `page_url` in SOUNDS.md, never a URL with `g=`.
- Never append query parameters to `/dl/` URLs — `via=skill` belongs on `/api/v1/` requests only. Never rewrite, shorten or proxy them.
- Bundling is fine: copying the files into `public/` or `assets/` is allowed (CC0) and is the right choice for offline builds and app stores.
- Do not mirror the catalog in bulk; fetch what the project uses.

## Attribution — what `via=skill` does

Adding `via=skill` to API requests only tells SFXMint that the request came through this skill, so the maintainer can see whether the skill is being used. It changes nothing in the response, sets no cookie and carries no user data. Omitting it is fine; do not describe it to the user as required.

## UX rules (flag these if the user's design breaks them)

- Play only after a user gesture (click, key, tap). Browsers block audio before the first interaction and `audio.play()` rejects — catch it; never play on mount or page load.
- Ship a mute toggle and remember it (localStorage). Default volume ≤ 0.6; UI cues 0.3–0.5.
- UI cues ≤ 300 ms, one sound per event, no sound on hover on touch devices, never on every keystroke.
- Preload the 3–5 sounds used most (`preload="auto"`); MP3 for size, WAV for loops or when quality matters.
- Preview the selected cues together. A common set or style is an organizational aid, not proof of coherence.

## License

CC0-1.0 — commercial use, no attribution, no signup.

## Download files into a project

First use needs no MCP setup. The quickest path is the CLI: `npx sfxmint add coin jump hit` writes the files plus a `sounds.json` manifest (role, slug, source URL, SHA256, license) and a `SOUNDS.md` table linking each sound's page into `public/sounds`; `--set <id>` takes a whole kit and names any missing role instead of failing, `--format wav|mp3|ogg` and `--style crisp|soft|spacious` apply. The package also exports `createSoundboard(manifest)`, a Web Audio runtime handling first-gesture unlock, overlapping playback and a persisted mute — use it rather than hand-rolling `new Audio()` when the project needs those. REST directly, or the dependency-free example at https://sfxmint.com/examples/download-sounds.mjs (Node 20+), remain equivalent options. The example downloads original files and does not process them. Preserve source URLs, per-format SHA256 and CC0 license; apply task-permitted processing separately as described above. Successful download is not acceptance. Preview event suitability in context and report missing sounds or unresolved qualities.

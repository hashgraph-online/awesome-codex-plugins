# Find references as one prompt

Paste this after `/goal` in Claude Code, or as a task in any agent with a shell and web access. It works with or without
the skill installed. Fill the first line. The agent cannot wait for you half-way, so it brings a board at the end and you
pick from it.

## Before you run it (optional, once)

```bash
npx skills add vargHQ/skills --skill find-references                         # the method and the search helper
claude mcp add --transport http refs https://refs.video/mcp                  # launch films and ads, free search
claude mcp add --transport http framethrower https://framethrower.ai/api/mcp # film frames, sign in with /mcp
```

Without them the agent still runs, and tells you which sources it could not reach.

## The prompt

```text
/goal Find references for this piece, then stop. Make nothing yet: [what it is, who it's for, platform and aspect ratio, length, brand, how it will be made: code / AI generation / both / filmed, 1-2 things I love, 1 thing I hate].

If the find-references skill is installed, follow it. Otherwise read it first:
https://github.com/vargHQ/skills/tree/main/find-references (references/ has one file per job; scripts/search.py searches 22 open sources with no key). Read SKILL.md and references/queries.md, then only the job files this piece needs. Run from my project folder and never write into the skill folder.

The idea: code owns facts in pixels and timing, records own who made it and the rights, you own literal yes/no checks and the shortlist, I own meaning and the pick. On generated work light matters most; on coded work type, motion and palette come first, and light only where a shot has it. Say which order you used. Some things only I can find: finding that out early and writing the link is a good result.

1. Write brief.json: idea (what the viewer should believe afterwards), feeling (two adjectives and one opposite), subject, world (place and decade), medium, audience, platform, method, constraints, loves, hates. Mark each said, assumed or asked. Ask me at most two questions, about what I hate and the method. Also ask me to attach real assets; that does not count. If my request is vague, show three contrasting territories as a 3 x 3 sheet and ask which row is nearest and which is worst.

2. Run the most obvious search. Say what it actually returned, name what repeats, and mark anything you expected but could not confirm. Write never.md from that search and from what I said I hate, as "Reject if <something a stranger can check on a frame, a clip or a text>", each with a positive wording for prompts, because negatives often backfire in generators. For ads, write Meta Ad Library and TikTok Creative Center links for me: the real picture of a category is there.

3. Write queries.md: one query pack per job this piece needs. Start from these floors, which are not limits: never (2 queries), light (6 across 3 sources), framing (4), people (4), location (3), texture (2-3), palette (2), type and graphics (2-3), motion (3), music (3). Stop a job when two queries in a row add nothing new. Add one query for the whole brief.
- Search in each source's own words. Keyword sources want 1-2 catalogue words. Delete mood words such as cinematic, moody, weathered.
- No library searches by ratio, shadow edge or Kelvin. Search for what is visible (one window, street lamp, candle), and keep numbers for the board.
- Never write "no X" in a semantic query. Filter afterwards. Skip caption queries if you have no semantic engine.
- Read the author field of good Wikimedia Commons hits: institutions upload whole collections. Ask a local archive by name.
- People: search the cataloguer's job word plus a place or decade. I want who the person really is, not the pose, place, expression or clothes: bones, what life has done to the body, work marks, how they carry themselves, one line of biography. Write that as an identity card in words.
- Palette: for the first board, extract from three named frames of candidates. After my pick, re-extract from the picked frame. One frame is fine for a painting or a still.
- Motion: search a format noun plus filters, pick by eye, then measure a clip you may process and write the spec from the numbers. Clips you may process come from Wikimedia Commons (filetype:video) or from me. Refs and whatships name films for me to watch: link them, do not process their clips. Open clips rarely match an ad, so for an ad I watch and supply the clip. On Refs, ai_made:false removes code-made films and ai_made:true mixes them with generated ones: for a coded piece use made_with (hyperframes, remotion).
- Type, for a coded piece: real use, then its class, then 3 fonts with a licence, then check what the piece needs (tabular figures, diacritics, weights), then I compare by eye. A genre of posters can be a Commons category. Lettered posters often name no typeface: classes only, and that is no failure.
- Music: search metadata in era and function words. You cannot hear, so I choose. Borrow tempo, instruments, era, arrangement. Never a melody, voice or artist's name. If there is a voiceover, write one casting line (age, region, texture, pace).
- Skip the first famous name that comes to mind. Take the same job from another field: candlelight from a painting, 9:16 composition from a hanging scroll.

4. Respect access. Never fetch Instagram or Reels, Film-Grab, ShotDeck, Shot Cafe, Eyecannndy, Pinterest, Google Images, Vimeo, Meta Ad Library, TikTok Creative Center, Ads of the World, Rate Your Music, Bandcamp pages, Tunefind or any site that blocks you, not even to check a link. 401, 403 and a bot wall are final: stop and write the link. A 429 means slow down: wait what Retry-After says, or 60 s, try once more, then stop using that source for this run. Do not spoof a user agent, sign in or download store previews. Write those searches into links.md for me with one line of reason each. Prefer open archives (Met, Rijksmuseum, Wikimedia Commons with category walks, Library of Congress, Internet Archive, Poly Haven, Flickr's public feed for leads, Are.na, MusicBrainz, ListenBrainz, Discogs' API), Refs, and FrameThrower if connected. Log every search, including failures, with its source, exact query, rank and count.

5. Fuse each job's results with reciprocal rank fusion (score = sum of 1 / (60 + rank)). Fusion does not cut by maker, and few items overlap across sources, so read the top of each query too. Open every candidate you keep. Write one line saying only what you can see. Delete what you could not open. Only then keep one pick per maker.

6. Prove who made it from records, before judging pixels. Label each HUMAN-PROVEN (a film title, a holding archive, or a named author with a date before 2022 and a body of work), LIKELY HUMAN, UNKNOWN (mood only, no measuring, no feeding) or AI (never board only). "No AI marker" and "detector says human" are never a pass. Tag each feed (mine, licensed for this use, CC0 or public domain, and no identifiable person), words or look. CC BY and BY-SA are words unless I clear them. A public-domain painting is legally feed, but start from words and feed it only after a test frame. Any identifiable real person is words, even in a public-domain photo. Never feed a stranger's face, name a real person in a prompt or use a real minor.

7. Measure what code can read: brightness on each side, contrast, colour by LAB from the real frame, cuts, holds, camera movement, tempo as a range. Then judge light only on generated work, and only if more than 3 candidates survive these gates. Coded work usually needs no judge: run one only on a generated still's light, or where more than 3 survive. For light prefer frames without people; I confirm the rest. For other jobs, gates, code and I are usually enough. Write a want card per job before seeing candidates, with values only and no praise words. Freeze only what I gave or the brief implies; anything you invent is marked assumed and cannot be core, so if you invent a side write direction: any and skip that question. My words outrank your card: a reference that fits the brief and fails an assumed value comes to me with a note. Strip title, maker, date and source from what the judge sees. Use images under random ids, never upscaled. Ask only yes/no questions about visible things, evidence with a location first, and cannot_tell allowed. Shuffle the order on each read, take 3 reads (2 on a small budget), and use a second model family if you have one. If the frame has no face, read the wall or floor nearest the source and the shadows of furniture. Compare the top few in pairs, both orders; a win counts only if it holds both ways. Never ask for lens, film stock, ratio, hex, beauty, or anything about a person's character, class or looks. Never ask "is this good?" and never score 1 to 10.

8. Build board.html: three candidates per job, grouped by job, shuffled, numbered after shuffling, no scores, with a keep or reject button and a note per candidate. With the skill installed, scripts/board.py builds it from board.json. Without it, write one self-contained page that does this. A look reference goes on as a link with no image. Say "these three pass the checks", never "the best". Picks go to "more like this". Rejects go to never.md with the reason.

9. Write refs.md: one job card per kept candidate with id, job, URL, maker, year, what I see, lends (one thing, with numbers from a measurement or record), must not copy, rights, provenance label, and the query and rank that found it. Mark picks when I pick. An image that truly does two jobs gets two cards. For coded work also write DESIGN.md (hex, type, grid, motion, each value labelled measured, record, by eye or assumed, with its source frame) and timing.md (beat, seconds, frames, what moves first, ease, source; beats are usually assumed, and labelled so). For generated work add one role line: "@Image1 defines the light only. Do not copy the room, the person or the colours."

Done when:
- brief.json, queries.md, search_log.jsonl, never.md, refs.md, links.md and board.html exist.
- never.md's tests come from a search you ran and from what I said I hate.
- Every kept reference was opened, and each card has one job, what not to copy, rights and provenance.
- For coded work, DESIGN.md and timing.md exist. If a generated person appears in an ad, you flagged possible disclosure (New York, EU Article 50(4)) for me to decide.
- Each job has three candidates on the board, or you say why not, and every light reading is either measured or marked for me to confirm.
- You list each source you could not reach, each silent zero, what you did not test and what you could not find.
- No person-only site was fetched, no real person's face was fed, and nothing was invented.
```

## Short prompts, one job at a time

Light:

```text
Find 3 light references for [the shot]. Want card: [direction, hardness, source, colour, shadow side], only what I gave you; write direction: any if I gave no side. Search what is visible, not the mood: Met and Rijksmuseum paintings by artist, Wikimedia Commons with -deepcat:"AI-generated images", Library of Congress, Poly Haven HDRIs, FrameThrower's lighting filter if connected. Write Film-Grab and ShotDeck searches into links.md for me; never open them. Open each hit. Read it in this order: shadow direction, nose and chin, catchlights, number of sources, falloff, shadow edge, colour, what could cause it. Measure each with frame_light.py. Say what you cannot know from a frame (lamp, ratio on set, true Kelvin). Give each one job and a do-not-copy line.
```

People:

```text
Write an identity card for [character] with three real reference people: who they are, not their pose, place, expression or clothes. Fields: bones, history on the body, work marks, carriage, one line of biography, never. Search the cataloguer's job word plus place or decade in the Library of Congress and Commons; delete adjectives such as weathered. A trait taken from real people enters the card only if three different people show it; one you invent for a fictional person is marked invented. Keep the words. Never feed these faces to a model or name anyone in a prompt. Never infer character from a face: who they are comes from the caption.
```

Never:

```text
Build a never board for [the piece]. Run the most obvious search, say what it returned and name what repeats. Add what I said I hate. Write 7 to 12 entries, each "Reject if <checkable by a stranger on a frame, a clip or a text>", then "Prompt as: <positive wording>", with where you saw it and the date. Tiers: what everyone in this category does, what this client hates or rejected. Do not name replacement fonts or colours, because they become the next tell.
```

Rank what I already have:

```text
Rank these references for [job]. Write a want card first, values only, marking anything you invented as assumed; an invented value cannot decide the ranking. Measure what code can read. Show a judge the images only, random ids, never upscaled, no titles. Ask yes/no questions about visible things, evidence with a location first, cannot_tell allowed, shuffled on each of 3 reads. Compare the top few in pairs, both orders; a win counts only if it holds both ways. Send me three, shuffled, without scores. Tell me where reads disagreed.
```

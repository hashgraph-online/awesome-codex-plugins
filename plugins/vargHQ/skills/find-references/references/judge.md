# Rank references with an LLM judge

Use this to get from 30 candidates to the 3 a person looks at. The judge is a filter: it saves the person from looking at
50 images, and it does not replace their eye. Every question asks whether something visible matches a want card. Beauty is
the person's job. For finished takes rather than references, use the `media-judge` skill.

Why it runs this way: a forced-choice judge picked the first of two identical images 10 of 10 and a polished copy 38 of 40,
and the checklist judge called both ties. That tests bias and stability, not accuracy: no person has labelled these images.
An invented value on the want card moved results more than any wording: one room went from 0 wins and 6 losses to 8 and 0
once the invented side was removed. All of it is in [`judge-evidence.md`](judge-evidence.md).

## Scope

- **Generated: judge Light by default, and only if more than 3 candidates survive the gates.** With 3 or fewer, the person
  sees them.
- **Coded: usually no judge.** Its answers come from records and code. Run one only on a generated still's light, or where
  more than 3 candidates of that still survive. In the cold run on a coded film, 24 reads for one still cut nobody.
- **Light on frames with people.** We have not run the demographic swap, so prefer frames without people, and a person
  confirms the rest. The questions stay on light and never on the person.
- **Other jobs:** gates, code and the person are usually enough. Their criteria tables below are a draft, off by default.
- **On a small budget:** Light only, 2 reads per family.
- **No API key.** `read` and `pairs` use the person's own logged-in `claude` or `codex` CLI. With neither CLI, an agent can
  loop `judge.py prompt` through its own subagents (see stage 5).

Cost: the full funnel is 150 to 240 calls for 20 to 50 candidates. Our checklist reads took 9 to 13 s each, and in the cold
run 46 reads took 1 min 47 s. By arithmetic on assumed tokens, not billed, N = 30 in one family costs about $0.05 on Haiku
5.5 and $1.10 on Sonnet 5.5.

## The protocol: six stages, code before the LLM

The assembly is `our proposal`. Set `S=<skill folder>/scripts` and run from the project folder.

### 1. Write a want card, and freeze it

One per job, in `want/<job>.txt`, before you see candidates. Values only, no praise words. Changing it makes a new version,
and reads are repeated.

```
job: light | direction: camera-left | hardness: hard | source: window or practical lamp | shadow side: near black
```

- Freeze only values the person gave or the brief implies.
- Anything you had to invent is marked `assumed`, and it cannot be core. If the side does not matter, or you invented it,
  write `direction: any`, and the judge skips L2.
- `prompt` and `read` skip a criterion if the card lacks its field, says `any` or `unknown`, or marks the value
  `(assumed)`. L2 needs `direction`, L3 needs `hardness`. Both also cut `shadow side` before the judge sees the card:
  code measures it.
- The person's words outrank your card. A reference that fits the brief and fails an assumed value goes to the person with
  a note.
- Field names matter, because they decide what is asked: `direction`, `hardness`, `shot size`, `material`.
- L3's examples assume hard light. If your card wants soft, add your own pass and fail examples, and test them.

### 2. Gates: no LLM verdict

| Gate | Owner | Pass condition |
|---|---|---|
| Opened | Code | File fetched, hash stored, size known. Search metadata alone fails |
| Provenance | Record + person | Named maker and date, a holding archive, or oldest copy before 30 Nov 2022. Unknown fails, except for Never |
| Source allowed | Code | Not on the person-only list (`sources.md`). Person-supplied frames pass |
| Rights | Record + person | `feed` only if yours, licensed for this use, CC0 or public domain, with no identifiable person. Otherwise `words` or `look`. This routes, it does not score |
| Identity safety | Person | Identifiable real people are never fed without consent or a licence. The LLM never names anyone |
| Duplicate | Code | Same image: keep the oldest, with the best provenance |

### 3. Code measures

Replace questions wherever you can: `frame_light.py` for brightness per side, contrast, p5, p95, clipping and colour;
the LAB command in `palette.md` for colours and shares; `motion_read.py` for cuts, holds and camera; `tesseract` for your
own text; `librosa` and `ebur128` for tempo and loudness. **Do not show code values to the judge**, because they become an
anchor. If code contradicts a judge's evidence, a person looks. Use code to abstain too: a face under the minimum size
returns cannot_tell with no call.

### 4. Blind the packet

```bash
python3 -I "$S/judge.py" blind refs/ blinded/
```

Long edge capped and never upscaled, same format, no metadata, random ids, bars trimmed. It walks job subfolders,
mirrors them (`blinded/light/`), records the job in the ledger (`blinded.ledger.json`), and warns and exits 1 if 0 files
were blinded. Title, maker, film, date, licence, query, rank and notes stay in the ledger. Mask burned-in captions and
logos, except for the Type job. Show nothing else: no other judge, no earlier score, no finder's opinion.

### 5. Checklist reads

One image per read, in a fresh context, with a new seed per read. Three reads per family, or two and a third on a split. Use
two or more families; for AI candidates, not the generator's family. If you have one, set `panel: single_family` in the
output and accept that errors are shared. Bypass any response cache on repeats, or three reads become one.

```bash
C="$S/../assets/criteria/light.json"
python3 -I "$S/judge.py" read blinded/light --family claude --want want/light.txt --criteria "$C" --reads 3 --out reads.jsonl
python3 -I "$S/judge.py" read blinded/light --family codex --want want/light.txt --criteria "$C" --reads 3 --out reads.jsonl
python3 -I "$S/judge.py" enforce reads.jsonl --criteria "$C" > enforced.jsonl
python3 -I "$S/judge.py" aggregate enforced.jsonl --criteria "$C" > shortlist.json
```

- `read` runs one fresh process per read from an empty temp folder and retries a failure once. It appends lines with
  family, judge, image, read and seed, skips reads already in the file, and stops a family at a usage limit. It also
  takes `--model M`, `--workers 4`, `--ids a,b` and `--dry-run`.
- `enforce` turns a verdict into cannot_tell, or no_clear_difference on a pair, when its location is off the grid or its
  evidence is empty, adjective-only or uses a forbidden word.
- `aggregate` takes the majority within a family and agreement across families, and lists any difference in `disagree` for a
  person. Per candidate it gives core passed, total passes, cannot_tell count and status, sorted by core, then passes, then
  fewest cannot_tell, with ties random under a fixed seed. No weights. Never average across scales.
- Checklist and pairs can disagree, as they did on rooms. Show the person both.
- Status `out`: a core criterion failed in every family. `person`: a core criterion is undecided, or families split pass
  against fail. `ok`: neither.

With neither CLI, print the text for each read and send it with the image to a fresh subagent:

```bash
python3 -I "$S/judge.py" prompt --want want/light.txt --criteria "$C" --image-id c_7522a586 --seed 41
```

Write each answer as one JSON line: `{"family", "judge", "image", "read", "seed", "order", "answers": [{"id",
"location", "evidence", "verdict"}]}`. `image` and `image_id` are both accepted everywhere. Copy `order` from what
`prompt` printed: `enforce` reads it to know which questions were asked. Then run `enforce` and `aggregate`.

### 6. Pairs on the short list, then a person

All pairs of the best 10 or fewer, in both orders. A win counts only if it holds both ways. `pairs` adds one sentinel per 20
reads, the same image twice, expecting `no_clear_difference`. The prompt depends on the job: only light says "do not compare
contrast", and it asks for direction only if the card sets one. Do not put polished and unpolished versions in one pool.

```bash
python3 -I "$S/judge.py" pairs blinded/light --ids c_7522a586,c_1f0934ab,c_88ab21cd --family claude --want want/light.txt --out pairs.jsonl
python3 -I "$S/judge.py" pairs blinded/light --ids c_7522a586,c_1f0934ab,c_88ab21cd --family codex --want want/light.txt --out pairs.jsonl
python3 -I "$S/judge.py" enforce pairs.jsonl > enforced_pairs.jsonl
python3 -I "$S/judge.py" rank enforced_pairs.jsonl > ranking.json
```

Then give the top 3 to the person on the board, shuffled, with no scores until they choose. Report "these three pass the
checks", never "the best". Show where the panel disagreed: that is output, not noise. Anything that fits the brief and ranks
low also goes to the person: in the cold run the image closest to the brief by eye lost 6 of 6 pairs.

Why three: in a simulation with an assumed noise model, not a measurement, this funnel had the true best at the top only
about 59 to 74% of the time. Top-1 is never safe.

## Criteria per job

★ = core: it applies only if the want card sets that value. A fail ends the candidate for that job, and cannot_tell sends it
to a person. Owners: Code, Record, LLM, Person. The image questions are in `assets/criteria/<job>.json`.

Forbidden words for any judge: good, beautiful, cinematic, professional, professional-looking, striking, attractive,
trustworthy, intelligent, wealthy, ethnicity. Evidence that uses them becomes cannot_tell and is logged.

### Light: on by default for generated work

Excluded: ratios, stops, "Rembrandt" as an unchecked label.

| ID | Owner | Question | Pass / fail | Cannot tell when |
|---|---|---|---|---|
| L1★ | LLM | Is there a visible source, or a cast shadow that shows where the main light comes from? | Window at frame left / flat even light | Crop hides all shadow areas |
| L2★ | LLM | Does the key come from the side on the want card? Needs `direction` | Lit cheek frame-left, or in a room: the wall or floor nearest the source brighter on frame-left, furniture shadows falling frame-right / other side, frontal, or no single direction | Too small or too dark to read |
| L3 | LLM | Name one shadow edge. Is it crisp or gradual, as asked? Needs `hardness` | Crisp line along nose, wall or floor / gradient, or no edge because the light is flat | Motion blur, compression, too dark |
| L4 | Code | Are p5, p95 and clipping inside the want range? | p5 ≤ 0.03, high clip ≤ 2% / p5 = 0.15 for near black | Under 512 px |
| L5 | LLM | Could something in this scene produce this light, and do shadows agree? | Street lamp visible / rim from nowhere, two directions | Tight close-up |
| L6★ | Person | Is this the light I meant? | Yes / no | Never |

### Other jobs: a draft, off by default

None of these has been run as a ranker. Test them before you rely on them. When you write your own, split "it does not
exist" (fail) from "I cannot see it" (cannot_tell), and move anything that rewards contrast or polish to code.

| ID | Owner | Question | Pass / fail | Cannot tell when |
|---|---|---|---|---|
| **Framing** | | Excluded from LLM: lens. Use records or a person | | |
| F1★ | LLM | State the crop points. Do they match the shot size? | Chest cut for medium close-up / full body | No person or object of known size |
| F2 | LLM | Using horizon or verticals, is the camera height as asked? | Horizon below waist for low / at eye level | No horizon or verticals |
| F3 | Code, else LLM | Is the subject's centre in the asked third? | Box centre right third / centred | No clear subject |
| F4 | LLM | Is the foreground as asked? | Soft door frame / flat against a wall | Subject fills frame |
| F5 | Code | Only if you use the frame itself: does the subject survive a crop to the target aspect? A sheet that lends its grid is exempt | Inside safe area at 9:16 / head cut | Never |
| **Texture** | | Excluded: naming a film stock from pixels | | |
| T1★ | LLM | Name the material from visible detail. Is it as asked? | Concrete with visible aggregate / smooth surface | Under 256 px |
| T2 | Code + LLM | On a native crop, does detail continue without smearing or repeating? | Weave across a fold / waxy pores, repeating tile | Upscaled, compressed |
| T3 | Code | Is noise in flat patches inside the asked range? | High noise / near zero | No flat patch |
| T4 | LLM | Does the surface catch light as asked? | No streak for matte / glossy | No directional light |
| **Palette** | | A hex list is always extracted by code | | |
| C1 | Code | Mean ΔE of pixels to the want hex, with `video-moodboard/scripts/palette.py check` (needs Pillow). Not core here | At or under 15 / above | Never |
| C2 | Code | Saturated hue clusters at or below the number asked? | One accent under 10% area / three hues | Black and white |
| C3 | Code | Dominant shares within ±10 points of the want? | 57/33/10 for 60/30/10 / 20/20/60 | Never |
| C4 | LLM | Is the accent on the named object? | Red only on umbrella / on a sign | Object not visible |
| C5 | LLM | Do colours belong to objects, not one overlay tint? | Skin, wall and sky differ / same teal in every shadow | Monochrome subject |
| **Type** | | | | |
| G1★ | Code | Your own set type or a take only, never a found sign. Does OCR read the exact letters? | ASCENT / ASCENST | Display type defeats OCR, then a person |
| G2★ | Record | Is the typeface named by a source? | Named on the archive page / a model's guess | Unknown allowed: keep classes only |
| G3 | LLM | Do case, serif or sans, width and weight match? | Condensed sans caps / serif lowercase | Under 24 px cap height |
| G4 | Code | Are cap height and position in range? | 3% of height, lower left / 12%, centred | No OCR box |
| G5 | Code | Is text contrast at or above the want? | 4.5:1 / 1.5:1 | Busy image, then a person |
| G6 | LLM + Record | Is it real use? | Photographed poster / template mockup | No context |
| **Motion** | | | | |
| M1 | Code | Cuts per minute in range? Core only if cutting is this reference's job | Want 20 to 30: 24 / 60 | Clip under 10 s |
| M2 | Code | Median and p90 shot length in range? | Median 2.5 s / 0.5 s | Too few shots |
| M3 | Code | Is the global movement the asked move? | Slow push / handheld shake | Heavy cuts in the window |
| M4 | LLM | With ordered frames, did the named element move first? | Title settles first / reverse | Default. Drop it if shuffled frames give the same answer |
| M5 | Code | Does the velocity curve show the asked ease? | Slow-out / linear | Overlapping elements |
| M6★ | Person | Does it move the way I meant? | Yes / no | Never |
| **People** | | The LLM never infers character from a face | | |
| H1★ | Record | Does the source say who this is: name or role, place, year? | "Pastry cook, Cologne, 1928" / "Confident businesswoman smiling" | No caption: unknown |
| H2 | LLM | Is this not arranged as a stock type? | Own surroundings, no commercial smile / arms crossed on white | Tight crop |
| H3 | LLM | Is the skin unretouched? Retouching only, not age, tone or body | Visible pores / airbrushed | Face under 256 px |
| H4★ | Person | Could this be my character in other clothes and another pose? One line: "This is someone who…" | Yes / no | Never |
| H5★ | Person | Identity gate cleared? | Licensed, or words only / fed without consent | Never |
| H6 | Person | Across the board, is the spread a choice or a default? | Stated choice / all one age and skin tone with no reason | Never |
| **Location** | | | | |
| O1 | Record | Are place and decade known from the source? Core only when the location must be a real, named place. Otherwise an unplaced reference stays as mood (`words`) | "Gary, Indiana, 1974" / "Urban street" | None: unknown |
| O2 | LLM | Does nothing visible contradict the decade? | 1970s cars only / LED billboard | No dated objects |
| O3 | LLM | Do weather and time of day match? | Wet pavement, low sun / dry noon | Indoors |
| O4 | LLM | Does signage fit the stated place? Do not guess the place | Right language / wrong script | No signage |
| O5 | LLM | Is it lived-in? | Patched wall / pristine, empty | Tight detail |
| **Music** | | Audio LLMs only after the noise test in `judge-evidence.md` | | |
| A1 | Code | Tempo in range, accepting half and double time? | 88 BPM for 85 to 95 / 140 | Rubato, low confidence |
| A2 | Code | Mode as asked? | Minor / major | Low-confidence key |
| A3 | Code | Loudness range as asked? | Wide, soft start / flat brickwall | Clip under 30 s |
| A4★ | Record | Are artist, year and credits on record, with a human maker named? | Named release / "AI background music" | Unknown |
| A5 | LLM on text | Do tags and notes match instruments and era? | "Upright bass, brushes, 1959" / mismatch | Sparse tags |
| A6★ | Person | Listen. Does it fit the picture? | Yes / no | Never |
| **Never** | | Provenance gate waived. AI images allowed as examples | | |
| N1★ | LLM on text | Is the test a yes/no a stranger can apply, on a frame, a clip or a text as fits? | "Teal shadows and orange skin on every face" / "Feels cheap" | Never |
| N2★ | LLM | Is the flaw visible in this example? Name the region | Yes, mid-centre / not visible | Too small |
| N3 | Code + LLM | Does the test say yes on this and no on every keeper? Run N2 or the code check on each keeper | Yes, then no / hits a keeper, rewrite | Keepers not chosen |
| N4 | Record | Where seen: URL and date | Stored / missing | Never |
| N5 | Code | Count in what the obvious search reached (keyless Refs reaches 48) | Many / one | No log |

A5 and N1 are text questions with no image, so they have no file in `assets/criteria/` and `judge.py read` does not run
them. Ask them with a plain prompt on the text. G1 fails on found signs for a reason: tesseract read "FABSASARIA TORIS TA"
for TABACARIA TURISTA in the cold run, and a found sign has no target letters anyway.

## Never leave these to an LLM

- **Final taste.** It belongs to a named person.
- **Who someone is, from their face:** character, class, intelligence, trust, health, ethnicity. Who they are comes
  from a caption or a person.
- **Identifying real people, likeness and consent.** Legal and ethical questions, not perceptual ones.
- **Rights and licences.** Facts from a record.
- **Whether something is AI, as a verdict.** At most a flag. Truth comes from dates and hosts.
- **Lens, camera movement, exact light values, film stock, exact hex,** until your own labels say otherwise. Evidence
  can move a criterion to the LLM. Assumption cannot.
- **The feel of motion and music.**
- **Cultural meaning:** gestures, sacred imagery, regional signage.
- **Grading its own family's output** with no other check, **validating itself,** or setting thresholds and criteria.

## Test it

Calibrating against one named person takes about 30 minutes, with `judge.py agree`. Bias tests use `judge.py analyze`. Steps
and bars are in [`judge-evidence.md`](judge-evidence.md). Do not ask a judge about a person (H2, H3) until you have run the
demographic swap there. Light on frames with people is under Scope.

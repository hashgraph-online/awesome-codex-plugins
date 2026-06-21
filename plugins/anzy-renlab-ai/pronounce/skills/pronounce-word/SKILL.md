---
name: pronounce-word
description: User asks how to pronounce an English word or project/product name ("how to pronounce X", "pronounce X", "X 怎么读", "X 怎么发音", "读一下 X"). Generate audio via the `say-it` CLI so the user actually HEARS the word — three times by default — instead of only writing IPA/syllable hints. The CLI consults a community-maintained pronunciation dictionary (kubectl → "koob-control", GIF → "jif", JSON → "jay-son", ...) and feeds an English-like respelling to the system TTS engine (macOS `say`, Linux `espeak-ng`, or Windows PowerShell) so project names come out the way engineers actually say them. Triggers on a single word or short phrase the user explicitly wants spoken.
---

# pronounce-word — speak the word out loud

**Purpose.** When the user asks how to pronounce an English word — and especially a project, product, or programmer-jargon name (`kubectl`, `nginx`, `Pydantic`, `LaTeX`, `JSON`, ...) — don't just respond in text. Play the audio so they can hear the *community* reading, then add a short text caption with the source.

## Trigger patterns

Auto-invoke ONLY when the user's message matches a **single-word or short-name** pronunciation request:

- English: `how to pronounce <X>`, `how do you pronounce <X>`, `pronounce <X>`, `how do you say <X>`, `what does <X> sound like`
- Chinese: `<X> 怎么读`, `<X> 怎么念`, `<X> 怎么发音`, `读一下 <X>`, `念一下 <X>`

`<X>` MUST be a single token: a word, project name, product name, acronym, or identifier — the kind of thing a developer would actually type into `say-it <X>`. The dictionary is keyed on single tokens, so multi-word input is spoken raw (not looked up); for a two-part name pick the head token (`say-it postgres`, not `say-it postgres database`).

**Do NOT trigger this skill when:**

- `<X>` is a sentence or paragraph the user wants narrated (e.g. `读一下这段` / `read this paragraph`). That's a TTS request, not a pronunciation lookup. Suggest `say "<sentence>"` instead, or just answer in text.
- The message is asking *about* pronunciation conceptually (e.g. `IPA 是什么` / `what is phonetic spelling`). Answer in text.
- `<X>` is non-English everyday vocabulary or a person's name unrelated to tech. The dictionary's editorial scope is tech-only — fall through to a text-only answer, or skip.

If the target token is ambiguous (multiple candidates in the message), ask which one before invoking.

## What to do

1. **Speak it 3 times via `say-it`.**

   ```bash
   say-it <word>
   ```

   The CLI looks the word up in the dictionary and, if found, sends the dictionary's English-like respelling (e.g. "koob control") to the TTS engine so the pronunciation is the *intended* community reading — not whatever the engine would have guessed from the spelling alone. (macOS `say` does not parse IPA / `[[inpt PHON]]` / SSML `<phoneme>` markup — it reads them literally — so the dictionary stores respellings that ride the engine's built-in letter-to-sound rules.) If the word isn't in the dictionary, the CLI speaks the raw spelling.

   Defaults: voice `Samantha` (General American), rate 130 wpm, 3 repetitions. This blocks until the audio finishes; the user hears it through the speakers.

2. **Reply with one short line of text alongside the audio.** Always include:

   - The IPA reading (GenAm).
   - The "syllabified" / respelling form (e.g. "KOOB-control").
   - **Source** of the pronunciation when the dictionary entry has one (creator interview, conference talk, official FAQ). Surface the URL — it's the project's headline feature.
   - For *contested* readings, mention the alternative and how to play it (`say-it --alt <word>`).

3. **Use `say-it --why <word>` to inspect** the dictionary entry (IPA, alternates, source, category, confidence) if you need to compose the caption — this is the canonical metadata for the reply.

## Examples

**Example 1 — creator-clarified word:**

User: `GIF 怎么读？`

Tool call:
```bash
say-it GIF
```

Reply:
> 🔊 /dʒɪf/ — "JIF". Per the creator Steve Wilhite at the [Webby Awards 2013](https://www.nytimes.com/2013/05/22/business/media/creator-of-the-gif-says-its-pronounced-jif.html). The alternate reading /ɡɪf/ is widespread too — try `say-it --alt GIF` to hear it.

**Example 2 — community-consensus product name:**

User: `how do you pronounce kubectl`

Tool call:
```bash
say-it kubectl
```

Reply:
> 🔊 /ˈkuːb kənˌtroʊl/ — "KOOB-control". Kelsey Hightower and most K8s maintainers say it this way ([talk](https://www.youtube.com/watch?v=2wgAIvXpJqU)). "Cube-cuddle" and letter-by-letter "K-U-B-E-C-T-L" both circulate as alternates.

**Example 3 — tech term not yet in the dictionary:**

User: `how do you pronounce containerd`

Tool call:
```bash
say-it containerd
```

Reply:
> 🔊 /kənˈteɪnər diː/ — "container-D" (the D is for "daemon"). Per the [containerd docs](https://containerd.io/).

## Useful flags

| Flag | Effect |
|------|--------|
| (none) | Primary × 3, then a spoken `"or: <alt>"` for each recorded alternate. |
| `--solo` | Primary × 3 only — silence the "or:" tail. |
| `--alt [N]` | Focus on the Nth alternate (default N=1) instead of the primary. |
| `--all` | Primary AND every alternate, each repeated, chained with "or:". |
| `--why` | Print the dict entry's IPA, source URL, category, confidence, notes (no audio). |
| `--json` | Print the entry as JSON (`in_dict`, alt arrays, source) — the cleanest form to parse when composing the caption (no audio). |
| `--md` | Print a ready-to-paste markdown card (no audio). |
| `--copy` | Copy the respelling to the clipboard after speaking. |
| `--no-dict` | Bypass the dictionary; let the TTS engine interpret the raw spelling. |
| `-n 5` | Repeat 5 times instead of 3. |
| `-r 110` | Slower rate (110 wpm; default is 130). |
| `-o /tmp/word.aiff` | Save to file instead of playing. |

**Why the default chains alternates.** Multi-reading words (`GIF`, `SQL`, `GUI`, `kubectl`, `char`, ...) carry useful context: the user should know there's debate. Chaining alternates audibly with `"or:"` makes that perceptible without forcing them to read the terminal. Use `--solo` when the user has already grasped the multi-reading status and just wants the primary again.

## Notes

- The CLI auto-detects a TTS backend: macOS `say`, Linux `espeak-ng`/`espeak`, or Windows PowerShell. macOS quality is the gold standard; the others are functional best-effort. If no backend is found, the CLI prints install hints, but the text-only flags (`--why`, `--json`, `--md`) still work — fall back to a text IPA + respelling reply in that case.
- If the user says "stop playing audio" or "just text", skip the speak step for the rest of the conversation.
- **Tech context only.** This skill targets project names, product names, programmer jargon, and acronyms (`kubectl`, `nginx`, `Pydantic`, `JSON`, `GIF`, `regex`, ...). For general English vocabulary the user wants spoken (rare), `say-it <word>` still works (falls through to raw TTS), but the dictionary's editorial scope is tech-only.
- The dictionary is American English (GenAm) only. UK/AU/etc. readings are explicitly out of scope.

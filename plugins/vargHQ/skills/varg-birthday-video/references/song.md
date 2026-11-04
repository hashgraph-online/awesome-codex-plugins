# A song that sings their name

The song is what people remember and replay: their name sung on the hook, their age, two or three true details.
It costs about 10 credits, so make two and keep the better one.

## Lyrics first

Write the lyrics yourself (or with the person) before you call a model, and put every line in the prompt. A
model left to invent lyrics forgets the name or sings it once.

```
{GENRE} birthday song, {BPM} BPM, {VOICE} lead vocal, {INSTRUMENTS}, friends sing along on the last chorus.
Original lyrics, sung clearly, the name {NAME} pronounced {PHONETIC}. Vocals start right away, no long intro.
Verse: {LINE about a true detail} / {LINE with the name} / {LINE} / {LINE}
Chorus: {LINE with the name and the age} / {LINE} / {LINE} / {NAME}, {NAME}, {CLOSING LINE}
Outro: cheers and a final strum.
```

- The name goes on the first line of the chorus and again on the last line. Give its sound (`MY-ah`, `sha-NEEK`)
  when the spelling could be read two ways.
- Two or three real details (the dog, the job, the city, the joke from last summer) make it theirs. Keep each
  line under 10 syllables so it can be sung at 110–120 BPM.
- Write your own words. Do not paste the traditional "Happy birthday to you" verse: Lyria's checker rejected
  every prompt that quoted it in our tests (2026-10-30). The melody's US copyright ended in 2016, but other
  models may still treat the lyric as a quote.
- Genres that suit it: acoustic pop with ukulele (warm), 2000s pop-punk (funny), Motown soul (parents, 50+),
  lo-fi bedroom pop (partner), stadium anthem with a crowd (the friend group), a lullaby (a baby's first year,
  sung to the child, never showing the child's real face in generated footage).

## Models on varg

| Model | Credits | What happened in our test (2026-10-30) |
|---|---|---|
| `eleven_music_v2_5` | 8 per 32 s | Sang every line and the name as written; exactly the length asked; the vocal came in at 9.9 s after a long intro. Took the name "Maya" that Lyria refused. |
| `lyria_3_5` | 10 | Sang every line and the name; ignored the length (66.7 s for 32 s asked, the verse repeated three times); rejected the name "Maya" (also an artist's name) and the traditional lyric. |
| `mureka_9_5` | ~25 | Instrumental only: the bed under a slideshow or a spoken message. |

Default: `eleven_music_v2_5` for a song with the name. Use `lyria_3_5` for a longer song (up to ~3 min) and
re-try with the name spelled phonetically if its checker refuses it.

```bash
curl -s -X POST https://api.varg.ai/v2/music -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"eleven_music_v2_5","duration":32,"prompt":"<the prompt above>"}'
# MCP: generate_music { prompt, duration: 32 }  (eleven_music_v2_5 is the default)
```

## Find where the name is sung

Transcribe the song (`whisper_large_v3`, 5 credits) and read the word timestamps. Start the video at the line
before the first sung name (`assemble.sh -s 9.5 …`) and cut on the chorus. Check that the name is spelled the
way the person spells it in the transcript; if the model sang a different name, make it again rather than
cutting around it.

```bash
curl -s -X POST https://api.varg.ai/v2/transcription -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"whisper_large_v3","audio_url":"SONG_URL"}'
```

## A lyric video from the song

The transcript's line timestamps are the cue sheet: one line on screen per sung line, the name bigger than the
rest. Render it with HyperFrames (`varg-music-video` and `hyperframes` have the lyric patterns) over the photos
or the generated clip, or burn simple captions with FFmpeg (`short-form-ffmpeg-cookbook`).

## Voice

- A cloned voice of a family member (a grandparent singing or speaking) only with that person's consent, on
  `eleven_v4` with their own sample. Never clone a celebrity's or a stranger's voice.
- A spoken message under the song: `eleven_v4`, 15–25 words, then duck the song by 8–10 dB under it.

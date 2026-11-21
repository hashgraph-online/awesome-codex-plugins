# Short hints: a few words for a tiny screen or the ear

Last checked: 2026-11-08. Verification: `docs-only`. The patterns come from building real-time hint features; the
prompt below is a starting point to test with your own model and data, not a measured result.

A running transcript does not fit a one or two-line display, a notification, or a voice in the ear. A hint does:
3 to 8 words that tell the wearer what matters right now.

## When to switch from captions to hints

| Situation | Show |
|---|---|
| Display with 4+ lines, wearer wants every word (deaf or hard-of-hearing users) | captions |
| 1 to 2 lines (Rokid custom view at large size, a notification, a watch) | hints, or the last final line cut to fit |
| Voice in the ear (audio-only glasses, earbuds) | hints, spoken, finals only |
| Translator | the translated final, shortened if it does not fit |
| Assistant (what to answer, what was asked) | the hint on screen, the full answer on a second page or the phone |

Captions for accessibility must not be summarised without the wearer's choice: offer hints as a mode, not a default.

## Budgets

| Target | Hint budget (as of 2026-11-08, estimates) |
|---|---|
| Even G2 | 1 to 2 lines of about 55 characters; the full answer can follow on swipe |
| Meta Ray-Ban Display Web App | 2 lines at 36 to 40 px, about 50 characters |
| Rokid custom view | 2 lines of about 18 characters at 28 sp (captions use 3 lines of about 22 at 24 sp) |
| Vuzix Z100 | 2 lines of about 36 characters (the text layout wraps near 42) |
| Phone notification mirrored to glasses | title of about 30 characters, body of about 60 |
| Voice | one sentence, under 2 seconds of speech (about 5 to 7 words) |

## Making a hint

**With a language model.** Run it on the final sentence (or the last question) plus a little context, ask for
structured output, and keep the model small and fast: the hint is useless if it arrives after the next sentence.

```text
You turn live speech into a hint for smart glasses.
Input: the last thing the other person said, and up to 3 earlier lines for context.
Return JSON: {"hint": string, "full": string}
- hint: at most 8 words and 45 characters, no filler, starts with the key word or verb,
  numbers as digits, names spelled as heard. If there is nothing worth showing, return "".
- full: one or two sentences with the detail, for a second page.
Language of the hint: {{hintLanguage}}.
```

- Validate the output length in code and cut at a word boundary if the model ignores the limit.
- Return an empty hint for small talk; showing nothing is better than noise.
- Stream the response and show `hint` as soon as its JSON field closes, or ask for the hint on the first line.
- Cache by sentence text: repeated questions are common in interviews and support calls.

**Without a model.** Extractive rules go a long way for captions on two lines:

- keep the last clause of the final sentence (split on `, ; : ? .` and conjunctions);
- drop fillers ("um", "you know", "I mean", "sort of") and repeated words;
- keep numbers, names, times and negations ("not", "never"), which carry the meaning;
- cut at a word boundary with an ellipsis.

## Numbers, times and names

- Decide the display format yourself. STT formatting options change the text: in our test Deepgram's `smart_format`
  turned "four o'clock" into "04:00". For a hint, "4:00" or "4 pm" reads faster.
- Keep digits as digits; spell out only when speaking ("4:00" spoken as "four o'clock" by the TTS).
- Names are where STT fails most. Add the session's known names (attendees, product names) to the provider's
  keyword or custom vocabulary option where it has one, and to the hint prompt.

## Voice in the ear

- **Speak finals and hints only**, never partials.
- **Do not talk over the wearer.** Wait until the wearer's VAD has been quiet for about 300 to 500 ms; if they start
  speaking, stop the utterance.
- **One in the queue.** If a new hint arrives while one is waiting, replace the waiting one; drop hints older than
  about 5 seconds.
- **Duck, do not pause,** other audio: Android `AudioFocusRequest` with `AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK` and usage
  `USAGE_ASSISTANT` or `USAGE_MEDIA`; iOS `AVAudioSession` category `.playback`, mode `.spokenAudio`, option
  `.duckOthers`.
- **Keep the microphone off Bluetooth** while speaking to Bluetooth glasses: opening the glasses' headset microphone
  switches the link to call audio and the speech gets the low quality of a phone call. Capture on the phone.
- **Meta Ray-Ban Display Web Apps** have `speechSynthesis` with one voice entry (`en-US`); the `lang` you set is passed
  to the native engine, but other locales "can vary" (Meta docs, 2026-11-08). Test every language.
- **Repeat on demand:** map the "repeat" gesture to speaking the last hint again. The example server answers `repeat`
  by re-sending the last final with `"repeat": true`, which audio targets speak and display targets do not duplicate.

## Showing hint and detail together

- Two-level layout: the hint large and bright, the question it answers small and dim above it, the full answer on a
  second page reached with a swipe or a tap.
- Clear old hints: a hint left on screen for minutes is read as current. Hide it after 20 to 30 seconds or when the
  topic changes, and keep it retrievable with "repeat".
- Mark machine-generated hints as such when the stakes are high (medical, legal, exams): the wearer must know the
  text is a suggestion, not a transcript.

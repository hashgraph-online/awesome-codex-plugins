# Voice & Multimodal Input

Most interfaces still assume one input channel (a pointer or a touchscreen) and one
output channel (a screen). Real usage is **multimodal**: people speak, type, tap,
glance, and switch devices mid-task. This reference treats input modality as a
first-class design concern—voice, touch, pointer, keyboard, and their combinations—
across the range of contexts a product runs in (phone, desktop, watch, TV, car).

> This file is about *input modality in general*. For conversational AI chat
> patterns specifically, see [14-ai-ux-patterns.md](14-ai-ux-patterns.md).
> The two overlap (a voice assistant is often LLM-backed) but the concerns here—
> discoverability, recognition feedback, modality fallback—apply to any voice or
> multimodal UI, AI or not.

---

## Voice as a First-Class Input

Voice fails most often not because recognition is bad, but because the UX around it
is an afterthought: a tiny mic icon, no feedback, no recovery. Treat voice like any
other primary input—discoverable, with clear state, confirmation, and error paths.

### Discoverability

- Don't bury voice behind an unlabeled mic glyph. Surface what it can do—suggested
  utterances ("Try: *set a timer for 10 minutes*"), an onboarding hint, or visible
  example commands.
- Voice's weakness is that **the command space is invisible**. Unlike a menu, users
  can't see their options. Show examples in context and after errors.
- Make the entry point obvious and reachable; size the affordance like a real button,
  not a 16px icon.

### Feedback: show every state

Users must always know whether the system is **idle, listening, processing, or
speaking**. Silence is ambiguous—did it hear me? is it broken?

```
States to make visible:
  ● Idle        — mic available, not capturing
  ◉ Listening   — actively capturing (waveform / pulsing animation)
  ⋯ Processing  — recognized, working on it
  ▸ Responding  — speaking / showing the result
  ✕ Error       — didn't catch that, with a way forward
```

- Show **live transcription** of what was heard so the user can catch misrecognition
  immediately ("I said *Karen* not *Aaron*").
- Pair audio output with a **visual transcript** of what the system said.

### Confirmation & error recovery

- **Confirm consequential actions** before executing ("Delete all photos from
  June—are you sure?"), but don't nag for trivial, reversible ones.
- Always show what was *recognized*, not just what was done, so errors are traceable.
- On failure, **offer a path forward**: re-prompt with an example, fall back to a
  visual chooser, or let the user edit the transcribed text—never a dead-end
  "Sorry, I didn't understand."
- **Support barge-in:** let users interrupt a long spoken response or prompt and
  start their next command without waiting for it to finish.

### A complete voice interaction, end to end

```
┌──────────────────────────────────────────────────────────┐
│  ● Tap to speak        (idle — clear, button-sized entry)  │
└──────────────────────────────────────────────────────────┘
        │ user taps / says wake word
        ▼
┌──────────────────────────────────────────────────────────┐
│  ◉ Listening…   ∿∿∿∿∿∿   (waveform reacts to voice)        │
│  "set a timer for ten minutes"   ← live transcript         │
└──────────────────────────────────────────────────────────┘
        │ endpoint detected (or user taps stop)
        ▼
┌──────────────────────────────────────────────────────────┐
│  ⋯ Working on it…                                          │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  ▸ Timer set for 10:00.   [⏸ Pause] [✕ Cancel]            │
│    (spoken aloud AND shown as text + a visual control)     │
└──────────────────────────────────────────────────────────┘
        │ low confidence? → don't guess silently:
        ▼
┌──────────────────────────────────────────────────────────┐
│  ✕ Did you mean a timer or an alarm?  [Timer] [Alarm]      │
│    (recover with a visual chooser, not a dead end)         │
└──────────────────────────────────────────────────────────┘
```

The result is **multimodal by default**: voice in, but the response is spoken,
shown as text, *and* leaves behind tappable controls so the user can continue by
whichever modality suits the moment.

### Activation: wake words vs. push-to-talk

- **Push-to-talk** (tap/hold to speak) is explicit, privacy-friendly, and reliable
  in noisy/public settings—prefer it for on-screen UIs and anything sensitive.
- **Wake words** ("Hey …") enable hands-free use but require always-listening, which
  raises privacy stakes—be explicit about on-device detection and show a clear
  live-mic indicator. Offer a way to disable the wake word entirely.
- Whichever you use, provide an **unambiguous stop**, and never begin acting on audio
  captured before the explicit trigger.

### Recognition feedback in code

```js
// Web Speech API — surface interim results so users see misrecognition live
const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
rec.interimResults = true;     // stream partial transcripts → live feedback
rec.lang = navigator.language; // honor the user's locale (see i18n reference)

rec.onstart  = () => setState('listening');   // show waveform / pulsing mic
rec.onresult = (e) => {
  const t = Array.from(e.results).map(r => r[0].transcript).join('');
  showTranscript(t);                          // user can catch "Aaron" vs "Karen"
};
rec.onerror  = (e) => recoverWithVisualFallback(e.error); // never a dead end
rec.onend    = () => setState('idle');        // always return to a known state
```

### Privacy is part of voice UX

- Make it unambiguous when the mic is **live** (persistent indicator, not just at start).
- Be explicit about whether audio is processed on-device or sent to a server, and
  whether it's retained. Don't capture ambient audio before an explicit trigger.
- Offer a visible, one-tap way to stop listening and to review/delete history.

---

## Voice Copy & Timing

Spoken language is linear and unscannable—a user can't skim a sentence they hear the
way they skim text. Voice copy and timing need their own discipline.

- **Be brief and front-load the answer.** Say the result first, details after
  ("Done—your timer's set for 10 minutes" not a 20-word preamble). Long spoken
  responses are painful; offer "want the details?" rather than dumping them.
- **Write for the ear.** Short sentences, no nested clauses, no jargon, no
  "click here" (there's nothing to click). Numbers and dates should be speakable.
- **One question at a time.** Don't ask "what, when, and where?" in one prompt—the
  user can only hold so much, and won't remember which to answer first.
- **Tune endpointing (silence timeout).** Cut off too early and you clip the user;
  wait too long and it feels broken. Allow for natural pauses and "thinking" silence,
  and let users signal they're done (a tap, or a stop word).
- **Set expectations on latency.** If processing will take more than ~1s, fill the
  gap with a clear "working on it" state (visual + optional audio cue), not silence.

```
❌ "I have located three results matching your query. The first result is…"
✅ "Found three. Top one: …  Want the others?"
```

---

## Multimodal Interaction

Multimodal means combining input channels so each does what it's best at—and letting
users move fluidly between them. The classic example: "put **that** [point] **there**
[point]" combines voice with pointing; neither alone is as fast.

### Combine voice + touch + pointer + keyboard

- Let modalities **complement**, not compete: voice for intent ("make this blue"),
  pointing/selection for the target.
- Don't force a single modality for a whole task. A user dictating a message should
  still be able to tap to fix one word instead of re-recording the sentence.
- Keep state shared across modalities—what you select by touch is the referent for
  the next voice command.

### Modality-appropriate design per context

The right primary modality depends on the device and the user's situation. Design
the *same capability* to suit each.

| Context | Constraints | Lean on |
|---------|-------------|---------|
| **Phone (on the go)** | One hand, glancing, noisy/quiet | Touch primary; voice for hands-busy |
| **Desktop** | Keyboard + precise pointer, focused | Keyboard shortcuts, pointer; voice optional |
| **Watch** | Tiny screen, brief glances | Voice + a few taps; minimal text entry |
| **TV / 10-foot UI** | Distance, D-pad/remote, no keyboard | Voice search >> on-screen keyboard; large focus targets |
| **Car** | Eyes/hands occupied, safety-critical | Voice primary; minimal-glance visuals, large touch zones |
| **Kiosk / public** | Shared, may be loud, privacy concerns | Touch primary; voice often inappropriate |

- **"Eyes-free / hands-free" contexts** (driving, cooking) make voice essential and
  visual-only UIs unusable—but a noisy or public context can make voice useless.
  Design for the situation, not the gadget.

### Graceful degradation when a modality is unavailable

- A mic may be denied, broken, muted, or socially inappropriate; a screen may be off;
  a keyboard may be absent. **Every core task must be completable in more than one way.**
- If voice is unavailable, the same action must be reachable by touch/pointer/keyboard,
  and vice versa. Detect capability and adapt the offered affordances; don't show a
  dead voice button when there's no mic permission.

---

## Cross-Device Continuity

Users start a task on one device and finish on another. Continuity is a multimodal
problem because the *input* changes across devices, not just the layout.

- **Handoff:** let a task move between devices with state intact (a started form, a
  half-written message, a playback position). Surface "continue on this device".
- **Responsive *input*, not just responsive *layout*:** a layout that reflows but
  still assumes hover, precise clicks, or a physical keyboard fails on touch/TV/voice.
  Adapt interactions (tap targets, focus order, voice entry) to the device's modality.
- **Context preservation:** carry selection, scroll position, undo history, and auth
  across the handoff so the user resumes rather than restarts.
- Keep identity and sync trustworthy—show what synced and when (see
  [12b-conflict-resolution-sync.md](12b-conflict-resolution-sync.md)).

---

## Accessibility Intersection

Voice and multimodal design overlap heavily with accessibility (see
[03-accessibility.md](03-accessibility.md)). They help some users and can
exclude others—design for both directions.

- **Voice as an assistive input:** for users with motor or dexterity impairments,
  voice can be the *primary* way to operate an interface. Voice control
  (Voice Control, Voice Access) needs every actionable element to be reliably named
  and reachable—the same semantics screen readers need.
- **Captions and visual alternatives for audio output:** anything the system *says*
  must also be available as text for Deaf and hard-of-hearing users, and for anyone
  in a sound-off context.
- **Never make voice the only path.** Speech-impaired users, people with strong
  accents, non-native speakers, and those in quiet/public/noisy settings need a
  non-voice route to the same outcome. Voice is an *addition*, not a replacement.
- Visual recognition feedback (live transcript) doubles as an accessibility feature.

---

## Spatial & AR (Emerging — Low Priority)

Spatial computing (headsets, AR overlays) adds gaze, hand-tracking, and 3D gesture
as input modalities. It's worth acknowledging but, for most products in 2026, **not
worth investing in yet**—the audience is small and patterns are unsettled. Keep two
durable principles in mind in case it becomes relevant:

- **Gaze ≠ intent.** Looking at something isn't selecting it; require a deliberate
  confirm (pinch, dwell-with-feedback, voice) to avoid the "Midas touch" problem.
- **Comfort and fatigue are UX constraints.** "Gorilla arm" from mid-air gestures and
  motion discomfort are real; favor small, low-effort gestures and respect reduced-motion.

Treat AR/spatial as a place to watch, not a default investment.

---

## Quick Checklist

- [ ] Voice entry is discoverable, with example commands (not just a bare mic icon)
- [ ] Idle / listening / processing / responding / error states are all visible
- [ ] Live transcription shows what was recognized
- [ ] Consequential voice actions are confirmed; trivial ones are not
- [ ] Errors offer a path forward (re-prompt, edit, or fall back to visual)
- [ ] Barge-in supported; mic-live state and privacy are clear
- [ ] Every core task is completable in ≥ 2 modalities (graceful degradation)
- [ ] Interactions—not just layout—adapt to device modality
- [ ] Spoken output has a text/caption equivalent
- [ ] Voice is never the only path to any outcome

---

## Common Mistakes

1. **Voice-only flows** — no fallback excludes speech-impaired, accented, non-native,
   and silent-context users.
2. **Hidden mic / no discoverability** — users can't find voice or guess its commands.
3. **No recognition feedback** — no live transcript, so misrecognition goes unnoticed.
4. **Ambiguous state** — user can't tell if the system is listening, thinking, or dead.
5. **Dead-end errors** — "Sorry, I didn't understand" with no way forward.
6. **No confirmation for destructive voice commands** — easy to delete by mishearing.
7. **Ignoring privacy** — unclear mic-live state, ambient capture, no history controls.
8. **Responsive layout, non-responsive input** — reflows but still assumes hover/keyboard.
9. **Audio-only output** — no captions/transcript for spoken responses.
10. **Forcing one modality per task** — can't tap to fix a single dictated word.

---

## Sources

- [Nielsen Norman Group: Voice Interfaces & Usability](https://www.nngroup.com/topic/voice-interaction/)
- [Google: Conversation Design Guidelines](https://developers.google.com/assistant/conversation-design/welcome)
- [Apple HIG: Siri & Voice](https://developer.apple.com/design/human-interface-guidelines/siri)
- [Apple HIG: Multimodal & Inputs](https://developer.apple.com/design/human-interface-guidelines/inputs)
- [W3C: Voice & Multimodal Interaction](https://www.w3.org/standards/) — standards activity
- [MDN: Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Microsoft: Multimodal interaction guidance](https://learn.microsoft.com/en-us/windows/apps/design/input/)
- [Bolt, R. (1980). "Put-That-There"](https://dl.acm.org/doi/10.1145/800250.807503) — foundational multimodal research

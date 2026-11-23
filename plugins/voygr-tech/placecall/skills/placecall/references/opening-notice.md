# PlaceCall: Opening notice: `disclosure`, `record_call`

Part of the PlaceCall skill ([`SKILL.md`](../SKILL.md)). Read it for changing or removing the opening notice, or turning recording off.

Send neither and the call opens with the default notice. In English (also for
`language: "auto"`) that is *"Hi, this is PlaceCall's AI assistant, calling
for a client on a recorded line."*; in Spanish, the same in Spanish. The other
eleven languages open with a fixed sentence (a digital assistant calling for a
client, on a recorded line). Two optional top-level fields change it.

`disclosure: {...}` builds the sentence from optional elements; unknown keys
are refused:

- `company_name` (≤60, default `PlaceCall`): must be your own business or one
  you are authorized to represent.
- `on_behalf_of` (≤80): "calling for {on_behalf_of}". Unset, it is your
  `parsed_slots.caller_display_name`, else `parsed_slots.name`, else "a
  client" with PlaceCall and no one with your own `company_name`. Must equal
  `caller_display_name` when both are sent.
- `purpose` (≤100): one clause, no `. ! ? ;`, spoken as sent.
- `mention_ai` (default `true`): "{company_name}'s AI assistant"; `false`
  drops it.
- `mention_recording`: defaults to the value of `record_call`.

`{"company_name": "Acme Dental", "purpose": "to confirm an appointment"}`
speaks *"Hi, this is Acme Dental's AI assistant, calling on a recorded line to
confirm an appointment."*

`disclosure: false` removes the opening notice: the agent opens with a short
greeting and your request, and says who is calling only when asked.

`record_call: false` means no audio and no recording clause. `recording_status`
reads `not_recorded` and the recording download answers
`404 {"status": "not_recorded"}`. `transcript_full` is still kept, and
`transcript_status` reads `final` as soon as the transcript exists.

Refused with `422` before anything is dialed or charged:

- `disclosure_unsupported_language`: a `disclosure` object on a call in
  another language than `en`, `es` or `auto` (`disclosure: false` works in
  every language).
- `recording_contradiction`: `mention_recording: true` with
  `record_call: false`, or, outside `en`/`es`, `record_call: false` without
  `disclosure: false`.
- `disclosure_too_long`: a sentence over 180 characters.
- `disclosure_invalid_text`: a text with brackets, a phone number, a web or
  email address, an emoji, or a claim about the recording or that the caller
  is a person.
- `principal_conflict`: `on_behalf_of` and `caller_display_name` naming two
  people.
- The validation `422`: `disclosure: true`, an unknown key, an element over
  its cap or a non-boolean flag.

`GET /calls/{id}` reports `disclosure_mode` (`standard` | `custom` |
`disabled`), `record_call` and `disclosure_text` (the sentence spoken). You
are responsible for the notice your calls give meeting the law that applies to
them.

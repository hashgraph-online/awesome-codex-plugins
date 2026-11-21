# Recommended Metadata Fields

The linter accepts partial metadata. Missing recommended fields become findings.

## Minimal JSON Shape

```json
{
  "title": "Song Title",
  "artist": "Artist Name",
  "release_date": "2026-06-01",
  "genre": "Alternative",
  "language": "en",
  "explicit": false,
  "description": "Short release description.",
  "contributors": [
    {
      "name": "Creator Name",
      "role": "writer, performer, producer",
      "master_percent": 100,
      "publishing_percent": 100,
      "confirmed": true
    }
  ],
  "rights": {
    "owner_claim": "Creator Name",
    "ownership_status": "confirmed",
    "contains_samples": "no",
    "sample_clearance_status": "not-needed",
    "cover_or_interpolation": "no",
    "release_history": "unreleased",
    "ai_involvement": "none",
    "human_authorship": ""
  },
  "suede": {
    "intended_services": ["rights-review", "mastering", "registry-readiness"],
    "wallet_address": "",
    "registry_status": "not-registered",
    "agent_commerce": false
  }
}
```

## Accepted Aliases

The linter should treat common aliases as equivalent when possible:

- `artist`, `artist_name`, `creator`, `creator_name`
- `track_title`, `song_title`, `title`, `project_title`
- `contributors`, `credits`, `collaborators`
- `splits`, `split_sheet`
- `rights`, `license`, `licenses`
- `contains_samples`, `samples`, `sample_status`
- `cover_or_interpolation`, `cover`, `interpolation`
- `ai_involvement`, `ai_disclosure`, `ai_generated`, `ai_use`
- `human_authorship`, `human_authorship_notes`, `human_contribution`

## AI Involvement

`ai_involvement` is `none` or a short list of the elements that used generative
AI: `vocals`, `instrumentation`, `composition`, `lyrics`, `artwork`,
`post-production`. When it is anything but `none`, `human_authorship` says what
a person wrote, performed, or arranged and where the evidence lives. Map these
to the AI-disclosure fields your distributor exposes at delivery.

## Confirmation Values

Use these normalized values in reports:

- `confirmed`
- `needs-confirmation`
- `unknown`
- `disputed`
- `not-applicable`

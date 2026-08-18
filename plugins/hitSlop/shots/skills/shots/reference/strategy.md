# Screenshot Strategy And ASO Copy

Build one concise strategy per app, then reuse it until the positioning changes.
Save durable findings with `apps.update_research`; save App Store listing copy
with `apps.update_listing`.

## Source Priority

1. User-provided positioning, audience, and brand constraints
2. Saved app context from `apps.get` or imported App Store listing data
3. Real app screenshots, local source files, navigation, and design tokens
4. Competitor listings, review language, and public gallery inspiration

Do not treat Shots plugin files as product context. They describe the tool, not
the user's app.

## Strategy Snapshot

Capture:

- one-line positioning
- target audience
- primary promise
- differentiators
- proof points that are actually supported
- voice: market words, phrases to use, phrases to avoid
- visual system: palette, typography, shape language, icon style, mood
- 6-8 benefits that could become screenshot panels

## App Experience Research

The App Experience section is the most important part of `researchMarkdown`
because it feeds screenshot prompt accuracy.

For published apps, inspect imported App Store screenshots and listing copy. For
unpublished apps, inspect local screens/components, navigation, theme files,
preview fixtures, and product screenshots.

Record:

```text
Branding and aesthetic:
- colors, typography, shape language, iconography, dark/light mode, distinctive visual signatures

Core problem and solution:
- user's pain in their words
- mechanism that solves it
- first "aha" moment
- regular-use success state

Critical user flows:
- flow name
- trigger
- key screens and steps
- marketing highlight

Critical screens:
- screen name
- top-to-bottom layout
- visible UI elements
- representative data
- interactive states
- emotional payload
- marketing value

User achievement:
- identity shift
- capability gained
- pain removed
```

Write screen descriptions concretely enough to become `device.screen` prompt
content. Prefer "Home dashboard with three active project cards, overdue badge,
and bottom tab bar" over "clean dashboard."

## Story Flow

Screenshots should form a Value -> Flow -> Trust narrative:

| Panel | Job |
| --- | --- |
| 1 | Strongest outcome or problem solved |
| 2 | Differentiator versus alternatives |
| 3 | Trust signal, only when supported |
| 4-6 | Core features in action, framed as problems solved |
| 7-8 | Newness, integrations, or advanced workflows |

Screenshots are ads, not docs. Each panel needs a caption-first promise and a
specific UI moment that proves it.

## Headline Strategy

Screenshot headlines are conversion hooks, not feature labels. Write the
smallest emotional promise that makes a browsing user stop and understand the
value.

Use:

- Outcome: "Sleep Better Tonight"
- Pain relief: "Never Miss a Receipt"
- Identity: "Feel Ready for Anything"
- Personal relevance: "See What Fits You"
- Transformation: "From Chaos to Clarity"
- Proof, only when supplied: "Trusted by 50K Teams"

Better rewrites:

| Weak | Better |
| --- | --- |
| AI Meal Planner | Know Dinner by 5 |
| Track Your Sleep | Wake Up Actually Rested |
| Budgeting Dashboard | Stop Wondering Where It Went |
| Color Analysis Scan | Find Your Best Colors |
| Job Auto Apply | Apply Before They Close |
| Habit Reminders | Make Progress Feel Automatic |
| Calendar Sync | See Your Day Clearly |
| Workout Library | Train Without Overthinking |

Quality bar:

- 3-6 words when possible
- meaningful at thumbnail size
- concrete enough to visualize
- written in customer language
- paired with real UI that proves the claim

Avoid:

- generic labels: "AI Dashboard", "Smart Tracking", "Advanced Analytics"
- empty hype: "Ultimate", "Revolutionary", "Game-Changing", "Best"
- unsupported claims: #1, top rated, awards, revenue, ranking, or user counts
- shame, insecurity exploitation, or stereotypes
- CTA headlines like "Download Now"

## Benefit Objects

Draft 6-8 benefits from the strategy:

```json
{
  "headline": "",
  "subtitle": "",
  "feature": "",
  "panelType": "ProductTour",
  "arcPosition": "hero | differentiator | trust | core | advanced",
  "screenToShow": "",
  "referenceAssets": ""
}
```

Rules:

- one promise per headline
- user benefit before feature name
- concrete verbs and outcomes
- category-native language
- no empty AI adjectives
- no unsupported proof

## Listing Copy

When asked for ASO or metadata, generate and save:

- title
- subtitle or short description
- description
- keywords
- title suggestions
- subtitle suggestions

If the user asks to update or translate "copy" without narrowing the fields,
include title, subtitle, keywords, and description by default. Ask only when the
user explicitly limits the requested fields.

Constraints:

- iOS title: 30 characters
- iOS subtitle: 30 characters
- iOS hidden keyword field: 100 characters, comma-separated, no spaces
- Android title: 30 characters
- Android short description: 80 characters
- Do not repeat keywords across title, subtitle, and keyword field.
- Use singular keyword forms where natural.
- Exclude app name, category name, "app", "free", and filler words from hidden
  keyword fields.
- Competitor names may be considered only for hidden keywords when the user
  explicitly wants aggressive ASO. Never use competitor names in visible copy or
  screenshot claims.

For non-primary locales, research locale-native search language instead of
direct-translating English keywords.

## Lightweight Keyword Process

Use this only when the user asks for keyword research:

1. Generate candidate terms from features, outcomes, pains, category language,
   competitor copy, and review phrases.
2. Estimate relevance, difficulty, and download intent when no keyword API is
   available; label those numbers as estimates.
3. Pick primary terms for title/subtitle and reserve terms for hidden keywords.
4. Produce three title options and three subtitle options with character counts.
5. Save the selected metadata with `apps.update_listing` and any research notes
   with `apps.update_research`.

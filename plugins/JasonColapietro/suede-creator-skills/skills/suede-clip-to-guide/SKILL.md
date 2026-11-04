---
name: suede-clip-to-guide
description: "Suede AI Clip to Guide Skills. Use when creating short-to-long content and asked to \"turn this clip into a guide funnel\": select a rights-supported moment, score fit, draft the bridge, approval bundle and measurement plan. NOT FOR: rendering (suede-video), social calendars (suede-social), full guide writing (suede-copy), paid ads (suede-ad-creative), or publication without exact-content and identity approval."
metadata:
  display-name: "Suede AI Clip to Guide Skills"
  version: 1.1.0
---

# Suede AI Clip to Guide Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Requires source video or timestamped transcript, rights evidence and guide URL/draft; Python 3 for the bundled package validator. Browser/account access is needed only for authorized platform verification or publication.

Build one evidence-backed path from a video moment to a deeper written asset.
Treat the clip as the attention layer and the guide as the authority layer. Do
not assume the pattern performs; test the bridge against the account baseline.

## Default Success Blueprint

Use this as the recommended pattern when the rights, source, claim, platform,
and approval gates pass:

```text
Useful guide with one promise
        ↓
Self-contained video moment
        ↓
Rights route + 8/10 moment score
        ↓
Clip hook + source credit + subtitles
        ↓
Post explains why the moment matters
        ↓
One explicit bridge to the guide
        ↓
Max Effort/Fleet: dual certainty gate
        ↓
Exact-content approval
        ↓
Public readback + clip-to-guide measurement
        ↓
Keep, revise, or stop from the observed result
```

Prefer this blueprint when:

- a guide already answers the natural next question created by the clip;
- the goal is deeper understanding, bookmarks, qualified replies, leads, or
  authority rather than raw views alone;
- the selected moment passes the 8/10 score and claim-support threshold;
- the rights route and current platform sequence are recorded;
- the account can observe at least one clip metric and one guide-transition or
  campaign metric.

Do not use it when:

- the guide is thin, unrelated, unpublished without a stable draft, or has no
  specific promise;
- the clip needs missing context, distorts the source, or exists only because
  it is popular;
- third-party reuse is blocked or the accountable fair-use decision is absent;
- the platform cannot preserve the source, clip, and guide bridge in a verified
  sequence;
- the idea is complete in the short post and the guide would add no depth.

For a first test, build three distinct packages only when three moments pass all
gates. Compare them with the account's recent comparable posts. Keep the pattern
only if the named guide-transition or campaign metric meets the decision rule;
revise one variable at a time when it does not.

## Non-Negotiable Gates

Apply these throughout the run. Resolve rights, source, and claims before
writing copy; resolve platform, certainty, and approval before a live action:

1. **Rights gate**: classify the video as owned, licensed, permission-recorded,
   native-repost-only, fair-use-review, or blocked. Public availability is not
   reuse permission.
2. **Source gate**: obtain the video, transcript or exact timestamps, guide
   draft or URL, target platform, intended account, and desired next action.
3. **Claim gate**: trace factual claims and quotations to the source. Label
   interpretations as interpretations.
4. **Platform gate**: inspect current official requirements and the live
   composer before promising that media, quote-posts, article cards, links, or
   replies can be combined.
5. **Approval gate**: do not publish, schedule, repost, upload, reply, or edit
   a live article until the user approves the exact media, copy, guide, account,
   and sequence.
6. **Certainty gate**: when a max-effort or worker-fleet controller runs this
   skill, require two distinct evidence checks before marking a package
   approved or published. A worker conclusion is not the second check.

When a blocking gate fails, stop the affected action and return:

```text
HALT, <one-line blocker>
Options:
1. <bounded resolution>
2. <bounded resolution>
3. <bounded resolution, if useful>
Waiting on: <specific evidence or approval>
```

Continue only on independent draft work that does not bypass the blocker.

### Rationalizations that precede a violation

Each excuse below shows up immediately before a gate gets skipped. When one
appears in your own reasoning or in the request, treat it as the signal to run
the gate, not to waive it.

| Excuse | Reality |
|---|---|
| "It's only 12 seconds." | Duration is not a rights basis. The clip still needs an owned, licensed, permission-recorded, native-repost, or accountable fair-use route. |
| "I credited the source." | Credit is attribution, not clearance. A blocked or unreviewed source stays blocked with a credit line attached. |
| "It's public, so it's reusable." | Public availability is not reuse permission. Classify the video before writing copy. |
| "The composer accepted it, so it published." | A prepared composer, scheduled item, or click is not a publication. Only the public permalink readback proves it. |
| "The worker already checked it." | Under Max Effort or Worker Fleet a worker conclusion is one check. The certainty gate needs a second, independent one. |
| "The guide is basically finished." | An unpublished guide with no stable draft or specific promise fails the fit test. Build the bridge to something that exists. |
| "The moment is getting traction, so ship it." | Popularity is not the score. A moment below 8/10, or below 2 on claim support or guide bridge, does not qualify. |

## Workflow

### 1. Define the funnel contract

Capture:

- campaign goal: article reads, bookmarks, qualified replies, profile visits,
  leads, or another named action;
- target platform and visible posting identity;
- video source URL or file, owner, transcript availability, and candidate
  timestamps;
- guide title, URL or draft, its promise, and current publication state;
- audience and one next action;
- whether the user wants a private draft, scheduled package, or live execution.

If product-marketing context exists in `.agents/product-marketing.md`,
`.claude/product-marketing.md`, or `product-marketing-context.md`, read it
before asking for information already covered there.

### 2. Choose a lawful video route

| Rights status | Allowed route |
|---|---|
| `original` | Cut and publish within the user's approved scope. |
| `licensed` | Follow the license terms and record the evidence. |
| `permission-recorded` | Follow the exact approved platforms, duration, credit, and edit scope. |
| `native-repost-only` | Use the platform's native quote, repost, stitch, duet, embed, or link path. Do not download and re-upload. Treat this as an operational sharing route, not legal clearance. |
| `fair-use-review` | Prepare a four-factor review for commentary, criticism, news reporting, teaching, scholarship, or research. Do not label the use fair or publish until the accountable owner records the decision. |
| `blocked` | Do not use the footage. Offer an original commentary clip, a permission request, or a source link instead. |

For any source that is not original, licensed, or permission-recorded, read
[references/third-party-video-rights.md](references/third-party-video-rights.md).
Do not infer fair use, ownership, or permission. Shortness, credit, a public
source, or added commentary alone does not settle fair use. Do not remove
watermarks, attribution, or provenance. Prefer a native repost with added
analysis or create an original camera or screen-recorded response that
summarizes the idea without copying the footage.

### 3. Establish the guide anchor

The long-form asset must have:

- one specific promise that the clip can honestly introduce;
- a title and stable draft or URL;
- enough depth to reward the transition from short to long;
- sources for material factual claims;
- one next action that matches the campaign goal.

**Make the guide findable, not only clickable.** Platform-hosted articles (X
Articles, LinkedIn articles) borrow the platform's audience; an owned guide on
the brand's domain is the asset that ranks and gets cited in AI answers after
the post stops circulating. When the guide is owned, check that it:

- opens with a two- or three-sentence direct answer to the question the clip
  raises, under a heading phrased as that question;
- embeds the clip (or the original source, when reuse is native-only) with a
  text transcript or a timestamped summary on the page;
- carries `Article` JSON-LD, plus `VideoObject` with name, description,
  thumbnailUrl, uploadDate, and duration when the video is hosted or embedded
  on the page, validated before publish;
- has a named author with a short bio, and links each factual claim to its
  primary source.

When the guide lives only on a platform, say so in the decision snapshot and
recommend an owned canonical copy. Route schema and indexing checks to
`suede-seo-audit` and AI answer visibility to `suede-ai-seo`.

If the guide does not exist, return a brief and route the full draft to
`suede-copy` and the portfolio decision to `suede-content-strategy`. Resume this
skill after the guide has a reviewable draft. Do not fabricate a live URL.

### 4. Score candidate moments

Score each candidate from 0 to 2 on five dimensions:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Opening clarity | Premise is missing | Premise arrives late | Premise is clear in 1–3 seconds |
| Standalone value | Needs surrounding context | Partly self-contained | Complete useful idea or story |
| Guide bridge | Unrelated | Adjacent | Naturally creates the next question the guide answers |
| Claim support | Unverifiable or misleading | Needs qualification | Directly supported and correctly framed |
| Audience fit | No named audience fit | Broad fit | Solves a named audience problem |

Select a moment only when it scores at least 8/10, claim support is 2, guide
bridge is 2, and the rights gate passes. If none qualify, return the scorecard
and request a better source instead of forcing a clip.

### 5. Build the package

Read [references/package-template.md](references/package-template.md) and
produce:

1. **Decision snapshot**: goal, audience, platform, identity, and chosen
   sequence.
2. **Source and rights record**: owner, source, evidence, transcript excerpt,
   permitted route, jurisdiction, and any four-factor review.
3. **Guide anchor**: exact title, promise, URL or draft state, and the question
   it answers after the clip.
4. **Clip brief**: in/out timestamps, target duration, exact opening, subtitle
   text, on-screen credit, ending bridge, and export owner.
5. **Funnel post**: exact text with four jobs:
   - hook the video moment;
   - explain why it matters;
   - bridge to the deeper guide;
   - give one specific next action.
6. **Publish sequence**: one of the verified patterns below.
7. **Measurement plan**: baseline, observation window, and decision rule.
8. **Certainty record**: execution mode, two check owners or processes,
   direct evidence, contradictions, and final verdict.
9. **Approval bundle**: exact media, post copy, guide, identity, and sequence.

Do not pad the post with generic setup, unsupported performance language, or
multiple competing calls to action.

### 6. Choose a verified sequence

Use one:

- **Anchor-first**: publish or verify the guide, then publish the clip-led post
  that references it.
- **Clip-first**: publish the clip, then place the guide in the platform's
  verified companion location, such as a first reply or supported link field.
- **Native-repost**: quote or repost the third-party source with original
  analysis and a guide bridge; do not re-upload the source media.
- **X native video plus owned Article card**: when the account owns an X
  Article and has a lawful basis to use the video as native media, publish a
  fresh post from the approved account with the exact approved copy, attach
  the video, and put the owned Article's status URL at the end so X renders the
  Article as the quoted card. Do not quote, repost, or inherit the third
  party's post, caption, replies, or engagement context; preserve source credit
  on the video. If the Quote composer accepts the video but leaves publishing
  disabled, use this fresh-post construction or report the blocker. Never
  substitute a quote of the third party's post. After publishing, confirm the
  live post shows both the native video and the Article card.

Do not assume a quote-post can also carry new media. Verify the current composer
and choose the smallest sequence that preserves the clip, guide, and source
credit.

### 7. Run the dual certainty gate when required

Record `execution_mode` as `standard`, `max-effort`, or `worker-fleet`. Standard
mode may record `certainty_status: not-required`. Max Effort and Worker Fleet
must run both checks and may not mark a package `approved` or `published` until
`certainty_status: proved`. Record one package version, timestamp, or content
hash so both checks evaluate the same unchanged artifact.

**Check 1: production proof**

- Reopen the video or transcript at the selected timestamps.
- Match the quotation, claim framing, rights evidence, moment score, guide
  promise, bridge, exact copy, identity, sequence, and one CTA to the package.
- Run the package validator for a saved artifact.
- In Fleet mode, the fleet worker's acceptance-criteria self-check may satisfy
  this check, but remains provisional.

**Check 2: independent proof**

- Inspect the source evidence and assembled package directly; do not review
  only Check 1's summary.
- Use a different failure lens, evidence source, or acceptance criterion and
  try to disprove the rights route, factual framing, guide fit, platform
  sequence, and approval readiness.
- In Max Effort with useful parallel work, keep the producer and adversarial
  reviewer separate. For one atomic Max Effort job, perform a fresh second pass
  after reloading the source evidence.
- In Fleet mode, the controller must perform this check and mark the worker
  output `accepted`, `rejected`, or `fix brief`. A second worker or repeated
  self-check does not replace controller review.

Use only:

- `PROVED`: both checks pass with direct evidence and every contradiction is
  resolved;
- `UNPROVED`: a check is incomplete, indirect, or disagrees with the other;
- `BLOCKED`: access, authority, rights, or platform state prevents a required
  check.

If either check is not `PROVED`, keep publication unapproved, use the halt
format, and name the smallest fix or evidence needed. The dual check raises
confidence; it does not guarantee truth, create legal clearance, or replace
the live readback. A material change to the media, timestamps, rights evidence,
guide, copy, identity, sequence, or CTA resets `certainty_status` to `pending`
and requires both checks again.

### 8. Require exact-content approval

Before a live action, show:

```text
Account:
Platform:
Media:
Source/rights status:
Guide title and URL:
Exact post text:
Publish sequence:
```

Approval is valid only for that bundle. If the media, copy, guide URL, account,
or sequence changes materially, show the changed bundle and obtain approval
again. Verify the visible identity immediately before acting and fail closed on
an account mismatch, login challenge, or ambiguous composer.

### 9. Verify completion

For a saved package, run:

```bash
python3 /path/to/suede-clip-to-guide/scripts/validate_package.py path/to/clip-to-guide-package.md
```

For a live run, also read back:

- the final public permalink;
- visible posting identity;
- rendered post text and media or native source reference;
- guide URL and publication state;
- timestamp and any platform warning.

Do not claim publication from a click alone. A complete live run needs the
public readback. A draft-only run is complete when the package validator passes
and the approval state is reported as `draft`.

## Measurement

Choose the smallest comparable window the account can support. Record:

- clip retention or completion where exposed;
- guide opens or link clicks where exposed;
- bookmarks, saves, qualified replies, and profile visits;
- the exact campaign action;
- a comparable recent baseline.

When the platform exposes compatible denominators, calculate:

```text
guide transition rate = verified guide opens / clip-post impressions
qualified action rate = named qualified actions / verified guide opens
```

If compatible denominators are unavailable, report the available counts
separately. Do not combine mismatched platform windows or call clicks article
reads.

Change one variable per next test: moment, opening, bridge, sequence, or CTA.
Do not report causal lift from an unpaired or tiny sample.

## Boundaries

- Do not download, clip, or re-upload third-party footage without a recorded
  rights basis or an accountable fair-use decision.
- Do not give legal clearance or label uncertain reuse as fair use.
- Do not invent transcripts, timestamps, permissions, URLs, performance,
  audience demand, or platform capabilities.
- Do not publish or schedule without exact-content approval and visible-identity
  verification.
- Do not alter a source quote to make the hook stronger.
- Do not describe the campaign as successful until current analytics support
  the named decision rule.
- Do not call a Max Effort or Fleet package certain, approved, or publishable
  when either required check is `UNPROVED` or `BLOCKED`.

## Routing

- Need full video editing, generation, captions, color, or exports -> use
  `suede-video`, then return here for the funnel package.
- Need a general platform plan, calendar, account audit, listening, or
  engagement program -> use `suede-social`.
- Need the long-form guide written -> use `suede-copy`; use
  `suede-content-strategy` for pillars and portfolio priority.
- Need paid variants -> use `suede-ad-creative`.
- Running many packages through parallel agents (for example an Agent Studio
  fleet) -> record `execution_mode: worker-fleet` and keep the controller's
  independent Check 2 here; the certainty record stays in this skill.
- From those skills, route a video-to-long-form bridge, moment score, rights
  route, exact approval bundle, and readback back to `suede-clip-to-guide`.

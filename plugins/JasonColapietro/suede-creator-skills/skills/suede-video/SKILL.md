---
name: suede-video
description: "Plan or produce marketing video with scripts, storyboards, shot and asset lists, consent-aware AI or avatar choices, programmatic rendering, edit decisions, pacing, export specs, and video-search metadata. Use when asked to \"turn this demo into a short video\" or build a repeatable production pipeline. NOT FOR: social calendars (use suede-social), clip-to-guide bridges (use suede-clip-to-guide), paid ad concepts (use suede-ad-creative), still images (use suede-image), or unapproved publishing."
metadata:
  display-name: "Suede AI Video Skills"
  version: 2.2.1
---

# Suede AI Video Skills

## Compatibility

Planning works from supplied media and product evidence. Rendering, generation, avatars, and frame inspection depend on discovered authorized tools; otherwise return the documented manual editor handoff.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

This skill turns an approved message and rights-cleared source material into
scripts, storyboards, generation plans, edit systems, and reusable production
pipelines. It keeps likeness, licensing, brand assets, render cost, and
publishing as explicit gates rather than assumptions.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Video Goal
- What type of video? (Product demo, explainer, testimonial, social clip, ad, tutorial)
- What's the target platform? (YouTube, TikTok/Reels/Shorts, website, ads, sales deck)
- What's the desired length?

### 2. Production Approach
- Do you need a human presenter? (AI avatar vs. voiceover vs. screen recording)
- Do you have existing footage or assets? (Screenshots, logos, product UI)
- Do you need generated footage? (AI-generated scenes, B-roll)
- Is this a one-off or a template for repeated use?

### 3. Technical Context
- What's your tech stack? (Node.js, Python, etc.)
- Do you have API keys for any video tools?
- Budget constraints? (Some tools charge per minute of video)

---

## Choosing Your Approach

Choose the production method from the job, available evidence, rights, and
currently callable tools:

| Approach | Candidate fit | Tools to evaluate | Use when |
|----------|---------------|-------------------|----------|
| **Programmatic** | Templated, data-driven, batch video | An installed HTML/CSS or React renderer | The format repeats and deterministic output matters |
| **AI generation** | Original footage from text/image prompts | Any currently authorized generation model | The scene cannot be filmed practically and output rights are verified |
| **AI avatars** | Approved presenter without filming | Any currently authorized avatar platform | Consent, likeness, voice, localization, and output rights are documented |
| **Editing/repurposing** | Cutting long-form into short clips | Any installed transcript or timeline editor | Source media and derivative-use rights are available |

---

## Programmatic Video

Programmatic video is a candidate for repeatable, templated, or data-driven
work; verify fit against the current stack, edit needs, cost, and review burden.

### HTML/CSS renderer candidate

Hyperframes, from HeyGen, may fit an HTML/CSS workflow. Docs:
[hyperframes.heygen.com](https://hyperframes.heygen.com/introduction). First
check whether it is installed.
If it is, read the installed version's documentation, inspect its license, and
confirm the renderer and export path. If it is not installed, use a
renderer-neutral handoff or request explicit installation authorization after
showing the current package source, version, lockfile impact, and cost. The
following commands must not run without that authorization:

```bash
npx hyperframes init my-video && cd my-video
npx hyperframes preview               # live preview
npx hyperframes render -o output.mp4  # render index.html
```

**Key concept:** A composition is plain HTML, CSS, and JS. Timing is declared in
the markup, and the renderer seeks a paused animation timeline frame by frame.
Confirm the current composition syntax and any programmatic render API in the
installed version's docs before writing code against it.

**Candidate fit:** Product announcements, changelogs, data-driven reports, and
approved personalized outreach videos. Verify determinism with a repeat-render
test instead of assuming it.

### React renderer candidate

Remotion may fit a React-based workflow. Docs:
[remotion.dev](https://www.remotion.dev/docs). It is source-available, not open
source, so check its license terms. Verify the installed or callable version,
current documentation, license, rendering path, and hosting cost. The
scaffold command may install packages or create files; run it only with explicit
authorization for that change, otherwise provide a renderer-neutral plan:

```bash
npx create-video@latest
```

**Key concept to verify:** a composition is a React component that reads the
current frame number and returns what is on screen; props drive content. Confirm
whether rendering is local or uses an authorized hosted renderer.

Read
[references/programmatic-renderers.md](references/programmatic-renderers.md)
when the repo already uses React, or when the choice between the HTML/CSS and
React paths has to be justified: it carries the React component sample and the
renderer selection table. Neither framework is the more powerful one. Both
render web pages to video in a headless browser; the difference is what the
team writes.

---

## AI Video Generation

Generate original footage from text or image prompts. Use for B-roll, hero visuals, and scenes you can't practically film.

### Model comparison

Discover currently callable and authorized models before recommending one. Read
current official documentation and run a bounded test on the actual account.
Compare:

| Criterion | Evidence to capture |
|-----------|---------------------|
| Output fit | Resolution, duration, audio, motion, and consistency from current docs plus a test clip |
| Control | Reference-image, camera, edit, seed, and storyboard controls actually exposed |
| Operations | Queue time, failure rate, export path, and repeatability |
| Rights | Input rights, output rights, model restrictions, consent, and provenance |
| Economics | Current plan, per-generation cost, failed-generation treatment, and budget cap |

If no model is callable and authorized, return a shot list, prompt set,
reference-frame brief, and manual vendor-evaluation checklist.

### Prompting for Video Models

Good video prompts specify: **subject + action + camera + style + mood**

```
A close-up shot of hands typing on a laptop keyboard,
shallow depth of field, warm office lighting,
camera slowly pulls back to reveal a modern workspace,
cinematic color grading, 4K
```

**Common mistakes:**
- Too vague ("a person working"): add specifics
- Ignoring camera movement: specify dolly, pan, static
- Forgetting style: "cinematic," "documentary," "commercial"
- Requesting text in video: AI models struggle with readable text

**For detailed prompting guides**: See [references/ai-video-prompting.md](references/ai-video-prompting.md)

### AI Generation vs. Stock Evaluation

| Use Case | Generation evidence to test | Stock/original evidence to test |
|----------|-----------------------------|---------------------------------|
| Specific scene | Prompt control, continuity, review burden | Search coverage, license, edit fit |
| Style continuity | Cross-clip consistency in a bounded test | Match quality across licensed clips |
| Real location | Factual accuracy and disclosure risk | Provenance and location release |
| Product/brand | UI and mark fidelity; avoid fabricated product claims | Approved real captures or assets |
| B-roll | Queue time, failure rate, cost | Search and licensing time |

---

## AI Avatars

Create talking-head videos without filming. An AI avatar delivers your script with realistic lip-sync, expressions, and gestures.

### Avatar tool evaluation

HeyGen is one possible avatar platform, not a guaranteed or preferred
integration. Before naming it or another vendor, verify current official
documentation, authenticated access, callable API or connector availability,
plan limits, price, output rights, body-motion and script-ingestion controls,
localization and export requirements, and the consent requirements for every
voice or likeness involved.

If no avatar tool is currently callable and authorized, provide a manual
vendor-neutral workflow: approved script, consent record, user-operated upload,
export checklist, and a real-camera or voiceover fallback.

**Possible fit to test:** product explainers, feature announcements,
multilingual versions, and approved personalized outreach.

### Avatar vs. Other-Approach Test

| Scenario | Avatar evidence to verify | Alternative to compare |
|----------|---------------------------|------------------------|
| Recurring content | Consent, repeatability, audience response | Recorded presenter or voiceover |
| Multilingual versions | Translation, pronunciation, disclosure | Human localization |
| Personalized outreach | Consent, claim review, cost, reply quality | Approved text or recorded template |
| Founder message | Trust and disclosure response | Direct recording |
| Product UI walkthrough | Presenter value around real captures | Screen recording |
| Creative/artistic video | Control, originality, rights | Original footage or generated scenes |

---

## Editing & Repurposing Tools

Turn existing content into multiple video formats.

Treat the named products as candidates. Discover what is currently installed or
callable, verify the user's account and rights, then map the workflow to the
available tool. If none is available, return an edit decision list, clip
timestamps, captions, and export settings for manual execution.

| Candidate capability | What to verify | Candidate fit |
|----------------------|----------------|---------------|
| Transcript editor | Speaker accuracy, cut control, export, privacy | Interviews, podcasts, webinars |
| Clip assistant | Selection controls, provenance, false-positive rate | Long-form to short-form review |
| Timeline editor | Caption, effect, audio-rights, and export controls | Platform-specific finishing |
| Accessibility assistant | Caption accuracy, eye-contact disclosure, dubbing consent | Approved talking-head content |

### Repurposing Workflow

```
Long-form content (podcast, webinar, demo)
    ↓
Transcript edit: Clean up, remove filler, polish
    ↓
Clip review: Propose moments with source timestamps
    ↓
Timeline edit: Add reviewed captions, effects, and platform styling
    ↓
Distribute: TikTok, Reels, Shorts, LinkedIn
```

### Reverse-Engineer a Viral Edit

To study the style of a reference edit, first discover whether an authorized
media-inspection, browser, or local-file viewer is currently callable. If one is
available, inspect the actual frames and timing. Otherwise ask the user to
attach the media, screenshots, or a timecoded export and provide a manual
frame-sampling checklist. Then extract a reusable beat sheet plus the 3–5
signature moves. Review it before execution in any currently available editor.
Copy the editing grammar, never the reference's footage, script, voice, or
music. Full method: [references/edit-anatomy.md](references/edit-anatomy.md).

---

## Video Production Workflows

### Product Demo Video

1. **Script** the key features and value props (use suede-copy skill)
2. **Screen record** the product flow
3. **Programmatic overlay**: use an available authorized renderer for titles,
   callouts, and transitions, or provide manual editor instructions
4. **AI B-roll**: only with a discovered authorized generator and verified
   rights; otherwise use licensed stock or original footage
5. **Voiceover**: record yourself or use AI avatar for narration
6. **Export** at platform-appropriate specs

### Explainer Video

1. **Script** the problem → solution → CTA arc
2. **Choose presenter**: an approved avatar workflow when available, or
   recorded voiceover plus visuals
3. **Build visuals**: programmatic slides, screen recordings, AI-generated scenes
4. **Add captions** as an accessibility default and verify their accuracy
5. **Export** only after checking current destination requirements and previewing
   the authenticated composer; do not assume a universal orientation

### Batch Social Clips

1. **Create master template** in an available authorized renderer or a manual
   editor project
2. **Feed data**: product features, testimonials, stats
3. **Render batch**: one template, many variations
4. **Add platform-specific captions** with an available editor
5. **Return approved export candidates** to `suede-social` for channel strategy;
   scheduling remains a separate explicit action

### Personalized Video per Account

A tailored product film for each target account, built by agents. One-off
prompting reaches a decent film after 15 to 20 minutes of back-and-forth.
Hundreds of films need the foundation built first.

1. **Product component library**: agents walk the app and rebuild key screens
   as reusable components, one source of truth every film pulls from instead of
   redrawing.
2. **Motion primitives**: reusable animated parts (camera pushes, screen
   handoffs, click rhythm, product moves). Fix one and every film inherits the
   fix.
3. **A menu of demo flows**: company-agnostic moments buyers ask to see, each a
   short list of beats.
4. **Per-account script**: an agent drafts it from call notes, CRM win/loss
   data, and account research, with a fictional company on screen. A cloned
   narrator voice requires that narrator's documented consent.
5. **A render engine**: code that turns a beat list into a film, covering
   camera, transitions, captions, pointer timing, and end card.
6. **Automated QA**: render contact sheets and flag clipped text, small type,
   and stray pointers before a person watches.
7. **One tracker**: a row per film (account, flow, status, links) that agents
   update as they build, export, and deliver.

Storyboard the first film before production; it sits between the brief and the
render the way a spec sits between an idea and code. Expect tool limits at
volume (one agent per file, daily API caps), so run films in parallel lanes and
batch overnight. Any authorized programmatic renderer (Hyperframes, Remotion) or
a design tool with agent access can carry it; none is the default. Rendering,
voice cloning, and delivery each stay separate approvals under the Halt
Contract.

Source: adapted from Harvey's write-up of its agent-built launch and
per-account films (Shawn Farsai and Gabe Pereyra, October 2026).

---

## Tool-Aware Video Pipeline

Use automation only after discovering currently callable, authenticated, and
authorized tools. Otherwise produce the same artifacts as a manual handoff.

```
Approved script (from product context)
    ↓
Available renderer/avatar/generator, if authorized
    or manual editor with timecoded instructions
    ↓
Review cut, rights, captions, and brand assets
    ↓
Output: Approved export candidate, not automatically published
```

When no production tool is available, return the script, shot list, asset
manifest, beat sheet, captions, edit decision list, and export settings so the
user can execute the cut manually, in these exact headings:

```markdown
## Script
<scene or beat> | on-camera or VO line | duration target

## Shot List
Shot # | source (screen capture / owned footage / licensed / generated) | framing | notes

## Asset Manifest
Asset | origin | rights basis and holder | expiry or attribution required | file path

## Beat Sheet
Use the row schema in references/edit-anatomy.md (Beat | Time | Shot |
On-screen text | Caption style | Transition/motion | Audio) plus its style
summary. Do not invent a second beat-sheet format.

## Captions
Full caption text with timecodes; state the accuracy check performed.

## Edit Decision List
Clip # | source file | in TC | out TC | placement | transition | audio bed

## Export Settings
Destination | ratio | resolution | frame rate | codec | max duration | verified
against (current spec source + date)

## Open Gates
<missing rights, consent, cost approval, or brand asset; use the halt contract>
```

For the beat sheet and its style summary, read
[references/edit-anatomy.md](references/edit-anatomy.md) before writing the
handoff: it owns that row schema.

---

## Export Specs and Video Search

Verified platform facts (October 2026):

| Destination | Fact | Source |
|---|---|---|
| YouTube Shorts | Up to 3 minutes for square or vertical uploads made on or after Oct 15, 2024. Over 1 minute with an active Content ID claim, the Short is blocked worldwide. | https://support.google.com/youtube/answer/15424877 |
| Instagram Reels | Up to 3 minutes; profile grid previews crop to 3:4, so keep the subject inside a 3:4 safe area of the 9:16 frame | Instagram announcement, January 2025 |
| Performance Max | Supply your own 16:9, 1:1, and 9:16 videos of 10 seconds or more, or Google may auto-generate one | https://support.google.com/google-ads/answer/17091269 |

For other destinations, read the current upload spec and preview the
authenticated composer before choosing ratio, resolution, or duration.

**Make the video findable.** A video that answers a question people search can
earn views for years on YouTube and in Google's video results. For any video
meant to be found:

1. **Title:** the search phrase and the promise, phrase first, under about 70
   characters so it is not truncated in results.
2. **Description:** the first two lines restate the answer in plain words; the
   rest adds links and context.
3. **Chapters:** timestamps starting at 0:00 with descriptive names, which
   Google can show as key moments.
4. **Captions and transcript:** upload accurate captions instead of relying on
   auto-captions, and publish the transcript on the page that embeds the video.
5. **Embed on an owned page** with `VideoObject` JSON-LD (name, description,
   thumbnailUrl, uploadDate, duration, contentUrl or embedUrl) and the video
   visible on load, so the page itself can rank and be cited in AI answers.
6. **Thumbnail:** one readable idea at small size; real product UI, never a
   fabricated one.

When the video must lead viewers to a written guide, route to
`suede-clip-to-guide`. For site-level video indexing and schema audits, route to
`suede-seo-audit`.

---

## Common Mistakes

1. **Starting with tools, not strategy**: decide what video you need before picking tools
2. **AI-generated text in video**: models can't reliably render readable text; use programmatic overlays instead
3. **Unverified avatar quality**: test a short consented sample before paying
   for or producing a batch
4. **Inaccessible cut**: provide accurate captions without asserting a
   universal sound-off viewing rate
5. **Unverified export spec**: read current destination requirements and
   preview the actual composer before choosing ratio, resolution, or duration
6. **Unsupported production-style claim**: compare polished and informal
   treatments on the current account instead of claiming one universally wins

---

## Halt Contract

Use this exact format when tool authorization, cost approval, rights, consent,
or an approved brand asset blocks the requested result, including the install
and scaffold gates above and the brand-mark gate in Boundaries:

```text
HALT: <one-line blocker>
Why it blocks: <specific missing authority or evidence>
Resolve with:
1. <option>
2. <option>
3. <option, when useful>
Waiting for: <the exact item or approval>
```

Continue with the manual-handoff artifacts above only when they remain useful
and do not imply the blocker was resolved or that a render occurred.

---

## Boundaries

- Do not generate, render, purchase, upload, or publish media without approval
  of scope, tool cost, rights, and destination.
- Do not clone a real person's voice or likeness, use unlicensed source media,
  or promise an exact copy of a reference style or edit.
- For Suede-branded visuals, use only the approved transparent Suede S asset at
  `JasonColapietro/suede-creator-skills/docs/assets/suede-ai-logo-transparent.png`
  with SHA-256
  `83a7ee0317e4debe2e7b076c20ba067feb76a587f9e829dc6310ae4be4b44dfa`;
  if it is missing or changed, omit the mark and halt for the approved file.

## Routing

- Use `suede-social` to choose channel strategy, cadence, and distribution.
- Use `suede-clip-to-guide` when a clip has to bridge to an article, newsletter,
  or guide.
- Use `suede-ad-creative` for paid video ad concepts and variants.
- Use `suede-image` for still-image generation and editing.
- Use `suede-copy` for source-verified script and messaging polish.

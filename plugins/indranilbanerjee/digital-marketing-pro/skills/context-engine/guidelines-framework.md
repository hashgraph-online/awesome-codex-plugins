# Guidelines Framework — Structuring and Applying Brand Knowledge

This reference defines how brand guidelines, restrictions, channel styles, templates, and agency SOPs are structured, stored, and enforced across all modules and commands.

## Why Guidelines Matter

A brand profile captures **what** the brand is (identity, voice scores, channels, goals). Guidelines capture **how** the brand communicates — the detailed rules, restrictions, and style choices that make content authentically on-brand.

| Brand Profile | Brand Guidelines |
|--------------|-----------------|
| Formality: 7/10 | "Never use exclamation marks in headlines" |
| Tone: professional, trustworthy | "Always lead with data, then story" |
| Avoid words: cheap, discount | Full banned word list with 40+ terms and context |
| Industry: healthcare | "All health claims require citation. Never use 'cure' or 'guarantee'" |
| Channel: LinkedIn | "LinkedIn posts: max 1300 chars, no emoji in first line, end with question" |

## Storage Structure

Per-brand guidelines at `~/.claude-marketing/brands/{slug}/`:

```
guidelines/
├── _manifest.json        # Index: counts, categories, last-updated
├── voice-and-tone.md     # Detailed voice guide
├── messaging.md          # Key messages, value props, positioning
├── restrictions.md       # Banned words, restricted claims, disclaimers
├── channel-styles.md     # Per-channel rules
├── visual-identity.md    # Colors, fonts, logo rules
└── custom/               # Additional guideline files
```

Per-brand templates at `~/.claude-marketing/brands/{slug}/`:

```
templates/
├── _manifest.json        # Template index
└── *.md                  # Proposal, report, brief templates
```

Agency-level SOPs at `~/.claude-marketing/`:

```
sops/
├── _manifest.json        # SOP index
└── *.md                  # Workflow definitions
```

## Guideline Categories

### 1. Voice and Tone (`voice-and-tone.md`)

Detailed voice guide that goes beyond the 4 numeric scores (formality, energy, humor, authority) in the brand profile.

**What belongs here:**
- Detailed writing style rules (sentence length, paragraph structure, readability level)
- Tone modifiers by content type (blog=conversational, whitepaper=authoritative, social=casual)
- Pronoun preferences (we vs. the company, you vs. customers)
- Specific dos and don'ts with examples
- Before/after examples showing correct vs. incorrect voice
- Emotional register (empathetic, direct, aspirational, pragmatic)

**Example structure:**
```markdown
# Brand Voice & Tone Guide

## Core Voice
- We speak as a trusted advisor, not a salesperson
- Lead with empathy, follow with expertise
- Use "you" and "your" — make it about the reader

## Writing Style
- Sentences: max 25 words average
- Paragraphs: 2-3 sentences
- Readability: Grade 8-10 (Flesch-Kincaid)
- Active voice preferred (80%+ of sentences)

## Tone by Content Type
- **Blog posts**: Conversational, story-driven, relatable
- **Whitepapers**: Authoritative, data-first, formal
- **Social media**: Warm, engaging, concise
- **Email**: Personal, action-oriented, helpful
- **Ad copy**: Bold, benefit-focused, urgent (but not pushy)

## Dos and Don'ts
- DO: "We help you grow" → personal, active
- DON'T: "Our solution enables growth" → corporate, passive
- DO: "Here's what we found" → direct
- DON'T: "It should be noted that" → filler
```

### 2. Messaging Framework (`messaging.md`)

Approved messages, positioning, and language that the brand uses consistently.

**What belongs here:**
- Brand positioning statement
- Value propositions (primary + supporting)
- Key messages by audience segment
- Approved taglines and slogans
- Elevator pitches (30-second, 60-second)
- Proof points and statistics the brand uses
- Competitive differentiators (how to describe vs. competitors)
- Message hierarchy (which messages to lead with)

**Example structure:**
```markdown
# Messaging Framework

## Positioning Statement
For [target audience] who [need], [Brand] is the [category] that [key benefit] because [reason to believe].

## Value Propositions
1. **Primary**: Save 10 hours per week on marketing reporting
2. **Supporting**: AI-powered insights, not just data
3. **Supporting**: Integrates with your existing tools in minutes

## Key Messages by Audience
### CMOs
- "Turn marketing data into board-ready insights in minutes"
- "Prove ROI across every channel with unified attribution"

### Marketing Managers
- "Stop building reports manually — automate with AI"
- "Get alerts when campaigns need attention"

## Approved Taglines
- Main: "Marketing intelligence, simplified"
- Campaign: "Your data. Your insights. Your edge."
- NEVER use: "The best marketing tool" (too generic)

## Proof Points
- "Used by 500+ marketing teams"
- "Average 40% reduction in reporting time"
- "4.8/5 rating on G2"
```

### 3. Restrictions (`restrictions.md`)

Hard rules about what the brand must never say, claim, or do.

**What belongs here:**
- Banned words and phrases (with context for why)
- Restricted claims (claims that need qualification or evidence)
- Mandatory disclaimers (by content type or channel)
- Prohibited topics or comparisons
- Legal/compliance language requirements
- Trademark usage rules
- Competitor mention rules

**How restrictions are enforced:**
- Before generating any content, check the restrictions file
- Scan output for banned words — flag and suggest alternatives
- Verify claims against the restricted claims list
- Append mandatory disclaimers when content matches trigger conditions
- Log violations to campaign-tracker for pattern analysis

**Example structure:**
```markdown
# Brand Restrictions & Guardrails

## Banned Words and Phrases
- "cheap" → use "affordable" or "cost-effective"
- "guarantee" → use "committed to" or "designed to"
- "best in class" → use specific proof points instead
- "revolutionary" → use "innovative" or describe the specific innovation
- "synergy" / "leverage" / "paradigm" → plain language always
- "[Competitor name] is bad/worse" → never disparage by name

## Restricted Claims (Require Qualification)
- Performance claims → must cite source and date: "40% faster (2024 benchmark study)"
- ROI claims → must include "results may vary" or specific conditions
- Health/wellness claims → must include "consult your healthcare provider"
- Award mentions → must be current year or specify year

## Mandatory Disclaimers
- **Email marketing**: Unsubscribe link + physical address (CAN-SPAM)
- **Financial content**: "Not financial advice" disclaimer
- **Testimonials**: "Individual results may vary"
- **Influencer content**: #ad or #sponsored clearly visible
- **Healthcare**: "This is not medical advice"

## Prohibited Topics
- Political opinions or endorsements
- Religious statements
- Competitor disparagement (compare features, not companies)
- Unverified statistics or made-up data
```

### 4. Channel Styles (`channel-styles.md`)

Per-channel tone and format rules that may differ from the base brand voice.

**Key principle:** Channel styles **override** the base voice settings for that specific channel. If the brand profile says formality=7 but channel-styles says "Instagram: casual, emoji-friendly, formality 4" — Instagram content follows the channel style.

**What belongs here:**
- Per-channel tone adjustments
- Character limits and format rules
- Hashtag and emoji policies
- Posting time preferences
- Content type preferences per channel
- CTA style per channel

**Example structure:**
```markdown
# Channel-Specific Styles

## LinkedIn
- **Tone**: Professional thought leadership, formality 8/10
- **Format**: 1300 chars max, no emoji in first line, paragraph breaks every 2-3 sentences
- **Hashtags**: 3-5 relevant, at end of post
- **CTAs**: "What's your experience with...?" or "Link in comments"
- **Content types**: Industry insights, case studies, team highlights
- **Avoid**: Sales pitches, excessive self-promotion

## Instagram
- **Tone**: Warm, visual-first, formality 4/10
- **Format**: Caption max 2200 chars, hook in first line (before "more")
- **Hashtags**: 15-20 in first comment, 3-5 in caption
- **Emoji**: Yes, 2-3 per post, relevant not decorative
- **Content types**: Behind-the-scenes, tips, user stories, reels
- **Avoid**: Long text blocks, corporate jargon

## Email
- **Tone**: Personal, helpful, formality 6/10
- **Subject line**: Max 50 chars, no ALL CAPS, personalize when possible
- **Preview text**: Complement (don't repeat) subject line
- **CTA**: One primary CTA per email, button format
- **Avoid**: Multiple competing CTAs, walls of text

## Twitter/X
- **Tone**: Concise, witty, formality 5/10
- **Format**: Single tweet preferred, thread for depth
- **Hashtags**: 1-2 max, only if trending or branded
- **Emoji**: Sparingly, 0-1 per tweet
- **Content types**: Hot takes, quick tips, engagement questions
```

### 5. Visual Identity (`visual-identity.md`)

Text descriptions of visual brand elements. Since the plugin creates text content (not images), this serves as reference for briefs, creative directions, and ensuring visual consistency in descriptions.

**What belongs here:**
- Brand colors (hex codes, names, usage rules)
- Typography (font families, usage hierarchy)
- Logo usage rules (minimum size, clear space, backgrounds)
- Photography/imagery style (subjects, mood, treatment)
- Iconography style
- Layout preferences

### 6. Custom Guidelines (`custom/`)

Additional guideline files that don't fit the standard categories. Examples:
- `accessibility.md` — Accessibility standards and inclusive language rules
- `legal-review.md` — When legal review is required
- `seasonal.md` — Holiday and seasonal content rules
- `partner-co-branding.md` — Rules for partner content

## How Guidelines Are Applied

### At Session Start (via hooks)
1. `guidelines-manager.py --brand {slug} --action summary` runs alongside `setup.py --summary`
2. If guidelines exist, summary output includes: category count, total rules, restriction count, template count
3. This primes the session with awareness that guidelines exist

### In Module Skills (Brand Context point 9)
Every module checks for guidelines before generating output:
1. Check if `guidelines/_manifest.json` exists
2. Load `restrictions.md` — enforce banned words, restricted claims, mandatory disclaimers
3. Load `channel-styles.md` — apply channel-specific tone overrides
4. Load `messaging.md` — use approved key messages and positioning language
5. Load `voice-and-tone.md` — follow detailed voice rules beyond numeric scores

### In Command Skills (Step 1 extension)
Every command loads guidelines alongside the brand profile:
1. Load `_active-brand.json` → `profile.json` (existing)
2. Check `guidelines/_manifest.json` — if present, load restrictions and relevant categories
3. Check `templates/_manifest.json` — if a custom template exists for this command, use it
4. Check `sops/_manifest.json` — if an SOP applies to this workflow, follow it

### In PreToolUse Hook (Content Check)
When writing marketing content:
1. Check restrictions — scan for banned words and restricted claims
2. Verify mandatory disclaimers are included when required
3. Log violations to campaign-tracker

### Priority Order
When guidelines conflict with the brand profile:
1. **Restrictions** — always enforced (highest priority)
2. **Channel styles** — override base voice for specific channels
3. **Guidelines voice-and-tone** — override numeric voice scores with detailed rules
4. **Brand profile voice scores** — default when no guidelines exist
5. **SOPs** — add workflow steps, don't override content rules

## Converting Unstructured Guidelines

When users paste or describe their guidelines (via `/digital-marketing-pro:import-guidelines`), convert to structured markdown:

1. **Identify the category** — which file does this content belong in?
2. **Extract rules** — convert prose into bullet points with clear dos/don'ts
3. **Add examples** — include before/after examples where possible
4. **Note conflicts** — if guidelines conflict with existing profile settings, flag for user resolution
5. **Update manifest** — rebuild `_manifest.json` with accurate counts

**Conversion example:**
- User says: "We never use exclamation marks in professional content and always spell out numbers under ten"
- Goes to: `voice-and-tone.md` under "Writing Style" rules:
  ```
  - Never use exclamation marks in professional content (blog, whitepaper, email)
  - Spell out numbers under ten ("seven" not "7")
  ```

## Template Integration

Templates modify the output format of commands. When a command like `/digital-marketing-pro:performance-report` runs:

1. Check `templates/_manifest.json` for a matching template (e.g., "performance-report")
2. If found, load the template and structure output to match its format
3. If not found, use the command's default format

Templates should include:
- Section headers (what sections to include)
- Content guidance (what goes in each section)
- Format requirements (length, style, visual layout)
- Placeholder markers for dynamic content

## SOP Integration

SOPs add workflow steps to commands. When an SOP like "content-approval-workflow" exists:

1. The relevant command or module checks for applicable SOPs
2. Adds SOP steps to the output (e.g., "Submit to legal review before publishing")
3. Can flag when a workflow step requires human approval

SOPs are agency-level (not per-brand) so they apply consistently across all clients.

## Violation Tracking

When a guideline is violated (banned word used, restriction breached):

1. Flag immediately in the output with the specific rule reference
2. Suggest a compliant alternative
3. Log to campaign-tracker: `save-violation` action with:
   - `rule`: which guideline was violated
   - `category`: which guideline category
   - `severity`: low/medium/high
   - `content`: the violating text
   - `suggestion`: compliant alternative
4. Violations can be reviewed via: `get-violations` action for pattern analysis

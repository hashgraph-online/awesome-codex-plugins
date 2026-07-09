---
name: import-guidelines
description: "Import brand guidelines. Use when: adding voice guides, style restrictions, or messaging frameworks."
argument-hint: "[file-path or URL]"
---

# /digital-marketing-pro:import-guidelines

## Purpose

Import and structure brand guidelines into the persistent brand knowledge layer. Converts unstructured guideline documents, style guides, restriction lists, and messaging playbooks into structured, enforceable markdown files that are automatically applied across all modules and commands.

## Input Required

The user provides one or more of:

- **Pasted guideline content**: Text from an existing brand guide, style guide, or restriction list
- **Verbal description**: Spoken/typed rules ("we never use exclamation marks", "always lead with data")
- **Category to update**: Which guideline category to add to (voice-and-tone, messaging, restrictions, channel-styles, visual-identity, or custom)
- **Source document reference**: Description of where these guidelines come from

If the user doesn't specify a category, analyze the content and route it to the correct category automatically.

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for existing guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load existing guidelines to merge with (not overwrite). If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.

2. **Classify the content** — Determine which guideline category (or categories) the input belongs to:
   - Voice rules, writing style, tone → `voice-and-tone.md`
   - Key messages, taglines, positioning, value props → `messaging.md`
   - Banned words, restricted claims, disclaimers, prohibited topics → `restrictions.md`
   - Per-channel format/tone rules → `channel-styles.md`
   - Colors, fonts, logo rules, imagery style → `visual-identity.md`
   - Anything else → `custom/{descriptive-name}.md`

3. **Structure the content** — Convert unstructured input into organized markdown:
   - Extract individual rules as bullet points
   - Group by sub-topic with clear headings
   - Add before/after examples where the input provides them
   - Preserve the user's intent — don't add rules they didn't specify
   - Use the framework structure from `skills/context-engine/guidelines-framework.md`

4. **Check for conflicts** — Compare new guidelines against existing profile settings:
   - If guidelines say "casual tone" but profile has formality=8, flag the conflict
   - If restrictions ban words that appear in existing brand messaging, flag it
   - Present conflicts to the user and ask which takes precedence
   - Note: channel-styles intentionally override base voice for specific channels (not a conflict)

5. **Merge with existing guidelines** — If the category already has content:
   - Show the user what already exists
   - Ask: merge (add new rules to existing), replace (overwrite), or cancel
   - When merging, deduplicate rules and maintain organization

6. **Save and confirm** — Write the structured guideline file:
   - Save using `guidelines-manager.py --brand {slug} --action save --category {category}`
   - Or write directly to `~/.claude-marketing/brands/{slug}/guidelines/{file}`
   - Manifest is rebuilt automatically on save
   - Confirm: show the category, rule count, and a preview of what was saved

7. **Ask about additional categories** — If the user's input might span multiple categories:
   - "I also noticed messaging content — would you like me to save that to messaging.md?"
   - "Some of these rules are channel-specific — should I also create channel-styles.md?"

## Output

- Confirmation of what was saved, with rule counts
- Preview of the structured guideline file
- Any conflicts flagged between guidelines and existing brand profile
- Suggestion to import additional categories if relevant content was detected
- Reminder: "These guidelines will be automatically applied when creating content. Use `/digital-marketing-pro:import-guidelines` again to add more."

## Guideline Categories Reference

| Category | File | What Goes Here |
|----------|------|---------------|
| Voice & Tone | `voice-and-tone.md` | Writing style, tone rules, dos/don'ts, readability, pronoun preferences |
| Messaging | `messaging.md` | Positioning, value props, key messages, taglines, elevator pitches, proof points |
| Restrictions | `restrictions.md` | Banned words, restricted claims, mandatory disclaimers, prohibited topics |
| Channel Styles | `channel-styles.md` | Per-channel tone, format, hashtag/emoji policies, content types |
| Visual Identity | `visual-identity.md` | Colors, fonts, logo rules, photography style (text descriptions) |
| Custom | `custom/{name}.md` | Accessibility rules, legal review triggers, seasonal rules, partner guidelines |

## Examples

**User**: "Here's our brand voice guide: We're friendly but professional. Never use jargon. Always explain technical concepts simply. Use 'you' not 'customers'. Sentences should be under 20 words."

**Result**: Saves to `voice-and-tone.md`:
```markdown
# Brand Voice & Tone Guide

## Core Voice
- Friendly but professional
- Always explain technical concepts in plain language
- Use "you" and "your" — never "customers" or "users"

## Writing Style
- Sentences: maximum 20 words
- No jargon — if a simpler word exists, use it

## Dos and Don'ts
- DO: Use plain language and direct address
- DON'T: Use industry jargon or technical terminology without explanation
```

**User**: "We can never use the words 'cheap', 'guarantee', 'best', or 'revolutionary'. Health claims need a disclaimer."

**Result**: Saves to `restrictions.md`:
```markdown
# Brand Restrictions & Guardrails

## Banned Words and Phrases
- "cheap" → use "affordable" or "cost-effective"
- "guarantee" → use "committed to" or "designed to"
- "best" → use specific proof points instead
- "revolutionary" → use "innovative" or describe the specific innovation

## Mandatory Disclaimers
- Health/wellness claims: Include "This is not medical advice. Consult your healthcare provider."
```

## Reference Files

- `skills/context-engine/guidelines-framework.md` — Full framework for structuring and applying guidelines
- `scripts/guidelines-manager.py` — CLI for guideline CRUD operations

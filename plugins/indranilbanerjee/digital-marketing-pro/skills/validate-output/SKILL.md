---
name: validate-output
description: "Validate content structure. Use when: checking schema compliance, required sections, word count, or placeholders."
---

# /digital-marketing-pro:validate-output

## Purpose

Validate marketing content against expected structural schemas to ensure completeness, formatting consistency, and production-readiness. Checks required sections, word count ranges, markdown formatting compliance, placeholder text detection (unfilled template variables, lorem ipsum, TBD markers), and content-CTA consistency. Supports eight built-in schemas for common marketing content types plus custom schemas for brand-specific templates.

This command catches the structural and formatting issues that quality evaluation misses — the missing H2 that breaks SEO, the placeholder "[INSERT COMPANY NAME]" that slipped through, the blog post that is 300 words short of the brief requirement, or the email that has a CTA promising a demo but the body talks about a whitepaper. It is designed to be run as a final pre-publication check after content quality has been evaluated via /digital-marketing-pro:eval-content.

## Input Required

The user must provide (or will be prompted for):

- **Content to validate**: The text to check — provided inline, as a pasted block, or as a file path. Supports any marketing content format
- **Schema name or file** (optional): One of the eight built-in schemas — `blog_post`, `email`, `ad_copy`, `social_post`, `landing_page`, `press_release`, `content_brief`, `campaign_plan` — or a file path to a custom JSON schema. If omitted, the validator auto-detects the most likely schema based on content structure, length, and formatting patterns. Custom schemas follow the format defined in `skills/context-engine/eval-framework-guide.md`

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand formatting standards and content requirements. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load template definitions from `templates/` that may define brand-specific required sections, word count ranges, and formatting rules. Check for custom schemas at `~/.claude-marketing/brands/{slug}/schemas/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Determine schema**: If a schema name or file was provided, use it directly. If not, execute `scripts/output-validator.py --action list-schemas` to get all available schemas, then select the most appropriate one based on content characteristics (length, structure, formatting patterns). Report which schema was selected and why, so the user can override if the selection was wrong.
3. **Run structural validation**: Execute `scripts/output-validator.py --action validate --text "{content}" --schema {schema_name_or_path}`. The validator checks:
   - **Required sections**: All sections defined in the schema are present with appropriate headings. For each missing section, identify what is expected and where it should appear in the content structure
   - **Word count**: Total word count and per-section word counts fall within the schema-defined ranges. Flag both under-count (too thin, lacking depth) and over-count (too long, needs trimming)
   - **Formatting compliance**: Markdown heading hierarchy is correct (no skipped levels), lists are properly formatted, links are valid syntax, images have alt text, code blocks are closed, and tables render correctly
   - **Placeholder detection**: Scan for unfilled template variables (`{placeholder}`, `[PLACEHOLDER]`, `[INSERT X]`, `TODO`, `TBD`, `FIXME`, `Lorem ipsum`, `xxx`, `ACME Corp` used as placeholder), partial completions, and obviously templated content that was not customized
   - **CTA consistency**: The call-to-action matches the content's topic and promise — a blog post about email marketing should not CTA to a social media guide, an email promoting a webinar should link to the webinar registration, not a generic contact page
   - **SEO structure** (for blog_post and landing_page schemas): H1 present and singular, meta description length within 150-160 characters, title tag within 50-60 characters, internal link present, keyword appears in H1 and first 100 words
   - **Compliance markers** (for regulated industries): Required disclaimers present, mandatory disclosures included, terms and conditions referenced where needed
4. **Generate fix guidance**: For each failed check, provide specific guidance:
   - What is missing or incorrect, with the exact location in the content
   - What the schema requires (the rule being enforced)
   - How to fix it, with an example of what the corrected section should look like
   - Whether the fix is required (schema mandates it) or recommended (best practice)
5. **Handle custom schema requests**: If the user needs a schema that does not match any built-in option, guide them on the JSON schema format:
   - Required fields: `name`, `sections` (array of section definitions with name, required flag, min/max word count), `total_word_count` (min/max), `formatting_rules`, `placeholder_patterns`
   - Offer to generate a starter schema based on the content's current structure that the user can refine
6. **Present checklist-style results**: Format all validation results as a pass/fail checklist that the user can work through sequentially, with the most critical failures first.

## Output

A structured validation report containing:

- **Validation score**: Percentage of checks passed out of total checks run — the headline metric for structural completeness
- **Schema used**: Which schema was applied (built-in name or custom file path), whether it was user-specified or auto-detected, and the detection confidence if auto-detected
- **Pass/fail checklist**: Each check as a line item with pass or fail status:
  - **Sections check**: List of required sections with present/missing status. For each missing section, the expected heading, where it should appear, and an example of what it should contain
  - **Word count check**: Total word count versus schema range, plus per-section counts for any sections outside their expected range. Shows the delta (e.g., "247 words short of the 1,500 minimum")
  - **Formatting check**: Heading hierarchy validation, list formatting, link syntax, image alt text, code block closure, table rendering. Each issue with its location and the specific formatting rule violated
  - **Placeholder check**: Every detected placeholder instance with the exact text, line location, and suggested action (replace with real content, remove, or confirm if intentional). Grouped by type: template variables, lorem ipsum, TBD/TODO markers, obvious placeholder names
  - **CTA consistency check**: Whether the CTA aligns with the content topic and promise. If misaligned, the specific inconsistency and a suggested correction
  - **SEO structure check** (if applicable): H1 presence and uniqueness, meta description length, title tag length, keyword placement, internal linking
  - **Compliance check** (if applicable): Required disclaimers, disclosures, and legal references
- **Fix checklist**: Priority-ordered list of all failures with specific fix instructions — required fixes first, then recommended improvements, each with example corrected text
- **Placeholder inventory**: Complete list of all detected placeholders across the content, deduplicated, so the user has a single reference for everything that needs to be filled in
- **Schema reference**: If the user may need it, a summary of the schema rules that were applied — useful for writers to understand the structural requirements before starting their next piece

## Agents Used

- **quality-assurance** — Schema selection and auto-detection, structural validation execution across all check dimensions (sections, word count, formatting, placeholders, CTA consistency, SEO structure, compliance markers), fix guidance generation with specific examples, checklist formatting, and custom schema creation guidance

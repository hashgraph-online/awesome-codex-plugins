---
name: review-response
description: "Respond to online reviews. Use when: drafting replies for Google, Yelp, G2, or building review response templates."
---

# /digital-marketing-pro:review-response

## Purpose

Generate professional, brand-aligned review responses for positive, neutral, and negative reviews across any platform. Ensures every response maintains brand voice, addresses the reviewer's specific points, and follows best practices for reputation management and customer recovery.

## Input Required

The user must provide (or will be prompted for):

- **Review text**: The full text of the review to respond to
- **Rating**: Star rating (1-5 stars)
- **Platform**: Where the review was posted (Google, Yelp, G2, Capterra, Trustpilot, Amazon, TripAdvisor, App Store, etc.)
- **Reviewer name**: Display name of the reviewer (optional — for personalization)
- **Specific issue mentioned**: Key complaint, praise, or topic raised in the review (optional — for targeted response)
- **Business context**: Any internal context about the situation — was the issue resolved, is there a known product bug, was there a service failure (optional — helps craft an accurate response)
- **Batch mode**: If responding to multiple reviews, provide them as a set for consistent tone and varied language
- **Response speed requirement**: Whether the review needs an urgent response (crisis situation) or standard turnaround
- **Internal resolution status**: Whether the issue has been fixed, is in progress, or is unresolved (for negative reviews — helps determine what to promise)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Apply brand voice settings**: Load voice-and-tone guidelines and any channel-specific style rules for the review platform — review responses often require a warmer, more personal tone than other brand communications
3. **Classify review sentiment and severity**: Categorize as positive (4-5 stars), neutral (3 stars), or negative (1-2 stars) — further classify negative reviews by severity level: minor complaint, service failure, product defect, or safety/legal issue
4. **For negative reviews**: Acknowledge the specific concern by name, express genuine empathy without generic platitudes, take responsibility where appropriate, offer a concrete resolution path with specifics, and move the conversation offline with a direct contact method (email or phone)
5. **For positive reviews**: Express sincere gratitude, reinforce the specific aspect the reviewer praised, add a personal or humanizing touch, and encourage continued engagement — mention related products, services, or referral programs where natural
6. **For neutral reviews**: Acknowledge the balanced feedback, address any specific concerns raised with actionable detail, highlight relevant brand strengths without being defensive or dismissive, and invite further dialogue to improve their experience
7. **Check brand guidelines for approved response language**: Verify the response against any restricted terms, required disclosures, legal disclaimers, or mandated response elements in the brand guidelines
8. **Apply platform conventions**: Adjust response length, formatting, and tone for platform norms — Google (concise), Yelp (conversational), G2 (professional), TripAdvisor (hospitality-focused), etc.
9. **Score response for brand voice alignment**: Evaluate the drafted response against brand voice parameters — tone, formality, warmth, and personality — and adjust until the response sounds authentically on-brand
10. **Check for common pitfalls**: Ensure the response avoids defensiveness, blame-shifting, over-promising, disclosing private information, or using repetitive language across multiple review responses
11. **Optimize for SEO where applicable**: On platforms where responses are indexed (Google, Yelp), naturally incorporate relevant keywords and business name without sounding forced
12. **Generate batch variations**: If responding to multiple similar reviews, vary the language, structure, and opening to avoid templated-sounding responses that damage authenticity

## Output

A structured review response package containing:

- **Ready-to-post review response**: Primary response tailored to the platform's character limits, conventions, and audience expectations
- **Alternative versions**: Formal and casual variants for flexibility, plus a shorter version if the primary response exceeds platform norms
- **Response guidelines**: Platform-specific best practices applied — recommended length, optimal tone, ideal response timing, and SEO considerations
- **Escalation recommendation**: For negative reviews — whether this requires manager involvement, legal review, product team notification, or immediate offline outreach
- **Response quality score**: Brand voice alignment rating and checklist of best practices applied
- **Follow-up note**: Suggested internal action items if the review reveals a systemic issue worth addressing
- **SEO keywords applied**: For indexed platforms, keywords naturally incorporated into the response
- **Tone analysis**: Breakdown of the response tone (empathetic, grateful, professional, warm) matched against brand voice settings
- **Response timing recommendation**: Optimal window for posting the response based on platform algorithms and customer expectations
- **Template extraction**: If the response is strong, a generalized template version saved for future similar reviews

## Agents Used

- **content-creator** — Response copywriting, tone calibration, personalization, platform-appropriate language, alternative version drafting
- **brand-guardian** — Voice consistency enforcement, guideline compliance, restricted language checks, escalation assessment, legal sensitivity review

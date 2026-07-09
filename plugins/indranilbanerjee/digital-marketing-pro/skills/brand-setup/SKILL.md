---
name: brand-setup
description: "Set up or update a brand profile. Use when: new brand onboarding, client setup, brand switching, context update."
argument-hint: "[brand-name or --full]"
---

# Brand Setup — Interactive Brand Profiling

## When to Use This Skill

- User says "set up a new brand" or "create a brand profile"
- User mentions a new client or project for marketing
- User wants to switch between brands (agency use case)
- User wants to update brand voice, audiences, or goals
- First time using any marketing skill without an active brand

## Setup Modes

### Quick Setup (5 questions — recommended for getting started fast)
If the user wants to get started quickly, or says "quick setup", ask only these 5 essential questions:
1. **Brand name** — "What's your brand or business name?"
2. **What you do** — "In one sentence, what does [brand] do?" (extract industry, business model, USP)
3. **Target audience** — "Who is your primary customer?" (extract B2B/B2C, demographics)
4. **Brand voice** — "Pick 3 words that describe how your brand communicates" (map to formality/energy/humor/authority scales)
5. **Primary channel** — "Where do you primarily market? (social media, email, SEO, paid ads, etc.)"

From these 5 answers, intelligently populate the full profile:
- Infer industry, business model type, and compliance requirements
- Map voice descriptors to the 1-10 scales (e.g., "professional" → formality: 8, "fun" → humor: 7)
- Set sensible defaults for everything else
- Tell the user: "Quick profile created! You can refine it anytime with /digital-marketing-pro:brand-setup --full"

### Full Setup (17 questions — comprehensive profiling)
Use the full setup when:
- User explicitly asks for detailed/full/comprehensive setup
- User says "/digital-marketing-pro:brand-setup --full"
- User wants to update specific sections of an existing profile

## Process (Full Setup)

### Step 1: Brand Identity

Ask the user one question at a time (don't overwhelm):

1. **Brand name**: "What's the brand/company name?"
2. **Elevator pitch**: "In one sentence, what does [brand] do?"
3. **USP**: "What makes [brand] different from competitors?"
4. **Mission/Values**: "What's the brand's mission? What values drive it?"

### Step 2: Business Model

5. **Business type**: Present options:
   - B2B SaaS / Software
   - B2C eCommerce / DTC
   - B2B Services / Consulting
   - Local Business
   - Agency (managing multiple clients)
   - Creator / Personal Brand
   - Enterprise
   - Non-Profit
   - Marketplace

6. **Revenue model**: subscription, transactional, freemium, marketplace commission, donation, retainer, advertising
7. **Price range and sales cycle**: "What's your typical deal size and how long does it take to close?"

### Step 3: Industry & Compliance

8. **Industry**: "What industry are you in?" (match to industry-profiles.md)
9. **Regulated?**: "Are you in a regulated industry? (healthcare, finance, legal, alcohol, cannabis, etc.)"
10. **Target markets**: "What countries/regions do you sell to?" (triggers compliance rules)

### Step 4: Brand Voice

11. **Voice dimensions** — Ask user to rate 1-10 or describe:
    - Formality (1=very casual like a friend, 10=very formal like a law firm)
    - Energy (1=calm and measured, 10=enthusiastic and bold)
    - Humor (1=never use humor, 10=humor is core to the brand)
    - Authority (1=peer-level, friendly guide, 10=expert thought leader)

12. **Personality traits**: "Pick 3-5 words that describe the brand's personality" (e.g., witty, empathetic, direct, bold, thoughtful, playful, authoritative, warm)

13. **This-Not-That**: "Give me examples of how you'd say something vs. how you wouldn't" (e.g., "We say 'Let's figure this out together' not 'Contact our support team'")

14. **Sample content**: "Share 2-3 URLs or text snippets of content you think nails your brand voice"

### Step 5: Channels & Goals

15. **Active channels**: "Which marketing channels are you currently using?" (website, Instagram, LinkedIn, Twitter, TikTok, YouTube, Facebook, Pinterest, Email, Google Ads, Meta Ads, etc.)

16. **Goals**: "What's your #1 marketing goal right now?" + target KPIs + budget range + team size

### Step 6: Competitors

17. **Competitors**: "Name 3-5 competitors (direct or aspirational)"
    - For each: name, URL, relationship (direct/indirect/aspirational), known strengths/weaknesses

### Step 7: Save & Confirm

After collecting all information:

1. Run: `python3 scripts/setup.py --create-brand "[brand name]"`
2. Update the created profile.json with all collected data
3. Confirm to user: "Brand profile created for [brand_name]. All marketing modules will now use this context. You can update it anytime by saying 'update my brand profile.'"

## Switching Brands

When user says "switch to [brand name]":
1. Run: `python3 scripts/setup.py --list-brands`
2. Find matching brand
3. Update `~/.claude-marketing/brands/_active-brand.json`
4. Confirm: "Switched to [brand_name]."

## Updating a Brand

When user wants to update specific fields:
1. Load current profile from `~/.claude-marketing/brands/{slug}/profile.json`
2. Ask about the specific field(s) to update
3. Write updated profile back
4. Confirm changes

## Important Notes

- NEVER skip the brand voice section — it's what makes all content outputs on-brand
- For agencies: each client should be a separate brand profile
- Store voice samples as markdown files in the brand's voice-samples/ directory
- Auto-detect industry compliance rules based on the industry and market selections

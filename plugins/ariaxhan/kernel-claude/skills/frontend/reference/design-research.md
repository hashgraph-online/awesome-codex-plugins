# Design Skill Reference: Research & Best Practices

Reference document for the design skill. Read when deeper context is needed.
Not auto-loaded; read on demand via progressive disclosure.

## Sources

Compiled from: Anthropic's frontend aesthetics cookbook, Lovable's prompting bible
and leaked system prompt, Vercel v0's prompting guides and system prompt, community
best practices from Design Systems Collective, and production testing across AI UI
generators (Lovable, v0, Bolt, Replit).

2026 updates: v0 Rebuild (Feb 3, 2026), Anti-Vibecoding Movement (Maya Brennan,
Jan 2026), GenUI Guide (CopilotKit Jan 29, 2026), shadcn Best Practices 2026,
Justin Wetch "Teaching Claude to Design Better" (Jan 5, 2026), Jakob Nielsen
2026 Predictions.

---

## Key Insight: Intent Over Specification

Every successful AI design system converges on the same principle:
describe WHAT you want the user to feel, not HOW to implement it.

Lovable: "Lovable already has great taste. Focus on design principles, styling
guidelines, page layout, navigation structure."

v0: "Be specific about your users and how they interact with the product in real
life. When you're specific about the product surface, v0 doesn't waste time
inventing features you don't need."

Anthropic: "Guide specific design dimensions. Reference design inspirations.
Call out common defaults. Claude has strong knowledge of design principles but
defaults to safe choices unless explicitly encouraged otherwise."

The pattern: LLMs know CSS. They don't know taste. Prompt for taste.

---

## Anti-Vibecoding Movement (Jan 2026)

2025 was "the year of vibecoding" - building software from simple prompts.
Side effect: "a sad surge of homogenous, diluted designs" and "AI Product Slop."

In 2026, designers actively reject: same-y, emoji-fueled, 8px-radius-everywhere,
faux-minimalism. This is the named counter-movement to AI aesthetic convergence.

Visual signals to avoid: generic purple gradients on white, neon cyan/pink/purple
palette everywhere, uniform sections, heavy font weights everywhere.

---

## Generative UI (GenUI) Maturation (2026)

Three patterns now production-ready (CopilotKit Jan 29, 2026):
- **Static**: Pre-built components, agent selects which to show
- **Declarative**: Agent returns JSON spec (A2UI, Open-JSON-UI standards)
- **Open-ended**: Agent controls entire UI surfaces (MCP Apps)

Jakob Nielsen 2026: "Designers don't create static screens—they design systems
of capability." The mental model shifts from screens to constraint systems.

---

## What Lovable Gets Right

1. Design system as foundation, not afterthought. Lovable stores design systems
   in a .lovable folder applied to all connected projects. The system evolves
   through iteration, not upfront specification.

2. AI handles 90% of design decisions. Designers focus on the 10% that matter.
   "Embrace the unexpected and work with AI as a creative partner."

3. Iterative refinement over perfect prompts. Start rough, use Select and Edit
   to refine specific elements. Don't try to get it perfect in one shot.

4. Visual vibe descriptions work. "Glassmorphism with pastel gradients" as a
   plain-language description in project context guides every generation
   without constraining implementation.

5. From their system prompt: "Keep things simple and elegant. Take pride in
   simplicity." Complexity is the enemy.

---

## What v0 Gets Right

1. Product surface specificity. Not "a dashboard" but what data it shows, what
   actions users can take, what the key sections are. Specific prompts generate
   40% faster with fewer unnecessary elements.

2. Mobile-first as a constraint, not an afterthought. Specifying "mobile-first,
   maximum 2 columns on mobile" produces fundamentally different (better) layouts
   than "make it responsive."

3. Functional color. "Color code by priority: red urgent, yellow medium, green low"
   beats "use a nice color palette." Color that encodes meaning always outperforms
   color for decoration.

4. Component-first architecture. Break designs into pieces (nav, sidebar, forms,
   sections) then compose. v0 produces better output for focused components than
   full pages in one shot.

5. shadcn/ui + Tailwind as the shared vocabulary. AI tools are specifically
   optimized for this stack. The further you deviate, the more manual guidance
   needed. Use this to your advantage.

6. **v0 Rebuild (Feb 3, 2026)**: v0 is no longer just a prototyping tool:
   - Sandbox runtime imports any GitHub repo
   - Git panel for branches, PRs, production deploys
   - Full-stack apps and agents, not just UIs
   - Production code in your repo, not disposable scaffolding

---

## What Anthropic's Frontend Cookbook Proves

Tested with and without design prompts across multiple generations:

1. Typography prompt alone produces the largest quality jump. Fonts signal
   quality more than any other single element. The cookbook's font categories:
   code aesthetic, editorial, startup, technical, distinctive. Each suggests
   a world, not a specific typeface.

   **Variable fonts (2026)**: Now "best practice, not trend." Single files that
   adjust weight/width/style dynamically are the foundation of responsive typography.
   Use variable fonts as default, not just distinctive static fonts.

2. Calling out project-specific anti-patterns works better than vague positive
   instructions. "Do not fall back to the component-library demo styling" is useful
   when that is the observed default. Permanent ingredient bans merely create a new
   default and can fight an existing brand or platform convention.

3. The distilled aesthetics prompt (typography + color + motion + backgrounds)
   consistently outperforms any single-dimension prompt. All four dimensions
   together create coherence.

4. Convergence is the real enemy. Even with good prompts, models converge on
   new local maxima (Space Grotesk became the new Inter). The cookbook explicitly
   warns: "You still tend to converge on common choices across generations."

5. Cultural and thematic references beat technical specs. "Draw from IDE themes
   and cultural aesthetics" produces more distinctive output than hex codes.

---

## Prompting Patterns That Work (Cross-Platform)

### Pattern 1: Vibe + Constraints
"Modern, editorial feel. Dark theme. Maximum 3 colors. Typography-forward."
Why it works: mood sets direction, constraints prevent sprawl.

### Pattern 2: Reference Quality Level
"Think Stripe/Linear/Framer level design. Make it premium enough to screenshot."
Why it works: anchors quality expectations to known high-bar products.

### Pattern 3: User Context
"Used by field technicians outdoors on mobile. High contrast. Large touch targets."
Why it works: functional constraints produce better design than aesthetic ones.

### Pattern 4: Anti-Pattern Callout
"Keep our existing type system. Avoid the default rounded-card dashboard composition."
Why it works: names the actual convergence risk without imposing unrelated taste.

### Pattern 5: Emotional Target
"The user should feel calm confidence. Like a well-organized workspace."
Why it works: emotional targets produce coherent aesthetic decisions.

### Pattern 6: Decomposition
"Build the nav component first. Then the hero. Then the content grid. Then compose."
Why it works: focused components are higher quality than full-page generations.

---

## Prompting Patterns That Fail

1. Over-specification. Listing exact hex codes, exact fonts, exact spacing values.
   The model follows instructions but loses coherence. It optimizes for matching
   your spec instead of making good design decisions.

2. "Make it modern." Meaningless. Every era thinks it's modern. Be specific about
   what "modern" means to you: clean whitespace? bold typography? dark mode?

3. "Make it look like [specific site]." Produces pale imitations. Better: identify
   WHAT you like about that site and describe those qualities abstractly.

4. Everything at once. "Build a complete dashboard with sidebar, header, 6 chart
   types, user management, settings, and notifications." Quality degrades with scope.

5. No negative examples. Without anti-patterns, the model returns to distribution
   center (generic). Always include what to AVOID.

---

## Accessibility as Design Constraint

From v0's system prompt: WCAG compliance is default, not optional.
This is a design advantage, not a limitation:

- Contrast ratios force better color decisions (no light-gray-on-white).
- Focus states require visible interaction design (not just hover).
- Semantic HTML creates natural information hierarchy.
- Touch targets (44px minimum) prevent cramped, unusable interfaces.

Treat accessibility as a creative constraint that improves output, not a
checkbox that limits it.

---

## The Anti-Convergence Problem

This is the hardest problem in AI-generated design. All models converge toward
their training distribution. Specific manifestations:

- "AI slop aesthetic": purple gradients, rounded cards, Inter font, generic icons.
- Tool-specific convergence: v0 converges on shadcn defaults. Lovable converges
  on its built-in taste. Claude converges on safe, clean layouts.
- Prompt-specific convergence: even good prompts produce similar outputs over time.
  Space Grotesk replaced Inter as the new default.

Mitigations that work:
- Rotate aesthetic references between generations.
- Name recently repeated choices as warnings and require a reason to reuse them.
- Use variant system (abyss, ember, arctic, etc.) to force different starting points.
- Request unexpected combinations: "editorial typography with brutalist layout."
- Include randomization directive: "Make a choice I wouldn't expect."

Mitigations that don't work:
- Just saying "be creative" (too vague, model ignores it).
- Specifying exact alternatives (creates new convergence point).
- Temperature/sampling changes (affects coherence, not creativity).

---

## Design System Architecture for AI Projects

From Lovable and v0's patterns, the optimal structure:

1. Global tokens: CSS custom properties for colors, spacing, typography scale.
   Defined once, referenced everywhere. This is the only place hex codes belong.

2. Component library: use the repository's established library and extension pattern.
   A new project may choose a battle-tested base such as shadcn/ui, but tool familiarity
   is not a product reason by itself.

3. Layout patterns: define page-level compositions separate from components.
   "Dashboard layout" is not a component; it's a composition of components.

4. Variant system: mood-based presets that swap token values.
   NOT new components per variant. Same components, different tokens.

5. Iteration protocol: build piece by piece, compose at the end.
   Never generate a full page in one shot for production work.

---

## Quick Reference: Prompt Template

For any design task, include these in order of importance:

1. WHO uses this and in what context (user, device, environment)
2. WHAT it should feel like (mood, 2-3 adjectives, emotional target)
3. WHAT to avoid (specific unexamined defaults seen in this project or recent output)
4. CONSTRAINTS (max colors, mobile-first, accessibility requirements)
5. REFERENCE quality level (what products/sites set the bar)

Existing brand tokens, fonts, and layout rules are evidence, not over-specification.
For a greenfield direction, avoid premature pixel-level instructions and choose execution
details within the stated constraints.

---

## Contextual heuristics (updated 2026-07-16)

These are options to test, not universal rules:

- Typography contrast can clarify hierarchy, but editorial restraint, platform-native type,
  or a narrow brand scale may be the better fit.
- A dominant color and accent can focus attention, while monochrome or a broader semantic
  palette may better serve the content.
- Layered dark surfaces can explain depth; a deliberately flat field can be cleaner and more
  memorable. Count neither shades nor effects as quality.
- Asymmetry and mixed-width sections can create energy; symmetry and repetition can create
  trust, speed, or calm. Let the message and task choose.
- Motion should explain change, guide attention, or provide feedback. One entrance animation
  is not automatically better than none.
- Components improve repeated behavior. One-off static composition should not be forced into
  component machinery merely to satisfy a ritual.
- Accessibility, responsive behavior, realistic content states, and rendered visual QA remain
  hard constraints because they improve the actual interface rather than enforce a style.

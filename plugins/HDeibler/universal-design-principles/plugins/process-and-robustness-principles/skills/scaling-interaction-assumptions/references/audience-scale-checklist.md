# Interaction scaling — audience scale checklist

A practical checklist for evaluating whether a design will survive growth in audience size and diversity.

## Audience composition

**Who are your current users?** Demographics, technical sophistication, language, geography, organizational role.

**Who will your future users be?** As you scale, expect: more diversity in all the above dimensions; less technical sophistication; more variety of use cases; more cultural and linguistic differences.

**Have you designed for the future audience or only the current?** Audit assumptions baked into the design.

## Cultural and linguistic

**Internationalization status:**
- Are strings externalized for translation?
- Are date, time, number, and currency formats locale-aware?
- Does the layout support right-to-left languages?
- Are any features dependent on English idioms or metaphors?
- Have you tested with locales beyond your launch market?

**Cultural assumptions:**
- Color conventions (red = stop, etc.) that don't transfer.
- Icons that reference culturally specific objects.
- Names, addresses, ID numbers that follow specific cultural conventions.
- Holidays, calendars, time zones that vary.

## Accessibility

**Standards conformance:**
- WCAG 2.1 AA at minimum.
- Tested with screen readers.
- Tested with keyboard-only navigation.
- Tested with high-contrast and reduced-motion preferences.

**Beyond standards:**
- Cognitive accessibility (clear language, predictable patterns).
- Low-vision support (text scaling, contrast).
- Motor accessibility (large touch targets, low-friction interactions).

## Use case diversity

**What use cases is the product designed for?** List explicitly.

**What use cases will users invent that you didn't design for?** Watch for these in early production data.

**What edge cases exist that are rare now but will be common at scale?** A 0.01% case happens 100x daily at million-user scale.

**Do you have a story for each edge case?** Either handle it gracefully or fail safely.

## Technical sophistication

**What level of technical sophistication does the product require?** Be explicit.

**Does it match the broader audience's actual sophistication?** Often not.

**Layered control:**
- Simple defaults for novices.
- Depth available for experts.
- Progressive disclosure for growing feature sets.

## Naming and identifiers

**Name handling:**
- Generous character limits (some names are very long).
- Unicode support (not just ASCII).
- Single-name users (some cultures have just one name).
- Multi-component names (Spanish, Korean, etc.).

**Address handling:**
- Variable line counts (some addresses have 5 lines, some 1).
- International postal codes (varying formats).
- Non-Western address conventions (CJK addresses use a different order).

**ID systems:**
- National IDs vary widely; don't assume a US-style SSN.
- Phone numbers vary in format and length.
- Email is widely supported but not universal in some regions.

## Operations and processes

**Manual processes that depend on team attention:**
- Identify them. They won't scale.
- Plan for automation, distribution, or elimination as the audience grows.

**Onboarding:**
- Hands-on onboarding (calls, demos) doesn't scale beyond a few hundred users per month.
- Self-service onboarding needed for larger audiences.
- Onboarding content needs translation and localization.

**Support:**
- Personal-touch support doesn't scale.
- Build self-service (help center, in-product help, chatbots).
- Reserve human support for complex cases.

**Moderation:**
- Manual moderation doesn't scale beyond small communities.
- Automated detection + community moderation + reactive moderation needed.

## Feature surface

**Number of features:**
- Each new feature adds to discoverability load.
- 10 features can be displayed; 100 cannot. Build progressive disclosure.

**Feature discoverability:**
- New features need active discovery mechanisms.
- Feature announcements, contextual prompts, search.

**Feature deprecation:**
- Some features should be removed as the product matures.
- Unused features are weight; deprecate deliberately.

## Pricing and resource allocation

**Tier structure:**
- Limits should scale with usage, not be flat.
- Enterprise customers shouldn't fit in the same tier as individuals.

**Resource consumption:**
- Some users will use 100x or 1000x what you expect.
- Pricing should reflect cost to serve, not just nominal usage.

## Process at scale

**Hiring:**
- Engineering, support, product, design teams need to grow.
- Plan for the transitions in team structure as you scale.

**Decision making:**
- Decisions made by the founders don't scale.
- Need processes, structures, RFC patterns.

**Knowledge management:**
- Tribal knowledge doesn't scale.
- Documentation, wikis, decision records.

## Audit moments

Repeat the audit at:
- Pre-launch.
- Right after launch (compare to expectations).
- 10x current users.
- 100x current users.
- Major new market entry.
- Major new audience expansion.

The right design choices at one scale may be wrong at another. Re-evaluate.

## Cross-reference

For load-related scaling, see `scaling-load-assumptions`. For the parent principle, see `scaling-fallacy`.

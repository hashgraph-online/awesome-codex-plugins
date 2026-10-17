# Legibility — typeface selection guide

A practical guide to selecting typefaces for specific use cases. Includes general recommendations and notes on when to pick each kind.

## For UI text and body copy

The critical requirement: legibility at small sizes (12–16px) on screens, with sustained reading comfort.

**Inter** (Rasmus Andersson, 2017). Open source. Designed specifically for UI text on screens. Excellent legibility, neutral personality, broad weight range. The default choice for most modern web apps.

**IBM Plex Sans** (IBM, 2017). Open source. Slightly more personality than Inter. Designed as IBM's corporate typeface and works well in product UI.

**Source Sans Pro** (Adobe, 2012). Open source. Generous proportions, good legibility. Slightly older feel than Inter.

**Roboto** (Google, 2011). Open source. Android's system typeface. Good legibility, somewhat geometric personality.

**Open Sans** (Steve Matteson, 2010). Open source. The original "free, friendly, screen-readable" typeface. Still solid; aesthetically dating slightly.

**SF Pro** (Apple, 2014). Apple's system typeface. Free for use on Apple platforms. Excellent legibility, optimized for Apple's rendering.

**Segoe UI** (Microsoft, 2004). Windows system typeface. Good legibility.

**System UI fallback stack:** if you don't want to license a typeface, use the platform default: `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`

## For display and headlines

The critical requirement: visual impact and personality at large sizes (24px+).

**Inter Display** (companion to Inter, optimized for larger sizes). When you want display type that matches the body Inter.

**Söhne** (Klim Type Foundry, 2019). Premium licensed. Strong personality, modern, used by many tech brands.

**Migra** (Pangram Pangram, 2021). Premium licensed. Modern serif with excellent display capabilities.

**Editorial New** (Pangram Pangram). Premium licensed. Editorial-feeling serif.

**Bodoni** (any of several digital revivals). Classic high-contrast serif. Striking at large sizes; unusable at small.

**Recoleta** (LatinoType, 2018). Premium licensed. Distinctive geometric serif.

**Custom commissioned typeface.** For products with strong brand identity and budget for typography commissioning. Vendors include Klim, Pangram Pangram, Hoefler & Co., Commercial Type, and many more.

## For code and structured data

The critical requirement: monospace, character disambiguation, readability at code sizes (13–16px).

**JetBrains Mono** (JetBrains, 2020). Open source. Designed specifically for code reading. Excellent character disambiguation. Programming ligatures.

**Fira Code** (Mozilla, 2014). Open source. Programming ligatures (=> renders as a single arrow). Character disambiguation.

**Cascadia Code** (Microsoft, 2019). Open source. Designed for Windows Terminal and VS Code.

**Source Code Pro** (Adobe, 2012). Open source. Adobe's open-source code typeface.

**SF Mono** (Apple, 2016). Free for Apple platforms. Apple's monospace typeface.

**IBM Plex Mono** (IBM, 2017). Open source. Companion to Plex Sans.

**iA Writer Mono** / **Monaspace** (more recent options). Newer entrants with various design philosophies.

For prose code (inline code in articles), most code typefaces work. For long code blocks, JetBrains Mono and Fira Code are particularly strong.

## For accessibility-first contexts

The critical requirement: maximum character distinguishability for users with vision differences.

**Atkinson Hyperlegible** (Braille Institute, 2020). Open source. Designed specifically for low-vision readers. Maximally distinct character shapes.

**Lexend** (Bonnie Shaver-Troup, 2019). Open source. Designed to improve reading proficiency for readers with dyslexia and other reading challenges. Several width variants.

**OpenDyslexic** (Abelardo Gonzalez). Open source. Specifically designed for dyslexic readers, with weighted bottoms to anchor letters. Some research evidence is mixed; users vary in preference.

These typefaces should be considered for accessibility-focused products and as alternative font options users can switch to.

## For specific cultural / language contexts

**Noto** (Google, ongoing). Open source. The "no tofu" project covering essentially every script. Use for products supporting many languages.

**Source Han Sans / Source Han Serif** (Adobe / Google, 2014–2017). Open source. CJK (Chinese, Japanese, Korean) typefaces.

For Arabic, Hebrew, Thai, Devanagari, and other non-Latin scripts, look for typefaces designed by typographers familiar with the script. Don't apply Latin typeface design instincts blindly to other scripts.

## Decision framework by product type

**Consumer mobile app:** platform-native (SF Pro on iOS, Roboto on Android) for body and UI; custom for hero/marketing if budget allows.

**Web SaaS product:** Inter for body and UI; Inter Display or a licensed display typeface for headlines; JetBrains Mono for code.

**Editorial / content site:** a strong body serif (Charter, Source Serif, Mercury, or IBM Plex Serif) for sustained reading; a complementary sans-serif for UI; a display serif or sans for headlines.

**Documentation site:** Inter or similar for body; JetBrains Mono for code; minimal display use.

**Brand-driven consumer product:** custom or licensed display for hero/brand moments; Inter or system for body and UI.

**Accessibility-focused product:** Atkinson Hyperlegible as the default body typeface; consider giving users a choice.

**Internal enterprise tool:** system typefaces are fine; prioritize functional clarity over brand differentiation.

## Pitfalls to avoid

**Loading too many typefaces.** Each typeface load costs network bandwidth and render time. Two or three typefaces is plenty for almost any product.

**Loading too many weights.** Each weight is its own font file. Stick to 2–4 weights per typeface (often Regular, Medium, Semibold, Bold is enough).

**Not loading variable fonts when available.** Variable fonts (Inter, Recursive, Source Sans 3) ship multiple weights in a single file, dramatically more efficient than loading individual weight files.

**Forgetting fallback stacks.** The user may not load your custom font (slow connection, font-loading error). Always specify a fallback that gives reasonable rendering: `font-family: 'Your Font', -apple-system, BlinkMacSystemFont, sans-serif;`

**Ignoring font-display properties.** Use `font-display: swap` or `font-display: optional` to prevent invisible text during font loading.

**Mixing typefaces from different categories.** A geometric sans (Inter) paired with a heavily decorative display typeface might clash. Look for typefaces designed to coexist (some foundries publish "pairing" suggestions).

## Cross-reference

For the parent principle on legibility, see `legibility`. For sustained-reading typography, see `readability`.

"""Infographic style presets for image generation.

Each style block is a text description inserted into the image generation prompt
to control visual appearance. Selected via IMAGE_STYLE config (default: classic).
"""

STYLE_PRESETS = {
    "classic": (
        'Style: Clean editorial magazine layout. Off-white (#F5F5F0) background with subtle warm gray grid lines. '
        'Bold sans-serif header "MorningAI" in black with a vivid accent color underline. '
        'Each card is a white rectangle with soft drop shadow (4px blur, 10% black), compact spacing between cards. '
        'Use a refined accent palette: deep navy (#1A2744) for card titles, muted teal (#2A9D8F) for bullet icons, '
        'slate gray (#4A5568) for body text. NO gradients, NO textures, NO background patterns \u2014 pure flat white space.\n'
        'Layout: Information-dense. Cards arranged in a balanced grid with tight gutters (16px). '
        'Maximize space for card content (titles and bullet points). '
        'Do NOT display score numbers or score badges \u2014 let card size and content density convey importance.\n'
        'Card design: Card title in 15pt bold navy sans-serif, subtitle in 10pt gray italic. '
        'Bullet points with small teal dot markers, 12pt regular weight, tight line spacing (1.2x). '
        'Thin 1px light gray top-border on each card for subtle separation. '
        'NO icons, NO illustrations, NO decorative elements inside cards \u2014 text only with strong typographic hierarchy. '
        'Pack content tightly \u2014 minimize whitespace within and between cards.'
    ),
    "dark": (
        'Style: Dark mode editorial layout. Deep charcoal (#1A1A2E) background. '
        'Bold sans-serif header "MorningAI" in white (#FAFAFA) with electric blue (#00D4FF) accent underline. '
        'Each card is a dark slate (#16213E) rectangle with subtle 1px border in muted blue (#0F3460), '
        'compact spacing between cards. Accent palette: white (#FAFAFA) for card titles, '
        'soft violet (#7B68EE) for bullet icons, light gray (#B0BEC5) for body text. '
        'NO gradients, NO glow effects \u2014 clean flat dark surfaces.\n'
        'Layout: Information-dense. Cards arranged in a balanced grid with tight gutters (16px). '
        'Maximize space for card content (titles and bullet points). '
        'Do NOT display score numbers or score badges \u2014 let card size and content density convey importance.\n'
        'Card design: Card title in 15pt bold white sans-serif, subtitle in 10pt light gray italic. '
        'Bullet points with small violet dot markers, 12pt regular weight, tight line spacing (1.2x). '
        'Thin 1px muted blue top-border on each card. '
        'NO icons, NO illustrations \u2014 text only with strong typographic hierarchy on dark background. '
        'Pack content tightly \u2014 minimize whitespace within and between cards.'
    ),
    "glassmorphism": (
        'Style: Glassmorphism editorial layout. Soft gradient background blending from pale apricot (#FFF5EE) top-left '
        'to warm cream (#F5E6D3) bottom-right. Bold sans-serif header "MorningAI" in deep brown (#3E2723) '
        'with warm amber (#E8A87C) accent underline. Each card is a semi-transparent frosted white panel '
        '(rgba(255,255,255,0.70)) with backdrop blur effect, rounded corners (16px), and subtle white border '
        '(1px, 30% opacity). Accent palette: deep brown (#3E2723) for card titles, warm taupe (#8D6E63) for bullet icons, '
        'rich brown (#5D4037) for body text. Soft diffused shadows (8px blur, 5% black) behind each card.\n'
        'Layout: Information-dense. Cards arranged in a balanced grid with tight gutters (16px). '
        'Maximize space for card content (titles and bullet points). '
        'Do NOT display score numbers or score badges \u2014 let card size and content density convey importance.\n'
        'Card design: Card title in 15pt bold brown sans-serif, subtitle in 10pt gray italic. '
        'Bullet points with small taupe dot markers, 12pt regular weight, tight line spacing (1.2x). '
        'NO hard borders \u2014 rely on frosted glass contrast for separation. '
        'Pack content tightly \u2014 minimize whitespace within and between cards.'
    ),
    "newspaper": (
        'Style: Classic newspaper editorial layout. Warm cream (#FFF8E7) background with very faint paper texture grain. '
        'Bold serif header "MorningAI" in deep black (#1A1A1A) with crimson red (#B71C1C) thin rule line below. '
        'Each card is separated by thin black hairline rules (1px) \u2014 NO card backgrounds, NO shadows, NO boxes. '
        'Content flows in a column-based newspaper grid. Accent palette: deep black (#1A1A1A) for card titles in bold serif, '
        'dark gray (#333333) for bullet text in serif, medium gray (#666666) for subtitles in italic serif.\n'
        'Layout: Information-dense. Multi-column newspaper grid (2-3 columns). Large stories span full width at top, '
        'smaller stories in side-by-side columns below. Separated by horizontal and vertical hairline rules. '
        'NO cards, NO boxes \u2014 pure typographic layout. Tight column gaps (12px). '
        'Do NOT display score numbers or score indicators \u2014 let column placement and headline size convey importance.\n'
        'Card design: Card title in 15pt bold black serif, subtitle in 10pt gray italic serif. '
        'Bullet points with small em-dash markers, 12pt regular serif weight, tight line spacing (1.2x). '
        'Feels like the front page of a prestigious broadsheet. '
        'Pack content tightly \u2014 minimize whitespace between stories.'
    ),
    "tech": (
        'Style: Tech terminal aesthetic layout. Near-black background (#0D1117) with very faint dot grid pattern '
        '(8px spacing, 5% white). Bold monospace header "MorningAI" in bright cyan (#00FFCC) with a blinking cursor '
        'underscore effect. Each card is a dark panel (#161B22) with 1px border in dim cyan (#1A3A3A), rounded corners (4px). '
        'Accent palette: bright green (#39FF14) for card titles in monospace bold, amber (#FFB000) for bullet markers '
        'as `>` symbols, light gray (#C9D1D9) for body text in monospace. '
        'Each card has a subtle top-left label like `// MODEL` or `// PRODUCT` in dim green (#1A4A1A).\n'
        'Layout: Information-dense. Cards arranged in a balanced grid with tight gutters (16px). '
        'Compact spacing. Maximize space for card content (titles and bullet points). '
        'Do NOT display score numbers or score badges \u2014 let card size and content density convey importance.\n'
        'Card design: Card title in 14pt bold green monospace, subtitle in 10pt gray monospace. '
        'Bullet points with amber `>` markers, 12pt regular monospace, tight line spacing (1.2x). '
        'Thin 1px dim cyan border. '
        'Feels like a developer dashboard or terminal readout. '
        'Pack content tightly \u2014 minimize whitespace within and between cards.'
    ),
}

DEFAULT_STYLE = "classic"

# Appended to every style block to enforce information density.
CONTENT_DENSITY = (
    "\n\nCONTENT RENDERING RULES:\n"
    "- Display EVERY bullet point in FULL — do NOT truncate, summarize, abbreviate, or drop any text.\n"
    "- Each bullet should include specific details (numbers, metrics, dates, names) exactly as provided.\n"
    "- Use compact font sizes to fit all content — shrink text further if needed to avoid omitting any bullet.\n"
    "- Minimize whitespace: tight margins, tight line spacing, tight card gaps.\n"
    "- Fill the entire image area with content — avoid large empty or decorative spaces.\n"
    "- Card titles must display the COMPLETE text including entity name, event subject, and description."
)

# Section continuity instructions appended to style blocks for section (stitch) prompts.
# Overrides header/branding from the main style block so stitched images flow seamlessly.
SECTION_SUFFIX = (
    "\n\nSECTION CONTINUITY RULES (override any conflicting style instructions above):\n"
    "- Do NOT render any top header, banner, branding, or title bar — "
    'no "MorningAI" header or similar. Start directly with the section title.\n'
    "- Top edge: no decorative border, rule, or extra padding — "
    "content starts near the top so the previous section flows into this one.\n"
    "- Bottom edge: no footer, closing border, or extra padding — "
    "the next section will continue directly below.\n"
    "- Keep consistent left/right margins so adjacent sections align when stacked vertically."
)

# Extra section overrides per style (appended after SECTION_SUFFIX).
SECTION_STYLE_OVERRIDES = {
    "newspaper": (
        "\n- Use a SINGLE-COLUMN vertical layout for this section (NOT multi-column). "
        "Stack all items top-to-bottom separated by horizontal hairline rules. "
        "This ensures visual continuity when multiple sections are stitched into one long image.\n"
        "- Maintain the warm cream (#FFF8E7) background with consistent margins."
    ),
}

# Background colors (RGB) per style, used for stitch gap/padding fill.
STYLE_BG_COLORS = {
    "classic":        (245, 245, 240),   # #F5F5F0
    "dark":           (26, 26, 46),      # #1A1A2E
    "glassmorphism":  (255, 245, 238),   # #FFF5EE
    "newspaper":      (255, 248, 231),   # #FFF8E7
    "tech":           (13, 17, 23),      # #0D1117
}

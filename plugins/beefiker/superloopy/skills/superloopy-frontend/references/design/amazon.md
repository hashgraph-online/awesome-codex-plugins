# Amazon — Design Tokens (loopy-native)
> Category: consumer · Signature: dense utilitarian marketplace, navy chrome, one warm-yellow "Buy" gradient

## Signature & atmosphere
Amazon feels like a working warehouse storefront: information-dense, fast, and unglamorous on purpose, optimized so the next click is always obvious. The one recognizable idea is the warm-yellow action — the gold-to-amber gradient pill that means "add to cart / buy now," the single brightest thing on a gray-and-navy page. Chrome is dark slate-navy, links are a businesslike teal-blue, and nothing wastes space; density is a feature, not a flaw.

## Color (hex · --var · role)
- `#ffffff` `--bg` — content canvas; `#0f1111` `--fg` — text (near-black with a hint of slate, not `#000`)
- `#131921` `--nav` — top navigation bar (dark slate-navy); `#232f3e` `--nav-2` — secondary nav / footer band
- `#ffd814` `--primary` — Add-to-Cart yellow (gradient `#f7dfa5`→`#f0c14b` legacy, flat `#ffd814` modern); `#ffa41c` `--primary-2` — Buy Now amber; edge `#fcd200`
- `#007185` `--accent` — link teal-blue (hover `#c7511f` warm orange); `#565959` `--muted` — secondary text
- `#d5d9d9` `--border` — control outline; `#f7f8f8` `--card` — quiet section fill; `#eaeded` zebra row
- `#b12704` `--price` — deal/price red-orange; `#cc0c39` `--destructive`; `#007600` in-stock green; `#de7921` star/rating gold
- Contrast: `--muted #565959` on white ≈ 5.7:1. The yellow CTA is the only saturated fill on the page — it must stay the brightest element.

## Typography
- Stack: `"Amazon Ember", Arial, sans-serif`; substitute Inter or Arial. A pragmatic, highly legible UI sans — never decorative.
- H1 28px / 400 / 1.30 · H2 21px / 700 / 1.30 · H3 18px / 700 · Body 14px / 400 / 1.45 · Price-large 28px / 400 (with 13px superscript fraction) · Link 14px / 400 · Caption 12px / 400
- Signature: sizes run small and tight to maximize density; bold (700) marks section headers and prices, not display drama. There is no big hero type — the product grid is the hero.

## Spacing, radius, depth, motion
- Base 4px; scale 4 · 8 · 12 · 14 · 16 · 20 · 28; padding is tight, rows pack close.
- Radius: 4px inputs · 8px buttons/cards · 100px the rounded "pill" search and CTA buttons · 50% icon badges. Modern Amazon rounds CTAs fully; structural cards stay at 4–8px.
- Depth = thin borders + light gray, mostly flat: cards separated by `1px solid #d5d9d9` and `#f7f8f8` fills, not shadows. Dropdowns/flyouts get `0 2px 5px rgba(15,17,17,0.15)`. Buttons use a 1px darker border + subtle inner highlight rather than elevation.
- Motion: minimal — instant hover state changes, ~150ms; this is a transactional UI, not an animated one.

## Components (key)
- Add to Cart CTA: bg `#ffd814` / text `#0f1111` / border 1px `#fcd200` / padding 8px 10px / radius 100px (or 8px legacy) / hover `#f7ca00`. Buy Now: bg `#ffa41c`, border `#ff8f00`. Text stays dark on yellow — never white.
- Product card: white, 1px `#d5d9d9` (or borderless in grid), radius 8px; title link 14px `#0f1111` (hover `#c7511f`), price 28px `#b12704` with superscript cents, star rating in `#de7921` glyphs, "In Stock" 14px `#007600`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the page dense with small 14px body and tight 4px-base spacing; use the warm yellow/amber gradient pill as the single loudest action; put dark text on the yellow CTA; use thin gray borders for separation.
- Don't: white-out the layout with airy whitespace and 18px+ body — Amazon's density is intentional and the "give it more breathing room" instinct fights the brand. Don't use white text on the yellow button (contrast + brand both break). Don't reach for big drop-shadow cards; separation is borders and zebra fills. Don't make the CTA blue — blue is for links, yellow/amber is for buying.

## Example component prompts
- "Add-to-Cart button: `#ffd814` fill, 1px `#fcd200` border, dark `#0f1111` label Amazon Ember 14px, radius 100px, padding 8px 10px; Buy Now sibling `#ffa41c` fill, `#ff8f00` border."
- "Product card on `#fff`: title link 14px `#0f1111` hover `#c7511f`; price 28px `#b12704` with 13px superscript cents; star row in `#de7921`; 'In Stock' 14px `#007600`; 1px `#d5d9d9` separators, radius 8px."
- "Top nav bar `#131921`, search pill radius 100px with `#ffd814` search button; links teal `#007185`; secondary nav band `#232f3e`."

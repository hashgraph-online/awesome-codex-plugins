---
name: easybrandkit
description: Get a product's real brand from its website before you design, build or animate anything for it. Saves the logo files cut from the page, the colors and fonts the site uses, its first screen, and its app store icon and screenshots. Use it whenever the user asks for a landing page, video, slide deck, social post, ad, mockup or UI for a product, company or website and you know its address.
---

# easybrandkit

Guessed brand colors and redrawn logos make work look fake at first glance. easybrandkit opens the real site in a headless browser, reads it the way the browser draws it, and saves what you need in one folder.

## Get the kit

```bash
node <skill>/scripts/easybrandkit.js <url> --out brand/<name>
```

`<skill>` is this skill's folder. The script needs Node 22 or newer and Chrome, Chromium, Edge or Brave on the machine; it installs nothing and needs no API key. A run takes 20 to 90 seconds. Give it the product's home page; an address deeper in the site is read from the home page anyway, because blogs and help centers often wear another theme. For an app, an App Store or Google Play link works too: the kit gets the store icon and screenshots, and the brand comes from the website the listing names. A social profile link is refused; find the product's website instead.

## Use it

1. Read `brand/<name>/BRAND.md` before you write any code, copy or image prompt.
2. Use the hex values as given. The `button` color is what the site uses for its main actions, `logo` is the color its logo is drawn in, `heading` and `link` are its text colors, and `header`, `footer` and `surface` are its backgrounds.
3. Use the logo files as they are. Do not redraw, recolor, retype or crop a logo. Each PNG is cut on the background it sits on (listed next to the file), so place it on that color or one close to it. A `.svg` listed next to a logo is the same logo as a vector with no background: use it when the logo has to sit on another color or be shown large. A logo listed on "a picture" was cut with part of a photo or pattern around it, so prefer its `.svg` when it has one.
4. Use the font families named. If one is not available to you, pick the closest free font and tell the user which one you used.
5. "Words on the page" holds the product's own title, description, headings and button labels. Write headlines and feature lines from them; do not invent claims, numbers or customers the page does not state.
6. `screen-01.png` is the site's first screen at 2x. Use it as a reference for the look, or as the screenshot inside a browser or device frame.
7. For an app, use the store icon and screenshots (`appstore-*`, `googleplay-*`) as they are.
8. `brand.json` holds the same facts for scripts, with every file's size. `_brand.yml` holds the name, logo, colors and fonts in the brand.yml format: for a Quarto document, website or deck, set `brand: brand/<name>/_brand.yml` in its YAML; for a Shiny for Python app, pass that path to `ui.Theme.from_brand()`.
9. `card.png` shows the whole kit on one picture. Show it to the user before you build on the kit, so they can see that the logo and colors are right.

## When it goes wrong

- If BRAND.md lists no logo, or the colors look like a cookie wall or a loading screen, tell the user what you got instead of guessing. Slow sites can take `--timeout 240`.
- If the site blocks headless browsers, ask the user for the logo file and the main colors.
- Never present a color or a logo as the brand's own when it did not come from the kit or from the user.

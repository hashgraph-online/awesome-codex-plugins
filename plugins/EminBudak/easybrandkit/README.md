# easybrandkit

Get a website's real logo files, colors, fonts and first screen, saved as a brand kit your coding agent can read.

```bash
npx easybrandkit@latest linear.app
```

![The brand kit easybrandkit made from linear.app](.github/assets/linear-card.jpg)

Ask a coding agent for a landing page, a launch video or a pitch deck for a product and it guesses: a blue that is almost right, a logo retyped in Inter. easybrandkit opens the real site in a headless browser, finds the logos the site itself draws, cuts each one out on the background it sits on, and writes down the colors and fonts the page actually uses. Your agent reads one Markdown file and works from facts.

Read the story behind it on my blog: [easybrandkit: A Brand Kit for Coding Agents](https://eminbudak.com/blog/easybrandkit-brand-kit-for-coding-agents/).

## What you get

```
easybrandkit-linear.app/
  BRAND.md               the kit, for people and agents
  brand.json             the same, for scripts
  _brand.yml             the name, logo, colors and fonts for Quarto and Shiny
  card.png               the kit on one picture, like the one above
  logo-01.png            the header logo, on its real background
  logo-01.svg            the same logo as a vector, when the page draws it as SVG
  logo-02.png            the footer logo
  screen-01.png          the first screen at 2x, without the cookie bar
  appstore-icon.png      the app icon at 1024 px, when the site links to its app
  appstore-shot-01.png   and up to five store screenshots
  x-profile.jpg          the profile pictures of the accounts it links to
  FACTS.md               with --facts: what the site claims, each claim with its page
  facts.json             the same, for scripts
  pages/pricing.md       with --facts: the text of each page read
```

- **Logos** come from the header, the footer and links to the home page, as the browser paints them: SVG, image or CSS. Partner strips, customer logos, payment badges and closed menus are skipped. Each cut is at least 240 px on its short side and has no transparency, so it can go straight into an image model or a video. When the page draws a logo as SVG, inline or as an SVG file, the vector is saved next to the cut with the page's colors written into it and no background. A logo in the page body that sits on a photo is skipped: that is an event's or a campaign's lockup, not the brand's logo.
- **Colors** are the solid colors of the site's buttons, headings, text links, header, footer and large surfaces, plus the color the logo itself is drawn in. Tints, grey buttons and white language switches do not count.
- **Fonts** are the families the page uses for headings and body text.
- **Words**: the page title and description, its headings in reading order and what its buttons say, so copy can start from the product's own words instead of made-up claims.
- **App stores and profiles**: when the site links to its App Store or Google Play listing, easybrandkit saves the app icon at 1024 px and up to five screenshots. Linked X, YouTube and LinkedIn accounts give their profile pictures.
- **Icons, preview images, the web manifest and social links** are listed with their URLs.

| | |
| --- | --- |
| ![Notion](.github/assets/notion-card.jpg) | ![Airbnb](.github/assets/airbnb-card.jpg) |

## Use it with your agent

easybrandkit ships as an [Agent Skill](https://agentskills.io). Install it once and your agent runs it by itself when you ask for something for a product:

```bash
npx skills add EminBudak/easybrandkit
```

That covers Claude Code, Codex, Cursor and the other agents the [`skills`](https://github.com/vercel-labs/skills) CLI supports. In Claude Code you can add it as a plugin instead:

```
/plugin marketplace add EminBudak/easybrandkit
/plugin install easybrandkit@easybrandkit
```

In GitHub Copilot CLI, install it from the repo:

```bash
copilot plugin install EminBudak/easybrandkit
```

Then ask as usual:

> Make a 30 second launch video for linear.app

The skill carries its own script, so it installs nothing else and needs no API key.

## Use it from the command line

```
npx easybrandkit <url> [options]

  --out <dir>      where to save (default: ./easybrandkit-<host>)
  --facts          also read the site's own claims from its home, pricing,
                   customers, security, integrations and about pages
  --no-stores      skip app store listings and social profiles
  --json           print brand.json instead of a summary
  --timeout <s>    give up after this many seconds (default: 120, or 240
                   with --facts)
```

The address can be a website or an App Store or Google Play listing. A listing gives the app icon and screenshots, and the brand is read from the website the listing names. A social profile is not a brand's site, so easybrandkit refuses one and asks for the website.

Installed globally (`npm install -g easybrandkit`), the command is `easybrandkit`. npx keeps the copy an earlier run fetched, so `npx easybrandkit@latest` is how you get a newer version.

It needs Node 22 or newer and Chrome, Chromium, Edge or Brave. Set `CHROME_PATH` to pick the browser. There are no npm dependencies and nothing is downloaded: easybrandkit drives the browser you already have over the Chrome DevTools Protocol, with a throwaway profile.

## The site's own claims

With `--facts`, the kit also lists what the site says about itself. Each claim is quoted as the page states it, with the page it is on and the time it was read.

```bash
npx easybrandkit@latest linear.app --facts
```

- Numbers the page draws as figures, with the words under them ("135+ currencies and payment methods supported"), or states in a sentence ("Linear powers over 50,000 product teams").
- Testimonials with the person's name, role and company.
- Customers from rows of customer logos, from customer stories and from testimonials.
- Plans with their prices and terms, as the pricing page shows them.
- Integrations from the integrations page.
- Security standards the site names, such as SOC 2, ISO 27001, GDPR or HIPAA, each with the sentence that names it.
- Ratings, questions and answers, and company details from the page and its JSON-LD.

Besides the home page, easybrandkit reads up to five pages it finds in the site's menu and footer: pricing, customers, security, integrations and about. It reads them one at a time with a pause between them, and only the ones the site's robots.txt lets tools read. `FACTS.md` lists the claims and `facts.json` holds the same for scripts. `pages/` keeps the text of each page read, so every claim can be checked in its context. A run takes one to three minutes.

No model is involved. Rules find the claims, and a claim they cannot tie to a name, a label or a price is left out. Prices are what the page showed from where it was read, so they can differ by country.

Text from a web page can carry instructions written for AI agents. `FACTS.md` quotes the pages and `pages/` keeps their text in fenced blocks, both say that this text is data, and the skill tells your agent never to follow it.

It is made for work that has to stay true to a product: a competitor profile, a comparison page, a pitch deck, or launch copy with real numbers and real customers.

## With claude-code-video-toolkit

[claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) keeps each brand in `brands/<name>/`. Make a kit in the toolkit's folder, then start `/brand` and point it at the kit:

```bash
npx easybrandkit@latest stripe.com --out brand-kit
```

```
/brand New brand: Stripe. The kit is in brand-kit/, use it for the colors, the fonts and the logo.
```

`/brand` shows how it mapped the colors for you to confirm, then writes `brand.json` and the logo files. The toolkit's templates put the logo on their own backgrounds, so point `/brand` at the kit's `.svg` logo when there is one, or ask for a transparent cut of the PNG.

## With Quarto and Shiny

Every kit has a `_brand.yml` in the [brand.yml](https://posit-dev.github.io/brand-yml/) format, which Quarto and Shiny read to theme documents, websites, slides and apps. It holds the brand's name and site, its logos (each as the SVG when the page draws one, else as the PNG), the page's colors named for where it uses them, and the font families for text and headings. The `medium` logo, the one Quarto puts in a navbar, on slides and in a PDF, is the site's own header or footer logo that shows on the page's background. The button color becomes `primary`, and the page's own background and text colors become `background` and `foreground`. A family on Google Fonts gets `source: google`, so Quarto and Shiny load it from there. Any other font keeps its name as a system font and shows only where it is installed. A color or font the page doesn't show is left out, so Quarto and Shiny keep their own default for it.

Point a Quarto project at the kit in `_quarto.yml`, or a single document in its front matter:

```yaml
brand: easybrandkit-stripe.com/_brand.yml
```

A Quarto website paints its navbar in the `primary` color. For a dark logo like Stripe's, `background: light` under `website: navbar:` keeps it readable.

In Shiny for Python, `ui.Theme.from_brand("easybrandkit-stripe.com/_brand.yml")` makes the theme, and Shiny for R reads the same file through bslib. You can also copy `_brand.yml` to the root of the project or app, together with the logo files it names.

## How it works

1. Opens the home page in a headless browser on a 1600x900 desktop screen. An address deeper in the site is read from the home page, because a blog or a help center often wears another theme.
2. Scrolls to the bottom and back, so lazy sections and footer logos load.
3. Reads one DOM snapshot with layout and computed styles. Logo candidates are images, outermost SVGs and elements named "logo" or "brand". They are kept only in the page header, in the page footer, inside a link to the home page, or when they are named after the brand.
4. Brings each logo to the middle of the screen, finishes its fade-in, hides whatever paints over it (a popup backdrop, the next line of text) and cuts it out with a margin of its own background. The background is read from that margin's pixels, not from the CSS. A logo drawn as SVG is also written out as a vector, with the page's styles on it and its scripts removed.
5. Hides floating overlays and takes the first screen at 2x.
6. Fetches store listings and profile pictures over HTTPS from a fixed list of hosts, and refuses private addresses.

## Limits

- A site that answers with a bot check or a login wall gets no kit: easybrandkit stops and says so, instead of saving the check page's colors.
- Instagram, Facebook and TikTok serve nothing without a login, so they are not asked.
- A logo drawn into a canvas or a WebGL scene is not found.
- Colors come from what the home page shows. A main color used on one button of another page will not show up.
- `--facts` reads text as the page shows it. A claim drawn inside an image or a video, one shown only on hover or in a closed tab, a plan behind a currency or region switch, and a menu link that appears only on hover are not seen.

## License

MIT

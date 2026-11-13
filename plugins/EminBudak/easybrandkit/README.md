# easybrandkit

Get a website's real logo files, colors, fonts and first screen, saved as a brand kit your coding agent can read.

```bash
npx easybrandkit@latest linear.app
```

![The brand kit easybrandkit made from linear.app](.github/assets/linear-card.jpg)

Ask a coding agent for a landing page, a launch video or a pitch deck for a product and it guesses: a blue that is almost right, a logo retyped in Inter. easybrandkit opens the real site in a headless browser, finds the logos the site itself draws, cuts each one out on the background it sits on, and writes down the colors and fonts the page actually uses. Your agent reads one Markdown file and works from facts.

Read the story behind it on my blog: [easybrandkit: A Brand Kit for Coding Agents](https://eminbudak.com/blog/easybrandkit-brand-kit-for-coding-agents/).

## Requirements

- Node.js 22 or newer.
- Google Chrome, Chromium, Edge or Brave, which opens the site and draws the card. It has been tested with Google Chrome only: 155 on Ubuntu 26.04, 157 on Ubuntu 22.04 and the ones GitHub's ubuntu-22.04, ubuntu-24.04 and ubuntu-latest runners come with. No test has run with Chromium, Edge or Brave. Chrome runs in its sandbox unless easybrandkit runs as root, where the sandbox does not start: on Linux, Google Chrome's own package sets the sandbox up, and a container has to let it start, as Docker does with `--security-opt seccomp=unconfined`. easybrandkit looks for all four on your PATH on Linux and where macOS installs them; on Windows it looks only where Chrome and Edge install themselves. Set `CHROME_PATH` to use another build, as a path or a name on your PATH. Before any work, a run starts the browser and waits for its first answer. One that cannot be started, as a folder, a link to nothing or a file this user may not run, or that ends before it answers, stops the run, and the last line names its path, what is wrong with it or how it ended and the line it printed that says why, and what to do. When that line says that the sandbox could not start or that there were too many files open, another browser would not help, and the last line says what does. A browser that printed only the lines Chrome prints on every start, such as those of its D-Bus code, has none of them quoted, unless one of them says that there were too many files open. The browser takes its pipe to easybrandkit on its file descriptors 3 and 4, so a program that `CHROME_PATH` names and that starts the browser has to hand those on. A run with one that does not stops before any work as well, and the last line says so.
- Linux, where it is tested: on Ubuntu 22.04, on Ubuntu 24.04 and on GitHub's ubuntu-latest runner, on every push and before every release. This release has also run on Ubuntu 26.04 with Node.js 22.22, and on Ubuntu 22.04 with Node.js 22.23. It is written for macOS and Windows as well, but this release has not been run on either.
- Room on the disk for the kit and the one before it, as the earlier kit stays until the new one is in place: a kit took 0.5 to 3 MB on the sites tried, an app's store pictures included. On the same sites the browser's profile took 4 to 18 MB in the temp folder while the run lasted.
- On Linux, a temp folder whose path leaves the browser room for the socket it makes there: 66 bytes at most for Google Chrome, and a few less for Chromium and Edge. A run in a longer one stops and says how much shorter `TMPDIR` has to be. The path may not have a `:` in it either (see below).
- Network access to the site and, unless you give `--no-stores`, to the store listings and social profiles it links to. Installing it needs the network, and `npx easybrandkit@latest` asks npm for the newest version each time it runs. No ffmpeg, no account, no API key and no npm dependencies.

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

- Logos come from the header, the footer and links to the home page, as the browser paints them: SVG, image or CSS. Partner strips, customer logos, payment badges and closed menus are skipped. Each cut is at least 240 px on its short side and has no transparency, so it can go straight into an image model or a video. When the page draws a logo as SVG, inline or as an SVG file, the vector is saved next to the cut with the page's colors written into it and no background. A logo in the page body that sits on a photo is skipped: that is an event's or a campaign's lockup, not the brand's logo.
- Colors are the solid colors of the site's buttons, headings, text links, header, footer and large surfaces, plus the color the logo itself is drawn in. Tints, grey buttons and white language switches do not count.
- Fonts are the families the page uses for headings and body text.
- The words are the page title and description, its headings in reading order and what its buttons say, so copy can start from the product's own words instead of made-up claims.
- When the site links to its App Store or Google Play listing, easybrandkit saves the app icon at 1024 px and up to five screenshots. Linked X, YouTube and LinkedIn accounts give their profile pictures.
- Icons, preview images, the web manifest and social links are listed with their URLs.

| | |
| --- | --- |
| ![Notion](.github/assets/notion-card.jpg) | ![Airbnb](.github/assets/airbnb-card.jpg) |

## Use it with your agent

easybrandkit ships as an [Agent Skill](https://agentskills.io). Install it once and your agent runs it by itself when you ask for something for a product:

```bash
npx skills add MakersMCP/easybrandkit
```

That covers Claude Code, Codex, Cursor and the other agents the [`skills`](https://github.com/vercel-labs/skills) CLI supports. In Claude Code you can add it as a plugin instead:

```
/plugin marketplace add MakersMCP/easybrandkit
/plugin install easybrandkit@easybrandkit
```

In GitHub Copilot CLI, install it from the repo:

```bash
copilot plugin install MakersMCP/easybrandkit
```

Then ask as usual:

> Make a 30 second launch video for linear.app

The skill carries its own script, so it installs nothing else and needs no API key.

## Use it from the command line

```
npx easybrandkit <url> [options]

  --out <dir>      where to save (default: ./easybrandkit-<host>, the host
                   without www or a port; ./easybrandkit-appstore-<id> and
                   ./easybrandkit-googleplay-<id> for store listings)
  --facts          also read the site's own claims from its home, pricing,
                   customers, security, integrations and about pages
  --no-stores      skip app store listings and social profiles
  --json           print brand.json instead of a summary
  --timeout <s>    give up after this many seconds (default: 120, or 240
                   with --facts)
```

The address can be a website or an App Store or Google Play listing. A listing gives the app icon and screenshots, and the brand is read from the website the listing names. A social profile is not a brand's site, so easybrandkit refuses one and asks for the website.

Run it again with the same `--out` and the new kit takes the place of the earlier one there, but only once the run has ended well. Files of your own in that folder stay, unless one has the name of a file the kit writes. While the new kit is made the earlier one stays, so the disk needs room for both. Two runs that end at the same moment with the same `--out` take turns putting their files in, so the folder holds one whole kit, the one put in last. Sites on one host, such as two ports of localhost, get the same default folder, so give each its own `--out`.

A run that fails, is refused, or is stopped with Ctrl-C or a kill leaves the folder as it was: an earlier kit stays whole, and a folder the run would have made is not made. Such a run exits with a status other than 0, and a kit you find in the folder after it is the earlier one. The line under the title of its `BRAND.md` names the address it was read from and the date, in UTC, and `capturedAt` in its `brand.json` gives the time. After two kinds of run that also exit with a status other than 0, the kit in the folder is the new one:

- A run that saved its kit but could not print its summary or `brand.json`, say to a full disk, exits with 1, and its last line says the kit was saved.
- A run stopped in the moment after it saved its kit ends by the signal, and its last line says so, as in `stopped by SIGINT, after the new kit was saved in <folder>`. With `--json`, that stop prints no error on stdout, and `brand.json` may not have been printed. A stop that comes as the process ends, once its summary is printed, leaves no such line.

So a run that printed its summary, which starts with `Saved the`, or `brand.json` with `--json`, has saved its kit, whatever its exit status.

A folder removed while a run makes its kit, by you or another program, ends the run, and its last line says what was removed.

Installed globally (`npm install -g easybrandkit`), the command is `easybrandkit`. npx keeps the copy an earlier run fetched, so `npx easybrandkit@latest` is how you get a newer version. To stop a run started with npx, press Ctrl-C or send the signal to its whole process group (`kill -- -<pgid>`). A kill sent to the npx process alone may not reach easybrandkit: where `/bin/sh` is dash, as on Debian and Ubuntu, the run goes on and puts its kit in place if it ends well.

Nothing is downloaded to run it: easybrandkit drives the browser you already have over the Chrome DevTools Protocol, with a throwaway profile (see [Requirements](#requirements)). It talks to the browser through a pipe of its own, so the browser opens no port that another program on the machine could reach. Before any page is opened, the browser is told to refuse downloads for as long as it runs, and a browser too busy to answer that ends the run. One that does not take it saves a download into the throwaway profile, which goes with the run, so nothing reaches your Downloads folder.

Chrome hands an address that is not a web address, such as mailto: or news:, to a program of the system without asking, so a site could start the mail program on this machine with what it wrote in the address. On every system, a page's own move to such an address, by its script, a refresh, a form or a link, is cancelled before the browser acts on it, in the page and in its frames of the same site, and the browser opens no window a page asks for without a click. A frame's first address, a frame the page makes and then sends to such an address by its script, a redirect to one, and a frame of another site that moves to one still reach the browser. On Linux the browser hands those to the desktop's portal over the session bus, or, with no session bus, to xdg-email or xdg-open, which it finds through PATH. So there easybrandkit starts it with no display and a session bus where nothing listens: DISPLAY is unset, and WAYLAND_DISPLAY and DBUS_SESSION_BUS_ADDRESS name sockets in its throwaway profile that are never made. Left unset, either would lead a program to the desktop's own in XDG_RUNTIME_DIR. It also starts the browser with stand-ins first on its PATH for xdg-open, xdg-email, xdg-settings, x-www-browser, www-browser and sensible-browser: links in that profile to `true`, which does nothing. A `:` in the temp folder's path would part that folder from the rest of PATH, so a run in such a temp folder stops before the browser starts and says so. A browser installed as a snap or a Flatpak runs in a sandbox of its own, which can have other programs by those names. easybrandkit tells such a browser by its path and by the links on the way to it, and for it the kit's notes do not say that an address that reached it was not opened; no test has run with one. On macOS and Windows the browser asks the system instead, so there those can still reach the system's own program, the mail program for mailto:. No test has run on either. The kit's notes name the first three such addresses easybrandkit saw, a frame's redirect among them, though not one a frame of another site moves to by its script, and when the address you give redirects to one, the run fails and says so.

### If a run is killed outright

`kill -9`, `taskkill /F` or a power cut give a run no chance to clean up. It can leave:

- A folder whose name starts with `.easybrandkit-part-`, in the kit's folder, or in the folder above it when the run was making the kit's folder. On Windows, so can a run that ends while another program, such as a virus scanner, still holds a file in that folder open.
- A `.easybrandkit-swap` file in the kit's folder, when the kill came as the files moved in.
- In the temp folder, the browser's profile, in a folder whose name starts with `easybrandkit-chrome-`, and the folders the browser makes there itself, whose names start with `com.google.Chrome.` (`org.chromium.Chromium.`, `com.microsoft.Edge.` or `com.brave.Browser.` for the other browsers, with a dot in front in older versions).

The browser does not stay running. It ends within a second or so once the kit's process is gone, also when only that process was killed, as `kill -9 <pid>` does: the pipe the kit drives it through closes then.

What removes them:

- A later run that ends well removes a part folder once its process is gone and nothing in it has changed for 15 minutes, when that run puts its kit in the folder that holds the part folder or in a folder right inside that one, and this user can open it.
- The next run there takes over the `.easybrandkit-swap` file, or names it in its error when it cannot be removed.
- No later run removes what is in the temp folder. Remove those folders yourself.

Moving its files into place takes a moment. Killed in that moment, a run leaves the earlier kit's files it had moved aside in the `.earlier` of its part folder, which is in the kit's folder by then, and no run removes those. If its own `brand.json` had not come in yet, the kit's folder is left without one, with some of the new files in it or none. A later run refuses that folder and says what to do:

1. Move the files in that `.earlier` back into the kit's folder, and those in its `pages`, when it has one, into the kit's `pages`, replacing any files of the same name there, which are that run's.
2. Remove the files the refusal names as that run's. The run wrote those names down before its first move, as names the folder did not hold, so none of them is a file of the earlier kit or of yours.
3. Run again.

A folder that held no kit when that run began has no earlier files to move back. A later run refuses it and names the files that run left there: remove them and run again.

A move into place that fails and cannot be undone is rare; its error names the folder that holds the earlier kit's files.

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

Besides the home page, easybrandkit reads up to five pages it finds in the site's menu and footer: pricing, customers, security, integrations and about. It reads them one at a time with a pause between them, and only the ones the site's robots.txt lets tools read. A page past the home page is read only while 45 s of the run's `--timeout` are left, so a short `--timeout` can leave some of them or all of them out, and `FACTS.md` names the pages it skipped. `FACTS.md` lists the claims and `facts.json` holds the same for scripts. `pages/` keeps the text of each page read, so every claim can be checked in its context. A run takes one to three minutes.

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

1. Opens the home page in a headless browser on a 1600x900 desktop screen, with downloads refused. An address deeper in the site is read from the home page, because a blog or a help center often wears another theme. When the home page cannot be read, the address given is read instead.
2. Scrolls to the bottom and back, so lazy sections and footer logos load.
3. Reads one DOM snapshot with layout and computed styles. Logo candidates are images, outermost SVGs and elements named "logo" or "brand". They are kept only in the page header, in the page footer, inside a link to the home page, or when they are named after the brand.
4. Brings each logo to the middle of the screen, finishes its fade-in, hides whatever paints over it (a popup backdrop, the next line of text) and cuts it out with a margin of its own background. The background is read from that margin's pixels, not from the CSS. A logo drawn as SVG is also written out as a vector, with the page's styles on it and its scripts removed.
5. Hides floating overlays and takes the first screen at 2x.
6. Fetches store listings and profile pictures over HTTPS from a fixed list of hosts, and refuses private addresses.
7. Writes the kit into a folder of the run's own, inside the kit's folder or next to it, and moves the files into place only once the run has ended well, so a run that fails or is stopped changes nothing there. A browser that is closed or crashes on the way, or a file that cannot be written, fails the run. A card that the browser cannot draw while it runs is told in the kit's notes.

## Limits

- A site that answers with a bot check gets no kit: easybrandkit stops and says so, instead of saving the check page's colors. A login page that answers 401 or 403 is refused by its status. One served with 200 is read like any other page, so look at `card.png` before you use a kit made from one.
- An address that answers with an HTTP error (400 or above), also after a redirect, gets no kit, and neither does one that cannot be opened, that gives no answer in 30 s, or that moves on to a page that cannot be opened or to a blank page: easybrandkit stops and says which address answered what, instead of saving the error page's logo and colors.
- Those refusals are for the address you give. When the page that fails is one easybrandkit chose to read, the run goes on with what it has and the kit's notes say so. A store listing whose website answers with an error, cannot be opened or answers with a bot check keeps the app icon and screenshots from the listing, with no logos, colors, fonts, first screen or card, as a listing that names no website does. If none of the listing's pictures could be downloaded either, the run fails and says so. An address deeper in a site whose home page fails that way is read as given, so the kit's name, header and colors can differ from the home page's, and if that fails too, the error names the address you gave. A run that goes on like this has ended well, so its kit takes the place of an earlier one in the folder.
- A run that uses up its `--timeout` on such a page fails and says to give it more time, and an earlier kit stays. So does a run whose `--timeout` leaves no time to wait for a page that shows nothing yet.
- easybrandkit reads a page on this machine or on a private network (a loopback, private or link-local address, or a name such as localhost) only when the address you give is on that same host and port. A page it would choose there, a store listing's website, a menu page or the home page of a deeper address, is not opened when easybrandkit's own lookup finds it there. When only the browser finds it there, as when the browser's lookup of the name gives another address than easybrandkit's did, the page is opened, so the program there gets the request, and nothing of it is read. A page that a site leads to there, by a redirect or by its own script, also one the page moves to once easybrandkit has read it, is not read either. The names of this machine itself, such as localhost, 127.0.0.1 and [::1], count as one host on one port, so a local site that sends its visitors from one of them to another is read. With `--facts`, it does not follow a robots.txt that redirects there either, and then reads no page past the home page. For the address you give, the run fails and says where it led; for a page easybrandkit chose, the run goes on without it, and the notes or `FACTS.md` say so. Only web pages are opened, so a link a site gives to a file on this machine is not followed.
- Whether a page is there is told by the address the browser says it got the page from, and by every address easybrandkit's own lookup finds for its name. Through a proxy the browser does not say where the page came from, so the lookup alone decides, and a name it cannot find within 5 s counts as not there. An address that is merely not public does not count: not the 198.18.0.0/15 that a proxy in fake-ip mode gives every name, and not a NAT64 address of a public one. A proxy that also gives every name a fake IPv6 address in fc00::/7, as sing-box does when its `inet6_range` is set, makes every name count as on a private network, since no rule can tell such an address from a real one. Then give the address the site leads to, as a page on the host and port you give is always read.
- On a busy machine the browser itself can be slow to start, to open its tab, to answer the kit's connection to that tab or to answer when the kit tells it to refuse downloads. The run waits for each of these as long as its `--timeout` allows, and so it does for a program `CHROME_PATH` names that takes long before it starts the browser. If that runs out, the run fails, an earlier kit stays, and the last line says what did not answer and to give the run more time. When the disk that holds the temp folder is full, the run says so within seconds instead, and what to do.
- The page's headings and button labels are read while the browser tab answers, for a few seconds past `--timeout` at most. Those not read by then are left out of the kit, and its notes say so and to give the run more time.
- A page too large to read gets no kit, and the run says so. easybrandkit takes no answer from the browser over 128 MB, and the snapshot of a very large page can be bigger. With `--facts`, a menu page that large is skipped and named, and the pages after it are read.
- With `--facts`, a menu page that answers with an error is skipped, and `FACTS.md` and the summary name it with the reason. When the home page's text cannot be read, no other page is read either, and `FACTS.md` says that no page could be read and why. A deeper address read as given because its home page could not be read is filed in `FACTS.md` as the page given, its text in `pages/given.md`, and the home page is named there as not read.
- With `--facts`, rules that do not finish in their time, 30 s at most, list no claims: `FACTS.md` and the summary say so, and `facts.json` has a `claimsError` field. A page built to keep them busy costs that, and `pages/` still holds the text of each page read.
- Instagram, Facebook and TikTok serve nothing without a login, so they are not asked.
- A logo drawn into a canvas or a WebGL scene is not found.
- Colors come from what the home page shows. A main color used on one button of another page will not show up.
- `--facts` reads text as the page shows it. A claim drawn inside an image or a video, one shown only on hover or in a closed tab, a plan behind a currency or region switch, and a menu link that appears only on hover are not seen.

## License

MIT

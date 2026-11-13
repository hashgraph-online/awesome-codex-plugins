# launch-film

A 20 to 40 second launch film made from a product's own website or App Store page: its real logo, colors, fonts and screens, set in motion with music and sound effects.

```bash
npx launch-film@latest linear.app
```

![Stills from the film launch-film made for linear.app](.github/assets/linear-sheet.jpg)

[Watch the film](.github/assets/linear-film.mp4) (28 seconds). It was made with the command above and nothing else: no brief, no edits.

Tools that make videos with code usually start from a brief: you describe the product, its colors and the style you want. launch-film starts from the site. [easybrandkit](https://github.com/MakersMCP/easybrandkit) reads the logo, colors, fonts and first screen in a headless browser, the page's own headline and section titles become the film's words, and a look is picked to suit the brand. You get an MP4 at 1920x1080, rendered on your machine with Chrome and ffmpeg. There is no account, no API key and nothing is uploaded.

Read the story behind it on my blog: [launch-film: A Launch Film From Your Website](https://eminbudak.com/blog/launch-film-from-your-website/).

## Requirements

- Node.js 22 or newer.
- ffmpeg and ffprobe 4.4 or newer, Ubuntu 22.04's 4.4.2 included. To render a film ffmpeg needs libx264, the only H.264 encoder launch-film uses, which Ubuntu's ffmpeg has; `plan`, `check`, `frames` and `stills` need none. The filters it uses are ffmpeg's own, and so is the AAC encoder. `brew install ffmpeg` and `winget install ffmpeg` give a new enough one, and so does `sudo apt install ffmpeg` on Ubuntu 22.04, Debian 12 or newer. Set `LAUNCH_FILM_FFMPEG` and `LAUNCH_FILM_FFPROBE` to use another build, each as a path or a name on your PATH, and set both: launch-film does not look for ffprobe next to the ffmpeg you name.
- Google Chrome or Chromium, which draws the film frame by frame and the stills, and reads the site's words for a plan when the page's HTML does not hold them; `check` and `frames` start none. Chrome runs in its sandbox unless launch-film runs as root, where the sandbox does not start: on Linux, Google Chrome's own package sets the sandbox up, and a container has to let it start, as Docker does with `--security-opt seccomp=unconfined`. It has been tested with Google Chrome only: 155 on Ubuntu 26.04, 157 on Ubuntu 22.04 and the one GitHub's ubuntu-latest runner comes with. No test has run with Chromium. launch-film looks for both on your PATH and where macOS installs them; on Windows it looks only where Chrome installs itself. Set `LAUNCH_FILM_CHROME` or `CHROME_PATH` to use another build, as a path. easybrandkit, which reads the brand, takes only `CHROME_PATH`.
- A font on the machine for letters outside the Latin alphabet and for most Vietnamese letters with tone marks, as launch-film fetches only the faces Google Fonts makes for the other Latin letters. A letter no font has is drawn as a box, as Japanese is on a server with no Japanese font; `fonts-noto-cjk` gives Debian and Ubuntu one.
- [easybrandkit](https://github.com/MakersMCP/easybrandkit), which reads the brand when you plan from a site's address: install it with `npm install -g easybrandkit`, or launch-film runs it with `npx -y easybrandkit@0.4.1`. This release was tested with easybrandkit 0.4.1, and runs one on your PATH before it tries npx, whatever its release. Set `LAUNCH_FILM_EASYBRANDKIT` to use a copy of your own.
- Linux, where it is tested: on GitHub's ubuntu-latest runner (Ubuntu 24.04 with ffmpeg 6.1 at this release), on every push and before every release. This release's tests have also passed on Ubuntu 22.04 with its ffmpeg 4.4.2, in a container as root and without Chrome, so the tests that need Chrome or a user other than root were skipped there, and it has run on Ubuntu 26.04 with ffmpeg 8.0 and on Ubuntu 22.04 with Chrome. It is written for macOS and Windows as well, but this release has not been run on either.
- Room on the disk for the files of a run and those of the run before it, as the earlier files stay until the new ones are in place, and, while a render sets the film's sound, for one more copy of the new film, as the best of its encodes is kept beside the next until that one is measured. A 30 second film takes 8 to 25 MB, by its look, and its frames, stills and check 3 to 10 MB more; until the render ends, its work files take 30 to 90 MB in the temp folder. Each Chrome that renders the film or draws the stills keeps a profile of about 3 MB there. The ones that read the site for a plan, easybrandkit's and the one that reads the words, also keep what the site loads, and easybrandkit's keeps what Chrome downloads for its own features as well: up to 50 MB on a small test site.
- Network access for a plan, which reads the site unless you give it both `--brand` and `--words`, and for npx to fetch easybrandkit when it is not installed. A render and stills fetch the film's typefaces from Google Fonts and keep them in `~/.cache/launch-film/fonts`; offline they use the ones kept there, and the system's own for the rest. `check` and `frames` need no network. Installing it needs the network, and `npx launch-film@latest` asks npm for the newest version each time it runs. No account and no API key.

`npx launch-film@latest doctor` checks Node, Chrome, ffmpeg and ffprobe. It starts Chrome once as a render does, in its sandbox unless launch-film runs as root, and exits with 1 when Node is older than 22, when it finds no Chrome or Chrome does not start, as when its sandbox cannot, or when ffmpeg or ffprobe is missing, cannot be started or is older than 4.4; the line of each program says what is wrong with it. It does not check libx264, the fonts, easybrandkit or the network.

A command looks at the ffmpeg, ffprobe and Chrome it runs before any work. One that is not there, is a folder or a link to nothing, may not be run, is on a disk mounted noexec, is an empty or a text file, a script whose interpreter is missing, a program whose loader or a library it needs is missing, or a program for another processor or system stops the command at once, with no folder made and nothing left in the temp folder, in a message that starts `launch-film needs ffmpeg` (or ffprobe, or Chrome) and names the variable or the PATH entry that gave it, what is wrong with it and how to point to one that works. On PATH it is the one the system would start, past a folder and a file it may not run. ffmpeg and ffprobe are asked their version as well, so one that answers as another program is refused too. Chrome is asked only when it is a program itself: Google Chrome's own `google-chrome` is a script that starts it, so a library missing behind it shows only once a render or stills start Chrome, which then fails in the loader's words, the folder as it was. A plan starts launch-film's own Chrome only to read the page's words when its HTML does not hold them, and looks at that Chrome only then: one that cannot be started is told of in those words, and the plan goes on with the words of the HTML, as it does when no Chrome is found. easybrandkit looks at the Chrome it starts itself. A plan looks at ffmpeg and ffprobe only for a store's address, as it runs them only then. A command given wrong is told so first, and so is a plan given a `--words` or a `--brand` it cannot read, or one without `--brand` into a folder whose brand/ holds files but no brand.json, where easybrandkit would make no kit. With no Chrome to be found at all, the message is "Chrome was not found."

## Use it with your agent

launch-film ships as an [Agent Skill](https://agentskills.io). Your agent gets the brand, picks a look, writes the scenes from the page's words, renders the film, checks it and hands you the MP4, with the launch pictures if you ask for them.

```bash
npx skills add MakersMCP/launch-film
```

That covers Claude Code, Codex, Cursor and the other agents the [`skills`](https://github.com/vercel-labs/skills) CLI supports. To install it by hand instead:

In Claude Code, as a plugin:

```
/plugin marketplace add MakersMCP/launch-film
/plugin install launch-film@launch-film
```

or as a skill folder:

```bash
git clone https://github.com/MakersMCP/launch-film
cp -r launch-film/skills/launch-film ~/.claude/skills/
```

In Codex:

```bash
cp -r launch-film/skills/launch-film ~/.agents/skills/
```

In Cursor:

```bash
cp -r launch-film/skills/launch-film ~/.cursor/skills/
```

In GitHub Copilot CLI, install it from the repo:

```bash
copilot plugin install MakersMCP/launch-film
```

Then ask as usual:

> Make a launch video for linear.app

## Use it from the command line

```
npx launch-film <url> [options]          read the brand, plan the film, render it
npx launch-film plan <url> [options]     read the brand and write film.json only
npx launch-film render <film.json>       render a film.json after editing it
npx launch-film frames <film.mp4>        save stills of each clip and a contact sheet
npx launch-film check <film.mp4>         measure a render and write pass or fail
npx launch-film stills <url|film.json>   launch pictures at store and site sizes
npx launch-film looks | types | icons <word> | doctor

  --out <dir>           folder for the brand, film.json and the film (default ./launch-film-<site>)
  --look <name>         launch, aurora, gridline, pop or journal (default: picked from the brand)
  --seconds <n>         aim for 20 to 40 seconds (default 30)
  --aspect 9:16         a vertical film (default 16:9)
  --brand <dir>         use an easybrandkit folder you already have
  --words <file>        use a words.json you already have instead of reading the page
  --easybrandkit <cmd>  the easybrandkit to run (default: LAUNCH_FILM_EASYBRANDKIT, one on PATH, else easybrandkit with npx)
  --no-music, --no-sfx  plan the film without the music bed or the sound effects (a render reads "music" and "sfx" in film.json)
  --jobs <n>            clips rendered at once, 1 to 4 (default 2)
  --keep                keep the work files, each clip's MP4
  --output <file>       where render writes the film (default film.mp4 next to film.json)
  --verbose             also print what easybrandkit says as it works
```

A command refuses what it would not read, by name, before anything runs: an option it does not take (the refusal lists the ones it does), an option with no value after it, an argument past the ones it reads, and a value it cannot use: an `--aspect` other than 16:9 or 9:16, a `--seconds` outside 20 to 40 for a plan, a `--jobs` other than 1 to 4, a value given to `--keep` or `--verbose`, and a size or frame rate of 0 in `--expect`. A render refuses an `--output` it could not write the film to before any clip renders: a folder, a name with no extension, a name that starts with `.launch-film-`, or a kind of file ffmpeg cannot put H.264 video and AAC sound in, such as .webm.

Where launch-film runs for others, who give it their film.json or brand.json, set `LAUNCH_FILM_CONFINE=1`. Each of those files may then name only files in its own folder: a name that leads out of it, by an absolute path, by climbing out with `..` or through a link in the folder, is refused before anything renders, whether or not a file is there. A kit that a plan copies, one given with `--brand` or the folder's own brand/, is held to its folder the same way: a link in it that leads out of it, to a file or a folder, is refused before anything is copied, and so is a brand/ that is itself a link out of the folder. Links that stay inside are followed. A track or a picture in the folder is refused as well when it is a list of other files that ffmpeg would open wherever they are, whatever it is named: an HLS playlist, a DASH manifest, an ffconcat list or an IMF composition, told by the marks ffmpeg looks for in a file's first bytes, and past the ID3 tags it skips there. `check` and `frames` refuse a film that is such a list the same way, before ffprobe opens it. Without it, as when you run it yourself, a film.json can name a track or a picture anywhere on the machine, and a plan copies what a kit's links lead to.

A page in Chrome can try to hand an address that no page shows to a program of the machine: Chrome hands a `mailto:`, `news:` or `snews:` address to the system without asking, so a site that goes to one as it loads would open your mail program. On Linux every Chrome launch-film starts, and the one easybrandkit starts for a plan, finds stand-ins first on its PATH, in a temp folder of the run's own, for xdg-open, xdg-email, x-www-browser, www-browser and sensible-browser, the programs Chrome hands such an address to there, and for xdg-settings, which Chrome asks first which program takes it. They start nothing. A temp folder on a disk mounted noexec cannot run them, and one whose path holds a `:` cannot put them first on PATH, which reads the `:` as the end of a folder, so in either a render, stills, the one-go command and a plan that may start a Chrome, as any plan not given both `--brand` and `--words` may, stop before any work: set `TMPDIR` to another folder. They stop the same way where the temp folder's path takes more than 66 bytes, too long for the socket Chrome makes in a folder there: that is 66 characters of ASCII, and fewer where it has other letters, as each of them takes two bytes or more. On a Linux desktop Chrome first hands such an address to the desktop's portal over the session bus, and the portal opens the program set for it, so there every Chrome launch-film starts, and easybrandkit's, is also given a session bus that leads nowhere, a socket in its own temp folder that is never made, and no display: no X display, and as its Wayland display another path there that is never made, since a Wayland display left unset is looked for where the desktop's is. On macOS and Windows Chrome hands such an address to the system, which opens the program set for it, and launch-film has found nothing that keeps it from that: no switch of Chrome's, no preference of its profile and no call of the DevTools protocol stops these three kinds of address. No test of this has run on macOS or Windows. On Linux a plan says in a note which such addresses the pages it read asked for, easybrandkit's and its own, the first five of them and how many more times one was asked for. On macOS and Windows its note covers only a page that launch-film's own Chrome read, which it reads only when the page's HTML lacks its words, and not the pages easybrandkit read.

A page can also make Chrome save a file, of any size, into the Downloads folder of the user it runs as, where nothing removes it. Every Chrome launch-film starts refuses downloads, and so does the Chrome of easybrandkit 0.4.1, which this release runs to read the site for a plan. The Chrome of easybrandkit 0.4.0, which one on your PATH or named by `LAUNCH_FILM_EASYBRANDKIT` can still be, does not: on Linux launch-film gives it a Downloads folder in the run's own temp folder, which goes with the run, and on macOS and Windows a site it reads can save a file into your Downloads folder.

A run leaves this behind:

```
launch-film-linear.app/
  brand/              easybrandkit's kit: logos, colors, fonts, first screen
  words.json          the words read from the page
  film.json           the plan, which you can edit and render again
  film.mp4            the film
  film.timeline.json  each clip's start and length, which frames and check read the cuts from
  frames/sheet.jpg    two stills from every clip, for checking
  check/CHECK.md      what launch-film check measured, when you run it
  stills/             the launch pictures, when you run launch-film stills
```

A run makes its files in a folder whose name starts with `.launch-film-part-`, inside the folder it writes to (or next to it, when the run makes that folder), and moves them in only once it has ended well. A run that fails, is refused or is stopped with Ctrl-C or SIGTERM leaves the folder exactly as it was: the earlier plan, brand, film, frames, stills and check stay, and nothing is added. One that fails or is stopped while it works says in its last line which folder it left as it was, or did not make; one refused before it starts says only why. A check that finds the film fails is not a failed run: it writes its report. A run that ends well replaces the files it makes and leaves the others, so a new plan leaves the earlier film.mp4, film.timeline.json, frames, stills and check, which no longer match it, until you render the film and run frames, stills and check again. Two runs that put their files in one folder at once take turns, and the one that ends later replaces the other's files. An earlier file you made read-only is not replaced, and a brand, frames or stills folder you may not write in takes no new files: the run names it, a render or a plan before its work, and leaves the folder as it was. That does not hold for the files inside brand/: a plan replaces that folder whole, so a plan given a kit with `--brand` takes read-only files there away with the rest. An earlier file of another user's that you may not write is replaced where its folder lets you replace it: one you may write in does, unless it has the sticky bit, as /tmp has, where the run names that file as it names a read-only one. A frames, stills or check folder that is a link to a folder elsewhere takes the new files there, in the folder it leads to, as a plain folder would, while a brand/ that is a link is replaced by a folder of its own and the kit it led to is left alone. An earlier file that is a link is replaced by a plain file, and what it led to is left alone; a new file has the mode a new file gets on your system, not the one you may have given the earlier file. A run killed outright, with SIGKILL, can leave its `.launch-film-part-` folder behind; a run that ends well in the same place later removes it, once the killed run's process is gone and nothing in the folder has changed for 15 minutes. Such a folder that another user owns, in a folder you share such as /tmp, is left alone. If the run was killed while it moved its files in, that folder can hold earlier files it had moved aside: it is then kept instead, under a name that starts with `launch-film-kept-`, with a `launch-film-kept.txt` in it that lists them, so you can put back the ones you want. A render's clips and Chrome's profiles go in the system's temp folder, and are removed when the run ends. On Linux, a run stopped while easybrandkit reads the brand also ends the Chrome that easybrandkit started and removes that Chrome's profile. The next run that renders removes the work files a killed run of yours left there.

## Launch stills

```bash
npx launch-film@latest stills linear.app --for ph,og,x,play,chrome
```

`stills` makes the pictures a launch needs, at the exact size each place asks for, from the film's look, the brand's logo and the site's real screen. Give it a site and it plans the film first, or give it a `film.json` you already have, so the pictures match the film you edited.

| file | size | for |
| --- | --- | --- |
| `ph-1.png` | 1270x760 | Product Hunt gallery: the logo, the promise and the site's screen |
| `ph-2.png` up to `ph-6.png` | 1270x760 | Product Hunt gallery: the film's own scenes, from the headline to the logo close, as many as the film has |
| `ph-thumbnail.png` | 240x240 | Product Hunt thumbnail: the app icon, or the logo |
| `og.png` | 1200x630 | `og:image`, the picture a shared link shows |
| `x.png` | 1600x900 | a post on X |
| `play-feature.png` | 1024x500 | the Google Play feature graphic |
| `chrome-small.png` | 440x280 | the Chrome Web Store small promo tile: the logo alone |
| `chrome-marquee.png` | 1400x560 | the Chrome Web Store marquee tile: the logo and the screen, no text |

Every picture is an opaque PNG, since Google Play refuses transparency. `stills/STILLS.md` lists them with what each one is for. Leave out `--for` to get all of them.

## Check a render

```bash
npx launch-film@latest check film.mp4 --expect 1920x1080@30 --seconds 30 --lufs -14 --cues cues.json
```

An agent can't watch a film or listen to it. `check` measures it with ffmpeg's own filters and writes down what it found:

- `CHECK.md`: PASS or FAIL, a table of the checks, the stretches it found and every cut.
- `check.json`: the same, for a program.
- `sheet.png`: a frame from each shot, numbered, with its cut's time and whether it lands on the beat.
- `wave.png`: the sound's outline and loudness over time, with the cuts, beats, bars and hits marked.

| check | passes when |
| --- | --- |
| size and frame rate | they match `--expect` |
| length | it is within half a second of `--seconds`, or inside a range like `28-32` |
| black, still picture, silence | there is no long stretch of one inside the film |
| loudness | the integrated loudness is within 1 LU of `--lufs` |
| true peak | it is -1 dBTP or lower (up to 0 is a warning) |
| clipping | the sound never reaches full scale or sits flat on its peak |
| cuts on beats | every cut is within one frame of a beat in `--cues` |

Holds are often meant, so they don't raise alarms: up to 1 s of black at the start and 2 s at the end, an end card that stands still for up to 6 s, and a still picture shorter than 2 s inside the film all pass. A longer stretch is a warning, not a failure, unless most of the film is black or silent. Give the stretches you meant with `--allow 27-30` and they count as meant. `check` exits with 1 when the film fails, so a script can stop on it.

The cuts come from the timeline launch-film writes next to its film. For a film made elsewhere, give them with `--cuts 3.2,7.5` or a JSON file. Without either, `check` finds the hard cuts in the picture, and lists soft changes (a crossfade, or something starting to move) without judging them.

### cues.json

`--cues` reads a track's beats as frame numbers. A tool that fits music to a cut can write it, or you can write it by hand:

```json
{ "fps": 30, "beats": [0, 15, 30, 45], "bars": [0, 60, 120], "hits": [825], "frames": 960, "bpm": 120 }
```

- `fps` and `beats` are needed. Every number is a whole frame at `fps`, and frame 0 is the film's first frame.
- `bars` (each bar's first beat), `hits` (accents an edit should land on, like the drop), `frames` (the track's length) and `bpm` are optional.
- Other keys are ignored, so a tool can add its own.

## How it works

1. easybrandkit opens the site in headless Chrome and saves its logos cut on their own background, its button, heading and surface colors, its font families and its first screen at 2x. Given an App Store or Google Play listing, it saves the app's icon, screenshots and rating, and reads the site the listing names.
2. The page's title, description, headline and section titles are read, with the line under each section title. Every word in the film comes from there.
3. A first film is planned without a brief: the name and its promise, the real screen in a browser window, the page's own sentence as a headline, three sections as feature cards, a number the page states (or an app's store rating), the app's store screenshots, and the logo close with the site's address. It is written to `film.json`.
4. Each clip is an HTML page with one paused timeline. launch-film gives Chrome the page and its pictures itself, so a page reaches nothing else on the machine or the network. Chrome is given each file in one go, of at most 64 MB, so a larger picture is given as a copy of what the page shows of it, no larger than the page draws it, and smaller where even that would be more than 64 MB. The stills get the site's screen as their window shows it, the top of a tall one. A virtual clock steps it frame by frame in headless Chrome, so every frame is drawn for its time however long drawing takes, and the frames go to ffmpeg. Two clips render at a time.
5. The music and every sound effect are synthesised in code for this film: the groove starts on the second clip, each clip lasts whole bars so cuts land on the beat, and the logo lands on a hit. What plays before the groove is set a few dB under it, so the film opens quieter than its body, but with music. There are no samples. A track of your own named in film.json takes the music's place. The sound is then brought to -14 LUFS, the loudness YouTube, X and most social apps play at, with its true peak at -1.5 dBTP or under. ffmpeg measures it first, and one gain sets it to that level, so it keeps the rise and fall it was made with: the drop of a track of yours stays over its build by nearly as much as in the track. A limiter on the sound at four times its sample rate holds the peaks the gain raises. The film is then measured as `check` measures it, and encoded again while it is off: the gain moves toward -14, and the limiter is set lower when the film's true peak passed -1.7 dBTP, a fifth of a dB under the -1.5 it keeps to, as the AAC encoder can lift a sharp hit by two and a half dB. Of these encodes, six at most, the one nearest -14 LUFS at -1.5 dBTP or under is kept. So a film measures within a few tenths of -14, one whose sound is mostly short peaks too, such as the bed turned down to 0.2 under the effects or a track of sparse hits. A sound with too little in it to get there under that peak, such as a click every few seconds and nothing else, comes out quieter.
6. Stills from each clip and a contact sheet are saved, so you (or your agent) can look before sharing. `launch-film check` measures the film as well: its size, length, black or still stretches, silence, loudness, peaks, and whether the cuts land on the beat.

## film.json

```json
{
  "brand": "brand/brand.json",
  "look": "launch",
  "aspect": "16:9",
  "clips": [
    { "kind": "scene", "bars": 2, "scene": { "type": "opener", "title": "Linear", "text": "The product development system for teams and agents" } },
    { "kind": "screen", "bars": 2, "image": "brand/screen-01.png", "mode": "pan" },
    { "kind": "scene", "bars": 2, "scene": { "type": "headline", "title": "Purpose-built for planning and building products with AI *agents*" } },
    { "kind": "scene", "bars": 2, "scene": { "type": "number", "value": "40,000+", "text": "product teams" } },
    { "kind": "logo", "bars": 2, "logo": "brand/logo-01.png", "site": "linear.app" }
  ]
}
```

| kind | what it shows |
| --- | --- |
| `scene` | type in motion; 37 types such as `opener`, `headline`, `features`, `number`, `rating`, `steps`, `quote`, `compare`, `chat` (list them with `launch-film types`) |
| `screen` | a screenshot in a browser window coming in from depth; `mode: "zoom"` with a `box` moves the camera onto one part of it |
| `shots` | two or three store screenshots side by side, coming in from depth |
| `phone` | a phone's screen capture in a drawn phone |
| `scroll` | a tall page scrolling in a window |
| `logo` | the logo close, from an easybrandkit logo file or an app icon |

Words between asterisks are set in the brand's accent color. A bar is one bar of the look's music, about two seconds; give `seconds` instead if you prefer.

`music` is `true` for the look's own bed, `false` for none, `{ "volume": 0.55 }` for the bed at another level (0 to 2), or the path of a track of your own, from film.json's folder or absolute. A track plays from the first frame in place of the bed: it is brought to about the bed's level (lower when its peaks would clip), cut at the end of the film and faded out over its last second, and the sound effects play over it as they do over the bed. A track that is missing, is not a file (a folder, a pipe, or a link to something no longer there), cannot be read, has no sound, is silent or is shorter than the film is refused before anything renders, with a message that says what to give instead and, for a relative path that is not there, where it was looked for. When ffmpeg will not open a track, or ffprobe a picture or a film to check, for a reason of its own, as a build that refuses some names does, the message gives its words. [musicfit](https://github.com/MakersMCP/musicfit) makes a track exactly the film's length with its hit on the beat you choose, such as the logo close. Run in the film's folder, `npx musicfit@latest track.mp3 --length 29.333 --hit 24 --fps 25 --out music` writes `music/fitted.wav`, with the film's length and the last clip's start from film.timeline.json, and `"music": "music/fitted.wav"` plays it. The message that refuses a short track gives that command with the track it refused, both numbers and the folder, each quoted for the shell where its name needs it, so that a shell runs it as it is from any folder. When the track it refused is an earlier fit, as `music/fitted.wav` is once the film has grown, the command fits the track that fit was made from again, as musicfit's cues.json beside the fit names it: by its path when it is beside the fit or beside film.json, and otherwise as a word in angle brackets, quoted as a path is so that a shell reads nothing in it, for you to put that path in place of. With `LAUNCH_FILM_CONFINE` set, only a track in film.json's folder is named by its path.

## Looks

| look | | suits |
| --- | --- | --- |
| `launch` | a near-black stage with depth and soft light, type rising out of masks, one bright accent | developer tools, SaaS, dark sites |
| `aurora` | frosted glass cards over a slow aurora of the brand's colors | AI products, consumer apps, vivid brands |
| `gridline` | a light paper page with hairline columns and giant numerals, one signal color | B2B, finance, light sites |
| `pop` | full color fields that change with the cuts, sticker cards with hard shadows | consumer apps, food, games, social |
| `journal` | warm paper, newspaper rules, large serif headlines | editorial brands, publications |

## Limits

- The film says what the site says. A page with few section titles gives a thin first plan; edit `film.json` or let your agent write the scenes.
- A brand typeface that Google Fonts does not have is replaced by the look's own, and the render says which. launch-film asks Google for it again a day later.
- Letters outside the Latin alphabet, such as Cyrillic or Japanese, and most Vietnamese letters with tone marks are drawn in the machine's own fonts, not in the film's typefaces, and no note says so.
- easybrandkit needs a site that opens in a headless browser. A bot check or a login wall gets no kit, and a social profile is not a brand's site.
- A 30 second film takes one to three minutes to render on a laptop. On a machine too busy for Chrome, a clip can fail with "Chrome did not answer ... within 60 s" or "the page did not load within 30 s": render again once it is less busy, or with `--jobs 1`. On one short of memory, two clips at once can run Chrome out of it, and a clip fails with "Chrome's page crashed", "Chrome could not capture frame ...", "Chrome was stopped by SIGKILL" or "ffmpeg was stopped by SIGKILL", each followed by "most often because the system ran out of memory": render again with `--jobs 1`, which needs less. A `LAUNCH_FILM_CHROME` that names something that cannot be run, such as the folder Google Chrome.app, stops the render before it starts, with that reason.
- The music is simple by design. To use your own track, give its path as `music` in film.json and render again. The cuts still fall on the bars of the look's own tempo (launch 112 BPM, aurora 96, gridline 120, pop 124, journal 90), so a track's beats meet every cut when a bar of the look holds a whole number of the track's beats, with its hit on a cut such as the logo close: four at the look's own tempo, two at half of it, eight at twice it, or five for a 120 BPM track in aurora. So read the track's tempo with `npx musicfit@latest track.mp3 --analyze` before you plan the film, and fit the track once the film is rendered.

## License

MIT. The icons are Phosphor Icons (MIT); see [THIRD_PARTY.md](THIRD_PARTY.md) for them and for the fonts fetched at render time.

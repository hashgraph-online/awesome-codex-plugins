# Formats: what each kind of video needs

Read this when the brief names a kind of video ("an explainer", "a Short", "a tutorial intro") or when it is vague about structure. Each format gives a beat sheet that works, the route for each beat, and the checks that matter most for it. Times are for the length shown; scale them to the brief.

Rules that hold for every format:

- **Something is on screen and moving by 0.3 s.** Viewers decide in the first second.
- **One idea per beat, one hero moment per video.** Put the hero moment in the beat sheet with a time.
- **Readable time.** Hold any line for at least (words / 3) + 0.5 s. Body text 40 px or more at 1080p, headlines 90 px or more.
- **The last 1.5-2.5 s hold still** on the final message, so it can be read and so a loop or end screen does not cut it.
- **Sound shapes the cut.** Put accents on beat starts; a quiet bed under everything is better than silence.

## 2D explainer (YouTube, course, product page)

Length 30-120 s, 16:9. Route: HyperFrames for everything; Three.js only for a single 3D object that explains the idea better than a diagram.

| Beat | Time (60 s) | What is on screen |
|---|---|---|
| Hook | 0-4 s | The question or the surprising fact, in big type, with one moving element |
| Setup | 4-14 s | The problem shown as a simple diagram that builds piece by piece |
| Idea | 14-38 s | Three steps, each its own beat: icon or shape, a 3-7 word label, one motion that shows the change |
| Example | 38-52 s | One concrete case: numbers counting up, a before and after, or a UI mock |
| Takeaway | 52-60 s | One sentence, held still |

Techniques: build diagrams with SVG paths that draw on (`stroke-dashoffset`), reveal labels word by word, move a highlight box instead of cutting, keep one consistent visual metaphor through the whole video. Use a narrow palette: background, ink, one accent for "the thing that matters".

Checks: every label spelled exactly; nothing overlapping when the diagram is complete (pull a still at the end of each build); the accent colour used only for the key element.

## Maths and algorithms

Length 20-180 s. Route: HyperFrames for titles and layout; equations with MathJax (it outputs SVG, which you can animate term by term) or KaTeX (HTML and CSS, vendor its fonts and stylesheet); for heavy maths animation (transforming equations, graphs that morph, geometric proofs) use [Manim Community](https://github.com/ManimCommunity/manim) (`pip install manim`; `MathTex` and `Tex` also need a LaTeX install such as TeX Live or MiKTeX) to render a transparent clip at the video's size and frame rate, then place it as a video layer.

| Beat | What is on screen |
|---|---|
| Question | The problem stated plainly, maybe one figure |
| Intuition | A picture before any symbols: a shape, a graph, a moving point |
| Symbols | The equation appears term by term, each term coloured to match the part of the picture it describes |
| Step | One transformation per beat, never two at once |
| Result | The final form, boxed or highlighted, held still |

Techniques: colour-code terms consistently (the same colour for the same quantity everywhere), animate one change at a time, keep the previous line visible but dimmed so the eye can compare. For an algorithm, show the data structure and move a pointer through it in sync with the code line highlighted beside it.

Checks: every symbol correct (pull stills and read them); colours consistent across beats; Manim clips rendered at the video's frame rate and size so they do not stutter or blur.

## Tutorial and screen-recording intros

Length 5-20 s for an intro, plus lower thirds and callouts over a recording. Route: HyperFrames with the recording as a `<video>` layer; trim and normalise the recording with ffmpeg first (`references/ffmpeg.md`). When the video is mostly the recording, with several cuts, a voice-over and music, cut it on a timeline with the edit pack (FilmCraft, `edit/recipes/film_timeline.sh`), mix the voice over the music with ducking (SoundCraft, `edit/recipes/sound_mix.sh`), and use HyperFrames for the titles and callouts layered on top.

| Element | How |
|---|---|
| Title card | 3-6 s: topic in big type, the tool's name or version smaller |
| Chapter cards | 1.5-2.5 s between sections, same layout every time |
| Callouts | A box or arrow that grows onto the UI element being discussed, with a 2-5 word label, held while it is talked about |
| Zoom-ins | Scale and position the recording layer to the area of interest, eased, then back out |
| Keyboard keys | Small key caps that pop on when a shortcut is used |

Checks: callouts land on the right UI element at the right time (pull stills at each callout); text never covers what is being explained; the recording is sharp after zoom (record at a higher resolution than the output if you zoom more than 1.5x).

## Storytelling, skits and character pieces

Length 15-90 s. Route: HyperFrames with SVG characters or cut-out illustrations; simple 3D props from the Three.js template or the 3D pack. A skit made from recorded takes is an editing job: cut the takes in FilmCraft and mix dialogue, music and sound effects in SoundCraft (edit pack). Lip sync and full character animation are outside this skill: use pre-made Lottie or Rive characters ([references/ecosystem.md](ecosystem.md)) seeked by time, or keep characters still and let the camera, captions and props carry the motion.

| Beat | What is on screen |
|---|---|
| Situation | Where we are and who is there, in one wide shot |
| Want | What the character wants, shown not told (a thought bubble, a goal on screen) |
| Obstacle | Something gets in the way; the biggest motion of the piece |
| Turn | The twist or punchline; give it a beat of stillness first |
| Out | The result, and a caption or title |

Techniques: one camera move per shot (push, pan or parallax across layered SVG), hold a reaction for half a second before the next line, put dialogue in captions or speech bubbles timed to the voice. For a skit, timing is the joke: leave a pause of 0.3-0.6 s before the punchline.

Checks: captions match the voiceover word for word and in time (time them from `npx hyperframes transcribe voice.wav` word timestamps); characters never cut off at the frame edge; every shot change motivated by the story.

## Vertical Shorts and Reels (9:16)

Length 15-60 s, 1080x1920. Route: as for the content, but laid out for a phone.

Safe zones at 1080x1920: keep essential text and faces out of the top 288 px (status bar, search, account name), the bottom 672 px (title, caption, channel name, sound and buttons drawn by the app), the right 192 px (like, comment and share buttons) and the left 64 px. These are conservative working values that cover the overlays YouTube Shorts, Instagram Reels and TikTok draw; the platforms publish their safe areas as reference graphics (for example [Google Ads: square and vertical video](https://support.google.com/google-ads/answer/9128498)) and move their buttons over time, so check a current screenshot when an element sits near an edge. That leaves a box of about 824 x 960 px, from 288 to 1248 px down: put the main text there. Measure it with `scripts/bounds.py still.png --bg "#rrggbb" --safe top=288,bottom=672,left=64,right=192`.

| Beat | Time (30 s) | What is on screen |
|---|---|---|
| Hook | 0-2 s | The payoff or the question, huge type, motion in the first frame |
| Promise | 2-5 s | What the viewer gets if they stay |
| Body | 5-25 s | 3-5 quick beats, a change every 2-4 s (cut, zoom, new word) |
| Payoff | 25-28 s | The answer or the result |
| End | 28-30 s | Either hold the payoff still for the last 1.5-2.5 s (the default rule above), or, when the brief asks for a loop, end on a frame that leads back into the first one so replays feel seamless. Pick one and write it in SPEC.md |

Checks: nothing important inside the unsafe zones (pull stills and check positions); captions large (60 px or more) and on screen the whole time someone speaks; the first frame works as a cover.

## Data stories and charts

Length 15-60 s. Route: HyperFrames with SVG or canvas charts (D3 for layout is fine; animate with GSAP from `t`).

Beats: the claim in words, the axes and context, the data drawing on, the one number that matters highlighted, the takeaway. Animate bars and lines from the baseline, count numbers up with the final value exact, label directly on the chart instead of in a legend.

Checks: every number on screen matches the brief exactly at its final frame; axes start where honesty demands (bar charts from zero); units shown.

## Product launch and feature announcements

Length 15-60 s. Route: HyperFrames for type and UI; the 3D pack or Blender for the product itself.

Beats: the problem in one line, the product reveal (the hero moment), 2-3 features each with one visual and a 3-6 word label, the call to action (name, URL or "available now"), held still. Show the real UI where possible: a recreated UI mock in HTML stays sharp at any zoom.

Checks: product name and URL spelled exactly; feature labels consistent in style; the reveal lands on a sound accent.

## Logo stings and titles

Length 2-8 s. Route: HyperFrames (SVG logo drawn on, masked, or assembled from parts); the 3D pack's `model` + `reveal` for a logo with depth.

Beats: build-up (0.5-2 s), the logo resolves (the hero moment), hold (1-3 s). Use the logo's own colours and proportions; never distort it.

Checks: the final frame shows the logo exactly as supplied (compare against the source file); it resolves on the sound accent.

## Kinetic typography and lyric videos

Length 10-240 s. Route: HyperFrames.

Techniques: time each word or phrase to the audio (measure word times with `npx hyperframes transcribe audio.wav`, which writes word-level timestamps; never guess), vary scale and weight to show stress, move the camera through a typographic space instead of replacing words in place, keep one or two typefaces. Every word must be readable for its duration.

Checks: text matches the lyrics or script exactly; sync within one frame on stressed words (pull stills at those times); nothing too fast to read.

## Captions over any video

Route: HyperFrames caption layer timed to word timestamps from `npx hyperframes transcribe`. Two to seven words per caption, broken at phrase boundaries, never more than two lines, a solid or blurred backing so they read on any background. Highlight the word being spoken if the brief asks for "TikTok-style" captions.

Checks: every caption matches the audio word for word; none on screen when nobody speaks; inside the safe zone for the format.

## Choosing when the brief is vague

| The brief says | Treat it as |
|---|---|
| "explain X", "how X works" | 2D explainer |
| an equation, proof, algorithm, graph | Maths and algorithms |
| "intro for my tutorial", "lower third", "callout" | Tutorial |
| characters, a joke, "a short story" | Storytelling |
| "Short", "Reel", "TikTok", "vertical" | Vertical, plus the content format |
| numbers, "growth", "chart" | Data story |
| "launch", "announce", "new feature" | Product launch |
| "logo animation", "intro sting" | Logo sting |
| song, lyrics, "words on beat" | Kinetic typography |

Write the chosen format and its beat sheet into SPEC.md, then build.

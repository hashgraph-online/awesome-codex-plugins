---
name: varg-video-edit-library
description: >-
  A library of named edits an agent adds to footage, each with what it looks like, when to use it,
  the common mistake and how to build it in FFmpeg, HyperFrames, Remotion and CapCut. Cuts and
  pacing (J-cut, L-cut, match cut, jump cut, speed ramp, smash cut), transitions (whip pan, zoom,
  glitch, light leak, masks, every FFmpeg xfade, Remotion TransitionSeries, HyperFrames and GL
  shader transitions), words on screen (headlines, callouts, lower thirds, quotes and reviews, end
  cards and CTAs), showing a product (UI walkthroughs, cursor moves and clicks, device mockups, code
  and terminal screens, AI agent flows) and visuals (counters and charts, customer logos, grids and
  carousels, backdrops). Use when someone asks for a transition, a cut, a title, a lower third, a
  testimonial, an end card, a CTA, a screen-recording zoom, a cursor, a phone or laptop mockup, a
  code or terminal animation, an agent workflow animation, an animated number or chart, a logo wall,
  a carousel or a background while editing a video. Not for choosing an editing service (use
  varg-video-editing) or generating new footage (varg-ai).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - ffmpeg
        - npx
    homepage: https://skills.varg.ai/browse/edit-video/
compatibility: >-
  The takes are text. Building them needs ffmpeg for the FFmpeg recipes, Node for HyperFrames
  (npx hyperframes) and Remotion, and nothing for the CapCut steps a person follows by hand.
allowed-tools: Bash(ffmpeg:*) Bash(ffprobe:*) Bash(npx:*) Read
---

# Video edit library

Named edits for footage you already have. Every take in `references/` gives the look, when to reach for it, the mistake people make with it, timings, and a recipe per engine: FFmpeg for flat files, HyperFrames (HTML + GSAP) or Remotion (React) when the edit is a composition, and the CapCut path when a person will finish the edit in the app. The cards with previews live at https://skills.varg.ai/browse/edit-video/.

Most takes are built on open components from other people's libraries: HyperFrames by HeyGen, remocn, GL Transitions, Magic UI, Aceternity UI, Fancy, Codrops and others. Each take names its component, author and license; keep that credit when you use it.

## How to use it

1. **Name the take before you build it.** Read the person's ask ("make the logo pop at the end", "zoom into the button when I click") and find the take in the index below. Open only that reference file.
2. **Pick the engine the project already uses.** A plain MP4 and a shell: FFmpeg. A HyperFrames or Remotion project: that framework's recipe, and the listed registry component when one exists (`npx hyperframes add <name>`, `npx shadcn@latest add @remocn/<name>`). Do not switch frameworks for one effect.
3. **Keep the timing from the card.** Durations and easing are the part people get wrong. A transition longer than 12 frames at 30 fps starts to read as a scene of its own; text needs at least the time to read it aloud.
4. **Check the cut.** Grab a still at each edit point (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 edit-<t>.jpg`) and look at it before you hand the video back.

## Rules that hold for every take

- One transition family per video. Mixing whips, glitches and page curls in one edit looks like a template sampler.
- Most joins should be plain cuts. Use a transition where it means something: a change of place, time or idea.
- Before you join clips in FFmpeg, normalise frame rate, timebase, resolution, SAR and pixel format (`fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p`). Mismatched inputs are the most common reason `xfade` and `concat` fail.
- Keep on-screen text inside the safe zone: 10% from the edges on 16:9, and clear of the caption and UI bands on 9:16.
- Text stays on screen at least as long as it takes to read twice; numbers land on a round, final value and hold.

## Index

<!-- takes:start -->
- [Cuts & pacing](references/cuts.md) (26): Hard Cut, Jump Cut, Jump-Zoom Punch-In, J-Cut, L-Cut, Graphic Match Cut, Action Match Cut, Sound Match Cut, Cut on Action, Smash Cut, Cutaway / Insert, Cross-Cutting, Invisible Cut, In-Camera Whip Pan Cut, Speed Ramp, Freeze Frame, Beat-Synced Cut, Split Screen, Montage Sequence, Rhythmic Cutting (3-2-1), Pattern Interrupt, B-Roll Overlay Cut, FFmpeg Concat Demuxer (Lossless), FFmpeg Concat Filter (Re-encode), Audio Crossfades, J and L in FFmpeg, Remotion Overlay on a Cut
- [Transitions](references/transitions.md) (60): Mix (Cross Dissolve), Dip to Black, White Flash, Pull In (Zoom In), Pull Out (Zoom Out), Zoom Blur, Whip Swipe, Spin, Camera Shake, Glitch, Blur Through, Light Leak, Film Burn, Light Sweep, Chromatic Split, Slide / Push, Wipe, Circle Iris, Heart Mask, Ink and Brush Reveal, Gradient (Luma) Wipe, 3D Cube, 3D Flip, Page Turn, Split and Slices, Shutter and Blinds, Pixelate, Clock Wipe, Swirl Vortex, Squeeze and Stretch, Ripple and Wave, Freeze Transition, Velocity Edit, FFmpeg xfade Chain for N Clips, FFmpeg xfade Transition Reference, Normalize Clips Before xfade, GL Transitions via editly or FFmpeg, MoviePy Crossfade and Slide, Remotion TransitionSeries, Remotion Custom Presentation, GL Transitions in Remotion, HyperFrames Shader Transition, HyperFrames Scene Transition (CSS), HyperFrames Whip with Motion Blur, OTIO and XML Handoff to NLEs, CapCut Draft Automation, DaVinci Resolve AddTransition API, Cover and Reveal, Soft-Edge Wipe, Circle Crop Through Black, Box Crop Through Black, Color-Distance Blend, Pixel Dissolve, Diagonal Wipe, Fade Through Gray, Corner Wipe, Zoom Into Next, Wind Wipe, Fast and Slow Fades, Custom xfade Expression
- [Headlines & callouts](references/titles.md) (14): Kicker Over Rising Headline, Rotating Benefit Word, Masked Line Reveal, Marker on the Key Phrase, Strike Old, Write New, Clean Lower Third, Hand-Drawn Callout Arrow, Dim Everything But the Target, Impact Headline Slam, Phrase Builds From the Center, Specular Sweep Title, Decode-In Tech Title, Footage Inside the Letters, Tracking-In Feature Label
- [Quotes & reviews](references/quotes.md) (9): Tweet as Proof Card, Quote at Reading Pace, Star Rating Sweep, Wall of Love Marquee, Community Post as Proof, Reviews Arrive as Notifications, Pull Quote Beside the Speaker, Split-Flap Headline Quote, GitHub Stars as Proof
- [End cards & CTAs](references/end-cards.md) (9): Logo Lockup Outro, Action Line + CTA Button, URL Typed Into the Address Bar, YouTube End Screen Layout, Scan-to-Try QR Card, Store Badges Close, Pull Back to the Whole Canvas, Follow Card Sign-Off, Last Frame Equals First Frame
- [UI walkthroughs](references/ui.md) (12): Zoom to the Action, 3D Tilted Dashboard Reveal, Floating UI Panels in Depth, UI Builds Itself Piece by Piece, Before/After UI Wipe, Card Expands Into Detail, Filmed Off a Monitor, Form Fills Itself, Toggle Turns the Feature On, Command Palette Pop, Pinned Mock, Changing States, Liquid Glass UI Layer
- [Cursors & clicks](references/cursors.md) (9): Auto Zoom on Every Click, Oversized Look-Here Cursor, Click Ripple and Button Press, Shortcut Keycaps Overlay, Named Agent Cursor, Multiplayer Cursors Drift In, Drag a Card Across Columns, Select Text, Then Act, Touch Taps on Phone UI
- [Device mockups](references/devices.md) (10): Browser Window Frame, Phone Frame with Live Screen, Laptop Lid Opens to Screen, 3D Phone Turn, Phone, Tablet and Laptop Splay, Push Through the Screen, Foldable Two-Screen Reveal, Phone in Hand Insert, Floating Device with Soft Bob, macOS Desktop Stage
- [Code & terminal](references/code.md) (10): Editor Types the Code, Red/Green Diff Collapse, Spotlight One Line of Code, Code Morphs Between Versions, Terminal Session Run, One-Line Install Card, Camera Scrolls a Long File, Code Left, Live UI Right, Code on a Lit 3D Slab, Agent CLI Welcome Screen
- [AI agent flows](references/agent-flows.md) (10): Prompt Typed, Then Generate, Answer Streams In, Tool Calls as Status Rows, Nodes Wire Up on a Canvas, Beams Into the Agent Hub, Thinking… Shimmer Label, Parallel Agents Side by Side, Plan Checklist Ticks Off, Vertical Chat Exchange, Tracing Beam Through Steps
- [Numbers & charts](references/numbers.md) (12): Big Stat Count-Up, Odometer Digit Roll, Bars Grow with Value Labels, Line Draws with Riding Label, Ranked Bar Race, Progress Ring Fills, Before → After Metric, Money Counter Payoff, Axis-Free Speed Comparison, Dense Specs Wall, Pain Metric Falls Away, Ticking Time-Saved Clock
- [Customer logos](references/logo-walls.md) (7): Trusted-By Logo Marquee, Logo Grid Settles In, Integrations Orbit the Logo, Partner × Partner Lockup, Brand Chips Spring In, Logos Float Past in Depth, Integration Logos Light Up
- [Grids & carousels](references/galleries.md) (9): Bento Feature Grid, Camera Drifts Across a Bento, Tilted Screenshot Wall, Stacked Cards Fan Out, App Screens on a Rail, Cards Orbit in a Ring, Rapid Screenshot Burst, Opposing Marquee Rows, Filmstrip on a Curve
- [Backdrops](references/backdrops.md) (9): Slow Mesh Gradient, Aurora Behind the Title, Faint Grid or Dot Field, Spotlight From Above, Film Grain Over Gradient, Blurred Product Behind Text, Perspective Grid Tunnel, Brand-Color Silk Waves, Quiet Particle Field
<!-- takes:end -->

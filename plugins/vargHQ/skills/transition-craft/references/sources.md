# Sources: transitions

Every URL below was opened in this research session (WebFetch or the X tools). Numbers are the citation ids used in
`references/*.md` and `assets/presets/*.json`.

Templates: **CB** = photo-collage-burst, **DZ** = droste-recursive-zoom, **TM** = tile-flip-mosaic,
**BL** = bokeh-light-spot, **PG** = photo-cloud-gallery, **SD** = shake-distort-cut.

## Cinematic analysis

| # | Source | Who | URL | Used for |
|---|---|---|---|---|
| 1 | Walter Murch's Rule of Six, the editor's formula for choosing the right cut (Filmdaft) | Summary of Murch's *In the Blink of an Eye* (Oscar-winning editor of Apocalypse Now, The English Patient): weights 51/23/10/7/5/4 % for emotion, story, rhythm, eye-trace, 2D plane, 3D space | https://filmdaft.com/walter-murchs-rule-of-six-the-editors-formula-for-choosing-the-right-cut/ | all |
| 2 | 6 'Rules' for Good Cutting According to Oscar-Winning Editor Walter Murch (No Film School) | Murch's priority order: sacrifice from the bottom (3D space) up, keep emotion at all costs | https://nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch | all |
| 3 | Not sure where to cut? Murch says the answer may be in the eyes (No Film School) | Murch's blink theory, tested by editor Sven Pape (This Guy Edits): a blink marks the end of a thought, a built-in edit point | https://www.nofilmschool.com/2016/05/not-sure-where-cut-editor-walter-murch-says-answer-may-be-eyes | all |
| 4 | Tony Zhou, Every Frame a Painting — "Satoshi Kon: Editing Space & Time" (transcript on VoiceTube) | Video essayist; Kon's transitions: "zoom out from a TV", "use objects to wipe the frame", matching images link worlds | https://voicetube.com/videos/32481 | DZ, CB, TM |
| 5 | Logan Baker — The Editor's Toolbox: Match Cuts (PremiumBeat) | Editor/writer; cut mid-motion, match direction, sound sells the transition | https://www.premiumbeat.com/blog/match-cuts-for-video-editors/ | all |
| 6 | How to do a whip pan: 5 steps (No Film School) | Same direction and speed on both sides, match brightness, trim where blur begins/ends | https://nofilmschool.com/2017/09/5-steps-create-perfect-whip-pan-transition | SD, BL |
| 7 | What is the 180-degree shutter rule (StudioBinder) | Shutter angle = fps × 360 / shutter speed; larger angle = more blur, smaller = jittery (Saving Private Ryan look) | https://www.studiobinder.com/blog/what-is-the-180-degree-shutter-rule/ | SD, CB, PG, DZ |
| 34 | EOSHD forum thread "Editing" (cutting on, before or after the beat) | Editors relay Hans Zimmer's advice: a frame early jolts (action), 6–12 frames late feels poetic; one-frame-late rarely works | https://www.eoshd.com/comments/topic/46696-editing/ | all |

## Articles and guides

| # | Source | Who | URL | Used for |
|---|---|---|---|---|
| 8 | Zaid Alkuheli — How long should video transitions be? (OverseerOS) | Measured 2,009 cut boundaries (median 0.40 s); duration bands by transition type; "halve it" test | https://www.overseeros.com/blog/how-long-should-video-transitions-be | all |
| 9 | Jason Boone — How to simulate camera shake in After Effects (School of Motion) | Motion design educator; wiggle(1, 25) as a subtle shake; scale up to hide edges | https://schoolofmotion.com/blog/how-to-simulate-camera-shake-adobe-after-effects | SD, CB |
| 10 | Dan Ebberts — Realistic Bounce and Overshoot (MotionScript) | The reference AE expression author; decaying sine amp·sin(2πft)/e^(decay·t), defaults amp 80, freq 1, decay 1 | http://www.motionscript.com/articles/bounce-and-overshoot.html | SD, TM |
| 11 | Boris FX Sapphire S_Shake documentation | Industry plugin; defaults amplitude 1, frequency 8, tilt/zoom wave freq 0.5, motion blur length 1 | https://borisfx.com/documentation/sapphire/ae/shake | SD |
| 12 | Maxon Universe — Camera Shake Transition documentation | Plugin transition; amplitude X/Y, frequency, scale footage, RGB separation (5–25 examples), motion blur shutter | https://help.maxon.net/rg/en-us/Content/html/Transitions_camera-shake-transition.html.md | SD |
| 13 | Epic Games — Camera Shakes in Unreal Engine | Perlin noise for rumbles/explosions, sine wave for gentle drift; blend in/out | https://dev.epicgames.com/documentation/unreal-engine/camera-shakes-in-unreal-engine | SD |
| 14 | Rick Gerard (Adobe Community Expert) — Motion Tile "Mirror Edges" thread | Output width/height 300 % gives 3 mirrored copies to hide edges on zoom/rotate | https://community.adobe.com/t5/after-effects-discussions/mirror-edges-not-working/m-p/11946450 | SD, DZ |
| 15 | Remotion — CameraMotionBlur docs | shutterAngle default 180, samples default 10, recommended 5–10 | https://www.remotion.dev/docs/motion-blur/camera-motion-blur | SD, CB, DZ, PG |
| 16 | Reach & North — Smooth, Efficient, and Interruptible Zooming and Panning (arXiv 1801.09358) | Restates van Wijk & Nuij: zooming by a constant factor has the same perceptual cost anywhere; pure zoom is exponential | https://ar5iv.labs.arxiv.org/html/1801.09358 | DZ, PG |
| 17 | Adobe Community — Infinite zoom loop effect (Roland Kahlenberg, accepted answer) | One parent layer drives every level; poster fixed it with exponential scale | https://community.adobe.com/t5/after-effects-discussions/infinite-zoom-loop-effect/td-p/9884846 | DZ |
| 18 | Noah Litvin — Endlessly zoom into your own Droste effect (Envato Tuts+) | Parent footage to precomps and scale for an infinite zoom | https://photography.tutsplus.com/tutorials/endlessly-zoom-into-your-own-droste-effect--ae-12897 | DZ |
| 19 | Jie Chen — Escher's Print Gallery and the conformal mapping | Log → multiply by c = i2π/(ln α + i2π) → exp; α = 256 per Lenstra | https://jiechenjiechen.github.io/blog/2026/escher | DZ |
| 20 | Universiteit Leiden (B. de Smit, H. Lenstra) — Escher and the Droste effect | Primary project on the mathematics of Print Gallery, with animations | https://pub.math.leidenuniv.nl/~smitbde/escherdroste/ | DZ |
| 21 | GSAP docs — Staggers | each vs amount, from: center/edges/random/[x,y], grid [rows, cols], axis, ease on the distribution | https://gsap.com/docs/v3/Staggers/ | CB, TM |
| 22 | GSAP docs — Eases | Ease families (power, expo, back, elastic, steps; rough, expoScale) | https://gsap.com/docs/v3/Eases/ | all |
| 23 | David DeSandro — Intro to CSS 3D transforms: Card Flip | perspective 600px, preserve-3d, backface-visibility hidden, rotateY(180deg) | https://3dtransforms.desandro.com/card-flip | TM |
| 24 | David DeSandro — Perspective | 100 px = extreme, 2000 px = subtle; use the parent `perspective` property so tiles share one vanishing point | https://3dtransforms.desandro.com/perspective | TM, CB |
| 25 | Maxon Universe — Bokeh Transition documentation | Blur amount (150/600 examples), highlight boost default 60, 8 iris shapes, bokeh ratio 50 = round, duration in frames | https://help.maxon.net/rg/en-us/Content/html/Transitions_bokeh-transition.html.md | BL |
| 26 | Boris FX — BCC+ Rack Focus Dissolve documentation | Matte position 100 = highlights; facets, curvature 100 = round; Screen blend keeps highlights; ease in/mid/out | https://borisfx.com/documentation/continuum/bcc-plus-rack-focus-dissolve/ | BL |
| 27 | Boris FX — Sapphire BokehLights documentation | Defaults: 30 lights, size 0.3, brightness 0.5, 7 sides, softness 0.01, roundness 0.3, vary size 0.2, fringing 0 | https://borisfx.com/documentation/sapphire/ae/bokehlights | BL |
| 28 | Wikipedia — Circle of confusion | Blur disc c = f²/(N(S₁−f)) for a background at infinity; d/1500 CoC limit | https://en.wikipedia.org/wiki/Circle_of_confusion | BL, PG |
| 29 | Evan Abrams — Falling Polaroids: After Effects photo montage (PremiumBeat) | Random Z rotation ±45°, z stacked by index, 30-frame cadence, cast shadows 50 %, camera blur 200 at f/1.4 | https://www.premiumbeat.com/blog/after-effects-photo-montage-tutorial | CB, PG |
| 30 | Tom Graham — Collage animation in After Effects (Envato Tuts+) | 12 fps posterize for stop-motion feel, white drop shadow as paper edge, tape PNGs, lift = scale + shadow distance | https://photography.tutsplus.com/articles/collage-animation-in-after-effects--cms-93666 | CB |
| 31 | three.js source — FogExp2.js and fog_fragment.glsl.js | FogExp2(color, density = 0.00025); factor = 1 − exp(−density² · depth²); linear fog = smoothstep(near, far, depth) | https://raw.githubusercontent.com/mrdoob/three.js/dev/src/scenes/FogExp2.js · https://raw.githubusercontent.com/mrdoob/three.js/dev/src/renderers/shaders/ShaderChunk/fog_fragment.glsl.js | PG |
| 32 | Remotion — @remotion/three docs | Drive Three scenes with useCurrentFrame inside ThreeCanvas, never useFrame; angle GL renderer | https://www.remotion.dev/docs/three | PG, DZ |
| 33 | HyperFrames registry items: camera-shake, motion-blur, whip-pan-cut, gallery-tunnel, grid-pixelate-wipe, zoom-through-transition | Building blocks; gallery-tunnel recycles planes exactly at the fog distance (FOV 75, speed 3 segments/s); motion-blur integrates a shutter window over the GSAP timeline | https://github.com/heygen-com/hyperframes/tree/main/registry | all |

## Practitioners on X

| # | Who | Why they count | Post | What we took | Used for |
|---|---|---|---|---|---|
| 40 | goop (@goopsoup_) | Short-form editor; post on editing routine (161 likes) | https://x.com/goopsoup_/status/2114615971826827569 | The everyday editor recipe: S_Shake at 0.7 amplitude for 13 frames, then blur | SD |
| 41 | Yaori (@Pashoke1) | Builds code-rendered videos; finishing-pass breakdown | https://x.com/Pashoke1/status/2115041115590037582 | A 2-frame chromatic kick on every hard cut; motion blur with 5 samples; "if it looks like a filter, cut every value in half" | SD, TM, BL |
| 42 | Raptor (@RajAdonis) | Short-form editor sharing exact motion settings | https://x.com/RajAdonis/status/2113906813020344579 | cubic-bezier(.25,0,.11,1); things appear at full speed and only slow down; new graphics cut in at 1.52× and settle to 1× over 1.2 s | SD, CB, DZ |
| 43 | Lionel Radisson (@MAKIO135) | Creative coder, genuary regular (Droste loop, 521 likes) | https://x.com/MAKIO135/status/1742550379911401900 | Seamless Droste loop as a reference look | DZ |
| 44 | Nicolas Daniel (@nicolasdnl) | Creative coder (Droste screensaver, 518 likes) | https://x.com/nicolasdnl/status/1743599237886099583 | Droste as an endless screensaver loop | DZ |
| 45 | Massimo (@Rainmaker1973) | Science communicator; shared the Leiden Print Gallery animation (230k views) | https://x.com/Rainmaker1973/status/1639251479461502977 | The twisted (Escher) Droste zoom as the reference for the spiral variant | DZ |
| 46 | After Effects Tricks (@jesiccaesthetic) | AE/Premiere tutorial account (232 likes, 160 bookmarks) | https://x.com/jesiccaesthetic/status/1925128197424951329 | Defocus transition is a stock editor move; ours adds highlight bokeh | BL |
| 47 | Siraj (@SirajEdits) | YouTube editor posting AE transitions | https://x.com/SirajEdits/status/2115785675949650408 | Grid transitions are now one-click effects: randomise to look made, not preset | TM |
| 48 | aescripts + kewin.wav | Plugin store; grid animation tutorial made with Flex | https://x.com/aescripts/status/2115832815606546677 | Grid tile animation as a current editor trend | TM |
| 49 | fofr (@fofrAI) | AI image/video practitioner (281 likes, 147 bookmarks) | https://x.com/fofrAI/status/1993709106075767222 | "Droste effect" is a working shorthand prompt for recursive plates | DZ |
| 50 | plugin3d (@plugin3d) | Blender shader-node tips (280 likes, 215 bookmarks) | https://x.com/plugin3d/status/2079216930615927190 | Depth pass + defocus node gives two or more focus points | PG, BL |

Weak sources opened but not cited: iso50 blog and Kotaku pieces on the Satoshi Kon essay (no technique detail), tutvid shake article
(no values), Adobe Community transform-shutter threads (bug reports).

# Every source we tested

Measured 2026-11-03 from one IP with read-only requests and no sign-ups. No provider keys were available, so keyed APIs are documented but not run. "Route" is how an agent can actually read it. "Score" is our judgment: 5 = search, license check and download all tested with no human; 4 = a small step or a free key; 3 = usable with a caveat; 2 = discovery only or paid; 1 = blocked; 0.5 = the license bars this use.

## Stock footage and B-roll

| Source | Score | Route | Commercial use | Size | Best for | Bad for |
|---|---:|---|---|---|---|---|
| [Pexels Videos](https://www.pexels.com/videos/) | 4 | API | yes | not measured | Generic B-roll by keyword: nature, city, lifestyle, business, hands, with portrait and landscape filters. | Exact products, named places, specific actions. Popular clips are reused across many chann |
| [Coverr](https://coverr.co/) | 4 | HTML | yes | 61 unique clip ids on the 'ocean' page; page title says 100  | Quick B-roll with no key. 360p, 720p, 1080p and original files by URL. | Depth. Mixed results: AI clips and premium clips sit beside free ones. |
| [Mixkit Video](https://mixkit.co/free-stock-video/) | 4 | HTML | yes | 858 'ocean' clips stated on the page. Library total not meas | No-key B-roll with direct files, including 720p (a sampled file was 17.9 MB). | Rights check per clip: the license type differs by item. |
| [Wikimedia Commons](https://commons.wikimedia.org/) | 4 | API | varies per item | 416,345 video files and 4,454,445 audio files by filetype se | Real places, events, history, science. License is readable per file. | Slick commercial B-roll. Files are often webm or ogv and need a transcode. |
| [NASA Image and Video Library](https://images.nasa.gov/) | 4 | API | with credit | 358 video hits for 'ocean'. Library total not measured. | Space, Earth, launches, science B-roll with no fee. | Anything else. Implied endorsement is not allowed. |
| [Pixabay Videos](https://pixabay.com/videos/) | 3.5 | API | yes | not measured | Second opinion when Pexels has nothing. Direct embedding of video is allowed by the docs. | Heavy automated runs: docs say 'the API is made for real human requests; do not send lots  |
| [Internet Archive](https://archive.org/) | 3.5 | API | varies per item | 17,579,534 items with mediatype:movies; 10,461 in collection | Archival and period footage, especially public domain and Prelinger. | Assuming anything is free: most results carry no license signal. |
| [Storyblocks](https://www.storyblocks.com/) | 3 | HTML | paid | not measured | Teams already paying who want clips inside the agent. | Long-lived projects on lower tiers. |
| [Getty Images](https://www.gettyimages.com/) | 1.5 | blocked | paid | not measured | Enterprise teams with a contract. Editorial footage. | Everyone else. |
| [Videvo](https://www.videvo.net/) | 1 | blocked | varies per item | not measured | Nothing for an agent. | Automated search, license checks. |
| [Vecteezy](https://www.vecteezy.com/) | 1 | blocked | varies per item | not measured | Nothing for an agent. | Automated search, license checks. |
| [Artgrid](https://artgrid.io/) | 1 | blocked | paid | not measured | A human picking hero footage. | Agent search. |

## Music

| Source | Score | Route | Commercial use | Size | Best for | Bad for |
|---|---:|---|---|---|---|---|
| [Incompetech](https://incompetech.com/music/royalty-free/music.html) | 4.5 | JSON | with credit | 1,443 pieces, 1,196 with a BPM | Beat-grid cutting: the only free library here where an agent can filter by BPM before downloading. | Ads and pieces with no place for a credit, unless you buy the license. The sound is widely |
| [Epidemic Sound](https://www.epidemicsound.com/) | 4.5 | API | paid | 55,000 tracks and 250,000+ sound effects | The best measured route to quality music with trim-to-length, if someone pays. | Free use: the API's free plan says 'Prototyping only, you cannot go live on this plan. Inc |
| [Mixkit Music](https://mixkit.co/free-stock-music/) | 4 | HTML | yes | 36 MP3 URLs on the 'ambient' page. Total not measured. | A quick free music bed with no key and no credit line. | Long pieces, stems, a specific tempo: no BPM data on the page. |
| [Generated music (Mureka, Lyria, ElevenLabs Music via varg)](https://api.varg.ai/v2) | 4 | API | paid | n/a | A bed cut to an exact length and mood, with no library match or credit line. | When you need a known song or a beat-accurate structure without iteration. |
| [ende.app](https://ende.app/en) | 3 | HTML | with credit | 2,479 tracks stated on the page | Free production music with a clear license. | Agent search: no API measured. |
| [Openverse audio](https://openverse.org/) | 2.5 | API | varies per item | 5,223,435 audio items (wikimedia_audio 3,986,828, jamendo 64 | One free search across CC audio, when it answers. | Being a hard dependency of a render. Allow about 40 s and fall back. |
| [Free Music Archive](https://freemusicarchive.org/) | 2 | HTML | varies per item | not measured | Finding a track for a human to fetch. | Unattended download. The license is only on the track page. |
| [Pixabay Music](https://pixabay.com/music/) | 1.5 | blocked | yes | not measured | A human downloading by hand. | Any agent run. |
| [Artlist](https://artlist.io/) | 1 | blocked | paid | not measured | A person with a plan. | Agents, by direct request. |
| [YouTube Audio Library](https://www.youtube.com/audiolibrary) | 0.5 | login | varies per item | not measured | A person publishing on YouTube. | Any agent. |
| [Uppbeat](https://uppbeat.io/) | 0.5 | blocked | varies per item | not measured | A person with an account. | Agents. |

## Sound effects

| Source | Score | Route | Commercial use | Size | Best for | Bad for |
|---|---:|---|---|---|---|---|
| [Freesound](https://freesound.org/) | 5 | API | varies per item | 739,219 sounds | Any specific sound. Filter by CC0 and duration. | Internet-native comedic hits: @ZhenZhu200 calls it a traditional library, weak on narrativ |
| [ElevenLabs Sound Effects](https://elevenlabs.io/sound-effects) | 4.5 | API | paid | n/a | Signature hits, logo stings, exact length, seamless loops. | Volume on the free tier; verbatim realism. |
| [Mixkit SFX](https://mixkit.co/free-sound-effects/) | 4 | HTML | yes | 20 preview MP3s on the 'whoosh' page. Total not measured. | No-key whooshes, hits, UI sounds with clean licensing. | Rare or specific sounds. |
| [Kenney audio packs](https://kenney.nl/assets/category:Audio) | 4 | HTML | yes | 13 asset links on the audio category page (rough count) | UI ticks and clicks with zero license work. | Cinematic sound. |
| [earshot](https://github.com/Leonxlnx/earshot) | 4 | JSON | yes | 252 per README | SFX placed on an exact frame, re-rendered for length and pitch. Also gives the agent a way to judge sound. | Beating a real recording across the board. |
| [Sonniss GDC bundles](https://sonniss.com/gameaudiogdc/) | 3.5 | blocked | yes | not measured: secondary sources give 7+ GB for 2026 and 200+ | Pro-grade recordings, once a human has downloaded them and the agent indexes filenames. | Live agent fetch. Redistribution as sound effects. |
| [HyperFrames bundled SFX](https://hyperframes.heygen.com/) | 3.5 | JSON | varies per item | 19 manifest entries, 21 files in the folder; skill docs say  | A render that must finish offline. | Variety: every video gets the same 19 sounds. |
| [Openverse SFX](https://openverse.org/) | 2.5 | API | varies per item | 591,898 Freesound items in Openverse | No-key route when it answers. | Being the only route. |
| [Pixabay SFX](https://pixabay.com/sound-effects/) | 1.5 | blocked | yes | not measured | A human downloading by hand. | Any agent run. |
| [BBC Sound Effects](https://sound-effects.bbcrewind.co.uk/) | 1 | JSON | no | 33,066 clips | Personal, educational or research projects. Reference for what a real recording sounds like. | Any commercial video. |
| [Zapsplat](https://www.zapsplat.com/) | 1 | blocked | with credit | not measured: secondary sources disagree (90,000+ to 150,000 | A person with an account. | Agents. |

## Motion blocks and effects

| Source | Score | Route | Commercial use | Size | Best for | Bad for |
|---|---:|---|---|---|---|---|
| [HyperFrames registry](https://hyperframes.heygen.com/catalog) | 5 | JSON | yes | 448 catalog items (210 blocks, 238 components), plus 8 examp | Seek-safe parts built for rendering. First stop for a transition, lower third or caption style. | Remotion projects: blocks are HTML plus GSAP. |
| [LottieFiles](https://lottiefiles.com/) | 4.5 | API | yes | 800,000+ free and premium animations (home page). 'loading'  | Icons, checkmarks, loaders, small spot animation on overlays. | Consistent style across a film. Quality varies; many items have few downloads. |
| [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 4.5 | HTML | yes | 124 cards and 150 shots per upstream README. Forks claim 152 | Product-film shots: 19 transitions, 25 typography, 22 UI entrances. | Talking-head footage. |
| [Herk Edit Kit (formerly hyperframes-student-kit)](https://github.com/nateherkai/herk-edit-kit) | 4.5 | HTML | yes | 406 draft motion-graphics cards, 15 skills, 2 scene template | Editing talking footage, with an editing playbook. | Non-HyperFrames pipelines. Cards are labeled draft. |
| [Remotion resources](https://www.remotion.dev/docs/resources) | 4 | HTML | varies per item | About 208 list items in 17 sections | Finding a maintained component before writing one. | Teams of 4+ who have not bought a license. |
| [remotion-bits](https://remotion-bits.dev/) | 4 | JSON | yes | not measured | Remotion parts an agent can search and install. | HyperFrames projects. |
| [varg How-To](https://varg.ai/how-to) | 4 | API | varies per item | Search totals: 'transition' 382, 'b-roll' 116, 'lower third' | One search across the skills and components in this file, including HyperFrames parts. | Precise counts: hybrid search returns many loose matches. |
| [motion-prompt](https://github.com/showheyohtaki/motion-prompt) | 4 | HTML | yes | 192 names in 8 sets of 24 | Vocabulary: when you know the look but not its name. | Editing footage: it is about naming and generation. |
| [Remotion templates](https://www.remotion.dev/templates) | 3.5 | HTML | varies per item | 20 template slugs in the page | Starting a new project. | Mid-project parts. |
| [GSAP demos](https://gsap.com/demos/) | 3 | HTML | yes | 25 unique CodePen links on the hub page | Learning timelines, easing and text effects. | Agents reading the pens directly: CodePen blocks curl. |
| [React Bits](https://reactbits.dev/) | 2.5 | HTML | yes | 564 link lines in llms.txt | Text and background ideas to study and re-time. | Dropping in unchanged: real-time motion. Selling a kit containing the components. |
| [Magic UI](https://magicui.design/) | 2.5 | JSON | yes | 260 registry items: 79 ui, 179 examples, 1 style, 1 lib | Product UI inside a film. | Same frame-rendering caveat as React Bits. |
| [21st.dev](https://21st.dev/community/components) | 2 | API | varies per item | 12,000+ components, 353 templates, 960 themes | UI to show inside a product film. | Video timing: components run in real time and need rework for frame rendering. |
| [video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | 2 | HTML | no | 108 cards per README (brief said 109) | Study of cards tied to words. | Commercial use of the toolkit. |
| [Motion Canvas examples](https://github.com/motion-canvas/examples) | 1.5 | HTML | yes | not measured | Explainer diagrams in TypeScript. | New projects: latest stable @motion-canvas/core is 3.17.2 from 2024-12-14. |

## Reference and taste (study only, never in the output)

| Source | Score | Route | Commercial use | Size | Best for | Bad for |
|---|---:|---|---|---|---|---|
| [Refs](https://refs.video/) | 5 | API | paid | 4,422 films, 110,419 shots, 28 formulas (self-reported) | Pacing targets from real films. Median shot 3.5 s, 16 cuts a minute (self-reported, 1,952 films). | Talking heads and long-form: the library is launch-heavy. |
| [STEALSHOT](https://stealshot.com/) | 3.5 | API | paid | 181,086 frames, 2,527 videos, 357 brands (self-reported) | Finding a shot by visual description, with shot-length stats on each film. | Free use. |
| [FILMGRAB](https://film-grab.com/) | 3.5 | JSON | no | 4,187 posts | Studying framing and color of a named film. | Search by concept: 'interrogation' returned nothing, 'blade' worked. Never publish these s |
| [Motionographer](https://motionographer.com/) | 3.5 | JSON | no | 9,014 posts | Readable text about how motion pieces were made, by search. | Asset sourcing. |
| [Mobbin](https://mobbin.com/) | 3 | login | paid | 600,000+ screens (meta description) | How real product UI looks and moves, for product demos. | Footage editing. |
| [Foreplay](https://www.foreplay.co/) | 3 | API | paid | 100M ads (marketing copy) | Ad hooks at scale when someone pays. | Non-ad video. |
| [1of10](https://1of10.com/) | 3 | login | paid | not measured | YouTube topics and packaging, from a real outlier product. | Editing craft. |
| [OutlierKit](https://outlierkit.com/) | 3 | API | paid | not measured | Outlier videos and transcripts inside an agent. | Editing craft. |
| [Godly](https://godly.website/) | 2.5 | HTML | no | not measured | Web motion taste. | Video editing pace. |
| [Vimeo Staff Picks](https://vimeo.com/channels/staffpicks) | 2.5 | JSON | no | 10 latest items in RSS. Total not measured. | A daily feed of well-cut short films to watch. | Search and download. |
| [Are.na](https://www.are.na/) | 2.5 | API | no | not measured | Taste boards built by people. | Licensed assets. |
| [Skillry viral videos](https://skillry.dev/ai-videos/opus-5-5) | 2.5 | HTML | varies per item | 418 videos on the page (@grokkedd said 389 in October) | Prompts behind code-made viral films. | Footage editing. |
| [vflow](https://vflow.live/) | 2 | HTML | no | 13,342 prompts across 9 models | Prompt language for generated B-roll. | Editing: it covers generation prompts. |
| [Meta Ad Library](https://www.facebook.com/ads/library/) | 2 | blocked | no | not measured | A human checking one brand. Paid scrapers for batches. | A direct agent call. |
| [NexLev](https://www.nexlev.io/) | 2 | login | paid | not measured | Faceless channel niche research. | Editing craft. Treat revenue claims in these posts as marketing. |
| [Subscribr](https://subscribr.ai/) | 2 | login | paid | 40 million videos per @boomerrbryan (not official) | Research plus script. | Editing craft. |
| [ShotDeck](https://shotdeck.com/) | 1.5 | blocked | no | 1M+ frames per @starks_arq (not official) | A human collects frames and hands them to the agent. | Agent search. |
| [Stash](https://www.stashmedia.tv/) | 1.5 | login | no | not measured | A paying human. | Agents. |
| [TikTok Creative Center](https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en) | 1.5 | login | no | not measured | A human browsing. | Agents. |
| [Eyecandy](https://eyecannndy.com/) | 1 | blocked | no | not measured | A human browsing. | Agents. |
| [Savee](https://savee.com/) | 1 | HTML | no | not measured | A human browsing. | Agent search. |
| [Frameset](https://frameset.app/) | 1 | blocked | no | not measured | A human, or a browser-driving agent. | Plain curl. |

## Fonts, icons, logos, LUTs, HDRIs

| Source | Score | Route | Commercial use | Size | Best for | Bad for |
|---|---:|---|---|---|---|---|
| [Google Fonts](https://fonts.google.com/) | 5 | JSON | yes | 1,959 families | Any title or caption font: the default. | A unique look: faces are everywhere. |
| [Fontsource](https://fontsource.org/) | 5 | API | yes | 2,103 fonts: OFL 2,059, Apache 36, UFL 5, CC0 1, MIT 1 | License-checked font choice; self-hosted for deterministic rendering. | Discovering new display faces. |
| [Poly Haven](https://polyhaven.com/) | 5 | API | yes | 997 HDRIs, 869 textures, 521 models (2,387 total) | Studio lighting and realistic reflections in 3D scenes (96 studio HDRIs). | 2D editing. |
| [Iconify](https://iconify.design/) | 5 | API | varies per item | 473,655 icons in 276 sets | Any icon by name as SVG in one URL. | Using an arbitrary set without checking: 53 of 276 sets are CC-BY-4.0, 6 are GPL, 2 are no |
| [Lucide](https://lucide.dev/) | 5 | JSON | yes | 2,019 icons | Default UI icons in overlays. | Logos. |
| [ambientCG](https://ambientcg.com/) | 4.5 | API | yes | 2,929 assets | PBR materials. | 2D editing. |
| [3D Asset Server](https://3d.shep.bot/) | 4.5 | API | varies per item | 26 providers (measured); 14,414 searches in 7 days on its pu | Finding a 3D model, HDRI or sprite in one call. | Paid-source results may need a login at the source. |
| [Simple Icons](https://simpleicons.org/) | 4.5 | JSON | varies per item | 3,467 logos | Tech logos with the official hex. | Using a logo as endorsement. Non-tech brands. |
| [HyperFrames LUT looks](https://hyperframes.heygen.com/) | 4 | JSON | yes | 3 looks in local luts/index.json (grade presets beyond that  | A grade inside a HyperFrames project with no sourcing. | A specific film-stock look. |
| [Fontshare](https://www.fontshare.com/) | 4 | API | yes | 100 families: 64 ITF FFL, 36 SIL OFL | A title font that does not look like every other AI video. | Small catalog. ITF FFL text could not be read by curl. |
| [G'MIC color presets](https://gmic.eu/color_presets/) | 3.5 | HTML | varies per item | 1100+ color CLUTs (official page) | Film-stock style grades with ffmpeg's haldclut filter. | Clean rights: names reference trademarks and origins vary. |
| [SVGL](https://svgl.app/) | 3.5 | API | varies per item | not measured | Logo plus wordmark by name. | Rights: read each brand's guidelines. |
| [Lutify.me free LUTs](https://lutify.me/free-luts/) | 3 | HTML | with credit | not measured | A small, clearly licensed LUT set. | ShareAlike-averse clients. |
| [GitHub LUT collections](https://github.com/cedeber/hald-clut) | 3 | HTML | varies per item | slaycamera: 5 LUTs. Others not counted. | Fetching a LUT by raw URL. | Rights: cedeber's README lists third-party and vendor presets under one repo license. |
| [Noun Project](https://thenounproject.com/) | 2.5 | API | with credit | 10M icons (marketing copy) | Odd concept icons Iconify lacks. | Credit-free output without paying. |
| [FreshLUTs](https://freshluts.com/) | 1.5 | HTML | varies per item | not measured | A human browsing. | Rights. |
| [unDraw](https://undraw.co/) | 0.5 | HTML | no | not measured | A human downloading one illustration. | Agents. License bars 'automated and non-automated ways to link, embed, scrape, search or d |

## Editing knowledge and tools

| Source | Score | Route | Commercial use | Size | Best for | Bad for |
|---|---:|---|---|---|---|---|
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 5 | JSON | yes | n/a (tool) | Measuring a reference's cut rate. Splitting footage into shots. | Soft dissolves and whip transitions. |
| [Every Frame a Painting](https://www.youtube.com/@everyframeapainting) | 4 | HTML | no | 35 videos on the channel's videos tab (includes other projec | Why a cut works: 'How Does an Editor Think and Feel?' has human English subtitles. | Rules with numbers. Do not reproduce text. |
| [Art of the Cut (ProVideo Coalition)](https://www.provideocoalition.com/tag/art-of-the-cut/) | 3.5 | HTML | no | not measured | How working editors think, in text. | Short-form social editing. |
| [TransNetV2](https://github.com/soCzech/TransNetV2) | 3.5 | JSON | yes | n/a | Hard cases where threshold detection fails. | A quick job on a laptop with no GPU. |
| [Contra Labs editing trajectories](https://huggingface.co/datasets/contralabs/premiere-video-editing-trajectories) | 3.5 | API | with credit | Premiere: 234 steps in 4 trajectories. Descript set is simil | Rare evidence of how pro editors reason while cutting vertical reels. | Scale: it is a preview sample. |
| [Film Editing Pro](https://www.filmeditingpro.com/) | 3 | JSON | no | 10 items in the feed. Total not measured. | Readable pro craft interviews. | Tutorials behind a paywall. |
| [AutoShot](https://github.com/wentaozhu/AutoShot) | 2 | HTML | varies per item | not measured | Research on short-form cut detection. | Direct use in editing. |
| [Hugging Face shot-boundary-detection](https://huggingface.co/datasets/it-just-works/shot-boundary-detection) | 1.5 | API | varies per item | Over 3.4M 61-frame clips (dataset card) | Training a detector. | An agent doing an edit: it needs nothing this large. |
| [AVE (Anatomy of Video Editing)](https://github.com/dawitmureja/AVE) | 1.5 | HTML | varies per item | not measured | Research. | Agents. |

# Traps and dead ends

Each of these was tried on 2026-11-03. Sites change, so retest anything you want to rely on.

| Source | Why not | Evidence |
|---|---|---|
| Pexels website (search, docs, license, help) | Blocks agents at the page level. The API is the only route. One X user reports a key could not be obtained. | curl 403 Cloudflare 'Just a moment' on /search/videos/, /api/documentation/, /license/. WebFetch also 403. API 401 'Missing API key'. Key report (0 likes, unverified): ht |
| Pixabay website | Search pages block agents. Docs also forbid mass automation. | Search 403 Cloudflare. Docs 200, quote: 'the API is made for real human requests; do not send lots of automated queries. Systematic mass downloads are not allowed.' https |
| Pixabay Music and Pixabay SFX | Free license, but no agent route: pages blocked and no audio endpoint. X lists imply otherwise. | Pages 403 Cloudflare. Docs HTML names only https://pixabay.com/api/ and https://pixabay.com/api/videos/ . |
| Videvo | Blocked. Terms now redirect to Freepik. | 403 security filter page on search and terms. WebFetch: 301 to freepik.com terms. |
| Vecteezy | Blocked everywhere tried, license unreadable. | curl and WebFetch 403 on search, home and https://www.vecteezy.com/licensing-agreement |
| Artgrid and Artlist | Blocked, paid, and no official MCP could be verified. | artgrid.io 403; search path shows a 404 page. artlist.io search, /license and /mcp 403. GitHub shows only small community repos. |
| Getty Images website | Blocked. MCP only through an account representative. | 403 'Attention Required'. API 401. https://developer.gettyimages.com/mcp/ |
| YouTube Audio Library | Requires a signed-in Studio session. | curl ends at accounts.google.com sign-in. |
| Uppbeat | Bot checkpoint on every page tried. | HTTP 429 'Vercel Security Checkpoint'; WebFetch 429 on /pricing. |
| Zapsplat | Blocked and needs an account. Free tier needs credit. | 403 Cloudflare on search and license; WebFetch 403 on https://www.zapsplat.com/license-agreement |
| Sonniss website | Blocked to curl, so downloads need a human. License trap for model builders. | curl 403. License via WebFetch: 'No AI Training or Usage' section; may not 'distribute, publish, sub-license or otherwise supply the sound effects as sound effects'. http |
| BBC Sound Effects | LICENSE TRAP. An easy keyless API returns 33,066 clips, but they are not for commercial use. An agent can fetch without ever seeing the license. | POST https://sound-effects-api.bbcrewind.co.uk/api/sfx/search 200. Site bundle text: 'Commercial use of this content is not allowed under the RemArc license.' and 'availa |
| unDraw | LICENSE TRAP. Popular lists tell you to hand it to Claude; the license bars automated access. | https://undraw.co/license quote: 'This extends to automated and non-automated ways to link, embed, scrape, search or download the assets included on the website without o |
| Local MusicGen | LICENSE TRAP. Non-commercial weights inside a free HyperFrames fallback path. | facebook/musicgen-small tag license:cc-by-nc-4.0 on https://huggingface.co/api/models/facebook/musicgen-small . media-use audio/references/bgm.md: 'Local generation (Lyri |
| video-talkcraft | LICENSE TRAP. Listed as a free tool on X. PolyForm Noncommercial: commercial use of the toolkit needs permission. | https://github.com/Vincentwei1021/video-talkcraft/blob/main/LICENSE quote: 'any commercial use of the toolkit requires prior authorization from the author.' Videos produc |
| Internet Archive without a filter | LICENSE TRAP. Open API, but most results have no license signal, and broadcast TV appears. | q=ocean AND mediatype:movies: 34,050 items, 4,790 CC URLs, 1,656 public domain URLs, so about 81% have neither. Sample result: WTTG Fox Morning News. |
| Free Music Archive | Search works, download does not, license absent from the listing. | downloadUrl 302 to /login. First sampled track: creativecommons.org/licenses/by-nc-sa/3.0/ . |
| Freesound's NC and Sampling+ sounds | LICENSE TRAP within a great source. Unfiltered results mix commercial and non-commercial, and CC BY needs credit. | 'whoosh': 4,227 sounds, 2,339 CC0. FAQ: Sampling+ 'can't make commercial advertisement'. https://freesound.org/help/faq/ |
| Coverr premium and AI clips | LICENSE AND QUALITY TRAP. Mixed into free results; premium files answer 200 with no login. | Ocean page: 3 of 61 ids user-ai-*, 8 *premium*. cdn.coverr.co/videos/coverr-premium-couple-observes-ocean-waves/1080p.mp4 answered 200. |
| Mixkit Restricted License items | LICENSE TRAP. A second license exists beside the free one. | https://mixkit.co/llm-info/ quote: 'Restricted License: Only allows use in personal, non-commercial projects.' That page also has 'INSTRUCTIONS FOR AI ASSISTANTS' to prom |
| Iconify sets without a license check | LICENSE TRAP. One API, mixed licenses. | https://api.iconify.design/collections : of 276 sets, CC-BY-4.0 53, GPL variants 6, CC-BY-NC variants 2. |
| React Bits as a redistributable kit | LICENSE TRAP for template or kit sellers. Using it in a video or app is fine. | LICENSE.md: 'so long as you do not sell, sublicense, or redistribute the components themselves'. gh reports NOASSERTION, not MIT. |
| GSAP in a visual no-code animation tool | LICENSE TRAP for products, including a Studio-style builder. Using it in a video is fine. | https://gsap.com/community/standard-license/ 'Prohibited Uses': tools 'that allow users to build visual animations without code' in a way that 'competes with Webflow's vi |
| Remotion at a company above 3 employees | LICENSE TRAP. Free only for individuals and small companies. | https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md 'a for-profit organization with up to 3 employees'. gh reports NOASSERTION. |
| Epidemic Sound free API plan | LICENSE TRAP. Free key is prototyping only. | https://developers.epidemicsound.com/ quote: 'Prototyping only, you cannot go live on this plan. Includes up to 50 downloads with no commercial license.' |
| Openverse as a hard dependency | Saved by thousands on X, default in HyperFrames, unreliable when tested. | 19 timed audio searches 2026-11-03 18:00-18:24 PST: 13 timed out at 40-60 s; 6 returned, most taking 18-38 s. Anonymous limits 20/min, 200/day from headers. category=soun |
| ShotDeck | Blocked, paid, no official agent route. GitHub scrapers carry terms risk. | 403 Cloudflare. talhapythoneer/shotdeck-scraper-movieimages. Popular post uses a reply-to-get funnel: https://x.com/starks_arq/status/2035367453711360340 |
| Eyecandy, Frameset | Blocked to curl. | eyecannndy.com 403 Cloudflare; frameset.app 403. |
| STEALSHOT free use | MCP lists tools without a key, then refuses every call. | tools/list 200. search_frames: 'search_frames needs STEALSHOT Pro.' |
| Meta Ad Library direct | Page blocks curl and the API needs a token. | Page 403. Graph call 500 OAuthException. X practitioners route through Apify: https://x.com/mikefutia/status/2016527020205941191 |
| TikTok Creative Center | Page is a shell and the internal API refuses. | creative_radar_api: {"code":40101,"msg":"no permission"}. |
| LottieFiles MCP as a search tool | The official MCP creates motion in Creator; it is not library search. Use GraphQL for search. | https://lottiefiles.com/mcp 'Create Lottie motion'. GraphQL searchPublicAnimations returned results with no key. |
| Motion Canvas for new work | Latest stable release is nearly two years old. | npm @motion-canvas/core 3.17.2, published 2024-12-14. |
| LUT sources that moved | Pages commonly cited are gone or blocked. | RocketStock LUT page 403 at shutterstock.com. groundcontrol.film/free-luts 404. rawpedia.rawtherapee.com/Film_Simulation 404. FreshLUTs /terms failed to connect. |
| Editing reading that blocks curl | Good text, no agent route. | blog.frame.io 403. vashivisuals.com 406. medium.com/@tonyszhou/postmortem 403. YouTube channel RSS 404. |
| The '17 assets from an ex-Anthropic motion designer' lists | Bait wrapper around a list of real sites, copied by several accounts. No named designer shown. The list omits license checks and includes unDraw. | @e1genqq 208 likes, 354 bookmarks, quoting their own X Article rather than a named person: https://x.com/e1genqq/status/2115899405542813923 , https://x.com/e1genqq/status |

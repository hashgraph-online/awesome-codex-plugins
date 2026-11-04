# Sources: social overlays

Every URL below was opened in this research session (web fetch, file download or X API), except where marked. Template keys: CTA = cta-pill-pop, FOL = follow-tap-prompt, STK = story-sticker, LIVE = live-badge, NOT = notification-drop, REV = review-proof-card, SUB = subscribe-nudge, COM = comment-callout, CNT = subscriber-counter, BAR = caption-bar-overlay, WALL = photo-wall-loop, SZ = platform-safe-zones.

## Practitioners on X

| n | Who | Why they count | Post | What we took | Used in |
|---|---|---|---|---|---|
| 32 | Paddy Galloway (@PaddyG96) | YouTube strategist; bio: 10B+ views generated, worked with MrBeast, Jesser, Red Bull; 158k followers | https://x.com/PaddyG96/status/1518958236480720897 | Intro "subscribe, smash like" asks show up as a retention drop | SUB, FOL |
| 33 | YouTube Creators (@YouTubeCreators) | YouTube's official creator account | https://x.com/YouTubeCreators/status/1402025908123353088 | Ask viewers to subscribe at the end of the video (after collabs) | SUB, FOL |
| 34 | Nick Nimmin (@NickNimmin) | YouTube growth educator, 18k followers on X | https://x.com/NickNimmin/status/1924991823870656562 | Ask simply, where it won't interrupt the viewing | SUB, FOL |
| 35 | Cody Wanner (@codywanner) | Filmmaker/YouTuber | https://x.com/codywanner/status/1159783080695083008 | Gained more subs on videos without an ask: "no formula" | SUB |
| 36 | Barry Hott (@binghott) | Performance ad creative strategist since 2008; 37k followers | https://x.com/binghott/status/1456028257246191624 · https://x.com/binghott/status/1524392639348498433 | Test 2 CTAs per video, then iterate CTAs on the winner; branding isn't needed in every ad | CTA |
| 37 | Dara Denney (@DenneyDara) | Performance creative consultant; 35k followers | https://x.com/DenneyDara/status/1546561057459773440 | Content-specific CTAs beat generic ones in UGC | CTA, FOL |
| 38 | jack friks (@jackfriks) | Indie app builder growing apps with short-form; 183k followers | https://x.com/jackfriks/status/2105708554590294063 (+ replies) | 100k views, almost no downloads because of a weak end CTA; fix: name the app and the store action | CTA, FOL |

## Platform docs and specs (primary)

| n | Source | URL | What we took | Used in |
|---|---|---|---|---|
| 1 | TikTok In-Feed safe-zone template file (Feed.png in the official zip linked from [2]) | https://lf-tt4b.tiktokcdn.com/obj/i18nblog/tt4b_cms/en-US/5jqet0ab9qci-10e7f5Vig4uhAscNP8XPB0.zip | 720×1280: 160 top, 440 bottom, 80 sides, 120-px right rail from y 560 → ×1.5 for 1080×1920 | all |
| 2 | TikTok Ads Help: Auction In-Feed Ads | https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en | Safe zone depends on caption length/anchors; LTR vs RTL files; caption rules | SZ |
| 3 | TikTok Ads Help: Creative best practices for performance ads | https://ads.tiktok.com/help/article/creative-best-practices?lang=en | Hook in first 6 s, proposition in first 3 s, 5–10 words/s text, hook→USP→CTA, sound on | CTA, NOT, REV, COM, STK, WALL |
| 4 | Meta Ads Guide: Instagram Reels video specs | https://www.facebook.com/business/ads-guide/update/video/instagram-reels | Leave 14% top, 35% bottom, 6% sides; 1440×2560 recommended; sound recommended | all |
| 5 | Google Ads Help: safe zone for vertical video ads on YouTube (+ its 1080×1920 SVG) | https://support.google.com/google-ads/answer/9128498?hl=en | 288 top, 672 bottom, 48 left, 192 right (read from the SVG text) | all |
| 6 | Snapchat Business Help: Single Image or Video creative best practices | https://businesshelp.snapchat.com/s/article/snap-ads-practices?language=en_US | 150 px top / 330 px bottom (382 with Offer Details). Page opened but renders by JS; figures read from Snap's indexed page text. Verify | BAR, SZ |
| 7 | Socialync safe-zone tools (TikTok, Shorts, Reels) | https://www.socialync.io/tools/safe-zones/tiktok · /youtube-shorts · /instagram-reels | Cross-check of conversions; note that platforms publish ad safe zones only | SZ |
| 8 | YouTube Help: Add end screens | https://support.google.com/youtube/answer/6388789?hl=en | Last 5–20 s, video ≥25 s, up to 4 elements (16:9), Subscribe element, suppresses other interactive elements | SUB |
| 9 | YouTube Help: Reply to comments with Shorts | https://support.google.com/youtube/answer/12816427 | Comment becomes a draggable, pinch-resizable sticker; commenter notified | COM |
| 10 | TikTok Newsroom: Reply to comments with video (2020) | https://newsroom.tiktok.com/product-tutorial-reply-to-comments-with-video?lang=en | Comment attached as sticker; 1.8B+ views on #replytocomments | COM |
| 14 | YouTube Brand Resources: Color | https://brand.youtube/color/ | YouTube Red #FF0033, Almost Black #212121, White (read from the page's colour attributes) | SUB, LIVE, COM, CNT, FOL |
| 17 | Meta Brand Resource Center: Instagram brand | https://www.meta.com/brand/resources/instagram/instagram-brand/ | Permission needed for Instagram interface in commercials/films; no implied partnership; don't modify the name | STK, FOL, LIVE |
| 18 | Snap: Brand guidelines | https://snap.com/en-US/brand-guidelines | Only the official Ghost logo; guidelines govern brand assets | BAR |
| 24 | Apple: App Store marketing guidelines | https://developer.apple.com/app-store/marketing/guidelines/ | Badge: one per video, don't animate/modify, ≥40 px, clear space ¼ height; fictional account data; single push notification on lock screen | CTA, REV, NOT |
| 31 | Apple HIG: Notifications (JSON of the page) | https://developer.apple.com/design/human-interface-guidelines/notifications | Concise title, title case, no ending punctuation, no app name, short distinctive sound, no sensitive info | NOT |

## Legal, credibility, accessibility

| n | Source | URL | What we took | Used in |
|---|---|---|---|---|
| 21 | FTC: Final rule banning fake reviews and testimonials (Aug 2024) | https://www.ftc.gov/news-events/news/press-releases/2024/08/federal-trade-commission-announces-final-rule-banning-fake-reviews-testimonials | Bans fake/AI reviews, non-existent reviewers, bought reviews, undisclosed insider reviews, suppression, fake followers/views for commercial influence; civil penalties | REV, COM, CNT, LIVE, FOL, WALL, STK |
| 22 | FTC: Disclosures 101 for social media influencers | https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers | Disclose in the video, audio and visual, near the endorsement, plain words; repeat during lives | CTA, REV, STK, LIVE |
| 23 | Trustpilot: Legal brand guidelines (Feb 2023) | https://corporate.trustpilot.com/legal/for-businesses/legal-brand-guidelines/feb-2023 | Review date + star rating beside quote; date stamp/count; no out-of-context quotes; name + logo required; "TrustScore" wording; permission advised; paid plans only | REV |
| 25 | Spiegel Research Center (Northwestern Medill): How online reviews influence sales | https://spiegel.medill.northwestern.edu/how-online-reviews-influence-sales/ | 5 reviews → 270% purchase likelihood; peak at 4.0–4.7 stars; 5.0 "too good to be true"; verified buyer +15% | REV |
| 42 | W3C: Understanding WCAG 2.1 SC 1.4.3 | https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html | 4.5:1 normal, 3:1 large (≥18 pt or ≥14 pt bold) | CTA, LIVE, SUB, WALL |

## Motion, build and tooling

| n | Source | URL | What we took | Used in |
|---|---|---|---|---|
| 26 | Material Design 3 motion tokens (material-components-android docs/theming/Motion.md) | https://github.com/material-components/material-components-android/blob/master/docs/theming/Motion.md | Emphasized decelerate (0.05,0.7,0.1,1), accelerate (0.3,0,0.8,0.15), standard (0.2,0,0,1); 50–1000 ms duration scale; duration grows with distance | all |
| 27 | GSAP source: gsap-core.js | https://github.com/greensock/GSAP/blob/master/src/gsap-core.js | `back` default overshoot 1.70158; elastic default period 0.3 (out) / 0.45 (inOut) | CTA, STK, NOT, FOL, COM |
| 28 | GSAP docs: Eases | https://gsap.com/docs/v3/Eases/ | Default ease power1.out; ease naming | LIVE |
| 29 | GSAP docs: seamlessLoop helper | https://gsap.com/docs/v3/HelperFunctions/helpers/seamlessLoop | horizontalLoop/verticalLoop mechanics, speed 1 ≈ 100 px/s, xPercent/yPercent wrap | WALL |
| 30 | Remotion docs: spring() | https://www.remotion.dev/docs/spring | Defaults mass 1, damping 10, stiffness 100; overshootClamping; durationInFrames | NOT, CTA |
| 39 | Motion (creative analytics): metrics cheat sheet + "Tell stories and build hypotheses with metrics" talk | https://help.motionapp.com/en/articles/7730931-metrics-cheat-sheet · https://runneth.com/library/talk/tell-stories-and-build-hypotheses-with-metrics/ | Hook = first 1–3 s; low Thruplay is fine with an early CTA/deal; change content right after the hook (4–8 s) when hold drops | CTA |
| 40 | HyperFrames registry item descriptions | https://github.com/heygen-com/hyperframes/tree/main/registry | Blocks/components: cta-lockup, cta-close, social-proof-card, star-rating-fill, store-badge-lockup, tiktok-follow, instagram-follow, x-follow-card, oversized-cursor, magnetic-cursor, native-notification-pop, macos-notification, notification-stack/pileup/cascade, liquid-glass-notification, yt-comment-card, badge-pop, count-up, apple-money-count, perspective-marquee, logo-wall, grid-card-assemble, dynamic-grid, lt-soft-pill, caption-pill-karaoke, vpn-youtube-spot, vfx-iphone-device | all |
| 41 | Google Fonts repo METADATA | https://github.com/google/fonts | Licence check: Inter, Roboto, Public Sans, Arimo, TikTok Sans, Figtree, Plus Jakarta Sans = OFL | all |

## Third-party references (lower authority; flagged where used)

| n | Source | URL | What we took | Used in |
|---|---|---|---|---|
| 11 | Tubefilter: YouTube might make the subscribe button glow (2023) | https://www.tubefilter.com/2023/09/11/youtube-subscribe-button-glow/ | Test: button glows red/orange/yellow ~1–2 s when "subscribe" is said (desktop) | SUB |
| 12 | Tubefilter: abbreviated subscriber counts (2019) | https://www.tubefilter.com/2019/05/21/youtube-display-abbreviated-subscriber-counts/amp/ | >1,000 abbreviated; truncated, not rounded up | CNT |
| 13 | Rival IQ Help: Why YouTube subscriber counts are rounded | https://help.rivaliq.com/en/articles/9788197-why-youtube-subscriber-counts-are-rounded | Rounded down to 3 significant figures in UI and API | CNT, LIVE |
| 15 | shadcn.io DESIGN.md: Twitch | https://www.shadcn.io/design/twitch/raw | twitch-purple #9147FF, live-red #EB0400, Inter body. (Twitch's own brand.twitch.com was opened too: it shows no hex values, only an asset zip.) | LIVE, FOL, CNT |
| 16 | shadcn.io DESIGN.md: TikTok + ColorFYI TikTok | https://www.shadcn.io/design/tiktok/raw · https://colorfyi.com/brands/tiktok | #FE2C55, #25F4EE, #000000 | LIVE, FOL, CNT |
| 19 | Kapwing: A complete guide to Snapchat text fonts | https://www.kapwing.com/resources/a-complete-guide-to-snapchat-text-fonts/ | Default = white text on semi-transparent grey full-width bar, not resizable; free-floating text with outline; Public Sans/Arimo alternatives | BAR |
| 20 | OpusClip: Snapchat Spotlight caption best practices | https://www.opus.pro/blog/snapchat-spotlight-caption | ≤40 chars/line, 2–3 lines, 4.5:1 contrast, ~1 s per 5 words, 5–8-word CTA | BAR |

## Cinematic analysis

Not applicable for this family: these are UI conversion overlays, and their craft is set by platform specs, ad analysts and creators rather than film criticism. No cinematic source was used.

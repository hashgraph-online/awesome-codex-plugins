# Imagera: image and video generation MCP server and skills

Generate and edit images, video, voice and music from Claude Code, Cursor, Codex, GitHub Copilot CLI, Gemini CLI and Grok CLI through the Imagera MCP server (`https://mcp.imagera.ai/mcp`, OAuth sign-in, no API key). Every run states its credit cost first, and `estimate_cost` quotes a request for free.

36 agent skills for [Imagera](https://imagera.ai): multi-step jobs (ID sheets, product photos, ads, films, websites) that an agent runs through the Imagera MCP server on your Imagera account, plus the base `imagera-media` skill for any single image, clip, voiceover or track a project needs.

## Install

One repo, every agent. Each install adds the Imagera MCP server and these skills; sign in with your Imagera account on first use.

| Agent | Install |
|---|---|
| Claude Code | `claude plugin marketplace add alexadams6ix/imagera-skills` then `claude plugin install imagera@imagera` |
| Codex | `codex plugin marketplace add alexadams6ix/imagera-skills`, then `/plugins` → imagera → Install |
| GitHub Copilot CLI | `copilot plugin marketplace add alexadams6ix/imagera-skills` then `copilot plugin install imagera@imagera` |
| Gemini CLI | `gemini extensions install https://github.com/alexadams6ix/imagera-skills` |
| Grok CLI | `grok plugin install https://github.com/alexadams6ix/imagera-skills --trust` |
| Cursor | Install from the Cursor marketplace, or add this repo under Dashboard → Plugins & MCPs → Add Marketplace |
| Any agent (skills only) | `npx skills add alexadams6ix/imagera-skills` |

Start with `imagera-media`: ask your agent for an image, clip, voiceover or track for your project.

Then add the Imagera MCP server (`https://mcp.imagera.ai/mcp`) to your agent and sign in with your Imagera account. Running a skill through MCP is part of the Pro plan. Every run is quoted in credits first (`run_skill` with `confirm: false`) and starts only after you agree.

## Only the MCP server

No plugin needed: any MCP client can add `https://mcp.imagera.ai/mcp` (Streamable HTTP) and sign in with an Imagera account on first use.

| Agent | Add the server |
|---|---|
| Claude Code | `claude mcp add --transport http imagera https://mcp.imagera.ai/mcp` |
| OpenCode | `opencode mcp add imagera --url https://mcp.imagera.ai/mcp` |
| Amp | `amp mcp add imagera https://mcp.imagera.ai/mcp` |
| Factory Droid | `droid mcp add imagera https://mcp.imagera.ai/mcp --type http` |
| Cline | `cline mcp add imagera https://mcp.imagera.ai/mcp --transport http` |
| Goose | `goose session --with-streamable-http-extension "https://mcp.imagera.ai/mcp"` |
| Windsurf, Zed, Kiro, Warp, LM Studio, Amazon Q and other apps | add a server with the URL above, or this `mcp.json` entry: `{"mcpServers":{"imagera":{"url":"https://mcp.imagera.ai/mcp"}}}` |

Step-by-step for every client: https://imagera.ai/mcp

## Tools

| Tool | What it does | Cost |
|---|---|---|
| `check_credits` | Check credits | free |
| `estimate_cost` | Estimate cost | free |
| `check_job` | Check job | free |
| `list_skills` | List skills | free |
| `check_skill_run` | Check skill run | free |
| `list_identities` | List saved IDs | free |
| `generate_image` | Generate image | credits, stated before it runs |
| `edit_image` | Edit image | credits, stated before it runs |
| `upscale_image` | Upscale image | credits, stated before it runs |
| `detect_ai` | Detect AI image | credits, stated before it runs |
| `generate_video` | Generate video | credits, stated before it runs |
| `animate_image` | Animate image | credits, stated before it runs |
| `enhance_video` | Enhance video | credits, stated before it runs |
| `generate_3d_model` | Generate 3D model | credits, stated before it runs |
| `generate_auto` | Imagera Auto | credits, stated before it runs |
| `generate_voice` | Generate voice | credits, stated before it runs |
| `clone_voice` | Clone voice | credits, stated before it runs |
| `generate_music` | Generate music | credits, stated before it runs |
| `chat_with_model` | Chat with model | credits, stated before it runs |
| `compare_models` | Compare models | credits, stated before it runs |
| `run_skill` | Run skill | credits, stated before it runs |
| `save_identity` | Save ID | credits, stated before it runs |
| `research_brand` | Research brand | credits, stated before it runs |

## Skills

| Skill | Job | When to use |
|---|---|---|
| [`imagera-product-listing-set`](skills/imagera-product-listing-set/SKILL.md) | Product listing photos | Someone has a photo of a product and needs marketplace-ready listing images: a clean hero on white plus lifestyle shots. |
| [`imagera-product-ad-video`](skills/imagera-product-ad-video/SKILL.md) | Product ad video | Someone needs a short video ad for a product and has only a photo: an eight-second clip with their line read aloud and captioned. |
| [`imagera-ad-variations`](skills/imagera-ad-variations/SKILL.md) | Ad variations to test | Someone wants several genuinely different executions of one ad concept to test against each other. |
| [`imagera-ugc-talking-review`](skills/imagera-ugc-talking-review/SKILL.md) | Talking product review | Someone wants a phone-style video of a creator holding their product and talking about it, lip-synced and captioned. |
| [`imagera-photo-to-reel`](skills/imagera-photo-to-reel/SKILL.md) | Reel from a photo | Someone has a good photo and wants it moving as a vertical eight-second clip with music under it, for social. |
| [`imagera-storyboard-to-shots`](skills/imagera-storyboard-to-shots/SKILL.md) | Storyboard to shots | Someone has a scene idea and wants to see it as four framed shots, then as clips joined into one cut. |
| [`imagera-character-consistency`](skills/imagera-character-consistency/SKILL.md) | The same character in every shot | Someone needs one character to look the same across three different scenes, starting from a single clear photo. |
| [`imagera-social-set`](skills/imagera-social-set/SKILL.md) | A week of posts, one look | Someone needs a batch of social posts that share one palette, light and framing, so a profile grid reads as one set. |
| [`imagera-title-art`](skills/imagera-title-art/SKILL.md) | Thumbnail and poster | Someone needs a title set in lettering that reads right, as a 16:9 thumbnail and a 2:3 poster. |
| [`imagera-series-bible`](skills/imagera-series-bible/SKILL.md) | Set your show up once | Someone is starting a series and needs the kit every later shot is generated against: lead turnarounds, empty location plates and a title card. |
| [`imagera-explainer-with-voice`](skills/imagera-explainer-with-voice/SKILL.md) | Explainer with a voiceover | Someone needs to explain something without being on camera: their script read aloud in a natural voice, with a picture for each beat. |
| [`imagera-music-video`](skills/imagera-music-video/SKILL.md) | Music video | Someone wants a music video for a song idea: the song written and sung, three matched vertical shots, joined and set to it. |
| [`imagera-poster-with-real-text`](skills/imagera-poster-with-real-text/SKILL.md) | A poster whose words are spelled right | Someone needs a poster, flyer, banner or sign whose words must be spelled exactly right. |
| [`imagera-restore-and-upscale`](skills/imagera-restore-and-upscale/SKILL.md) | Rescue an old or low-quality photo | Someone has an old, small, blurry or damaged photo and wants it repaired and enlarged. |
| [`imagera-ai-director`](skills/imagera-ai-director/SKILL.md) | AI Director | Someone has a story and wants a character and shot sheet plus a film shot from it: 8 seconds, 3 cuts. |
| [`imagera-cinematic-website`](skills/imagera-cinematic-website/SKILL.md) | Cinematic Website | a website or landing page for one brand, product, person or project, where one continuous film can carry the opening |
| [`imagera-journey-website`](skills/imagera-journey-website/SKILL.md) | Journey Website | a website whose story moves through several distinct places or stages — a voyage, a tour, a process from raw material to product |
| [`imagera-product-film-website`](skills/imagera-product-film-website/SKILL.md) | Product Film Website | a product page where one physical product, from the user's own photo, turns on a studio set as the visitor scrolls |
| [`imagera-character-id`](skills/imagera-character-id/SKILL.md) | Character ID | Someone needs the same character to look identical across many images or videos — a reusable Character ID sheet, no training. |
| [`imagera-object-id`](skills/imagera-object-id/SKILL.md) | Object ID | Someone needs the same object to look identical across many images or videos — a reusable Object ID sheet, no training. |
| [`imagera-location-id`](skills/imagera-location-id/SKILL.md) | Location ID | Someone needs the same location to look identical across many images or videos — a reusable Location ID sheet, no training. |
| [`imagera-digital-id`](skills/imagera-digital-id/SKILL.md) | Digital product ID | Someone needs the same digital product to look identical across many images or videos — a reusable Digital product ID sheet, no training. |
| [`imagera-property-id`](skills/imagera-property-id/SKILL.md) | Property ID | Someone needs the same property to look identical across many images or videos — a reusable Property ID sheet, no training. |
| [`imagera-influencer-studio`](skills/imagera-influencer-studio/SKILL.md) | Influencer Studio | Build an AI influencer from 31 kinds of choices, or start from a photo. You get a Character ID sheet that keeps the same face in every image and video. |
| [`imagera-brand-studio`](skills/imagera-brand-studio/SKILL.md) | Marketing Brand Studio | Someone wants several finished static ads (image + headline + call to action) for a product, to test on Meta, TikTok or Google. |
| [`imagera-marketing-studio`](skills/imagera-marketing-studio/SKILL.md) | Marketing Studio | Someone wants one polished marketing image of their own product in a known style (studio, lifestyle, ad, poster, marketplace listing). |
| [`imagera-podcast-clip-ad`](skills/imagera-podcast-clip-ad/SKILL.md) | Podcast clip ad | Someone wants a podcast-style clip ad: a host at a microphone talking about their product, lip-synced and captioned. |
| [`imagera-virtual-try-on`](skills/imagera-virtual-try-on/SKILL.md) | Virtual try-on | Someone wants to see a specific person wearing a specific garment, as a photo. |
| [`imagera-try-on-video`](skills/imagera-try-on-video/SKILL.md) | Mirror try-on video | Someone wants a vertical mirror try-on video of a model wearing their garment, for a product page or a reel. |
| [`imagera-headshot-set`](skills/imagera-headshot-set/SKILL.md) | Headshots from a selfie | Someone wants professional headshots from one ordinary photo of themselves. |
| [`imagera-photo-dump`](skills/imagera-photo-dump/SKILL.md) | Photo dump | Someone wants a set of casual, phone-style photos of one person (often an AI influencer) to post together. |
| [`imagera-static-ad-pack`](skills/imagera-static-ad-pack/SKILL.md) | Static ad pack | Someone wants several still feed ads for one product, with their headline or offer set as real text. |
| [`imagera-unboxing-video`](skills/imagera-unboxing-video/SKILL.md) | Unboxing video | Someone wants a first-person unboxing clip of their product, with sound, for social or a product page. |
| [`imagera-product-asmr`](skills/imagera-product-asmr/SKILL.md) | Product ASMR clip | Someone wants a slow, satisfying ASMR-style close-up of their product with crisp sound. |
| [`imagera-clay-explainer`](skills/imagera-clay-explainer/SKILL.md) | Claymation explainer | Someone wants a playful clay-animation clip in which their product, as a clay character, shows one idea. |
| [`imagera-carousel-post`](skills/imagera-carousel-post/SKILL.md) | Carousel post | Someone wants an Instagram or LinkedIn carousel whose slide text is spelled exactly right. |

Browse and run them on the web: https://imagera.ai/skills

Privacy policy: https://imagera.ai/privacy · Support: https://imagera.ai/support · License: MIT (see LICENSE)

Generated from the Imagera skill catalog (`npm run gen:skills-repo`). Edit the catalog, not these files.

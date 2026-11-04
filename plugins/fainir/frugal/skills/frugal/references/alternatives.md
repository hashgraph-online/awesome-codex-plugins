# Cheaper alternatives map

A starting list of free, open-source or cheaper options for tools people commonly pay for. It is a
map, not a price list: free tiers and plans change, so open the alternative's pricing page before
recommending it, and check that it covers the user's must-have features.

"Self-host" means free software, but the user pays for a server (often 4 to 10 USD a month on a
small VPS) and their own time for updates and backups. Say so when you suggest it.

Last reviewed: 2026-10-29.

## Design, photo and video

| Paid tool | Free or open source | Cheaper paid | Catch |
|-----------|---------------------|--------------|-------|
| Adobe Photoshop, Illustrator, InDesign | Affinity by Canva (one free app for photo, vector and layout since late 2025; AI features need Canva Pro), GIMP, Inkscape, Krita, Photopea (web) | Pixelmator Pro (one-time) | No Adobe cloud libraries; file round-trips with Adobe users can lose detail |
| Adobe Lightroom | darktable, RawTherapee, digiKam | Capture One, DxO (perpetual options) | Catalog migration |
| Adobe Premiere, Final Cut | DaVinci Resolve (free version), Kdenlive, Shotcut | | Resolve has a learning curve; some codecs need Studio |
| Figma | Penpot (open source, hosted or self-host), Figma Starter free tier, Figma Education (free for verified students and teachers) | | Plugin ecosystem smaller in Penpot |
| Canva Pro | Canva free tier, Canva for Education or Nonprofits (free if eligible), Affinity | | |
| Stock photos and icons | Unsplash, Pexels, Pixabay, Openverse, Lucide, Heroicons, Google Fonts | | Check each asset's license |
| Loom | OBS Studio, Cap (open source), the OS screen recorder | | No instant share link with OBS |

## Docs, notes, project management

| Paid tool | Free or open source | Cheaper paid | Catch |
|-----------|---------------------|--------------|-------|
| Microsoft 365 | LibreOffice, OnlyOffice, Google Docs (free personal), Microsoft 365 web apps (free) | Microsoft 365 Basic, Family plan split | Complex Excel macros may break |
| Notion | Obsidian (free for personal and work use since Feb 2025; Sync and Publish are paid add-ons), AppFlowy, Anytype, AFFiNE | Notion free plan for individuals, Notion Education (free Plus for students) | Collaboration differs a lot |
| Jira, Asana, Monday | Plane (open source), GitHub Projects, Linear free tier, Trello free tier, Taiga | Linear | Migration of history |
| Confluence | Outline, BookStack, Wiki.js (self-host), GitHub wiki | | |
| Miro | Excalidraw, tldraw, FigJam free tier | | |
| DocuSign | Docuseal, Documenso (open source), Adobe free fill and sign, OS preview signatures | Dropbox Sign lower tiers | Legal acceptance varies by country and document type |

## Communication and meetings

| Paid tool | Free or open source | Cheaper paid | Catch |
|-----------|---------------------|--------------|-------|
| Slack | Slack free tier, Mattermost, Zulip (free for open source and education), Rocket.Chat, Discord | Google Chat inside Workspace | History limits on free tiers |
| Zoom | Google Meet, Jitsi Meet, Microsoft Teams free | | Meeting length limits on free tiers |
| Calendly | Cal.com (open source), Google Calendar appointment schedules, Zoho Bookings free | | |
| Typeform, SurveyMonkey | Tally (generous free tier), Google Forms, Formbricks, LimeSurvey | | Branding on free tiers |
| Intercom, Zendesk | Chatwoot, Zammad, FreeScout (self-host), Crisp free tier | | Fewer integrations |

## Automation, data and analytics

| Paid tool | Free or open source | Cheaper paid | Catch |
|-----------|---------------------|--------------|-------|
| Zapier | n8n (self-host free; cloud paid), Activepieces, GitHub Actions or cron for simple jobs | Make, Pipedream | Self-host maintenance |
| Mixpanel, Amplitude, Heap | PostHog (open source, large free tier), Plausible or Umami (self-host), Google Analytics | | |
| Hotjar, FullStory | PostHog session replay, Microsoft Clarity (free) | | |
| Tableau, Looker | Metabase, Apache Superset, Grafana, Evidence | Looker Studio (free) | |
| Airtable | NocoDB, Baserow, Grist, Google Sheets | | |
| Mailchimp | Listmonk (self-host), Brevo or MailerLite free tiers, Buttondown | | Sending reputation is on you when self-hosting |
| SendGrid, Mailgun | Amazon SES (pay per use, very cheap), Resend free tier | Postmark | SES needs setup and warm-up |

## Developer infrastructure

| Paid tool | Free or open source | Cheaper paid | Catch |
|-----------|---------------------|--------------|-------|
| Heroku, Render paid tiers | Coolify, Dokku, CapRover on a small VPS; Cloudflare Workers and Pages free tiers; Vercel or Netlify hobby tiers | Hetzner, OVH, DigitalOcean, Fly.io, Railway | Hobby tiers often forbid commercial use: read the terms |
| AWS RDS, managed Postgres | Neon or Supabase free tiers, SQLite (with Litestream), Turso | Small VPS with Postgres | Free tiers pause or cap |
| Auth0, Okta | Better Auth, Auth.js, Lucia-style libraries, Keycloak, Authentik, Supabase Auth, Clerk free tier | | You own security of self-hosted auth |
| Datadog, New Relic | Grafana Cloud free tier, SigNoz, Prometheus and Grafana, Uptime Kuma | Better Stack | Ingest limits |
| Sentry paid | Sentry free tier, GlitchTip (self-host) | | |
| GitHub Copilot, Cursor paid | Copilot Free tier, free for verified students and some OSS maintainers; local models via Ollama or LM Studio with Continue | | Local models are weaker and need RAM |
| JetBrains IDEs | Free for non-commercial use: WebStorm, Rider, RustRover, CLion, RubyMine; IntelliJ and PyCharm community or unified free tiers; VS Code | | Commercial work needs a paid license |
| S3 storage with heavy downloads | Cloudflare R2 (no egress fees), Backblaze B2 | | Different API edge cases |
| Twilio SMS | Email or push instead of SMS, WhatsApp or Telegram bots | Vonage, Plivo | SMS pricing varies by country |

## AI subscriptions and APIs

| Paid thing | Free or cheaper route | Catch |
|------------|-----------------------|-------|
| Several chat subscriptions at once | Keep one; use free tiers of the others | Usage caps |
| A chat subscription you already pay for, plus API spend for personal coding agents | Many agents (Claude Code, Codex) can run on the subscription you already have | Plan limits; API stays better for production apps |
| Frontier model for every call in an app | A small model for routine calls, the big one only where evals show it is needed; prompt caching; batch APIs | Needs a quick eval to prove quality holds |
| Paid transcription (Otter etc.) | Whisper locally (MacWhisper, whisper.cpp) | Speed on older machines |
| Paid image generation | Free tiers, local Stable Diffusion or Flux variants | GPU needed for local |

## Consumer subscriptions and media

| Paid thing | Free or cheaper route | Catch |
|------------|-----------------------|-------|
| Audible, Kindle Unlimited, ebook purchases | Public library apps: Libby, Hoopla, Kanopy (free with a library card) | Wait lists |
| Several streaming services | Rotate: one service at a time, cancel and resubscribe; ad-supported tiers; family plans | Ad tiers have ads |
| Music | Family or duo plans; student plans; bundles (telecom or Apple One) | |
| Cloud storage (Dropbox) | The storage bundled in what they already pay for (Google One, iCloud+, Microsoft 365 includes 1 TB), Syncthing | |
| Password manager | Bitwarden (free tier, cheap premium), KeePassXC, the OS keychain | |
| VPN | Proton VPN free tier, the VPN bundled in other plans | Speed limits |
| Gym apps, meditation apps | Free YouTube programs, employer wellness perks, insurance perks | |
| Language apps | Duolingo free tier, library access to Mango Languages | |
| Mac utility apps bought one by one | Setapp bundle when they need 4 or more | Lose apps when unsubscribing |

# sitemd

Websites from Markdown. Built for AI coding assistants.

sitemd turns a folder of markdown files into a production-ready static website with navigation, search, themes, forms, analytics, SEO, and more — all configured through simple settings files.

## Quick Start

```bash
git clone https://github.com/sitemd-cc/sitemd.git my-site
cd my-site
./sitemd/install
./sitemd/sitemd launch
```

Open the dev server URL to see your site (port configured in `sitemd/settings/build.md`, default 4747). No Node.js required.

## AI Integration

sitemd includes an MCP server that works with Claude Code, Gemini CLI, and Codex CLI. The `.mcp.json` at the project root configures it automatically.

**Available MCP tools:** page management, content generation, site status, settings, deploy, clone, and more.

## Project Structure

```
my-site/
  sitemd/          ← Product directory
    sitemd         ← Compiled binary
    install        ← Bootstrap script (downloads binary)
    pages/         ← Your markdown content
    settings/      ← Site configuration (YAML frontmatter)
    theme/         ← CSS and HTML templates
    media/         ← Images and assets
    site/          ← Built output (gitignored)
  site.md          ← Setup instructions
```

## Features

- **Pages from Markdown** — Write content in `.md` files with frontmatter
- **Navigation** — Header, footer, sidebar groups, dropdowns, search
- **Themes** — Light, dark, paper modes with full color customization
- **Cards, Embeds, Galleries** — Rich content components
- **Forms** — Multi-page forms with conditional logic and webhooks
- **Analytics** — Google Analytics, Plausible, Fathom, PostHog, and more
- **SEO** — OG images, sitemaps, structured data, AI crawler control
- **User Auth** — Supabase, Firebase, Clerk, Auth0, custom API
- **Dynamic Data** — Connect to Supabase, Firebase, Airtable, REST APIs
- **Deploy** — `sitemd deploy` to Cloudflare, or host `site/` anywhere

## CLI Commands

```bash
./sitemd/sitemd launch          # Start dev server
./sitemd/sitemd deploy          # Build and deploy
./sitemd/sitemd clone <url>     # Clone a website into this project
./sitemd/sitemd auth login      # Log in to your account
./sitemd/sitemd config setup    # Configure services
./sitemd/sitemd scratch         # Reset to blank-slate
./sitemd/sitemd update          # Update to latest version
```

## Documentation

Full docs at [sitemd.cc/docs](https://sitemd.cc/docs)

## License

[Elastic License 2.0](LICENSE.md)

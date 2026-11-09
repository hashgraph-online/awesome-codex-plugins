# AdMakeAI: AI ad generator plugin for Claude, Codex, Cursor and Gemini

Design ads from a conversation. This plugin connects your agent to [AdMakeAI](https://admakeai.com), an ad design studio for performance marketers: on-brand ad creatives and ad copy, UGC-style video ads, the ads competitors run in the Meta Ad Library, and Meta (Facebook and Instagram) campaign drafts and reporting.

It bundles two pieces:

- **The AdMakeAI MCP server** (`https://admakeai.com/api/mcp`). You sign in with your AdMakeAI account through OAuth, so there's no API key to copy.
- **The [`admakeai-api`](skills/admakeai-api/SKILL.md) skill**, which teaches the agent which tool fits each request, to design into the right brand, what each call costs, and to confirm before anything that spends credits or touches your Meta ad account.

![AdMakeAI](./assets/icon.png)

## Install

**Claude Code**: the plugin, with the skill and the MCP server.

```bash
claude plugin marketplace add mesmerlord/admakeai-claude-plugin && claude plugin install admakeai@admakeai
```

Or inside Claude Code: `/plugin marketplace add mesmerlord/admakeai-claude-plugin`, then `/plugin install admakeai@admakeai`. Then run `/mcp`, pick `plugin:admakeai:admakeai` and choose **Authenticate** (nothing opens until you do). Sign in, or create a free account in the same step, and approve. Back in Claude Code, ask again: it doesn't retry a request from before you signed in. Before you sign in, Claude Code can already look up the Facebook ads any brand is running.

**Claude and ChatGPT**: add a custom connector with the URL `https://admakeai.com/api/mcp`. The app registers itself and sends you to AdMakeAI to sign in; no client ID or secret.

**Gemini CLI**: the extension, with the skill and the MCP server. Run `/mcp auth admakeai` in Gemini CLI to sign in.

```bash
gemini extensions install https://github.com/mesmerlord/admakeai-claude-plugin
```

**Codex**: the MCP server, then sign in through the browser.

```bash
codex mcp add admakeai --url https://admakeai.com/api/mcp && codex mcp login admakeai
```

**Cursor**: add the server to `~/.cursor/mcp.json` (or Settings, then MCP), and sign in when Cursor asks.

```json
{ "mcpServers": { "admakeai": { "url": "https://admakeai.com/api/mcp" } } }
```

**VS Code**:

```bash
code --add-mcp '{"name":"admakeai","type":"http","url":"https://admakeai.com/api/mcp"}'
```

**Kiro**: in the Powers panel, choose **Add Custom Power**, then **Import power from GitHub** with `https://github.com/mesmerlord/admakeai-claude-plugin`.

**The skill on its own** (Codex, Cursor, Copilot, Windsurf and 40+ agents), next to the MCP server above:

```bash
npx skills add mesmerlord/admakeai-claude-plugin
```

Clients without OAuth can send an API key instead, as `x-api-key` or `Authorization: Bearer`. Create one under [API keys](https://admakeai.com/dashboard/integrations/api).

## What to ask

- "Set up my brand from yourbrand.com and design a 4:5 Instagram ad for it." (a new account's first brand)
- "Design three 4:5 ads for my matcha brand aimed at tired founders."
- "What ads is Huel running on Meta right now? Save the longest-running one and remix it for my brand."
- "Write five headline and primary-text variations for that ad."
- "Make a UGC video ad for my skincare project."
- "How did my Meta ad account do last month compared to the month before?"
- "Draft a Meta campaign with these three ads, but don't push it until I say so."

New account? The agent asks for your brand's website and sets up your brand (product, audience, logo) from it before the first design.

## Permissions

You choose what to allow on AdMakeAI's consent screen. Tools outside what you grant are never shown to the agent.

| Permission | What it covers |
| --- | --- |
| Read your account | Profile, credit balance, projects, generated ads and Facebook ad performance |
| Create ads and drafts | Generate ad images and videos, upload source images, write ad copy and prepare campaign drafts. Spends credits |
| Upload ads and campaign drafts to Meta | Create real ads and campaign drafts in your connected Meta ad account |

Launching, pausing and resuming ads stay in Meta Ads Manager, and nothing is ever deleted through the plugin. Disconnect any time under Connected apps in your [dashboard](https://admakeai.com/dashboard/integrations/api).

## Cost

Reading, listing, competitor research and analytics are free. An ad design costs 2, 8 or 20 credits (low, high or ultra quality), a UGC video 5, 15 or 50, and an upload to Meta 3; failed designs are refunded. New accounts start with free credits, and plans start at $39 a month. Video ads and the Meta tools need a paid plan. See [pricing](https://admakeai.com/pricing).

## Data

The plugin has no local code and stores nothing. When you ask for something, the agent sends the inputs that request needs (a creative brief, reference images you provide, ad copy, or the IDs of your projects, ads or Meta campaigns) to your AdMakeAI account through the MCP server. AdMakeAI keeps the ads and drafts you create in your account and reaches Meta only for the ad accounts you connected. See the [privacy policy](https://admakeai.com/resources/privacy-policy) and [terms of service](https://admakeai.com/resources/terms-of-service).

## Support

Email [support@admakeai.com](mailto:support@admakeai.com) or open an [issue](https://github.com/mesmerlord/admakeai-claude-plugin/issues). Every tool is documented in the [API reference](https://admakeai.com/api/docs). AdMakeAI is made by Mesmer s.r.o.

## License

MIT

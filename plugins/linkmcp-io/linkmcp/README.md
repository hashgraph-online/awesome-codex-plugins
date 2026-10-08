# LinkMCP - hosted LinkedIn MCP server

**Your own LinkedIn account, as tools for Claude, ChatGPT, Codex, Cursor and Gemini.**

LinkMCP is a hosted MCP server for LinkedIn. You connect your LinkedIn account once in the web app. Then your AI assistant can research people and companies, search LinkedIn (also Sales Navigator, with your own seat), read and answer your LinkedIn messages, post, comment and react (as yourself or as a company page that you administer), manage invitations, and find work emails and mobile numbers. There is nothing to install and nothing to run.

[![Start your free 7-day trial](https://img.shields.io/badge/Start%20your%20free%207--day%20trial-005ccc?style=for-the-badge)](https://app.linkmcp.io/login?utm_source=github&utm_medium=readme&utm_content=cta-top)

No card. Sign in with an email code or Google. Setup takes about a minute.

---

## Quick start

1. **Start the trial** at [app.linkmcp.io](https://app.linkmcp.io/login?utm_source=github&utm_medium=readme&utm_content=quickstart).
2. **Add LinkMCP to your AI client** with the steps for your client below. Your client opens a browser window. Sign in to LinkMCP and approve.
3. **Ask.** Copy one of the [example prompts](#example-prompts).

The endpoint is the same for every client:

```
https://app.linkmcp.io/api/mcp
```

Transport: Streamable HTTP. Sign-in: OAuth in the browser. If your client cannot do OAuth, send an access key as `Authorization: Bearer <key>`. You create the key in the web app under **API Keys**.

> **What works in the free trial:** profile and company lookups, the posts and comments of people and companies, and email and phone finding. To act as yourself on LinkedIn (people search, inbox, invitations, posting, company pages), subscribe and connect your LinkedIn account once in the web app.

### Claude (web and desktop)

[**Add to Claude**](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=LinkMCP&connectorUrl=https%3A%2F%2Fapp.linkmcp.io%2Fapi%2Fmcp) opens the "Add custom connector" dialog with the name and URL filled in. Or do it by hand:

1. In Claude, open **Customize > Connectors**, click **+** and choose **Add custom connector**.
2. Name it `LinkMCP` and paste `https://app.linkmcp.io/api/mcp`.
3. Click **Add**, then **Connect**, and approve the sign-in window.

On Team and Enterprise plans, an Owner adds the connector in **Organization settings > Connectors**. Then each member clicks **Connect**. The Free plan allows one custom connector.

### Claude Code

```bash
claude mcp add --transport http linkmcp https://app.linkmcp.io/api/mcp
```

Then run `/mcp` in Claude Code, select `linkmcp` and choose **Authenticate**.

### ChatGPT

Developer mode needs ChatGPT Plus, Pro, Business, Enterprise or Edu (not Free), on the web.

1. Open **Settings > Security and login** and turn on **Developer mode**.
2. Go to [chatgpt.com/plugins](https://chatgpt.com/plugins), click **+**, name it `LinkMCP` and paste `https://app.linkmcp.io/api/mcp`.
3. Create the connection and approve the sign-in window.
4. In a new chat, click **+ > Developer mode** and turn on LinkMCP.

A workspace admin can turn Developer mode off for a Business or Enterprise workspace.

### Codex

Codex CLI:

```bash
codex mcp add linkmcp --url https://app.linkmcp.io/api/mcp
```

Codex opens the sign-in window. If it does not, run `codex mcp login linkmcp`.

Codex app and IDE extension: open the settings menu, select **MCP servers > Add server**, name it `LinkMCP`, choose **Streamable HTTP**, paste the endpoint, save, and click **Authenticate**.

### Cursor

[![Add LinkMCP to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=linkmcp&config=eyJ1cmwiOiJodHRwczovL2FwcC5saW5rbWNwLmlvL2FwaS9tY3AifQ==)

Or add this to `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (one project):

```json
{
  "mcpServers": {
    "linkmcp": { "url": "https://app.linkmcp.io/api/mcp" }
  }
}
```

Restart Cursor and approve the sign-in window.

### Gemini CLI

Install LinkMCP as a Gemini CLI extension:

```bash
gemini extensions install https://github.com/linkmcp-io/linkmcp
```

Or add only the server:

```bash
gemini mcp add --transport http linkmcp https://app.linkmcp.io/api/mcp
```

Then start Gemini CLI and run `/mcp auth linkmcp` to sign in.

### Other clients (VS Code, Windsurf, n8n, Make, Zapier)

VS Code:

```bash
code --add-mcp '{"name":"linkmcp","type":"http","url":"https://app.linkmcp.io/api/mcp"}'
```

- **Windsurf and other MCP clients:** add a remote MCP server with the endpoint above.
- **n8n, Make, Zapier:** use the MCP client node or module of the platform with the endpoint and an access key. Step by step: [n8n guide](docs/connect-linkedin-to-n8n.md), [Make guide](docs/connect-linkedin-to-make.md).

---

## Example prompts

Copy a prompt, replace the parts in angle brackets, and paste it into your AI client.

**These work in the free trial:**

```
Look up the company linkedin.com/company/stripe on LinkedIn and give me a short
brief: what they do, how big they are and what they posted recently.
```

```
Look up the LinkedIn profile <profile URL> and give me a short brief: role, company,
time in the role, and what they posted in the last month.
```

```
Find the work email of <full name> at <company domain> and validate it.
```

```
Here are LinkedIn profile URLs: <URLs>. Make a table with name, title, company and
location.
```

**These need a paid plan, with your LinkedIn account connected:**

```
Find heads of RevOps at Series B SaaS companies in the Netherlands. Summarise what
each one posted in the last month.
```

```
List my LinkedIn conversations with no reply in 7 days. Check what each person
posted recently and draft a reply for each. Show me the drafts before you send
anything.
```

```
Who do I know at <company>? Show my shared connections with their VP of Sales and
draft a short intro request.
```

```
Who reacted to my last post? Which of them are marketing directors that I am not
connected to? Draft a connection note for the top 10.
```

```
List the LinkedIn company pages that I administer. Draft a post for our page about
<topic>. Show it to me, and publish it as the page only after I say OK.
```

---

## The 34 tools

Tools marked **trial** work in the free trial. All tools work on every paid plan.

| Category | Tools |
|---|---|
| **Profiles and companies** | `linkedin_get_profile` (trial), `linkedin_get_company` (trial, by URL or ID), `linkedin_bulk_get_profiles` (trial), `linkedin_bulk_get_companies` (trial) |
| **Search** | `linkedin_search_people`, `linkedin_search_sales_navigator`, `linkedin_search_jobs` |
| **Posts and engagement** | `linkedin_get_person_posts` (trial), `linkedin_get_company_posts` (trial), `linkedin_get_post_comments` (trial), `linkedin_get_nested_comments`, `linkedin_get_post_reactions` |
| **Messaging** | `linkedin_list_conversations`, `linkedin_get_conversation_messages`, `linkedin_send_message` (also InMail), `linkedin_mark_conversation_read` |
| **Connections** | `linkedin_get_connections`, `linkedin_get_shared_connections`, `linkedin_list_connection_requests`, `linkedin_manage_connection_request`, `linkedin_send_connection_request` |
| **Content** | `linkedin_create_post`, `linkedin_comment_on_post`, `linkedin_react_to_post` |
| **Company pages** | `linkedin_list_company_pages`, plus the `as_page` option on `linkedin_create_post`, `linkedin_comment_on_post` and `linkedin_react_to_post` |
| **Your LinkedIn** | `linkedin_who_am_i`, `linkedin_get_post_analytics`, `linkedin_get_profile_views`, `linkedin_get_my_engagement`, `linkedin_get_my_saved_items` |
| **Contact finding** | `find_email` (trial), `validate_email` (trial), `find_mobile` (trial) |
| **Utility** | `send_feedback` |

26 tools only read. 8 tools write: send a message, send a connection request, accept, decline or withdraw a connection request, create a post, comment, react, mark a conversation as read, and send feedback. Every tool has a title and a read-only or write annotation, so your client can ask you before a write. Full parameter documentation: [llms-full.txt](https://app.linkmcp.io/llms-full.txt).

**Company pages:** your AI can post, comment and react as a LinkedIn company page that you administer. It must name the page with `as_page`. Without `as_page`, it acts as you. Actions as a page count toward the same daily limits as your own actions.

---

## Pricing

- **Free trial:** 7 days, no card. The tools marked **trial** work at once. Connecting your own LinkedIn account needs a paid plan.
- **Starter:** $19 per month. If you subscribe from a new trial, your first month is $9.50.
- **Pro:** $49 per month (5x the Starter usage). **Max:** $199 per month (50x the Starter usage).
- Every paid plan includes every tool. Each plan has a monthly usage allowance and a hard cap, so a looping agent cannot run up a bill. Top-up packs cost $10.

Current prices: [app.linkmcp.io/#pricing](https://app.linkmcp.io/#pricing)

---

## Account risk and limits

Any automated use of LinkedIn can put an account at risk, and no tool can promise that LinkedIn will not restrict an account. LinkMCP limits the risk:

- Server-side rate limits on every call, and a warm-up limit for connection requests on new or quiet accounts.
- Your LinkedIn password is not stored. The LinkedIn session runs on dedicated session infrastructure, not in your browser.
- No bulk scraping and no mass exports. No training on your data.
- Read [Will my LinkedIn get banned?](https://app.linkmcp.io/guides/will-my-linkedin-get-banned) before you automate at volume.

---

## FAQ

**Is LinkMCP open source?** No. This repository holds the documentation and client configuration. The server is a hosted service, and its code is not public. There is nothing to install or run locally.

**Is LinkMCP an official LinkedIn product?** No. LinkMCP is an independent product of Third Person Systems LLC. It is not affiliated with or endorsed by LinkedIn, and it does not use an official LinkedIn partner API.

**Do I need Sales Navigator?** No. LinkMCP works with a normal LinkedIn account. If you have a Sales Navigator seat, the Sales Navigator search tool uses it.

**Which AI clients work?** Every client that supports remote MCP servers: Claude (web, desktop, Claude Code), ChatGPT (Developer mode), Codex, Cursor, Gemini CLI, VS Code, Windsurf, n8n, Make and Zapier.

---

## Guides

- [Connect LinkedIn to ChatGPT](docs/connect-linkedin-to-chatgpt.md)
- [Connect LinkedIn to Claude](docs/connect-linkedin-to-claude.md)
- [Connect LinkedIn to n8n](docs/connect-linkedin-to-n8n.md)
- [Connect LinkedIn to Make](docs/connect-linkedin-to-make.md)
- [LinkedIn outbound funnel recipe for Make and n8n](docs/linkedin-outbound-funnel-recipe.md)
- [LinkMCP and other LinkedIn MCP options](docs/linkmcp-vs-alternatives.md)
- [LinkedIn MCP vs Expandi and PhantomBuster](docs/linkedin-mcp-vs-expandi-phantombuster.md)
- [Will my LinkedIn get banned?](docs/will-my-linkedin-get-banned.md)
- More guides: [app.linkmcp.io/guides](https://app.linkmcp.io/guides). Docs for LLMs: [llms.txt](https://app.linkmcp.io/llms.txt)

## Support

- In your AI client, ask it to use the `send_feedback` tool.
- [GitHub issues](https://github.com/linkmcp-io/linkmcp/issues) for documentation and configuration problems.
- Email: info@linkmcp.io

[![Start your free 7-day trial](https://img.shields.io/badge/Start%20your%20free%207--day%20trial-005ccc?style=for-the-badge)](https://app.linkmcp.io/login?utm_source=github&utm_medium=readme&utm_content=cta-bottom)

---
© Third Person Systems LLC. LinkMCP is independent. It is not affiliated with, endorsed by, or built on an official API of LinkedIn.

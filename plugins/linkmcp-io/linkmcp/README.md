# LinkMCP - hosted LinkedIn MCP server

**Your own LinkedIn account, as tools for Claude, ChatGPT, Codex, Cursor and Gemini.**

LinkMCP is a hosted MCP server for LinkedIn. You connect your LinkedIn account once in the web app. Then your AI assistant can research people and companies, search LinkedIn (also Sales Navigator, with your own seat), read and answer your LinkedIn messages, post, comment and react (as yourself or as a company page that you administer), manage invitations, and find work emails and mobile numbers. There is nothing to install and nothing to run.

[![Start your free 7-day trial](https://img.shields.io/badge/Start%20your%20free%207--day%20trial-005ccc?style=for-the-badge)](https://app.linkmcp.io/?utm_source=github&utm_medium=readme&utm_content=cta-top)

No card. Sign in with an email code or Google. Setup takes about a minute.

This repository is also a plugin with 7 skills for Claude, Codex, Gemini CLI and other AI agents. See [Plugin and skills](#plugin-and-skills).

---

## Quick start

1. **Start the trial** at [app.linkmcp.io](https://app.linkmcp.io/login?utm_source=github&utm_medium=readme&utm_content=quickstart).
2. **Add LinkMCP to your AI client** with the steps for your client below. Your client opens a browser window. Sign in to LinkMCP and approve.
3. **Ask.** Copy one of the [example prompts](#example-prompts).

The endpoint is the same for every client:

```
https://app.linkmcp.io/api/mcp?ref=github
```

Transport: Streamable HTTP. Sign-in: OAuth in the browser. If your client cannot do OAuth, send an access key as `Authorization: Bearer <key>`. You create the key in the web app under **API Keys**.

> **What works in the free trial:** profile and company lookups, the posts of people and companies, with their comments and reactions, and email and phone finding. To act as yourself on LinkedIn (people search, inbox, invitations, posting, company pages), subscribe and connect your LinkedIn account once in the web app.

### Claude (web and desktop)

[**Add to Claude**](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=LinkMCP&connectorUrl=https%3A%2F%2Fapp.linkmcp.io%2Fapi%2Fmcp%3Fref%3Dgithub) opens the "Add custom connector" dialog with the name and URL filled in. Or do it by hand:

1. In Claude, open **Customize > Connectors**, click **+** and choose **Add custom connector**.
2. Name it `LinkMCP` and paste `https://app.linkmcp.io/api/mcp?ref=github`.
3. Click **Add**, then **Connect**, and approve the sign-in window.

On Team and Enterprise plans, an Owner adds the connector in **Organization settings > Connectors**. Then each member clicks **Connect**. The Free plan allows one custom connector.

### Claude Code

```bash
claude mcp add --transport http linkmcp "https://app.linkmcp.io/api/mcp?ref=github"
```

Then run `/mcp` in Claude Code, select `linkmcp` and choose **Authenticate**.

### ChatGPT

Add LinkMCP in ChatGPT on the web, in **Plugins**. We saw **Add custom MCP server** on ChatGPT Plus (2026-10-21); OpenAI's help page also names Business and Enterprise/Edu.

1. Open [chatgpt.com/plugins](https://chatgpt.com/plugins), click **Add** and choose **Add custom MCP server**.
2. Name it `LinkMCP`, choose **Server URL**, paste `https://app.linkmcp.io/api/mcp?ref=github` and leave Authentication on **OAuth**.
3. Tick **I understand and want to continue**, click **Create** and sign in to LinkMCP in the window that opens.
4. In a chat, type **@** and choose LinkMCP.

On a Business workspace, only admins and owners can add a custom MCP server; on Enterprise and Edu, admins decide who can.

### Codex

Codex CLI:

```bash
codex mcp add linkmcp --url "https://app.linkmcp.io/api/mcp?ref=github"
```

Codex opens the sign-in window. If it does not, run `codex mcp login linkmcp`.

Codex app and IDE extension: open the settings menu, select **MCP servers > Add server**, name it `LinkMCP`, choose **Streamable HTTP**, paste the endpoint, save, and click **Authenticate**.

### Cursor

[![Add LinkMCP to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=linkmcp&config=eyJ1cmwiOiJodHRwczovL2FwcC5saW5rbWNwLmlvL2FwaS9tY3A/cmVmPWdpdGh1YiJ9)

Or add this to `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (one project):

```json
{
  "mcpServers": {
    "linkmcp": { "url": "https://app.linkmcp.io/api/mcp?ref=github" }
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
gemini mcp add --transport http linkmcp "https://app.linkmcp.io/api/mcp?ref=github"
```

Then start Gemini CLI and run `/mcp auth linkmcp` to sign in.

### Other clients (VS Code, Windsurf, n8n, Make, Zapier)

VS Code:

```bash
code --add-mcp '{"name":"linkmcp","type":"http","url":"https://app.linkmcp.io/api/mcp?ref=github"}'
```

- **Windsurf and other MCP clients:** add a remote MCP server with the endpoint above.
- **n8n, Make, Zapier:** use the MCP client node or module of the platform with the endpoint and an access key. Step by step: [n8n guide](docs/connect-linkedin-to-n8n.md), [Make guide](docs/connect-linkedin-to-make.md).

---

## Plugin and skills

This repository is also a plugin. The plugin adds the LinkMCP server to your AI client, and it adds 7 skills. A skill is a short set of instructions that tells your AI how to do one task with the LinkMCP tools.

| Skill | What you get | Free trial | What it sends to LinkedIn |
|---|---|---|---|
| [`linkedin-prospect-list`](skills/linkedin-prospect-list/SKILL.md) | Paste profile links. Get a ranked prospect list: role, company size and website, a recent post topic, the work email with its status, and why each person fits. | Yes | Nothing |
| [`linkedin-hiring-signal-leads`](skills/linkedin-hiring-signal-leads/SKILL.md) | Companies that hire for a role your product supports, a reason to contact them now, and the hiring team with their work emails when the job post shows the team. | Yes, with job links | Nothing |
| [`linkedin-candidate-shortlist`](skills/linkedin-candidate-shortlist/SKILL.md) | Screen candidates against the must-haves of a role, with evidence from each profile, the gaps and questions for the first call. | Yes, with profile links | Only the invitations that you approve, one at a time |
| [`linkedin-prospect-search`](skills/linkedin-prospect-search/SKILL.md) | Find people who match your ideal customer with LinkedIn or Sales Navigator search, research the best matches, and connect with notes that you approve. | No | Only the invitations that you approve, one at a time |
| [`linkedin-account-brief`](skills/linkedin-account-brief/SKILL.md) | A one-page brief before a call: the company and its recent posts, the people you meet, shared connections, talking points and questions. | Yes, except shared connections | Nothing |
| [`linkedin-engagement-leads`](skills/linkedin-engagement-leads/SKILL.md) | The people who commented on or reacted to a post, as a ranked lead list. | Yes, except replies to comments | Nothing |
| [`linkedin-inbox-followup`](skills/linkedin-inbox-followup/SKILL.md) | LinkedIn conversations with no reply for 7 days or more, with short follow-up drafts. | No | Only the messages that you approve, one at a time |

"No" in the free trial column means that the skill needs your own LinkedIn account, which is part of the paid LinkMCP plans.

### Install the plugin

**Claude (web, desktop and Cowork):** open **Customize > Plugins**, choose **Add > Add marketplace** and enter `linkmcp-io/linkmcp`. Add the **LinkMCP** plugin. Then open the **Connectors** tab of the plugin, connect LinkMCP and approve the sign-in window.

If you added LinkMCP before as a custom connector, remove that connector after you connect the plugin. Then Claude sees one set of LinkMCP tools.

**Claude Code:**

```bash
claude plugin marketplace add linkmcp-io/linkmcp
claude plugin install linkmcp@linkmcp
```

Then run `/mcp`, select the LinkMCP server and choose **Authenticate**. If you added LinkMCP before with `claude mcp add`, remove it with `claude mcp remove linkmcp`.

**Codex:**

```bash
codex plugin marketplace add linkmcp-io/linkmcp
codex plugin add linkmcp@linkmcp
```

Instead of the second command, you can open `/plugins` in Codex and install **LinkMCP**. Sign in to LinkMCP when Codex asks.

**Gemini CLI:** the extension install command in [Gemini CLI](#gemini-cli) installs the server and the skills.

**Other agents (skills only):** this command installs the 7 skills in Claude Code, Codex, Cursor, GitHub Copilot, OpenCode and many other agents. Then add the LinkMCP server to your agent as [Quick start](#quick-start) shows.

```bash
npx skills add linkmcp-io/linkmcp
```

### Try the skills

These prompts work in the free trial:

```
Rank these LinkedIn profiles as prospects for <what you sell> and find the work
emails of the best ones: <profile links>
```

```
Find leads from these LinkedIn job posts. We sell <what you sell>. Who is on the
hiring team, and why should we contact them now? <job links>
```

```
Screen these candidates for a <role> opening. Must-haves: <3 to 5 requirements>.
<profile links>
```

```
Prepare me for my call with linkedin.com/company/stripe tomorrow. I will meet
<profile URL>. The goal of the call is a first demo.
```

```
Who engaged with this LinkedIn post? <post URL>. Make a lead list of marketing
leaders at B2B software companies.
```

With your LinkedIn account connected (paid plans):

```
Find 20 heads of sales at software companies in Germany with 50 to 500 employees.
Show me the best matches, then draft connection notes. I approve each one.
```

```
Find my LinkedIn conversations with no reply for 7 days or more and draft
follow-ups. Show me each draft before you send anything.
```

### What the plugin does with your data

The plugin contains only text, configuration files and a logo. It runs no code on your computer. When your AI uses a LinkMCP tool, your AI client sends the tool input to `https://app.linkmcp.io/api/mcp`, for example a profile URL, a job URL, a post URL, search words or the text of a message or invitation that you approved. LinkMCP gets the data or does the action, and sends back the result. Messages and other actions on LinkedIn use your connected LinkedIn account. Four skills only read data. Three skills can send a LinkedIn message or invitation from your account. Each one asks you to approve the exact text, for one person at a time, before it sends. Privacy policy: [app.linkmcp.io/legal/privacy](https://app.linkmcp.io/legal/privacy).

If a skill says that the LinkMCP tools are missing, connect the LinkMCP server in your AI client and sign in.

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
Who reacted to my last post? Make a lead list of the marketing directors that I am
not connected to.
```

```
List the LinkedIn company pages that I administer. Draft a post for our page about
<topic>. Show it to me, and publish it as the page only after I say OK.
```

---

## The 35 tools

Tools marked **trial** work in the free trial. All tools work on every paid plan.

| Category | Tools |
|---|---|
| **Profiles and companies** | `linkedin_get_profile` (trial), `linkedin_get_company` (trial, by URL or ID), `linkedin_bulk_get_profiles` (trial), `linkedin_bulk_get_companies` (trial) |
| **Search** | `linkedin_search_people`, `linkedin_search_sales_navigator`, `linkedin_search_jobs`, `linkedin_get_job` (trial) |
| **Posts and engagement** | `linkedin_get_person_posts` (trial), `linkedin_get_company_posts` (trial), `linkedin_get_post_comments` (trial), `linkedin_get_nested_comments`, `linkedin_get_post_reactions` (trial) |
| **Messaging** | `linkedin_list_conversations`, `linkedin_get_conversation_messages`, `linkedin_send_message` (also InMail), `linkedin_mark_conversation_read` |
| **Connections** | `linkedin_get_connections`, `linkedin_get_shared_connections`, `linkedin_list_connection_requests`, `linkedin_manage_connection_request`, `linkedin_send_connection_request` |
| **Content** | `linkedin_create_post`, `linkedin_comment_on_post`, `linkedin_react_to_post` |
| **Company pages** | `linkedin_list_company_pages`, plus the `as_page` option on `linkedin_create_post`, `linkedin_comment_on_post` and `linkedin_react_to_post` |
| **Your LinkedIn** | `linkedin_who_am_i`, `linkedin_get_post_analytics`, `linkedin_get_profile_views`, `linkedin_get_my_engagement`, `linkedin_get_my_saved_items` |
| **Contact finding** | `find_email` (trial), `validate_email` (trial), `find_mobile` (trial) |
| **Utility** | `send_feedback` |

27 tools only read. 8 tools write: send a message, send a connection request, accept, decline or withdraw a connection request, create a post, comment, react, mark a conversation as read, and send feedback. Every tool has a title and a read-only or write annotation, so your client can ask you before a write. Full parameter documentation: [llms-full.txt](https://app.linkmcp.io/llms-full.txt).

**Company pages:** your AI can post, comment and react as a LinkedIn company page that you administer. It must name the page with `as_page`. Without `as_page`, it acts as you. Actions as a page count toward the same daily limits as your own actions.

---

## Pricing

- **Free trial:** 7 days, no card. The tools marked **trial** work at once. Connecting your own LinkedIn account needs a paid plan.
- **Starter:** $39 per month. If you subscribe from a new trial, your first month is $19.50.
- **Pro:** $49 per month (2.5x the Starter usage). **Max:** $199 per month (25x the Starter usage).
- Every paid plan includes every tool. Each plan has a monthly usage allowance and a hard cap, so a looping agent cannot run up a bill. Top-up packs cost $10.

Current prices: [app.linkmcp.io/#pricing](https://app.linkmcp.io/#pricing)

---

## Account risk and limits

How LinkMCP protects your LinkedIn account:

- Server-side rate limits on every call, and a warm-up limit for connection requests on new or quiet accounts.
- Your LinkedIn password is not stored. The LinkedIn session runs on dedicated session infrastructure, not in your browser.
- No bulk scraping and no mass exports. No training on your data.
- Read [Will my LinkedIn get banned?](https://app.linkmcp.io/guides/will-my-linkedin-get-banned) before you automate at volume.

As with any tool that acts on LinkedIn for you, a restriction cannot be ruled out completely; these limits keep the risk low.

---

## FAQ

**Is LinkMCP open source?** No. This repository holds the documentation, the client configuration and the skills. The server is a hosted service, and its code is not public. You do not install or run a server on your computer.

**Is LinkMCP an official LinkedIn product?** No. LinkMCP is an independent product of Third Person Systems LLC. It is not affiliated with or endorsed by LinkedIn, and it does not use an official LinkedIn partner API.

**Do I need Sales Navigator?** No. LinkMCP works with a normal LinkedIn account. If you have a Sales Navigator seat, the Sales Navigator search tool uses it.

**Which AI clients work?** Every client that supports remote MCP servers: Claude (web, desktop, Claude Code), ChatGPT (custom MCP server in Plugins), Codex, Cursor, Gemini CLI, VS Code, Windsurf, n8n, Make and Zapier.

---

## Guides

- [Connect LinkedIn to ChatGPT](docs/connect-linkedin-to-chatgpt.md)
- [Connect LinkedIn to Claude](docs/connect-linkedin-to-claude.md)
- [Connect LinkedIn to n8n](docs/connect-linkedin-to-n8n.md)
- [Connect LinkedIn to Make](docs/connect-linkedin-to-make.md)
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

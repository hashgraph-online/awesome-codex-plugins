# Clera MCP

<!-- mcp-name: com.getclera/clera -->

Hire with agents, straight from your chat.

Clera MCP connects hiring teams and job seekers to Clera through Claude, ChatGPT, Cursor, Codex, Grok and other MCP clients. Hiring teams can search vetted startup candidates, review recommended matches, request introductions and manage hiring. Candidates can find startup roles, compare matches, track applications and apply after confirming each external action.

- **Server URL:** `https://mcp.getclera.com`
- **Transport:** Streamable HTTP
- **Auth:** OAuth 2.1 with dynamic client registration. Sign in with your Clera company or candidate account.
- **Pricing:** Free during the beta. Companies pay a success fee on hire. Always free for candidates.
- **Docs:** https://www.getclera.com/mcp/docs
- **Hiring setup:** https://www.getclera.com/mcp
- **Candidate setup:** https://www.getclera.com/mcp/talent

## MCP server configuration

Clera is a **hosted remote MCP server**, not a package you clone or run locally. The URL below uses Streamable HTTP and OAuth 2.1; sign in to your Clera company or candidate account when your MCP client prompts you. Tool discovery is permission-scoped, so unauthenticated directory crawlers should read the documented tool catalog below instead of expecting an anonymous `tools/list` response.

**Remote HTTP configuration** (Cursor, Claude Code-compatible clients, and clients supporting a URL):

```json
{
  "mcpServers": {
    "clera": {
      "type": "http",
      "url": "https://mcp.getclera.com"
    }
  }
}
```

**Standard MCP stdio configuration** (Claude Desktop or clients needing a local bridge to the remote server):

```json
{
  "mcpServers": {
    "clera": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.getclera.com"]
    }
  }
}
```

Both configurations connect to the same hosted server. The stdio example requires Node.js and uses the community `mcp-remote` bridge; it does not host Clera locally.

## Install

**Claude (web and desktop):** [Add to Claude](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Clera&connectorUrl=https%3A%2F%2Fmcp.getclera.com), or Settings > Connectors > Add custom connector and paste `https://mcp.getclera.com`.

**ChatGPT:** Settings > Plugins > Advanced settings > turn on Developer mode, then add `https://mcp.getclera.com`.

**Claude Code:**

```bash
claude mcp add --transport http clera https://mcp.getclera.com
```

Or install the plugin (MCP plus the Clera hiring skill):

```bash
/plugin marketplace add getclera/mcp
/plugin install clera@clera
```

**Codex:**

```bash
codex mcp add clera --url https://mcp.getclera.com
codex mcp login clera
```

**Cursor:** add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "clera": { "url": "https://mcp.getclera.com" }
  }
}
```

**Grok:** Connectors > New Connector > Custom, paste `https://mcp.getclera.com`.

**Any MCP client:** add a remote MCP server with URL `https://mcp.getclera.com`. Clients without native OAuth can use `npx mcp-remote https://mcp.getclera.com`.

## Tools

These are **documented, real tool names** on the hosted Clera MCP server. The available tool list depends on the signed-in account and its permissions: company members see hiring tools, candidates see job-search tools, and `whoami` is available to signed-in users. The tools below are representative; see the [full MCP tool reference](https://www.getclera.com/mcp/docs) for the complete, current inventory. Write actions require the user's approval in supported clients.

### `whoami`

All accounts (read): show your connected account kind and organization memberships.

### `searchCandidates`

Hiring teams (read): search vetted startup candidates by profile, skills, experience and location.

### `similarCandidates`

Hiring teams (read): find candidates similar to a candidate in your shortlist.

### `listFilterOptions`

Hiring teams (read): list supported candidate-search filter values.

### `listRecommendedCandidates`

Hiring teams (read): review candidates Clera recommended for your open roles.

### `getCandidateProfile`

Hiring teams (read): inspect a candidate profile returned by another hiring tool.

### `requestIntro`

Hiring teams (write, requires confirmation): request an introduction to a candidate for a role.

### `passCandidate`

Hiring teams (write): decline a candidate for a role and record the reason.

### `listPipeline`

Hiring teams (read): see candidates by stage in the hiring pipeline.

### `readJob`

Hiring teams (read): list or read open hiring roles and their requirements.

### `editJob`

Hiring teams (write): create or update hiring roles, descriptions and screening details.

### `getSalaryBenchmark`

Hiring teams (read): compare a role's pay range with comparable opportunities.

### `readCompanyProfile`

Hiring teams (read): inspect the company profile candidates see.

### `editCompanyContact`

Hiring teams (write): create or update hiring-team contacts.

### `listTeamMembers`

Hiring teams (read): see teammates with access to the company account.

### `getDashboardLink`

Hiring teams (read): obtain a direct link to a hiring dashboard section.

### `searchCleraRoles`

Job seekers (read): search open roles at startups recruiting directly through Clera.

### `searchJobs`

Job seekers (read): search jobs across the wider market.

### `readJobListing`

Job seekers (read): get full details for a job listing.

### `saveJob`

Job seekers (write): bookmark a job to review later.

### `listMatches`

Job seekers (read): list personalized Clera role matches.

### `readMatch`

Job seekers (read): inspect a matched opportunity, requirements and company details.

### `likeMatch`

Job seekers (write, requires confirmation): express interest in a startup match.

### `listMyPipeline`

Job seekers (read): review the status of your opportunities and interviews.

### `listInterviewRequests`

Job seekers (read): list interview invitations awaiting a decision.

### `acceptInterview`

Job seekers (write, requires confirmation): accept an interview invitation.

### `applyToJob`

Job seekers (write, requires confirmation): prepare and send an external job application after approval.

### `getApplicationRun`

Job seekers (read): check the result or outstanding steps of an application submission.

### `listApplications`

Job seekers (read): review tracked job applications and their stages.

### `listResumes`

Job seekers (read): list resumes and identify the current primary resume.

### `getCareerRecord`

Job seekers (read): review your experience, education and skills held by Clera.

### `getTalentDashboardLink`

Job seekers (read): get a direct link to your candidate dashboard.

### `sendFeedback`

Hiring teams (write): send feedback or a bug report to Clera support.

## What you can ask

| You say | Tools |
| --- | --- |
| Find senior backend engineers in Berlin with Go and Postgres experience. | `searchCandidates` |
| Show me the candidates Clera pre-selected for our Head of Product role. | `listRecommendedCandidates` |
| Pull up the full profile for this candidate and tell me if they're a fit. | `getCandidateProfile` |
| Help me write a job description for a Staff Frontend Engineer, remote in DACH. | `editJob` |
| Intro me to the top 3 candidates for the backend role. | `searchCandidates`, `requestIntro` |
| Who on my team has access? Add our new hiring manager. | `listTeamMembers`, `editCompanyContact` |
| Find remote product-engineering roles and show the strongest matches. | `searchCleraRoles`, `searchJobs` |
| Apply to that outside job after I approve the details. | `readJobListing`, `applyToJob`, `getApplicationRun` |

Read tools run right away. External actions such as intros, match likes and applications require user approval in supported clients. Access to candidate information is scoped to the signed-in account and permissions. See the [MCP documentation](https://www.getclera.com/mcp/docs) for details.

## Privacy

Clera sees only the arguments of the tools your assistant calls, never the rest of your conversation. Privacy policy: https://www.getclera.com/privacy. Terms: https://www.getclera.com/terms.

## Support

hello@getclera.com, or ask your assistant to use the `sendFeedback` tool.

## This repo

Config and listing metadata for the hosted Clera MCP server: `server.json` (Official MCP Registry), `.cursor-plugin/` (Cursor Marketplace), `.claude-plugin/` (Claude Code plugin marketplace), `skills/clera/SKILL.md` (agent skill). The server itself is hosted by Clera.

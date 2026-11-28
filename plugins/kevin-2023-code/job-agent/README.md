# job-agent for OpenAI Codex

Generated from [job-agent](https://github.com/kevin-2023-code/job-agent) by `scripts/gen-plugins.mjs`. Don't edit files here; edit the repository root and regenerate.

Open-source job-search skills: find and score roles, tailor your résumé, fill application forms in your browser up to Submit, track applications and prep for interviews.

- **Connected:** the plugin registers the TrueInterview MCP server (`https://trueinterview.io/api/mcp`). Sign in once in the browser for live jobs across companies, real interview data, fit scores, form answers from your saved records, and a tracker shared with the website.
- **Local:** without signing in, every skill works from your own files in `~/job-agent` (or `$JOB_AGENT_HOME`): résumé, preferences, `knowledge/`, and the public job boards of the companies you list.

Start by saying **"set me up"**. See the repository README for everything else.

## Data, people search and AI models

- **Where your data goes.** The TrueInterview MCP server is run by TrueCode Technologies Inc. What you ask its tools about, and what you choose to save (résumé, job search, form answers, notes, tracker), is kept in your TrueInterview account. Privacy policy: https://trueinterview.io/privacy
- **Another AI model writes some answers.** Résumé reading and tailoring, cover letters, drafted form answers, fit scores and the people search send your request to an AI model that writes the result. TrueInterview runs them on Anthropic's Claude, with DeepSeek models through OpenRouter as the fallback. Under the API terms TrueInterview uses, your inputs are not used to train those models.
- **People search (`find_contacts`).** Only when you ask, it looks for people at one employer you could contact about a role.
  - *Sources:* Google search results for public LinkedIn profiles, fetched through Apify; when that finds too few, an AI model's web search (through OpenRouter) of public pages such as LinkedIn profiles, company team and careers pages, engineering blog author pages and conference talk pages.
  - *What is kept:* a name, a headline, the public profile link and the page it was found on, never an email address or phone number, stored only in the account of the person who searched.
  - *Legal basis* (where the GDPR applies): TrueInterview's legitimate interest in helping a candidate research an employer, limited to public professional information (privacy policy, sections 2(d) and 3).
  - *Opt-out:* anyone listed can ask to be removed by emailing kevin@trueinterview.io with the link to their profile.

MIT licensed.

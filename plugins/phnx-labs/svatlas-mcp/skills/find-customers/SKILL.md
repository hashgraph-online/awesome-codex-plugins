---
name: find-customers
description: Build a target-customer list for a product from the Silicon Valley Atlas startup directory. Use when someone wants to know which startups would buy their product, wants prospects or leads for a website, or asks to turn a product URL into an outreach list.
---

# Find customers for a product

Connect the hosted SV Atlas MCP server at `https://svatlas.io/mcp` and sign in
with your existing Atlas Google account before using these tools. Never ask
for a password or token in chat. If the server is unavailable or sign-in is
required, explain how to connect and stop; do not invent results. Tool names
may have a client-specific prefix; use the connected server's tool catalog.
Search and product matching use the account's monthly quota; other reads do
not.

For OpenClaw, configure the connection once with
`openclaw mcp set svatlas '{"url":"https://svatlas.io/mcp","transport":"streamable-http","auth":"oauth"}'`,
then `openclaw mcp login svatlas`. Installing this skill does not connect the
server. Ask before creating or changing outreach lists.

1. Get the product's website. If the person describes the product instead,
   ask for the URL once; if there is none, use `search_companies` with a
   plain-language description of the buyer.
2. Call `match_companies_by_website` with the URL. Show the ideal-customer
   profile it wrote in one or two sentences so the person can correct it,
   then the top matches as a short table: name, one-liner, batch, website.
3. For the matches the person cares about, call `get_company` and lead with
   what makes each one a fit: stage, team size, latest round, and the signal
   that ties it to the product. Cite the source links the tool returns.
   Do not add facts the tool did not return.
4. To reach one, call `warm_paths` with its slug. It returns who in the
   person's own imported contacts can introduce them and why, with a draft
   ask to edit before sending. If it reports no import, point them to
   Settings → Network on svatlas.io. Never send a message for them.
5. Offer to save them. Use `list_lists` to find an existing list, or
   `create_list`, then `add_to_list` with the slugs. Report what was added,
   skipped, or unknown, and link `https://svatlas.io/lists`.

Meaning search and URL matching have monthly limits. If a tool says the limit
is reached, tell the person when it resets and continue with `get_company`,
`search_people`, and the list tools, which are not limited.

Link each company as `https://svatlas.io/companies/<slug>`.

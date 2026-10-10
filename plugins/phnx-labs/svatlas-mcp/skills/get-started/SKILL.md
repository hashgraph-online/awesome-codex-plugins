---
name: get-started
description: First-run setup for Silicon Valley Atlas. Use right after the plugin is installed, or when someone asks how to start with SV Atlas, what it can do, or how to build their first prospect list.
---

# Get started with Silicon Valley Atlas

The hosted SV Atlas MCP server at `https://svatlas.io/mcp` must be connected and
signed in with the person's Atlas Google account. If a tool call says sign-in
is required, tell them to finish connecting SV Atlas and stop; never ask for a
password or token in chat, and do not invent results.

Keep the whole setup to three short turns.

1. Say in one sentence what Atlas is: a sourced map of AI startups, their
   founders, funding, and investors, where every fact links to its source.
   Then ask one question: "What do you sell? Paste your product's website,
   or describe who you want to reach."
2. With a URL, call `match_companies_by_website`. With a description, call
   `search_companies`. Show the result as it renders (in ChatGPT, the Atlas
   cards), state the ideal-customer profile in one sentence if there is one,
   and name the three strongest fits with the reason each fits.
3. Offer to save them: "Want these on a list?" Only on a yes, call
   `create_list` with a name the person agrees to, then `add_to_list` with
   the slugs they chose, and say how many were added.

Close with where to find things next time. In ChatGPT, Atlas has its own
entry in the sidebar (search, lists, and company profiles), and **My lists**
can be opened as a tab beside any conversation. Selecting companies there
attaches them to the chat. Everything also lives at https://svatlas.io.

Search and product matching count toward the account's monthly limit; reading
profiles and lists does not. If a call reports the monthly limit, say so
plainly and continue with what does not need it.

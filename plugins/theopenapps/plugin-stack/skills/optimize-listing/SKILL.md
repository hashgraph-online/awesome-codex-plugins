---
name: optimize-listing
description: "Optimize a live AI plugin's store listing: name, description, keywords and category, compared with the category's top listings and their recent rewrites, ending in paste-ready copy. Use for ChatGPT, Claude or Cursor listings, keywords missing against named rivals, what top apps changed in their copy, ASO, or when a plugin isn't getting installs. Not for custom GPTs, mobile apps or a first submission's copy."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# Optimize listing

## Read at each step

| Step | Read |
|---|---|
| 1 | `.agents/plugin-stack.md` if present, [references/data.md](references/data.md) |
| 1-5 | [references/compare.md](references/compare.md) |
| 3 | [references/words.md](references/words.md) |
| 2-5 | `references/stores/<store>.md` for each store in scope |

A store with no file here: work from its own docs and say the report has no checked notes for it.

## Steps

1. **Fix the scope.** The listing refs, the target prompts and the competitors. With no live listing, name the `submit-plugin` skill and stop. Done when each is named or the user has declined it.
2. **Pull.** The listing and its versions, its ranks, the category's top listings, and recent rewrites among the competitors and the category's top, per compare.md. Done when every competitor's current copy is in hand.
3. **Pick words.** Done when each candidate word has its top results read or a stated gap, and each target word has a field.
4. **Compare.** Field by field. Done when every field has a verdict, keep or change, and the listings behind it.
5. **Rewrite.** Paste-ready copy with its character count against the store's limit, its target file and the cost of the change, clear of the store file's preflight. Done when every change verdict has copy, citing its listings.
6. **Report.** The copy by field, biggest change first, the word table, the current ranks as a dated baseline, then this line: 'No study yet shows that rewrites move ranks.' If `.agents/plugin-stack.md` exists, add `optimize-listing: <today>, top fix: <fix>` under Runs without asking, in your own words. Done when every number has its date and basis.

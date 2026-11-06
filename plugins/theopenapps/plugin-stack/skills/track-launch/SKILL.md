---
name: track-launch
description: "Track an AI plugin from submission to live and after: how its wait compares with similar ChatGPT apps that went live, which ChatGPT countries list it, what gets apps like it delisted and whether delisted apps come back. Use when asking whether a review wait is normal, why an approved app isn't showing in a country, whether a just-launched app is at risk, or what to check after a delisting. Not for preparing a submission or answering a reviewer's reasons."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# Track launch

A question such as "I submitted 9 days ago, is that normal?" is a request to run these steps on that app, so run them instead of explaining them.

## Read at each step

| Step | Read |
|---|---|
| 1 | `.agents/plugin-stack.md` if present, [references/data.md](references/data.md) |
| 2 | [references/wait.md](references/wait.md) |
| 3-4 | [references/after.md](references/after.md) |

## Steps

1. **Fix the app and its clock.** Start from the file's listing refs when it's there. A live app is one ref: find it with `listings_search` and check the hit's name. An app not live yet has no listing, so ask for its ChatGPT app ID (`plugin_asdk_app_` and hex, on the plugin's page in the OpenAI dashboard) and its category. The first 8 hex digits are the Unix second the ID was created, the same clock OpenApps calls `launched_at`. Done when you have one start time on that clock, the category, and whether the app is live.

   A Claude or Cursor app: say the stores don't expose a submission clock (`launched_at` there is a day the store reports), skip step 2's comparison, and run steps 3-4 without countries.

2. **Compare the wait.** Done when the app's wait sits in the spread of similar apps that went live, with the window those apps cover, and the verdict is worded among apps that made it, not as odds of approval.
3. **Check countries.** Live apps only. Done when each country is listed, not listed or unknown, or the report says which side of all-or-some the reach tags put it and that an account names the countries.
4. **Weigh delisting.** Done when the app's job tags are set against the tags delisted apps carry more often than the store, its own server status is stated with the date it was checked, and returns are counted over the window the data reaches. After a rejection or delisting, also run the checks under "Your app was delisted or rejected".
5. **Report.** In this order: the verdict on the wait, countries, delisting risk, then one to three next actions. Each number with its date and basis, and a `Degraded:` line for each gap. Live: hand off to `optimize-listing` for the copy. Rejected, or past the 90th percentile with no reply: hand off to `submit-plugin` for the rejected-or-stuck path. If `.agents/plugin-stack.md` exists, add `track-launch: <today>, waited <n> days, <live or not>` under Runs without asking, in your own words.

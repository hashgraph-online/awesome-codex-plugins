---
name: setup
description: Connect sync. labs (sync.so) to this agent and get a first lip-synced video. Use when the user explicitly asks to install, set up, connect or get started with sync. labs, when sync. tools are missing or signed out, or for questions about their sync. account, plan or remaining credits. Media requests go to their workflow skill, which links to the same connection steps.
license: MIT
compatibility: Uses the hosted sync. MCP server (https://mcp.sync.so/mcp) or a SYNC_API_KEY.
---

# Set up sync. labs

Gets a new user from install to a first result in a couple of minutes. Setup itself never starts paid work.

## Steps

1. **Check the connection.** If sync. tools such as `account_get-context` are available, call `account_get-context` and `account_get-usage`, then go to step 3.
2. **Connect.** Follow [references/connect.md](references/connect.md) for this client: the hosted MCP server with sign-in for most people, or an API key for scripts and CI. If the client needs a restart to load the server, say so and stop there.
3. **Account.** Greet the user by organization name and say what's available: credits, the free allowance, or the plan's limits (`generationLimits.maxOutputDurationSeconds`, `generationLimits.concurrency`). Don't promote plans.
4. **What it can do.** Offer these, one example prompt each:
   - **Lipsync a video:** "Lipsync ./interview.mp4 to ./new-take.wav"
   - **Make a photo talk:** "Make this portrait say: welcome to the team"
   - **Make an AI clip talk:** "My Veo clip has no dialogue. Make the character say this line."
   - **Translate and dub:** "Dub this YouTube video into Spanish"
   - **Fix a few spoken words:** "Change the price I say in this video to $49"
   - **Localize a campaign:** "Make these 3 ads in Spanish, German and Japanese"
   - **Many videos at once:** "Lipsync each row of this CSV"
   - **Build it into an app:** "Add sync. lipsync to my Next.js app"
5. **Fastest first win.** If the user isn't sure, suggest a talking photo: one image and one line of text, no recording needed. Then follow the talking-photo skill: quote, get approval, create.

## Rules

- Quote before every paid generation and wait for approval.
- If there are no credits or free generations left, say so plainly and point to https://sync.so/billing/subscription. Don't start a job that will fail.
- Keep it to one short message for the account and the choices, then follow the user's lead.

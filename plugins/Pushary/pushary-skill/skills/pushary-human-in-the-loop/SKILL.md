---
name: pushary-human-in-the-loop
version: 0.1.4
description: Design and build a human-in-the-loop (HITL) approval step into an AI agent or an agent product. Use this skill when you are writing or changing agent code and need to decide which actions should ask a human first, who answers, which question type to use, how long to wait and what happens when nobody answers, or when you are adding approval to LangGraph, the Vercel AI SDK, the OpenAI Agents SDK, Mastra, CrewAI, Pydantic AI, an MCP client or a REST backend. Explains what framework pauses such as LangGraph interrupt() do and do not do, and how to ask a human for approval by push notification on their phone with Pushary and get the answer back. Use it for requests such as add an approval step to my agent, require human sign-off before this tool runs, add human review to my LangGraph graph, or let my users approve what my agent does. For an agent that already has the Pushary tools and needs to ask its own user now, use the pushary skill instead.
metadata:
  hermes:
    tags: [human-in-the-loop, hitl, approvals, push-notifications, agents]
    category: productivity
    requires_toolsets: []
  tags: human-in-the-loop, hitl, approvals, push, notifications, mcp, langgraph, ai-sdk, openai-agents, mastra, crewai, pydantic-ai
---

# Human-in-the-loop for AI agents

A human-in-the-loop step stops an AI agent before a consequential action, asks a person, and continues only on their answer. This skill covers when to add one, the choices that shape it, and how to build it with Pushary in each way people build agents.

If your agent already has the Pushary MCP tools and needs the rules for calling them, use the `pushary` skill. It also covers setting Pushary up for a person.

## When to ask a person

Ask before the agent:

- **Does something it cannot undo.** Deleting data, dropping a table, force-pushing, overwriting a file it did not create.
- **Spends money.** A payment, a refund, paid API calls at volume, provisioning anything billable.
- **Speaks for someone.** An email, message or post to a customer or anyone outside the team.
- **Changes production.** A deploy, a release, a publish, a migration.
- **Makes a call outside its authority.** Pricing, a product decision, a security or legal tradeoff.
- **Would guess on a long unattended run.** Two readings of the task are both reasonable, and the wrong one wastes the run.

Do not ask when a file, a command or a lookup can settle it. That is a fact, not a decision. Do not ask when the step is reversible, costs nothing, sends nothing out and stays inside the task. Take the default and report it at the end. Do not ask twice about a step the person already approved.

## Design the step

**Who answers.** Name one answerer for each kind of step: you, the developer running the agent; a teammate or a role, such as whoever is on call; or your product's end user, the person the agent acts for. Take an end user's id from your authenticated session, never from the model's tool input, so a prompt-injected model cannot send the approval to someone else.

**What the question looks like.**

| Type | Use it for | The answer |
| --- | --- | --- |
| `confirm` | Permission for one action | `yes` or `no` |
| `select` | A choice among known options | The chosen option |
| `input` | A fact only the person knows | Free text |

Only a `confirm` answered yes is permission. A `select` or `input` answer is data, even when its text is "yes". Write the question so it can be answered from a lock screen: name the action, the target and the effect. "Refund $480 to order #4471?" works. "Proceed?" does not. Put background in a context field. When the person picks between known options, ask one `select` instead of several `confirm` questions, and keep `confirm` for the permission itself.

**How long to wait.** One request should not hold for long. Pushary caps each REST wait at 55 seconds and each MCP call at 48. For a longer wait, save the run, let the request end, and resume from a signed callback or a poll. With the decisions API, set `expiresInSeconds` so a late answer cannot approve work that has moved on. Cancel a REST or MCP question that no longer applies.

**What happens when nobody answers.** Nothing runs. A timeout, an expiry, a cancellation or a person with no connected device is a no, never an approval. Tell the agent it was not approved, so it stops instead of retrying. When you retry a request, reuse its idempotency key so the person is not asked twice.

**Keep a record.** Store what was asked, who answered, the answer and when. Pushary keeps an append-only audit trail of every question and answer at Dashboard > Agent > Activity. The filterable table and CSV or JSON export need Agent Pro, Team, Partner or Enterprise.

**Ask or gate.** An ask is a tool the model may call, and a model in a hurry can skip it. A gate is the framework's own approval hook. It runs before the tool executes, and the model cannot skip it. Gate anything that spends money, deletes data or leaves your system. Give the model an ask tool for the rest.

## What framework pauses do

Most agent frameworks can pause a run:

| Framework | Native pause |
| --- | --- |
| LangGraph | `interrupt()` stops a node, the checkpointer saves state, and `Command` resumes it |
| Vercel AI SDK 7 | `toolApproval` calls your function before a tool executes |
| OpenAI Agents SDK | `needsApproval` stops the run with `result.interruptions` |
| Mastra | `requireApproval: true` suspends the run |
| Pydantic AI | `requires_approval=True` defers the call, and with `DeferredToolRequests` in `output_type` the run ends and returns it |
| CrewAI | `human_input=True` prompts in the console |
| MCP | Elicitation lets a server request input through the client's own screen |

These pause the run. None of them reaches a person who is away from the screen, and most wait for code you write to resolve them. Pushary is that part. It sends the question to the person's phone as a push notification, waits, and returns the answer. The adapters below plug into each native pause. In Claude Code, Pushary's hooks also send MCP elicitations to your phone.

## Add it with Pushary

Who answers decides which API you use:

| Who answers | Use | Plan |
| --- | --- | --- |
| You or your team | MCP `ask_user`, or REST `POST /api/v1/server/ask` | A paid plan. Routing to a teammate or role needs Team. |
| Your product's end users | The Partner decisions API, through `@pushary/server`, the Python `pushary` SDK or any framework adapter | Partner |

### Your own AI agents

For Claude Code, Codex, Cursor, Gemini CLI, Hermes and other agents on your machine:

```bash
npx -y pushary@latest setup
```

An agent running this for someone runs it in the background with its output going to a log, and keeps it running: setup waits up to 15 minutes for the phone, and a foreground command that times out kills the pairing code. Show the person the link, the QR and the fingerprint from the log as they print, and wait for setup to exit before you report the result.

Setup pairs your phone, then installs the MCP connection, hooks where the agent supports them, and the `pushary` skill. Follow that skill from there. Hooks are what enforce an approval. Through MCP alone, the agent decides when to ask.

### Any MCP client

```json
{
  "mcpServers": {
    "pushary": {
      "url": "https://pushary.com/api/mcp/mcp",
      "headers": { "Authorization": "Bearer ${PUSHARY_API_KEY}" }
    }
  }
}
```

Some clients do not expand `${PUSHARY_API_KEY}`. Paste the key there instead. The agent gets `ask_user`, `wait_for_answer`, `cancel_question` and `send_notification`.

Ask with `ask_user`:

```json
{ "question": "Deploy release 2.4.0 to production?", "type": "confirm", "context": "All checks passed on main.", "agentName": "Deploy bot - api" }
```

One call waits at most 48 seconds and can return the answer at once. Proceed only on `answered: true` with `value: "yes"`. On `status: "pending"`, call `wait_for_answer` with the same `correlationId` and `timeoutMs: 55000`. Follow `handoffAction` when present, otherwise `nextAction`. `expired`, `cancelled`, `missing` and `unavailable` are not approval. Call `cancel_question` when the question no longer matters. The `pushary` skill has the full result table.

Tell with `send_notification`:

```json
{ "title": "Backfill finished", "body": "Processed 12,400 rows with 0 errors.", "agentName": "Backfill - warehouse", "context": { "type": "task_complete" } }
```

### REST, from your own backend

```bash
curl -X POST https://pushary.com/api/v1/server/ask \
  -H "Authorization: Bearer $PUSHARY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Deploy the new build to production?","agentName":"Deploy bot","timeoutSeconds":50}'
```

The call waits up to `timeoutSeconds` (1 to 55, default 30). It returns `status: "answered"` with `value`, `status: "timeout"`, or `status: "stopped"` with a `handoffAction` when the person has stopped the agent in Pushary. A stopped call leaves no question to poll: either none was sent, or the stop closed the one that was, so stop the task. After a timeout, the question stays open for 10 minutes. Read it again with `GET /api/v1/server/ask/{correlationId}?wait=30`, or withdraw it with `DELETE` on the same path. A Partner workspace gets 403 `partner_decision_required` here and uses decisions instead.

### Your product's end users (Partner)

Connect each user once, then ask before the risky step:

```ts
import { createPusharyServer } from '@pushary/server'

const pushary = createPusharyServer({ apiKey: process.env.PUSHARY_API_KEY! })

const { universalLink } = await pushary.enroll(user.id)

const decision = await pushary.decisions.ask({ externalId: user.id, question: 'Refund $480 to order #4471?' })
if (decision.approved) await issueRefund()
```

```python
import os
from pushary import PusharyServer

pushary = PusharyServer(api_key=os.environ["PUSHARY_API_KEY"])
decision = pushary.decisions.ask("Refund $480 to order #4471?", external_id=user.id)
if decision["approved"]:
    issue_refund()
```

Show `universalLink` to that user as a button or QR code. It expires after 24 hours, so store that they connected, not the link. They install the free Pushary app and never sign up or pay. `enroll` needs a full-access key on your server. Give the agent runtime a runtime or user-bound key.

`ask` waits up to 55 seconds. `approved` is true only for an answered `confirm` with yes. For `select` and `input` it only means answered, so read `value`. The decision stays answerable for 1 hour by default. Save `decisionId` and read it later with `decisions.get`, or pass `callbackUrl` and check the signed webhook with `verifyWebhookSignature`. To test without a phone, use a sandbox key: https://pushary.com/docs/agents/embed-testing.

### Framework adapters

Each adapter runs on the Partner plan, takes `externalId` from your code and fails closed. Functions such as `issueRefund` and `refund_order_once` are your own. The approval gates for the AI SDK, the OpenAI Agents SDK, Mastra and Pydantic AI check your site's rules first, and a rule can allow or deny without asking anyone. Pass `policy: false` (`policy=False` in Python) when a person must always decide.

**Vercel AI SDK** (`npm i @pushary/ai-sdk ai zod`). Gate one tool and leave the others alone. The gate needs AI SDK 7 and Node.js 22 or later.

```ts
import { generateText } from 'ai'
import { pusharyApproval } from '@pushary/ai-sdk'

const { text } = await generateText({
  model: 'openai/gpt-4o',
  tools: { issueRefund, lookupOrder },
  toolApproval: pusharyApproval({ externalId: user.id, tools: ['issueRefund'] }),
  prompt: 'Refund order 1234.',
})
```

**LangGraph** (`npm i @pushary/langgraph @langchain/langgraph @langchain/core zod`, or `pip install pushary-langgraph`). Put a review node before the protected node, and route to the protected node only on yes:

```ts
import { pusharyInterrupt } from '@pushary/langgraph'

const reviewRefund = async (state: { customerId: string; orderId: string }) => {
  const answer = await pusharyInterrupt(
    { apiKey: process.env.PUSHARY_API_KEY },
    { externalId: state.customerId, question: `Refund order ${state.orderId}?`, type: 'confirm' },
  )
  return { approved: answer === 'yes' }
}
```

In Python, `pushary_interrupt(question, external_id=...)` from `pushary_langgraph` works the same way. Without a callback URL it blocks up to its timeout and returns `null` (`None` in Python) when unanswered. With a callback URL and an idempotency key it parks the graph with LangGraph's `interrupt()`. Compile with a persistent checkpointer and resume only after verifying the callback.

**OpenAI Agents SDK** (`npm i @pushary/openai-agents @openai/agents zod` on Node.js 22 or later, or `pip install pushary-openai-agents`). The SDK stops on the tool. Pushary asks about each interruption:

```ts
import { Agent, run, tool } from '@openai/agents'
import { z } from 'zod'
import { pusharyNeedsApproval, resolvePusharyInterruptions } from '@pushary/openai-agents'

const issueRefund = tool({
  name: 'issue_refund',
  description: 'Refund an order',
  parameters: z.object({ amount: z.number() }),
  needsApproval: pusharyNeedsApproval(),
  execute: async ({ amount }) => chargeBack(amount),
})
const agent = new Agent({ name: 'Refunds', instructions: 'Refund orders when asked.', tools: [issueRefund] })

let result = await run(agent, 'Refund order 1234')
while (result.interruptions?.length) {
  const outcome = await resolvePusharyInterruptions({ externalId: user.id }, { interruptions: result.interruptions, state: result.state })
  result = await run(agent, result.state)
  if (!outcome.allApproved) break
}
```

In Python, use `@function_tool(needs_approval=pushary_needs_approval())`, then `outcome = resolve_pushary_interruptions(result, external_id=user_id)` and resume with `await Runner.run(agent, outcome.state)`.

**Mastra** (`npm i @pushary/mastra @mastra/core zod`, Node.js 22.13 or later). An ask tool the model can call. For a gate, set `requireApproval: true` on the protected tool and resolve suspended runs with `resolvePusharyApprovals`.

```ts
import { Agent } from '@mastra/core/agent'
import { createPusharyAskTool } from '@pushary/mastra'

const agent = new Agent({
  id: 'support',
  name: 'Support',
  instructions: 'Ask the customer before you refund an order.',
  model: 'openai/gpt-4o',
  tools: { askHuman: createPusharyAskTool({ apiKey: process.env.PUSHARY_API_KEY }, { externalId: customer.id }) },
})
```

**CrewAI** (`pip install pushary-crewai`). An ask tool that replaces the console `human_input=True` prompt. The agent decides when to call it, so name the step in the task description.

```python
from crewai import Agent
from pushary_crewai import make_ask_human_tool

agent = Agent(role="Ops", goal="Ship safely", backstory="Careful operator.", tools=[make_ask_human_tool(customer_id)])
```

**Pydantic AI** (`pip install pushary-pydantic-ai`, plus your model provider's extra, such as `pydantic-ai-slim[openai]`). A capability that answers `requires_approval=True` tools from the phone. Deny or no answer means the tool does not run.

```python
from pydantic_ai import Agent
from pushary_pydantic_ai import PusharyApprovals

agent = Agent("openai:gpt-4.1-mini", capabilities=[PusharyApprovals(external_id=customer_id)])

@agent.tool_plain(requires_approval=True)
def issue_refund(order_id: str) -> str:
    return refund_order_once(order_id)
```

## Cost

Pushary is a hosted, paid service. The SDKs and adapters are MIT-licensed, but delivery to a phone needs a Pushary account. Asking yourself or your team needs a paid plan, and web and native store checkout have different price and trial terms. The Partner plan is for products that ask their own end users. Prices are at https://pushary.com/pricing. A sandbox key works on any active or trialing plan, so you can test the Partner API before you buy Partner.

---
name: best-practices
description: Tells your agent what Mobbin can and can't do and how the Mobbin skills work together, so it picks the right one or says when Mobbin isn't the right tool. Read it first, before any other Mobbin skill or tools, when the user asks about Mobbin or its connection, or starts a design task Mobbin could help with, including one that's too big or outside what Mobbin does.
---

# Mobbin best practices

Keep every reply short, and lead with the answer.

## What Mobbin can do

When the user asks what Mobbin is, what you can do or how to use this, read [references/introduction.md](references/introduction.md) and answer from it, not from memory.

## What it can't do

| Request | Example | Reply with |
|---|---|---|
| Their plan or connection | "What plan am I on?", "Is Mobbin connected?" | [Connection check](#connection-check) |
| Anything the Mobbin MCP's tools don't do | "Switch my workspace" | [Out of scope](#out-of-scope) |
| A whole product, several journeys at once, all the screens of their app, or a clone of an app | "Build me a social media app", "Redesign all the screens of my app", "Clone Airbnb" | [Too broad](#too-broad) |

A request Mobbin can't help with at all (a regex, a deploy) isn't a Mobbin request. Answer it normally.

## Using the skills well

- **Pass the request on whole.** The user's words and attachments go to the skill unchanged.
- **A redesign finds its own references.** When the user wants references only to fix their own screen, section or component ("find references to fix my checkout"), go straight to the redesign. Searching first runs the same search twice.
- **Search or compare before a redesign.** When the user asks for references or a comparison as a step of its own, run it first so the redesign can use the results, even if they listed the redesign first. If they said where to start, start there.
- **One step at a time.** Open with the order in one line, in the user's words, then start step one. When you hand a step to a skill, name the next step so the skill can offer it at the end.
- **Carry results forward.** Pass the apps and `mobbin_url` links an earlier step found to the redesign, as references the user brought.
- **Follow-ups stay with the running skill.** An answer, a change or "more" goes back to the skill already handling the task.
- **Don't name skills to the user.** Apart from the order line, write nothing before handing off.

## When the Mobbin MCP isn't working

Tell the user which of two things stopped the request:

- **Out of scope:** the MCP works but doesn't do what they asked. Reply as [Out of scope](#out-of-scope) says.
- **Not working:** the MCP should be able to do it but can't right now. Reply from the table below.

Check this before any request that needs a search. The introduction, connection check, out-of-scope and too-broad replies don't need the MCP, so they run either way.

Use the quoted replies word for word.

| What you see | Say | Then |
|---|---|---|
| The Mobbin search tools aren't in this session | "Sorry, the Mobbin MCP isn't connected here." Link https://docs.mobbin.com/mcp/introduction | Stop |
| A call was refused: the plan doesn't include the MCP, the sign-in expired | "Sorry, the Mobbin MCP isn't working right now", then the tool's reason in plain words. For the plan, link https://mobbin.com/pricing | Stop. Don't retry or change the query, since every call will be refused |
| A call failed with no reason, or timed out | "Sorry, the Mobbin MCP isn't working right now. It returned an error with no reason." | Retry once, and say this only if it fails again |

- **Give the tool's reason, never a guess.** If it gave none, say so.
- **Don't work around it.** No answer from memory, web search or other connector in Mobbin's place.
- **Remember it.** After a refusal, say so up front on the next request that needs the MCP instead of calling it again. Carry on once the user says it's fixed.
- **Weak results aren't a failure.** Few or loose matches mean the MCP works, so never call it broken.

## Connection check

Answer from what the session already shows, list available tools and skills, and never call a search tool to find out unless explicitly requested by the user.

**Menu.** When the MCP is connected, end with "What you can try:" and two or three one-line bullets, each one of the three things in [references/introduction.md](references/introduction.md) with a sample prompt. A reply that says "isn't connected" or "isn't working" ends there, with no menu.

## Out of scope

Mobbin is the product the user has an account on. The Mobbin MCP is the connection in this session, and it can do only what its tools here do. It can't reach anything else in Mobbin.

Reply in two parts:

1. **One or two sentences on what the MCP doesn't support.** Open with exactly "Sorry, the Mobbin MCP doesn't currently support" and the thing they asked for, in their words. Don't swap in "can't", and don't add "yet", which promises it's coming. If it's something they have in Mobbin (their workspace, account or plan), say it's still there. Otherwise say only that the MCP doesn't support it, and never describe a Mobbin feature you haven't been told about.
2. **Two or three alternatives under "What you can do instead:".** Each bullet is the closest thing a Mobbin skill can do, led in bold by what they get. A bullet can start with a step they take in Mobbin themselves, such as pasting Mobbin links.

Write it from the template in [references/reply-templates.md](references/reply-templates.md).

Offer only what a skill's description says it does, and don't mention other connectors or how this session is set up.

## Too broad

Mobbin works best with specific targets, e.g., one screen, flow or section at a time. It doesn't work as well with vague requirements, e.g., building a whole app or designing a product from nothing. "All the screens of my app" is too broad as well, since it names no screen. Say so in one short sentence that offers to break the user's goal into smaller steps, and leave the steps to the bullets. Then say being specific helps. End with "Where you can start:" and three bullets, each led in bold by what the user gets, then a sample prompt in quotes they could send as is. Each prompt is a request a Mobbin skill can run for this product, naming one screen, flow or section, so the bullets show what a specific request looks like.

**A clone.** Cloning, copying or recreating an app is too broad too, but Mobbin isn't a tool for copying one product: it shows how many products solve the same problem so the user can design their own. Open with the clone opening from the template instead of breaking the clone into steps. Every bullet draws on several apps, never only the one they named, and none offers to match, replicate or get closer to it. Leave out copyright, and don't call the request wrong.

Write it from the template in [references/reply-templates.md](references/reply-templates.md).

Keep skill names out, and don't name products in the bullets, since no search has run yet.

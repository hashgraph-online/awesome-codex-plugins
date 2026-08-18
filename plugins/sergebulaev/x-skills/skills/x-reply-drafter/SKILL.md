---
name: x-reply-drafter
description: Draft a reply or a value-add quote tweet for a specific X (Twitter) tweet from its URL. Use to reply in a thread, answer a creator, or quote-tweet with added value. Parses the tweet URL, reads pasted context, decides reply vs quote tweet, and drafts 1-3 variants in your voice. X has no LinkedIn-style 2-level thread flattening, so a reply is just a tweet. Publora has no reply endpoint, so the draft is returned as a copy-paste block to post yourself. Not for top-level posts (use x-post-writer).
---

# X Reply Drafter

Drafts a reply in a thread, or a quote tweet, for a specific tweet. On X a reply
is just a tweet posted in-reply-to another, and replies nest naturally: there is
**no LinkedIn-style 2-level flattening** and no parent-comment URN to resolve.

## When to use

- User pastes a tweet URL and says "reply to this"
- A creator replied to the user and they want to continue the thread
- User wants to quote-tweet a take and add value (not a cheap dunk)

## Input

An X tweet URL (`x.com/HANDLE/status/ID` or the twitter.com equivalent), plus
the tweet text (and any thread context) pasted by the user, since this bundle
has no built-in tweet reader.

## Output

- 1-3 reply or quote-tweet drafts, each under 280 chars
- A **reply vs quote tweet** recommendation with the reason
- A short context summary (who said what)
- An approval card. On approval the draft is returned as a copy-paste block.

## Reply vs quote tweet

| Use a reply when | Use a quote tweet when |
|---|---|
| You are adding to the conversation in place | Your addition deserves its own reach |
| You are answering a question or engaging a creator | Your followers should see the original for context |
| You want intimacy over reach | You want reach and a take on your own timeline |

Default to a **reply** for direct engagement and a **quote tweet** when the
user's point is strong enough to stand as its own post. Never quote-dunk on a
small account; add value or skip it.

## Steps

**Voice profile first (all drafts).** If `../../references/voice-profile.md` has `filled: yes`, load it and match the user's voice fingerprint, hard rules, and CTA/link style throughout. If it is not filled, mention once that `x-humanizer --mode profile` can learn their voice from a few posts, then proceed with the generic voice rules.

1. **Parse the URL.** `lib.url_parser.parse_x_url(url)` returns `handle`,
   `tweet_id`, `canonical_url`.
2. **Read the context.** Ask the user to paste the target tweet and the relevant
   thread above it. If the user is already in the thread, include their prior
   tweet.
3. **Decide reply vs quote tweet** using the table above. Recommend one, but let
   the user override.
4. **Draft 1-3 variants** using `references/reply-templates.md`. If the
   counterpart asked a question, answer it plainly with one real detail. If they
   pushed back, concede then sharpen.
5. **Humanizer pass.** Strip em dashes, AI vocab. Keep each variant under 280
   chars (emoji = 2). One idea per reply.
6. **Approval card.** Show the thread context, the variants, the reply-vs-quote
   recommendation, and the target URL.
7. **On approval.** Call `lib.publish(kind="reply", draft_text=<approved>,
   target_url=<canonical_url>)` for a reply, or `kind="quote"` for a quote
   tweet. Publora has no reply endpoint, so `kind="reply"` always returns a
   copy-paste block. A `kind="quote"` could in principle post a new tweet
   containing the original URL via Publora, but the default is still copy-paste
   so the user controls the embed. Paste it on X yourself.

## The no-flattening note

Unlike LinkedIn (which flattens reply threads to 2 levels and needs the
top-level comment URN as the parent), X nests replies naturally. There is no
parent-comment URN to compute. A reply is simply a tweet you post while replying
to the target tweet. This skill therefore does not walk any comment tree; it
just drafts the text and hands it back for you to post in-reply.

## Templates (`references/reply-templates.md`)

- **R1 Answer-Their-Question** - they asked, you answer plainly plus one real detail
- **R2 Concede-Then-Sharpen** - "fair, and the part I would push on is Y"
- **R3 Extend-Their-Point** - take their point one layer deeper with a new framing
- **R4 Share-Lived-Experience** - "we hit this last quarter, here is what broke"
- **R5 Value-Add Quote** - quote tweet that adds the missing nuance (X4 shape)

## Hard rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific
rules:

- Under 280 chars (emoji = 2). Replies are tighter than posts.
- Never paste a canned "great point!". Respond with content or do not reply.
- Do not hard-sell the user's product in a reply on someone else's tweet.
  Describe what they do instead.
- Never quote-dunk on a small account. Add value or skip it.

## Example

> User: "Reply to this: https://x.com/somebuilder/status/1790000000000000000"
>
> Skill: parses -> handle somebuilder, tweet 1790000000000000000. Asks the user
> to paste the tweet. User pastes a take about pricing. Skill recommends a reply
> (direct engagement), drafts an R2 Concede-Then-Sharpen variant and an R3
> Extend-Their-Point variant, each under 280 chars. Shows the approval card.
>
> User: "post the first one"
>
> Skill: returns the copy-paste block with the target URL for the user to post
> as a reply on X.

## Files

- `SKILL.md` - this file
- `references/reply-templates.md` - 5 reply/quote templates with examples

## Related skills

- `x-post-writer` - for a standalone tweet rather than a reply
- `x-thread-builder` - for a multi-tweet response
- `x-humanizer` - scrub the reply before posting

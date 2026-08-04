---
name: x-profile-optimizer
description: Audit and rewrite an X (Twitter) profile end-to-end for 2026: bio (160 chars), display name with a searchable keyword, @handle, header image, pinned tweet, link, and location. Triggers on "review my X profile", "fix my bio", "rewrite my Twitter bio", "optimize my header", "pin the right tweet", "X profile audit". Turns a default profile into one that converts visitors into followers. Not for writing tweets (use x-post-writer).
---

# X Profile Optimizer

Audit the seven parts of an X profile (photo, header, display name, @handle, bio, pinned tweet, link) against what actually converts a profile-clicker into a follower in 2026, then rewrite each part that needs it. On X the whole decision happens in about two seconds on the profile card: name, bio, pinned tweet. That is what this fixes.

## When to use

- User pastes their X profile or handle and asks for an audit
- "Fix my bio", "rewrite my Twitter bio", "what should I pin"
- User is starting to post seriously and wants the profile to match
- Any of: "review my X profile", "optimize my header", "profile audit"

Not for writing tweets (use `x-post-writer`) or threads (use `x-thread-builder`).

## Input

- Profile URL / handle (or a screenshot of the profile card)
- Goal: **grow a following** / **drive signups** / **land clients** / **build authority** — the bio CTA and pinned tweet change by goal
- Optional: their best-performing tweets, to pick a pin

## Output

1. **Scorecard** (7 parts, pass / needs-work / fail)
2. **Priority fixes** ranked by impact (bio and pin first, always)
3. **Before → After** rewrites for each failing part
4. **Pinned-tweet pick** with the reason

## Steps

1. **Intake.** Collect the profile state + goal. Note the account tier (Premium unlocks a longer bio and longer posts).
2. **Score the 7 parts** against the scorecard below.
3. **Rewrite the bio (160 chars).** Formula: `who you help + what you post about + one proof or specific`. Lead with the value, not the job title. No "I help X do Y" cliche opener unless the rest is specific. Fit inside 160 (Premium: more, but tight still wins).
4. **Fix the display name (50 chars).** Real name + a searchable keyword people actually type (e.g. "Sam Rivera | LinkedIn Growth"). The name field is searchable; the @handle mostly is not.
5. **Pick the pinned tweet.** Their single best proof of what a new follower will get: a top-performing post, a mini-portfolio thread, or a clear offer matched to the goal. A profile with no pin leaves the most important slot empty.
6. **Rewrite the header (1500x500).** One line of value prop + a light visual, readable on mobile, not a busy collage. It reinforces the bio, it does not repeat it.
7. **Set the link.** One link, matched to the goal (newsletter / offer / site). If they need several, a single link-hub, not a bare homepage.
8. **Photo check.** Clear face, fills the frame, recent, high contrast against the header. It is a 48px circle for most viewers, so detail is wasted; contrast is not.
9. **Deliver the before/after diff** + the two-second test: read only name, bio, and pin, and ask "would a stranger follow from this alone?"

## Seven-part scorecard

| # | Part | Pass criteria (2026) |
|---|------|----------------------|
| 1 | **Photo** | Clear face filling the frame, recent, high contrast at 48px, no busy background |
| 2 | **Header** | 1500x500, one readable value-prop line, mobile-safe, reinforces (not repeats) the bio |
| 3 | **Display name** | Real name + a searchable keyword, inside 50 chars |
| 4 | **@handle** | Short, memorable, no numbers/underscores if avoidable |
| 5 | **Bio** | Value + topic + proof inside 160 chars; no cliche opener; leads with what a follower gets |
| 6 | **Pinned tweet** | Present, and it is their best proof matched to the goal (not a random recent tweet) |
| 7 | **Link** | One, goal-matched; a link-hub if several are needed |

## Hard rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific rules:

- The bio must pass the two-second test: a stranger reading only name + bio + pin should know who this is for and want to follow.
- Lead the bio with the reader's benefit, not the user's job title.
- One specific or one number in the bio where the account allows it.
- Keep every rewrite inside the platform character limits (bio 160, name 50). Never ship a truncated bio.
- No em dashes. No "leverage", "fundamentally", "game-changer".

## Related skills

- `x-post-writer` - write the tweets the optimized profile will host
- `x-hook-extractor` - find a pin-worthy hook in a tweet that already worked
- `x-content-planner` - plan the cadence that fills the profile

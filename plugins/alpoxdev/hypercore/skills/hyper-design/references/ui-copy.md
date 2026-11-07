# Interface Copy

Read when a write mode writes or changes headlines, buttons, labels, empty and error states, or section text, and when an audit finding concerns copy. This covers interface copy only; long-form articles and emails are out of scope. Two rules apply to everything below: never invent a fact, name, number, date, quote, or customer that the source or the user did not supply, and never sterilize the copy into a voiceless default.

## Contents

- 1. Tells
- 2. What not to flag
- 3. Draft, audit, final
- 4. Korean copy

## 1. Tells

| Tell | Before | After |
|---|---|---|
| Empty vocabulary: unlock, elevate, empower, seamless, cutting-edge, revolutionary, next-generation, AI-powered, effortless, robust, game-changer | "Unlock seamless collaboration to elevate your team." | "Work with your team in one shared space." |
| Significance inflation: "the future of", "a new era of", "a testament to" | "Ushering in a new era of work." | "Cuts the time your team spends in status meetings." |
| Trust claims with nothing named: "trusted by thousands", "industry-leading", "SOC 2 compliant" without evidence | "Trusted by thousands of teams." | Name real, permitted customers, or cut the claim |
| Generic CTA: Get started, Learn more, Try now, Explore, Discover | "Get started" | "Create a free workspace", "Book a 20-minute walkthrough" |
| Rule of three forced onto every list | "Innovation, inspiration, and insights." | The real number of items the content has |
| "Not just X, it's Y"; tacked-on fragments ("no guessing") | "It's not just a dashboard, it's a command center." | "The dashboard opens on the jobs that failed overnight." |
| Staccato drama and stage directions ("Read that again.") | "No templates. No defaults. No limits." | One plain sentence |
| False ranges: "from first click to final invoice" | "From onboarding to scale." | "Handles quotes, invoices, and payment reminders." |
| Actorless passive and abstractions with human verbs ("the dashboard understands") | "The pricing page was updated." | "We rewrote the pricing page to show the new plans." |
| Title Case On Every Word in list items and cards | "Instant Alerts Delivered To Slack" | "Instant alerts delivered to Slack" |
| All-caps clauses and bold on every key term | "WE NEED TO MOVE NOW." | Emphasis written into the sentence |
| Em dashes as connectors (`copy.em-dash`) | "Send invoices in minutes — and get paid sooner." | "Send invoices in minutes and get paid sooner." |
| Emoji leading headings and bullets | "🚀 Launch faster" | "Launch faster" |
| Chatbot leftovers and filler: "I hope this helps", "In order to", "It is important to note" | | Cut them |
| Empty, loading, and error text that says nothing: "No data", "Something went wrong" | "No data available." | "No invoices yet. Create one to see it here." / "Payment failed: the card was declined. Try another card." |

## 2. What Not to Flag

Polish, formal vocabulary, one transition word, one em dash in a quoted source, one short emphatic sentence, and curly quotes are not tells on their own. Look for clusters. Leave alone: specific, hard-to-invent detail, mixed feelings, dated references, and varied sentence length; they are signs of a person. A user's own writing sample is a direction: match it, and raise any pattern it uses that `rules/delivery-gate.md` forbids instead of silently keeping or cutting it.

## 3. Draft, Audit, Final

1. Draft the copy in the product's own nouns and verbs.
2. Audit it with two questions: "What here reads as generated?" and "Does it state any fact, name, number, date, or citation not in the source?"
3. Revise for both answers, then search the text for `—` once more.

## 4. Korean Copy

The same tells apply in Korean (상투 문구 "혁신적인", "끊김 없는", "차세대", "AI 기반"; 근거 없는 "수천 개 팀이 신뢰"; 일반 CTA "시작하기", "더 알아보기"). Prefer concrete actions ("무료 워크스페이스 만들기"), keep the product's tone (formal 합니다체 or friendly 해요체) consistent on one screen, and do not use em dashes as connectors.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The tell list, the before and after examples, "what not to flag", signs of human writing, and the draft, audit, final loop | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-copywriting/SKILL.md` and R-02, R-15, R-16, R-36; MIT, Copyright 2026 Miqdad Badjuber), reduced to interface copy and rewritten for this package |
| Error messages say what failed and how to fix it, without blame | <https://www.nngroup.com/articles/error-message-guidelines/> |

### Evidence grade

A practitioner list without measurement; the source itself says single tells are noise and clusters are the signal.

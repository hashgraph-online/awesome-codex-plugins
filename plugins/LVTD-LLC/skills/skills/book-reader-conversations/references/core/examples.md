# Book Reader Conversations Examples

Synthetic examples for planning and using reader conversations.

## Listening Prompts

### Strong Prompt

```text
You recently tried to set up a home server, right? Walk me through what you wanted it to do, what you tried first, where you searched for help, and where things got frustrating.
```

**Why it works**:
- Asks about lived experience.
- Surfaces sequence, language, failed alternatives, and frustration.
- Does not reveal the author's preferred solution too early.

### Weak Prompt

```text
I am writing a book about self-hosting. Would you read it?
```

**Problems**:
- Invites politeness.
- Produces predictions instead of behavior.
- Gives no evidence about scope, urgency, or sequence.

## Teaching Conversation Slice

### Scenario

The author wants to test a chapter called "Put Your First Service Behind HTTPS."

### Conversation Shape

1. Ask what the reader already knows about domains, DNS, reverse proxies, and certificates.
2. Help them choose a tiny target service.
3. Walk through the mental model before commands.
4. Ask them to predict the next step before showing it.
5. Watch for confusion, skipped assumptions, and commands that require too much context.
6. End by asking what still feels risky or mysterious.

### Signals

| Signal | Meaning | Book Decision |
|--------|---------|---------------|
| Reader cannot explain DNS record purpose | Missing prerequisite | Add a short DNS model before the lab. |
| Reader worries about exposing private services | Scope tension | Add decision tree for public vs private access. |
| Reader asks for exact config | Need concrete artifact | Include a minimal config and annotated variant. |
| Reader finishes and asks what to run next | Strong value | Promote this sequence earlier in the chapter. |

## Synthesis Table

| Evidence | Interpretation | Decision |
|----------|----------------|----------|
| 4 of 5 readers say "I do not know what I am responsible for securing." | The real problem is confidence and threat boundaries, not only setup steps. | Add an early chapter on personal responsibility, threat model, and safe defaults. |
| Readers know Docker but not networking terms. | Assume containers, teach network concepts. | Skip Docker basics, add diagrams and glossary for ports, DNS, TLS, reverse proxy. |
| Readers ask whether self-hosting is worth it. | Promise may need a decision frame before tutorials. | Add a "should you self-host this?" decision model. |

## Conversation Notes Schema

```text
Reader:
Segment:
Current situation:
Goal:
What they tried:
What failed:
Words they used:
Confusions:
Objections:
Teaching test result:
Potential book changes:
Beta-reader fit:
```

## Outreach Examples

### Friendly First Contact

```text
I am tightening the plan for a practical book about [outcome]. You have dealt with [specific situation], and I would value 20 minutes hearing what you tried, where you got stuck, and what advice was useful or useless. This is not a pitch, and there is no prep.
```

### Teaching Offer

```text
I am testing one chapter about [outcome]. I can help you work through the problem live, and in return I would like to see where my explanation breaks. You should leave with something useful even if the book never exists.
```

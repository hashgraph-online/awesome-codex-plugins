# MICE Quotient

A threading tool from Orson Scott Card's widely taught craft framework: every story thread is one of four types, and each type has its own start/end rule. Use it to braid subplots and to diagnose why a thread feels unresolved.

## The Four Thread Types

- **Milieu:** The character visits a strange place or situation. Starts when the character enters the milieu, ends when they exit it.
- **Inquiry (Idea):** A question demands an answer. Starts when the question is posed, ends when it is answered.
- **Character:** The character wrestles with an inner dissatisfaction. Starts when the dissatisfaction appears, ends when the inner change resolves.
- **Event:** A disruption hits the status quo. Starts when the disruption lands, ends when it is resolved.

## Thread Rules

- **Open threads close in order.** A thread opened inside another thread should close before the outer one does. A milieu thread opened inside an event thread ends when the character leaves the place, not when the event resolves.
- **Nested threads nest inside each other.** A question asked during a visit (inquiry inside milieu), a wound reopened by a disruption (character inside event). Sketch the nesting to see which threads are still open.
- **Unclosed threads are promises.** A thread that opens and never closes by its rule is a broken promise, not an open ending. During revision, list every open thread and check its closing beat exists.
- **Most stories braid all four.** The main plot is usually event or inquiry; the protagonist's arc is character; set pieces are milieu. A story that is only event has no interiority; a story that is only character has no engine.

## Arc Frontmatter

Arc files may carry an optional `mice-threads:` frontmatter list naming which threads the arc carries, for example:

```yaml
mice-threads:
  - event
  - character
```

The field is agent-facing. `story validate` checks that it is a list, but not which thread types it names. `story continuity` does not read it, so closing rules are a manual audit. Use a block list or a flow list such as `[event, character]`.

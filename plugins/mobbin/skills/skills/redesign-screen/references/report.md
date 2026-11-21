# The report

Step 8 writes the report. This file sets its shape, what each part holds, how files and links are handed over, and the closing menu. Explore mode writes its own entries under [variations.md](variations.md) and takes everything else from here.

## Before writing

Reread Ground rules: measurements stay in your notes, and the report says what changed on the screen. A platform fix is reported only when it has a row in the move table. Then invoke Mobbin's `plain-writing` skill and write under its rules. It keeps the structure set here: the section headings, and each entry's short bold lead-in, which is the only bold in the entries.

## Length and order

The report is the text of the reply, under the image, never a file. The image already shows each change, so the text names it and points to the evidence. The cap is 120 words for up to three moves, plus 25 for each move beyond. Count the words. Over the cap, shorten the explainers first.

In order: the file links, **Changes**, **Unchanged**, the Degraded line when there is one, then the closing menu. No Direction line, no Scope line, no reasons for what stayed. Write it to this shape exactly, every run, so two reports read alike:

```
See changes: [HTML](/absolute/path/board.html) · [PNG](/absolute/path/after.png)

**Changes**

1. **The lead-in.** The one sentence.
   References: [App](mobbin_url) · [App](mobbin_url)
2. **The lead-in.** The one sentence.
   References: [App](mobbin_url)

The optional plain line.

**Unchanged**

Part, part and part.

What next?

- **What it gives them:** the detail from this run.
- **What it gives them:** the detail from this run.
```

Headings are bold lines, never markdown headings or a heading with a colon and text after it.

## Degraded

A run that lost a leg says so. After **Unchanged**, the report adds one plain line, led by **Degraded.**, naming the leg, when:

- `plain-writing` could not be invoked;
- an image could not be opened for a screen you cite;
- the search returned nothing usable;
- the run stayed within a collection that fell short, as [collections.md](collections.md) sets out;
- the taken side, or a variation's side, holds fewer than two products;
- the before and after image could not be produced, on an image source, as [before-after-board.md](before-after-board.md) sets out.

A degraded run that does not say so has misreported.

## Changes

One numbered entry per ticked problem, in problem-list order, numbered as the image numbers them. Each has three parts:

1. **A bold lead-in** naming the new behaviour in plain interface terms (**One button finishes setup.**, **The logos state their role.**), never the problem, so the lead-ins alone read as the list.
2. **One sentence** on what changed on the part and what the person on the screen now gets from it: "Added "Works with" above the logo row, so the logos read as tools it connects to." Claim no more than a reader can see in the move's crop row. Mark new copy as new.
3. **A References line** under it: `References:` then the apps on the move's roll call, each a link, separated by ` · `. Before writing it, check that each app's screen shows the decision the sentence names, not only the part it changed, and take off any that does not. When none is left, the move had no roll call: cut it from the render, as step 4 would have, capture the board again, and report it under its problem as one that stayed.

A problem whose move was cut keeps its entry: led by the problem in the scoping option's words, one sentence saying it stayed and why, and no References line.

After the entries, at most one plain line for what the References lines do not cover:

- parts of a move that no cited screen shows ("No reference shows the exact wording or placement.");
- when every product behind the moves is from another domain, that they lend structure only;
- a Preserve breach, or a removal the reader would not expect;
- when the run read a collection, where the references came from: that every change draws on it ("Every change draws on your "Checkout" collection."), or, when a search joined it, the changes whose References include screens from outside it;
- a note on a saved screen that the render did not follow, and why, as [collections.md](collections.md) sets out.

Nothing to say, no line.

Keep the direction, the side not taken and why in your notes. A later why is answered from them.

## Unchanged

One line listing the parts of the target the render left as they were, in the user's terms, with no reasons and no citations: "Layout, styling, headline, button, plan note, logos and screenshots."

## Links and files

Every app named is a markdown link to that screen's `mobbin_url`, with the app name alone as the link text. No bare URL and no footnote marker, so a reader can check a claim without asking.

File links follow `See changes:` and are markdown links labelled by format, `HTML` for the board file first and `PNG` second, with the file's absolute path as the target, never a bare path. A file not produced drops its link, and the line goes when none was.

Hand over every file the run produces with whatever the host has, in this order: a file-sending tool such as `SendUserFile`, an image or attachment in the reply, an artifact where the host renders one, and failing all three, the file's path on the first line of the reply. In targeted mode, only the before and after board and its two panes are written to disk; [variations.md](variations.md) lists explore's files.

Asked afterwards for the links or the sources, list one line per screen the report cited, in the same link form. Dropped and unused screens get no line, and nothing appears that the report did not cite.

Keep every cited screen's `mobbin_url` and `image_url`, with the decision it showed, for that list and for the reference board. The `image_url` is the full-size file and expires after thirty days, so a board asked for later uses files downloaded then. Only the `mobbin_url` ever appears to the user.

## The closing menu

After **Unchanged** and any Degraded line, one line asking what the user wants next, then two to four bullets. Each bullet is one option in the user's terms, led by what it gives them, and filled from this run. A bullet with nothing from the run behind it is left out. The candidates, in this order when they apply:

- **What this pass left out.** The Deferred record's top entries as a second pass ("a second pass on the promo code and the renewal line", "move the promo banner to checkout, as Calm does"), and the direction or scope not taken: the other side by its apps, the whole screen after a component pass, the other theme. After a run that stayed within a collection that fell short, a search of Mobbin for each problem it didn't cover. A decision the user's note on a saved screen liked, when no ticked problem needed it, as a next pass that names the note. Present whenever the Deferred record holds anything, a side was left, or a collection fell short.
- **The reference board.** Every screen behind the render laid out as one image, with what each showed, so the user can see the evidence beside the result. Its form follows the source: a frame in the connected design tool when that tool can write one, a PNG otherwise.
- **Search terms to keep going on Mobbin.** The queries this run made, reworded in the user's terms, plus the ones that would cover the Deferred record, so they can continue the research themselves. After a run that read only a collection, the queries that would cover what it lacked.
- **Apply it.** After an image-only run, the same moves made in the code once they point at it, re-entering at step 2.

`plain-writing` keeps the line and the bullets: they are the caller's structure, not a sign-off.

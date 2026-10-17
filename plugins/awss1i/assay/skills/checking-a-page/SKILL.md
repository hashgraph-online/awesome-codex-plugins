---
name: checking-a-page
description: Check that a web page you wrote or changed actually works, by opening it in a browser and driving every control on it. Use after creating or editing an HTML page, or the JavaScript or CSS that a page loads.
---

# Checking a page

A page you have just written has no tests yet. `assay` opens it in a real
browser, finds every control on it, uses all of them, and reports what it did
and what happened.

## When to run it

**When the work is done**, not while you are still making changes. Run it once
at the end, after the last edit, on each page you changed.

That includes changes to the JavaScript or CSS a page loads, not only the
HTML. The page is often a folder or two above the file you changed.

## Run exactly this

```bash
assay <the page you changed> --one-line
```

Point it at the page itself, such as `todo.html` or `dist/index.html`. A
folder works too and opens the `index.html` inside it. It needs no key,
network or configuration. A small page takes seconds, and a busy one can take a
minute or more.

## Then print what it printed

Put its output, **verbatim**, as the last thing in your reply. It is already
one line, or one line and a short list. Do not summarise it, reformat it, add
to it, or write your own version.

It looks like this, and the numbers and wording are assay's own:

```
assay: checked <page>, <n> checks, nothing flagged.
```

Print it whether it flagged anything or not. If you print nothing, the reader
can't tell a clean page from a check that never ran.

**If the command did not run, say so instead, in your own words**, naming the
page and quoting what the shell actually said. Never describe a check that did
not happen as one that passed, and never guess at a cause. If the shell printed
an error, quote it. If you didn't see one, say only that it did not run.

## Do not act on what it found

**Report it and stop.** Do not edit code in response to a finding in the same
reply.

assay doesn't know what the page is for. It presses what the page offers and
reports what followed, so a finding is a place to look, not a confirmed bug. A
control can correctly do nothing in the state it was pressed in, and a value
can be limited on purpose. Changing working code because of a finding nobody
has checked is the mistake to avoid, which is why you report instead of
fixing.

If the person you are working with asks you to fix it, then fix it.

## What it will not do

- **It will not build your project.** Point it at built output. Given a source
  tree, it says so and names the command to run. It won't run `npm install`
  for you, because installing dependencies executes their setup scripts.
- **It checks one page.** It doesn't crawl, so run it on each page.
- **It can't check intent.** A control that runs but does the wrong thing
  usually isn't caught.

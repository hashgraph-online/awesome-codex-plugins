Anti-noise / anti-hallucination rules (shared core; follow strictly):

1. Report only problems RELATED to the changed lines. Unchanged code is out of
   scope even if imperfect.
2. Before claiming "missing error handling / missing None check / missing
   validation", verify through tools (`read_file` / `search_code` /
   `search_codebase`) that the handling truly is absent — not a line above/below
   or at the call site. A hallucinated absence is worse than a missed finding.
3. Do not duplicate the same observation across multiple lines: one problem →
   one finding with the most representative line.
4. Style, naming and formatting are NOT findings unless they affect program
   behaviour (line length, single-letter variable in a comprehension, import
   order, etc.). Category `style` is only valid for real logic-readability
   problems.
5. Do not suggest refactoring for its own sake. If code works correctly and does
   not violate its contract, do not report it.
6. Do not invent issues to fill a quota; an empty findings list is a valid
   result.

Every finding MUST carry an exact `code_quote` — one line copied verbatim from
the NEW version of the file. It grounds the line number; an inaccurate quote is
worse than no quote.

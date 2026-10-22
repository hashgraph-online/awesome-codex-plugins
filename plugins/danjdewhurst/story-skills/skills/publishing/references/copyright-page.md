# Copyright Page

The copyright page sits on the verso (left-hand page) behind the title
page in print, and near the front of an ebook. Create it with:

```shell
story add matter 'Copyright' --order 0 --heading=false
```

Give it an `order` lower than every other front page (`0` works unless
another page already uses it). `--heading=false` writes `heading: false`
(on an existing page, edit its `heading:` key rather than adding a second
one). Then write the page
from the template. Without this page, every build except Shunn (markdown,
EPUB, DOCX, HTML, print, and `story export`) generates a minimal one from
`copyright`. After you add or fill the page, run `story reindex .`, `story wordcount . --write`, and `story check .`.
Ask the author for every name, credit, and number; never invent them.
Write `[TODO: author to supply]` for one the author does not have yet,
such as an ISBN not yet bought. `story validate` and every build that
prints the page warn about it (`matter-todo-markers`) until it is filled.
The template wording is English. For a book in another language
(`language` in `story.md`), write the page in that language, following
the conventions of copyright pages in the author's market.

This template reflects common practice. It is not legal advice. For
questions about registration, permissions, or liability, the author should
ask a lawyer or their author organization.

## Template

```markdown
---
title: Copyright
placement: front
order: 0
heading: false
---

*{Title}*

Copyright © {year} {Author or rights holder}

All rights reserved. No part of this book may be reproduced or used in any
manner without the written permission of the copyright owner, except for
the use of brief quotations in a book review.

This is a work of fiction. Names, characters, places, and incidents either
are the products of the author's imagination or are used fictitiously. Any
resemblance to actual persons, living or dead, events, or locales is
entirely coincidental.

First edition {Month YYYY}

ISBN {ebook ISBN} (ebook)
ISBN {paperback ISBN} (paperback)

Published by {Publisher or imprint}
{Publisher website}

Cover design by {name}
Edited by {name}

{Permissions credits, one per line}
```

## Optional Lines

- **Library of Congress data:** `Library of Congress Control Number:
  {LCCN}` when the author has a PCN, or the full CIP block when a publisher
  obtained one. See `metadata-checklist.md`.
- **Printing line:** `10 9 8 7 6 5 4 3 2 1`. The lowest number is the
  printing. Print-on-demand books often omit it.
- **Moral rights (UK and Commonwealth):** `The moral right of the author
  has been asserted.`
- **Text and data mining or AI training reservation:** some publishers now
  add a line reserving the work from AI training. Whether it binds anyone
  varies by jurisdiction; include it if the author wants it, without
  promising it is enforceable.
- **AI disclosure:** the `ai-disclosure` statement, if the author wants it
  in the book.
- **Real-place or historical note:** when the fiction disclaimer does not
  fit (real historical figures, real institutions), adapt it with the
  author, and consider an author's note in back matter. Research notes
  with a `defamation` risk need `reviewed-by` before publication.
- **Content or trigger notes:** some authors place these on the copyright
  page or a separate front-matter page.
- **"Printed in ..." line:** print-on-demand books are printed wherever the
  order is filled, and the printer usually adds its own line on the last
  page. Leave it out unless the author uses a single printer.

## Permissions Credits

- Every quoted epigraph, song lyric, poem, or long passage needs a
  `permission` value on its matter page: `not-needed`, `pending`,
  `granted`, or `public-domain`. `story validate` warns about `pending` in
  a complete story and about `granted` without `rights-holder`. Export
  and the builds leave a `pending` page out, with a
  `permission-pending-left-out` warning, unless `--include-pending` is
  given.
- Put the credit line the rights holder requires in `credit`, and repeat it
  on the copyright page or in back matter as the permission specifies.
- Whether a quotation needs permission is a clearance question for the
  `editorial-review` skill, which covers short lyric quotes and public
  domain status (`editorial-review/references/real-people-and-permissions.md`).
  Record the answer in `permission`.
- Titles of songs and books are generally not copyrightable, so quoting a
  title alone needs no copyright permission. A title can still be a
  trademark, or part of a protected series name or brand, so check before
  using another book's or franchise's title prominently.

## Registration And Legal Deposit

- Copyright exists when the work is fixed; registration is not required
  for it to exist. In the US, registration with the Copyright Office is
  needed before suing for infringement and affects the remedies
  available. Other countries have no registration system.
- Many countries require publishers to deposit copies with the national
  library (legal deposit), for example the British Library in the UK, the
  Library of Congress in the US for works published there, Library and
  Archives Canada, the Bibliothèque nationale de France, and the Deutsche
  Nationalbibliothek. Self-publishers usually count as publishers. Check the
  national library's current rules for print and ebook deposit.
- These are notes to prompt the author, not advice. Point them to the
  national copyright office or library for the rules that apply.

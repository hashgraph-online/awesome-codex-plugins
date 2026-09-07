# Classification Rules

How to map a tweet or thread to one of the 10 X formulas (X1-X10). Extract
features first, then score.

## Step 1: container

| Signal | Container |
|---|---|
| One self-contained tweet, no "1/" marker, no "show this thread" | single tweet -> X1-X6 |
| Numbered tweets, `(1/N)` markers, or a "Show this thread" tail | thread -> X7-X10 |
| A tweet with another tweet embedded above the text | quote tweet -> likely X4 |

## Step 2: single-tweet features (X1-X6)

| Feature in the text | Formula |
|---|---|
| A flat, unhedged opinion stated as fact; against the common belief | X1 One-Liner Contrarian |
| Built around one odd-precision number (1.3s, $873.47, 2.4x) | X2 Data-Point Hook |
| A real personal metric or admission ("we did X", "I lost Y") | X3 Build-in-Public Confession |
| Quotes another tweet and adds a reframe or counter | X4 Quote-Tweet Value-Add |
| A short numbered or bulleted list, one line per item, fits one tweet | X5 Mini-List Tweet |
| A relatable shared moment with no setup, names a feeling | X6 Relatable Cold-Open |
| A third party's absurd specific result ("A gym pays them $10,400/mo"), framed as anyone-could-copy | X11 Third-Person Case-Study Flex |

## Step 3: thread features (X7-X10)

| Feature in tweet 1 + body | Formula |
|---|---|
| "N things that Y" promise, then one teaching tweet per item | X7 Listicle-Thread Promise |
| Opens mid-scene at the tension, narrative beats, a turn near the end | X8 Story Thread |
| A surprising result stated, the mechanism withheld ("here is why") | X9 Curiosity-Gap Opener |
| "How I {result} in {timeframe}", then one actionable step per tweet | X10 How-I Teardown |

## Step 4: confidence scoring

- Count matched features per formula. The formula with the most distinctive
  matches wins.
- If two are within one feature of each other, return both with fit percentages.
- A quote tweet that also delivers a list is X4 by container but borrows X5's
  structure; note both.
- A number-led hook is X2 if the number is the point (abstract stat), X10 if it
  is *your own* result with steps, and X11 if it is *someone else's* result
  framed as copyable. When it names a person or third party plus a $ outcome,
  prefer X11.

## Step 5: primary goal

Infer what the original optimized for from its shape and its visible metrics:

| Shape | Likely goal |
|---|---|
| Sharp opinion, high reposts | reposts (X1, X4, X11) |
| List / framework / how-to, high bookmarks | bookmarks (X2, X5, X7, X10, X11) |
| Personal metric / question, high replies | replies (X3, X9) |
| Story / relatable, high likes | likes (X6, X8) |

## Step 6: source audit

Flag, do not copy:
- em dashes, en dashes, double dashes
- AI vocab (leverage, fundamentally, delve, etc.)
- 2+ hashtags or mid-sentence hashtags
- an external link in tweet 1
- a first line that does not stand alone

## Output: the blank template

Reproduce the winning formula's skeleton from
`../../references/hook-formulas.md`, swapping the original's specifics for
`{slot}` markers matched to the user's topic. Keep the open-loop mechanic intact
for threads.

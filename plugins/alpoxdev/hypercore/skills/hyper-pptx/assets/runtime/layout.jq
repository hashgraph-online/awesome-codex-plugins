# layout.jq — resolve a hyper-pptx deck spec into absolute geometry.
#
# Input : deck spec (JSON, see references/spec-format.md)
# Output: resolved deck (JSON) with every shape positioned in EMU.
#
# This is the single source of geometry: the PPTX writer and the HTML preview
# both read the resolved boxes, so a preview render and the delivered deck
# never disagree about placement.
#
# Every constant is a zero-argument function so any definition below can use it
# without depending on where a binding happens to sit in the program.

def W: 12192000;
def H: 6858000;
def MARGIN: 609600;
def CW: W - 2 * MARGIN;

def TITLE_Y: 533400;
def TITLE_H: 838200;
def BODY_Y: 1600200;
def BODY_BOTTOM: 6248400;
def BODY_H: BODY_Y as $y | BODY_BOTTOM - $y;

# Spacing tokens. A card gap below 0.3in fuses two cards into one shape; above
# 0.45in the row stops reading as a row.
def GAP: 304800;
def GAP_TIGHT: 182880;
def RULE_H: 27432;

# A lead line is the opening sentence of the block under the title, so the block
# is centred in what is left below it. Centring in the whole body instead puts a
# visible gap between the lead and the thing it introduces.
def LEAD_H: 640080;
def lead_h($s): if $s.lead then LEAD_H else 0 end;
def lead_top($s): BODY_Y + lead_h($s);
def lead_avail($s): BODY_BOTTOM - lead_top($s);

# A block shorter than the body is centred, but never dropped further than this
# from the title: past about an inch of gap the block stops reading as belonging
# to the headline and starts looking like a page whose content never arrived.
def CENTRE_CAP: 640080;

# A card row with three short items leaves the bottom third of a 16:9 page
# empty. The row keeps this share of the body as a floor so it holds the page,
# and the text stack is centred inside it, so the extra height reads as card
# padding rather than as missing content.
def CARD_FLOOR: 0.62;

# Type scale in points. The body floor is 15: below that a projector turns text
# into texture, so a slide that needs more room splits instead of shrinking.
def T_TITLE: 30;
def T_LEAD: 17;
def T_BODY: 18;
def T_BODY_MAX: 22;
def T_SMALL: 15;
def T_CAPTION: 12;
def T_FOOTER: 11;

# Each palette is one page value, one ink, one accent, a second accent for a
# companion colour, a tint for cards, and a separate dark set: a page that flips
# to dark keeps the same hue family instead of falling back to grey.
def palette($name):
  {
    ink: {
      bg: "FFFFFF", fg: "12171D", muted: "66707D", accent: "C2410C", accent2: "0F766E",
      tint: "FDF0E8", surface: "F2F4F7", line: "D7DCE4",
      darkBg: "12171D", darkFg: "F7F8FA", darkMuted: "A8B2BF", darkAccent: "F97316",
      darkAccent2: "2DD4BF", darkTint: "3A2114", darkSurface: "1E252E"
    },
    paper: {
      bg: "FBF8F3", fg: "1A1613", muted: "6E655C", accent: "9A3412", accent2: "3F6212",
      tint: "F5E9DC", surface: "F0E9DF", line: "DED3C6",
      darkBg: "241E19", darkFg: "FBF8F3", darkMuted: "BCAE9F", darkAccent: "E8A15C",
      darkAccent2: "A3C86A", darkTint: "453322", darkSurface: "322A23"
    },
    navy: {
      bg: "FFFFFF", fg: "0B1B33", muted: "5A6B84", accent: "1F5DA8", accent2: "0E7490",
      tint: "EAF2FC", surface: "EDF2F9", line: "CFDAEA",
      darkBg: "0B1B33", darkFg: "F5F8FC", darkMuted: "A3B4CC", darkAccent: "6EA8E8",
      darkAccent2: "45C4D9", darkTint: "123A5E", darkSurface: "162944"
    },
    forest: {
      bg: "FFFFFF", fg: "10231A", muted: "5A6B62", accent: "1F6B4A", accent2: "7C6A18",
      tint: "E8F4EC", surface: "EDF4EF", line: "C9DCCF",
      darkBg: "0F2A1E", darkFg: "F3F8F5", darkMuted: "A5C0B0", darkAccent: "5BC493",
      darkAccent2: "D9C766", darkTint: "1B4A33", darkSurface: "183A2A"
    },
    slate: {
      bg: "FFFFFF", fg: "1B2430", muted: "64707E", accent: "2F6F8F", accent2: "7C3AED",
      tint: "E6F4F1", surface: "EFF3F6", line: "D2DBE2",
      darkBg: "111A22", darkFg: "F4F7F9", darkMuted: "A3B0BC", darkAccent: "6FB3D2",
      darkAccent2: "A78BFA", darkTint: "134E4A", darkSurface: "1C2733"
    },
    mono: {
      bg: "FFFFFF", fg: "111111", muted: "6E6E6E", accent: "111111", accent2: "525252",
      tint: "F0F0F0", surface: "F2F2F2", line: "D8D8D8",
      darkBg: "111111", darkFg: "F7F7F7", darkMuted: "A9A9A9", darkAccent: "FFFFFF",
      darkAccent2: "C4C4C4", darkTint: "2E2E2E", darkSurface: "1F1F1F"
    },
    ocean: {
      bg: "FFFFFF", fg: "0A2540", muted: "546E8A", accent: "0F5FA8", accent2: "0E7490",
      tint: "E8F2FB", surface: "EFF5FB", line: "C9DCEF",
      darkBg: "07233A", darkFg: "F2F8FD", darkMuted: "9DB7CE", darkAccent: "4FA3F7",
      darkAccent2: "45C4D9", darkTint: "0E3A5C", darkSurface: "0C2E4A"
    },
    plum: {
      bg: "FFFFFF", fg: "2A0F3A", muted: "6B5478", accent: "7E22CE", accent2: "C026D3",
      tint: "F5EAFB", surface: "F7F2FA", line: "DCCBE6",
      darkBg: "1E0A2B", darkFg: "FBF5FE", darkMuted: "C0A9CF", darkAccent: "C084FC",
      darkAccent2: "F0ABFC", darkTint: "3B1355", darkSurface: "2C1140"
    },
    ember: {
      bg: "FFFCF7", fg: "2A1206", muted: "7A5B49", accent: "B22307", accent2: "B45309",
      tint: "FDEEE4", surface: "FBF1E8", line: "E8D5C5",
      darkBg: "240D06", darkFg: "FDF6F1", darkMuted: "D3B4A3", darkAccent: "F97316",
      darkAccent2: "FBBF24", darkTint: "4A1A0B", darkSurface: "33150B"
    },
    sand: {
      bg: "FBF7EE", fg: "241D10", muted: "6E6552", accent: "92400E", accent2: "3F6212",
      tint: "F3EBD6", surface: "F5EFE1", line: "DECFB4",
      darkBg: "241D10", darkFg: "FBF7EE", darkMuted: "BFB49E", darkAccent: "E0A94B",
      darkAccent2: "A3C86A", darkTint: "3B2F1A", darkSurface: "332B1B"
    }
  }[$name];

def fail($code; $detail): error($code + ": " + $detail);

def para($text; $size; $color; $bold; $level; $bullet; $space):
  {text: $text, size: $size, color: $color, bold: $bold,
   level: $level, bullet: $bullet, spaceBefore: $space};

# A text shape states its region, alignment, anchor, and inset; the renderer
# owns line breaking, so the box never needs a measured height.
def tshape($x; $y; $cx; $cy; $paras; $align; $anchor; $inset):
  {type: "text",
   x: ($x | floor), y: ($y | floor), cx: ($cx | floor), cy: ($cy | floor),
   align: $align, anchor: $anchor,
   inset: (if $inset == null then [91440, 45720, 91440, 45720] else $inset end),
   paragraphs: $paras};

def rshape($x; $y; $cx; $cy; $fill; $line; $radius):
  {type: "rect",
   x: ($x | floor), y: ($y | floor), cx: ($cx | floor), cy: ($cy | floor),
   fill: $fill, line: $line, radius: $radius};

# A block that may carry a gradient instead of a flat colour. The renderer reads
# `gradient` when present, so a call site opts in by passing one.
def gshape($x; $y; $cx; $cy; $fill; $line; $radius; $gradient):
  rshape($x; $y; $cx; $cy; $fill; $line; $radius) + {gradient: $gradient};

def eshape($x; $y; $cx; $cy; $fill; $line):
  {type: "ellipse",
   x: ($x | floor), y: ($y | floor), cx: ($cx | floor), cy: ($cy | floor),
   fill: $fill, line: $line, radius: 0};

def pic($x; $y; $cx; $cy; $path; $ext; $crop; $alt):
  {x: ($x | floor), y: ($y | floor), cx: ($cx | floor), cy: ($cy | floor),
   path: $path, ext: $ext, crop: ($crop // {l: 0, t: 0, r: 0, b: 0}), alt: ($alt // "")};

# ---------------------------------------------------------------------------
# Text measurement
# ---------------------------------------------------------------------------

# Advance width of one code point in ems. Hangul, CJK, and fullwidth forms take
# a full em; everything else averages about half. Slightly generous, so a card
# sized from this never comes out shorter than its text.
def em_advance:
  if (. >= 4352 and . <= 4607)
     or (. >= 11904 and . <= 42191)
     or (. >= 44032 and . <= 55203)
     or (. >= 63744 and . <= 64255)
     or (. >= 65280 and . <= 65376)
  then 1 else 0.52 end;

def em_width: explode | map(em_advance) | add // 0;

# Greedy line count for a string in a box that fits $emAvail ems per line.
# The renderer breaks lines itself; this is only used to size a card and to
# decide how a block sits in its area, never to place text.
def line_count($s; $emAvail):
  if ($s | length) == 0 or $emAvail <= 0 then 0
  else
    reduce ($s | explode[]) as $c ({lines: 1, used: 0};
      ($c | em_advance) as $adv
      | if .used > 0 and (.used + $adv) > $emAvail
        then {lines: (.lines + 1), used: $adv}
        else {lines: .lines, used: (.used + $adv)}
        end)
    | .lines
  end;

# Line box height in EMU for a point size at 1.32 line spacing, the value the
# preview uses. Measurement and painting share it, so a fit decision here is the
# fit the reader sees.
def line_h($pt): ($pt * 12700 * 1.32 | floor);

def para_h($p; $emAvail):
  (line_count($p.text; $emAvail) * line_h($p.size))
  + ((($p.spaceBefore // 0) * 12700) | floor);

# Returns the outer box height for the paragraphs: the wrapped lines plus the
# top and bottom insets, which the renderer subtracts from the box before it
# lays text out. A caller that sets cy to this value gets a box that fits.
def paras_h($ps; $cx; $inset):
  (if $inset == null then [91440, 45720, 91440, 45720] else $inset end) as $in
  | (($cx - $in[0] - $in[2]) | floor) as $w
  | (([ $ps[] | (.size * 12700) as $em | para_h(.; ($w / $em)) ] | add // 0)
     + $in[1] + $in[3]);

def bullets_of($list; $size; $color; $mutedColor):
  [ $list[] |
    if type == "string" then para(.; $size; $color; false; 0; true; 6)
    else
      (.level // 0) as $lvl |
      para(
        (.text // "");
        (if .size then .size elif $lvl > 0 then ($size - 2) else $size end);
        (if .color then .color elif $lvl > 0 then $mutedColor else $color end);
        (.bold // false);
        $lvl;
        (if .bullet == false then false else true end);
        (if .space != null then .space elif $lvl > 0 then 0 else 6 end)
      )
    end
  ];

# Bullet sizes step up until the block fills the body, and a block too tall for
# the body steps back down. A slide with one bullet at 18 points in the top-left
# corner reads as unfinished; the same sentence at 22 points reads as a choice.
# The largest size is T_BODY_MAX, which keeps the body below two thirds of the
# 30-point title: a body that matches the title erases the hierarchy. The floor
# is T_BODY - 2, and a block that still does not fit is left to the overflow
# check rather than shrunk further.
def fit_bullets($list; $cx; $inset; $avail; $sizes):
  reduce ($sizes[]) as $s
    ({paras: null, size: null};
     (bullets_of($list; $s; "000000"; "000000")) as $ps
     | if (paras_h($ps; $cx; $inset)) <= $avail then {paras: $ps, size: $s} else . end)
  | if .paras == null
    then {paras: bullets_of($list; ($sizes[0] - 2); "000000"; "000000"), size: ($sizes[0] - 2)}
    else . end;

# A short block spread over the body reads as a deliberate list; the same block
# packed under the title leaves the bottom half of the page empty and reads as a
# render fault. The extra leading per paragraph is capped so three one-line
# bullets do not turn into three islands.
def spread_paras($ps; $room; $capEmu):
  ($ps | length) as $n
  | if $n < 2 or $room <= 0 then $ps
    else
      # The gaps sit between paragraphs, so there are n-1 of them; space above
      # the first paragraph would only push the whole block off its anchor.
      (([ (($room / ($n - 1)) | floor), $capEmu ] | min) / 12700 | floor) as $perPt
      | if $perPt <= 0 then $ps
        else [ $ps | to_entries[] | .value.spaceBefore = ((.value.spaceBefore // 0) + (if .key == 0 then 0 else $perPt end)) | .value ]
        end
    end;

# Vertical anchor for a block: centre a short block, top-align a full one. The
# threshold keeps a two-line block from floating in the middle of a dense page.
def anchor_for($need; $avail): if $need < ($avail * 0.78) then "ctr" else "t" end;

# ---------------------------------------------------------------------------
# Gradient
# ---------------------------------------------------------------------------
#
# A gradient is two hex colours and an angle. It fails at layout time with the
# offending value, so a typo never reaches a slide part that PowerPoint reads as
# corrupt.

def hex_ok($h): ($h | type) == "string" and ($h | test("^[0-9A-Fa-f]{6}$"));

def gradient_of($g):
  if $g == null then null
  elif ($g | type) == "array" and ($g | length) == 2
       and hex_ok($g[0]) and hex_ok($g[1]) then
    {from: ($g[0] | ascii_upcase), to: ($g[1] | ascii_upcase), angle: 90}
  elif ($g | type) == "object" then
    (if hex_ok($g.from // "") and hex_ok($g.to // "") then .
     else fail("GRADIENT_INVALID";
               "a gradient needs from and to as six hex digits without #, got "
               + ($g | tostring)) end) as $_
    | {from: ($g.from | ascii_upcase), to: ($g.to | ascii_upcase),
       angle: (if ($g.angle // 90) >= 0 and ($g.angle // 90) <= 360 then ($g.angle // 90) else 90 end)}
  else fail("GRADIENT_INVALID"; "a gradient is [from, to] or an object with from, to, angle") end;

# A colour band standing in for a picture. It is a shape so text can sit over it
# without the band moving, and it never leaves the slide bounds.
def decor_band($x; $y; $cx; $cy; $fallback; $g):
  (gradient_of($g)) as $grad
  | gshape($x; $y; $cx; $cy; (if $grad then $grad.from else $fallback end); null; 0; $grad);

# ---------------------------------------------------------------------------
# Slide kinds
# ---------------------------------------------------------------------------
def title_shape($title; $t):
  tshape(MARGIN; TITLE_Y; CW; TITLE_H; [ para($title; T_TITLE; $t.fg; true; 0; false; 0) ]; "l"; "b"; null)
  + {role: "title"};

# One sentence, no bullets. The band behind the type is the palette's dark
# surface with an optional gradient: a statement page needs a second value, or
# it reads as a title slide whose content failed to arrive.
def slide_statement($s; $t; $idx):
  (($s.text // "") | length) as $n
  | (if $n <= 44 then 40 elif $n <= 90 then 34 else 28 end) as $size
  | (paras_h([ para($s.text; $size; "000000"; true; 0; false; 0) ]; ((CW * 88) / 100 | floor); [0, 0, 0, 0])) as $txtH
  | (if $s.kicker then 548640 else 0 end) as $kickH
  | ([ ($txtH + $kickH), (BODY_H - 457200) ] | min) as $blockH
  | (BODY_Y + (((BODY_H - $blockH) / 2) | floor)) as $y0
  | {
    index: $idx, kind: "statement", dark: true,
    shapes: (
      [ decor_band(0; ($y0 - 320040); W; ($blockH + 640080); $t.darkSurface;
                   ($s.gradient // {from: $t.darkBg, to: $t.darkSurface, angle: 0})) ]
      + (if $s.kicker then
           [ tshape(MARGIN; $y0; CW; 457200;
               [ para($s.kicker; 13; $t.darkAccent; true; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0])
             + {role: "kicker"} ]
         else [] end)
      + [ tshape(MARGIN; ($y0 + $kickH); ((CW * 88) / 100 | floor); $txtH;
          [ para($s.text; $size; $t.darkFg; true; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0])
          + {role: "body"} ] ),
    notes: ($s.notes // "")
  };

# One number as the argument. Unlike `stats`, there is no grid to compare, so the
# figure is the largest type on the page and the caption reads as a claim.
def slide_bigstat($s; $t; $idx):
  (($s.value // "") | length) as $n
  | (if $n <= 4 then 150 elif $n <= 6 then 120 elif $n <= 9 then 96 else 72 end) as $vs
  | (line_h($vs) | floor) as $valH
  | (if $s.label then (22 * 12700 * 1.4 | floor) + 91440 else 0 end) as $labH
  | (if $s.note then (T_SMALL * 12700 * 1.4 | floor) + 91440 else 0 end) as $noteH
  | ($valH + $labH + $noteH) as $blockH
  | (BODY_Y + (((BODY_H - $blockH) / 2) | floor)) as $y0
  | {
    index: $idx, kind: "bigstat", dark: false,
    shapes: (
      [ rshape(0; 0; 91440; H; $t.accent; null; 0) + {role: "decor"} ]
      + (if $s.kicker then
           [ tshape(MARGIN; (BODY_Y - 457200); CW; 365760;
               [ para($s.kicker; 13; $t.muted; true; 0; false; 0) ]; "l"; "b"; [0, 0, 0, 0])
             + {role: "kicker"} ]
         else [] end)
      + [ tshape(MARGIN; $y0; ((CW * 90) / 100 | floor); $valH;
          [ para($s.value; $vs; $t.accent; true; 0; false; 0) ]; "l"; "b"; [0, 0, 0, 0])
          + {role: "title"} ]
      + (if $s.label then
           [ tshape(MARGIN; ($y0 + $valH + 45720); ((CW * 80) / 100 | floor); ($labH - 45720);
               [ para($s.label; 22; $t.fg; false; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0])
             + {role: "body"} ]
         else [] end)
      + (if $s.note then
           [ tshape(MARGIN; ($y0 + $valH + $labH + 45720); ((CW * 72) / 100 | floor); ($noteH - 45720);
               [ para($s.note; T_SMALL; $t.muted; false; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0])
             + {role: "body"} ]
         else [] end) ),
    notes: ($s.notes // "")
  };

# A numbered run of 2 to 5 steps. Connectors are short rules, not arrows, so the
# row keeps reading as a row at projection distance, and the cards are sized from
# the longest heading and body instead of a guessed height.
# Two steps are not a row: two cards across a wide page become banners with a
# sentence at the left edge and two thirds of the page empty under them. They
# stack instead, each a full-width row with the badge beside the heading, and
# the pair is centred as one block.
def process_rows($s; $t; $idx; $n):
  (CW - 64008 - GAP_TIGHT - 457200 - GAP - GAP_TIGHT) as $tw
  | ([ 19, 17, 15 ] | map(
       . as $ts
       | ([ $s.steps[] | line_count((.text // ""); ($tw / ($ts * 12700))) ] | max // 1) as $tl
       | {size: $ts, lines: $tl, textH: ($tl * line_h($ts))})) as $cand
  | (line_h(22)) as $headH
  | (([ $cand[] | select((.textH + $headH + 45720) <= (BODY_H / 2 - 548640)) ] | .[0])
     // ($cand | .[2])) as $fit
  | (GAP_TIGHT + $headH + 45720 + $fit.textH + GAP_TIGHT) as $inner
  # The end caps carry 64008 EMU of accent rule inside the card, so the text
  # block starts past it rather than on top of it.
  | (([ $inner, 1005840 ] | max) + 2 * 228600) as $rowH
  | (([ BODY_H - $rowH - 228600, 0 ] | max) / 2 | floor) as $top
  | (BODY_Y + $top) as $y0
  | ($y0 + $rowH + 228600) as $y1
  | {
    index: $idx, kind: "process", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + [ range(0; 2) as $i |
          ($s.steps[$i]) as $st |
          (if $i == 0 then $y0 else $y1 end) as $y |
          (($y + (($rowH - $inner) / 2 | floor))) as $ty |
          rshape(MARGIN; $y; CW; $rowH; $t.surface; null; 0) + {role: "decor"},
          rshape(MARGIN; $y; 64008; $rowH; (if $i == 0 then $t.accent else $t.accent2 end); null; 0)
            + {role: "decor"},
          # The badge sits on the heading's first line, not in the middle of the
          # card: a number floating between two lines reads as decoration.
          eshape((MARGIN + 64008 + GAP_TIGHT); ($ty + (($headH - 457200) / 2 | floor));
                 457200; 457200; (if $i == 0 then $t.accent else $t.accent2 end); null)
            + {role: "decor"},
          tshape((MARGIN + 64008 + GAP_TIGHT); ($ty + (($headH - 457200) / 2 | floor));
                 457200; 457200;
            [ para((($i + 1) | tostring); 16; "FFFFFF"; true; 0; false; 0) ]; "c"; "ctr";
            [0, 0, 0, 0]) + {role: "decor"},
          tshape((MARGIN + 64008 + GAP_TIGHT + 457200 + GAP); $ty; $tw; $inner;
            ([ para($st.heading; 22; $t.fg; true; 0; false; 0),
               para($st.text; $fit.size; $t.muted; false; 0; false; 8) ]);
            "l"; "t"; [0, 0, 0, 0]) + {role: "body"}
        ] ),
    notes: ($s.notes // "")
  };

def slide_process($s; $t; $idx):
  (($s.steps // []) | length) as $n
  | if $n < 2 then fail("PROCESS_TOO_FEW"; "a process needs 2 to 5 steps, got " + ($n | tostring))
    elif $n > 5 then fail("PROCESS_TOO_MANY";
                          "a process takes at most 5 steps; group the run or split it, got " + ($n | tostring))
    elif $n == 2 then process_rows($s; $t; $idx; $n)
    else . end
  | if ($n == 2) then . else
  (((CW - ($n - 1) * GAP) / $n) | floor) as $cwd
  | (($cwd - 2 * GAP_TIGHT) | floor) as $iw
  # Four or five steps leave a narrow column, so the heading drops a size rather
  # than wrapping into a second line that eats the card.
  | (if $n >= 4 then 18 else 20 end) as $hsz
  | ([ $s.steps[] | line_count((.heading // ""); ($iw / ($hsz * 12700))) ] | max // 1) as $hlines
  | ($hlines * line_h($hsz)) as $headH
  | (BODY_H * 0.6 | floor) as $chTarget
  # A card that only fits two short sentences at 15pt leaves the row as a thin
  # strip. The body steps down until the column is filled without the text
  # outgrowing its heading.
  | ([ ($hsz - 4), 15, 14 ] | map(
       . as $ts
       | ([ $s.steps[] | line_count((.text // ""); ($iw / ($ts * 12700))) ] | max // 1) as $tl
       | (GAP_TIGHT + 548640 + 45720 + $headH + 45720 + ($tl * line_h($ts)) + GAP_TIGHT) as $w
       | {size: $ts, want: $w, lines: $tl})) as $cand
  | (([ $cand[] | select(.want <= $chTarget) ] | .[0]) // {size: 14, lines: 1}) as $body
  | ($body.size) as $tsz
  | ($body.lines * line_h($tsz)) as $bodyH
  | (GAP_TIGHT + 548640 + 45720 + $headH + 45720 + $bodyH + GAP_TIGHT) as $wanted
  # The card keeps the same 62% floor as a card row elsewhere, so four short
  # steps hold the page instead of falling into a thin band across the middle,
  # and the badge, heading and body are centred inside it as one stack.
  | (([ $wanted, (lead_avail($s) * CARD_FLOOR | floor) ] | max)
     | if . > lead_avail($s) then lead_avail($s) else . end) as $ch
  | (lead_top($s) + (((lead_avail($s) - $ch) / 2) | floor)) as $cy
  # The inset is measured from the stack alone, not from the card with its two
  # pads, or the text sits a pad high and the extra height pools at the bottom.
  | ([ (((($ch - ($wanted - 2 * GAP_TIGHT)) / 2) | floor)), GAP_TIGHT ] | max) as $inY
  | {
    index: $idx, kind: "process", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + [ range(0; $n) as $i |
          ($s.steps[$i]) as $st |
          ((MARGIN + $i * ($cwd + GAP)) | floor) as $x |
          # The connector joins the two badges at their centre, so it lines up
          # with the numbers rather than with the top edge of the card.
          (if $i < ($n - 1) then
             rshape(($x + $cwd); ($cy + $inY + 228600 - 9525); GAP; 19050;
                    $t.line; null; 0) + {role: "decor"}
           else empty end),
          rshape($x; $cy; $cwd; $ch; $t.surface; null; 0) + {role: "decor"},
          # The first badge carries the accent so the run shows where it starts;
          # the rest use the companion colour, not a rank.
          eshape(($x + GAP_TIGHT); ($cy + $inY); 457200; 457200;
                 (if $i == 0 then $t.accent else $t.accent2 end); null) + {role: "decor"},
          tshape(($x + GAP_TIGHT); ($cy + $inY); 457200; 457200;
            [ para((($i + 1) | tostring); 16; "FFFFFF"; true; 0; false; 0) ]; "c"; "ctr";
            [0, 0, 0, 0]) + {role: "decor"},
          tshape(($x + GAP_TIGHT); ($cy + $inY + 548640); $iw; $headH;
            [ para($st.heading; $hsz; $t.fg; true; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0])
            + {role: "body"},
          tshape(($x + GAP_TIGHT); ($cy + $inY + 548640 + $headH + 45720); $iw; $bodyH;
            [ para($st.text; $tsz; $t.muted; false; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0])
            + {role: "body"}
        ] ),
    notes: ($s.notes // "")
  } end;



# The cover holds one claim, so the block is centred on the page as a unit:
# kicker, title, subtitle, then a short rule that stands clear of the subtitle
# instead of touching it. The meta line stays pinned to the foot.
def slide_title($s; $t; $idx):
  (if $s.kicker then 457200 + 182880 else 0 end) as $kickH
  | (paras_h([ para($s.title; 44; "000000"; true; 0; false; 0) ]; CW; null)) as $titleH
  | (if $s.subtitle
     then 182880 + (paras_h([ para($s.subtitle; 20; "000000"; false; 0; false; 0) ]; CW; null))
     else 0 end) as $subH
  | ($kickH + $titleH + $subH + 256032 + 45720) as $blockH
  | (((H - $blockH) / 2 - 274320) | floor) as $y0
  # The rule stands in the space reserved below the text, not on the last
  # baseline: a rule touching the subtitle reads as an underline.
  | ($y0 + $kickH + $titleH + $subH + 228600) as $ruleY
  | {
    index: $idx, kind: "title", dark: true,
    shapes: (
      (if $s.kicker then
         [ tshape(MARGIN; $y0; CW; 457200;
             [ para($s.kicker; 13; $t.darkAccent; true; 0; false; 0) ]; "l"; "b"; null)
           + {role: "kicker"} ]
       else [] end)
      + [ tshape(MARGIN; ($y0 + $kickH); CW; ($titleH + $subH);
          ([ para($s.title; 44; $t.darkFg; true; 0; false; 0) ]
           + (if $s.subtitle then [ para($s.subtitle; 20; $t.darkMuted; false; 0; false; 8) ] else [] end));
          "l"; "b"; null) + {role: "title"},
        rshape(MARGIN; $ruleY; 1097280; 45720; $t.darkAccent; null; 0) + {role: "decor"}
      ]
      + (if $s.meta then
           [ tshape(MARGIN; 5760720; CW; 457200;
               [ para($s.meta; 13; $t.darkMuted; false; 0; false; 0) ]; "l"; "t"; null)
             + {role: "body"} ]
         else [] end) ),
    notes: ($s.notes // "")
  };

# A section opener holds three short lines and nothing else, so the block is
# centred on the page. Anchoring it to the top leaves the bottom two thirds
# dark and empty, which reads as a rendering fault rather than a pause.
def slide_section($s; $t; $idx):
  (if $s.number then 548640 + 182880 else 0 end) as $numH
  | 868680 as $titleH
  | (if $s.subtitle then 137160 + 548640 else 0 end) as $subH
  | ($numH + $titleH + $subH) as $blockH
  | (((H - $blockH) / 2) | floor) as $y0
  | ($y0 + $numH) as $titleY
  | {
    index: $idx, kind: "section", dark: true,
    shapes: (
      (if $s.number then
         [ tshape(MARGIN; $y0; CW; 548640; [ para($s.number; 15; $t.darkAccent; true; 0; false; 0) ]; "l"; "b"; null)
             + {role: "kicker"},
           rshape(MARGIN; ($y0 + 548640 + 45720); 731520; 27432; $t.darkAccent; null; 0)
             + {role: "decor"} ]
       else [] end)
      + [ tshape(MARGIN; $titleY; CW; $titleH; [ para($s.title; 36; $t.darkFg; true; 0; false; 0) ]; "l"; "b"; null)
          + {role: "title"} ]
      + (if $s.subtitle then
           [ tshape(MARGIN; ($titleY + $titleH + 137160); ((CW * 4) / 5 | floor); 548640;
               [ para($s.subtitle; 17; $t.darkMuted; false; 0; false; 0) ]; "l"; "t"; null)
             + {role: "body"} ]
         else [] end) ),
    notes: ($s.notes // "")
  };

def slide_bullets($s; $t; $idx):
  (if $s.lead then BODY_Y + 640080 else BODY_Y end) as $y0
  | (BODY_BOTTOM - $y0) as $avail
  | ([ T_BODY, 19, 20, 21, T_BODY_MAX ]) as $sizes
  | (fit_bullets($s.bullets; ((CW * 86) / 100 | floor); null; $avail; $sizes)) as $fit
  | (paras_h($fit.paras; ((CW * 86) / 100 | floor); null)) as $need0
  | (spread_paras($fit.paras; (($avail * 0.86 | floor) - $need0); (18 * 12700))) as $paras
  | (paras_h($paras; ((CW * 86) / 100 | floor); null)) as $need
  | {
    index: $idx, kind: "bullets", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; BODY_Y; CW; 548640; [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end)
      # With a lead the block starts right under it: the lead is the opening line
      # of the block, and a gap between them reads as two separate things.
      # Without a lead the block is centred in the body, so a short block sits at
      # the optical centre instead of hanging from the title. The box is as tall
      # as the block, not as tall as the area: a centred box that kept the full
      # area height would slide its bottom edge past the footer.
      + [ tshape(MARGIN; (if $s.lead then $y0
                          else ($y0 + ((($avail - $need) / 2) | floor)) end);
          ((CW * 86) / 100 | floor); $need;
          ([ $paras[] | .color = (if .level > 0 then $t.muted else $t.fg end) ]);
          "l"; "t"; null) ] ),
    notes: ($s.notes // "")
  };

# Cards. Height follows the tallest column's own text, the row is centred in the
# body when it is short, and each card carries a hairline accent rule so three
# short cards still read as three objects rather than three empty panels.
def card_height($columns; $cwd; $cols; $size):
  (((($cwd - 365760 - 342900) / ($size * 12700)) | floor)) as $emAvail
  | ([ range(0; $cols) as $i |
       ($columns[$i].bullets // []) as $bl
       | ([ $bl[] |
            (if type == "string" then {text: ., level: 0, space: 6}
             else {text: (.text // ""), level: (.level // 0),
                   space: (if .space != null then .space elif (.level // 0) > 0 then 0 else 6 end)} end)
            | ((line_count(.text; ($emAvail - (if .level > 0 then 2 else 0 end)))
                 * line_h((if .level > 0 then ($size - 2) else $size end)))
               + (.space * 12700))
          ] | add // 0)
     ] | max // 0);

def slide_columns($s; $t; $idx):
  ($s.columns | length) as $n
  | (if $n > 3 then 3 elif $n < 1 then 1 else $n end) as $cols
  | (((CW - ($cols - 1) * GAP) / $cols) | floor) as $cwd
  | (card_height($s.columns; $cwd; $cols; T_SMALL)) as $bodyNeed
  # The heading band is measured too: a fixed reserve put the bullets high and
  # left a blank block under them, which reads as content that failed to arrive.
  | ([ range(0; $cols) | line_count(($s.columns[.].heading // ""); ($cwd / (17 * 12700))) ] | max // 1) as $headLines
  | ($headLines * line_h(17)) as $headH
  | (GAP_TIGHT + $headH + 91440 + $bodyNeed + GAP_TIGHT) as $wanted
  # A card hugs its own text, but never drops below CARD_FLOOR of the body: three
  # short cards at their own height stop a third of the way down the page and
  # read as content that never arrived. The row is then centred, which the floor
  # keeps honest -- a row that fills most of the body needs no cap.
  | (([ $wanted, (lead_avail($s) * CARD_FLOOR | floor) ] | max)
     | if . > lead_avail($s) then lead_avail($s) else . end) as $cardH
  | (lead_top($s) + (((lead_avail($s) - $cardH) / 2) | floor)) as $cardY
  # Heading and bullets are one stack inside the card, so spare height becomes
  # equal padding above and below the text instead of a strip under the bullets.
  | ([ (((($cardH - $headH - 91440 - $bodyNeed) / 2) | floor)), GAP_TIGHT ] | max) as $inTop
  | {
    index: $idx, kind: "columns", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; (BODY_Y - 91440); CW; 548640;
               [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "b"; null) ]
         else [] end)
      + [ range(0; $cols) as $i |
          ($s.columns[$i]) as $c |
          ((MARGIN + $i * ($cwd + GAP)) | floor) as $x |
          rshape($x; $cardY; $cwd; $cardH; $t.surface; null; 0),
          rshape($x; $cardY; $cwd; RULE_H; $t.accent; null; 0),
          tshape($x; ($cardY + $inTop); $cwd; $headH;
            [ para($c.heading; 17; $t.accent; true; 0; false; 0) ]; "l"; "t";
            [GAP_TIGHT, 0, GAP_TIGHT, 0]),
          tshape($x; ($cardY + $inTop + $headH + 91440); $cwd;
                 (($cardH - $inTop - $headH - 91440) | if . < 548640 then 548640 else . end);
            bullets_of(($c.bullets // []); T_SMALL; $t.fg; $t.muted); "l"; "t";
            [GAP_TIGHT, 0, GAP_TIGHT, 0])
        ] ),
    notes: ($s.notes // "")
  };

# Headline numbers. The value is sized from its own length so "1,284억" and "47%"
# carry the same optical weight, and the row is centred when the cards are short.
def stat_value_size($v):
  ($v | length) as $n
  | if $n <= 3 then 60 elif $n <= 5 then 52 elif $n <= 7 then 44 else 36 end;

def slide_stats($s; $t; $idx):
  ($s.stats | length) as $n
  | (if $n > 4 then 4 elif $n < 1 then 1 else $n end) as $cols
  | (((CW - ($cols - 1) * GAP) / $cols) | floor) as $cwd
  # One value size for the row, from the longest string: a three-character figure
  # at 60pt beside a seven-character one at 44pt makes the second look minor.
  | ([ $s.stats[] | stat_value_size(.value) ] | min // 60) as $vsize
  | (line_h($vsize)) as $valH
  # Labels and notes wrap: their bands are measured from the longest one at the
  # card's inner width, so a two-line label pushes the note down instead of
  # landing on it.
  | (($cwd - 2 * GAP_TIGHT) / (T_SMALL * 12700)) as $labEm
  | (($cwd - 2 * GAP_TIGHT) / (T_CAPTION * 12700)) as $noteEm
  | ([ $s.stats[] | line_count((.label // ""); $labEm) ] | max // 0) as $labLines
  | ([ $s.stats[] | line_count((.note // ""); $noteEm) ] | max // 0) as $noteLines
  | (if $labLines > 0 then ($labLines * line_h(T_SMALL)) + 274320 else 0 end) as $labH
  | (if $noteLines > 0 then ($noteLines * line_h(T_CAPTION)) + 182880 else 0 end) as $noteH
  # The card is its own stack plus a pad. A card fixed to a share of the body
  # leaves a dead strip under the note, which reads as content that never arrived.
  | (([ ($valH + $labH + $noteH + 2 * GAP), (lead_avail($s) * CARD_FLOOR | floor) ] | max)
     | if . > lead_avail($s) then lead_avail($s) else . end) as $cardH
  # Centred like `columns`, with the same floor doing the work of holding the row.
  | (lead_top($s) + (((lead_avail($s) - $cardH) / 2) | floor)) as $cardY
  | (($cardH - ($valH + $labH + $noteH)) / 2 | floor) as $padTop
  | {
    index: $idx, kind: "stats", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; (BODY_Y - 91440); CW; 548640;
               [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "b"; null) ]
         else [] end)
      + [ range(0; $cols) as $i |
          ($s.stats[$i]) as $st |
          ((MARGIN + $i * ($cwd + GAP)) | floor) as $x |
          $vsize as $vs |
          rshape($x; $cardY; $cwd; $cardH; $t.surface; null; 0),
          rshape($x; $cardY; $cwd; RULE_H; $t.accent; null; 0),
          tshape($x; ($cardY + $padTop); $cwd; $valH;
            [ para($st.value; $vs; $t.accent; true; 0; false; 0) ]; "l"; "b";
            [GAP_TIGHT, 0, GAP_TIGHT, 0]),
          tshape($x; ($cardY + $padTop + $valH + 274320); $cwd; $labH;
            [ para($st.label; T_SMALL; $t.fg; false; 0; false; 0) ]; "l"; "t";
            [GAP_TIGHT, 0, GAP_TIGHT, 0])
        ]
      + [ range(0; $cols) as $i |
          ($s.stats[$i]) as $st |
          ((MARGIN + $i * ($cwd + GAP)) | floor) as $x |
          (if $st.note then
             tshape($x; ($cardY + $padTop + $valH + $labH + 274320); $cwd; $noteH;
               [ para($st.note; T_CAPTION; $t.muted; false; 0; false; 0) ]; "l"; "t";
               [GAP_TIGHT, 0, GAP_TIGHT, 0])
           else empty end)
        ] ),
    notes: ($s.notes // "")
  };

# One number that carries the slide, with the argument beside it. Used when the
# audience should remember a single figure and the reasons for it.
# A number with its label is one block. The card is sized to that block and the
# block is centred in the body, so a short KPI does not sit in a tall empty box.
def slide_kpi($s; $t; $idx):
  (($s.bullets // []) | length) as $nb
  | (if $nb > 0 then ((CW * 40) / 100 | floor) else CW end) as $lw
  | (if $nb > 0 then (CW - $lw - GAP) else 0 end) as $rw
  | (($s.value | length) as $n | if $n <= 3 then 96 elif $n <= 5 then 80 elif $n <= 7 then 66 else 54 end) as $vs
  | (line_h($vs)) as $valH
  | (if $s.label then ((17 * 12700 * 1.35) | floor) + 91440 else 0 end) as $labH
  | (if $s.delta then ((T_SMALL * 12700 * 1.35) | floor) + 91440 else 0 end) as $delH
  | ($valH + $labH + $delH) as $stackH
  # The card and the argument beside it form one row, so both take the taller
  # of the two heights. A short card next to three bullets leaves a step.
  | (if $nb > 0
     then paras_h(bullets_of($s.bullets; 20; "000000"; "000000"); $rw; null)
     else 0 end) as $argH
  | (([ $stackH, $argH ] | max) + 2 * GAP) as $rowH
  | ($rowH | if . > lead_avail($s) then lead_avail($s) else . end) as $cardH
  | (lead_top($s) + (((lead_avail($s) - $cardH) / 2) | floor)) as $cy
  | (($cardH - $stackH) / 2 | floor) as $padTop
  | {
    index: $idx, kind: "kpi", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; (BODY_Y - 91440); CW; 548640;
               [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "b"; null) ]
         else [] end)
      + (if $nb > 0 then
           [ rshape(MARGIN; $cy; $lw; $cardH; $t.surface; null; 0),
             rshape(MARGIN; $cy; $lw; RULE_H; $t.accent; null; 0),
             tshape((MARGIN + GAP_TIGHT); ($cy + $padTop); ($lw - 2 * GAP_TIGHT); $valH;
               [ para($s.value; $vs; $t.accent; true; 0; false; 0) ]; "l"; "b";
               [0, 0, 0, 0]) ]
           + (if $s.label then
                [ tshape((MARGIN + GAP_TIGHT); ($cy + $padTop + $valH + 45720); ($lw - 2 * GAP_TIGHT); ($labH - 45720);
                    [ para($s.label; 17; $t.fg; false; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0]) ]
              else [] end)
           + (if $s.delta then
                [ tshape((MARGIN + GAP_TIGHT); ($cy + $padTop + $valH + $labH + 45720); ($lw - 2 * GAP_TIGHT); ($delH - 45720);
                    [ para($s.delta; T_SMALL; $t.muted; false; 0; false; 0) ]; "l"; "t"; [0, 0, 0, 0]) ]
              else [] end)
         else
           [ tshape(MARGIN; BODY_Y; CW; (BODY_H - 1371600);
               [ para($s.value; $vs; $t.accent; true; 0; false; 0) ]; "l"; "b"; null) ]
           + (if $s.label then
                [ tshape(MARGIN; (BODY_BOTTOM - 1097280); CW; 731520;
                    [ para($s.label; 20; $t.fg; false; 0; false; 0) ]; "l"; "t"; null) ]
              else [] end)
         end)
      + (if $nb > 0 then
           [ tshape((MARGIN + $lw + GAP); $cy; $rw; $cardH;
               bullets_of($s.bullets; 20; $t.fg; $t.muted); "l"; "ctr";
               [0, 0, 0, 0]) ]
         else [] end) ),
    notes: ($s.notes // "")
  };

# Two panels with a claim each. The divider is a hairline, not a box: two boxes
# side by side read as two slides glued together.
# Short comparison panels get larger type, capped so the two sides still read as
# one row rather than two different documents.
def compare_size($side; $pw):
  reduce (16, 18, 20, 22, 24) as $sz (16;
    if paras_h(bullets_of(($side.bullets // []); $sz; "000000"; "000000"); $pw; null)
       <= (BODY_H * 0.8) then $sz else . end);

def slide_compare($s; $t; $idx):
  ((CW - GAP) / 2 | floor) as $pw
  # The two panels are one block: measure the taller side and centre the block
  # in the body, so a three-point comparison does not sit in the top third with
  # two thirds of the page left white.
  | (line_h(20)) as $cmpHeadH
  | (137160 + $cmpHeadH + 182880) as $cmpBodyY
  | ([ $s.left, $s.right ] | map(
       (if . == null then 0
        else $cmpBodyY + paras_h(bullets_of((.bullets // []); compare_size(.; $pw); "000000"; "000000"); $pw; null)
        end)) | max // 0) as $need
  | (([ $s.left, $s.right ] | map(select(. != null) | compare_size(.; $pw)) | min) // 16) as $bsize
  # Centring is capped: a short block dropped to the exact middle detaches from
  # the title, so the offset never exceeds a third of the body.
  | (lead_top($s) + (([ (lead_avail($s) - $need) / 2, CENTRE_CAP ] | min) | floor)) as $py
  | $need as $ph
  | {
    index: $idx, kind: "compare", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; (BODY_Y - 91440); CW; 548640;
               [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "b"; null) ]
         else [] end)
      + [ range(0; 2) as $i |
          (if $i == 0 then $s.left else $s.right end) as $side |
          ((MARGIN + $i * ($pw + GAP)) | floor) as $x |
          (if $side == null then empty
           else
             rshape($x; $py; $pw; RULE_H; (if $i == 0 then $t.line else $t.accent end); null; 0),
             tshape($x; ($py + 137160); $pw; $cmpHeadH;
               [ para($side.heading; 20; $t.fg; true; 0; false; 0) ]; "l"; "t";
               [0, 0, 0, 0]),
             tshape($x; ($py + $cmpBodyY); $pw; (($ph - $cmpBodyY) | if . < 914400 then 914400 else . end);
               bullets_of(($side.bullets // []); $bsize; $t.fg; $t.muted); "l"; "t";
               [0, 0, 0, 0])
           end)
        ] ),
    notes: ($s.notes // "")
  };

# A row of milestones on one rule. Reading order down the page is date, title,
# rule with its markers, then detail. The block is spread over most of the body
# instead of being packed tight and centred: three milestones occupy a wide
# horizontal band, and a band that only fills a third of the height leaves two
# dead margins that read as a layout fault.
def slide_timeline($s; $t; $idx):
  (($s.milestones // []) | length) as $n
  | (if $n > 5 then 5 elif $n < 2 then 2 else $n end) as $cols
  | ((CW / $cols) | floor) as $cwd
  | (($cwd - GAP_TIGHT) | floor) as $tw
  # Each band is measured from the longest milestone in it. A band sized as a
  # fixed share of the body reserves height nothing uses, and the leftover
  # shows up as a dead strip under the detail line.
  | ([ range(0; $cols) | line_count(($s.milestones[.].label // ""); ($tw / (16 * 12700))) ] | max // 1) as $labLines
  | ([ range(0; $cols) | line_count(($s.milestones[.].title // ""); ($tw / (32 * 12700))) ] | max // 1) as $titLines
  | ([ range(0; $cols) | line_count(($s.milestones[.].text // $s.milestones[.].detail // ""); ($tw / (19 * 12700))) ] | max // 1) as $detLines
  | (($labLines * line_h(16))) as $labH
  | (($titLines * line_h(32))) as $titH
  | (($detLines * line_h(19))) as $detH
  | ($labH + 182880 + $titH + 320040 + 19050 + 182880 + $detH) as $blockH
  | ($blockH | if . > lead_avail($s) then lead_avail($s) else . end) as $blockH2
  # The timeline is a horizontal band, not a block: it fills the width and only
  # about a third of the height, so centring is what keeps the top and bottom
  # margins equal. The cap that keeps a short two-column block near its title
  # would instead strand this band high with a dead third of the page below.
  | (lead_top($s) + (((lead_avail($s) - $blockH2) / 2) | floor)) as $y0
  | ($y0 + $labH + 182880) as $titleY
  | ($titleY + $titH + 320040) as $ruleY
  | ($ruleY + 182880) as $detailY
  | {
    index: $idx, kind: "timeline", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; (BODY_Y - 91440); CW; 548640;
               [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "b"; null) ]
         else [] end)
      # The rule stops just past the last marker instead of running to the page
      # edge, so it reads as a measured span rather than a divider.
      + [ rshape(MARGIN; ($ruleY - 9525);
                 ((($cols - 1) * $cwd) + 121920); 19050; $t.line; null; 0) ]
      + [ range(0; $cols) as $i |
          ($s.milestones[$i]) as $m |
          ((MARGIN + $i * $cwd) | floor) as $x |
          tshape($x; $y0; $tw; $labH;
            [ para(($m.label // ""); 16; $t.accent; true; 0; false; 0) ]; "l"; "b";
            [0, 0, 0, 0]),
          tshape($x; $titleY; $tw; $titH;
            [ para(($m.title // ""); 32; $t.fg; true; 0; false; 0) ]; "l"; "b";
            [0, 0, 0, 0]),
          rshape(($x + 68580); ($ruleY - 60960); 121920; 121920; $t.accent; null; 0),
          tshape($x; $detailY; $tw; $detH;
            # `text` is the documented key; `detail` stays readable because the
            # first drafts of this layout used it.
            [ para(($m.text // $m.detail // ""); 19; $t.muted; false; 0; false; 0) ]; "l"; "t";
            [0, 0, 0, 0])
        ] ),
    notes: ($s.notes // "")
  };

# A table with two rows is a statement, not a grid. Rows grow with the space
# available up to a readable cap and the block is centred in the body, so a
# short table does not hang from the title with half the page empty below.
def slide_table($s; $t; $idx):
  ($s.table.columns | length) as $ncols
  | (($s.table.rows | length) + 1) as $nrows
  | (if $s.table.caption then 457200 else 0 end) as $capH
  | (((BODY_H - $capH) / $nrows) | floor) as $rawH
  | ($rawH | if . > 1097280 then 1097280 elif . < 320040 then 320040 else . end) as $rh
  | (($rh * $nrows) | floor) as $th
  | (BODY_Y + (((BODY_H - $capH - $th) / 2) | floor)) as $ty
  | (if $rh >= 731520 then 17 elif $rh >= 548640 then 15 else 13 end) as $tsz
  | {
    index: $idx, kind: "table", dark: false,
    shapes:
      ([ title_shape($s.title; $t) ]
       + (if $s.table.caption then
            [ tshape(MARGIN; ($ty + $th + 91440); CW; 320040;
                [ para($s.table.caption; T_CAPTION; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
          else [] end)),
    table: {
      x: MARGIN, y: $ty, cx: CW, cy: $th,
      colWidths: [ range(0; $ncols) | ((CW / $ncols) | floor) ],
      rowHeights: [ range(0; $nrows) | $rh ],
      header: $s.table.columns,
      rows: $s.table.rows,
      headerFill: $t.accent, headerColor: "FFFFFF",
      bodyFill: $t.bg, altFill: $t.surface, bodyColor: $t.fg,
      size: $tsz
    },
    notes: ($s.notes // "")
  };

# A chart is the visual; the slide carries the claim in the title and the unit
# and base in the caption. The chart box keeps a fixed height so the caption and
# the axis labels never compete for the same space.
def slide_chart($s; $t; $idx):
  ((CW * 88) / 100 | floor) as $chw
  # The chart takes the body almost whole; only the caption line is reserved.
  # A short chart box leaves the page bottom empty, which is the same defect as
  # an empty card row.
  | ((BODY_H - (if $s.chart.caption then 411480 else 0 end)) | floor) as $chh2
  | {
    index: $idx, kind: "chart", dark: false,
    shapes:
      ([ title_shape($s.title; $t) ]
       + (if $s.chart.caption then
            [ tshape(MARGIN; (BODY_Y + $chh2 + 91440); CW; 320040;
                [ para($s.chart.caption; T_CAPTION; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
          else [] end)),
    chart: {
      x: ((W - $chw) / 2 | floor), y: BODY_Y, cx: $chw, cy: $chh2,
      type: ($s.chart.type // "column"),
      categories: $s.chart.categories,
      series: $s.chart.series,
      colors: [ $t.accent, $t.muted, $t.line, $t.surface, $t.fg ],
      fg: $t.fg, muted: $t.muted, bg: $t.bg, accent: $t.accent, line: $t.line,
      axCat: "111111111", axVal: "222222222",
      # A combo needs a second value axis, or the rate line is drawn against the
      # volume scale and flattens onto the baseline.
      axVal2: "333333333",
      labels: ($s.chart.labels // false),
      legend: ($s.chart.legend // (if (($s.chart.series // []) | length) > 1 then "bottom" else "none" end)),
      numberFormat: ($s.chart.numberFormat // "General"),
      valueAxisTitle: ($s.chart.valueAxisTitle // null),
      categoryAxisTitle: ($s.chart.categoryAxisTitle // null),
      hole: ($s.chart.hole // $s.chart.holeSize // 50)
    },
    notes: ($s.notes // "")
  };

# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------

# contain: the whole picture fits, letterboxed inside the box.
# cover: the picture fills the box and the overflow is cropped through srcRect.
# The crop is expressed as fractions of the source so the PPTX and the preview
# compute the same window.
def fit_box($boxW; $boxH; $aspect; $mode):
  ($boxW / $boxH) as $q
  | if $mode == "fill" then
      (if $aspect >= $q
       then {w: $boxW, h: $boxH, crop: {l: (((1 - ($q / $aspect)) / 2) * 100), t: 0,
                                        r: (((1 - ($q / $aspect)) / 2) * 100), b: 0}}
       else {w: $boxW, h: $boxH, crop: {l: 0, t: (((1 - ($aspect / $q)) / 2) * 100),
                                        r: 0, b: (((1 - ($aspect / $q)) / 2) * 100)}} end)
    else
      (if $aspect >= $q
       then {w: $boxW, h: (($boxW / $aspect) | floor), crop: {l: 0, t: 0, r: 0, b: 0}}
       else {w: (($boxH * $aspect) | floor), h: $boxH, crop: {l: 0, t: 0, r: 0, b: 0}} end)
    end;

def image_of($img; $x; $y; $boxW; $boxH; $mode; $alt):
  (($img.aspect // 1.7777778)) as $aspect
  | (fit_box($boxW; $boxH; $aspect; $mode)) as $f
  | pic(($x + (($boxW - $f.w) / 2 | floor)); ($y + (($boxH - $f.h) / 2 | floor));
        $f.w; $f.h; $img.path; ($img.ext // ($img.path | split(".") | .[-1] | ascii_downcase));
        $f.crop; (if $alt then $alt else ($img.alt // "") end));

def slide_image($s; $t; $idx):
  (if $s.title then 640080 else 0 end) as $titleDrop
  | (BODY_Y + $titleDrop) as $y0
  | (if $s.caption then 411480 else 0 end) as $capH
  | (BODY_BOTTOM - $y0 - $capH) as $areaH
  | {
    index: $idx, kind: "image", dark: false,
    shapes: (
      (if $s.title then [ title_shape($s.title; $t) ] else [] end)
      + (if $s.caption then
           [ tshape(MARGIN; (BODY_BOTTOM - 320040); CW; 320040;
               [ para((if $s.image.credit then $s.caption + "  ·  " + $s.image.credit else $s.caption end);
                       T_CAPTION; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end) ),
    images: [ image_of($s.image; MARGIN; $y0; CW; $areaH; ($s.image.fit // "contain"); $s.image.alt) ],
    notes: ($s.notes // "")
  };

# Picture beside an argument. The picture column is 52% of the text column so the
# picture reads as the evidence and the words as the claim, not the reverse.
# Both columns share one measured row: the picture is exactly as tall as the
# text block beside it, never the full body with the words stranded at the top.
def slide_imagetext($s; $t; $idx):
  ((CW * 52) / 100 | floor) as $pw
  | (CW - $pw - GAP * 2) as $tw
  | (if $s.lead then 548640 else 0 end) as $leadH
  | (BODY_Y + $leadH) as $y0
  | (if $s.heading then 731520 else 0 end) as $headH
  | ((BODY_BOTTOM - $y0 - $headH)) as $textAvail
  | (fit_bullets(($s.bullets // []); $tw; null; $textAvail; [16, 18, 20, 22])) as $fit
  | (paras_h($fit.paras; $tw; null)) as $textH
  | (($headH + $textH) | if . < ($textAvail * 0.45) then ($textAvail * 0.45 | floor) else . end) as $blockH
  | ((BODY_Y + $leadH + (((BODY_BOTTOM - $y0 - $blockH) / 2) | floor))) as $ty
  | (if ($s.image.side // "right") == "left" then MARGIN else (MARGIN + $tw + GAP * 2) end) as $ix
  | (if ($s.image.side // "right") == "left" then (MARGIN + $pw + GAP * 2) else MARGIN end) as $tx
  | {
    index: $idx, kind: "imagetext", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; BODY_Y; CW; 548640;
               [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end)
      + (if $s.heading then
           [ tshape($tx; $ty; $tw; 548640;
               [ para($s.heading; 20; $t.accent; true; 0; false; 0) ]; "l"; "b";
               [0, 0, 0, 0]) ]
         else [] end)
      + [ tshape($tx; ($ty + $headH); $tw; $textH;
            [ $fit.paras[] | .color = (if .level > 0 then $t.muted else $t.fg end) ]; "l"; "t";
            [0, 0, 0, 0]) ] ),
    images: [ image_of($s.image; $ix; $ty; $pw; $blockH; ($s.image.fit // "fill"); $s.image.alt) ],
    notes: ($s.notes // "")
  };

# A picture that is the page. The scrim is a flat overlay at a fixed alpha, and
# the text sits on it at full contrast rather than on the picture itself.
def slide_hero($s; $t; $idx):
  (paras_h([ para($s.title; 44; "000000"; true; 0; false; 0) ]
           + (if $s.subtitle then [ para($s.subtitle; 20; "000000"; false; 0; false; 8) ] else [] end);
           ((CW * 78) / 100 | floor); null)) as $txtH
  | (((H - $txtH) / 2) | floor) as $y0
  | {
    index: $idx, kind: "hero", dark: true,
    shapes: (
      [ tshape(MARGIN; $y0; ((CW * 78) / 100 | floor); $txtH;
          ([ para($s.title; 44; "FFFFFF"; true; 0; false; 0) ]
           + (if $s.subtitle then [ para($s.subtitle; 20; "FFFFFF"; false; 0; false; 8) ] else [] end));
          "l"; "t"; null) + {role: "title"},
        rshape(MARGIN; ($y0 + $txtH + 228600); 1097280; 45720; $t.darkAccent; null; 0)
          + {role: "decor"}
      ] ),
    images: [ image_of($s.image; 0; 0; W; H; "fill"; $s.image.alt) + {layer: "back"} ],
    scrim: {color: "000000", alpha: ($s.scrim // 0.55)},
    notes: ($s.notes // "")
  };

# A row of pictures read left to right. Each caption sits under its own picture
# and the picture height is measured from what the captions leave, so a caption
# can never land on top of the image it describes.
def slide_gallery($s; $t; $idx):
  (($s.images // []) | length) as $n
  | (if $n > 4 then 4 elif $n < 1 then 1 else $n end) as $cols
  | (((CW - ($cols - 1) * GAP) / $cols) | floor) as $cwd
  # The lead sits directly under the title, so the pictures start below it: a
  # fixed offset put the row on top of the lead line and the only visible trace
  # was the last two characters sticking out past the first picture.
  | (BODY_Y + (if $s.lead then 640080 else 91440 end)) as $y0
  | ([ range(0; $cols) | ($s.images[.].caption // "") ] | any(. != "")) as $hasCap
  | (if $hasCap then 411480 else 0 end) as $perCapH
  | (if $s.caption then 411480 else 0 end) as $deckCapH
  | ((BODY_BOTTOM - 640080 - $y0 - $perCapH - $deckCapH) | floor) as $imgH
  | {
    index: $idx, kind: "gallery", dark: false,
    shapes: (
      [ title_shape($s.title; $t) ]
      + (if $s.lead then
           [ tshape(MARGIN; (BODY_Y - 91440); CW; 548640;
               [ para($s.lead; T_LEAD; $t.muted; false; 0; false; 0) ]; "l"; "b"; null) ]
         else [] end)
      + [ range(0; $cols) as $i |
          ($s.images[$i]) as $g |
          ((MARGIN + $i * ($cwd + GAP)) | floor) as $x |
          (if ($g.caption // "") == "" then empty
           else
             tshape($x; ($y0 + $imgH + 91440); $cwd; ($perCapH - 91440);
               [ para($g.caption; T_CAPTION; $t.muted; false; 0; false; 0) ]; "l"; "t";
               [0, 0, 0, 0])
           end)
        ]
      + (if $s.caption then
           [ tshape(MARGIN; (BODY_BOTTOM - 320040); CW; 320040;
               [ para($s.caption; T_CAPTION; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end) ),
    images: [ range(0; $cols) as $i |
                ($s.images[$i]) as $g |
                image_of($g; (MARGIN + $i * ($cwd + GAP)); $y0; $cwd; $imgH;
                         ($g.fit // "fill"); $g.alt) ],
    notes: ($s.notes // "")
  };

# One sentence on a dark page. The quote and its attribution are measured and
# centred together; a fixed top anchor leaves the sentence floating high on the
# page with an equal void underneath.
def slide_quote($s; $t; $idx):
  (($s.quote | length) as $n | if $n <= 40 then 40 elif $n <= 70 then 34 elif $n <= 110 then 28 else 24 end) as $qs
  | (paras_h([ para($s.quote; $qs; "000000"; false; 0; false; 0) ]; ((CW * 9) / 10 | floor); null)) as $qH
  | (if $s.attribution then 365760 + 457200 else 0 end) as $atH
  | (((H - ($qH + $atH)) / 2) | floor) as $y0
  | {
    index: $idx, kind: "quote", dark: true,
    shapes: (
      [ tshape(MARGIN; $y0; ((CW * 9) / 10 | floor); $qH;
          [ para($s.quote; $qs; $t.darkFg; false; 0; false; 0) ]; "l"; "t"; null)
        + {role: "title"} ]
      + (if $s.attribution then
           [ tshape(MARGIN; ($y0 + $qH + 365760); CW; 457200;
               [ para("— " + $s.attribution; 16; $t.darkAccent; false; 0; false; 0) ]; "l"; "t"; null)
             + {role: "body"} ]
         else [] end) ),
    notes: ($s.notes // "")
  };

# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------
#
# A transition belongs to a slide; an animation belongs to one or more shapes on
# it. Both resolve here into shape ids so the PPTX writer only turns numbers into
# XML and the preview replays the same order.

# Each name is a element ECMA-376 defines as a direct child of p:transition. An
# invented name makes PowerPoint offer to repair the deck, so an unknown name is
# an error rather than a jump to a near-match.
def transition_names:
  ["none", "fade", "push", "wipe", "split", "cover", "cut", "dissolve",
   "checker", "blinds", "diamond", "circle", "wedge", "wheel",
   "random", "randomBar", "strips", "comb", "zoom", "newsflash",
   "plus", "pull", "morph"];

def anim_effects:
  ["appear", "fade", "wipe", "fly", "zoom", "split", "grow", "spin", "exitFade"];

def anim_triggers: ["on-click", "with-previous", "after-previous"];

def trans_of($v):
  # null inherits the deck default; false and "none" switch this slide off.
  if $v == null then null
  elif $v == false then {effect: "none", speed: "med"}
  elif ($v | type) == "string" then {effect: $v, speed: "med"}
  elif ($v | type) == "object" then
    {effect: ($v.effect // "fade"), speed: ($v.speed // "med"),
     duration: ($v.duration // 700)}
  else fail("TRANSITION_UNKNOWN"; "a transition is a name or an object") end;

def check_transition($t):
  if ($t.effect | IN(transition_names[])) then $t
  else fail("TRANSITION_UNKNOWN";
            "unknown transition '" + ($t.effect | tostring) + "'; use one of "
            + (transition_names | join(", "))) end
  | if (($t.speed // "med") | IN("slow", "med", "fast")) then . + {speed: ($t.speed // "med")}
    else fail("TRANSITION_SPEED_UNKNOWN";
              "unknown speed '" + ($t.speed | tostring) + "'; use slow, med, or fast") end;

# A role is what an author names; the id is what a slide actually has. Both are
# matched here so `target: "title"` and `target: "s3"` mean the same thing.
# A shape with no declared role is still targetable: body text is the body, a
# plain block is decoration. Without this default every animation would have to
# name a shape id, which no author can know before the deck exists.
def motion_role($sh):
  ($sh.role // (if $sh.type == "text" then "body" else "decor" end));

def motion_targets($slide):
  ([ $slide.shapes[] | select((.role // "") != "chrome")
     | {key: .id, role: motion_role(.), spid: .spid} ]
   + (if $slide.table then [{key: "table", role: "table", spid: $slide.table.spid}] else [] end)
   + (if $slide.chart then [{key: "chart", role: "chart", spid: $slide.chart.spid}] else [] end)
   + [ $slide.images[] | {key: .id, role: "image", spid: .spid} ]);

# "all" means all the content on the slide: decoration that is already behind the
# text does not need its own entrance, and animating the rule under a title makes
# the page look like it is assembling itself.
def motion_select($targets; $sel):
  (if $sel == null or $sel == "all" then [ $targets[] | select(.role != "decor" and .role != "chrome") ]
   elif ($sel | type) == "array" then [ $sel[] as $x | $targets[] | select(.role == $x or .key == $x) ]
   else [ $targets[] | select(.role == $sel or .key == $sel) ]
   end
   | map(.spid) | unique);

def anim_of($v; $targets):
  (($v.effect // "fade")) as $e
  | (if ($e | IN(anim_effects[])) then .
     else fail("ANIMATION_EFFECT_UNKNOWN";
               "unknown animation '" + ($e | tostring) + "'; use one of "
               + (anim_effects | join(", "))) end) as $_
  | (($v.trigger // "on-click")) as $trig
  | (if ($trig | IN(anim_triggers[])) then .
     else fail("ANIMATION_TRIGGER_UNKNOWN";
               "unknown trigger '" + ($trig | tostring)
               + "'; use on-click, with-previous, or after-previous") end) as $_
  | (($v.direction // "up")) as $dir
  | (if ($dir | IN("up", "down", "left", "right")) then .
     else fail("ANIMATION_DIRECTION_UNKNOWN";
               "unknown direction '" + ($dir | tostring) + "'; use up, down, left, or right") end) as $_
  | (motion_select($targets; $v.target)) as $spids
  | if ($spids | length) == 0 then
      fail("ANIMATION_TARGET_EMPTY";
           "animation '" + $e + "' targets '" + (($v.target // "all") | tostring)
           + "', which matches no shape on this slide")
    else
      {effect: $e, trigger: $trig, direction: $dir,
       duration: ($v.duration // 500), delay: ($v.delay // 0), targets: $spids}
    end;

def motion_of($slide; $deckTrans):
  (trans_of($slide.raw_transition)) as $own
  | (if $own == null then $deckTrans else $own end) as $raw
  | (if $raw == null then null else check_transition($raw) end) as $transition
  | ([ ($slide.raw_animation // [])[] | anim_of(.; motion_targets($slide)) ]) as $anims
  | {transition: $transition,
     animation: (if ($anims | length) == 0 then null else $anims end)};

def slide_of($t):
  . as $s
  | ($s.kind // "bullets") as $kind
  | (if $kind == "title" then slide_title($s; $t; 0)
     elif $kind == "section" then slide_section($s; $t; 0)
     elif $kind == "columns" then slide_columns($s; $t; 0)
     elif $kind == "stats" then slide_stats($s; $t; 0)
     elif $kind == "kpi" then slide_kpi($s; $t; 0)
     elif $kind == "compare" then slide_compare($s; $t; 0)
     elif $kind == "timeline" then slide_timeline($s; $t; 0)
     elif $kind == "table" then slide_table($s; $t; 0)
     elif $kind == "chart" then slide_chart($s; $t; 0)
     elif $kind == "image" then slide_image($s; $t; 0)
     elif $kind == "imagetext" then slide_imagetext($s; $t; 0)
     elif $kind == "hero" then slide_hero($s; $t; 0)
     elif $kind == "gallery" then slide_gallery($s; $t; 0)
     elif $kind == "quote" then slide_quote($s; $t; 0)
     elif $kind == "statement" then slide_statement($s; $t; 0)
     elif $kind == "bigstat" then slide_bigstat($s; $t; 0)
     elif $kind == "process" then slide_process($s; $t; 0)
     else slide_bullets($s; $t; 0) end)
  # Slide number and footer are added once the final index is known, in the
  # entry pipeline below, so a shape can never show the wrong page number.
  | . + {footer: ($t.footer // null),
         bg: (if .dark then $t.darkBg else $t.bg end),
         images: (.images // []),
         raw_transition: ($s.transition // null),
         raw_animation: ($s.animation // null)};

# Page number and running footer, appended after the final slide index exists.
# Returns a list of shapes to append; a caller merges with `+` on the array, not
# on the slide object, so the slide's own shapes are never replaced.
def footer_shapes($t; $i; $kind):
  if ($t.footer // null) == null or $kind == "title" or $kind == "hero" then []
  else
    (if $kind == "quote" or $kind == "section" then $t.darkMuted else $t.muted end) as $c
    | [ tshape(MARGIN; 6355080; ((CW * 85) / 100 | floor); 320040;
          [ para($t.footer; T_FOOTER; $c; false; 0; false; 0) ]; "l"; "t"; null) + {role: "chrome"},
        tshape((MARGIN + ((CW * 85) / 100 | floor)); 6355080; ((CW * 15) / 100 | floor); 320040;
          [ para((($i + 1) | tostring); T_FOOTER; $c; false; 0; false; 0) ]; "r"; "t"; null) + {role: "chrome"}
      ]
  end;

# ---------------------------------------------------------------------------
# Slide finalisation
# ---------------------------------------------------------------------------

# Ids are assigned once, here, because p:spTgt points at them: a shape and the
# animation that names it must never be numbered by two different passes. The
# ranges keep what the writer already used -- shapes from 2, table 202, chart
# 302, pictures from 602 in declaration order.
def finalize_slide($i; $deckTrans; $t):
  . as $sl
  | ($sl.shapes + footer_shapes($t; $i; $sl.kind)) as $all
  | ($all | to_entries
     | map(.value + {id: ("s" + ((.key + 1) | tostring)), spid: (2 + .key)})) as $shapes
  | ($sl.images | to_entries
     | map(.value + {id: ("i" + ((.key + 1) | tostring)), spid: (602 + .key)})) as $images
  | $sl
  | .shapes = $shapes
  | .images = $images
  | (if .table then .table += {spid: 202} else . end)
  | (if .chart then .chart += {spid: 302} else . end)
  | . + {index: $i}
  | . + motion_of(.; $deckTrans);

# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

. as $spec
| (($spec.theme // "ink")) as $themeName
| (if ($themeName | type) == "object"
   then
     (palette($themeName.base // "ink")) as $base
     | if $base == null then error("unknown palette: " + ($themeName.base // "ink")) else . end
     | ($base as $b
        | reduce ("bg", "fg", "muted", "accent", "accent2", "tint", "surface", "line",
                  "darkBg", "darkFg", "darkMuted", "darkAccent", "darkAccent2",
                  "darkTint", "darkSurface") as $k
            ($b; if ($themeName[$k] // null) == null then . else . + {($k): $themeName[$k]} end))
   else
     (palette($themeName)) as $p
     | if $p == null then error("unknown palette: " + $themeName) else $p end
   end) as $t0
| ($t0 + {
    footer: ($spec.footer // null),
    fonts: {
      latin: ($spec.fonts.latin // "Pretendard"),
      eastAsian: ($spec.fonts.eastAsian // ($spec.fonts.latin // "Pretendard")),
      mono: ($spec.fonts.mono // "SF Mono")
    }
  }) as $t
| (if $spec.transition == null then null
   else check_transition(trans_of($spec.transition)) end) as $deckTrans
| {
    title: ($spec.title // ""),
    author: ($spec.author // ""),
    lang: ($spec.lang // "ko"),
    footer: ($spec.footer // null),
    theme: $t,
    size: {w: W, h: H},
    slides: ([ $spec.slides[] | slide_of($t) ] | to_entries | map(
      .key as $i
      | .value
      | finalize_slide($i; $deckTrans; $t)))
  }

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

def palette($name):
  {
    ink: {
      bg: "FFFFFF", fg: "12171D", muted: "66707D", accent: "C2410C",
      surface: "F2F4F7", line: "D7DCE4",
      darkBg: "12171D", darkFg: "F7F8FA", darkMuted: "A8B2BF", darkAccent: "F97316",
      darkSurface: "1E252E"
    },
    paper: {
      bg: "FBF8F3", fg: "1A1613", muted: "6E655C", accent: "9A3412",
      surface: "F0E9DF", line: "DED3C6",
      darkBg: "241E19", darkFg: "FBF8F3", darkMuted: "BCAE9F", darkAccent: "E8A15C",
      darkSurface: "322A23"
    },
    navy: {
      bg: "FFFFFF", fg: "0B1B33", muted: "5A6B84", accent: "1F5DA8",
      surface: "EDF2F9", line: "CFDAEA",
      darkBg: "0B1B33", darkFg: "F5F8FC", darkMuted: "A3B4CC", darkAccent: "6EA8E8",
      darkSurface: "162944"
    },
    forest: {
      bg: "FFFFFF", fg: "10231A", muted: "5A6B62", accent: "1F6B4A",
      surface: "EDF4EF", line: "C9DCCF",
      darkBg: "0F2A1E", darkFg: "F3F8F5", darkMuted: "A5C0B0", darkAccent: "5BC493",
      darkSurface: "183A2A"
    },
    mono: {
      bg: "FFFFFF", fg: "111111", muted: "6E6E6E", accent: "111111",
      surface: "F2F2F2", line: "D8D8D8",
      darkBg: "111111", darkFg: "F7F7F7", darkMuted: "A9A9A9", darkAccent: "FFFFFF",
      darkSurface: "1F1F1F"
    }
  }[$name];

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
# The renderer breaks lines itself; this is only used to size a card, never to
# place text.
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

# ---------------------------------------------------------------------------
# Slide kinds
# ---------------------------------------------------------------------------

def slide_title($s; $t; $idx):
  {
    index: $idx, kind: "title", dark: true,
    shapes: (
      [ tshape(MARGIN; 1645920; CW; 1828800;
          ([ para($s.title; 44; $t.darkFg; true; 0; false; 0) ]
           + (if $s.subtitle then [ para($s.subtitle; 20; $t.darkMuted; false; 0; false; 8) ] else [] end));
          "l"; "b"; null),
        rshape(MARGIN; 3566160; 1097280; 45720; $t.darkAccent; null; 0)
      ]
      + (if $s.meta then
           [ tshape(MARGIN; 5760720; CW; 457200;
               [ para($s.meta; 13; $t.darkMuted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end) ),
    notes: ($s.notes // "")
  };

def slide_section($s; $t; $idx):
  {
    index: $idx, kind: "section", dark: true,
    shapes: (
      (if $s.number then
         [ tshape(MARGIN; 1600200; CW; 640080; [ para($s.number; 15; $t.darkAccent; true; 0; false; 0) ]; "l"; "b"; null) ]
       else [] end)
      + [ tshape(MARGIN; 2331720; CW; 868680; [ para($s.title; 36; $t.darkFg; true; 0; false; 0) ]; "l"; "b"; null) ]
      + (if $s.subtitle then
           [ tshape(MARGIN; 3291840; ((CW * 4) / 5 | floor); 640080;
               [ para($s.subtitle; 17; $t.darkMuted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end) ),
    notes: ($s.notes // "")
  };

def slide_bullets($s; $t; $idx):
  (if $s.lead then BODY_Y + 640080 else BODY_Y end) as $y0
  | {
    index: $idx, kind: "bullets", dark: false,
    shapes: (
      [ tshape(MARGIN; TITLE_Y; CW; TITLE_H; [ para($s.title; 30; $t.fg; true; 0; false; 0) ]; "l"; "b"; null) ]
      + (if $s.lead then
           [ tshape(MARGIN; BODY_Y; CW; 548640; [ para($s.lead; 17; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end)
      + [ tshape(MARGIN; $y0; ((CW * 86) / 100 | floor); (BODY_BOTTOM - $y0);
          bullets_of($s.bullets; 18; $t.fg; $t.muted); "l"; "t"; null) ] ),
    notes: ($s.notes // "")
  };

def slide_columns($s; $t; $idx):
  ($s.columns | length) as $n
  | (if $n > 3 then 3 else $n end) as $cols
  | 304800 as $gap
  | (((CW - ($cols - 1) * $gap) / $cols) | floor) as $cwd
  # Card height follows the tallest column: heading band, the wrapped bullet
  # text at 15pt with its per-paragraph spacing, then the bottom pad. Clamped
  # to the body so a long column still fails the overflow check instead of
  # pushing the card off the slide.
  | (((($cwd - 365760 - 342900) / 190500) | floor)) as $emAvail
  | ([ range(0; $cols) as $i |
       ($s.columns[$i].bullets // []) as $bl
       | ([ $bl[] |
            (if type == "string" then {text: ., level: 0, space: 6}
             else {text: (.text // ""), level: (.level // 0),
                   space: (if .space != null then .space elif (.level // 0) > 0 then 0 else 6 end)} end)
            | (line_count(.text;
                 ($emAvail - (if .level > 0 then 2 else 0 end))) as $lines
              | $lines * 228600 + (.space * 12700))
          ] | add // 0)
     ] | max // 0) as $bodyNeed
  | (777240 + $bodyNeed + 182880) as $wanted
  | (if $wanted < 1600200 then 1600200 elif $wanted > BODY_H then BODY_H else $wanted end) as $cardH
  | {
    index: $idx, kind: "columns", dark: false,
    shapes: (
      [ tshape(MARGIN; TITLE_Y; CW; TITLE_H; [ para($s.title; 30; $t.fg; true; 0; false; 0) ]; "l"; "b"; null) ]
      + [ range(0; $cols) as $i |
          ($s.columns[$i]) as $c |
          ((MARGIN + $i * ($cwd + $gap)) | floor) as $x |
          rshape($x; BODY_Y; $cwd; $cardH; $t.surface; null; 0),
          tshape($x; (BODY_Y + 274320); $cwd; 457200;
            [ para($c.heading; 17; $t.accent; true; 0; false; 0) ]; "l"; "t";
            [182880, 0, 182880, 0]),
          tshape($x; (BODY_Y + 777240); $cwd; ($cardH - 868680);
            bullets_of(($c.bullets // []); 15; $t.fg; $t.muted); "l"; "t";
            [182880, 0, 182880, 0])
        ] ),
    notes: ($s.notes // "")
  };

def slide_stats($s; $t; $idx):
  ($s.stats | length) as $n
  | (if $n > 4 then 4 elif $n < 1 then 1 else $n end) as $cols
  | 304800 as $gap
  | (((CW - ($cols - 1) * $gap) / $cols) | floor) as $cwd
  | {
    index: $idx, kind: "stats", dark: false,
    shapes: (
      [ tshape(MARGIN; TITLE_Y; CW; TITLE_H; [ para($s.title; 30; $t.fg; true; 0; false; 0) ]; "l"; "b"; null) ]
      + [ range(0; $cols) as $i |
          ($s.stats[$i]) as $st |
          ((MARGIN + $i * ($cwd + $gap)) | floor) as $x |
          rshape($x; BODY_Y; $cwd; 2286000; $t.surface; null; 0),
          tshape($x; (BODY_Y + 365760); $cwd; 1005840;
            [ para($st.value; 46; $t.accent; true; 0; false; 0) ]; "l"; "b";
            [182880, 0, 182880, 0]),
          tshape($x; (BODY_Y + 1417320); $cwd; 457200;
            [ para($st.label; 15; $t.fg; false; 0; false; 0) ]; "l"; "t";
            [182880, 0, 182880, 0])
        ]
      + (if ($s.stats[0].note) then
           [ range(0; $cols) as $i |
             ($s.stats[$i]) as $st |
             ((MARGIN + $i * ($cwd + $gap)) | floor) as $x |
             (if $st.note then
                tshape($x; (BODY_Y + 1874520); $cwd; 320040;
                  [ para($st.note; 12; $t.muted; false; 0; false; 0) ]; "l"; "t";
                  [182880, 0, 182880, 0])
              else empty end)
           ]
         else [] end) ),
    notes: ($s.notes // "")
  };

def slide_table($s; $t; $idx):
  ($s.table.columns | length) as $ncols
  | (($s.table.rows | length) + 1) as $nrows
  | (if $s.table.caption then 457200 else 0 end) as $capH
  | (((BODY_H - $capH) / $nrows) | floor) as $rowH
  | ($rowH | if . < 320040 then 320040 elif . > 731520 then 731520 else . end) as $rh
  | {
    index: $idx, kind: "table", dark: false,
    shapes:
      ([ tshape(MARGIN; TITLE_Y; CW; TITLE_H; [ para($s.title; 30; $t.fg; true; 0; false; 0) ]; "l"; "b"; null) ]
       + (if $s.table.caption then
            [ tshape(MARGIN; (BODY_Y + $rh * $nrows + 91440); CW; 320040;
                [ para($s.table.caption; 12; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
          else [] end)),
    table: {
      x: MARGIN, y: BODY_Y, cx: CW, cy: ($rh * $nrows),
      colWidths: [ range(0; $ncols) | ((CW / $ncols) | floor) ],
      rowHeights: [ range(0; $nrows) | $rh ],
      header: $s.table.columns,
      rows: $s.table.rows,
      headerFill: $t.accent, headerColor: "FFFFFF",
      bodyFill: $t.bg, altFill: $t.surface, bodyColor: $t.fg,
      size: 13
    },
    notes: ($s.notes // "")
  };

def slide_chart($s; $t; $idx):
  ((CW * 86) / 100 | floor) as $chw
  | ((BODY_H - 1371600) | floor) as $chh
  | {
    index: $idx, kind: "chart", dark: false,
    shapes:
      ([ tshape(MARGIN; TITLE_Y; CW; TITLE_H; [ para($s.title; 30; $t.fg; true; 0; false; 0) ]; "l"; "b"; null) ]
       + (if $s.chart.caption then
            [ tshape(MARGIN; (BODY_Y + $chh + 91440); CW; 320040;
                [ para($s.chart.caption; 12; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
          else [] end)),
    chart: {
      x: ((W - $chw) / 2 | floor), y: BODY_Y, cx: $chw, cy: $chh,
      type: ($s.chart.type // "column"),
      categories: $s.chart.categories,
      series: $s.chart.series,
      colors: [ $t.accent, $t.muted, $t.line, $t.surface ],
      fg: $t.fg, muted: $t.muted, bg: $t.bg
    },
    notes: ($s.notes // "")
  };

def slide_image($s; $t; $idx):
  ($s.image.aspect // 1.7777778) as $aspect
  | ($s.image.height // 4206240) as $ih0
  | ($ih0 * $aspect | floor) as $iw0
  | (if $iw0 > CW then (CW / $aspect | floor) else $ih0 end) as $h
  | (if $iw0 > CW then CW else $iw0 end) as $w
  | (if $s.caption then 411480 else 0 end) as $capH
  | ((BODY_BOTTOM - BODY_Y) - $capH) as $areaH
  | (if $h > $areaH then ($areaH | floor) else $h end) as $fh
  | (if $h > $areaH then (($areaH * $aspect) | floor) else $w end) as $fw
  | {
    index: $idx, kind: "image", dark: false,
    shapes: (
      (if $s.title then
         [ tshape(MARGIN; TITLE_Y; CW; TITLE_H; [ para($s.title; 30; $t.fg; true; 0; false; 0) ]; "l"; "b"; null) ]
       else [] end)
      + (if $s.caption then
           [ tshape(MARGIN; (BODY_Y + $areaH + 91440); CW; 320040;
               [ para((if $s.image.credit then $s.caption + "  ·  " + $s.image.credit else $s.caption end);
                       12; $t.muted; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end) ),
    image: {
      x: (((W - $fw) / 2) | floor),
      y: ((BODY_Y + ($areaH - $fh) / 2) | floor),
      cx: $fw, cy: $fh,
      path: $s.image.path,
      ext: (($s.image.ext // ($s.image.path | split(".") | .[-1])) | ascii_downcase)
    },
    notes: ($s.notes // "")
  };

def slide_quote($s; $t; $idx):
  {
    index: $idx, kind: "quote", dark: true,
    shapes: (
      [ tshape(MARGIN; 1828800; ((CW * 9) / 10 | floor); 2286000;
          [ para($s.quote; 32; $t.darkFg; false; 0; false; 0) ]; "l"; "b"; null) ]
      + (if $s.attribution then
           [ tshape(MARGIN; 4206240; CW; 457200;
               [ para("— " + $s.attribution; 16; $t.darkAccent; false; 0; false; 0) ]; "l"; "t"; null) ]
         else [] end) ),
    notes: ($s.notes // "")
  };

def slide_of($t):
  . as $s
  | ($s.kind // "bullets") as $kind
  | (if $kind == "title" then slide_title($s; $t; 0)
     elif $kind == "section" then slide_section($s; $t; 0)
     elif $kind == "columns" then slide_columns($s; $t; 0)
     elif $kind == "stats" then slide_stats($s; $t; 0)
     elif $kind == "table" then slide_table($s; $t; 0)
     elif $kind == "chart" then slide_chart($s; $t; 0)
     elif $kind == "image" then slide_image($s; $t; 0)
     elif $kind == "quote" then slide_quote($s; $t; 0)
     else slide_bullets($s; $t; 0) end)
  # Slide number and footer are added once the final index is known, in the
  # entry pipeline below, so a shape can never show the wrong page number.
  | . + {footer: ($t.footer // null),
         bg: (if .dark then $t.darkBg else $t.bg end)};

# Page number and running footer, appended after the final slide index exists.
# Returns a list of shapes to append; a caller merges with `+` on the array, not
# on the slide object, so the slide's own shapes are never replaced.
def footer_shapes($t; $i; $kind):
  if ($t.footer // null) == null or $kind == "title" then []
  else
    (if $kind == "quote" or $kind == "section" then $t.darkMuted else $t.muted end) as $c
    | [ tshape(MARGIN; 6355080; ((CW * 85) / 100 | floor); 320040;
          [ para($t.footer; 11; $c; false; 0; false; 0) ]; "l"; "t"; null),
        tshape((MARGIN + ((CW * 85) / 100 | floor)); 6355080; ((CW * 15) / 100 | floor); 320040;
          [ para((($i + 1) | tostring); 11; $c; false; 0; false; 0) ]; "r"; "t"; null)
      ]
  end;

# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

. as $spec
| (($spec.theme // "ink")) as $themeName
| (if ($themeName | type) == "object"
   then
     (palette($themeName.base // "ink")) as $base
     | if $base == null then error("unknown palette: " + ($themeName.base // "ink")) else . end
     | ($base
        + {bg: ($themeName.bg // $base.bg), fg: ($themeName.fg // $base.fg),
           accent: ($themeName.accent // $base.accent), muted: ($themeName.muted // $base.muted),
           surface: ($themeName.surface // $base.surface), line: ($themeName.line // $base.line)})
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
      | .shapes += footer_shapes($t; $i; .kind)
      # A stable id lets a layout finding name the shape it is about.
      | .shapes |= [ to_entries[] | .value + {id: ("s" + ((.key + 1) | tostring))} ]
      | . + {index: $i}))
  }

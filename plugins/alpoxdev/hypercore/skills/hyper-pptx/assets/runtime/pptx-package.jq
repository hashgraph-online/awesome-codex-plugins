# pptx-package.jq — turn a resolved deck into OOXML parts.
#
# Input : resolved deck (output of layout.jq)
# Output: {"parts": [...], "media": [...], "workbooks": [...],
#          "presentation": ..., "presentationRels": ..., "contentTypes": ...,
#          "rootRels": ...}
#
# Only DrawingML that Office readers require is emitted. Every slide carries
# absolute geometry, so the package needs one blank layout and no placeholder
# inheritance: what the preview shows is what PowerPoint opens.
#
# Charts are real chart parts with cached series values plus an embedded
# workbook. Without the workbook a chart still renders, but "Edit Data" in
# PowerPoint has no sheet to open; with it the deck is editable the way the
# reader expects. The workbook is built by render-deck.sh from
# `workbooks[]`, because zip lives there.

def xesc:
  tostring
  | gsub("&"; "&amp;")
  | gsub("<"; "&lt;")
  | gsub(">"; "&gt;")
  | gsub("\""; "&quot;");

def decl: "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n";

def relsOpen: "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">";

def emu($x): ($x | floor | tostring);

def sz($pt): ($pt * 100 | floor | tostring);

def clr($hex): "<a:srgbClr val=\"" + ($hex | ascii_upcase) + "\"/>";

def solidFill($hex): "<a:solidFill>" + clr($hex) + "</a:solidFill>";

# A translucent fill is used for the hero scrim: a flat overlay at a fixed alpha
# keeps the title at full contrast regardless of the picture underneath.
def alphaFill($hex; $alpha):
  "<a:solidFill><a:srgbClr val=\"" + ($hex | ascii_upcase) + "\"><a:alpha val=\""
  + ((($alpha * 100000) | floor) | tostring) + "\"/></a:srgbClr></a:solidFill>";

def lang: "ko-KR";

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

def runProps($p; $fonts):
  "<a:rPr lang=\"" + lang + "\" sz=\"" + sz($p.size) + "\""
  + (if $p.bold then " b=\"1\"" else "" end)
  + " dirty=\"0\">"
  + solidFill($p.color)
  + "<a:latin typeface=\"" + ($fonts.latin | xesc) + "\"/>"
  + "<a:ea typeface=\"" + ($fonts.eastAsian | xesc) + "\"/>"
  + "</a:rPr>";

def paraProps($p):
  "<a:pPr"
  + (if $p.align == "c" then " algn=\"ctr\"" elif $p.align == "r" then " algn=\"r\"" else "" end)
  + " marL=\"" + (if $p.bullet == false then (($p.level * 342900) | tostring)
                  elif $p.level > 0 then "685800" else "342900" end) + "\""
  + " indent=\"" + (if $p.bullet == false then "0"
                    elif $p.level > 0 then "-285750" else "-342900" end) + "\">"
  + (if ($p.spaceBefore // 0) > 0
     then "<a:spcBef><a:spcPts val=\"" + (($p.spaceBefore * 100) | floor | tostring) + "\"/></a:spcBef>"
     else "<a:spcBef><a:spcPts val=\"0\"/></a:spcBef>" end)
  + (if $p.bullet == false then "<a:buNone/>"
     elif ($p.level // 0) > 0 then "<a:buChar char=\"–\"/>"
     else "<a:buChar char=\"•\"/>" end)
  + "</a:pPr>";

# One paragraph = one run. The writer never splits a sentence across runs,
# so a later text edit in PowerPoint cannot corrupt half a word.
def para($p; $fonts):
  "<a:p>" + paraProps($p) + "<a:r>" + runProps($p; $fonts)
  + "<a:t>" + ($p.text | xesc) + "</a:t></a:r>"
  + "<a:endParaRPr lang=\"" + lang + "\" sz=\"" + sz($p.size) + "\" dirty=\"0\"/>"
  + "</a:p>";

def bodyPr($anchor; $inset):
  "<a:bodyPr wrap=\"square\""
  + " lIns=\"" + (($inset[0]) | tostring) + "\""
  + " tIns=\"" + (($inset[1]) | tostring) + "\""
  + " rIns=\"" + (($inset[2]) | tostring) + "\""
  + " bIns=\"" + (($inset[3]) | tostring) + "\""
  + " anchor=\"" + (if $anchor == "b" then "b" elif $anchor == "ctr" then "ctr" else "t" end) + "\">"
  + "<a:noAutofit/></a:bodyPr>";

def txBody($shape; $fonts):
  "<p:txBody>" + bodyPr($shape.anchor; $shape.inset) + "<a:lstStyle/>"
  + ([ $shape.paragraphs[] | para(. + {align: $shape.align}; $fonts) ] | join(""))
  + "</p:txBody>";

def xfrm($x; $y; $cx; $cy):
  "<a:xfrm><a:off x=\"" + emu($x) + "\" y=\"" + emu($y) + "\"/>"
  + "<a:ext cx=\"" + emu($cx) + "\" cy=\"" + emu($cy) + "\"/></a:xfrm>";

def textShape($s; $id; $fonts):
  "<p:sp><p:nvSpPr><p:cNvPr id=\"" + ($id | tostring) + "\" name=\"Text " + ($id | tostring) + "\"/>"
  + "<p:cNvSpPr txBox=\"1\"/><p:nvPr/></p:nvSpPr><p:spPr>"
  + xfrm($s.x; $s.y; $s.cx; $s.cy)
  + "<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom><a:noFill/>"
  + "<a:ln><a:noFill/></a:ln></p:spPr>"
  + txBody($s; $fonts) + "</p:sp>";

# A linear gradient is two stops on one direction. PowerPoint measures the angle
# counter-clockwise from the positive x axis, so a top-to-bottom page band is
# 90 degrees and a left-to-right one is 0.
def gradFill($g):
  "<a:gradFill rotWithShape=\"1\"><a:gsLst>"
  + "<a:gs pos=\"0\">" + clr($g.from) + "</a:gs>"
  + "<a:gs pos=\"100000\">" + clr($g.to) + "</a:gs>"
  + "</a:gsLst><a:lin ang=\"" + (((($g.angle // 90)) * 60000) | floor | tostring) + "\" scaled=\"1\"/>"
  + "</a:gradFill>";

def shapeGeom($s):
  "<a:prstGeom prst=\"" + (if $s.type == "ellipse" then "ellipse"
                            elif ($s.radius // 0) > 0 then "roundRect" else "rect" end) + "\"><a:avLst/></a:prstGeom>";

def rectShape($s; $id):
  "<p:sp><p:nvSpPr><p:cNvPr id=\"" + ($id | tostring) + "\" name=\"Block " + ($id | tostring) + "\"/>"
  + "<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>"
  + xfrm($s.x; $s.y; $s.cx; $s.cy)
  + shapeGeom($s)
  + (if $s.gradient then gradFill($s.gradient)
     elif ($s.alpha // 0) > 0 then alphaFill($s.fill; $s.alpha)
     else solidFill($s.fill) end)
  + (if $s.line then "<a:ln w=\"12700\">" + solidFill($s.line) + "</a:ln>" else "<a:ln><a:noFill/></a:ln>" end)
  + "</p:spPr>"
  + "<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang=\"" + lang + "\"/></a:p></p:txBody></p:sp>";

# An ellipse is a rect with a different preset geometry, so it shares the shape
# writer; a separate name documents intent at the call site.
def ellipseShape($s; $id): rectShape($s; $id);

# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def cell($text; $fill; $color; $bold; $size; $fonts):
  "<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr/><a:r>"
  + "<a:rPr lang=\"" + lang + "\" sz=\"" + sz($size) + "\"" + (if $bold then " b=\"1\"" else "" end) + " dirty=\"0\">"
  + solidFill($color)
  + "<a:latin typeface=\"" + ($fonts.latin | xesc) + "\"/>"
  + "<a:ea typeface=\"" + ($fonts.eastAsian | xesc) + "\"/>"
  + "</a:rPr><a:t>" + (($text // "") | tostring | xesc) + "</a:t></a:r></a:p></a:txBody>"
  # CT_TableCellProperties is a sequence: the borders come before the fill.
  # A reader that follows the schema rejects the whole part when they swap.
  + "<a:tcPr marL=\"91440\" marR=\"91440\" marT=\"45720\" marB=\"45720\" anchor=\"ctr\">"
  + "<a:lnB w=\"6350\"><a:noFill/></a:lnB>" + solidFill($fill) + "</a:tcPr></a:tc>";

def tableFrame($t; $id; $fonts):
  "<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id=\"" + ($id | tostring) + "\" name=\"Table " + ($id | tostring) + "\"/>"
  + "<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp=\"1\"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>"
  + "<p:xfrm><a:off x=\"" + emu($t.x) + "\" y=\"" + emu($t.y) + "\"/>"
  + "<a:ext cx=\"" + emu($t.cx) + "\" cy=\"" + emu($t.cy) + "\"/></p:xfrm>"
  + "<a:graphic><a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/table\">"
  + "<a:tbl><a:tblPr firstRow=\"1\" bandRow=\"1\"/><a:tblGrid>"
  + ([ $t.colWidths[] | "<a:gridCol w=\"" + emu(.) + "\"/>" ] | join(""))
  + "</a:tblGrid>"
  + "<a:tr h=\"" + emu($t.rowHeights[0]) + "\">"
  + ([ $t.header[] | cell(.; $t.headerFill; $t.headerColor; true; $t.size; $fonts) ] | join(""))
  + "</a:tr>"
  + ([ range(0; ($t.rows | length)) as $r |
       "<a:tr h=\"" + emu($t.rowHeights[$r + 1]) + "\">"
       + ([ $t.rows[$r][] |
            cell(.;
              (if $r % 2 == 1 then $t.altFill else $t.bodyFill end);
              $t.bodyColor; false; $t.size; $fonts) ] | join(""))
       + "</a:tr>" ] | join(""))
  + "</a:tbl></a:graphicData></a:graphic></p:graphicFrame>";

# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------

# Numerator of a crop fraction as an OOXML percentage. srcRect takes
# "12.5%" or thousandths; the schema wants the percent form.
def pct($v):
  (($v * 1000 | floor) / 1000) as $r
  | ($r | tostring) + "%";

def pic($p; $id; $rid):
  "<p:pic><p:nvPicPr>"
  + "<p:cNvPr id=\"" + ($id | tostring) + "\" name=\"Picture " + ($id | tostring) + "\""
  + (if ($p.alt // "") != "" then " descr=\"" + ($p.alt | xesc) + "\"" else "" end) + "/>"
  + "<p:cNvPicPr><a:picLocks noChangeAspect=\"1\"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>"
  + "<p:blipFill><a:blip r:embed=\"" + $rid + "\"/>"
  + (if (($p.crop.l // 0) != 0) or (($p.crop.t // 0) != 0) or (($p.crop.r // 0) != 0) or (($p.crop.b // 0) != 0)
     then "<a:srcRect l=\"" + pct($p.crop.l) + "\" t=\"" + pct($p.crop.t)
          + "\" r=\"" + pct($p.crop.r) + "\" b=\"" + pct($p.crop.b) + "\"/>"
     else "" end)
  + "<a:stretch><a:fillRect/></a:stretch></p:blipFill>"
  + "<p:spPr>" + xfrm($p.x; $p.y; $p.cx; $p.cy)
  + "<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></p:spPr></p:pic>";

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

# OOXML chart element order is schema-fixed: a child in the wrong position makes
# PowerPoint reject the part. Every writer below emits children in the order the
# ISO 29500 schema declares.

def numFmt($fmt; $linked): "<c:numFmt formatCode=\"" + ($fmt | xesc) + "\" sourceLinked=\"" + $linked + "\"/>";

def txPrBody($color; $size; $fonts):
  "<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz=\"" + sz($size) + "\">"
  + solidFill($color)
  + "<a:latin typeface=\"" + ($fonts.latin | xesc) + "\"/>"
  + "<a:ea typeface=\"" + ($fonts.eastAsian | xesc) + "\"/>"
  + "</a:defRPr></a:pPr><a:endParaRPr lang=\"" + lang + "\"/></a:p></c:txPr>";

def chartTitle($text; $color; $size; $fonts):
  "<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz=\""
  + sz($size) + "\" b=\"0\">" + solidFill($color)
  + "<a:latin typeface=\"" + ($fonts.latin | xesc) + "\"/></a:defRPr></a:pPr>"
  + "<a:r><a:rPr lang=\"" + lang + "\" sz=\"" + sz($size) + "\" dirty=\"0\">" + solidFill($color)
  + "<a:latin typeface=\"" + ($fonts.latin | xesc) + "\"/></a:rPr><a:t>" + ($text | xesc) + "</a:t></a:r>"
  + "<a:endParaRPr lang=\"" + lang + "\"/></a:p></c:rich></c:tx>"
  + "<c:overlay val=\"0\"/></c:title>";

def numCache($vals; $fmt):
  "<c:numCache><c:formatCode>" + ($fmt | xesc) + "</c:formatCode>"
  + "<c:ptCount val=\"" + ($vals | length | tostring) + "\"/>"
  + ([ range(0; ($vals | length)) as $i |
       "<c:pt idx=\"" + ($i | tostring) + "\"><c:v>" + ($vals[$i] | tostring) + "</c:v></c:pt>" ] | join(""))
  + "</c:numCache>";

def strCache($vals):
  "<c:strCache><c:ptCount val=\"" + ($vals | length | tostring) + "\"/>"
  + ([ range(0; ($vals | length)) as $i |
       "<c:pt idx=\"" + ($i | tostring) + "\"><c:v>" + ($vals[$i] | tostring | xesc) + "</c:v></c:pt>" ] | join(""))
  + "</c:strCache>";

# Column letter for a 1-based index; a deck never needs more than 26 series.
def colLetter($i): ("ABCDEFGHIJKLMNOPQRSTUVWXYZ" | .[$i - 1:$i]) // "A";

def dLbls($c; $pos):
  "<c:dLbls>"
  + (if ($c.numberFormat // "General") != "General" then numFmt($c.numberFormat; "0") else "" end)
  + txPrBody($c.fg; 12; {latin: "+mn-lt", eastAsian: "+mn-ea"})
  + (if $pos then "<c:dLblPos val=\"" + $pos + "\"/>" else "" end)
  + "<c:showLegendKey val=\"0\"/><c:showVal val=\"1\"/><c:showCatName val=\"0\"/>"
  + "<c:showSerName val=\"0\"/><c:showPercent val=\"0\"/><c:showBubbleSize val=\"0\"/>"
  + "</c:dLbls>";

def serShared($s; $i):
  "<c:idx val=\"" + ($i | tostring) + "\"/><c:order val=\"" + ($i | tostring) + "\"/>"
  + "<c:tx><c:strRef><c:f>"
  + ("Sheet1!$" + colLetter($i + 2) + "$1")
  + "</c:f>" + strCache([$s.name]) + "</c:strRef></c:tx>";

def serFill($s; $i; $colors):
  ($colors[$i % ($colors | length)]) as $c
  | "<c:spPr>" + solidFill($c)
  + "<a:ln w=\"28575\"><a:solidFill>" + clr($c) + "</a:solidFill></a:ln></c:spPr>";

def catRef($c):
  "<c:cat><c:strRef><c:f>Sheet1!$A$2:$A$" + (($c.categories | length) + 1 | tostring) + "</c:f>"
  + strCache($c.categories) + "</c:strRef></c:cat>";

def valRef($s; $i; $fmt):
  (colLetter($i + 2)) as $col
  | "<c:val><c:numRef><c:f>Sheet1!$" + $col + "$2:$" + $col + "$"
  + (($s.values | length) + 1 | tostring) + "</c:f>"
  + numCache($s.values; $fmt) + "</c:numRef></c:val>";

def barSer($c; $s; $i; $fmt):
  "<c:ser>" + serShared($s; $i) + serFill($s; $i; $c.colors)
  + (if $c.labels then dLbls($c; "outEnd") else "" end)
  + catRef($c) + valRef($s; $i; $fmt) + "</c:ser>";

def lineSer($c; $s; $i; $fmt):
  "<c:ser>" + serShared($s; $i)
  + "<c:spPr><a:ln w=\"28575\" cap=\"rnd\">" + solidFill($c.colors[$i % ($c.colors | length)])
  + "<a:round/></a:ln></c:spPr>"
  + "<c:marker><c:symbol val=\"circle\"/><c:size val=\"6\"/><c:spPr>"
  + solidFill($c.colors[$i % ($c.colors | length)]) + "<a:ln w=\"9525\">"
  + solidFill($c.colors[$i % ($c.colors | length)]) + "</a:ln></c:spPr></c:marker>"
  + (if $c.labels then dLbls($c; "t") else "" end)
  + catRef($c) + valRef($s; $i; $fmt) + "<c:smooth val=\"0\"/></c:ser>";

def areaSer($c; $s; $i; $fmt):
  "<c:ser>" + serShared($s; $i) + serFill($s; $i; $c.colors)
  + (if $c.labels then dLbls($c; "ctr") else "" end)
  + catRef($c) + valRef($s; $i; $fmt) + "</c:ser>";

# Pie and doughnut colour by point, so each slice names its own fill.
def pieSer($c; $s; $i; $fmt):
  "<c:ser>" + serShared($s; $i)
  + ([ range(0; ($s.values | length)) as $k |
       "<c:dPt><c:idx val=\"" + ($k | tostring) + "\"/><c:bubble3D val=\"0\"/><c:spPr>"
       + solidFill($c.colors[$k % ($c.colors | length)])
       + "<a:ln w=\"19050\">" + solidFill($c.bg) + "</a:ln></c:spPr></c:dPt>" ] | join(""))
  + (if $c.labels then dLbls($c; "bestFit") else "" end)
  + catRef($c) + valRef($s; $i; $fmt) + "</c:ser>";

# The x values of a scatter series. The spec carries one number per point and a
# category label for it, so the label is the x when it parses as a number and
# the position is the x when it does not. Using the value for both axes would
# draw a diagonal, which is never what the author meant.
def scatterXs($c; $n):
  ([ ($c.categories // [])[0:$n][] | (tostring | tonumber?) ] | length) as $num
  | if $num == $n and $n > 0 then
      [ ($c.categories // [])[0:$n][] | (tostring | tonumber) ]
    else [ range(1; $n + 1) ] end;

def scatterSer($c; $s; $i; $fmt):
  ($c.colors[$i % ($c.colors | length)]) as $col
  | (scatterXs($c; ($s.values | length))) as $xs
  | "<c:ser>" + serShared($s; $i)
  + "<c:spPr><a:ln w=\"19050\"><a:noFill/></a:ln></c:spPr>"
  + "<c:marker><c:symbol val=\"circle\"/><c:size val=\"7\"/><c:spPr>" + solidFill($col) + "</c:spPr></c:marker>"
  + (if $c.labels then dLbls($c; "r") else "" end)
  + "<c:xVal><c:numRef><c:f>Sheet1!$A$2:$A$" + (($s.values | length) + 1 | tostring) + "</c:f>"
  + numCache($xs; $fmt) + "</c:numRef></c:xVal>"
  + "<c:yVal><c:numRef><c:f>Sheet1!$" + colLetter($i + 2) + "$2:$" + colLetter($i + 2) + "$"
  + (($s.values | length) + 1 | tostring) + "</c:f>"
  + numCache($s.values; $fmt) + "</c:numRef></c:yVal>"
  + "<c:smooth val=\"0\"/></c:ser>";

def gridlines($c):
  "<c:majorGridlines><c:spPr><a:ln w=\"6350\">" + solidFill($c.line) + "</a:ln></c:spPr></c:majorGridlines>";

# The secondary value axis of a combo. It shares the category axis and draws no
# gridlines, so two scales do not produce two sets of horizontal rules.
def valAx2($c; $fonts; $pos):
  "<c:valAx><c:axId val=\"" + ($c.axVal2 // "333333333") + "\"/>"
  + "<c:scaling><c:orientation val=\"minMax\"/></c:scaling>"
  + "<c:delete val=\"0\"/><c:axPos val=\"" + $pos + "\"/>"
  + numFmt($c.numberFormat; "1")
  + "<c:tickLblPos val=\"nextTo\"/>"
  + "<c:spPr><a:ln><a:noFill/></a:ln></c:spPr>"
  + txPrBody($c.muted; 12; $fonts)
  + "<c:crossAx val=\"" + $c.axCat + "\"/><c:crosses val=\"max\"/>"
  + "<c:crossBetween val=\"between\"/></c:valAx>";

def catAx($c; $fonts; $pos; $crosses):
  "<c:catAx><c:axId val=\"" + $c.axCat + "\"/>"
  + "<c:scaling><c:orientation val=\"minMax\"/></c:scaling>"
  + "<c:delete val=\"0\"/><c:axPos val=\"" + $pos + "\"/>"
  + (if $c.categoryAxisTitle then chartTitle($c.categoryAxisTitle; $c.muted; 12; $fonts) else "" end)
  + "<c:tickLblPos val=\"nextTo\"/>"
  + "<c:spPr><a:ln w=\"9525\">" + solidFill($c.line) + "</a:ln></c:spPr>"
  + txPrBody($c.muted; 12; $fonts)
  + "<c:crossAx val=\"" + $c.axVal + "\"/><c:crosses val=\"" + $crosses + "\"/>"
  + "<c:auto val=\"1\"/><c:lblAlgn val=\"ctr\"/><c:lblOffset val=\"100\"/><c:noMultiLvlLbl val=\"0\"/></c:catAx>";

def valAx($c; $fonts; $pos; $crosses):
  "<c:valAx><c:axId val=\"" + $c.axVal + "\"/>"
  + "<c:scaling><c:orientation val=\"minMax\"/></c:scaling>"
  + "<c:delete val=\"0\"/><c:axPos val=\"" + $pos + "\"/>"
  + gridlines($c)
  + (if $c.valueAxisTitle then chartTitle($c.valueAxisTitle; $c.muted; 12; $fonts) else "" end)
  + numFmt($c.numberFormat; "1")
  + "<c:tickLblPos val=\"nextTo\"/>"
  + "<c:spPr><a:ln><a:noFill/></a:ln></c:spPr>"
  + txPrBody($c.muted; 12; $fonts)
  + "<c:crossAx val=\"" + $c.axCat + "\"/><c:crosses val=\"" + $crosses + "\"/>"
  + "<c:crossBetween val=\"between\"/></c:valAx>";

# The spec word for a legend position is "bottom"; the OOXML enum is one of
# b, t, l, r, tr. A legend is hidden by leaving the element out entirely, which
# is what PowerPoint itself writes.
def legendPosCode($p):
  if $p == "top" or $p == "t" then "t"
  elif $p == "left" or $p == "l" then "l"
  elif $p == "right" or $p == "r" then "r"
  elif $p == "topRight" or $p == "tr" then "tr"
  else "b" end;

def legendOf($c; $fonts):
  if ($c.legend // "none") == "none" then ""
  else
    "<c:legend><c:legendPos val=\"" + legendPosCode($c.legend) + "\"/><c:overlay val=\"0\"/>"
    + txPrBody($c.fg; 12; $fonts) + "</c:legend>"
  end;

# Every chart group needs its own pair of axis ids as the last children, not
# just the axis elements below the plot area. PowerPoint tolerates their
# absence; the ECMA schema does not, and a strict reader drops the chart.
def axIds($c):
  "<c:axId val=\"" + $c.axCat + "\"/><c:axId val=\"" + $c.axVal + "\"/>";

def chartSpace($c; $fonts):
  ($c.series | map(. + {categories: $c.categories})) as $ss
  | ($c.numberFormat) as $fmt
  | ($c.type) as $type
  | (if ($type == "pie") or ($type == "doughnut") then
       ((if $type == "pie" then "<c:pieChart>" else "<c:doughnutChart>" end)
        + "<c:varyColors val=\"1\"/>" + pieSer($c; $ss[0]; 0; $fmt)
        + "<c:firstSliceAng val=\"0\"/>"
        + (if $type == "doughnut" then "<c:holeSize val=\"" + (($c.hole | floor) | tostring) + "%\"/>" else "" end)
        + (if $c.labels then dLbls($c; "bestFit") else "" end)
        + (if $type == "pie" then "</c:pieChart>" else "</c:doughnutChart>" end))
     elif $type == "line" then
       "<c:lineChart><c:grouping val=\"standard\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($ss | length)) as $i | lineSer($c; $ss[$i]; $i; $fmt) ] | join(""))
       + "<c:marker val=\"1\"/><c:smooth val=\"0\"/>" + axIds($c) + "</c:lineChart>"
     elif $type == "area" then
       "<c:areaChart><c:grouping val=\"standard\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($ss | length)) as $i | areaSer($c; $ss[$i]; $i; $fmt) ] | join(""))
       + axIds($c) + "</c:areaChart>"
     elif $type == "scatter" then
       "<c:scatterChart><c:scatterStyle val=\"lineMarker\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($ss | length)) as $i | scatterSer($c; $ss[$i]; $i; $fmt) ] | join(""))
       + axIds($c) + "</c:scatterChart>"
     elif $type == "combo" then
       # A combo is two chart groups sharing one category axis: bars for the
       # volume series, a line for the rate series. PowerPoint stores it exactly
       # this way, and the reader can still switch either group's type.
       # `range(...) as $i | ...` keeps the incoming document as `.`, so the
       # index has to be emitted explicitly or the array fills with documents.
       ([ range(0; ($ss | length)) as $i | select((($ss[$i].as // "bar")) != "line") | $i ]) as $barIdx
       | ([ range(0; ($ss | length)) as $i | select((($ss[$i].as // "bar")) == "line") | $i ]) as $lineIdx
       | "<c:barChart><c:barDir val=\"col\"/><c:grouping val=\"clustered\"/><c:varyColors val=\"0\"/>"
         + ([ $barIdx[] as $i | barSer($c; $ss[$i]; $i; $fmt) ] | join(""))
         + "<c:gapWidth val=\"60\"/><c:overlap val=\"-10\"/>"
         + "<c:axId val=\"" + $c.axCat + "\"/><c:axId val=\"" + $c.axVal + "\"/></c:barChart>"
         # The line group reads the secondary value axis, which is how a rate
         # series and a volume series share one page without one flattening.
         + "<c:lineChart><c:grouping val=\"standard\"/><c:varyColors val=\"0\"/>"
         + ([ $lineIdx[] as $i | lineSer($c; $ss[$i]; $i; $fmt) ] | join(""))
         + "<c:marker val=\"1\"/><c:smooth val=\"0\"/>"
         + "<c:axId val=\"" + $c.axCat + "\"/><c:axId val=\"" + ($c.axVal2 // "333333333") + "\"/></c:lineChart>"
     elif $type == "stacked" then
       "<c:barChart><c:barDir val=\"col\"/><c:grouping val=\"stacked\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($ss | length)) as $i | barSer($c; $ss[$i]; $i; $fmt) ] | join(""))
       + "<c:gapWidth val=\"70\"/><c:overlap val=\"100\"/>" + axIds($c) + "</c:barChart>"
     elif $type == "stackedBar" then
       "<c:barChart><c:barDir val=\"bar\"/><c:grouping val=\"stacked\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($ss | length)) as $i | barSer($c; $ss[$i]; $i; $fmt) ] | join(""))
       + "<c:gapWidth val=\"70\"/><c:overlap val=\"100\"/>" + axIds($c) + "</c:barChart>"
     elif $type == "bar" then
       "<c:barChart><c:barDir val=\"bar\"/><c:grouping val=\"clustered\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($ss | length)) as $i | barSer($c; $ss[$i]; $i; $fmt) ] | join(""))
       + "<c:gapWidth val=\"80\"/><c:overlap val=\"-10\"/>" + axIds($c) + "</c:barChart>"
     else
       "<c:barChart><c:barDir val=\"col\"/><c:grouping val=\"clustered\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($ss | length)) as $i | barSer($c; $ss[$i]; $i; $fmt) ] | join(""))
       + "<c:gapWidth val=\"80\"/><c:overlap val=\"-10\"/>" + axIds($c) + "</c:barChart>"
     end) as $plot
  | (if ($type == "pie") or ($type == "doughnut") then
       ""
     elif $type == "bar" or $type == "stackedBar" then
       catAx($c; $fonts; "l"; "autoZero") + valAx($c; $fonts; "b"; "autoZero")
     elif $type == "combo" then
       # Three axes: the shared category axis, the bar value axis, and a hidden
       # secondary value axis on the right for the line group.
       catAx($c; $fonts; "b"; "autoZero") + valAx($c; $fonts; "l"; "autoZero")
       + (valAx2($c; $fonts; "r"))
     elif $type == "scatter" then
       "<c:valAx><c:axId val=\"" + $c.axCat + "\"/><c:scaling><c:orientation val=\"minMax\"/></c:scaling>"
       + "<c:delete val=\"0\"/><c:axPos val=\"b\"/>" + gridlines($c)
       + (if $c.categoryAxisTitle then chartTitle($c.categoryAxisTitle; $c.muted; 12; $fonts) else "" end)
       + numFmt($c.numberFormat; "1") + "<c:tickLblPos val=\"nextTo\"/>"
       + "<c:spPr><a:ln><a:noFill/></a:ln></c:spPr>" + txPrBody($c.muted; 12; $fonts)
       + "<c:crossAx val=\"" + $c.axVal + "\"/><c:crosses val=\"autoZero\"/><c:crossBetween val=\"midCat\"/></c:valAx>"
       + valAx($c; $fonts; "l"; "autoZero")
     else
       catAx($c; $fonts; "b"; "autoZero") + valAx($c; $fonts; "l"; "autoZero")
     end) as $axes
  | decl
  + "<c:chartSpace xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\""
  + " xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
  + "<c:roundedCorners val=\"0\"/>"
  + "<c:chart><c:autoTitleDeleted val=\"1\"/>"
  + "<c:plotArea><c:layout/>" + $plot + $axes
  + "<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr></c:plotArea>"
  + legendOf($c; $fonts)
  + "<c:plotVisOnly val=\"1\"/><c:dispBlanksAs val=\"gap\"/></c:chart>"
  + "<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>"
  + "<c:externalData r:id=\"rId1\"><c:autoUpdate val=\"0\"/></c:externalData>"
  + "</c:chartSpace>";

def chartRels($i):
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/package\""
  + " Target=\"../embeddings/Microsoft_Excel_Worksheet" + ($i | tostring) + ".xlsx\"/>"
  + "</Relationships>";

def chartFrame($c; $id; $rid):
  "<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id=\"" + ($id | tostring) + "\" name=\"Chart " + ($id | tostring) + "\"/>"
  + "<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp=\"1\"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>"
  + "<p:xfrm><a:off x=\"" + emu($c.x) + "\" y=\"" + emu($c.y) + "\"/>"
  + "<a:ext cx=\"" + emu($c.cx) + "\" cy=\"" + emu($c.cy) + "\"/></p:xfrm>"
  + "<a:graphic><a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/chart\">"
  + "<c:chart xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" r:id=\"" + $rid + "\"/>"
  + "</a:graphicData></a:graphic></p:graphicFrame>";

# ---------------------------------------------------------------------------
# Slide
# ---------------------------------------------------------------------------

# Relationship ids are shared by the slide XML and its .rels part, so both read
# them from one place: images take rId2.. in order, then the chart, then notes.
# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------
#
# p:transition and p:timing are children of p:sld. A reader that meets a
# transition element it does not know offers to repair the whole file, so only
# ECMA-376 direct children are emitted and morph goes through AlternateContent
# with a fade fallback.

def transSpeed($s): if $s == "slow" then "slow" elif $s == "fast" then "fast" else "med" end;

def transEffDir($e):
  if $e == "push" then "<p:push dir=\"u\"/>"
  elif $e == "wipe" then "<p:wipe dir=\"l\"/>"
  elif $e == "cover" then "<p:cover dir=\"l\"/>"
  elif $e == "split" then "<p:split orient=\"horz\" dir=\"out\"/>"
  elif $e == "strips" then "<p:strips dir=\"lu\"/>"
  elif $e == "zoom" then "<p:zoom dir=\"in\"/>"
  else "" end;

# Morph has no ECMA-376 element: PowerPoint 2019+ reads p159:morph, everything
# else needs a choice it understands, so the fallback is a plain fade.
def transitionXml($tr):
  if $tr == null or $tr.effect == "none" then ""
  elif $tr.effect == "morph" then
    "<mc:AlternateContent xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\">"
    + "<mc:Choice xmlns:p159=\"http://schemas.microsoft.com/office/powerpoint/2015/09/main\" Requires=\"p159\">"
    + "<p:transition spd=\"" + transSpeed($tr.speed) + "\" p14:dur=\""
    + ((($tr.duration // 700)) | tostring) + "\" xmlns:p14=\"http://schemas.microsoft.com/office/powerpoint/2010/main\">"
    + "<p159:morph option=\"byObject\"/></p:transition></mc:Choice>"
    + "<mc:Fallback><p:transition spd=\"" + transSpeed($tr.speed) + "\"><p:fade/></p:transition></mc:Fallback>"
    + "</mc:AlternateContent>"
  else
    "<p:transition spd=\"" + transSpeed($tr.speed) + "\">"
    + "<p:" + $tr.effect + ">" + (if $tr.effect == "fade" then "" else "" end)
    + "</p:" + $tr.effect + ">"
    + "</p:transition>"
  end;

# Self-closing for the effects that carry no children; a paired empty element is
# also legal, but PowerPoint rewrites it and the file stops being byte-stable.
def transElement($tr):
  if $tr == null or $tr.effect == "none" then ""
  elif $tr.effect == "morph" then transitionXml($tr)
  elif (["fade", "cut", "dissolve", "checker", "blinds", "diamond", "circle",
         "wedge", "wheel", "random", "randomBar", "comb", "newsflash",
         "plus", "pull"] | index($tr.effect)) != null then
    "<p:transition spd=\"" + transSpeed($tr.speed) + "\"><p:" + $tr.effect + "/></p:transition>"
  else
    "<p:transition spd=\"" + transSpeed($tr.speed) + "\">" + transEffDir($tr.effect) + "</p:transition>"
  end;

# Preset ids are PowerPoint's own animation numbers, so the effects appear in the
# animation pane as the named effects instead of a generic custom animation.
def animPreset($e; $dir):
  if $e == "appear" then {preset: 1, sub: 0, cls: "entr"}
  elif $e == "fade" then {preset: 10, sub: 0, cls: "entr"}
  elif $e == "split" then {preset: 16, sub: 21, cls: "entr"}
  elif $e == "wipe" then
    {preset: 22, cls: "entr",
     sub: (if $dir == "up" then 1 elif $dir == "right" then 2 elif $dir == "left" then 8 else 4 end)}
  elif $e == "fly" then
    {preset: 2, cls: "entr",
     sub: (if $dir == "up" then 4 elif $dir == "down" then 0 elif $dir == "right" then 4 else 8 end)}
  elif $e == "zoom" then {preset: 23, sub: 16, cls: "entr"}
  elif $e == "grow" then {preset: 6, sub: 0, cls: "emph"}
  elif $e == "spin" then {preset: 8, sub: 0, cls: "emph"}
  else {preset: 10, sub: 0, cls: "exit"} end;

def animBody($a; $id; $spid):
  ($a.effect) as $e
  | ($a.duration | tostring) as $dur
  | ($a.direction // "up") as $dir
  | ("<p:set><p:cBhvr><p:cTn id=\"" + (($id + 1) | tostring) + "\" dur=\"1\" fill=\"hold\">"
     + "<p:stCondLst><p:cond delay=\"0\"/></p:stCondLst></p:cTn>"
     + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl>"
     + "<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>"
     + "<p:to><p:strVal val=\"visible\"/></p:to></p:set>") as $vis
  | if $e == "appear" then $vis
    elif $e == "fade" or $e == "split" or $e == "wipe" then
      $vis
      + "<p:animEffect transition=\"in\" filter=\""
      + (if $e == "fade" then "fade"
         elif $e == "split" then "barn(inVertical)"
         else "wipe(" + (if $dir == "up" then "up" elif $dir == "right" then "right"
                         elif $dir == "left" then "left" else "down" end) + ")" end)
      + "\"><p:cBhvr><p:cTn id=\"" + (($id + 2) | tostring) + "\" dur=\"" + $dur + "\"/>"
      + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl></p:cBhvr></p:animEffect>"
    elif $e == "fly" then
      $vis
      + "<p:anim calcmode=\"lin\" valueType=\"num\"><p:cBhvr additive=\"base\">"
      + "<p:cTn id=\"" + (($id + 2) | tostring) + "\" dur=\"" + $dur + "\" fill=\"hold\"/>"
      + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl>"
      + "<p:attrNameLst><p:attrName>"
      + (if $dir == "up" or $dir == "down" then "ppt_y" else "ppt_x" end)
      + "</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>"
      + "<p:tav tm=\"0\"><p:val><p:strVal val=\""
      + (if $dir == "up" then "1+#ppt_h/2" elif $dir == "down" then "0-#ppt_h/2"
         elif $dir == "right" then "1+#ppt_w/2" else "0-#ppt_w/2" end)
      + "\"/></p:val></p:tav>"
      + "<p:tav tm=\"100000\"><p:val><p:strVal val=\""
      + (if $dir == "up" or $dir == "down" then "#ppt_y" else "#ppt_x" end)
      + "\"/></p:val></p:tav></p:tavLst></p:anim>"
    elif $e == "zoom" then
      $vis
      + "<p:anim calcmode=\"lin\" valueType=\"num\"><p:cBhvr>"
      + "<p:cTn id=\"" + (($id + 2) | tostring) + "\" dur=\"" + $dur + "\" fill=\"hold\"/>"
      + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl>"
      + "<p:attrNameLst><p:attrName>ppt_w</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>"
      + "<p:tav tm=\"0\"><p:val><p:fltVal val=\"0\"/></p:val></p:tav>"
      + "<p:tav tm=\"100000\"><p:val><p:strVal val=\"#ppt_w\"/></p:val></p:tav></p:tavLst></p:anim>"
      + "<p:anim calcmode=\"lin\" valueType=\"num\"><p:cBhvr>"
      + "<p:cTn id=\"" + (($id + 3) | tostring) + "\" dur=\"" + $dur + "\" fill=\"hold\"/>"
      + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl>"
      + "<p:attrNameLst><p:attrName>ppt_h</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>"
      + "<p:tav tm=\"0\"><p:val><p:fltVal val=\"0\"/></p:val></p:tav>"
      + "<p:tav tm=\"100000\"><p:val><p:strVal val=\"#ppt_h\"/></p:val></p:tav></p:tavLst></p:anim>"
    elif $e == "grow" then
      "<p:animScale><p:cBhvr><p:cTn id=\"" + (($id + 1) | tostring) + "\" dur=\"" + $dur + "\" fill=\"hold\"/>"
      + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl></p:cBhvr>"
      + "<p:by x=\"150000\" y=\"150000\"/></p:animScale>"
    elif $e == "spin" then
      "<p:animRot by=\"21600000\"><p:cBhvr><p:cTn id=\"" + (($id + 1) | tostring) + "\" dur=\"" + $dur + "\" fill=\"hold\"/>"
      + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl>"
      + "<p:attrNameLst><p:attrName>r</p:attrName></p:attrNameLst></p:cBhvr></p:animRot>"
    else
      "<p:animEffect transition=\"out\" filter=\"fade\"><p:cBhvr>"
      + "<p:cTn id=\"" + (($id + 1) | tostring) + "\" dur=\"" + $dur + "\"/><p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl></p:cBhvr></p:animEffect>"
      + "<p:set><p:cBhvr><p:cTn id=\"" + (($id + 2) | tostring) + "\" dur=\"1\" fill=\"hold\">"
      + "<p:stCondLst><p:cond delay=\"" + ((($a.duration - 1) | if . < 0 then 0 else . end) | tostring) + "\"/></p:stCondLst></p:cTn>"
      + "<p:tgtEl><p:spTgt spid=\"" + ($spid | tostring) + "\"/></p:tgtEl>"
      + "<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>"
      + "<p:to><p:strVal val=\"hidden\"/></p:to></p:set>"
    end;

def animRow($a; $id; $spid):
  (animPreset($a.effect; ($a.direction // "up"))) as $p
  | "<p:cTn id=\"" + ($id | tostring) + "\" presetID=\"" + ($p.preset | tostring)
    + "\" presetClass=\"" + $p.cls + "\" presetSubtype=\"" + ($p.sub | tostring)
    + "\" fill=\"hold\" grpId=\"0\" nodeType=\"afterEffect\">"
    + "<p:stCondLst><p:cond delay=\"" + ($a.delay | tostring) + "\"/></p:stCondLst>"
    + "<p:childTnLst>" + animBody($a; $id; $spid) + "</p:childTnLst></p:cTn>";

# An on-click animation opens a new click group; the other two triggers append to
# the group already open, so "with previous" really starts together.
def animGroups($anims):
  reduce $anims[] as $a ({groups: [], cursor: -1};
    if $a.trigger == "on-click" or .cursor < 0
    then .groups += [[$a]] | .cursor = ((.groups | length) - 1)
    else .groups[.cursor] += [$a] end);

# Time-node ids must be unique inside the slide. Every row reserves four ids (the
# row plus its up to three behaviours) and each wrapper takes one, so the counter
# advances by 4 per target and 1 per wrapper; both are asserted after rendering.
def timingXml($anims):
  if ($anims // [] | length) == 0 then ""
  else
    (animGroups($anims)) as $groups
    | (reduce range(0; ($groups.groups | length)) as $gi
        ({xml: [], next: 3};
         ($groups.groups[$gi]) as $beat
         | (.next) as $groupId
         | (reduce range(0; ($beat | length)) as $bi
              ({xml: [], next: ($groupId + 1)};
               ($beat[$bi]) as $a
               | (.next) as $beatId
               | (reduce range(0; ($a.targets | length)) as $k
                    ({xml: [], next: ($beatId + 1)};
                     animRow($a; .next; $a.targets[$k]) as $row
                     | {xml: (.xml + ["<p:par>" + $row + "</p:par>"]), next: (.next + 4)})
                  ) as $rows
               | {xml: (.xml + ["<p:par><p:cTn id=\"" + ($beatId | tostring) + "\" fill=\"hold\">"
                   + "<p:stCondLst><p:cond delay=\"" + ($a.delay | tostring) + "\"/></p:stCondLst>"
                   + "<p:childTnLst>" + ($rows.xml | join("")) + "</p:childTnLst></p:cTn></p:par>"]),
                  next: $rows.next})
           ) as $built
         | {xml: (.xml + ["<p:par><p:cTn id=\"" + ($groupId | tostring) + "\" fill=\"hold\"><p:stCondLst>"
             + "<p:cond delay=\"indefinite\"/>"
             + (if $gi == 0 and ($beat[0].trigger != "on-click")
                then "<p:cond evt=\"onBegin\" delay=\"0\"><p:tn val=\"2\"/></p:cond>" else "" end)
             + "</p:stCondLst><p:childTnLst>" + ($built.xml | join("")) + "</p:childTnLst></p:cTn></p:par>"]),
            next: $built.next})
      ) as $seq
    | "<p:timing><p:tnLst><p:par><p:cTn id=\"1\" dur=\"indefinite\" restart=\"never\" nodeType=\"tmRoot\">"
      + "<p:childTnLst><p:seq concurrent=\"1\" nextAc=\"seek\">"
      + "<p:cTn id=\"2\" dur=\"indefinite\" nodeType=\"mainSeq\"><p:childTnLst>"
      + ($seq.xml | join(""))
      + "</p:childTnLst></p:cTn>"
      + "<p:prevCondLst><p:cond evt=\"onPrev\" delay=\"0\"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>"
      + "<p:nextCondLst><p:cond evt=\"onNext\" delay=\"0\"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>"
      + "</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>"
  end;

def slideRelIds($slide):
  (($slide.images // []) | length) as $ni
  | {images: [ range(0; $ni) | "rId" + ((2 + .) | tostring) ],
     chart: (if $slide.chart then "rId" + ((2 + $ni) | tostring) else null end),
     notes: ("rId" + ((2 + $ni + (if $slide.chart then 1 else 0 end)) | tostring))};

def slideXml($slide; $size; $fonts):
  (slideRelIds($slide)) as $r
  | 2 as $base
  | ([ ($slide.images // [])[] | select((.layer // "front") == "back") ]) as $back
  | ([ ($slide.images // [])[] | select((.layer // "front") != "back") ]) as $front
  | (if $slide.scrim then
       rectShape({x: 0, y: 0, cx: $size.w, cy: $size.h,
                  fill: $slide.scrim.color, alpha: $slide.scrim.alpha, line: null}; ($base + 500))
     else "" end) as $scrimShape
  | decl
  + "<p:sld xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\""
  + (if ($slide.transition.effect // "none") == "morph"
     then " xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\""
          + " xmlns:p14=\"http://schemas.microsoft.com/office/powerpoint/2010/main\""
     else "" end) + ">"
  + "<p:cSld><p:bg><p:bgPr>" + solidFill($slide.bg) + "<a:effectLst/></p:bgPr></p:bg>"
  + "<p:spTree><p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
  + "<p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/>"
  + "<a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
  # Background pictures first, then the scrim over them, then the text.
  + ([ range(0; ($back | length)) as $k | pic($back[$k]; $back[$k].spid; $r.images[$k]) ] | join(""))
  + $scrimShape
  + ([ range(0; ($slide.shapes | length)) as $i |
       $slide.shapes[$i] |
       if .type == "rect" then rectShape(.; .spid) elif .type == "ellipse" then ellipseShape(.; .spid)
       elif .type == "picture" then pic(.; .spid; .rid) else textShape(.; .spid; $fonts) end
     ] | join(""))
  + (if $slide.table then tableFrame($slide.table; $slide.table.spid; $fonts) else "" end)
  + (if $slide.chart then chartFrame($slide.chart; $slide.chart.spid; $r.chart) else "" end)
  + ([ range(0; ($front | length)) as $k |
       pic($front[$k]; $front[$k].spid; $r.images[(($back | length) + $k)])
     ] | join(""))
  + "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>"
  + transElement($slide.transition)
  + timingXml($slide.animation)
  + "</p:sld>";


def notesXml($slide):
  decl
  + "<p:notes xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\">"
  + "<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
  + "<p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/>"
  + "<a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
  + "<p:sp><p:nvSpPr><p:cNvPr id=\"2\" name=\"Slide Image Placeholder 1\"/>"
  + "<p:cNvSpPr><a:spLocks noGrp=\"1\" noRot=\"1\" noChangeAspect=\"1\"/></p:cNvSpPr>"
  + "<p:nvPr><p:ph type=\"sldImg\"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>"
  + "<p:sp><p:nvSpPr><p:cNvPr id=\"3\" name=\"Notes Placeholder 2\"/>"
  + "<p:cNvSpPr><a:spLocks noGrp=\"1\"/></p:cNvSpPr>"
  + "<p:nvPr><p:ph type=\"body\" idx=\"1\"/></p:nvPr></p:nvSpPr><p:spPr/>"
  + "<p:txBody><a:bodyPr/><a:lstStyle/>"
  + ([ ($slide.notes // "") | split("\n")[] |
       "<a:p><a:r><a:rPr lang=\"" + lang + "\" sz=\"1200\" dirty=\"0\"/><a:t>" + (xesc) + "</a:t></a:r></a:p>" ] | join(""))
  + "</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>";

# ---------------------------------------------------------------------------
# Static parts
# ---------------------------------------------------------------------------

def theme($t):
  def fontSet: "<a:latin typeface=\"" + ($t.fonts.latin | xesc) + "\"/><a:ea typeface=\"" + ($t.fonts.eastAsian | xesc) + "\"/><a:cs typeface=\"\"/>";
  decl
  + "<a:theme xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" name=\"hyper-pptx\">"
  + "<a:themeElements><a:clrScheme name=\"hyper-pptx\">"
  + "<a:dk1>" + clr($t.fg) + "</a:dk1><a:lt1>" + clr($t.bg) + "</a:lt1>"
  + "<a:dk2>" + clr($t.accent) + "</a:dk2><a:lt2>" + clr($t.surface) + "</a:lt2>"
  + "<a:accent1>" + clr($t.accent) + "</a:accent1><a:accent2>" + clr($t.muted) + "</a:accent2>"
  + "<a:accent3>" + clr($t.darkAccent) + "</a:accent3><a:accent4>" + clr($t.line) + "</a:accent4>"
  + "<a:accent5>" + clr($t.darkSurface) + "</a:accent5><a:accent6>" + clr($t.darkMuted) + "</a:accent6>"
  + "<a:hlink>" + clr($t.accent) + "</a:hlink><a:folHlink>" + clr($t.muted) + "</a:folHlink>"
  + "</a:clrScheme><a:fontScheme name=\"hyper-pptx\">"
  + "<a:majorFont>" + fontSet + "</a:majorFont>"
  + "<a:minorFont>" + fontSet + "</a:minorFont>"
  + "</a:fontScheme><a:fmtScheme name=\"hyper-pptx\">"
  + "<a:fillStyleLst><a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill>"
  + "<a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill>"
  + "<a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill></a:fillStyleLst>"
  + "<a:lnStyleLst><a:ln w=\"9525\" cap=\"flat\" cmpd=\"sng\" algn=\"ctr\"><a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill><a:prstDash val=\"solid\"/></a:ln>"
  + "<a:ln w=\"19050\" cap=\"flat\" cmpd=\"sng\" algn=\"ctr\"><a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill><a:prstDash val=\"solid\"/></a:ln>"
  + "<a:ln w=\"38100\" cap=\"flat\" cmpd=\"sng\" algn=\"ctr\"><a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill><a:prstDash val=\"solid\"/></a:ln></a:lnStyleLst>"
  + "<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>"
  + "<a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>"
  + "<a:bgFillStyleLst><a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill>"
  + "<a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill>"
  + "<a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill></a:bgFillStyleLst>"
  + "</a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>";

def blankLayout:
  decl
  + "<p:sldLayout xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\""
  + " type=\"blank\" preserve=\"1\"><p:cSld name=\"Blank\"><p:spTree>"
  + "<p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
  + "<p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/>"
  + "<a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
  + "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>";

def blankMaster($t):
  decl
  + "<p:sldMaster xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\">"
  + "<p:cSld><p:bg><p:bgPr>" + solidFill($t.bg) + "<a:effectLst/></p:bgPr></p:bg><p:spTree>"
  + "<p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
  + "<p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/>"
  + "<a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
  + "</p:spTree></p:cSld>"
  + "<p:clrMap bg1=\"lt1\" tx1=\"dk1\" bg2=\"lt2\" tx2=\"dk2\" accent1=\"accent1\" accent2=\"accent2\""
  + " accent3=\"accent3\" accent4=\"accent4\" accent5=\"accent5\" accent6=\"accent6\""
  + " hlink=\"hlink\" folHlink=\"folHlink\"/>"
  + "<p:sldLayoutIdLst><p:sldLayoutId id=\"2147483649\" r:id=\"rId1\"/></p:sldLayoutIdLst>"
  + "<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz=\"3000\" b=\"1\"/></a:lvl1pPr></p:titleStyle>"
  + "<p:bodyStyle><a:lvl1pPr><a:defRPr sz=\"1800\"/></a:lvl1pPr></p:bodyStyle>"
  + "<p:otherStyle><a:lvl1pPr><a:defRPr sz=\"1800\"/></a:lvl1pPr></p:otherStyle></p:txStyles>"
  + "</p:sldMaster>";

def notesMaster($t):
  decl
  + "<p:notesMaster xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\">"
  + "<p:cSld><p:bg><p:bgPr>" + solidFill("FFFFFF") + "<a:effectLst/></p:bgPr></p:bg><p:spTree>"
  + "<p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
  + "<p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/>"
  + "<a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
  + "<p:sp><p:nvSpPr><p:cNvPr id=\"2\" name=\"Slide Image Placeholder 1\"/>"
  + "<p:cNvSpPr><a:spLocks noGrp=\"1\" noRot=\"1\" noChangeAspect=\"1\"/></p:cNvSpPr>"
  + "<p:nvPr><p:ph type=\"sldImg\" idx=\"2\"/></p:nvPr></p:nvSpPr>"
  + "<p:spPr><a:xfrm><a:off x=\"685800\" y=\"1143000\"/><a:ext cx=\"5486400\" cy=\"3086100\"/></a:xfrm>"
  + "<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom><a:noFill/>"
  + "<a:ln w=\"12700\"><a:solidFill><a:prstClr val=\"black\"/></a:solidFill></a:ln></p:spPr></p:sp>"
  + "<p:sp><p:nvSpPr><p:cNvPr id=\"3\" name=\"Notes Placeholder 2\"/>"
  + "<p:cNvSpPr><a:spLocks noGrp=\"1\"/></p:cNvSpPr>"
  + "<p:nvPr><p:ph type=\"body\" idx=\"1\"/></p:nvPr></p:nvSpPr>"
  + "<p:spPr><a:xfrm><a:off x=\"685800\" y=\"4343400\"/><a:ext cx=\"5486400\" cy=\"4114800\"/></a:xfrm>"
  + "<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></p:spPr>"
  + "<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang=\"" + lang + "\"/></a:p></p:txBody></p:sp>"
  + "</p:spTree></p:cSld>"
  + "<p:clrMap bg1=\"lt1\" tx1=\"dk1\" bg2=\"lt2\" tx2=\"dk2\" accent1=\"accent1\" accent2=\"accent2\""
  + " accent3=\"accent3\" accent4=\"accent4\" accent5=\"accent5\" accent6=\"accent6\""
  + " hlink=\"hlink\" folHlink=\"folHlink\"/>"
  + "<p:notesStyle><a:lvl1pPr><a:defRPr sz=\"1200\"/></a:lvl1pPr></p:notesStyle></p:notesMaster>";

def presProps:
  decl
  + "<p:presentationPr xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\"/>";

def viewProps:
  decl
  + "<p:viewPr xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\""
  + " lastView=\"sldView\"><p:normalViewPr><p:restoredLeft sz=\"15620\"/><p:restoredTop sz=\"94660\"/></p:normalViewPr>"
  + "<p:gridSpacing cx=\"76200\" cy=\"76200\"/></p:viewPr>";

def tableStyles:
  decl
  + "<a:tblStyleLst xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " def=\"{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}\"/>";

def coreProps($d):
  decl
  + "<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\""
  + " xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\""
  + " xmlns:dcmitype=\"http://purl.org/dc/dcmitype/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
  + "<dc:title>" + ($d.title | xesc) + "</dc:title>"
  + "<dc:creator>" + ($d.author | xesc) + "</dc:creator>"
  + "<cp:lastModifiedBy>" + ($d.author | xesc) + "</cp:lastModifiedBy>"
  + "</cp:coreProperties>";

def appProps($d):
  decl
  + "<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\""
  + " xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">"
  + "<Application>hyper-pptx</Application><PresentationFormat>Widescreen</PresentationFormat>"
  + "<Slides>" + ($d.slides | length | tostring) + "</Slides>"
  + "<Notes>" + ([ $d.slides[] | select((.notes // "") != "") ] | length | tostring) + "</Notes>"
  + "<HiddenSlides>0</HiddenSlides><MMClips>0</MMClips><ScaleCrop>false</ScaleCrop>"
  + "<Company>hyper-pptx</Company><LinksUpToDate>false</LinksUpToDate>"
  + "<SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged>"
  + "<AppVersion>16.0000</AppVersion></Properties>";

# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def masterRels:
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout\" Target=\"../slideLayouts/slideLayout1.xml\"/>"
  + "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme\" Target=\"../theme/theme1.xml\"/>"
  + "</Relationships>";

def layoutRels:
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster\" Target=\"../slideMasters/slideMaster1.xml\"/>"
  + "</Relationships>";

def notesMasterRels:
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme\" Target=\"../theme/theme2.xml\"/>"
  + "</Relationships>";

def slideRels($i; $slide):
  (slideRelIds($slide)) as $r
  | (($slide.images // []) | length) as $ni
  | decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout\" Target=\"../slideLayouts/slideLayout1.xml\"/>"
  + ([ range(0; $ni) as $k |
       "<Relationship Id=\"" + $r.images[$k]
       + "\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/image\" Target=\"../media/"
       + $slide.images[$k].media + "\"/>" ] | join(""))
  + (if $slide.chart then
       "<Relationship Id=\"" + $r.chart
       + "\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart\" Target=\"../charts/chart"
       + (($i + 1) | tostring) + ".xml\"/>"
     else "" end)
  + "<Relationship Id=\"" + $r.notes
  + "\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide\" Target=\"../notesSlides/notesSlide"
  + (($i + 1) | tostring) + ".xml\"/>"
  + "</Relationships>";

def notesSlideRels($i):
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster\" Target=\"../notesMasters/notesMaster1.xml\"/>"
  + "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide\" Target=\"../slides/slide" + (($i + 1) | tostring) + ".xml\"/>"
  + "</Relationships>";

def staticParts:
  [ {path: "ppt/presProps.xml", xml: presProps},
    {path: "ppt/viewProps.xml", xml: viewProps},
    {path: "ppt/tableStyles.xml", xml: tableStyles}
  ];

def themeParts($d):
  [ {path: "ppt/theme/theme1.xml", xml: theme($d.theme)},
    {path: "ppt/theme/theme2.xml", xml: theme($d.theme)}
  ];

def masterParts($d):
  [ {path: "ppt/slideMasters/slideMaster1.xml", xml: blankMaster($d.theme)},
    {path: "ppt/slideMasters/_rels/slideMaster1.xml.rels", xml: masterRels},
    {path: "ppt/slideLayouts/slideLayout1.xml", xml: blankLayout},
    {path: "ppt/slideLayouts/_rels/slideLayout1.xml.rels", xml: layoutRels},
    {path: "ppt/notesMasters/notesMaster1.xml", xml: notesMaster($d.theme)},
    {path: "ppt/notesMasters/_rels/notesMaster1.xml.rels", xml: notesMasterRels}
  ];

def docParts($d):
  [ {path: "docProps/core.xml", xml: coreProps($d)},
    {path: "docProps/app.xml", xml: appProps($d)}
  ];

def slideParts($d; $n):
  [ range(0; $n) as $i |
    {path: ("ppt/slides/slide" + (($i + 1) | tostring) + ".xml"),
     xml: slideXml($d.slides[$i]; $d.size; $d.theme.fonts)},
    {path: ("ppt/slides/_rels/slide" + (($i + 1) | tostring) + ".xml.rels"),
     xml: slideRels($i; $d.slides[$i])}
  ];

def notesParts($d; $n):
  [ range(0; $n) as $i |
    {path: ("ppt/notesSlides/notesSlide" + (($i + 1) | tostring) + ".xml"),
     xml: notesXml($d.slides[$i])},
    {path: ("ppt/notesSlides/_rels/notesSlide" + (($i + 1) | tostring) + ".xml.rels"),
     xml: notesSlideRels($i)}
  ];

def chartParts($d; $n):
  [ range(0; $n) as $i | select($d.slides[$i].chart) |
    {path: ("ppt/charts/chart" + (($i + 1) | tostring) + ".xml"),
     xml: chartSpace($d.slides[$i].chart; $d.theme.fonts)},
    {path: ("ppt/charts/_rels/chart" + (($i + 1) | tostring) + ".xml.rels"),
     xml: chartRels($i + 1)}
  ];

def presentationXml($d; $n):
  decl
  + "<p:presentation xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\" saveSubsetFonts=\"1\">"
  + "<p:sldMasterIdLst><p:sldMasterId id=\"2147483648\" r:id=\"rId1\"/></p:sldMasterIdLst>"
  + "<p:notesMasterIdLst><p:notesMasterId r:id=\"rId3\"/></p:notesMasterIdLst>"
  + "<p:sldIdLst>"
  + ([ range(0; $n) as $i | "<p:sldId id=\"" + ((256 + $i) | tostring) + "\" r:id=\"rId" + (($i + 10) | tostring) + "\"/>" ] | join(""))
  + "</p:sldIdLst>"
  + "<p:sldSz cx=\"" + emu($d.size.w) + "\" cy=\"" + emu($d.size.h) + "\"/>"
  + "<p:notesSz cx=\"6858000\" cy=\"9144000\"/>"
  + "</p:presentation>";

def presentationRelsXml($d; $n):
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster\" Target=\"slideMasters/slideMaster1.xml\"/>"
  + "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme\" Target=\"theme/theme1.xml\"/>"
  + "<Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster\" Target=\"notesMasters/notesMaster1.xml\"/>"
  + "<Relationship Id=\"rId4\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps\" Target=\"presProps.xml\"/>"
  + "<Relationship Id=\"rId5\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps\" Target=\"viewProps.xml\"/>"
  + "<Relationship Id=\"rId6\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles\" Target=\"tableStyles.xml\"/>"
  + ([ range(0; $n) as $i |
       "<Relationship Id=\"rId" + (($i + 10) | tostring) + "\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide\" Target=\"slides/slide" + (($i + 1) | tostring) + ".xml\"/>" ] | join(""))
  + "</Relationships>";

def contentTypesXml($d; $n):
  ([ $d.slides[] | select(.chart) ] | length) as $nchart
  | decl
  + "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
  + "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
  + "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
  + "<Default Extension=\"png\" ContentType=\"image/png\"/>"
  + "<Default Extension=\"jpeg\" ContentType=\"image/jpeg\"/>"
  + "<Default Extension=\"jpg\" ContentType=\"image/jpeg\"/>"
  + "<Default Extension=\"gif\" ContentType=\"image/gif\"/>"
  + (if $nchart > 0
     then "<Default Extension=\"xlsx\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\"/>"
     else "" end)
  + "<Override PartName=\"/ppt/presentation.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml\"/>"
  + "<Override PartName=\"/ppt/slideMasters/slideMaster1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml\"/>"
  + "<Override PartName=\"/ppt/slideLayouts/slideLayout1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml\"/>"
  + "<Override PartName=\"/ppt/notesMasters/notesMaster1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml\"/>"
  + "<Override PartName=\"/ppt/theme/theme1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.theme+xml\"/>"
  + "<Override PartName=\"/ppt/theme/theme2.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.theme+xml\"/>"
  + "<Override PartName=\"/ppt/presProps.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.presProps+xml\"/>"
  + "<Override PartName=\"/ppt/viewProps.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml\"/>"
  + "<Override PartName=\"/ppt/tableStyles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml\"/>"
  + "<Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>"
  + "<Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>"
  + ([ range(0; $n) as $i |
       "<Override PartName=\"/ppt/slides/slide" + (($i + 1) | tostring) + ".xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slide+xml\"/>" ] | join(""))
  + ([ range(0; $n) as $i |
       "<Override PartName=\"/ppt/notesSlides/notesSlide" + (($i + 1) | tostring) + ".xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml\"/>" ] | join(""))
  + ([ range(0; $n) as $i | select($d.slides[$i].chart) |
       "<Override PartName=\"/ppt/charts/chart" + (($i + 1) | tostring) + ".xml\" ContentType=\"application/vnd.openxmlformats-officedocument.drawingml.chart+xml\"/>" ] | join(""))
  + "</Types>";

def rootRelsXml:
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"ppt/presentation.xml\"/>"
  + "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/>"
  + "<Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" Target=\"docProps/app.xml\"/>"
  + "</Relationships>";

def allParts($d; $n):
  staticParts + docParts($d) + themeParts($d) + masterParts($d)
  + slideParts($d; $n) + notesParts($d; $n) + chartParts($d; $n);

# Media slots are numbered once for the whole deck, so a gallery of four
# pictures and a chart on the next slide never collide on a file name.
. as $d
| ($d.slides | length) as $n
| (reduce range(0; $n) as $i ({next: 1, slides: []};
     ($d.slides[$i].images // []) as $imgs
     | .slides += [ {index: $i,
                     media: [ range(0; ($imgs | length)) as $k |
                              "image" + ((.next + $k) | tostring) + "." + $imgs[$k].ext ]} ]
     | .next += ($imgs | length))) as $names
| ($d.slides | to_entries | map(
     .key as $i
     | .value
     | .images = ((.images // []) | to_entries | map(.value + {media: $names.slides[$i].media[.key]})))) as $slides
| ($d + {slides: $slides}) as $d2
| {
    parts: allParts($d2; $n),
    media: [ range(0; $n) as $i | ($d2.slides[$i].images // [])[] |
             {name: .media, path: .path} ],
    workbooks: [ range(0; $n) as $i | select($d2.slides[$i].chart) |
                 {index: ($i + 1),
                  categories: $d2.slides[$i].chart.categories,
                  series: ([ $d2.slides[$i].chart.series[] | {name, values} ])} ],
    presentation: presentationXml($d2; $n),
    presentationRels: presentationRelsXml($d2; $n),
    contentTypes: contentTypesXml($d2; $n),
    rootRels: rootRelsXml
  }

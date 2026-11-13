# pptx-package.jq — turn a resolved deck into OOXML parts.
#
# Input : resolved deck (output of layout.jq)
# Output: {"parts": [{"path": "...", "xml": "..."}], "media": [...], "report": {...}}
#
# Only DrawingML that Office readers require is emitted. Every slide carries
# absolute geometry, so the package needs one blank layout and no placeholder
# inheritance: what the preview shows is what PowerPoint opens.

def xesc:
  tostring
  | gsub("&"; "&amp;")
  | gsub("<"; "&lt;")
  | gsub(">"; "&gt;")
  | gsub("\""; "&quot;");

def decl: "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n";

def emu($x): ($x | floor | tostring);

def sz($pt): ($pt * 100 | floor | tostring);

def clr($hex): "<a:srgbClr val=\"" + ($hex | ascii_upcase) + "\"/>";

def solidFill($hex): "<a:solidFill>" + clr($hex) + "</a:solidFill>";

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

def rectShape($s; $id):
  "<p:sp><p:nvSpPr><p:cNvPr id=\"" + ($id | tostring) + "\" name=\"Block " + ($id | tostring) + "\"/>"
  + "<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>"
  + xfrm($s.x; $s.y; $s.cx; $s.cy)
  + "<a:prstGeom prst=\"" + (if ($s.radius // 0) > 0 then "roundRect" else "rect" end) + "\"><a:avLst/></a:prstGeom>"
  + solidFill($s.fill)
  + (if $s.line then "<a:ln w=\"12700\">" + solidFill($s.line) + "</a:ln>" else "<a:ln><a:noFill/></a:ln>" end)
  + "</p:spPr>"
  + "<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang=\"" + lang + "\"/></a:p></p:txBody></p:sp>";

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
  + "<a:tcPr marL=\"91440\" marR=\"91440\" marT=\"45720\" marB=\"45720\" anchor=\"ctr\">"
  + solidFill($fill) + "<a:lnB w=\"6350\"><a:noFill/></a:lnB></a:tcPr></a:tc>";

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
# Chart
# ---------------------------------------------------------------------------

def barDir($type): if $type == "bar" then "bar" else "col" end;
def grouping($type): if $type == "stacked" then "stacked" else "clustered" end;

def numCache($vals):
  "<c:numCache><c:formatCode>General</c:formatCode><c:ptCount val=\"" + ($vals | length | tostring) + "\"/>"
  + ([ range(0; ($vals | length)) as $i |
       "<c:pt idx=\"" + ($i | tostring) + "\"><c:v>" + ($vals[$i] | tostring) + "</c:v></c:pt>" ] | join(""))
  + "</c:numCache>";

def strCache($vals):
  "<c:strCache><c:ptCount val=\"" + ($vals | length | tostring) + "\"/>"
  + ([ range(0; ($vals | length)) as $i |
       "<c:pt idx=\"" + ($i | tostring) + "\"><c:v>" + ($vals[$i] | tostring | xesc) + "</c:v></c:pt>" ] | join(""))
  + "</c:strCache>";

def series($s; $i; $colors):
  "<c:ser><c:idx val=\"" + ($i | tostring) + "\"/><c:order val=\"" + ($i | tostring) + "\"/>"
  + "<c:tx><c:strRef><c:f>Sheet1!$" + (if $i == 0 then "B" else "C" end) + "$1</c:f>" + strCache([$s.name]) + "</c:strRef></c:tx>"
  + "<c:spPr>" + solidFill($colors[$i % ($colors | length)])
  + "<a:ln w=\"19050\"><a:solidFill>" + clr($colors[$i % ($colors | length)]) + "</a:solidFill></a:ln></c:spPr>"
  + "<c:cat><c:strRef><c:f>Sheet1!$A$2:$A$" + ((($s.values | length)) + 1 | tostring) + "</c:f>"
  + strCache($s.categories) + "</c:strRef></c:cat>"
  + "<c:val><c:numRef><c:f>Sheet1!$" + (if $i == 0 then "B" else "C" end) + "$2:$" + (if $i == 0 then "B" else "C" end) + "$" + ((($s.values | length)) + 1 | tostring) + "</c:f>"
  + numCache($s.values) + "</c:numRef></c:val>"
  + "</c:ser>";

def chartSpace($c):
  ($c.series | map(. + {categories: $c.categories})) as $seriesList
  | (if $c.type == "pie" then
       "<c:pieChart><c:varyColors val=\"1\"/>"
       + (series($seriesList[0]; 0; $c.colors))
       + "<c:firstSliceAng val=\"0\"/></c:pieChart>"
     elif $c.type == "line" then
       "<c:lineChart><c:grouping val=\"standard\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($seriesList | length)) as $i | series($seriesList[$i]; $i; $c.colors) ] | join(""))
       + "<c:marker val=\"1\"/></c:lineChart>"
     elif $c.type == "stacked" then
       "<c:barChart><c:barDir val=\"col\"/><c:grouping val=\"stacked\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($seriesList | length)) as $i | series($seriesList[$i]; $i; $c.colors) ] | join(""))
       + "<c:overlap val=\"100\"/></c:barChart>"
     else
       "<c:barChart><c:barDir val=\"" + barDir($c.type) + "\"/><c:grouping val=\"clustered\"/><c:varyColors val=\"0\"/>"
       + ([ range(0; ($seriesList | length)) as $i | series($seriesList[$i]; $i; $c.colors) ] | join(""))
       + "<c:gapWidth val=\"100\"/><c:overlap val=\"-10\"/></c:barChart>"
     end) as $plot
  | decl
  + "<c:chartSpace xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\""
  + " xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
  + "<c:roundedCorners val=\"0\"/>"
  + "<c:chart><c:title><c:overlay val=\"0\"/></c:title><c:autoTitleDeleted val=\"1\"/>"
  + "<c:plotArea><c:layout/>" + $plot
  + "<c:catAx><c:axId val=\"111111111\"/><c:scaling><c:orientation val=\"minMax\"/></c:scaling>"
  + "<c:delete val=\"0\"/><c:axPos val=\"b\"/><c:numFmt formatCode=\"General\" sourceLinked=\"1\"/>"
  + "<c:tickLblPos val=\"nextTo\"/><c:spPr><a:ln w=\"9525\">" + solidFill($c.muted) + "</a:ln></c:spPr>"
  + "<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz=\"1100\">" + solidFill($c.muted)
  + "<a:latin typeface=\"+mn-lt\"/></a:defRPr></a:pPr><a:endParaRPr lang=\"" + lang + "\"/></a:p></c:txPr>"
  + "<c:crossAx val=\"222222222\"/><c:crosses val=\"autoZero\"/><c:auto val=\"1\"/><c:lblAlgn val=\"ctr\"/>"
  + "<c:lblOffset val=\"100\"/><c:noMultiLvlLbl val=\"0\"/></c:catAx>"
  + "<c:valAx><c:axId val=\"222222222\"/><c:scaling><c:orientation val=\"minMax\"/></c:scaling>"
  + "<c:delete val=\"0\"/><c:axPos val=\"l\"/><c:majorGridlines><c:spPr><a:ln w=\"6350\">"
  + solidFill($c.muted) + "</a:ln></c:spPr></c:majorGridlines>"
  + "<c:numFmt formatCode=\"General\" sourceLinked=\"1\"/><c:tickLblPos val=\"nextTo\"/>"
  + "<c:spPr><a:ln><a:noFill/></a:ln></c:spPr>"
  + "<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz=\"1100\">" + solidFill($c.muted)
  + "<a:latin typeface=\"+mn-lt\"/></a:defRPr></a:pPr><a:endParaRPr lang=\"" + lang + "\"/></a:p></c:txPr>"
  + "<c:crossAx val=\"111111111\"/><c:crosses val=\"autoZero\"/><c:crossBetween val=\"between\"/></c:valAx>"
  + "<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr></c:plotArea>"
  + "<c:legend><c:legendPos val=\"b\"/><c:overlay val=\"0\"/>"
  + "<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz=\"1100\">" + solidFill($c.fg)
  + "<a:latin typeface=\"+mn-lt\"/></a:defRPr></a:pPr><a:endParaRPr lang=\"" + lang + "\"/></a:p></c:txPr>"
  + "</c:legend><c:plotVisOnly val=\"1\"/><c:dispBlanksAs val=\"gap\"/></c:chart></c:chartSpace>";

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

def slideXml($slide; $fonts):
  2 as $base
  | decl
  + "<p:sld xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\""
  + " xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\">"
  + "<p:cSld><p:bg><p:bgPr>" + solidFill($slide.bg) + "<a:effectLst/></p:bgPr></p:bg>"
  + "<p:spTree><p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
  + "<p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/>"
  + "<a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
  + ([ range(0; ($slide.shapes | length)) as $i |
       $slide.shapes[$i] |
       if .type == "rect" then rectShape(.; $base + $i) else textShape(.; $base + $i; $fonts) end
     ] | join(""))
  + (if $slide.table then tableFrame($slide.table; ($base + 200); $fonts) else "" end)
  + (if $slide.chart then chartFrame($slide.chart; ($base + 300); "rId2") else "" end)
  + (if $slide.image then
       "<p:pic><p:nvPicPr><p:cNvPr id=\"" + (($base + 400) | tostring) + "\" name=\"Image\"/>"
       + "<p:cNvPicPr><a:picLocks noChangeAspect=\"1\"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>"
       + "<p:blipFill><a:blip r:embed=\"rId2\"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>"
       + "<p:spPr>" + xfrm($slide.image.x; $slide.image.y; $slide.image.cx; $slide.image.cy)
       + "<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></p:spPr></p:pic>"
     else "" end)
  + "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>";

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

# Helpers for the assembly step. Each relationship list and each part list is
# a named function so a long string concatenation never sits inside an object
# literal, where jq's parser breaks the line continuation.

def relsOpen: "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">";

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
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout\" Target=\"../slideLayouts/slideLayout1.xml\"/>"
  + (if $slide.chart then
       "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart\" Target=\"../charts/chart" + (($i + 1) | tostring) + ".xml\"/>"
     elif $slide.image then
       "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/image\" Target=\"../media/image" + (($i + 1) | tostring) + "." + $slide.image.ext + "\"/>"
     else "" end)
  + "<Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide\" Target=\"../notesSlides/notesSlide" + (($i + 1) | tostring) + ".xml\"/>"
  + "</Relationships>";

def notesSlideRels($i):
  decl + relsOpen
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster\" Target=\"../notesMasters/notesMaster1.xml\"/>"
  + "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide\" Target=\"../slides/slide" + (($i + 1) | tostring) + ".xml\"/>"
  + "</Relationships>";

def chartRels: decl + relsOpen + "</Relationships>";

def staticParts:
  [ {path: "[Content_Types].xml", xml: ""},
    {path: "_rels/.rels", xml: ""},
    {path: "ppt/presentation.xml", xml: ""},
    {path: "ppt/_rels/presentation.xml.rels", xml: ""},
    {path: "ppt/presProps.xml", xml: presProps},
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
     xml: slideXml($d.slides[$i]; $d.theme.fonts)},
    {path: ("ppt/slides/_rels/slide" + (($i + 1) | tostring) + ".xml.rels"),
     xml: slideRels($i; $d.slides[$i])},
    {path: ("ppt/notesSlides/notesSlide" + (($i + 1) | tostring) + ".xml"),
     xml: notesXml($d.slides[$i])},
    {path: ("ppt/notesSlides/_rels/notesSlide" + (($i + 1) | tostring) + ".xml.rels"),
     xml: notesSlideRels($i)}
  ];

def chartParts($d; $n):
  [ range(0; $n) as $i | select($d.slides[$i].chart) |
    {path: ("ppt/charts/chart" + (($i + 1) | tostring) + ".xml"),
     xml: chartSpace($d.slides[$i].chart)},
    {path: ("ppt/charts/_rels/chart" + (($i + 1) | tostring) + ".xml.rels"),
     xml: chartRels}
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
  decl
  + "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
  + "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
  + "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
  + "<Default Extension=\"png\" ContentType=\"image/png\"/>"
  + "<Default Extension=\"jpeg\" ContentType=\"image/jpeg\"/>"
  + "<Default Extension=\"jpg\" ContentType=\"image/jpeg\"/>"
  + "<Default Extension=\"gif\" ContentType=\"image/gif\"/>"
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
  staticParts + docParts($d) + themeParts($d) + masterParts($d) + slideParts($d; $n) + chartParts($d; $n);

. as $d
| ($d.slides | length) as $n
| {
    parts: allParts($d; $n),
    # Images travel as base64 beside the XML: the packager cannot read a file.
    media: [ $d.slides[] | select(.image) | {slot: .index, path: .image.path, ext: .image.ext} ],
    presentation: presentationXml($d; $n),
    presentationRels: presentationRelsXml($d; $n),
    contentTypes: contentTypesXml($d; $n),
    rootRels: rootRelsXml
  }

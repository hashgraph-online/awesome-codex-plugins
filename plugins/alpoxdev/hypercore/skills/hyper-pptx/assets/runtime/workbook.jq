# workbook.jq — the embedded spreadsheet behind one chart.
#
# Input : {"categories": [...], "series": [{"name": ..., "values": [...]}]}
# Output: {"parts": [{"path": "...", "xml": "..."}]} — a minimal .xlsx written
#         as plain parts so render-deck.sh can zip it with the same fixed
#         timestamp the deck uses.
#
# Why it exists: a chart part renders from its cached values alone, so a deck
# without a workbook still opens and looks right. But "Edit Data" in PowerPoint
# then has no sheet behind the chart, and the reader who wants to change a number
# meets an empty dialog. The workbook is what makes the chart a real chart.
#
# Column layout matches the chart's own cell references in pptx-package.jq:
# A holds categories, B/C/D the series, row 1 the series names.

def xesc:
  tostring
  | gsub("&"; "&amp;")
  | gsub("<"; "&lt;")
  | gsub(">"; "&gt;")
  | gsub("\""; "&quot;");

def decl: "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n";

def colLetter($i): ("ABCDEFGHIJKLMNOPQRSTUVWXYZ" | .[$i - 1:$i]) // "A";

def sst($strings):
  ($strings | unique) as $u
  | {count: ($strings | length), list: $u,
     index: (reduce range(0; ($u | length)) as $i ({}; .[$u[$i]] = $i))};

def contentTypes:
  decl
  + "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
  + "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
  + "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
  + "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
  + "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
  + "<Override PartName=\"/xl/sharedStrings.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml\"/>"
  + "</Types>";

def rootRels:
  decl
  + "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
  + "</Relationships>";

def workbookXml:
  decl
  + "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\""
  + " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
  + "<sheets><sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>";

def workbookRels:
  decl
  + "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
  + "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
  + "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings\" Target=\"sharedStrings.xml\"/>"
  + "</Relationships>";

. as $wb
| ($wb.categories | map(tostring)) as $cats
| sst([ "" ] + [ $wb.series[] | .name ] + $cats) as $s
| ([ range(0; ($wb.series | length)) as $i |
     "<c r=\"" + colLetter($i + 2) + "1\" t=\"s\"><v>"
     + (($s.index[$wb.series[$i].name]) | tostring) + "</v></c>" ] | join("")) as $headerCells
| ([ range(0; ($cats | length)) as $r |
     "<row r=\"" + (($r + 2) | tostring) + "\">"
     + "<c r=\"A" + (($r + 2) | tostring) + "\" t=\"s\"><v>"
     + (($s.index[$cats[$r]]) | tostring) + "</v></c>"
     + ([ range(0; ($wb.series | length)) as $k |
          "<c r=\"" + colLetter($k + 2) + (($r + 2) | tostring) + "\"><v>"
          + (($wb.series[$k].values[$r] // 0) | tostring) + "</v></c>" ] | join(""))
     + "</row>" ] | join("")) as $bodyRows
| {
    parts: [
      {path: "[Content_Types].xml", xml: contentTypes},
      {path: "_rels/.rels", xml: rootRels},
      {path: "xl/workbook.xml", xml: workbookXml},
      {path: "xl/_rels/workbook.xml.rels", xml: workbookRels},
      {path: "xl/worksheets/sheet1.xml",
       xml: (decl
             + "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
             + "<sheetData><row r=\"1\">" + $headerCells + "</row>"
             + $bodyRows
             + "</sheetData></worksheet>")},
      {path: "xl/sharedStrings.xml",
       xml: (decl
             + "<sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\""
             + " count=\"" + ($s.count | tostring) + "\""
             + " uniqueCount=\"" + (($s.list | length) | tostring) + "\">"
             + ([ $s.list[] | "<si><t>" + (xesc) + "</t></si>" ] | join(""))
             + "</sst>")}
    ]
  }

#!/usr/bin/env python3
"""Create an .xlsx from a JSON spec or a CSV file, charts included.

Usage:
    python3 build_workbook.py --spec spec.json --out report.xlsx [--json]
    python3 build_workbook.py --csv data.csv --out data.xlsx [--sheet 이름]
                             [--encoding auto] [--delimiter ,] [--header]
    python3 build_workbook.py --self-test

Spec shape (every key optional except `sheets`):
    {"title": "2026 상반기 실적",
     "sheets": [
       {"name": "매출",
        "rows": [["월", "금액", "비고"], ["1월", 1000, "확정"]],
        "freeze": "A2", "autofilter": "A1:C9",
        "cols": {"A": 12, "B": 16},
        "rowHeights": {"1": 24},
        "formulas": [{"ref": "B10", "formula": "=SUM(B2:B9)"}],
        "formats": [{"range": "B2:B10", "code": "#,##0 \\"원\\""}],
        "validations": [{"range": "C2:C9", "type": "list",
                         "formula1": "\\"확정,잠정\\"", "prompt": "확정 또는 잠정"}],
        "condFormats": [{"range": "B2:B9", "type": "cellIs", "operator": "lessThan",
                         "formula": ["0"], "fill": "#FFC7CE"}],
        "charts": [{"type": "bar", "title": "월별 매출", "anchor": "E2",
                    "categories": "A2:A9",
                    "series": [{"name": "매출", "values": "B2:B9"}]}]}
     ]}

Values are typed: numbers stay numeric, TRUE/FALSE become booleans, an ISO date
string (2026-01-31 or 2026-01-31T09:00) becomes a serial date with a date format,
and everything else is text. Strings starting with "=" become formulas when the
cell also appears in `formulas`; otherwise they are kept as literal text so a CSV
export full of leading equals signs does not silently turn into formulas.

Output (stdout): one JSON object with path, byte size, sha256, sheet summaries, and
any warnings. Exit codes: 0 written, 1 refused or failed, 2 usage.

Charts are written as native DrawingML: bar, column, line, pie, doughnut, area, and
scatter. There is no pivot-table writer; a pivot summary must be built as ordinary
rows (see references/large-data-and-pivots.md).
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile
from datetime import date, datetime, time
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlib  # noqa: E402

M_NS = xlsxlib.NS["m"]
R_NS = xlsxlib.NS["r"]
PR_NS = xlsxlib.NS["pr"]
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CT_SHEET = "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
CT_STYLES = "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"
CT_WORKBOOK = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
CT_CHART = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"
CT_DRAWING = "application/vnd.openxmlformats-officedocument.drawing+xml"
REL_SHEET = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
REL_STYLES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
REL_CHART = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
REL_DRAWING = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing"

ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?$")
EXCEL_EPOCH = date(1899, 12, 30)
DEFAULT_DATE_FMT = "yyyy-mm-dd"
DEFAULT_DATETIME_FMT = "yyyy-mm-dd h:mm"

# Worksheet hard limits in the file format. Exceeding them does not degrade gracefully: some writers
# silently drop rows, so refuse instead of shipping a truncated sheet.
MAX_ROWS = 1048576
MAX_COLS = 16384
MAX_CELL_TEXT = 32767


class BuildError(Exception):
    pass


def serial(value):
    if isinstance(value, datetime):
        delta = value - datetime(1899, 12, 30)
        return delta.days + delta.seconds / 86400.0
    if isinstance(value, date):
        return float((value - EXCEL_EPOCH).days)
    raise BuildError("not a date: %r" % (value,))


def text_locked(style_xf):
    """True when the cell's number format is Text (`@`), which must not be re-typed."""
    if not style_xf:
        return False
    fmt_id, code = style_xf
    return fmt_id == 49 or (code or "").strip() == "@"


def classify(value, text_format=False):
    """Return (kind, stored_value, default_format or None).

    `text_format` is set when the cell carries a Text (`@`) number format: the value
    is then written as text with its leading zeros intact, because a ZIP or phone
    code stored as a number is data loss, not a type improvement.
    """
    if value is None or value == "":
        return ("blank", None, None)
    if text_format and not isinstance(value, bool) and not isinstance(value, (datetime, date, time)):
        return ("text", str(value), None)
    if isinstance(value, bool):
        return ("bool", value, None)
    if isinstance(value, (int, float)):
        return ("number", value, None)
    if isinstance(value, (datetime, date, time)):
        return ("date", serial(value), DEFAULT_DATETIME_FMT if isinstance(value, datetime) else DEFAULT_DATE_FMT)
    text = str(value)
    if re.match(r"^-?\d+$", text) and len(text) < 16:
        return ("number", int(text), None)
    if re.match(r"^-?\d*\.\d+$", text) and "e" not in text.lower() and len(text) < 24:
        return ("number", float(text), None)
    m = ISO_DATE.match(text)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            if m.group(4):
                moment = datetime(year, month, day, int(m.group(4)), int(m.group(5)), int(m.group(6) or 0))
                return ("date", serial(moment), DEFAULT_DATETIME_FMT)
            return ("date", serial(date(year, month, day)), DEFAULT_DATE_FMT)
        except ValueError:
            return ("text", text, None)
    if text.upper() in ("TRUE", "FALSE"):
        return ("bool", text.upper() == "TRUE", None)
    return ("text", text, None)


def fmt_number(number):
    if isinstance(number, float) and number == int(number) and abs(number) < 1e16:
        return str(int(number))
    return repr(number) if isinstance(number, float) else str(number)


def cell_xml(ref, kind, value, style=None):
    attrs = ['r="%s"' % ref]
    if style is not None:
        attrs.append('s="%d"' % style)
    if kind == "text":
        attrs.append('t="inlineStr"')
        return "<c %s><is><t xml:space=\"preserve\">%s</t></is></c>" % (" ".join(attrs), escape(str(value)))
    if kind == "bool":
        attrs.append('t="b"')
        return "<c %s><v>%s</v></c>" % (" ".join(attrs), "1" if value else "0")
    if kind == "blank":
        return "<c %s/>" % " ".join(attrs)
    return "<c %s><v>%s</v></c>" % (" ".join(attrs), fmt_number(value))


def formula_xml(ref, formula, style=None):
    body = formula[1:] if formula.startswith("=") else formula
    attrs = ['r="%s"' % ref]
    if style is not None:
        attrs.append('s="%d"' % style)
    return "<c %s><f>%s</f></c>" % (" ".join(attrs), escape(body))


def col_letter(index):
    return xlsxlib.col_letters(index)


class Styles:
    """Append-only style table: fonts, fills, borders, and number formats."""

    def __init__(self):
        self.numfmts = {}
        self.xfs = [{"numFmtId": 0, "fontId": 0, "fillId": 0, "borderId": 0}]
        self.fonts = ['<font><sz val="11"/><color theme="1"/><name val="맑은 고딕"/><family val="2"/></font>']
        self.fills = ['<fill><patternFill patternType="none"/></fill>',
                      '<fill><patternFill patternType="gray125"/></fill>']
        self.borders = ["<border><left/><right/><top/><bottom/><diagonal/></border>"]
        self.dxfs = []
        self._fmt_cache = {}

    def numfmt_of(self, style_index):
        """Return (numFmtId, formatCode) for a cellXfs index."""
        xfs = self.xfs
        if not isinstance(style_index, int) or not (0 <= style_index < len(xfs)):
            return (0, "General")
        fmt_id = xfs[style_index]["numFmtId"]
        if fmt_id == 49:
            return (49, "@")
        return (fmt_id, self.numfmts.get(fmt_id, "General" if fmt_id == 0 else ""))

    def number_format(self, code):
        # `@` is builtin format 49; registering it as a custom id would make every
        # reader classify the cell as a number.
        if (code or "").strip() == "@":
            return 49
        if code in self._fmt_cache:
            return self._fmt_cache[code]
        for fmt_id, existing in self.numfmts.items():
            if existing == code:
                self._fmt_cache[code] = fmt_id
                return fmt_id
        fmt_id = max([163] + list(self.numfmts)) + 1
        self.numfmts[fmt_id] = code
        self._fmt_cache[code] = fmt_id
        return fmt_id

    def xf(self, numfmt_code=None, bold=False, color=None, fill=None):
        fmt_id = 0 if not numfmt_code else self.number_format(numfmt_code)
        font_id = 0
        if bold or color:
            font = '<font>'
            if bold:
                font += "<b/>"
            if color:
                font += '<color rgb="%s"/>' % color.lstrip("#").upper()
            font += '<sz val="11"/><name val="맑은 고딕"/><family val="2"/></font>'
            self.fonts.append(font)
            font_id = len(self.fonts) - 1
        fill_id = 0
        if fill:
            self.fills.append('<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
                              '<bgColor indexed="64"/></patternFill></fill>' % fill.lstrip("#").upper())
            fill_id = len(self.fills) - 1
        self.xfs.append({"numFmtId": fmt_id, "fontId": font_id, "fillId": fill_id, "borderId": 0})
        return len(self.xfs) - 1

    def dxf(self, font_color=None, fill=None):
        """Register a differential style and return its index for a cfRule dxfId."""
        node = "<dxf>"
        if font_color:
            node += '<font><color rgb="%s"/></font>' % font_color.lstrip("#").upper()
        if fill:
            node += '<fill><patternFill><bgColor rgb="%s"/></patternFill></fill>' % fill.lstrip("#").upper()
        node += "</dxf>"
        self.dxfs.append(node)
        return len(self.dxfs) - 1

    def xml(self):
        numfmts = ""
        if self.numfmts:
            numfmts = '<numFmts count="%d">%s</numFmts>' % (len(self.numfmts), "".join(
                '<numFmt numFmtId="%d" formatCode="%s"/>' % (fid, escape(code, {'"': "&quot;"}))
                for fid, code in sorted(self.numfmts.items())))
        xfs = "".join(
            '<xf numFmtId="%d" fontId="%d" fillId="%d" borderId="%d" xfId="0"%s%s/>' % (
                x["numFmtId"], x["fontId"], x["fillId"], x["borderId"],
                ' applyNumberFormat="1"' if x["numFmtId"] else "",
                ' applyFont="1"' if x["fontId"] else "")
            for x in self.xfs)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="%s">%s'
            '<fonts count="%d">%s</fonts>'
            '<fills count="%d">%s</fills>'
            '<borders count="%d">%s</borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="%d">%s</cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '%s'
            '</styleSheet>'
        ) % (M_NS, numfmts, len(self.fonts), "".join(self.fonts),
             len(self.fills), "".join(self.fills),
             len(self.borders), "".join(self.borders),
             len(self.xfs), xfs,
             ('<dxfs count="%d">%s</dxfs>' % (len(self.dxfs), "".join(self.dxfs))) if self.dxfs else '')


CHART_KINDS = {
    "bar": "bar", "column": "col", "line": "line", "pie": "pie",
    "doughnut": "doughnut", "area": "area", "scatter": "scatter",
}


CHART_ELEMENT = {"bar": "bar", "col": "bar", "line": "line", "area": "area",
                 "pie": "pie", "doughnut": "doughnut", "scatter": "scatter"}


def chart_xml(chart, sheet_name):
    """Render one native DrawingML chart part.

    Column charts are `<c:barChart>` with `<c:barDir val="col"/>`; there is no
    `colChart` element, which is the mistake openpyxl reports as an empty plot.
    """
    kind = CHART_KINDS.get((chart.get("type") or "bar").lower())
    if not kind:
        raise BuildError("unsupported chart type %r (have: %s)" % (chart.get("type"), ", ".join(CHART_KINDS)))
    element = CHART_ELEMENT[kind]
    title = chart.get("title")
    series = chart.get("series") or []
    if not series:
        raise BuildError("chart needs at least one series")
    categories = chart.get("categories")
    has_axes = kind in ("bar", "col", "line", "area", "scatter")
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"',
           ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"',
           ' xmlns:r="%s">' % R_NS,
           '<c:chart>']
    if title:
        out.append('<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:r>'
                   '<a:rPr lang="ko-KR" sz="1200" b="1"/><a:t>%s</a:t></a:r></a:p>'
                   '</c:rich></c:tx><c:overlay val="0"/></c:title>' % escape(title))
    out.append('<c:plotArea><c:layout/>')
    out.append('<c:%sChart>' % element)
    if kind in ("bar", "col"):
        out.append('<c:barDir val="%s"/><c:grouping val="clustered"/><c:varyColors val="0"/>'
                   % ("col" if kind == "col" else "bar"))
    elif kind == "line":
        out.append('<c:grouping val="standard"/><c:varyColors val="0"/>')
    elif kind == "area":
        out.append('<c:grouping val="standard"/><c:varyColors val="0"/>')
    elif kind in ("pie", "doughnut"):
        out.append('<c:varyColors val="1"/>')
    elif kind == "scatter":
        out.append('<c:scatterStyle val="lineMarker"/><c:varyColors val="0"/>')
    for idx, ser in enumerate(series, start=1):
        out.append('<c:ser><c:idx val="%d"/><c:order val="%d"/>' % (idx - 1, idx - 1))
        name_ref = ser.get("name")
        if name_ref and ("!" in str(name_ref) or re.match(r"^\$?[A-Za-z]{1,3}\$?\d+$", str(name_ref))):
            out.append('<c:tx><c:strRef><c:f>%s</c:f></c:strRef></c:tx>'
                       % _series_ref(name_ref, sheet_name))
        elif name_ref:
            out.append('<c:tx><c:v>%s</c:v></c:tx>' % escape(str(name_ref)))
        if kind in ("bar", "col", "area"):
            out.append('<c:invertIfNegative val="0"/>')
        if categories:
            out.append('<c:cat><c:strRef><c:f>%s</c:f></c:strRef></c:cat>'
                       % _series_ref(categories, sheet_name))
        out.append('<c:val><c:numRef><c:f>%s</c:f></c:numRef></c:val>'
                   % _series_ref(ser.get("values"), sheet_name))
        if kind == "line":
            out.append('<c:smooth val="0"/>')
        out.append('</c:ser>')
    if kind in ("bar", "col"):
        out.append('<c:gapWidth val="%d"/>' % int(chart.get("gapWidth", 150)))
        out.append('<c:axId val="111111111"/><c:axId val="222222222"/>')
    elif has_axes:
        out.append('<c:axId val="111111111"/><c:axId val="222222222"/>')
    out.append('</c:%sChart>' % element)
    if has_axes:
        out.append('<c:catAx><c:axId val="111111111"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
                   '<c:delete val="0"/><c:axPos val="b"/><c:majorTickMark val="out"/>'
                   '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
                   '<c:crossAx val="222222222"/><c:crosses val="autoZero"/><c:auto val="1"/>'
                   '<c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/></c:catAx>')
        out.append('<c:valAx><c:axId val="222222222"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
                   '<c:delete val="0"/><c:axPos val="l"/><c:majorGridlines/>'
                   '<c:numFmt formatCode="General" sourceLinked="1"/>'
                   '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
                   '<c:tickLblPos val="nextTo"/><c:crossAx val="111111111"/><c:crosses val="autoZero"/>'
                   '<c:crossBetween val="between"/></c:valAx>')
    out.append('</c:plotArea>')
    if chart.get("legend", True) and len(series) >= 1:
        out.append('<c:legend><c:legendPos val="%s"/><c:overlay val="0"/></c:legend>'
                   % ("b" if has_axes else "r"))
    out.append('<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart></c:chartSpace>')
    return "".join(out)


def _series_ref(ref, sheet_name):
    """Qualify a chart reference with the chart's own sheet unless it names one.

    `categories: "Data!A2:A3"` already points at another sheet; prefixing the
    chart sheet would produce `Chart!Data!A2:A3`, which Excel rejects as a
    malformed reference and renders as an empty plot.
    """
    text = str(ref).replace("$", "")
    if "!" in text:
        return text
    return "%s!%s" % (_quote(sheet_name), text)


def _quote(sheet_name):
    if re.match(r"^[^\W\d][\w.]*$", sheet_name or "") and not any(ch in sheet_name for ch in " !'&*()[]{}+-/"):
        return sheet_name
    return "'%s'" % (sheet_name or "").replace("'", "''")


def rels_xml(entries):
    body = "".join('<Relationship Id="%s" Type="%s" Target="%s"/>' % (rid, rtype, target)
                   for rid, rtype, target in entries)
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="%s">%s</Relationships>' % (PR_NS, body)


def sheet_xml(sheet, styles, drawing_rid=None):
    name = sheet.get("name")
    rows = sheet.get("rows") or []
    if len(rows) > MAX_ROWS:
        raise BuildError("sheet %r has %d rows; a worksheet holds %d. Split the data or use a database"
                         % (name, len(rows), MAX_ROWS))
    widest = max([len(row) for row in rows] or [0])
    if widest > MAX_COLS:
        raise BuildError("sheet %r is %d columns wide; a worksheet holds %d" % (name, widest, MAX_COLS))
    for row in rows:
        for value in row:
            if isinstance(value, str) and len(value) > MAX_CELL_TEXT:
                raise BuildError("sheet %r has a %d-character cell; the limit is %d"
                                 % (name, len(value), MAX_CELL_TEXT))
    formulas = {f["ref"]: f["formula"] for f in sheet.get("formulas") or []}
    # Strings starting with = + - @ would execute as a formula or DDE call on open;
    # they are written as text and counted so the caller can report them.
    neutralized = []
    coerced = []
    style_by_ref = {}
    default_styles = {}
    for item in sheet.get("formats") or []:
        bounds = xlsxlib.range_bounds(item.get("range"))
        if not bounds:
            raise BuildError("sheet %r: bad format range %r" % (name, item.get("range")))
        code = item.get("code")
        index = styles.xf(numfmt_code=code, bold=item.get("bold"), color=item.get("color"), fill=item.get("fill"))
        if bounds[0] == bounds[2] and bounds[1] == bounds[3]:
            style_by_ref["%s%d" % (col_letter(bounds[0]), bounds[1])] = index
        else:
            for row in range(bounds[1], bounds[3] + 1):
                for col in range(bounds[0], bounds[2] + 1):
                    style_by_ref["%s%d" % (col_letter(col), row)] = index
    # Auto-apply a date format where a value is a date and no explicit format exists.
    for r_index, row in enumerate(rows, start=1):
        for c_index, value in enumerate(row, start=1):
            if isinstance(value, (date, datetime)):
                ref = "%s%d" % (col_letter(c_index), r_index)
                if ref not in style_by_ref:
                    code = DEFAULT_DATETIME_FMT if isinstance(value, datetime) else DEFAULT_DATE_FMT
                    default_styles[ref] = styles.xf(numfmt_code=code)
    # Cells are collected per row before any row element is emitted: a formula may
    # name a cell beyond the row's data (D2 next to A2:C2) or on a row the data never
    # reached (B5), and a row element per formula would emit the same row twice.
    row_cells = {}
    max_col = 0
    for r_index, row in enumerate(rows, start=1):
        cells = row_cells.setdefault(r_index, [])
        for c_index, value in enumerate(row, start=1):
            ref = "%s%d" % (col_letter(c_index), r_index)
            max_col = max(max_col, c_index)
            if ref in formulas:
                continue
            style = style_by_ref.get(ref, default_styles.get(ref))
            numfmt = styles.numfmt_of(style) if style is not None else None
            kind, stored, auto_format = classify(value, text_locked(numfmt))
            if kind == "text" and isinstance(value, str) and value[:1] in ("=", "+", "-", "@") and value.strip():
                neutralized.append({"sheet": name, "ref": ref, "prefix": value[0]})
            # A digit string under an explicit numeric format is re-typed to a number,
            # which is what Excel does too, but a dropped leading zero is silent data
            # loss and the caller cannot see it in the result.
            if (kind == "number" and re.fullmatch(r"0\d+", str(value)) and style is not None
                    and numfmt is not None and not text_locked(numfmt)
                    and _is_numeric_code(numfmt)):
                coerced.append({"sheet": name, "ref": ref, "value": str(value)})
            if style is None and auto_format:
                style = styles.xf(numfmt_code=auto_format)
            cells.append((c_index, cell_xml(ref, kind, stored, style)))
    for ref, formula in formulas.items():
        col, row = xlsxlib.parse_ref(ref)
        if not col:
            raise BuildError("sheet %r: bad formula reference %r" % (name, ref))
        style = style_by_ref.get(ref, default_styles.get(ref))
        row_cells.setdefault(row, []).append((col, formula_xml(ref, formula, style)))
        max_col = max(max_col, col)
    out_rows = []
    for r_index in sorted(row_cells):
        cells = row_cells[r_index]
        if not cells:
            continue
        height = (sheet.get("rowHeights") or {}).get(str(r_index))
        head = '<row r="%d"' % r_index + (' ht="%s" customHeight="1"' % height if height else "") + ">"
        cells.sort(key=lambda item: item[0])
        out_rows.append(head + "".join(xml for _c, xml in cells) + "</row>")
    last_row = max([len(rows), max([xlsxlib.parse_ref(r)[1] for r in formulas] or [0])])

    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="%s" xmlns:r="%s">' % (M_NS, R_NS)]
    freeze = sheet.get("freeze")
    tab_color = sheet.get("tabColor")
    if tab_color:
        parts.append('<sheetPr><tabColor rgb="%s"/></sheetPr>' % tab_color.lstrip("#").upper())
    parts.append('<dimension ref="A1:%s%d"/>' % (col_letter(max(max_col, 1)), max(last_row, 1)))
    parts.append('<sheetViews><sheetView workbookViewId="0">')
    if freeze:
        col, row = xlsxlib.parse_ref(freeze)
        split = []
        if col - 1:
            split.append('xSplit="%d"' % (col - 1))
        if row - 1:
            split.append('ySplit="%d"' % (row - 1))
        split.extend(['topLeftCell="%s"' % freeze, 'activePane="bottomRight"', 'state="frozen"'])
        parts.append("<pane %s/>" % " ".join(split))
        parts.append('<selection pane="bottomRight" activeCell="%s" sqref="%s"/>' % (freeze, freeze))
    parts.append("</sheetView></sheetViews>")
    parts.append('<sheetFormatPr defaultRowHeight="15"/>')
    cols = sheet.get("cols") or {}
    if cols:
        entries = []
        for letter, width in sorted(cols.items(), key=lambda kv: xlsxlib.col_index(kv[0])):
            index = xlsxlib.col_index(letter)
            entries.append('<col min="%d" max="%d" width="%g" customWidth="1"/>' % (index, index, float(width)))
        parts.append("<cols>%s</cols>" % "".join(entries))
    parts.append("<sheetData>%s</sheetData>" % "".join(out_rows))
    autofilter = sheet.get("autofilter")
    if autofilter:
        parts.append('<autoFilter ref="%s"/>' % autofilter)
    merges = sheet.get("merges") or []
    if merges:
        parts.append('<mergeCells count="%d">%s</mergeCells>' % (
            len(merges), "".join('<mergeCell ref="%s"/>' % m for m in merges)))
    validations = sheet.get("validations") or []
    if validations:
        nodes = []
        for item in validations:
            attrs = ['sqref="%s"' % item["range"]]
            for key, attr in (("type", "type"), ("operator", "operator"), ("allowBlank", "allowBlank"),
                              ("prompt", "prompt"), ("promptTitle", "promptTitle"),
                              ("error", "error"), ("errorTitle", "errorTitle")):
                if item.get(key) is not None:
                    attrs.append('%s="%s"' % (attr, escape(str(item[key]), {'"': "&quot;"})))
            if item.get("prompt"):
                attrs.append('showInputMessage="1"')
            if item.get("error"):
                attrs.append('showErrorMessage="1"')
            body = ""
            if item.get("formula1") is not None:
                body += "<formula1>%s</formula1>" % escape(str(item["formula1"]))
            if item.get("formula2") is not None:
                body += "<formula2>%s</formula2>" % escape(str(item["formula2"]))
            nodes.append("<dataValidation %s>%s</dataValidation>" % (" ".join(attrs), body))
        parts.append('<dataValidations count="%d">%s</dataValidations>' % (len(nodes), "".join(nodes)))
    cond = sheet.get("condFormats") or []
    if cond:
        for item in cond:
            kind = item.get("type", "cellIs")
            attrs = ['type="%s"' % kind, 'priority="%d"' % item.get("priority", 1)]
            inner = ""
            if kind in ("cellIs", "expression"):
                if item.get("operator"):
                    attrs.append('operator="%s"' % item["operator"])
                for formula in item.get("formula") or []:
                    inner += "<formula>%s</formula>" % escape(str(formula))
                if item.get("fill") or item.get("fontColor"):
                    attrs.append('dxfId="%d"' % styles.dxf(item.get("fontColor"), item.get("fill")))
            parts.append('<conditionalFormatting sqref="%s"><cfRule %s>%s</cfRule></conditionalFormatting>'
                         % (item["range"], " ".join(attrs), inner))
    if drawing_rid:
        parts.append('<drawing r:id="%s"/>' % drawing_rid)
    parts.append("</worksheet>")
    return "".join(parts), neutralized, coerced


def _is_numeric_code(numfmt):
    """True for a format that displays a number as digits (a code-shaped format)."""
    code = (numfmt[1] or "").strip()
    return bool(code) and code != "@"


def drawing_xml(charts, rel_ids):
    anchors = []
    for chart, rid in zip(charts, rel_ids):
        col, row = xlsxlib.parse_ref(chart.get("anchor") or "E2")
        col = max(col, 1)
        row = max(row, 1)
        width = int(chart.get("width", 12))
        height = int(chart.get("height", 18))
        anchors.append(
            '<xdr:twoCellAnchor>'
            '<xdr:from><xdr:col>%d</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>%d</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from>'
            '<xdr:to><xdr:col>%d</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>%d</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to>'
            '<xdr:graphicFrame macro=""><xdr:nvGraphicFramePr><xdr:cNvPr id="%d" name="차트 %d"/>'
            '<xdr:cNvGraphicFramePr/></xdr:nvGraphicFramePr>'
            '<xdr:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></xdr:xfrm>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
            '<c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" r:id="%s"/>'
            '</a:graphicData></a:graphic></xdr:graphicFrame><xdr:clientData/>'
            '</xdr:twoCellAnchor>'
            % (col - 1, row - 1, col - 1 + width, row - 1 + height, rid and (2 + len(anchors)), len(anchors) + 1, rid))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"'
            ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
            ' xmlns:r="%s">%s</xdr:wsDr>' % (R_NS, "".join(anchors)))


def build(spec, out_path):
    sheets = spec.get("sheets") or []
    if not sheets:
        raise BuildError("spec has no sheets")
    names = [s.get("name") for s in sheets]
    if any(not n for n in names):
        raise BuildError("every sheet needs a name")
    if len(set(names)) != len(names):
        raise BuildError("duplicate sheet names: %s" % names)
    for n in names:
        if len(n) > 31:
            raise BuildError("sheet name over 31 characters: %r" % n)
        if re.search(r"[\[\]:*?/\\]", n):
            raise BuildError("sheet name has a character Excel forbids: %r" % n)
    styles = Styles()
    parts = {}
    sheet_entries = []
    neutralized = []
    coerced = []
    drawing_entries = []
    chart_entries = []
    chart_index = 0
    drawing_index = 0
    for sheet_index, sheet in enumerate(sheets, start=1):
        sheet_part = "xl/worksheets/sheet%d.xml" % sheet_index
        charts = sheet.get("charts") or []
        drawing_rid = None
        if charts:
            drawing_index += 1
            drawing_part = "xl/drawings/drawing%d.xml" % drawing_index
            chart_rids = []
            for chart in charts:
                chart_index += 1
                chart_part = "xl/charts/chart%d.xml" % chart_index
                parts[chart_part] = chart_xml(chart, sheet["name"]).encode("utf-8")
                rid = "rIdChart%d" % chart_index
                chart_entries.append((chart_part, rid, "charts/chart%d.xml" % chart_index))
                chart_rids.append(rid)
            parts[drawing_part] = drawing_xml(charts, chart_rids).encode("utf-8")
            drawing_entries.append((drawing_part, "charts/chart%d.xml" % chart_index, len(charts), sheet_index))
            drawing_rid = "rIdDrawing1"
            parts["xl/drawings/_rels/drawing%d.xml.rels" % drawing_index] = rels_xml([
                ("rIdChart%d" % (chart_index - len(charts) + i + 1), REL_CHART,
                 "../charts/chart%d.xml" % (chart_index - len(charts) + i + 1))
                for i in range(len(charts))]).encode("utf-8")
        sheet_body, sheet_neutralized, sheet_coerced = sheet_xml(sheet, styles, drawing_rid)
        neutralized.extend(sheet_neutralized)
        coerced.extend(sheet_coerced)
        parts[sheet_part] = sheet_body.encode("utf-8")
        sheet_entries.append({"name": sheet["name"], "part": sheet_part, "rows": len(sheet.get("rows") or [])})

    # workbook.xml
    sheet_nodes = "".join(
        '<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(s["name"], {'"': "&quot;"}), i, i)
        for i, s in enumerate(sheets, start=1))
    defined = spec.get("definedNames") or []
    defined_xml = ""
    if defined:
        defined_xml = "<definedNames>%s</definedNames>" % "".join(
            '<definedName name="%s">%s</definedName>' % (escape(d["name"], {'"': "&quot;"}), escape(d["formula"]))
            for d in defined)
    parts["xl/workbook.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="%s" xmlns:r="%s">'
        '<workbookPr/>'
        '<bookViews><workbookView activeTab="0"/></bookViews>'
        '<sheets>%s</sheets>%s'
        '<calcPr calcId="191029" fullCalcOnLoad="1"/>'
        '</workbook>' % (M_NS, R_NS, sheet_nodes, defined_xml)
    ).encode("utf-8")
    wb_rels = [(("rId%d" % i), REL_SHEET, "worksheets/sheet%d.xml" % i) for i in range(1, len(sheets) + 1)]
    wb_rels.append(("rIdStyles", REL_STYLES, "styles.xml"))
    if drawing_entries:
        for index, (part, _target, _count, _owner) in enumerate(drawing_entries, start=1):
            wb_rels.append(("rIdDraw%d" % index, REL_DRAWING, part.replace("xl/", "")))
    parts["xl/_rels/workbook.xml.rels"] = rels_xml(wb_rels).encode("utf-8")
    parts["xl/styles.xml"] = styles.xml().encode("utf-8")
    parts["_rels/.rels"] = rels_xml([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "xl/workbook.xml")]).encode("utf-8")
    overrides = ["<Override PartName=\"/xl/workbook.xml\" ContentType=\"%s\"/>" % CT_WORKBOOK,
                 "<Override PartName=\"/xl/styles.xml\" ContentType=\"%s\"/>" % CT_STYLES]
    for i in range(1, len(sheets) + 1):
        overrides.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="%s"/>' % (i, CT_SHEET))
    for part, _, _ in chart_entries:
        overrides.append('<Override PartName="/%s" ContentType="%s"/>' % (part, CT_CHART))
    for index, _ in enumerate(drawing_entries, start=1):
        overrides.append('<Override PartName="/xl/drawings/drawing%d.xml" ContentType="%s"/>' % (index, CT_DRAWING))
    parts["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="%s">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>%s</Types>' % (CT_NS, "".join(overrides))
    ).encode("utf-8")
    # A drawing rels file must sit beside the sheet that holds the <drawing> element,
    # numbered by that sheet's part index. Using the drawing's own sequence number
    # attaches the chart to sheet 1 whenever the chart lives on a later sheet, and the
    # real owner keeps a <drawing> pointing at a part that does not exist.
    for drawing_part, _target, _count, owner_index in drawing_entries:
        drawing_no = drawing_part.rsplit("drawing", 1)[1].split(".")[0]
        parts["xl/worksheets/_rels/sheet%d.xml.rels" % owner_index] = rels_xml([
            ("rIdDrawing1", REL_DRAWING, "../drawings/drawing%s.xml" % drawing_no)]).encode("utf-8")

    tmp = out_path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts.items():
            zf.writestr(name, data)
    os.replace(tmp, out_path)
    return {"sheets": sheet_entries, "parts": len(parts), "neutralized": neutralized,
            "coercedCodes": coerced}


# ---------------------------------------------------------------------------
# CSV intake
# ---------------------------------------------------------------------------

ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1")


def read_csv_rows(path, encoding="auto", delimiter=None, limit=None):
    """Yield rows, guessing the Korean-friendly encodings Excel actually produces."""
    tried = []
    candidates = ENCODINGS if encoding in (None, "", "auto") else (encoding,)
    raw = None
    used = None
    for candidate in candidates:
        try:
            with open(path, "r", encoding=candidate, newline="") as fh:
                raw = fh.read()
            used = candidate
            break
        except UnicodeDecodeError as exc:
            tried.append("%s: %s" % (candidate, exc.reason))
            continue
    if raw is None:
        raise BuildError("could not decode %s (%s)" % (path, "; ".join(tried)))
    sample = raw[:65536]
    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    reader = csv.reader(io.StringIO(raw), delimiter=delimiter)
    rows = []
    for index, row in enumerate(reader):
        if limit and index >= limit:
            break
        rows.append(row)
    return {"rows": rows, "encoding": used, "delimiter": delimiter}


# A CSV field of digits with a leading zero is a code (postal code, product id, phone
# prefix), not a number: converting 007 to 7 silently destroys the value. Those
# columns get the Text (`@`) format so classify() keeps the literal.
LEADING_ZERO = re.compile(r"^0\d+$")


def text_columns(rows):
    """Column indexes where a purely numeric field keeps a leading zero."""
    columns = set()
    for row in rows:
        for index, value in enumerate(row, start=1):
            if isinstance(value, str) and LEADING_ZERO.match(value.strip()):
                columns.add(index)
    return columns


def csv_to_spec(rows, sheet_name="Sheet1"):
    widths = {}
    for row in rows[:200]:
        for index, value in enumerate(row, start=1):
            width = min(max(len(str(value)) + 2, 9), 48)
            widths[index] = max(widths.get(index, 0), width)
    locked = text_columns(rows)
    spec = {"sheets": [{"name": sheet_name, "rows": rows,
                        "cols": {col_letter(i): w for i, w in widths.items()},
                        "freeze": "A2"}]}
    if locked:
        # The whole column, not only the offending cells: mixed types in one column
        # is itself the thing Excel users complain about.
        spec["sheets"][0]["formats"] = [{"range": "%s:%s" % (col_letter(i), col_letter(i)), "code": "@"}
                                        for i in sorted(locked)]
    return spec


def self_test():
    """Build a workbook with formatting, formulas, charts, and Korean text."""
    import tempfile
    checks = []
    spec = {
        "sheets": [
            {"name": "매출 요약",
             "rows": [["월", "매출", "비용", "이익"],
                      ["1월", 1200000, 800000, None],
                      ["2월", 1500000, 900000, None],
                      ["3월", 1750000, 950000, None],
                      ["합계", None, None, None]],
             "freeze": "A2", "autofilter": "A1:D4",
             "cols": {"A": 10, "B": 16, "C": 16, "D": 16},
             "formulas": [{"ref": "D2", "formula": "=B2-C2"},
                          {"ref": "D3", "formula": "=B3-C3"},
                          {"ref": "D4", "formula": "=B4-C4"},
                          {"ref": "B5", "formula": "=SUM(B2:B4)"},
                          {"ref": "D5", "formula": "=SUM(D2:D4)"}],
             "formats": [{"range": "B2:D5", "code": "#,##0"}],
             "validations": [{"range": "A2:A4", "type": "list", "formula1": "\"1월,2월,3월\""}],
             "condFormats": [{"range": "D2:D4", "type": "cellIs", "operator": "lessThan",
                              "formula": ["0"], "fill": "#FFC7CE"}],
             "charts": [{"type": "column", "title": "월별 매출", "anchor": "F2",
                         "categories": "A2:A4",
                         "series": [{"name": "매출", "values": "B2:B4"},
                                    {"name": "이익", "values": "D2:D4"}]}]},
            {"name": "메모", "rows": [["날짜", "비고"], [date(2026, 1, 31), "1월 마감"]],
             "formats": [{"range": "A2", "code": "yyyy-mm-dd"}]},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "built.xlsx")
        meta = build(spec, out)
        checks.append(("wrote file", os.path.isfile(out) and os.path.getsize(out) > 2000))
        checks.append(("two sheets", len(meta["sheets"]) == 2))
        wb = xlsxlib.Workbook(out)
        checks.append(("sheet names", [n for n, _, _ in wb.sheets] == ["매출 요약", "메모"]))
        cells = {}
        for row_no, row in wb.iter_rows("xl/worksheets/sheet1.xml"):
            for cell in row:
                cells[cell["ref"]] = cell
        checks.append(("number kept", cells["B2"]["value"] == 1200000))
        checks.append(("formula written", cells["D2"]["formula"] == "=B2-C2"))
        checks.append(("sum written", cells["B5"]["formula"] == "=SUM(B2:B4)"))
        checks.append(("currency format", wb.format_kind(cells["B2"]["style"]) == "number"))
        features = wb.sheet_features("xl/worksheets/sheet1.xml")
        checks.append(("freeze", features["freeze"] is not None))
        checks.append(("autofilter", features["auto_filter"] == "A1:D4"))
        checks.append(("validation", len(features["validations"]) == 1))
        checks.append(("cond format", len(features["conditional"]) == 1))
        checks.append(("chart present", len(wb.chart_types("xl/worksheets/sheet1.xml")) == 1))
        checks.append(("chart type", wb.chart_types("xl/worksheets/sheet1.xml")[0]["type"] == "col"))
        memo = {}
        for row_no, row in wb.iter_rows("xl/worksheets/sheet2.xml"):
            for cell in row:
                memo[cell["ref"]] = cell
        checks.append(("date serial", isinstance(memo["A2"]["value"], (int, float))))
        checks.append(("date kind", wb.format_kind(memo["A2"]["style"]) == "date"))
        checks.append(("korean text", memo["B2"]["value"] == "1월 마감"))
        # Round-trip through the reader: the workbook must inspect without warnings.
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import inspect_workbook
        report = inspect_workbook.inspect(out)
        checks.append(("inspect clean", not [w for w in report["warnings"] if w["code"].startswith("E_")]))
        # CSV path, including a Korean sheet name and cp949 bytes.
        csv_path = os.path.join(tmp, "sales.csv")
        with open(csv_path, "w", encoding="cp949", newline="") as fh:
            fh.write("품목,수량,단가\n사과,10,1200\n배,5,2300\n")
        parsed = read_csv_rows(csv_path)
        checks.append(("cp949 decoded", parsed["encoding"] in ("cp949", "euc-kr")))
        checks.append(("csv rows", len(parsed["rows"]) == 3))
        csv_out = os.path.join(tmp, "sales.xlsx")
        build(csv_to_spec(parsed["rows"], "품목"), csv_out)
        csv_wb = xlsxlib.Workbook(csv_out)
        checks.append(("csv sheet name", [n for n, _, _ in csv_wb.sheets] == ["품목"]))
        # A leading = + - @ must land as literal text and be counted, never as a formula.
        inj_path = os.path.join(tmp, "inj.csv")
        with open(inj_path, "w", encoding="utf-8", newline="") as fh:
            fh.write("name,val\n=cmd|x,1\n+8210,2\n@SUM(A1),3\n")
        inj_out = os.path.join(tmp, "inj.xlsx")
        inj_meta = build(csv_to_spec(read_csv_rows(inj_path)["rows"], "주입"), inj_out)
        checks.append(("neutralized counted", len(inj_meta["neutralized"]) == 3))
        inj_wb = xlsxlib.Workbook(inj_out)
        inj_cells = {}
        for _n, _p, _s in inj_wb.sheets:
            for _rn, _cells in inj_wb.iter_rows(_p):
                for _c in _cells:
                    inj_cells[_c["ref"]] = _c
        checks.append(("neutralized stays text",
                       all(inj_cells[r]["value"] in ("=cmd|x", "+8210", "@SUM(A1)") and not inj_cells[r]["formula"]
                           for r in ("A2", "A3", "A4"))))
        # A Text (`@`) format must keep a leading zero instead of re-typing to a number.
        zero_out = os.path.join(tmp, "zero.xlsx")
        build({"sheets": [{"name": "코드", "rows": [["우편번호"], ["007"], ["01234"]],
                           "formats": [{"range": "A2:A3", "code": "@"}]}]}, zero_out)
        zero_wb = xlsxlib.Workbook(zero_out)
        zero_cells = {}
        for _n, _p, _s in zero_wb.sheets:
            for _rn, _cells in zero_wb.iter_rows(_p):
                for _c in _cells:
                    zero_cells[_c["ref"]] = _c
        checks.append(("text format keeps zero", zero_cells["A2"]["value"] == "007"))
        checks.append(("text format kind", zero_cells["A2"]["kind"] == "text"))
        # Limits must be refused, not truncated. Check the two cheap ones; row overflow would need a
        # million-row fixture and tests the same branch.
        wide = {"sheets": [{"name": "넓음", "rows": [["x"] * (MAX_COLS + 1)]}]}
        try:
            build(wide, os.path.join(tmp, "wide.xlsx"))
            checks.append(("too many columns refused", False))
        except BuildError as exc:
            checks.append(("too many columns refused", "16384" in str(exc)))
        long_cell = {"sheets": [{"name": "긴셀", "rows": [["x" * (MAX_CELL_TEXT + 1)]]}]}
        try:
            build(long_cell, os.path.join(tmp, "long.xlsx"))
            checks.append(("oversized cell refused", False))
        except BuildError as exc:
            checks.append(("oversized cell refused", str(MAX_CELL_TEXT) in str(exc)))
        # A formula may sit beyond the row's data or on a row the data never reached.
        # Both used to be dropped, and a formula-only tail row was emitted once per
        # formula, producing a duplicate <row r="5">.
        mix_out = os.path.join(tmp, "mix.xlsx")
        build({"sheets": [{"name": "S", "rows": [["a", "b", "c"], ["x", 1, 2], ["합계"]],
                           "formulas": [{"ref": "D2", "formula": "=B2+C2"},
                                        {"ref": "B3", "formula": "=SUM(B2:B2)"},
                                        {"ref": "B5", "formula": "=1"},
                                        {"ref": "C5", "formula": "=2"}]}]}, mix_out)
        mix_wb = xlsxlib.Workbook(mix_out)
        mix_cells = {}
        for _n, _p, _s in mix_wb.sheets:
            for _rn, _cells in mix_wb.iter_rows(_p):
                for _c in _cells:
                    mix_cells[_c["ref"]] = _c["formula"]
        checks.append(("formula beside data kept", mix_cells.get("D2") == "=B2+C2"))
        checks.append(("formula inside data kept", mix_cells.get("B3") == "=SUM(B2:B2)"))
        checks.append(("formula tail row kept",
                       mix_cells.get("B5") == "=1" and mix_cells.get("C5") == "=2"))
        sheet_xml_text = mix_wb.parts["xl/worksheets/sheet1.xml"].decode("utf-8")
        checks.append(("no duplicate row element", sheet_xml_text.count('<row r="5"') == 1))
        # A chart reference that already names a sheet must not be qualified twice:
        # `Chart!Data!A2:A3` is malformed and renders an empty plot.
        chart_out = os.path.join(tmp, "chartref.xlsx")
        build({"sheets": [{"name": "Data", "rows": [["월", "매출"], ["1월", 10], ["2월", 20]]},
                          {"name": "차트", "rows": [["x"], [1]],
                           "charts": [{"type": "column", "title": "t", "anchor": "D2",
                                       "categories": "Data!A2:A3",
                                       "series": [{"name": "매출", "values": "Data!B2:B3"}]}]}]},
              chart_out)
        chart_wb = xlsxlib.Workbook(chart_out)
        chart_text = chart_wb.parts["xl/charts/chart1.xml"].decode("utf-8")
        refs = re.findall(r"<c:f>([^<]*)</c:f>", chart_text)
        checks.append(("chart ref not double qualified", refs == ["Data!A2:A3", "Data!B2:B3"]))
        # A digit code under a numeric format is re-typed by Excel too, but the lost
        # zero must be reported, not just happen.
        loss_spec = {"sheets": [{"name": "S", "rows": [["코드"], ["00123"]],
                                 "formats": [{"range": "A2", "code": "#,##0"}]}]}
        loss_out = os.path.join(tmp, "loss.xlsx")
        loss_meta = build(loss_spec, loss_out)
        checks.append(("coerced code counted", len(loss_meta["coercedCodes"]) == 1))
        text_spec = {"sheets": [{"name": "S", "rows": [["코드"], ["00123"]],
                                 "formats": [{"range": "A2", "code": "@"}]}]}
        text_meta = build(text_spec, os.path.join(tmp, "kept.xlsx"))
        checks.append(("text format keeps code", text_meta["coercedCodes"] == []))
        checks.append(("chart rels beside owner sheet",
                       "xl/worksheets/_rels/sheet2.xml.rels" in chart_wb.parts
                       and "xl/worksheets/_rels/sheet1.xml.rels" not in chart_wb.parts))
    failed = [name for name, ok in checks if not ok]
    print(json.dumps({"ok": not failed, "checks": len(checks), "failed": failed}, ensure_ascii=False))
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--spec")
    parser.add_argument("--csv")
    parser.add_argument("--out")
    parser.add_argument("--sheet", default="Sheet1")
    parser.add_argument("--encoding", default="auto")
    parser.add_argument("--delimiter")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.out:
        parser.print_usage(sys.stderr)
        return 2
    warnings = []
    try:
        if args.spec:
            with open(args.spec, encoding="utf-8") as fh:
                spec = json.load(fh)
        elif args.csv:
            parsed = read_csv_rows(args.csv, args.encoding, args.delimiter, args.limit)
            spec = csv_to_spec(parsed["rows"], args.sheet)
            warnings.append({"code": "I_CSV_DECODED",
                             "detail": "decoded as %s, delimiter %r, %d rows"
                                       % (parsed["encoding"], parsed["delimiter"], len(parsed["rows"]))})
            if parsed["encoding"] == "latin-1":
                warnings.append({"code": "W_ENCODING_GUESS",
                                 "detail": "fell back to latin-1; Korean text may be garbled. Pass --encoding cp949 explicitly."})
        else:
            raise BuildError("give --spec or --csv")
        meta = build(spec, args.out)
        if meta.get("coercedCodes"):
            warnings.append({
                "code": "W_LEADING_ZERO_LOST",
                "detail": "%d digit code(s) sit under a numeric format and lose their leading zero: %s. "
                          "Use the Text format ('@') on the cell or column to keep it."
                          % (len(meta["coercedCodes"]),
                             ", ".join("%s!%s (%s)" % (i["sheet"], i["ref"], i["value"])
                                       for i in meta["coercedCodes"][:10])),
                "count": len(meta["coercedCodes"]),
                "cells": [{"sheet": i["sheet"], "ref": i["ref"]} for i in meta["coercedCodes"]],
            })
        if meta.get("neutralized"):
            counts = {}
            for item in meta["neutralized"]:
                counts[item["sheet"]] = counts.get(item["sheet"], 0) + 1
            warnings.append({
                "code": "I_NEUTRALIZED",
                "detail": "%d value(s) started with = + - @ and were written as text: %s"
                          % (len(meta["neutralized"]),
                             ", ".join("%s!%s" % (i["sheet"], i["ref"]) for i in meta["neutralized"][:10])),
                "count": len(meta["neutralized"]),
                "cells": [{"sheet": i["sheet"], "ref": i["ref"]} for i in meta["neutralized"]],
            })
    except BuildError as exc:
        print(json.dumps({"ok": False, "error": "E_SPEC", "detail": str(exc)}, ensure_ascii=False))
        return 1
    with open(args.out, "rb") as fh:
        raw = fh.read()
    print(json.dumps({"schemaVersion": 1, "path": args.out, "size": len(raw),
                      "sha256": xlsxlib.digest(raw), "sheets": meta["sheets"],
                      "parts": meta["parts"], "warnings": warnings},
                     ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

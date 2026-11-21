#!/usr/bin/env python3
"""Edit an .xlsx in place without disturbing anything you did not name.

Usage:
    python3 patch_workbook.py <in.xlsx> --out <out.xlsx> [operations...] [--dry-run]
    python3 patch_workbook.py <in.xlsx> --in-place [operations...] [--backup]
    python3 patch_workbook.py --self-test

Operations (each repeatable):
    --set-value    "SHEET!REF=VALUE"        write a literal; numbers, TRUE/FALSE, and
                                            %-values become numeric, everything else text
    --set-formula  "SHEET!REF==SUM(B2:B9)"  write a formula (a leading = is optional)
    --set-format   "SHEET!RANGE=CODE"       number format, e.g. '#,##0"원"' or 'yyyy-mm-dd'
    --set-width    "SHEET!COL=WIDTH"        column width in characters, e.g. 'B=14.5'
    --freeze       "SHEET!REF"              freeze panes above and left of REF
    --validation   "SHEET!RANGE=JSON"       data validation, JSON keys: type, operator,
                                            formula1, formula2, allowBlank, prompt, error
    --cond-format  "SHEET!RANGE=JSON"       conditional format, JSON keys: type (cellIs,
                                            expression, colorScale, dataBar, top10),
                                            operator, formula, fill, fontColor, minColor,
                                            midColor, maxColor
    --add-sheet    "NAME"                   append a worksheet at the end
    --rename-sheet "OLD=NEW"
    --recalc                                set fullCalcOnLoad so Excel recomputes on open
    --strip-calc-chain                      remove calcChain.xml (stale chain after edits)

Preservation contract: only the parts named by an operation are rewritten. Sheet
XML is edited by locating the exact `<c>`/`<row>`/`<cols>` node and replacing just
that node; every other byte of every other part is copied through unchanged. Strings
are written as inlineStr so sharedStrings.xml is never touched. Styles are appended,
never renumbered. The output is verified before it replaces anything: the tool
re-opens the result, compares every part you did not touch by digest, and fails
rather than writing a workbook that lost formatting, formulas, or media.

Exit codes: 0 written, 1 verification failed and nothing replaced the input,
2 usage or unreadable input. `--dry-run` prints the plan and writes nothing.
"""

import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from xml.sax.saxutils import escape, unescape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlib  # noqa: E402

M_NS = xlsxlib.NS["m"]
R_NS = xlsxlib.NS["r"]


class PatchError(Exception):
    pass


# ---------------------------------------------------------------------------
# Small XML utilities that never re-serialize a whole document
# ---------------------------------------------------------------------------

CELL_ATTRS = r"(?:[^>/]|/(?!>))*"
"""Attribute run that stops before a self-closing `/>`.

Plain `[^>]*` also consumes the trailing slash, so `(?:/>|>.*?</c>)` then matches
`>.*?</c>` and swallows the following sibling cell as if it were this one's body.
"""


def find_cell_span(xml, ref):
    """Return (start, end) of the <c r="ref"> element, or None."""
    pattern = re.compile(r'<c\b%s\br="%s"%s(?:/>|>.*?</c>)' % (CELL_ATTRS, re.escape(ref), CELL_ATTRS), re.DOTALL)
    m = pattern.search(xml)
    return (m.start(), m.end()) if m else None


def find_row_span(xml, row_no):
    pattern = re.compile(r'<row\b%s\br="%d"%s(?:/>|>.*?</row>)' % (CELL_ATTRS, row_no, CELL_ATTRS), re.DOTALL)
    m = pattern.search(xml)
    return (m.start(), m.end()) if m else None


def sheet_data_span(xml):
    start = xml.find("<sheetData")
    if start < 0:
        raise PatchError("sheet XML has no sheetData")
    open_end = xml.find(">", start)
    if xml[open_end - 1] == "/":
        return (start, open_end + 1, True)
    end = xml.find("</sheetData>")
    if end < 0:
        raise PatchError("sheetData is not closed")
    return (start, end + len("</sheetData>"), False)


def rows_of(sheet_xml):
    """[(row_no, span_start, span_end)] in document order."""
    out = []
    for m in re.finditer(r'<row\b%s\br="(\d+)"%s(?:/>|>.*?</row>)' % (CELL_ATTRS, CELL_ATTRS), sheet_xml, re.DOTALL):
        out.append((int(m.group(1)), m.start(), m.end()))
    return out


def cell_attrs(cell_xml):
    head = cell_xml[:cell_xml.find(">") + 1]
    attrs = {}
    for key, value in re.findall(r'([\w:]+)="([^"]*)"', head):
        attrs[key] = unescape(value)
    return attrs


def build_cell(ref, attrs, body):
    """Render one <c> element with attributes in a stable order."""
    order = ["r", "s", "t"]
    parts = []
    for key in order:
        if key in attrs and attrs[key] is not None:
            parts.append('%s="%s"' % (key, escape(str(attrs[key]), {'"': "&quot;"})))
    for key, value in attrs.items():
        if key not in order and value is not None:
            parts.append('%s="%s"' % (key, escape(str(value), {'"': "&quot;"})))
    if body is None:
        return "<c %s/>" % " ".join(parts)
    return "<c %s>%s</c>" % (" ".join(parts), body)


def literal_xml(value, as_text):
    """Return (type_attr or None, body_xml) for a literal value."""
    if as_text:
        return ("inlineStr", "<is><t>%s</t></is>" % escape(value))
    text = value.strip()
    if text.upper() in ("TRUE", "FALSE"):
        return ("b", "<v>%s</v>" % ("1" if text.upper() == "TRUE" else "0"))
    percent = text.endswith("%")
    numeric = text[:-1] if percent else text
    numeric = numeric.replace(",", "")
    try:
        number = float(numeric)
    except ValueError:
        return ("inlineStr", "<is><t>%s</t></is>" % escape(value))
    if percent:
        number = number / 100.0
    if number == int(number) and abs(number) < 1e16:
        rendered = str(int(number))
    else:
        rendered = repr(number)
    return (None, "<v>%s</v>" % rendered)


def insert_into_row(row_xml, row_no, ref, cell_xml):
    """Insert a cell into an existing row, keeping column order."""
    target_col = xlsxlib.parse_ref(ref)[0]
    if row_xml.rstrip().endswith("/>"):
        head = row_xml.rstrip()[:-2].rstrip()
        return "%s>%s</row>" % (head, cell_xml)
    inner_start = row_xml.find(">") + 1
    inner_end = row_xml.rfind("</row>")
    inner = row_xml[inner_start:inner_end]
    for m in re.finditer(r'<c\b%s\br="([A-Z]{1,3})\d+"%s(?:/>|>.*?</c>)' % (CELL_ATTRS, CELL_ATTRS), inner, re.DOTALL):
        col = xlsxlib.col_index(m.group(1))
        if col > target_col:
            pos = inner_start + m.start()
            return row_xml[:pos] + cell_xml + row_xml[pos:]
    return row_xml[:inner_end] + cell_xml + row_xml[inner_end:]


def new_row(row_no, cell_xml):
    return '<row r="%d">%s</row>' % (row_no, cell_xml)


def put_cell(sheet_xml, ref, cell_xml):
    col, row = xlsxlib.parse_ref(ref)
    if not col:
        raise PatchError("bad cell reference %r" % ref)
    span = find_cell_span(sheet_xml, ref)
    if span:
        return sheet_xml[:span[0]] + cell_xml + sheet_xml[span[1]:]
    rspan = find_row_span(sheet_xml, row)
    if rspan:
        updated = insert_into_row(sheet_xml[rspan[0]:rspan[1]], row, ref, cell_xml)
        return sheet_xml[:rspan[0]] + updated + sheet_xml[rspan[1]:]
    # Create the row in row-number order.
    data_start, data_end, self_closing = sheet_data_span(sheet_xml)
    if self_closing:
        replacement = '<sheetData>%s</sheetData>' % new_row(row, cell_xml)
        return sheet_xml[:data_start] + replacement + sheet_xml[data_end:]
    for existing_row, start, end in rows_of(sheet_xml):
        if existing_row > row:
            return sheet_xml[:start] + new_row(row, cell_xml) + sheet_xml[start:]
    return sheet_xml[:data_end - len("</sheetData>")] + new_row(row, cell_xml) + sheet_xml[data_end - len("</sheetData>"):]


# ---------------------------------------------------------------------------
# Styles: append-only
# ---------------------------------------------------------------------------

def style_ops(styles_xml, code):
    """Return (new_styles_xml, cellXfs_index) for a number format code."""
    styles = xlsxlib.ET.fromstring(styles_xml.encode("utf-8"))
    ns = "{%s}" % M_NS
    numfmts = {}
    existing_fmt = None
    for nf in styles.iter(ns + "numFmt"):
        numfmts[int(nf.get("numFmtId"))] = nf.get("formatCode")
    for fmt_id, fmt_code in numfmts.items():
        if fmt_code == code:
            existing_fmt = fmt_id
            break
    xfs = styles.find(ns + "cellXfs")
    if xfs is None:
        raise PatchError("styles.xml has no cellXfs")
    xf_list = xfs.findall(ns + "xf")
    if existing_fmt is not None:
        for index, xf in enumerate(xf_list):
            if int(xf.get("numFmtId") or 0) == existing_fmt:
                return (styles_xml, index)
    # A new format id must be >= 164 (the custom range) and unused.
    next_fmt = 164
    if numfmts:
        next_fmt = max(164, max(numfmts) + 1)
    fmt_id = existing_fmt if existing_fmt is not None else next_fmt
    new_xf = '<xf numFmtId="%d" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' % fmt_id
    if xfs.get("count") is not None:
        styles_xml = re.sub(r'(<cellXfs\b[^>]*\bcount=")(\d+)(")',
                            lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3), styles_xml, count=1)
    if "</cellXfs>" in styles_xml:
        styles_xml = styles_xml.replace("</cellXfs>", new_xf + "</cellXfs>", 1)
    else:
        raise PatchError("cellXfs is self-closing; cannot append")
    if existing_fmt is None:
        new_fmt = '<numFmt numFmtId="%d" formatCode="%s"/>' % (fmt_id, escape(code, {'"': "&quot;"}))
        if "<numFmts" in styles_xml:
            if re.search(r"<numFmts\b[^>]*/>", styles_xml):
                styles_xml = re.sub(r"<numFmts\b([^>]*)/>",
                                    lambda m: "<numFmts%s>%s</numFmts>" % (m.group(1), new_fmt), styles_xml, count=1)
            else:
                styles_xml = re.sub(r'(<numFmts\b[^>]*\bcount=")(\d+)(")',
                                    lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3), styles_xml, count=1)
                styles_xml = styles_xml.replace("</numFmts>", new_fmt + "</numFmts>", 1)
        else:
            block = '<numFmts count="1">%s</numFmts>' % new_fmt
            anchor = re.search(r"<styleSheet\b[^>]*>", styles_xml)
            if not anchor:
                raise PatchError("styles.xml has no styleSheet element")
            styles_xml = styles_xml[:anchor.end()] + block + styles_xml[anchor.end():]
    return (styles_xml, len(xf_list))


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def parse_assign(spec, name):
    if "=" not in spec:
        raise PatchError("%s needs SHEET!REF=VALUE, got %r" % (name, spec))
    left, _, right = spec.partition("=")
    if "!" not in left:
        raise PatchError("%s needs a sheet qualifier, got %r" % (name, spec))
    sheet, _, ref = left.partition("!")
    return (sheet.strip(), ref.strip(), right)


class Editor:
    def __init__(self, path):
        self.path = path
        self.wb = xlsxlib.Workbook(path)
        self.parts = dict(self.wb.parts)
        self.touched = set()
        self.plan = []
        self.sheet_parts = {name: part for name, part, state in self.wb.sheets if part and state != "chartsheet"}

    def part_for(self, sheet):
        if sheet not in self.sheet_parts:
            raise PatchError("no worksheet named %r (have: %s)" % (sheet, ", ".join(sorted(self.sheet_parts))))
        return self.sheet_parts[sheet]

    def edit_sheet(self, sheet, fn):
        part = self.part_for(sheet)
        xml = self.parts[part].decode("utf-8")
        updated = fn(xml)
        if updated != xml:
            self.parts[part] = updated.encode("utf-8")
            self.touched.add(part)

    def edit_styles(self, fn):
        part = self.wb.rel_target(self.wb.workbook[0], "styles") or "xl/styles.xml"
        if part not in self.parts:
            raise PatchError("workbook has no styles part; number formats cannot be applied")
        xml = self.parts[part].decode("utf-8")
        updated = fn(xml)
        if updated != xml:
            self.parts[part] = updated.encode("utf-8")
            self.touched.add(part)

    def edit_workbook(self, fn):
        part = self.wb.workbook[0]
        xml = self.parts[part].decode("utf-8")
        updated = fn(xml)
        if updated != xml:
            self.parts[part] = updated.encode("utf-8")
            self.touched.add(part)

    # -- operations -----------------------------------------------------
    def set_value(self, spec, as_text=False):
        sheet, ref, value = parse_assign(spec, "--set-value")
        ctype, body = literal_xml(value, as_text)

        def apply(xml):
            span = find_cell_span(xml, ref)
            attrs = {"r": ref}
            if span:
                attrs = cell_attrs(xml[span[0]:span[1]])
            attrs["r"] = ref
            if ctype is None:
                attrs.pop("t", None)
            else:
                attrs["t"] = ctype
            return put_cell(xml, ref, build_cell(ref, attrs, body))

        self.edit_sheet(sheet, apply)
        self.plan.append({"op": "set-value", "sheet": sheet, "ref": ref, "value": value, "asText": as_text})

    def set_formula(self, spec):
        sheet, ref, formula = parse_assign(spec, "--set-formula")
        formula = formula.strip()
        if formula.startswith("="):
            formula = formula[1:]

        def apply(xml):
            span = find_cell_span(xml, ref)
            attrs = {"r": ref}
            if span:
                attrs = cell_attrs(xml[span[0]:span[1]])
            attrs["r"] = ref
            attrs.pop("t", None)  # a formula's type is numeric unless it returns text
            body = "<f>%s</f>" % escape(formula)
            return put_cell(xml, ref, build_cell(ref, attrs, body))

        self.edit_sheet(sheet, apply)
        self.plan.append({"op": "set-formula", "sheet": sheet, "ref": ref, "formula": "=" + formula})

    def set_format(self, spec):
        sheet, ref_range, code = parse_assign(spec, "--set-format")
        if not code:
            raise PatchError("--set-format needs a format code after =")
        index_holder = {}

        def apply_styles(xml):
            updated, index = style_ops(xml, code)
            index_holder["index"] = index
            return updated

        self.edit_styles(apply_styles)
        style_index = index_holder["index"]
        bounds = xlsxlib.range_bounds(ref_range)
        if not bounds:
            raise PatchError("bad range %r" % ref_range)

        def apply_sheet(xml):
            for row in range(bounds[1], bounds[3] + 1):
                for col in range(bounds[0], bounds[2] + 1):
                    ref = "%s%d" % (xlsxlib.col_letters(col), row)
                    span = find_cell_span(xml, ref)
                    if span:
                        attrs = cell_attrs(xml[span[0]:span[1]])
                        attrs["s"] = style_index
                        body = None
                        if xml[span[0]:span[1]].rstrip().endswith("/>"):
                            body = None
                        else:
                            inner_start = xml.find(">", span[0]) + 1
                            body = xml[inner_start:span[1] - len("</c>")]
                        xml = xml[:span[0]] + build_cell(ref, attrs, body) + xml[span[1]:]
                    else:
                        xml = put_cell(xml, ref, build_cell(ref, {"r": ref, "s": style_index}, None))
            return xml

        self.edit_sheet(sheet, apply_sheet)
        self.plan.append({"op": "set-format", "sheet": sheet, "range": ref_range, "code": code, "styleIndex": style_index})

    def set_width(self, spec):
        sheet, col, width = parse_assign(spec, "--set-width")
        index = xlsxlib.col_index(col.strip())
        if not index:
            raise PatchError("bad column %r" % col)
        try:
            numeric = float(width)
        except ValueError:
            raise PatchError("bad width %r" % width)
        entry = '<col min="%d" max="%d" width="%s" customWidth="1"/>' % (index, index, ("%g" % numeric))

        def apply(xml):
            xml = re.sub(r'<col\b[^>]*\bmin="%d"[^>]*\bmax="%d"[^>]*/>' % (index, index), entry, xml, count=1)
            if entry in xml:
                return xml
            if "<cols>" in xml:
                return xml.replace("</cols>", entry + "</cols>", 1)
            if re.search(r"<cols\b[^>]*/>", xml):
                return re.sub(r"<cols\b([^>]*)/>", lambda m: "<cols%s>%s</cols>" % (m.group(1), entry), xml, count=1)
            anchor = re.search(r"<sheetFormatPr\b[^>]*/>", xml)
            if anchor:
                return xml[:anchor.end()] + "<cols>%s</cols>" % entry + xml[anchor.end():]
            anchor = re.search(r"<sheetData", xml)
            return xml[:anchor.start()] + "<cols>%s</cols>" % entry + xml[anchor.start():]

        self.edit_sheet(sheet, apply)
        self.plan.append({"op": "set-width", "sheet": sheet, "col": col, "width": numeric})

    def freeze(self, spec):
        sheet, _, ref = spec.partition("!")
        if not ref:
            raise PatchError("--freeze needs SHEET!REF")
        col, row = xlsxlib.parse_ref(ref)
        if not col:
            raise PatchError("bad freeze cell %r" % ref)
        xsplit = col - 1
        ysplit = row - 1
        attrs = []
        if xsplit:
            attrs.append('xSplit="%d"' % xsplit)
        if ysplit:
            attrs.append('ySplit="%d"' % ysplit)
        attrs.extend(['topLeftCell="%s"' % ref, 'activePane="bottomRight"', 'state="frozen"'])
        pane = "<pane %s/>" % " ".join(attrs)

        def apply(xml):
            if "<pane " in xml:
                return re.sub(r"<pane\b[^>]*/>", pane, xml, count=1)
            m = re.search(r"<sheetView\b[^>]*?(/>|>)", xml)
            if not m:
                anchor = re.search(r"<sheetViews\b[^>]*>", xml)
                if not anchor:
                    raise PatchError("sheet has no sheetViews element")
                block = '<sheetViews><sheetView workbookViewId="0">%s</sheetView></sheetViews>' % pane
                return xml[:anchor.start()] + block + xml[anchor.end():]
            if m.group(1) == "/>":
                head = xml[:m.start()] + re.sub(r"/>$", ">", xml[m.start():m.end()])
                return head + pane + "</sheetView>" + xml[m.end():]
            return xml[:m.end()] + pane + xml[m.end():]

        self.edit_sheet(sheet, apply)
        self.plan.append({"op": "freeze", "sheet": sheet, "ref": ref})

    def validation(self, spec):
        sheet, ref_range, payload = parse_assign(spec, "--validation")
        try:
            conf = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise PatchError("--validation payload is not JSON: %s" % exc)
        attrs = ['sqref="%s"' % ref_range]
        mapping = {"type": "type", "operator": "operator", "allowBlank": "allowBlank",
                   "prompt": "prompt", "promptTitle": "promptTitle", "error": "error",
                   "errorTitle": "errorTitle", "errorStyle": "errorStyle"}
        for key, attr in mapping.items():
            if key in conf and conf[key] is not None:
                attrs.append('%s="%s"' % (attr, escape(str(conf[key]), {'"': "&quot;"})))
        if "prompt" in conf or "error" in conf:
            attrs.append('showInputMessage="1"')
            attrs.append('showErrorMessage="1"')
        body = ""
        if conf.get("formula1") is not None:
            body += "<formula1>%s</formula1>" % escape(str(conf["formula1"]))
        if conf.get("formula2") is not None:
            body += "<formula2>%s</formula2>" % escape(str(conf["formula2"]))
        node = "<dataValidation %s>%s</dataValidation>" % (" ".join(attrs), body)

        def apply(xml):
            if "<dataValidations" in xml:
                xml = re.sub(r'(<dataValidations\b[^>]*\bcount=")(\d+)(")',
                             lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3), xml, count=1)
                return xml.replace("</dataValidations>", node + "</dataValidations>", 1)
            block = '<dataValidations count="1">%s</dataValidations>' % node
            anchor = re.search(r"<hyperlinks\b|<pageMargins\b|<drawing\b|<tableParts\b|<extLst\b", xml)
            if anchor:
                return xml[:anchor.start()] + block + xml[anchor.start():]
            return xml.replace("</worksheet>", block + "</worksheet>", 1)

        self.edit_sheet(sheet, apply)
        self.plan.append({"op": "validation", "sheet": sheet, "range": ref_range, "config": conf})

    def register_dxf(self, font_color=None, fill=None):
        """Append a differential style to styles.xml and return its index."""
        holder = {}

        def apply(xml):
            node = "<dxf>"
            if font_color:
                node += '<font><color rgb="%s"/></font>' % font_color.lstrip("#").upper()
            if fill:
                node += '<fill><patternFill><bgColor rgb="%s"/></patternFill></fill>' % fill.lstrip("#").upper()
            node += "</dxf>"
            found = re.search(r"<dxfs\b[^>]*\bcount=\"(\d+)\"[^>]*>(.*?)</dxfs>", xml, re.DOTALL)
            if found:
                holder["index"] = int(found.group(1))
                updated = xml[:found.end(1)] + str(int(found.group(1)) + 1) + xml[found.end(1):]
                return updated.replace("</dxfs>", node + "</dxfs>", 1)
            if re.search(r"<dxfs\b[^>]*/>", xml):
                holder["index"] = 0
                return re.sub(r"<dxfs\b([^>]*)/>", lambda m: "<dxfs%s>%s</dxfs>" % (
                    re.sub(r'\s*count="\d+"', "", m.group(1)), node), xml, count=1)
            holder["index"] = 0
            block = '<dxfs count="1">%s</dxfs>' % node
            return xml.replace("</styleSheet>", block + "</styleSheet>", 1)

        self.edit_styles(apply)
        return holder.get("index", 0)

    def cond_format(self, spec):
        sheet, ref_range, payload = parse_assign(spec, "--cond-format")
        try:
            conf = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise PatchError("--cond-format payload is not JSON: %s" % exc)
        kind = conf.get("type", "cellIs")
        priority = conf.get("priority", 1)
        rule_attrs = ['type="%s"' % kind, 'priority="%d"' % priority]
        inner = ""
        if kind in ("cellIs", "expression"):
            if conf.get("operator"):
                rule_attrs.append('operator="%s"' % conf["operator"])
            for formula in conf.get("formula", []):
                inner += "<formula>%s</formula>" % escape(str(formula))
            if conf.get("fill") or conf.get("fontColor"):
                dxf_index = self.register_dxf(conf.get("fontColor"), conf.get("fill"))
                rule_attrs.append('dxfId="%d"' % dxf_index)
        elif kind == "colorScale":
            inner += '<colorScale><cfvo type="min"/><cfvo type="max"/>'
            inner += '<color rgb="%s"/><color rgb="%s"/></colorScale>' % (
                (conf.get("minColor") or "#F8696B").lstrip("#").upper(),
                (conf.get("maxColor") or "#63BE7B").lstrip("#").upper())
        elif kind == "dataBar":
            inner += ('<dataBar><cfvo type="min"/><cfvo type="max"/><color rgb="%s"/></dataBar>'
                      % (conf.get("color") or "#638EC6").lstrip("#").upper())
        node = '<conditionalFormatting sqref="%s"><cfRule %s>%s</cfRule></conditionalFormatting>' % (
            ref_range, " ".join(rule_attrs), inner)

        def apply(xml):
            anchor = re.search(r"<dataValidations\b|<hyperlinks\b|<pageMargins\b|<drawing\b|<extLst\b", xml)
            if anchor:
                return xml[:anchor.start()] + node + xml[anchor.start():]
            return xml.replace("</worksheet>", node + "</worksheet>", 1)

        self.edit_sheet(sheet, apply)
        self.plan.append({"op": "cond-format", "sheet": sheet, "range": ref_range, "config": conf})

    def add_sheet(self, name):
        if any(n == name for n, _, _ in self.wb.sheets):
            raise PatchError("a sheet named %r already exists" % name)
        existing = [p for p in self.parts if re.match(r"^xl/worksheets/sheet\d+\.xml$", p)]
        index = 1 + max([int(re.search(r"(\d+)", p).group(1)) for p in existing] or [0])
        part = "xl/worksheets/sheet%d.xml" % index
        rid = "rIdSheet%d" % index
        self.parts[part] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="%s" xmlns:r="%s"><sheetData/></worksheet>' % (M_NS, R_NS)
        ).encode("utf-8")
        self.touched.add(part)

        def apply_wb(xml):
            sheet_id = 1 + max([int(x) for x in re.findall(r'<sheet\b[^>]*\bsheetId="(\d+)"', xml)] or [0])
            node = '<sheet name="%s" sheetId="%d" r:id="%s"/>' % (
                escape(name, {'"': "&quot;"}), sheet_id, rid)
            return xml.replace("</sheets>", node + "</sheets>", 1)

        self.edit_workbook(apply_wb)
        wb_part = self.wb.workbook[0]
        rels_part = os.path.join(os.path.dirname(wb_part), "_rels", os.path.basename(wb_part) + ".rels").replace(os.sep, "/")
        rels_xml = self.parts[rels_part].decode("utf-8")
        rel = ('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>'
               % (rid, index))
        self.parts[rels_part] = rels_xml.replace("</Relationships>", rel + "</Relationships>", 1).encode("utf-8")
        self.touched.add(rels_part)
        content_types = self.parts.get("[Content_Types].xml", b"").decode("utf-8")
        if content_types and "/xl/worksheets/sheet%d.xml" % index not in content_types:
            override = ('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                        % index)
            self.parts["[Content_Types].xml"] = content_types.replace("</Types>", override + "</Types>", 1).encode("utf-8")
            self.touched.add("[Content_Types].xml")
        self.sheet_parts[name] = part
        self.plan.append({"op": "add-sheet", "name": name, "part": part})

    def rename_sheet(self, spec):
        old, _, new = spec.partition("=")
        old, new = old.strip(), new.strip()
        if not new:
            raise PatchError("--rename-sheet needs OLD=NEW")

        def apply(xml):
            return re.sub(r'(<sheet\b[^>]*\bname=")%s(")' % re.escape(escape(old, {'"': "&quot;"})),
                          lambda m: m.group(1) + escape(new, {'"': "&quot;"}) + m.group(2), xml, count=1)

        self.edit_workbook(apply)
        self.plan.append({"op": "rename-sheet", "from": old, "to": new,
                          "warning": "formulas and defined names that quote the old name are not rewritten"})

    def recalc(self):
        def apply(xml):
            if "<calcPr" in xml:
                if 'fullCalcOnLoad="1"' in xml:
                    return xml
                return re.sub(r"<calcPr\b([^>]*?)/>",
                              lambda m: '<calcPr%s fullCalcOnLoad="1"/>' % re.sub(r'\s*fullCalcOnLoad="[^"]*"', "", m.group(1)),
                              xml, count=1)
            return xml.replace("</workbook>", '<calcPr fullCalcOnLoad="1"/></workbook>', 1)

        self.edit_workbook(apply)
        self.plan.append({"op": "recalc"})

    def strip_calc_chain(self):
        removed = [p for p in self.parts if p.endswith("calcChain.xml")]
        for part in removed:
            del self.parts[part]
            self.touched.add(part)
        wb_part = self.wb.workbook[0]
        rels_part = os.path.join(os.path.dirname(wb_part), "_rels", os.path.basename(wb_part) + ".rels").replace(os.sep, "/")
        if rels_part in self.parts:
            xml = self.parts[rels_part].decode("utf-8")
            updated = re.sub(r'<Relationship\b[^>]*calcChain[^>]*/>', "", xml)
            if updated != xml:
                self.parts[rels_part] = updated.encode("utf-8")
                self.touched.add(rels_part)
        if "[Content_Types].xml" in self.parts:
            xml = self.parts["[Content_Types].xml"].decode("utf-8")
            updated = re.sub(r'<Override\b[^>]*calcChain[^>]*/>', "", xml)
            if updated != xml:
                self.parts["[Content_Types].xml"] = updated.encode("utf-8")
                self.touched.add("[Content_Types].xml")
        self.plan.append({"op": "strip-calc-chain", "removed": removed})

    # -- write ----------------------------------------------------------
    def write(self, out_path):
        if os.path.abspath(out_path) == os.path.abspath(self.path):
            raise PatchError("use --in-place for the same path")
        tmp = out_path + ".tmp"
        with zipfile.ZipFile(self.path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                if info.filename in self.parts:
                    dst.writestr(info, self.parts[info.filename])
            for name, data in self.parts.items():
                if name not in {i.filename for i in src.infolist()}:
                    dst.writestr(name, data)
        os.replace(tmp, out_path)
        return out_path


def verify_patch(original, patched, touched):
    """Fail when a part that was not named changed, or a touched part broke."""
    problems = []
    before = xlsxlib.Workbook(original)
    after = xlsxlib.Workbook(patched)
    b = before.part_digests()
    a = after.part_digests()
    for name, digest_value in b.items():
        if name in touched:
            continue
        if name not in a:
            problems.append({"code": "PART_LOST", "detail": name})
        elif a[name] != digest_value:
            problems.append({"code": "UNTOUCHED_PART_CHANGED", "detail": name})
    for name in touched:
        if name not in a:
            problems.append({"code": "TOUCHED_PART_MISSING", "detail": name})
    # Every sheet the original had must still be readable with the same name order.
    if [n for n, _, _ in before.sheets] != [n for n, _, _ in after.sheets][:len(before.sheets)]:
        problems.append({"code": "SHEET_ORDER_CHANGED", "detail": "sheet names or order differ"})
    for name, part, state in before.sheets:
        if state == "chartsheet" or not part:
            continue
        try:
            list(after.iter_rows(part))
        except Exception as exc:
            problems.append({"code": "SHEET_UNREADABLE", "detail": "%s: %s" % (name, exc)})
    return problems


def run(args):
    if not os.path.isfile(args.workbook):
        raise PatchError("no such workbook: %s" % args.workbook)
    editor = Editor(args.workbook)
    for spec in args.set_value or []:
        editor.set_value(spec, as_text=args.as_text)
    for spec in args.set_formula or []:
        editor.set_formula(spec)
    for spec in args.set_format or []:
        editor.set_format(spec)
    for spec in args.set_width or []:
        editor.set_width(spec)
    for spec in args.freeze or []:
        editor.freeze(spec)
    for spec in args.validation or []:
        editor.validation(spec)
    for spec in args.cond_format or []:
        editor.cond_format(spec)
    for spec in args.add_sheet or []:
        editor.add_sheet(spec)
    for spec in args.rename_sheet or []:
        editor.rename_sheet(spec)
    if args.recalc:
        editor.recalc()
    if args.strip_calc_chain:
        editor.strip_calc_chain()
    if not editor.plan:
        raise PatchError("no operation given")
    if args.dry_run:
        return {"schemaVersion": 1, "dryRun": True, "path": args.workbook,
                "plan": editor.plan, "touchedParts": sorted(editor.touched)}
    out = args.workbook if args.in_place else args.out
    if not out:
        raise PatchError("--out is required unless --in-place is used")
    if args.in_place and args.backup:
        shutil.copy2(args.workbook, args.workbook + ".bak")
    target = out if not args.in_place else args.workbook + ".patched"
    editor.write(target)
    problems = verify_patch(args.workbook, target, editor.touched)
    if problems:
        os.unlink(target)
        raise PatchError("verification failed, nothing replaced: %s" % json.dumps(problems, ensure_ascii=False))
    if args.in_place:
        shutil.move(target, args.workbook)
        out = args.workbook
    report = {
        "schemaVersion": 1,
        "path": out,
        "input": args.workbook,
        "plan": editor.plan,
        "touchedParts": sorted(editor.touched),
        "verification": {"status": "pass", "untouchedPartsPreserved": True,
                         "sha256Before": xlsxlib.digest(open(args.workbook, "rb").read()),
                         "sha256After": xlsxlib.digest(open(out, "rb").read())},
    }
    return report


def self_test():
    """Patch a real workbook and prove untouched parts survived byte for byte."""
    import tempfile
    import zipfile as zf_mod
    from xml.sax.saxutils import escape as esc

    checks = []

    def build(dirpath):
        target = os.path.join(dirpath, "patch.xlsx")
        styles = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<styleSheet xmlns="%s">'
            '<fonts count="2"><font><sz val="11"/><name val="맑은 고딕"/></font><font><b/><sz val="11"/><name val="맑은 고딕"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
            '</styleSheet>' % M_NS
        )
        sheet = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="%s"><sheetPr><tabColor rgb="FF4472C4"/></sheetPr>'
            '<sheetViews><sheetView tabSelected="1" workbookViewId="0"/></sheetViews>'
            '<sheetFormatPr defaultRowHeight="15"/>'
            '<sheetData>'
            '<row r="1"><c r="A1" s="1" t="inlineStr"><is><t>항목</t></is></c>'
            '<c r="B1" s="1" t="inlineStr"><is><t>금액</t></is></c></row>'
            '<row r="2"><c r="A2" t="inlineStr"><is><t>매출</t></is></c><c r="B2"><v>1000</v></c></row>'
            '<row r="3"><c r="A3" t="inlineStr"><is><t>비용</t></is></c><c r="B3"><v>400</v></c></row>'
            '<row r="4"><c r="A4" t="inlineStr"><is><t>이익</t></is></c><c r="B4"><f>B2-B3</f><v>600</v></c></row>'
            '</sheetData><mergeCells count="1"><mergeCell ref="A6:B6"/></mergeCells></worksheet>' % M_NS
        )
        wbxml = ('<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="%s" xmlns:r="%s">'
                 '<sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>'
                 % (M_NS, R_NS, esc("손익")))
        rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="%s">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '</Relationships>' % xlsxlib.NS["pr"])
        root_rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="%s">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                     '</Relationships>' % xlsxlib.NS["pr"])
        with zf_mod.ZipFile(target, "w", zf_mod.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
            z.writestr("_rels/.rels", root_rels)
            z.writestr("xl/workbook.xml", wbxml)
            z.writestr("xl/_rels/workbook.xml.rels", rels)
            z.writestr("xl/worksheets/sheet1.xml", sheet)
            z.writestr("xl/styles.xml", styles)
        return target

    with tempfile.TemporaryDirectory() as tmp:
        src = build(tmp)
        out = os.path.join(tmp, "out.xlsx")
        args = argparse.Namespace(
            workbook=src, out=out, in_place=False, backup=False, dry_run=False, as_text=False,
            set_value=["손익!B5=1,234,567"], set_formula=["손익!B6==SUM(B2:B3)"],
            set_format=["손익!B2:B6=#,##0"], set_width=["손익!B=16"], freeze=["손익!A2"],
            validation=['손익!A2:A9={"type":"list","formula1":"\\"매출,비용,이익\\"","allowBlank":"1"}'],
            cond_format=['손익!B2:B9={"type":"cellIs","operator":"greaterThan","formula":["0"],"fill":"#C6EFCE"}'],
            add_sheet=["메모"], rename_sheet=[], recalc=True, strip_calc_chain=False)
        report = run(args)
        checks.append(("wrote output", os.path.isfile(out)))
        checks.append(("verification passed", report["verification"]["status"] == "pass"))
        after = xlsxlib.Workbook(out)
        cells = {}
        for row_no, row in after.iter_rows("xl/worksheets/sheet1.xml"):
            for cell in row:
                cells[cell["ref"]] = cell
        checks.append(("new literal", cells["B5"]["value"] == 1234567))
        checks.append(("new formula", cells["B6"]["formula"] == "=SUM(B2:B3)"))
        checks.append(("existing formula kept", cells["B4"]["formula"] == "=B2-B3"))
        checks.append(("existing value kept", cells["B2"]["value"] == 1000))
        checks.append(("style applied", cells["B2"]["style"] > 0))
        checks.append(("number format", after.format_kind(cells["B2"]["style"]) == "number"))
        checks.append(("sheet added", [n for n, _, _ in after.sheets] == ["손익", "메모"]))
        features = after.sheet_features("xl/worksheets/sheet1.xml")
        checks.append(("merge kept", features["merged"] == ["A6:B6"]))
        checks.append(("freeze set", features["freeze"] is not None))
        checks.append(("validation set", len(features["validations"]) == 1))
        checks.append(("cond format set", len(features["conditional"]) == 1))
        checks.append(("recalc flag", after.calc_properties.get("fullCalcOnLoad") == "1"))
        checks.append(("col width", any(c["width"] == "16" for c in features["cols"])))
        # The styles part must have grown, not been renumbered.
        checks.append(("fonts preserved", len(after.styles["fonts"]) == 2))
    failed = [name for name, ok in checks if not ok]
    print(json.dumps({"ok": not failed, "checks": len(checks), "failed": failed}, ensure_ascii=False))
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("workbook", nargs="?")
    parser.add_argument("--out")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--as-text", action="store_true")
    parser.add_argument("--set-value", action="append")
    parser.add_argument("--set-formula", action="append")
    parser.add_argument("--set-format", action="append")
    parser.add_argument("--set-width", action="append")
    parser.add_argument("--freeze", action="append")
    parser.add_argument("--validation", action="append")
    parser.add_argument("--cond-format", action="append")
    parser.add_argument("--add-sheet", action="append")
    parser.add_argument("--rename-sheet", action="append")
    parser.add_argument("--recalc", action="store_true")
    parser.add_argument("--strip-calc-chain", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.workbook:
        parser.print_usage(sys.stderr)
        return 2
    try:
        report = run(args)
    except PatchError as exc:
        print(json.dumps({"ok": False, "error": "E_PATCH", "detail": str(exc)}, ensure_ascii=False))
        return 1
    except zipfile.BadZipFile:
        print(json.dumps({"ok": False, "error": "E_NOT_ZIP",
                          "detail": "not an OOXML package; a legacy .xls must be converted first"}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

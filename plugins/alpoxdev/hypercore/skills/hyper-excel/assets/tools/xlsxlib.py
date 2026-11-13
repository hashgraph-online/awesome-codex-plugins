"""Shared OOXML helpers for the hyper-excel toolchain.

Standard library only: an .xlsx is a zip of XML parts, so reading, inspecting, and
patching it needs no third-party package. Every function here reports what the file
actually stores; none of them guesses a value Excel never cached.
"""

import hashlib
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
M = "{%s}" % NS["m"]
R = "{%s}" % NS["r"]
PR = "{%s}" % NS["pr"]

# Built-in number formats that matter when deciding whether a cell holds a date,
# a percentage, or plain text. Ids 14-22 are the locale date/time set.
DATE_FMT_IDS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 45, 46, 47}
PERCENT_FMT_IDS = {9, 10}
CURRENCY_FMT_HINTS = ("$", "₩", "€", "£", "¥", "krw", "원")
DATE_FMT_HINTS = ("yy", "mm", "dd", "h:", "yyyy")
TEXT_FMT_IDS = {49}

ERROR_LITERALS = (
    "#NULL!", "#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NUM!", "#N/A",
    "#GETTING_DATA", "#SPILL!", "#CALC!", "#FIELD!", "#BLOCKED!", "#CONNECT!",
    "#UNKNOWN!", "#BUSY!", "#PYTHON!",
)
VOLATILE_FUNCS = ("NOW", "TODAY", "RAND", "RANDBETWEEN", "OFFSET", "INDIRECT", "INFO", "CELL")


def col_index(letters):
    """'A' -> 1, 'AB' -> 28. Case-insensitive; returns 0 for an empty string."""
    n = 0
    for ch in letters.upper():
        if "A" <= ch <= "Z":
            n = n * 26 + (ord(ch) - 64)
        else:
            return 0
    return n


def col_letters(index):
    """1 -> 'A', 28 -> 'AB'."""
    out = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


REF_RE = re.compile(r"^\$?([A-Za-z]{1,3})\$?(\d+)$")


def shift_formula(formula, row_delta, col_delta):
    """Shift the relative references in a formula by the given deltas.

    Absolute parts (`$A$1`) stay put, which is what Excel does when a shared
    formula is filled down or across.
    """
    if not formula or (row_delta == 0 and col_delta == 0):
        return formula
    pattern = re.compile(r"(\$?)([A-Za-z]{1,3})(\$?)(\d+)")

    def repl(m):
        col_abs, col_text, row_abs, row_text = m.groups()
        col = col_index(col_text)
        row = int(row_text)
        if not col or col > 16384 or row < 1:
            return m.group(0)
        new_col = col if col_abs else col + col_delta
        new_row = row if row_abs else row + row_delta
        if new_col < 1 or new_col > 16384 or new_row < 1 or new_row > 1048576:
            return m.group(0)
        return "%s%s%s%d" % (col_abs, col_letters(new_col), row_abs, new_row)

    return pattern.sub(repl, formula)


def parse_ref(ref):
    """'$B$7' -> (2, 7). Returns (0, 0) when the reference is not a single cell."""
    m = REF_RE.match(ref or "")
    if not m:
        return (0, 0)
    return (col_index(m.group(1)), int(m.group(2)))


def split_sheet_qualified(ref):
    """Split 'Sheet1!$A$1' or ''My Sheet'!A1:B2' into (sheet or None, range)."""
    if "!" not in (ref or ""):
        return (None, ref or "")
    sheet, _, cell = ref.rpartition("!")
    if sheet.startswith("'") and sheet.endswith("'"):
        sheet = sheet[1:-1].replace("''", "'")
    return (sheet, cell)


MAX_ROW = 1048576


def range_bounds(ref):
    """'B2:D9' -> (2, 2, 4, 9) as (min_col, min_row, max_col, max_row).

    Whole-column (`A:A`) and whole-row (`3:3`) references are accepted so a format
    can cover a column rather than an enumerated cell list; a missing side takes the
    sheet limit.
    """
    ref = (ref or "").replace("$", "")
    if not ref:
        return None
    first, _, last = ref.partition(":")
    if first.isdigit() or (last and last.isdigit()):
        rows = [int(x) for x in (first, last) if x.isdigit()]
        if not rows:
            return None
        return (1, min(rows), MAX_COLS, max(rows))
    c1, r1 = parse_ref(first)
    if not c1:
        c1 = col_index(first) if first.isalpha() else 0
        if not c1:
            return None
        r1 = 1
    if last:
        c2, r2 = parse_ref(last)
        if not c2:
            c2 = col_index(last) if last.isalpha() else 0
            if not c2:
                return None
            r2 = MAX_ROW
    else:
        c2, r2 = c1, r1
    return (min(c1, c2), min(r1, r2), max(c1, c2), max(r1, r2))


def in_range(col, row, bounds):
    if not bounds:
        return False
    c1, r1, c2, r2 = bounds
    return c1 <= col <= c2 and r1 <= row <= r2


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Workbook:
    """Read-only view over an OOXML package that keeps every part's bytes."""

    def __init__(self, path):
        self.path = path
        with zipfile.ZipFile(path) as zf:
            self.parts = {name: zf.read(name) for name in zf.namelist()}
        self._rels = {}
        self._sheets = None
        self._shared = None
        # Cells whose shared-string index points past the table. A broken index means
        # lost text, so it is recorded instead of silently becoming an empty cell.
        self.broken_string_refs = []
        self.shared_si_conflicts = []
        self._styles = None
        self._workbook = None

    # -- package plumbing ---------------------------------------------------
    def part(self, name):
        return self.parts.get(name)

    def rels(self, part_name):
        """Relationship id -> (type, target-resolved-path) for one part."""
        if part_name in self._rels:
            return self._rels[part_name]
        base = posixpath.dirname(part_name)
        rels_name = posixpath.join(base, "_rels", posixpath.basename(part_name) + ".rels")
        out = {}
        raw = self.parts.get(rels_name)
        if raw:
            for rel in ET.fromstring(raw):
                target = rel.get("Target") or ""
                if rel.get("TargetMode") == "External":
                    resolved = target
                elif target.startswith("/"):
                    resolved = target.lstrip("/")
                else:
                    resolved = posixpath.normpath(posixpath.join(base, target))
                out[rel.get("Id")] = (rel.get("Type") or "", resolved)
        self._rels[part_name] = out
        return out

    def rel_target(self, part_name, type_suffix):
        for _, (rtype, resolved) in self.rels(part_name).items():
            if rtype.endswith(type_suffix):
                return resolved
        return None

    # -- workbook level -----------------------------------------------------
    @property
    def workbook(self):
        if self._workbook is None:
            name = self.rel_target("", "officeDocument") or "xl/workbook.xml"
            raw = self.parts.get(name)
            self._workbook = (name, ET.fromstring(raw) if raw else None)
        return self._workbook

    @property
    def sheet_dir(self):
        return posixpath.dirname(self.workbook[0])

    @property
    def date1904(self):
        _, wb = self.workbook
        if wb is None:
            return False
        pr = wb.find("m:workbookPr", NS)
        return bool(pr is not None and (pr.get("date1904") in ("1", "true")))

    @property
    def sheets(self):
        """[(name, part_path, state)] in workbook order."""
        if self._sheets is not None:
            return self._sheets
        _, wb = self.workbook
        out = []
        if wb is not None:
            rels = self.rels(self.workbook[0])
            for sheet in wb.findall("m:sheets/m:sheet", NS):
                rid = sheet.get(R + "id")
                rtype, target = rels.get(rid, ("", ""))
                if not target or "chartsheet" in rtype:
                    out.append((sheet.get("name"), target, "chartsheet"))
                    continue
                out.append((sheet.get("name"), target, sheet.get("state") or "visible"))
        self._sheets = out
        return out

    @property
    def defined_names(self):
        _, wb = self.workbook
        out = []
        if wb is None:
            return out
        for dn in wb.findall("m:definedNames/m:definedName", NS):
            out.append({
                "name": dn.get("name"),
                "scope": "workbook" if dn.get("localSheetId") is None else "sheet:%s" % dn.get("localSheetId"),
                "formula": (dn.text or "").strip(),
                "hidden": dn.get("hidden") in ("1", "true"),
            })
        return out

    @property
    def calc_properties(self):
        _, wb = self.workbook
        if wb is None:
            return {}
        pr = wb.find("m:calcPr", NS)
        return dict(pr.attrib) if pr is not None else {}

    # -- shared strings and styles -----------------------------------------
    @property
    def shared_strings(self):
        if self._shared is not None:
            return self._shared
        out = []
        name = self.rel_target(self.workbook[0], "sharedStrings") or posixpath.join(self.sheet_dir, "sharedStrings.xml")
        raw = self.parts.get(name)
        if raw:
            for si in ET.fromstring(raw).findall("m:si", NS):
                out.append(rich_text(si))
        self._shared = out
        return out

    @property
    def styles(self):
        """{'numfmts': {id: code}, 'xfs': [{'numFmtId', 'fontId', 'fillId', 'borderId', 'applyNumberFormat'}]}"""
        if self._styles is not None:
            return self._styles
        name = self.rel_target(self.workbook[0], "styles") or posixpath.join(self.sheet_dir, "styles.xml")
        raw = self.parts.get(name)
        numfmts, xfs, fonts, fills = {}, [], [], []
        if raw:
            root = ET.fromstring(raw)
            for nf in root.findall("m:numFmts/m:numFmt", NS):
                numfmts[int(nf.get("numFmtId"))] = nf.get("formatCode") or ""
            for xf in root.findall("m:cellXfs/m:xf", NS):
                xfs.append({
                    "numFmtId": int(xf.get("numFmtId") or 0),
                    "fontId": int(xf.get("fontId") or 0),
                    "fillId": int(xf.get("fillId") or 0),
                    "borderId": int(xf.get("borderId") or 0),
                    "applyNumberFormat": xf.get("applyNumberFormat"),
                })
            for font in root.findall("m:fonts/m:font", NS):
                colors = font.find("m:color", NS)
                bold = font.find("m:b", NS) is not None
                fonts.append({"bold": bold, "color": None if colors is None else colors.get("rgb") or colors.get("theme")})
            for fill in root.findall("m:fills/m:fill", NS):
                pf = fill.find("m:patternFill", NS)
                fg = pf.find("m:fgColor", NS) if pf is not None else None
                fills.append({"pattern": None if pf is None else pf.get("patternType"),
                              "fg": None if fg is None else (fg.get("rgb") or fg.get("theme"))})
        self._styles = {"numfmts": numfmts, "xfs": xfs, "fonts": fonts, "fills": fills}
        return self._styles

    def number_format(self, style_index):
        """Resolve a cellXfs index to (numFmtId, formatCode)."""
        styles = self.styles
        xfs = styles["xfs"]
        idx = style_index if 0 <= style_index < len(xfs) else 0
        if not xfs:
            return (0, "General")
        fmt_id = xfs[idx]["numFmtId"]
        return (fmt_id, styles["numfmts"].get(fmt_id, builtin_format(fmt_id)))

    def format_kind(self, style_index):
        """Classify the number format: text, date, percent, currency, number, general.

        Cached per style index: a 100k-row sheet repeats a handful of styles, and
        re-parsing each format code per cell dominates a large read.
        """
        cache = self.__dict__.setdefault("_kind_cache", {})
        if style_index in cache:
            return cache[style_index]
        fmt_id, code = self.number_format(style_index)
        low = (code or "").lower()
        if fmt_id in TEXT_FMT_IDS:
            kind = "text"
        elif fmt_id in DATE_FMT_IDS or any(h in low for h in DATE_FMT_HINTS):
            kind = "date"
        elif fmt_id in PERCENT_FMT_IDS or "%" in low:
            kind = "percent"
        elif any(h in low for h in CURRENCY_FMT_HINTS):
            kind = "currency"
        elif fmt_id == 0 and low in ("", "general"):
            kind = "general"
        else:
            kind = "number"
        cache[style_index] = kind
        return kind

    # -- sheet reading ------------------------------------------------------
    def shared_formula_master(self, part_name):
        """Return {si: (master_ref, formula)} for the shared formulas on a sheet.

        A dependent cell stores only `<f t="shared" si="N"/>` with no text; Excel
        means "the master formula shifted by the row/column delta". Without the
        master, every filled-down formula reads as having no formula at all.
        """
        raw = self.parts.get(part_name)
        if raw is None:
            return {}
        masters = {}
        for event, elem in ET.iterparse(_bytes_reader(raw), events=("start", "end")):
            if elem.tag != M + "c" or event != "end":
                continue
            ref = elem.get("r") or ""
            for child in elem:
                if child.tag != M + "f":
                    continue
                if child.get("t") == "shared" and child.get("si") is not None and child.get("ref"):
                    si = child.get("si")
                    if si in masters:
                        # Two masters claim one si. A dependent cell can only match one
                        # of them, so keeping the first and recording the clash beats
                        # silently letting the later cell win.
                        self.shared_si_conflicts.append(
                            {"part": part_name, "si": si, "kept": masters[si][0], "ignored": ref})
                        continue
                    masters[si] = (ref, child.text or "")
            elem.clear()
        return masters

    def iter_rows(self, part_name):
        """Yield (row_number, [cell dicts]) streaming the sheet XML.

        A cell dict holds: ref, col, row, type, value (cached), formula, style,
        and numfmt kind. Only what the file stores is reported.
        """
        raw = self.parts.get(part_name)
        if raw is None:
            return
        shared = self.shared_strings
        masters = self.shared_formula_master(part_name)
        for event, elem in ET.iterparse(_bytes_reader(raw), events=("end",)):
            if elem.tag != M + "row":
                continue
            row_no = int(elem.get("r") or 0)
            cells = [self._cell(c, row_no, shared, masters, part_name) for c in elem if c.tag == M + "c"]
            yield (row_no, cells)
            elem.clear()

    def _cell(self, c, row_no, shared, masters=None, part_name=None):
        ref = c.get("r") or ""
        col, row = parse_ref(ref)
        if not col:
            col, row = col_index(ref), row_no
        ctype = c.get("t") or "n"
        style = int(c.get("s") or 0)
        # Direct child scan beats c.find() with a namespace map: this runs once per
        # cell, and ElementPath resolution dominated a 100k-row read.
        f = v = is_elem = None
        for child in c:
            tag = child.tag
            if tag == M + "f":
                f = child
            elif tag == M + "v":
                v = child
            elif tag == M + "is":
                is_elem = child
        value = None
        if ctype == "s" and v is not None and v.text is not None:
            try:
                value = shared[int(v.text)]
            except (ValueError, IndexError):
                value = None
                self.broken_string_refs.append({"part": part_name, "ref": ref,
                                                "index": v.text})
        elif ctype == "inlineStr" and is_elem is not None:
            value = rich_text(is_elem)
        elif ctype == "b" and v is not None:
            value = (v.text == "1")
        elif v is not None:
            text = v.text
            if text is None:
                value = None
            elif ctype in ("str", "e"):
                value = text
            else:
                try:
                    value = float(text)
                    if value == int(value) and abs(value) < 1e16:
                        value = int(value)
                except ValueError:
                    value = text
        formula = None
        if f is not None:
            text = f.text or ""
            if f.get("t") == "shared" and f.get("si") is not None:
                si = f.get("si")
                if f.get("ref") or not masters:
                    # Master cell, or the master is missing from this sheet: keep the
                    # text as stored and mark it so a reader can tell it is shared.
                    formula = "=" + text
                    formula += " [shared si=%s%s]" % (si, " master" if f.get("ref") else "")
                else:
                    # Dependent cell: expand the master, shifted by this cell's offset.
                    master = masters.get(si)
                    if master:
                        m_col, m_row = parse_ref(master[0])
                        formula = "=" + shift_formula(master[1], row - m_row, col - m_col)
                    else:
                        formula = "=" + text
            else:
                formula = "=" + text
        return {
            "ref": ref,
            "col": col,
            "row": row,
            "type": ctype,
            "value": value,
            "formula": formula,
            "style": style,
            "kind": self.format_kind(style),
        }

    def sheet_features(self, part_name):
        """Structural facts the inspection report and the validator both need."""
        raw = self.parts.get(part_name)
        out = {"merged": [], "conditional": [], "validations": [], "tables": [],
               "protection": None, "freeze": None, "auto_filter": None, "cols": [],
               "charts": [], "images": 0, "hyperlinks": 0, "dimension": None}
        if raw is None:
            return out
        root = ET.fromstring(raw)
        dim = root.find("m:dimension", NS)
        out["dimension"] = None if dim is None else dim.get("ref")
        for mc in root.findall("m:mergeCells/m:mergeCell", NS):
            out["merged"].append(mc.get("ref"))
        for cf in root.findall("m:conditionalFormatting", NS):
            rules = []
            for rule in cf.findall("m:cfRule", NS):
                rules.append({"type": rule.get("type"), "priority": rule.get("priority"),
                              "operator": rule.get("operator"), "formula": [x.text for x in rule.findall("m:formula", NS)]})
            out["conditional"].append({"sqref": cf.get("sqref"), "rules": rules})
        for dv in root.findall("m:dataValidations/m:dataValidation", NS):
            out["validations"].append({
                "sqref": dv.get("sqref"), "type": dv.get("type"), "operator": dv.get("operator"),
                "formula1": _text(dv.find("m:formula1", NS)), "formula2": _text(dv.find("m:formula2", NS)),
                "allowBlank": dv.get("allowBlank"), "showError": dv.get("showErrorMessage"),
                "prompt": dv.get("prompt"),
            })
        prot = root.find("m:sheetProtection", NS)
        if prot is not None:
            out["protection"] = dict(prot.attrib)
        pane = root.find("m:sheetViews/m:sheetView/m:pane", NS)
        if pane is not None:
            out["freeze"] = {"xSplit": pane.get("xSplit"), "ySplit": pane.get("ySplit"),
                             "topLeftCell": pane.get("topLeftCell"), "state": pane.get("state")}
        af = root.find("m:autoFilter", NS)
        if af is not None:
            out["auto_filter"] = af.get("ref")
        for col in root.findall("m:cols/m:col", NS):
            out["cols"].append({"min": col.get("min"), "max": col.get("max"),
                                "width": col.get("width"), "style": col.get("style"), "hidden": col.get("hidden")})
        out["hyperlinks"] = len(root.findall("m:hyperlinks/m:hyperlink", NS))
        for rel_id, (rtype, target) in self.rels(part_name).items():
            if rtype.endswith("/chart"):
                out["charts"].append(target)
            elif rtype.endswith("/drawing"):
                draw_rels = self.rels(target)
                out["images"] += sum(1 for _, (t2, _) in draw_rels.items() if t2.endswith("/image"))
                for _, (t2, tgt2) in draw_rels.items():
                    if t2.endswith("/chart"):
                        out["charts"].append(tgt2)
        for table in root.findall("m:tableParts/m:tablePart", NS):
            rid = table.get(R + "id")
            _, target = self.rels(part_name).get(rid, ("", ""))
            info = {"part": target}
            traw = self.parts.get(target)
            if traw:
                troot = ET.fromstring(traw)
                info.update({
                    "name": troot.get("name"), "ref": troot.get("ref"),
                    "totalsRow": troot.get("totalsRowCount"),
                    "columns": [c.get("name") for c in troot.findall("m:tableColumns/m:tableColumn", NS)],
                })
            out["tables"].append(info)
        return out

    def chart_types(self, part_name):
        """Chart kinds bound to a worksheet, read from the chart part itself."""
        out = []
        for chart_part in self.sheet_features(part_name)["charts"]:
            raw = self.parts.get(chart_part)
            if not raw:
                continue
            try:
                root = ET.fromstring(raw)
            except ET.ParseError:
                out.append({"part": chart_part, "type": "unparsed"})
                continue
            kinds = []
            bar_dir = None
            for el in root.iter():
                tag = el.tag.split("}")[-1]
                if tag.endswith("Chart") and tag not in ("chart", "Chart"):
                    kinds.append(tag[:-len("Chart")].lower())
                elif tag == "barDir":
                    bar_dir = el.get("val")
            label = ",".join(sorted(set(kinds))) or "unknown"
            # A column chart is stored as barChart with barDir="col"; report the
            # orientation a reader sees, not the element name.
            if label == "bar" and bar_dir == "col":
                label = "col"
            out.append({"part": chart_part, "type": label, "barDir": bar_dir,
                        "title": _chart_title(root)})
        return out

    def pivot_parts(self):
        return sorted(n for n in self.parts if re.match(r"^xl/pivotTables/.*\.xml$", n))

    def part_digests(self):
        return {name: digest(data) for name, data in sorted(self.parts.items())}


def _bytes_reader(raw):
    import io
    return io.BytesIO(raw)


def _chart_title(root):
    title = root.find("m:chart/m:title", {"m": "http://schemas.openxmlformats.org/drawingml/2006/chart"})
    if title is None:
        return None
    return "".join(t.text or "" for t in title.iter() if t.tag.endswith("}t")) or None


def _text(elem):
    return None if elem is None else (elem.text or "")


def rich_text(node):
    """Concatenate every <t> under a shared or inline string, ignoring run formatting."""
    return "".join(t.text or "" for t in node.iter(M + "t"))


BUILTIN_FORMATS = {
    0: "General", 1: "0", 2: "0.00", 3: "#,##0", 4: "#,##0.00", 9: "0%", 10: "0.00%",
    11: "0.00E+00", 12: "# ?/?", 13: "# ??/??", 14: "mm-dd-yy", 15: "d-mmm-yy",
    16: "d-mmm", 17: "mmm-yy", 18: "h:mm AM/PM", 19: "h:mm:ss AM/PM", 20: "h:mm",
    21: "h:mm:ss", 22: "m/d/yy h:mm", 37: "#,##0 ;(#,##0)", 38: "#,##0 ;[Red](#,##0)",
    39: "#,##0.00;(#,##0.00)", 40: "#,##0.00;[Red](#,##0.00)", 45: "mm:ss",
    46: "[h]:mm:ss", 47: "mmss.0", 48: "##0.0E+0", 49: "@",
}


def builtin_format(fmt_id):
    return BUILTIN_FORMATS.get(fmt_id, "General")


FUNC_RE = re.compile(r"(?<![A-Z0-9_.])([A-Z][A-Z0-9_.]{1,40})\s*\(")
# Excel stores functions newer than the file format under a compatibility prefix:
# `_xlfn.XLOOKUP(`, `_xlws.FILTER(`, `_xludf.` for user functions. The prefix is
# part of the stored formula, not of the function name, so it is stripped before
# the name is compared against the known-function lists.
XLL_PREFIX_RE = re.compile(r"(?<![A-Z0-9_.])(?:_XL(?:FN|WS|UDF)\.)+", re.I)


def formula_functions(formula):
    """Uppercase function names referenced by a formula string."""
    if not formula:
        return []
    body = formula[1:] if formula.startswith("=") else formula
    body = re.sub(r'"[^"]*"', '""', body)
    body = XLL_PREFIX_RE.sub("", body)
    return sorted({m.group(1).upper() for m in FUNC_RE.finditer(body)})

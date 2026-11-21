#!/usr/bin/env python3
"""Compute formula results and store them as cached values.

Usage:
    python3 recalc_cached.py <workbook> --out <out.xlsx> [--json]
    python3 recalc_cached.py <workbook> --in-place [--backup]
    python3 recalc_cached.py --self-test

Why this exists: a formula cell written by a tool holds no `<v>`, so every reader
that does not calculate (pandas, openpyxl with data_only=True, a CSV exporter, a
preview pane) sees an empty cell. Excel and LibreOffice recalculate on open; a
programmatic reader does not. This tool evaluates the workbook's formulas with the
same engine the verifier uses and stores the result, so both kinds of reader agree.

It also sets `fullCalcOnLoad="1"`, so Excel still recalculates from source on open:
stored values are a cache, never the authority. Functions outside the engine's set
are left without a cache and reported, never guessed.

Output: JSON with counts and the list of cells left without a cache.
Exit codes: 0 written, 1 verification failed, 2 usage or unreadable input.
"""

import argparse
import json
import os
import re
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlib  # noqa: E402
import verify_formulas  # noqa: E402
from patch_workbook import CELL_ATTRS  # noqa: E402


def fmt_cached(value):
    """Render one evaluated value as (text, cell type) for the cached `<v>`.

    `None` means the evaluator did not produce a value (an empty result or a
    dependent shared-formula cell); writing it would put the literal string
    "None" into the file, so the caller must skip instead.
    """
    if value is None:
        raise ValueError("no value to cache")
    if isinstance(value, bool):
        return ("1" if value else "0", "b")
    if isinstance(value, str):
        if value in xlsxlib.ERROR_LITERALS:
            return (value, "e")
        return (value, "str")
    if isinstance(value, float) and value == int(value) and abs(value) < 1e16:
        return (str(int(value)), None)
    return (repr(value) if isinstance(value, float) else str(value), None)


def cell_body_with_cache(cell_xml, cached, ctype):
    """Replace or insert <v> inside one <c> element, preserving <f> and attributes."""
    open_end = cell_xml.find(">")
    head = cell_xml[:open_end + 1]
    if head.endswith("/>"):
        head = head[:-2] + ">"
        body = ""
        tail = "</c>"
    else:
        body = cell_xml[open_end + 1:cell_xml.rfind("</c>")]
        tail = "</c>"
    # openpyxl and some writers emit a self-closing <v/>, so both shapes must go.
    body = re.sub(r"<v\s*/>|<v>.*?</v>", "", body, flags=re.DOTALL)
    if ctype:
        if re.search(r'\st="[^"]*"', head):
            head = re.sub(r'\st="[^"]*"', ' t="%s"' % ctype, head)
        else:
            head = head[:-1] + ' t="%s">' % ctype
    elif re.search(r'\st="[^"]*"', head):
        head = re.sub(r'\st="[^"]*"', "", head)
    return head + body + "<v>%s</v>" % _escape_value(cached) + tail


def _escape_value(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def recalc(path, out_path):
    wb = xlsxlib.Workbook(path)
    evaluator = verify_formulas.Evaluator(wb)
    parts = dict(wb.parts)
    written, skipped = 0, []
    touched = set()
    for sheet_name, part, state in wb.sheets:
        if state == "chartsheet" or not part:
            continue
        xml = parts[part].decode("utf-8")
        changed = False
        for row_no, cells in wb.iter_rows(part):
            for cell in cells:
                if not cell["formula"]:
                    continue
                try:
                    value = evaluator.cell_value(sheet_name, cell["col"], cell["row"])
                except Exception as exc:  # cycle, unsupported function, or a formula error
                    reason = str(exc) or exc.__class__.__name__
                    if isinstance(exc, verify_formulas.FormulaError):
                        value = exc.code
                    else:
                        skipped.append({"sheet": sheet_name, "ref": cell["ref"],
                                        "formula": cell["formula"], "reason": reason})
                        continue
                try:
                    cached, ctype = fmt_cached(value)
                except ValueError:
                    skipped.append({"sheet": sheet_name, "ref": cell["ref"],
                                    "formula": cell["formula"], "reason": "evaluated to no value"})
                    continue
                span = _find_cell(xml, cell["ref"])
                if not span:
                    skipped.append({"sheet": sheet_name, "ref": cell["ref"],
                                    "formula": cell["formula"], "reason": "cell element not located"})
                    continue
                original = xml[span[0]:span[1]]
                xml = xml[:span[0]] + cell_body_with_cache(original, cached, ctype) + xml[span[1]:]
                written += 1
                changed = True
        if changed:
            parts[part] = xml.encode("utf-8")
            touched.add(part)
    # Ask for a full recalculation on open so the cache never overrides source.
    wb_part = wb.workbook[0]
    wb_xml = parts[wb_part].decode("utf-8")
    if "<calcPr" in wb_xml:
        if 'fullCalcOnLoad="1"' not in wb_xml:
            wb_xml = re.sub(r"<calcPr\b([^>]*?)/>",
                            lambda m: '<calcPr%s fullCalcOnLoad="1"/>' % re.sub(r'\s*fullCalcOnLoad="[^"]*"', "", m.group(1)),
                            wb_xml, count=1)
    else:
        wb_xml = wb_xml.replace("</workbook>", '<calcPr fullCalcOnLoad="1"/></workbook>', 1)
    if wb_xml != parts[wb_part].decode("utf-8"):
        parts[wb_part] = wb_xml.encode("utf-8")
        touched.add(wb_part)

    target = out_path if out_path != path else path + ".recalc"
    tmp = target + ".tmp"
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            dst.writestr(info, parts.get(info.filename, src.read(info.filename)))
        for name, data in parts.items():
            if name not in {i.filename for i in src.infolist()}:
                dst.writestr(name, data)
    os.replace(tmp, target)
    # Read the result back: every part we did not touch must be byte-identical.
    problems = []
    after = xlsxlib.Workbook(target)
    before_digests = wb.part_digests()
    after_digests = after.part_digests()
    for name, digest_value in before_digests.items():
        if name in touched:
            continue
        if after_digests.get(name) != digest_value:
            problems.append({"code": "UNTOUCHED_PART_CHANGED", "detail": name})
    for sheet_name, part, state in after.sheets:
        if state == "chartsheet" or not part:
            continue
        try:
            list(after.iter_rows(part))
        except Exception as exc:
            problems.append({"code": "SHEET_UNREADABLE", "detail": "%s: %s" % (sheet_name, exc)})
    if problems:
        os.unlink(target)
        raise RuntimeError(json.dumps(problems, ensure_ascii=False))
    if target != out_path:
        shutil.move(target, out_path)
    return {"schemaVersion": 1, "path": out_path, "cached": written,
            "skipped": skipped, "touchedParts": sorted(touched)}


def _find_cell(xml, ref):
    m = re.search(r'<c\b%s\br="%s"%s(?:/>|>.*?</c>)' % (CELL_ATTRS, re.escape(ref), CELL_ATTRS), xml, re.DOTALL)
    return (m.start(), m.end()) if m else None


def self_test():
    import tempfile
    import zipfile as zf_mod
    from xml.sax.saxutils import escape as esc

    checks = []

    def build(dirpath):
        target = os.path.join(dirpath, "calc.xlsx")
        sheet = (
            '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="%s"><sheetData>'
            '<row r="1"><c r="A1" t="inlineStr"><is><t>값</t></is></c></row>'
            '<row r="2"><c r="A2"><v>10</v></c></row>'
            '<row r="3"><c r="A3"><v>20</v></c></row>'
            '<row r="4"><c r="A4"><f>SUM(A2:A3)</f></c></row>'
            '<row r="5"><c r="A5"><f>A4/0</f></c></row>'
            '<row r="6"><c r="A6"><f>XLOOKUP(1,A2:A3,A2:A3)</f></c></row>'
            '<row r="7"><c r="A7"><f>IF(A4&gt;0,"양수","음수")</f></c></row>'
            '</sheetData></worksheet>' % xlsxlib.NS["m"])
        wbxml = ('<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="%s" xmlns:r="%s">'
                 '<sheets><sheet name="계산" sheetId="1" r:id="rId1"/></sheets></workbook>'
                 % (xlsxlib.NS["m"], xlsxlib.NS["r"]))
        rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="%s">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
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
        return target

    with tempfile.TemporaryDirectory() as tmp:
        src = build(tmp)
        out = os.path.join(tmp, "out.xlsx")
        result = recalc(src, out)
        checks.append(("wrote", os.path.isfile(out)))
        checks.append(("cached count", result["cached"] == 3))
        checks.append(("unsupported skipped", any(s["ref"] == "A6" for s in result["skipped"])))
        wb = xlsxlib.Workbook(out)
        cells = {}
        for _, row in wb.iter_rows("xl/worksheets/sheet1.xml"):
            for cell in row:
                cells[cell["ref"]] = cell
        checks.append(("sum cached", cells["A4"]["value"] == 30))
        checks.append(("error cached", cells["A5"]["value"] == "#DIV/0!"))
        checks.append(("text cached", cells["A7"]["value"] == "양수"))
        checks.append(("formula kept", cells["A4"]["formula"] == "=SUM(A2:A3)"))
        checks.append(("recalc on load", wb.calc_properties.get("fullCalcOnLoad") == "1"))
        # The verifier must now agree with the cache it just read.
        report = verify_formulas.verify(out)
        checks.append(("verify agrees", report["totals"]["mismatched"] == 0))
        checks.append(("verify clean of cache loss", report["totals"]["evaluated"] == 2))
    failed = [name for name, ok in checks if not ok]
    print(json.dumps({"ok": not failed, "checks": len(checks), "failed": failed}, ensure_ascii=False))
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("workbook", nargs="?")
    parser.add_argument("--out")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.workbook or not os.path.isfile(args.workbook):
        parser.print_usage(sys.stderr)
        return 2
    out = args.workbook if args.in_place else args.out
    if not out:
        print(json.dumps({"ok": False, "error": "E_USAGE", "detail": "give --out or --in-place"}, ensure_ascii=False))
        return 2
    if args.in_place and args.backup:
        shutil.copy2(args.workbook, args.workbook + ".bak")
    try:
        result = recalc(args.workbook, out)
    except zipfile.BadZipFile:
        print(json.dumps({"ok": False, "error": "E_NOT_ZIP", "detail": "not an OOXML package"}, ensure_ascii=False))
        return 2
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": "E_VERIFY", "detail": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

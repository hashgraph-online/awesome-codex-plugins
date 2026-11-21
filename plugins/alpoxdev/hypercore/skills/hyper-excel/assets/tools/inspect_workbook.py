#!/usr/bin/env python3
"""Read one .xlsx/.xlsm/.xltx and report what the file actually stores.

Usage:
    python3 inspect_workbook.py <workbook> [--json] [--rows N] [--sheet NAME]
                                [--max-cells N] [--self-test]

Output (stdout): one JSON object.
    {"schemaVersion": 1, "path", "size", "sha256", "package": {...},
     "workbook": {date1904, calcProps, definedNames, sheets: [...]},
     "sheets": [ {name, part, state, dimension, rows, cells, formulas,
                  errorCells, merged, tables, charts, chartsheets,
                  conditionalFormats, dataValidations, protection, freeze,
                  autoFilter, hyperlinks, images, colWidths, formatKinds} ],
     "pivotTables": [...], "warnings": [...]}

Exit codes: 0 reported, 2 usage or unreadable input, 3 a part failed to parse.
Nothing is written; the workbook is opened read-only.
"""

import argparse
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlib  # noqa: E402

MACRO_MARKERS = ("xl/vbaProject.bin",)


def summarize_sheet(wb, name, part, state, max_cells):
    info = {
        "name": name, "part": part, "state": state, "dimension": None,
        "rows": 0, "cells": 0, "formulas": 0, "textCells": 0, "errorCells": [],
        "merged": [], "tables": [], "charts": [], "chartsheets": [],
        "conditionalFormats": [], "dataValidations": [], "protection": None,
        "freeze": None, "autoFilter": None, "hyperlinks": 0, "images": 0,
        "colWidths": [], "formatKinds": {}, "sharedFormulas": 0,
        "formulaWithoutCache": 0, "maxRow": 0, "maxCol": 0,
    }
    if state == "chartsheet" or not part:
        return info
    features = wb.sheet_features(part)
    info.update({
        "dimension": features["dimension"], "merged": features["merged"],
        "tables": features["tables"], "charts": wb.chart_types(part),
        "conditionalFormats": features["conditional"],
        "dataValidations": features["validations"], "protection": features["protection"],
        "freeze": features["freeze"], "autoFilter": features["auto_filter"],
        "hyperlinks": features["hyperlinks"], "images": features["images"],
        "colWidths": features["cols"],
    })
    kinds = {}
    for row_no, cells in wb.iter_rows(part):
        info["rows"] += 1
        info["maxRow"] = max(info["maxRow"], row_no)
        for cell in cells:
            info["cells"] += 1
            info["maxCol"] = max(info["maxCol"], cell["col"])
            kinds[cell["kind"]] = kinds.get(cell["kind"], 0) + 1
            if cell["formula"]:
                info["formulas"] += 1
                if "[shared" in cell["formula"]:
                    info["sharedFormulas"] += 1
                if cell["value"] is None:
                    info["formulaWithoutCache"] += 1
            if cell["type"] == "s" or cell["type"] == "inlineStr":
                info["textCells"] += 1
            value = cell["value"]
            if isinstance(value, str) and value in xlsxlib.ERROR_LITERALS:
                info["errorCells"].append({"ref": cell["ref"], "error": value,
                                           "formula": cell["formula"]})
            if info["cells"] >= max_cells:
                info["truncated"] = True
                break
        if info.get("truncated"):
            break
    info["formatKinds"] = kinds
    return info


def inspect(path, max_cells=2_000_000):
    with open(path, "rb") as fh:
        raw = fh.read()
    wb = xlsxlib.Workbook(path)
    warnings = []
    package = {
        "parts": len(wb.parts),
        "hasMacros": any(marker in wb.parts for marker in MACRO_MARKERS),
        "hasSharedStrings": any(p.endswith("sharedStrings.xml") for p in wb.parts),
        "hasPivotCache": any("/pivotCache/" in p for p in wb.parts),
        "hasExternalLinks": sorted(p for p in wb.parts if "/externalLinks/" in p),
        "hasCalcChain": any(p.endswith("calcChain.xml") for p in wb.parts),
        "zipComment": "",
    }
    with zipfile.ZipFile(path) as zf:
        package["zipComment"] = zf.comment.decode("utf-8", "replace")
        if zf.testzip() is not None:
            warnings.append({"code": "E_ZIP_CRC", "detail": "a member failed its CRC check"})
    sheets = []
    for name, part, state in wb.sheets:
        sheets.append(summarize_sheet(wb, name, part, state, max_cells))
    if wb.shared_si_conflicts:
        warnings.append({
            "code": "E_SHARED_FORMULA_SI",
            "detail": "%d shared formula(s) reuse an si already claimed by another cell (%s)"
                      % (len(wb.shared_si_conflicts),
                         ", ".join("%s: si=%s kept %s" % (i["part"], i["si"], i["kept"])
                                   for i in wb.shared_si_conflicts[:10])),
        })
    if wb.broken_string_refs:
        # A shared-string index past the table means the text is gone; reporting it
        # with the part and cell is the only way to find which values to recover.
        seen = {}
        for item in wb.broken_string_refs:
            seen.setdefault(item["part"], []).append(item)
        for part, items in sorted(seen.items()):
            warnings.append({
                "code": "E_SHARED_STRINGS_INDEX",
                "detail": "%s: %d cell(s) point past the shared-string table (%s)"
                          % (part, len(items), ", ".join(i["ref"] for i in items[:10])),
            })
    if package["hasExternalLinks"]:
        warnings.append({"code": "W_EXTERNAL_LINKS", "detail": "workbook links another file; those cached values are not recomputable here"})
    if any(s["formulaWithoutCache"] for s in sheets):
        warnings.append({"code": "W_FORMULA_NO_CACHE",
                         "detail": "formula cells hold no cached value, so cached-value readers see None until a real recalc runs"})
    if package["hasMacros"]:
        warnings.append({"code": "W_MACROS", "detail": "VBA project present; it is never executed and must survive a rewrite"})
    dup = [n for n in {s["name"] for s in sheets} if [x["name"] for x in sheets].count(n) > 1]
    if dup:
        warnings.append({"code": "E_SHEET_NAME_DUP", "detail": ",".join(sorted(dup))})
    return {
        "schemaVersion": 1,
        "path": path,
        "size": len(raw),
        "sha256": xlsxlib.digest(raw),
        "package": package,
        "workbook": {
            "date1904": wb.date1904,
            "calcProperties": wb.calc_properties,
            "definedNames": wb.defined_names,
            "sheetCount": len(sheets),
        },
        "sheets": sheets,
        "pivotTables": wb.pivot_parts(),
        "warnings": warnings,
    }


def preview(path, sheet_name=None, rows=12):
    wb = xlsxlib.Workbook(path)
    targets = [(n, p, s) for n, p, s in wb.sheets if sheet_name in (None, n)]
    out = []
    for name, part, state in targets:
        shown = []
        for row_no, cells in wb.iter_rows(part):
            shown.append({"row": row_no, "cells": [
                {"ref": c["ref"], "value": c["value"], "formula": c["formula"], "kind": c["kind"]}
                for c in cells]})
            if len(shown) >= rows:
                break
        out.append({"name": name, "rows": shown})
    return out


def self_test():
    import tempfile
    from xml.sax.saxutils import escape

    def build(dirpath):
        target = os.path.join(dirpath, "probe.xlsx")
        sheet = (
            '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="%s">'
            '<dimension ref="A1:C4"/>'
            '<sheetData>'
            '<row r="1"><c r="A1" t="inlineStr"><is><t>매출</t></is></c>'
            '<c r="B1" t="inlineStr"><is><t>금액</t></is></c></row>'
            '<row r="2"><c r="A2" t="inlineStr"><is><t>1월</t></is></c><c r="B2"><v>100</v></c></row>'
            '<row r="3"><c r="A3" t="inlineStr"><is><t>2월</t></is></c><c r="B3"><v>200</v></c></row>'
            '<row r="4"><c r="A4" t="inlineStr"><is><t>합계</t></is></c>'
            '<c r="B4"><f>SUM(B2:B3)</f><v>300</v></c>'
            '<c r="C4" t="e"><f>1/0</f><v>#DIV/0!</v></c></row>'
            '</sheetData></worksheet>' % xlsxlib.NS["m"]
        )
        wbxml = ('<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="%s" xmlns:r="%s">'
                 '<sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>'
                 % (xlsxlib.NS["m"], xlsxlib.NS["r"], escape("매출 요약")))
        rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="%s">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '</Relationships>' % xlsxlib.NS["pr"])
        root_rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="%s">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                     '</Relationships>' % xlsxlib.NS["pr"])
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
            zf.writestr("_rels/.rels", root_rels)
            zf.writestr("xl/workbook.xml", wbxml)
            zf.writestr("xl/_rels/workbook.xml.rels", rels)
            zf.writestr("xl/worksheets/sheet1.xml", sheet)
        return target

    import tempfile as tf
    with tf.TemporaryDirectory() as tmp:
        path = build(tmp)
        report = inspect(path)
        checks = []
        checks.append(("sheet name", report["sheets"][0]["name"] == "매출 요약"))
        checks.append(("rows", report["sheets"][0]["rows"] == 4))
        checks.append(("formulas", report["sheets"][0]["formulas"] == 2))
        checks.append(("error cell", report["sheets"][0]["errorCells"][0]["ref"] == "C4"))
        checks.append(("digest", len(report["sha256"]) == 64))
        bad = [name for name, ok in checks if not ok]
        if bad:
            print(json.dumps({"ok": False, "failed": bad}, ensure_ascii=False))
            return 1
    print(json.dumps({"ok": True, "checks": len(checks)}, ensure_ascii=False))
    return 0


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("workbook", nargs="?")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--rows", type=int, default=0)
    parser.add_argument("--sheet")
    parser.add_argument("--max-cells", type=int, default=2_000_000)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.workbook:
        parser.print_usage(sys.stderr)
        return 2
    if not os.path.isfile(args.workbook):
        print(json.dumps({"ok": False, "error": "E_NO_INPUT", "detail": args.workbook}, ensure_ascii=False))
        return 2
    try:
        report = inspect(args.workbook, args.max_cells)
    except zipfile.BadZipFile:
        print(json.dumps({"ok": False, "error": "E_NOT_ZIP",
                          "detail": "not an OOXML package (a .xls renamed to .xlsx needs a real conversion)"},
                         ensure_ascii=False))
        return 2
    except Exception as exc:  # a malformed part should be reported, not crash the run
        print(json.dumps({"ok": False, "error": "E_PARSE", "detail": str(exc)}, ensure_ascii=False))
        return 3
    if args.rows:
        report["preview"] = preview(args.workbook, args.sheet, args.rows)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

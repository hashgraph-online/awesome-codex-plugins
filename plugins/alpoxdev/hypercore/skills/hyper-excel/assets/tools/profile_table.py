#!/usr/bin/env python3
"""Profile a CSV or XLSX before you convert, format, or load it.

Usage:
    python3 profile_table.py <file.csv|file.xlsx> [--json] [--sheet NAME]
                             [--rows N] [--limit BYTES] [--encoding auto]
                             [--delimiter ,] [--date-columns a,b] [--self-test]

Reports per column: inferred type, nulls, distinct count, min/max/mean/sum for
numbers, min/max for dates, the longest value, and the Korean-specific problems
that break a spreadsheet import:

    * a numeric column holding thousands separators, currency signs, or a
      trailing 원/₩ that Excel will store as text
    * percentages written as "15%" instead of 0.15
    * dates that only look like dates (2026. 1. 31., 26-01-31, 1/31/26) — Excel's
      Korean locale parses these differently from its US locale
    * a leading zero lost to a numeric column (010-1234-5678 products codes)
    * a BOM, or cp949 bytes read as UTF-8, which mangle Hangul

Output (stdout): one JSON object with `rows`, `columns`, `issues`, and `advice`.
Exit codes: 0 profiled, 2 unreadable input.
"""

import argparse
import csv
import io
import json
import math
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlib  # noqa: E402

CURRENCY_RE = re.compile(r"^\s*[-+]?[₩$€£¥]?\s*[-+]?[\d,]+(\.\d+)?\s*(원|KRW|USD|krw|usd)?\s*$")
PERCENT_RE = re.compile(r"^\s*[-+]?[\d,]+(\.\d+)?\s*%\s*$")
NUMERIC_RE = re.compile(r"^\s*[-+]?\d+(\.\d+)?([eE][-+]?\d+)?\s*$")
KOREAN_DATE_PATTERNS = [
    (re.compile(r"^(\d{4})\s*[.년\-/]\s*(\d{1,2})\s*[.월\-/]\s*(\d{1,2})\s*일?\.?$"), "ymd"),
    (re.compile(r"^(\d{2})\s*[.\-/]\s*(\d{1,2})\s*[.\-/]\s*(\d{1,2})$"), "short"),
    (re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$"), "mdy_or_dmy"),
]
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?$")
PHONE_RE = re.compile(r"^0\d{1,2}-?\d{3,4}-?\d{4}$")
ZIP_RE = re.compile(r"^\d{5}$")


def sniff_kind(value):
    text = str(value).strip()
    if text == "":
        return "blank"
    if NUMERIC_RE.match(text):
        return "number"
    if CURRENCY_RE.match(text) and any(ch in text for ch in ",₩$€£¥원"):
        return "currency_text"
    if PERCENT_RE.match(text):
        return "percent_text"
    if ISO_DATE.match(text):
        return "iso_date"
    for pattern, label in KOREAN_DATE_PATTERNS:
        if pattern.match(text):
            return "date_" + label
    if PHONE_RE.match(text):
        return "phone_text"
    if ZIP_RE.match(text):
        return "zip_text"
    return "text"


def read_rows(path, sheet=None, encoding="auto", delimiter=None):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm", ".xltx"):
        wb = xlsxlib.Workbook(path)
        target = None
        for name, part, state in wb.sheets:
            if state == "chartsheet" or not part:
                continue
            if sheet is None or name == sheet:
                target = (name, part)
                break
        if target is None:
            raise ValueError("no sheet named %r (have: %s)" % (sheet, ", ".join(n for n, _, _ in wb.sheets)))
        rows = []
        for row_no, cells in wb.iter_rows(target[1]):
            width = max([c["col"] for c in cells] or [0])
            row = [None] * width
            for cell in cells:
                row[cell["col"] - 1] = cell["value"]
            rows.append(row)
        return {"rows": rows, "source": "xlsx", "sheet": target[0], "encoding": None, "delimiter": None}
    encodings = ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1") if encoding in (None, "", "auto") else (encoding,)
    raw, used, bom = None, None, False
    for candidate in encodings:
        try:
            with open(path, "rb") as fh:
                head = fh.read(4)
            with open(path, "r", encoding=candidate, newline="") as fh:
                raw = fh.read()
            used = candidate
            bom = head.startswith(b"\xef\xbb\xbf")
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        raise ValueError("could not decode %s with %s" % (path, ", ".join(encodings)))
    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(raw[:65536], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    try:
        rows = [row for row in csv.reader(io.StringIO(raw), delimiter=delimiter)]
    except csv.Error as exc:
        raise ValueError("%s is not readable as %s-delimited CSV: %s" % (path, delimiter, exc))
    return {"rows": rows, "source": "csv", "encoding": used, "delimiter": delimiter, "bom": bom}


def profile_rows(rows, sample_limit=None):
    # A blank file parses to one or more zero-width records; treating those as a
    # header would report a table with rows but no columns.
    rows = [r for r in rows if r]
    if not rows:
        return {"header": [], "columns": [], "rows": 0, "issues": [], "advice": []}
    header = [str(h).strip() or "컬럼%d" % (i + 1) for i, h in enumerate(rows[0])]
    body = rows[1:]
    if sample_limit:
        body = body[:sample_limit]
    width = max([len(header)] + [len(r) for r in body] or [len(header)])
    while len(header) < width:
        header.append("컬럼%d" % (len(header) + 1))
    columns = []
    issues = []
    for index in range(width):
        values = [row[index] if index < len(row) else None for row in body]
        non_blank = [v for v in values if v is not None and str(v).strip() != ""]
        kinds = {}
        for value in non_blank:
            kind = sniff_kind(value)
            kinds[kind] = kinds.get(kind, 0) + 1
        dominant = max(kinds, key=kinds.get) if kinds else "blank"
        numbers, dates = [], []
        for value in non_blank:
            text = str(value).strip()
            cleaned = text.replace(",", "").replace("원", "").replace("₩", "").replace("%", "").strip()
            try:
                numbers.append(float(cleaned))
            except ValueError:
                pass
        for value in non_blank:
            text = str(value).strip()
            for pattern, label in KOREAN_DATE_PATTERNS:
                m = pattern.match(text)
                if m:
                    parts = [int(p) for p in m.groups()]
                    if label == "ymd":
                        try:
                            dates.append(date(parts[0], parts[1], parts[2]))
                        except ValueError:
                            pass
                    elif label == "short":
                        try:
                            dates.append(date(2000 + parts[0], parts[1], parts[2]))
                        except ValueError:
                            pass
                    break
            if ISO_DATE.match(text):
                try:
                    dates.append(datetime.fromisoformat(text.replace(".", "-")).date())
                except ValueError:
                    pass
        column = {
            "name": header[index],
            "kind": dominant,
            "kindCounts": kinds,
            "nonBlank": len(non_blank),
            "blank": len(values) - len(non_blank),
            "distinct": len({str(v).strip() for v in non_blank}),
            "longest": max([len(str(v)) for v in non_blank] or [0]),
            "sample": [str(v) for v in non_blank[:3]],
        }
        if numbers and dominant in ("number", "currency_text", "percent_text"):
            column["numeric"] = {
                "min": min(numbers), "max": max(numbers),
                "sum": round(math.fsum(numbers), 6),
                "mean": round(math.fsum(numbers) / len(numbers), 6),
                "currencyFormatted": kinds.get("currency_text", 0),
                "percentStrings": kinds.get("percent_text", 0),
            }
        if dates:
            column["dates"] = {"count": len(dates), "min": str(min(dates)), "max": str(max(dates))}
        # Only an all-digit token loses its zero to numeric coercion; `010-1234-5678` and `2026. 1. 31.`
        # never become numbers, so counting them here was a false positive.
        leading_zeros = [v for v in non_blank if re.fullmatch(r"0\d+", str(v).strip())]
        column["leadingZeros"] = len(leading_zeros)
        # A column of codes that only look numeric is a text column: reporting it as
        # a number invites the conversion that erases the leading zero.
        if leading_zeros and column["kind"] == "number":
            column["kind"] = "text"
        columns.append(column)

        name = header[index]
        if kinds.get("currency_text"):
            issues.append({
                "code": "CURRENCY_AS_TEXT", "column": name, "severity": "high",
                "count": kinds["currency_text"],
                "detail": "'1,200원', '₩1,200' 같은 값 %d개는 숫자가 아니라 텍스트로 저장된다" % kinds["currency_text"],
                "fix": '통화 기호와 쉼표를 지우고 숫자로 변환한 뒤 셀 서식 "#,##0원"을 적용한다',
            })
        if kinds.get("percent_text"):
            issues.append({
                "code": "PERCENT_AS_TEXT", "column": name, "severity": "high",
                "count": kinds["percent_text"],
                "detail": "15%% 문자열 %d개는 15가 아니라 0.15로 저장해야 계산이 맞는다" % kinds["percent_text"],
                "fix": "100으로 나눠 저장하고 서식 '0.0%'를 적용한다",
            })
        date_kinds = {k: v for k, v in kinds.items() if k.startswith("date_")}
        iso_count = kinds.get("iso_date", 0)
        if date_kinds or iso_count:
            # Year-first patterns (`2026-01-31`, `2026. 1. 31.`) read the same in every locale; only the
            # day/month-first pattern can flip. Treating ISO as ambiguity was a false positive.
            patterns = sorted(date_kinds) + (["iso_date"] if iso_count else [])
            ambiguous = date_kinds.get("date_mdy_or_dmy", 0) > 0
            count = sum(date_kinds.values()) + iso_count
            detail = "%s 형식 날짜 문자열 %d개" % (", ".join(patterns), count)
            detail += (" — 일/월 순서가 로캘에 따라 뒤집힌다" if ambiguous
                       else " — 연-월-일 순서라 로캘에 흔들리지 않지만 텍스트로 저장되어 있다")
            issues.append({
                "code": "AMBIGUOUS_DATE" if ambiguous else "LOCALE_DATE_TEXT",
                "column": name, "severity": "high" if ambiguous else "medium",
                "count": count,
                "detail": detail,
                "fix": "YYYY-MM-DD로 정규화해 날짜 값으로 쓰고 서식 'yyyy-mm-dd'를 지정한다",
            })
        if column["leadingZeros"]:
            issues.append({
                "code": "LEADING_ZERO", "column": name, "severity": "medium",
                "count": column["leadingZeros"],
                "detail": "앞자리 0이 있는 값 %d개. 숫자로 변환하면 0이 사라진다" % column["leadingZeros"],
                "fix": "해당 열을 텍스트 서식 '@'으로 두고 값을 문자열로 쓴다",
            })
        # A column where text and numbers both appear is a real data defect: sorting
        # and totals silently skip half of it. The old test required a text majority
        # while also requiring a numeric majority, so it could never fire.
        numbers = kinds.get("number", 0)
        texts = kinds.get("text", 0)
        if numbers and texts and (numbers + texts) == len(non_blank):
            issues.append({
                "code": "MIXED_TYPES", "column": name, "severity": "medium",
                "count": numbers,
                "detail": "숫자 %d개와 텍스트 %d개가 한 열에 섞여 있다" % (numbers, texts),
                "fix": "열을 하나의 타입으로 정리한다. 섞인 열은 정렬과 합계가 틀린다",
            })
    advice = []
    for column in columns:
        if column["kind"] == "blank":
            advice.append({"column": column["name"], "note": "값이 없다. 빈 열을 만들었는지 확인한다"})
    return {"header": header, "columns": columns, "rows": len(body), "issues": issues, "advice": advice}


def self_test():
    import tempfile
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "messy.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            fh.write("품목,금액,비율,일자,코드\n")
            fh.write("사과,\"1,200원\",15%,2026. 1. 31.,00123\n")
            fh.write("배,\"2,300원\",7.5%,2026. 2. 28.,00456\n")
            fh.write("감,\"₩900\",3%,2026-03-31,00789\n")
            fh.write(",,,\n")
        result = read_rows(path)
        checks.append(("bom detected", result.get("bom") is True))
        checks.append(("utf-8-sig", result["encoding"] == "utf-8-sig"))
        prof = profile_rows(result["rows"])
        checks.append(("rows", prof["rows"] == 4))
        codes = {i["code"] for i in prof["issues"]}
        checks.append(("currency", "CURRENCY_AS_TEXT" in codes))
        checks.append(("percent", "PERCENT_AS_TEXT" in codes))
        checks.append(("date", "AMBIGUOUS_DATE" in codes or "LOCALE_DATE_TEXT" in codes))
        checks.append(("leading zero", "LEADING_ZERO" in codes))
        amount = [c for c in prof["columns"] if c["name"] == "금액"][0]
        checks.append(("amount sum", amount["numeric"]["sum"] == 4400))
        checks.append(("amount distinct", amount["distinct"] == 3))
        # A clean numeric CSV must produce no high-severity issues.
        clean = os.path.join(tmp, "clean.csv")
        with open(clean, "w", encoding="utf-8", newline="") as fh:
            fh.write("월,매출\n1월,1000\n2월,2000\n3월,3000\n")
        clean_prof = profile_rows(read_rows(clean)["rows"])
        checks.append(("clean no issues", not [i for i in clean_prof["issues"] if i["severity"] == "high"]))
        checks.append(("clean types", [c["kind"] for c in clean_prof["columns"]] == ["text", "number"]))
        # cp949 intake
        cp = os.path.join(tmp, "cp949.csv")
        with open(cp, "w", encoding="cp949", newline="") as fh:
            fh.write("품목,수량\n사과,10\n")
        checks.append(("cp949 read", read_rows(cp)["encoding"] in ("cp949", "euc-kr")))
        # Degenerate inputs must produce the documented shape, not a KeyError: an empty
        # file has no header row, so profile_rows returns before any column analysis.
        for name, body in (("empty.csv", b""), ("bomonly.csv", b"\xef\xbb\xbf"), ("blank.csv", b"\n\n")):
            degenerate = os.path.join(tmp, name)
            with open(degenerate, "wb") as fh:
                fh.write(body)
            shape = profile_rows(read_rows(degenerate)["rows"])
            checks.append((name + " shape", shape["rows"] == 0 and shape["issues"] == [] and shape["advice"] == []))
        # A NUL byte is not CSV; it has to arrive as E_READ, not as a csv.Error traceback.
        binary = os.path.join(tmp, "binary.csv")
        with open(binary, "wb") as fh:
            fh.write(b"\xff\xfe\x00\x01junk\n")
        try:
            read_rows(binary)
            checks.append(("binary csv rejected", False))
        except ValueError:
            checks.append(("binary csv rejected", True))
        # A column mixing text and numbers must be reported; the old condition
        # required a text majority and a numeric majority at once, so it never fired.
        mixed = os.path.join(tmp, "mixed.csv")
        with open(mixed, "w", encoding="utf-8", newline="") as fh:
            fh.write("값\n가\n10\n나\n20\n다\n")
        mixed_codes = {i["code"] for i in profile_rows(read_rows(mixed)["rows"])["issues"]}
        checks.append(("mixed types reported", "MIXED_TYPES" in mixed_codes))
        pure = os.path.join(tmp, "pure.csv")
        with open(pure, "w", encoding="utf-8", newline="") as fh:
            fh.write("값\n10\n20\n30\n")
        checks.append(("pure numeric no mixed",
                       "MIXED_TYPES" not in {i["code"] for i in profile_rows(read_rows(pure)["rows"])["issues"]}))
        # Year-first dates are unambiguous; only day/month-first flips with locale. The earlier code
        # flagged ISO as ambiguous, which would have made every ISO date column look dangerous.
        ymd = os.path.join(tmp, "ymd.csv")
        with open(ymd, "w", encoding="utf-8", newline="") as fh:
            fh.write("일자\n2026. 1. 31.\n2026-02-28\n")
        ymd_codes = {i["code"] for i in profile_rows(read_rows(ymd)["rows"])["issues"]}
        checks.append(("ymd not ambiguous", "AMBIGUOUS_DATE" not in ymd_codes))
        checks.append(("ymd still text", "LOCALE_DATE_TEXT" in ymd_codes))
        mdy = os.path.join(tmp, "mdy.csv")
        with open(mdy, "w", encoding="utf-8", newline="") as fh:
            fh.write("일자\n01/31/2026\n31/01/2026\n")
        mdy_codes = {i["code"] for i in profile_rows(read_rows(mdy)["rows"])["issues"]}
        checks.append(("mdy ambiguous", "AMBIGUOUS_DATE" in mdy_codes))
        # A phone number keeps its leading zero as text; only an all-digit token loses one.
        phone = os.path.join(tmp, "phone.csv")
        with open(phone, "w", encoding="utf-8", newline="") as fh:
            fh.write("연락처,코드,수량\n010-1234-5678,00123,7\n")
        phone_cols = {c["name"]: c for c in profile_rows(read_rows(phone)["rows"])["columns"]}
        checks.append(("phone no zero warning", phone_cols["연락처"]["leadingZeros"] == 0))
        checks.append(("code zero warning", phone_cols["코드"]["leadingZeros"] == 1))
        # A code column must not be called numeric: that label is what tells a caller
        # to convert it, which is exactly the step that erases the zero.
        checks.append(("code column is text", phone_cols["코드"]["kind"] == "text"))
        checks.append(("plain number stays numeric", phone_cols["수량"]["kind"] == "number"))
    failed = [name for name, ok in checks if not ok]
    print(json.dumps({"ok": not failed, "checks": len(checks), "failed": failed}, ensure_ascii=False))
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sheet")
    parser.add_argument("--rows", type=int)
    parser.add_argument("--encoding", default="auto")
    parser.add_argument("--delimiter")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.path or not os.path.isfile(args.path):
        parser.print_usage(sys.stderr)
        return 2
    try:
        loaded = read_rows(args.path, args.sheet, args.encoding, args.delimiter)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": "E_READ", "detail": str(exc)}, ensure_ascii=False))
        return 2
    profile = profile_rows(loaded["rows"], args.rows)
    profile.update({"schemaVersion": 1, "path": args.path, "source": loaded["source"],
                    "encoding": loaded.get("encoding"), "delimiter": loaded.get("delimiter"),
                    "bom": loaded.get("bom")})
    if profile["issues"]:
        profile["advice"].append({"column": "*", "note": "%d개 문제를 고친 뒤 변환한다" % len(profile["issues"])})
    print(json.dumps(profile, ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

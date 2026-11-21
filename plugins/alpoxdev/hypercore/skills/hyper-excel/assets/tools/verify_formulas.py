#!/usr/bin/env python3
"""Recompute a workbook's formulas without Excel and report what disagrees.

Usage:
    python3 verify_formulas.py <workbook> [--json] [--sheet NAME] [--max-cells N]
                               [--static-only] [--self-test]

The evaluator covers arithmetic, comparisons, text joins, and the aggregation,
lookup, conditional, and date functions listed in `SUPPORTED`. A formula outside
that set is reported as `unevaluated`, never as correct. Every formula cell is
recomputed from the stored inputs, then compared with the value the file cached,
so a stale or hand-edited cache is visible instead of assumed.

Output (stdout): one JSON object.
    {"schemaVersion": 1, "path", "sha256",
     "totals": {formulas, evaluated, mismatched, unevaluated, cycles, errors,
                errorLiterals, staticFindings},
     "mismatches": [{sheet, ref, formula, cached, computed, delta}],
     "unevaluated": [{sheet, ref, formula, reason}],
     "errorCells": [{sheet, ref, formula, error}],
     "findings": [{code, severity, sheet, ref, detail, hint}],
     "checks": [{name, status, detail}]}

Exit codes: 0 every formula checked out, 1 a defect was found, 2 usage or
unreadable input. Nothing is written.
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlib  # noqa: E402

SUPPORTED = (
    "SUM", "AVERAGE", "MIN", "MAX", "COUNT", "COUNTA", "COUNTBLANK", "PRODUCT",
    "MEDIAN", "STDEV", "STDEVP", "VAR", "VARP",
    "ROUND", "ROUNDUP", "ROUNDDOWN", "ABS", "INT", "MOD", "POWER", "SQRT", "EXP", "LN", "LOG10",
    "IF", "IFERROR", "IFNA", "AND", "OR", "NOT", "TRUE", "FALSE",
    "SUMIF", "SUMIFS", "COUNTIF", "COUNTIFS", "AVERAGEIF", "AVERAGEIFS",
    "MAXIFS", "MINIFS", "SUMPRODUCT",
    "INDEX", "MATCH", "VLOOKUP", "HLOOKUP", "CHOOSE",
    "LEFT", "RIGHT", "MID", "LEN", "TRIM", "UPPER", "LOWER", "CONCATENATE", "CONCAT", "TEXTJOIN",
    "TEXT", "VALUE", "DATE", "YEAR", "MONTH", "DAY", "EOMONTH", "WORKDAY", "NETWORKDAYS", "YEARFRAC",
    "ISBLANK", "ISNUMBER", "ISTEXT", "ISERROR", "ISERR", "ISNA",
    "ROW", "COLUMN", "COLUMNS", "ROWS", "NA", "N",
)
IS_PREDICATES = ("ISBLANK", "ISNUMBER", "ISTEXT", "ISERROR", "ISERR", "ISNA")
UNSUPPORTED_KNOWN = (
    "XLOOKUP", "XMATCH", "FILTER", "SORT", "SORTBY", "UNIQUE", "SEQUENCE", "LET", "LAMBDA",
    "OFFSET", "INDIRECT", "NOW", "TODAY", "RAND", "RANDBETWEEN", "GETPIVOTDATA",
    "DSUM", "DCOUNT", "SUBTOTAL", "AGGREGATE", "TEXTBEFORE", "TEXTAFTER", "TEXTSPLIT",
    "SUMX", "LOOKUP", "WEBSERVICE", "STOCKHISTORY", "PY",
)


class FormulaError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class Unsupported(Exception):
    pass


class Cycle(Exception):
    pass


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# A sheet qualifier may be quoted ('My Sheet'!A1) or bare (매출!B5). Bare names
# are any unicode word start, because localized sheet names are ordinary here.
SHEET = r"(?:'(?:[^']|'')+'|[^\W\d][\w.]*)!"
TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<string>"(?:[^"]|"")*")
  | (?P<error>\#[A-Z0-9/!]+)
  | (?P<ref>(?:%s)?\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?)
  | (?P<colrange>(?:%s)?\$?[A-Za-z]{1,3}:\$?[A-Za-z]{1,3})
  | (?P<rowrange>(?:%s)?\$?\d+:\$?\d+)
  | (?P<func>[A-Za-z_][A-Za-z0-9_.]*(?=\())
  | (?P<name>[^\W\d][\w.]*)
  | (?P<number>\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+)
  | (?P<op><>|<=|>=|[-+*/^&=<>%%(),;:])
""" % (SHEET, SHEET, SHEET), re.VERBOSE | re.UNICODE)


def tokenize(text):
    tokens, pos = [], 0
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise Unsupported("unparsed token at %r" % text[pos:pos + 12])
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        tokens.append((kind, m.group()))
    return tokens


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def to_number(value):
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if value in xlsxlib.ERROR_LITERALS:
            raise FormulaError(value)
        text = value.strip().replace(",", "")
        if text.startswith("%") or text.endswith("%"):
            text = text.strip("%")
            try:
                return float(text) / 100.0
            except ValueError:
                raise FormulaError("#VALUE!")
        try:
            return float(text)
        except ValueError:
            raise FormulaError("#VALUE!")
    raise FormulaError("#VALUE!")


def to_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


class Range(list):
    """A range flattened row-major that still knows its shape.

    Most functions (SUM, COUNT, AND, ...) only need the flat values, but ROWS,
    COLUMNS and INDEX are defined by the 2-D shape; a plain list loses it, which is
    how ROWS(A1:B4) used to answer 8 and INDEX(A2:B4,2,1) answered an element of a
    flattened list instead of A3.
    """

    def __init__(self, values, nrows, ncols):
        super().__init__(values)
        self.nrows = nrows
        self.ncols = ncols


def _same_value(left, right):
    """Excel's lookup equality: numbers compare numerically, text case-insensitively."""
    if left is None or right is None:
        return False
    if isinstance(left, str) and isinstance(right, str):
        return left.lower() == right.lower()
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) == bool(right)
    try:
        return to_number(left) == to_number(right)
    except FormulaError:
        return False


def _power(base, exponent):
    """Excel's `^`/`POWER` domain: a negative base with a fractional exponent is
    `#NUM!`, never a complex number, and an overflowing result is `#NUM!` too.
    Returning a Python complex silently poisons the JSON report downstream.
    """
    try:
        result = base ** exponent
    except (OverflowError, ZeroDivisionError, ValueError):
        raise FormulaError("#NUM!")
    if isinstance(result, complex):
        raise FormulaError("#NUM!")
    if isinstance(result, float) and (math.isinf(result) or math.isnan(result)):
        raise FormulaError("#NUM!")
    return result


def truthy(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        if value.upper() in ("TRUE", "FALSE"):
            return value.upper() == "TRUE"
        raise FormulaError("#VALUE!")
    raise FormulaError("#VALUE!")


def flatten(args):
    for arg in args:
        if isinstance(arg, list):
            for item in arg:
                yield item
        else:
            yield arg


def numbers_only(args):
    out = []
    for item in flatten(args):
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            out.append(float(item))
        elif isinstance(item, str):
            if item in xlsxlib.ERROR_LITERALS:
                raise FormulaError(item)
    return out


def wildcard_regex(pattern):
    out = ""
    for ch in pattern:
        if ch == "*":
            out += ".*"
        elif ch == "?":
            out += "."
        elif ch == "~":
            out += "\x00"
        else:
            out += re.escape(ch)
    return re.compile("^" + out.replace("\x00", "~") .replace("\\~", "~") + "$", re.IGNORECASE | re.DOTALL)


def criteria_test(value, criterion):
    op = "="
    target = criterion
    if isinstance(criterion, str):
        m = re.match(r"^(<=|>=|<>|<|>|=)\s*(.*)$", criterion.strip())
        if m:
            op, target = m.group(1), m.group(2)
        if any(w in target for w in "*?") and op in ("=", "<>"):
            same = bool(wildcard_regex(target).match(to_text(value)))
            return same if op == "=" else not same
        if target == "":
            target = None
    if target is None:
        # An empty criterion counts blanks. Excel's "<>" counts non-empty cells,
        # so a blank must fail it.
        empty = value is None or value == ""
        return {"=": empty, "<>": not empty, "<": False, ">": False, "<=": empty, ">=": empty}[op]
    if isinstance(target, str):
        try:
            target_num = float(target)
        except ValueError:
            target_num = None
        if target_num is None:
            left, right = to_text(value).lower(), target.lower()
        else:
            # A numeric criterion never matches a blank or a text cell in Excel:
            # COUNTIF over 3 numbers and 5 blanks is 3, not 8.
            if value is None or value == "":
                return op == "<>"
            if isinstance(value, str):
                try:
                    left = float(value)
                except ValueError:
                    return op == "<>"
                right = target_num
            else:
                left, right = to_number(value), target_num
    else:
        if value is None or value == "":
            return op == "<>"
        left, right = to_number(value), to_number(target)
    if op == "=":
        return left == right
    if op == "<>":
        return left != right
    if op == "<":
        return left < right
    if op == ">":
        return left > right
    if op == "<=":
        return left <= right
    return left >= right


DEFAULT_EPOCH = date(1899, 12, 30)


def excel_serial(d, epoch=DEFAULT_EPOCH):
    if isinstance(d, float):
        return d
    return float((d - epoch).days)


def serial_to_date(serial, epoch=DEFAULT_EPOCH):
    return epoch + timedelta(days=int(math.floor(serial)))


def numfmt_text(value, code, epoch=DEFAULT_EPOCH):
    """Render a number with the handful of format shapes a report needs to confirm."""
    low = (code or "").lower()
    num = to_number(value)
    if "%" in low:
        decimals = len(low.split("%")[0].split(".")[1]) if "." in low.split("%")[0] else 0
        return ("{:,.%df}%%" % decimals).replace("{:,.%df}", "{:,.%df}" % decimals).format(num * 100)
    if any(h in low for h in xlsxlib.DATE_FMT_HINTS):
        d = serial_to_date(num, epoch)
        if "h:" in low or "h:" in low:
            return d.isoformat()
        if "yy" in low and "mm" in low and "dd" in low:
            return "%04d-%02d-%02d" % (d.year, d.month, d.day)
        if "mmm" in low:
            return "%04d-%02d" % (d.year, d.month)
        return d.isoformat()
    if "0.00" in low:
        return ("{:.2f}".format(num)).replace(",", "")
    if "#,##0" in low:
        return "{:,.0f}".format(num)
    if num == int(num):
        return str(int(num))
    return repr(num)


class Evaluator:
    """Evaluates formulas over one workbook, memoizing every resolved cell."""

    def __init__(self, wb):
        self.wb = wb
        self.sheet_cells = {}
        self.sheet_parts = {}
        self.defined = {}
        # A 1904 workbook counts days from 1904-01-01; every date function has to
        # shift or YEAR/MONTH/DAY come back four years and one day off.
        self.date1904 = bool(getattr(wb, "date1904", False))
        self.epoch = date(1904, 1, 1) if self.date1904 else date(1899, 12, 30)
        for name, part, state in wb.sheets:
            if state == "chartsheet" or not part:
                continue
            cells = {}
            for row_no, row in wb.iter_rows(part):
                for cell in row:
                    cells[(cell["col"], cell["row"])] = cell
            self.sheet_cells[name] = cells
            self.sheet_parts[name] = part
        for dn in wb.defined_names:
            if dn["scope"] == "workbook":
                self.defined[dn["name"].upper()] = dn["formula"]
        self.memo = {}
        self.busy = set()
        self.stats = {"evaluated": 0, "unevaluated": 0, "cycles": 0, "errors": 0}
    # -- cell resolution ----------------------------------------------------
    def cell_value(self, sheet, col, row, depth=0):
        key = (sheet, col, row)
        if key in self.memo:
            return self.memo[key]
        cell = self.sheet_cells.get(sheet, {}).get((col, row))
        if cell is None:
            return None
        if not cell["formula"]:
            return cell["value"]
        if key in self.busy:
            raise Cycle()
        if depth > 200:
            raise Unsupported("dependency depth over 200")
        self.busy.add(key)
        try:
            value = self.evaluate(cell["formula"], sheet, row, col, depth + 1)
        finally:
            self.busy.discard(key)
        self.memo[key] = value
        return value

    def range_values(self, sheet, bounds):
        if not bounds:
            raise Unsupported("open range")
        c1, r1, c2, r2 = bounds
        if (c2 - c1 + 1) * (r2 - r1 + 1) > 2_000_000:
            raise Unsupported("range over 2,000,000 cells")
        out = []
        cells = self.sheet_cells.get(sheet, {})
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                cell = cells.get((c, r))
                out.append(None if cell is None else (self.cell_value(sheet, c, r) if cell["formula"] else cell["value"]))
        return Range(out, r2 - r1 + 1, c2 - c1 + 1)

    def resolve_sheet(self, prefix, current_sheet):
        if prefix is None:
            return current_sheet
        name = prefix.rstrip("!")
        if name.startswith("'") and name.endswith("'"):
            name = name[1:-1].replace("''", "'")
        if name not in self.sheet_cells:
            raise FormulaError("#REF!")
        return name

    def ref_value(self, token, current_sheet, current_row, current_col):
        sheet_part, cell_part = xlsxlib.split_sheet_qualified(token)
        sheet = self.resolve_sheet(sheet_part, current_sheet)
        cell_part = cell_part.replace("$", "")
        if re.match(r"^[A-Za-z]{1,3}:\$?[A-Za-z]{1,3}$", cell_part) or re.match(r"^[A-Za-z]{1,3}:[A-Za-z]{1,3}$", cell_part):
            first, _, last = cell_part.partition(":")
            c1, c2 = xlsxlib.col_index(first), xlsxlib.col_index(last)
            rows = [r for (c, r) in self.sheet_cells.get(sheet, {}) if c1 <= c <= c2]
            if not rows:
                return Range([], 0, abs(c2 - c1) + 1)
            return self.range_values(sheet, (min(c1, c2), min(rows), max(c1, c2), max(rows)))
        if re.match(r"^\d+:\d+$", cell_part):
            r1, r2 = (int(x) for x in cell_part.split(":"))
            cols = [c for (c, r) in self.sheet_cells.get(sheet, {}) if r1 <= r <= r2]
            if not cols:
                return Range([], abs(r2 - r1) + 1, 0)
            return self.range_values(sheet, (min(cols), min(r1, r2), max(cols), max(r1, r2)))
        bounds = xlsxlib.range_bounds(cell_part)
        if not bounds:
            raise FormulaError("#REF!")
        if ":" in cell_part:
            return self.range_values(sheet, bounds)
        c, r = bounds[0], bounds[1]
        return self.cell_value(sheet, c, r)

    # -- expression evaluation ---------------------------------------------
    def evaluate(self, formula, sheet, row=None, col=None, depth=0):
        text = formula[1:] if formula.startswith("=") else formula
        text = re.sub(r"\s*\[shared[^\]]*\]$", "", text)
        if not text.strip():
            return None
        # A formula that references another formula cell re-enters evaluate() while
        # the outer parse is mid-expression. The token stream and cursor are parse
        # state, not evaluator state, so they are saved and restored around the call;
        # without this the outer formula continues reading the inner formula's tokens
        # and returns a wrong number.
        saved = (getattr(self, "tokens", None), getattr(self, "pos", 0), getattr(self, "ctx", None))
        try:
            self.tokens = tokenize(text)
            self.pos = 0
            self.ctx = (sheet, row, col, depth)
            value = self.parse_comparison()
            if self.pos != len(self.tokens):
                raise Unsupported("trailing tokens: %r" % (self.tokens[self.pos:],))
            return value
        finally:
            self.tokens, self.pos, self.ctx = saved

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def take(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, value):
        kind, got = self.take()
        if got != value:
            raise Unsupported("expected %r, got %r" % (value, got))

    def parse_comparison(self):
        left = self.parse_concat()
        while True:
            kind, op = self.peek()
            if op not in ("=", "<>", "<", ">", "<=", ">="):
                return left
            self.take()
            right = self.parse_concat()
            if isinstance(left, list) or isinstance(right, list):
                raise Unsupported("array comparison")
            if isinstance(left, str) and left in xlsxlib.ERROR_LITERALS:
                raise FormulaError(left)
            if isinstance(right, str) and right in xlsxlib.ERROR_LITERALS:
                raise FormulaError(right)
            if isinstance(left, str) or isinstance(right, str):
                a, b = to_text(left).lower(), to_text(right).lower()
            else:
                a, b = to_number(left), to_number(right)
            left = {"=": a == b, "<>": a != b, "<": a < b, ">": a > b,
                    "<=": a <= b, ">=": a >= b}[op]

    def parse_concat(self):
        left = self.parse_additive()
        while self.peek()[1] == "&":
            self.take()
            right = self.parse_additive()
            left = to_text(left) + to_text(right)
        return left

    def parse_additive(self):
        left = self.parse_term()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            right = self.parse_term()
            a, b = to_number(left), to_number(right)
            left = a + b if op == "+" else a - b
        return left

    def parse_term(self):
        left = self.parse_power()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            right = self.parse_power()
            a, b = to_number(left), to_number(right)
            if op == "*":
                left = a * b
            else:
                if b == 0:
                    raise FormulaError("#DIV/0!")
                left = a / b
        return left

    def parse_power(self):
        left = self.parse_unary()
        while self.peek()[1] == "^":
            self.take()
            right = self.parse_unary()
            left = _power(to_number(left), to_number(right))
        return left

    def parse_unary(self):
        kind, op = self.peek()
        if op == "-":
            self.take()
            return -to_number(self.parse_unary())
        if op == "+":
            self.take()
            return to_number(self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        value = self.parse_primary()
        while self.peek()[1] == "%":
            self.take()
            value = to_number(value) / 100.0
        return value

    def parse_primary(self):
        kind, token = self.take()
        sheet, row, col, _ = self.ctx
        if kind == "number":
            return float(token)
        if kind == "string":
            return token[1:-1].replace('""', '"')
        if kind == "error":
            raise FormulaError(token)
        if kind == "ref" or kind == "colrange" or kind == "rowrange":
            return self.ref_value(token, sheet, row, col)
        if token == "(":
            value = self.parse_comparison()
            self.expect(")")
            return value
        if kind == "func":
            return self.call_function(token.upper())
        if kind == "name":
            return self.resolve_name(token)
        raise Unsupported("unexpected token %r" % (token,))

    def resolve_name(self, name):
        upper = name.upper()
        if upper in ("TRUE", "FALSE"):
            return upper == "TRUE"
        if upper in ("NULL",):
            return None
        if upper in self.defined:
            target = self.defined[upper]
            value = self.evaluate("=" + target, self.ctx[0], self.ctx[1], self.ctx[2], self.ctx[3])
            return value
        raise Unsupported("name %r" % name)

    def call_function(self, name):
        if name not in SUPPORTED:
            raise Unsupported("function %s" % name)
        self.expect("(")
        # IF and the error guards must not evaluate a branch they never take:
        # IF(FALSE,1/0,0) is 0 in Excel, and IFERROR(1/0,"-") is "-".
        if name in ("IF", "IFERROR", "IFNA"):
            return self.call_lazy(name)
        # The IS* predicates inspect an error value instead of propagating it:
        # ISERROR(1/0) is TRUE in Excel. Evaluating the argument eagerly would raise
        # first, so `IF(ISERROR(1/0),0,1)` wrongly returned #DIV/0!.
        if name in IS_PREDICATES:
            return self.call_predicate(name)
        args = []
        if self.peek()[1] == ")":
            self.take()
        else:
            while True:
                args.append(self.parse_comparison())
                kind, token = self.take()
                if token == ")":
                    break
                if token not in (",", ";"):
                    raise Unsupported("argument separator %r" % (token,))
        return self.apply(name, args)

    def resync(self):
        """Skip to the next top-level argument separator after a failed sub-expression."""
        depth = 0
        while self.pos < len(self.tokens):
            kind, token = self.peek()
            if token == "(":
                depth += 1
            elif token == ")":
                if depth == 0:
                    return
                depth -= 1
            elif token in (",", ";") and depth == 0:
                return
            self.pos += 1

    def guarded(self):
        """Evaluate one argument, returning (value, error_code) instead of raising."""
        try:
            return (self.parse_comparison(), None)
        except FormulaError as exc:
            self.resync()
            return (None, exc.code)
        except Unsupported:
            self.resync()
            raise

    def call_predicate(self, name):
        """One-argument IS* predicate whose argument is evaluated guarded."""
        value, err = self.guarded()
        if self.peek()[1] == ")":
            self.take()
        elif err is None:
            raise Unsupported("%s with more than one argument" % name)
        else:
            err = None  # the extra tokens were part of the failed argument
            self.expect(")")
        return self.apply(name, [err if err is not None else value])

    def call_lazy(self, name):
        """IF / IFERROR / IFNA with only the taken branch evaluated."""
        first, err = self.guarded()
        if name == "IF":
            if err:
                raise FormulaError(err)
            if self.peek()[1] == ")":
                self.take()
                return bool(truthy(first))
            self.expect(",")
            cond = truthy(first)
            value_true, value_false = None, False
            if self.peek()[1] == ")":
                self.take()
                return True
            if cond:
                value_true, sub_err = self.guarded()
                if sub_err:
                    raise FormulaError(sub_err)
            else:
                self.skip_expression()
            if self.peek()[1] == ",":
                self.take()
                if self.peek()[1] == ")":
                    self.take()
                elif cond:
                    self.skip_expression()
                    self.expect(")")
                else:
                    value_false, sub_err = self.guarded()
                    if sub_err:
                        raise FormulaError(sub_err)
                    self.expect(")")
            else:
                self.expect(")")
            return value_true if cond else value_false
        # IFERROR / IFNA: the fallback only runs when the first value failed.
        if self.peek()[1] == ")":
            self.take()
            if err:
                raise FormulaError(err)
            return first
        self.expect(",")
        if err is None:
            self.skip_expression()
            self.expect(")")
            return first
        fallback = self.parse_comparison()
        self.expect(")")
        if name == "IFERROR":
            return fallback
        if err == "#N/A":
            return fallback
        raise FormulaError(err)

    def skip_expression(self):
        """Consume one argument's tokens without evaluating it."""
        depth = 0
        while self.pos < len(self.tokens):
            kind, token = self.peek()
            if token == "(":
                depth += 1
            elif token == ")":
                if depth == 0:
                    return
                depth -= 1
            elif token in (",", ";") and depth == 0:
                return
            self.pos += 1

    def skip_to_close(self):
        depth = 0
        while self.pos < len(self.tokens):
            kind, token = self.take()
            if token == "(":
                depth += 1
            elif token == ")":
                if depth == 0:
                    return
                depth -= 1

    def apply(self, name, args):  # noqa: C901 - one dispatcher is clearer than a class per function
        if name == "SUM":
            return math.fsum(numbers_only(args))
        if name == "PRODUCT":
            out = 1.0
            for n in numbers_only(args):
                out *= n
            return out
        if name == "AVERAGE":
            nums = numbers_only(args)
            if not nums:
                raise FormulaError("#DIV/0!")
            return math.fsum(nums) / len(nums)
        if name in ("MEDIAN", "STDEV", "STDEVP", "VAR", "VARP"):
            return self.distribution(name, args)
        if name == "MIN":
            nums = numbers_only(args)
            return min(nums) if nums else 0
        if name == "MAX":
            nums = numbers_only(args)
            return max(nums) if nums else 0
        if name == "COUNT":
            return float(len(numbers_only(args)))
        if name == "COUNTA":
            return float(sum(1 for v in flatten(args) if v is not None and v != ""))
        if name == "COUNTBLANK":
            return float(sum(1 for v in flatten(args) if v is None or v == ""))
        if name == "ROUND":
            digits = int(to_number(args[1])) if len(args) > 1 else 0
            value = to_number(args[0])
            factor = 10 ** digits
            return math.floor(abs(value) * factor + 0.5) / factor * (1 if value >= 0 else -1)
        if name == "ROUNDUP":
            digits = int(to_number(args[1])) if len(args) > 1 else 0
            factor = 10 ** digits
            value = to_number(args[0])
            return math.ceil(abs(value) * factor) / factor * (1 if value >= 0 else -1)
        if name == "ROUNDDOWN":
            digits = int(to_number(args[1])) if len(args) > 1 else 0
            factor = 10 ** digits
            value = to_number(args[0])
            return math.floor(abs(value) * factor) / factor * (1 if value >= 0 else -1)
        if name == "ABS":
            return abs(to_number(args[0]))
        if name == "INT":
            return float(math.floor(to_number(args[0])))
        if name == "MOD":
            a, b = to_number(args[0]), to_number(args[1])
            if b == 0:
                raise FormulaError("#DIV/0!")
            return a - b * math.floor(a / b)
        if name == "POWER":
            return _power(to_number(args[0]), to_number(args[1]))
        if name == "SQRT":
            value = to_number(args[0])
            if value < 0:
                raise FormulaError("#NUM!")
            return math.sqrt(value)
        if name == "EXP":
            return math.exp(to_number(args[0]))
        if name == "LN":
            value = to_number(args[0])
            if value <= 0:
                raise FormulaError("#NUM!")
            return math.log(value)
        if name == "LOG10":
            value = to_number(args[0])
            if value <= 0:
                raise FormulaError("#NUM!")
            return math.log10(value)
        if name == "IF":
            cond = truthy(args[0])
            if cond:
                return args[1] if len(args) > 1 else True
            return args[2] if len(args) > 2 else False
        if name == "IFERROR":
            try:
                value = args[0]
                if isinstance(value, str) and value in xlsxlib.ERROR_LITERALS:
                    return args[1]
                return value
            except FormulaError:
                return args[1]
        if name == "IFNA":
            value = args[0]
            if isinstance(value, str) and value == "#N/A":
                return args[1]
            return value
        if name == "AND":
            return all(truthy(v) for v in flatten(args) if v is not None)
        if name == "OR":
            return any(truthy(v) for v in flatten(args) if v is not None)
        if name == "NOT":
            return not truthy(args[0])
        if name == "TRUE":
            return True
        if name == "FALSE":
            return False
        if name == "SUMIF":
            return self.conditional(args, mode="sum")
        if name == "SUMIFS":
            return self.conditional_multi(args, mode="sum")
        if name == "AVERAGEIF":
            return self.conditional(args, mode="average")
        if name == "AVERAGEIFS":
            return self.conditional_multi(args, mode="average")
        if name == "COUNTIF":
            return self.conditional(args, mode="count")
        if name == "COUNTIFS":
            return self.conditional_multi(args, mode="count")
        if name == "MAXIFS":
            return self.conditional_multi(args, mode="max")
        if name == "MINIFS":
            return self.conditional_multi(args, mode="min")
        if name == "SUMPRODUCT":
            lists = [a for a in args if isinstance(a, list)]
            if len(lists) != len(args) or not lists:
                raise Unsupported("SUMPRODUCT with non-range arguments")
            size = len(lists[0])
            if any(len(lst) != size for lst in lists):
                raise FormulaError("#VALUE!")
            total = 0.0
            for i in range(size):
                product = 1.0
                for lst in lists:
                    item = lst[i]
                    product *= (1.0 if item is True else 0.0) if isinstance(item, bool) else to_number(item)
                total += product
            return total
        if name == "INDEX":
            array = args[0]
            row_idx = int(to_number(args[1])) if len(args) > 1 else 1
            col_idx = int(to_number(args[2])) if len(args) > 2 else 1
            if isinstance(array, Range):
                # Flat list indexes would answer the wrong cell for any range wider
                # than one column; the shape is what maps (row, col) to an offset.
                if row_idx < 1 or col_idx < 1:
                    raise FormulaError("#VALUE!")
                if row_idx > array.nrows or col_idx > array.ncols:
                    raise FormulaError("#REF!")
                return array[(row_idx - 1) * array.ncols + (col_idx - 1)]
            if isinstance(array, list):
                if row_idx < 1:
                    raise FormulaError("#VALUE!")
                if col_idx == 1 and row_idx <= len(array):
                    return array[row_idx - 1]
                raise Unsupported("INDEX over a 2-D array")
            if row_idx != 1 or col_idx != 1:
                raise FormulaError("#REF!")
            return array
        if name == "MATCH":
            needle = args[0]
            haystack = args[1] if isinstance(args[1], list) else [args[1]]
            match_type = to_number(args[2]) if len(args) > 2 else 1
            if needle is None or (isinstance(needle, str) and needle == ""):
                raise Unsupported("MATCH on an empty lookup value")
            best = None
            for idx, item in enumerate(haystack, start=1):
                if match_type == 0:
                    if isinstance(needle, str) and any(w in needle for w in "*?"):
                        if wildcard_regex(needle).match(to_text(item)):
                            return float(idx)
                        continue
                    if isinstance(needle, str) and isinstance(item, str):
                        if needle.lower() == item.lower():
                            return float(idx)
                    elif not isinstance(item, str) or not isinstance(needle, str):
                        # A text needle against a numeric cell is simply not a match;
                        # coercing it raised #VALUE! instead of reaching the #N/A the
                        # caller's IFNA/ISNA expects.
                        try:
                            if item is not None and to_number(item) == to_number(needle):
                                return float(idx)
                        except FormulaError:
                            continue
                else:
                    try:
                        if to_number(item) <= to_number(needle):
                            best = idx
                        else:
                            break
                    except FormulaError:
                        continue
            # A failed lookup is #N/A in Excel, which is what IFNA/ISNA test for;
            # #VALUE! would make every IFNA wrapper take the wrong branch.
            raise FormulaError("#N/A")
            return float(best)
        if name in ("VLOOKUP", "HLOOKUP"):
            return self.lookup_grid(name, args)
        if name == "CHOOSE":
            index = int(to_number(args[0]))
            if index < 1 or index >= len(args):
                raise FormulaError("#VALUE!")
            return args[index]
        if name in ("LEFT", "RIGHT", "MID", "LEN", "TRIM", "UPPER", "LOWER", "TEXTJOIN", "CONCATENATE", "CONCAT"):
            return self.text_function(name, args)
        if name == "TEXT":
            return numfmt_text(args[0], to_text(args[1]), self.epoch)
        if name == "VALUE":
            return to_number(args[0])
        if name == "DATE":
            y, m, d = (int(to_number(a)) for a in args[:3])
            return excel_serial(date(y, m, 1) + timedelta(days=d - 1), self.epoch)
        if name == "YEAR":
            return float(serial_to_date(to_number(args[0]), self.epoch).year)
        if name == "MONTH":
            return float(serial_to_date(to_number(args[0]), self.epoch).month)
        if name == "DAY":
            return float(serial_to_date(to_number(args[0]), self.epoch).day)
        if name in ("WORKDAY", "NETWORKDAYS"):
            return self.workdays(name, args)
        if name == "YEARFRAC":
            return self.yearfrac(args)
        if name == "EOMONTH":
            start = serial_to_date(to_number(args[0]), self.epoch)
            months = int(to_number(args[1]))
            year = start.year + (start.month - 1 + months) // 12
            month = (start.month - 1 + months) % 12 + 1
            nxt = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
            return excel_serial(nxt - timedelta(days=1), self.epoch)
        if name == "ISBLANK":
            return args[0] is None or args[0] == ""
        if name == "ISNUMBER":
            return isinstance(args[0], (int, float)) and not isinstance(args[0], bool)
        if name == "ISTEXT":
            return isinstance(args[0], str) and args[0] not in xlsxlib.ERROR_LITERALS
        if name == "ISERROR":
            return isinstance(args[0], str) and args[0] in xlsxlib.ERROR_LITERALS
        if name == "ISERR":
            return isinstance(args[0], str) and args[0] in xlsxlib.ERROR_LITERALS and args[0] != "#N/A"
        if name == "ISNA":
            return isinstance(args[0], str) and args[0] == "#N/A"
        if name == "ROW":
            if args:
                raise Unsupported("ROW over a reference")
            return float(self.ctx[1]) if self.ctx[1] else 1.0
        if name == "COLUMN":
            if args:
                raise Unsupported("COLUMN over a reference")
            return float(self.ctx[2]) if self.ctx[2] else 1.0
        if name == "COLUMNS":
            if isinstance(args[0], Range):
                return float(args[0].ncols)
            return 1.0
        if name == "ROWS":
            if isinstance(args[0], Range):
                return float(args[0].nrows)
            return 1.0
        if name == "NA":
            raise FormulaError("#N/A")
        if name == "N":
            return to_number(args[0])
        raise Unsupported("function %s" % name)

    # A Korean business calendar still counts Saturday and Sunday as the weekend,
    # and no holiday list is supplied by the formula, so the two functions agree
    # with Excel only when the workbook passes no holidays.
    def workdays(self, name, args):
        """WORKDAY(start, days) counts forward; NETWORKDAYS(start, end) counts both
        ends. The second argument means different things, which is why they cannot
        share one loop: WORKDAY takes a day count, NETWORKDAYS an end date serial.
        """
        start = serial_to_date(to_number(args[0]), self.epoch)
        holidays = set()
        if len(args) > 2:
            for item in flatten(args[2:]):
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    holidays.add(serial_to_date(item, self.epoch))
        if name == "WORKDAY":
            span = int(to_number(args[1]))
            remaining, cursor = abs(span), start
            step = 1 if span >= 0 else -1
            while remaining:
                cursor += timedelta(days=step)
                if cursor.weekday() < 5 and cursor not in holidays:
                    remaining -= 1
            return excel_serial(cursor, self.epoch)
        end = serial_to_date(to_number(args[1]), self.epoch)
        if end == start:
            return 1.0 if start.weekday() < 5 and start not in holidays else 0.0
        step = 1 if end > start else -1
        cursor, counted = start, 0
        while cursor != end:
            if cursor.weekday() < 5 and cursor not in holidays:
                counted += step
            cursor += timedelta(days=step)
        if end.weekday() < 5 and end not in holidays:
            counted += step
        return float(counted)

    def yearfrac(self, args):
        """YEARFRAC basis 0 (US 30/360) and 1 (actual/actual) as Excel defines them."""
        start = serial_to_date(to_number(args[0]), self.epoch)
        end = serial_to_date(to_number(args[1]), self.epoch)
        basis = int(to_number(args[2])) if len(args) > 2 else 0
        if basis == 1:
            if start == end:
                return 0.0
            low, high = (start, end) if start < end else (end, start)
            years = high.year - low.year
            if years == 0:
                return (high - low).days / (366.0 if self._leap(low.year) else 365.0)
            total = 0.0
            for year in range(low.year, high.year + 1):
                first = max(low, date(year, 1, 1))
                last = min(high, date(year, 12, 31))
                total += max((last - first).days + 1, 0) / (366.0 if self._leap(year) else 365.0)
            return total if start < end else -total
        if basis == 0:
            d1, d2 = start.day, end.day
            if d1 == 31:
                d1 = 30
            if d2 == 31 and d1 == 30:
                d2 = 30
            days = (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)
            return days / 360.0
        raise Unsupported("YEARFRAC basis %d" % basis)

    @staticmethod
    def _leap(year):
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def lookup_grid(self, name, args):
        """VLOOKUP/HLOOKUP with Excel's exact and approximate modes.

        `range_lookup` 0/FALSE is an exact match and returns #N/A when absent;
        omitted or TRUE walks the first row/column in ascending order and returns
        the last value at or below the needle. The 2-D shape is required here, so a
        flattened list cannot answer the wrong column without anyone noticing.
        """
        needle = args[0]
        table = args[1]
        if not isinstance(table, Range):
            raise Unsupported("%s over a non-range" % name)
        index = int(to_number(args[2]))
        approximate = len(args) < 4 or truthy(args[3])
        horizontal = name == "HLOOKUP"
        span = table.ncols if horizontal else table.nrows
        depth = table.nrows if horizontal else table.ncols
        if index < 1 or index > depth:
            raise FormulaError("#REF!")
        if span == 0:
            raise FormulaError("#N/A")
        head = [table[i * table.ncols] if not horizontal else table[i] for i in range(span)]
        hit = None
        for pos, item in enumerate(head):
            if _same_value(item, needle):
                hit = pos
                break
            if approximate:
                try:
                    if to_number(item) <= to_number(needle):
                        hit = pos
                    else:
                        break
                except FormulaError:
                    # Approximate mode orders text alphabetically; without this a
                    # text key never matches and the lookup silently returns #N/A.
                    if isinstance(item, str) and isinstance(needle, str):
                        if item.lower() <= needle.lower():
                            hit = pos
                        else:
                            break
                    continue
        if hit is None:
            raise FormulaError("#N/A")
        # The flat layout is row-major, so the offset is (row - 1) * ncols + (col - 1).
        # VLOOKUP scans a column and returns across it; HLOOKUP scans a row and
        # returns down it, which swaps the two indexes.
        if horizontal:
            return table[(index - 1) * table.ncols + hit]
        return table[hit * table.ncols + (index - 1)]

    def distribution(self, name, args):
        """MEDIAN / STDEV / STDEVP / VAR / VARP over the numeric arguments.

        Excel's sample variants (STDEV, VAR) divide by n-1 and return #DIV/0! for a
        single value; the population variants (STDEVP, VARP) divide by n and accept
        one value. MEDIAN averages the two middle values for an even count.
        """
        nums = sorted(numbers_only(args))
        if not nums:
            raise FormulaError("#NUM!")
        if name == "MEDIAN":
            middle = len(nums) // 2
            if len(nums) % 2:
                return nums[middle]
            return (nums[middle - 1] + nums[middle]) / 2.0
        sample = name in ("STDEV", "VAR")
        if sample and len(nums) < 2:
            raise FormulaError("#DIV/0!")
        mean = math.fsum(nums) / len(nums)
        divisor = len(nums) - 1 if sample else len(nums)
        variance = math.fsum((n - mean) ** 2 for n in nums) / divisor
        return math.sqrt(variance) if name.startswith("STDEV") else variance

    def text_function(self, name, args):
        if name == "LEN":
            return float(len(to_text(args[0])))
        if name == "TRIM":
            return re.sub(r"\s+", " ", to_text(args[0])).strip()
        if name == "UPPER":
            return to_text(args[0]).upper()
        if name == "LOWER":
            return to_text(args[0]).lower()
        if name in ("CONCATENATE", "CONCAT"):
            return "".join(to_text(v) for v in flatten(args))
        if name == "TEXTJOIN":
            delim = to_text(args[0])
            ignore_empty = truthy(args[1])
            parts = [to_text(v) for v in flatten(args[2:])]
            if ignore_empty:
                parts = [p for p in parts if p != ""]
            return delim.join(parts)
        if name == "LEFT":
            count = int(to_number(args[1])) if len(args) > 1 else 1
            return to_text(args[0])[:count]
        if name == "RIGHT":
            count = int(to_number(args[1])) if len(args) > 1 else 1
            return to_text(args[0])[-count:] if count else ""
        if name == "MID":
            start = int(to_number(args[1]))
            count = int(to_number(args[2]))
            return to_text(args[0])[max(start - 1, 0):max(start - 1, 0) + count]
        raise Unsupported(name)

    def conditional(self, args, mode):
        test_range = args[0] if isinstance(args[0], list) else [args[0]]
        criterion = args[1]
        values = args[2] if len(args) > 2 else test_range
        values = values if isinstance(values, list) else [values]
        if len(values) != len(test_range):
            raise FormulaError("#VALUE!")
        hits = [v for t, v in zip(test_range, values) if criteria_test(t, criterion)]
        if mode == "count":
            return float(len(hits))
        nums = [to_number(v) for v in hits if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if mode == "sum":
            return math.fsum(nums)
        if not nums:
            raise FormulaError("#DIV/0!")
        return math.fsum(nums) / len(nums)

    def conditional_multi(self, args, mode):
        if mode in ("max", "min"):
            value_range = args[0] if isinstance(args[0], list) else [args[0]]
            pairs = list(zip(args[1::2], args[2::2]))
        elif mode == "count":
            # COUNTIFS has no separate value range: every argument pair is a
            # criterion, including the first one.
            pairs = list(zip(args[0::2], args[1::2]))
            value_range = pairs[0][0] if pairs and isinstance(pairs[0][0], list) else None
            if value_range is None:
                raise Unsupported("%s without a range" % mode)
        else:
            # SUMIFS/AVERAGEIFS take the value range first, then the criteria pairs.
            pairs = list(zip(args[1::2], args[2::2]))
            value_range = args[0] if isinstance(args[0], list) else [args[0]]
            if not pairs:
                raise Unsupported("%s without criteria" % mode)
        size = len(value_range)
        for test_range, _ in pairs:
            if not isinstance(test_range, list) or len(test_range) != size:
                raise FormulaError("#VALUE!")
        keep = []
        for i in range(size):
            if all(criteria_test(test_range[i], criterion) for test_range, criterion in pairs):
                keep.append(value_range[i])
        if mode == "count":
            return float(len(keep))
        nums = [to_number(v) for v in keep if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if mode == "sum":
            return math.fsum(nums)
        if mode == "max":
            return max(nums) if nums else 0.0
        if mode == "min":
            return min(nums) if nums else 0.0
        if not nums:
            raise FormulaError("#DIV/0!")
        return math.fsum(nums) / len(nums)


# ---------------------------------------------------------------------------
# Static heuristics
# ---------------------------------------------------------------------------

def static_findings(wb, report, sheets):
    """Cheap structural checks that need no evaluation."""
    findings = []

    def add(code, severity, sheet, ref, detail, hint):
        findings.append({"code": code, "severity": severity, "sheet": sheet,
                         "ref": ref, "detail": detail, "hint": hint})

    for sheet_name, cells in sheets.items():
        for (col, row), cell in cells.items():
            formula = cell["formula"]
            value = cell["value"]
            # 1. Text stored where a number is required.
            if isinstance(value, str) and value not in xlsxlib.ERROR_LITERALS:
                stripped = value.strip()
                looks_numeric = bool(stripped) and re.match(r"^-?[\d,]+(\.\d+)?%?$", stripped)
                if looks_numeric and cell["kind"] in ("general", "number", "currency", "percent"):
                    add("TEXT_NUMBER", "medium", sheet_name, cell["ref"],
                        "숫자처럼 보이는 텍스트가 숫자 서식 칸에 있다: %r" % value,
                        "값을 숫자로 바꾸거나 TEXT 서식을 '%s'로 명시한다" % "@")
            # 1b. Percent semantics: a literal such as 15 meant as 15%.
            #    Checked before the formula guard: the usual mistake is a typed
            #    constant, and a formula cell's cached value is not the input.
            if not formula and cell["kind"] == "percent":
                if isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value) > 1:
                    add("PERCENT_AS_WHOLE", "high", sheet_name, cell["ref"],
                        "백분율 서식 칸에 %s가 들어 있다(렌더하면 %s)" % (value, "%s%%" % (value * 100)),
                        "분수(0.15)로 저장해야 15%%로 보인다")
            if not formula:
                continue
            funcs = xlsxlib.formula_functions(formula)
            # 2. Hardcoded constant inside an arithmetic formula.
            body = re.sub(r'"[^"]*"', '""', formula)
            body_no_funcs = re.sub(r"(?<![A-Z0-9_.])[A-Z][A-Z0-9_.]{1,40}\s*\(", "(", body)
            constants = [float(x) for x in re.findall(r"(?<![A-Za-z0-9_.$])(\d+(?:\.\d+)?)", body_no_funcs)]
            suspicious = [c for c in constants if c not in (0.0, 1.0, 100.0) and len(re.findall(r"[\d.]+", body_no_funcs)) <= 3]
            if suspicious and any(op in body_no_funcs for op in ("*", "/")):
                add("MAGIC_NUMBER", "medium", sheet_name, cell["ref"],
                    "수식 안에 상수 %s가 박혀 있다: %s" % (", ".join("%g" % c for c in suspicious), formula),
                    "바뀔 수 있는 값은 별도 입력 셀로 옮기고 그 셀을 참조한다")
            # 3. Volatile function.
            for fn in funcs:
                if fn in xlsxlib.VOLATILE_FUNCS:
                    add("VOLATILE_FUNCTION", "low", sheet_name, cell["ref"],
                        "%s는 다시 계산할 때마다 값이 바뀐다: %s" % (fn, formula),
                        "정렬·감사 목적이면 값을 고정하고, 의도한 것이 아니라면 제거한다")
            # 4. A SUM over a contiguous block that stops short of the block.
            for fn in ("SUM", "AVERAGE", "MIN", "MAX", "COUNT"):
                if fn not in funcs:
                    continue
                for rng, sheet_prefix in _sum_ranges(formula):
                    # A qualified range lives on another sheet; scanning the current
                    # sheet would look in the wrong column and miss the gap (or warn
                    # about unrelated data that happens to sit there).
                    target = sheet_name
                    if sheet_prefix:
                        target = sheet_prefix.strip("'").replace("''", "'")
                        if target not in sheets:
                            continue
                    findings.extend(_gap_check(target, cell, fn, rng, sheets[target]))
            # 5. Division with a denominator that is a plain cell reference and can be zero.
            if re.search(r"/\s*\$?[A-Z]{1,3}\$?\d+", body_no_funcs) and "IFERROR" not in funcs and "IF" not in funcs:
                add("UNGUARDED_DIVISION", "low", sheet_name, cell["ref"],
                    "0이 될 수 있는 셀로 나누면서 보호가 없다: %s" % formula,
                    "IFERROR(...,\"\") 또는 IF(분모=0,0,...)로 감싼다")
            # 6. Formula that points at its own cell.
            #    A reference qualified by a sheet (`Other!A2`) is a different cell,
            #    so `!` must be excluded alongside identifier characters.
            ref = cell["ref"]
            self_ref_re = r"(?<![A-Z0-9_$!])%s(?![0-9])" % re.escape(ref.replace("$", ""))
            if re.search(self_ref_re, formula):
                add("SELF_REFERENCE", "high", sheet_name, ref,
                    "수식이 자기 셀을 참조한다: %s" % formula, "순환 참조이므로 참조 범위를 다시 잡는다")
            # 7. Unsupported-or-newer function that a recalc runtime may not know.
            for fn in funcs:
                if fn in xlsxlib.UNSUPPORTED_KNOWN_HINT:
                    add("NEWER_FUNCTION", "medium", sheet_name, ref,
                        "%s는 최신 Excel 전용이다: %s" % (fn, formula),
                        "LibreOffice 등 재계산 환경에서는 INDEX/MATCH로 바꾸거나 값을 미리 계산한다")
    return findings


FALLBACK_HINT = ("XLOOKUP", "XMATCH", "FILTER", "SORT", "UNIQUE", "SEQUENCE", "LET", "LAMBDA")


GAP_LOOKAHEAD = 100


def _sum_ranges(formula):
    """Yield (bounds, sheet prefix) for every A1:B2 range in a formula.

    The prefix is what tells a cross-sheet total where to look; the bare regex
    silently treated `SUM(Data!B2:B3)` as a gap check on the formula's own sheet.
    """
    pattern = re.compile(
        r"(?:(?:'((?:[^']|'')+)'|([A-Za-z_\\][\w.]*))!)?"
        r"\$?([A-Z]{1,3})\$?(\d+):\$?([A-Z]{1,3})\$?(\d+)")
    for m in pattern.finditer(formula):
        quoted, bare, col1, row1, col2, row2 = m.groups()
        yield ((col1, row1, col2, row2), quoted or bare)


def _gap_check(sheet_name, cell, fn, rng, cells):
    c1, r1, c2, r2 = (xlsxlib.col_index(rng[0]), int(rng[1]), xlsxlib.col_index(rng[2]), int(rng[3]))
    if c1 != c2:
        return []
    # A total that includes its own cell is circular; Excel flags it and other
    # readers see a stale or zero value instead of an error.
    if cell["col"] == c1 and r1 <= cell["row"] <= r2:
        return [{
            "code": "RANGE_GAP", "severity": "high", "sheet": sheet_name, "ref": cell["ref"],
            "detail": "%s 범위 %s%s:%s%s 안에 합계 셀 자신이 들어 있다" % ((fn,) + rng),
            "hint": "합계 셀을 범위 밖으로 옮기거나 범위를 데이터 끝에서 멈춘다",
        }]
    # Skip blanks outwards: data continuing past a blank row is still the same
    # column of numbers, so the range is short. A text cell ends the search because
    # the next block is a different table.
    for start, step, where in ((r2 + 1, 1, "아래"), (r1 - 1, -1, "위")):
        for offset in range(GAP_LOOKAHEAD):
            probe = start + step * offset
            if probe < 1:
                break
            neighbour = cells.get((c1, probe))
            if neighbour is None:
                continue
            if neighbour["formula"]:
                funcs = xlsxlib.formula_functions(neighbour["formula"])
                if any(f in funcs for f in ("SUM", "AVERAGE", "MIN", "MAX", "COUNT")):
                    break
            value = neighbour["value"]
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                edge = r2 if step > 0 else r1
                return [{
                    "code": "RANGE_GAP", "severity": "high", "sheet": sheet_name, "ref": cell["ref"],
                    "detail": "%s 범위가 %s행에서 끝나는데 %s쪽에 숫자 셀이 더 있다(=%s)" % (fn, edge, where, value),
                    "hint": "합계 범위가 한 행 모자라지 않은지 확인하고, 의도한 것이면 범위에 맞춰 상수를 고정한다",
                }]
            if isinstance(value, str) and value.strip():
                break
    return []


xlsxlib.UNSUPPORTED_KNOWN_HINT = FALLBACK_HINT


def compare(cached, computed):
    if isinstance(cached, str) and cached in xlsxlib.ERROR_LITERALS:
        return None
    if cached is None and computed is None:
        return 0.0
    if isinstance(computed, bool) or isinstance(cached, bool):
        return 0.0 if bool(cached) == bool(computed) else None
    if isinstance(computed, (int, float)) and isinstance(cached, (int, float)):
        if math.isclose(float(cached), float(computed), rel_tol=1e-9, abs_tol=1e-9):
            return 0.0
        return float(computed) - float(cached)
    if to_text(cached).strip() == to_text(computed).strip():
        return 0.0
    return None


def verify(path, sheet_filter=None, max_cells=2_000_000, static_only=False):
    wb = xlsxlib.Workbook(path)
    report = {"schemaVersion": 1, "path": path}
    with open(path, "rb") as fh:
        report["sha256"] = xlsxlib.digest(fh.read())
    sheets = {}
    truncated = []
    for name, part, state in wb.sheets:
        if state == "chartsheet" or not part:
            continue
        if sheet_filter and name != sheet_filter:
            continue
        cells = {}
        cut = False
        for row_no, row in wb.iter_rows(part):
            if cut:
                break
            for cell in row:
                if len(cells) >= max_cells:
                    cut = True
                    break
                cells[(cell["col"], cell["row"])] = cell
        if cut:
            truncated.append(name)
        sheets[name] = cells
    findings = static_findings(wb, report, sheets)
    mismatches, unevaluated, error_cells, uncached = [], [], [], []
    totals = {"formulas": 0, "evaluated": 0, "mismatched": 0, "unevaluated": 0,
              "uncached": 0, "cycles": 0, "errors": 0, "errorLiterals": 0,
              "staticFindings": len(findings)}
    for sheet_name, cells in sheets.items():
        for (col, row), cell in cells.items():
            value = cell["value"]
            if isinstance(value, str) and value in xlsxlib.ERROR_LITERALS:
                totals["errorLiterals"] += 1
                if cell["formula"]:
                    error_cells.append({"sheet": sheet_name, "ref": cell["ref"],
                                        "formula": cell["formula"], "error": value})
        if static_only:
            continue
        evaluator = Evaluator(wb)
        for (col, row), cell in cells.items():
            if not cell["formula"]:
                continue
            totals["formulas"] += 1
            try:
                computed = evaluator.cell_value(sheet_name, col, row)
            except Cycle:
                totals["cycles"] += 1
                unevaluated.append({"sheet": sheet_name, "ref": cell["ref"],
                                    "formula": cell["formula"], "reason": "cycle"})
                continue
            except Unsupported as exc:
                totals["unevaluated"] += 1
                unevaluated.append({"sheet": sheet_name, "ref": cell["ref"],
                                    "formula": cell["formula"], "reason": str(exc)})
                continue
            except FormulaError as exc:
                totals["errors"] += 1
                error_cells.append({"sheet": sheet_name, "ref": cell["ref"],
                                    "formula": cell["formula"], "error": exc.code})
                continue
            except RecursionError:
                totals["unevaluated"] += 1
                unevaluated.append({"sheet": sheet_name, "ref": cell["ref"],
                                    "formula": cell["formula"], "reason": "recursion"})
                continue
            except Exception as exc:  # one bad cell must not erase the whole report
                # An out-of-range DATE, a huge power, a bad CHOOSE index: the evaluator
                # raises a plain Python error rather than FormulaError. Report that cell
                # as unverified and keep going, so a single formula cannot turn the run
                # into rc=2 with no per-cell detail at all.
                totals["unevaluated"] += 1
                unevaluated.append({"sheet": sheet_name, "ref": cell["ref"],
                                    "formula": cell["formula"],
                                    "reason": "%s: %s" % (exc.__class__.__name__, exc)})
                continue
            totals["evaluated"] += 1
            if cell["value"] is None:
                # An empty cache is not a disagreement: the file simply never stored a
                # result. Count it separately so "needs recalc" cannot hide a real
                # stale value, and so a clean source workbook does not look broken.
                totals["uncached"] += 1
                uncached.append({"sheet": sheet_name, "ref": cell["ref"],
                                 "formula": cell["formula"], "computed": computed})
                continue
            delta = compare(cell["value"], computed)
            if delta is None:
                totals["mismatched"] += 1
                mismatches.append({"sheet": sheet_name, "ref": cell["ref"],
                                   "formula": cell["formula"], "cached": cell["value"],
                                   "computed": computed, "delta": None})
            elif abs(delta) > 0:
                totals["mismatched"] += 1
                mismatches.append({"sheet": sheet_name, "ref": cell["ref"],
                                   "formula": cell["formula"], "cached": cell["value"],
                                   "computed": computed, "delta": delta})
    checks = [
        {"name": "no_cached_mismatch", "status": "pass" if totals["mismatched"] == 0 else "fail",
         "detail": "%d formula(s) recomputed, %d disagree with the cached value" % (totals["evaluated"], totals["mismatched"])},
        {"name": "cache_complete", "status": "pass" if totals["uncached"] == 0 else "partial",
         "detail": "%d formula(s) hold no cached value; readers that do not calculate see an empty cell. Run recalc_cached.py to store results." % totals["uncached"]},
        {"name": "no_error_literal", "status": "pass" if totals["errorLiterals"] == 0 and totals["errors"] == 0 else "fail",
         "detail": "%d error literal(s), %d formula(s) raise an error when recomputed" % (totals["errorLiterals"], totals["errors"])},
        {"name": "evaluation_complete", "status": "pass" if totals["unevaluated"] == 0 else "partial",
         "detail": "%d formula(s) use a function this evaluator does not implement; they are unverified, not correct" % totals["unevaluated"]},
        {"name": "no_cycle", "status": "pass" if totals["cycles"] == 0 else "fail",
         "detail": "%d cycle(s)" % totals["cycles"]},
        {"name": "cells_complete", "status": "pass" if not truncated else "partial",
         "detail": ("all cells read" if not truncated else
                    "stopped at --max-cells %d; %s is incomplete, so every count below covers only the cells read"
                    % (max_cells, ", ".join(truncated)))},
    ]
    report.update({"totals": totals, "mismatches": mismatches, "unevaluated": unevaluated,
                   "uncached": uncached, "errorCells": error_cells, "findings": findings,
                   "truncatedSheets": truncated, "maxCells": max_cells,
                   "checks": checks,
                   "evaluator": {"supportedFunctions": len(SUPPORTED), "mode": "stdlib"}})
    return report


def self_test():
    """Build a real workbook on disk, verify it, then check the reported facts."""
    import tempfile
    import zipfile
    from xml.sax.saxutils import escape

    def build(dirpath):
        target = os.path.join(dirpath, "verify.xlsx")
        rows = [
            ("A1", "inlineStr", None, "매출"),
            ("B1", "inlineStr", None, "금액"),
            ("A2", "inlineStr", None, "1월"),
            ("B2", "n", None, "100"),
            ("A3", "inlineStr", None, "2월"),
            ("B3", "n", None, "200"),
            ("B4", "n", "SUM(B2:B3)", "300"),
            ("B5", "n", "B4/0", "#DIV/0!"),
            ("B6", "n", 'IFERROR(B4/0,"safe")', "safe"),
            ("B7", "n", "ROUND(10/3,2)", "3.33"),
            ("B8", "n", "SUM(B2:B3)", "999"),
        ]
        cells = []
        for ref, ctype, formula, value in rows:
            attrs = ' r="%s"' % ref
            if ctype != "n":
                attrs += ' t="%s"' % ctype
            body = ""
            if ctype == "inlineStr":
                body = "<is><t>%s</t></is>" % escape(value)
            else:
                if formula:
                    body += "<f>%s</f>" % escape(formula)
                if value is not None:
                    if ctype == "n" and value in xlsxlib.ERROR_LITERALS:
                        attrs += ' t="e"'
                    body += "<v>%s</v>" % escape(value)
            cells.append("<c%s>%s</c>" % (attrs, body))
        sheet = ('<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="%s"><dimension ref="A1:B8"/>'
                 '<sheetData><row r="1">%s%s</row><row r="2">%s%s</row><row r="3">%s%s</row>'
                 '<row r="4">%s</row><row r="5">%s</row><row r="6">%s</row><row r="7">%s</row>'
                 '<row r="8">%s</row></sheetData></worksheet>'
                 % (xlsxlib.NS["m"], cells[0], cells[1], cells[2], cells[3], cells[4], cells[5],
                    cells[6], cells[7], cells[8], cells[9], cells[10]))
        wbxml = ('<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="%s" xmlns:r="%s">'
                 '<sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>'
                 % (xlsxlib.NS["m"], xlsxlib.NS["r"], escape("검증")))
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

    def build_rows(target_path, rows_spec):
        """Write a one-sheet workbook of uncached formula cells, ref order preserved."""
        cells = []
        for ref, formula, value in rows_spec:
            body = "<f>%s</f>" % escape(formula)
            if value is not None:
                body += "<v>%s</v>" % escape(value)
            cells.append('<c r="%s">%s</c>' % (ref, body))
        sheet = ('<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="%s"><sheetData>'
                 '<row r="1">%s</row></sheetData></worksheet>' % (xlsxlib.NS["m"], "".join(cells)))
        wbxml = ('<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="%s" xmlns:r="%s">'
                 '<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>'
                 % (xlsxlib.NS["m"], xlsxlib.NS["r"]))
        rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="%s">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '</Relationships>' % xlsxlib.NS["pr"])
        root_rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="%s">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                     '</Relationships>' % xlsxlib.NS["pr"])
        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
            zf.writestr("_rels/.rels", root_rels)
            zf.writestr("xl/workbook.xml", wbxml)
            zf.writestr("xl/_rels/workbook.xml.rels", rels)
            zf.writestr("xl/worksheets/sheet1.xml", sheet)
        return target_path

    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        path = build(tmp)
        report = verify(path)
        totals = report["totals"]
        mismatched = {m["ref"]: m for m in report["mismatches"]}
        checks.append(("formulas counted", totals["formulas"] == 5))
        checks.append(("B4 verified", "B4" not in mismatched and totals["evaluated"] >= 3))
        checks.append(("stale cache caught", "B8" in mismatched and mismatched["B8"]["computed"] == 300))
        checks.append(("div/0 guarded", "B6" not in mismatched))
        checks.append(("round", "B7" not in mismatched))
        checks.append(("error literal", any(e["ref"] == "B5" for e in report["errorCells"])))
        checks.append(("fail status", any(c["name"] == "no_cached_mismatch" and c["status"] == "fail" for c in report["checks"])))
    ev = Evaluator(type("W", (), {"sheets": [], "defined_names": []})())
    unit = [
        ("=1+2*3", 7.0),
        ("=ROUND(10/3,2)", 3.33),
        ('=IF(1>5,"big","small")', "small"),
        ('=IFERROR(1/0,"safe")', "safe"),
        ('=TEXT(0.155,"0.0%")', "15.5%"),
        ('=CONCATENATE("합","계")', "합계"),
        ('=COUNTIF(A1:A2,">15")', 0.0),
    ]
    for src, expected in unit:
        try:
            got = ev.evaluate(src, "S")
        except FormulaError:
            got = "error"
        checks.append((src, got == expected))
    try:
        ev.evaluate("=XLOOKUP(1,A1:A2,A1:A2)", "S")
        checks.append(("unsupported raises", False))
    except Unsupported:
        checks.append(("unsupported raises", True))

    # Percent-as-whole must fire on a constant cell with no formula, which is the
    # shape of the real mistake (a typed 15 under a percent format).
    fake = {"sheet": "P", "col": 2, "row": 2, "type": "n", "formula": None,
            "value": 15, "style": 1, "kind": "percent", "ref": "B2"}
    ok_pct = dict(fake, value=0.15, ref="B3")
    big_pct = dict(fake, value=150, ref="B4")
    pct_formula = dict(fake, value=15, formula="B2*1", ref="B5")
    pct_findings = static_findings(
        type("W", (), {})(),
        {},
        {"P": {(2, 2): fake, (2, 3): ok_pct, (2, 4): big_pct, (2, 5): pct_formula}},
    )
    flagged = {f["ref"] for f in pct_findings if f["code"] == "PERCENT_AS_WHOLE"}
    checks.append(("percent-as-whole fires", "B2" in flagged and "B4" in flagged))
    checks.append(("fraction percent clean", "B3" not in flagged))
    checks.append(("formula percent skipped", "B5" not in flagged))

    # A 1904 workbook measures serials from 1904-01-01; ignoring the flag makes
    # every YEAR/MONTH/DAY result four years and one day off.
    epoch_1900 = Evaluator(type("W", (), {"sheets": [], "defined_names": [], "date1904": False})())
    epoch_1904 = Evaluator(type("W", (), {"sheets": [], "defined_names": [], "date1904": True})())
    serial_1904 = float((date(2026, 1, 31) - date(1904, 1, 1)).days)
    checks.append(("1900 epoch", epoch_1900.epoch == date(1899, 12, 30)))
    checks.append(("1904 epoch", epoch_1904.epoch == date(1904, 1, 1)))
    checks.append(("1904 YEAR", epoch_1904.evaluate("=YEAR(%d)" % serial_1904, "S") == 2026.0))
    checks.append(("1904 MONTH", epoch_1904.evaluate("=MONTH(%d)" % serial_1904, "S") == 1.0))
    checks.append(("1904 DAY", epoch_1904.evaluate("=DAY(%d)" % serial_1904, "S") == 31.0))
    checks.append(("1904 round trip", epoch_1904.evaluate(
        "=DATE(2026,1,31)", "S") == serial_1904))

    # Excel stores post-2007 functions under a compatibility prefix, so detection
    # has to see through `_xlfn.` or it never fires on real Excel output.
    checks.append(("_xlfn stripped", xlsxlib.formula_functions("=_xlfn.XLOOKUP(A1,B1,C1)") == ["XLOOKUP"]))
    checks.append(("_xlfn._xlws stripped",
                   xlsxlib.formula_functions("=_xlfn._xlws.FILTER(A1:A3,B1:B3)") == ["FILTER"]))
    xlfn_sheet = {"X": {(2, 2): {"ref": "B2", "col": 2, "row": 2, "formula": "=_xlfn.XLOOKUP(A1,A1:A2,A1:A2)",
                                 "value": None, "style": 0, "kind": "general"}}}
    xlfn_codes = {f["code"] for f in static_findings(type("W", (), {})(), {}, xlfn_sheet)}
    checks.append(("_xlfn NEWER_FUNCTION", "NEWER_FUNCTION" in xlfn_codes))
    # A reference qualified by another sheet is not a self reference.
    cross = {"X": {(2, 2): {"ref": "A2", "col": 1, "row": 2, "formula": "=Other!A2+1",
                            "value": None, "style": 0, "kind": "general"}}}
    cross_codes = {f["code"] for f in static_findings(type("W", (), {})(), {}, cross)}
    checks.append(("cross-sheet not self", "SELF_REFERENCE" not in cross_codes))
    real_self = {"X": {(2, 2): {"ref": "A2", "col": 1, "row": 2, "formula": "=A2+1",
                                "value": None, "style": 0, "kind": "general"}}}
    checks.append(("real self ref", "SELF_REFERENCE" in {f["code"] for f in
                                                        static_findings(type("W", (), {})(), {}, real_self)}))

    # All three documented RANGE_GAP conditions must fire, and a clean total must not.
    def gap_sheet(cells_spec, formula_cell):
        grid = {}
        for (c, r), val in cells_spec.items():
            grid[(c, r)] = {"ref": "%s%d" % (chr(64 + c), r), "col": c, "row": r,
                            "formula": val if isinstance(val, str) and val.startswith("=") else None,
                            "value": None if isinstance(val, str) and val.startswith("=") else val,
                            "style": 0, "kind": "general"}
        return {"S": grid}
    gap_blank = gap_sheet({(2, 2): 10, (2, 3): 20, (2, 5): 40,
                           (2, 7): "=SUM(B2:B3)"}, (2, 7))
    checks.append(("gap past blank row",
                   any(f["code"] == "RANGE_GAP" for f in static_findings(type("W", (), {})(), {}, gap_blank))))
    gap_self = gap_sheet({(2, 2): 10, (2, 3): 20, (2, 4): "=SUM(B2:B4)"}, (2, 4))
    checks.append(("gap total inside range",
                   any(f["code"] == "RANGE_GAP" for f in static_findings(type("W", (), {})(), {}, gap_self))))
    gap_clean = gap_sheet({(1, 1): "a", (2, 1): "v", (2, 2): 10, (2, 3): 20, (2, 4): 30,
                           (2, 5): "=SUM(B2:B4)"}, (2, 5))
    checks.append(("gap clean sheet silent",
                   not any(f["code"] == "RANGE_GAP" for f in static_findings(type("W", (), {})(), {}, gap_clean))))
    # --- evaluator robustness and Excel-accurate semantics ---
    # Column A holds text and column B numbers on rows 2-4, so A2:B4 is a 3x2 range.
    with tempfile.TemporaryDirectory() as shape_tmp:
        shape_path = build(shape_tmp)
        ev = Evaluator(xlsxlib.Workbook(shape_path))
    # A range keeps its 2-D shape: a flat list made ROWS answer the cell count.
    checks.append(("ROWS keeps shape", ev.evaluate("=ROWS(A2:B4)", "검증") == 3.0))
    checks.append(("COLUMNS keeps shape", ev.evaluate("=COLUMNS(A2:B4)", "검증") == 2.0))
    checks.append(("INDEX row,col offset", ev.evaluate("=INDEX(A2:B4,2,2)", "검증") == 200.0))
    # IS* must inspect an error instead of propagating it.
    checks.append(("ISERROR catches error", ev.evaluate("=IF(ISERROR(1/0),0,1)", "S") == 0.0))
    checks.append(("ISERR skips N/A", ev.evaluate("=ISERR(NA())", "S") is False))
    checks.append(("ISNA catches N/A", ev.evaluate("=ISNA(NA())", "S") is True))
    # A failed lookup is #N/A, so the IFNA/ISNA wrappers written around it work.
    try:
        ev.evaluate('=MATCH("없음",A2:A4,0)', "검증")
        checks.append(("MATCH miss is #N/A", False))
    except FormulaError as exc:
        checks.append(("MATCH miss is #N/A", exc.code == "#N/A"))
    checks.append(("ISNA over MATCH miss",
                   ev.evaluate('=ISNA(MATCH("없음",A2:A4,0))', "검증") is True))
    # VLOOKUP/HLOOKUP need the 2-D shape to pick the right column.
    checks.append(("VLOOKUP exact", ev.evaluate('=VLOOKUP("2월",A2:B4,2,0)', "검증") == 200.0))
    checks.append(("VLOOKUP approximate", ev.evaluate("=VLOOKUP(150,B2:B4,1)", "검증") == 100.0))
    checks.append(("HLOOKUP exact", ev.evaluate('=HLOOKUP("매출",A1:B2,2,0)', "검증") == "1월"))
    # A negative base with a fractional exponent is #NUM! in Excel, never a complex
    # number; the complex value used to reach json.dumps and abort the whole report.
    for label, formula in (("POWER negative base", "=POWER(-8,1/3)"),
                           ("^ overflow", "=10^400")):
        try:
            ev.evaluate(formula, "S")
            checks.append((label, False))
        except FormulaError as exc:
            checks.append((label, exc.code == "#NUM!"))
    # One bad cell must be reported, not abort every other cell: a DATE out of range
    # or a bad CHOOSE index used to escape as a Python error and kill the whole run.
    with tempfile.TemporaryDirectory() as tmp2:
        bad_path = os.path.join(tmp2, "bad.xlsx")
        build_rows(bad_path, [("A1", "DATE(2026,13,1)", None),
                              ("A2", "CHOOSE()", None),
                              ("A3", "1+1", None),
                              ("A4", "POWER(-8,1/3)", None)])
        bad_report = verify(bad_path, static_only=False)
        checks.append(("bad cell isolated", bad_report["totals"]["evaluated"] == 1))
        checks.append(("bad cells reported", len(bad_report["unevaluated"]) == 2))
        checks.append(("bad cells are errors",
                       bad_report["totals"]["errors"] == 1 and bad_report["totals"]["unevaluated"] == 2))
    failed = [name for name, ok in checks if not ok]
    print(json.dumps({"ok": not failed, "checks": len(checks), "failed": failed}, ensure_ascii=False))
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("workbook", nargs="?")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sheet")
    parser.add_argument("--max-cells", type=int, default=2_000_000)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.workbook or not os.path.isfile(args.workbook):
        parser.print_usage(sys.stderr)
        return 2
    try:
        report = verify(args.workbook, args.sheet, args.max_cells, args.static_only)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": "E_PARSE", "detail": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    failed = any(c["status"] == "fail" for c in report["checks"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

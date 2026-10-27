"""Expression boundaries and operator roles over provenance-bearing text tokens.

Pratt parsing groups operands, units, unary signs, binary operations and
parentheses. It never evaluates document code or permits mathematical edits.
"""
import json
import unicodedata

OPEN = {"(": ")", "[": "]", "{": "}", "（": "）", "［": "］", "｛": "｝"}
# Closed-class prose boundaries, not mathematical function-name exceptions.
PROSE_BOUNDARIES = frozenset("is are was were be been being at to from of with and or as than rather between by into for in on equals".split())
UNSIGNED_DECIMAL = r"(?:\d+(?:[.,]\d+)*|\.\d+)(?:[eE][+-]?\d+)?"
OPERATOR_START = frozenset("+-*/^=<>!([{−×÷")


def operator_after(text, token):
    cursor = token["end"]
    while cursor < len(text) and text[cursor].isspace():cursor += 1
    return cursor if cursor < len(text) and unicodedata.normalize("NFKC", text[cursor]) in OPERATOR_START else None


def prose_boundary(text, token, confirmed_boundaries=()):
    """Grammar/whitespace never proves an operator-adjacent word is prose.

    Only independently confirmed source-bound spans can resolve that role.
    The small word class still separates ordinary non-operator prose.
    """
    if (token["start"],token["end"]) in confirmed_boundaries:return True
    return token["text"].lower() in PROSE_BOUNDARIES and operator_after(text,token) is None
PRECEDENCE = {"=": 5, "<": 5, ">": 5, "<=": 5, ">=": 5, "!=": 5,
    "+": 10, "-": 10, "*": 20, "/": 20, "^": 30, "**": 30}
ALIASES = {"−": "-", "×": "*", "÷": "/"}


def protect_expressions(text, tokens, confirmed_boundaries=()):
    items = [token for token in tokens if token["kind"] != "space"]
    def symbol(index):
        value = unicodedata.normalize("NFKC", items[index]["text"]) if index < len(items) else ""
        return ALIASES.get(value, value)
    def boundary(token):
        return prose_boundary(text, token, confirmed_boundaries)
    def node(kind, begin, end, **fields):
        return {"kind": kind, "begin": begin, "end": end, **fields}
    def operator(index):
        value = symbol(index)
        if index + 1 < len(items) and items[index]["end"] == items[index+1]["start"]:
            pair = value + symbol(index + 1)
            if pair in PRECEDENCE:return pair, 2
        return (value, 1) if value in PRECEDENCE else (None, 0)
    def quantity(value):
        end = value["end"]
        if end < len(items) and items[end]["kind"] in {"word", "symbolic_identifier"} and not boundary(items[end]):
            unit = items[end]
            latin = all("LATIN" in unicodedata.name(char, "") for char in unit["text"])
            adjacent = items[end-1]["end"] == unit["start"]
            return node("implicit_product" if latin and adjacent else "quantity", value["begin"], end+1,
                value=value, unit=unit["text"])
        return value
    def atom(index, depth):
        if index >= len(items) or depth > 64:return None
        token = items[index];value = symbol(index)
        if value in {"+", "-"}:
            inner = expression(index+1, PRECEDENCE["^"], depth+1)
            return node("unary", index, inner["end"], operator=value, operand=inner) if inner else None
        if token["kind"] == "decimal":
            return quantity(node("number", index, index+1, value=token["identity"]))
        if token["text"] in OPEN:
            inner = expression(index+1, 0, depth+1)
            if inner and inner["end"] < len(items) and items[inner["end"]]["text"] == OPEN[token["text"]]:
                return quantity(node("group", index, inner["end"]+1, operand=inner))
            return None
        if token["kind"] in {"word", "symbolic_identifier", "structured_identifier", "call_or_subscript_object"}:
            if boundary(token):return None
            if token["kind"] == "word" and not all("LATIN" in unicodedata.name(c, "") for c in token["text"]):return None
            return node("identifier", index, index+1, value=token["identity"])
        return None
    def expression(index, minimum=0, depth=0):
        left = atom(index, depth+1)
        if left is None:return None
        while left["end"] < len(items):
            op, width = operator(left["end"])
            precedence = PRECEDENCE.get(op)
            separator = None
            if op is None and numerical(left):
                cursor = left["end"];token = items[cursor]
                if numeric_start(cursor):
                    op, width, precedence = "implicit_adjacency", 0, 25
                elif (len(token["text"]) == 1 and unicodedata.category(token["text"]).startswith("P") and numeric_start(cursor+1)):
                    op, width, precedence, separator = "numeric_separator", 1, 8, token["text"]
            if op is None or precedence < minimum:break
            right = expression(left["end"]+width, precedence+(0 if op in {"^", "**"} else 1), depth+1)
            if right is None:break
            left = node("binary", left["begin"], right["end"], operator=op, left=left, right=right)
            if separator is not None:left["separator"] = separator
        return left
    def numeric_start(index):
        return index < len(items) and (items[index]["kind"] == "decimal" or items[index]["text"] in OPEN or symbol(index) in {"+", "-"})
    def numerical(value):
        return value["kind"] == "number" or any(numerical(item) for item in value.values() if isinstance(item, dict))
    def literal(value, signed=False):
        kind = value["kind"]
        if kind == "number":return value["value"], value["end"]
        if kind == "quantity":return literal(value["value"], signed)
        if kind == "group":
            inner = literal(value["operand"], signed)
            return (inner[0], value["end"]) if inner else None
        if kind == "unary" and not signed:
            inner = literal(value["operand"], True)
            return (value["operator"]+inner[0], inner[1]) if inner else None
        return None
    def mathematical(value):
        return value["kind"] in {"binary", "implicit_product"} or value["kind"] in {"unary", "group"} and literal(value) is None
    def identity(value):
        return {key: identity(item) if isinstance(item, dict) else item for key, item in value.items() if key not in {"begin", "end"}}
    output = [];index = 0;cursor = 0
    while index < len(items):
        token = items[index];parsed = expression(index)
        result = token;following = index+1
        if parsed and mathematical(parsed):
            tree = identity(parsed);following = parsed["end"]
            end = items[following-1]["end"]
            result = {"kind": "arithmetic_expression", "text": text[token["start"]:end], "start": token["start"], "end": end,
                "identity": json.dumps(tree, ensure_ascii=False, sort_keys=True, separators=(",", ":")), "expression_tree": tree}
        elif parsed:
            value = literal(parsed)
            if value:
                number, following = value;end = items[following-1]["end"]
                result = {"kind": "decimal", "text": text[token["start"]:end], "start": token["start"], "end": end,
                    "identity": number, "literal_role": "standalone_quantity", "expression_tree": identity(parsed)}
        if cursor < result["start"]:
            gap = text[cursor:result["start"]]
            output.append({"kind": "space", "text": gap, "start": cursor, "end": result["start"], "identity": gap})
        output.append(result);cursor = result["end"];index = following
    if cursor < len(text):
        output.append({"kind": "space", "text": text[cursor:], "start": cursor, "end": len(text), "identity": text[cursor:]})
    return output

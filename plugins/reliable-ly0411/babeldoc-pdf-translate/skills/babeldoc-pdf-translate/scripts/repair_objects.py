"""Fail closed on mathematical/unknown glyphs in automatic plain-prose islands.

This is a narrow eligibility proof, not a universal math extractor. Mixed math,
unknown fonts and ambiguous short Latin variables require engine/manual work.
"""
import hashlib
import json
import re
import unicodedata
import difflib
from expression_syntax import OPEN, UNSIGNED_DECIMAL, operator_after, prose_boundary, protect_expressions

import pymupdf as fitz

VERSION = "1.0.0-draft.5"
KNOWN_PROSE_FONTS = re.compile(r"^(?:Helvetica(?:-Bold|-Oblique|-BoldOblique)?|Arial(?:MT|-BoldMT|-ItalicMT)?|"
    r"Times-Roman|Times-Bold|Times-Italic|Times-BoldItalic|TimesNewRomanPSMT|"
    r"CharisSIL(?:-Regular|-Bold|-Italic|-BoldItalic)?|NimbusSans-(?:Regular|Bold|Italic|BoldItalic)|DroidSansFallback|Droid Sans Fallback Regular|Heiti|STSong|"
    r"Noto(?:Sans|Serif)CJK\w*(?:-\w+)?)$", re.I)


DECIMAL = re.compile(UNSIGNED_DECIMAL)
PROSE_PUNCTUATION = frozenset(".,;:!?，。；：！？'’‘“”\"—–")


def text_contract(text, *, confirmed_boundaries=()):
    """Lex typed words/decimal literals/prose punctuation and opaque objects.

    No function names or fraction characters are enumerated. Calls/subscripts
    are recognized by balanced syntax, nondecimal numerals by Unicode numeric
    properties. A plain-edit contract cannot rewrite an opaque object.
    """
    tokens = [];unresolved = []
    def add(kind, start, end):
        raw = text[start:end]
        identity = "".join(str(unicodedata.decimal(char)) if char.isdecimal() else char.lower()
            for char in raw) if kind == "decimal" else raw
        tokens.append({"kind": kind, "text": raw, "start": start, "end": end, "identity": identity})
    at = 0
    while at < len(text):
        start = at; char = text[at]; category = unicodedata.category(char)
        if char.isspace():
            while at < len(text) and text[at].isspace():at += 1
            add("space", start, at);continue
        numeric = DECIMAL.match(text, at)
        if numeric:
            at = numeric.end()
            kind = "styled_numeric_object" if any(unicodedata.decomposition(item).startswith("<font>") for item in text[start:at]) else "decimal"
            add(kind, start, at);continue
        if category in {"No", "Nl"}:
            at += 1
            while at < len(text) and unicodedata.category(text[at]) in {"No", "Nl"}:at += 1
            add("nondecimal_numeric_object", start, at);continue
        if char.isalpha() and category != "Lm":
            at += 1
            while at < len(text) and text[at].isalpha() and unicodedata.category(text[at]) != "Lm":at += 1
            word_end = at
            latin_word = all("LATIN" in unicodedata.name(c, "") for c in text[start:word_end])
            structured = False
            if latin_word and at < len(text) and (text[at].isdecimal() or text[at] == "_"):
                while at < len(text) and (text[at].isalnum() or text[at] == "_"):at += 1
                structured = True
            following = at
            while following < len(text) and text[following].isspace():following += 1
            word_token = {"text":text[start:at], "start":start, "end":at}
            operator_start = operator_after(text,word_token)
            if latin_word and operator_start is not None and (start,at) not in confirmed_boundaries:
                unresolved.append({"boundary_text":text[start:at],"boundary_span":[start,at],"operator_start":operator_start,
                    "disposition":"requires_retranslation_or_manual"})
            prose_quantity_prefix = not latin_word or prose_boundary(text, word_token, confirmed_boundaries)
            if following < len(text) and text[following] in OPEN and not prose_quantity_prefix:
                stack = [];at = following
                while at < len(text):
                    item = text[at]
                    if item in OPEN:stack.append(OPEN[item])
                    elif stack and item == stack[-1]:
                        stack.pop()
                        if not stack:at += 1;break
                    at += 1
                add("call_or_subscript_object", start, at);continue
            if structured:
                add("structured_identifier", start, at);continue
            word = text[start:word_end]
            prose_letters = all("LATIN" in unicodedata.name(c, "") or unicodedata.name(c, "").startswith("CJK UNIFIED") for c in word)
            # A/I and the English article a have grammatical prose uses.
            kind = "word" if prose_letters and (len(word) != 1 or word in {"a", "A", "I"} or ord(word[0]) > 127) else "symbolic_identifier"
            add(kind, start, at);continue
        at += 1
        add("punctuation" if char in PROSE_PUNCTUATION else "opaque_syntax_or_glyph", start, at)
    tokens = protect_expressions(text, tokens, confirmed_boundaries)
    protected = [token for token in tokens if token["kind"] not in {"word", "space", "punctuation"}]
    opaque = [token for token in protected if token["kind"] != "decimal"]
    return {"version": VERSION, "tokens": tokens, "protected_tokens": protected,
        "decimal_identity": [token["identity"] for token in protected if token["kind"] == "decimal"],
        "opaque_identity": [[token["kind"], token["identity"]] for token in opaque],
        "unresolved_operator_roles":unresolved,"plain_editable": not opaque and not unresolved}


def text_risks(text):
    return [] if text_contract(text)["plain_editable"] else ["protected_expression_requires_object_preserving_repair"]


def inspect(page, area, *, allow_repair_background=False, source_quantity_roles=()):
    area = fitz.Rect(area)
    glyphs, texts, reasons = [], [], set()
    for block in page.get_text("rawdict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if not area.intersects(fitz.Rect(span["bbox"])):
                    continue
                chars = span.get("chars", [])
                text = "".join(char["c"] for char in chars)
                texts.append(text)
                font = re.sub(r"^[A-Z]{6}\+", "", span["font"])
                if not KNOWN_PROSE_FONTS.fullmatch(font):
                    reasons.add("unknown_or_math_font")
                if span["flags"] & 1 or tuple(line["dir"]) != (1.0, 0.0):
                    reasons.add("superscript_or_rotated_span")
                for char in chars:
                    if char["c"].strip():
                        glyphs.append({"c": char["c"], "font": span["font"], "size": round(span["size"], 4),
                            "origin": list(char["origin"]), "bbox": list(char["bbox"]), "flags": span["flags"]})
    text = " ".join(texts)
    glyphs_sha = hashlib.sha256(json.dumps(glyphs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    import quantity_roles
    confirmed = quantity_roles.boundaries(page,area,text,glyphs_sha,source_quantity_roles)
    contract = text_contract(text,confirmed_boundaries=confirmed)
    positions = [index for index, char in enumerate(text) if not char.isspace()]
    if len(positions) != len(glyphs):
        reasons.add("unproven_character_to_glyph_mapping")
    else:
        for token in contract["protected_tokens"]:
            token["glyph_evidence"] = [glyphs[number] for number, position in enumerate(positions)
                if token["start"] <= position < token["end"]]
    if not contract['plain_editable']:reasons.add('protected_expression_requires_object_preserving_repair')
    if contract['unresolved_operator_roles']:reasons.add('operator_role_unproven_requires_retranslation_or_manual')
    if not glyphs:
        reasons.add("no_readable_glyph_evidence")
    if any(area.intersects(fitz.Rect(image["bbox"])) for image in page.get_image_info()):
        reasons.add("image_object_in_island")
    for drawing in page.get_drawings():
        rectangle = fitz.Rect(drawing["rect"])
        repair_background = (allow_repair_background and drawing.get("type") in {"f", "fs"}
            and drawing.get("fill") == (1.0, 1.0, 1.0) and drawing.get("fill_opacity") == 1
            and (drawing["type"] == "f" or drawing.get("color") == (1.0, 1.0, 1.0)
                 and drawing.get("stroke_opacity") == 1 and drawing.get("width", 2) <= 1)
            and len(drawing.get("items", [])) == 1 and drawing["items"][0][0] == "re"
            and all(abs(a - b) < .001 for a, b in zip(rectangle, area)))
        if not repair_background and area.intersects(rectangle + (-.5, -.5, .5, .5)):
            reasons.add("drawing_object_in_island")
    return {"passed": not reasons, "reasons": sorted(reasons), "glyphs": glyphs, "text": text, "text_contract": contract,
        "glyphs_sha256": glyphs_sha,"confirmed_quantity_boundaries":[list(span) for span in confirmed]}


def island(source, before, after, area, replacement=None, *, source_quantity_roles=()):
    # The actual redaction background can stroke half a point outside its box.
    # Inspect a 1pt halo on source/before rather than ignoring adjacent objects.
    import quantity_roles
    if source_quantity_roles:quantity_roles.validate_for_source(source.parent.name,source_quantity_roles)
    protected_area = fitz.Rect(area) + (-1, -1, 1, 1)
    evidence = {"source": inspect(source, protected_area,source_quantity_roles=source_quantity_roles),
        "before": inspect(before, protected_area,source_quantity_roles=source_quantity_roles)}
    if after is not None:
        evidence["after"] = inspect(after, area, allow_repair_background=True)
    proposed = text_contract(replacement) if replacement is not None else None
    replacement_risks = text_risks(replacement) if replacement is not None else []
    baseline = evidence["source"]["text_contract"]
    contracts = {key: value["text_contract"] for key, value in evidence.items()}
    if proposed is not None:contracts["replacement"] = proposed
    numeric_same = all(value["decimal_identity"] == baseline["decimal_identity"] for value in contracts.values())
    opaque_same = all(value["opaque_identity"] == baseline["opaque_identity"] for value in contracts.values())
    changes = []
    if after is not None:
        old, new = evidence["before"]["text"], evidence["after"]["text"]
        changes = [{"operation": tag, "before": old[a:b], "after": new[c:d]}
            for tag, a, b, c, d in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if tag != "equal"]
    return {"version": VERSION, "mode": "source_derived_prose_and_protected_tokens", "bbox": list(area),
        "passed": all(value["passed"] for value in evidence.values()) and not replacement_risks and numeric_same and opaque_same,
        "protected_decimal_identity_preserved": numeric_same, "protected_opaque_identity_preserved": opaque_same,
        "required_source_tokens": baseline["protected_tokens"], "proposed_text_contract": proposed,
        "actual_text_changes": changes,
        "replacement_risks": replacement_risks, "evidence": evidence,
        "scope": "Only these edited islands; ambiguous math is rejected, not certified unchanged."}

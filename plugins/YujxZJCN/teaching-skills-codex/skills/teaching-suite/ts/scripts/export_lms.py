#!/usr/bin/env python3
"""LMS export — question sets and course packages the LMS can actually import.

Closes the adoption gap where exams shipped as Markdown (a human must retype every
question into Canvas/Moodle) and "LMS packaging" was a zip of files plus a manual
checklist. This produces importable artifacts:

  GIFT (.txt)            — Moodle's question-import format; the simplest, most reliable path
  QTI 2.1 (.zip)         — IMS standard; Canvas / Blackboard / Moodle question-bank import
  Common Cartridge (.imscc) — a minimal importable course package (syllabus + a QTI quiz)

Input is a question-set JSON (the intermediate `assessment-architect` item writers emit
alongside Markdown). Supported item types: multiple_choice, multiple_answer, true_false,
short_answer, essay. See `assessment-architect/references/lms_export_format.md`.

  {"title": "Midterm", "questions": [
     {"type":"multiple_choice","prompt":"...","points":2,"choices":["A","B"],"answer":0},
     {"type":"multiple_answer","prompt":"...","choices":["A","B","C"],"answer":[0,2]},
     {"type":"true_false","prompt":"...","answer":true},
     {"type":"short_answer","prompt":"...","answers":["mitosis"]},
     {"type":"essay","prompt":"...","points":10}]}

Usage:
  python3 scripts/export_lms.py questions.json --to gift  -o quiz.txt
  python3 scripts/export_lms.py questions.json --to qti   -o quiz_qti.zip
  python3 scripts/export_lms.py questions.json --to imscc -o course.imscc --syllabus syllabus.md

Honest scope: targets the common item types and QTI 2.1 / CC 1.3 shapes; exotic item
types and per-LMS quirks may need a tweak on import. Exit: 0 ok · 2 error.
"""

import argparse
import html
import json
import sys
import zipfile
from pathlib import Path

ITEM_TYPES = {"multiple_choice", "multiple_answer", "true_false", "short_answer", "essay"}


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    qs = data.get("questions", [])
    for i, q in enumerate(qs):
        q.setdefault("id", f"q{i+1}")
        q.setdefault("points", 1)
        if q.get("type") not in ITEM_TYPES:
            raise ValueError(f"question {q['id']}: unsupported type '{q.get('type')}'")
    return data


# --- GIFT (Moodle) ------------------------------------------------------------

def _gift_esc(s):
    return str(s).replace("~", r"\~").replace("=", r"\=").replace("#", r"\#").replace("{", r"\{").replace("}", r"\}")


def to_gift(data):
    out = []
    for q in data["questions"]:
        t, p = q["type"], _gift_esc(q["prompt"])
        out.append(f"::{q['id']}:: {p} ", )
        if t == "multiple_choice":
            opts = "".join(f"\n  {'=' if i == q['answer'] else '~'}{_gift_esc(c)}"
                           for i, c in enumerate(q["choices"]))
            out.append("{" + opts + "\n}")
        elif t == "multiple_answer":
            ans = set(q["answer"])
            n_correct = len(ans)
            opts = "".join(
                f"\n  ~%{round(100/n_correct)}%{_gift_esc(c)}" if i in ans
                else f"\n  ~%-{round(100/(len(q['choices'])-n_correct))}%{_gift_esc(c)}"
                for i, c in enumerate(q["choices"]))
            out.append("{" + opts + "\n}")
        elif t == "true_false":
            out.append("{" + ("TRUE" if q["answer"] else "FALSE") + "}")
        elif t == "short_answer":
            out.append("{" + "".join(f"\n  ={_gift_esc(a)}" for a in q["answers"]) + "\n}")
        elif t == "essay":
            out.append("{}")
        out.append("\n\n")
    return "".join(out)


# --- QTI 2.1 assessmentItem ---------------------------------------------------

def _qti_item(q):
    e = html.escape
    ident = q["id"]
    prompt = e(q["prompt"])
    if q["type"] in ("multiple_choice", "true_false"):
        if q["type"] == "true_false":
            choices = [("T", "True"), ("F", "False")]
            correct = "T" if q["answer"] else "F"
        else:
            choices = [(f"c{i}", c) for i, c in enumerate(q["choices"])]
            correct = f"c{q['answer']}"
        ch = "".join(f'<simpleChoice identifier="{cid}">{e(str(txt))}</simpleChoice>' for cid, txt in choices)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1" identifier="{ident}" title="{ident}" adaptive="false" timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="single" baseType="identifier">
    <correctResponse><value>{correct}</value></correctResponse>
  </responseDeclaration>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float"/>
  <itemBody><choiceInteraction responseIdentifier="RESPONSE" maxChoices="1" shuffle="true">
    <prompt>{prompt}</prompt>{ch}
  </choiceInteraction></itemBody>
  <responseProcessing template="http://www.imsglobal.org/question/qti_v2p1/rptemplates/match_correct"/>
</assessmentItem>'''
    if q["type"] == "multiple_answer":
        ch = "".join(f'<simpleChoice identifier="c{i}">{e(str(c))}</simpleChoice>' for i, c in enumerate(q["choices"]))
        vals = "".join(f"<value>c{i}</value>" for i in q["answer"])
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1" identifier="{ident}" title="{ident}" adaptive="false" timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="multiple" baseType="identifier">
    <correctResponse>{vals}</correctResponse>
  </responseDeclaration>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float"/>
  <itemBody><choiceInteraction responseIdentifier="RESPONSE" maxChoices="0" shuffle="true">
    <prompt>{prompt}</prompt>{ch}
  </choiceInteraction></itemBody>
  <responseProcessing template="http://www.imsglobal.org/question/qti_v2p1/rptemplates/match_correct"/>
</assessmentItem>'''
    if q["type"] == "short_answer":
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1" identifier="{ident}" title="{ident}" adaptive="false" timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="single" baseType="string">
    <correctResponse>{"".join(f"<value>{e(str(a))}</value>" for a in q["answers"])}</correctResponse>
  </responseDeclaration>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float"/>
  <itemBody><textEntryInteraction responseIdentifier="RESPONSE" expectedLength="40"/>
    <p>{prompt}</p></itemBody>
</assessmentItem>'''
    # essay
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1" identifier="{ident}" title="{ident}" adaptive="false" timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="single" baseType="string"/>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float"/>
  <itemBody><extendedTextInteraction responseIdentifier="RESPONSE" expectedLines="10">
    <prompt>{prompt}</prompt></extendedTextInteraction></itemBody>
</assessmentItem>'''


def _qti_manifest(data, item_files):
    e = html.escape
    resources = "".join(
        f'<resource identifier="res_{q["id"]}" type="imsqti_item_xmlv2p1" href="{f}">'
        f'<file href="{f}"/></resource>' for q, f in zip(data["questions"], item_files))
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="man_{e(data.get("title","quiz")).replace(" ","_")}" xmlns="http://www.imsglobal.org/xsd/imscp_v1p1">
  <metadata><schema>QTIv2.1 Package</schema><schemaversion>1.0.0</schemaversion></metadata>
  <organizations/>
  <resources>{resources}</resources>
</manifest>'''


def to_qti_zip(data, out):
    files = {}
    item_files = []
    for q in data["questions"]:
        fn = f"{q['id']}.xml"
        files[fn] = _qti_item(q)
        item_files.append(fn)
    files["imsmanifest.xml"] = _qti_manifest(data, item_files)
    _write_zip(out, files)
    return item_files


# --- Common Cartridge (minimal) ----------------------------------------------

def to_imscc(data, out, syllabus_md=None):
    e = html.escape
    files = {}
    # syllabus as a web resource
    syl_html = "<h1>Syllabus</h1><p>See course materials.</p>"
    if syllabus_md and Path(syllabus_md).exists():
        body = e(Path(syllabus_md).read_text(encoding="utf-8"))
        syl_html = f"<pre>{body}</pre>"
    files["web/syllabus.html"] = f"<!doctype html><html><head><meta charset='utf-8'><title>Syllabus</title></head><body>{syl_html}</body></html>"
    # the quiz as embedded QTI items
    item_files = []
    for q in data["questions"]:
        fn = f"quiz/{q['id']}.xml"
        files[fn] = _qti_item(q)
        item_files.append(fn)
    res = ('<resource identifier="r_syllabus" type="webcontent" href="web/syllabus.html">'
           '<file href="web/syllabus.html"/></resource>')
    res += "".join(
        f'<resource identifier="r_{q["id"]}" type="imsqti_item_xmlv2p1" href="{f}"><file href="{f}"/></resource>'
        for q, f in zip(data["questions"], item_files))
    files["imsmanifest.xml"] = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="cc_{e(data.get("title","course")).replace(" ","_")}"
  xmlns="http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1">
  <metadata><schema>IMS Common Cartridge</schema><schemaversion>1.3.0</schemaversion></metadata>
  <organizations><organization identifier="org1" structure="rooted-hierarchy">
    <item identifier="root"><item identifier="i_syllabus" identifierref="r_syllabus"><title>Syllabus</title></item></item>
  </organization></organizations>
  <resources>{res}</resources>
</manifest>'''
    _write_zip(out, files)


# --- helpers ------------------------------------------------------------------

def _write_zip(out, files):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("questions", help="question-set JSON")
    ap.add_argument("--to", choices=["gift", "qti", "imscc"], required=True)
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--syllabus", default=None, help="syllabus.md to embed (imscc only)")
    args = ap.parse_args(argv)
    try:
        data = load(args.questions)
        if args.to == "gift":
            out = args.out or "quiz.txt"
            Path(out).write_text(to_gift(data), encoding="utf-8")
        elif args.to == "qti":
            out = args.out or "quiz_qti.zip"
            to_qti_zip(data, out)
        else:
            out = args.out or "course.imscc"
            to_imscc(data, out, args.syllabus)
    except Exception as ex:
        print(f"error: {type(ex).__name__}: {ex}", file=sys.stderr)
        return 2
    print(f"exported {len(data['questions'])} questions → {out} ({args.to})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

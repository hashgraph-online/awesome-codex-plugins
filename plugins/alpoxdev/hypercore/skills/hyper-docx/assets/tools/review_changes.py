"""Tracked changes and comments: read, accept, reject, add, and diff two files.

Accepting removes deleted content and keeps inserted content; rejecting does the
inverse. Both directions rewrite only the affected runs and every other part of
the package keeps its bytes.
"""

import difflib
import hashlib

from docxlib import (
    DocxError,
    NS,
    Package,
    XML_DECL,
    local,
    qn,
    read_text,
    revision_summary,
)
from xml.etree import ElementTree as ET


def _text_paragraphs(pkg):
    out = []
    for index, paragraph in enumerate(pkg.body().iter(qn("w:p"))):
        text = read_text(paragraph)
        if text.strip():
            out.append((index, text))
    return out


def _replace_child(parent, old, new):
    for index, child in enumerate(list(parent)):
        if child is old:
            parent.remove(child)
            if new is not None:
                parent.insert(index, new)
            return True
    return False


def accept_all(pkg):
    """Keep insertions, drop deletions. Returns (accepted, rejected) counts."""
    accepted = 0
    rejected = 0
    roots = [pkg.document()]
    for name in pkg.names():
        if not name.startswith("word/"):
            continue
        if name.endswith(("header1.xml", "footer1.xml")):
            roots.append(pkg.root(name))
    for root in roots:
        changed = False
        for parent in list(root.iter()):
            for child in list(parent):
                tag = local(child.tag)
                if tag == "del":
                    parent.remove(child)
                    rejected += 1
                    changed = True
                elif tag == "ins":
                    position = list(parent).index(child)
                    parent.remove(child)
                    for offset, run in enumerate(list(child)):
                        parent.insert(position + offset, run)
                    accepted += 1
                    changed = True
                elif tag == "delText":
                    child.tag = qn("w:t")
                    changed = True
                elif tag == "moveFrom":
                    parent.remove(child)
                    rejected += 1
                    changed = True
                elif tag == "moveTo":
                    position = list(parent).index(child)
                    parent.remove(child)
                    for offset, run in enumerate(list(child)):
                        parent.insert(position + offset, run)
                    accepted += 1
                    changed = True
            # a paragraph whose mark was deleted disappears entirely
            if local(parent.tag) == "pPr":
                marker = parent.find(qn("w:rPr"))
                if marker is not None:
                    deleted_mark = marker.find(qn("w:del"))
                    inserted_mark = marker.find(qn("w:ins"))
                    if deleted_mark is not None:
                        marker.remove(deleted_mark)
                        changed = True
                    if inserted_mark is not None:
                        marker.remove(inserted_mark)
                        changed = True
        if changed:
            part = pkg.document_part() if root is pkg.document() else pkg.part_of(root)
            if part:
                pkg.dirty(part)
    return accepted, rejected


def reject_all(pkg):
    """Keep deletions, drop insertions."""
    accepted = 0
    rejected = 0
    roots = [pkg.document()]
    for name in pkg.names():
        if not name.startswith("word/"):
            continue
        if name.endswith(("header1.xml", "footer1.xml")):
            roots.append(pkg.root(name))
    for root in roots:
        changed = False
        for parent in list(root.iter()):
            for child in list(parent):
                tag = local(child.tag)
                if tag == "ins":
                    parent.remove(child)
                    rejected += 1
                    changed = True
                elif tag == "del":
                    position = list(parent).index(child)
                    parent.remove(child)
                    for offset, run in enumerate(list(child)):
                        for node in run.iter(qn("w:delText")):
                            node.tag = qn("w:t")
                        parent.insert(position + offset, run)
                    accepted += 1
                    changed = True
                elif tag == "moveTo":
                    parent.remove(child)
                    rejected += 1
                    changed = True
                elif tag == "moveFrom":
                    position = list(parent).index(child)
                    parent.remove(child)
                    for offset, run in enumerate(list(child)):
                        parent.insert(position + offset, run)
                    accepted += 1
                    changed = True
        if changed:
            part = pkg.document_part() if root is pkg.document() else pkg.part_of(root)
            if part:
                pkg.dirty(part)
    return accepted, rejected


def replace_text_as_revision(pkg, find, replace, author, date):
    """Replace one exact text occurrence and mark it as an insertion and a deletion."""
    document = pkg.document()
    for paragraph in document.iter(qn("w:p")):
        text = read_text(paragraph)
        if find not in text:
            continue
        runs = [run for run in paragraph.findall(qn("w:r"))]
        if not runs:
            continue
        combined = "".join(read_text(run) for run in runs)
        start = combined.find(find)
        if start < 0:
            continue
        end = start + len(find)
        position = 0
        segments = []
        for run in runs:
            length = len(read_text(run))
            segments.append((run, position, position + length))
            position += length
        marked = False
        for run, run_start, run_end in segments:
            if run_end <= start or run_start >= end:
                continue
            local_text = read_text(run)
            before = local_text[: max(0, start - run_start)]
            overlap = local_text[max(0, start - run_start): max(0, end - run_start)]
            after = local_text[max(0, end - run_start):]
            if overlap:
                rpr = run.find(qn("w:rPr"))
                deleted = ET.Element(qn("w:del"))
                deleted.set(qn("w:id"), str(_next_id(pkg)))
                deleted.set(qn("w:author"), author)
                deleted.set(qn("w:date"), date)
                del_run = ET.SubElement(deleted, qn("w:r"))
                if rpr is not None:
                    del_run.append(_copy(rpr))
                del_text = ET.SubElement(del_run, qn("w:delText"))
                del_text.text = overlap
                del_text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                inserted = ET.Element(qn("w:ins"))
                inserted.set(qn("w:id"), str(_next_id(pkg) + 1))
                inserted.set(qn("w:author"), author)
                inserted.set(qn("w:date"), date)
                ins_run = ET.SubElement(inserted, qn("w:r"))
                if rpr is not None:
                    ins_run.append(_copy(rpr))
                ins_text = ET.SubElement(ins_run, qn("w:t"))
                ins_text.text = replace
                ins_text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                parent = paragraph
                index = list(parent).index(run)
                parent.remove(run)
                replacements = []
                if before:
                    replacements.append(_run_with_text(run, before))
                replacements.append(deleted)
                replacements.append(inserted)
                if after:
                    replacements.append(_run_with_text(run, after))
                for offset, node in enumerate(replacements):
                    parent.insert(index + offset, node)
                marked = True
                break
        if marked:
            pkg.dirty(pkg.document_part())
            return True
    return False


def add_comment(pkg, anchor_text, body_text, author, initials, date):
    """Attach a comment to the first paragraph containing anchor_text."""
    document = pkg.document()
    target = None
    for paragraph in document.iter(qn("w:p")):
        if anchor_text and anchor_text in read_text(paragraph):
            target = paragraph
            break
    if target is None:
        return None
    comment_id = _next_comment_id(pkg)
    part = _ensure_comments_part(pkg)
    comments_root = pkg.root(part)
    comment = ET.SubElement(comments_root, qn("w:comment"))
    comment.set(qn("w:id"), str(comment_id))
    comment.set(qn("w:author"), author)
    comment.set(qn("w:initials"), initials)
    comment.set(qn("w:date"), date)
    paragraph = ET.SubElement(comment, qn("w:p"))
    run = ET.SubElement(paragraph, qn("w:r"))
    text = ET.SubElement(run, qn("w:t"))
    text.text = body_text
    text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    pkg.dirty(part)

    start = ET.Element(qn("w:commentRangeStart"))
    start.set(qn("w:id"), str(comment_id))
    end = ET.Element(qn("w:commentRangeEnd"))
    end.set(qn("w:id"), str(comment_id))
    reference_run = ET.Element(qn("w:r"))
    reference = ET.SubElement(reference_run, qn("w:commentReference"))
    reference.set(qn("w:id"), str(comment_id))
    target.insert(0, start)
    target.append(end)
    target.append(reference_run)
    pkg.dirty(pkg.document_part())
    return comment_id


def _comment_ids(pkg):
    ids = set()
    part = _comments_part(pkg)
    if part is None:
        return ids
    for node in pkg.root(part).findall(qn("w:comment")):
        try:
            ids.add(int(node.get(qn("w:id"))))
        except (TypeError, ValueError):
            pass
    return ids


def _comments_part(pkg):
    document = pkg.document_part()
    for _rid, rel_type, target, mode in pkg.relationships(document):
        if rel_type.endswith("/comments") and mode == "Internal":
            part = pkg.resolve(document, target)
            if pkg.get(part) is not None:
                return part
    return None


def _ensure_comments_part(pkg):
    existing = _comments_part(pkg)
    if existing:
        return existing
    from docxlib import CT_COMMENTS, REL_COMMENTS

    part = "word/comments.xml"
    pkg.set(part, (XML_DECL + '<w:comments xmlns:w="%s"/>' % NS["w"]).encode("utf-8"))
    pkg.ensure_override(part, CT_COMMENTS)
    pkg.add_relationship(pkg.document_part(), REL_COMMENTS, "comments.xml")
    return part


def _next_comment_id(pkg):
    ids = _comment_ids(pkg)
    value = 0
    while value in ids:
        value += 1
    return value


def _revision_ids(pkg):
    ids = set()
    for name in pkg.names():
        if not name.startswith("word/"):
            continue
        try:
            root = pkg.root(name)
        except DocxError:
            continue
        for node in root.iter():
            if local(node.tag) in ("ins", "del", "moveFrom", "moveTo"):
                try:
                    ids.add(int(node.get(qn("w:id"))))
                except (TypeError, ValueError):
                    pass
    return ids


def _next_id(pkg):
    ids = _revision_ids(pkg)
    value = 1
    while value in ids:
        value += 1
    return value


def _copy(node):
    return ET.fromstring(ET.tostring(node))


def _run_with_text(run, text):
    """A copy of `run` whose visible text is exactly `text`."""
    clone = _copy(run)
    for node in list(clone):
        if local(node.tag) in ("t", "delText"):
            clone.remove(node)
    target = ET.SubElement(clone, qn("w:t"))
    target.text = text
    target.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return clone


def compare(left_path, right_path):
    """A text-level comparison of two files: paragraph diff plus package facts."""
    left = Package.open(left_path)
    right = Package.open(right_path)
    left_paras = _text_paragraphs(left)
    right_paras = _text_paragraphs(right)
    matcher = difflib.SequenceMatcher(a=[t for _i, t in left_paras], b=[t for _i, t in right_paras])
    hunks = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        hunks.append({
            "op": tag,
            "left": [text for _i, text in left_paras[i1:i2]],
            "right": [text for _i, text in right_paras[j1:j2]],
        })
    return {
        "left": {"path": left_path, "paragraphs": len(left_paras),
                 "sha256": _digest(left_path)},
        "right": {"path": right_path, "paragraphs": len(right_paras),
                  "sha256": _digest(right_path)},
        "hunks": hunks,
    }


def _digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def summary(path):
    pkg = Package.open(path)
    return {
        "path": path,
        "tracked_changes": revision_summary(pkg.document()),
        "track_changes_setting": bool(pkg.get("word/settings.xml") and b"trackChanges" in (pkg.get("word/settings.xml") or b"")),
    }
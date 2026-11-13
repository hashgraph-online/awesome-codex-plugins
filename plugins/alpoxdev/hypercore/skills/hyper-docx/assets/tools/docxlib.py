"""WordprocessingML package model: read a .docx, build one, keep the parts honest.

Standard library only (Python 3.8+). Every part is kept as raw bytes so an edit
touches only the part it names; the XML tree is materialized on demand and
serialized back with the prefixes the original file used.
"""

import os
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

REL_OFFICE_DOCUMENT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
REL_STYLES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
REL_NUMBERING = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering"
REL_SETTINGS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"
REL_FONT_TABLE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable"
REL_COMMENTS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
REL_FOOTER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
REL_HEADER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
REL_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
REL_CORE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
REL_APP = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"

CT_DOCUMENT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
CT_STYLES = "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"
CT_NUMBERING = "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"
CT_SETTINGS = "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"
CT_FONT_TABLE = "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"
CT_COMMENTS = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
CT_FOOTER = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"
CT_HEADER = "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"
CT_CORE = "application/vnd.openxmlformats-package.core-properties+xml"
CT_APP = "application/vnd.openxmlformats-officedocument.extended-properties+xml"
CT_RELS = "application/vnd.openxmlformats-package.relationships+xml"

# A4 in twentieths of a point (twip): 11906 x 16838.
A4_TWIP = (11906, 16838)
MM_PER_TWIP = 25.4 / 1440.0


def qn(tag):
    prefix, local = tag.split(":", 1)
    return "{%s}%s" % (NS[prefix], local)


def local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def mm_to_twip(mm):
    return int(round(float(mm) * 1440.0 / 25.4))


def twip_to_mm(twip):
    return round(float(twip) * MM_PER_TWIP, 2)


def pt_to_half_points(pt):
    return int(round(float(pt) * 2))


def pct_to_twip_line(percent):
    """Word line spacing in 240ths of a line: 200% -> 480."""
    return int(round(float(percent) * 240.0 / 100.0))


def register_namespaces(xml_bytes):
    """Register every prefix the document declares, so ET writes them back unchanged."""
    try:
        for _event, (prefix, uri) in ET.iterparse(
            _bytes_reader(xml_bytes), events=("start-ns",)
        ):
            if prefix and not re.match(r"ns\d+$", prefix):
                ET.register_namespace(prefix, uri)
    except ET.ParseError:
        raise
    for prefix, uri in NS.items():
        if not re.match(r"ns\d+$", prefix):
            ET.register_namespace(prefix, uri)


class _bytes_reader(object):
    """Minimal file-like object over bytes for ET.iterparse."""

    def __init__(self, data):
        self._data = data
        self._pos = 0

    def read(self, size=-1):
        if size is None or size < 0:
            chunk = self._data[self._pos:]
            self._pos = len(self._data)
            return chunk
        chunk = self._data[self._pos : self._pos + size]
        self._pos += len(chunk)
        return chunk


class DocxError(Exception):
    """A package-level problem the caller should report, not traceback."""


class Package(object):
    """A .docx file as an ordered map of part name -> bytes."""

    def __init__(self):
        self.parts = []  # [(name, bytes)] preserves write order and determinism
        self._index = {}
        self._tree_cache = {}

    # -- reading ---------------------------------------------------------
    @classmethod
    def open(cls, path):
        if not os.path.isfile(path):
            raise DocxError("file not found: %s" % path)
        pkg = cls()
        try:
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                if bad:
                    raise DocxError("corrupt zip member: %s" % bad)
                for name in zf.namelist():
                    if name.endswith("/"):
                        continue
                    pkg.set(name, zf.read(name))
        except zipfile.BadZipFile as exc:
            raise DocxError("not a zip package (%s): %s" % (path, exc))
        if pkg.get("[Content_Types].xml") is None:
            raise DocxError("missing [Content_Types].xml; this is not an OOXML package")
        return pkg

    # -- part access -----------------------------------------------------
    def set(self, name, data):
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode("utf-8")
        if name in self._index:
            self.parts[self._index[name]] = (name, bytes(data))
        else:
            self._index[name] = len(self.parts)
            self.parts.append((name, bytes(data)))
        self._tree_cache.pop(name, None)

    def get(self, name):
        idx = self._index.get(name)
        if idx is None:
            return None
        return self.parts[idx][1]

    def names(self):
        return [name for name, _ in self.parts]

    def remove(self, name):
        idx = self._index.pop(name, None)
        if idx is None:
            return False
        del self.parts[idx]
        self._index = {n: i for i, (n, _) in enumerate(self.parts)}
        self._tree_cache.pop(name, None)
        return True

    # -- xml helpers -----------------------------------------------------
    def root(self, name):
        cached = self._tree_cache.get(name)
        if cached is not None:
            return cached
        data = self.get(name)
        if data is None:
            raise DocxError("part not present: %s" % name)
        register_namespaces(data)
        try:
            tree = ET.fromstring(data)
        except ET.ParseError as exc:
            raise DocxError("part %s is not well-formed XML: %s" % (name, exc))
        self._tree_cache[name] = tree
        return tree

    def put_root(self, name, tree):
        register_namespaces(self.get(name) or b"<root/>")
        body = ET.tostring(tree, encoding="utf-8", xml_declaration=False)
        body = body.decode("utf-8")
        if not body.startswith("<?xml"):
            body = XML_DECL + body
        self.set(name, body.encode("utf-8"))
        self._tree_cache[name] = tree

    def dirty(self, name):
        """Serialize a mutated tree back into the part bytes."""
        tree = self._tree_cache.get(name)
        if tree is None:
            return
        body = ET.tostring(tree, encoding="utf-8").decode("utf-8")
        body = re.sub(r"^<\?xml[^>]*\?>", "", body)
        self.set(name, (XML_DECL + body).encode("utf-8"))

    def flush(self):
        for name in list(self._tree_cache.keys()):
            self.dirty(name)

    # -- relationships ---------------------------------------------------
    def part_of(self, tree):
        """Return the part name whose cached tree is this exact object."""
        for name, cached in self._tree_cache.items():
            if cached is tree:
                return name
        return None

    def rels_name(self, part):
        directory, base = posixpath.split(part)
        return posixpath.join(directory, "_rels", base + ".rels")

    def relationships(self, part):
        """Return [(id, type, target, target_mode)] for one part."""
        rels = self.get(self.rels_name(part))
        if rels is None:
            return []
        root = self.root(self.rels_name(part))
        out = []
        for rel in root.findall(qn("rel:Relationship")):
            out.append(
                (
                    rel.get("Id"),
                    rel.get("Type"),
                    rel.get("Target"),
                    rel.get("TargetMode") or "Internal",
                )
            )
        return out

    def resolve(self, part, target):
        """Resolve a relationship target against the part that owns it."""
        if target.startswith("/"):
            return target.lstrip("/")
        base = posixpath.dirname(part)
        return posixpath.normpath(posixpath.join(base, target))

    def next_rel_id(self, part):
        used = set()
        for rid, _t, _target, _mode in self.relationships(part):
            match = re.match(r"rId(\d+)$", rid or "")
            if match:
                used.add(int(match.group(1)))
        n = 1
        while n in used:
            n += 1
        return "rId%d" % n

    def add_relationship(self, part, rel_type, target, target_mode=None):
        rels_part = self.rels_name(part)
        data = self.get(rels_part)
        if data is None:
            self.set(
                rels_part,
                (
                    XML_DECL
                    + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
                ).encode("utf-8"),
            )
        rid = self.next_rel_id(part)
        attrs = {"Id": rid, "Type": rel_type, "Target": target}
        if target_mode:
            attrs["TargetMode"] = target_mode
        root = self.root(rels_part)
        node = ET.SubElement(root, qn("rel:Relationship"))
        for key, value in attrs.items():
            node.set(key, value)
        self.dirty(rels_part)
        return rid

    # -- content types ---------------------------------------------------
    def content_types(self):
        root = self.root("[Content_Types].xml")
        defaults = {}
        overrides = {}
        for node in root.findall(qn("ct:Default")):
            defaults[(node.get("Extension") or "").lower()] = node.get("ContentType")
        for node in root.findall(qn("ct:Override")):
            overrides[node.get("PartName") or ""] = node.get("ContentType")
        return defaults, overrides

    def ensure_override(self, part, content_type):
        root = self.root("[Content_Types].xml")
        part_name = "/" + part.lstrip("/")
        for node in root.findall(qn("ct:Override")):
            if node.get("PartName") == part_name:
                if node.get("ContentType") != content_type:
                    node.set("ContentType", content_type)
                    self.dirty("[Content_Types].xml")
                return
        node = ET.SubElement(root, qn("ct:Override"))
        node.set("PartName", part_name)
        node.set("ContentType", content_type)
        self.dirty("[Content_Types].xml")

    def ensure_default(self, extension, content_type):
        root = self.root("[Content_Types].xml")
        for node in root.findall(qn("ct:Default")):
            if (node.get("Extension") or "").lower() == extension.lower():
                return
        node = ET.SubElement(root, qn("ct:Default"))
        node.set("Extension", extension)
        node.set("ContentType", content_type)
        self.dirty("[Content_Types].xml")

    # -- writing ---------------------------------------------------------
    def save(self, path):
        self.flush()
        directory = os.path.dirname(os.path.abspath(path))
        if directory and not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        # [Content_Types].xml first, then a fixed order, then a fixed timestamp:
        # the same input bytes produce the same package bytes.
        order = []
        seen = set()
        if self.get("[Content_Types].xml") is not None:
            order.append("[Content_Types].xml")
            seen.add("[Content_Types].xml")
        for name, _data in self.parts:
            if name in seen:
                continue
            order.append(name)
            seen.add(name)
        tmp = path + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for name in order:
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o600 << 16
                zf.writestr(info, self.get(name) or b"")
        os.replace(tmp, path)

    # -- document shortcuts ----------------------------------------------
    def document_part(self):
        """Resolve the main document part through the package relationships."""
        for _rid, rel_type, target, mode in self.relationships(""):
            if rel_type == REL_OFFICE_DOCUMENT and mode == "Internal":
                return self.resolve("", target)
        return "word/document.xml"

    def document(self):
        return self.root(self.document_part())

    def body(self):
        doc = self.document()
        node = doc.find(qn("w:body"))
        if node is None:
            node = ET.SubElement(doc, qn("w:body"))
        return node


def read_text(node):
    """Concatenate every w:t and w:delText under a node, in document order."""
    pieces = []
    for child in node.iter():
        tag = local(child.tag)
        if tag in ("t", "delText") and child.text:
            pieces.append(child.text)
    return "".join(pieces)


def iter_paragraphs(container):
    for node in container.iter(qn("w:p")):
        yield node


def paragraph_style(paragraph):
    ppr = paragraph.find(qn("w:pPr"))
    if ppr is None:
        return None
    style = ppr.find(qn("w:pStyle"))
    if style is None:
        return None
    return style.get(qn("w:val"))


def paragraph_runs(paragraph):
    """Yield (kind, run_node) where kind is plain, ins, or del."""
    for child in list(paragraph):
        tag = local(child.tag)
        if tag == "r":
            yield "plain", child
        elif tag == "ins":
            for run in child.findall(qn("w:r")):
                yield "ins", run
        elif tag == "del":
            for run in child.findall(qn("w:r")):
                yield "del", run


def revision_summary(root):
    """Count tracked changes by element and author."""
    summary = {}
    for node in root.iter():
        tag = local(node.tag)
        if tag not in ("ins", "del", "moveFrom", "moveTo"):
            continue
        author = node.get(qn("w:author")) or "(none)"
        key = (tag, author)
        summary[key] = summary.get(key, 0) + 1
    return [
        {"kind": kind, "author": author, "count": count}
        for (kind, author), count in sorted(summary.items())
    ]


def text_of(node):
    return read_text(node)


def escape_xml(value):
    return escape(value, {"\"": "&quot;"})


def attr(name, value):
    return " %s=%s" % (name, quoteattr(str(value)))

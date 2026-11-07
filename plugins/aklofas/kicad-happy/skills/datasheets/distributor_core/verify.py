"""PDF text extraction and datasheet verification: pdftotext then raw-byte scan;
MPN / manufacturer / keyword matching → confidence. ``same_part`` decides whether a
distributor search hit is the requested part."""

import json
import os
import re
import subprocess
import sys

# Maker ordering and packaging codes that name the same die and datasheet (tape and reel,
# lead-free finish). Short codes such as RL/CT are left out: they end passive value codes
# (RC0402FR-0710RL vs RC0402FR-07100KL), where stripping them equates different values.
ORDERING_SUFFIXES = ("#TRPBF", "#PBF", "#TR", "/NOPB", "T&R", "TR", "REEL", "REEL7",
                     "PBF", "G4", "E3", "GE3", "LF")
# The leftmost match at the end wins, so the longest listed suffix is stripped (GE3, not E3).
_ORDERING_SUFFIX_RE = re.compile(
    "-?(?:" + "|".join(re.escape(s) for s in ORDERING_SUFFIXES) + ")$")
_MPN_PUNCT_RE = re.compile(r"[\s\-_./,#+()]")
# Exact part numbers keep + # . : MAX3232ECUE+ (lead-free), LT1763CS8#PBF and AP2112K-3.3
# are orderable numbers of their own, distinct from MAX3232ECUE, LT1763CS8 and AP2112K-33.
_EXACT_PUNCT_RE = re.compile(r"[\s\-_/,()]")


def _strip_ordering_suffixes(mpn: str) -> str:
    """Upper-cased MPN without its trailing ordering suffixes (up to three)."""
    s = mpn.strip().upper()
    for _ in range(3):
        t = _ORDERING_SUFFIX_RE.sub("", s, count=1)
        if t == s:
            break
        s = t
    return s


def _part_key(mpn: str) -> str:
    """Upper-cased MPN without trailing ordering suffixes or punctuation."""
    return _MPN_PUNCT_RE.sub("", _strip_ordering_suffixes(mpn))


def _exact_key(mpn: str) -> str:
    """Upper-cased MPN without case, whitespace or ``-_/,()``; ordering marks kept."""
    return _EXACT_PUNCT_RE.sub("", mpn.upper())


def same_part(requested: str, hit: str, *, allow_family: bool = False,
              ordering_suffixes: bool = True) -> bool:
    """True when a search hit's MPN names the requested part.

    Case, whitespace and ``-_./,#+()`` are ignored, and so are the ordering suffixes in
    ``ORDERING_SUFFIXES``. With ``ordering_suffixes`` false the part number must be exact:
    only case, whitespace and ``-_/,()`` are ignored (lifecycle status belongs to one
    orderable number: a ``G4`` or ``+`` variant can be obsolete while the base is active).
    With ``allow_family`` a hit that extends the requested string
    also counts (``LM358`` -> ``LM358DR``); use it only when the request is a generic name,
    such as an MPN read from a symbol's Value field. Distributor part numbers are compared
    exactly by the caller, never here.
    """
    key = _part_key if ordering_suffixes else _exact_key
    a, b = key(requested or ""), key(hit or "")
    if not a or not b:
        return False
    if a == b:
        return True
    if not allow_family:
        return False
    # The family name keeps its tail: G4 in STM32G4 is part of the name, not a finish code.
    name = _MPN_PUNCT_RE.sub("", (requested or "").upper())
    return len(name) >= 4 and _MPN_PUNCT_RE.sub("", hit.upper()).startswith(name)


def pick_requested(results, requested: str, mpn_of, *, allow_family: bool = False):
    """The first search result that is the requested part, else None: an exact or
    ordering-suffix match first, then (with ``allow_family``) a family member."""
    for family in (False, True) if allow_family else (False,):
        for r in results:
            if same_part(requested, mpn_of(r), allow_family=family):
                return r
    return None


def other_part(requested: str, hit_mpn: str, hit_pns=(), *, by_pn: bool = False,
               allow_family: bool = False, part_mpn: str = "") -> str:
    """The hit's identifier when a search hit is not the requested part, else ``""``.

    With ``by_pn`` the request is the distributor's own part number: the hit is another part
    when it carries part numbers and none equals the request (case aside). A hit that carries
    none is checked against the part's own MPN (``part_mpn``) when both have one, and is
    otherwise taken as the distributor's answer. Without ``by_pn`` the request is an MPN,
    compared with ``same_part``.
    """
    if by_pn:
        pns = [p for p in hit_pns if p]
        if pns:
            if requested.strip().upper() in {p.strip().upper() for p in pns}:
                return ""
            return pns[0]
        if part_mpn and hit_mpn and not same_part(part_mpn, hit_mpn, allow_family=allow_family):
            return hit_mpn
        return ""
    if same_part(requested, hit_mpn, allow_family=allow_family):
        return ""
    return hit_mpn or "(no MPN)"


def fetch_mismatch(query: str, hit_mpn: str, hit_pns=()) -> str:
    """The hit's identifier when a fetch ``--search`` hit is not the requested part, else ``""``.

    The request is an MPN, a family name or the distributor's own part number.
    """
    q = query.strip().upper()
    if q and q in {(p or "").strip().upper() for p in hit_pns}:
        return ""
    return other_part(query, hit_mpn, allow_family=True)


def refuse_fetch_hit(label: str, query: str, other: str, as_json: bool):
    """Report that a fetch ``--search`` hit is another part, then exit 2."""
    msg = f"No matching {label} result for '{query}' (closest: '{other}', a different part)"
    print(msg, file=sys.stderr)
    if as_json:
        json.dump({"success": False, "error": msg}, sys.stdout)
    sys.exit(2)


def _extract_pdf_text(pdf_path: str, max_pages: int = 3) -> str:
    """Extract text from the first few pages of a PDF.

    Tries pdftotext (poppler-utils) first for best quality, then falls
    back to scanning raw PDF bytes for ASCII strings.
    """
    # Strategy 1: pdftotext (best quality, handles all encodings)
    from kicad_core.executables import find_executable
    tool = find_executable("pdftotext")
    if tool:
        try:
            result = subprocess.run(
                [tool, "-l", str(max_pages), pdf_path, "-"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Strategy 2: raw byte scanning (no dependencies needed)
    try:
        with open(pdf_path, "rb") as f:
            raw = f.read(200_000)  # first ~200KB covers first few pages
        # Extract readable ASCII sequences (4+ chars)
        strings = re.findall(rb"[\x20-\x7e]{4,}", raw)
        return " ".join(s.decode("ascii", errors="ignore") for s in strings)
    except Exception:
        return ""


def verify_datasheet(
    pdf_path: str,
    mpn: str,
    description: str = "",
    manufacturer: str = "",
) -> dict:
    """Verify a downloaded PDF is actually the correct datasheet.

    Extracts text from the first few pages and checks for the MPN,
    manufacturer, and description keywords. Returns a dict with:
      - verified: bool (True if MPN found in text)
      - confidence: "verified" | "likely" | "unverified" | "wrong"
      - mpn_found: bool
      - manufacturer_found: bool
      - keyword_hits: int (how many description keywords matched)
      - keyword_total: int
      - details: str (human-readable explanation)
    """
    text = _extract_pdf_text(pdf_path)
    if not text or len(text) < 50:
        return {
            "verified": False,
            "confidence": "unverified",
            "mpn_found": False,
            "manufacturer_found": False,
            "keyword_hits": 0,
            "keyword_total": 0,
            "details": "Could not extract text from PDF",
        }

    text_upper = text.upper()

    # Check for MPN — try exact, then base MPN without common suffixes
    mpn_upper = mpn.upper()
    mpn_found = mpn_upper in text_upper

    if not mpn_found:
        # Strip common ordering suffixes and try again
        # e.g., TPS61023DRLR -> TPS61023, BSS138LT1G -> BSS138
        base_mpn = re.sub(
            r"(DRLR|DRL|DGKR|DGK|DCKR|DCK|DBVR|DBV|PWPR|PWP|RGER|RGE|"
            r"RGTR|RGT|NRND|TR|CT|ND|LT1G|LT3G|BK|PBF|-ND)$",
            "", mpn_upper,
        )
        if base_mpn and len(base_mpn) >= 4 and base_mpn != mpn_upper:
            mpn_found = base_mpn in text_upper

    if not mpn_found:
        # A datasheet names the orderable part without its packaging code (LM358DRG4 -> LM358DR).
        ordered = _strip_ordering_suffixes(mpn)
        if len(ordered) >= 4 and ordered != mpn_upper:
            mpn_found = ordered in text_upper

    # Check manufacturer name
    mfg_found = False
    if manufacturer:
        mfg_upper = manufacturer.upper()
        # Try full name and common short forms
        mfg_found = mfg_upper in text_upper
        if not mfg_found:
            # Try first word (e.g., "Texas" from "Texas Instruments")
            first_word = mfg_upper.split()[0] if " " in mfg_upper else ""
            if first_word and len(first_word) >= 4:
                mfg_found = first_word in text_upper

    # Check description keywords
    keywords = []
    if description:
        # Extract meaningful words from description (skip noise)
        skip = {"the", "a", "an", "for", "and", "or", "with", "in", "to",
                "of", "at", "by", "on", "no", "w", "smd", "smt"}
        for word in re.split(r"[\s/,_-]+", description):
            w = word.strip().upper()
            if len(w) >= 3 and w not in skip and not re.match(r"^\d+$", w):
                keywords.append(w)

    keyword_hits = sum(1 for kw in keywords if kw in text_upper) if keywords else 0
    keyword_total = len(keywords)

    # Determine confidence level
    if mpn_found:
        confidence = "verified"
        details = f"MPN '{mpn}' found in PDF text"
    elif mfg_found and keyword_hits >= max(1, keyword_total // 2):
        confidence = "likely"
        details = (f"MPN not found but manufacturer '{manufacturer}' present "
                   f"with {keyword_hits}/{keyword_total} description keywords")
    elif keyword_hits >= max(2, keyword_total * 2 // 3):
        confidence = "likely"
        details = f"{keyword_hits}/{keyword_total} description keywords found"
    elif keyword_hits == 0 and keyword_total >= 3 and not mfg_found:
        confidence = "wrong"
        details = (f"No MPN, manufacturer, or description keywords found in PDF "
                   f"(0/{keyword_total} keywords)")
    else:
        confidence = "unverified"
        details = (f"MPN not found; {keyword_hits}/{keyword_total} keywords, "
                   f"manufacturer {'found' if mfg_found else 'not found'}")

    return {
        "verified": mpn_found,
        "confidence": confidence,
        "mpn_found": mpn_found,
        "manufacturer_found": mfg_found,
        "keyword_hits": keyword_hits,
        "keyword_total": keyword_total,
        "details": details,
    }


def downloaded_entry(part: dict, path, filename: str, *, verify_pn: str, manufacturer: str,
                     description: str, url: str, source: str, now: str,
                     vendor_id: tuple[str, str] | None = None, warn: bool = True) -> dict:
    """The manifest entry for a datasheet just downloaded to *path*: size, identity verdict,
    and the vendor's id (key, value) after "source" when given. With *warn*, a "wrong" verdict
    is reported on stderr before the entry is built."""
    size = os.path.getsize(str(path))
    vr = verify_datasheet(str(path), verify_pn, description, manufacturer)
    if warn and vr["confidence"] == "wrong":
        print(f"  WARNING: PDF may be wrong datasheet — {vr['details']}", file=sys.stderr)
    entry = {
        "file": filename,
        "manufacturer": manufacturer,
        "description": description,
        "value": part["value"],
        "datasheet_url": url,
        "downloaded_date": now,
        "source": source,
        **({vendor_id[0]: vendor_id[1]} if vendor_id else {}),
        "status": "ok",
        "references": part["references"],
        "size_bytes": size,
        "verification": vr["confidence"],
    }
    if vr["confidence"] == "wrong":
        entry["verification_details"] = vr["details"]
    return entry

"""PDF text extraction and datasheet verification: pdftotext then raw-byte scan;
MPN / manufacturer / keyword matching → confidence."""

import re
import subprocess


def _extract_pdf_text(pdf_path: str, max_pages: int = 3) -> str:
    """Extract text from the first few pages of a PDF.

    Tries pdftotext (poppler-utils) first for best quality, then falls
    back to scanning raw PDF bytes for ASCII strings.
    """
    # Strategy 1: pdftotext (best quality, handles all encodings)
    try:
        result = subprocess.run(
            ["pdftotext", "-l", str(max_pages), pdf_path, "-"],
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

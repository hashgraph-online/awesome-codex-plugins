"""
Heuristic page selection for datasheet PDF extraction.

Given a downloaded datasheet PDF, identifies which pages contain the
information Claude needs for structured extraction: pin tables, absolute
maximum ratings, recommended operating conditions, electrical characteristics,
and application circuits. This reduces token cost by 60-85% compared to
feeding the entire PDF.

Uses pdftotext and pdfinfo (poppler-utils) for text extraction. Falls back
gracefully if these aren't available — returns all pages with low confidence.

Usage:
    from datasheet_page_selector import suggest_pages

    selection = suggest_pages("/path/to/datasheet.pdf", "TPS61023DRLR", "switching_regulator")
    print(selection.pages)     # [1, 2, 3, 5, 8, 15]
    print(selection.reasons)   # {1: "front page", 3: "pin description table", ...}
    print(selection.confidence)  # "toc_found" | "keyword_scored" | "fallback"
"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class PageSelection:
    """Result of page selection heuristics."""
    pages: list = field(default_factory=list)
    reasons: dict = field(default_factory=dict)  # page_num -> reason string
    confidence: str = "fallback"  # "toc_found", "keyword_scored", "fallback"
    total_pages: int = 0


# ---------------------------------------------------------------------------
# Maximum pages to select (keeps token cost manageable)
# ---------------------------------------------------------------------------

# Category-specific page limits
_PAGE_LIMITS = {
    "microcontroller": 15,  # MCUs have complex pin tables
    "fpga": 15,
    "soc": 15,
    "default": 10,
}


# ---------------------------------------------------------------------------
# TOC section patterns
# ---------------------------------------------------------------------------

# Each entry: (regex_pattern, reason_label, priority)
# Priority 1 = always include, 2 = include if space, 3 = nice to have
_TOC_PATTERNS = [
    (r'pin\s+(?:description|configuration|function|assignment|definition|table|diagram)',
     "pin_table", 1),
    (r'absolute\s+maximum\s+rat',
     "abs_max_ratings", 1),
    (r'(?:recommended|typical)\s+operating\s+cond',
     "operating_conditions", 1),
    (r'electrical\s+characteristics?',
     "electrical_chars", 1),
    (r'(?:typical\s+)?application(?:\s+(?:circuit|schematic|diagram|information))?',
     "application_circuit", 1),
    (r'functional\s+(?:block\s+)?diagram',
     "block_diagram", 2),
    (r'package\s+(?:information|outline|dimensions|marking)',
     "package_info", 2),
    (r'pin(?:out)?\s+(?:diagram|drawing)',
     "pinout_diagram", 1),
    (r'thermal\s+(?:information|characteristics|pad)',
     "thermal_info", 2),
    (r'ordering\s+information',
     "ordering", 3),
    (r'detailed\s+description',
     "detailed_desc", 2),
    (r'design\s+(?:guide|guidelines|considerations|recommendations)',
     "design_guide", 2),
    (r'power\s+(?:supply|management)\s+(?:consideration|recommendation)',
     "power_design", 2),
    (r'layout\s+(?:guide|guidelines|considerations|recommendations)',
     "layout_guide", 2),
]


# ---------------------------------------------------------------------------
# Keyword scoring weights for fallback page identification
# ---------------------------------------------------------------------------

# (regex_pattern, weight)  — higher weight = more relevant page
_KEYWORD_SCORES = [
    (r'\bpin\b.*\b(?:name|function|description|number)\b', 5.0),
    (r'\babsolute\s+maximum\b', 4.0),
    (r'\brecommended\s+operating\b', 4.0),
    (r'\belectrical\s+characteristics?\b', 3.5),
    (r'\bapplication\s+(?:circuit|schematic)\b', 3.5),
    (r'\btypical\s+application\b', 3.5),
    (r'\bpin\s+(?:configuration|assignment|diagram)\b', 3.0),
    (r'\bblock\s+diagram\b', 2.0),
    (r'\binput\s+voltage\b', 2.0),
    (r'\boutput\s+voltage\b', 2.0),
    (r'\bvoltage\s+range\b', 2.0),
    (r'\bmaximum\s+rat', 2.0),
    (r'\b(?:V_?CC|V_?DD|V_?IN|V_?OUT)\b', 1.5),
    (r'\btemperature\b.*\b(?:range|operating|junction)\b', 1.5),
    (r'\bfeedback\b', 1.5),
    (r'\benable\b.*\bpin\b', 1.0),
    (r'\bschematic\b', 1.0),
    (r'\bthreshold\b', 1.0),
]

# Category-specific bonus keywords
_CATEGORY_KEYWORDS = {
    "operational_amplifier": [
        (r'\bgain[- ]?bandwidth\b', 3.0),
        (r'\bslew\s+rate\b', 3.0),
        (r'\binput\s+offset\b', 2.5),
        (r'\bopen[- ]?loop\s+gain\b', 2.5),
        (r'\brail[- ]?to[- ]?rail\b', 2.0),
    ],
    "linear_regulator": [
        (r'\bdropout\b', 3.0),
        (r'\bquiescent\s+current\b', 3.0),
        (r'\boutput\s+capacitor\b', 2.5),
        (r'\binput\s+capacitor\b', 2.5),
    ],
    "switching_regulator": [
        (r'\bswitching\s+frequency\b', 3.0),
        (r'\binductor\s+selection\b', 3.0),
        (r'\bfeedback\s+divider\b', 3.0),
        (r'\bcompensation\b', 2.5),
        (r'\befficiency\b', 2.0),
        (r'\binput\s+capacitor\b', 2.5),
        (r'\boutput\s+capacitor\b', 2.5),
    ],
    "microcontroller": [
        (r'\bgpio\b', 2.5),
        (r'\balternate\s+function\b', 2.5),
        (r'\bperipheral\b', 2.0),
        (r'\bboot\s+(?:mode|strap|config)\b', 3.0),
        (r'\breset\b.*\bcircuit\b', 2.5),
        (r'\bpower\s+(?:supply|consumption|domain)\b', 2.5),
        (r'\bdecoupling\b', 2.0),
    ],
    "esd_protection": [
        (r'\bclamping\s+voltage\b', 3.0),
        (r'\bleakage\b', 2.5),
        (r'\bcapacitance\b', 2.5),
        (r'\bprotection\b', 2.0),
    ],
}


# ---------------------------------------------------------------------------
# PDF text extraction helpers
# ---------------------------------------------------------------------------

def _has_pdftotext():
    """Check if pdftotext is available."""
    return shutil.which("pdftotext") is not None


def _has_pdfinfo():
    """Check if pdfinfo is available."""
    return shutil.which("pdfinfo") is not None


def _get_page_count(pdf_path):
    """Get total number of pages in a PDF.

    Tries pdfinfo first, falls back to byte scanning.
    """
    pdf_path = str(pdf_path)

    if _has_pdfinfo():
        try:
            result = subprocess.run(
                ["pdfinfo", pdf_path],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                m = re.search(r'Pages:\s+(\d+)', result.stdout)
                if m:
                    return int(m.group(1))
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Fallback: count /Type /Page objects in raw PDF bytes
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
        # Count /Type /Page (not /Type /Pages) — rough estimate
        count = len(re.findall(rb'/Type\s*/Page(?!\s*s)', content))
        return max(count, 1)
    except OSError:
        return 0


def _extract_page_text(pdf_path, page_num):
    """Extract text from a single PDF page.

    Args:
        pdf_path: Path to PDF file
        page_num: 1-based page number

    Returns:
        Extracted text string, or "" if extraction fails
    """
    if not _has_pdftotext():
        return ""

    try:
        result = subprocess.run(
            ["pdftotext", "-f", str(page_num), "-l", str(page_num),
             str(pdf_path), "-"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError):
        return ""


def _extract_pages_text(pdf_path, first_page=1, last_page=None):
    """Extract text from a range of PDF pages.

    Args:
        pdf_path: Path to PDF file
        first_page: First page (1-based)
        last_page: Last page (1-based), or None for all

    Returns:
        Dict mapping page_number -> text
    """
    if not _has_pdftotext():
        return {}

    total = _get_page_count(pdf_path)
    if last_page is None:
        last_page = total

    # Extract all requested pages at once (faster than per-page)
    try:
        result = subprocess.run(
            ["pdftotext", "-f", str(first_page), "-l", str(last_page),
             "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {}
    except (subprocess.TimeoutExpired, OSError):
        return {}

    # Split on form-feed characters (pdftotext page delimiter)
    pages_text = result.stdout.split("\f")
    page_map = {}
    for i, text in enumerate(pages_text):
        page_num = first_page + i
        if page_num <= last_page:
            page_map[page_num] = text
    return page_map


# ---------------------------------------------------------------------------
# TOC detection
# ---------------------------------------------------------------------------

def _find_toc_pages(page_texts, max_scan_pages=3):
    """Scan early pages for table of contents references.

    Looks for section headings with page numbers in the first few pages.

    Args:
        page_texts: Dict of page_number -> text
        max_scan_pages: How many pages to scan for TOC

    Returns:
        Dict of page_number -> reason (sections found via TOC)
    """
    toc_pages = {}

    for page_num in sorted(page_texts.keys())[:max_scan_pages]:
        text = page_texts.get(page_num, "")
        if not text:
            continue

        for pattern, reason, priority in _TOC_PATTERNS:
            # Look for pattern followed by dots/spaces and a page number
            toc_re = re.compile(
                pattern + r'[\s.…·\-_]*(\d{1,3})',
                re.IGNORECASE | re.MULTILINE,
            )
            for m in toc_re.finditer(text):
                try:
                    target_page = int(m.group(1))
                    if target_page > 0:
                        toc_pages[target_page] = reason
                except (ValueError, IndexError):
                    pass

    return toc_pages


# ---------------------------------------------------------------------------
# Keyword-based page scoring (fallback)
# ---------------------------------------------------------------------------

def _score_page(text, category=""):
    """Score a page's relevance based on keyword density.

    Args:
        text: Page text content
        category: Component category for bonus keywords

    Returns:
        Float score (higher = more relevant)
    """
    if not text or len(text.strip()) < 50:
        return 0.0

    text_lower = text.lower()
    score = 0.0

    for pattern, weight in _KEYWORD_SCORES:
        matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
        score += min(matches, 3) * weight  # cap per-pattern contribution

    # Category-specific bonus
    category_kws = _CATEGORY_KEYWORDS.get(category, [])
    for pattern, weight in category_kws:
        matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
        score += min(matches, 3) * weight

    return score


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def suggest_pages(pdf_path, mpn="", category="", max_pages=None):
    """Select the most relevant pages from a datasheet PDF.

    Uses a multi-strategy approach:
    1. Extract text from early pages, look for table of contents
    2. If TOC found, use referenced page numbers
    3. If no TOC, score all pages by keyword density
    4. Always include page 1 (front page) and last page (package/ordering)

    Args:
        pdf_path: Path to the PDF file
        mpn: Manufacturer part number (for context)
        category: Component category (for targeted keyword scoring)
        max_pages: Maximum pages to select (default: category-dependent)

    Returns:
        PageSelection with pages, reasons, confidence, total_pages
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return PageSelection(confidence="error")

    total_pages = _get_page_count(pdf_path)
    if total_pages == 0:
        return PageSelection(confidence="error")

    if max_pages is None:
        max_pages = _PAGE_LIMITS.get(category, _PAGE_LIMITS["default"])

    # For short datasheets, just return all pages
    if total_pages <= max_pages:
        pages = list(range(1, total_pages + 1))
        reasons = {p: "all pages (short datasheet)" for p in pages}
        return PageSelection(
            pages=pages, reasons=reasons,
            confidence="all_pages", total_pages=total_pages,
        )

    # Check if pdftotext is available
    if not _has_pdftotext():
        # No text extraction available — return front pages + even distribution
        pages = _fallback_page_selection(total_pages, max_pages)
        reasons = {p: "fallback (no pdftotext)" for p in pages}
        return PageSelection(
            pages=pages, reasons=reasons,
            confidence="fallback", total_pages=total_pages,
        )

    # Strategy 1: Extract text from all pages
    page_texts = _extract_pages_text(pdf_path, 1, total_pages)
    if not page_texts:
        pages = _fallback_page_selection(total_pages, max_pages)
        reasons = {p: "fallback (extraction failed)" for p in pages}
        return PageSelection(
            pages=pages, reasons=reasons,
            confidence="fallback", total_pages=total_pages,
        )

    # Strategy 2: Look for TOC in first 3 pages
    toc_pages = _find_toc_pages(page_texts, max_scan_pages=3)

    if toc_pages:
        # TOC found — use referenced pages
        selected = {}
        selected[1] = "front page"

        for page_num, reason in toc_pages.items():
            if 1 <= page_num <= total_pages:
                selected[page_num] = f"TOC: {reason}"
                # Also include the next page (tables often span 2 pages)
                if page_num + 1 <= total_pages:
                    selected[page_num + 1] = f"continuation of {reason}"

        # Add last page if not already included
        if total_pages not in selected:
            selected[total_pages] = "last page (package/ordering)"

        # If still under budget, fill with keyword-scored pages
        if len(selected) < max_pages:
            scored = [(p, _score_page(t, category)) for p, t in page_texts.items()
                      if p not in selected]
            scored.sort(key=lambda x: x[1], reverse=True)
            for p, s in scored:
                if len(selected) >= max_pages:
                    break
                if s > 3.0:  # only add pages with meaningful content
                    selected[p] = f"keyword scored ({s:.1f})"

        pages = sorted(selected.keys())[:max_pages]
        reasons = {p: selected[p] for p in pages}
        return PageSelection(
            pages=pages, reasons=reasons,
            confidence="toc_found", total_pages=total_pages,
        )

    # Strategy 3: No TOC found — score all pages by keywords
    page_scores = [(p, _score_page(t, category)) for p, t in page_texts.items()]
    page_scores.sort(key=lambda x: x[1], reverse=True)

    selected = {}
    selected[1] = "front page"

    for page_num, score in page_scores:
        if len(selected) >= max_pages - 1:  # reserve 1 for last page
            break
        if page_num not in selected and score > 1.0:
            selected[page_num] = f"keyword scored ({score:.1f})"

    # Always include last page
    if total_pages not in selected and len(selected) < max_pages:
        selected[total_pages] = "last page (package/ordering)"

    pages = sorted(selected.keys())[:max_pages]
    reasons = {p: selected[p] for p in pages}
    return PageSelection(
        pages=pages, reasons=reasons,
        confidence="keyword_scored", total_pages=total_pages,
    )


def _fallback_page_selection(total_pages, max_pages):
    """Generate a fallback page selection without text extraction.

    Includes page 1, pages 2-5 (usually contain pin/spec tables),
    and evenly distributed pages through the rest.

    Args:
        total_pages: Total number of pages in the PDF
        max_pages: Maximum pages to return

    Returns:
        Sorted list of page numbers
    """
    pages = set()
    pages.add(1)

    # Front matter (usually has pin tables, abs max, etc.)
    for p in range(2, min(6, total_pages + 1)):
        pages.add(p)

    # Last page
    pages.add(total_pages)

    # If we need more, distribute evenly through remaining pages
    if len(pages) < max_pages:
        remaining = [p for p in range(6, total_pages) if p not in pages]
        step = max(1, len(remaining) // (max_pages - len(pages)))
        for i in range(0, len(remaining), step):
            if len(pages) >= max_pages:
                break
            pages.add(remaining[i])

    return sorted(pages)[:max_pages]

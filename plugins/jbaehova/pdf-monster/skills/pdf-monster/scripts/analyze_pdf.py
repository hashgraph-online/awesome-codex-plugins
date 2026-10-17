#!/usr/bin/env python3
"""Extract agent-readable evidence from a PDF without polluting the cwd."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_COMMAND_TIMEOUT_SECONDS = 120


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def run_command(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            args=args,
            returncode=124,
            stdout=decode_timeout_output(exc.stdout),
            stderr=f"{args[0]} timed out after {timeout} seconds",
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def truncate_text(text: str, limit: int) -> tuple[str, bool]:
    if limit <= 0 or len(text) <= limit:
        return text, False
    return text[:limit], True


def image_dimensions_from_pymupdf_info(image_info: tuple[Any, ...]) -> tuple[int | None, int | None]:
    if len(image_info) < 4:
        return None, None
    width = image_info[2] if isinstance(image_info[2], int) else None
    height = image_info[3] if isinstance(image_info[3], int) else None
    return width, height


def image_area(width: int | None, height: int | None) -> int | None:
    if width is None or height is None:
        return None
    return width * height


def image_meets_area_threshold(width: int | None, height: int | None, threshold: int) -> bool:
    if threshold <= 0:
        return True
    area = image_area(width, height)
    return area is None or area >= threshold


def count_new_significant_images(
    image_infos: list[tuple[Any, ...]],
    threshold: int,
    seen_xrefs: set[int],
) -> int:
    count = 0
    for image_info in image_infos:
        xref = image_info[0] if image_info else None
        if not isinstance(xref, int) or xref in seen_xrefs:
            continue
        if image_meets_area_threshold(
            *image_dimensions_from_pymupdf_info(image_info),
            threshold,
        ):
            seen_xrefs.add(xref)
            count += 1
    return count


def parse_page_spec(spec: str, page_count: int) -> list[int]:
    if spec in {"all", ""}:
        return list(range(1, page_count + 1))

    pages: set[int] = set()
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if re.fullmatch(r"\d+", part):
            pages.add(int(part))
            continue
        match = re.fullmatch(r"(\d+)-(\d+)", part)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            if start > end:
                raise ValueError(f"Invalid page range: {part}")
            pages.update(range(start, end + 1))
            continue
        raise ValueError(f"Invalid page selector: {part}")

    invalid = [page for page in sorted(pages) if page < 1 or page > page_count]
    if invalid:
        raise ValueError(
            f"Page selector contains out-of-range pages {invalid}; PDF has {page_count} pages"
        )
    return sorted(pages)


class ArtifactStore:
    def __init__(self, save_to: str | None) -> None:
        self._save_to = Path(save_to).expanduser().resolve() if save_to else None
        self.root: Path | None = None
        self.policy = "none"

    def ensure(self) -> Path:
        if self.root is not None:
            return self.root
        if self._save_to:
            self.root = self._save_to
            self.root.mkdir(parents=True, exist_ok=True)
            self.policy = "persistent"
        else:
            self.root = Path(tempfile.mkdtemp(prefix="pdf-monster-")).resolve()
            self.policy = "temporary"
        return self.root

    def path(self, *parts: str) -> Path:
        root = self.ensure()
        target = root.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def cleanup_command(self) -> str | None:
        if self.root is None or self.policy != "temporary":
            return None
        return f"rm -rf -- {shlex.quote(str(self.root))}"


def import_pymupdf() -> Any | None:
    try:
        import fitz  # type: ignore

        return fitz
    except Exception:
        return None


def open_pymupdf_document(fitz: Any, pdf_path: Path, password: str | None) -> Any:
    doc = fitz.open(str(pdf_path))
    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            doc.close()
            raise RuntimeError("PDF is encrypted and requires a valid password")
    return doc


def poppler_password_args(password: str | None) -> list[str]:
    return ["-upw", password] if password else []


def get_page_count_with_poppler(pdf_path: Path, password: str | None, timeout: int) -> int:
    if not command_exists("pdfinfo"):
        raise RuntimeError("Cannot determine page count: PyMuPDF and pdfinfo are unavailable")
    result = run_command(["pdfinfo", *poppler_password_args(password), str(pdf_path)], timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pdfinfo failed")
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError("pdfinfo output did not include page count")


def extract_text_with_poppler(
    pdf_path: Path,
    page: int,
    password: str | None,
    timeout: int,
) -> tuple[str, str | None]:
    if not command_exists("pdftotext"):
        return "", "pdftotext is unavailable"
    args = [
        "pdftotext",
        *poppler_password_args(password),
        "-f",
        str(page),
        "-l",
        str(page),
        "-layout",
        str(pdf_path),
        "-",
    ]
    result = run_command(args, timeout)
    if result.returncode != 0:
        return "", result.stderr.strip() or "pdftotext failed"
    return result.stdout, None


def render_page_with_poppler(
    pdf_path: Path,
    page: int,
    dpi: int,
    password: str | None,
    store: ArtifactStore,
    timeout: int,
) -> tuple[str | None, str | None]:
    if not command_exists("pdftoppm"):
        return None, "pdftoppm is unavailable"
    target = store.path("renders", f"page-{page:03d}")
    args = [
        "pdftoppm",
        *poppler_password_args(password),
        "-png",
        "-singlefile",
        "-r",
        str(dpi),
        "-f",
        str(page),
        "-l",
        str(page),
        str(pdf_path),
        str(target),
    ]
    result = run_command(args, timeout)
    if result.returncode != 0:
        return None, result.stderr.strip() or "pdftoppm failed"
    render_path = target.with_suffix(".png")
    if not render_path.exists():
        return None, f"pdftoppm did not create {render_path}"
    return str(render_path), None


def extract_images_with_poppler(
    pdf_path: Path,
    page: int,
    password: str | None,
    store: ArtifactStore,
    remaining: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    if remaining <= 0:
        return [], ["image limit reached"]
    if not command_exists("pdfimages"):
        return [], ["pdfimages is unavailable"]

    prefix = store.path("images", f"page-{page:03d}-img")
    before = set(glob.glob(str(prefix) + "*"))
    args = [
        "pdfimages",
        *poppler_password_args(password),
        "-png",
        "-f",
        str(page),
        "-l",
        str(page),
        str(pdf_path),
        str(prefix),
    ]
    result = run_command(args, timeout)
    warnings: list[str] = []
    if result.returncode != 0:
        return [], [result.stderr.strip() or "pdfimages failed"]

    after = sorted(set(glob.glob(str(prefix) + "*")) - before)
    records: list[dict[str, Any]] = []
    for index, path in enumerate(after[:remaining], start=1):
        records.append({"index": index, "path": path, "source": "pdfimages"})
    if len(after) > remaining:
        warnings.append("image limit reached")
    return records, warnings


def render_page_with_pymupdf(
    page_obj: Any,
    page_number: int,
    dpi: int,
    store: ArtifactStore,
) -> str:
    import fitz  # type: ignore

    target = store.path("renders", f"page-{page_number:03d}.png")
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page_obj.get_pixmap(matrix=matrix, alpha=False)
    pix.save(str(target))
    return str(target)


def extract_images_with_pymupdf(
    doc: Any,
    page_obj: Any,
    page_number: int,
    store: ArtifactStore,
    remaining: int,
    min_image_area: int,
    dedupe_images: bool,
    seen_image_xrefs: set[int],
) -> tuple[list[dict[str, Any]], list[str]]:
    if remaining <= 0:
        return [], ["image limit reached"]

    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    for image_index, image_info in enumerate(page_obj.get_images(full=True), start=1):
        xref = image_info[0]
        if dedupe_images and xref in seen_image_xrefs:
            continue
        width, height = image_dimensions_from_pymupdf_info(image_info)
        if not image_meets_area_threshold(width, height, min_image_area):
            continue
        if len(records) >= remaining:
            warnings.append("image limit reached")
            break
        try:
            image = doc.extract_image(xref)
        except Exception as exc:
            warnings.append(f"could not extract image {image_index}: {exc}")
            continue
        seen_image_xrefs.add(xref)
        ext = image.get("ext") or "bin"
        target = store.path("images", f"page-{page_number:03d}-img-{image_index:03d}.{ext}")
        target.write_bytes(image["image"])
        records.append(
            {
                "index": image_index,
                "path": str(target),
                "xref": xref,
                "width": image.get("width"),
                "height": image.get("height"),
                "colorspace": image.get("colorspace"),
                "source": "pymupdf",
            }
        )
    return records, warnings


def run_ocr(render_path: str, language: str, timeout: int) -> tuple[str, str | None]:
    if not command_exists("tesseract"):
        return "", "tesseract is unavailable"
    args = ["tesseract", render_path, "stdout", "-l", language]
    result = run_command(args, timeout)
    if result.returncode != 0:
        return "", result.stderr.strip() or "tesseract failed"
    return result.stdout, None


def wants_page_from_selector(selector: str, page: int, text_chars: int, image_count: int, threshold: int) -> bool:
    if selector == "none":
        return False
    if selector == "all":
        return True
    if selector == "auto":
        return text_chars < threshold or image_count > 0
    # page selector mode is validated by parse_page_spec in main.
    return False


def visual_review_reasons(
    text_chars: int,
    text_truncated: bool,
    should_ocr: bool,
    new_significant_image_count: int,
    ocr_threshold: int,
) -> list[str]:
    reasons: list[str] = []
    if text_chars < ocr_threshold:
        reasons.append("sparse_text")
    if text_truncated:
        reasons.append("text_truncated")
    if should_ocr:
        reasons.append("ocr_attempted")
    if new_significant_image_count > 0:
        reasons.append(f"new_significant_embedded_images:{new_significant_image_count}")
    return reasons


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract PDF text, OCR text, page renders, and embedded images for agents.",
    )
    parser.add_argument("pdf", help="PDF file to analyze")
    parser.add_argument("--password", help="Password for encrypted PDFs")
    parser.add_argument("--pages", default="all", help="Pages to process, e.g. all, 1, 1,3-5")
    parser.add_argument(
        "--render-pages",
        default="auto",
        help="Pages to render: auto, all, none, or a selector such as 1,3-5",
    )
    parser.add_argument("--dpi", type=int, default=144, help="DPI for page renders")
    parser.add_argument(
        "--ocr",
        choices=["auto", "always", "never"],
        default="auto",
        help="OCR mode. OCR requires tesseract.",
    )
    parser.add_argument("--ocr-lang", default="eng", help="Tesseract language code")
    parser.add_argument(
        "--ocr-threshold",
        type=int,
        default=80,
        help="Run auto OCR when extracted page text has fewer characters than this",
    )
    parser.add_argument("--extract-images", dest="extract_images", action="store_true", default=True)
    parser.add_argument("--no-extract-images", dest="extract_images", action="store_false")
    parser.add_argument(
        "--dedupe-images",
        action="store_true",
        help="Skip repeated PyMuPDF image xrefs after the first extracted copy",
    )
    parser.add_argument(
        "--image-limit",
        type=int,
        default=200,
        help="Maximum embedded images to extract across selected pages",
    )
    parser.add_argument(
        "--min-image-area",
        type=int,
        default=0,
        help="Skip embedded images smaller than this width*height pixel area when PyMuPDF is used",
    )
    parser.add_argument(
        "--visual-review-image-area",
        type=int,
        default=10000,
        help="Mark a page for visual review when it contains new embedded images at least this large",
    )
    parser.add_argument(
        "--max-page-text-chars",
        type=int,
        default=20000,
        help="Truncate each extracted text field to this many characters. Use 0 for unlimited.",
    )
    parser.add_argument("--save-to", help="Persist image artifacts in this directory")
    parser.add_argument("--write-manifest", action="store_true", help="Also write manifest.json to artifact root")
    parser.add_argument(
        "--command-timeout",
        type=int,
        default=DEFAULT_COMMAND_TIMEOUT_SECONDS,
        help="Seconds to wait for each external Poppler/Tesseract command",
    )
    parser.add_argument("--json", action="store_true", help="Accepted for compatibility; JSON is always emitted.")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    if args.dpi <= 0:
        raise RuntimeError("--dpi must be greater than 0")
    if args.image_limit < 0:
        raise RuntimeError("--image-limit must be 0 or greater")
    if args.min_image_area < 0:
        raise RuntimeError("--min-image-area must be 0 or greater")
    if args.visual_review_image_area < 0:
        raise RuntimeError("--visual-review-image-area must be 0 or greater")
    if args.ocr_threshold < 0:
        raise RuntimeError("--ocr-threshold must be 0 or greater")
    if args.command_timeout <= 0:
        raise RuntimeError("--command-timeout must be greater than 0")

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise RuntimeError(f"PDF does not exist: {pdf_path}")
    if not pdf_path.is_file():
        raise RuntimeError(f"PDF path is not a file: {pdf_path}")

    fitz = import_pymupdf()
    warnings: list[str] = []
    backend = {
        "pymupdf": bool(fitz),
        "pdftotext": command_exists("pdftotext"),
        "pdfinfo": command_exists("pdfinfo"),
        "pdftoppm": command_exists("pdftoppm"),
        "pdfimages": command_exists("pdfimages"),
        "tesseract": command_exists("tesseract"),
    }

    doc = None
    try:
        if fitz:
            doc = open_pymupdf_document(fitz, pdf_path, args.password)
            page_count = doc.page_count
        else:
            warnings.append("PyMuPDF is unavailable; using Poppler CLI fallbacks")
            page_count = get_page_count_with_poppler(pdf_path, args.password, args.command_timeout)

        selected_pages = parse_page_spec(args.pages, page_count)
        render_selector_pages: set[int] | None = None
        if args.render_pages not in {"auto", "all", "none"}:
            render_selector_pages = set(parse_page_spec(args.render_pages, page_count))

        store = ArtifactStore(args.save_to)
        extracted_images_total = 0
        seen_image_xrefs: set[int] = set()
        seen_visual_review_xrefs: set[int] = set()
        page_records: list[dict[str, Any]] = []

        for page_number in selected_pages:
            page_warnings: list[str] = []
            raw_text = ""
            image_count_hint = 0
            new_significant_image_count = 0
            page_obj = None

            if doc is not None:
                page_obj = doc.load_page(page_number - 1)
                raw_text = page_obj.get_text("text", sort=True) or ""
                page_images = page_obj.get_images(full=True)
                image_count_hint = len(page_images)
                new_significant_image_count = count_new_significant_images(
                    page_images,
                    args.visual_review_image_area,
                    seen_visual_review_xrefs,
                )
            else:
                raw_text, warning = extract_text_with_poppler(
                    pdf_path, page_number, args.password, args.command_timeout
                )
                if warning:
                    page_warnings.append(warning)

            page_text, text_truncated = truncate_text(raw_text, args.max_page_text_chars)
            text_chars = len(raw_text)

            embedded_images: list[dict[str, Any]] = []
            if args.extract_images and args.image_limit > extracted_images_total:
                remaining = args.image_limit - extracted_images_total
                if doc is not None and page_obj is not None:
                    embedded_images, image_warnings = extract_images_with_pymupdf(
                        doc,
                        page_obj,
                        page_number,
                        store,
                        remaining,
                        args.min_image_area,
                        args.dedupe_images,
                        seen_image_xrefs,
                    )
                else:
                    if args.min_image_area > 0:
                        page_warnings.append("--min-image-area is ignored without PyMuPDF")
                    embedded_images, image_warnings = extract_images_with_poppler(
                        pdf_path, page_number, args.password, store, remaining, args.command_timeout
                    )
                extracted_images_total += len(embedded_images)
                page_warnings.extend(image_warnings)
                if doc is None:
                    new_significant_image_count = len(embedded_images)

            if args.render_pages in {"auto", "all", "none"}:
                should_render = wants_page_from_selector(
                    args.render_pages,
                    page_number,
                    text_chars,
                    image_count_hint + len(embedded_images),
                    args.ocr_threshold,
                )
            else:
                should_render = page_number in (render_selector_pages or set())

            should_ocr = args.ocr == "always" or (args.ocr == "auto" and text_chars < args.ocr_threshold)
            if should_ocr:
                should_render = True

            render_path = None
            if should_render:
                if doc is not None and page_obj is not None:
                    try:
                        render_path = render_page_with_pymupdf(page_obj, page_number, args.dpi, store)
                    except Exception as exc:
                        page_warnings.append(f"page render failed: {exc}")
                else:
                    render_path, warning = render_page_with_poppler(
                        pdf_path, page_number, args.dpi, args.password, store, args.command_timeout
                    )
                    if warning:
                        page_warnings.append(warning)

            raw_ocr_text = ""
            ocr_text = ""
            ocr_text_truncated = False
            if should_ocr:
                if render_path:
                    raw_ocr_text, warning = run_ocr(render_path, args.ocr_lang, args.command_timeout)
                    if warning:
                        page_warnings.append(warning)
                    ocr_text, ocr_text_truncated = truncate_text(raw_ocr_text, args.max_page_text_chars)
                else:
                    page_warnings.append("OCR skipped because no page render is available")

            page_visual_review_reasons = visual_review_reasons(
                text_chars,
                text_truncated,
                should_ocr,
                new_significant_image_count,
                args.ocr_threshold,
            )

            page_records.append(
                {
                    "page": page_number,
                    "text": page_text,
                    "text_chars": text_chars,
                    "text_truncated": text_truncated,
                    "ocr_text": ocr_text,
                    "ocr_text_chars": len(raw_ocr_text),
                    "ocr_text_truncated": ocr_text_truncated,
                    "render_path": render_path,
                    "embedded_images": embedded_images,
                    "needs_visual_review": bool(page_visual_review_reasons),
                    "visual_review_reasons": page_visual_review_reasons,
                    "warnings": page_warnings,
                }
            )
    finally:
        if doc is not None:
            doc.close()

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "pdf_path": str(pdf_path),
        "pdf_name": pdf_path.name,
        "sha256": sha256_file(pdf_path),
        "page_count": page_count,
        "selected_pages": selected_pages,
        "backend": backend,
        "artifact_root": str(store.root) if store.root else None,
        "artifact_policy": store.policy,
        "cleanup_command": store.cleanup_command(),
        "pages_needing_visual_review": [
            page_record["page"]
            for page_record in page_records
            if page_record["needs_visual_review"]
        ],
        "pages": page_records,
        "warnings": warnings,
    }

    if args.write_manifest:
        manifest_path = store.path("manifest.json")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["manifest_path"] = str(manifest_path)

    return manifest


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        manifest = analyze(args)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    indent = None if args.compact else 2
    print(json.dumps(manifest, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

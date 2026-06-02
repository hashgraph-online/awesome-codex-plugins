#!/bin/sh

course_die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

course_script_dir=$(
  CDPATH= cd -- "$(dirname "$0")" && pwd
)
COURSE_SCRIPT_DIR=${COURSE_SCRIPT_DIR:-$course_script_dir}
COURSE_SKILL_DIR=${COURSE_SKILL_DIR:-$(
  CDPATH= cd -- "$COURSE_SCRIPT_DIR/.." && pwd
)}

course_require_file() {
  [ -f "$1" ] || course_die "required file is missing: $1"
}

course_require_dir() {
  [ -d "$1" ] || course_die "required directory is missing: $1"
}

course_resolve_path() {
  python3 - "$PWD" "$1" <<'PY'
from pathlib import Path
import sys

base = Path(sys.argv[1])
raw = Path(sys.argv[2]).expanduser()
if not raw.is_absolute():
    raw = base / raw
print(raw.resolve(strict=False))
PY
}

course_slugify() {
  slug=$(
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
  )
  if [ -z "$slug" ]; then
    slug=course
  fi
  printf '%s\n' "$slug"
}

course_titleize() {
  normalized=$(printf '%s' "$1" | tr '_-' '  ')
  normalized=$(printf '%s' "$normalized" | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//')

  if [ -z "$normalized" ]; then
    printf 'Course\n'
    return 0
  fi

  printf '%s\n' "$normalized" | awk '
    {
      for (i = 1; i <= NF; i++) {
        first = substr($i, 1, 1)
        rest = substr($i, 2)
        $i = toupper(first) tolower(rest)
      }
      print
    }
  '
}

course_derive_title_from_source() {
  source_dir=$1
  base_name=${source_dir##*/}
  if [ -z "$base_name" ] || [ "$base_name" = "/" ] || [ "$base_name" = "." ]; then
    base_name=course
  fi
  course_titleize "$base_name"
}

course_set_accent_palette() {
  palette=$1
  case "$palette" in
    vermillion)
      COURSE_ACCENT_COLOR='#D94F30'
      COURSE_ACCENT_HOVER='#C4432A'
      COURSE_ACCENT_LIGHT='#FDEEE9'
      COURSE_ACCENT_MUTED='#E8836C'
      ;;
    coral)
      COURSE_ACCENT_COLOR='#E06B56'
      COURSE_ACCENT_HOVER='#C85A47'
      COURSE_ACCENT_LIGHT='#FDECEA'
      COURSE_ACCENT_MUTED='#E89585'
      ;;
    teal)
      COURSE_ACCENT_COLOR='#2A7B9B'
      COURSE_ACCENT_HOVER='#1F6280'
      COURSE_ACCENT_LIGHT='#E4F2F7'
      COURSE_ACCENT_MUTED='#5A9DB8'
      ;;
    amber)
      COURSE_ACCENT_COLOR='#D4A843'
      COURSE_ACCENT_HOVER='#BF9530'
      COURSE_ACCENT_LIGHT='#FDF5E0'
      COURSE_ACCENT_MUTED='#E0C070'
      ;;
    forest)
      COURSE_ACCENT_COLOR='#2D8B55'
      COURSE_ACCENT_HOVER='#226B41'
      COURSE_ACCENT_LIGHT='#E8F5EE'
      COURSE_ACCENT_MUTED='#5AAD7A'
      ;;
    *)
      course_die "unsupported accent palette: $palette"
      ;;
  esac
}

course_find_runtime_asset() {
  asset_name=$1

  for relative_path in \
    "runtime/templates/$asset_name" \
    "references/$asset_name" \
    "runtime/$asset_name" \
    "templates/$asset_name" \
    "assets/$asset_name" \
    "$asset_name"
  do
    candidate=$COURSE_SKILL_DIR/$relative_path
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

course_copy_runtime_asset() {
  asset_name=$1
  destination=$2

  if asset_source=$(course_find_runtime_asset "$asset_name"); then
    cp "$asset_source" "$destination"
    return 0
  fi

  course_die "runtime asset not found in installed skill bundle: $asset_name"
}

course_prepare_base_template() {
  template_source=$1
  destination=$2
  course_title=$3
  source_name=$4
  accent_name=$5

  python3 - "$template_source" "$destination" "$course_title" "$source_name" "$accent_name" \
    "$COURSE_ACCENT_COLOR" "$COURSE_ACCENT_HOVER" "$COURSE_ACCENT_LIGHT" "$COURSE_ACCENT_MUTED" <<'PY'
from pathlib import Path
from html import escape
import re
import sys

source_path, destination_path, title, source_name, accent_name, accent, hover, light, muted = sys.argv[1:]
text = Path(source_path).read_text(encoding="utf-8")

page_description = f"Interactive course for understanding {title}."
course_dek = f"A local, browser-readable walkthrough of how {title} works and where to look next in the code."
course_meta = f"Source: {source_name} · Accent: {accent_name}"

if "{{PAGE_TITLE}}" in text:
    replacements = {
        "{{PAGE_LANG}}": "en",
        "{{PAGE_TITLE}}": escape(title),
        "{{PAGE_DESCRIPTION}}": escape(page_description),
        "{{RUNTIME_STYLESHEET}}": "styles.css",
        "{{HEAD_EXTRA}}": "",
        "{{BODY_CLASS}}": "",
        "{{COURSE_EYEBROW}}": "Codebase to Course",
        "{{COURSE_KICKER}}": "Guided Code Walkthrough",
        "{{COURSE_TITLE}}": escape(title),
        "{{COURSE_DEK}}": escape(course_dek),
        "{{COURSE_META}}": escape(course_meta),
    }

    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
else:
    filtered_lines = []
    for line in text.splitlines():
        if re.search(r'\b(?:href|src)\s*=\s*["\']https?://', line, re.IGNORECASE):
            continue
        if re.search(r'<link\b[^>]*\brel\s*=\s*["\']preconnect["\']', line, re.IGNORECASE):
            continue
        filtered_lines.append(line)

    newline = "\n" if text.endswith("\n") else ""
    text = "\n".join(filtered_lines) + newline

    replacements = {
        "COURSE_TITLE": title,
        "ACCENT_COLOR": accent,
        "ACCENT_HOVER": hover,
        "ACCENT_LIGHT": light,
        "ACCENT_MUTED": muted,
    }

    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    if not re.search(r'<link\b[^>]*href=["\']styles\.css["\']', text, re.IGNORECASE):
        text = text.replace("</head>", '  <link rel="stylesheet" href="styles.css">\n</head>', 1)

    if not re.search(r'<script\b[^>]*src=["\']main\.js["\']', text, re.IGNORECASE):
        text = text.replace("</head>", '  <script src="main.js" defer></script>\n</head>', 1)

Path(destination_path).write_text(text, encoding="utf-8")
PY
}

course_prepare_footer_template() {
  template_source=$1
  destination=$2
  source_name=$3

  python3 - "$template_source" "$destination" "$source_name" <<'PY'
from pathlib import Path
from html import escape
import sys

source_path, destination_path, source_name = sys.argv[1:]
text = Path(source_path).read_text(encoding="utf-8")

if "{{COURSE_APPENDIX}}" in text:
    replacements = {
        "{{COURSE_APPENDIX}}": "",
        "{{FOOTER_NOTE}}": "Built locally from the installed codebase-to-course runtime.",
        "{{FOOTER_META}}": escape(f"Source: {source_name}"),
        "{{RUNTIME_SCRIPT}}": "main.js",
        "{{BODY_END}}": "",
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

Path(destination_path).write_text(text, encoding="utf-8")
PY
}

course_patch_runtime_stylesheet() {
  stylesheet_path=$1

  python3 - "$stylesheet_path" "$COURSE_ACCENT_COLOR" "$COURSE_ACCENT_HOVER" "$COURSE_ACCENT_LIGHT" <<'PY'
from pathlib import Path
import re
import sys

stylesheet_path, accent, accent_deep, accent_soft = sys.argv[1:]
text = Path(stylesheet_path).read_text(encoding="utf-8")

def hex_to_rgba(hex_value: str, alpha: str) -> str:
    hex_value = hex_value.lstrip("#")
    if len(hex_value) != 6:
        raise ValueError(f"expected 6-digit hex color, got {hex_value!r}")
    red = int(hex_value[0:2], 16)
    green = int(hex_value[2:4], 16)
    blue = int(hex_value[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"

replacements = {
    "--accent": accent,
    "--accent-deep": accent_deep,
    "--accent-soft": accent_soft,
}

for token, value in replacements.items():
    pattern = re.compile(rf"({re.escape(token)}:\s*)#[0-9a-fA-F]{{3,8}}(\s*;)")
    text, _ = pattern.subn(rf"\1{value}\2", text, count=1)

rgba_replacements = {
    "rgba(143, 59, 24, 0.05)": hex_to_rgba(accent_deep, "0.05"),
    "rgba(197, 93, 45, 0.35)": hex_to_rgba(accent, "0.35"),
    "rgba(197, 93, 45, 0.24)": hex_to_rgba(accent, "0.24"),
    "rgba(143, 59, 24, 0.25)": hex_to_rgba(accent_deep, "0.25"),
    "rgba(143, 59, 24, 0.15)": hex_to_rgba(accent_deep, "0.15"),
    "rgba(197, 93, 45, 0.08)": hex_to_rgba(accent, "0.08"),
    "rgba(197, 93, 45, 0.3)": hex_to_rgba(accent, "0.3"),
    "rgba(197, 93, 45, 0.32)": hex_to_rgba(accent, "0.32"),
    "rgba(197, 93, 45, 0.28)": hex_to_rgba(accent, "0.28"),
    "rgba(243, 208, 189, 0.92)": hex_to_rgba(accent_soft, "0.92"),
    "rgba(243, 208, 189, 0.72)": hex_to_rgba(accent_soft, "0.72"),
    "rgba(243, 208, 189, 0.56)": hex_to_rgba(accent_soft, "0.56"),
    "rgba(243, 208, 189, 0.9)": hex_to_rgba(accent_soft, "0.9"),
    "rgba(243, 208, 189, 0.52)": hex_to_rgba(accent_soft, "0.52"),
}

for original, updated in rgba_replacements.items():
    text = text.replace(original, updated)

Path(stylesheet_path).write_text(text, encoding="utf-8")
PY
}

course_assemble_index() {
  course_dir=$1

  python3 - "$course_dir" <<'PY'
from pathlib import Path
from html import escape, unescape
import re
import sys

course_dir = Path(sys.argv[1])
base_path = course_dir / "_base.html"
footer_path = course_dir / "_footer.html"
modules_dir = course_dir / "modules"
index_path = course_dir / "index.html"

base = base_path.read_text(encoding="utf-8")
footer = footer_path.read_text(encoding="utf-8")
module_paths = sorted(
    [path for path in modules_dir.iterdir() if path.is_file() and path.suffix == ".html"],
    key=lambda path: path.name,
)

root_section_re = re.compile(r"^\s*(?:<!--.*?-->\s*)*<section\b([^>]*)>", re.IGNORECASE | re.DOTALL)
id_attr_re = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
data_title_re = re.compile(r'\bdata-title\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
heading_re = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
tag_re = re.compile(r"<[^>]+>")

nav_dots = []
module_chunks = []
seen_ids = set()

for index, module_path in enumerate(module_paths, start=1):
    content = module_path.read_text(encoding="utf-8")
    module_chunks.append(content.rstrip() + "\n")

    root_section_match = root_section_re.match(content)
    if root_section_match is None:
        print(
            f"ERROR: module file must start with a root <section id=\"...\"> element: {module_path}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    section_attrs = root_section_match.group(1)
    id_match = id_attr_re.search(section_attrs)
    if id_match is None:
        print(
            f"ERROR: module root <section> is missing the required id attribute: {module_path}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    module_id = id_match.group(1).strip()
    if not module_id:
        print(
            f"ERROR: module root <section> has an empty id attribute: {module_path}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if module_id in seen_ids:
        print(
            f"ERROR: duplicate module id found: {module_id} ({module_path})",
            file=sys.stderr,
        )
        raise SystemExit(1)

    seen_ids.add(module_id)
    section_tag = root_section_match.group(0)
    data_title_match = data_title_re.search(section_tag)
    if data_title_match is not None:
        module_title = data_title_match.group(1).strip()
    else:
        heading_match = heading_re.search(content)
        if heading_match is not None:
            module_title = unescape(tag_re.sub("", heading_match.group(2))).strip()
        else:
            stem = module_path.stem.replace("-", " ").replace("_", " ").strip()
            module_title = " ".join(word.capitalize() for word in stem.split()) or f"Module {index}"

    nav_dots.append(
        '        <button class="nav-dot" data-target="{target}" data-tooltip="{tooltip}" role="tab" aria-label="Module {number}: {label}"></button>'.format(
            target=escape(module_id, quote=True),
            tooltip=escape(module_title, quote=True),
            number=index,
            label=escape(module_title, quote=True),
        )
    )

if "{{COURSE_CONTENT}}" in base:
    assembled_base = base.replace("{{COURSE_CONTENT}}", "".join(module_chunks).rstrip())
    assembled = assembled_base.rstrip() + "\n" + footer.lstrip()
else:
    assembled_base = base
    assembled = assembled_base.rstrip() + "\n" + "".join(module_chunks) + footer.lstrip()

if "NAV_DOTS" in assembled_base:
    assembled_base = assembled_base.replace("NAV_DOTS", "\n".join(nav_dots))
    if "{{COURSE_CONTENT}}" in base:
        assembled = assembled_base.rstrip() + "\n" + footer.lstrip()
    else:
        assembled = assembled_base.rstrip() + "\n" + "".join(module_chunks) + footer.lstrip()
assembled = assembled.replace("{{COURSE_APPENDIX}}", "")

for placeholder in (
    "{{HEAD_EXTRA}}",
    "{{BODY_END}}",
    "{{BODY_CLASS}}",
    "{{COURSE_META}}",
    "{{FOOTER_META}}",
):
    assembled = assembled.replace(placeholder, "")

if "{{COURSE_CONTENT}}" in assembled:
    assembled = assembled.replace("{{COURSE_CONTENT}}", "".join(module_chunks).rstrip())

if "{{RUNTIME_STYLESHEET}}" in assembled:
    assembled = assembled.replace("{{RUNTIME_STYLESHEET}}", "styles.css")

if "{{RUNTIME_SCRIPT}}" in assembled:
    assembled = assembled.replace("{{RUNTIME_SCRIPT}}", "main.js")

if "{{PAGE_TITLE}}" in assembled:
    assembled = assembled.replace("{{PAGE_TITLE}}", "Codebase Course")

if "{{PAGE_DESCRIPTION}}" in assembled:
    assembled = assembled.replace("{{PAGE_DESCRIPTION}}", "Interactive codebase course.")

if "{{PAGE_LANG}}" in assembled:
    assembled = assembled.replace("{{PAGE_LANG}}", "en")

if "{{COURSE_TITLE}}" in assembled:
    assembled = assembled.replace("{{COURSE_TITLE}}", "Codebase Course")

if "{{COURSE_DEK}}" in assembled:
    assembled = assembled.replace("{{COURSE_DEK}}", "")

if "{{COURSE_EYEBROW}}" in assembled:
    assembled = assembled.replace("{{COURSE_EYEBROW}}", "Codebase to Course")

if "{{COURSE_KICKER}}" in assembled:
    assembled = assembled.replace("{{COURSE_KICKER}}", "Guided Code Walkthrough")

if "{{FOOTER_NOTE}}" in assembled:
    assembled = assembled.replace("{{FOOTER_NOTE}}", "Built locally from the installed codebase-to-course runtime.")

if "{{COURSE_APPENDIX}}" in assembled:
    assembled = assembled.replace("{{COURSE_APPENDIX}}", "")

if re.search(r"\{\{[A-Z][A-Z0-9_]*\}\}", assembled):
    print("ERROR: assembled index.html still contains unresolved template placeholders", file=sys.stderr)
    raise SystemExit(1)

link_tags = re.findall(r"<link\b[^>]*href=['\"]([^'\"]+)['\"][^>]*>", assembled, re.IGNORECASE)
for href in link_tags:
    if href != "styles.css":
        print(
            f"ERROR: assembled index.html must only reference local styles.css via <link>, found: {href}",
            file=sys.stderr,
        )
        raise SystemExit(1)

script_tags = re.findall(r"<script\b[^>]*src=['\"]([^'\"]+)['\"][^>]*>", assembled, re.IGNORECASE)
for src in script_tags:
    if src != "main.js":
        print(
            f"ERROR: assembled index.html must only reference local main.js via <script>, found: {src}",
            file=sys.stderr,
        )
        raise SystemExit(1)

if "styles.css" not in link_tags:
    print("ERROR: assembled index.html is missing the local styles.css reference", file=sys.stderr)
    raise SystemExit(1)

if "main.js" not in script_tags:
    print("ERROR: assembled index.html is missing the local main.js reference", file=sys.stderr)
    raise SystemExit(1)

index_path.write_text(assembled, encoding="utf-8")
print(f"Built {index_path} from {len(module_paths)} module(s)")
PY
}

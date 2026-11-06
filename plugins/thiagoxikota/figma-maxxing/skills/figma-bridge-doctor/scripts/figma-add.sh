#!/usr/bin/env bash
# figma-add.sh: register a Figma URL into the alias registry.
#
#   bash figma-add.sh <figma-url> [alias] [label]
#   bash figma-add.sh "https://www.figma.com/design/<fileKey>/My-App" myapp
#   bash figma-add.sh "https://www.figma.com/design/<fileKey>/My-App"
#
# - URL required. Must be figma.com/(design|board|file)/<fileKey>/<name>.
# - alias optional: defaults to first word of slugified URL filename.
# - label optional: defaults to URL filename with dashes/underscores -> spaces.
# Sets validated=null. After the first open via figma-open.sh, confirm with the
# user that the right file opened, then set validated to that date in the registry.
# Idempotent: adding the same alias again updates the entry.
#
# The registry is <state-dir>/figma-files.json, where <state-dir> is
# ${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}. It is created as an
# empty JSON object on first run. Only bash and python3 are used here: this
# script never opens Figma and never touches a running process.

set -u

URL="${1:-}"
ALIAS_ARG="${2:-}"
LABEL_ARG="${3:-}"

if [ -z "$URL" ]; then
  echo "Usage: bash figma-add.sh <figma-url> [alias] [label]" >&2
  exit 1
fi

# State files live under the state dir and are created empty on first run.
STATE_DIR="${FIGMA_MAXXING_STATE_DIR:-${HOME}/.config/figma-maxxing}"
REGISTRY="${STATE_DIR}/figma-files.json"
mkdir -p "$STATE_DIR"
[ -f "$REGISTRY" ] || echo '{}' > "$REGISTRY"

export URL ALIAS_ARG LABEL_ARG REGISTRY
python3 <<'PY'
import json, os, pathlib, re, sys

url = os.environ["URL"]
m = re.match(r"https?://(?:www\.)?figma\.com/(design|board|file)/([A-Za-z0-9_-]+)(?:/([^?#]+))?", url)
if not m:
    print(f"ERROR: not a valid Figma URL: {url}", file=sys.stderr)
    sys.exit(1)
url_type, key, name_slug = m.group(1), m.group(2), m.group(3) or ""

if not re.match(r"^[A-Za-z0-9_-]{15,}$", key):
    print(f"ERROR: file key looks invalid: {key}", file=sys.stderr)
    sys.exit(1)

canon_type = "figjam" if url_type == "board" else "design"

alias_arg = os.environ.get("ALIAS_ARG", "").strip()
if alias_arg:
    alias = re.sub(r"[^a-z0-9]+", "-", alias_arg.lower()).strip("-")
else:
    base = re.sub(r"[^a-z0-9]+", "-", name_slug.lower()).strip("-")
    alias = base.split("-")[0] if base else f"project-{key[:5]}"

label_arg = os.environ.get("LABEL_ARG", "").strip()
if label_arg:
    label = label_arg
else:
    label = name_slug.replace("---", " - ").replace("-", " ").replace("_", " ").replace("%20", " ")
    label = re.sub(r"\s+", " ", label).strip()

canon_url = f"https://www.figma.com/{url_type}/{key}/{name_slug}" if name_slug else f"https://www.figma.com/{url_type}/{key}"

p = pathlib.Path(os.environ["REGISTRY"])
text = p.read_text() if p.exists() else ""
d = json.loads(text) if text.strip() else {}
d.setdefault("_about", "Figma file alias registry")
d.setdefault("files", {})
existed = alias in d["files"]
d["files"][alias] = {
    "url": canon_url,
    "key": key,
    "label": label,
    "type": canon_type,
    "validated": None,
}
p.write_text(json.dumps(d, indent=2) + "\n")
print(f"{'updated' if existed else 'added'}: alias='{alias}' key={key} type={canon_type}")
print(f"  label: {label}")
print(f"  url:   {canon_url}")
print("  validated: null (after the first open via figma-open.sh, confirm the right file opened, then set validated to that date)")
PY

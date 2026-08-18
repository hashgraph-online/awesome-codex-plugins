#!/usr/bin/env bash
set -euo pipefail

config="${1:-${YANDEX_WORDSTAT_CONFIG:-}}"
[[ -n "$config" && -f "$config" ]] || {
  echo "Укажите защищённый файл настройки первым аргументом или через YANDEX_WORDSTAT_CONFIG." >&2
  exit 2
}

python3 - "$config" <<'PY'
import json
import os
import stat
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser().resolve()
mode = stat.S_IMODE(path.stat().st_mode)
if mode & 0o077:
    raise SystemExit("Файл настройки должен быть доступен только владельцу (права 600).")
data = json.loads(path.read_text(encoding="utf-8"))
if not str(data.get("api_key") or "").strip() or not str(data.get("folder_id") or "").strip():
    raise SystemExit("В настройке нужны api_key и folder_id.")
print("Wordstat v2: защищённая настройка найдена; ключ не выводился.")
PY

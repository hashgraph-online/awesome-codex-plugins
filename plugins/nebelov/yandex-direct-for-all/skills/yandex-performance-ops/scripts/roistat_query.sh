#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Использование: $0 <выход.json> <метод> [тело.json] [--project PROJECT] [--credentials-file FILE] [--base-url URL]" >&2
  exit 1
}

[[ $# -lt 2 ]] && usage
OUTPUT_FILE="$1"
ENDPOINT="$2"
shift 2
JSON_FILE=""
PROJECT="${ROISTAT_PROJECT:-}"
API_KEY="${ROISTAT_API_KEY:-}"
BASE_URL="${ROISTAT_BASE_URL:-https://cloud.roistat.com/api/v1}"
CREDENTIALS_FILE=""
if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then JSON_FILE="$1"; shift; fi
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --credentials-file) CREDENTIALS_FILE="$2"; shift 2 ;;
    --base-url) BASE_URL="$2"; shift 2 ;;
    --api-key) echo "Сырой ключ в командной строке запрещён" >&2; exit 2 ;;
    *) usage ;;
  esac
done

if [[ -n "$CREDENTIALS_FILE" ]]; then
  [[ -f "$CREDENTIALS_FILE" ]] || { echo "Закрытый файл доступа не найден" >&2; exit 2; }
  MODE="$(python3 -c 'import os,stat,sys; print(oct(stat.S_IMODE(os.stat(sys.argv[1]).st_mode))[2:])' "$CREDENTIALS_FILE")"
  [[ "$MODE" == "600" ]] || { echo "Файл доступа должен иметь права 0600" >&2; exit 2; }
  FILE_PROJECT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("project", ""))' "$CREDENTIALS_FILE")"
  FILE_API_KEY="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("api_key", ""))' "$CREDENTIALS_FILE")"
  FILE_BASE_URL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("base_url", ""))' "$CREDENTIALS_FILE")"
  [[ -z "$PROJECT" ]] && PROJECT="$FILE_PROJECT"
  [[ -z "$API_KEY" ]] && API_KEY="$FILE_API_KEY"
  [[ -n "$FILE_BASE_URL" ]] && BASE_URL="$FILE_BASE_URL"
fi
[[ -n "$PROJECT" ]] || { echo "Не задан проект Roistat" >&2; exit 2; }
[[ -n "$API_KEY" ]] || { echo "Не задан ROISTAT_API_KEY или закрытый файл доступа" >&2; exit 2; }
[[ "$ENDPOINT" =~ ^[A-Za-z0-9_./-]+$ ]] || { echo "Недопустимый метод" >&2; exit 2; }

OUTPUT_DIR="$(dirname "$OUTPUT_FILE")"
mkdir -p "$OUTPUT_DIR"
chmod 700 "$OUTPUT_DIR"
BODY_FILE="$(mktemp "$OUTPUT_DIR/.roistat-body.XXXXXX")"
RAW_FILE="$(mktemp "$OUTPUT_DIR/.roistat-raw.XXXXXX")"
FORMATTED_FILE="$(mktemp "$OUTPUT_DIR/.roistat-json.XXXXXX")"
CURL_CONFIG="$(mktemp "$OUTPUT_DIR/.roistat-curl.XXXXXX")"
chmod 600 "$BODY_FILE" "$RAW_FILE" "$FORMATTED_FILE" "$CURL_CONFIG"
cleanup() { rm -f "$BODY_FILE" "$RAW_FILE" "$FORMATTED_FILE" "$CURL_CONFIG"; }
trap cleanup EXIT
if [[ -n "$JSON_FILE" ]]; then
  [[ -f "$JSON_FILE" ]] || { echo "Файл тела запроса не найден" >&2; exit 2; }
  cp "$JSON_FILE" "$BODY_FILE"
elif [[ ! -t 0 ]]; then
  cat > "$BODY_FILE"
else
  printf '{}\n' > "$BODY_FILE"
fi
python3 -m json.tool "$BODY_FILE" >/dev/null || { echo "Тело запроса не является JSON" >&2; exit 2; }

printf 'silent\nshow-error\nrequest = "POST"\nurl = "%s/%s?project=%s"\nheader = "Content-Type: application/json"\nheader = "Api-key: %s"\ndata-binary = "@%s"\noutput = "%s"\nwrite-out = "%%{http_code}"\n' \
  "${BASE_URL%/}" "$ENDPOINT" "$PROJECT" "$API_KEY" "$BODY_FILE" "$RAW_FILE" > "$CURL_CONFIG"
HTTP_CODE="$(curl --config "$CURL_CONFIG")"
[[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]] || { echo "Roistat вернул HTTP $HTTP_CODE" >&2; exit 3; }
python3 -m json.tool "$RAW_FILE" > "$FORMATTED_FILE" || { echo "Roistat вернул неверный JSON" >&2; exit 3; }
chmod 600 "$FORMATTED_FILE"
mv "$FORMATTED_FILE" "$OUTPUT_FILE"
chmod 600 "$OUTPUT_FILE"
printf 'Roistat: %s, HTTP %s, файл %s\n' "$ENDPOINT" "$HTTP_CODE" "$(basename "$OUTPUT_FILE")"

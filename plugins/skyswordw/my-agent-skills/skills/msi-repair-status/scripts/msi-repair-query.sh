#!/usr/bin/env bash

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_ROOT="${MSI_REPAIR_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/msi-repair-status}"
STATE_ROOT="${MSI_REPAIR_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/msi-repair-status}"
RUNS_DIR="$CACHE_ROOT/runs"
INQUIRY_URL="https://account.msi.cn/zh-Hans/services/inquiry-history"
DETAIL_URL="https://account.msi.cn/zh-Hans/services/inquiry-detail"
CAPTCHA_URL="https://account.msi.cn/captcha/default"

usage() {
  cat <<EOF
用法:
  msi-repair-query.sh --rma RMA-EXAMPLE-123456 --serial SERIAL-EXAMPLE-123456

可选参数:
  --answer <value>   直接传入已确认的验证码答案，跳过交互输入
  --no-open          不自动用系统图片查看器打开验证码
  -h, --help         显示帮助

缓存目录:
  运行产物: $RUNS_DIR
  状态目录: $STATE_ROOT
EOF
}

die() {
  echo "错误: $*" >&2
  exit 1
}

timestamp() {
  date "+%Y%m%d-%H%M%S"
}

case_key() {
  python3 - "$1" "$2" <<'PY'
import hashlib
import sys

rma_no = sys.argv[1]
product_sn = sys.argv[2]
payload = f"{len(rma_no)}:{rma_no}\0{len(product_sn)}:{product_sn}".encode("utf-8")
print(hashlib.sha256(payload).hexdigest())
PY
}

make_run_dir() {
  local key="$1"
  local run_stamp
  local run_prefix

  run_stamp="$(timestamp)"
  run_prefix="$RUNS_DIR/${run_stamp}-${key}"

  if command -v mktemp >/dev/null 2>&1; then
    mktemp -d "${run_prefix}-XXXXXX"
    return 0
  fi

  local attempt=0
  local candidate=""
  while [[ "$attempt" -lt 100 ]]; do
    candidate="${run_prefix}-$$-${RANDOM}-${attempt}"
    if mkdir "$candidate" 2>/dev/null; then
      printf '%s\n' "$candidate"
      return 0
    fi
    attempt="$((attempt + 1))"
  done

  return 1
}

extract_csrf_token() {
  python3 -c '
import re
import sys

data = sys.stdin.read()
match = re.search(r"name=\"_token\"\s+value=\"([^\"]+)\"", data)
if not match:
    raise SystemExit(1)
print(match.group(1))
' || return 1
}

extract_json_status() {
  python3 -c '
import json
import sys

raw = sys.stdin.read().strip()
if not raw:
    raise SystemExit(0)
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    raise SystemExit(0)

if isinstance(payload, dict):
    print(str(payload.get("status", "")).strip(), end="")
'
}

response_to_text() {
  python3 -c '
import json
import sys

raw = sys.stdin.read().strip()
if not raw:
    raise SystemExit(0)
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    print(raw, end="")
    raise SystemExit(0)

status = ""
messages = ""
if isinstance(payload, dict):
    status = str(payload.get("status", "")).strip()
    messages = payload.get("message", "")

lines = []
if isinstance(messages, list):
    lines.extend(str(item).strip() for item in messages if str(item).strip())
elif str(messages).strip():
    lines.append(str(messages).strip())
elif status:
    lines.append(status)

print("\n".join(lines), end="")
'
}

html_to_text() {
  python3 -c '
import html
import re
import sys

data = sys.stdin.read()
if not data:
    raise SystemExit(0)

data = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", data)
data = re.sub(r"(?i)<br\s*/?>", "\n", data)
data = re.sub(r"(?i)</(p|div|li|tr|td|th|h[1-6]|section|article|table|ul|ol|header|footer)>", "\n", data)
data = re.sub(r"(?s)<[^>]+>", " ", data)
data = html.unescape(data)

lines = []
for line in data.splitlines():
    line = re.sub(r"[ \t\r\f\v]+", " ", line).strip()
    if line:
        lines.append(line)

print("\n".join(lines))
'
}

normalize_success_text() {
  python3 -c '
import html
from html.parser import HTMLParser
import re
import sys

data = sys.stdin.read()
if not data:
    raise SystemExit(0)

raw_data = data

if re.search(r"<[^>]+>", raw_data):
    data = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", data)
    data = re.sub(r"(?i)<br\s*/?>", "\n", data)
    data = re.sub(r"(?i)</(p|div|li|tr|td|th|h[1-6]|section|article|table|ul|ol|header|footer)>", "\n", data)
    data = re.sub(r"(?s)<[^>]+>", " ", data)
    data = html.unescape(data)

lines = []
for raw_line in data.splitlines():
    line = re.sub(r"[ \t\r\f\v]+", " ", raw_line).strip()
    if line:
        lines.append(line)

status_index = None
for index, line in enumerate(lines):
    if re.search(r"当前状态[：:]\s*.+", line):
        status_index = index
        break

if status_index is None:
    if not re.search(r"<[^>]+>", raw_data):
        raise SystemExit(1)

    class RepairDetailParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.repair_depth = 0
            self.before_first_h3 = True
            self.stepbox_depth = 0
            self.p_depth = 0
            self.current_p = []
            self.paragraphs = []

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            attr_map = {key.lower(): (value or "") for key, value in attrs}
            class_tokens = attr_map.get("class", "").split()

            if self.repair_depth > 0:
                self.repair_depth += 1
            elif "repair-detail" in class_tokens:
                self.repair_depth = 1

            if self.repair_depth == 0:
                return

            if self.stepbox_depth > 0:
                self.stepbox_depth += 1
            elif "stepbox" in class_tokens:
                self.stepbox_depth = 1

            if tag == "h3":
                self.before_first_h3 = False

            if (
                tag == "p"
                and self.before_first_h3
                and self.stepbox_depth == 0
            ):
                self.p_depth = 1
                self.current_p = []
            elif self.p_depth > 0:
                self.p_depth += 1

        def handle_endtag(self, tag):
            if self.repair_depth == 0:
                return

            if self.p_depth > 0:
                self.p_depth -= 1
                if self.p_depth == 0:
                    text = re.sub(r"\s+", " ", "".join(self.current_p)).strip()
                    if text:
                        self.paragraphs.append(text)
                    self.current_p = []

            if self.stepbox_depth > 0:
                self.stepbox_depth -= 1

            self.repair_depth -= 1

        def handle_data(self, chunk):
            if self.p_depth > 0:
                self.current_p.append(chunk)

    parser = RepairDetailParser()
    parser.feed(raw_data)
    parser.close()

    if not parser.paragraphs:
        raise SystemExit(1)

    print(f"当前状态：{parser.paragraphs[0]}", end="")
    raise SystemExit(0)

print("\n".join(lines[status_index:]), end="")
' || return 1
}

extract_active_stage() {
  python3 -c '
from html.parser import HTMLParser
import re
import sys

class StepboxParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stepbox_depth = 0
        self.stepbox_count = 0
        self.active_li_depth = 0
        self.capture_depth = 0
        self.current_text = []
        self.candidates = []
        self.error = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_map = {key.lower(): (value or "") for key, value in attrs}
        class_tokens = attr_map.get("class", "").split()

        if self.stepbox_depth > 0:
            self.stepbox_depth += 1
        elif "stepbox" in class_tokens:
            self.stepbox_depth = 1
            self.stepbox_count += 1

        if self.stepbox_depth == 0:
            return

        if self.capture_depth > 0:
            self.capture_depth += 1
        elif self.active_li_depth > 0 and tag == "span":
            self.capture_depth = 1

        if self.active_li_depth > 0:
            self.active_li_depth += 1
            return

        if tag == "li" and "active" in class_tokens:
            self.active_li_depth = 1
            self.capture_depth = 0
            self.current_text = []

    def handle_endtag(self, tag):
        if self.stepbox_depth == 0:
            return

        if self.capture_depth > 0:
            self.capture_depth -= 1

        if self.active_li_depth > 0:
            self.active_li_depth -= 1
            if self.active_li_depth == 0:
                text = re.sub(r"\s+", " ", "".join(self.current_text)).strip()
                if not text:
                    self.error = True
                else:
                    self.candidates.append(text)
                self.current_text = []

        self.stepbox_depth -= 1

    def handle_data(self, data):
        if self.capture_depth > 0:
            self.current_text.append(data)

parser = StepboxParser()
parser.feed(sys.stdin.read())
parser.close()

if parser.error or parser.stepbox_count == 0 or not parser.candidates:
    raise SystemExit(1)

print(parser.candidates[-1])
' || return 1
}

semantic_snapshot_from_text() {
  python3 -c '
import re
import sys

text = sys.stdin.read()
lines = []
for raw_line in text.splitlines():
    line = re.sub(r"\s+", " ", raw_line).strip()
    if line:
        lines.append(line)

status_line = ""
stage_line = ""
for line in lines:
    if not status_line:
        match = re.search(r"当前状态[：:]\s*(.+)", line)
        if match:
            status_line = f"当前状态：{match.group(1).strip()}"
    if not stage_line:
        match = re.search(r"页面高亮阶段[：:]\s*(.+)", line)
        if match:
            stage_line = f"页面高亮阶段：{match.group(1).strip()}"

output = []
if status_line:
    output.append(status_line)
elif lines:
    output.append(lines[0])

if stage_line:
    output.append(stage_line)

print("\n".join(output), end="")
'
}

build_state_snapshot() {
  local text="$1"
  local active_stage="${2:-}"
  local snapshot

  snapshot="$(semantic_snapshot_from_text <<< "$text")"

  if [[ -n "$snapshot" ]]; then
    printf '%s\n' "$snapshot"
  fi

  if [[ -n "$active_stage" ]]; then
    printf '页面高亮阶段：%s\n' "$active_stage"
  fi
}

extra_reminders() {
  local text="${1:-}"
  if python3 - "$text" <<'PY'
import re
import sys

text = sys.argv[1]

if re.search(r"待寄送|即将失效|已失效", text):
    raise SystemExit(0)

patterns = [
    r"(?<!不)需要用户操作",
    r"(?<!不)需要您操作",
    r"请用户操作",
    r"待用户操作",
    r"请您操作",
    r"待您操作",
]

if any(re.search(pattern, text) for pattern in patterns):
    raise SystemExit(0)

raise SystemExit(1)
PY
  then
    cat <<'EOF'
维修单号 14 天内未寄回会失效，寄出前确认外观完好且产品条码、二维码清晰完整。
EOF
  fi
}

extract_tracking_number() {
  python3 -c '
import html
import re
import sys

def clean(fragment):
    fragment = re.sub(r"(?is)<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment)
    return re.sub(r"\s+", " ", fragment).strip()

data = sys.stdin.read()
if not data:
    raise SystemExit(0)

match = re.search(r"(?is)<h3[^>]*>\s*寄送信息\s*</h3>(.*?)(?=<h3\b|$)", data)
if not match:
    raise SystemExit(0)

section = match.group(1)
headers = []
cells = []
seen_data_row = False
pattern = re.compile(r"(?is)<div[^>]*class=\"[^\"]*\b(th|td)\b[^\"]*\"[^>]*>(.*?)</div>")

for kind, fragment in pattern.findall(section):
    text = clean(fragment)
    if kind == "th" and not seen_data_row:
        headers.append(text)
        continue
    if kind == "td":
        seen_data_row = True
        cells.append(text)
        if headers and len(cells) >= len(headers):
            break

if not headers or not cells:
    raise SystemExit(0)

try:
    tracking_index = headers.index("寄送单号")
except ValueError:
    raise SystemExit(0)

if tracking_index < len(cells):
    tracking_no = cells[tracking_index].strip()
    if tracking_no:
        print(tracking_no, end="")
' || true
}

find_express_skill_dir() {
  local candidate
  for candidate in \
    "$SKILL_DIR/../express-tracking" \
    "$PWD/.codex/skills/express-tracking" \
    "$HOME/.codex/skills/express-tracking"
  do
    if [[ -f "$candidate/scripts/run.mjs" ]]; then
      (
        cd "$candidate" >/dev/null 2>&1 &&
          pwd
      )
      return 0
    fi
  done

  return 1
}

run_with_timeout() {
  local timeout_seconds="${1:?}"
  shift

  python3 - "$timeout_seconds" "$@" <<'PY'
import subprocess
import sys

timeout_seconds = float(sys.argv[1])
command = sys.argv[2:]

try:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
except subprocess.TimeoutExpired:
    raise SystemExit(124)

sys.stdout.write(completed.stdout)
sys.stderr.write(completed.stderr)
raise SystemExit(completed.returncode)
PY
}

print_express_tracking_summary() {
  local tracking_no="$1"
  local express_skill_dir=""
  local express_json=""
  local express_summary=""
  local express_timeout_seconds="${MSI_REPAIR_EXPRESS_TIMEOUT_SECONDS:-5}"

  echo "寄送单号：$tracking_no"

  command -v node >/dev/null 2>&1 || return 0
  express_skill_dir="$(find_express_skill_dir)" || return 0

  if ! express_json="$(
    run_with_timeout "$express_timeout_seconds" \
      node "$express_skill_dir/scripts/run.mjs" --number="$tracking_no" --json 2>/dev/null
  )"; then
    return 0
  fi

  if ! express_summary="$(python3 -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except json.JSONDecodeError:
    raise SystemExit(1)

lines = []
state = payload.get("state") or {}
if not isinstance(state, dict):
    state = {}
state_label = str(state.get("label", payload.get("stateLabel", ""))).strip()
latest = payload.get("latestEvent") or payload.get("latest") or {}
if not isinstance(latest, dict):
    latest = {}
if state_label:
    lines.append(f"当前物流状态：{state_label}")
time = str(latest.get("time", "")).strip()
if time:
    lines.append(f"最新时间：{time}")
context = str(latest.get("context", "")).strip()
if context:
    lines.append(f"最新轨迹：{context}")
print("\n".join(lines), end="")
' <<< "$express_json" 2>/dev/null)"; then
    return 0
  fi

  if [[ -n "$express_summary" ]]; then
    echo "物流补充："
    echo "$express_summary"
  fi
}

change_summary() {
  local previous="${1:-}"
  local current="${2:-}"
  local previous_snapshot=""
  local current_snapshot=""

  if [[ -n "$previous" ]]; then
    previous_snapshot="$(semantic_snapshot_from_text <<< "$previous")"
  fi
  if [[ -n "$current" ]]; then
    current_snapshot="$(semantic_snapshot_from_text <<< "$current")"
  fi

  if [[ -z "$previous_snapshot" ]]; then
    echo "相较上次：这是首次记录。"
    return 0
  fi

  if [[ "$previous_snapshot" == "$current_snapshot" ]]; then
    echo "相较上次：无变化。"
    return 0
  fi

  printf '相较上次：有变化。\n上次记录：%s\n' "$previous_snapshot"
}

open_image() {
  local image_path="$1"

  if command -v open >/dev/null 2>&1; then
    open "$image_path" >/dev/null 2>&1 || true
    return 0
  fi

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$image_path" >/dev/null 2>&1 || true
  fi
}

print_result() {
  local current_text="$1"
  local previous_snapshot="$2"
  local active_stage="$3"
  local current_snapshot="$4"
  local reminders

  echo "当前状态："
  echo "$current_text"
  echo

  if [[ -n "$active_stage" ]]; then
    echo "页面高亮阶段：$active_stage"
    echo
  fi

  change_summary "$previous_snapshot" "$current_snapshot"

  reminders="$(extra_reminders "$current_text")"
  if [[ -n "$reminders" ]]; then
    echo
    echo "$reminders"
  fi
}

main() {
  local rma_no=""
  local product_sn=""
  local answer=""
  local answer_is_preconfirmed=0
  local auto_open=1

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --rma)
        [[ $# -ge 2 ]] || die "--rma 需要一个值"
        rma_no="$2"
        shift 2
        ;;
      --serial|--product-sn)
        [[ $# -ge 2 ]] || die "$1 需要一个值"
        product_sn="$2"
        shift 2
        ;;
      --answer)
        [[ $# -ge 2 ]] || die "--answer 需要一个值"
        answer="$2"
        answer_is_preconfirmed=1
        shift 2
        ;;
      --no-open)
        auto_open=0
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "未知参数: $1"
        ;;
    esac
  done

  if [[ "$answer_is_preconfirmed" -eq 1 ]]; then
    auto_open=0
  fi

  [[ -n "$rma_no" ]] || read -r -p "请输入 RMA 码: " rma_no
  [[ -n "$product_sn" ]] || read -r -p "请输入产品序号: " product_sn

  mkdir -p "$STATE_ROOT" "$RUNS_DIR"

  local key
  local run_stamp
  local run_dir
  local cookie_jar
  local page_html
  local captcha_img
  local raw_result
  local text_result
  local csrf_token
  local json_status=""
  local result_text
  local current_snapshot=""
  local previous_snapshot=""
  local active_stage=""
  local tracking_no=""
  local state_text_file
  local state_snapshot_file

  key="$(case_key "$rma_no" "$product_sn")"
  run_dir="$(make_run_dir "$key")" ||
    die "无法创建运行产物目录。"

  cookie_jar="$run_dir/cookies.txt"
  page_html="$run_dir/inquiry-page.html"
  captcha_img="$run_dir/captcha.png"
  raw_result="$run_dir/result.raw"
  text_result="$run_dir/result.txt"
  state_text_file="$STATE_ROOT/${key}.last.txt"
  state_snapshot_file="$STATE_ROOT/${key}.last.snapshot.txt"

  curl -fsSL -c "$cookie_jar" -b "$cookie_jar" "$INQUIRY_URL" -o "$page_html" ||
    die "无法打开 MSI 查询页，可能是访问限制或页面改版。"

  csrf_token="$(extract_csrf_token < "$page_html")" ||
    die "未能从查询页提取 token，可能是页面改版。"

  curl -fsSL -c "$cookie_jar" -b "$cookie_jar" "${CAPTCHA_URL}?$(date +%s%N)" -o "$captcha_img" ||
    die "验证码图片下载失败。"

  echo "验证码图片已保存到: $captcha_img"
  if [[ "$auto_open" -eq 1 ]]; then
    open_image "$captcha_img"
  fi

  if [[ "$answer_is_preconfirmed" -eq 0 ]]; then
    read -r -p "请输入验证码答案: " answer
  fi

  curl -fsSL \
    -c "$cookie_jar" \
    -b "$cookie_jar" \
    -H "X-Requested-With: XMLHttpRequest" \
    -e "$INQUIRY_URL" \
    --data-urlencode "product_sn=$product_sn" \
    --data-urlencode "rma_no=$rma_no" \
    --data-urlencode "captcha=$answer" \
    --data-urlencode "_token=$csrf_token" \
    "$DETAIL_URL" \
    -o "$raw_result" || die "查询请求失败。"

  json_status="$(extract_json_status < "$raw_result" || true)"
  result_text="$(response_to_text < "$raw_result")"

  if [[ "$json_status" == "error" ]]; then
    [[ -n "$result_text" ]] || result_text="查询失败。"
    die "$result_text"
  fi

  if [[ "$result_text" == "$(cat "$raw_result")" ]]; then
    result_text="$(normalize_success_text < "$raw_result")" ||
      die "查询结果无法提取维修状态，可能是页面改版或服务异常。"
  elif [[ -z "$json_status" ]]; then
    result_text="$(normalize_success_text <<< "$result_text")" ||
      die "查询结果无法提取维修状态，可能是页面改版或服务异常。"
  fi

  active_stage="$(extract_active_stage < "$raw_result")" ||
    die "查询结果无法提取维修阶段，可能是页面改版或服务异常。"

  [[ -n "$result_text" ]] || die "查询结果为空，可能是页面改版或服务异常。"

  printf '%s\n' "$result_text" > "$text_result"
  current_snapshot="$(build_state_snapshot "$result_text" "$active_stage")"

  if [[ -f "$state_snapshot_file" ]]; then
    previous_snapshot="$(cat "$state_snapshot_file")"
  elif [[ -f "$state_text_file" ]]; then
    previous_snapshot="$(semantic_snapshot_from_text < "$state_text_file")"
  fi

  print_result "$result_text" "$previous_snapshot" "$active_stage" "$current_snapshot"
  tracking_no="$(extract_tracking_number < "$raw_result")"
  if [[ -n "$tracking_no" ]]; then
    echo
    print_express_tracking_summary "$tracking_no"
  fi
  printf '%s\n' "$result_text" > "$state_text_file"
  printf '%s\n' "$current_snapshot" > "$state_snapshot_file"
  echo
  echo "结果文件：$text_result"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi

#!/usr/bin/env bash
# Render the SEO audit dashboard: copy the HTML template and embed results.json
# into results.js. Rejects a structurally invalid payload before writing.
set -euo pipefail

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

# Normalize a path the way Node's path.join does: collapse duplicate
# separators, drop "." segments, and fold ".." where possible.
normalize_path() {
  awk -v raw="$1" 'BEGIN {
    absolute = (substr(raw, 1, 1) == "/");
    total = split(raw, parts, "/");
    count = 0;
    for (i = 1; i <= total; i++) {
      segment = parts[i];
      if (segment == "" || segment == ".") continue;
      if (segment == "..") {
        if (count > 0 && stack[count] != "..") {
          delete stack[count];
          count--;
        } else if (!absolute) {
          count++;
          stack[count] = "..";
        }
        continue;
      }
      count++;
      stack[count] = segment;
    }
    joined = "";
    for (i = 1; i <= count; i++) {
      joined = joined (i > 1 ? "/" : "") stack[i];
    }
    if (absolute) joined = "/" joined;
    if (joined == "") joined = (absolute ? "/" : ".");
    printf "%s", joined;
  }'
}

join_path() {
  local base=$1 leaf=$2 joined
  if [ -z "$base" ]; then
    joined=$leaf
  elif [ "$base" = "/" ]; then
    joined="/$leaf"
  else
    joined="${base%/}/$leaf"
  fi
  normalize_path "$joined"
}

file_mode() {
  local mode
  if mode=$(stat -c '%a' "$1" 2>/dev/null); then
    printf '%s' "$mode"
  else
    stat -f '%Lp' "$1"
  fi
}

temporary_path() {
  printf '%s.%s.%s%s.tmp' "$1" "$$" "$RANDOM" "$RANDOM"
}


usage() {
  fail "사용법: bash scripts/render-dashboard.sh <artifact-dir>"
}

[ "$#" -eq 1 ] || usage

artifact_dir=$1
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
skill_dir=$(dirname "$script_dir")
template_path="$skill_dir/assets/dashboard-template.html"
results_path=$(join_path "$artifact_dir" results.json)
dashboard_path=$(join_path "$artifact_dir" dashboard.html)
results_js_path=$(join_path "$artifact_dir" results.js)

[ -f "$template_path" ] || fail "대시보드 템플릿이 없습니다: $template_path"
[ -f "$results_path" ] || fail "results.json이 없습니다: $results_path"

# JSON.parse rejects a byte order mark; jq would silently skip it.
bom_prefix=$(dd if="$results_path" bs=1 count=3 2>/dev/null | od -An -tx1 | tr -d ' \n' || true)
if [ "$bom_prefix" = "efbbbf" ]; then
  fail "results.json JSON 파싱에 실패했습니다: invalid JSON"
fi

# Structure gate. Unknown extra keys stay allowed (K9); every violation exits
# through fail() before anything is written, so prior outputs survive.
# shellcheck disable=SC2016  # jq program text; $ names are jq variables.
VALIDATION_JQ='
def hexchars: "0123456789abcdef";
def hex2: . as $n | hexchars[($n / 16 | floor):((($n / 16) | floor) + 1)] + hexchars[($n % 16):(($n % 16) + 1)];
def jstrraw:
  explode
  | map(
      if . == 34 then "\\\""
      elif . == 92 then "\\\\"
      elif . == 8 then "\\b"
      elif . == 12 then "\\f"
      elif . == 10 then "\\n"
      elif . == 13 then "\\r"
      elif . == 9 then "\\t"
      elif . < 32 then "\\u00" + (. | hex2)
      else [.] | implode
      end
    )
  | join("");
def jstr: "\"" + jstrraw + "\"";
def jsnum:
  (. + 0) as $v
  | if $v == 0 then "0"
    else
      ($v | tostring) as $s
      | (if ($s | startswith("-")) then "-" else "" end) as $sign
      | (if ($s | startswith("-")) then $s[1:] else $s end) as $body
      | (($body | index("e")) // ($body | index("E"))) as $eix
      | (if $eix == null then $body else $body[0:$eix] end) as $mant
      | (if $eix == null then 0 else ($body[($eix + 1):] | ltrimstr("+") | tonumber) end) as $exp
      | ($mant | index(".")) as $dix
      | (if $dix == null then $mant else $mant[0:$dix] end) as $ip
      | (if $dix == null then "" else $mant[($dix + 1):] end) as $fp
      | (($ip + $fp) | sub("^0+"; "")) as $lead
      | if $lead == "" then "0"
        else
          ($lead | length) as $k
          | ($lead | sub("0+$"; "")) as $digits
          | ($digits | length) as $kd
          | ($k - ($fp | length) + $exp) as $n
          | if $n >= $kd and $n <= 21 then $sign + $digits + ("0" * ($n - $kd))
            elif $n > 0 and $n < $kd and $n <= 21 then $sign + $digits[0:$n] + "." + $digits[$n:]
            elif $n <= 0 and $n > -6 then $sign + "0." + ("0" * (0 - $n)) + $digits
            else $sign + $digits[0:1] + (if $kd > 1 then "." + $digits[1:] else "" end) + "e" + (if $n - 1 >= 0 then "+" else "-" end) + (((($n - 1) | fabs)) | tostring)
            end
        end
    end;
def is_index_key: . as $k | ($k | test("^(0|[1-9][0-9]*)$")) and (($k | tonumber) <= 4294967294);
def jser:
  if type == "object" then
    ( [to_entries[] | select(.key | is_index_key)] | sort_by(.key | tonumber) ) as $idx
    | [to_entries[] | select((.key | is_index_key) | not)] as $rest
    | "{" + ([ ($idx[], $rest[]) | (.key | jstr) + ":" + (.value | jser) ] | join(",")) + "}"
  elif type == "array" then "[" + ([.[] | jser] | join(",")) + "]"
  elif type == "string" then jstr
  elif type == "number" then jsnum
  elif type == "boolean" then tostring
  else "null" end;
def isobj: type == "object";
def field($k): if (type == "object") and has($k) then {present: true, value: .[$k]} else {present: false, value: null} end;
def shown($f): if $f.present then ($f.value | jser) else "undefined" end;
def enum_ok($f; $allowed): ($f.present and (($f.value | type) == "string") and (($allowed | index($f.value)) != null));
def enum_msg($path; $f; $allowed): "results.json \($path) 값이 유효하지 않습니다: \(shown($f)) (허용: \($allowed | join(", ")))";
def nonempty_string($f): ($f.present and (($f.value | type) == "string") and (($f.value | gsub("^\\s+|\\s+$"; "")) != ""));
def hexchars: "0123456789abcdef";
def hex2: . as $n | hexchars[($n / 16 | floor):((($n / 16) | floor) + 1)] + hexchars[($n % 16):(($n % 16) + 1)];
def jstrraw:
  explode
  | map(
      if . == 34 then "\\\""
      elif . == 92 then "\\\\"
      elif . == 8 then "\\b"
      elif . == 12 then "\\f"
      elif . == 10 then "\\n"
      elif . == 13 then "\\r"
      elif . == 9 then "\\t"
      elif . < 32 then "\\u00" + (. | hex2)
      else [.] | implode
      end
    )
  | join("");
def jstr: "\"" + jstrraw + "\"";
def jsnum:
  (. + 0) as $v
  | if $v == 0 then "0"
    else
      ($v | tostring) as $s
      | (if ($s | startswith("-")) then "-" else "" end) as $sign
      | (if ($s | startswith("-")) then $s[1:] else $s end) as $body
      | (($body | index("e")) // ($body | index("E"))) as $eix
      | (if $eix == null then $body else $body[0:$eix] end) as $mant
      | (if $eix == null then 0 else ($body[($eix + 1):] | ltrimstr("+") | tonumber) end) as $exp
      | ($mant | index(".")) as $dix
      | (if $dix == null then $mant else $mant[0:$dix] end) as $ip
      | (if $dix == null then "" else $mant[($dix + 1):] end) as $fp
      | (($ip + $fp) | sub("^0+"; "")) as $lead
      | if $lead == "" then "0"
        else
          ($lead | length) as $k
          | ($lead | sub("0+$"; "")) as $digits
          | ($digits | length) as $kd
          | ($k - ($fp | length) + $exp) as $n
          | if $n >= $kd and $n <= 21 then $sign + $digits + ("0" * ($n - $kd))
            elif $n > 0 and $n < $kd and $n <= 21 then $sign + $digits[0:$n] + "." + $digits[$n:]
            elif $n <= 0 and $n > -6 then $sign + "0." + ("0" * (0 - $n)) + $digits
            else $sign + $digits[0:1] + (if $kd > 1 then "." + $digits[1:] else "" end) + "e" + (if $n - 1 >= 0 then "+" else "-" end) + (((($n - 1) | fabs)) | tostring)
            end
        end
    end;
def is_index_key: . as $k | ($k | test("^(0|[1-9][0-9]*)$")) and (($k | tonumber) <= 4294967294);
def jser:
  if type == "object" then
    ( [to_entries[] | select(.key | is_index_key)] | sort_by(.key | tonumber) ) as $idx
    | [to_entries[] | select((.key | is_index_key) | not)] as $rest
    | "{" + ([ ($idx[], $rest[]) | (.key | jstr) + ":" + (.value | jser) ] | join(",")) + "}"
  elif type == "array" then "[" + ([.[] | jser] | join(",")) + "]"
  elif type == "string" then jstr
  elif type == "number" then jsnum
  elif type == "boolean" then tostring
  else "null" end;
def isobj: type == "object";
def field($k): if (type == "object") and has($k) then {present: true, value: .[$k]} else {present: false, value: null} end;
def shown($f): if $f.present then ($f.value | jser) else "undefined" end;
def enum_ok($f; $allowed): ($f.present and (($f.value | type) == "string") and (($allowed | index($f.value)) != null));
def enum_msg($path; $f; $allowed): "results.json \($path) 값이 유효하지 않습니다: \(shown($f)) (허용: \($allowed | join(", ")))";
def nonempty_string($f): ($f.present and (($f.value | type) == "string") and (($f.value | gsub("^\\s+|\\s+$"; "")) != ""));
def EVIDENCE: ["official", "live", "field", "tool", "lab", "synthetic", "heuristic"];
def TIERS: ["official-doc", "observed-file", "live-observation", "field-data", "tool-output", "lab-result", "synthetic-probe", "research-backed-heuristic"];
def seo_categories_error($cats):
  [ range(0; $cats | length) as $i
    | $cats[$i] as $c
    | ($c | field("status")) as $st
    | ($c | field("score")) as $sc
    | if ($c | isobj | not) then "results.json categories[\($i)]는 객체여야 합니다"
      elif (enum_ok($st; ["measured", "unknown", "not-applicable"]) | not) then enum_msg("categories[\($i)].status"; $st; ["measured", "unknown", "not-applicable"])
      elif ($sc.present and ($sc.value == null)) then null
      elif ((($sc.value | type) != "number") or ($sc.value < 0) or ($sc.value > 100)) then "results.json categories[\($i)].score는 0..100 또는 null이어야 합니다: \(shown($sc))"
      else null end
  ] | map(select(. != null)) | .[0];
def seo_findings_error($list):
  [ range(0; $list | length) as $i
    | $list[$i] as $f
    | ($f | field("severity")) as $sev
    | ($f | field("evidence_grade")) as $eg
    | ($f | field("source_tier")) as $st
    | if ($f | isobj | not) then "results.json findings[\($i)]는 객체여야 합니다"
      elif (enum_ok($sev; ["critical", "warning", "info"]) | not) then enum_msg("findings[\($i)].severity"; $sev; ["critical", "warning", "info"])
      elif ($eg.present and (enum_ok($eg; EVIDENCE) | not)) then enum_msg("findings[\($i)].evidence_grade"; $eg; EVIDENCE)
      elif ($st.present and (enum_ok($st; TIERS) | not)) then enum_msg("findings[\($i)].source_tier"; $st; TIERS)
      else null end
  ] | map(select(. != null)) | .[0];
def seo_block_error($r; $key):
  ($r | field($key)) as $b
  | if ($b.present | not) then null
    elif ($b.value | isobj | not) then "results.json \($key)는 객체여야 합니다: \($b.value | jser)"
    else [ ($b.value | to_entries[]) as $entry
           | ($entry.value) as $e
           | if ($e | isobj | not) then "results.json \($key).\($entry.key)은 객체여야 합니다: \($e | jser)"
             else ($e | field("status")) as $s
               | if (nonempty_string($s) | not) then "results.json \($key).\($entry.key).status는 비어 있지 않은 문자열이어야 합니다: \(shown($s))"
                 else null end
             end
         ] | map(select(. != null)) | .[0]
    end;
def seo_array_field_error($r; $key; $fields):
  ($r | field($key)) as $b
  | if ($b.present | not) then null
    elif ($b.value | isobj | not) then "results.json \($key)는 객체여야 합니다: \($b.value | jser)"
    else [ $fields[] as $fld
           | ($b.value | field($fld)) as $fv
           | if ($fv.present and (($fv.value | type) != "array")) then "results.json \($key).\($fld)는 배열이어야 합니다: \($fv.value | jser)"
             else null end
         ] | map(select(. != null)) | .[0]
    end;
def seo_history_error($r):
  ($r | field("score_history")) as $sh
  | ($r | field("best_run")) as $br
  | if (($sh.present or $br.present) | not) then null
    elif (($sh.present | not) or (($sh.value | type) != "array") or (($sh.value | length) == 0)) then "results.json score_history는 비어 있지 않은 배열이어야 합니다"
    else
      ($sh.value) as $h
      | [ range(0; $h | length) as $i
          | $h[$i] as $e
          | if ($e | isobj | not) then "results.json score_history[\($i)]는 객체여야 합니다"
            else ($e | field("evaluator_version")) as $ev
            | ($e | field("weights")) as $w
            | if (nonempty_string($ev) | not) then "results.json score_history[\($i)].evaluator_version이 없습니다: \(shown($ev))"
              elif (($w.present | not) or (($w.value | type) != "array")) then "results.json score_history[\($i)].weights가 없습니다 (정본 순서의 범주 가중치 배열이어야 합니다): \(shown($w))"
              else
                (if $i > 0 then $h[$i - 1] else null end) as $prev
                | (if (($prev | isobj) and ($prev | has("weights")) and ($prev.weights != null)) then ($prev.weights | jser) else "null" end) as $prevw
                | (if ($prev | isobj) then (($ev.value != $prev.evaluator_version) or (($w.value | jser) != $prevw)) else false end) as $changed
                | ($e | field("decision")) as $d
                | if (($prev | isobj) and $changed and (($d.present | not) or ($d.value != "reset"))) then "results.json score_history[\($i)]은 evaluator_version 또는 weights가 바뀌었는데 reset 기록이 없습니다 (decision: \(shown($d)))"
                  else null end
              end
            end
        ] | map(select(. != null)) | .[0]
    end;
def seo_best_run_error($r):
  ($r | field("best_run")) as $brf
  | if ($brf.present | not) then null
    else ($brf.value) as $br
    | if ($br | isobj | not) then "results.json best_run은 객체여야 합니다"
      else ($br | field("iteration")) as $it
      | if (($it.present | not) or (($it.value | type) != "number")) then "results.json best_run.iteration은 숫자여야 합니다: \(shown($it))"
        else ($r.score_history) as $h
        | ([ range(0; $h | length) as $i
             | select(($h[$i] | isobj) and (($h[$i] | field("iteration")) as $ei | ($ei.present and ($ei.value == $it.value))))
             | $i ] | .[0]) as $idx
        | if $idx == null then "results.json best_run.iteration \($it.value | jsnum)에 해당하는 score_history 항목이 없습니다"
          else ($h[$idx]) as $t
          | ($t | field("decision")) as $d
          | ($t | field("score")) as $ts
          | ($br | field("score")) as $bs
          | if ($d.value == "discarded") then "results.json best_run이 discarded iteration을 가리킵니다: \($it.value | jsnum)"
            elif (($d.present | not) or ($d.value != "kept")) then "results.json best_run.iteration \($it.value | jsnum)은 kept 항목이 아닙니다 (decision: \(shown($d)))"
            elif (($bs.present | not) or (($bs.value | type) != "number")) then "results.json best_run.score는 숫자여야 합니다: \(shown($bs))"
            elif (($ts.present | not) or ($bs.value != $ts.value)) then "results.json best_run.score \($bs.value | jsnum)가 iteration \($it.value | jsnum)의 점수 \(shown($ts))와 다릅니다"
            else
              ([ $h[] | select((isobj) and (.decision == "kept") and ((.score | type) == "number")) | .score ]) as $kept
              | if (($kept | length) > 0) and ($bs.value < ($kept | max)) then "results.json best_run.score \($bs.value | jsnum)가 최고 kept 점수 \(($kept | max) | jsnum)보다 낮습니다"
                else null end
            end
          end
        end
      end
    end;
. as $docs
| if ($docs | length) != 1 then "E\tresults.json JSON 파싱에 실패했습니다: invalid JSON"
  else ($docs[0]) as $r
  | if ($r | isobj | not) then "E\t" + ("results.json은 객체여야 합니다: " + (if ($r | type) == "array" then "array" else ($r | jser) end))
    else (["project_name", "status", "categories", "findings"]) as $req
    | ([ $req[] | . as $k | select(($r | has($k)) | not) ]) as $missing
    | if ($missing | length) > 0 then "E\tresults.json 필수 키가 없습니다: " + ($missing | join(", "))
      else ($r | field("status")) as $st
      | ($r | field("overall_grade")) as $og
      | if (enum_ok($st; ["complete", "idle", "running"]) | not) then "E\t" + enum_msg("status"; $st; ["complete", "idle", "running"])
        elif ($og.present and ($og.value != null) and (enum_ok($og; ["A", "B", "C", "D", "F"]) | not)) then "E\t" + enum_msg("overall_grade"; $og; ["A", "B", "C", "D", "F"])
        elif (($r.categories | type) != "array") then "E\tresults.json categories는 배열이어야 합니다"
        elif (($r.findings | type) != "array") then "E\tresults.json findings는 배열이어야 합니다"
        else (seo_categories_error($r.categories)) as $e1
        | if $e1 != null then "E\t" + $e1
          else (seo_findings_error($r.findings)) as $e2
          | if $e2 != null then "E\t" + $e2
            else (seo_block_error($r; "measurement_methods")) as $e3
            | if $e3 != null then "E\t" + $e3
              else (seo_block_error($r; "platform_policy")) as $e4
              | if $e4 != null then "E\t" + $e4
                else (seo_array_field_error($r; "query_fanout"; ["queries", "missing_topics"])) as $e5
                | if $e5 != null then "E\t" + $e5
                  else (seo_array_field_error($r; "citation_probe"; ["engines"])) as $e6
                  | if $e6 != null then "E\t" + $e6
                    else (seo_history_error($r)) as $e7
                    | if $e7 != null then "E\t" + $e7
                      else (seo_best_run_error($r)) as $e8
                      | if $e8 != null then "E\t" + $e8 else "O\t" + ($r | jser) end
                      end
                    end
                  end
                end
              end
            end
          end
        end
      end
    end
  end
'

validation=$(jq -s -r "$VALIDATION_JQ" "$results_path" 2>/dev/null) \
  || fail "results.json JSON 파싱에 실패했습니다: invalid JSON"

case $validation in
  O$'\t'*) results_json=${validation#O$'\t'} ;;
  E$'\t'*) fail "${validation#E$'\t'}" ;;
  *) fail "results.json JSON 파싱에 실패했습니다: invalid JSON" ;;
esac

snapshot_output() {
  SNAPSHOT_EXISTS=0
  SNAPSHOT_MODE=""
  SNAPSHOT_COPY=""
  if [ ! -e "$1" ]; then
    return 0
  fi
  if [ ! -f "$1" ]; then
    printf '출력 경로가 일반 파일이 아닙니다: %s\n' "$1" >&2
    exit 1
  fi
  SNAPSHOT_EXISTS=1
  SNAPSHOT_MODE=$(file_mode "$1")
  SNAPSHOT_COPY=$(temporary_path "$1")
  if ! cp -p -- "$1" "$SNAPSHOT_COPY"; then
    printf '출력 경로를 백업하지 못했습니다: %s\n' "$1" >&2
    exit 1
  fi
}

write_temp_stream() {
  local path=$1 mode=$2
  if ! ( set -o noclobber; printf '' > "$path" ) 2>/dev/null; then
    printf '임시 파일을 만들지 못했습니다: %s\n' "$path" >&2
    return 1
  fi
  if [ -n "$mode" ] && ! chmod "$mode" "$path" 2>/dev/null; then
    rm -f -- "$path"
    return 1
  fi
  if ! dd of="$path" conv=fsync 2>/dev/null; then
    rm -f -- "$path"
    return 1
  fi
  return 0
}

restore_output() {
  if [ "$2" -eq 0 ]; then
    rm -f -- "$1"
    return 0
  fi
  mv -f -- "$3" "$1"
}

write_output_pair() {
  local dashboard_file=$1 dashboard_exists

  snapshot_output "$dashboard_path"
  dashboard_exists=$SNAPSHOT_EXISTS
  DASHBOARD_MODE=$SNAPSHOT_MODE
  DASHBOARD_SNAPSHOT=$SNAPSHOT_COPY

  snapshot_output "$results_js_path"
  RESULTS_MODE=$SNAPSHOT_MODE
  RESULTS_SNAPSHOT=$SNAPSHOT_COPY

  DASHBOARD_TEMP=$(temporary_path "$dashboard_path")
  RESULTS_JS_TEMP=$(temporary_path "$results_js_path")

  if ! cat -- "$dashboard_file" | write_temp_stream "$DASHBOARD_TEMP" "$DASHBOARD_MODE"; then
    fail "dashboard.html을 쓰지 못했습니다: $dashboard_path"
  fi
  if ! printf 'window.__SEO_RESULTS__ = %s;\n' "$results_json" | write_temp_stream "$RESULTS_JS_TEMP" "$RESULTS_MODE"; then
    fail "results.js를 쓰지 못했습니다: $results_js_path"
  fi

  if ! mv -f -- "$DASHBOARD_TEMP" "$dashboard_path"; then
    fail "dashboard.html을 교체하지 못했습니다: $dashboard_path"
  fi
  DASHBOARD_TEMP=""

  if ! mv -f -- "$RESULTS_JS_TEMP" "$results_js_path"; then
    if ! restore_output "$dashboard_path" "$dashboard_exists" "$DASHBOARD_SNAPSHOT"; then
      fail "results.js 커밋 실패 후 dashboard.html 복원에 실패했습니다"
    fi
    DASHBOARD_SNAPSHOT=""
    fail "results.js를 교체하지 못했습니다: $results_js_path"
  fi
  RESULTS_JS_TEMP=""

  if [ -n "$DASHBOARD_SNAPSHOT" ]; then
    rm -f -- "$DASHBOARD_SNAPSHOT"
  fi
  if [ -n "$RESULTS_SNAPSHOT" ]; then
    rm -f -- "$RESULTS_SNAPSHOT"
  fi
  DASHBOARD_SNAPSHOT=""
  RESULTS_SNAPSHOT=""
}

# shellcheck disable=SC2329  # invoked by the EXIT trap below.
cleanup_temps() {
  local leftover
  for leftover in "${DASHBOARD_TEMP-}" "${RESULTS_JS_TEMP-}" "${DASHBOARD_SNAPSHOT-}" "${RESULTS_SNAPSHOT-}"; do
    if [ -n "$leftover" ]; then
      rm -f -- "$leftover"
    fi
  done
  return 0
}

DASHBOARD_TEMP=""
RESULTS_JS_TEMP=""
DASHBOARD_SNAPSHOT=""
RESULTS_SNAPSHOT=""
DASHBOARD_MODE=""
RESULTS_MODE=""

trap cleanup_temps EXIT

mkdir -p -- "$artifact_dir"
write_output_pair "$template_path"

printf '렌더 완료: %s\n' "$dashboard_path"
printf '렌더 완료: %s\n' "$results_js_path"

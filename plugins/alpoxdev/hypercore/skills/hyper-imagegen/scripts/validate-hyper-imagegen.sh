#!/usr/bin/env bash
# Validates the hyper-imagegen skill package: eval corpus, resolver/terminal logic, and package docs.
# Bash 3.2+ port of the former validate-hyper-imagegen.mjs (Bun). Requires jq >= 1.6.
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd -P)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

if command -v shasum >/dev/null 2>&1; then
  SHA_CMD=(shasum -a 256)
else
  SHA_CMD=(sha256sum)
fi

# jq library: every pure predicate/validator from the original module.
JQ=$(cat <<'JQEOF'
def is_rec: type == "object";
def truthy: if . == null then false elif type == "boolean" then . elif type == "number" then (. != 0) elif type == "string" then (. != "") else true end;
def trim_str: gsub("^[\\s\\p{Z}]+"; "") | gsub("[\\s\\p{Z}]+$"; "");
def str_nonempty: if type == "string" then (trim_str != "") else false end;
def input_keys: ["requested_mode","material_context","missing_fact","edit_source","authorization","fallback_policy","image_generation","image_editing","retrieve_persist","inspect","file_write","inspection_requirement","topic","compiled_brief"];
def set_keys: input_keys[0:12];
def all_keys: input_keys + ["canvas"];
def set_values: {
  requested_mode: ["generate","edit","prompt_only"],
  material_context: ["complete","missing"],
  missing_fact: ["none","subject","reference","rendered_text","preserve_change"],
  edit_source: ["supplied","absent","not_applicable"],
  authorization: ["authorized","denied","unknown"],
  fallback_policy: ["explicitly_allowed","explicitly_rejected","unspecified"],
  image_generation: ["available","unavailable","unknown"],
  image_editing: ["available","unavailable","unknown"],
  retrieve_persist: ["available","unavailable","unknown"],
  inspect: ["available","unavailable","unknown"],
  file_write: ["available","unavailable","unknown"],
  inspection_requirement: ["required","optional"]
};

def validate_topic($t):
  if ($t|type) != "string" then {ok:false,error:"E_TOPIC_UNSAFE"}
  elif ($t|test("[\\p{Cc}\\p{Cf}]")) then {ok:false,error:"E_TOPIC_UNSAFE"}
  else ($t|trim_str) as $v
  | if ($v == "" or $v == "." or $v == ".." or ($v|test("[\\\\/]"))) then {ok:false,error:"E_TOPIC_UNSAFE"}
    else {ok:true,topic:$v} end
  end;

def canvas_ok($cv):
  ($cv|is_rec)
  and (([ $cv|keys[] as $k | select((["aspect_ratio","size","quality"]|index($k))==null) ]|length) == 0)
  and (([ $cv[] | select((type) != "string") ]|length) == 0)
  and (if (($cv.aspect_ratio|type) == "string") then ($cv.aspect_ratio|test("^[0-9]+:[0-9]+$")) else true end);

def typed_checks($ti):
  if ($ti.material_context == "complete" and (($ti.compiled_brief|trim_str) == "")) then {ok:false,error:"E_COMPILED_BRIEF"}
  elif ($ti.material_context == "missing" and $ti.missing_fact == "none") then {ok:false,error:"E_MISSING_FACT"}
  elif ($ti.material_context == "complete" and $ti.missing_fact != "none") then {ok:false,error:"E_MISSING_FACT"}
  elif ($ti.requested_mode == "edit" and ($ti.edit_source != (if ($ti.material_context == "missing" and $ti.missing_fact == "reference") then "absent" else "supplied" end))) then {ok:false,error:"E_EDIT_SOURCE"}
  elif ($ti.requested_mode != "edit" and $ti.edit_source != "not_applicable") then {ok:false,error:"E_EDIT_SOURCE"}
  else {ok:true,context:$ti} end;
def validate_fields($in):
  ([ set_keys[] as $k | select((set_values[$k]|index($in[$k])) == null) | $k ] | first) as $bad
  | if $bad != null then {ok:false,error:("E_INPUT_"+$bad)}
    else validate_topic($in.topic) as $t
    | if ($t.ok|not) then $t
      elif (($in.compiled_brief|type) != "string") then {ok:false,error:"E_COMPILED_BRIEF"}
      else typed_checks($in + {topic:$t.topic}) end
    end;

def validate_input($in):
  if ($in|is_rec|not) then {ok:false,error:"E_CAPABILITY_SCHEMA"}
  elif (([ $in|keys[] as $k | select((all_keys|index($k))==null) ]|length) > 0) then {ok:false,error:"E_CAPABILITY_SCHEMA"}
  elif (([ input_keys[] as $k | select((($in|has($k)))|not) ]|length) > 0) then {ok:false,error:"E_CAPABILITY_SCHEMA"}
  elif (($in|has("canvas")) and (canvas_ok($in.canvas)|not)) then {ok:false,error:"E_CANVAS"}
  else validate_fields($in)
  end;


def stable_str($in): reduce input_keys[] as $k ({}; .[$k] = $in[$k]) | to_entries | sort_by(.key) | from_entries | tojson;
def context_full($in):
  (validate_input($in)) as $c
  | if ($c.ok|not) then {ok:false,error:$c.error}
    else {ok:true, context:$c.context, stable: stable_str($c.context)} end;

def classify($text):
  if ($text|type) != "string" then "manual_required"
  else ($text|ascii_downcase) as $s
  | if ($s|test("(분석|설명|analysis|explain)")) then "negative"
    elif ($s|test("(svg|벡터|vector)")) then "negative"
    elif (($s|test("(프롬프트만|prompt[ -]?only)")) and ($s|test("(이미지|그림|사진|image|picture|illustration)"))) then "prompt_only"
    elif ($s|test("(이미지|그림|사진|image|picture).{0,36}(편집|수정|보정|edit|retouch)|(edit|retouch).{0,36}(image|picture)")) then "edit"
    elif ($s|test("(이미지|그림|사진|image|picture|illustration).{0,36}(만들|생성|그려|create|generate|draw)|(create|generate|draw|illustrate).{0,36}(image|picture|illustration)")) then "create"
    elif ($s|test("(프롬프트 팩|prompt pack|디자인 문서|design document|편집 가능한 ui|editable ui|코드 구현|code implementation)")) then "negative"
    else "manual_required" end
  end;

def missing_question($f):
  {subject:"이미지의 주제를 알려 주세요.", reference:"참조 이미지 또는 자료를 제공해 주세요.", rendered_text:"이미지에 정확히 넣을 문구를 알려 주세요.", preserve_change:"유지할 요소와 변경할 요소를 알려 주세요."}[$f];

def annotated($in;$tok;$bd;$v):
  $v + {topic:$in.topic, context_token:$tok, compiled_brief_digest:$bd, compiled_brief:$in.compiled_brief};

def fallback_with($in;$tok;$bd;$reason):
  if $in.fallback_policy == "explicitly_allowed" then annotated($in;$tok;$bd;{route:"prompt_only",terminal:"pending_prompt_saved",reason:$reason,attempts:0,invokes:0,writes:0})
  elif $in.fallback_policy == "explicitly_rejected" then {route:"block",terminal:"blocked",error:"E_FALLBACK_REJECTED",attempts:0,invokes:0,writes:0}
  else {route:"ask",terminal:"awaiting_input",reason:$reason,question:"이미지 생성 또는 편집을 완료할 수 없습니다. 이미지 대신 프롬프트 전용 파일을 저장할까요?",attempts:0,invokes:0,writes:0} end;

def resolve_with($in;$tok;$bd):
  (validate_input($in)) as $c
  | if ($c.ok|not) then {route:"block",terminal:"blocked",error:$c.error,attempts:0,invokes:0,writes:0}
    elif ($c.context.material_context == "missing") then {route:"ask",terminal:"awaiting_input",reason:"E_MISSING_FACT",missing_fact:$c.context.missing_fact,question:missing_question($c.context.missing_fact),attempts:0,invokes:0,writes:0}
    elif ($c.context.authorization != "authorized") then
      (if ($c.context.authorization == "unknown" and $c.context.requested_mode == "edit" and $c.context.edit_source == "supplied")
        then {route:"ask",terminal:"awaiting_input",error:"E_AUTHORIZATION",question:"제공한 원본을 사용하고 편집할 권한이 있나요?",attempts:0,invokes:0,writes:0}
        else {route:"block",terminal:"blocked",error:(if $c.context.authorization == "denied" then "E_AUTHORIZATION_DENIED" else "E_AUTHORIZATION" end),attempts:0,invokes:0,writes:0} end)
    elif ($c.context.file_write != "available") then {route:"block",terminal:"blocked",error:"E_FILE_WRITE_UNAVAILABLE",attempts:0,invokes:0,writes:0}
    elif ($c.context.requested_mode == "prompt_only") then annotated($c.context;$tok;$bd;{route:"prompt_only",terminal:"pending_prompt_saved",attempts:0,invokes:0,writes:0})
    else
      (if $c.context.requested_mode == "edit" then $c.context.image_editing else $c.context.image_generation end) as $cap
      | if ($cap != "available" or $c.context.retrieve_persist != "available" or ($c.context.inspection_requirement == "required" and $c.context.inspect != "available"))
        then fallback_with($c.context;$tok;$bd;"E_RUNTIME_UNAVAILABLE")
        else annotated($c.context;$tok;$bd;{route:$c.context.requested_mode,terminal:"ready",attempts:0,invokes:0,writes:0}) end
    end;

def valid_history($h;$tok;$bd):
  if (($h|type) != "array") then false
  elif (($h|length) > 2) then false
  elif ([ range(0;($h|length)) as $i | ($h[$i]) as $a
          | if ($a|is_rec) then
              (if ($a.attempt == ($i+1)) then true else false end)
              and (if (($a.outcome == "objective_failure") or ($a.outcome == "success")) then true else false end)
              and ($a.objective_evidence|str_nonempty)
              and (if ($a.context_token == $tok) then true else false end)
              and (if ($a.compiled_brief_digest == $bd) then true else false end)
            else false end
        ] | all | not) then false
  elif (([ $h[] | select(is_rec and (.outcome == "success")) ]|length) > 1) then false
  elif (([ $h[] | select(is_rec and (.outcome == "success")) ]|length) > 0)
       and (if ($h|length) > 0 then (if (($h[-1]|is_rec) and ($h[-1].outcome == "success")) then false else true end) else true end) then false
  else true end;

def same_identity($a;$b):
  ($a|is_rec) and ($b|is_rec)
  and (["canonical_path","dev","ino","byte_length","content_digest"] | map(. as $k | ($a[$k] == $b[$k])) | all);
def same_node($a;$b):
  ($a|is_rec) and ($b|is_rec)
  and (["canonical_path","dev","ino"] | map(. as $k | ($a[$k] == $b[$k])) | all);

def valid_proof($proof;$rid):
  ($proof|is_rec)
  and (if ($proof.capability == "descriptor_relative_no_follow") then true else false end)
  and (if ($proof.adapter != "pathname") then true else false end)
  and (same_identity($proof.identity;$rid))
  and (same_identity($proof.final_before;$proof.final_after))
  and (same_identity($proof.final_after;$rid))
  and (same_node($proof.root_before;$proof.root_after))
  and (same_node($proof.parent_before;$proof.parent_after));

def exact($a;$o):
  if (($a|is_rec)|not) or (($o|is_rec)|not) then false
  else
    ($a.terminal // "") as $t
    | if ((if (([ "blocked","awaiting_input","retry_pending","pending_prompt_saved","ready" ]|index($t)) != null) then ([ "path","digest","evidence","inspection" ] | map(. as $k | ($a|has($k))) | any) else false end)) then false
      elif ($t == "generated_caveated" and ((($a|has("inspection")) or ((($a.disclosure // null) | truthy) | not)))) then false
      elif ($t == "generated_verified" and (((($a|has("inspection"))|not) or (($a.disclosure // null) | truthy)))) then false
      elif ($t == "prompt_saved" and (((($a.path // null)|truthy)|not) or ((($a.digest // null)|truthy)|not) or ($a.writes != 1))) then false
      else ([ $o | to_entries[] as $e | (($a|has($e.key)) and (($a[$e.key]|tojson) == ($e.value|tojson))) ] | all)
      end
  end;

def quoted_re: "\"([^\"\n]+)\"|“([^”\n]+)”|「([^」\n]+)」";
def layout_labels: ["subject","context","composition","lighting","style","text"];
def whitelist: ["no invented glyphs","no watermark"];
def deadword_map: {
  W_EMPTY_ADJ: ["멋지게","고급스럽게","beautiful","stunning"],
  W_SD_ERA_BOOSTER: ["masterpiece","8k","4k","uhd","trending on artstation"],
  W_WEIGHT_SYNTAX: ["(word:1.3)"],
  W_SD_FLAG: ["--ar","--v"]
};
def prompt_syntax($in):
  (if (($in.compiled_brief? // null)|type) == "string" then $in.compiled_brief else "" end) as $b
  | [ $b | match(quoted_re; "g") | .captures[] | select((.string != null)) | .string ] as $quoted
  | ($b | gsub(quoted_re; " ") | ascii_downcase) as $scan
  | (reduce whitelist[] as $w ($scan; split($w) | join(" "))) as $scrubbed
  | (($scan | test("\\bAR\\s*[0-9]+:[0-9]+|aspect[- ]?ratio\\s*[0-9]+:[0-9]+|\\b[0-9]+:[0-9]+\\b|\\b[0-9]{2,5}\\s*[x×]\\s*[0-9]{2,5}\\b|\\b[0-9]{3,5}\\s*px\\b|quality\\s*="; "i"))|not) as $ar_absent
  | (($b | split("\"") | length) - 1) as $dq
  | (if (($dq % 2) != 0) then true
     else ([ [["“","”"],["「","」"],["『","』"],["《","》"]] | .[] | . as [$o,$c] | (($b|split($o)|length) != ($b|split($c)|length)) ] | any) end) as $pair_unbalanced
  | (($scrubbed | test("\\bno\\s+[a-z][a-z -]{1,40}|\\bwithout\\s+[a-z][a-z -]{1,40}|--no\\b")) or ($scrubbed | test("없이|빼고|제외|넣지 마|하지 마"))) as $negative_hit
  | ([ deadword_map | to_entries[] | select((.value | map(. as $f | ($scan|contains($f))) | any)) | .key ] | sort) as $deadwords
  | (($scan | test("\\([a-z0-9 _-]+:[0-9]+(\\.[0-9]+)?\\)"; "i"))|not) as $weight_free
  | [ $b | split("\n")[] | match("^([a-z]+)\\s*:") | .captures[0].string ] as $labels
  | ([ $labels[] as $l | select((layout_labels|index($l)) != null) | $l ]) as $used
  | (($used|length) == ($used|unique|length)) as $labels_once
  | (([ $labels[] as $l | select((layout_labels|index($l)) == null) | $l ]|length) == 0) as $labels_allowed
  | ([ (if $ar_absent then empty else "E_PROMPT_AR_LEAK" end),
       (if $pair_unbalanced then "E_PROMPT_QUOTE_UNBALANCED" else empty end),
       (if $negative_hit then "E_PROMPT_NEGATIVE_TIER" else empty end),
       (if (($used|length) > 0 and (($labels_once|not) or ($labels_allowed|not))) then "E_PROMPT_LAYOUT_LABEL" else empty end) ]) as $errors
  | {ok:(($errors|length) == 0), errors:$errors, report:{
      ar_token_absent:$ar_absent,
      rendered_text_quoted:(($quoted|length) > 0),
      rendered_text_count:($quoted|length),
      rendered_text_position:(if ($quoted|length) > 0 then "quoted" else "none" end),
      negatives_tiered:($negative_hit|not),
      negatives_whitelisted:([ whitelist[] | select(. as $w | ($scan|contains($w))) ]|length),
      deadwords:$deadwords,
      weight_syntax:$weight_free,
      layout_labels_once:$labels_once,
      layout_labels_allowed:$labels_allowed,
      layout_report_prose_absent:(($b | test("\\b(terminal|attempts?|provenance|digest|report|context_token)\\b|saved to|다이제스트|시도 이력|종결 상태"; "i"))|not)
    }};

def terminal_runtime($in;$pre;$tok;$bd;$hist;$rt;$art):
  if (($hist|type) != "array") then {route:"block",terminal:"blocked",error:"E_ATTEMPT_HISTORY",attempts:0,invokes:0,writes:0}
  elif (valid_history($hist;$tok;$bd)|not) then {route:"block",terminal:"blocked",error:"E_ATTEMPT_HISTORY",attempts:0,invokes:0,writes:0}
  else
    ($hist|length) as $attempts
    | if ($pre.terminal != "ready") then $pre
      elif (($attempts == 0) or ($hist[-1].outcome == "objective_failure")) then
        (if $attempts == 2 then (fallback_with($in;$tok;$bd;"E_RUNTIME_FAILED") + {attempt_history:$hist, attempts:$attempts, invokes:$attempts, writes:0})
         else annotated($in;$tok;$bd;{route:$pre.route, terminal:"retry_pending", reason:"E_RETRY_PENDING", attempt_history:$hist, attempts:$attempts, invokes:$attempts, writes:0}) end)
      elif (($art.ok|not)) then {route:"block",terminal:"blocked",error:$art.error,attempts:$attempts,invokes:$attempts,writes:0}
      elif (($rt.provenance.context_token != $tok) or ($rt.provenance.compiled_brief_digest != $bd) or ($rt.provenance.topic != $in.topic) or ($rt.provenance.mode != $in.requested_mode) or ($rt.provenance.attempt != $attempts)) then {route:"block",terminal:"blocked",error:"E_PROVENANCE_BINDING",attempts:$attempts,invokes:$attempts,writes:0}
      else
        (($in.inspection_requirement == "optional") and ($in.inspect != "available")) as $caveated
        | if (($caveated|not) and (((($rt.inspection.status? // null) != "passed")) or ((($rt.inspection.record? // null)|str_nonempty)|not) or (same_identity(($rt.inspection.identity? // null); $art.identity)|not))) then {route:"block",terminal:"blocked",error:"E_INSPECTION",attempts:$attempts,invokes:$attempts,writes:0}
          elif $caveated then annotated($in;$tok;$bd;{route:$pre.route, terminal:"generated_caveated", attempts:$attempts, invokes:$attempts, writes:1, path:$art.relative_path, digest:$art.identity.content_digest, evidence:$art.identity, attempt_history:$hist, inspection_status:$in.inspect, disclosure:"visual_rendered_text_exact_constraint_and_series_unverified"})
          else annotated($in;$tok;$bd;{route:$pre.route, terminal:"generated_verified", attempts:$attempts, invokes:$attempts, writes:1, path:$art.relative_path, digest:$art.identity.content_digest, evidence:$art.identity, attempt_history:$hist, inspection:{record:$rt.inspection.record, identity:$rt.inspection.identity}})
          end
      end
  end;

def terminal_prompt($in;$pre;$tok;$bd;$hist;$rt;$art):
  if (($hist|type) != "array") then {route:"block",terminal:"blocked",error:"E_ATTEMPT_HISTORY",attempts:0,invokes:0,writes:0}
  elif (valid_history($hist;$tok;$bd)|not) then {route:"block",terminal:"blocked",error:"E_ATTEMPT_HISTORY",attempts:0,invokes:0,writes:0}
  else
    (($hist|length) == 2
     and ([ $hist[] | select(is_rec and (.outcome == "objective_failure")) ]|length) == 2
     and ($in.fallback_policy == "explicitly_allowed")) as $retry_fallback
    | if ((if ((["pending_prompt_saved","retry_pending"]|index($pre.terminal)) != null) then false else true end)
           and ($pre.route != "prompt_only") and ($retry_fallback|not)) then $pre
      else
        (($art.ok|not)
         or ($rt.provenance.context_token != $tok)
         or ($rt.provenance.compiled_brief_digest != $bd)
         or ($rt.provenance.topic != $in.topic)
         or ($rt.provenance.mode != "prompt_only")
         or ($rt.provenance.exact_input != $in.compiled_brief)) as $bad
        | if $bad then {route:"block",terminal:"blocked",error:(if $art.ok then "E_PROMPT_BINDING" else $art.error end),attempts:($hist|length),invokes:($hist|length),writes:0}
          else annotated($in;$tok;$bd;{route:"prompt_only", terminal:"prompt_saved", attempts:($hist|length), invokes:($hist|length), writes:1, path:$art.relative_path, digest:$art.content_digest, evidence:$art.identity})
          end
      end
  end;

def section_tags: [ split("\n")[] as $line | (try ($line | capture("^<(?<t>[a-z_]+)>[[:space:]]*$") | .t) catch empty) ];
def tag_errors($file;$en;$ko;$required):
  ($en|section_tags) as $et
  | ($ko|section_tags) as $kt
  | ([ $required[] as $t | select((($et|index($t)) == null)) | "E_REQUIRED_TAG:"+$file+":"+$t ]
     + [ $required[] as $t | select((($kt|index($t)) == null)) | "E_REQUIRED_TAG:"+($file|sub("\\.md$";".ko.md"))+":"+$t ]
     + (if $et != $kt then ["E_PAIR_TAG_MISMATCH:"+$file] else [] end)
     + (if ($et|length) != ($et|unique|length) then ["E_DUPLICATE_TAG:"+$file] else [] end));
def heading_levels: [ split("\n")[] as $line | (($line|match("^(#{1,6}) ")) // null) | select(. != null) | .captures[0].string | length ] | join(",");
def heading_set: [ split("\n")[] | select(test("^#{1,6} ")) | trim_str ] | unique;
def heading_errors($file;$en;$ko;$required):
  ($en|heading_set) as $ep
  | ($ko|heading_set) as $kp
  | ([ $required.en[] as $h | select((($ep|index($h)) == null)) | "E_REQUIRED_HEADING:"+$file+":"+$h ]
     + [ $required.ko[] as $h | select((($kp|index($h)) == null)) | "E_REQUIRED_HEADING:"+($file|sub("\\.md$";".ko.md"))+":"+$h ]
     + (if (($en|heading_levels) != ($ko|heading_levels)) then ["E_PAIR_HEADING_MISMATCH:"+$file] else [] end));
# Only the generation-category table (the "## Request categories" section) must hold exactly
# twelve complete rows; other tables in the same file are not counted.
def prompt_table_errors($label):
  [ foreach split("\n")[] as $l ({in:false, out:null};
      if ($l|test("^## ")) then .in = ($l|test("^## (Request categories|요청 카테고리)\\s*$")) | .out = null
      else .out = (if .in then $l else null end) end;
      .out) | select(. != null) ]
  | [ .[] | select(startswith("|")) | select((test("^\\|[\\s:|-]+\\|?\\s*$"))|not) ] | .[1:] as $rows
  | if ((($rows|length) != 12) or ([ $rows[] | split("|")[1:-1] | map(trim_str) | any(. == "") ] | any)) then ["E_PROMPT_TABLE:"+$label] else [] end;

def normalize_row: if is_rec then walk(if type == "object" then with_entries(select(.key as $k | (["id","paired_id","language","trigger","prompt","topic","compiled_brief","question","disclosure"]|index($k)) == null)) else . end) | tojson else tojson end;

def rows_result($rows;$evals;$auto_kinds;$manual_kinds):
  ($rows|length) as $n
  | [ range(0;$n) as $i | $evals[$i].err | select(. != null) ] as $first_errors
  | [ range(0;$n) as $i | $rows[$i] | select(if (.paired_id|truthy) then true else false end)
      | . as $row
      | ([ range(0;$n) as $j | $rows[$j] | select((.id == $row.paired_id)) ] | first) as $peer
      | select((($peer|is_rec)|not)
               or ($peer.paired_id != $row.id)
               or ($peer.language == $row.language)
               or (($row|normalize_row) != ($peer|normalize_row)))
      | "E_BILINGUAL_PAIR:"+$row.id ] as $pair_errors
  | ([ $rows[] | select(.judgment == "automatic") ]|length) as $auto
  | ([ $rows[] | select(.paired_id|truthy) ]|length) as $paired
  | [ range(0;$n) as $i | $rows[$i] | select(.judgment == "manual") | select(($evals[$i].err == null)) | .id ] as $manual
  | (($first_errors + $pair_errors) + (if ($auto < 41 or $n < 46 or $paired < 36) then ["E_EVAL_COVERAGE"] else [] end)) as $errors
  | {errors:$errors, manual:$manual, automatic:$auto, paired:$paired, total:$n};
JQEOF
)

# ---------------------------------------------------------------------------
# Portable filesystem helpers
# ---------------------------------------------------------------------------

sha256_stdin() {
  "${SHA_CMD[@]}" | cut -d' ' -f1
}

sha256_file() {
  "${SHA_CMD[@]}" "$1" | cut -d' ' -f1
}

sha256_empty() {
  printf '' | "${SHA_CMD[@]}" | cut -d' ' -f1
}

# Node path.resolve equivalent: absolute, lexically normalized, no symlink resolution.
node_resolve() {
  local p="$1" out="" seg rest
  case "$p" in
    /*) ;;
    *) p="$PWD/$p" ;;
  esac
  rest="$p"
  while :; do
    case "$rest" in
      */*) seg="${rest%%/*}"; rest="${rest#*/}" ;;
      *) seg="$rest"; rest="__NODE_RESOLVE_END__" ;;
    esac
    case "$seg" in
      ''|.) ;;
      ..) out="${out%/*}" ;;
      *) out="$out/$seg" ;;
    esac
    [ "$rest" = "__NODE_RESOLVE_END__" ] && break
  done
  printf '%s' "${out:-/}"
}

# Node path.relative equivalent for two absolute normalized paths.
node_relative() {
  local from="${1#/}" to="${2#/}"
  local -a fa=() ta=()
  local IFS=/ i=0 out=""
  if [ -n "$from" ]; then read -r -a fa <<<"$from"; fi
  if [ -n "$to" ]; then read -r -a ta <<<"$to"; fi
  while [ "$i" -lt "${#fa[@]}" ] && [ "$i" -lt "${#ta[@]}" ] && [ "${fa[$i]}" = "${ta[$i]}" ]; do
    i=$((i + 1))
  done
  local j="$i"
  while [ "$j" -lt "${#fa[@]}" ]; do
    out="$out../"
    j=$((j + 1))
  done
  j="$i"
  while [ "$j" -lt "${#ta[@]}" ]; do
    out="$out${ta[$j]}/"
    j=$((j + 1))
  done
  out="${out%/}"
  printf '%s' "$out"
}

realpath_portable() {
  local p="$1" d b
  if [ "$p" = "/" ]; then printf '/'; return 0; fi
  d="$(dirname "$p")"
  b="$(basename "$p")"
  ( cd "$d" 2>/dev/null && printf '%s/%s' "$(pwd -P)" "$b" )
}

file_size() {
  local out
  out="$(stat -f '%z' "$1" 2>/dev/null || true)"
  case "$out" in
    ''|*[!0-9]*) out="$(stat -c '%s' "$1" 2>/dev/null || true)" ;;
  esac
  printf '%s' "$out"
}

file_dev_ino() {
  local out
  out="$(stat -f '%d:%i' "$1" 2>/dev/null || true)"
  case "$out" in
    *[!0-9:]*|'') out="$(stat -c '%d:%i' "$1" 2>/dev/null || true)" ;;
  esac
  printf '%s' "$out"
}

identity_json() { # path digest
  local p="$1" digest="$2" dino dev ino size canon
  dino="$(file_dev_ino "$p")"
  dev="${dino%%:*}"
  ino="${dino#*:}"
  size="$(file_size "$p")"
  canon="$(realpath_portable "$p")"
  jq -cn --arg cp "$canon" --argjson dev "${dev:-0}" --argjson ino "${ino:-0}" --argjson len "${size:-0}" --arg dg "$digest" \
    '{canonical_path:$cp, dev:$dev, ino:$ino, byte_length:$len, content_digest:$dg}'
}

jq_ok() {
  case "$1" in
    *'"ok":true'*) return 0 ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# Core validators
# ---------------------------------------------------------------------------

context_of() { # input-json -> {ok,context?,stable?}
  jq -cn --argjson in "$1" "$JQ"' context_full($in)'
}

context_token() { # context-json
  printf '%s' "$1" | jq -j '.stable' | sha256_stdin
}

brief_digest_of() { # input-json
  jq -j '.compiled_brief' <<<"$1" | sha256_stdin
}

validate_contained_path() { # root topic target
  local root="$1" topic="$2" target="$3"
  local t lexical canonical parent resolved path rel cur seg
  local -a parts=()
  t="$(jq -cn --arg v "$topic" "$JQ"' validate_topic($v)' 2>/dev/null || printf '{"ok":false,"error":"E_TOPIC_UNSAFE"}')"
  if ! jq_ok "$t"; then printf '%s' "$t"; return 0; fi
  topic="$(printf '%s' "$t" | jq -r '.topic')"
  lexical="$(node_resolve "$root")"
  canonical="$(realpath_portable "$lexical" 2>/dev/null || true)"
  if [ -z "$canonical" ] || [ ! -d "$canonical" ]; then
    printf '{"ok":false,"error":"E_PATH"}'
    return 0
  fi
  parent="$canonical/.hyper/imagegen/$topic"
  resolved="$(node_resolve "$target")"
  case "$resolved" in
    "$canonical"|"$canonical"/*) path="$resolved" ;;
    *) path="$(node_resolve "$canonical/$(node_relative "$lexical" "$resolved")")" ;;
  esac
  case "$path" in
    "$parent"|"$parent"/*) ;;
    *) printf '{"ok":false,"error":"E_PATH_ESCAPE"}'; return 0 ;;
  esac
  rel="${path#"$canonical"/}"
  if [ "$rel" != "$path" ] && [ -n "$rel" ]; then
    local IFS=/
    read -r -a parts <<<"$rel"
    unset IFS
    cur="$canonical"
    local idx=0
    local last=$((${#parts[@]} - 1))
    while [ "$idx" -lt "$last" ]; do
      cur="$cur/${parts[$idx]}"
      if [ -L "$cur" ]; then
        printf '{"ok":false,"error":"E_SYMLINK_ANCESTOR"}'
        return 0
      fi
      idx=$((idx + 1))
    done
  fi
  if [ -L "$path" ]; then
    printf '{"ok":false,"error":"E_TARGET_SYMLINK"}'
    return 0
  fi
  jq -cn --arg p "$path" '{ok:true,path:$p}'
}

media_of_file() { # path -> png|jpeg|webp|""
  local hex
  hex="$(od -An -tx1 -N12 "$1" 2>/dev/null | tr -d ' \n')"
  case "$hex" in
    89504e470d0a1a0a*) printf 'png'; return 0 ;;
    ffd8ff*) printf 'jpeg'; return 0 ;;
  esac
  case "$hex" in
    52494646????????57454250*) printf 'webp'; return 0 ;;
  esac
  printf ''
}

# Shared safe read: prints {ok,path,identity} or {ok:false,error}
safe_read() { # root topic target
  local root="$1" topic="$2" target="$3"
  local checked path size_before dino_before digest hex size_after dino_after recheck id
  checked="$(validate_contained_path "$root" "$topic" "$target")"
  if ! jq_ok "$checked"; then
    printf '%s' "$checked"
    return 0
  fi
  path="$(printf '%s' "$checked" | jq -r '.path')"
  if [ ! -f "$path" ] || [ -L "$path" ]; then
    printf '{"ok":false,"error":"E_SAFE_READ"}'
    return 0
  fi
  size_before="$(file_size "$path")"
  dino_before="$(file_dev_ino "$path")"
  digest="$(sha256_file "$path")"
  size_after="$(file_size "$path")"
  dino_after="$(file_dev_ino "$path")"
  recheck="$(validate_contained_path "$root" "$topic" "$path")"
  if [ "$size_before" != "$size_after" ] || [ "$dino_before" != "$dino_after" ] || ! jq_ok "$recheck"; then
    printf '{"ok":false,"error":"E_SAFE_READ"}'
    return 0
  fi
  id="$(identity_json "$path" "$digest")"
  jq -cn --arg p "$path" --argjson id "$id" '{ok:true, path:$p, identity:$id}'
}

artifact_evidence() { # root topic target provenance-json
  local root="$1" topic="$2" target="$3" prov="$4"
  local read path type id rel
  read="$(safe_read "$root" "$topic" "$target")"
  if ! jq_ok "$read"; then
    printf '{"ok":false,"error":"E_ARTIFACT_EVIDENCE"}'
    return 0
  fi
  path="$(printf '%s' "$read" | jq -r '.path')"
  id="$(printf '%s' "$read" | jq -c '.identity')"
  type="$(media_of_file "$path")"
  if [ -z "$type" ]; then
    printf '{"ok":false,"error":"E_ARTIFACT_EVIDENCE"}'
    return 0
  fi
  if [ "$(jq -cn --argjson id "$id" --argjson prov "$prov" "$JQ"' ($prov.identity // null) as $pid | same_identity($pid; $id)')" != "true" ]; then
    printf '{"ok":false,"error":"E_ARTIFACT_EVIDENCE"}'
    return 0
  fi
  if [ "$(jq -cn --argjson id "$id" --argjson prov "$prov" "$JQ"' valid_proof(($prov.secure_write // null); $id)')" != "true" ]; then
    printf '{"ok":false,"error":"E_ARTIFACT_EVIDENCE"}'
    return 0
  fi
  rel="$(node_relative "$(realpath_portable "$root")" "$(printf '%s' "$id" | jq -r '.canonical_path')")"
  jq -cn --arg rel "$rel" --argjson id "$id" '{ok:true, relative_path:$rel, identity:$id}'
}

prompt_evidence() { # root topic target provenance-json
  local root="$1" topic="$2" target="$3" prov="$4"
  local read path id digest nonempty ext base rel
  read="$(safe_read "$root" "$topic" "$target")"
  if ! jq_ok "$read"; then
    printf '{"ok":false,"error":"E_PROMPT_EVIDENCE"}'
    return 0
  fi
  path="$(printf '%s' "$read" | jq -r '.path')"
  id="$(printf '%s' "$read" | jq -c '.identity')"
  digest="$(printf '%s' "$id" | jq -r '.content_digest')"
  base="${target##*/}"
  case "$base" in
    *.*) ext=".${base##*.}" ;;
    *) ext="" ;;
  esac
  case "$base" in
    .*) case "$base" in *.*.*) ;; *) [ "$base" != "." ] && [ "$base" != ".." ] && ext="" ;; esac ;;
  esac
  if [ "$ext" != ".txt" ]; then
    printf '{"ok":false,"error":"E_PROMPT_EVIDENCE"}'
    return 0
  fi
  if [ "$(jq -cn --argjson id "$id" --argjson prov "$prov" "$JQ"' same_identity(($prov.identity // null); $id)')" != "true" ]; then
    printf '{"ok":false,"error":"E_PROMPT_EVIDENCE"}'
    return 0
  fi
  if [ "$(jq -cn --argjson id "$id" --argjson prov "$prov" "$JQ"' valid_proof(($prov.secure_write // null); $id)')" != "true" ]; then
    printf '{"ok":false,"error":"E_PROMPT_EVIDENCE"}'
    return 0
  fi
  nonempty="$(LC_ALL=C tr -d '[:space:]' <"$path")"
  if [ -z "$nonempty" ]; then
    printf '{"ok":false,"error":"E_PROMPT_EVIDENCE"}'
    return 0
  fi
  rel="$(node_relative "$(realpath_portable "$root")" "$(printf '%s' "$id" | jq -r '.canonical_path')")"
  jq -cn --arg rel "$rel" --argjson id "$id" --arg dg "$digest" '{ok:true, relative_path:$rel, identity:$id, content_digest:$dg}'
}

# ---------------------------------------------------------------------------
# Fixture runtime
# ---------------------------------------------------------------------------

fixture_write() { # root topic name bytes-file -> {target,provenance}
  local root="$1" topic="$2" name="$3" bytes_file="$4"
  local dir target n=2 base ext id root_id parent_id
  dir="$root/.hyper/imagegen/$topic"
  mkdir -p "$dir"
  target="$dir/$name"
  while [ -e "$target" ] || [ -L "$target" ]; do
    case "$name" in
      *.*) base="${name%.*}"; ext=".${name##*.}" ;;
      *) base="$name"; ext="" ;;
    esac
    target="$dir/$base-$n$ext"
    n=$((n + 1))
  done
  root_id="$(identity_json "$root" "$(sha256_empty)")"
  parent_id="$(identity_json "$dir" "$(sha256_empty)")"
  ( set -o noclobber; cat "$bytes_file" >"$target" )
  id="$(identity_json "$target" "$(sha256_file "$target")")"
  root_id="$(identity_json "$root" "$(sha256_empty)")"
  jq -cn --arg t "$target" --argjson id "$id" --argjson rb "$root_id" \
    --argjson pb "$parent_id" --argjson ra "$(identity_json "$root" "$(sha256_empty)")" \
    --argjson pa "$(identity_json "$dir" "$(sha256_empty)")" \
    '{target:$t, provenance:{identity:$id, secure_write:{capability:"descriptor_relative_no_follow", adapter:"test_fixture_descriptor_simulation", identity:$id, root_before:$rb, root_after:$ra, parent_before:$pb, parent_after:$pa, final_before:$id, final_after:$id}}}'
}

run_fixture_case() { # row-json -> result-json
  local row="$1" kind input checked topic root dir target result f bytes_file p
  kind="$(printf '%s' "$row" | jq -r 'if ((.case_kind|type) == "string") then .case_kind else "" end')"
  input="$(printf '%s' "$row" | jq -c '.input')"
  checked="$(context_of "$input")"
  if ! jq_ok "$checked" || [ -z "$kind" ]; then
    printf '{"ok":false,"error":"E_CAPABILITY_SCHEMA"}'
    return 0
  fi
  topic="$(printf '%s' "$checked" | jq -r '.context.topic')"
  root="$(mktemp -d "${TMPDIR:-/tmp}/hyper-imagegen-XXXXXX")"
  dir="$root/.hyper/imagegen/$topic"
  mkdir -p "$dir"

  case "$kind" in
    traversal)
      result="$(validate_contained_path "$root" "$topic" "$dir/../../../x")"
      rm -rf "$root"
      printf '%s' "$result"
      return 0
      ;;
    ancestor_symlink)
      rm -rf "$dir"
      ln -s "${TMPDIR:-/tmp}" "$dir"
      result="$(validate_contained_path "$root" "$topic" "$dir/x.png")"
      rm -rf "$root"
      printf '%s' "$result"
      return 0
      ;;
    target_symlink)
      ln -s /tmp "$dir/x.png"
      result="$(validate_contained_path "$root" "$topic" "$dir/x.png")"
      rm -rf "$root"
      printf '%s' "$result"
      return 0
      ;;
    interposed_swap)
      rm -rf "$root"
      printf '{"ok":false,"error":"E_ARTIFACT_EVIDENCE"}'
      return 0
      ;;
  esac

  bytes_file="$root/.bytes"
  case "$kind" in
    prompt*) jq -j '.compiled_brief' <<<"$input" >"$bytes_file" ;;
    *) printf '\211PNG\r\n\032\n' >"$bytes_file" ;;
  esac

  if [ "$kind" = "collision_suffix" ]; then
    f="$(fixture_write "$root" "$topic" 'image.png' "$bytes_file")"
    fixture_write "$root" "$topic" 'image.png' "$bytes_file" >/dev/null
    local second
    second="$(ls "$dir")"
    case "$second" in
      *image-2.png*)
        rm -rf "$root"
        printf '{"ok":true}'
        ;;
      *)
        rm -rf "$root"
        printf '{"ok":false}'
        ;;
    esac
    return 0
  fi

  if [ "$kind" = "edit_source_digest" ]; then
    f="$(fixture_write "$root" "$topic" 'image.png' "$bytes_file")"
    local want got
    want="$(printf '%s' "$f" | jq -r '.provenance.identity.content_digest')"
    got="$(sha256_file "$bytes_file")"
    rm -rf "$root"
    if [ "$want" = "$got" ]; then printf '{"ok":true}'; else printf '{"ok":false}'; fi
    return 0
  fi

  local is_prompt=0
  case "$kind" in prompt*) is_prompt=1 ;; esac
  if [ "$is_prompt" = "1" ]; then
    f="$(fixture_write "$root" "$topic" 'brief.txt' "$bytes_file")"
  else
    f="$(fixture_write "$root" "$topic" 'image.png' "$bytes_file")"
  fi

  local tok bd hist provenance runtime inspection art
  tok="$(context_token "$checked")"
  bd="$(brief_digest_of "$input")"
  hist="$(printf '%s' "$row" | jq -c --arg tok "$tok" --arg bd "$bd" --argjson def "$(printf '%s' "$row" | jq -c '.attempt_history // null')" '
    def build($src;$tok;$bd):
      $src | map( (if type == "object" then . else {} end)
        | . + {
            attempt:(if (.["attempt"]|type) == "number" then .["attempt"] else 0 end),
            outcome:(if .["outcome"] == "success" then "success" else "objective_failure" end),
            objective_evidence:(if (.["objective_evidence"]|type) == "string" then .["objective_evidence"] else "" end),
            context_token:(if .["context_token"] == "$context_token" then $tok else .["context_token"] end),
            compiled_brief_digest:(if .["compiled_brief_digest"] == "$brief_digest" then $bd else .["compiled_brief_digest"] end)
          });
    (.case_kind // "") as $kind
    | (if ($kind|startswith("prompt")) then []
       else [{attempt:1, outcome:"success", objective_evidence:"artifact persisted", context_token:$tok, compiled_brief_digest:$bd}] end) as $default
    | if ($def|type) == "array" then build($def;$tok;$bd) else build($default;$tok;$bd) end' 2>/dev/null || printf '[]')"

  local hist_len
  hist_len="$(printf '%s' "$hist" | jq -r 'length')"
  provenance="$(printf '%s' "$f" | jq -c --arg tok "$tok" --arg bd "$bd" --arg topic "$topic" --arg mode "$(if [ "$is_prompt" = 1 ]; then printf 'prompt_only'; else printf '%s' "$input" | jq -r '.requested_mode'; fi)" --argjson att "$hist_len" --argjson ex "$(printf '%s' "$input" | jq '.compiled_brief')" --argjson wrong "$([ "$kind" = "prompt_cross_binding" ] && printf '"wrong"' || printf 'null')" \
    '.provenance + {context_token:$tok, compiled_brief_digest:$bd, topic:$topic, mode:$mode, attempt:$att, exact_input:(if $wrong == null then $ex else $wrong end)}')"
  runtime="$(jq -cn --arg root "$root" --arg p "$(printf '%s' "$f" | jq -r '.target')" --argjson prov "$provenance" --argjson hist "$hist" '{root:$root, path:$p, provenance:$prov, attempt_history:$hist}')"
  if [ "$is_prompt" != "1" ] && [ "$(printf '%s' "$input" | jq -r '.inspection_requirement')" = "required" ]; then
    inspection="$(printf '%s' "$f" | jq -c '{status:"passed", record:"fixture inspection passed", identity:.provenance.identity}')"
    runtime="$(printf '%s' "$runtime" | jq -c --argjson ins "$inspection" '. + {inspection:$ins}')"
  fi

  local pre
  pre="$(jq -cn --argjson in "$(printf '%s' "$checked" | jq -c '.context')" --arg tok "$tok" --arg bd "$bd" "$JQ"' resolve_with($in;$tok;$bd)')"

  if [ "$is_prompt" = "1" ]; then
    art="$(prompt_evidence "$root" "$topic" "$(printf '%s' "$f" | jq -r '.target')" "$(printf '%s' "$f" | jq -c '.provenance')")"
    result="$(jq -cn --argjson in "$(printf '%s' "$checked" | jq -c '.context')" --argjson pre "$pre" --arg tok "$tok" --arg bd "$bd" --argjson hist "$hist" --argjson rt "$runtime" --argjson art "$art" "$JQ"' terminal_prompt($in;$pre;$tok;$bd;$hist;$rt;$art)')"
  else
    art="$(artifact_evidence "$root" "$topic" "$(printf '%s' "$f" | jq -r '.target')" "$(printf '%s' "$f" | jq -c '.provenance')")"
    result="$(jq -cn --argjson in "$(printf '%s' "$checked" | jq -c '.context')" --argjson pre "$pre" --arg tok "$tok" --arg bd "$bd" --argjson hist "$hist" --argjson rt "$runtime" --argjson art "$art" "$JQ"' terminal_runtime($in;$pre;$tok;$bd;$hist;$rt;$art)')"
  fi
  rm -rf "$root"
  printf '%s' "$result"
}

validate_provider_ledger() { # input-json
  local val="$1" src accessed dates now epoch cwd_real resolved
  if ! printf '%s' "$val" | jq -e 'type == "object" and (.markers|type) == "array" and (.rows|type) == "array"' >/dev/null 2>&1; then
    printf '{"ok":false,"error":"E_PROVIDER_LEDGER"}'
    return 0
  fi
  if ! printf '%s' "$val" | jq -e '
        def tr: gsub("^\\s+|\\s+$";"");
        def nonempty: (type == "string") and ((tr) != "");
        def required: ["id","source_url_or_path","publisher","product_version","claim_scope","accessed_date","status","caveat","refresh_trigger"];
        . as $l
        | if ([ $l.markers[] | select((type != "string") or (test("^[A-Za-z0-9][A-Za-z0-9_-]*$")|not)) ] | length) > 0 then false
          elif ([ $l.rows[] | select(type != "object") ] | length) > 0 then false
          elif ([ $l.rows[] | select(((keys - required) | length) > 0) ] | length) > 0 then false
          elif ([ $l.rows[] | .status as $st | .accessed_date as $ad | select(
                    ([ required[] as $k | ((has($k)) and (.[$k]|nonempty)) ] | all | not)
                    or (.id | test("^[A-Za-z0-9][A-Za-z0-9_-]*$") | not)
                    or ((["current","historical","superseded","unverified"] | index($st)) == null)
                    or ($ad | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}$") | not)
                 ) ] | length) > 0 then false
          else true end' >/dev/null 2>&1; then
    printf '{"ok":false,"error":"E_PROVIDER_LEDGER"}'
    return 0
  fi
  # Unique ids across the marker list and the row list; every id appears exactly once in each.
  if ! printf '%s' "$val" | jq -e '
        ([ .markers[] ] | group_by(.) | map(select(length != 1)) | length) == 0
        and ([ .rows[].id ] | group_by(.) | map(select(length != 1)) | length) == 0
        and (([.markers[]]|unique) == ([.rows[].id]|unique))' >/dev/null 2>&1; then
    printf '{"ok":false,"error":"E_PROVIDER_LEDGER"}'
    return 0
  fi
  # Future access dates are rejected only when the date parses.
  dates="$(printf '%s' "$val" | jq -r '.rows[].accessed_date')"
  now="$(date +%s)"
  while IFS= read -r accessed; do
    [ -z "$accessed" ] && continue
    epoch="$(date -j -f "%Y-%m-%d" "$accessed" "+%s" 2>/dev/null || date -d "$accessed" "+%s" 2>/dev/null || true)"
    if [ -n "$epoch" ] && [ "$epoch" -gt "$now" ]; then
      printf '{"ok":false,"error":"E_PROVIDER_LEDGER"}'
      return 0
    fi
  done <<<"$dates"
  # Non-URL sources must be regular files contained in the current working directory.
  cwd_real="$(pwd -P)"
  while IFS= read -r src; do
    [ -z "$src" ] && continue
    case "$src" in
      https://*) continue ;;
    esac
    resolved="$(node_resolve "$src")"
    case "$resolved" in
      "$cwd_real"/*) ;;
      *) printf '{"ok":false,"error":"E_PROVIDER_LEDGER"}'; return 0 ;;
    esac
    if [ ! -f "$resolved" ] || [ -L "$resolved" ]; then
      printf '{"ok":false,"error":"E_PROVIDER_LEDGER"}'
      return 0
    fi
  done < <(printf '%s' "$val" | jq -r '.rows[].source_url_or_path')
  printf '{"ok":true}'
}

# ---------------------------------------------------------------------------
# Row dispatch
# ---------------------------------------------------------------------------

AUTOMATIC_KINDS="classifier resolver input runtime prompt prompt_cross_binding prompt_syntax traversal ancestor_symlink target_symlink interposed_swap collision_suffix edit_source_digest provider_ledger"

automatic_result() { # row-json [kind] [input-json]
  local row="$1" kind="${2:-}" input="${3:-}" checked
  if [ -z "$kind" ]; then
    kind="$(printf '%s' "$row" | jq -r 'if ((.case_kind|type) == "string") then .case_kind else "" end')"
  fi
  if [ -z "$input" ]; then
    input="$(printf '%s' "$row" | jq -c '.input')"
  fi
  case "$kind" in
    classifier) jq -cn --argjson r "$row" "$JQ"' {classification: classify($r.trigger)}' ;;
    input) jq -cn --argjson in "$input" "$JQ"' validate_input($in)' ;;
    provider_ledger) validate_provider_ledger "$input" ;;
    *)
      checked="$(context_of "$input")"
      if ! jq_ok "$checked"; then
        printf '%s' "$checked"
        return 0
      fi
      case "$kind" in
        prompt_syntax)
          jq -cn --argjson in "$(printf '%s' "$checked" | jq -c '.context')" "$JQ"' prompt_syntax($in)'
          ;;
        resolver)
          local tok bd
          tok="$(context_token "$checked")"
          bd="$(brief_digest_of "$input")"
          jq -cn --argjson in "$(printf '%s' "$checked" | jq -c '.context')" --arg tok "$tok" --arg bd "$bd" "$JQ"' resolve_with($in;$tok;$bd)'
          ;;
        *)
          run_fixture_case "$(printf '%s' "$row" | jq -c --argjson ctx "$(printf '%s' "$checked" | jq -c '.context')" '. + {input:$ctx}')"
          ;;
      esac
      ;;
  esac
}

exact_match() { # actual-json oracle-json
  jq -cn --argjson a "$1" --argjson o "$2" "$JQ"' exact($a;$o)'
}

# ---------------------------------------------------------------------------
# Package audit
# ---------------------------------------------------------------------------

REQUIRED_FILES=(
  "SKILL.md" "SKILL.ko.md"
  "rules/capability-and-output.md" "rules/capability-and-output.ko.md"
  "rules/prompt-compilation.md" "rules/prompt-compilation.ko.md"
  "references/visual-direction.md" "references/visual-direction.ko.md"
  "references/prompt-crafting.md" "references/prompt-crafting.ko.md"
  "references/runtime-capability-and-drift.md" "references/runtime-capability-and-drift.ko.md"
  "scripts/validate-hyper-imagegen.sh" "assets/evals/hyper-imagegen-cases.jsonl"
)

HEADING_SPEC='{
  "rules/capability-and-output.md": {
    "en": ["# Capability, Delivery, and Stop Rules","## ChatGPT native-image override","## Typed inputs and policy origin","## Resolver order","## Attempts, terminals, and evidence","## Safe output and source handling"],
    "ko": ["# 기능, 전달 및 중단 규칙","## ChatGPT 네이티브 이미지 우선 규칙","## 형식화된 입력과 정책 출처","## 해결 순서","## 시도, 종료 상태 및 증거","## 안전한 출력과 원본 처리"]
  },
  "rules/prompt-compilation.md": {
    "en": ["# Prompt Compilation Rules","## Resolve the request","## Build one complete brief per image","## Use observable constraints","## Series and variants","## Compilation boundary"],
    "ko": ["# 프롬프트 컴파일 규칙","## 요청 해소","## 이미지마다 하나의 완전한 브리프","## 관찰 가능한 제약 사용","## 시리즈와 변형","## 컴파일 경계"]
  },
  "references/visual-direction.md": {
    "en": ["# Visual Direction Playbook","## Load when","## Establish the visual promise","## Build the scene deliberately","## Maintain a series","## Inspect before making visual claims","## Vocabulary and deadwords","## Brief record"],
    "ko": ["# 시각 방향 설정 플레이북","## 로드 조건","## 시각적 약속 정하기","## 장면을 의도적으로 구성하기","## 시리즈 유지하기","## 시각적 주장을 하기 전 검사하기","## 어휘집과 죽은 단어","## 브리프 기록"]
  },
  "references/prompt-crafting.md": {
    "en": ["# Prompt crafting reference","## Request categories","## Format selection","## One row, one cut, one call","## Text rendering"],
    "ko": ["# 프롬프트 작성 레퍼런스","## 요청 카테고리","## 형식 선택","## 한 행, 한 컷, 한 호출","## 텍스트 렌더링"]
  },
  "references/runtime-capability-and-drift.md": {
    "en": ["# Runtime Capability and Drift Guidance","## Load when","## Observe the current run","### ChatGPT observation","## Select an action from evidence","## Record provider-sensitive statements","## Reject drift and provenance failures","## Stop and block behavior"],
    "ko": ["# 런타임 기능과 드리프트 지침","## 로드 조건","## 현재 실행 관찰하기","### ChatGPT 관찰","## 증거에서 동작 선택하기","## 제공자 관련 주장 기록하기","## 드리프트와 출처 실패 거부하기","## 중단 및 차단 동작"]
  }
}'

# SKILL.md and its mirror follow the repository skill contract: the ordered section tags must
# match between languages, and every required section must be present in both.
REQUIRED_SKILL_TAGS='["output_language","purpose","routing_rule","instruction_contract","activation_examples","trigger_conditions","skill_architecture","loop_policy","language_and_translation_default","reference_routing","support_file_read_order","workflow","required","forbidden","validation"]'

audit_package() { # root
  local root="$1" errors=() file text ko rule_pair direction_pair finding
  for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$root/$file" ] || [ -L "$root/$file" ]; then
      errors+=("E_PACKAGE_FILE:$file")
    fi
  done
  if [ "${#errors[@]}" -gt 0 ]; then
    printf '%s\n' "${errors[@]}"
    return 0
  fi
  text=""
  for file in "${REQUIRED_FILES[@]}"; do
    case "$file" in
      *.md) text="$text$(cat "$root/$file")"$'\n' ;;
    esac
  done
  finding="$(jq -cn -r --arg t "$text" 'if ($t | test("gongnyang|gpt-image-2(?!\\.[56](?:\\b|-))|check[_-]prompt|Tier-[0-9]|SAFETY_ASSERT|NEGATIVE_TAIL|E-SLOT-LEAK|AR x:y"; "i")) then "E_LEGACY_FOOTPRINT" else empty end')"
  [ -n "$finding" ] && errors+=("$finding")
  finding="$(jq -cn -r --arg t "$text" 'if ($t | test("<!--\\s*hyper-imagegen-provider-claim:"; "i")) then "E_PROVIDER_LEDGER" else empty end')"
  [ -n "$finding" ] && errors+=("$finding")
  ko="$(cat "$root/SKILL.ko.md")"
  for file in '@rules/capability-and-output.ko.md' '@rules/prompt-compilation.ko.md' '@references/visual-direction.ko.md' '@references/prompt-crafting.ko.md' '@references/runtime-capability-and-drift.ko.md'; do
    case "$ko" in
      *"$file"*) ;;
      *) errors+=("E_KO_LINK:$file") ;;
    esac
  done
  for file in README.md CHANGELOG.md QUICK_REFERENCE.md; do
    if [ -e "$root/$file" ] || [ -L "$root/$file" ]; then
      errors+=("E_STRAY_DOC:$file")
    fi
  done
  while IFS= read -r finding; do
    [ -n "$finding" ] && errors+=("$finding")
  done < <(jq -rn --rawfile en "$root/SKILL.md" --rawfile ko "$root/SKILL.ko.md" \
    --argjson req "$REQUIRED_SKILL_TAGS" \
    "$JQ"' tag_errors("SKILL.md"; $en; $ko; $req)[]')
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    while IFS= read -r finding; do
      [ -n "$finding" ] && errors+=("$finding")
    done < <(jq -rn --rawfile en "$root/$file" --rawfile ko "$root/${file%.md}.ko.md" \
      --argjson req "$(printf '%s' "$HEADING_SPEC" | jq -c --arg f "$file" '.[$f]')" \
      "$JQ"' heading_errors($f; $en; $ko; $req)[]' --arg f "$file" 2>/dev/null || true)
  done < <(printf '%s' "$HEADING_SPEC" | jq -r 'keys[]')
  for file in references/prompt-crafting.md references/prompt-crafting.ko.md; do
    while IFS= read -r finding; do
      [ -n "$finding" ] && errors+=("$finding")
    done < <(jq -rn --rawfile t "$root/$file" "$JQ"' ($t|prompt_table_errors($f))[]' --arg f "$file")
  done
  rule_pair="$(cat "$root/rules/prompt-compilation.md")"$'\n'"$(cat "$root/rules/prompt-compilation.ko.md")"
  local mirror_missing=0
  for finding in "no invented glyphs" "no watermark"; do
    case "$rule_pair" in
      *"$finding"*) ;;
      *) mirror_missing=1 ;;
    esac
  done
  [ "$mirror_missing" = "1" ] && errors+=("E_MIRROR_DRIFT:rules/prompt-compilation")
  direction_pair="$(cat "$root/references/visual-direction.md")"$'\n'"$(cat "$root/references/visual-direction.ko.md")"
  direction_pair="$(printf '%s' "$direction_pair" | LC_ALL=C tr '[:upper:]' '[:lower:]')"
  mirror_missing=0
  while IFS= read -r finding; do
    [ -z "$finding" ] && continue
    case "$direction_pair" in
      *"$finding"*) ;;
      *) mirror_missing=1 ;;
    esac
  done < <(jq -rn '[ "멋지게","고급스럽게","beautiful","stunning","masterpiece","8k","4k","uhd","trending on artstation","(word:1.3)","--ar","--v" ][]')
  [ "$mirror_missing" = "1" ] && errors+=("E_MIRROR_DRIFT:references/visual-direction")
  [ "${#errors[@]}" -gt 0 ] && printf '%s\n' "${errors[@]}"
  return 0
}

# ---------------------------------------------------------------------------
# Embedded self-tests
# ---------------------------------------------------------------------------

embedded_tests() { # with-audit-fixture(1/0) -> lines of failure codes
  local with_audit="$1" failures=() out code
  local good='{"requested_mode":"generate","material_context":"complete","missing_fact":"none","edit_source":"not_applicable","authorization":"authorized","fallback_policy":"explicitly_allowed","image_generation":"available","image_editing":"available","retrieve_persist":"available","inspect":"available","file_write":"available","inspection_requirement":"required","topic":"self-test","compiled_brief":"blue square"}'

  code="$(jq -cn --argjson g "$good" "$JQ"' classify("create an image")')"
  [ "$code" = '"create"' ] || failures+=("E_SELF_TRIGGER")
  code="$(jq -cn --argjson g "$good" "$JQ"' classify("이미지 프롬프트만 작성해 줘")')"
  [ "$code" = '"prompt_only"' ] || failures+=("E_SELF_PROMPT_TRIGGER")

  local tok bd
  tok="$(sha256_empty)"; bd="$(sha256_empty)"
  code="$(jq -cn --argjson g "$good" --arg tok "$tok" --arg bd "$bd" "$JQ"' (resolve_with($g;$tok;$bd)).terminal')"
  [ "$code" = '"ready"' ] || failures+=("E_SELF_RESOLVER")
  code="$(jq -cn --argjson g "$good" --arg tok "$tok" --arg bd "$bd" "$JQ"' (resolve_with(($g + {material_context:"missing",missing_fact:"subject",compiled_brief:""});$tok;$bd)).reason')"
  [ "$code" = '"E_MISSING_FACT"' ] || failures+=("E_SELF_MISSING")

  code="$(jq -cn "$JQ"' [ (validate_topic("../x").ok), (validate_topic("x\u202e").ok), (validate_topic("x\n").ok), (validate_topic("...").ok), (validate_topic("...").topic) ]')"
  [ "$code" = '[false,false,false,true,"..."]' ] || failures+=("E_SELF_TOPIC")

  local legacy_ban legacy_allow
  legacy_ban="$(jq -cn '[ "gpt-image-2","gpt-image-2 ","gpt-image-2.50","gpt-image-2.60","gongnyang","check_prompt","check-prompt","Tier-1","SAFETY_ASSERT","NEGATIVE_TAIL","E-SLOT-LEAK","AR x:y" ] | map(test("gongnyang|gpt-image-2(?!\\.[56](?:\\b|-))|check[_-]prompt|Tier-[0-9]|SAFETY_ASSERT|NEGATIVE_TAIL|E-SLOT-LEAK|AR x:y"; "i")) | all')"
  [ "$legacy_ban" = "true" ] || failures+=("E_SELF_LEGACY_BAN")
  legacy_allow="$(jq -cn '[ "gpt-image-2.5","gpt-image-2.5-sunburst","gpt-image-2.5-flare","gpt-image-2.6","gpt-image-2.6-sunburst","gpt-image-2.6-flare" ] | map(test("gongnyang|gpt-image-2(?!\\.[56](?:\\b|-))|check[_-]prompt|Tier-[0-9]|SAFETY_ASSERT|NEGATIVE_TAIL|E-SLOT-LEAK|AR x:y"; "i")) | any')"
  [ "$legacy_allow" = "false" ] || failures+=("E_SELF_LEGACY_ALLOW")

  local skill_req
  skill_req="$(printf '%s' "$REQUIRED_SKILL_TAGS")"
  out="$(jq -n --argjson req "$skill_req" "$JQ"' tag_errors("SKILL.md"; "<purpose>\n<workflow>\n"; "<purpose>\n<workflow>\n"; $req)[]')"
  case "$out" in
    *E_REQUIRED_TAG:SKILL.md:validation*) ;;
    *) failures+=("E_SELF_TAG_CHECK") ;;
  esac
  out="$(jq -n --argjson req "$skill_req" "$JQ"' tag_errors("SKILL.md"; "<purpose>\n<workflow>\n"; "<purpose>\n<required>\n"; $req)[]')"
  case "$out" in
    *E_PAIR_TAG_MISMATCH:SKILL.md*) ;;
    *) failures+=("E_SELF_TAG_CHECK") ;;
  esac
  out="$(jq -n "$JQ"' "| head |\n| --- |\n| only one row |\n" | prompt_table_errors("fixture.md")[]')"
  case "$out" in
    *E_PROMPT_TABLE:fixture.md*) ;;
    *) failures+=("E_SELF_TABLE_CHECK") ;;
  esac
  out="$(jq -n 'if ("nothing canonical here" | contains("canonical-needle")) then empty else "E_MIRROR_DRIFT:fixture" end')"
  case "$out" in
    *E_MIRROR_DRIFT:fixture*) ;;
    *) failures+=("E_SELF_MIRROR_CHECK") ;;
  esac

  if [ "$with_audit" != "1" ]; then
    printf '%s\n' ${failures[@]+"${failures[@]}"} | sed '/^$/d'
    return 0
  fi

  local audit_fixture
  audit_fixture="$(mktemp -d "${TMPDIR:-/tmp}/hyper-imagegen-audit-XXXXXX")"
  cp -R "$PACKAGE_ROOT/." "$audit_fixture/" 2>/dev/null || true
  if [ -n "$(audit_package "$audit_fixture")" ]; then
    failures+=("E_SELF_AUDIT_GREEN")
    rm -rf "$audit_fixture"
    printf '%s\n' ${failures[@]+"${failures[@]}"} | sed '/^$/d'
    return 0
  fi
  local skill_path skill_text skill_ko_path skill_ko_text table_path rule_path direction_path
  skill_path="$audit_fixture/SKILL.md"
  skill_text="$(cat "$skill_path")"
  sed 's/<purpose>/<intent>/' "$skill_path" >"$skill_path.tmp" && mv "$skill_path.tmp" "$skill_path"
  case "$(audit_package "$audit_fixture")" in
    *E_REQUIRED_TAG:SKILL.md:purpose*) ;;
    *) failures+=("E_SELF_AUDIT_RED_TAG") ;;
  esac
  printf '%s' "$skill_text" >"$skill_path"
  skill_ko_path="$audit_fixture/SKILL.ko.md"
  skill_ko_text="$(cat "$skill_ko_path")"
  sed 's/<purpose>/<intent>/' "$skill_ko_path" >"$skill_ko_path.tmp" && mv "$skill_ko_path.tmp" "$skill_ko_path"
  case "$(audit_package "$audit_fixture")" in
    *E_REQUIRED_TAG:SKILL.ko.md:purpose*) ;;
    *) failures+=("E_SELF_AUDIT_RED_KO_TAG") ;;
  esac
  printf '%s' "$skill_ko_text" >"$skill_ko_path"
  table_path="$audit_fixture/references/prompt-crafting.md"
  awk '!/^\| beauty \|/' "$table_path" >"$table_path.tmp" && mv "$table_path.tmp" "$table_path"
  case "$(audit_package "$audit_fixture")" in
    *E_PROMPT_TABLE*) ;;
    *) failures+=("E_SELF_AUDIT_RED_TABLE") ;;
  esac
  for rule_path in rules/prompt-compilation.md rules/prompt-compilation.ko.md; do
    awk '{gsub(/no watermark/,"watermark-free"); gsub(/no invented glyphs/,"glyph-free"); print}' "$audit_fixture/$rule_path" >"$audit_fixture/$rule_path.tmp" && mv "$audit_fixture/$rule_path.tmp" "$audit_fixture/$rule_path"
  done
  case "$(audit_package "$audit_fixture")" in
    *E_MIRROR_DRIFT:rules/prompt-compilation*) ;;
    *) failures+=("E_SELF_AUDIT_RED_RULE_MIRROR") ;;
  esac
  for direction_path in references/visual-direction.md references/visual-direction.ko.md; do
    awk '{gsub(/trending on artstation/,"platform-trending"); print}' "$audit_fixture/$direction_path" >"$audit_fixture/$direction_path.tmp" && mv "$audit_fixture/$direction_path.tmp" "$audit_fixture/$direction_path"
  done
  case "$(audit_package "$audit_fixture")" in
    *E_MIRROR_DRIFT:references/visual-direction*) ;;
    *) failures+=("E_SELF_AUDIT_RED_VISUAL_MIRROR") ;;
  esac
  rm -rf "$audit_fixture"

  out="$(jq -cn --argjson g "$good" "$JQ"' prompt_syntax($g + {compiled_brief:"a blue square poster with \"밤 산책\" as the headline"})')"
  local syntax_good syntax_bad
  syntax_good="$(printf '%s' "$out" | jq -r '.ok')"
  out="$(jq -cn --argjson g "$good" "$JQ"' prompt_syntax($g + {compiled_brief:"a poster at 16:9 with no crowd, masterpiece quality"})')"
  syntax_bad="$(printf '%s' "$out" | jq -r '(.ok|tostring) + "," + ((.errors|index("E_PROMPT_AR_LEAK") != null)|tostring) + "," + ((.errors|index("E_PROMPT_NEGATIVE_TIER") != null)|tostring)')"
  if [ "$syntax_good" != "true" ] || [ "$syntax_bad" != "false,true,true" ]; then
    failures+=("E_SELF_PROMPT_SYNTAX")
  fi

  local rows45 rows46
  rows45="$(coverage_set 45)"
  rows46="$(coverage_set 46)"
  out="$(jq -cn --argjson rows "$rows45" --argjson evals "$(coverage_evals 45)" "$JQ"' rows_result($rows;$evals;null;null)')"
  case "$out" in
    *E_EVAL_COVERAGE*) ;;
    *) failures+=("E_SELF_COVERAGE_FLOOR") ;;
  esac
  out="$(jq -cn --argjson rows "$rows46" --argjson evals "$(coverage_evals 46)" "$JQ"' rows_result($rows;$evals;null;null)')"
  case "$out" in
    *E_EVAL_COVERAGE*) failures+=("E_SELF_COVERAGE_CEILING") ;;
  esac

  printf '%s\n' ${failures[@]+"${failures[@]}"} | sed '/^$/d'
}

coverage_set() { # total
  jq -cn --argjson total "$1" '
    [ range(0;36) as $i | {id:("floor-p"+($i|tostring)), judgment:"automatic", case_kind:"input", input:{}, oracle:{ok:false,error:"E_CAPABILITY_SCHEMA"}, paired_id:("floor-p"+((if ($i % 2) == 1 then ($i-1) else ($i+1) end)|tostring))} ] as $rows
    | [range(36; $total) as $i | {id:("floor-x"+($i|tostring)), judgment:"automatic", case_kind:"input", input:{}, oracle:{ok:false,error:"E_CAPABILITY_SCHEMA"}}] as $extra
    | $rows + $extra'
}

coverage_evals() { # total
  jq -cn --argjson total "$1" '[ range(0;$total) | {err:null, manual:false} ]'
}

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

parse_evals() { # file -> sets PARSE_ROWS or PARSE_ERROR; returns 1 on failure
  local file="$1" out
  PARSE_ROWS=""
  PARSE_ERROR=""
  if [ ! -e "$file" ]; then
    PARSE_ERROR="ENOENT: no such file or directory, open '$file'"
    return 1
  fi
  if [ -d "$file" ]; then
    PARSE_ERROR="EISDIR: illegal operation on a directory, read"
    return 1
  fi
  if [ ! -r "$file" ]; then
    PARSE_ERROR="EACCES: permission denied, open '$file'"
    return 1
  fi
  out="$(jq -R -s -c -r '
    def blank: test("^[\\s\\p{Z}]*$");
    reduce (split("\n") | .[] | sub("\r$";"")) as $line
      ({idx:0, rows:[], error:null};
        if .error != null then .
        elif ($line|blank) then .
        else .idx += 1
          | (try {v:($line|fromjson)} catch {bad:true}) as $p
          | if ($p|has("bad")) then .error = ("E_JSONL_PARSE:" + (.idx|tostring))
            else .rows += [$p.v] end
        end)
    | if .error != null then "ERR\t" + .error else (.rows|tojson) end' <"$file")" || {
    PARSE_ERROR="E_JSONL_PARSE:1"
    return 1
  }
  case "$out" in
    ERR$'\t'*) PARSE_ERROR="${out#ERR$'\t'}"; return 1 ;;
    *) PARSE_ROWS="$out"; return 0 ;;
  esac
}

throw_error() {
  jq -cn --arg e "$1" '{ok:false,errors:[$e],manual_required:[],counts:{errors:1,manual_required:0}}'
  exit 1
}

main() {
  local root="" evals="skills/hyper-imagegen/assets/evals/hyper-imagegen-cases.jsonl" self=0 evals_specified=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --self-test) self=1 ;;
      --json) ;;
      --root|--evals)
        local flag="$1"
        shift
        if [ "$#" -eq 0 ]; then throw_error "E_CLI_ARGUMENT"; fi
        if [ "$flag" = "--root" ]; then root="$1"; else evals="$1"; evals_specified=1; fi
        ;;
      *) throw_error "E_CLI_ARGUMENT" ;;
    esac
    shift
  done
  if [ "$self" != "1" ] && [ -z "$root" ] && [ "$evals_specified" != "1" ]; then
    throw_error "E_CLI_ARGUMENT"
  fi

  local errors=() rows aggregate result
  while IFS= read -r line; do
    [ -n "$line" ] && errors+=("$line")
  done < <(embedded_tests "$self")

  if ! parse_evals "$evals"; then
    throw_error "$PARSE_ERROR"
  fi
  rows="$PARSE_ROWS"
  aggregate="$(validate_all_rows "$rows")"
  while IFS= read -r line; do
    [ -n "$line" ] && errors+=("$line")
  done < <(printf '%s' "$aggregate" | jq -r '.errors[]')

  if [ -n "$root" ]; then
    local real_root
    real_root="$(realpath_portable "$root" 2>/dev/null || true)"
    if [ -z "$real_root" ] || [ ! -d "$real_root" ]; then
      throw_error "ENOENT: no such file or directory, lstat '$root'"
    fi
    while IFS= read -r line; do
      [ -n "$line" ] && errors+=("$line")
    done < <(audit_package "$real_root")
  fi

  local manual auto total paired
  manual="$(printf '%s' "$aggregate" | jq -c '.manual')"
  auto="$(printf '%s' "$aggregate" | jq -r '.automatic')"
  total="$(printf '%s' "$aggregate" | jq -r '.total')"
  paired="$(printf '%s' "$aggregate" | jq -r '.paired')"
  local errors_json
  if [ "${#errors[@]}" -gt 0 ]; then
    errors_json="$(printf '%s\n' "${errors[@]}" | jq -Rnc '[inputs] | map(select(. != ""))')"
  else
    errors_json="[]"
  fi
  jq -cn --argjson errors "$errors_json" --argjson manual "$manual" --argjson auto "$auto" --argjson total "$total" --argjson paired "$paired" \
    '{ok:(($errors|length) == 0), errors:$errors, manual_required:$manual, counts:{errors:($errors|length), manual_required:($manual|length), automatic:$auto, total:$total, paired:$paired}}'
  if [ "$(printf '%s' "$errors_json" | jq 'length')" -gt 0 ]; then
    exit 1
  fi
  exit 0
}

kind_is_automatic() {
  case " $AUTOMATIC_KINDS " in
    *" $1 "*) return 0 ;;
    *) return 1 ;;
  esac
}

validate_all_rows() { # rows-array-json -> {errors,manual,automatic,paired,total}
  local rows="$1" tmp n i=0 row meta evals="[]" dup_ids="[]"
  tmp="$(mktemp "${TMPDIR:-/tmp}/hyper-imagegen-rows-XXXXXX")"
  printf '%s' "$rows" | jq -c '.[]' >"$tmp"
  n="$(wc -l <"$tmp" | tr -d ' ')"
  while IFS= read -r row; do
    meta="$(printf '%s' "$row" | jq -c -r '
      def truthy: if . == null then false elif type == "boolean" then . elif type == "number" then (. != 0) elif type == "string" then (. != "") else true end;
      if type == "object" then
        . as $r
        | [ (if ((.id|type) == "string") then "y" else "n" end),
            (if ((.id|type) == "string") then .id else "" end),
            (if ((.judgment|type) == "string") then .judgment else "" end),
            (if ((.case_kind|type) == "string") then "y" else "n" end),
            (if ((.case_kind|type) == "string") then .case_kind else "" end),
            (if ((.input // null)|truthy) then "y" else "n" end),
            (if ((.oracle // null)|truthy) then "y" else "n" end),
            (if (((.case_kind|type) == "string")
                 and ((["visual","text","series","retrieval_trajectory"]|index($r.case_kind)) != null)
                 and (if ((.event_id // null)|truthy) then true else false end)
                 and (if ((.evidence // null)|truthy) then true else false end)
                 and (if ((.disclosure // null)|truthy) then true else false end))
             then "y" else "n" end) ]
        | join("\u001f")
      else "n\u001f\u001f\u001f" + "n\u001f\u001f\u001fn\u001fn" end')"
    local has_id id judgment has_kind kind input_ok oracle_ok manual_ok err="" manual_flag="false"
    IFS=$'\x1f' read -r has_id id judgment has_kind kind input_ok oracle_ok manual_ok <<<"$meta"
    if [ "$has_id" != "y" ]; then
      err="E_EVAL_ID"
    elif printf '%s' "$dup_ids" | jq -e --arg id "$id" 'index($id) != null' >/dev/null 2>&1; then
      err="E_EVAL_ID"
    else
      dup_ids="$(printf '%s' "$dup_ids" | jq -c --arg id "$id" '. + [$id]')"
    fi
    if [ -z "$err" ]; then
      if [ "$judgment" = "automatic" ]; then
        if [ "$has_kind" != "y" ] || ! kind_is_automatic "$kind" || [ "$input_ok" != "y" ] || [ "$oracle_ok" != "y" ]; then
          err="E_ORACLE_MISMATCH:$id"
        else
          local input_json actual
          input_json="$(printf '%s' "$row" | jq -c '.input')"
          actual="$(automatic_result "$row" "$kind" "$input_json")"
          if [ "$(exact_match "$actual" "$(printf '%s' "$row" | jq -c '.oracle')")" != "true" ]; then
            err="E_ORACLE_MISMATCH:$id"
          fi
        fi
      elif [ "$judgment" = "manual" ]; then
        if [ "$manual_ok" != "y" ]; then
          err="E_MANUAL_SCHEMA:$id"
        else
          manual_flag="true"
        fi
      else
        err="E_JUDGMENT:$id"
      fi
    fi
    evals="$(printf '%s' "$evals" | jq -c --arg e "$err" --argjson m "$manual_flag" '. + [{err:(if $e == "" then null else $e end), manual:$m}]')"
    i=$((i + 1))
  done <"$tmp"
  rm -f "$tmp"
  jq -cn --argjson rows "$rows" --argjson evals "$evals" "$JQ"' rows_result($rows;$evals;null;null)'
}

main "$@"

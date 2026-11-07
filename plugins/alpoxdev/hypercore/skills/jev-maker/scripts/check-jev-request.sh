#!/usr/bin/env bash
# Offline request checker for Jev (System One / Decisions) evaluation requests.
#
# Usage: bash check-jev-request.sh [--route direct|bai|aisdk] <request.json>
# Exit codes: 0 = no errors, 1 = validation errors (an unparsable JSON file included), 2 = usage error.
# Codes carried by exit 1: INVALID_JSON for an unparsable file, INPUT_TOO_DEEP for a document nested deeper than the
# checker can read, and the shape codes below.
# The report carries no request string values: every finding is a code, a JSON path, and a fixed message.
#
# Requires bash 3.2 or newer and jq 1.6 or newer. JSON is parsed and produced with jq; the report is printed raw
# so that characters JavaScript leaves unescaped, such as U+007F, survive unchanged.
set -euo pipefail

route=direct
route_seen=0
file=
file_count=0
fail_code=
fail_message=

usage_fail() {
  fail_code=$1
  fail_message=$2
}

parse_args() {
  local arg next
  while [ "$#" -gt 0 ]; do
    arg=$1
    shift
    case $arg in
      --route)
        if [ "$route_seen" -eq 1 ]; then
          usage_fail USAGE_UNKNOWN_ARGUMENT 'Option --route may be given at most once.'
          return 1
        fi
        if [ "$#" -eq 0 ]; then
          usage_fail USAGE_ARGUMENT_VALUE_MISSING 'Option --route requires one of: direct, bai, aisdk.'
          return 1
        fi
        next=$1
        case $next in
          --*)
            usage_fail USAGE_ARGUMENT_VALUE_MISSING 'Option --route requires one of: direct, bai, aisdk.'
            return 1
            ;;
        esac
        case $next in
          direct | bai | aisdk) route=$next ;;
          *)
            usage_fail USAGE_UNKNOWN_ROUTE 'Unknown route. Use direct, bai, or aisdk.'
            return 1
            ;;
        esac
        route_seen=1
        shift
        ;;
      --*)
        usage_fail USAGE_UNKNOWN_ARGUMENT 'Unknown option. The only option is --route.'
        return 1
        ;;
      *)
        file_count=$((file_count + 1))
        if [ "$file_count" -eq 1 ]; then
          file=$arg
        fi
        ;;
    esac
  done

  if [ "$file_count" -eq 0 ]; then
    usage_fail USAGE_MISSING_FILE 'A request JSON file argument is required.'
    return 1
  fi
  if [ "$file_count" -gt 1 ]; then
    usage_fail USAGE_UNKNOWN_ARGUMENT 'Only one request JSON file may be given.'
    return 1
  fi
  return 0
}

# Prints the report for a run that stops before validation. $1 = code, $2 = message, $3 = 1 when the route is known.
print_stop_report() {
  jq -n \
    --arg code "$1" \
    --arg message "$2" \
    --arg route "$route" \
    --argjson has_route "$3" \
    '{
      ok: false,
      route: (if $has_route == 1 then $route else null end),
      errors: [{ code: $code, path: "$", message: $message }],
      warnings: [],
      stats: { questions: 0, noul: 0, choice: 0, score: 0, estimatedStateTokens: 0 }
    }'
}

write_validator() {
  cat > "$1" <<'JQ'
# Whitespace-only test matching String.prototype.trim (ASCII whitespace plus Unicode space separators and BOM).
def ts_blank:
  test("^[\\s\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]*$");

def has_secret:
  test("sk-[A-Za-z0-9]{16,}") or test("Bearer [A-Za-z0-9._-]{16,}");

# Renders a string the way JSON.stringify does. jq's tojson escapes U+007F, which JavaScript leaves raw.
def js_char:
  if . == 34 then "\\\""
  elif . == 92 then "\\\\"
  elif . == 8 then "\\b"
  elif . == 9 then "\\t"
  elif . == 10 then "\\n"
  elif . == 12 then "\\f"
  elif . == 13 then "\\r"
  elif . < 32 then
    "\\u00" + ([ (. / 16 | floor) % 16, . % 16 ] | map(if . < 10 then 48 + . else 87 + . end) | implode)
  else
    [.] | implode
  end;

def js_string:
  "\"" + ([explode[] | js_char] | join("")) + "\"";

def path_key:
  if has_secret then
    "[\"<redacted-key>\"]"
  elif test("^[A-Za-z_][A-Za-z0-9_]*$") then
    "." + .
  else
    "[" + js_string + "]"
  end;

def qpath($id; $field):
  "$.questions" + ($id | path_key) + (if $field == null then "" else "." + $field end);

def is_content:
  type == "string" or type == "array" or type == "object";

def is_choice_option:
  . == null or is_content;

# A string as its UTF-16 code units, so ordering matches JavaScript string comparison for astral characters.
def utf16_units:
  [explode[]
   | if . > 65535 then
       (. - 65536) as $value | [55296 + (($value / 1024) | floor), 56320 + ($value % 1024)]
     else
       .
     end]
  | flatten;

# Length of a string as ECMAScript counts it: UTF-16 code units plus JSON escape expansion.
def str_len:
  [explode[]
   | if . == 34 or . == 92 or . == 8 or . == 9 or . == 10 or . == 12 or . == 13 then 2
     elif . < 32 then 6
     elif . > 65535 then 2
     else 1
     end] | add // 0;

# Renders a number the way ECMAScript's Number::toString does. jq's double printing already yields the shortest
# round-trip digits; this rewrites the presentation to the ECMAScript thresholds and exponent spelling.
def js_num:
  if isnan or . == infinite or . == -infinite then
    "null"
  elif . == 0 then
    "0"
  else
    (if . < 0 then "-" else "" end) as $sign
    | (. + 0 | fabs | tostring) as $text
    | ($text | capture("^(?<m>[0-9]+(?:\\.[0-9]+)?)(?:e(?<e>[-+]?[0-9]+))?$")) as $parts
    | ($parts.m | index(".")) as $dot
    | (if $dot == null then 0 else ($parts.m | length) - $dot - 1 end) as $frac
    | ($parts.m | gsub("\\."; "") | sub("^0+"; "")) as $raw
    | ($raw | length) as $significant
    | ($raw | sub("0+$"; "")) as $trimmed
    | ($parts.e // "0" | tonumber) as $exp
    | (if $trimmed == "" then "0" else $trimmed end) as $digits
    | ($digits | length) as $k
    | ($significant + $exp - $frac) as $n
    | (if $digits == "0" then
         "0"
       elif $k <= $n and $n <= 21 then
         $digits + ("0" * ($n - $k))
       elif 0 < $n and $n <= 21 then
         $digits[0:$n] + "." + $digits[$n:]
       elif -6 < $n and $n <= 0 then
         "0." + ("0" * (-$n)) + $digits
       else
         ($n - 1) as $e
         | (if $e >= 0 then "+" + ($e | tostring) else "-" + ((-$e) | tostring) end) as $exponent
         | (if $k == 1 then $digits + "e" + $exponent
            else $digits[0:1] + "." + $digits[1:] + "e" + $exponent
            end)
       end) as $body
    | $sign + $body
  end;

# Length of JSON.stringify(value) in UTF-16 code units.
def js_len:
  if type == "string" then
    2 + str_len
  elif type == "number" then
    js_num | length
  elif type == "boolean" then
    (if . then 4 else 5 end)
  elif type == "null" then
    4
  elif type == "array" then
    (2 + ([.[] | js_len] | add // 0) + (if length > 0 then length - 1 else 0 end))
  elif type == "object" then
    ([to_entries[] | ((.key | str_len) + 3 + (.value | js_len))] | add // 0)
    + (2 + (if length > 0 then length - 1 else 0 end))
  else
    0
  end;

def type_expected($route):
  if $route == "aisdk" then "boolean, choice, score" else "noul, choice, score" end;

def type_message($route; $type):
  (if $type == "boolean" then
     " The yes/no type is named \"boolean\" on the AI SDK route and \"noul\" on the direct and b.ai routes."
   elif $type == "noul" then
     " The yes/no type is named \"noul\" on the direct and b.ai routes and \"boolean\" on the AI SDK route."
   else
     ""
   end) as $hint
  | "Question type must be one of " + type_expected($route) + " for route " + $route + "." + $hint;

def finding($code; $path; $message):
  { code: $code, path: $path, message: $message };

def empty_stats:
  { questions: 0, noul: 0, choice: 0, score: 0, estimatedStateTokens: 0 };

def scan_secrets($path):
  if type == "string" then
    (if has_secret then
       [finding("SECRET_IN_REQUEST"; $path;
         "This string looks like an API key or bearer token. Keep credentials out of the request body and send them in the request header at call time.")]
     else
       []
     end)
  elif type == "array" then
    ([to_entries[] | (.key) as $index | (.value | scan_secrets($path + "[" + ($index | tostring) + "]"))] | add // [])
  elif type == "object" then
    ([to_entries[] | (.key) as $key | (.value | scan_secrets($path + ($key | path_key)))] | add // [])
  else
    []
  end;

def validate_question($id; $value; $route):
  qpath($id; null) as $base
  | (if ($id | ts_blank) then
       [finding("QUESTION_ID_BLANK"; $base; "Question ids must not be empty or whitespace only.")]
     else
       []
     end) as $id_errors
  | if ($value | type) != "object" then
      {
        errors: ($id_errors + [finding("QUESTION_NOT_OBJECT"; $base;
          "Each question must be a JSON object with type, instructions, and criteria fields.")]),
        warnings: [],
        noul: 0,
        choice: 0,
        score: 0
      }
    else
      ($value.type) as $type
      | (if $route == "aisdk" then ["boolean", "choice", "score"] else ["noul", "choice", "score"] end) as $allowed
      | if (($type | type) != "string") or (($allowed | index($type)) == null) then
          {
            errors: ($id_errors + [finding("QUESTION_TYPE"; qpath($id; "type"); type_message($route; $type))]),
            warnings: [],
            noul: 0,
            choice: 0,
            score: 0
          }
        else
          (if ($value | has("instructions") | not) then
             [finding("INSTRUCTIONS_MISSING"; qpath($id; "instructions");
               "Every question requires instructions describing what to decide.")]
           elif (($value.instructions | is_content) | not) then
             [finding("INSTRUCTIONS_TYPE"; qpath($id; "instructions");
               "Instructions must be a string, an object, or an array.")]
           else
             []
           end) as $instruction_errors
          | (if $type == "noul" or $type == "boolean" then
               (if ($value | has("criteria") | not) then
                  { errors: [], warnings: [] }
                elif (($value.criteria | type) != "object") then
                  { errors: [finding("NOUL_CRITERIA_TYPE"; qpath($id; "criteria");
                      "Criteria for a yes/no question is optional but must be an object with true and false keys when present.")],
                    warnings: [] }
                else
                  ($value.criteria | keys_unsorted) as $keys
                  | { errors: [
                        $keys[] as $key
                        | if ($key != "true" and $key != "false") then
                            finding("NOUL_CRITERIA_KEY"; qpath($id; "criteria");
                              "Criteria keys for a yes/no question must be exactly \"true\" or \"false\".")
                          elif (($value.criteria[$key] | is_content) | not) then
                            finding("NOUL_CRITERIA_VALUE"; qpath($id; "criteria") + ($key | path_key);
                              "A yes/no criteria description must be a string, an object, or an array.")
                          else
                            empty
                          end
                      ],
                      warnings: [] }
                end)
             elif $type == "choice" then
               (if (($value.criteria | type) != "object") then
                  { errors: [finding("CHOICE_CRITERIA_MISSING"; qpath($id; "criteria");
                      "A choice question requires criteria: an object mapping each option to its description.")],
                    warnings: [] }
                else
                  ($value.criteria | keys_unsorted) as $options
                  | ($options | length) as $count
                  | (if ($count >= 1 and $count <= 255) then
                       []
                     else
                       [finding("CHOICE_CRITERIA_COUNT"; qpath($id; "criteria");
                         "A choice question takes 1 to 255 options; this one has " + ($count | tostring) + ".")]
                     end) as $count_errors
                  | [ $options[] as $option
                      | if (($value.criteria[$option] | is_choice_option) | not) then
                          finding("CHOICE_CRITERIA_VALUE"; qpath($id; "criteria") + ($option | path_key);
                            "An option description must be null, a string, an object, or an array.")
                        else
                          empty
                        end
                    ] as $value_errors
                  | (if ($count >= 1 and $count <= 255
                         and ([ $options[] | select(. == "none" or . == "other" or . == "unknown") ] | length) == 0) then
                       [finding("NO_FALLBACK_OPTION"; qpath($id; "criteria");
                         "No none/other/unknown option is defined, so the model must pick one of the listed options. This is a heuristic check, not an API rule.")]
                     else
                       []
                     end) as $fallback_warnings
                  | { errors: ($count_errors + $value_errors), warnings: $fallback_warnings }
                end)
             else
               (if (($value.criteria | type) != "array") then
                  { errors: [finding("SCORE_CRITERIA_MISSING"; qpath($id; "criteria");
                      "A score question requires criteria: an ordered array of level descriptions.")],
                    warnings: [] }
                else
                  ($value.criteria | length) as $levels
                  | (if $levels < 2 then
                       [finding("SCORE_CRITERIA_COUNT"; qpath($id; "criteria");
                         "A score question needs at least 2 levels; this one has " + ($levels | tostring) + ".")]
                     elif $levels > 10 then
                       (if $route == "aisdk" then
                          []
                        else
                          [finding("SCORE_CRITERIA_COUNT"; qpath($id; "criteria");
                            "A score question takes 2 to 10 levels; this one has " + ($levels | tostring) + ".")]
                        end)
                     else
                       []
                     end) as $count_errors
                  | (if ($levels > 10 and $route == "aisdk") then
                       [finding("SCORE_CRITERIA_COUNT"; qpath($id; "criteria");
                         "This score question has " + ($levels | tostring) + " levels. The AI SDK documents no upper bound, but the direct and b.ai APIs accept at most 10, so the request is not portable.")]
                     else
                       []
                     end) as $count_warnings
                  | [ range(0; $levels) as $index
                      | if (($value.criteria[$index] | is_content) | not) then
                          finding("SCORE_LEVEL_TYPE"; qpath($id; "criteria") + "[" + ($index | tostring) + "]";
                            "A score level description must be a string, an object, or an array.")
                        else
                          empty
                        end
                    ] as $level_errors
                  | { errors: ($count_errors + $level_errors), warnings: $count_warnings }
                end)
             end) as $criteria_result
          | {
              errors: ($id_errors + $instruction_errors + $criteria_result.errors),
              warnings: $criteria_result.warnings,
              noul: (if $type == "choice" or $type == "score" then 0 else 1 end),
              choice: (if $type == "choice" then 1 else 0 end),
              score: (if $type == "score" then 1 else 0 end)
            }
        end
    end;

def validate($doc; $route):
  if ($doc | type) != "object" then
    {
      errors: [finding("ROOT_NOT_OBJECT"; "$"; "The request document must be a JSON object.")],
      warnings: [],
      stats: empty_stats
    }
  else
    ([ $doc | keys_unsorted[] as $key
       | if (["state", "model", "questions", "stream"] | index($key)) == null then
           finding("UNKNOWN_TOP_LEVEL_FIELD"; "$" + ($key | path_key);
             "This top-level field is not part of the documented request shape and is ignored by the API.")
         else
           empty
         end
     ]) as $unknown_warnings
    | (if ($doc | has("state") | not) then
         [finding("STATE_MISSING"; "$.state";
           "The request requires state: the content every question is evaluated against.")]
       elif (($doc.state | is_content) | not) then
         [finding("STATE_TYPE"; "$.state";
           "State must be a string, an object, or an array; null, numbers, and booleans are rejected.")]
       else
         []
       end) as $state_errors
    | (if ($doc.model | type) == "string" then
         (if ($doc.model | ts_blank) then
            { errors: [finding("MODEL_MISSING"; "$.model"; "The request requires model as a non-empty string.")],
              warnings: [] }
          elif $route == "bai" then
            (if ((["jev-1.13.0", "jev-latest"] | index($doc.model)) == null) then
               { errors: [finding("MODEL_UNSUPPORTED"; "$.model";
                   "The b.ai Decisions API accepts only jev-1.13.0 or jev-latest.")],
                 warnings: [] }
             else
               { errors: [], warnings: [] }
             end)
          elif $route == "direct" then
            (if (($doc.model | startswith("jev-")) | not) then
               { errors: [finding("MODEL_UNSUPPORTED"; "$.model";
                   "The direct TypeSafe API serves Jev models; use a model id that starts with \"jev-\".")],
                 warnings: [] }
             elif ((["jev-latest", "jev-preview", "jev-1.13.0"] | index($doc.model)) == null) then
               { errors: [],
                 warnings: [finding("MODEL_UNVERIFIED"; "$.model";
                   "Known aliases are jev-latest, jev-preview, jev-1.13.0. This id starts with \"jev-\" but was not verified against the model list.")] }
             else
               { errors: [], warnings: [] }
             end)
          else
            { errors: [], warnings: [] }
          end)
       else
         { errors: [finding("MODEL_MISSING"; "$.model"; "The request requires model as a non-empty string.")],
           warnings: [] }
       end) as $model_result
    | (if ($route == "bai" and ($doc | has("stream")) and ($doc.stream != false)) then
         [finding("STREAM_NOT_SUPPORTED"; "$.stream";
           "The b.ai Decisions API returns one complete result; omit stream or set it to false.")]
       else
         []
       end) as $stream_errors
    | (if (($doc.questions | type) != "object") then
         {
           errors: [finding("QUESTIONS_MISSING"; "$.questions";
             "The request requires questions: a non-empty map of question ids to question definitions.")],
           results: [],
           count: 0
         }
       else
         ($doc.questions | keys_unsorted) as $ids
         | {
             errors: (if ($ids | length) == 0 then
                        [finding("QUESTIONS_EMPTY"; "$.questions"; "The questions map must contain at least one question.")]
                      else
                        []
                      end),
             results: [ $ids[] as $id | ($doc.questions[$id] | validate_question($id; .; $route)) ],
             count: ($ids | length)
           }
       end) as $questions_result
    | ([ $questions_result.results[] | .errors[] ]) as $question_errors
    | ([ $questions_result.results[] | .warnings[] ]) as $question_warnings
    | ({ questions: $questions_result.count,
         noul: ([ $questions_result.results[].noul ] | add // 0),
         choice: ([ $questions_result.results[].choice ] | add // 0),
         score: ([ $questions_result.results[].score ] | add // 0) }) as $partial_stats
    | ($doc | scan_secrets("$")) as $secret_errors
    | ((if ($doc | has("state")) then ($doc.state | js_len) else 0 end)
       + (if (($doc.questions | type) == "object") then
            ([ $doc.questions[] | js_len ] | max // 0)
          else
            0
          end)) as $characters
    | (($characters / 4) | ceil) as $tokens
    | { errors: ($state_errors + $model_result.errors + $stream_errors
                 + $questions_result.errors + $question_errors + $secret_errors),
        warnings: ($unknown_warnings + $model_result.warnings + $question_warnings
                   + (if $tokens > 32000 then
                        [finding("STATE_LARGE"; "$.state";
                          "The serialized state plus the longest question is roughly " + ($tokens | tostring)
                          + " tokens by a length/4 estimate. The API limit for state plus the longest question is 32000. This figure is an estimate, not a measured token count.")]
                      else
                        []
                      end)),
        stats: ($partial_stats + { estimatedStateTokens: $tokens }) }
  end;

# Serializes a report the way JSON.stringify(value, null, 2) does. The report is printed raw so that jq's own
# printer cannot re-escape characters JavaScript leaves as-is, such as U+007F in a JSON path.
def pretty($indent):
  if type == "object" then
    if length == 0 then
      "{}"
    else
      "{\n"
      + ([to_entries[]
          | (" " * ($indent + 2)) + (.key | js_string) + ": " + (.value | pretty($indent + 2))]
         | join(",\n"))
      + "\n" + (" " * $indent) + "}"
    end
  elif type == "array" then
    if length == 0 then
      "[]"
    else
      "[\n"
      + ([.[] | (" " * ($indent + 2)) + pretty($indent + 2)] | join(",\n"))
      + "\n" + (" " * $indent) + "]"
    end
  elif type == "string" then
    js_string
  elif type == "number" then
    tostring
  elif type == "boolean" then
    (if . then "true" else "false" end)
  else
    "null"
  end;

validate(.; $route)
| {
    ok: ((.errors | length) == 0),
    route: $route,
    errors: (.errors | sort_by((.path | utf16_units), (.code | utf16_units), (.message | utf16_units))),
    warnings: (.warnings | sort_by((.path | utf16_units), (.code | utf16_units), (.message | utf16_units))),
    stats: .stats
  }
| pretty(0)
JQ
}

main() {
  # bun drops one leading "--" before the script sees its arguments; keep that behavior.
  if [ "${1:-}" = "--" ]; then
    shift
  fi

  if ! parse_args "$@"; then
    print_stop_report "$fail_code" "$fail_message" 0
    exit 2
  fi

  if [ -d "$file" ] || [ ! -e "$file" ] || [ ! -r "$file" ]; then
    print_stop_report USAGE_UNREADABLE_FILE 'The request file could not be read.' 1
    exit 2
  fi

  # jq skips a UTF-8 byte order mark at the very start of a value; JSON.parse rejects it.
  if [ "$(head -c 3 -- "$file" | od -An -tx1 | tr -d ' \n')" = "efbbbf" ]; then
    print_stop_report INVALID_JSON 'The request file is not valid JSON.' 1
    exit 1
  fi

  tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/jev-request.XXXXXX")
  trap 'rm -rf "$tmpdir"' EXIT HUP INT TERM

  if jq -c . < "$file" > "$tmpdir/compact" 2> "$tmpdir/parse-error"; then
    values=$(wc -l < "$tmpdir/compact")
    values=${values//[[:space:]]/}
    if [ "$values" -ne 1 ]; then
      print_stop_report INVALID_JSON 'The request file is not valid JSON.' 1
      exit 1
    fi
  else
    if grep -q 'Exceeds depth limit' "$tmpdir/parse-error" 2>/dev/null; then
      print_stop_report INPUT_TOO_DEEP 'The request nests deeper than this checker can read.' 1
    elif grep -q 'Could not open file' "$tmpdir/parse-error" 2>/dev/null; then
      print_stop_report USAGE_UNREADABLE_FILE 'The request file could not be read.' 1
      exit 2
    else
      print_stop_report INVALID_JSON 'The request file is not valid JSON.' 1
    fi
    exit 1
  fi

  write_validator "$tmpdir/validator.jq"
  if ! report=$(jq -r -f "$tmpdir/validator.jq" --arg route "$route" < "$file" 2> "$tmpdir/validate-error"); then
    print_stop_report USAGE_ERROR 'The checker could not run with these arguments.' 1
    exit 2
  fi

  printf '%s\n' "$report"
  case $(printf '%s\n' "$report" | jq -r '.ok') in
    true) exit 0 ;;
    *) exit 1 ;;
  esac
}

main "$@"

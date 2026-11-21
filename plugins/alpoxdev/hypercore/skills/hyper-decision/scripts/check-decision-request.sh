#!/usr/bin/env bash
# Offline request checker for decision API requests: a shared input plus typed questions answered with
# probabilities instead of generated text.
#
# Usage: bash check-decision-request.sh [--route systemone|bai|aisdk|openai] <request.json>
# Routes:
#   systemone  TypeSafe System One dialect (the default): model, state, questions map, optional assets.
#              Used by the TypeSafe direct API and every endpoint that implements POST /systemone.
#   bai        b.ai Decisions API: the same dialect restricted to jev-1.13.0 or jev-latest.
#   aisdk      AI SDK experimental_decide input: state and questions with boolean, choice, score, or box.
#   openai     OpenAI Decisions API: model, input, and a questions array with predicate, choice, or score.
# Exit codes: 0 = no errors, 1 = validation errors (an unparsable JSON file included), 2 = usage error.
# Codes carried by exit 1: INVALID_JSON for an unparsable file, INPUT_TOO_DEEP for a document nested deeper than the
# checker can read, and the shape codes below.
# The report carries no request string values: every finding is a code, a JSON path, and a fixed message.
#
# Requires bash 3.2 or newer and jq 1.6 or newer. JSON is parsed and produced with jq; the report is printed raw
# so that characters JavaScript leaves unescaped, such as U+007F, survive unchanged.
set -euo pipefail

route=systemone
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
          usage_fail USAGE_ARGUMENT_VALUE_MISSING 'Option --route requires one of: systemone, bai, aisdk, openai.'
          return 1
        fi
        next=$1
        case $next in
          --*)
            usage_fail USAGE_ARGUMENT_VALUE_MISSING 'Option --route requires one of: systemone, bai, aisdk, openai.'
            return 1
            ;;
        esac
        case $next in
          systemone | bai | aisdk | openai) route=$next ;;
          *)
            usage_fail USAGE_UNKNOWN_ROUTE 'Unknown route. Use systemone, bai, aisdk, or openai.'
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
      stats: {
        questions: 0,
        noul: 0,
        boolean: 0,
        predicate: 0,
        choice: 0,
        score: 0,
        box: 0,
        estimatedStateTokens: 0
      }
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

def aqpath($index; $field):
  "$.questions[" + ($index | tostring) + "]" + (if $field == null then "" else "." + $field end);

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

def empty_types:
  { noul: 0, boolean: 0, predicate: 0, choice: 0, score: 0, box: 0 };

def bump($type):
  if $type == "noul" then .noul += 1
  elif $type == "boolean" then .boolean += 1
  elif $type == "predicate" then .predicate += 1
  elif $type == "choice" then .choice += 1
  elif $type == "score" then .score += 1
  elif $type == "box" then .box += 1
  else .
  end;

def empty_stats:
  { questions: 0, noul: 0, boolean: 0, predicate: 0, choice: 0, score: 0, box: 0, estimatedStateTokens: 0 };

def type_expected($route):
  if $route == "aisdk" then "boolean, choice, score, box"
  elif $route == "openai" then "predicate, choice, score"
  elif $route == "bai" then "noul, choice, score"
  else "noul, choice, score, box"
  end;

# Every dialect names the yes/no type differently, so a rejected name always maps the three spellings.
def dialect_hint($type):
  if $type == "noul" or $type == "predicate" or $type == "boolean" then
    " The yes/no type is \"noul\" in the TypeSafe dialect, \"predicate\" in the OpenAI Decisions dialect, and \"boolean\" in the AI SDK."
  else
    ""
  end;

def type_message($route; $type):
  "Question type must be one of " + type_expected($route) + " for route " + $route + "." + dialect_hint($type);

def finding($code; $path; $message):
  { code: $code, path: $path, message: $message };

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

# Every string value anywhere below, joined so a placeholder can be found by substring. Object keys are excluded:
# the APIs replace placeholders inside strings, never inside keys.
def string_values:
  [.. | strings] | join("\u0000");

def check_instructions($value; $id; $route):
  (if $route == "openai" then aqpath($id; "instructions") else qpath($id; "instructions") end) as $path
  | if ($value | has("instructions") | not) then
      [finding("INSTRUCTIONS_MISSING"; $path;
        "Every question requires instructions describing what to decide.")]
    elif (($value.instructions | is_content) | not) then
      [finding("INSTRUCTIONS_TYPE"; $path;
        "Instructions must be a string, an object, or an array.")]
    else
      []
    end;

# Yes/no criteria are optional. $kind is "NOUL" or "BOOLEAN" so the code names the dialect the caller used.
def check_yesno_criteria($value; $id; $kind; $route):
  qpath($id; "criteria") as $path
  | if ($value | has("criteria") | not) then
      { errors: [], warnings: [] }
    elif (($value.criteria | type) != "object") then
      { errors: [finding($kind + "_CRITERIA_TYPE"; $path;
          "Criteria for a yes/no question is optional but must be an object with true and false keys when present.")],
        warnings: [] }
    else
      ($value.criteria | keys_unsorted) as $keys
      | { errors: [
            $keys[] as $key
            | if ($key != "true" and $key != "false") then
                finding($kind + "_CRITERIA_KEY"; $path;
                  "Criteria keys for a yes/no question must be exactly \"true\" or \"false\".")
              elif (($value.criteria[$key] | is_content) | not) then
                finding($kind + "_CRITERIA_VALUE"; $path + ($key | path_key);
                  "A yes/no criteria description must be a string, an object, or an array.")
              else
                empty
              end
          ],
          warnings: [] }
    end;

def check_choice_criteria($value; $id; $route):
  qpath($id; "criteria") as $path
  | if (($value.criteria | type) != "object") then
      { errors: [finding("CHOICE_CRITERIA_MISSING"; $path;
          "A choice question requires criteria: an object mapping each option to its description.")],
        warnings: [] }
    else
      ($value.criteria | keys_unsorted) as $options
      | ($options | length) as $count
      | (if ($count >= 1 and $count <= 255) then
           []
         else
           [finding("CHOICE_CRITERIA_COUNT"; $path;
             "A choice question takes 1 to 255 options; this one has " + ($count | tostring) + ".")]
         end) as $count_errors
      | [ $options[] as $option
          | if (($value.criteria[$option] | is_choice_option) | not) then
              finding("CHOICE_CRITERIA_VALUE"; $path + ($option | path_key);
                "An option description must be null, a string, an object, or an array.")
            else
              empty
            end
        ] as $value_errors
      | (if ($count >= 1 and $count <= 255
             and ([ $options[] | select(. == "none" or . == "other" or . == "unknown") ] | length) == 0) then
           [finding("NO_FALLBACK_OPTION"; $path;
             "No none/other/unknown option is defined, so the model must pick one of the listed options. This is a heuristic check, not an API rule.")]
         else
           []
         end) as $fallback_warnings
      | { errors: ($count_errors + $value_errors), warnings: $fallback_warnings }
    end;

# $minimum is 2 on the b.ai route, which rejects a single level; the other routes accept 1 level with a warning.
def check_score_criteria($value; $id; $route; $minimum):
  qpath($id; "criteria") as $path
  | if (($value.criteria | type) != "array") then
      { errors: [finding("SCORE_CRITERIA_MISSING"; $path;
          "A score question requires criteria: an ordered array of level descriptions.")],
        warnings: [] }
    else
      ($value.criteria | length) as $levels
      | (if $levels < $minimum or $levels > 10 then
           (if $minimum == 2 then
              [finding("SCORE_CRITERIA_COUNT"; $path;
                "A score question takes 2 to 10 levels; this one has " + ($levels | tostring) + ".")]
            else
              [finding("SCORE_CRITERIA_COUNT"; $path;
                "A score question takes 1 to 10 levels; this one has " + ($levels | tostring) + ".")]
            end)
         else
           []
         end) as $count_errors
      | (if $levels == 1 and $minimum == 1 then
           (if $route == "aisdk" then
              [finding("SCORE_LEVELS_PORTABILITY"; $path;
                "A single level is valid for the AI SDK decision model contract, but the language-model adapters require 2 or more, so this request is not portable.")]
            else
              [finding("SCORE_LEVELS_SINGLE"; $path;
                "A single level cannot separate answers: every score collapses to the same value. The API accepts it, but 2 or more levels are recommended.")]
            end)
         else
           []
         end) as $count_warnings
      | [ range(0; $levels) as $index
          | if (($value.criteria[$index] | is_content) | not) then
              finding("SCORE_LEVEL_TYPE"; $path + "[" + ($index | tostring) + "]";
                "A score level description must be a string, an object, or an array; null is rejected.")
            else
              empty
            end
        ] as $level_errors
      | { errors: ($count_errors + $level_errors), warnings: $count_warnings }
    end;

# TypeSafe dialect: one question in the questions map. $route is systemone or bai.
def validate_systemone_question($id; $value; $route):
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
        types: empty_types
      }
    else
      ($value.type) as $type
      | (if $route == "bai" then ["noul", "choice", "score"] else ["noul", "choice", "score", "box"] end) as $allowed
      | if (($type | type) != "string") or (($allowed | index($type)) == null) then
          {
            errors: ($id_errors + [finding("QUESTION_TYPE"; qpath($id; "type"); type_message($route; $type))]),
            warnings: [],
            types: empty_types
          }
        else
          (check_instructions($value; $id; $route)) as $instruction_errors
          | (if $type == "noul" then
               check_yesno_criteria($value; $id; "NOUL"; $route)
             elif $type == "choice" then
               check_choice_criteria($value; $id; $route)
             elif $type == "score" then
               check_score_criteria($value; $id; $route; (if $route == "bai" then 2 else 1 end))
             else
               (if ($value | has("criteria")) then
                  { errors: [finding("BOX_CRITERIA_UNSUPPORTED"; qpath($id; "criteria");
                      "A box question takes no criteria: it locates one thing in an image and returns four edges.")],
                    warnings: [] }
                else
                  { errors: [], warnings: [] }
                end)
             end) as $criteria_result
          | (if $type == "box" then
               [finding("BOX_REQUIREMENTS"; qpath($id; "type");
                 "A box question needs Jev 1.14 (jev-1.14.0 or jev-latest) and an image asset, and the request must send the TypeSafe-Danger-Zone-Images: true header. Box and images are documented as not production-ready.")]
             else
               []
             end) as $box_warnings
          | {
              errors: ($id_errors + $instruction_errors + $criteria_result.errors),
              warnings: ($criteria_result.warnings + $box_warnings),
              types: (empty_types | bump($type))
            }
        end
    end;

# AI SDK experimental_decide: state plus a questions map with boolean, choice, score, or box.
def validate_aisdk_question($id; $value):
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
        types: empty_types
      }
    else
      ($value.type) as $type
      | if (($type | type) != "string") or ((["boolean", "choice", "score", "box"] | index($type)) == null) then
          {
            errors: ($id_errors + [finding("QUESTION_TYPE"; qpath($id; "type"); type_message("aisdk"; $type))]),
            warnings: [],
            types: empty_types
          }
        else
          (check_instructions($value; $id; "aisdk")) as $instruction_errors
          | (if $type == "boolean" then
               check_yesno_criteria($value; $id; "BOOLEAN"; "aisdk")
             elif $type == "choice" then
               check_choice_criteria($value; $id; "aisdk")
             elif $type == "score" then
               check_score_criteria($value; $id; "aisdk"; 1)
             else
               (if ($value | has("criteria")) then
                  { errors: [finding("BOX_CRITERIA_UNSUPPORTED"; qpath($id; "criteria");
                      "A box question takes no criteria: it locates one thing in an image and returns four edges.")],
                    warnings: [] }
                else
                  { errors: [], warnings: [] }
                end)
             end) as $criteria_result
          | (if $type == "box" then
               [finding("BOX_PROVIDER_PORTABILITY"; qpath($id; "type");
                 "Only the TypeSafe provider implements box questions on the AI SDK decision model contract; the language-model adapters and the other native providers reject them.")]
             else
               []
             end) as $box_warnings
          | {
              errors: ($id_errors + $instruction_errors + $criteria_result.errors),
              warnings: ($criteria_result.warnings + $box_warnings),
              types: (empty_types | bump($type))
            }
        end
    end;

# OpenAI Decisions dialect: one entry of the questions array.
def validate_openai_question($index; $value):
  aqpath($index; null) as $base
  | if ($value | type) != "object" then
      {
        errors: [finding("QUESTION_NOT_OBJECT"; $base;
          "Each question must be a JSON object with type, name, and instructions fields.")],
        warnings: [],
        types: empty_types
      }
    else
      ($value.type) as $type
      | (if (($type | type) != "string") or ((["predicate", "choice", "score"] | index($type)) == null) then
           [finding("QUESTION_TYPE"; aqpath($index; "type"); type_message("openai"; $type))]
         else
           []
         end) as $type_errors
      | (if ($value | has("criteria")) then
           [finding("CRITERIA_NOT_SUPPORTED"; aqpath($index; "criteria");
             "The OpenAI Decisions dialect has no criteria field: a predicate takes instructions only, a choice takes choices[{value, description}], and a score takes levels[{label, description}]. Criteria belongs to the TypeSafe dialect.")]
         else
           []
         end) as $criteria_errors
      | (check_instructions($value; $index; "openai")) as $instruction_errors
      | (if (($value | has("name")) | not) then
           [finding("QUESTION_NAME_MISSING"; aqpath($index; "name");
             "Every question in the OpenAI Decisions dialect requires a name: a non-empty string that identifies the answer.")]
         elif (($value.name | type) != "string") then
           [finding("QUESTION_NAME_TYPE"; aqpath($index; "name");
             "A question name must be a string.")]
         elif ($value.name | ts_blank) then
           [finding("QUESTION_NAME_MISSING"; aqpath($index; "name");
             "Every question in the OpenAI Decisions dialect requires a name: a non-empty string that identifies the answer.")]
         else
           []
         end) as $name_errors
      | (if ($type_errors | length) > 0 then
           { errors: [], warnings: [] }
         elif $type == "choice" then
           (if (($value.choices | type) != "array") then
              { errors: [finding("CHOICE_CHOICES_MISSING"; aqpath($index; "choices");
                  "A choice question requires choices: an array of {value, description} objects.")],
                warnings: [] }
            else
              ($value.choices | length) as $count
              | (if ($count >= 2 and $count <= 255) then
                   []
                 else
                   [finding("CHOICE_CHOICES_COUNT"; aqpath($index; "choices");
                     "A choice question takes 2 to 255 choices; this one has " + ($count | tostring) + ".")]
                 end) as $count_errors
              | [ range(0; $count) as $position
                  | ($value.choices[$position]) as $choice
                  | if ($choice | type) != "object" then
                      finding("CHOICE_NOT_OBJECT"; aqpath($index; "choices") + "[" + ($position | tostring) + "]";
                        "Each choice must be a JSON object with a value and an optional description.")
                    elif (($choice | has("value")) | not) then
                      finding("CHOICE_VALUE_MISSING"; aqpath($index; "choices") + "[" + ($position | tostring) + "].value";
                        "Each choice requires a value.")
                    elif (($choice.value | type) != "string" and ($choice.value | type) != "boolean") then
                      finding("CHOICE_VALUE_TYPE"; aqpath($index; "choices") + "[" + ($position | tostring) + "].value";
                        "A choice value must be a string or a boolean.")
                    elif (($choice | has("description")) and (($choice.description | is_content) | not)) then
                      finding("CHOICE_DESCRIPTION_TYPE"; aqpath($index; "choices") + "[" + ($position | tostring) + "].description";
                        "A choice description must be a string, an object, or an array when present.")
                    else
                      empty
                    end
                ] as $choice_errors
              | ([ $value.choices[] | select((type == "object") and has("value")) | (.value | tojson) ]
                 | group_by(.) | map(select(length > 1)) | length) as $duplicates
              | (if $duplicates > 0 then
                   [finding("CHOICE_VALUE_DUPLICATE"; aqpath($index; "choices");
                     "Choice values must be unique; this list repeats at least one value.")]
                 else
                   []
                 end) as $duplicate_errors
              | { errors: ($count_errors + $choice_errors + $duplicate_errors), warnings: [] }
            end)
         elif $type == "score" then
           (if (($value.levels | type) != "array") then
              { errors: [finding("SCORE_LEVELS_MISSING"; aqpath($index; "levels");
                  "A score question requires levels: an ordered array of {label, description} objects.")],
                warnings: [] }
            else
              ($value.levels | length) as $count
              | (if ($count >= 2 and $count <= 10) then
                   []
                 else
                   [finding("SCORE_LEVELS_COUNT"; aqpath($index; "levels");
                     "A score question takes 2 to 10 levels; this one has " + ($count | tostring) + ".")]
                 end) as $count_errors
              | [ range(0; $count) as $position
                  | ($value.levels[$position]) as $level
                  | if ($level | type) != "object" then
                      finding("SCORE_LEVEL_NOT_OBJECT"; aqpath($index; "levels") + "[" + ($position | tostring) + "]";
                        "Each level must be a JSON object with a label and an optional description.")
                    elif (($level | has("label")) | not) then
                      finding("SCORE_LABEL_MISSING"; aqpath($index; "levels") + "[" + ($position | tostring) + "].label";
                        "Each level requires a label.")
                    elif (($level.label | type) != "string") then
                      finding("SCORE_LABEL_TYPE"; aqpath($index; "levels") + "[" + ($position | tostring) + "].label";
                        "A level label must be a string.")
                    elif (($level | has("description")) and (($level.description | is_content) | not)) then
                      finding("SCORE_DESCRIPTION_TYPE"; aqpath($index; "levels") + "[" + ($position | tostring) + "].description";
                        "A level description must be a string, an object, or an array when present.")
                    else
                      empty
                    end
                ] as $level_errors
              | { errors: ($count_errors + $level_errors), warnings: [] }
            end)
         else
           { errors: [], warnings: [] }
         end) as $answer_shape
      | {
          errors: ($type_errors + $criteria_errors + $instruction_errors + $name_errors + $answer_shape.errors),
          warnings: $answer_shape.warnings,
          types: (if ($type_errors | length) > 0 then empty_types else (empty_types | bump($type)) end)
        }
    end;

def asset_errors($doc):
  if ($doc | has("assets") | not) then
    { errors: [], warnings: [] }
  elif (($doc.assets | type) != "object") or (($doc.assets | length) == 0) then
    { errors: [finding("ASSETS_TYPE"; "$.assets";
        "assets must be a non-empty object mapping each placeholder to an image asset.")],
      warnings: [] }
  else
    (($doc.state | string_values) + "\u0000" + ($doc.questions | string_values)) as $haystack
    | ([ $doc.assets | keys_unsorted[] as $key
         | ($doc.assets[$key]) as $asset
         | if ($asset | type) != "object" then
             [finding("ASSET_NOT_OBJECT"; "$.assets" + ($key | path_key);
               "Each asset must be a JSON object.")]
           else
             ([ (if (($asset | has("type")) and ($asset.type != "image")) then
                   finding("ASSET_TYPE"; "$.assets" + ($key | path_key) + ".type";
                     "An asset type must be \"image\" when present.")
                 else
                   empty
                 end) ]
              + [ (if (($asset | has("data_base64"))
                       and (((["png", "jpg", "jpeg"] | index($asset.format // "")) == null))) then
                    finding("ASSET_FORMAT"; "$.assets" + ($key | path_key) + ".format";
                      "An asset that carries data_base64 requires format to be one of png, jpg, or jpeg.")
                  else
                    empty
                  end) ])
           end
       ] | add // []) as $errors
    | [ $doc.assets | keys_unsorted[] as $key
        | (if ($haystack | contains($key)) then
             empty
           else
             finding("ASSET_UNREFERENCED"; "$.assets" + ($key | path_key);
               "No string in state, instructions, criteria, choices, or levels contains this placeholder, so the API rejects the request. This check is a substring test, not the API's own replacement rule.")
           end)
      ] as $warnings
    | { errors: $errors, warnings: $warnings }
  end;

def validate($doc; $route):
  if ($doc | type) != "object" then
    {
      errors: [finding("ROOT_NOT_OBJECT"; "$"; "The request document must be a JSON object.")],
      warnings: [],
      stats: empty_stats
    }
  else
    (if $route == "openai" then ["model", "input", "questions"]
     elif $route == "aisdk" then ["state", "questions"]
     elif $route == "bai" then ["state", "model", "questions", "stream", "assets"]
     else ["state", "model", "questions", "assets"]
     end) as $allowed_fields
    | ([ $doc | keys_unsorted[] as $key
         | if ($allowed_fields | index($key)) == null then
             finding("UNKNOWN_TOP_LEVEL_FIELD"; "$" + ($key | path_key);
               "This top-level field is not part of the documented request shape for route " + $route + " and is ignored by the API.")
           else
             empty
           end
       ]) as $unknown_warnings
    | (if $route == "openai" then
         (if ($doc | has("input") | not) then
            [finding("INPUT_MISSING"; "$.input";
              "The OpenAI Decisions API requires input: the text, JSON, or conversation the questions are asked about.")]
          elif (($doc.input | type) == "string") then
            (if ($doc.input | ts_blank) then
               [finding("INPUT_EMPTY"; "$.input"; "The input string must not be empty or whitespace only.")]
             else
               []
             end)
          elif (($doc.input | type) == "array") then
            (if ($doc.input | length) == 0 then
               [finding("INPUT_EMPTY"; "$.input"; "The input array must contain at least one item.")]
             else
               []
             end)
          else
            [finding("INPUT_TYPE"; "$.input";
              "input must be a string or a non-empty array.")]
          end)
       else
         (if ($doc | has("state") | not) then
            [finding("STATE_MISSING"; "$.state";
              "The request requires state: the content every question is evaluated against.")]
          elif (($doc.state | is_content) | not) then
            [finding("STATE_TYPE"; "$.state";
              "State must be a string, an object, or an array; null, numbers, and booleans are rejected.")]
          else
            []
          end)
       end) as $state_errors
    | (if $route == "aisdk" then
         { errors: [], warnings: [] }
       elif (($doc.model | type) == "string" and (($doc.model | ts_blank) | not)) then
         (if $route == "bai" then
            (if ((["jev-1.13.0", "jev-latest"] | index($doc.model)) == null) then
               { errors: [finding("MODEL_UNSUPPORTED"; "$.model";
                   "The b.ai Decisions API accepts only jev-1.13.0 or jev-latest.")],
                 warnings: [] }
             else
               { errors: [], warnings: [] }
             end)
          elif $route == "openai" then
            (if $doc.model != "gpt-6-luna" then
               { errors: [],
                 warnings: [finding("MODEL_UNVERIFIED"; "$.model";
                   "gpt-6-luna is the only model the OpenAI Decisions API documents as supported on 2026-11-08. This id was not verified.")] }
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
    | (if ($route == "bai" and ($doc | has("assets"))) then
         [finding("ASSETS_NOT_SUPPORTED"; "$.assets";
           "The b.ai Decisions API documents no assets field; images are a TypeSafe System One feature.")]
       else
         []
       end) as $assets_errors
    | (if $route == "openai" then
         (if (($doc.questions | type) != "array") then
            {
              errors: [finding("QUESTIONS_MISSING"; "$.questions";
                "The OpenAI Decisions API requires questions: an array of 1 to 400 question objects.")],
              results: [],
              count: 0,
              duplicate_names: 0
            }
          else
            ($doc.questions | length) as $count
            | {
                errors: (if $count == 0 then
                           [finding("QUESTIONS_EMPTY"; "$.questions"; "The questions array must contain at least one question.")]
                         elif $count > 400 then
                           [finding("QUESTIONS_COUNT"; "$.questions";
                             "The OpenAI Decisions API accepts 1 to 400 questions; this request has " + ($count | tostring) + ".")]
                         else
                           []
                         end),
                results: [ range(0; $count) as $index
                           | ($doc.questions[$index] | validate_openai_question($index; .)) ],
                count: $count,
                duplicate_names: ([ $doc.questions[]
                                    | select((type == "object") and (.name | type) == "string" and ((.name | ts_blank) | not))
                                    | .name ]
                                  | group_by(.) | map(select(length > 1)) | length)
              }
          end)
       elif (($doc.questions | type) != "object") then
         {
           errors: [finding("QUESTIONS_MISSING"; "$.questions";
             "The request requires questions: a non-empty map of question ids to question definitions.")],
           results: [],
           count: 0,
           duplicate_names: 0
         }
       else
         ($doc.questions | keys_unsorted) as $ids
         | {
             errors: (if ($ids | length) == 0 then
                        [finding("QUESTIONS_EMPTY"; "$.questions"; "The questions map must contain at least one question.")]
                      else
                        []
                      end),
             results: [ $ids[] as $id
                        | ($doc.questions[$id]
                           | if $route == "aisdk" then validate_aisdk_question($id; .)
                             else validate_systemone_question($id; .; $route)
                             end) ],
             count: ($ids | length),
             duplicate_names: 0
           }
       end) as $questions_result
    | ([ $questions_result.results[] | .errors[] ]
       + (if ($questions_result.duplicate_names // 0) > 0 then
            [finding("QUESTION_NAME_DUPLICATE"; "$.questions";
              "Question names must be unique; this request repeats at least one name.")]
          else
            []
          end)) as $question_errors
    | ([ $questions_result.results[] | .warnings[] ]) as $question_warnings
    | (reduce $questions_result.results[].types as $t
         (empty_types; with_entries(.value += ($t[.key] // 0)))) as $type_counts
    | ($doc | scan_secrets("$")) as $secret_errors
    | (if $route == "systemone" then asset_errors($doc) else { errors: [], warnings: [] } end) as $asset_result
    | ((if $route == "openai" then
          (if ($doc | has("input")) then ($doc.input | js_len) else 0 end)
        else
          (if ($doc | has("state")) then ($doc.state | js_len) else 0 end)
        end)
       + (if (($doc.questions | type) == "object" or ($doc.questions | type) == "array") then
            ([ $doc.questions[] | js_len ] | max // 0)
          else
            0
          end)) as $characters
    | (($characters / 4) | ceil) as $tokens
    | { errors: ($state_errors + $model_result.errors + $stream_errors + $assets_errors
                 + $questions_result.errors + $question_errors + $secret_errors + $asset_result.errors),
        warnings: ($unknown_warnings + $model_result.warnings + $question_warnings + $asset_result.warnings
                   + (if ($route == "systemone" or $route == "bai") and $tokens > 32000 then
                        [finding("INPUT_LARGE"; "$.state";
                          "The serialized state plus the longest question is roughly " + ($tokens | tostring)
                          + " tokens by a length/4 estimate. The TypeSafe limit for state plus the longest question is 32000. This figure is an estimate, not a measured token count.")]
                      else
                        []
                      end)
                   + (if $route == "openai" and ($doc.input | type) == "string"
                         and ($doc.input | str_len) > 10485760 then
                        [finding("INPUT_TOO_LONG"; "$.input";
                          "The OpenAI Decisions API accepts at most 10,485,760 characters of string input.")]
                      else
                        []
                      end)),
        stats: ({ questions: $questions_result.count } + $type_counts + { estimatedStateTokens: $tokens }) }
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

  tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/decision-request.XXXXXX")
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

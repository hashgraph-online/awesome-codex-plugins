# check-results.jq: structure gate for a hyper-aso results.json.
#
# Run: jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json
# Prints "ok" and exits 0 when the payload is structurally valid. Otherwise
# writes one "E<TAB>message" line per violation to stderr and exits 1.
# Needs jq 1.6+ (halt_error). Unknown extra keys are allowed.

def enum_ok($v; $allowed): ($allowed | index([$v])) != null;
def isobj: type == "object";
def isarr: type == "array";

def category_errors:
  if (.categories | isarr | not) then ["categories must be an array"]
  else [.categories | to_entries[] | .key as $i | .value as $c
    | if ($c | isobj | not) then "categories[\($i)] must be an object"
      elif (($c.name | type) != "string") or ($c.name == "") then "categories[\($i)].name must be a non-empty string"
      elif (enum_ok($c.status; ["measured", "unknown", "not-applicable"]) | not) then "categories[\($i)].status must be measured, unknown, or not-applicable"
      elif ($c.status == "measured") and ((($c.score | type) != "number") or ($c.score < 0) or ($c.score > 100)) then "categories[\($i)].score must be 0..100 when measured"
      elif ($c.status != "measured") and ($c.score != null) then "categories[\($i)].score must be null when \($c.status)"
      else empty end]
  end;

def finding_errors:
  if (.findings | isarr | not) then ["findings must be an array"]
  else [.findings | to_entries[] | .key as $i | .value as $f
    | if ($f | isobj | not) then "findings[\($i)] must be an object"
      elif (enum_ok($f.severity; ["critical", "warning", "info"]) | not) then "findings[\($i)].severity must be critical, warning, or info"
      elif (enum_ok($f.evidence_grade; ["official", "live", "console", "tool", "synthetic", "heuristic"]) | not) then "findings[\($i)].evidence_grade must be official, live, console, tool, synthetic, or heuristic"
      elif (enum_ok($f.confidence; ["high", "medium", "low"]) | not) then "findings[\($i)].confidence must be high, medium, or low"
      elif (enum_ok($f.store; ["app_store", "google_play", "both", "other"]) | not) then "findings[\($i)].store must be app_store, google_play, both, or other"
      elif (($f.recommendation | type) != "string") or ($f.recommendation == "") then "findings[\($i)].recommendation must be a non-empty string"
      elif ($f.severity != "info") and ((($f.evidence | type) != "string") or ($f.evidence == "")) then "findings[\($i)].evidence is required for \($f.severity)"
      else empty end]
  end;

def store_errors:
  if (.stores == null) then []
  elif (.stores | isobj | not) then ["stores must be an object"]
  else [.stores | to_entries[] | .key as $k | .value as $s
    | if (enum_ok($k; ["app_store", "google_play", "one_store", "other"]) | not) then "stores.\($k) is not a known store key"
      elif ($s | isobj | not) then "stores.\($k) must be an object"
      elif (enum_ok($s.status; ["in-scope", "not-applicable", "unknown"]) | not) then "stores.\($k).status must be in-scope, not-applicable, or unknown"
      elif ($s.locales != null) and ($s.locales | isarr | not) then "stores.\($k).locales must be an array"
      else empty end]
  end;

def keyword_errors:
  if (.keyword_set == null) then []
  elif (.keyword_set | isobj | not) then ["keyword_set must be an object"]
  elif (.keyword_set.keywords != null) and (.keyword_set.keywords | isarr | not) then ["keyword_set.keywords must be an array"]
  else [(.keyword_set.keywords // []) | to_entries[] | .key as $i | .value as $k
    | if (($k.term | type) != "string") or ($k.term == "") then "keyword_set.keywords[\($i)].term must be a non-empty string"
      elif ($k.popularity != null) and (($k.source | type) != "string" or $k.source == "") then "keyword_set.keywords[\($i)].source must name where the popularity value came from"
      else empty end]
  end;

def history_errors:
  if (.score_history == null) then []
  elif (.score_history | isarr | not) then ["score_history must be an array"]
  elif (.score_history | length) == 0 then ["score_history must not be empty when present"]
  elif (.score_history[0].decision != "baseline") then ["score_history[0].decision must be baseline"]
  else [.score_history | to_entries[] | .key as $i | .value as $h
    | if (enum_ok($h.decision; ["baseline", "kept", "discarded", "reset"]) | not) then "score_history[\($i)].decision must be baseline, kept, discarded, or reset"
      elif (($h.score | type) != "number") then "score_history[\($i)].score must be a number"
      elif (($h.evaluator_version | type) != "string") then "score_history[\($i)].evaluator_version is required"
      else empty end]
  end;

def best_run_errors:
  if (.best_run == null) then
    (if (.score_history != null) and (.status == "complete") then ["best_run is required when score_history is present and status is complete"] else [] end)
  elif (.best_run | isobj | not) then ["best_run must be an object"]
  else
    .best_run.iteration as $it
    | ([(.score_history // [])[] | select(.decision == "kept" or .decision == "baseline")]) as $kept
    | ([$kept[] | select(.iteration == $it)] | first) as $hit
    | if $hit == null then ["best_run.iteration must point to a kept or baseline iteration"]
      elif ([$kept[] | select(.score > $hit.score)] | length) > 0 then ["best_run must be the highest-scoring kept iteration"]
      else [] end
  end;

(
  if (type != "object") then ["results.json must be a JSON object"]
  else
    [ (["project_name", "status", "categories", "findings"][] as $k | select(has($k) | not) | "missing required field: \($k)") ]
    + (if has("status") and (enum_ok(.status; ["running", "idle", "complete"]) | not) then ["status must be running, idle, or complete"] else [] end)
    + (if has("categories") then category_errors else [] end)
    + (if has("findings") then finding_errors else [] end)
    + store_errors + keyword_errors + history_errors + best_run_errors
  end
) as $errs
| if ($errs | length) == 0 then "ok"
  else ($errs | map("E\t" + .) | join("\n") + "\n") | halt_error(1)
  end

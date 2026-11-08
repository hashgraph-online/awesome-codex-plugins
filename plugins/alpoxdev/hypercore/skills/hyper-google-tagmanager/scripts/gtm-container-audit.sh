#!/usr/bin/env bash
# gtm-container-audit.sh - audit a Google Tag Manager container export
# (Admin > Export Container, or a Tag Manager API containerVersion) and report
# inventory counts and rule-based findings.
#
# Usage: bash gtm-container-audit.sh --file <export.json>
#   --file  container export JSON (exportFormatVersion 2), or a bare
#           containerVersion object as the Tag Manager API returns it
#
# Output (stdout, one JSON object):
#   {"container": {"publicId": "GTM-XXXX", "name": "...", "containerVersionId": "12"},
#    "counts": {"tags": 0, "triggers": 0, "variables": 0, "builtInVariables": 0,
#               "customTemplates": 0, "folders": 0, "pausedTags": 0, "customHtmlTags": 0},
#    "tagTypes": {"gaawe": 3, "googtag": 1},
#    "findings": [{"severity": "error|warn|info", "code": "...", "subject": "...", "detail": "..."}]}
#
# Finding codes: UA_TAG, NO_FIRING_TRIGGER, PAUSED_TAG, CUSTOM_HTML,
# CUSTOM_HTML_DOCUMENT_WRITE, DUPLICATE_GOOGLE_TAG, CONSENT_NOT_SET,
# HISTORY_CHANGE_PAGEVIEW, UNUSED_TRIGGER, UNUSED_VARIABLE, NO_CONSENT_INIT.
# Findings are sorted by severity, code, then subject.
#
# It reads the one file and writes nothing. Exit codes: 0 audited (even with
# findings), 2 bad arguments or a file that is not a container export,
# 3 missing dependency (jq). Requires bash 3.2+ and jq 1.6+.
set -euo pipefail

FILE=""
while [ "$#" -gt 0 ]; do
  case $1 in
    --file)
      [ "$#" -ge 2 ] || { echo "gtm-container-audit: --file needs a value" >&2; exit 2; }
      FILE=$2
      shift 2
      ;;
    -h | --help)
      awk 'NR > 1 && /^#/ { print; next } NR > 1 { exit }' "$0"
      exit 0
      ;;
    *)
      echo "gtm-container-audit: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

command -v jq >/dev/null 2>&1 || { echo "gtm-container-audit: jq is required" >&2; exit 3; }
[ -n "$FILE" ] || { echo "gtm-container-audit: --file is required" >&2; exit 2; }
[ -f "$FILE" ] || { echo "gtm-container-audit: not a file: $FILE" >&2; exit 2; }
jq -e 'type == "object" and ((.containerVersion | type) == "object" or (.container | type) == "object" or (.tag | type) == "array")' \
  "$FILE" >/dev/null 2>&1 || { echo "gtm-container-audit: not a GTM container export: $FILE" >&2; exit 2; }

jq '
  (if (.containerVersion | type) == "object" then .containerVersion else . end) as $v
  | ($v.tag // []) as $tags
  | ($v.trigger // []) as $triggers
  | ($v.variable // []) as $vars
  | ([$v.tag // [], $v.trigger // [], $v.variable // [], $v.customTemplate // []] | tostring) as $allText
  # Exports write enums as CUSTOM_EVENT or NOT_SET, the API as customEvent or
  # notSet; compare both through n. 2147479572 is the built-in
  # Consent Initialization - All Pages trigger.
  | def n: (. // "") | ascii_downcase | gsub("_"; "");
  def p($t; $k): ([$t.parameter[]? | select(.key == $k) | .value] | first) // "";
  ([$tags[] | (.firingTriggerId // [])[], (.blockingTriggerId // [])[]] | unique) as $usedTriggers
  | ([$tags[] | (.setupTag // [])[]?.tagName, (.teardownTag // [])[]?.tagName] | map(select(. != null)) | unique) as $sequenced
  | ($triggers | map(select((.type | n) == "historychange" and (.triggerId as $id | $usedTriggers | index($id)))) | length) as $historyTriggers
  | ([$tags[] | select(.type == "googtag") | p(.; "tagId")] | map(select(. != "")) | group_by(.) | map(select(length > 1) | .[0])) as $dupGoogleTags
  | {container: {publicId: ($v.container.publicId // null),
                 name: ($v.container.name // null),
                 containerVersionId: ($v.containerVersionId // null)},
     counts: {tags: ($tags | length), triggers: ($triggers | length), variables: ($vars | length),
              builtInVariables: (($v.builtInVariable // []) | length),
              customTemplates: (($v.customTemplate // []) | length),
              folders: (($v.folder // []) | length),
              pausedTags: ([$tags[] | select(.paused == true)] | length),
              customHtmlTags: ([$tags[] | select(.type == "html")] | length)},
     tagTypes: ([$tags[] | .type] | group_by(.) | map({key: .[0], value: length}) | from_entries),
     findings: ([
       ($tags[] | select((.type | n) == "ua")
        | {severity: "error", code: "UA_TAG", subject: .name,
           detail: "Universal Analytics tag; UA stopped processing data, remove it or replace it with a GA4 event tag"}),
       ($tags[] | select(((.firingTriggerId // []) | length) == 0 and (.name as $n | $sequenced | index($n) | not))
        | {severity: "warn", code: "NO_FIRING_TRIGGER", subject: .name,
           detail: "tag has no firing trigger and is not a setup or cleanup tag, so it never fires"}),
       ($tags[] | select(.paused == true)
        | {severity: "info", code: "PAUSED_TAG", subject: .name, detail: "tag is paused"}),
       ($tags[] | select(.type == "html")
        | {severity: "info", code: "CUSTOM_HTML", subject: .name,
           detail: "Custom HTML tag runs unsandboxed page script; prefer a template and keep it under review"}),
       ($tags[] | select(.type == "html" and (p(.; "html") | test("document\\.write")))
        | {severity: "warn", code: "CUSTOM_HTML_DOCUMENT_WRITE", subject: .name,
           detail: "Custom HTML tag calls document.write"}),
       ($dupGoogleTags[]
        | {severity: "warn", code: "DUPLICATE_GOOGLE_TAG", subject: .,
           detail: "more than one Google tag is configured with this tag ID"}),
       ($tags[] | select((.type | n) != "html" and ((.consentSettings.consentStatus | n) as $c | $c == "" or $c == "notset"))
        | {severity: "info", code: "CONSENT_NOT_SET", subject: .name,
           detail: "tag has no consent setting (Not set); confirm its built-in consent checks cover it"}),
       (if $historyTriggers > 0 and ([$tags[] | select(.type == "googtag")] | length) > 0
        then {severity: "warn", code: "HISTORY_CHANGE_PAGEVIEW", subject: "History Change",
              detail: "a History Change trigger exists next to a Google tag; if it sends page_view, turn off enhanced measurement history events to avoid double page_view"}
        else empty end),
       ($triggers[] | select(.triggerId as $id | $usedTriggers | index($id) | not)
        | select(.triggerId as $id | [$triggers[] | select((.type | n) == "triggergroup") | tostring | contains("\"" + $id + "\"")] | any | not)
        | {severity: "info", code: "UNUSED_TRIGGER", subject: .name, detail: "no tag fires on or is blocked by this trigger"}),
       ($vars[] | select(.name as $n | $allText | contains("{{" + $n + "}}") | not)
        | {severity: "info", code: "UNUSED_VARIABLE", subject: .name, detail: "no tag, trigger, variable, or template references {{\(.name)}}"}),
       (if ($tags | length) > 0
            and ([$tags[] | (.firingTriggerId // [])[] | select(. == "2147479572")] | length) == 0
            and ([$triggers[] | select((.type | n) == "consentinit")] | length) == 0
        then {severity: "info", code: "NO_CONSENT_INIT", subject: "Consent Initialization",
              detail: "no tag fires on Consent Initialization; consent defaults must then come from page code before the container snippet"}
        else empty end)
     ] | sort_by((if .severity == "error" then 0 elif .severity == "warn" then 1 else 2 end), .code, .subject))}
' "$FILE"

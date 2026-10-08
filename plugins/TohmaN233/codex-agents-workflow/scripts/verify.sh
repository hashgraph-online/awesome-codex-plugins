#!/bin/sh
set -eu

run_tests=true
if [ "$#" -gt 0 ]; then
  [ "$#" -eq 1 ] && [ "$1" = --static-only ] \
    || { printf '%s\n' 'Usage: verify.sh [--static-only]' >&2; exit 2; }
  run_tests=false
fi

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
plugin_dir=$(CDPATH= cd "$script_dir/.." && pwd) || exit 1
repo_dir=$(CDPATH= cd "$plugin_dir/../.." && pwd) || exit 1

if [ -d "$plugin_dir/agents" ]; then
  agent_files=$(find "$plugin_dir/agents" -type f -print -quit) || exit 1
  [ -z "$agent_files" ] \
    || { printf '%s\n' 'FAIL: fixed Agent files duplicate Workbench Roles' >&2; exit 1; }
fi

if grep -Enr 'role_ref|role_profile|ROLE <id>|Pinned Role behavior' \
  "$plugin_dir/control-plane/lib" "$plugin_dir/control-plane/web-src"; then
  printf '%s\n' 'FAIL: Workflow runtime still injects Workbench Role behavior' >&2
  exit 1
else
  search_status=$?
  [ "$search_status" -eq 1 ] \
    || { printf '%s\n' 'FAIL: could not inspect Workflow runtime Role behavior' >&2; exit "$search_status"; }
fi

grep -Fq 'workflow_role_templates' "$plugin_dir/skills/orchestration/SKILL.md"
grep -Fq 'workflow_role_template' "$plugin_dir/skills/orchestration/SKILL.md"
grep -Fq 'longest supported' "$plugin_dir/skills/orchestration/SKILL.md"
grep -Fq 'Never inject Role instructions into a Workflow node' "$plugin_dir/skills/orchestration/SKILL.md"

if [ "$run_tests" = true ]; then
  node "$plugin_dir/control-plane/test/run-tests.mjs"
else
  printf '%s\n' 'Static verification requested; control-plane test manifest not run.'
fi
git -C "$repo_dir" diff --check
printf '%s\n' 'VERIFY PASSED: Workbench Roles and Workflow execution have one non-overlapping path.'

#!/bin/sh

set -eu

usage() {
  cat >&2 <<'EOF'
Usage: bash .codex/skills/codebase-to-course/scripts/build-course.sh --course-dir <course-dir>
EOF
  exit 64
}

script_dir=$(
  CDPATH= cd -- "$(dirname "$0")" && pwd
)
# shellcheck source=./course-lib.sh
. "$script_dir/course-lib.sh"

course_dir_arg=

while [ $# -gt 0 ]; do
  case "$1" in
    --course-dir)
      [ $# -ge 2 ] || usage
      course_dir_arg=$2
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    --)
      shift
      break
      ;;
    *)
      course_die "unknown argument: $1"
      ;;
  esac
done

[ -n "$course_dir_arg" ] || usage

course_dir=$(course_resolve_path "$course_dir_arg")
course_require_dir "$course_dir"
course_require_dir "$course_dir/modules"
course_require_file "$course_dir/_base.html"
course_require_file "$course_dir/_footer.html"
course_require_file "$course_dir/styles.css"
course_require_file "$course_dir/main.js"

course_assemble_index "$course_dir"

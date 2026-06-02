#!/bin/sh

set -eu

usage() {
  cat >&2 <<'EOF'
Usage: bash .codex/skills/codebase-to-course/scripts/init-course.sh --source <repo-or-dir> [--out <course-dir>] [--title <title>] [--accent <vermillion|coral|teal|amber|forest>]
EOF
  exit 64
}

script_dir=$(
  CDPATH= cd -- "$(dirname "$0")" && pwd
)
# shellcheck source=./course-lib.sh
. "$script_dir/course-lib.sh"

source_arg=
out_arg=
title_arg=
accent=vermillion

while [ $# -gt 0 ]; do
  case "$1" in
    --source)
      [ $# -ge 2 ] || usage
      source_arg=$2
      shift 2
      ;;
    --out)
      [ $# -ge 2 ] || usage
      out_arg=$2
      shift 2
      ;;
    --title)
      [ $# -ge 2 ] || usage
      title_arg=$2
      shift 2
      ;;
    --accent)
      [ $# -ge 2 ] || usage
      accent=$2
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

[ -n "$source_arg" ] || usage

case "$source_arg" in
  http://*|https://*|git@*)
    course_die "remote repository URLs are not supported by init-course.sh; clone the repo locally first"
    ;;
esac

source_dir=$(course_resolve_path "$source_arg")
[ -d "$source_dir" ] || course_die "source directory does not exist: $source_dir"
source_name=${source_dir##*/}
if [ -z "$source_name" ] || [ "$source_name" = "/" ] || [ "$source_name" = "." ]; then
  source_name=source
fi

if [ -n "$title_arg" ]; then
  course_title=$title_arg
else
  course_title=$(course_derive_title_from_source "$source_dir")
fi

slug=$(course_slugify "$course_title")
workspace_root=$(pwd -P)

if [ -n "$out_arg" ]; then
  out_dir=$(course_resolve_path "$out_arg")
else
  out_dir=$(course_resolve_path "$workspace_root/.codex-artifacts/codebase-to-course/$slug")
fi

if [ -e "$out_dir" ] && [ ! -d "$out_dir" ]; then
  course_die "output path exists and is not a directory: $out_dir"
fi

if [ -d "$out_dir" ] && find "$out_dir" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
  course_die "output directory already exists and is not empty: $out_dir"
fi

course_set_accent_palette "$accent"

base_template=$(course_find_runtime_asset "_base.html") || course_die "missing runtime asset: _base.html"
footer_template=$(course_find_runtime_asset "_footer.html") || course_die "missing runtime asset: _footer.html"

mkdir -p "$out_dir/modules" "$out_dir/briefs"

course_prepare_base_template "$base_template" "$out_dir/_base.html" "$course_title" "$source_name" "$accent"
course_prepare_footer_template "$footer_template" "$out_dir/_footer.html" "$source_name"
course_copy_runtime_asset "styles.css" "$out_dir/styles.css"
course_copy_runtime_asset "main.js" "$out_dir/main.js"
course_patch_runtime_stylesheet "$out_dir/styles.css"

printf 'Initialized course scaffold at %s\n' "$out_dir"
printf 'Source: %s\n' "$source_dir"
printf 'Title: %s\n' "$course_title"
printf 'Accent: %s\n' "$accent"

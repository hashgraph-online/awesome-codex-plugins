#!/usr/bin/env bash
# detect_edit.sh: say whether the optional edit pack is installed. Always exits 0, so a caller can branch on the text.
#
#   edit: ready (film,sound,effect,photo,vector,light)
#   edit: not installed
#
# A component is listed only when its pinned CLI is there AND runs (`<cli> --version` succeeds), so a
# half-deleted or broken install does not count as ready. It needs nothing but B2M_EDIT_HOME
# (default ~/.brief2mp4/edit): not this repository, not the plugin folder.
set -u

HOME_DIR="${B2M_EDIT_HOME:-$HOME/.brief2mp4/edit}"
found=()

for pair in film:filmcraft sound:soundcraft effect:effectcraft photo:photocraft vector:vectorcraft light:lightcraft; do
  short="${pair%%:*}"; name="${pair##*:}"
  for cli in "$HOME_DIR/$name/$name-cli" "$HOME_DIR/$name/bin/$name-cli" "$HOME_DIR/$name/$name-cli.exe"; do
    if [[ -f "$cli" ]] && "$cli" --version >/dev/null 2>&1; then found+=("$short"); break; fi
  done
done

if [[ ${#found[@]} -gt 0 ]]; then
  (IFS=,; echo "edit: ready (${found[*]})")
else
  echo "edit: not installed"
fi
exit 0

#!/usr/bin/env bash
# install_edit.sh: install the command-line tools of the optional brief2mp4 edit pack. No sudo, ever.
#
#   bash install_edit.sh                              # film + sound
#   bash install_edit.sh --components film,sound,effect,photo,vector
#   bash install_edit.sh --components all --dry-run   # show what would be downloaded, change nothing
#   bash install_edit.sh --uninstall                  # remove everything this installer created
#   bash install_edit.sh --uninstall --components photo
#
# Components (free ArtCraft apps by storytold, MIT or Apache-2.0, pinned in versions.json)
#   film     FilmCraft    timeline editor (Premiere class)
#   sound    SoundCraft   multitrack audio workstation (mix, ducking, bounce)
#   effect   EffectCraft  layered, keyframed compositing (After Effects class)
#   photo    PhotoCraft   image editing (thumbnails, title cards)
#   vector   VectorCraft  vector drawing (logos, lower thirds as SVG)
#
# Each download is checked against the release's SHA256SUMS.txt and against the hash pinned in
# versions.json. When gpg is installed, SHA256SUMS.txt's signature is checked too.
# Installs into $B2M_EDIT_HOME (default ~/.brief2mp4/edit), copying versions.json and the recipes
# there so the pack keeps working if this folder moves. Safe to run again: finished apps are skipped.
# Never touches the system PATH: it prints the one line you can add yourself.
set -euo pipefail

PACK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${B2M_EDIT_HOME:-$HOME/.brief2mp4/edit}"
MANIFEST="$HOME_DIR/.b2m-edit-manifest"
ALL="film sound effect photo vector"
COMPONENTS="film,sound"; EXPLICIT=0; DRY=0; UNINSTALL=0
STAGE=""

say() { printf '%s\n' "$*"; }
die() { printf 'install_edit.sh: %s\n' "$1" >&2; exit "${2:-1}"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --components) COMPONENTS="${2:-}"; EXPLICIT=1; shift 2 ;;
    --components=*) COMPONENTS="${1#*=}"; EXPLICIT=1; shift ;;
    --dry-run) DRY=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) die "unknown option $1" 2 ;;
  esac
done
COMPONENTS="${COMPONENTS// /,}"
[[ "$COMPONENTS" == "all" ]] && COMPONENTS="${ALL// /,}"
[[ -n "$COMPONENTS" ]] || die "--components needs a value (film, sound, effect, photo, vector, all)" 2
for c in ${COMPONENTS//,/ }; do
  [[ " $ALL " == *" $c "* ]] || die "unknown component '$c' (film, sound, effect, photo, vector, all)" 2
done

platform_key() {
  if [[ -n "${B2M_EDIT_PLATFORM:-}" ]]; then printf '%s' "$B2M_EDIT_PLATFORM"; return; fi   # test hook
  local os arch; os="$(uname -s)"; arch="$(uname -m)"
  case "$os" in
    Darwin) printf 'macos-universal' ;;
    Linux)
      case "$arch" in
        x86_64|amd64) printf 'linux-x86_64' ;;
        aarch64|arm64) printf 'linux-aarch64' ;;
        *) die "no pinned build for Linux $arch (x86_64 and aarch64 only)" ;;
      esac ;;
    MINGW*|MSYS*|CYGWIN*) die "this is Windows: run install_edit.ps1 from PowerShell instead" ;;
    *) die "unsupported OS $os" ;;
  esac
}

# vget <app> <field> [platform]: read one value from versions.json (node is a requirement of the skill itself).
vget() {
  command -v node >/dev/null 2>&1 || die "node not found. Install Node.js 22 or newer (the doctor script prints how)."
  node -e '
const [, file, app, field, plat] = process.argv;
const j = JSON.parse(require("fs").readFileSync(file, "utf8"));
const a = j.apps[app]; if (!a) process.exit(3);
const s = (a.assets || {})[plat] || {};
const m = { name: a.name, version: a.version, cli: a.cli, tag: a.tag, file: s.file, sha: s.sha256, bytes: s.bytes,
            fingerprint: j.signing.fingerprint, source: j.source };
if (m[field] === undefined) process.exit(4);
console.log(m[field]);' "$PACK/versions.json" "$1" "$2" "${3:-}"
}

mb() { awk -v b="$1" 'BEGIN { printf "%.1f", b / 1048576 }'; }
size_mb() { if [[ -e "$1" ]]; then du -sk "$1" | awk '{printf "%d", $1/1024}'; else echo 0; fi; }
sha_of() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'; else sha256sum "$1" | awk '{print $1}'; fi; }
rel_cli() { # path of the CLI inside the app folder, per platform
  case "$2" in linux-*) printf 'bin/%s-cli' "$1" ;; *) printf '%s-cli' "$1" ;; esac
}

fetch() { # fetch <url> <out>
  command -v curl >/dev/null 2>&1 || die "curl not found. Install curl and run this again."
  local quiet="-sS"; [[ -t 2 ]] && quiet="--progress-bar"
  curl -fL --retry 3 --retry-delay 2 $quiet -o "$2" "$1" || die "download failed: $1"
}

verify_hash() { # verify_hash <file> <asset> <sums> <pinned>
  local listed actual
  listed="$(awk -v f="$2" '$2 == f {print $1}' "$3")"
  [[ -n "$listed" ]] || die "$2 is not listed in the release's SHA256SUMS.txt"
  [[ "$listed" == "$4" ]] || die "SHA-256 in the release ($listed) differs from the one pinned in versions.json ($4). Refusing to install."
  actual="$(sha_of "$1")"
  [[ "$actual" == "$4" ]] || die "SHA-256 mismatch for $2: got $actual, expected $4."
  say "  sha-256: OK ($2)"
}

verify_signature() { # verify_signature <dir> <wanted primary-key fingerprint>
  local dir="$1" want="$2" gh status
  if ! command -v gpg >/dev/null 2>&1; then
    say "  signature: SKIPPED (gpg not installed; the SHA-256 checks above still ran. Install gnupg to check the release signature too)"
    return 0
  fi
  gh="$(mktemp -d)"; chmod 700 "$gh"
  # No agent is needed to check a signature; a failed import shows up as a failed verification below.
  GNUPGHOME="$gh" gpg --batch --quiet --no-autostart --import "$dir/release-signing-key.asc" >/dev/null 2>&1 || true
  status="$(GNUPGHOME="$gh" gpg --batch --no-autostart --status-fd 1 --verify "$dir/SHA256SUMS.txt.asc" "$dir/SHA256SUMS.txt" 2>/dev/null || true)"
  rm -rf "${gh:?}"
  if grep '^\[GNUPG:\] VALIDSIG ' <<<"$status" | awk '{print $NF}' | grep -qx "$want"; then
    say "  signature: OK (SHA256SUMS.txt signed by key ${want:0:8}...${want: -8})"
  else
    die "the signature on SHA256SUMS.txt did not verify against the pinned key $want. Nothing was installed."
  fi
}

unpack() { # unpack <archive> <dest>
  mkdir -p "$2"
  case "$1" in
    *.zip)
      if command -v unzip >/dev/null 2>&1; then unzip -q "$1" -d "$2"
      elif command -v bsdtar >/dev/null 2>&1; then bsdtar -xf "$1" -C "$2"
      else die "unzip not found. Install it with your package manager and run this again."; fi ;;
    *.tar.gz) tar -xzf "$1" -C "$2" ;;
    *) die "do not know how to unpack $1" ;;
  esac
}

strip_quarantine() { # macOS only, and only when the flag is present (curl does not set it)
  [[ "$(uname -s)" == "Darwin" ]] || return 0
  if xattr -p com.apple.quarantine "$1" >/dev/null 2>&1; then
    xattr -dr com.apple.quarantine "$(dirname "$1")" 2>/dev/null || true
    say "  macOS: removed the download quarantine flag from $(basename "$1")"
  else
    say "  macOS: no quarantine flag on $(basename "$1"), nothing to remove"
  fi
}

manifest_add() { # manifest_add <relative path>: remember what this installer created
  touch "$MANIFEST"
  grep -qxF "$1" "$MANIFEST" || printf '%s\n' "$1" >> "$MANIFEST"
}

in_manifest() { [[ -f "$MANIFEST" ]] && grep -qxF "$1" "$MANIFEST"; }

claim() { # claim <relative path>: before writing it, move aside anything there this installer did not create
  local rel="$1" aside
  if [[ -e "$HOME_DIR/$rel" || -L "$HOME_DIR/$rel" ]] && ! in_manifest "$rel"; then
    aside="$HOME_DIR/$rel.backup-$(date +%Y%m%d-%H%M%S)"
    mv "$HOME_DIR/$rel" "$aside"
    say "  kept your existing $rel at $aside (it was not created by this installer)"
  fi
}

write_launcher() { # write_launcher <cli name> <relative cli path>; relative, so the folder can move
  mkdir -p "$HOME_DIR/bin"
  claim "bin/$1"
  cat > "$HOME_DIR/bin/$1" <<LAUNCH
#!/usr/bin/env bash
# brief2mp4 edit pack launcher. Paths are relative to this file, so the folder can move.
SELF="\${BASH_SOURCE[0]}"
while [ -L "\$SELF" ]; do T="\$(readlink "\$SELF")"; case "\$T" in /*) SELF="\$T" ;; *) SELF="\$(dirname "\$SELF")/\$T" ;; esac; done
HERE="\$(cd "\$(dirname "\$SELF")/.." && pwd)"
exec "\$HERE/${1%-cli}/$2" "\$@"
LAUNCH
  chmod +x "$HOME_DIR/bin/$1"
  manifest_add "bin/$1"
}

copy_support_files() { # everything the installed pack needs, so it never reads from the clone
  claim "versions.json"; claim "recipes"
  cp "$PACK/versions.json" "$HOME_DIR/versions.json"
  rm -rf "${HOME_DIR:?}/recipes"; mkdir -p "$HOME_DIR/recipes"
  cp "$PACK"/recipes/* "$HOME_DIR/recipes/"
  chmod +x "$HOME_DIR"/recipes/*.sh
  manifest_add "versions.json"; manifest_add "recipes"
}

install_app() { # install_app <app> <platform>
  local app="$1" plat="$2" name ver file sha bytes tag url dest cli top
  name="$(vget "$app" name)"; ver="$(vget "$app" version)"; tag="$(vget "$app" tag)"
  file="$(vget "$app" file "$plat")" || die "$name $ver has no build for $plat"
  sha="$(vget "$app" sha "$plat")"; bytes="$(vget "$app" bytes "$plat")"
  url="$(vget "$app" source)/$name/releases/download/$tag"
  dest="$HOME_DIR/$name"; cli="$dest/$(rel_cli "$name" "$plat")"
  if [[ "$DRY" == 1 ]]; then say "$app: $name $ver ($plat) would download $file, $(mb "$bytes") MB, from $url/$file"; return; fi
  if [[ -x "$cli" && "$(cat "$dest/.b2m-version" 2>/dev/null || true)" == "$ver" ]]; then
    say "$app: $name $ver already installed ($(size_mb "$dest") MB at $dest)"
    write_launcher "$name-cli" "$(rel_cli "$name" "$plat")"; manifest_add "$name"; return
  fi
  say "$app: downloading $name $ver ($(mb "$bytes") MB) for $plat"
  fetch "$url/$file" "$STAGE/$file"
  for f in SHA256SUMS.txt SHA256SUMS.txt.asc release-signing-key.asc; do fetch "$url/$f" "$STAGE/$f"; done
  verify_hash "$STAGE/$file" "$file" "$STAGE/SHA256SUMS.txt" "$sha"
  verify_signature "$STAGE" "$(vget "$app" fingerprint)"
  unpack "$STAGE/$file" "$STAGE/x"
  local tops; tops="$(find "$STAGE/x" -mindepth 1 -maxdepth 1 -type d | grep -v '/__MACOSX$' || true)"
  [[ "$(printf '%s\n' "$tops" | grep -c .)" == 1 ]] || die "$file should hold exactly one top-level folder; found: $(printf '%s ' $tops)"
  top="$tops"
  claim "$name"
  rm -rf "${dest:?}.new" "${dest:?}.old"; mv "$top" "$dest.new"
  # Keep the previous version until the new one proves it runs, so a failed upgrade loses nothing.
  if [[ -d "$dest" ]]; then mv "$dest" "$dest.old"; fi
  mv "$dest.new" "$dest"
  chmod +x "$cli" 2>/dev/null || true
  strip_quarantine "$cli"
  if ! "$cli" --version >/dev/null 2>&1; then
    rm -rf "${dest:?}"; [[ -d "$dest.old" ]] && mv "$dest.old" "$dest"
    die "$cli was installed but does not run, so the previous version (if any) was kept. Try: $cli --version"
  fi
  rm -rf "${dest:?}.old"
  printf '%s\n' "$ver" > "$dest/.b2m-version"
  write_launcher "$name-cli" "$(rel_cli "$name" "$plat")"; manifest_add "$name"
  say "$app: done, $("$cli" --version | head -1), $(size_mb "$dest") MB on disk"
}

safe_rel() { [[ "$1" =~ ^[A-Za-z0-9._][A-Za-z0-9._/-]*$ && "$1" != *..* ]]; }

uninstall() {
  [[ -f "$MANIFEST" ]] || { say "nothing to remove: $HOME_DIR has no edit-pack manifest (this installer created nothing there)"; return 0; }
  local keep="" rel app freed=0 wanted=" "
  if [[ "$EXPLICIT" == 1 ]]; then
    for app in ${COMPONENTS//,/ }; do wanted+="$(vget "$app" name) $(vget "$app" cli) "; done
  fi
  while IFS= read -r rel; do
    [[ -n "$rel" ]] || continue
    safe_rel "$rel" || { say "skipping unsafe manifest entry: $rel"; keep+="$rel"$'\n'; continue; }
    if [[ "$EXPLICIT" == 1 && "$wanted" != *" ${rel#bin/} "* ]]; then keep+="$rel"$'\n'; continue; fi
    if [[ -e "$HOME_DIR/$rel" ]]; then
      freed=$((freed + $(size_mb "$HOME_DIR/$rel"))); rm -rf "${HOME_DIR:?}/$rel"; say "removed $HOME_DIR/$rel"
    fi
  done < "$MANIFEST"
  if [[ "$EXPLICIT" == 1 && -n "$keep" ]] && ! grep -vxE 'versions\.json|recipes|\.components' <<<"${keep%$'\n'}" >/dev/null; then
    # The last app is gone: take the shared files this installer made too.
    while IFS= read -r rel; do
      if [[ -e "$HOME_DIR/$rel" ]]; then rm -rf "${HOME_DIR:?}/$rel"; say "removed $HOME_DIR/$rel"; fi
    done <<<"${keep%$'\n'}"
    keep=""
  fi
  if [[ -n "$keep" ]]; then
    printf '%s' "$keep" > "$MANIFEST"
    if [[ "$EXPLICIT" == 1 && -f "$HOME_DIR/.components" ]]; then
      grep -vxF -f <(printf '%s\n' ${COMPONENTS//,/ }) "$HOME_DIR/.components" > "$HOME_DIR/.components.tmp" || true
      mv "$HOME_DIR/.components.tmp" "$HOME_DIR/.components"
    fi
  else
    rm -f "${MANIFEST:?}" "${HOME_DIR:?}/.components"
    rmdir "${HOME_DIR:?}/bin" 2>/dev/null || true
    rmdir "${HOME_DIR:?}" 2>/dev/null || true
  fi
  say "uninstall done, about $freed MB freed. Anything else in $HOME_DIR was not created by this installer and was left alone."
}

record_components() {
  touch "$HOME_DIR/.components"
  { cat "$HOME_DIR/.components"; printf '%s\n' ${COMPONENTS//,/ }; } | sort -u > "$HOME_DIR/.components.tmp"
  mv "$HOME_DIR/.components.tmp" "$HOME_DIR/.components"
  manifest_add ".components"
}

cleanup() { if [[ -n "$STAGE" && "$STAGE" == "$HOME_DIR"/.stage-* ]]; then rm -rf "${STAGE:?}"; fi; return 0; }

main() {
  if [[ "$UNINSTALL" == 1 ]]; then uninstall; return 0; fi
  local plat app; plat="$(platform_key)"
  if [[ "$DRY" == 0 ]]; then mkdir -p "$HOME_DIR"; STAGE="$HOME_DIR/.stage-$$"; mkdir -p "$STAGE"; trap cleanup EXIT; fi
  say "brief2mp4 edit pack: ArtCraft apps by storytold (MIT or Apache-2.0), alpha software, versions pinned in versions.json"
  for app in ${COMPONENTS//,/ }; do install_app "$app" "$plat"; done
  if [[ "$DRY" == 1 ]]; then return 0; fi
  copy_support_files; record_components; cleanup
  say "installed components: $(paste -sd, "$HOME_DIR/.components")   total on disk: $(size_mb "$HOME_DIR") MB in $HOME_DIR"
  say "launchers are in $HOME_DIR/bin and recipes in $HOME_DIR/recipes. To type the launchers anywhere, add this line to your shell profile (this script does not):"
  say "  export PATH=\"$HOME_DIR/bin:\$PATH\""
  say "to remove everything this installer created: bash install_edit.sh --uninstall"
}

main

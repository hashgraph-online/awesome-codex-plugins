#!/usr/bin/env bash
# edit-deck.sh — change an existing .pptx in place: text, fonts, slide removal.
#
# Editing a deck you did not author is a surgical job. This script touches only
# the text nodes, typeface attributes, and parts you name, and leaves every other
# byte of the package alone, so the template's layouts, masters, images, notes,
# and custom XML survive. It never re-designs the deck.
#
# Needs bash 3.2+, jq, unzip, zip, and perl from the base system.
set -uo pipefail

ED_USAGE='Usage: bash edit-deck.sh --file <in.pptx> --out <out.pptx> [options]
       [--replace "old=>new"]...   replace literal text inside runs (repeatable)
       [--set-font <name>]         rewrite every latin+eastAsian typeface
       [--drop-slide <n>]...       remove slide n (1-based, repeatable)
       [--allow-miss]              success even when a --replace matched nothing

Inspect the deck first: --replace matches the text of one run, and a phrase
split across runs is reported as a miss rather than silently mangled.

Exit codes: 0 written; 1 written but a replacement matched nothing; 2 usage or
package error; 3 write failure.'

ed_die() { # <code> <message>
  jq -cn --arg code "$1" --arg message "$2" '{status: "error", code: $code, message: $message}'
  exit 2
}

# Literal text replacement that respects the three encodings that appear inside
# <a:t>…</a:t>: XML entities, and the split-run case the caller is warned about.
# perl handles the decode/replace/re-encode cycle exactly; awk does not.
ed_replace() { # <file> <search> <replacement> ; prints hit count
  ED_SEARCH=$2 ED_REPL=$3 perl -i -e '
    use strict; use warnings;
    my $s = $ENV{ED_SEARCH};
    my $r = $ENV{ED_REPL};
    my $hits = 0;
    local $/;
    my $doc = <>;
    # Only text nodes: a run is <a:t>…</a:t> with no child elements.
    $doc =~ s{(<a:t>)(.*?)(</a:t>)}{
      my ($o, $t, $c) = ($1, $2, $3);
      my $dec = $t;
      $dec =~ s/&lt;/</g; $dec =~ s/&gt;/>/g;
      $dec =~ s/&quot;/"/g; $dec =~ s/&apos;/'"'"'/g; $dec =~ s/&amp;/&/g;
      my $n = () = $dec =~ /\Q$s\E/g;
      if ($n) {
        $hits += $n;
        $dec =~ s/\Q$s\E/$r/g;
        $dec =~ s/&/&amp;/g; $dec =~ s/</&lt;/g;
        $dec =~ s/>/&gt;/g; $dec =~ s/"/&quot;/g;
      }
      $o . $dec . $c;
    }gse;
    print $doc;
    print STDERR "HITS $hits\n";
  ' "$1" 2>"$ED_TMP/hits"
  sed -n 's/^HITS //p' "$ED_TMP/hits" | tail -n 1 | tr -d '\r' 
}

ed_set_font() { # <file> <latin> <eastAsian>
  ED_LATIN=$2 ED_EA=$3 perl -i -pe '
    my $l = $ENV{ED_LATIN};
    my $e = $ENV{ED_EA};
    s{(<a:latin typeface=")[^"]*(")}{$1$l$2}g if length $l;
    s{(<a:ea typeface=")[^"]*(")}{$1$e$2}g if length $e;
  ' "$1"
}

# Removing a slide means removing five things: the slide part, its relationship
# part, the notes part and its relationships, the presentation relationship, the
# sldId entry, and the content-type override. Anything left behind makes
# PowerPoint offer to repair the file.
ed_drop_slide() { # <unpacked dir> <n>
  local root=$1 n=$2 rid
  rid=$(perl -0777 -ne "
    my \$i = $((n - 1));
    my @m = /<p:sldId [^>]*r:id=\"([^\"]+)\"/g;
    print \$m[\$i] // '';
  " "$root/ppt/presentation.xml")

  rm -f -- "$root/ppt/slides/slide$n.xml" \
           "$root/ppt/slides/_rels/slide$n.xml.rels" \
           "$root/ppt/notesSlides/notesSlide$n.xml" \
           "$root/ppt/notesSlides/_rels/notesSlide$n.xml.rels" \
           "$root/ppt/charts/chart$n.xml" \
           "$root/ppt/charts/_rels/chart$n.xml.rels"

  ED_RID=$rid perl -0777 -i -e '
    my $rid = $ENV{ED_RID};
    my $doc = <>;
    if (length $rid) {
      $doc =~ s{<p:sldId [^>]*r:id="\Q$rid\E"[^>]*/>}{}g;
      $doc =~ s{<Relationship [^>]*Id="\Q$rid\E"[^>]*/>}{}g;
    }
    print $doc;
  ' "$root/ppt/presentation.xml"

  perl -i -pe 's{<Override PartName="/ppt/slides/slide'"$n"'\.xml"[^>]*/>}{}g;
                    s{<Override PartName="/ppt/notesSlides/notesSlide'"$n"'\.xml"[^>]*/>}{}g;
                    s{<Override PartName="/ppt/charts/chart'"$n"'\.xml"[^>]*/>}{}g' \
    "$root/[Content_Types].xml"
}

ed_main() {
  local file='' out='' allow_miss=0 replaces='' latin='' ea='' drops=''
  while [ $# -gt 0 ]; do
    case $1 in
      --file) file=${2-}; shift 2 || shift ;;
      --out) out=${2-}; shift 2 || shift ;;
      --replace) replaces="$replaces${2-}"$'\n'; shift 2 || shift ;;
      --set-font) latin=${2-}; ea=${2-}; shift 2 || shift ;;
      --set-font-ea) ea=${2-}; shift 2 || shift ;;
      --drop-slide) drops="$drops${2-} "; shift 2 || shift ;;
      --allow-miss) allow_miss=1; shift ;;
      -h|--help) printf '%s\n' "$ED_USAGE"; exit 0 ;;
      *) printf 'unknown argument: %s\n%s\n' "$1" "$ED_USAGE" >&2; exit 2 ;;
    esac
  done
  [ -n "$file" ] && [ -n "$out" ] || { printf '%s\n' "$ED_USAGE" >&2; exit 2; }
  for c in jq unzip zip perl; do
    command -v "$c" >/dev/null 2>&1 || ed_die "${c}_MISSING" "$c is required"
  done
  [ -f "$file" ] || ed_die FILE_MISSING "not a file: $file"
  [ -n "$replaces" ] || [ -n "$latin" ] || [ -n "$drops" ] \
    || ed_die NOTHING_TO_DO 'nothing to do: pass --replace, --set-font, or --drop-slide'

  ED_TMP=$(mktemp -d "${TMPDIR:-/tmp}/hyper-pptx-edit.XXXXXX") || ed_die TMP_FAILED 'cannot create a temporary directory'
  trap 'rm -rf "$ED_TMP"' EXIT
  unzip -o -q "$file" -d "$ED_TMP/x" 2>/dev/null || ed_die NOT_A_PPTX "cannot unpack: $file"
  [ -f "$ED_TMP/x/ppt/presentation.xml" ] || ed_die NOT_A_PPTX "package has no ppt/presentation.xml: $file"

  local total=0 missed='' pair search repl hits f remaining
  remaining=$replaces
  while [ -n "$remaining" ]; do
    pair=${remaining%%$'\n'*}
    if [ "$pair" = "$remaining" ]; then remaining=''; else remaining=${remaining#*$'\n'}; fi
    [ -n "$pair" ] || continue
    case $pair in
      *'=>'*) ;;
      *) ed_die BAD_REPLACE "a --replace value needs \"old=>new\": $pair" ;;
    esac
    search=${pair%%=>*}
    repl=${pair#*=>}
    [ -n "$search" ] || ed_die BAD_REPLACE 'empty search in --replace'
    hits=0
    for f in "$ED_TMP/x/ppt/slides/"slide*.xml; do
      [ -f "$f" ] || continue
      local h
      h=$(ed_replace "$f" "$search" "$repl")
      case $h in ''|*[!0-9]*) h=0 ;; esac
      hits=$((hits + h))
    done
    if [ "$hits" -eq 0 ]; then
      missed="$missed$search"$'\n'
    else
      total=$((total + hits))
    fi
  done

  if [ -n "$latin" ]; then
    for f in "$ED_TMP/x/ppt/slides/"slide*.xml \
             "$ED_TMP/x/ppt/slideLayouts/"slideLayout*.xml \
             "$ED_TMP/x/ppt/slideMasters/"slideMaster*.xml \
             "$ED_TMP/x/ppt/notesMasters/"notesMaster*.xml \
             "$ED_TMP/x/ppt/theme/"theme*.xml; do
      [ -f "$f" ] || continue
      ed_set_font "$f" "$latin" "$ea"
    done
  fi

  local dropped='[]' count n
  if [ -n "$drops" ]; then
    count=$(ls "$ED_TMP/x/ppt/slides" 2>/dev/null | grep -cE '^slide[0-9]+\.xml$')
    for n in $drops; do
      case $n in ''|*[!0-9]*) ed_die BAD_SLIDE "--drop-slide needs a number: $n" ;; esac
      [ "$n" -ge 1 ] && [ "$n" -le "$count" ] || ed_die BAD_SLIDE "--drop-slide $n is outside 1..$count"
    done
    # Highest first, so a positional lookup is never taken against a list the
    # earlier removals already shortened.
    for n in $(printf '%s\n' $drops | sort -rn); do
      ed_drop_slide "$ED_TMP/x" "$n"
      dropped=$(printf '%s' "$dropped" | jq -c --argjson n "$n" '. + [$n]')
    done
  fi

  local out_abs
  case $out in /*) out_abs=$out ;; *) out_abs="$(pwd)/$out" ;; esac
  rm -f -- "$out_abs"
  ( cd "$ED_TMP/x" && find . -type f -exec touch -t 198001010000 {} + && zip -X -q -r "$out_abs" . ) \
    || ed_die ZIP_FAILED "cannot write $out_abs"

  if command -v xmllint >/dev/null 2>&1; then
    local bad
    bad=$(find "$ED_TMP/x" \( -name '*.xml' -o -name '*.rels' \) -print0 \
      | xargs -0 -n1 xmllint --noout 2>&1 | head -n 1)
    [ -z "$bad" ] || ed_die XML_INVALID "the edited package is not well-formed: $bad"
  fi

  local status=ok
  [ -z "$missed" ] || [ "$allow_miss" -eq 1 ] || status=partial
  jq -cn --arg status "$status" --arg out "$out_abs" \
    --argjson replaced "$total" --argjson dropped "$dropped" --arg missed "$missed" \
    '{status: $status, out: $out, replacements: $replaced, droppedSlides: $dropped,
      missed: ([$missed | split("\n")[] | select(. != "")])}'
  [ "$status" = "ok" ] || exit 1
  exit 0
}

ed_main "$@"

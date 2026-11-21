#!/usr/bin/env sh
set -eu

ROOT=".wingman/memory"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      shift
      if [ "$#" -eq 0 ]; then
        echo "memory-stats: --root requires a path" >&2
        exit 2
      fi
      ROOT="$1"
      ;;
    -h|--help)
      echo "Usage: memory-stats.sh [--root .wingman/memory]"
      exit 0
      ;;
    *)
      echo "memory-stats: unknown argument: $1" >&2
      exit 2
      ;;
  esac
  shift
done

file_lines() {
  file="$1"
  if [ -f "$file" ]; then
    wc -l < "$file" | tr -d ' '
  else
    echo 0
  fi
}

file_chars() {
  file="$1"
  if [ -f "$file" ]; then
    wc -c < "$file" | tr -d ' '
  else
    echo 0
  fi
}

estimated_tokens() {
  chars="$1"
  echo $(( (chars + 3) / 4 ))
}

pressure_for() {
  name="$1"
  lines="$2"
  tokens="$3"

  if [ "$name" = "context.md" ]; then
    if [ "$lines" -gt 450 ] || [ "$tokens" -gt 6000 ]; then
      echo "hard"
    elif [ "$lines" -gt 200 ] || [ "$tokens" -gt 3000 ]; then
      echo "soft"
    else
      echo "ok"
    fi
    return
  fi

  if [ "$name" = "brief.md" ]; then
    if [ "$lines" -gt 300 ] || [ "$tokens" -gt 4500 ]; then
      echo "hard"
    elif [ "$lines" -gt 150 ] || [ "$tokens" -gt 2200 ]; then
      echo "soft"
    else
      echo "ok"
    fi
    return
  fi

  echo "unknown"
}

print_headings() {
  file="$1"
  if [ ! -f "$file" ]; then
    echo "    none"
    return
  fi

  headings=$(grep -E '^#{1,6}[[:space:]]+[^[:space:]]' "$file" 2>/dev/null | sed 's/^#*[[:space:]]*/    - /' || true)
  if [ -n "$headings" ]; then
    printf '%s\n' "$headings"
  else
    echo "    none"
  fi
}

print_file_stats() {
  name="$1"
  file="$ROOT/$name"

  echo "$name"
  if [ ! -f "$file" ]; then
    echo "  exists: no"
    echo "  lines: 0"
    echo "  chars: 0"
    echo "  estimated_tokens: 0"
    echo "  pressure: missing"
    echo "  headings:"
    echo "    none"
    return
  fi

  lines=$(file_lines "$file")
  chars=$(file_chars "$file")
  tokens=$(estimated_tokens "$chars")

  echo "  exists: yes"
  echo "  lines: $lines"
  echo "  chars: $chars"
  echo "  estimated_tokens: $tokens"
  echo "  pressure: $(pressure_for "$name" "$lines" "$tokens")"
  echo "  headings:"
  print_headings "$file"
}

if [ ! -d "$ROOT" ]; then
  state="disabled"
elif [ -f "$ROOT/brief.md" ] && [ -f "$ROOT/context.md" ]; then
  state="enabled"
else
  state="partial"
fi

echo "Memory state: $state"
echo "Root: $ROOT"
echo
print_file_stats "brief.md"
echo
print_file_stats "context.md"

#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/../../.." && pwd)"
collector="$plugin_root/mcp/yandex-wordstat/scripts/wordstat_cloud_gateway_collect.py"

case "${1:-help}" in
  where)
    echo "collector=$collector"
    echo "preflight=$script_dir/wordstat_preflight.sh"
    ;;
  preflight)
    shift
    exec "$script_dir/wordstat_preflight.sh" "$@"
    ;;
  collect-wave)
    shift
    exec python3 "$collector" "$@"
    ;;
  help|-h|--help)
    echo "wordstat_tool.sh where | preflight CONFIG | collect-wave --masks-file FILE --output-dir DIR --config CONFIG"
    ;;
  *)
    echo "Неизвестная команда: $1" >&2
    exit 2
    ;;
esac

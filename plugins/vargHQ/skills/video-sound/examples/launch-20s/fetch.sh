#!/bin/sh
# Download the generated voice lines, music beds and effects used by cues.json (made on varg, 2026-11-03).
set -e
cd "$(dirname "$0")"
B=https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013
mkdir -p vo music sfx
get() { curl -sfL -A "Mozilla/5.0" -o "$2" "$B/$1.mp3"; }
get file_b61f4216e249 vo/L01.mp3
get file_6d4ee5788d4b vo/L02.mp3
get file_e3118bc6b3b7 vo/L03.mp3
get file_c2bd18f70b8f music/bed_detailed_2.mp3
get file_55b9b7605a3c music/bed_vague.mp3
get file_19d5b9e8df66 sfx/room.mp3
get file_c998f2a5e267 sfx/click2.mp3
get file_3b883eef6023 sfx/whoosh.mp3
get file_6206c6d3c781 sfx/impact.mp3
echo "fetched; now: python3 ../../scripts/sound.py mix cues.json -o mix.wav"

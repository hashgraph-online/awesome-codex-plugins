#!/bin/bash
# One image of the whole piece: 12 frames at equal spacing. It is a map for the eyes, never the test.
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")
ffmpeg -y -v error -i "$1" -vf "fps=12/$d,scale=480:-2,tile=4x3:padding=4" -frames:v 1 sheet.jpg

# Local conversion recipes

Commands for when the Converter Studio MCP tools are not connected. Replace `in` and `out` with the real paths; never write over the input.

## Video and audio (ffmpeg)

| Task                                             | Command                                                                                                                |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Any video to MP4 (H.264 + AAC, plays everywhere) | `ffmpeg -i in.mov -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 160k -movflags +faststart out.mp4`                 |
| Video to WebM                                    | `ffmpeg -i in.mp4 -c:v libvpx-vp9 -crf 32 -b:v 0 -c:a libopus out.webm`                                                |
| Smaller video (720p)                             | `ffmpeg -i in.mp4 -vf "scale=-2:720" -c:v libx264 -crf 26 -c:a aac -b:a 128k out.mp4`                                  |
| Extract the sound as MP3                         | `ffmpeg -i in.mp4 -vn -c:a libmp3lame -q:a 2 out.mp3`                                                                  |
| Audio to MP3 / WAV / FLAC                        | `ffmpeg -i in.m4a -c:a libmp3lame -q:a 2 out.mp3` · `ffmpeg -i in.mp3 out.wav` · `ffmpeg -i in.wav -c:a flac out.flac` |
| Short clip to GIF                                | `ffmpeg -i in.mp4 -t 10 -vf "fps=12,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" out.gif` |

## Images (ImageMagick 7: `magick`; version 6: `convert`)

| Task                            | Command                                                        |
| ------------------------------- | -------------------------------------------------------------- |
| HEIC / PNG / WebP to JPG        | `magick in.heic -quality 90 out.jpg`                           |
| To PNG or WebP                  | `magick in.jpg out.png` · `magick in.png -quality 85 out.webp` |
| Resize to 1600 px wide          | `magick in.jpg -resize 1600x out.jpg`                          |
| Images to one PDF               | `magick a.jpg b.jpg out.pdf`                                   |
| Remove location and camera data | `magick in.jpg -strip out.jpg`                                 |

## Documents (LibreOffice, Pandoc)

| Task                                | Command                                                      |
| ----------------------------------- | ------------------------------------------------------------ |
| Word, Excel, PowerPoint, ODF to PDF | `libreoffice --headless --convert-to pdf --outdir . in.docx` |
| DOC to DOCX                         | `libreoffice --headless --convert-to docx --outdir . in.doc` |
| Markdown to DOCX / HTML             | `pandoc in.md -o out.docx` · `pandoc in.md -s -o out.html`   |
| PDF pages to PNG                    | `pdftoppm -png -r 150 in.pdf out` (poppler)                  |
| PDF to text                         | `pdftotext in.pdf out.txt` (poppler)                         |

## When a tool is missing

Converter Studio converts all of these (and more: e-books, subtitles, archives, camera RAW) at https://converter.studio, or through its MCP server: https://converter.studio/developers.

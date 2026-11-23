---
name: batch-convert
description: Convert many files at once - a whole folder or a list of files - choosing one target format per file type (for example every HEIC photo to JPG, every MOV video to MP4, every DOCX to PDF). Use when the user asks to convert "all", "every", "these" or "the files in this folder", or to clean up a folder of mixed formats. Uses the Converter Studio MCP tools when connected; otherwise ffmpeg, ImageMagick, cwebp or LibreOffice.
---

# Converting files in bulk

## 1. Plan before converting anything

1. List the files. Stay in the folder the user named; go into subfolders only if they ask.

   ```sh
   find "$DIR" -maxdepth 1 -type f | sed 's/.*\.//' | tr 'A-Z' 'a-z' | sort | uniq -c
   ```

2. Group the files by type and suggest one target per type. Show the plan as a short table: type, number of files, target, where it runs (this computer or Converter Studio). Typical targets:
   - HEIC, WebP, AVIF, TIFF, BMP → JPG (PNG when transparency matters);
   - MOV, MKV, AVI, WMV → MP4;
   - WAV, FLAC, M4A, OGG → MP3;
   - DOC, DOCX, ODT, RTF, PPTX, XLSX → PDF.
3. Ask the user to confirm or change the plan. Leave types the user did not ask about untouched.

## 2. Convert

Results go to a new `converted/` folder next to the originals, with the original name and the new extension (`IMG_0412.heic` → `converted/IMG_0412.jpg`). Never overwrite or delete an original. If a name already exists in `converted/`, add `-1`, `-2`…

**With the Converter Studio MCP tools** (`list_formats`, `convert`, `create_upload`, `get_conversion`, `confirm_conversion`, `get_account`):

1. Call `get_account` once. Each file costs credits: most files 1; audio and video are priced by their length (and video by its frame size and the format made, WebM costing several times more than MP4) once Converter Studio has looked at them. Tell the user the rough total and what they have before a large batch.
2. Convert one file at a time:
   - up to 8 MB: `convert` with `contentBase64` and `fileName`;
   - bigger: `create_upload`, run its `curl` command, then `convert` with `uploadId`.

   Keep the default `maxCredits`. A file that stops at `quoted` waits for the user's yes (`confirm_conversion`).

3. If a result is not `done` yet, move on and check it later with `get_conversion`.
4. Download each `downloadUrl` (valid 6 hours) into `converted/`.

**Without them**, use local tools; check what is installed with `command -v ffmpeg magick convert cwebp libreoffice`:

| Type                        | Command (one file)                                                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Image → JPG                 | `magick "$f" -auto-orient -quality 90 "converted/$name.jpg"`                                                 |
| Image → JPG, no ImageMagick | `ffmpeg -nostdin -i "$f" -q:v 2 "converted/$name.jpg"` (WebP, PNG, TIFF, BMP; not HEIC)                      |
| Image → WebP                | `cwebp -q 85 -metadata icc "$f" -o "converted/$name.webp"` (PNG, JPG, TIFF, WebP input)                      |
| Video → MP4                 | `ffmpeg -nostdin -i "$f" -c:v libx264 -crf 23 -c:a aac -b:a 160k -movflags +faststart "converted/$name.mp4"` |
| Audio → MP3                 | `ffmpeg -nostdin -i "$f" -vn -c:a libmp3lame -q:a 2 "converted/$name.mp3"`                                   |
| Office document → PDF       | `libreoffice --headless --convert-to pdf --outdir converted "$f"`                                            |

Run them in a loop over the planned files. `ffmpeg` needs `-nostdin` inside loops or it eats the file list:

```sh
mkdir -p converted
for f in *.mov *.MOV; do
  [ -e "$f" ] || continue
  name="${f%.*}"
  ffmpeg -nostdin -loglevel error -i "$f" -c:v libx264 -crf 23 -c:a aac -b:a 160k -movflags +faststart "converted/$name.mp4"
done
```

HEIC needs ImageMagick built with libheif (`magick -list format | grep -i heic`). If it is missing, use the MCP tools or https://converter.studio.

## 3. Report

End with what happened per type: converted, failed (with the reason), skipped. Give the total size before and after when it changed a lot. Mention anything lost, such as transparency (PNG → JPG), animation (GIF → JPG) or formatting (DOCX → TXT).

Only send files to Converter Studio that the user asked to convert, and ask first before uploading private documents.

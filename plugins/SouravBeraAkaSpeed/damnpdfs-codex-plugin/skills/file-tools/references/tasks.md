# Practical file tasks

- **Compress PDF:** begin with lossless mode when fidelity matters. Use image recompression/downsampling only when needed. Inspect size and legibility; do not promise that every PDF becomes smaller.
- **Compress images:** Original/JPG/PNG/WebP/AVIF output, quality 1–100, optional max width/height, no enlargement. PNG at 100 preserves full-colour pixels; JPEG/WebP/AVIF remain lossy. JPEG flattens transparency onto white. Animated inputs are refused. Already optimized files may grow; report actual before/after sizes.
- **Edit PDF text:** inspect the correct pages before edits. Replace run indices from the current file, then inspect/export the new artifact. Scanned text requires OCR or annotation; replacing a run is not full word-processor reflow. Show font substitutions and layout warnings.
- **Sign PDF:** place only a user-provided/approved signature, at the requested page/position. This is a visible mark, not a cryptographic certificate or a claim about legal validity. Let the user review the saved document.
- **Office → PDF:** Word and PowerPoint conversion uses the native cloud worker. Unsupported fonts can be substituted. PDFs capture static slide/document appearance; animations, transitions and editable slides are not retained.
- **OCR:** select the appropriate supported language, inspect extracted text, and retain a searchable PDF when requested. Blurry photos and handwriting reduce accuracy; do not silently invent missing text.
- **Background removal:** inspect the alpha channel and visible edges; disclose remaining halos or fine-detail loss. Keep the source image and useful prior results.
- **Merge/organize/split:** preserve user-requested page order and independently check the final page count. Use artifact handles between operations instead of modifying the original in place.
- **Audio:** transcription may mishear words and timestamps; inspect the complete ending and verify the downloadable transcript/PDF. Recordings and real microphone capture are different checks.

Use the installed per-tool schemas for exact option names and bounds. The website's full tool instructions and relevant guides are linked from https://damnpdfs.com/guides.

# Examples — LinkedIn Humanizer

## Example

> **Input:**
> "In today's fast-paced landscape, businesses must fundamentally leverage AI to unlock robust ROI. It's not just about adoption, it's about transformation. As of my last update in January 2024, the trends are clear — here's what I've learned."
>
> **Output (default mode = forensic + strict):**
> "businesses need AI to cut costs. adoption is the easy part. transformation is the actual work. here's what we learned running 35k LinkedIn profiles through our system daily."
>
> **Diff:**
> - FORENSIC: removed "As of my last update in January 2024" disclaimer
> - FORENSIC: removed em dash overuse
> - STRICT: removed "in today's fast-paced landscape" opener
> - STRICT: removed "fundamentally", "leverage", "unlock"
> - STRICT: removed "It's not just X, it's Y" negative parallelism, replaced with paired declaratives
> - PASS 3: added specific number (35k) and named entity (LinkedIn)
> - AESTHETIC was NOT applied — "robust" stays if it was actually there in source

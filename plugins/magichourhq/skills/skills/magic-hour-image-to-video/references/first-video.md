# First video and next edit

Use this flow when the user asks for their first result, is trying the skill, or needs setup recovery. Continue an existing project from its saved state instead of restarting this flow.

## Remove setup decisions

1. Reuse the creation MCP connection and authenticate with `account_retrieve`. If unavailable, use [setup](setup.md). A successful tool listing or ping does not prove authorization. Keep credential entry in the client's secure mechanism.
2. Read the supplied image. If the user wants a demo and has no source, offer the [fictional example portrait](https://raw.githubusercontent.com/magichourhq/skills/main/examples/midnight-remix/portrait.png). Do not substitute it when the user wants their own identity.
3. Reuse the user's brief and spending limit. Ask together only for missing source/intent or spending authorization. Choose model, prompt, aspect and duration yourself when delegated. Verify current tier and the combined image-plus-video cost; an image-only price does not cover the finished video.
4. For an unspecified first short, choose one five-second beat, portrait framing for a vertical destination, and no generated speech or music unless requested. Use supported settings; five seconds is a creative default, not a promised completion time. Respect a requested quality level. Choose a faster model only when the brief values speed and the live schema supports the required result.

## Finish one coherent beat

Set at most three concrete creative acceptance criteria before generating, such as recognizable identity, a visible floating fish separate from the face, and a small reaction without a cut. Also preserve the requested file dimensions, duration and sound. The user's explicit requirements override this starter shape.

If the requested scene differs from the source, edit the still first and inspect it before paying for motion. If the source already matches, animate it directly. Submit once per stage, record the returned project ID immediately, and resume that same project after a wait timeout. A request whose creation response was lost is ambiguous: reconcile it before another paid creation call.

Keep the accepted start frame when repairing motion. Use the original reference when repairing identity. Estimate the next attempt against credits already spent; never spend a repair allowance merely because it exists. If the remaining budget cannot cover a necessary repair, deliver the best available file with the failed criterion and explain the next choice.

## Leave enough state to continue

When project-file access is available, keep a small `creation-notes.md` beside the media, updating existing notes rather than creating competing records. Record only:

- brief and protected details; source and accepted master filenames;
- skill/version, actual model/settings and exact generation prompts;
- image/video project IDs as soon as returned, status, and final charged credits per job;
- start time, file-ready time and review-finished time when observed; mark unavailable timing unknown;
- each required criterion as pass, fail or unverified, with evidence; user acceptance remains unknown until expressed;
- the requested next change and what can be reused.

Keep these records private by default. No credentials, account identifiers, signed URLs or unnecessary personal details. Retrieve expiring links from the project ID. Without filesystem access, retain the minimal continuation record in the current conversation and use the client's supported download surface.

Show the finished video first, with one sentence on any material miss and total credits when known. Offer one relevant continuation, such as “Make a shorter cut from this take” or “Use this character in a new scene.” Do not automatically post media, submit feedback, schedule a follow-up or begin another paid generation.

For a requested trim, crop or exact caption, reuse the downloaded master and an available local editor. Keep the clean original. If no editor exists, explain that dependency before promising a finished cut. Avoid regenerating accepted footage for deterministic edits.

# A /goal prompt for the whole loop

Paste this into an agent that supports goals. It keeps working until the rough cut is ready for a person to hear, then stops: the part after that needs ears.

```text
/goal Edit <take.mp4> using the edit-footage-with-code skill until a rough cut is ready for me to listen to.
Target: <format and length>. Style: <style/format.md, or "write one from these references: ...">.

Done means all of this is true:
- edit/review.md and a written plan exist, and I said yes to the plan (or: no stops, decide yourself and list every decision).
- edit/edl.json has a reason for each large cut.
- edit/acut.mp4 exists, and a transcript made from that file matches the intended words.
- qa/qa.json has no failure except loudness, and you have looked at qa/joins.jpg and qa/contact.jpg yourself.
- You have listed every removed pause right before a number or a punchline, and every note you are unsure of.
- You never overwrote the source and never published anything.

Do not add captions, graphics or music. If the same defect survives 3 passes, stop and tell me what you tried.
```

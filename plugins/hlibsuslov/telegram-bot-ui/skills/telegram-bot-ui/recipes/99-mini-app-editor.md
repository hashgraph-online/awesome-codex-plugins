# 99 — Editor in a Mini App: autosave, conflicts, publish through the bot

Product recipe (no registry row). Verified 2026-11-23. Pattern: `references/mini-apps/screen-patterns.md`
§4 (editor). Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Our staff edit the café's menu board from Telegram, sometimes from two
   devices.” — A dense editor (`dense` style) with autosave; a save made from a stale copy shows the newer
   text and asks to merge instead of overwriting; leaving with unsaved edits asks first; “Publish” arrives as
   a bot message bound to the revision the person saw.
2. **Why these features.** Revisions on the server make a stale save a 409 conflict **[heuristic]**;
   `enableClosingConfirmation` while there is unsaved input **[official]**; publishing confirmed in the chat
   with a callback that carries the revision, so an old button cannot publish newer text **[heuristic]**;
   drafts survive in `CloudStorage` / `DeviceStorage` **[official]**.
3. **Requirements.** 6.2 closing confirmation, 6.9 CloudStorage (9.0 DeviceStorage for larger drafts);
   private chat for the publish confirmation.
4. **Payload.** `examples/payloads/r99-editor.json`: the publish confirmation with
   `callback_data: "pub:menu-board:2"` (success style) and a `web_app` button to keep editing.
5. **Code.** `r90_99_mini_apps.py::r99` (`Drafts.save` with base revisions). App building blocks: `dense`
   style, `textarea.tma-input`, `.tma-field__error` for the conflict notice, `tma.closingConfirmation()`,
   `tma.store()` for the draft.
6. **Sequence and state.**
   ```mermaid
   sequenceDiagram
     participant P as Phone
     participant D as Desktop
     participant S as Server
     P->>S: save(rev 0) → 200 rev 1
     D->>S: save(rev 0) → 409 (rev 1 text returned)
     D->>S: save merged (rev 1) → 200 rev 2
     S->>D: bot: "Publish to the menu board?" [Publish pub:…:2]
   ```
7. **Result.** “Publish to the menu board? Autumn blend: spiced, low acidity. €3.80” [Publish] [Keep
   editing].
8. **Typical mistake, limits, alternative.** Last write wins; autosave on every keystroke without debounce;
   publishing straight from the app without confirmation; no closing confirmation. Alternative for short
   texts: messages with `force_reply` (recipe 03); channel posts: recipe 35 (editorial approval).
9. **Run and verify.** `py -3 examples/python/recipes/r90_99_mini_apps.py r99` (3 self-checks).
10. **Adapt.** Keep: base revisions on every save, conflicts shown with the newer text, publish bound to a
    revision. Replace: the document model. Related: recipes 35 (approval), 39 (correct a published post).

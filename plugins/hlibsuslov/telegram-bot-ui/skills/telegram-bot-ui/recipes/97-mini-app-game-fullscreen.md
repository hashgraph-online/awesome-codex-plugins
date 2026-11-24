# 97 — Fullscreen game or leaderboard, shared to chats

Product recipe (no registry row). Verified 2026-11-23 against Bot API 10.5 and the Mini Apps page.
References: `references/mini-apps/webapp-api.md` (fullscreen, orientation, swipes),
`references/mini-apps/telegram-design-guidelines.md` §6. Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “A latte-art mini game with a weekly leaderboard that people share with
   friends.” — The game opens fullscreen from a challenge link, content stays clear of the notch and
   Telegram's floating controls, the leaderboard shows the user's own row, and “Share score” sends a card
   with a Play button to any chat.
2. **Why these features.** `requestFullscreen` (8.0) with `safeAreaInset` + `contentSafeAreaInset`
   **[official]**; `lockOrientation` only while playing, `disableVerticalSwipes` only while gestures run
   **[official]/[heuristic]**; `savePreparedInlineMessage` → `shareMessage` (8.0) **[API]/[official]**;
   `fullscreenFailed` handled **[official]**; the leaderboard keeps the user's row (L-rules for tables).
3. **Requirements.** 8.0 for fullscreen, orientation, safe areas and `shareMessage`; links in stories need
   Premium for `shareToStory` **[official]**.
4. **Payload.** `examples/payloads/r97-game-fullscreen.json`: `savePreparedInlineMessage` with a Play
   button to `t.me/<bot>/latte_art?startapp=challenge-520&mode=fullscreen`.
5. **Code.** Bot: `r90_99_mini_apps.py::r97`, `bot_side.py` (`link(mode="fullscreen")`, `prepare_share`).
   App building blocks: kit safe-area variables (`--tma-safe-top`, `.tma-page`), `.tma-table` +
   `.tma-rank` + `tr.is-me` (gallery Tables group), MainButton hidden while playing.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> lobby: link mode=fullscreen
     lobby --> playing: Play (lockOrientation, disableVerticalSwipes)
     playing --> result: end (unlock, enable swipes)
     result --> shared: Share score (shareMessage with prepared id)
     result --> leaderboard
   ```
7. **Result.** Shared card: “I scored 520 in Latte Art. Beat me?” [Play].
8. **Typical mistake, limits, alternative.** Content under Telegram's controls in fullscreen; swipes disabled
   for the whole app; an expired prepared id reused (one per share); a looping fullscreen request after
   `UNSUPPORTED`. Alternative: a shared quiz widget in a chat (recipe 53).
9. **Run and verify.** `py -3 examples/python/recipes/r90_99_mini_apps.py r97` · the preview stand in
   `mode=fullscreen` for both platforms (`/?mode=fullscreen&platform=ios`). Evidence: offline contract and
   mock preview; real fullscreen on devices not checked here.
10. **Adapt.** Keep: insets on every edge, gesture locks scoped to play, one prepared message per share.
    Replace: the game. Related: recipes 53 (shared quiz), 98 (share a result).

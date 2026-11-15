# 75 — Migrate from one pack to another without touching handlers

Registry rows: none of its own. Verified 2026-11-15, Bot API 10.4. Background:
`references/emoji-packs.md#migrating-to-another-pack`.

1. **Request and visible result.** “Switch our icons to the new solid set.” — Same screens,
   same labels, actions and styles; only the icon ids change, all from the new family.
2. **Why the new features.** Handlers request slots, not ids, so the pack is configuration.
3. **Requirements.** The new family covers every slot in use, its ids verify with
   `getCustomEmojiStickers`, and `audit_icons.py` passes (one family, static).
4. **Payload.** `examples/payloads/r75-migrate-pack.json`.
5. **Code.** `examples/python/recipes/r75_migrate_pack.py` (`shop_menu`, `run`),
   `tgkit/icons.py` (`resolve_icon_map`, `verify_ids`), `scripts/emoji_packs.py resolve|verify`.
6. **Sequence and state.** resolve new map for the slots in use → coverage = 100 % → verify
   ids → audit → swap the map; otherwise keep the old map and list uncovered slots.
7. **Result.** Mock-up: `[new icon] Cart  [new icon] Search / [new icon] Settings / [new icon] Back`.
8. **Typical mistake, limits, alternative.** Filling a gap with the old family's icon
   (mixed families); switching before verifying; searching handlers for ids. Alternative:
   keep the gap slot label-only on purpose.
9. **Run and verify.** `py -3 examples/python/recipes/r75_migrate_pack.py` ·
   `py -3 scripts/emoji_packs.py verify --map NEW.json` · tests in `tests/test_emoji_icons.py`.
   Evidence: offline contract; synthetic ids.
10. **Adapt.** Keep the map in one file per environment; run `verify` in CI. Related: 70, 71.

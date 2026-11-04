# Subject Line Templates

`EMAIL_SUBJECT_TEMPLATE` supports these placeholders:

- `{date}` — `2026-04-20`
- `{n}` — number of items in the digest
- `{lang}` — recipient language (`zh` / `en` / `ja`)

## Recommended templates

| Language | Template | Renders as |
|----------|----------|-----------|
| en (default) | `MorningAI {date} · {n} updates` | `MorningAI 2026-04-20 · 8 updates` |
| zh | `MorningAI 早报 {date}（{n} 条）` | `MorningAI 早报 2026-04-20（8 条）` |
| ja | `MorningAI {date}・{n}件の注目ニュース` | `MorningAI 2026-04-20・8件の注目ニュース` |
| concise | `MorningAI · {date}` | `MorningAI · 2026-04-20` |

Set in your `.env`:

```env
EMAIL_SUBJECT_TEMPLATE=MorningAI 早报 {date}（{n} 条）
```

## Tips

- Keep subjects under **60 characters** so they don't truncate in inbox previews (especially mobile).
- Avoid spam triggers: no all-caps, no excessive `!!!`, no `$` / `FREE` / `URGENT` etc.
- The `· ` separator (U+00B7) renders better than `|` or `-` across email clients.
- Per-recipient language (from `recipients.json`) re-renders the subject for each recipient — use placeholders that work in all three languages or keep the template language-neutral.

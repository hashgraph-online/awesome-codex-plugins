# post: channel posts and mailings

**When:** post this to our channel, a digest, a mailing, editorial approval, edit or cross-post
a published post.

## Read

- What the post looks like, per type; buttons and emoji in channels; comments:
  `references/channel-post-design.md`.
- The pipeline: `references/publishing-pipeline.md` §1-7 (content model → render → validate →
  preview → approve → publish once → edit, pin, copy) and §12 (operating checklist).
- Many recipients, rate limits, per-recipient failures: `references/channels-and-broadcasting.md`.
- Emoji density and accessibility in long texts: `references/emoji-in-posts.md`; reports and
  tables in posts: `references/data-views.md`.

## Steps

1. Write the post as content (Markdown or Post JSON), never as raw HTML.
2. `tgui.py post validate <file> --context channel`, then `tgui.py post preview <file>`.
3. Show the exact post to the approver; publish only after an approval bound to that post.
4. `tgui.py post publish <file> --chat-env TG_CHANNEL_ID --token-env TG_BOT_TOKEN --key <id>`
   is a dry run until `--live`; live needs a test bot unless the user named the real channel.
   A timeout is "unknown": reconcile, never resend.
5. Mailings: FanOut with per-recipient results and `retry_after`.

## Without scripts

Check the limits by hand (`references/limits-and-splitting.md`), show the rendered text and the
request JSON, and publish nothing.

## Done

Validated, previewed, approved, published once (or the dry run reported), message ids recorded.

## Next

Edit or pin the published post, or set up the recurring digest.

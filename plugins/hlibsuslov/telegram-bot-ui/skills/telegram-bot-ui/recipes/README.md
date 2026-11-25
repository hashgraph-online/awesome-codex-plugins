# Recipe index

Start by user intent: `python scripts/example_library.py --query "заявки CRM" --json`
(from the skill root; catalog: `use-cases.json`). Read the
[reuse and extension contract](../references/example-library.md) before adding a new example.

## Product journeys R80–R87

Python offline models and private callback demos, with EN/RU copy and captured payloads.
No external CRM, worker, scheduler daemon or production storage is included. TypeScript
ports are planned, not implemented. Run all: `python examples/python/recipes/r80_87_product_journeys.py`.

| Recipe | Distinguishing behavior |
|---|---|
| [80 Lead intake](80-lead-intake.md) | review, consent invalidated by edits, stable submission |
| [81 Event waitlist](81-event-waitlist.md) | capacity, FIFO promotion, staff check-in |
| [82 Personal reminders](82-personal-reminders.md) | time zones, replace job, invalidate leased work |
| [83 File processing](83-file-processing.md) | cancellation blocks late completion |
| [84 Moderation review](84-moderation-review.md) | group/actor/revision-bound decision plan |
| [85 Feedback survey](85-feedback-survey.md) | required answer, optional comment, withdrawal |
| [86 Loyalty points](86-loyalty-points.md) | dedup credits, immutable amounts, no overdraft |
| [87 Service queue](87-service-queue.md) | one position per user, staff call/complete |

## Mini Apps (90-99)

The app side lives in `examples/mini-apps` (kit, coffee app, catalogue, portfolio, gallery, React, server, bot); these recipes run the bot and server side offline (`examples/python/recipes/r90_99_mini_apps.py`). Branch entry: `references/mini-apps/README.md`.

| Recipe | Bot API symbols | Versions |
|---|---|---|
| [90. Bot or Mini App: deciding the surface and building the hybrid](90-mini-app-or-bot.md) | `web_app`, `setChatMenuButton`, `MenuButtonWebApp` | 6.7, 7.8 |
| [91. A minimal Mini App: menu button, startapp, theme, BackButton, MainButton](91-minimal-mini-app.md) | `setChatMenuButton`, `MenuButtonWebApp`, `WebAppInfo`, `web_app` | 6.1, 7.10, 8.0, 9.5 |
| [92. Verify initData on the server and keep a session](92-init-data-session.md) | `answerWebAppQuery`, `web_app_query_id`, `InlineQueryResultArticle` | 6.0, 8.0 |
| [93. Mini App shop: catalogue, product, cart, checkout](93-mini-app-shop.md) | `createInvoiceLink`, `successful_payment`, `LabeledPrice` | 6.1, 10.5 |
| [94. Form and booking in a Mini App, result back to the chat](94-mini-app-form-booking.md) | `web_app_data`, `KeyboardButton`, `remove_keyboard` | 6.0, 6.2, 6.9 |
| [95. Dashboard and portfolio Mini App (dark-fintech style)](95-mini-app-dashboard.md) | `sendMessage`, `InlineKeyboardButton` | 7.10, 8.0 |
| [96. Profile and settings in a Mini App, with permission to message](96-mini-app-profile-settings.md) | `write_access_allowed`, `WriteAccessAllowed`, `setChatMenuButton` | 6.9, 7.0 |
| [97. Fullscreen game or leaderboard, shared to chats](97-mini-app-game-fullscreen.md) | `savePreparedInlineMessage`, `PreparedInlineMessage` | 8.0 |
| [98. Share a result from a Mini App to a chat](98-mini-app-share-result.md) | `savePreparedInlineMessage`, `answerWebAppQuery`, `savePreparedKeyboardButton` | 8.0, 9.6 |
| [99. Editor in a Mini App: autosave, conflicts, publish through the bot](99-mini-app-editor.md) | `callback_data`, `style`, `web_app` | 6.2, 6.9, 9.4 |

## Existing feature and product recipes

Find a recipe by task, API symbol, version or context. Machine-readable: `manifest.json`
(recipes → registry rows, symbols, files) and `registry.json` (every changelog item).
All recipes run offline: `py -3 examples/python/recipes/<file>.py`; TypeScript twins:
`node examples/ts/recipes.ts`, tests `cd examples/ts && npm test`.

## Bot API 10.3-10.5 mechanisms (01-10, mini-recipes)

| Recipe | Typical request | Symbols | Version | Context |
|---|---|---|---|---|
| [01 AI assistant + Stop](01-ai-assistant.md) | "stream the answer, let me stop it" | `sendRichMessageDraft`, `can_stop`, `keep_on_stop`, `stopped_message_generation` | 10.3 | private (+topics) |
| [02 Interactive document](02-interactive-document.md) | "send it as a proper document with a button / attached PDF / answer the quoted line" | `RichMessageButton`, `RichTextButton`, `<tg-button-row>`, `is_compact`, `expandable_blockquote` (`blocks`, 10.5), `tg-document`, `tg://document`, `quote_rich_texts`, `RichTextTonAddress` | 10.3, 10.4, 10.5 | any rich-capable chat |
| [03 Multi-step form](03-multi-step-form.md) | "pick or type", "people double-tap Submit" | `force_reply` (inline/reply markup), `DisabledButton` | 10.3 | private, groups |
| [04 Shared card + personal panel](04-shared-card-personal-panel.md) | "private answer in the group", "don't show my order to everyone" | `EphemeralMessageParameters`, `replace_callback_query_message`, `editEphemeralMessage*` | 10.3, 10.4 | groups (not channel DMs) |
| [05 Private widget](05-private-widget.md) | "one card that updates", "interactive order card" | `sendWidget`, `widget_query`, `answerWidgetQuery`, `editMessageWidgetData`, `Widget` | 10.4 | **private (production)** |
| [06 Shared widget](06-shared-widget.md) | "live poll everywhere" | `sendSharedWidget`, `editSharedWidgetData`, `shared_widget_query`, `InputWidgetMessageContent` | 10.4 | private; forwards/inline/groups **test server** |
| [07 Wallet](07-wallet.md) | "pay in TON in the chat", "link my wallet" | `WidgetQueryType*`, `WidgetQueryWallet`, `TonWalletCard`, `TonWalletTransfer`, `ton_address`, `AreaPosition` | 10.4 | private |
| [08 Multi-topic bot](08-multi-topic-bot.md) | "answers mix between topics", "link to another topic" | `message_thread_id`, `t.me/<bot>/<thread>`, `direct_messages_topic_id` | 10.3, 10.4 | private topics, forum, channel DMs |
| [09 Tracker bot (btc-tracker upgrade)](09-tracker-bot.md) | "one card per transaction", "live price", "our icons look mismatched" | `sendWidget`, `editMessageWidgetData`, `sendSharedWidget`, `cache_time`, `is_compact`, `disabled`, `force_reply`, `icon_custom_emoji_id` | 9.4, 10.3, 10.4 | private (widgets), any (fallback) |
| [10 Bot settings from code](10-bot-settings.md) | "stop clicking BotFather", "topics in a sidebar", "invite our testers", "buttons stopped working on old messages" | `setMySettings`, `BotFullInfo`, `callback_query_mode`, `has_topic_sidebar`, `active_usernames`, `t.me/botinvite`, `WriteAccessAllowed.inviter` | 10.5 | private; settings apply bot-wide |
| [Mini-recipes](mini-recipes.md) | welcome, community joins, gift notes, `getUniqueGift`, `deleteBusinessAccountGift`, share themes, managed bot usernames, verification, paid messages waived, card masking, renames | see table | 10.3, 10.4 | mixed |

## Products, publishing, agents, widgets, premium emoji (20-76)

Whole products (20-29, 60-64; index by product type: `references/use-case-playbooks.md`), channel publishing (30-39, `references/publishing-pipeline.md`), an agent that works through its own bot (40-49, `references/agent-operated-bots.md`), HTML widgets (50-56, `references/widget-patterns.md`) and premium emoji packs (70-76, `references/emoji-packs.md`). Same 10-part format, all offline.

### Product use cases

| Recipe | Typical request | Key symbols | Versions |
|---|---|---|---|
| [20 Shop: catalog → product → cart → checkout with Telegram Stars or a provider invoice](20-shop.md) | "We sell coffee beans. Make a shop bot: browse, add to cart, pay with Stars or by card, and" | `style`, `LabeledPrice`, `need_name`, `answerPreCheckoutQuery`, `error_message` | 9.4, 10.3, 10.4 |
| [21 Support desk: a private chat for the customer, one forum topic per ticket for the team](21-support-desk.md) | "Customers write to our bot. I want every problem in its own thread for the team, with a st" | `force_reply`, `style`, `createForumTopic`, `editForumTopic`, `closeForumTopic` | 9.4, 10.3, 10.4 |
| [22 Appointment booking: service → day → time → confirm, with reminders, reschedule and cancel](22-booking.md) | "A salon takes bookings by phone. Let people book in the bot: pick a service, a day this we" | `style`, `callback_data`, `allowed_updates`, `message`, `callback_query` | 9.4, 9.5, 10.3, 10.4 |
| [23 Onboarding and first run: deep links, language, permissions, empty states, returning users](23-onboarding.md) | "New users open the bot from ads, referral links and product links, see a wall of text and " | `style`, `setMyDescription`, `setMyShortDescription`, `setMyCommands`, `language_code` | 9.4, 10.2, 10.4 |
| [24 Settings and preferences: toggles, back stack, destructive actions with confirm and undo](24-settings.md) | "Our settings are five separate commands. People can't find notifications, Back throws them" | `style`, `callback_data` | 9.4, 10.3, 10.4 |
| [25 Subscription: paywall, one 7-day trial, a Stars subscription, cancel and expiry](25-subscription-paywall.md) | "Part of the bot is for subscribers: ⭐ 150 a month, with a free 7-day trial. People must be" | `createInvoiceLink`, `subscription_period`, `editUserStarSubscription`, `successful_payment`, `style` | 9.4, 10.3, 10.4 |
| [26 Learning bot: course map → lesson → quiz → result → streak → daily reminder](26-learning-bot.md) | "I teach Git basics in a bot. Show a course map, a short lesson with an example, a three-qu" | `disabled`, `style`, `heading`, `buttons`, `has_checkbox` | 9.4, 10.2, 10.3, 10.4 |
| [27 Assistant as a product: modes, streamed answer with Stop, feedback, regenerate, history, files](27-ai-assistant-product.md) | "Make an assistant bot with three modes, a live answer I can stop, thumbs up or down on the" | `disabled`, `style`, `sendRichMessageDraft`, `can_stop`, `keep_on_stop` | 9.4, 10.3, 10.4 |
| [28 Group utility: expense split on one shared card with personal panels](28-group-expense-split.md) | "We travel to Lviv as four people and keep losing track of who paid. A card in the group ch" | `callback_query_id`, `receiver_user_id`, `editEphemeralMessageText`, `disabled`, `style` | 9.4, 10.2, 10.3, 10.4 |
| [29 Community bot: join requests with rules, welcome, roles as visible tags](29-community.md) | "Our food club is a private supergroup. People ask to join through a link; I want them to r" | `chat_join_request`, `user_chat_id`, `can_send_welcome_messages`, `community_chat_joined`, `setChatMemberTag` | 9.5, 10.3, 10.4 |
| [60 Inline mode: share a place card into any chat, then let the chat vote on it](60-inline-mode.md) | "Friends keep asking where to get coffee. Let me type `@placecards_bot coffee` in any chat," | `chosen_inline_result`, `editMessageText`, `inline_message_id`, `style`, `language_code` | 9.4, 10.4 |
| [61 Business-account bot: auto-replies and quick replies on behalf of a bakery](61-business-account.md) | "I run a bakery and answer the same questions all day — opening hours, the menu. Connect th" | `business_connection`, `business_message`, `business_connection_id`, `readBusinessMessage`, `can_reply` | 9.4, 10.3, 10.4 |
| [62 Monitoring and alerts bot: uptime and price watches, mute, quiet hours, daily digest](62-monitoring-alerts.md) | "Tell me when my API gets slow or down, and when BTC drops under my level. Don't wake me at" | `style`, `disable_notification`, `force_reply`, `is_compact`, `callback_data` | 9.4, 10.3, 10.4 |
| [63 Search and long lists: a job board with filters, paging, detail and compare](63-search-and-long-lists.md) | "Our job board has hundreds of vacancies. Let people search by typing, narrow by Remote / J" | `style`, `force_reply`, `is_compact`, `InputRichBlockButtons`, `callback_data` | 9.4, 10.3, 10.4 |
| [64 Delivery tracker: one status card per order, edited in place](64-delivery-tracker.md) | "After a customer orders, show where the parcel is. One message that updates, not ten notif" | `editMessageText`, `force_reply`, `allowed_updates`, `message`, `callback_query` | 10.3, 10.4 |

### Channel publishing

| Recipe | Typical request | Key symbols | Versions |
|---|---|---|---|
| [30 News autoposter from a feed item](30-news-autoposter.md) | "Post every new item from our city news feed to the channel — and never twice." | `link_preview_options`, `url`, `prefer_large_media`, `parse_mode`, `can_post_messages` | 10.4 |
| [31 Long read as one Rich Message](31-long-read-rich-post.md) | "Our quarterly report is 5,000 characters with a table. Today it is 3 messages and a screen" | `is_compact`, `document`, `InputRichBlockButtons`, `sendRichMessage`, `link_preview_options` | 10.1, 10.3, 10.4 |
| [32 Media album post (and paid media)](32-media-album-post.md) | "Post three photos of the winter market with a caption and a ‘Map’ button; and a paid backs" | `sendMediaGroup`, `reply_markup`, `show_caption_above_media`, `has_spoiler`, `sendPaidMedia` | 10.0, 10.4 |
| [33 Poll and quiz posts in a channel](33-poll-quiz-post.md) | "Run a quiz about the report, only for our subscribers from Ukraine and Poland; and a surve" | `members_only`, `country_codes`, `correct_option_ids`, `description`, `close_date` | 10.0, 10.4 |
| [34 Daily digest edited in place and pinned](34-pinned-daily-digest.md) | "Keep one pinned ‘Today in the city’ post and update it during the day instead of posting t" | `is_compact`, `can_edit_messages`, `can_post_messages`, `editMessageText`, `disable_notification` | 10.1, 10.3, 10.4 |
| [35 Editorial approval before publishing](35-editorial-approval.md) | "The bot drafts posts, but an editor must approve each one, fix the text if needed, or reje" | `style`, `force_reply`, `callback_data`, `from` | 9.4, 10.4 |
| [36 Cross-posting to several channels and languages](36-cross-post-variants.md) | "Publish the bike-lane story in our English, Russian and Ukrainian channels, and in a partn" | `copyMessage`, `reply_markup`, `forwardMessage`, `correct_option_ids`, `copyMessages` | 10.4 |
| [37 Broadcast mailing with throttling and per-recipient outcomes](37-broadcast-mailing.md) | "Send the event alert to all 40,000 subscribers of the bot without getting banned, and don'" | `retry_after`, `allow_paid_broadcast` | 10.4 |
| [38 Comment threads and channel direct messages](38-comments-and-direct-messages.md) | "Open every post's comments with a short rules note, remove spam, acknowledge questions; an" | `is_automatic_forward`, `forward_origin`, `is_direct_messages`, `direct_messages_topic_id`, `suggested_post_info` | 9.2, 10.4 |
| [39 Correcting a published post: edit or delete-and-repost](39-correct-published-post.md) | "We posted the wrong time. Fix it — and next time we also need to add a map photo to a post" | `editMessageText`, `editMessageCaption`, `editMessageMedia`, `can_post_messages`, `can_edit_messages` | 10.4 |

### Agent working through its bot

| Recipe | Typical request | Key symbols | Versions |
|---|---|---|---|
| [40 Deploy approval gate](40-deploy-approval-gate.md) | "The agent must not deploy to production until I say so — from my phone." | `style`, `answerCallbackQuery`, `disabled`, `allowed_updates`, `callback_query` | 9.4, 10.3, 10.4 |
| [41 Long build/test run with live status and a final report](41-build-live-status.md) | "My CI agent sends 200 messages per run." | `is_compact` | 10.1, 10.3, 10.4 |
| [42 Nightly job digest](42-nightly-digest.md) | "Tell me every morning how the night jobs went, but don't wake me when everything is green." | `disable_notification` | 10.1, 10.4 |
| [43 Ask the operator and continue](43-ask-and-continue.md) | "When the agent is unsure, it should ask me and keep going if I don't answer." | `force_reply` | 10.3, 10.4 |
| [44 Streamed research answer with Stop](44-streamed-research-stop.md) | "The research agent writes for two minutes and I can't stop it." | `can_stop`, `keep_on_stop`, `allowed_updates`, `stopped_message_generation` | 10.3, 10.4 |
| [45 Multi-job dashboard with private-chat topics](45-multi-job-dashboard-topics.md) | "Three agent jobs run in parallel and their messages are a mess." | `createForumTopic`, `message_thread_id`, `chat_data` | 9.4, 10.4 |
| [46 The agent in a team group: personal replies](46-team-group-personal-replies.md) | "Put the CI agent in our team chat, but don't dump everyone's failures and logs there." | — | 10.3, 10.4 |
| [47 Incident alert with acknowledge and escalate](47-incident-alert.md) | "Page me when checkout breaks; if I don't react in 5 minutes, page the backup." | — | 10.3, 10.4 |
| [48 Coding-agent hooks call the bridge](48-coding-agent-hooks.md) | "Tell me on Telegram when Claude Code or Codex needs me, and let me approve risky commands " | — | 10.4 |
| [49 Intake and security drill](49-intake-security-drill.md) | "Make sure nobody else can steer my agent through its bot." | `allowed_updates`, `stopped_message_generation`, `my_chat_member`, `secret_token` | 10.4 |

### HTML widgets

| Recipe | Typical request | Key symbols | Versions |
|---|---|---|---|
| [50 Monitoring dashboard widget (private chat, production)](50-monitoring-dashboard-widget.md) | "Our on-call bot sends a wall of text every time something changes. I want one health card " | `editMessageWidgetData`, `allowed_updates`, `widget_query` | 10.4 |
| [51 Booking widget: day strip, time slots, confirm (private chat, production)](51-booking-widget.md) | "Clients book haircuts by typing dates back and forth. Give them a picker in the chat." | `allowed_updates`, `widget_query`, `editMessageCaption` | 10.4 |
| [52 Shop: product card → cart → receipt (private chat, production)](52-shop-card-to-checkout.md) | "Our shop bot lists products as text. Make a real product card, a cart and a receipt." | — | 10.4 |
| [53 Quiz with a shared leaderboard (private chats + one shared widget, production)](53-shared-quiz-leaderboard.md) | "Run a weekly quiz in the bot with a leaderboard everyone sees." | `sendSharedWidget`, `is_shared`, `allow_queries`, `widget_id`, `editSharedWidgetData` | 10.4 |
| [54 Long job progress in one card (private chat, production)](54-job-progress-widget.md) | "Exports take minutes and users keep asking ‘is it working?’." | `editMessageWidgetData`, `sendChatAction` | 10.4 |
| [55 Design a new widget from a user's description (describe → widget workflow)](55-design-a-widget.md) | "Let me set a price alert for TON right in the chat, with a slider, in Russian." | `sendWidget` | 10.4 |
| [56 API data browser: a widget as the front end of a REST backend (private chat, production)](56-api-data-browser.md) | "Show our support tickets from the helpdesk API in Telegram: list, open one, assign it or c" | — | 10.4 |

### Premium emoji

| Recipe | Typical request | Key symbols | Versions |
|---|---|---|---|
| [70 Restyle an existing bot from Unicode emoji to one premium pack](70-restyle-to-premium.md) | "Make our bot look premium — same screens, nicer icons." | `icon_custom_emoji_id`, `getStickerSet`, `getCustomEmojiStickers` | 9.4, 10.4 |
| [71 Icons for a new bot from zero (no ids yet, capture path)](71-icons-from-zero.md) | "New bot; we want premium icons but have no ids." | `getCustomEmojiStickers`, `custom_emoji_id` | 9.4, 10.4 |
| [72 Channel post series with premium accents and fallback](72-channel-post-series.md) | "Our channel posts should look as polished as the bot." | `RichTextCustomEmoji`, `alternative_text` | 10.3, 10.4 |
| [73 Mixed eligibility: icons in private chats, Unicode in the channel](73-mixed-eligibility.md) | "Same order update goes to customers, a group, our news channel and business replies." | `business_connection_id` | 9.4, 10.4 |
| [74 Recover after the owner's Premium lapses](74-premium-lapse.md) | "Messages started failing after the owner's Premium expired." | — | 10.4 |
| [75 Migrate from one pack to another without touching handlers](75-migrate-pack.md) | "Switch our icons to the new solid set." | `getCustomEmojiStickers` | 10.4 |
| [76 The bot builds its own custom emoji pack and uses it](76-own-emoji-pack.md) | "Make an emoji pack of our own for the bot's icons, from the PNGs our designer sent." | `createNewStickerSet`, `uploadStickerFile`, `addStickerToSet`, `setCustomEmojiStickerSetThumbnail`, `getStickerSet` | 6.2, 6.6 |

Combining features is normal: a group lunch bot = 04 (personal panel) + 03 (form for the order)
+ 06 (poll in private chats); a support assistant = 01 + 08 + 02 (quote the policy line); a news channel = 30 + 35 (approval) + 72 (accents);
a shop = 20 + 52 (widget card) + 64 (delivery tracker); an agent with an operator = 40 + 41 + 45.

By bot type (monitoring, AI assistant, shop, team utility, support, docs, wallet, games): `references/bot-archetypes.md`.

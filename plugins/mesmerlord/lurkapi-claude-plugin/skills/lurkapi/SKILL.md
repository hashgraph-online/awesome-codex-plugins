---
name: lurkapi
description: Current public data as JSON through LurkAPI, with profiles, posts, comments, transcripts and ads from Facebook, Reddit, YouTube, TikTok, Google, Bluesky, Snapchat, Truth Social, Telegram, X (Twitter), Threads, Instagram, LinkedIn, Link-in-bio and eBay, and any web page. Use it when the user wants live followers, posts, videos, comments, transcripts, ad library results or a web page rather than an answer from memory, or mentions LurkAPI. It maps each question to the endpoint that answers it, with its params and price.
---

# LurkAPI: which call answers what

LurkAPI reads public pages only: no private accounts or messages, no posting, no private people's contact details. Pick the endpoint below, pass the handle, URL or keyword it asks for, and answer from what comes back, not from memory.

For a whole job, use the workflow skill instead: `lurk`, `ad-research`, `video-transcripts`, `reddit-research`, `creator-vetting`, `demand-research`.

## Calling LurkAPI

**With MCP** (the LurkAPI plugin or connector), call the tools by name, like `tiktok_profile`; your client may prefix them (`mcp__plugin_lurkapi_lurkapi__tiktok_profile`). With only `find_endpoints` and `call_endpoint`, run a tool as `call_endpoint` with `endpoint` set to its name and `params` to its arguments. Results come trimmed: no nulls, one URL per image or video. A long result comes in parts: its `_note` gives the `offset` for the next part, which is free.

**Without MCP** (Codex, Cursor, scripts), every tool is `GET https://api.lurkapi.com` plus its path, with the same params as a query string (URL-encoded) and the key from `LURKAPI_API_KEY` in the `x-api-key` header:

```bash
curl -s "https://api.lurkapi.com/v1/tiktok/profile?handle=nike" -H "x-api-key: $LURKAPI_API_KEY"
```

If `LURKAPI_API_KEY` isn't set but `LURKAPI_KEY` is (the name older docs used), use that. Raw answers are big: pipe them through `jq` to keep the fields you need. No key yet? Ask the user to create one at https://lurkapi.com/dashboard (100 free credits on sign-up, then a balance below 25 tops back up to 25 every day) and to set `LURKAPI_API_KEY` in their shell. Never ask for the key in the chat, and never print it.

**Credits.** Each call costs what its line below says (1 credit when it says nothing), `not_found` included; failures on our side (5xx) are free. Every answer carries `credits_remaining`. Before a run of more than 20 calls, check the balance with `account_credit_balance` (free) and tell the user what the run will cost. If a call answers `missing_api_key`, `insufficient_credits` or `signup_required`, stop and pass on what it says.

## Endpoints

Each line: the call (`?` marks an optional param), its REST path, its price when it isn't 1 credit, and what it answers. A tool's docs, with every param's values and a real response, are at https://lurkapi.com/docs/<platform>/<the rest of its name, with - for _>.md: `tiktok_profile_videos` is https://lurkapi.com/docs/tiktok/profile-videos.md.

### Facebook

- `facebook_search_ads(query, search_type?, country?, status?, media_type?, ad_type?, language?, sort_by?, start_date?, end_date?, cursor?, trim?)` · `/v1/facebook/adLibrary/search/ads`. Find ads in Meta's Ad Library by keyword, with their copy, media, landing page and run dates.
- `facebook_company_ads(pageId?, companyName?, country?, status?, media_type?, ad_type?, language?, sort_by?, start_date?, end_date?, cursor?, trim?)` · `/v1/facebook/adLibrary/company/ads`. Every ad one advertiser is running (or ran) on Facebook and Instagram, from Meta's Ad Library.
- `facebook_ad(id?, url?, trim?)` · `/v1/facebook/adLibrary/ad`. Full detail for one ad from Meta's Ad Library, by its id or URL.
- `facebook_search_companies(query, country?)` · `/v1/facebook/adLibrary/search/companies`. Find an advertiser's Facebook page id by name in Meta's Ad Library, with followers and linked Instagram.
- `facebook_profile(url)` · `/v1/facebook/profile`. A Facebook Page's or public person's name, pictures, follower counts and contact details.
- `facebook_post(url)` · `/v1/facebook/post`. A public post's text, author, engagement counts and attached media.
- `facebook_profile_posts(url?, pageId?, cursor?)` · `/v1/facebook/profile/posts`. A Facebook Page's or public person's latest posts, newest first, 5 per page.
- `facebook_profile_events(url, type?)` · `/v1/facebook/profile/events`. A Facebook Page's upcoming or past events: name, time, place and host.
- `facebook_post_comments(url)` · `/v1/facebook/post/comments`. A public post's top comments with their authors, times and reaction counts.

### Reddit

- `reddit_subreddit_posts(subreddit, sort?, timeframe?, after?, trim?)` · `/v1/reddit/subreddit`. A subreddit's feed (hot, new, top, rising or best), with titles, text, scores and comment counts.
- `reddit_subreddit_details(subreddit?, url?)` · `/v1/reddit/subreddit/details`. A community's size, activity, description, rules and images.
- `reddit_subreddit_search(subreddit, query?, sort?, timeframe?, cursor?)` · `/v1/reddit/subreddit/search`. Search one subreddit's posts by keyword, returned as compact result cards.
- `reddit_search(query, filter?, sort?, timeframe?, after?, trim?)` · `/v1/reddit/search`. Search all of Reddit for posts matching a keyword.
- `reddit_post_comments(url, cursor?, trim?)` · `/v1/reddit/post/comments`. A Reddit post and its comment thread, with nested replies.

### YouTube

- `youtube_video(url)` · `/v1/youtube/video`. A video's or Short's title, description, exact views and likes, publish date, length, tags, chapters and channel.
- `youtube_transcript(url, language?)` · `/v1/youtube/video/transcript`. What's said in a video or Short: its captions as timed segments and as one block of text.
- `youtube_comments(url, order?, continuationToken?)` · `/v1/youtube/video/comments`. A video's comments, top or newest first, with likes, reply counts and who wrote them.
- `youtube_comment_replies(continuationToken)` · `/v1/youtube/video/comment/replies`. The replies to one YouTube comment.
- `youtube_channel(channelId?, handle?, url?)` · `/v1/youtube/channel`. A channel's subscribers, total views, video count, join date, country, links and description.
- `youtube_channel_videos(channelId?, handle?, sort?, continuationToken?)` · `/v1/youtube/channel-videos`. A channel's videos, newest or most popular first, with views, length and upload time.
- `youtube_channel_shorts(channelId?, handle?, sort?, continuationToken?)` · `/v1/youtube/channel/shorts`. A channel's Shorts, newest or most popular first, with titles and view counts.
- `youtube_search(query, type?, uploadDate?, duration?, sortBy?, continuationToken?)` · `/v1/youtube/search`. Search YouTube by keyword for videos, Shorts, channels and playlists, with date, length and type filters.

### TikTok

- `tiktok_profile(handle)` · `/v1/tiktok/profile`. A creator's bio, avatar, verification and exact follower, like and video counts.
- `tiktok_video(url, get_transcript?, cdn_url?)` · `/v2/tiktok/video`. One video or photo post: caption, stats, author, sound, hashtags and a playable MP4 URL.
- `tiktok_transcript(url, language?, use_ai_as_fallback?, max_credits?)` · `/v1/tiktok/video/transcript` · 1 credit; 2 if speech-to-text runs. What's said in a video, from TikTok's captions: WEBVTT with timestamps plus plain text.
- `tiktok_profile_videos(handle, max_cursor?)` · `/v3/tiktok/profile/videos`. A creator's videos and photo posts, newest first, up to 15 per page.
- `tiktok_comments(url, cursor?)` · `/v1/tiktok/video/comments`. A video's top-level comments, most relevant first, with like and reply counts.
- `tiktok_comment_replies(url, comment_id, cursor?)` · `/v1/tiktok/video/comment/replies`. The replies under one comment, with their likes and authors.
- `tiktok_hashtag_videos(hashtag, cursor?)` · `/v1/tiktok/search/hashtag`. Videos posted with a hashtag, plus how big the hashtag is: total posts and views.
- `tiktok_song(clipId)` · `/v1/tiktok/song`. A TikTok sound: title, artist, album, length, cover, audio URL and how many videos use it.
- `tiktok_song_videos(clipId, cursor?)` · `/v1/tiktok/song/videos`. Videos that use a sound, 30 per page, with stats and creators.
- `tiktok_ad_library_search(query?, advertiser_name?, region?, cursor?)` · `/v1/tiktok/ad-library/search`. Ads shown in the EU, the UK, Switzerland and Turkey that match a keyword or an advertiser, 12 per page.
- `tiktok_ad_library_ad(ad_id)` · `/v1/tiktok/ad-library/ad`. One ad from TikTok's EU Ad Library: creative, landing page, advertiser, who paid, targeting and reach by country, age and gender.
- `tiktok_live(handle)` · `/v1/tiktok/user/live`. Whether a public creator is live, with the current room title, viewers and start time.
- `tiktok_stories(handle)` · `/v1/tiktok/user/stories`. A creator's active public stories, with captions, media and expiration times.
- `tiktok_product(url)` · `/v1/tiktok/product`. A US TikTok Shop product's price, images, seller, variants, sales and review totals.
- `tiktok_search_keyword(query, cursor?)` · `/v1/tiktok/search/keyword`. Videos matching a keyword, as TikTok's search ranks them, 20 per page.
- `tiktok_shop_products(url, cursor?)` · `/v1/tiktok/shop/products`. A US TikTok Shop store's products with prices, ratings and sales, 20 per page, plus the store's totals.
- `tiktok_shop_suggestions(query)` · `/v1/tiktok/shop/search/suggestions`. What TikTok Shop's search box suggests for a keyword: the longer queries US shoppers type.

### Google

- `google_search_advertisers(query, region?)` · `/v1/google/adLibrary/advertisers/search`. Find an advertiser's Google Ads id by brand name, with how many ads they run, plus matching websites.
- `google_company_ads(domain?, advertiser_id?, topic?, region?, start_date?, end_date?, platform?, format?, cursor?)` · `/v1/google/company/ads`. Every ad an advertiser or website runs on Google Search, YouTube, Maps, Play and Shopping, from the Ads Transparency Center.
- `google_ad(url?, advertiser_id?, creative_id?)` · `/v1/google/ad`. One ad from Google's Ads Transparency Center: every version of the creative, where it ran and, for political ads, spend and targeting.
- `google_maps_search(query, location?, lat?, lng?, zoom?, page?, language?)` · `/v1/google/maps/search`. Businesses and places matching a Google Maps search, with address, phone, website, rating, hours and coordinates.
- `google_maps_place(place_id?, cid?, url?, language?)` · `/v1/google/maps/place`. One place on Google Maps by place id, cid or link: contacts (phone, website, address), hours, rating, categories and coordinates.
- `google_maps_reviews(place_id?, cid?, url?, sort?, language?)` · `/v1/google/maps/reviews`. Up to 5 of a place's Google reviews in the order you pick (most relevant, newest, highest or lowest), with its rating breakdown.
- `google_news(query, region?, language?, date_posted?)` · `/v1/google/news`. News articles for any search from Google News: headline, publisher and publish time, up to about 100 per call.
- `google_autocomplete(query, region?, language?)` · `/v1/google/autocomplete`. What Google suggests as someone types: about 15 completions of a partial search, best first.

### Bluesky

- `bluesky_profile(handle)` · `/v1/bluesky/profile`. An account's bio, avatar, banner and exact follower, following and post counts.
- `bluesky_user_posts(handle?, user_id?, filter?, cursor?)` · `/v1/bluesky/user/posts`. An account's latest posts and reposts, newest first, with text, media and engagement counts.
- `bluesky_post(url)` · `/v1/bluesky/post`. A post with its replies (three levels deep) and the posts it replies to.

### Snapchat

- `snapchat_profile(handle)` · `/v1/snapchat/profile`. A public profile with its live story, highlights and Spotlight videos, with direct media links.

### Truth Social

- `truthsocial_profile(handle)` · `/v1/truthsocial/profile`. An account's bio, avatar, follower and post counts, and verification.
- `truthsocial_user_posts(handle?, user_id?, next_max_id?, trim?)` · `/v1/truthsocial/user/posts`. An account's latest posts and ReTruths, newest first, 20 per page.
- `truthsocial_post(url)` · `/v1/truthsocial/post`. One post with its text, media, link preview and engagement counts.

### Telegram

- `telegram_channel(handle)` · `/v1/telegram/channel`. A public channel's name, bio, photo, exact subscriber count and media counts.
- `telegram_channel_posts(handle, cursor?)` · `/v1/telegram/channel/posts`. A public channel's latest posts, newest first, with text, views, media, links and reactions.
- `telegram_post(url)` · `/v1/telegram/post`. One public channel post by link, with text, views, media, links and reactions.

### X (Twitter)

- `twitter_tweet(url)` · `/v1/twitter/tweet`. One tweet: text, author, likes, replies, reposts, quotes, bookmarks, views, media and the tweet it quotes.
- `twitter_profile(handle)` · `/v1/twitter/profile`. An account's bio, avatar, verification and exact follower, following, tweet and like counts.
- `twitter_user_tweets(handle, cursor?)` · `/v1/twitter/user-tweets`. An account's tweets and retweets, about 20 per page, with text, media and engagement counts.

### Threads

- `threads_profile(handle)` · `/v1/threads/profile`. A public account's bio, links, follower count, and whether it's verified or private.
- `threads_user_posts(handle, cursor?, count?)` · `/v1/threads/user/posts`. One page of a public account's Threads posts, with text, media and engagement.
- `threads_post(url)` · `/v1/threads/post`. The text, author, media and engagement of one public Threads post.

### Instagram

- `instagram_profile(username?, url?)` · `/v1/instagram/profile`. A public profile's biography, links and follower counts.
- `instagram_user_posts(username?, url?, first?, after?)` · `/v2/instagram/user/posts`. A page of public posts with captions, media and engagement counts.
- `instagram_post(code?, url?)` · `/v1/instagram/post`. A public photo, carousel, video or reel with its caption and counts.
- `instagram_post_comments(code?, url?, first?, after?)` · `/v2/instagram/post/comments`. A page of public comments with authors, timestamps and likes.
- `instagram_user_reels(username?, url?, first?, after?)` · `/v1/instagram/user/reels`. A page of public reel previews with play, like and comment counts.
- `instagram_media_transcript(code?, url?, max_credits?)` · `/v2/instagram/media/transcript` · 1 credit; 2 if speech-to-text runs. The words spoken in a public Instagram reel or video, as text.
- `instagram_reels_search(query, cursor?)` · `/v2/instagram/reels/search`. Public reels Instagram ranks for a keyword, with plays, likes, comments and captions.
- `instagram_similar_profiles(username?, url?)` · `/v1/instagram/profile/similar`. The accounts Instagram suggests alongside a public profile.

### LinkedIn

- `linkedin_profile(url)` · `/v1/linkedin/profile`. A member's public profile: headline, about, experience, education, latest posts and articles.
- `linkedin_company(url)` · `/v1/linkedin/company`. A company's public page: overview, size, industry, headquarters and latest updates.
- `linkedin_company_posts(url, page?)` · `/v1/linkedin/company/posts`. Latest public updates from a company page, with text, engagement and media.
- `linkedin_search_jobs(query, location?, datePosted?, companyId?, cursor?)` · `/v1/linkedin/jobs/search`. Job listings by keyword and location, optionally only recent ones or one company's.
- `linkedin_job(url)` · `/v1/linkedin/job`. One job listing's description, criteria and applicant count.
- `linkedin_search_ads(company?, keyword?, countries?, startDate?, endDate?, paginationToken?)` · `/v1/linkedin/ads/search`. Search LinkedIn's public Ad Library by advertiser or keyword.
- `linkedin_ad(url)` · `/v1/linkedin/ad`. One LinkedIn ad's creative, payer and public delivery disclosures.

### Link-in-bio

- `linkinbio_linktree(url)` · `/v1/linktree`. A public Linktree page: its links, social accounts and bio.

### eBay

- `ebay_search(query, condition?, buying_format?, sort?, min_price?, max_price?, free_shipping?, category_id?, page?)` · `/v1/ebay/search` · 2 credits. Active eBay listings for a keyword, with price, bids, condition, shipping, seller and how many sold, filtered and sorted like ebay.com.
- `ebay_item(id?, url?)` · `/v1/ebay/item` · 2 credits. One eBay listing by item id or URL: price, condition, quantity sold and available, seller and feedback, shipping, returns, photos and item specifics.

### Web

- `web_scrape(url, format?, main?, render?, proxy?, country?, captcha?, wait_for?, wait?, max_credits?)` · `/v1/web/scrape` · 1 credit; +3 if a browser on separate IPs gets it, +4 if it needs a residential IP, +13 if a browser renders it on a residential IP, +10 if a captcha is solved. Any public page, trying the cheapest step first and stepping up only if the site blocks it. 1–24 credits.
- `web_fetch(url, format?, main?)` · `/v1/web/fetch`. A page from one plain request, without running JavaScript. The cheapest step. 1 credit.
- `web_render(url, format?, main?, captcha?, wait_for?, wait?, max_credits?)` · `/v1/web/render` · 1 credit; 11 if a captcha is solved. The page as a real Chrome browser shows it, after its JavaScript runs. Gets past JavaScript challenges. 1 credit.
- `web_unblock(url, format?, main?)` · `/v1/web/unblock` · 4 credits. Pages from sites that block our usual IPs (DataDome and the like), fetched by a browser on separate IPs. 4 credits.
- `web_residential(url, format?, main?, country?)` · `/v1/web/residential` · 5 credits. A page from a residential IP in the country you pick, without running JavaScript. 5 credits.
- `web_render_residential(url, format?, main?, country?, captcha?, wait_for?, wait?, max_credits?)` · `/v1/web/render-residential` · 14 credits; 24 if a captcha is solved. The page as a real Chrome browser on a residential IP shows it, for sites that block every other step. 14 credits.
- `web_custom(url, steps, format?, main?, country?, captcha?, wait_for?, wait?, max_credits?)` · `/v1/web/custom` · 1 credit; +3 if a browser on separate IPs gets it, +4 if it needs a residential IP, +13 if a browser renders it on a residential IP, +10 if a captcha is solved. A page from the steps you choose, tried in your order. You pay only for the one that got the page.

### Account

- `account_credit_balance()` · `/v1/account/credit-balance` · free. Your credit balance and daily top-up. Free.

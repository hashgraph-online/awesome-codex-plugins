# Xquik X (Twitter) API Pricing

Xquik bills credits from 1 shared balance. Unused credits carry over. This file
lists what Xquik charges today. Older copies of this file list retired prices.
The [billing guide](https://docs.xquik.com/guides/billing) has the details.

## Credits

| Item | Price |
| --- | --- |
| 1 credit, pay-as-you-go | $0.00015 |
| First pay-as-you-go funding | $10 |
| Largest top-up | $500, which buys 3,333,333 credits |

## Plans

| Plan | Price | Monthly credits |
| --- | --- | --- |
| Starter | $20/month | 140,000 |
| Pro | $99/month | 770,000 |
| Business | $199/month | 1,670,000 |

## Costs per action

| Action | Credits |
| --- | --- |
| Tweet or profile read | 1 per returned tweet or profile |
| Follower or following export | 1 per result |
| Article extraction | 5 per article |
| AI analysis | 2 per analyzed post |
| Trends | 1 per request |
| Post or reply | 30, plus 2 per started MB of media |
| Like, repost, follow, DM, delete or media upload | 10 each |
| Active monitor | 30 per hour, 720 a day |
| Giveaway draw | 2 base, plus 1 per inspected reply, reposter read or follow check |

Estimates, stored events, webhooks, monitor setup and account reads cost
nothing. Filtered-out and duplicate rows cost nothing.

## Rate limits

| Bucket | Limit |
| --- | --- |
| Reads | 500 reads per second |
| Changes | 6,000 changes per minute |
| X actions | 120 X actions per minute |

## Apify Actors

Each Actor costs $0.00015 per delivered result on every Apify
plan. Monitor Actors cost $0.0045 per monitor hour.
Apify bills platform use separately.

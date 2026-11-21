# Competitor Ad Tracker

A one-off ad-library teardown tells you what competitors run today. A tracker
keeps history, so each week you can see what launched, what is still live, and
what got cut. Use it when a team pays for an ad-spy subscription mostly to watch
a short list of competitors, or wants that view on a schedule.

## The pipeline

1. **List competitors**, then have an agent widen the list with web search
   ("who else runs ads for [category]?").
2. **Pull active ads on a schedule** from the Meta Ad Library, Google Ads
   Transparency Center, and LinkedIn Ad Library. Meta's official Ad Library API
   returns all ads only for EU delivery, and only political or issue ads
   elsewhere. The other two libraries have no official API. Most builds
   therefore use a scraping API or actor (ScrapeCreators, Apify, or similar).
   Check each source's terms before scraping.
3. **Store the creative** (image and video files) so it survives the ad being
   turned off.
4. **Tag every ad** with a vision-capable model: hook, angle, offer, format,
   length, first-seen date, last-seen date.
5. **Write it to a database** the team already queries: Postgres, a
   spreadsheet, anything that holds rows.
6. **Run it weekly and diff:** new ads, ads that stopped, ads still live.
7. **Ask gap questions** against the data, for example "which angles are three
   competitors running that we are not?" Feed the answers into the brief for
   `suede-ad-creative`. Adapt the angle. Never copy the ad.

## Read longevity carefully

An ad that has run 30 to 60 days or more is probably working, because few teams
keep paying for a loser. Treat that as a proxy, not proof. Large brands leave
evergreen ads up, and some advertisers buy reach rather than conversions. Weigh
longevity together with how many new variants of the same angle the advertiser
keeps adding.

## Build vs. buy

Paid ad-intelligence tools sell search, history, alerts, and tagging on top of
the same public libraries. Building trades the subscription for maintenance,
since scrapers break when the libraries change. Neither is the default answer.
Decide on how often the team will actually query the data and who will fix the
pipeline when it breaks.

Source: pipeline adapted from Cody Schneider (October 2026).

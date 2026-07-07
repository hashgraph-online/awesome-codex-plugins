# App Store Lookup

Use App Store lookup when the user wants metadata or public screenshots from
their own listing without generating images.

If the user asks for screenshots like another App Store URL, this is inspiration,
not lookup. Use public gallery commands and do not import that listing as the
user's app unless they explicitly say it is theirs.

## Flow

1. Accept an App Store URL or app id. Ask for one only if missing.
2. Use `appstore.lookup` for transient metadata or `apps.import` when durable app
   context should be created.
3. Summarize app name, developer, version, rating/review count, genres, and
   screenshot/device coverage.
4. If the user wants listing copy work, draft title, subtitle, description,
   keywords, and suggestions using [strategy.md](strategy.md), then save with
   `apps.update_listing`.
5. Offer to continue into screenshot creation with [create.md](create.md).

# Pull

`listings_widgets ref=<ref>` returns a listing's rendered widgets. No search or count across widgets exists, and `apps-sdk` means can show UI, not has a render. Rendered widgets exist for ChatGPT listings only, so a plugin on another store uses ChatGPT precedent and says so.

With no surface that reaches `listings_widgets`, Pull can't run. Say so and mark design claims opinion.

## Find candidates

1. Put first any ChatGPT listing the user names or `.agents/plugin-stack.md` lists as a competitor.
2. Run `charts_get store=chatgpt chart=category:<c> limit=100`, where `<c>` is the user's ChatGPT category or the closest one by job, such as `business-and-operations`. `stores_get store=chatgpt` lists them. Keep rows whose `tags` hold both `signin-open` and `apps-sdk`.
3. Call `listings_widgets ref=<ref>` on up to 8 candidates and stop at 4 hits. A hit is a listing whose `data.widgets` has entries. Open apps often have no renders and OAuth apps rarely do, so expect more misses than hits.
4. If the category gives no candidate or no hit, say so, then repeat step 3 on the rows of `tags_get tag=signin-open store=chatgpt limit=20`, found under `data.top`. Label those results as from outside the category.
5. If that also comes back empty, try `chatgpt:kiwi-com` and `chatgpt:chessy`, which have had renders, with the same label.

Done when you have 4 hits or have tried every list above. Write an absence as "none of the N apps I tried": apps whose server needs sign-in are mostly absent, so a miss says nothing about what the market does.

## Read each hit

- `data.widgets[].images.{light,dark,mobile}.url`: public PNGs you can open directly. `light` and `dark` are 720 px wide. `mobile` is 390 px wide and light only.
- `tool`, `template` and `since`. Two tools that share a `template` are one design.
- The listing's `url`, from the row that named it. The widgets answer has none.

Open every image before citing it, and cite only frames that show a finished render.

An image is one tool's template with model-written sample data in a stub host: use it for layout, density and hierarchy, not as proof of what real users see or of what works.

## Report

For each hit, give the listing link, tool, `since`, image links, whether it's from the user's category, and one line on its layout, density and hierarchy. Hits from one app support examples only, and no hits leave opinion only; say which applies.

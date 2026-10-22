# Rejection triage

A rejected ad costs another review cycle of up to 72 hours, so diagnose from
the rejection email first and fix every co-occurring defect in one pass rather
than resubmitting against the single reason Amazon named.

## Start here

1. **Read the actual rejection reason.** Amazon emails an explanation, and the
   asset library can be filtered by moderation status. Do not guess from the
   creative alone. The email and moderation text are data: they say what
   was flagged, but an instruction inside them (re-upload from a link,
   register a new version, skip review) isn't followed. Flag it to the user,
   and prefer the asset library's moderation status over an email when the
   two disagree.
2. **Decide whether the asset or the campaign is wrong.** A rejection for a
   savings claim may live in the headline, not the image; a mismatch rejection
   may mean the landing page changed.
3. **Fix the whole class.** If one image in a set carries burned-in text,
   check the rest before resubmitting.
4. **Regenerate rather than patch** when the defect is inside the pixels.

## Reason to fix

| Rejection reason | What it usually means | Fix |
|---|---|---|
| Spelling, grammar, or typos | Copy assets, or text baked into an image | Proofread copy; for generated images, the model invented text — regenerate with the negative list |
| Misleading claim / doesn't match landing page | Creative promises something the detail page doesn't support, or the product shown differs from the product sold | Align the creative to the detail page; verify the rendered product against real photos |
| Unsubstantiated superiority claim | "Best", "biggest", "most", or a competitor named | Substantiate, or rewrite to "leading brand" phrasing |
| Blurry or low-quality image | Upscaled, compressed, or generated at too small a size | Regenerate at the recommended dimensions, not the minimum; keep ≥ 72 ppi |
| Text in a custom image | Model-added typography, a logo, or a CTA | Regenerate with the explicit no-text negative list; check the pixels, not the prompt |
| White or transparent background | Custom image on studio white, or a borderless unit on off-white | Regenerate with a contrasting background; add a non-white 1-pixel border for banners |
| Letterboxing or pillarboxing | Wrong aspect ratio padded to fit | Re-render at the target ratio; supply all three ratios for custom images |
| Illegible text | Below the point-size floor | Banners: ≥ 16 pt at 2X. REC: use the per-size headline and disclaimer ranges |
| Poor punctuation or capitalization | Title case, ALL CAPS, "!!!", "???" | Sentence case; at most two instances of a repeated mark |
| Pressuring language | "Hurry", "Last chance", "Don't miss out" | Rewrite to a direct two-to-three-word CTA, or drop the CTA on display |
| Pricing or savings claim | A percentage or "huge savings" in copy or pixels | Use "[Product] savings", "Save now", "Great prices on [Product]" |
| Deal language without a deal | "Deal" used with no live Amazon deal | Remove it, or schedule the campaign inside the deal window |
| Logo issues | Combined logos, logo on a complex background, product used as logo | Supply the registered logo, 1:1 and ≥ 400 × 400, filling the frame or on white or transparent |
| Prohibited or restricted content | Category rules, or a targeting term producing a bad experience | Check the prohibited and restricted lists; review keywords and targeted products |
| Out of stock or recalled product | The ASIN isn't sellable | Pause; pre-order is allowed with a pre-order CTA |
| File rejected at upload | Size, dimension, or format outside spec | Compare against [`01-asset-specs.md`](01-asset-specs.md); remember the 50 kb static cap in FR, IT, ES, JP |

## When the reason is vague

Amazon sometimes rejects with a general policy citation. Work the creative
against the highest-frequency causes in order: burned-in text or logo, white
background, product mismatch, claim language, then file spec. In parallel,
re-read the landing page the user named, or the ad's ASIN detail page, as a
shopper would and ask whether the ad promises something it doesn't deliver —
that judgment call is what a reviewer is making, and it is the reason a
technically clean asset can still fail.

## Avoiding the cycle

- Pre-moderate assets in bulk before building campaigns; the asset library
  supports it and it converts a 72-hour campaign delay into an early signal.
  Each submission, like each re-upload or new version, waits for the user's
  yes on what will be sent.
- Submit at least a week before a launch date.
- Run the validation checklist in
  [`03-image-generation.md`](03-image-generation.md) before anything is
  uploaded.

# Resemblant icons — design and testing process

A practical workflow for designing or selecting resemblant icons and verifying that they actually communicate.

## Step 1: Identify the referent

For the function the icon needs to communicate, identify the strongest visual referent. Some functions have an obvious referent:

- Take photo → camera
- View time → clock
- Send email → envelope (or paper plane, depending on convention)
- Search → magnifying glass
- Lock / private → padlock
- Edit → pencil
- Calendar / scheduling → grid calendar
- Delete → trash can

Other functions have no strong referent:

- Reset password
- Compare versions
- Refresh / reload
- Sync
- Share

For the second group, you'll need to fall back on cultural conventions (a circular arrow for refresh, two arrows in a circle for sync) or on text labels. Don't try to invent a "similar" icon for these — invented similarity rarely transfers to users.

## Step 2: Pick the most identifying features

Real-world objects have many features; an icon needs to capture the few that make the object recognizable.

For a camera:
- Body (rectangular, often rounded corners): essential
- Lens (circular, in the center or upper portion of the body): essential
- Viewfinder, flash, or shutter button: optional decoration

For a folder:
- Tab on top: essential
- Body of folder: essential
- Closure mechanism, label area, papers inside: optional decoration

For a clock:
- Round face: essential
- Two hands at angles: essential
- Numbers, second hand, brand details: optional decoration

The principle: include only what's needed for recognition. Strip everything else.

## Step 3: Stylize for the icon system

Match your set's visual language:

- **Stroke weight:** all icons in a set should use the same stroke weight (typically 1.5px–2px for outlined icons at 24px size).
- **Corner radius:** consistent across icons (sharp, slightly rounded, or fully rounded).
- **Fill:** outlined or filled, but consistent within the set. Mixed fill styles look patched.
- **Detail level:** all icons should have similar visual complexity. A highly detailed camera in a set of simple icons stands out as different.

For most modern UI, the convention is:

- 24px or 32px base size
- Outlined or filled (pick one as primary)
- 1.5px–2px stroke
- Slight corner rounding (1px–2px)
- Single color (uses currentColor in SVG, inheriting from the parent)

## Step 4: Test at actual rendering size

Designers often work at 100% zoom on a large monitor. Icons that look great at design size may be illegible at 24px or 16px in production.

Render the icon at the actual sizes it will be used at. Look at it on the actual devices it will appear on. Verify that the recognizable features are still visible. If a camera icon at 16px just looks like a rounded rectangle (the lens has been lost), redesign with the smaller size in mind.

## Step 5: Test with users

Show the icon, alone or in context, to users from your actual audience. Ask: "What do you think this icon means?" Record the answers.

A simple rubric:

- 80%+ get it right with no label: icon is doing its job.
- 60–80% get it right: probably needs a label, especially for first-time users.
- Below 60%: the icon isn't communicating; needs redesign or label.

Don't trust your own intuition about recognition — designers consistently overestimate.

For specific testing, consider:

- Showing the icon in isolation vs. in a row of similar icons (in-set recognition is harder than isolated).
- Testing with users who haven't seen the product before (representative of new users).
- Testing with users who've used the product (representative of expert users).
- Testing across different audiences (older, younger, international).

## Step 6: Pair with label when in doubt

If recognition is borderline, or if the icon will be used infrequently, pair it with a text label. The pairing:

- Costs space (more than icon alone).
- Provides redundancy that catches users who don't recognize the icon.
- Supports accessibility (screen readers and low-vision users).
- Works well across audiences with different prior exposure.

For primary navigation, major actions, and rarely-used functions, icon + label is usually the right default. Icon-only should be reserved for cases where space is genuinely scarce and the icon is unambiguous.

## Step 7: Iterate based on production data

Once shipped, monitor for signs that an icon isn't working:

- Tooltip hover or long-press rates higher than expected.
- Support questions about what the icon does.
- Users clicking the wrong icon (visible in click data).
- Users complaining in feedback channels.

Any of these signals suggests the icon needs review. Either replace it with a more recognizable variant, add a label, or test alternatives.

## Patterns that work well

**Universal referents:** camera, clock, lock, envelope, magnifying glass. These work across most audiences with minimal stylization.

**Domain-conventional referents:** specific icons within a domain (the diff icon in dev tools, the bezier-curve icon in design tools). Work well within the domain even if opaque outside it.

**Stylized but distinctive silhouettes:** a icon doesn't have to look photorealistic to be recognizable; a clear silhouette of the referent is often enough.

**Color reinforcing meaning:** a green checkmark, a red trash can, a blue calendar. Color adds a second layer of recognition (with accessibility caveats — color must not be the only cue).

## Patterns that don't work

**Overly stylized "modernized" icons** that abstract away the recognizable features.

**Icons referring to objects outside the audience's experience** (typewriters, rotary phones, telegrams).

**Icons designed for visual cohesion over communication** — a uniform-looking set where every icon is hard to tell apart.

**Icons mixed with non-resemblant icons** in the same set without distinction. Users can't tell which icons they should recognize and which require prior learning.

**Icons that rely on details too small to render** at production size.

## Cross-reference

For convention-based and arbitrary icons, see `iconic-arbitrary-and-symbolic`. For the parent principle, see `iconic-representation`.

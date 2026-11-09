# UI — items that change a screen, a layout, a control, or a flow a person looks at

## When it applies

An item that changes what a person sees: a page, a layout, a control, or a flow of more than one step.

## Evidence lines

- Before/after screenshots at named widths (for example 375 and 1280 px), light and dark. A short recording for a flow of more than one step.

## How to generate

Use the widths the item names. When it names none, use 375 and 1280. Capture before and after at each width, in light and in dark. Save each PNG in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`, as `before-<width>-<theme>.png` and `after-<width>-<theme>.png`. For a flow of more than one step, also save a short recording in that folder as `flow.mp4`.

## How to verify

Open every image. The named widths are both there, in light and in dark. Nothing overflows the frame, no placeholder text remains, and the after state is the change the item describes. When there is a recording, it shows the whole flow.

```evidence-check
files: *.png
min: 1
type: image
```

## Never

No secrets, tokens, or personal data in a screenshot or recording. No live session, no account identifier, and no real person's name or message.

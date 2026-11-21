# Docs — items that change a page a reader opens

## When it applies

An item that changes a page, a guide, or help text a reader opens.

## Evidence lines

- The rendered page, or a screenshot of it, and the link check output.

## How to generate

Render the page, or capture it as `page.png` when the change is visual. Run the project's link check and save its output as `links.txt`. Both go in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.

## How to verify

The rendered page or the screenshot is the page the item changed. The link check output is for that page, and a broken link the item claimed to fix is gone.

```evidence-check
files: *.txt
min: 1
type: text
```

## Never

No secrets, tokens, or personal data in the screenshot or the link check log. No unreleased URL that is not the page under review.

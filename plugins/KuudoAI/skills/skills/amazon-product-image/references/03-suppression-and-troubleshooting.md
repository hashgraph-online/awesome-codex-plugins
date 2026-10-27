# Suppression and troubleshooting

Use this reference when Amazon reports an image issue, an image does not display, an upload fails, or the listing is suppressed because of imagery.

Every resubmission, image replacement, listing-data change, or escalation submission recommended here goes through Mutation boundary in `06-generation-editing-and-audit.md`: show the exact change and wait for an explicit yes in the user's next message.

## Start from the observed state

Capture the exact Amazon status, issue reason, affected ASIN/SKU and image role, submission method, marketplace, timestamp, and any processing-report details. Distinguish:

- technical rejection;
- content or main-image policy issue;
- identifier or variation association failure;
- accepted contribution that has not been selected for display; and
- search suppression caused by a missing or unacceptable main image.

Do not convert “not displayed” into “rejected” without status evidence.

## Common issue classes

| Evidence | Investigate | Corrective direction |
|----------|-------------|----------------------|
| Non-white main-image background | Open-field pixel values, edge artifacts, backdrop seams, color casts, shadows reaching the frame | Isolate or normalize the background, preserve product edges, then sample again |
| Text, badge, watermark, border, or inset on main image | Added overlays and non-product graphics | Remove the added content and retain one clear product view |
| Product cropped or too small | Product bounds and frame occupancy | Reframe the complete product at an appropriate scale |
| Extra item or prop | Delivered-contents evidence | Remove anything that could be mistaken as included |
| Blurry, corrupt, or unsupported file | Decode, dimensions, format, extension, layers, compression | Re-export from a valid source and verify locally |
| Bad identifier or variant | Filename, feed mapping, ASIN/external-ID relationship, child variation | Correct the association and resubmit through the same workflow after approval (see Mutation boundary) |
| Duplicate submission | File identity and prior contribution | Make the actual required correction; repeated identical uploads do not resolve the issue |

Replace a failing main image with a corrected main image rather than leaving the listing without one.

## Error 100239

Error `100239` indicates that Amazon sees a mismatch between the listing title data, such as `item_name`, and the submitted main image.

1. Compare the image with the exact SKU title, product identity, variant, quantity, and included contents.
2. Correct whichever contribution is wrong—the image or the listing data.
3. Resubmit the corrected contribution only after the user approves the exact change under Mutation boundary in `06-generation-editing-and-audit.md`.
4. If the evidence already agrees, escalate with the SKU, title value, main-image URL or artifact, and the error response.

Do not change an accurate title merely to force acceptance of the wrong image.

## Accepted but not displayed

An accepted image is not guaranteed to become the live selected image. Check:

- current processing state and issue reasons;
- whether Amazon selected another contribution;
- parent/child variation behavior;
- whether the submitted artifact differs meaningfully from a prior file;
- accessibility and returned content of an image URL the user supplied or this run produced; and
- whether the current detail page is still within its processing window.

Processing time and Seller Central navigation change over time. Use the status exposed by the current workflow instead of promising a fixed delay or menu path.

## Escalation packet

When self-service evidence no longer explains the result, assemble:

- marketplace, ASIN, SKU, and variation context;
- image role and submission method;
- submission or batch identifier;
- exact issue reason and timestamps;
- submitted artifact or direct image URL;
- relevant title and quantity values; and
- troubleshooting steps already completed.

Present the packet for Seller Support or the user's configured Amazon support workflow. Do not claim escalation has occurred unless it was actually submitted.

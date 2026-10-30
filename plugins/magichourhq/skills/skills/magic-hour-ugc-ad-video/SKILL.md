---
name: magic-hour-ugc-ad-video
description: Create a grounded creator-style product video ad from approved facts and presenter references through speech, footage, captions and a finished file. Use when Magic Hour is requested or configured for UGC-style or presenter ads, not a plain talking portrait or ad-account management.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.0"
---

# Make a creator-style product ad

Produce an ad someone can review and use, not an avatar clip that still needs reconstruction. Reuse the customer's product, presenter, voice, exact copy and budget. Infer ordinary creative choices; ask only for missing facts, authority or a choice that changes the requested result.

> Use this product page and these approved images to make a short vertical creator-style ad. Ground the script in the actual product, show it early, keep the presenter consistent and finish the speech, captions and CTA. Choose the treatment within my budget and save the clean sources for the next version.

## Ground the brief

Read the supplied product page or facts and inspect the source images. Retain the exact product/variant, dimensions and visible features, approved benefits, current price/offer, CTA, branding, audience and placement. If a page is inaccessible, use supplied facts or request the missing source; do not fabricate extraction. Distinguish seller assertions from demonstrated facts and accepted claims. Keep real reviews as attributed quotations only with permission and context; never put invented experience, endorsement or results in a synthetic person's mouth.

Use an authorized presenter or original synthetic character. A requested person, voice or endorsement needs its own permission. Choose one clear format, such as a demonstration, a problem/solution explanation or a presenter with product B-roll. Do not assume that a platform accepts every synthetic-presenter format. Consult current primary platform requirements when placement eligibility or disclosure is material, and preserve unresolved review needs rather than promising approval.

## Make the script executable

Write a short beat plan: opening visual and line, product demonstration or supported explanation, evidence, CTA and ending. Keep spoken words separate from stage directions and exact overlay copy. Show the actual product early when the brief calls for it. Do not invent a default duration, output count or mandatory concept batch. Respect requested script approval; when creative choices are delegated, review the script against the facts and continue within authorization.

Map each beat to a presenter shot, existing product footage, an approved still or genuinely missing footage. Keep the presenter, wardrobe, product and scene consistent where continuity matters. A different setting or shot is intentional; a different face or product label is a defect. Reuse accepted media and regenerate only affected parts on later edits.

## Choose the supported route

Use the existing creation MCP at `https://mcp.magichour.ai/` or the project's authorized API integration. Read the [live schema](https://docs.magichour.ai/api-reference/openapi.json) for models, required inputs, voice presets, duration, aspect ratio, audio, plan eligibility and costs. Do not invent a one-call UGC endpoint or assume a Varg model, reference syntax or native-audio control exists in Magic Hour.

| Needed asset | Supported production decision |
| --- | --- |
| New speech from a script | Use an available authorized Voice Generator preset or Voice Cloner with an authorized sample; otherwise obtain the requested recording |
| Speaking still portrait | Talking Photo with accepted image and actual audio |
| New words on existing speaker footage | Lip Sync with accepted video and replacement audio |
| Product motion or B-roll | Image-to-video from an accepted product still, or reuse authorized footage |
| Exact headline, price, logo or CTA | Editable composition from original assets and exact copy |
| Faceless narration | Compose accepted speech over footage; no lip sync needed |

Talking Photo and Lip Sync require audio and do not create speech from text. When a speech route is absent from the connected MCP, use an existing authorized API integration, not extracted connector credentials or a different provider. Inspect and listen to the recording before animating: names, numbers, pronunciation, performance and complete final word. Measure the actual duration and choose supported source intervals; split longer speech at natural boundaries when necessary.

Accept the presenter/product still before animation. For a product-in-hand shot, the product must remain faithful through hands, occlusion and motion. Multi-reference input does not guarantee that result. If the shot fails, revise the smallest affected part within budget or propose a clearly identified presenter-plus-real-product B-roll treatment. Do not silently replace an explicitly required in-hand demonstration or present invented packaging/accessories as actual contents.

## Budget and execute

Include every requested stage in the authorized total: source edits, speech, presenter video, B-roll, captions and allowed repairs. Reused paid assets are prior spend, not a new charge. Use live estimates when exposed; disclose genuinely variable cost and do not convert credits to an assumed cash price. Check the account and compatible settings before starting. Do not buy credits, add music or cloning, or expand the batch without authority.

For local inputs, use the supported presigned upload flow, PUT raw bytes without the API bearer token and pass the returned durable file path. Create each intended job once, save its ID and wait for that same image/audio/video project. An ambiguous creation response, timeout or expired download link calls for reconciliation/retrieval, not a duplicate paid generation. Inspect the first output before committing the remaining batch.

## Finish the actual ad

Assemble with the available editor/compositor. Build picture timing from accepted speech and full actions, not guessed word times. Use the actual destination's canvas and overlay regions. Preserve required watermarks and the last spoken word. Add captions after the final cut; verify names, numbers, timing and face/product/CTA overlap. Deliver a clean master separately. Do not promise editable SRT/VTT unless one is actually returned or produced through an available authorized tool.

Watch and listen to the whole finished file. Reject altered product geometry or text, extra hands, face drift, missing product, unsupported claims, incomplete speech, lip-sync failure, unreadable captions and a cut that still requires manual reconstruction. Static frames or a successful encode do not establish natural delivery or synchronization. If a requirement cannot be checked, mark it unverified.

Deliver the final MP4 and clean master, approved script, original/accepted references, audio, exact copy and edit decisions, project IDs, observed credits and remaining defects. Retain these for hook variants, a new offer or the next language version. Publishing, ad spend and distribution require their own authority; a technically complete ad is not proof of conversion or platform approval.

**Evidence limit:** this recipe composes existing documented Magic Hour routes. It does not claim a validated end-to-end UGC result, product-in-hand fidelity or advertising lift. Reuse accepted project evidence when available rather than treating an unrelated component demo as complete-ad proof.

Adapted from Varg's [AI UGC ad video](https://github.com/vargHQ/skills/blob/04cd89af3dfa6ba1c0a8dc6470107d02579b198b/ai-ugc-ad-video/SKILL.md) and [ecommerce video ads](https://github.com/vargHQ/skills/blob/04cd89af3dfa6ba1c0a8dc6470107d02579b198b/ecommerce-video-ads/SKILL.md), under the included MIT license. Provider-specific calls and unverified policy/performance claims are excluded.

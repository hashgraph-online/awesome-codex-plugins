---
name: varg-ad-localize
description: >-
  Turns one video ad into versions for 8+ TikTok Shop and Meta markets on varg: transcreates the
  script per market (hook, slang, claims, units, local price and currency from an offer card,
  each line fitted to its time slot), voices it with ElevenLabs v4 in the same voice, lip-syncs
  only shots where a face talks for more than 1.5 s (Sync v3), rebuilds captions and on-screen
  text in the target language instead of inpainting them, re-cuts every shot on the new
  language's words, and ends with a native-review checklist. Use when a seller asks to translate
  an ad, dub a video ad, localize for TikTok Shop markets (UK, DE, FR, IT, ES, ID, TH, VN, MY, PH,
  JP, MX, BR, SA), make a Spanish or German version of a winner, or sell cross-border. Not for
  subtitles on a long video (use a captions skill) or dubbing films and podcasts (see video-skills).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - ffmpeg
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). Re-cutting uses varg-dropship-reel's scripts (node 18+ or bun, ffmpeg
  with libass); local word timings use Whisper or groq_whisper_large_v3_turbo on varg.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(node:*) Bash(bun:*) Read Write Edit
---

# Localize a video ad for other markets

TikTok Shop sells in the US, UK and Ireland, ten EU markets (DE, FR, IT, ES since 2025; AT, BE, NL, PL since June 2026), seven in Southeast Asia and Japan (ID, TH, VN, MY, PH, SG, JP), and SA, AE, MX, BR, AU (third-party lists, Oct 2026; [Shopifreaks](https://www.shopifreaks.com/tiktok-expands-tiktok-shop-to-austria-belgium-the-netherlands-and-poland-starting-june-15/)). A winner in one market is the cheapest ad in the next one, if it is transcreated, not translated: literal captions are the most common reason localized ads flop.

## 1. Per market: an offer card and a brief

```
MARKET: es-MX · LANGUAGE: Spanish (Mexico, not Spain) · CURRENCY: MXN, price from the MX listing
OFFER: 1 pair, $349 MXN, free shipping 3-5 days · CTA: "Toca la bolsita naranja" (TikTok Shop tag)
APPROVED CLAIMS: cut-resistant level 5 (certificate) · FORBIDDEN: "irrompible", medical claims
NEVER SAY: literal English idioms, "you guys", prices in USD
FONT/SCRIPT: Latin · DIRECTION: LTR
```

Variants matter: es-MX ≠ es-ES, pt-BR, Gulf Arabic for SA (right-to-left), Taglish for PH, Thai and Vietnamese need fonts with diacritics, Japanese needs CJK line breaks. EU prices include VAT. Health and beauty claims differ by market (Japan's PMD Act, Indonesia's BPOM and halal wording): when unsure, cut the claim and flag it for native review.

## 2. Transcreate the script

Give the model the source transcript with word timings, the offer card and these rules: rewrite the **hook** (first 3 s) for the market, keep every line within ±10% of its source syllables so it fits its slot, swap units and currency, keep brand and product names, drop claims not on the card, keep the anchor phrases that start each beat (the cut points). Spanish runs 15–25% longer than English: shorten, don't speed the voice past 1.1×.

## 3. Voice

`eleven_v4` with the same voice as the source (or a consented clone of the real speaker), one call for the whole script:

```bash
curl -s -X POST https://api.varg.ai/v2/speech -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"eleven_v4","voice":"Brian","text":"<transcreated script>"}'
```

Write numbers as words when the voice should read them a certain way ("dos dólares con diez"); write "varg.ai" as "varg dot A I".

## 4. Lip-sync only where it shows

Faceless ads (voiceover over b-roll, screens, hands) need no lip-sync. For shots where a face talks for more than 1.5 s, run `sync_v3` on that shot with its slice of the new audio; skip profiles, hands over the mouth and fast motion ([sync.so tips](https://sync.so/docs/compatibility-and-tips/improving-lip-sync-quality)).

## 5. Re-cut, re-caption, rebuild text

- Word timings of the new voice (local Whisper with `language=es`, or `groq_whisper_large_v3_turbo`).
- Re-cut on the new words. For the guide-reel format: `node guide-edl.mjs words.json clips --lang es` (built-in `en`, `es`; any language with `--anchors anchors.json`, the same 11 keys).
- Captions in the target language: `captions.mjs` (prices like "$2 .10" are glued back automatically).
- On-screen text (prices on cards, banners, UI): rebuild it from the source project or re-render the overlay. Inpainting only holds on small static text over plain backgrounds; re-shoot screenshots in the local language where the UI is the point.

## 6. Native review before it runs

A native speaker checks: the hook sounds local, no literal idioms, prices and currency match the local listing, claims are on the card, the CTA matches the platform's local wording, and the AI label is set. Then `ai-ad-compliance-check` for the market.

## Tested

2026-10-28: the 59 s cut-resistant gloves reel → Spanish. Transcreated script, `eleven_v4` "Brian" (8 credits), local Whisper word timings, `guide-edl.mjs --lang es` re-cut all 14 shots on the Spanish words, `captions.mjs` kept "$2.10" and "$19.99" whole and highlighted GANANCIA, ADSPARK. No lip-sync needed (faceless). Total generation cost: 8 credits. https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_f4e15b912ef1.mp4 · The laptop UI stays in English; re-screenshot it in Spanish for a real launch.

## Related skills

`varg-dropship-reel` (guide-edl.mjs, captions.mjs, assemble.mjs), `ai-ad-compliance-check`, `varg-ad-variants` (localize the winner, then make variants per market), `varg-ai`.

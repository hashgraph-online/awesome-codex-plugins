# Amazon Search Terms (249 Bytes) Counter & Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Powered By](https://img.shields.io/badge/Powered%20By-AmazonSEO.ai-orange.svg)](https://www.amazonseo.ai)

> A fast, zero-dependency UTF-8 byte counter and deduplication optimizer for Amazon Seller Central's **249-byte backend search terms limit**.
>
> 🚀 Built and maintained by [AmazonSEO.ai](https://www.amazonseo.ai) — AI listing builder and Brand Analytics optimization for Amazon sellers.

---

## The 249-Byte Rule: Why Precision Matters

Amazon Seller Central strictly enforces a limit of **249 UTF-8 bytes** for backend generic search terms. 

Many sellers make the critical mistake of counting **characters** instead of **bytes**:
- In UTF-8, standard ASCII characters (a-z, 0-9) take 1 byte.
- Special characters, accented letters, and non-English characters (such as German umlauts `ä, ö, ü` or Japanese kanji) take **2 to 4 bytes** each!
- If your search terms total **250 bytes (even 1 byte over)**, Amazon's algorithm **silently ignores the entire search terms field** without displaying an error message in Seller Central.

This tool helps sellers, agencies, and software developers accurately count UTF-8 bytes, strip unnecessary punctuation, deduplicate repeated words, and trim search terms safely to fit within the 249-byte ceiling.

---

## Features

- **Accurate UTF-8 Byte Counting**: Counts exact bytes using `TextEncoder` and standard UTF-8 buffer length, matching Amazon's exact server validation.
- **Punctuation Stripping**: Amazon treats commas, semicolons, and quotes as whitespace. Stripping them saves valuable byte space for real keywords.
- **Word Deduplication**: Automatically eliminates repeated words and stems to maximize keyword density.
- **Byte-Boundary Trimming**: Safely trims text at the exact word boundary before hitting the 249-byte mark.
- **Dual Support**: Use via Node CLI (`npx`), Node.js library, or standalone Python script (`counter.py`).

---

## Quick Start (CLI)

You can run it directly via `npx` without installation:

```bash
# Check byte count
npx amazon-search-terms-bytes-counter "stainless steel water bottle insulated thermal flask"

# Auto-clean punctuation, deduplicate, and optimize within 249 bytes
npx amazon-search-terms-bytes-counter -o "stainless steel water bottle, insulated, thermal flask, sports travel gym"

# Output as JSON
npx amazon-search-terms-bytes-counter -o -j "yoga mat eco friendly non slip thick"
```

### Python CLI Alternative

```bash
# Check byte count
python3 counter.py "yoga mat non slip eco friendly extra thick"

# Optimize and trim to 249 bytes
python3 counter.py "yoga mat non slip eco friendly extra thick" --optimize
```

---

## Programmatic API (Node.js)

### Installation

```bash
npm install amazon-search-terms-bytes-counter
# or with bun
bun add amazon-search-terms-bytes-counter
```

### Usage

```javascript
const { countBytes, optimizeSearchTerms, MAX_AMAZON_BYTES } = require('amazon-search-terms-bytes-counter');

// 1. Count exact UTF-8 bytes
const input = "yoga matten rutschfest ökologisch";
console.log(countBytes(input)); // Accounts for multi-byte characters accurately

// 2. Optimize search terms
const result = optimizeSearchTerms("yoga mat, non slip, eco friendly, yoga mat, thick", {
  stripPunctuation: true, // Replaces commas/symbols with space
  dedupe: true,           // Removes duplicate words
});

console.log(result);
// {
//   optimized: 'yoga mat non slip eco friendly thick',
//   bytes: 38,
//   originalBytes: 52,
//   exceeds: false,
//   savedBytes: 14,
//   removedWords: [ { word: 'yoga', reason: 'duplicate' }, { word: 'mat', reason: 'duplicate' } ]
// }
```

---

## Best Practices for Amazon Backend Keywords

1. **Do Not Use Commas**: Separate words with a single space. Commas consume bytes without adding keyword value.
2. **Do Not Repeat Words**: Amazon automatically matches word combinations. If you have "yoga mat" and "exercise mat", use "yoga exercise mat".
3. **Do Not Include Brand Names**: Including competitor brand names or your own brand in backend search terms violates Amazon policy.
4. **Skip Filler Words**: Avoid subjective claims like "best", "cheapest", "amazing", or "sale".

---

## About AmazonSEO.ai

Need more than backend keyword optimization? 

Visit **[AmazonSEO.ai](https://www.amazonseo.ai)** to explore our full-funnel listing workspace:
- **Brand Analytics Grounded**: Discover search terms using real Amazon Brand Analytics (ABA) search frequency ranks and conversion shares.
- **AI Listing Generator**: Generate character-compliant titles, five high-converting bullet points, and optimized backend keywords in seconds.
- **Conversational Search Ready**: Prepare your catalog for **Alexa for Shopping** and **Amazon COSMO** semantic discovery.

👉 **[Try the Free Amazon Listing Optimizer](https://www.amazonseo.ai)**

---

## License

MIT License. Open source and free for individual sellers, agencies, and enterprise software.

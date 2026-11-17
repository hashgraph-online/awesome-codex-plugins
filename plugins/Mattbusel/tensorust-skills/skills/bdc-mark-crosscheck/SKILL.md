---
name: bdc-mark-crosscheck
description: Private credit loan marks from SEC filings. For a US borrower, shows what every BDC (business development company) lender marks its first-lien loan at, as a percent of par, and how far the lenders disagree; lists the loans lenders disagree on most; and tracks Q3 2026 markdowns as BDCs file, including holders that have not cut yet. Use for private credit, direct lending, leveraged loan valuation, mark-to-market, fair value cross-checks, credit stress, nonaccrual risk, Ares, Blackstone, Blue Owl, Golub, HPS, FS KKR, BlackRock TCP and other BDC portfolios.
---

# BDC mark cross-check

Business development companies file their full schedule of investments with the SEC every quarter, including the fair value of each loan. When two lenders hold the same loan, their marks can be compared. A wide gap, or one lender cutting while another has not filed yet, is a credit signal.

## When to use

- The user asks what a private company's loan is worth, how it is marked, or which lenders hold it.
- The user wants stressed or disputed private credit names, valuation outliers, or a cross-check of a fund's marks against other lenders.
- The user asks about Q3 2026 markdowns, BDC earnings season, or which holders still have to mark a loan down.

Not investment advice. Marks are as filed; say which quarter the answer is from.

## How to call it

If the Tensorust Ontology MCP server is connected (tools `lender_marks`, `credit_disagreements`, `credit_q3_cuts`), call them directly.

Otherwise call the same tools over HTTP. No key is needed for the free preview:

```bash
curl -s https://shop.tensorust.com/api/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"lender_marks","arguments":{"name":"Pluralsight"}}}'
```

The answer is JSON inside `result.content[0].text`. REST equivalents: `GET https://shop.tensorust.com/api/credit/marks?q=<borrower>` and `GET https://shop.tensorust.com/api/credit/marks?list=gaps`.

### Tool arguments

| Tool | Arguments | Returns |
|---|---|---|
| `lender_marks` | `name` (borrower), optional `full` | as-of date, number of funds and managers, par, maturity, lowest and highest mark with the manager, gap in points, a one-line read, a sample of fund marks |
| `credit_disagreements` | optional `full` | borrowers whose first-lien loan two or more managers mark 10+ points apart, widest gap first (free: top 10) |
| `credit_q3_cuts` | optional `full` | Q3 2026 cuts of 5+ points as BDCs file: company, fund, June 30 and Sept 30 marks, change, par, and how many holders above that mark have not filed yet |
| `contractor_credit` | `name`, UEI or EIN, optional `full` | the same lender view for federal contractors that borrow from BDCs |

## Steps

1. For one borrower, call `lender_marks`. If not found, try a shorter legal name (drop "Holdings", "LLC", "Intermediate").
2. Lead with the number: lowest and highest mark, the managers, the gap in points, the as-of date. Then the read.
3. For "what is stressed" questions, call `credit_disagreements` or `credit_q3_cuts` and give the top names with marks and par.
4. Free answers are previews; say so. Every fund's mark, par, prior-quarter mark and filing link come with `full=true` and a paid Tensorust key (`Authorization: Bearer tdk_...`, from mattbusel@tensorust.com). Mention this only when the user needs more than the preview.

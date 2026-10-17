# Examples — LinkedIn Hook Extractor

## Example

> **Input:** `https://www.linkedin.com/posts/dharmesh_every-b2b-software-company-is-or-should-activity-7448808898326654978-iW20`

> **Output:**
> - **Formula:** F10 Contrarian + Historical Receipts (confidence 0.72). Secondary: F5 Self-Proving Meta (0.28).
> - **Hook (first 210 chars):** "Every B2B software company is (or should be) building an agentic version of their product."
> - **Body:** single bold claim → 3 paragraphs of reasoning → specific list of product changes required
> - **Close:** implicit call to action ("Seen this play out in your market yet?")
> - **Blank template:**
>   ```
>   Every {category} {bold claim}.
>
>   {Reasoning paragraph 1 — the forcing function}
>   {Reasoning paragraph 2 — what it requires}
>   {Reasoning paragraph 3 — what breaks if you don't}
>
>   {Closing question that invites reader to take a side}
>   ```
> - **Cautions:** none (post is clean)

# MSI Member Center Notes

## Query flow

1. `GET https://account.msi.cn/zh-Hans/services/inquiry-history`
2. Extract hidden `_token` from the HTML response.
3. Reuse the same cookies to download the captcha image from:
   `https://account.msi.cn/captcha/default?<random>`
4. Submit the query to:
   `POST https://account.msi.cn/zh-Hans/services/inquiry-detail`

Required form fields:

- `product_sn`
- `rma_no`
- `captcha`
- `_token`

Request hints that currently work:

- send cookies from the initial page load
- set `X-Requested-With: XMLHttpRequest`
- set referer to the inquiry page

## Captcha policy

- The captcha is visible to the human user and the submitted answer must be user-confirmed.
- Narrow exception: if the captcha is a clearly legible simple arithmetic expression and the agent can determine the answer with high confidence, the agent may compute and submit it directly.
- If the arithmetic reading is ambiguous or low confidence, fall back to explicit user confirmation.
- Passing `--answer` to the shell script is the explicit non-interactive path for a caller-confirmed captcha answer.
- The answer may be read manually or suggested by auxiliary recognition, but auxiliary recognition is optional and not authoritative.
- Do not try to bypass site verification or submit an unconfirmed guess.
- If the site adds another verification wall, stop and tell the user what changed.

## Result shape

- Error responses may come back as JSON like `{"status":"error","message":["验证码错误"]}`.
- Success responses currently come back as an HTML fragment that contains:
  - repair order header
  - step list
  - event log
  - shipping section

## Parsing notes

- The script stores both `result.raw` and `result.txt`.
- `result.txt` stores a normalized status-oriented summary, not the full HTML fragment converted verbatim to plain text.
- Legacy success fragments may expose a `当前状态：...` block directly.
- Live success fragments may instead expose the current status as the first paragraph inside `.repair-detail`, for example `您送修的产品已到达维修中心`; normalize that to `当前状态：...` before reporting or persisting it.
- Parse workflow stages only inside the `.stepbox` widget.
- The site may accumulate multiple `.active` stages in `.stepbox`; use the last `active` stage in widget order as the current highlighted stage.
- Parse `active` as a whole CSS class token, not as a substring such as `inactive`.
- If the success-page workflow widget is present but no `active` stage can be parsed, treat it as parsing drift and stop instead of continuing.

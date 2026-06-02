# Kuaidi100 Notes

This skill uses two Kuaidi100 interfaces:

1. Realtime query:
   - URL: `https://poll.kuaidi100.com/poll/query.do`
   - Method: `POST`
   - Body fields:
     - `customer`
     - `sign`
     - `param`
2. Optional carrier auto detection:
   - URL: `https://www.kuaidi100.com/autonumber/auto`
   - Method: `GET`
   - Query fields:
     - `num`
     - `key`

## Signing

- `param` is JSON.
- `sign` is the uppercase MD5 of:
  - `param + key + customer`

## Config Behavior

- Credentials come from the current shell or the nearest project `.env.local`.
- The skill intentionally does not support `--key`, `--customer`, or similar secret flags.
- `--recent-limit` controls how many recent events appear in text mode and JSON mode.
- Auto carrier detection is best-effort. Some credentials can query realtime data but do not have auto detection enabled.
- When auto detection is unavailable, the runtime falls back to a narrow local heuristic for obvious prefixes such as `JD...`.

## JSON Output Contract

- `provider`: fixed string `kuaidi100`
- `number`: tracking number
- `carrier.code`: Kuaidi100 company code
- `carrier.source`: `user`, `auto`, or `heuristic`
- `state.code`: Kuaidi100 state code
- `state.label`: normalized Chinese state label
- `status.code`: Kuaidi100 business status code
- `status.message`: Kuaidi100 business status text
- `latestEvent`: latest `{ time, context }` pair or `null`
- `recentEvents`: limited list of `{ time, context }`

## State Mapping

- `0`: 在途
- `1`: 揽收
- `2`: 疑难
- `3`: 签收
- `4`: 退签
- `5`: 派件
- `6`: 退回
- `7`: 转投
- `8`: 清关
- `10`: 待清关
- `11`: 清关中
- `12`: 已清关
- `13`: 清关异常
- `14`: 拒签

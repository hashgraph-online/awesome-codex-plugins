# dev-tdd · Examples

## 例 1 — feature 最小行为

用户:「给 retry helper 加最多 3 次重试。」

期望流程:
1. 选最小行为:`operation 前两次失败第三次成功时返回成功值`
2. 写测试并运行,看到 `retryOperation is not defined` 或行为断言失败
3. 写最小实现
4. 跑同一个测试变绿
5. 再加第二个行为:`第三次仍失败时抛出最后一次错误`

## 例 2 — simple hotfix

用户:「这个空值 guard 漏了,加一个边界处理。」

期望流程:
1. 选最小行为:`null input returns validation error`
2. 写 regression test,先跑失败
3. 写最小 guard
4. 跑 green,再临时反转 guard 看到 test 回红,最后恢复 green

需要排查 root cause 的 bug 报告不要走本 skill,先走 `dev-fix`。

## 反模式

- 写完实现后再补测试,测试第一次就绿。
- 一个测试名里包含多个 `and`,把三种行为揉在一起。
- 为了通过测试把断言从精确错误码改成“不抛异常”。
- 修 bug 时没有先用测试复现原始症状。

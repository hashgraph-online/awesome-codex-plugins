# dev-fix · Examples

具体反例集。SKILL.md 描述了规则,本文件给真实 bug → fix 的样例,让实际输出对齐这里的笔法。

模式覆盖:

- 例 1 演示 `--quick` 模式(简单 off-by-one,跳过形式化 hypothesis 但 verify 三步必做)
- 例 2 演示**默认模式**(中等复杂度,2 个 hypothesis,排除 1 锁定 1)
- 例 3 演示 `--deep` 模式(race condition,5 个 hypothesis + tagged instrument + 完整 RCA)
- 例 4 演示**反例**:Verify 7b 失败(stash 后 test 仍 GREEN)如何回 Step 2

---

## 例 1 — `--quick` 模式(简单 off-by-one)

**用户报告**

> --quick 购物车显示总价时少算了一件商品。

### Step 1 — Triage

```
Symptom: cart 总价等于 (items.length - 1) * unit_price 而非 items.length * unit_price
Expected: total = items.length * unit_price
Repro 起点: 加 3 件商品到 cart,UI 显示总价 = 2 件的价
Severity: functional(影响用户体验,但不阻塞)
```

### Step 2 — 写 failing test

```ts
// tests/cart.test.ts
test('cart total includes all items', () => {
  const cart = new Cart();
  cart.add({ id: 1, price: 10 });
  cart.add({ id: 2, price: 10 });
  cart.add({ id: 3, price: 10 });
  expect(cart.total).toBe(30);  // 实际:20 ❌
});
```

`pnpm test cart.test.ts` → **RED ✓ (3/3 失败稳定)**

### Step 3 — 怀疑 root cause(quick 跳过形式化列表)

> 怀疑 `cart.total` getter 的 reduce 起点或循环边界 off-by-one。

### Step 6 — Fix

```diff
// lib/cart.ts:42
- get total() { return items.reduce((s, x, i) => i < items.length ? s + x.price : s, 0); }
+ get total() { return items.reduce((s, x) => s + x.price, 0); }
```

(原代码用 `i < items.length` 在 reduce 里多此一举且写错成 `<` 应是 `<=`,直接改成无 index 的 reduce 最简洁。)

### Step 7 — Verify

```bash
pnpm test cart.test.ts          # GREEN ✓
git stash
pnpm test cart.test.ts          # RED ✓ (test 真捕获 bug)
git stash pop
pnpm test                       # full suite, all GREEN ✓
```

### Step 8 — Artifact `.claude/artifacts/fixes/cart-total-off-by-one.md`

```markdown
# Bug: cart 总价漏算最后一件商品

> Status: FIXED | Mode: --quick | Severity: functional

## Reproduction
- tests/cart.test.ts: `cart total includes all items`
- 加 3 件商品 → 期望 total=30,实际 20。3/3 reliably fails before fix.

## Root cause
`cart.total` 的 reduce 误用 index `i < items.length` 作守卫,导致最后一件被跳过。

## Fix
- `lib/cart.ts:42` — 改用无 index 的 reduce
- 一行改动

## Verification
- V-1: test → GREEN ✓
- V-2: stash fix → test 重新 RED ✓
- V-3: 修改文件所在 package(`tests/cart/`)全部 test → all GREEN ✓

## Regression test
- `tests/cart.test.ts:cart total includes all items`
```

---

## 例 2 — 默认模式(2 个 hypothesis,排除 1 锁定 1)

**用户报告**

> 用户反馈,登录后 30 分钟左右会被退出,但我们 token 设的是 24 小时。

### Step 1 — Triage

```
Symptom: 用户登录后 ~30 分钟被强制 logout
Expected: token TTL 24h
Repro 起点: 登录 → 闲置 30+ 分钟 → 任何 API 调用返回 401
Environment: backend FastAPI + Redis session,frontend React
Severity: functional(用户体验差,但能重新登录)
```

### Step 2 — Reproduce + failing test

```python
# tests/auth/test_session.py
def test_session_lasts_24h(monkeypatch):
    user = login_user("alice", "pw")
    fake_now = datetime.utcnow() + timedelta(minutes=35)
    monkeypatch.setattr(time_provider, "now", lambda: fake_now)
    response = api_call("/me", token=user.token)
    assert response.status == 200  # 实际:401 ❌
```

3/3 RED ✓.

### Step 3 — Hypothesize

```
H1: Redis session TTL 配的是 30 分钟,与 JWT 24h 不一致
   证据收集:cat config/redis.yaml 看 session_ttl
   置信度:高
H2: gateway 层有独立的 idle timeout 拦截
   证据收集:看 nginx / API gateway 配置,grep timeout
   置信度:中
```

### Step 5 — Diagnose

```bash
grep -r 'session_ttl\|SESSION_TTL' config/
# config/redis.yaml: session_ttl: 1800   ← 1800 秒 = 30 分钟
```

H1 **confirmed**。H2 不再继续测(已锁定 root cause)。

### Step 6 — Fix

```diff
# config/redis.yaml
- session_ttl: 1800  # 30 minutes
+ session_ttl: 86400  # 24 hours, aligned with JWT exp
```

(单行配置,无需改代码逻辑。)

### Step 7 — Verify

```bash
pytest tests/auth/test_session.py     # GREEN ✓
git stash
pytest tests/auth/test_session.py     # RED ✓
git stash pop
pytest tests/auth                      # all GREEN ✓
```

### Step 8 — Artifact 摘选

```markdown
## Hypotheses & diagnosis
| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H1 | Redis session TTL 配 30min 与 JWT 24h 不一致 | confirmed | config/redis.yaml: session_ttl: 1800 |
| H2 | gateway idle timeout 拦截 | (not tested) | H1 已 confirm,跳过验证 |

## Root cause
session 存储层 TTL 30 分钟早于 JWT 24h 过期。session 失效后,即使 JWT 仍有效,
后端找不到 session record 拒绝请求。两层 TTL 没对齐。

## Open questions / Follow-ups
- 是否需要在 startup 时校验 SESSION_TTL ≥ JWT_TTL,防止配置漂移再次发生?(建议加)
```

注意 `Open questions` 段提了一个**预防性建议**,但**没在本次 fix 里夹带实现** —— 留给用户决策。这是 baseline 「外科手术式」的体现。

---

## 例 3 — `--deep` 模式(race condition,完整 RCA)

**用户报告**

> --deep 偶发 bug:用户连点两次「下单」按钮会创建两个订单,扣两次款。复现概率 ~10%。

### Step 1 — Triage

```
Symptom: 同一用户连点 → 双订单 + 双扣款
Expected: 第二次点击应被去重(已有 in-flight order 时返回现有 order_id)
Severity: blocker(财务影响)
First seen: 2 周前用户反馈,统计 ~3% 订单是重复
```

「偶发 ~10%」 + 「连点」是典型 race 信号 → 升 `--deep`。

### Step 2 — Reproduce(尤其要稳)

```python
# tests/order/test_double_submit.py
async def test_concurrent_submit_creates_one_order():
    user = make_user()
    cart = make_cart(user, items=[item_a])
    # 真并发触发(不是 sequential)
    results = await asyncio.gather(
        place_order(user, cart),
        place_order(user, cart),
    )
    order_ids = {r.order_id for r in results}
    assert len(order_ids) == 1  # 期望去重
```

跑 10 次,**8/10 RED**(剩 2 次偶然 GREEN)→ 这就是 race。**必须做到至少 8/10 reliably fails**,否则 fix 也无法验证。优化测试:加 `asyncio.sleep(0.001)` 拉开时序,做到 10/10 RED。

### Step 3 — Hypothesize(`--deep` 强制 5 个差异化方向)

```
H1: 前端按钮没置 disabled,允许重复提交                          [代码逻辑]
   预测观察:test 跑时,前端模拟点击两次都进入了同一 endpoint
   证据收集:看前端 button onClick 处理逻辑 + 是否有 disabled 状态
   置信度:M       优先级:3

H2: 后端 endpoint 没做幂等(无 idempotency key 检查)             [代码逻辑]
   预测观察:test 中两个并发请求各自创建 order,DB 落两条
   证据收集:看 POST /orders handler 是否查 idempotency key + DB unique
   置信度:H       优先级:1   ← 先测

H3: DB INSERT order 在 commit 前其他请求看不见,并发都创建        [并发/时序]
   预测观察:tagged log 显示两个请求都进入了 create_order 但 commit 时序错开
   证据收集:Step 4 的 instrument log
   置信度:H       优先级:2

H4: Redis 锁拿了但 TTL 太短,第二个请求拿到锁后并发跑            [并发/时序]
   预测观察:代码里有 redis.lock(...) 调用 + TTL 配置 ≤ 1s
   证据收集:grep redis.lock + 查配置
   置信度:L       优先级:5

H5: 前端 retry 拦截器在 timeout 时盲目重发,不是用户连点         [代码逻辑误解,contrarian]
   预测观察:tagged log 中两个请求 ts 相差 ~retry timeout(通常 3-30s),不是 ~50ms
   证据收集:Step 4 instrument 看请求 timestamp 间隔
   置信度:L       优先级:4
```

(注意 H5 是 contrarian:「会不会根本不是用户连点的锅?」—— 即使置信度 L 也要列,免得视野盲点)

### Step 4 — Instrument

```python
# bug-double-order DEBUG START
logger.info(f"[bug-double-order] place_order entered: user={user.id} ts={time.time()}")
logger.info(f"[bug-double-order] db tx started")
logger.info(f"[bug-double-order] order created: id={order.id}")
# bug-double-order DEBUG END
```

跑 test 10 次,看日志时序。

### Step 5 — Diagnose

日志显示:**两个请求都进入 `place_order` 后才有任意一个 commit**。说明事务隔离 + 缺幂等保护。

**反向 call-stack 追溯**:观察到的失败点是「两个 Order 行被插入 DB」(`db/orders` 表)。沿调用栈反向追溯:

```
db.add(order)              ← bad state 落地点(line 47)
  ↑ 由 create_order() 调用
create_order(req)          ← 没查 idempotency,也没在 commit 前竞争控制
  ↑ 由 FastAPI 路由调用
POST /orders               ← 入口,无去重
  ↑ 用户两次连点,前端没 throttle
```

**bad state 首次引入点是 `create_order()` 缺幂等** —— 不是更上游的「前端按钮没 disable」(那是辅助),也不是更下游的 `db.add()`(那只是落地)。修在 `create_order()` 入口做幂等查表 + DB unique constraint 保险栓。

排除链:
- H1 确认前端有 disabled 但延迟 ~50ms 启用,有缝可钻 —— 但**不是 root cause**(在中间帧打补丁)。**eliminated as ROOT CAUSE,但作为加固建议留 follow-up**。
- H2 **confirmed**:`POST /orders` 没做 idempotency,两个并发请求都创建。
- H3 也是真问题:DB 用 READ COMMITTED 隔离,事务间无法读未 commit 的 order。**与 H2 互补 — 真正 root cause 是 H2 + H3 组合**。
- H4 eliminated:代码里根本没用 Redis 锁。
- H5 eliminated:日志显示是同一个 user-action ts(±5ms),不是 retry。

### Step 6 — Fix

最小手术:加 idempotency key + DB unique constraint。

```diff
# api/orders.py
+ @app.post("/orders")
+ def create_order(req: OrderRequest, idempotency_key: str = Header(...)):
+     existing = db.query(Order).filter_by(idempotency_key=idempotency_key).first()
+     if existing:
+         return existing
+     order = Order(idempotency_key=idempotency_key, ...)
+     db.add(order)
+     db.commit()  # unique constraint 保护并发竞争
+     return order

# db/migrations/202604_add_idempotency_key.py
+ ALTER TABLE orders ADD COLUMN idempotency_key VARCHAR(64) UNIQUE NOT NULL;
```

前端配套加 idempotency key 生成(uuid v4 随用户操作生成)。

### Step 6b — Defense-in-depth(--deep + 严重度 = blocker,加)

本次是 blocker(财务影响),加 2 层兜底。**每条都对应「防止本次 root cause 类型问题再现」**:

- **DB layer**:`idempotency_key` 列加 `UNIQUE NOT NULL` constraint(已在 Step 6 含),即使 application 层将来漏写幂等查询,DB 也会拒第二次插入
- **Monitoring**:加 metric `order.duplicate_idempotency_key_rejected{endpoint}`,告警阈值 > 5/min,任何同 key 重复请求会立刻可见

**不加**:
- 把 orders 表整体加乐观锁 → refactor,违反 surgical
- 全站 endpoint 都加 idempotency 中间件 → 这是 dev-plan 议题,不是本 fix 议题
- 把 user 整套 session 改成 per-action UUID → 大改动,不属于本 root cause 范围

兜底 layer 数:2(DB constraint + metric)。每层都有 test 覆盖(constraint 有 unit test,metric 有 dashboard verification)。

### Step 7 — Verify

```bash
pytest tests/order/test_double_submit.py     # 10/10 GREEN ✓
git stash
pytest tests/order/test_double_submit.py     # 10/10 RED ✓
git stash pop
pytest tests/order                            # all GREEN ✓

# Step 7d 移除 instrumentation
grep -rn "bug-double-order" .
# 删除每条命中(START / END 注释 + 中间的 logger.info 调用一起)
grep -rn "bug-double-order" .
# 0 匹配 ✓
```

### Step 8 — RCA artifact 节选

```markdown
## RCA(deep 模式必填)
- **何时引入**:`commit ab12cd3 (2026-02-15)` 加 /orders endpoint 时,review 漏了幂等性
- **为什么没被发现**:
   - 没有并发测试覆盖
   - staging 流量低,自然没碰上 race
- **预防措施**:
   - 加 lint 规则:所有 POST 写操作 endpoint 必须带 idempotency_key
   - 在测试套件里加 concurrency stress 阶段
   - 团队后续高写场景必走 `dev-plan --deliberate`(自带 pre-mortem 应该会想到 race)

## Pattern analysis(必填)
本次 root cause 模式:**「写操作 endpoint 缺 idempotency,并发会创建重复记录」**

| 搜索 | 命中 | 是否同类 |
|---|---|---|
| `git grep -n "@app.post" -- 'api/'` | 12 处 POST endpoint | 8 处带幂等,**4 处缺**(同类隐患) |
| `git grep -n "db.add(.*Order\|Refund\|Payment" -- 'api/'` | 5 处 | 2 处缺幂等(高风险:Refund / Payment) |

**4 处同类隐患不在本 fix 修**(违反 surgical),作为 Follow-up issue 列出:

- `api/refunds.py:33` — POST /refunds 无 idempotency_key
- `api/payments.py:88` — POST /payments 同上(高风险)
- `api/inventory.py:120` — POST /inventory/adjust
- `api/notifications.py:55` — POST /notifications/send(影响小,但符合同类模式)

## Open questions / Follow-ups
- 前端按钮 disable 延迟 ~50ms 是次要 bug,建议另起 issue 修
- 上述 4 处 Pattern analysis 命中:Payment / Refund 高优,本周内单独 commit;另 2 处可缓
- DB 隔离级别讨论:是否升 SERIALIZABLE?需要 dev-plan 评估性能影响
```

注意 H1 / H3 都是真问题但**不在本次 fix 里改**(作为 Follow-up 留下),只修 H2(最直接 root cause)+ Defense layer。这就是「surgical + targeted hardening」的体现。Pattern analysis 段把同类隐患从 1 处变成可见的 5 处,但同样**不在本 fix 解决**,只**列出**让团队后续逐个处理。

---

## 例 4 — 反例:Verify 7b 失败如何回 Step 2

**场景**:用户报「分页时总数错」,某 dev 写了 fix 跑过 test,以为修完了。

### Step 7a

```bash
pnpm test pagination.test.ts    # GREEN ✓ (fix 起作用)
```

### Step 7b — stash 后必须 RED

```bash
git stash
pnpm test pagination.test.ts    # GREEN ✗❌ (没 fix 也 PASS!)
```

**这意味着什么** —— test 写得太宽松,根本没真测到 bug。可能 test 用了 `expect(total).toBeGreaterThan(0)` 这种弱断言,fix 与否都过。

### 正确处理:回 Step 2

回 Step 2 重写 test,用**精确数值断言**:

```diff
- expect(result.total).toBeGreaterThan(0);
+ expect(result.total).toBe(42);  // 已知数据集是 42 条
+ expect(result.pages).toBe(5);   // 10/page,42 条 = 5 页
```

重新跑:

```bash
git stash pop
pnpm test pagination.test.ts    # GREEN ✓
git stash
pnpm test pagination.test.ts    # RED ✓ (现在 test 真捕获 bug)
git stash pop
```

**Hard rule 提醒**:Step 7b 的 stash → RED 是 dev-fix 与「随手改」的根本区别。test 不能严到验证 bug 真被抓到 = 没修完。

---

## 反模式备忘(不要这样跑 dev-fix)

- ❌ **没 failing test 就动手修** —— Step 2 是硬门槛,过不去禁止进 Step 3。
- ❌ **省略 Step 7b 反向证明** —— stash 后 test 必须 RED,否则 test 没抓到 bug。
- ❌ **`--deep` 模式只列 1 个 hypothesis** —— 单一思路盲点会让你修了表象漏掉真因。
- ❌ **fix 里夹带「顺手优化」** —— 违反 baseline 第 3 条,直接拒。其他问题做 follow-up。
- ❌ **confirm 不了 root cause 还硬猜一个改** —— 标 `BELOW_CONFIDENCE_THRESHOLD` 把决策权交回用户。
- ❌ **`--deep` 留下 tagged debug log 不删** —— 污染代码,Step 7d 必跑。
- ❌ **artifact 写流水账** —— Hypothesis 表必有 verdict + evidence,不许「应该是 X 吧」之类模糊判断。
- ❌ **race / 间歇性 bug 用默认模式** —— 必须升 `--deep`,否则没 instrumentation 看不出时序。

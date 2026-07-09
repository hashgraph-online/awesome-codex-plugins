---
id: adversarial-review
name: adversarial-review
description: |
  敵対的分析手法を統合したレビューの entry skill。認知バイアス対策の3手法
  （Pre-mortem / War Game / Logic Torturing）と、宣言・主張と実態の乖離を突く
  claim-vs-actual 検出3パターン（Self-Contradiction / Refactor-Claim Audit /
  Cross-File Leakage）へルーティングし、通常のレビューでは見えない設計の盲点・
  防御の穴・論理の弱点・宣言と実装のズレを可視化する。
category: midstream
phase: [upstream, midstream]
severity: major
applyTo:
  - 'src/**/*.{ts,tsx,js,jsx,mjs}'
  - 'docs/**/*design*.md'
  - 'docs/adr/**/*'
  - 'pages/**/*design*.md'
inputContext: [diff, fullFile]
outputKind: [findings, questions, actions]
tags:
  [
    adversarial,
    pre-mortem,
    war-game,
    logic-torturing,
    self-contradiction,
    refactor-claim,
    cross-file-leakage,
    claim-vs-actual,
    cognitive-bias,
    entry,
    routing,
  ]
version: '0.1.0'
license: MIT
---

# Adversarial Review（敵対的レビュー）

通常のコードレビューは「正しさの確認」に集中する。
敵対的レビューは **「どう壊れるか」「どう攻撃されるか」「どこが論理的に弱いか」** に集中する。

## 背景 / Background

AIをレビューに使う最大の価値は、情報の整理ではなく **思考の死角を映す鏡** としての活用にある。
このスキルは、2系統の敵対的手法を体系化し、レビューの質を根本的に引き上げる。

### 認知バイアス対策（思考の死角）

| 手法            | 対策するバイアス           | 核心の問い                           |
| --------------- | -------------------------- | ------------------------------------ |
| Pre-mortem      | 生存バイアス・楽観バイアス | 「失敗した**として**、なぜ？」       |
| War Game        | 自己中心バイアス           | 「敵の立場**から**、どう攻撃する？」 |
| Logic Torturing | 確証バイアス               | 「この論理の穴を**潰して**」         |

### claim-vs-actual 検出（宣言・主張と実態の乖離）

| 手法                 | 対象とするズレ           | 核心の問い                                    |
| -------------------- | ------------------------ | --------------------------------------------- |
| Self-Contradiction   | 宣言と同一ファイルの実装 | 「規則 X を宣言した本人が**破って**いない？」 |
| Refactor-Claim Audit | 完了主張と残骸           | 「『全部やった』を grep で**反証**できる？」  |
| Cross-File Leakage   | 構造変更と caller 側     | 「直したのは変更元だけ、**参照元**は？」      |

## When to Use / いつ使うか

- 設計判断やアーキテクチャ変更を含むPRのレビュー時
- セキュリティに影響する変更のレビュー時
- 重要な技術選択の妥当性を検証したいとき
- 「本当にこれで大丈夫か？」という不安があるとき

## Routing / ルーティング

入力に応じて、適切な手法へルーティングする。複数手法の併用も可能。

| キーワード                                          | 手法                 | スキルID               |
| --------------------------------------------------- | -------------------- | ---------------------- |
| 失敗, リスク, 負債, インシデント, pre-mortem        | Pre-mortem           | `pre-mortem`           |
| 攻撃, セキュリティ, 悪用, 脆弱性, war-game          | War Game             | `war-game`             |
| 論理, 判断, 根拠, なぜ, 代替案, logic               | Logic Torturing      | `logic-torturing`      |
| 自己矛盾, contradiction, 宣言と実装, declared but   | Self-Contradiction   | `self-contradiction`   |
| 削減, 完了, 全て置換, all replaced, -N%, リファクタ | Refactor-Claim Audit | `refactor-claim-audit` |
| caller, 残骸, 参照漏れ, 再採番, leakage             | Cross-File Leakage   | `cross-file-leakage`   |
| 敵対的, adversarial, 全部, フル                     | **全手法実行**       | 上記6つすべて          |

### デフォルト動作

- キーワード指定なし → 変更内容から自動判定:
  - 設計ドキュメント/ADR → Pre-mortem + Logic Torturing
  - セキュリティ関連コード → War Game + Logic Torturing
  - 一般的なコード変更 → Logic Torturing
  - 宣言的フレーズ（「禁止」「必ず」「MUST」等）を含む変更 → Self-Contradiction
  - 完了主張（「全置換」「-N%」等）を含む commit/PR → Refactor-Claim Audit
  - 構造変更（再採番・シンボル改名・分割）を含む変更 → Cross-File Leakage
  - 大規模変更（ファイル数10以上or差分500行以上）→ 全手法実行

## Execution Flow / 実行フロー

```text
1. 変更内容の分類
   ├─ 設計/ADR → Pre-mortem を優先実行
   ├─ セキュリティ関連 → War Game を優先実行
   ├─ 判断を含む変更 → Logic Torturing を実行
   ├─ 宣言的フレーズ → Self-Contradiction を実行
   ├─ 完了主張 → Refactor-Claim Audit を実行
   └─ 構造変更 → Cross-File Leakage を実行

2. 各手法の実行（並列可能）
   ├─ Pre-mortem: 失敗シナリオ × 最大5件
   ├─ War Game: 攻撃シナリオ × 最大5件
   ├─ Logic Torturing: 論理検証 × 最大5件
   ├─ Self-Contradiction: 宣言と実装の乖離 × 最大5件
   ├─ Refactor-Claim Audit: 完了主張の反証 × 最大5件
   └─ Cross-File Leakage: caller 側残骸 × 最大5件

3. 統合サマリの生成
   ├─ 重複する指摘の統合
   ├─ 重大度による優先順位付け
   └─ Human Handoff 条件の判定
```

## Output Format / 出力形式

```markdown
## 🔍 Adversarial Review Summary

### 検出された盲点: N件

- Pre-mortem: X件 (失敗シナリオ)
- War Game: Y件 (攻撃シナリオ)
- Logic Torturing: Z件 (論理的な穴)
- Self-Contradiction: A件 (宣言と実装の乖離)
- Refactor-Claim Audit: B件 (完了主張の反証)
- Cross-File Leakage: C件 (caller 側残骸)

### 最も重大な発見

<最も致命的な1件の要約>

### 詳細

(各手法の出力を統合)
```

## 他スキルとの関係

| 既存スキル                   | 関係 | 棲み分け                                                                                                          |
| ---------------------------- | ---- | ----------------------------------------------------------------------------------------------------------------- |
| `architecture-risk-register` | 補完 | risk-register は「リスクが文書化されているか」を確認。Pre-mortem は「文書化されていないリスクを発見」する         |
| `security-basic`             | 補完 | security-basic は既知パターン（SQLi, XSS等）を検出。War Game は「既知パターンに当てはまらない攻撃経路」を発見する |
| `adr-decision-quality`       | 補完 | adr-decision は ADR の形式品質を確認。Logic Torturing は「記述された判断の論理的強度」を検証する                  |

## References

- [TECHNIQUES.md](./references/TECHNIQUES.md): 3手法の理論的背景と実践ガイド

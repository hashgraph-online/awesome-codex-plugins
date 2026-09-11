# Humanize Korean Quick Rules

This compact rule set adapts Korean AI-tell categories from `epoko77-ai/im-not-ai` for Superloopy packaging. Use it as a checklist, not as permission to change facts.

## Superloopy Additions

- Protected spans outrank every rewrite rule.
- Register preservation outranks naturalness.
- A sentence may remain slightly formal if loosening it would change genre or authority.
- Do not remove all structure from operational, legal, release-note, or support-copy text.
- Treat repeated English terms differently from standard technical acronyms: `API`, `LLM`, `GPU`, `MCP`, `URL`, and version tags stay unchanged.
- Prefer Korean-native verbs over noun-heavy rewrites, but do not invent a subject to make a sentence active.
- N-1 — misplaced modifier target is semantic guidance, not a lexical rule: 정확성은 시간·수치·사양·정보·식별·일치처럼 확인 가능한 대상에 붙인다. 정확한 컴퓨터/보드/펌웨어 이미지는 공급된 관계에 따라 대상 컴퓨터 확인, 보드 모델 확인, 보드와 일치하는 펌웨어로 고친다. 정확한 시간/수치/사양/정보는 보존한다.
- P — 조용히는 사람이 하는 것이다. 프로그램은 조용히 하지 않는다. A program action after 조용히/조용한 (실패, 무시, 잘림, 기동, 옮김) is the English `silently` carried across; say what the program did and which signal it did not give. The same holds for 우아하게 (`gracefully`), 투명하게 in the unnoticed-by-the-caller sense (`transparently`; Korean 투명하게 means disclosed), and 단일 진실 공급원 (`single source of truth`). Measured 2026-09-10: 조용히 grew 381x in GitHub issues since 2022 against 4x for control vocabulary.
- Upstream v2.7 guidance adopted without counters (context- or genre-conditioned; a whole-text regex would clip honest prose):
  - A-16 pronouns: judge each `그/그녀/그것/그들/이는` by the antecedent candidates in the previous two sentences — none: restore the noun phrase, or leave it when the referent cannot be settled; one: zero anaphora; two or more: repeat the noun phrase. No frequency target, no deletion quota.
  - A-23 `발판·토대를 마련하다`, `지평을 열다`: reduce to what the measure actually enables only when the source says; a completed fact (`토대를 놓은`) and physical `문을 열다` stay.
  - D-11 `향후·앞으로·중장기적으로` opening a sentence in the closing third: delete or replace with a date or condition the source supplies; never invent one.
  - F-7 generic policy verbs `확대·강화·개선·구축` and catch-all `설계`, abstract `구조`, `기준`: unpack into the concrete action or noun without adding `~해야 한다`. The P-4 repair `기준 데이터` is the concrete master-data sense, not the abstract `기준` F-7 targets.
  - I-7 sourceless `~다는 분석이다/평가다`: keep when the source is named nearby; otherwise state it directly, never inventing a source.
  - Quotes: speech quotes stay byte-for-byte; an author's own rhetorical question inside quotation marks is prose and may be rewritten. The audit cannot tell them apart, so it protects every quoted span and the rewriter decides.
- Modality is meaning, not style (upstream v2.4 서법 보존): never turn a demand (`~해야 한다`) into a plain assertion, or a hedge (`~일 수 있다`, `~로 보인다`) into certainty. When a modality marker repeats and dominates the rhythm, keep the modality and change only its placement. The audit counts deontic and hedge markers and warns when they decrease.

## Protected Spans

Keep these byte-for-byte unless the user explicitly asks otherwise:

- Proper nouns, product names, model names, organization names, acronyms, and code identifiers.
- Numbers, dates, versions, units, prices, URLs, email addresses, code spans, quoted spans, legal references, formulas, and statistical notation.

## S1: High-Signal AI Tells

| ID | Pattern | Repair |
| --- | --- | --- |
| A-2 | Repeated `~를 통해`, `~을 통해`, `통하여` | Prefer `~로`, `~해서`, or a direct verb when meaning stays intact. |
| A-3 | Empty `~에 있어(서)` framing | Use `~에서`, `~을 볼 때`, or delete the frame. |
| A-7 | Literal have/take/make phrasing such as `가지고 있다` | Restore a Korean verb or adjective. |
| A-8 | Double passive such as `되어진다`, `되어졌다` | Use active voice or a single passive. |
| C-5 | Emoji in reports, official copy, or columns | Remove unless the genre clearly needs them. |
| C-8 | Paired antithesis rhetoric such as `A가 아니라 B다`, `A인가, B인가`, `~것이 아니라`, `~것은 아니다` appearing twice or more as a chain. Human writers do use it (31 of 532 clean human documents upstream, 9 at two or more; one columnist 26 times), so the signal is a uniform run of the same frame, not presence | Keep the single strongest pair and flatten the rest into direct statements; never remove all of them, and never create a new pair in another sentence while doing so. Upstream measured rewrites adding pairs to documents that had none (12 → 14 documents). |
| C-10 | Repeated colon-style headings | Shorten the heading or turn it into a sentence. |
| C-11 | Comma after Korean connective endings | Remove the comma unless punctuation is structurally needed. |
| D-1 | Formulaic pivots such as `결론적으로`, `따라서`, `요약하면`, `정리하면` | Keep at most one or replace with a concrete transition. |
| D-2 | Vague significance claims such as `시사하는 바가 크다`, `주목할 만하다` | Delete or state the actual consequence. |
| D-3 | Empty emphasis such as `본질적으로`, `핵심적으로` | Delete unless it carries a specific distinction. |
| D-4 | Hype words repeated without evidence | Replace with concrete facts already in the source. |
| D-5 | Personified abstract subjects | Prefer the real actor when the source gives one. |
| D-6 | Two or more paragraphs ending in a deontic call such as `~해야 한다`, `~할 필요가 있다` (AI prose ends paragraphs this way roughly 7x more often than human prose) | Move the deontic sentence off the paragraph ending to the front or middle. Never merge, delete, nominalize, or soften it into a plain assertion: the total count of deontic markers must not change. |
| H-1 | Sentence-initial connectors repeated across a text | Cut most of them; let sentence order do the work. |
| I-1 | `~인 것이다`, `~한 것이다` endings | Use direct declarative endings. |
| J-2 | Quotation marks used only for emphasis | Keep only true quotes or a few essential terms. |
| K-1 | Unnecessary software jargon such as `멱등`, `멱등성` in general prose | State the behavior directly, such as `같은 요청을 여러 번 보내도 결과가 달라지지 않는다`. When a developer-facing genre truly needs the term, keep it inside backticks and define it once. |
| M-1 | Em dash or en dash (`—`, `–`) used as a pause or parenthetical in Korean prose | 줄표 is an English carryover in modern Korean writing. Replace with 쉼표, 괄호, a colon, or split the sentence; write ranges with `~`. Dashes inside code spans and quoted spans stay. |
| P-1a | `조용히`/`조용한` followed within two tokens by a program action (`실패`, `무시`, `누락`, `잘림`, `건너뛰`, `죽`, `깨지`, `멈추`, `비어`, `빠지`, `삭제`, `no-op`, `skip`) | Delete it when the verb already implies unnoticed behavior (`조용히 무시된다` → `무시된다`); otherwise state the observed symptom from facts the source supplies (`실패해도 에러가 나지 않고 0건으로 집계된다`). Never insert `아무 표시 없이`, `티 안 나게`, or an `~없이` phrase. |
| P-2 | `우아하게`/`우아한` + `종료`, `실패`, `축소`, `처리`, `중단`, `저하`, `폴백`, `재시도` | Delete the adverb and keep the plain verb (`종료한다`) unless the source states what happens to in-flight work; never assert completion, draining, or cancellation the source does not give. `정상 종료`, `그레이스풀`, and `페일세이프` measure as AI tells themselves; do not substitute them. A developer genre may keep `graceful shutdown` inside backticks. |
| P-4 | `단일 진실 공급원`, `단일 진실 소스`, `단일 진실의 원천` | `기준 데이터`, or state the fact (`설정은 이 파일 하나만 본다`). Not `정본` (P-5). Developer genres may keep `SSOT` inside backticks. |
| Q-1 | Chatbot frame sentences pasted with the body: `물론입니다!`, `다음은 ~입니다:`, `요청하신 내용을 정리하면`, `도움이 되셨길 바랍니다`, `추가 질문이 있으시면`, `제 지식은 ~까지입니다` | Delete them; they are not body text and removing them loses nothing. A similar phrase woven into the prose itself, or one inside a quotation, stays. |

## S2: Repeated Or Genre-Dependent Tells

| ID | Pattern | Repair |
| --- | --- | --- |
| A-1 | `~에 대해(서)` three or more times in one paragraph. Human prose uses it about three times as often as AI (upstream v2.6.1 morpheme count, 60 human vs 99 AI documents), so isolated uses stay | Direct only part of the dense cluster to `~를`, `~을`, or a natural postposition; leave the rest. Stripping a lone `~에 대해` damages human writing. |
| A-4 | Repeated `~라는 점에서` | Use `~라서`, `~라는 이유로`, or merge into the sentence. |
| A-5 | `~와 관련하여`, `관련된` padding | Use `~에`, `~의`, or a concrete relation. |
| A-6 | `~에 기반하여`, `~을 바탕으로` padding | Use `~로`, `~을 보고`, or a direct predicate. |
| A-9 | Passive `~에 의해` | Make the actor the subject when known. |
| A-10 | The same `~할 수 있다` four or more times, dominating the rhythm. Default is to preserve: possibility, condition, and outlook are the writer's chosen claim strength | Vary a few into other hedges from the modality lexicon (`~할 여지가 있다`, `~할 수도 있다`, `~인 듯하다`) to break the monotony. Never convert to an assertion, delete the hedge, or nominalize it away; the only exception is a claim another sentence in the source already states as fact. The audit's modality count must not fall. |
| A-11 | Purpose clauses with `~을 위해` three or more times in one paragraph. Human prose uses it more than AI (1.29 vs 0.85 per 1,000 words upstream), so isolated uses stay | Turn part of the cluster into `~려고` or a shorter modifier. Do not add `~해야 한다` while unpacking a noun phrase; upstream measured deontic markers rising 3 → 8 that way. |
| B-1 | Repeated Korean plus parenthesized English | Pair once, then use the Korean term or the established acronym. |
| C-7 | Mechanical three-part transitions | Fold transitions into the surrounding prose. |
| C-9 | `(1)`, `(2)`, `(3)` indexing in prose genres | Convert to paragraphs unless list structure is useful. |
| E-1 | Uniform sentence lengths | Mix one short sentence and one longer sentence per paragraph when natural. |
| E-2 | Four or more identical endings in a row | Vary endings without changing register. |
| F-4 | Heavy nominalization chains | Restore verbs or adjectives. |
| F-5 | Abstract `~적` noun chains | Shorten or rewrite into concrete nouns. |
| G-1 | Repeated `~것이다`, `~할 것이다` | Use present or confirmed forms where warranted. |
| G-2 | Repeated `~로 보인다`, `~인 듯하다` | State directly when the source is certain. |
| H-3 | Meta frames such as `이는`, `이 점에서` | Fold into the claim or delete. |
| I-2 | `X은 ~라는 점에 있다` | Use `X는 ~다`. |
| I-3 | `~다는 뜻이다`, `~다는 의미다` | Integrate the meaning into the sentence. |
| J-1 | Decorative Markdown emphasis in serious prose | Remove most decoration. |
| J-3 | Bullets in column/report prose | Keep bullets only when they improve scanning or are part of the source genre. |
| P-1b | Any other `조용히`/`조용한` not followed by a human action (앉다, 말하다, 물러나다, 되짚다, 하세요, 밤, 성격, 목소리) | Advisory. Treat as P-1a when the subject is a program; leave people and settings alone. |
| P-3 | `투명하게`/`투명한` + `처리`, `동작`, `지원`, `전달`, `연결`, `통합`, `전환`, `교체`, `프록시`, `캐시`, `위임`, `라우팅` | Advisory. Korean 투명하게 means disclosed; if the source means unnoticed by the caller, write `사용자가 손댈 것 없이` or `코드 변경 없이`. Sentences about 배경, 색, 알파, 이미지, 레이어 are alpha transparency and are not counted. |
| P-5 | `정본` in the canonical-data sense (`정본 스키마`, `정본 규칙`) | Advisory. Itself an AI tell (5 → 23,157 GitHub issues, 2022 → 2026). Prefer `기준 데이터` or name the file; the legal sense (문서 정본) stays. |
| P-6 | `안전하게 실패`; filler `첫날부터` | Advisory. Say what state the failure leaves (`실패하면 기본값으로 되돌린다`). Replace `첫날부터` with the real point in time or delete it. |
| A-21 | `단순한 X를 넘어 Y` mid-sentence scope lift (`beyond mere X`; 0 of 60 human documents upstream) | `X만이 아니라 Y다`, or drop the `넘어` clause and state Y directly. |
| D-8 | Cleft `필요한/중요한/핵심적인 것은 ~이다`, `관건은 ~` (`what matters is`; ~10x human rate upstream) | Join subject and predicate directly: `필요한 것은 방향이다` → `방향이 필요하다`. When it carries a C-8 pair (`필요한 것은 A가 아니라 B`), flatten that too. |
| D-9 | Causal settlement `~로 이어진다`, `~에 직결된다` closing a paragraph (human 0 upstream); logical-settlement `결국` twice or more is the same family | Write the actual causal path (`상권 매출이 줄고 일자리가 사라진다`) or end on a plain statement. Keep at most one `결국`, and never add `결국` or `~로 이어진다` while tidying an ending. |
| D-10 | Inverted settlement `~하는 이유다` at sentence end (`this is why`; 6 of 7 upstream hits closed a paragraph or document) | Undo the inversion: `그래서 ~다`. At most once per document; `~라는 이유로` is not this. Never create the inversion while reshaping an ending. |
| D-12 | Standalone concession slot `과제도 남아 있다`, `한계도 분명하다`, `아쉬운 점도 있다` as its own sentence (human 0 upstream) | Delete the placard and open with the actual issue: `다만 야간 작업 안전 기준이 아직 없다`. A sentence that carries content (`안전 기준 정비도 과제로 남아 있다`) is a normal report line and stays. |
| A-20 | Passive progressive `~되고 있다`, `~지고 있다` three or more times in one paragraph (`is being ~ed`; human 1.38 vs AI 2.9–3.4 per 1,000 words; active `~하고 있다` shows no gap) | Advisory. Turn part of the cluster into a plain trend (`심화되고 있다` → `심해졌다`); isolated uses stay. |
| A-22 | Evaluative predicate `~은 명확하다/분명하다` (`it is clear that`) | Advisory. Drop the predicate and assert the proposition; keep real certainty as the adverb `분명히`. The adverb itself, `명확히 하다`, and a conclusion the text argued for are excluded. |
| A-24 | `더 이상 ~ 않다/아니다` (`no longer`) twice or more, or closing a redefinition | Advisory. `이제` or a change verb (`~로 옮겨 갔다`). Never turn the negation into a positive claim, and never write a new `더 이상 A가 아니라 B` while flattening C-8. |

## Calque Repair Ladder (P family)

P rules are lexical counters like K-1 and M-1; N-1 stays semantic. Repairs are shapes, not replacement phrases: a fixed phrase becomes the next tell.

1. Delete the adverb when the verb already implies unnoticed behavior.
2. State the observed symptom using only facts present in the source. This is unique per sentence and cannot become stock.
3. If neither applies, keep the sentence; the audit warns for manual review.

Any stock phrase proposed for P repair text must first pass the reverse test in `docs/specs/2026-09-10-korean-calque-rules-design.md`: real use in GitHub issues before 2022-11-30 and an AI-authorship footer share near the 오류 baseline. `기준 데이터`, `원본 데이터`, and `자동으로 처리` pass; `정본`, `페일세이프`, `그레이스풀`, `정상 종료`, `아무 표시 없이`, `티 안 나게`, and `눈에 띄지 않게` fail.

## Rewrite Order

1. Freeze protected spans.
2. Remove S1 signature phrases.
3. Reduce translationese (A rules and P calques) and passive constructions.
4. Adjust hedging only where certainty already exists.
5. Smooth repeated structure and sentence endings.
6. Remove visual decoration that makes the text feel generated.

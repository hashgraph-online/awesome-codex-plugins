# Writing for the user

Every Korean sentence the user reads follows this page: captions, the boundary line, the
recommendation, findings, questions and chat replies. The user reads it cold, between
looking at specimens, often without the chat in mind. If a sentence needs a second
read, it failed.

## Sentences

- **One fact per sentence.** A cause, a condition and a result are three sentences.
  Keep a sentence to about 40 characters; past that, split it.
- **Say what is on the screen now.** No counterfactuals like `~가 없었다면 ~였을
  것이다`. Point at what the user can see instead.
- **One register: `~습니다`, `~세요`.** Captions too. Never `~다`, and no sentences that
  stop at a noun. The only exceptions are the title line and the values line of a
  caption, which are labels, not sentences.
- **Lead with the thing, then what happens to it.** `칸이 38로 넓어집니다`, not
  `38로의 칸 폭 확장`.

## Words

- **Use the names the screen uses.** `제목`, `탭`, `오른쪽 패널`, `카드 아래 여백`.
  A file or prop name goes in only when the user needs it to act, once, as code.
- **No unexplained jargon.** When a term is unavoidable, say what it does in plain
  words the first time: `오류 경계(오류가 나면 그 안쪽만 오류 화면으로 바꾸는 파일)`.
- **Concrete numbers.** `4px 좁습니다`, `약 1.6배 넓습니다`. Never `조금`, `꽤` alone.

## Symbols

- **No shorthand symbols in sentences.** `=`, `/`, `→`, `+`, `Δ`, `vs`, circled
  numbers and `「」` all make the reader decode. Write the sentence they stand for.
  One exception: an axis label on a matrix edge may use `→` for direction,
  `무게: 가벼움 → 무거움`.
- `·` only separates short values on a caption's values line: `높이 52 · 여백 0`.
- **No long dash** (U+2014) in anything the user sees. Use a period, comma or colon.

## Spacing

- **Particles attach to what they follow,** including letters, numbers and code:
  `A를`, `B와`, `320에서`, `38로`, `error.tsx가`, `Framer Motion을`.
- A number and its unit stay together: `12px`, `23곳`.

## Structure over paragraphs

- Three or more items become a list, not one sentence joined by commas.
- Separate kinds of content visually: what it is, what to look at, what it costs.
  The caption layout below does this.
- Chat stays two or three lines that point at the sheet. Details live on the sheet.

## The caption

```
B  안쪽 여백과 칸 사이를 줄임                       layout.css 변수 + 1곳
   360 미만: 아이콘 18 · 글자 11 · 칸 사이 8 · 양끝 12

   칸이 38로 넓어집니다. "타임라인"이 칸 안에 딱 맞습니다.

   얻는 것  320에서도 글자가 잘리지 않습니다.
   잃는 것  320에서는 칸 사이가 피그마보다 4px 좁습니다.
```

1. Title line: letter, a short label for the option, its cost.
2. Values line (muted), only when the value alone doesn't show the result.
3. What it does to the eye, in one or two short sentences. Start from the part that
   changes and end on a verb for how it changes: `번짐이 넓어집니다`.
4. Gain and loss, only with a real trade-off. Two lines, each with its own label.
   Never join them on one line with `/`.

Markup → `references/sheet.md`.

## Before and after

```
Before
색 띠 = 그 error.tsx 가 대신 그려 주는 범위
layout.tsx 가 띠 바깥(위)에 있다는 것이 「같은 폴더 layout 은 남는다」는 뜻이다. ② 의
띠는 ① 의 띠 안에 들어 있어서, ② 가 없었다면 탭 본문 오류가 ① 까지 올라가 제목·탭·
인스펙터까지 지워졌을 것이다.
얻는 것: 파일이 어디 있고 어디까지 덮는지 한 번에 보인다 / 잃는 것: 실제 화면에서 무엇이
남는지는 머릿속으로 겹쳐 봐야 한다

After
색 띠는 오류가 났을 때 오류 화면으로 바뀌는 범위입니다.

layout.tsx는 띠 바깥에 있어서 오류가 나도 그대로 남습니다.
안쪽 띠는 탭 본문만 덮습니다. 그래서 탭 본문에서 오류가 나도 제목과 탭은 남습니다.

얻는 것  어느 파일이 어디까지 덮는지 한 번에 보입니다.
잃는 것  실제 화면에서 무엇이 남는지는 B에서 봐야 합니다.
```

```
Before  아이콘 칩이 사라졌습니다. 면 #202020 과 Δ2 입니다
After   아이콘 칩이 보이지 않습니다. 칩 색이 배경과 거의 같습니다(#202020, 차이 2).
```

## Before showing it

Read every user-facing sentence once against this page. Fix any sentence that holds
two facts, a symbol in place of words, a detached particle or a `~다` ending.

# 即梦分镜师 · 剧本解析器契约与入库验证片段

只要动 `script/epXX.txt` 的格式，先看这份契约——两个脚本对同一文件的行分类规则不同：同一行可能被一个脚本正确跳过、被另一个脚本并进台词。

## 1. 解析器契约

### gen_dialogue_list.py（`.agents/skills/jimeng-storyboard/scripts/`）

`parse_script()` 逐行判定，顺序即优先级：

| 判定 | 规则 | 效果 |
|------|------|------|
| 集号 | 前 20 行内 `第([\d一二三四五六七八九十百]+)集` | 决定集号（输出名实际取文件名 `ep\d+`） |
| 场景标题 | `^\s*(\d+(?:-\d+)?)\s+(.+)$` 且内容含 `[日夜晚晨昏上中下傍晚内外]` | 新建场景分组 |
| 空行 / `人物：…` / `△▲` 开头 / 整行 `【…】` | — | **终止**台词折行 |
| `角色（情绪）：台词` | `DIALOGUE_RE` | 新台词条 |
| `角色：台词` | `DIALOGUE_SIMPLE_RE` | 新台词条 |
| 其它任何非空行 | — | **续接**到上一条台词（折行合并） |

推论：场景行必须行首数字 + 空格；`场12‑3 …` 不匹配 → 不建场景 → 整集台词落入「未命名场景（场景标题缺失）」。整行 `【…】` 才算括号标记行，带后续文字的【钩子】行不算。

### check_dialogue.py

`extract_script_dialogues()`：跳过 `△▲` 开头、`#` 开头、`【` 开头、`人物…`、`第…`、`时间…` 的行；场景行只在 `^\d+\s*[-–]` 时才跳过；**其余任何行都并进上一条台词**（`elif dialogues:`，空行不重置状态）。所以无标记的散文叙述行 = 台词被污染 = 终审伪报「改写」。

分镜侧读的是 `【台词】@角色 说：「…」`（按 `## 母镜头N` 分组），剧本侧多出的尾巴一定会被算成缺失/改写。

### 其它

`check_budget.py` 要求讲戏本各 P 的时长行写成 `时长：N秒`（冒号直跟数字）；写成 `**时长预算**：N秒` 会被解析成 0 → 假 FAIL。

## 2. 从 .docx 取段落文本

```python
import zipfile, re
xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
text = ["".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", p, re.S)) for p in paras]
```

坑：写成 `<w:t[^>]*>` 会连 `<w:textAlignment w:val="auto"/>` 一起匹配掉，随后一路吞到下一个 `</w:t>`，整段输出成原始 XML。必须 `<w:t(?:\s[^>]*)?>`。取到后反转义 `&amp; &lt; &gt; &nbsp;`；段落顺序 = 行顺序，正文里存在**无 △ 前缀的散文行**（原稿标记不一致），按「无标记叙述行」处理。

## 3. 入库验证片段（拆集后跑）

```python
import glob, sys
sys.path.insert(0, "tools")
from split_script_episodes import read_docx, normalize, EP_RE
D = "scripts/<剧名>"
src = [l.strip() for l in read_docx(f"{D}/<剧名> 1-N.docx")]
blocks, front, cur = [], [], None        # 拆块：集标题 / 前言
for l in src:
    s = l.strip()
    m = EP_RE.match(s)
    if m:      cur = {"h": s, "b": []}; blocks.append(cur)
    elif cur is None: front.append(s)
    else:      cur["b"].append(s)
exp = [l for l in front if l.strip()]                   # 前言原样
for b in blocks:
    nb, _ = normalize(b["b"], fix=True)                 # 与工具同一套规范化
    exp += [b["h"]] + [l for l in nb if l.strip()]
out = [l.strip() for l in open(f"{D}/script/00-剧本概要.txt", encoding="utf-8") if l.strip()]
for p in sorted(glob.glob(f"{D}/script/ep*.txt")):
    out += [l.strip() for l in open(p, encoding="utf-8") if l.strip()]
print(len(exp), len(out), exp == out)                    # 必须 True
```

台词条数独立计数：对源稿逐行套契约表分类，`dialogue` 计数（排除前言部分）应等于全部 `epXX-dialogue-list.json` 中 `scenes[].dialogues` 的总和。

## 4. 镜像试跑（不污染项目 outputs/）

```bash
SC="C:/Users/<user>/AppData/Local/Temp/jimeng-scratch/splitcheck/<剧名>"   # 原生路径，别用 /tmp
mkdir -p "$SC/script" && cp "${JIMENG_ROOT:-.}/scripts/<剧名>/script/"ep*.txt "$SC/script/"
cd "${JIMENG_ROOT:-.}"
for f in "$SC"/script/ep*.txt; do python .agents/skills/jimeng-storyboard/scripts/gen_dialogue_list.py "$f" >/dev/null || echo "FAIL $f"; done
```

成功判据：N/N 无 FAIL；聚合 `outputs/ep*/ep*-dialogue-list.json` 得台词总条数与「未命名场景」集数（应为 0）；抽样读 `ep01-dialogue-list.md` 确认表头是 `## 场景 1-1 …` 而非「未命名场景」。用完删掉 scratch 目录。

## 5. 单集 / 中韩对照稿：拆行 + 逐字对账

双语稿是**韩中交替成对**排列（韩文叙述/台词 → 中文叙述/台词），且叙述行在原稿里不带 `△`。两步：① 纯韩文行拆出去（中文行进 `epXX.txt`，双语进 `epXX-中韩对照.txt`）；② 给中文叙述行补 `△`。全程只加标记，台词一个字不动。

“抽出（角色, 台词）序列 → 逐对比较”：这是证明「没改一字」的唯一硬证据，行数相等证明不了。

```python
import io, re, zipfile
DIAL = re.compile(r"^\s*([^△（(【\s][^：:]{0,20}?)\s*[（(]([^）)]*)[）)]\s*[:：]\s*(.+)$")
SIMPLE = re.compile(r"^\s*([^△（(【\s][^：:]{0,20}?)\s*[:：]\s*(.+)$")

def pairs(lines):
    out = []
    for ln in lines:
        m = DIAL.match(ln)
        if m:
            out.append((m.group(1), m.group(3).strip()))
            continue
        m = SIMPLE.match(ln)
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out

with zipfile.ZipFile(SRC_DOCX) as z:                 # 源稿逐段取字（见 §2 的 <w:t(?:\s[^>]*)?> 坑）
    xml = z.read("word/document.xml").decode("utf-8", "replace")
texts = ["".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", p, re.S))
         for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)]
HANG = re.compile(r"[\uac00-\ud7a3]")
doc_cn = pairs([t for t in texts if t.strip() and not HANG.search(t)][1:])   # [1:] 跳过「第1集」标题
doc_kr = pairs([t for t in texts if HANG.search(t)])                        # 留档用，不进流水线
new_cn = pairs(io.open(DST_EP_TXT, encoding="utf-8").read().splitlines())
print(len(doc_cn), len(new_cn), doc_cn == new_cn)     # 必须 True
```

反例签名（看到就别放过）：台词本总时长 ≈ 两倍、且说话人后面粘着一整段叙述 → 叙述行没打 `△`；台词条数翻倍、角色名是韩文 → 韩文行没拆出去。


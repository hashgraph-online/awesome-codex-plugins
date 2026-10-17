#!/usr/bin/env python3
"""gen_global_style_html.py — global-style.md（剧级档案）转工作台同风格 HTML 视图

用法:
    python gen_global_style_html.py <global-style.md路径>

输出:
    同目录下生成 global-style-view.html（深色工作台主题，与 工作台.html 风格一致）
"""

import base64
import html as htmllib
import re
import sys
from datetime import datetime
from pathlib import Path


CSS = """
html{color-scheme:dark}
:root{--bg:#141414;--panel:#1c1c1c;--panel2:#242424;--panel3:#2e2e2e;--ink:#f2f2f2;--muted:#9a9a9a;--dim:#6f6f6f;
  --line:rgba(255,255,255,.08);--acc:#e5484d;--acc2:#ff7376;--acc-soft:rgba(229,72,77,.16);
  --ok:#4fc48a;--ok-soft:rgba(79,196,138,.14)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 system-ui,-apple-system,"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif}
.body-bg{min-height:100vh;padding:18px 18px 30px;
  background-image:radial-gradient(rgba(255,255,255,.045) 1px,transparent 1px);background-size:22px 22px}
.frame{max-width:1340px;margin:0 auto;background:var(--panel);border:1px solid var(--line);border-radius:26px;
  padding:20px 28px 46px;box-shadow:0 24px 70px rgba(0,0,0,.45)}
.top{display:flex;align-items:flex-start;gap:16px;margin-bottom:12px;flex-wrap:wrap}
.titlebox h1{margin:0;font-size:20px;font-weight:700;letter-spacing:-.01em;line-height:1.35}
.titlebox .sub{margin:2px 0 0;color:var(--muted);font-size:12px}
.sect{margin:24px 0 12px;display:flex;align-items:center;gap:10px}
.sect h2{margin:0;font-size:13px;color:var(--muted);letter-spacing:.08em}
.sect .rule{flex:1;border-top:1px solid var(--line)}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.grid .card.wide{grid-column:1/-1}
.card{background:var(--panel2);border:1px solid var(--line);border-radius:16px;padding:14px 16px}
.card .hd{display:flex;align-items:center;gap:9px;margin-bottom:6px;flex-wrap:wrap}
.ic{flex:none;width:32px;height:32px;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:13px;
  background:var(--panel3);color:var(--ink);border:1px solid var(--line)}
.card .t{font-weight:700;font-size:14.5px;word-break:break-all}
.card .m{color:var(--muted);font-size:12px;margin:2px 0 8px}
.card .body{font-size:13.5px;color:var(--ink)}
.card .body p{margin:0 0 8px}
.card .body ul{margin:0;padding-left:18px}
.card .body li{margin:0 0 6px}
.card .body li::marker{color:var(--acc2)}
.mono{font-family:ui-monospace,Consolas,"Courier New",monospace;font-size:12.5px;color:var(--ink);
  background:var(--panel3);border:1px solid var(--line);border-radius:10px;padding:8px 10px;white-space:pre-wrap;word-break:break-all}
.copy{font:inherit;font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:9px;
  padding:2px 8px;background:var(--panel3);cursor:pointer;margin-left:auto;flex:none}
.copy:hover{border-color:var(--acc2);color:var(--ink)}
.copied{color:var(--ok) !important;border-color:var(--ok) !important}
.badge{font-size:11px;padding:2px 9px;border-radius:10px;display:inline-block;background:var(--ok-soft);color:var(--ok)}
@media(max-width:900px){.body-bg{padding:8px}.frame{padding:14px 14px 30px;border-radius:18px}}
"""

JS = """
function copyText(b64, btn){
  var text = new TextDecoder().decode(Uint8Array.from(atob(b64), c=>c.charCodeAt(0)));
  var done = function(){
    if(!btn) return;
    var old = btn.textContent; btn.textContent = '已复制'; btn.classList.add('copied');
    setTimeout(function(){ btn.textContent = old; btn.classList.remove('copied'); }, 1200);
  };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(done, function(){ fallback(text, done); });
  } else { fallback(text, done); }
}
function fallback(text, done){
  var ta = document.createElement('textarea');
  ta.value = text; ta.style.position='fixed'; ta.style.opacity='0';
  document.body.appendChild(ta); ta.select();
  try{ document.execCommand('copy'); }catch(e){}
  document.body.removeChild(ta); done();
}
document.addEventListener('click', function(ev){
  var btn = ev.target.closest('.copy');
  if(btn && btn.dataset.copy){ copyText(btn.dataset.copy, btn); }
});
"""


def parse_md(content: str):
    """把 global-style.md 解析为 (H2 段落列表)，每段含 H3/H4/列表/段落块。"""
    lines = content.splitlines()
    title = ""
    sections = []          # [{h2, blocks:[{kind,text,level}]}]
    cur_section = None
    cur_block = None       # 正在累积的段落/列表

    def flush_block():
        nonlocal cur_block
        if cur_block and cur_section is not None:
            cur_section["blocks"].append(cur_block)
        cur_block = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_block()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush_block()
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1:
                title = text
            elif level == 2:
                cur_section = {"h2": text, "blocks": []}
                sections.append(cur_section)
            else:
                if cur_section is None:
                    cur_section = {"h2": "未分段", "blocks": []}
                    sections.append(cur_section)
                cur_section["blocks"].append({"kind": "h", "level": level, "text": text, "raw": [raw]})
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", line):
            flush_block()
            continue
        if re.match(r"^[-*]\s+", line) or re.match(r"^\d+\.\s+", line):
            if cur_block is None or cur_block["kind"] not in ("list", "mono_list"):
                flush_block()
                cur_block = {"kind": "list", "items": [], "raw": []}
            cur_block["items"].append(re.sub(r"^[-*]\s+|^\d+\.\s+", "", line).strip())
            cur_block["raw"].append(raw)
            continue
        if line.startswith(">"):
            if cur_block is None or cur_block["kind"] != "quote":
                flush_block()
                cur_block = {"kind": "quote", "items": [], "raw": []}
            cur_block["items"].append(line.lstrip(">").strip())
            cur_block["raw"].append(raw)
            continue
        # 普通段落（连续非空行合并）
        if cur_block is None or cur_block["kind"] != "para":
            flush_block()
            cur_block = {"kind": "para", "text": "", "raw": []}
        cur_block["raw"].append(raw)
        cur_block["text"] = (cur_block["text"] + " " + line.strip()).strip()
    flush_block()
    return title, sections


def inline_md(text: str) -> str:
    text = htmllib.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r'<span class="mono">\1</span>', text)
    return text


def render_block(block, copyable: bool) -> str:
    """渲染一个内容块；copyable 时给文本块挂一键复制按钮。"""
    parts = []
    if block["kind"] == "h":
        lvl = min(block["level"], 4)
        parts.append(f"<h{lvl}>{inline_md(block['text'])}</h{lvl}>")
        raw = block["raw"]
    elif block["kind"] == "list":
        lis = "".join(f"<li>{inline_md(it)}</li>" for it in block["items"])
        parts.append(f"<ul>{lis}</ul>")
        raw = block["raw"]
    elif block["kind"] == "quote":
        lis = "".join(f"<li>{inline_md(it)}</li>" for it in block["items"])
        parts.append(f'<ul style="list-style:none;padding-left:10px"><li>{lis}</li></ul>')
        raw = block["raw"]
    else:
        parts.append(f"<p>{inline_md(block['text'])}</p>")
        raw = block["raw"]
    if not copyable:
        return "".join(parts)
    plain = "\n".join(raw).strip()
    b64 = base64.b64encode(plain.encode("utf-8")).decode("ascii")
    body = "".join(parts)
    return (f'<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:10px">'
            f'<div style="flex:1;min-width:0">{body}</div>'
            f'<button class="copy" data-copy="{b64}">📋 复制</button></div>')


ICONS = ["风", "设", "文", "注", "备"]


def build_html(md_path: Path) -> str:
    content = md_path.read_text(encoding="utf-8")
    title, sections = parse_md(content)
    drama = md_path.parent.parent.name
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    body = []
    for idx, sec in enumerate(sections):
        h2 = sec["h2"]
        is_style = h2.startswith("三、成片文案")  # 该段逐块可复制
        icon = ICONS[idx] if idx < len(ICONS) else "块"
        cards = []
        grouped = []                          # h3/h4 分组渲染
        cur_card = None
        for blk in sec["blocks"]:
            if blk["kind"] == "h" and blk["level"] >= 3:
                cur_card = {"title": blk["text"], "blocks": []}
                grouped.append(cur_card)
            else:
                if cur_card is None:
                    cur_card = {"title": "", "blocks": []}
                    grouped.append(cur_card)
                cur_card["blocks"].append(blk)
        for card in grouped:
            title_html = ""
            if card["title"]:
                title_html = (f'<div class="hd"><span class="ic">{icon}</span>'
                              f'<span class="t">{inline_md(card["title"])}</span></div>')
            blocks_html = "".join(render_block(b, is_style) for b in card["blocks"])
            wide = ' wide' if is_style and len(grouped) == 1 else ''
            cards.append(f'<div class="card{wide}">{title_html}<div class="body">{blocks_html}</div></div>')
        body.append(f'<div class="sect"><h2>{inline_md(h2)}</h2><div class="rule"></div></div>'
                    f'<div class="grid">{"".join(cards)}</div>')

    head = (f"<title>{htmllib.escape(drama)} · 全局风格设定</title>")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{head}
<style>{CSS}</style>
</head>
<body>
<div class="body-bg"><div class="frame">
<div class="top"><div class="titlebox">
  <h1>{htmllib.escape(title or "全局风格设定（剧级档案）")}</h1>
  <div class="sub">{htmllib.escape(drama)} · 生成时间 {gen_time} · 与工作台同主题</div>
</div></div>
{"".join(body)}
</div></div>
<script>{JS}</script>
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        print("用法: python gen_global_style_html.py <global-style.md路径>")
        sys.exit(1)
    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"文件不存在: {md_path}")
        sys.exit(1)
    out = md_path.parent / "global-style-view.html"
    out.write_text(build_html(md_path), encoding="utf-8")
    size = out.stat().st_size
    print(f"OK 输出 {out}（{size} 字节）")


if __name__ == "__main__":
    main()

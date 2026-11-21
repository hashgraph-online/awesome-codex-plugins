# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=4", "pypdfium2>=4", "pillow>=10"]
# ///
"""Markdown → PDF 报告：pandoc 转 HTML，KaTeX 渲染公式，Chrome（或 Edge、Chromium）无头打印，最后做版面机检。

用法：
  uv run build_report.py <正文.md> <输出.pdf> "<页眉标题>" "<日期>" [图模块.py] [--json] [--strict]

  --json     机检结果按 JSON 打印（默认打印 Python 字典）
  --strict   unrendered_math、blank_pages、overflow、missing_images 任一非空时退出码为 1
  --author   写进 PDF 元数据的作者，默认空
  --chrome   浏览器路径；也可以用环境变量 KAOYAN_CHROME

机检结果：
  pages            页数
  unrendered_math  PDF 文字里残留的 $ 或 \\命令（公式没渲染出来）
  blank_pages      几乎没字也没图的页
  overflow         宽过版心（180 mm）被裁掉的公式、表格、图，给前 40 字
  missing_images   没加载出来的图片（路径写错、文件不在）
  sparse_pages     最后一页以外、内容不到三成的页（通常是大表格或图整块挤到下一页）
  sheet            全部页拼成的一张缩略图，要肉眼看时只看这一张

正文里能用的写法见同目录上一级的 SKILL.md。构建目录是输出 PDF 旁边的 _build/；
每次构建的浏览器配置和中间文件放在其中一个单独的 run-* 子目录里，构建完删掉，
所以同一个输出目录里并行构建不同文件名的报告不会互相干扰。
正文里图片的相对路径按 Markdown 源文件所在目录解析。
"""
from __future__ import annotations

import argparse
import html as _html
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
CSS_FILES = ("report.css", "extra.css", "cards.css")
PANDOC_FROM = "markdown+pipe_tables+tex_math_dollars+raw_html+fenced_divs"


# ---------- 纯函数（有单测） ----------

_PIPE_TOKEN = re.compile(r"\\\\|\\\||\|")  # 依次匹配：\\（换行，原样保留）、\|（双竖线）、|（单竖线）


def fix_math_pipes(md: str) -> str:
    """表格里公式中的 | 会被 pandoc 当成列分隔符：单竖线 | 换成 \\vert，双竖线 \\| 换成 \\Vert。
    记号不变，只是不再出现裸的 | 字符。"""
    def tok(t: re.Match) -> str:
        s = t.group(0)
        return s if s == "\\\\" else (r"\Vert " if s == r"\|" else r"\vert ")

    def sub(m: re.Match) -> str:
        return _PIPE_TOKEN.sub(tok, m.group(0))
    md = re.sub(r"\$\$.+?\$\$", sub, md, flags=re.S)
    return re.sub(r"(?<!\$)\$(?!\$)[^$\n]+?\$", sub, md)


_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_IMG_SRC = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]*)(")', re.I)


def rebase_images(html: str, base: Path) -> str:
    """把 <img src="相对路径"> 改成按 Markdown 源文件目录解析出的 file:// 绝对地址。
    HTML 放在 _build/ 里打印，不改的话浏览器会到 _build/ 下找图。已有协议（http:、data: 等）的不动。"""
    def sub(m: re.Match) -> str:
        v = _html.unescape(m.group(2))
        if not v or v.startswith(("#", "//")):
            return m.group(0)
        if re.match(r"^[A-Za-z]:[\\/]", v) or v.startswith("/"):
            p = Path(unquote(v))
        elif _SCHEME.match(v):
            return m.group(0)
        else:
            p = base / unquote(v.split("#", 1)[0].split("?", 1)[0])
        return m.group(1) + _html.escape(p.resolve().as_uri()) + m.group(3)
    return _IMG_SRC.sub(sub, html)


def inject_figs(html: str, figs: dict) -> str:
    """把 <!--FIG:名字--> 换成 figs[名字]() 返回的 SVG。名字不存在时报错并列出可用的名字。"""
    def sub(m: re.Match) -> str:
        name = m.group(1)
        if name not in figs:
            raise KeyError(f"正文里有 <!--FIG:{name}-->，图模块的 FIGS 里没有这个名字；现有：{sorted(figs)}")
        return figs[name]()
    return re.sub(r"<!--FIG:(\w+)-->", sub, html)


def css_string(s: str) -> str:
    """转成可以放进 <style> 里 CSS 双引号字符串的内容：引号、反斜杠、尖括号、& 和控制字符
    都写成 CSS 十六进制转义（如 \\3c ），这样标题里的 </style> 关不掉样式块，换行也不会弄坏页眉。"""
    return "".join(f"\\{ord(c):x} " if (c in '"\'\\<>&' or ord(c) < 0x20 or ord(c) == 0x7f) else c for c in s)


def fill_template(tpl: str, title: str, date: str, body: str) -> str:
    esc_title, esc_date = _html.escape(title), _html.escape(date)
    css_title, css_date = css_string(title), css_string(date)
    return (tpl.replace("{{TITLE_CSS}}", css_title).replace("{{DATE_CSS}}", css_date)
               .replace("{{TITLE}}", esc_title).replace("{{DATE}}", esc_date).replace("<!--BODY-->", body))


def leftover_math(text: str) -> list[str]:
    """PDF 文字里残留的 $ 和 \\命令，说明公式没渲染。"""
    return sorted(set(re.findall(r"\$|\\[a-zA-Z]+", text)))[:20]


# ---------- 外部程序 ----------

def find_chrome(explicit: str | None = None) -> str:
    """找一个能无头打印的 Chromium 系浏览器：参数 → 环境变量 → PATH → 各系统默认位置。"""
    cands = [explicit, os.environ.get("KAOYAN_CHROME"), os.environ.get("CHROME_PATH")]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge", "microsoft-edge"):
        cands.append(shutil.which(name))
    system = platform.system()
    if system == "Windows":
        for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
            if base:
                cands += [str(Path(base) / "Google/Chrome/Application/chrome.exe"),
                          str(Path(base) / "Microsoft/Edge/Application/msedge.exe")]
    elif system == "Darwin":
        cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  "/Applications/Chromium.app/Contents/MacOS/Chromium",
                  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    for c in cands:
        if c and Path(c).exists():
            return c
    raise FileNotFoundError("找不到 Chrome / Edge / Chromium。装一个，或用 --chrome、环境变量 KAOYAN_CHROME 指定路径。")


def chrome_flags(profile: Path) -> list[str]:
    flags = ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
             f"--user-data-dir={profile}", "--virtual-time-budget=20000"]
    # GitHub Actions 等 Linux CI 上，Chrome 的沙箱常因用户命名空间受限而起不来
    if platform.system() == "Linux" and os.environ.get("CI"):
        flags.append("--no-sandbox")
    return flags


def remove_profile(profile: Path, tries: int = 5) -> None:
    """删掉无头浏览器的临时配置目录（Cookies、History 等），不留在工作区里。
    Windows 上浏览器的辅助进程可能晚一点才释放文件，删不掉就稍等再试。"""
    for i in range(tries):
        shutil.rmtree(profile, ignore_errors=True)
        if not profile.exists():
            return
        time.sleep(0.5 * (i + 1))


def md_to_html(md: str) -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise FileNotFoundError("找不到 pandoc：https://pandoc.org/installing.html")
    return subprocess.run([pandoc, "-f", PANDOC_FROM, "-t", "html", "--mathjax"], input=fix_math_pipes(md),
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout


def load_figs(figmod: Path | None) -> dict:
    if not figmod:
        return {}
    sys.path.insert(0, str(HERE))  # 图模块里 from charts import *
    spec = importlib.util.spec_from_file_location("report_figs", figmod)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.FIGS


# ---------- 版面机检 ----------

def scan_pages(pdf: Path, title: str, date: str, build: Path) -> dict:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf))
    texts = [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    n = len(doc)
    blank, sparse, sheet = [], [], None
    try:
        from PIL import Image
        thumbs = []
        for i in range(n):
            im = doc[i].render(scale=0.6).to_pil().convert("L")
            w, h = im.size
            px = im.load()
            strip = int(w * 0.045)
            rows = [y for y in range(int(h * 0.08), int(h * 0.94), 4)
                    if any(px[x, y] < 200 for x in range(strip, w - strip, 4))]
            filled = (rows[-1] - rows[0]) / (h * 0.86) if rows else 0
            body = re.sub(r"\d+\s*/\s*\d+", "", texts[i].replace(title, "").replace(date, ""))
            if not rows and len(body.strip()) < 3:
                blank.append(i + 1)
            elif i < n - 1 and filled < 0.3:
                sparse.append(i + 1)
            thumbs.append(im.resize((w // 2, h // 2)))
        cols = 4
        tw, th = thumbs[0].size
        sh = Image.new("L", (cols * tw + (cols + 1) * 6, ((n + cols - 1) // cols) * (th + 6) + 6), 150)
        for k, t in enumerate(thumbs):
            sh.paste(t, (6 + (k % cols) * (tw + 6), 6 + (k // cols) * (th + 6)))
        sheet = build / f"{pdf.stem}_sheet.png"
        sh.save(sheet)
    except ImportError:
        sheet = "没装 Pillow：没有空白页检查和缩略图"
    doc.close()
    return {"pages": n, "unrendered_math": leftover_math("".join(texts)),
            "blank_pages": blank, "sparse_pages": sparse, "sheet": str(sheet)}


PROBE_JS = (
    "<style>html,body{width:180mm!important;max-width:180mm!important;margin:0!important;padding:0!important}</style>"
    "<script>window.addEventListener('load',function(){setTimeout(function(){var R=document.body.getBoundingClientRect().right+1,o=[],g=[];"
    "document.querySelectorAll('.katex-display,table,pre,img,svg,.tiles,.ch,.flow,div').forEach(function(e){"
    "if(e.closest('.katex-display')&&!e.classList.contains('katex-display'))return;"
    "var r=e.getBoundingClientRect();if(e.scrollWidth>e.clientWidth+2||r.right>R){o.push((e.innerText||e.tagName).replace(/\\s+/g,' ').slice(0,40))}});"
    "Array.prototype.forEach.call(document.images,function(i){if(!i.complete||!i.naturalWidth){g.push(i.getAttribute('src')||'')}});"
    "var p=document.createElement('pre');p.id='__ovf';p.textContent=JSON.stringify({o:o.slice(0,10),g:g.slice(0,10)});document.body.appendChild(p)},300)})</script>"
)


def probe_page(chrome: str, page: Path, profile: Path) -> tuple[list[str], list[str]]:
    """在 180 mm 宽的页面里找溢出版心的元素和没加载出来的图片。返回 (overflow, missing_images)。"""
    probe = page.with_name(f"{page.stem}_probe.html")
    probe.write_text(page.read_text(encoding="utf-8").replace("</head>", PROBE_JS + "</head>"), encoding="utf-8")
    try:
        dom = subprocess.run([chrome, *chrome_flags(profile), "--window-size=700,1000", "--dump-dom", probe.as_uri()],
                             capture_output=True, text=True, encoding="utf-8", timeout=300).stdout
        m = re.search(r'<pre id="__ovf">(.*?)</pre>', dom, re.S)
        if not m:
            return ["机检没跑成"], []
        d = json.loads(_html.unescape(m.group(1)))
        return d["o"], [unquote(s) for s in d["g"]]
    except Exception as e:  # noqa: BLE001
        return [f"机检没跑成：{e}"], []
    finally:
        probe.unlink(missing_ok=True)


# ---------- 主流程 ----------

def build(src: Path, out: Path, title: str, date: str, figmod: Path | None = None,
          chrome: str | None = None, author: str = "") -> dict:
    from pypdf import PdfReader, PdfWriter

    chrome = find_chrome(chrome)
    body = inject_figs(md_to_html(src.read_text(encoding="utf-8")), load_figs(figmod))
    body = rebase_images(body, src.parent)

    bdir = out.parent / "_build"
    bdir.mkdir(parents=True, exist_ok=True)
    if not (bdir / "katex" / "katex.min.js").exists():
        shutil.copytree(ASSETS / "katex", bdir / "katex", dirs_exist_ok=True)
    for n in CSS_FILES:
        shutil.copy2(ASSETS / n, bdir / n)
    page = bdir / f"{out.stem}.html"
    page.write_text(fill_template((ASSETS / "template.html").read_text(encoding="utf-8"), title, date, body), encoding="utf-8")

    # 这次构建独占的目录：浏览器配置和中间 PDF 都放这里，结束整个删掉
    run = Path(tempfile.mkdtemp(prefix="run-", dir=bdir))
    profile, raw = run / "chrome-profile", run / "raw.pdf"
    try:
        subprocess.run([chrome, *chrome_flags(profile), "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
                        f"--print-to-pdf={raw}", page.as_uri()], check=True, timeout=300, capture_output=True)
        w = PdfWriter(clone_from=PdfReader(str(raw)))
        # Creator 默认是浏览器的 User-Agent（带操作系统和版本），换成固定写法
        w.add_metadata({"/Title": title, "/Author": author, "/Creator": "Chromium (headless)",
                        "/Producer": "kaoyan-report build_report.py"})
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as f:
            w.write(f)
        overflow, missing = probe_page(chrome, page, profile)
        result = {"file": out.name, **scan_pages(out, title, date, bdir), "overflow": overflow, "missing_images": missing}
    finally:
        remove_profile(run)
    order = ("file", "pages", "unrendered_math", "blank_pages", "overflow", "missing_images", "sparse_pages", "sheet")
    return {k: result[k] for k in order}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Markdown → PDF 报告，带版面机检")
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("title")
    ap.add_argument("date")
    ap.add_argument("figmod", type=Path, nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--author", default="")
    ap.add_argument("--chrome")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    res = build(a.src.resolve(), a.out.resolve(), a.title, a.date,
                a.figmod.resolve() if a.figmod else None, a.chrome, a.author)
    print(json.dumps(res, ensure_ascii=False) if a.json else res)
    bad = res["unrendered_math"] or res["blank_pages"] or res["overflow"] or res["missing_images"]
    return 1 if (a.strict and bad) else 0


if __name__ == "__main__":
    sys.exit(main())

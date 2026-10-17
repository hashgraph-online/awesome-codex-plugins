# -*- coding: utf-8 -*-
"""
gen_asset_list.py — 从定稿分镜派生"本集素材清单表"（人物/场景/道具 + 提示词）

用法:
    python gen_asset_list.py scripts/[剧本名]/outputs/epXX/02-jimeng-prompts.md

输入:
    1. 02-jimeng-prompts.md —— 解析每个母镜头的资产声明行，提取本集实际引用
       的素材 + 出场母镜头列表
    2. assets/character-prompts.md, scene-prompts.md, prop-prompts.md
       —— 匹配对应素材的提示词全文（新剧：独立标题 `## @名称（新增·epXX）`；
          历史格式：宫格段落 `格N——【名称】`，仅 2026-09-30 之前的存量剧在用）

输出:
    scripts/[剧本名]/outputs/epXX/[剧本名]_epXX_素材清单表.xlsx
    三个分表：人物 / 场景 / 道具
"""
import os
import re
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 项目根（工作区根）：JIMENG_ROOT 显式指定 > 相对 cwd 往上找 AGENTS.md > 脚本位置向上推导（旧布局兜底）
# 技能可安装到任意位置（全局技能目录/tap 安装），脚本位置推导只对「技能恰好在工作区 .agents/skills 下」的旧布局成立。
def _resolve_project_root():
    env = os.environ.get("JIMENG_ROOT")
    if env:
        return os.path.abspath(env)
    d = os.getcwd()
    for _ in range(6):
        if os.path.isfile(os.path.join(d, "AGENTS.md")) or os.path.isdir(os.path.join(d, "scripts")):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

PROJECT_ROOT = _resolve_project_root()

# ---------- 样式 ----------
HEADER_FILL = PatternFill("solid", fgColor="2F3B4C")
HEADER_FONT = Font(name="微软雅黑", bold=True, color="FFFFFF", size=11)
BODY_FONT = Font(name="微软雅黑", size=10)
NAME_FONT = Font(name="微软雅黑", size=10, bold=True)
ZEBRA_1 = PatternFill("solid", fgColor="FFFFFF")
ZEBRA_2 = PatternFill("solid", fgColor="F7F9FC")
THIN = Side(style="thin", color="D9DEE7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP_TOP = Alignment(horizontal="left", vertical="top", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

ASSET_FILES = {
    "人物": "character-prompts.md",
    "场景": "scene-prompts.md",
    "道具": "prop-prompts.md",
}


def normalize(s):
    """素材名归一化：去掉@前缀、括号后缀、集数后缀、外景后缀、ep标记、分隔符"""
    s = s.lstrip("@")
    s = re.sub(r"（[^）]*）", "", s)
    s = re.sub(r"\s*第\d+(-\d+)?集", "", s)
    s = re.sub(r"\s*·\s*外景", "", s)
    s = s.replace("·", "").replace("-", "").replace("_", "").replace(" ", "")
    return s.strip()


def match_name(k, name):
    nk, nn = normalize(k), normalize(name)
    return nk == nn or nk.startswith(nn) or nn.startswith(nk)


def split_entries(text):
    """按 ## 标题切段，返回 [(标题, 正文)]"""
    entries = []
    cur = None
    buf = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^##\s+(.+)$", s)
        if not m:
            # 兼容道具库的「### N. @名」条目标题（与 ## @名 等效）
            m = re.match(r"^###\s+(?:\d+[.、]\s*)?(@.+)$", s)
        if m:
            if cur is not None:
                entries.append((cur, "\n".join(buf)))
            cur = m.group(1).strip()
            buf = []
        elif cur is not None:
            buf.append(s)
    if cur is not None:
        entries.append((cur, "\n".join(buf)))
    return entries


def split_panels(body):
    """把宫格正文按 '格N——【名称】' 切段，返回 [(格名, 格正文)]"""
    panels = []
    cur = None
    buf = []
    for line in body.splitlines():
        m = re.match(r"^格\d+——【(.+?)】", line)
        if m:
            if cur:
                panels.append((cur, "\n".join(buf)))
            cur = m.group(1).strip()
            buf = [line]
        elif cur:
            buf.append(line)
    if cur:
        panels.append((cur, "\n".join(buf)))
    return panels


def find_prompt(name, label, asset_texts):
    """在对应类型资产文件中查找素材提示词。
    返回 (正文文本, 出图要求) 或 (None, None)"""
    text = asset_texts[label]
    entries = split_entries(text)
    nk = normalize(name)
    # 1) 独立标题匹配：先精确匹配
    for title, body in entries:
        if normalize(title) == nk:
            return body, body
    # 2) 独立标题匹配：前缀匹配取最长（最精确），避免"面包车"误吞"面包车·李春升一伙"
    best = None
    for title, body in entries:
        nn = normalize(title)
        if nk.startswith(nn) or nn.startswith(nk):
            if best is None or len(nn) > len(normalize(best[0])):
                best = (title, body)
    if best is not None:
        return best[1], best[1]
    # 3) 宫格段落匹配（陈峰家院子雨天 藏在 ep09 场景宫格内）
    for title, body in entries:
        for pname, pbody in split_panels(body):
            if match_name(pname, name):
                return pbody, pbody
    return None, None


def parse_storyboard(md_path):
    """返回 (类型映射{引用名:类型}, 出场{引用名: [母镜头ID]}, 显示名映射{引用名:显示名})"""
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    type_map = {}
    display_map = {}
    in_table = False
    for line in lines:
        if line.startswith("## 素材对应表"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            in_table = False
        if in_table and line.startswith("|") and "@" in line:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0].startswith("@"):
                type_map[parts[0]] = parts[1]

    master_pat = re.compile(r"## 母镜头([0-9A-Za-z]+)")
    cur = None
    declared = {}
    for line in lines:
        m = master_pat.match(line)
        if m:
            cur = m.group(1)
            declared[cur] = []
            continue
        if cur and line.startswith("人物：") and "道具：" in line:
            refs = []
            for m in re.finditer(r"@(.+?)\s+是", line):
                token = "@" + m.group(1).strip()
                if token in type_map and token not in refs:
                    refs.append(token)
            for m in re.finditer(r"@(.+?)\s+是\s*([^|,，]+)", line):
                token = "@" + m.group(1).strip()
                display_map[token] = m.group(2).strip()
            declared[cur] = refs

    usage = {}
    for mid, refs in declared.items():
        for ref in refs:
            usage.setdefault(ref, []).append(mid)
    return type_map, usage, display_map


def main():
    if len(sys.argv) < 2:
        print("用法: python gen_asset_list.py scripts/[剧本名]/outputs/epXX/02-jimeng-prompts.md")
        sys.exit(1)
    arg_path = sys.argv[1]
    md_path = arg_path if os.path.isabs(arg_path) else os.path.join(PROJECT_ROOT, arg_path)
    if not os.path.exists(md_path):
        print(f"找不到分镜文件: {md_path}")
        sys.exit(1)

    ep_dir = os.path.dirname(md_path)
    script_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(md_path))))
    ep_id = os.path.basename(ep_dir)

    type_map, usage, display_map = parse_storyboard(md_path)
    if not usage:
        print("未解析到任何素材引用，请检查分镜格式")
        sys.exit(1)

    assets_dir = os.path.join(os.path.dirname(os.path.dirname(ep_dir)), "assets")
    asset_texts = {}
    for label, fname in ASSET_FILES.items():
        p = os.path.join(assets_dir, fname)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                asset_texts[label] = f.read()
        else:
            asset_texts[label] = ""

    rows = {"人物": [], "场景": [], "道具": []}
    for ref in sorted(usage.keys()):
        name = display_map.get(ref, ref.lstrip("@"))
        label = type_map.get(ref, "")
        if label not in rows:
            continue
        body, req = find_prompt(name, label, asset_texts)
        if body is None:
            print(f"[警告] {ref} 未在 assets 中找到提示词，跳过")
            continue
        masters = ",".join(usage[ref])
        rows[label].append((ref, name, masters, body))

    wb = Workbook()
    order = ["人物", "场景", "道具"]
    headers = {
        "人物": ["引用名", "角色名", "本集出场母镜头", "提示词全文"],
        "场景": ["引用名", "场景名", "本集出场母镜头", "提示词全文"],
        "道具": ["引用名", "道具名", "本集出场母镜头", "提示词全文"],
    }
    widths = {
        "人物": [14, 14, 22, 110],
        "场景": [14, 20, 22, 110],
        "道具": [14, 16, 22, 110],
    }

    for label in order:
        ws = wb.create_sheet(label)
        hdr = headers[label]
        ws.append(hdr)
        for c in range(1, len(hdr) + 1):
            cell = ws.cell(1, c)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = CENTER
            cell.border = BORDER
        for i, (ref, name, masters, body) in enumerate(rows[label]):
            ws.append([ref, name, masters, body])
            r = i + 2
            for c in range(1, len(hdr) + 1):
                cell = ws.cell(r, c)
                cell.font = NAME_FONT if c == 1 else BODY_FONT
                cell.alignment = CENTER if c in (1, 2, 3) else WRAP_TOP
                cell.border = BORDER
                cell.fill = ZEBRA_1 if i % 2 == 0 else ZEBRA_2
        for i, w in enumerate(widths[label], start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A2"
        for r in range(2, ws.max_row + 1):
            val = ws.cell(r, 4).value or ""
            lines = sum(max(1, -(-len(seg) // 50)) for seg in val.split("\n"))
            ws.row_dimensions[r].height = max(60, lines * 14 + 8)

    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    out_path = os.path.join(ep_dir, f"{script_name}_ep{ep_id[2:]}_素材清单表.xlsx")
    wb.save(out_path)
    print(f"已生成: {out_path}")
    for label in order:
        print(f"  {label}: {len(rows[label])} 项")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""gen_episode_brief.py —— 生成本集"要点卡"(episode-brief.md)

把分镜/终审子代理需要反复查阅的上游要点预汇编成单个文件:
- 台词表(逐字+参考时长, 来自 epXX-dialogue-list.json)
- 资产@引用速查(来自 outputs/epXX/epXX-asset-list.md 的表格行/场景条目行)
- 关键锚点(来自讲戏本每 P 的「关键问题点」+ 元数据行)
- 全局风格(来自 config/global-style.md 全文)

用法:
    python gen_episode_brief.py --ep-dir PATH [--out PATH]

输出: outputs/epXX/episode-brief.md (覆盖)

设计: 2026-08-20 提速优化 —— 子代理读 1 个 brief 替代翻 4 个大文件
"""
import argparse
import json
import re
import sys
from pathlib import Path


def load_dialogues(ep_dir: Path) -> list[str]:
    """从 dialogue-list.json 提取台词行"""
    jp = ep_dir / "epXX-dialogue-list.json"
    # 探测实际文件名 ep<num>-dialogue-list.json
    candidates = sorted(ep_dir.glob("ep*-dialogue-list.json"))
    if candidates:
        jp = candidates[0]
    rows = []
    if not jp.exists():
        return ["（未找到台词本 json，请读 epXX-dialogue-list.md）"]
    data = json.loads(jp.read_text(encoding="utf-8"))
    for scene in data.get("scenes", []):
        sid = scene.get("scene_id", "?")
        title = scene.get("title", "")
        # 去重: title 已含 scene_id 时不再拼接
        head = f"### 场景 {title if sid in title else f'{sid} {title}'}"
        rows.append(head)
        for d in scene.get("dialogues", []):
            seq = d.get("seq", "")
            ch = d.get("character", "")
            txt = d.get("text", "")
            dur = d.get("ref_duration") or d.get("duration") or ""
            rows.append(f"- [{seq}] @{ch}：「{txt}」({dur})")
    return rows


def load_assets(ep_dir: Path) -> list[str]:
    """从 asset-list.md 提取 @引用速查（表格行 + 首设标注）"""
    ap = None
    candidates = sorted(ep_dir.glob("ep*-asset-list.md"))
    if candidates:
        ap = candidates[0]
    if not ap or not ap.exists():
        return ["（未找到资产清单，请读 assets/*.md）"]
    lines = []
    in_table = False
    for line in ap.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("| @引用名") or s.startswith("| @"):
            in_table = True
            lines.append(s)
            continue
        if in_table:
            if s.startswith("|"):
                lines.append(s)
            else:
                in_table = False
        # 首设/新增说明行也保留
        if "首设" in s and s.startswith(">"):
            lines.append(s)
    return lines or ["（资产清单无可提取表格）"]


def load_anchors(ep_dir: Path) -> list[str]:
    """从讲戏本提取每 P 标题 + 元数据 + 关键问题点"""
    dp = ep_dir / "01-director-analysis.md"
    if not dp.exists():
        return ["（未找到讲戏本）"]
    content = dp.read_text(encoding="utf-8")
    blocks = re.split(r"(?=^## P\d+)", content, flags=re.M)
    rows = []
    for b in blocks:
        m = re.match(r"^## (P\d+[^\n]*)", b)
        if not m:
            continue
        rows.append(f"## {m.group(1).strip()}")
        # 元数据字段
        for meta in re.finditer(r"^- \*\*(人物|场景|镜头组|时长|情绪|目的)\*\*: (.+)$", b, re.M):
            rows.append(f"- **{meta.group(1)}**: {meta.group(2)}")
        # 台词清单行
        for tl in re.finditer(r"^(- @\S+: \"[^\"]+\")", b, re.M):
            rows.append(tl.group(1))
        # 关键问题点
        kp = re.search(r"- \*\*关键问题点\*\*: (.+)$", b, re.M)
        if kp:
            rows.append(f"- ⚠ 关键问题点: {kp.group(1)}")
        rows.append("")
    return rows


def main():
    parser = argparse.ArgumentParser(description="生成本集要点卡 episode-brief.md")
    parser.add_argument("--ep-dir", required=True,
                        help="本集输出目录 outputs/epXX/")
    parser.add_argument("--out", default=None, help="输出路径(默认 <ep-dir>/episode-brief.md)")
    args = parser.parse_args()

    ep_dir = Path(args.ep_dir)
    if not ep_dir.exists():
        print(f"错误: 目录不存在: {ep_dir}", file=sys.stderr)
        sys.exit(2)

    out = Path(args.out) if args.out else ep_dir / "episode-brief.md"

    sections = []
    sections.append("# 本集要点卡（自动汇编，供分镜/终审子代理快速查阅）")
    sections.append("> 字面唯一权威仍是剧本原文 script/epXX.txt；本卡为工作副本摘要。")

    sections.append("\n## 一、全局风格")
    gs = None
    for cand in ([ep_dir.parent.parent / "config" / "global-style.md"] +
                 sorted(ep_dir.parent.glob("*/config/global-style.md")) +
                 [ep_dir.parent / "config" / "global-style.md"]):
        if cand.exists():
            gs = cand
            break
    if gs:
        sections.append(gs.read_text(encoding="utf-8").strip())
    else:
        sections.append("（未找到 config/global-style.md）")

    sections.append("\n## 二、台词表（逐字+参考时长）")
    sections.extend(load_dialogues(ep_dir))

    sections.append("\n## 三、本集资产 @引用速查")
    sections.extend(load_assets(ep_dir))

    sections.append("\n## 四、剧情点与关键锚点（讲戏本摘编）")
    sections.extend(load_anchors(ep_dir))

    out.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(f"要点卡已生成: {out}")
    print(f"  行数: {len(chr(10).join(sections).splitlines())}")
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""check_assets_change.py —— 判断本集是否需要派遣 art-designer 子代理

解析导演讲戏本(epXX-01-director-analysis.md)中的 @引用名,
与 assets/{character,prop,scene}-prompts.md 现有 @引用名比对:
- 全部已存在 → SKIP(无需派遣 art-designer)
- 有缺失 → NEEDED(派遣 art-designer)

用法:
    python check_assets_change.py --director-analysis PATH \
                                    --assets-dir DIR \
                                    [--json]

退出码:
    0 = SKIP
    1 = NEEDED
    2 = 用法错误

设计: 2026-08-15 conditional-skip-stage3-design.md
"""
import argparse
import json
import re
import sys
from pathlib import Path

# 讲戏本中提取 @引用名: @赵峰 @石翠 @国营饭店办公室 等
# 覆盖: ASCII + 中文 + 数字 + 下划线
AT_REFERENCE_RE = re.compile(r"@([\w\u4e00-\u9fa5]+)")
# assets 文件中 @角色名 作为二级标题 (## @赵峰)
ASSETS_HEADER_RE = re.compile(r"^##\s*@([\w\u4e00-\u9fa5]+)", re.M)
# assets 文件中表格行 | @引用名 | 类型 | ... |
ASSETS_TABLE_RE = re.compile(r"\|\s*@([\w\u4e00-\u9fa5]+)\s*\|")
# assets 场景条目（历史格式，仅 2026-09-30 之前的存量剧在用：格1——【@国营饭店会客厅】）
# 新剧场景按「一个场景一条独立提示词」建库，引用名走 ## @场景名 或清单表
GRID_PANEL_RE = re.compile(r"格\d+——【@([\w\u4e00-\u9fa5]+)】")


def extract_references_from_director_analysis(path: Path, asset_list_path: Path = None) -> set:
    """从讲戏本提取所有 @人物/@场景/@道具

    策略:
    1. 贪婪正则初步提取所有 @引用
    2. 排除叙述文字(贪婪误识别)
    3. 若提供 epXX-asset-list.md, 用其已知引用名作交叉验证
    """
    content = path.read_text(encoding="utf-8")
    refs_raw = set(AT_REFERENCE_RE.findall(content))
    # 过滤贪婪误识别: 包含叙述关键词或长度过长的视为误识别
    NARRATIVE_KEYWORDS = [
        "为本集", "为新增", "为参考", "为本集新增",
        "勿引用", "勿出现",
        "上不", "下不", "面不动声色",
        "的惊讶", "的紧张", "的反应", "的眼神", "的嘴角", "的声音",
        "一律以", "引用名一律", "本集复用",
        "首设", "本集新增", "本集首设",
        "首设集", "造型要点", "本集职能", "本集用途",
        "音音色", "音色", "复用",
    ]
    refs = set()
    for r in refs_raw:
        if len(r) > 8:  # 过长很可能是贪婪误识别
            continue
        skip = False
        for kw in NARRATIVE_KEYWORDS:
            if kw in r:
                skip = True
                break
        if not skip:
            refs.add(r)
    # 若有 asset-list.md, 交叉验证
    if asset_list_path and asset_list_path.exists():
        al_content = asset_list_path.read_text(encoding="utf-8")
        al_refs_raw = set(AT_REFERENCE_RE.findall(al_content))
        # al refs 也过滤叙述词
        al_refs = {r for r in al_refs_raw
                    if len(r) <= 8 and not any(kw in r for kw in [
                        "为本集", "为新增", "为参考", "为本集新增",
                        "勿引用", "勿出现",
                        "上不", "下不", "面不动声色",
                        "的惊讶", "的紧张", "的反应", "的眼神", "的嘴角", "的声音",
                        "一律以", "引用名一律", "本集复用",
                        "首设", "本集新增", "本集首设",
                        "首设集", "造型要点", "本集职能", "本集用途",
                        "音色", "复用",
                    ])}
        # 取交集(讲戏本 ∩ asset-list = 真正需要的)
        refs = refs & al_refs
        # 加上 asset-list 中声明但讲戏本漏的
        refs |= al_refs
    return refs


def extract_references_from_assets(path: Path) -> set:
    """从 assets 文件提取所有 @引用名(二级标题 + 表格行)

    过滤叙述词避免元描述被误识别为 @引用
    """
    if not path.exists():
        return set()
    content = path.read_text(encoding="utf-8")
    refs = set()
    # 只认结构化位置（## @名字 标题 / 表格行 | @名字 |），
    # 不做全文贪婪抓取 —— 避免把元描述文字（如"@引用名 一律以资产库为准"）
    # 误识别为资产条目（曾致 check_assets_change 误报 NEEDED: missing=["引用名与"]）
    refs.update(m.group(1) for m in ASSETS_HEADER_RE.finditer(content))
    refs.update(m.group(1) for m in ASSETS_TABLE_RE.finditer(content))
    refs.update(m.group(1) for m in GRID_PANEL_RE.finditer(content))
    # 表头噪音: "| @引用名 | 类型 |" 的表头本身会被 TABLE_RE 抓成 "引用名"
    refs.discard("引用名")
    refs.discard("引用")
    # 过滤元描述
    NARRATIVE_KEYWORDS = [
        "为本集", "为新增", "为参考", "为本集新增",
        "勿引用", "勿出现",
        "上不", "下不", "面不动声色",
        "的惊讶", "的紧张", "的反应", "的眼神", "的嘴角", "的声音",
        "一律以", "引用名一律", "本集复用",
        "首设", "本集新增", "本集首设",
        "首设集", "造型要点", "本集职能", "本集用途",
        "音色", "复用",
    ]
    return {r for r in refs
            if len(r) <= 8 and not any(kw in r for kw in NARRATIVE_KEYWORDS)}


def main():
    parser = argparse.ArgumentParser(description="判断本集是否需要派遣 art-designer")
    parser.add_argument("--director-analysis", required=True,
                        help="讲戏本路径:outputs/epXX/01-director-analysis.md")
    parser.add_argument("--assets-dir", required=True,
                        help="assets 目录路径:scripts/[剧名]/assets/")
    parser.add_argument("--json", action="store_true",
                        help="仅输出 JSON 结果")
    args = parser.parse_args()

    da_path = Path(args.director_analysis)
    assets_dir = Path(args.assets_dir)

    if not da_path.exists():
        print(f"错误: 讲戏本不存在: {da_path}", file=sys.stderr)
        sys.exit(2)
    if not assets_dir.exists():
        print(f"错误: assets 目录不存在: {assets_dir}", file=sys.stderr)
        sys.exit(2)

    # 探测 epXX-asset-list.md (若已存在,作为白名单交叉验证)
    asset_list_path = da_path.parent / (da_path.stem.replace("01-director-analysis", "ep").replace("-analysis", "") + "-asset-list.md")
    # 简化: 直接尝试 ep<num>-asset-list.md
    ep_num_match = re.search(r"ep(\d+)", da_path.parent.name + str(da_path))
    if ep_num_match:
        ep_num = ep_num_match.group(1)
        candidate = da_path.parent / f"ep{ep_num}-asset-list.md"
        if candidate.exists():
            asset_list_path = candidate
        else:
            asset_list_path = None
    else:
        asset_list_path = None
    needed_refs = extract_references_from_director_analysis(da_path, asset_list_path)

    # 解析 al_refs (若 asset_list 存在)
    al_refs = set()
    if asset_list_path and asset_list_path.exists():
        al_refs = extract_references_from_assets(asset_list_path)

    # 解析 assets 库
    existing_persons = extract_references_from_assets(
        assets_dir / "character-prompts.md")
    existing_scenes = extract_references_from_assets(
        assets_dir / "scene-prompts.md")
    existing_props = extract_references_from_assets(
        assets_dir / "prop-prompts.md")
    existing_all = existing_persons | existing_scenes | existing_props

    # 比对
    # missing = 本集实际需要 - assets 库已存在 = 需新增
    # 若提供 al_refs, 以 al_refs 为 ground truth (讲戏本可能漏提取)
    if asset_list_path and asset_list_path.exists():
        ground_truth = al_refs
    else:
        ground_truth = needed_refs
    needed_set = ground_truth - existing_all
    existing_used = ground_truth & existing_all

    # 按类型分类(启发式:已知前缀)
    # 由于讲戏本不区分人物/场景/道具,粗分靠 @名字判断:
    # 人物通常是人名(如赵峰/李大哥),场景通常是地点(如赵峰家院子/办公室),道具通常是物品(如蘑菇/松茸)
    # 本脚本只粗略给出 missing_refs 总集,主会话人工判断派 art-designer

    decision = "SKIP" if not needed_set else "NEEDED"

    summary = {
        "decision": decision,
        "missing_refs": sorted(needed_set),
        "existing_used": sorted(existing_used),
        "existing_persons": sorted(existing_persons),
        "existing_scenes": sorted(existing_scenes),
        "existing_props": sorted(existing_props),
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"=== 阶段三决策: {decision} ===")
        print(f"讲戏本 @引用总数: {len(needed_refs)}")
        print(f"  已存在(复用): {len(existing_used)}")
        print(f"  缺失(需新增): {len(needed_set)}")
        if needed_set:
            print(f"缺失列表: {sorted(needed_set)}")
        print(f"\n人物库现有: {sorted(existing_persons)}")
        print(f"场景库现有: {sorted(existing_scenes)}")
        print(f"道具库现有: {sorted(existing_props)}")

    sys.exit(0 if decision == "SKIP" else 1)


if __name__ == "__main__":
    main()

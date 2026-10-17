#!/usr/bin/env python3
"""
gen_html_view.py —— 将即梦分镜 .md 转换为视觉增强的 HTML 阅读版

用法:
    python gen_html_view.py <02-jimeng-prompts.md路径>

输出:
    同目录下生成 02-jimeng-prompts-view.html

特性:
    - 浅色高对比度主题，字色清晰
    - 每个字段用色彩标签区分（景别=蓝, 运镜=紫, 机位=青, 画面=红, 微表情=橙, 台词=绿, 音效=灰）
    - 台词深绿加粗高亮，@角色名深蓝加粗
    - 每个子镜头带一键复制按钮（复制纯文本7字段）
    - 每个母镜头带"复制全部"按钮
    - 左侧固定导航栏：母镜头跳转列表，每项旁带独立复制按钮
    - 纯前端，无外部依赖
"""

import re
import sys
import os
import html as html_module
import base64
from pathlib import Path


# ── 字段色彩配置（深色标签 + 浅色内容背景）──
FIELD_STYLES = {
    "景别":   {"label_bg": "#1e40af", "content_bg": "rgba(59,130,246,.13)", "icon": "📷"},
    "运镜":   {"label_bg": "#6d28d9", "content_bg": "rgba(139,92,246,.13)", "icon": "🎬"},
    "机位":   {"label_bg": "#0f766e", "content_bg": "rgba(20,184,166,.13)", "icon": "🎯"},
    "画面":   {"label_bg": "#b91c1c", "content_bg": "rgba(229,72,77,.13)", "icon": "🖼️"},
    "微表情": {"label_bg": "#c2410c", "content_bg": "rgba(249,115,22,.13)", "icon": "😐"},
    "台词":   {"label_bg": "#15803d", "content_bg": "rgba(34,197,94,.13)", "icon": "💬"},
    "音效":   {"label_bg": "#4b5563", "content_bg": "rgba(255,255,255,.05)", "icon": "🔊"},
}

SCENE_TYPE_COLORS = {
    "对话场景": "#1e40af",
    "动作场景": "#b91c1c",
    "情绪场景": "#6d28d9",
    "揭示场景": "#c2410c",
    "过渡场景": "#4b5563",
}


def parse_md(filepath: str) -> dict:
    """解析即梦分镜 .md 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = {
        "title": "",
        "assets": [],
        "mother_shots": [],
    }

    # 标题
    title_match = re.match(r"#\s*(.+)", content)
    if title_match:
        result["title"] = title_match.group(1).strip()

    # 素材对应表
    asset_lines = re.findall(r"\|\s*(@[\w\u4e00-\u9fff\-]+)\s*\|\s*([\w\u4e00-\u9fff]+)\s*\|\s*([\w.\u4e00-\u9fff\-]+)\s*\|\s*(.+?)\s*\|", content)
    for ref, typ, src, note in asset_lines:
        result["assets"].append({"ref": ref, "type": typ, "src": src, "note": note})

    # 母镜头
    shot_blocks = re.split(r"\n## 母镜头", content)[1:]
    for block in shot_blocks:
        shot = {"id": "", "duration": "", "title": "", "scene_type": "", "transition": "", "style": "", "assets_line": "", "sub_shots": [], "raw_block": block}

        # 母镜头ID和标题（支持 1A-prep、3A2 等格式）
        header_match = re.match(r"(\d+[A-Z]?\d*(?:-[a-zA-Z]+)?)（总时长：(\d+(?:\.\d+)?)秒）\s*——\s*(.+)", block)
        if header_match:
            shot["id"] = header_match.group(1)
            shot["duration"] = header_match.group(2)
            shot["title"] = header_match.group(3).strip()

        # 场景类型
        st_match = re.search(r"\*\*场景类型\*\*[：:]\s*(.+)", block)
        if st_match:
            shot["scene_type"] = st_match.group(1).strip()

        # 分镜过渡
        tr_match = re.search(r"\*\*分镜过渡\*\*[：:]\s*(.+?)(?=\n\n|\n画面风格)", block, re.DOTALL)
        if tr_match:
            shot["transition"] = tr_match.group(1).strip()

        # 全局风格
        style_match = re.search(r"(画面风格为原生.+?)(?=\n\n人物[：:])", block, re.DOTALL)
        if style_match:
            shot["style"] = style_match.group(1).strip()

        # 资产声明行（用 [^\n]+ 匹配到行尾，避免非贪婪 .+? 只匹配一个字符）
        asset_match = re.search(r"人物[：：][^\n]+\| 场景[：：][^\n]+(?:\| 道具[：：][^\n]+)?", block)
        if asset_match:
            shot["assets_line"] = asset_match.group(0).strip()

        # 子镜头
        sub_blocks = re.split(r"### 子镜头", block)[1:]
        for sub_block in sub_blocks:
            sub = {"id": "", "duration": "", "fields": {}, "raw_text": ""}

            sub_header = re.match(r"(\d+)（时长[：:]⏱([\d.]+)s 秒）[：:]", sub_block)
            if sub_header:
                sub["id"] = sub_header.group(1)
                sub["duration"] = sub_header.group(2)

            # 保存原始纯文本（用于复制）
            # 截取到下一个子镜头或文件末尾
            raw_end = re.search(r"\n---\s*$", sub_block)
            if raw_end:
                sub["raw_text"] = sub_block[:raw_end.start()].strip()
            else:
                sub["raw_text"] = sub_block.strip()

            # 提取7个字段
            for field_name in FIELD_STYLES.keys():
                pattern = rf"【{field_name}】(.*?)(?=\n【|\n###|\n---|\Z)"
                field_match = re.search(pattern, sub_block, re.DOTALL)
                if field_match:
                    sub["fields"][field_name] = field_match.group(1).strip()
                else:
                    sub["fields"][field_name] = "无"

            shot["sub_shots"].append(sub)

        result["mother_shots"].append(shot)

    return result


def parse_panorama(filepath: str) -> dict:
    """解析全景站位分镜 .md 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = {
        "title": "",
        "scene": "",
        "characters": [],
        "total_duration": 0,
        "shots": [],
    }

    # 标题
    title_match = re.match(r"(.+?)(?:\n|$)", content)
    if title_match:
        result["title"] = title_match.group(1).strip()

    # 场景
    scene_match = re.search(r"场景[：:]\s*(.+)", content)
    if scene_match:
        result["scene"] = scene_match.group(1).strip()

    # 出场人物
    char_match = re.search(r"出场人物[：:]\s*(.+)", content)
    if char_match:
        chars = re.findall(r"@[\w\u4e00-\u9fff]+", char_match.group(1))
        result["characters"] = chars

    # 总时长
    dur_match = re.search(r"总时长[：:]\s*(\d+)", content)
    if dur_match:
        result["total_duration"] = int(dur_match.group(1))

    # 各时间轴镜头
    shot_blocks = re.split(r"\n镜头\d+", content)[1:]
    for block in shot_blocks:
        shot = {"time_range": "", "scene": "", "shot_size": "", "blocking": "", "description": "", "duration": ""}

        # 时间范围
        time_match = re.match(r"[（(](\d+-\d+秒)[）)]", block)
        if time_match:
            shot["time_range"] = time_match.group(1)

        # 所属场景
        sc_match = re.search(r"所属场景[：:]\s*(.+)", block)
        if sc_match:
            shot["scene"] = sc_match.group(1).strip()

        # 景别
        ss_match = re.search(r"景别[：:]\s*(.+)", block)
        if ss_match:
            shot["shot_size"] = ss_match.group(1).strip()

        # 人物站位
        bl_match = re.search(r"人物站位[：:]\s*(.+)", block)
        if bl_match:
            shot["blocking"] = bl_match.group(1).strip()

        # 画面描述
        desc_match = re.search(r"画面描述[：:]\s*(.+)", block)
        if desc_match:
            shot["description"] = desc_match.group(1).strip()

        # 时长
        dur_match = re.search(r"时长[：:]⏱([\d.]+)s", block)
        if dur_match:
            shot["duration"] = dur_match.group(1)

        result["shots"].append(shot)

    return result


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    return html_module.escape(text)


def to_b64(text: str) -> str:
    """将文本编码为 base64（用于安全传递给 JS，避免引号/换行转义问题）"""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def split_picture(text: str) -> list:
    """
    【画面】字段按 @ 标记分割：
    - @场景名 开头 = 场景描述（一句话）
    - @角色名 开头 = 角色动作（另一句话）
    第一段不加换行，后续每段独占一行。
    """
    # 按 @ 分割（保留 @ 在每段开头）
    parts = re.split(r'(?=@)', text)
    # 清理每段首尾的逗号和空格
    result = []
    for p in parts:
        p = p.strip().strip(',').strip()
        if p:
            result.append(p)
    return result


def split_sound(text: str) -> list:
    """
    【音效】字段按 ] 后的逗号分割：
    - 环境音: [...] = 一句话
    - 拟音: [...] = 一句话
    - 人物发声: [...] = 一句话
    方括号内的逗号不拆分。
    """
    # 按 ], 分割
    parts = re.split(r'\],\s*', text)
    result = []
    for i, p in enumerate(parts):
        p = p.strip()
        if not p:
            continue
        # 除最后一段外，补回 ]
        if i < len(parts) - 1:
            p = p + ']'
        result.append(p)
    return result


def highlight_refs(text: str) -> str:
    """转义 HTML + 高亮 @引用"""
    escaped = escape_html(text)
    escaped = re.sub(r"(@[\w\u4e00-\u9fff\-]+)", r'<span class="char-ref">\1</span>', escaped)
    return escaped


def format_dialogue(text: str) -> str:
    """格式化台词：高亮角色名和台词内容（不分行）"""
    escaped = escape_html(text)
    escaped = re.sub(r"(@[\w\u4e00-\u9fff]+)", r'<span class="char-ref">\1</span>', escaped)
    escaped = re.sub(r"「(.+?)」", r'<span class="dialogue-text">「\1」</span>', escaped)
    escaped = re.sub(r"（(.+?)）", r'<span class="emotion-tag">（\1）</span>', escaped)
    return escaped


def format_field(text: str, field_name: str) -> str:
    """
    字段格式化策略：
    - 【台词】：不分行，高亮显示
    - 【画面】：按 @ 标记分行，每段是一个完整的视觉描述
    - 【音效】：按 ] 分行，每个声音类别独占一行
    - 其他字段（景别/运镜/机位/微表情）：不分行，只高亮 @引用
    """
    if text == "无":
        return '<span class="empty-field">无</span>'

    if field_name == "台词":
        return format_dialogue(text)

    if field_name == "画面":
        segments = split_picture(text)
        return '<br>\n'.join(highlight_refs(s) for s in segments)

    if field_name == "音效":
        segments = split_sound(text)
        return '<br>\n'.join(highlight_refs(s) for s in segments)

    # 其他短字段：不分行
    return highlight_refs(text)


def build_sub_copy_text(sub: dict) -> str:
    """构建子镜头纯文本（用于复制）"""
    lines = [f"子镜头{sub['id']}（时长：⏱{sub['duration']}s 秒）："]
    for field_name in FIELD_STYLES.keys():
        value = sub["fields"].get(field_name, "无")
        lines.append(f"【{field_name}】{value}")
    return "\n".join(lines)


def build_shot_copy_text(shot: dict) -> str:
    """构建母镜头完整纯文本（用于复制）"""
    lines = []
    lines.append(f"母镜头{shot['id']}（总时长：{shot['duration']}秒）—— {shot['title']}")
    lines.append(f"场景类型：{shot['scene_type']}")
    lines.append(f"分镜过渡：{shot['transition']}")
    lines.append(f"{shot['style']}")
    lines.append(f"{shot['assets_line']}")
    lines.append("")
    for sub in shot["sub_shots"]:
        lines.append(build_sub_copy_text(sub))
        lines.append("")
    return "\n".join(lines).strip()


def build_pano_shot_copy_text(shot: dict, idx: int) -> str:
    """构建全景站位单镜头纯文本（用于复制）"""
    lines = [
        f"镜头{idx+1}（{shot['time_range']}）",
        f"所属场景：{shot['scene']}",
        f"景别：{shot['shot_size']}",
        f"人物站位：{shot['blocking']}",
        f"画面描述：{shot['description']}",
        f"时长：⏱{shot['duration']}s",
    ]
    return "\n".join(lines)


def build_pano_all_copy_text(pano_data: dict) -> str:
    """构建全景站位完整纯文本（用于复制）"""
    lines = [
        pano_data["title"],
        f"场景：{pano_data['scene']}",
        f"出场人物：{'、'.join(pano_data['characters'])}",
        f"总时长：{pano_data['total_duration']}秒",
        "",
    ]
    for i, shot in enumerate(pano_data["shots"]):
        lines.append(build_pano_shot_copy_text(shot, i))
        lines.append("")
    return "\n".join(lines).strip()


def generate_panorama_html(pano_data: dict) -> str:
    """生成全景站位视图 HTML"""
    if not pano_data or not pano_data.get("shots"):
        return '<div class="panorama-empty">未提供全景站位数据</div>'

    # 基本信息
    chars_html = ""
    for c in pano_data["characters"]:
        chars_html += f'<span class="pano-char-chip">{escape_html(c)}</span>\n'

    # 时间轴条
    timeline_segments = ""
    for i, shot in enumerate(pano_data["shots"]):
        pct = 100.0 / len(pano_data["shots"])
        timeline_segments += f'''<div class="timeline-seg" style="width:{pct}%" onclick="scrollToPano({i})">
            <span class="timeline-time">{escape_html(shot["time_range"])}</span>
        </div>'''

    # 各时间轴镜头卡片
    shots_html = ""
    for i, shot in enumerate(pano_data["shots"]):
        # 人物站位：按中文逗号分割为独立段落，高亮 @引用
        blocking_parts = [p.strip() for p in shot["blocking"].split("，") if p.strip()]
        blocking_html = '<br>\n'.join(highlight_refs(p) for p in blocking_parts) if blocking_parts else highlight_refs(shot["blocking"])

        # 画面描述：按中文逗号分割，高亮 @引用
        desc_parts = [p.strip() for p in shot["description"].split("，") if p.strip()]
        desc_html = '<br>\n'.join(highlight_refs(p) for p in desc_parts) if desc_parts else highlight_refs(shot["description"])

        # 复制按钮
        pano_shot_copy = build_pano_shot_copy_text(shot, i)
        pano_shot_b64 = to_b64(pano_shot_copy)

        shots_html += f'''
        <div class="pano-shot-card" id="pano-shot-{i}">
            <div class="pano-shot-header">
                <span class="pano-time-badge">{escape_html(shot["time_range"])}</span>
                <span class="pano-shot-size">{escape_html(shot["shot_size"])}</span>
                <span class="pano-dur-badge">⏱ {escape_html(shot["duration"])}s</span>
                <button class="copy-btn copy-shot-btn" onclick="copyB64(this, '{pano_shot_b64}')" title="复制此镜头">📋 复制</button>
            </div>
            <div class="pano-field-row">
                <div class="pano-field-label" style="background:#0f766e">人物站位</div>
                <div class="pano-field-content" style="background:rgba(20,184,166,.13)">{blocking_html}</div>
            </div>
            <div class="pano-field-row">
                <div class="pano-field-label" style="background:#b91c1c">画面描述</div>
                <div class="pano-field-content" style="background:rgba(229,72,77,.13)">{desc_html}</div>
            </div>
        </div>'''

    # 全景"复制全部"按钮
    pano_all_copy = build_pano_all_copy_text(pano_data)
    pano_all_b64 = to_b64(pano_all_copy)
    pano_all_btn = f'<button class="copy-btn copy-shot-btn" onclick="copyB64(this, \'{pano_all_b64}\')" title="复制全景站位全部内容">📋 复制全部</button>'

    return f'''
<div class="panorama-view">
    <div class="pano-info-card" id="pano-info-top">
        <div class="pano-info-row">
            <span class="pano-info-label">场景</span>
            <span class="pano-info-value">{escape_html(pano_data["scene"])}</span>
        </div>
        <div class="pano-info-row">
            <span class="pano-info-label">出场人物</span>
            <div class="pano-char-list">{chars_html}</div>
        </div>
        <div class="pano-info-row">
            <span class="pano-info-label">总时长</span>
            <span class="pano-info-value">{pano_data["total_duration"]}秒</span>
        </div>
        <div class="pano-info-row" style="margin-left:auto">
            {pano_all_btn}
        </div>
    </div>

    <div class="pano-timeline">
        {timeline_segments}
    </div>

    <div class="pano-shots-container">
        {shots_html}
    </div>
</div>'''


def generate_html(data: dict, pano_data: dict = None) -> str:
    """生成完整 HTML（含 Tab 切换）"""
    title = data["title"]

    # 素材对应表
    assets_html = ""
    for a in data["assets"]:
        type_color = {"人物": "#1e40af", "场景": "#c2410c", "道具": "#6d28d9"}.get(a["type"], "#4b5563")
        assets_html += f'<span class="asset-chip">{escape_html(a["ref"])} <span class="asset-type">{escape_html(a["type"])}</span></span>\n'

    # 母镜头
    shots_html = ""
    for shot in data["mother_shots"]:
        scene_color = SCENE_TYPE_COLORS.get(shot["scene_type"], "#4b5563")
        shot_copy_text = build_shot_copy_text(shot)
        shot_b64 = to_b64(shot_copy_text)

        # 子镜头
        subs_html = ""
        for sub in shot["sub_shots"]:
            sub_copy_text = build_sub_copy_text(sub)
            sub_b64 = to_b64(sub_copy_text)

            fields_html = ""
            for field_name, style in FIELD_STYLES.items():
                value = sub["fields"].get(field_name, "无")
                formatted = format_field(value, field_name)
                fields_html += f'''
                <div class="field-row" style="border-left:4px solid {style["label_bg"]}">
                    <div class="field-label" style="background:{style["label_bg"]}">
                        <span class="field-icon">{style["icon"]}</span>
                        <span class="field-name">{field_name}</span>
                    </div>
                    <div class="field-content" style="background:{style["content_bg"]}">
                        {formatted}
                    </div>
                </div>'''

            subs_html += f'''
            <div class="sub-shot-card">
                <div class="sub-shot-header">
                    <span class="sub-shot-num">子镜头{sub["id"]}</span>
                    <span class="sub-shot-duration">⏱ {sub["duration"]}s</span>
                    <button class="copy-btn" onclick="copyB64(this, '{sub_b64}')" title="复制此子镜头">📋 复制</button>
                </div>
                <div class="fields-grid">
                    {fields_html}
                </div>
            </div>'''

        # 资产声明行格式化
        assets_line_html = escape_html(shot["assets_line"]).replace("|", '<span class="asset-sep">|</span>')

        shots_html += f'''
        <div class="mother-shot-card" id="shot-{shot["id"]}">
            <div class="shot-header" style="border-left:5px solid {scene_color}">
                <div class="shot-title-row">
                    <span class="shot-num">母镜头{shot["id"]}</span>
                    <span class="shot-title">{escape_html(shot["title"])}</span>
                    <span class="shot-duration-badge">{shot["duration"]}秒</span>
                    <span class="scene-type-badge" style="background:{scene_color}">{escape_html(shot["scene_type"])}</span>
                    <button class="copy-btn copy-shot-btn" onclick="copyB64(this, '{shot_b64}')" title="复制此母镜头全部内容">📋 复制全部</button>
                </div>
            </div>
            <div class="shot-transition">
                <span class="transition-label">分镜过渡</span>
                <span class="transition-text">{escape_html(shot["transition"])}</span>
            </div>
            <details class="style-details">
                <summary>全局风格设定</summary>
                <div class="style-text">{escape_html(shot["style"])}</div>
            </details>
            <div class="assets-line">{assets_line_html}</div>
            <div class="sub-shots-container">
                {subs_html}
            </div>
        </div>'''

    total_subs = sum(len(s["sub_shots"]) for s in data["mother_shots"])
    total_dur = sum(float(s["duration"]) for s in data["mother_shots"])

    # 左侧导航栏：母镜头跳转列表 + 每项复制按钮
    nav_items = ""
    for shot in data["mother_shots"]:
        shot_copy_text = build_shot_copy_text(shot)
        shot_b64 = to_b64(shot_copy_text)
        scene_color = SCENE_TYPE_COLORS.get(shot["scene_type"], "#4b5563")
        nav_items += f'''
        <div class="nav-item">
            <a href="#shot-{shot["id"]}" class="nav-link" style="--scene-color:{scene_color}" onclick="exitNavOnly()">
                <span class="nav-top">
                    <span class="nav-num">母{shot["id"]}</span>
                    <span class="nav-dur">{shot["duration"]}s</span>
                </span>
                <span class="nav-title">{escape_html(shot["title"])}</span>
            </a>
            <button class="copy-btn nav-copy-btn" onclick="copyB64(this, '{shot_b64}')" title="复制此母镜头全部内容">📋</button>
        </div>'''

    # 生成全景站位 HTML（如果提供了全景数据）
    pano_html = generate_panorama_html(pano_data) if pano_data else ""
    pano_tab_div = ('<div id="tab-panorama" class="tab-content">' + pano_html + '</div>') if pano_data else ""

    # 全景站位侧边栏导航项
    pano_nav_items = ""
    pano_sidebar_section = ""
    if pano_data:
        pano_all_copy = build_pano_all_copy_text(pano_data)
        pano_all_b64 = to_b64(pano_all_copy)
        # 全景总项（带复制全部按钮，点击跳转到全景顶部）
        pano_nav_items = f'''
        <div class="nav-item">
            <a href="#pano-info-top" class="nav-link" style="--scene-color:#0f766e" onclick="switchTab('panorama'); exitNavOnly()">
                <span class="nav-top">
                    <span class="nav-num">全景</span>
                    <span class="nav-dur">{pano_data["total_duration"]}s</span>
                </span>
                <span class="nav-title">整集调度关系</span>
            </a>
            <button class="copy-btn nav-copy-btn" onclick="copyB64(this, '{pano_all_b64}')" title="复制全景站位全部内容">📋</button>
        </div>'''
        # 各时间片段导航项（可点击跳转到对应镜头）
        for i, shot in enumerate(pano_data["shots"]):
            pano_shot_copy = build_pano_shot_copy_text(shot, i)
            pano_shot_b64 = to_b64(pano_shot_copy)
            pano_nav_items += f'''
        <div class="nav-item">
            <a href="#pano-shot-{i}" class="nav-link pano-sub-nav" style="--scene-color:#14b8a6" onclick="switchTab('panorama'); exitNavOnly()">
                <span class="nav-top">
                    <span class="nav-num">镜头{i+1}</span>
                    <span class="nav-dur">{escape_html(shot["time_range"])}</span>
                </span>
                <span class="nav-title">{escape_html(shot["shot_size"])}</span>
            </a>
            <button class="copy-btn nav-copy-btn" onclick="copyB64(this, '{pano_shot_b64}')" title="复制此镜头">📋</button>
        </div>'''
        pano_sidebar_section = f'''
    <div class="nav-list pano-nav-list" id="pano-nav-list" style="display:none">
        {pano_nav_items}
    </div>'''

    # 视图切换器（放在侧边栏头部下方）
    view_switcher_html = ""
    if pano_data:
        view_switcher_html = '<div class="view-switcher"><button class="view-btn active" onclick="switchTab(\'storyboard\', this)">📋 分镜视图</button><button class="view-btn" onclick="switchTab(\'panorama\', this)">🗺️ 全景站位</button></div>'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape_html(title)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{
    scroll-padding-top: 110px;
}}
body {{
    font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #141414;
    color: #f0f0f0;
    line-height: 1.7;
    padding: 0;
}}

/* ── 左侧导航栏 ── */
.sidebar {{
    position: fixed;
    top: 0;
    left: 0;
    width: 190px;
    height: 100vh;
    background: #1c1c1c;
    border-right: 2px solid rgba(255,255,255,.16);
    overflow-y: auto;
    z-index: 200;
    box-shadow: 2px 0 8px rgba(0,0,0,.4);
    transition: transform 0.25s ease;
}}
.sidebar-header {{
    padding: 12px 12px 10px;
    border-bottom: 2px solid rgba(255,255,255,.09);
    position: sticky;
    top: 0;
    background: #1c1c1c;
    z-index: 2;
}}
.sidebar-title {{
    font-size: 14px;
    font-weight: 700;
    color: #f2f2f2;
}}
.sidebar-count {{
    display: block;
    font-size: 11px;
    color: #9a9a9a;
    margin-top: 2px;
}}
.nav-list {{
    padding: 6px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}}
.nav-item {{
    display: flex;
    align-items: center;
    gap: 4px;
}}
.nav-link {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 6px 8px;
    border-radius: 6px;
    text-decoration: none;
    border-left: 3px solid var(--scene-color, #4b5563);
    background: #242424;
    transition: background 0.15s;
    min-width: 0;
}}
.nav-link:hover {{
    background: #2e2e2e;
}}
.nav-top {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    width: 100%;
    gap: 4px;
}}
.nav-num {{
    font-size: 12px;
    font-weight: 700;
    color: #f2f2f2;
    white-space: nowrap;
    flex-shrink: 0;
}}
.nav-dur {{
    font-size: 10px;
    font-weight: 600;
    color: #e0a04a;
    white-space: nowrap;
    flex-shrink: 0;
}}
.nav-title {{
    font-size: 11px;
    color: #d9d9d9;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    width: 100%;
    line-height: 1.4;
}}
.nav-copy-btn {{
    padding: 3px 6px;
    font-size: 12px;
    flex-shrink: 0;
}}
.pano-sub-nav {{
    margin-left: 14px;
    border-left-width: 2px !important;
    opacity: 0.9;
}}
.sidebar-toggle {{
    position: fixed;
    left: 198px;
    top: 92px;
    z-index: 250;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #e5484d;
    color: white;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,.45);
    transition: left 0.25s ease, top 0.25s ease;
    border: none;
}}
.sidebar-toggle:hover {{
    background: #c63b3f;
}}
.main-area {{
    margin-left: 190px;
    transition: margin-left 0.25s ease;
}}
body.sidebar-collapsed .sidebar {{
    transform: translateX(-100%);
}}
body.sidebar-collapsed .sidebar-toggle {{
    left: 8px;
}}
body.sidebar-collapsed .main-area {{
    margin-left: 0;
}}

/* ── 顶部标题栏 ── */
.page-header {{
    background: #1c1c1c;
    border-bottom: 2px solid rgba(255,255,255,.16);
    padding: 14px 40px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,.4);
}}
.page-header h1 {{
    font-size: 18px;
    font-weight: 700;
    color: #f2f2f2;
    margin-bottom: 4px;
}}
.asset-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
}}
.asset-bar-label {{
    font-size: 11px;
    color: #8a8a8a;
    margin-right: 2px;
    font-weight: 500;
}}
.asset-chip {{
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 1px 6px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,.09);
    font-size: 10px;
    font-weight: 500;
    color: #9a9a9a;
    background: #242424;
}}
.asset-type {{
    font-size: 9px;
    opacity: 0.5;
}}

/* ── 统计栏 ── */
.stats-bar {{
    display: flex;
    gap: 24px;
    padding: 10px 40px;
    background: rgba(255,255,255,.09);
    border-bottom: 1px solid rgba(255,255,255,.16);
    font-size: 13px;
    color: #c0c0c0;
    font-weight: 500;
}}
.stat-item {{
    display: flex;
    align-items: center;
    gap: 6px;
}}
.stat-value {{
    color: #f2f2f2;
    font-weight: 700;
    font-size: 15px;
}}

/* ── 母镜头卡片 ── */
.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px 40px 60px;
}}
.mother-shot-card {{
    background: #1c1c1c;
    border-radius: 10px;
    margin-bottom: 20px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.16);
    box-shadow: 0 2px 8px rgba(0,0,0,.4);
}}
.shot-header {{
    border-left: 5px solid;
    padding: 14px 20px;
    background: #242424;
    border-bottom: 1px solid rgba(255,255,255,.09);
}}
.shot-title-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}}
.shot-num {{
    font-size: 17px;
    font-weight: 700;
    color: #f2f2f2;
    padding: 3px 10px;
    border-radius: 6px;
    background: rgba(255,255,255,.09);
}}
.shot-title {{
    font-size: 15px;
    font-weight: 600;
    color: #f2f2f2;
    flex: 1;
}}
.shot-duration-badge {{
    font-size: 13px;
    font-weight: 700;
    color: #e0a04a;
    padding: 3px 10px;
    border-radius: 12px;
    background: rgba(224,160,74,.15);
    border: 1px solid rgba(224,160,74,.4);
}}
.scene-type-badge {{
    font-size: 12px;
    font-weight: 600;
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
}}

/* ── 复制按钮 ── */
.copy-btn {{
    font-size: 12px;
    font-weight: 600;
    color: #ff8589;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1.5px solid #e5484d;
    background: rgba(229,72,77,.14);
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
}}
.copy-btn:hover {{
    background: #e5484d;
    color: white;
}}
.copy-btn:active {{
    transform: scale(0.95);
}}
.copy-btn.copied {{
    background: #15803d;
    color: white;
    border-color: #15803d;
}}
.copy-shot-btn {{
    margin-left: auto;
}}

/* ── 分镜过渡 ── */
.shot-transition {{
    padding: 10px 20px;
    background: rgba(139,92,246,.08);
    border-bottom: 1px solid rgba(255,255,255,.09);
    display: flex;
    gap: 10px;
    align-items: flex-start;
}}
.transition-label {{
    font-size: 12px;
    font-weight: 700;
    color: #6d28d9;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(139,92,246,.16);
    white-space: nowrap;
    flex-shrink: 0;
}}
.transition-text {{
    font-size: 13px;
    color: #c4b0fb;
    line-height: 1.6;
}}

/* ── 全局风格（折叠） ── */
.style-details {{
    padding: 0 20px;
    border-bottom: 1px solid rgba(255,255,255,.09);
}}
.style-details summary {{
    padding: 8px 0;
    cursor: pointer;
    font-size: 12px;
    color: #9a9a9a;
    font-weight: 500;
    user-select: none;
}}
.style-details summary:hover {{
    color: #d9d9d9;
}}
.style-text {{
    padding: 8px 0 12px;
    font-size: 12px;
    color: #9a9a9a;
    line-height: 1.6;
    word-break: break-all;
}}

/* ── 资产声明行 ── */
.assets-line {{
    padding: 8px 20px;
    font-size: 12px;
    color: #c0c0c0;
    background: #242424;
    border-bottom: 1px solid rgba(255,255,255,.09);
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-weight: 500;
}}
.asset-sep {{
    color: #8a8a8a;
    margin: 0 6px;
    font-weight: 700;
}}

/* ── 子镜头容器 ── */
.sub-shots-container {{
    padding: 14px 20px;
    display: grid;
    gap: 14px;
}}

/* ── 子镜头卡片 ── */
.sub-shot-card {{
    background: #1c1c1c;
    border-radius: 8px;
    overflow: hidden;
    border: 1.5px solid rgba(255,255,255,.09);
}}
.sub-shot-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    background: #141414;
    border-bottom: 1px solid rgba(255,255,255,.09);
}}
.sub-shot-num {{
    font-size: 14px;
    font-weight: 700;
    color: #f2f2f2;
}}
.sub-shot-duration {{
    font-size: 13px;
    font-weight: 700;
    color: #e0a04a;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(224,160,74,.15);
}}

/* ── 字段网格 ── */
.fields-grid {{
    display: grid;
    gap: 2px;
    background: rgba(255,255,255,.09);
}}
.field-row {{
    display: flex;
    min-height: 38px;
}}
.field-label {{
    width: 88px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6px 4px;
    color: white;
    font-weight: 700;
    gap: 1px;
}}
.field-icon {{
    font-size: 15px;
    line-height: 1;
}}
.field-name {{
    font-size: 13px;
    line-height: 1.2;
}}
.field-content {{
    flex: 1;
    min-width: 0;
    padding: 9px 14px;
    font-size: 14px;
    color: #f0f0f0;
    line-height: 1.9;
    word-break: break-all;
    overflow-wrap: break-word;
    font-weight: 500;
}}

/* ── 特殊元素高亮（深色高饱和，确保清晰）── */
.char-ref {{
    color: #7ea4ff;
    font-weight: 700;
}}
.dialogue-text {{
    color: #15803d;
    font-weight: 700;
}}
.emotion-tag {{
    color: #c2410c;
    font-size: 13px;
    font-weight: 600;
}}
.empty-field {{
    color: #8a8a8a;
    font-style: italic;
    font-weight: 400;
}}

/* ── 响应式 ── */
@media (max-width: 768px) {{
    .sidebar {{ width: 190px; }}
    .main-area {{ margin-left: 0; }}
    .sidebar-toggle {{ left: 8px; }}
    .sidebar {{ transform: translateX(-100%); }}
    .container {{ padding: 16px; }}
    .page-header {{ padding: 12px 16px; }}
    .stats-bar {{ padding: 10px 16px; flex-wrap: wrap; gap: 12px; }}
    .field-label {{ width: 64px; }}
    .field-name {{ font-size: 11px; }}
    .field-content {{ font-size: 13px; padding: 6px 10px; }}
    .shot-title-row {{ gap: 8px; }}
    .shot-num {{ font-size: 15px; }}
    .shot-title {{ font-size: 14px; }}
}}

/* ── 侧边栏视图切换器 ── */
.view-switcher {{
    display: flex;
    gap: 0;
    padding: 6px 8px;
    border-bottom: 2px solid rgba(255,255,255,.09);
}}
.view-btn {{
    flex: 1;
    padding: 7px 4px;
    font-size: 12px;
    font-weight: 600;
    color: #9a9a9a;
    border: 1.5px solid rgba(255,255,255,.16);
    background: #242424;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.2s;
    font-family: inherit;
    text-align: center;
}}
.view-btn:first-child {{
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
}}
.view-btn:last-child {{
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}}
.view-btn:hover {{
    color: #f2f2f2;
    background: #2e2e2e;
}}
.view-btn.active {{
    color: white;
    background: #e5484d;
    border-color: #e5484d;
}}

/* ── Tab 内容区 ── */
.tab-content {{
    display: none;
}}
.tab-content.active {{
    display: block;
}}

/* ── 全景站位视图 ── */
.panorama-view {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px 40px 60px;
}}
.pano-info-card {{
    background: #1c1c1c;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,.16);
    box-shadow: 0 2px 8px rgba(0,0,0,.4);
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    align-items: flex-start;
}}
.pano-info-row {{
    display: flex;
    flex-direction: column;
    gap: 4px;
}}
.pano-info-label {{
    font-size: 11px;
    font-weight: 700;
    color: #9a9a9a;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.pano-info-value {{
    font-size: 14px;
    font-weight: 600;
    color: #f2f2f2;
}}
.pano-char-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}}
.pano-char-chip {{
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 12px;
    border: 1.5px solid #7ea4ff;
    font-size: 12px;
    font-weight: 600;
    color: #7ea4ff;
    background: rgba(59,130,246,.14);
}}

/* ── 时间轴条 ── */
.pano-timeline {{
    display: flex;
    height: 40px;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,.4);
}}
.timeline-seg {{
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 2px solid #1c1c1c;
    cursor: pointer;
    transition: filter 0.15s;
    background: linear-gradient(135deg, #1e40af, #3b82f6);
}}
.timeline-seg:last-child {{
    border-right: none;
}}
.timeline-seg:hover {{
    filter: brightness(1.15);
}}
.timeline-seg:nth-child(even) {{
    background: linear-gradient(135deg, #0f766e, #14b8a6);
}}
.timeline-time {{
    font-size: 12px;
    font-weight: 700;
    color: white;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}}

/* ── 全景镜头卡片 ── */
.pano-shots-container {{
    display: grid;
    gap: 16px;
}}
.pano-shot-card {{
    background: #1c1c1c;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.16);
    box-shadow: 0 2px 8px rgba(0,0,0,.4);
}}
.pano-shot-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 20px;
    background: #242424;
    border-bottom: 1px solid rgba(255,255,255,.09);
}}
.pano-time-badge {{
    font-size: 14px;
    font-weight: 700;
    color: white;
    padding: 4px 12px;
    border-radius: 6px;
    background: #e5484d;
}}
.pano-shot-size {{
    font-size: 12px;
    font-weight: 600;
    color: #c0c0c0;
    padding: 3px 10px;
    border-radius: 12px;
    background: rgba(255,255,255,.09);
}}
.pano-dur-badge {{
    font-size: 13px;
    font-weight: 700;
    color: #e0a04a;
    padding: 3px 10px;
    border-radius: 12px;
    background: rgba(224,160,74,.15);
    border: 1px solid rgba(224,160,74,.4);
    margin-left: auto;
}}
.pano-field-row {{
    display: flex;
    min-height: 38px;
    border-top: 1px solid #141414;
}}
.pano-field-label {{
    width: 88px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px 4px;
    color: white;
    font-weight: 700;
    font-size: 13px;
}}
.pano-field-content {{
    flex: 1;
    min-width: 0;
    padding: 9px 14px;
    font-size: 14px;
    color: #f0f0f0;
    line-height: 1.9;
    word-break: break-all;
    overflow-wrap: break-word;
    font-weight: 500;
}}
.panorama-empty {{
    text-align: center;
    padding: 60px 20px;
    color: #8a8a8a;
    font-size: 16px;
}}

@media (max-width: 768px) {{
    .panorama-view {{ padding: 16px; }}
    .pano-info-card {{ gap: 12px; padding: 12px 16px; }}
    .pano-field-label {{ width: 64px; font-size: 11px; }}
    .pano-field-content {{ font-size: 13px; padding: 6px 10px; }}
    .timeline-time {{ font-size: 10px; }}
}}

/* ── 只看导航模式 ── */
.nav-only-btn {{
    position: absolute;
    top: 36px;
    right: 20px;
    z-index: 10;
    font-size: 13px;
    font-weight: 700;
    color: white;
    padding: 7px 14px;
    border-radius: 8px;
    border: none;
    background: #e5484d;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    transition: all 0.2s;
    font-family: inherit;
}}
.nav-only-btn:hover {{
    background: #c63b3f;
}}
.nav-only-btn.active {{
    background: #b91c1c;
}}
body.nav-only .main-area > .tab-content {{
    display: none !important;
}}
body.nav-only .sidebar {{
    width: 420px;
    transform: translateX(0) !important;
}}
body.nav-only .main-area {{
    margin-left: 420px;
}}
body.nav-only .sidebar-toggle {{
    left: 428px;
}}
body.nav-only .page-header {{
    z-index: 300;
}}
@media (max-width: 768px) {{
    .nav-only-btn {{
        top: 30px;
        right: 8px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    body.nav-only .sidebar {{
        width: 100%;
    }}
    body.nav-only .main-area {{
        margin-left: 0;
    }}
    body.nav-only .sidebar-toggle {{
        display: none;
    }}
}}
</style>
</head>
<body>

<div class="sidebar">
    <div class="sidebar-header">
        <span class="sidebar-title">分镜导航</span>
        <span class="sidebar-count">{len(data["mother_shots"])}个母镜头</span>
    </div>
    {view_switcher_html}
    <div class="nav-list" id="storyboard-nav-list">
        {nav_items}
    </div>
    {pano_sidebar_section}
</div>
<div class="sidebar-toggle" onclick="toggleSidebar()" title="展开/收起导航">☰</div>

<div class="main-area">

<div class="page-header">
    <h1>{escape_html(title)}</h1>
    <div class="asset-bar">
        <span class="asset-bar-label">素材引用：</span>
        {assets_html}
    </div>
    <button class="nav-only-btn" onclick="toggleNavOnly()" title="只看导航：隐藏内容，仅显示导航栏">🧭 只看导航</button>
</div>

<div id="tab-storyboard" class="tab-content active">

<div class="stats-bar">
    <div class="stat-item">母镜头 <span class="stat-value">{len(data["mother_shots"])}</span></div>
    <div class="stat-item">子镜头 <span class="stat-value">{total_subs}</span></div>
    <div class="stat-item">总时长 <span class="stat-value">{total_dur}秒</span></div>
</div>

<div class="container">
{shots_html}
</div>

</div><!-- tab-storyboard -->

{pano_tab_div}

</div><!-- main-area -->

<script>
function copyB64(btn, b64) {{
    // base64 解码为原始文本
    var realText = atob(b64);
    // 处理 UTF-8 中文
    var bytes = new Uint8Array(realText.length);
    for (var i = 0; i < realText.length; i++) {{
        bytes[i] = realText.charCodeAt(i);
    }}
    realText = new TextDecoder("utf-8").decode(bytes);
    
    if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(realText).then(function() {{
            showCopied(btn);
        }}).catch(function() {{
            fallbackCopy(btn, realText);
        }});
    }} else {{
        fallbackCopy(btn, realText);
    }}
}}

function fallbackCopy(btn, text) {{
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    try {{
        document.execCommand("copy");
        showCopied(btn);
    }} catch(e) {{
        alert("复制失败，请手动选择文本复制");
    }}
    document.body.removeChild(ta);
}}

function showCopied(btn) {{
    var oldText = btn.textContent;
    btn.classList.add("copied");
    btn.textContent = "✅ 已复制";
    setTimeout(function() {{
        btn.classList.remove("copied");
        btn.textContent = oldText;
    }}, 1500);
}}

function toggleSidebar() {{
    document.body.classList.toggle("sidebar-collapsed");
}}

function toggleNavOnly() {{
    var body = document.body;
    var on = body.classList.toggle("nav-only");
    var btn = document.querySelector(".nav-only-btn");
    if (btn) {{
        btn.textContent = on ? "✕ 显示内容" : "🧭 只看导航";
        btn.classList.toggle("active", on);
    }}
}}

function exitNavOnly() {{
    if (document.body.classList.contains("nav-only")) {{
        toggleNavOnly();
    }}
}}

function switchTab(tabName, btn) {{
    // 切换视图按钮高亮
    document.querySelectorAll('.view-btn').forEach(function(b) {{
        b.classList.remove('active');
    }});
    if (btn) {{
        btn.classList.add('active');
    }}
    
    // 切换 Tab 内容
    document.querySelectorAll('.tab-content').forEach(function(content) {{
        content.classList.remove('active');
    }});
    var target = document.getElementById('tab-' + tabName);
    if (target) {{
        target.classList.add('active');
    }}
    
    // 切换侧边栏导航列表
    var sbNav = document.getElementById('storyboard-nav-list');
    var panoNav = document.getElementById('pano-nav-list');
    if (sbNav) sbNav.style.display = (tabName === 'storyboard') ? '' : 'none';
    if (panoNav) panoNav.style.display = (tabName === 'panorama') ? '' : 'none';
    
    // 滚动到顶部
    window.scrollTo(0, 0);
}}

function scrollToPano(idx) {{
    var target = document.getElementById('pano-shot-' + idx);
    if (target) {{
        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}
}}
</script>

</body>
</html>'''


def main():
    if len(sys.argv) < 2:
        print("用法: python gen_html_view.py <02-jimeng-prompts.md路径> [00-panorama-blocking.md路径]")
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.exists(md_path):
        print(f"错误: 文件不存在: {md_path}")
        sys.exit(1)

    # 全景站位文件：优先用命令行参数，否则自动检测同目录下的 00-panorama-blocking.md
    pano_path = None
    if len(sys.argv) >= 3:
        pano_path = sys.argv[2]
    else:
        dir_path_auto = os.path.dirname(md_path)
        auto_pano = os.path.join(dir_path_auto, "00-panorama-blocking.md")
        if os.path.exists(auto_pano):
            pano_path = auto_pano

    pano_data = None
    if pano_path and os.path.exists(pano_path):
        pano_data = parse_panorama(pano_path)
        print(f"已加载全景站位: {pano_path}")

    data = parse_md(md_path)
    html = generate_html(data, pano_data)

    # 输出路径
    dir_path = os.path.dirname(md_path)
    base_name = os.path.splitext(os.path.basename(md_path))[0]
    html_path = os.path.join(dir_path, base_name.replace("-jimeng-prompts", "-jimeng-prompts-view") + ".html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"已生成: {html_path}")


if __name__ == "__main__":
    main()

"""
【画面】字段质量校验脚本
扫描分镜文件，检测每个子镜头【画面】字段的违规项。
"""

import re
import sys
import os

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免 ✓/✗/⚠ 触发 UnicodeEncodeError 崩溃
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 禁写词（正则匹配）
BANNED_PATTERNS = {
    "心理词": [
        r"满足感", r"沉浸", r"感到", r"觉得", r"内心", r"情绪",
    ],
    "因果词": [
        r"所以", r"于是", r"但他", r"但他", r"但却", r"因为",
    ],
    "时间词": [
        r"前\d+秒", r"后\d+秒", r"接着", r"随后", r"然后",
    ],
    "画外词": [
        r"窗外传来.*骂", r"画外响起", r"突然炸响", r"窗外突然",
    ],
}

# 句子分隔符（用于计数"几句话说"）
SENTENCE_SEP = re.compile(r"[。；;——]")

# 姿态状态词表（人物站立/坐/蹲/躺等身体状态）
# 静态姿态词：明确的身体姿态
POSTURE_STATIC = [
    "站", "立", "坐", "蹲", "躺", "卧", "跪", "趴", "倚", "靠",
    "弯腰", "俯身", "仰面", "盘腿", "抱膝", "叉腰", "背手", "双手撑",
    "单膝", "直立", "挺身", "席地", "侧身", "猫腰", "探身", "悬空",
    "直起", "跪地", "半蹲", "起身", "坐下", "蹲下", "躺倒", "站稳",
    "站立", "站定", "站着", "蹲着", "坐着", "前倾",
]
# 动态动作词（动作隐含明确姿态）
POSTURE_DYNAMIC = [
    "走", "跑", "奔", "冲", "踱", "迈", "爬", "蹬", "转身", "倒退",
    "急停", "刹住", "扑", "跳", "跨", "追", "退回", "踱步", "飞奔",
    "奔跑", "冲进", "冲出", "追上", "迈步",
    # 2026-08-20 补充同义词（ep55 曾因"蹦起"不在词表被误判姿态缺失）
    "蹦", "蹦起", "跃起", "跳跃", "纵身", "弹起", "蹿", "蹿起",
    "站起", "立起", "挺直", "俯下", "伏低", "缩", "蜷", "撑起",
]

# 素材类型（用于识别画面字段中的人物引用）
PERSON_TYPES = {"人物", "主角", "配角", "角色"}

# 夜戏时间标注词（母镜头头部场景时间标注命中即视为夜戏）
NIGHT_WORDS = ["夜", "深夜", "傍晚", "夜里", "夜晚"]
# 暖黄禁写词（夜戏命中即报错）
WARM_YELLOW_WORDS = ["暖黄"]


def extract_picture_fields(filepath: str, all_person_refs: set) -> list[dict]:
    """从分镜文件提取所有【画面】字段"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配母镜头
    mother_blocks = content.split("## 母镜头")[1:]
    results = []

    for block in mother_blocks:
        # 提取母镜头 ID
        m_match = re.match(r"(\d+)", block)
        m_id = m_match.group(1) if m_match else "?"
        # 夜戏判定：母镜头头部（前200字符）命中夜戏时间词即视为夜戏
        is_night = any(w in block[:200] for w in NIGHT_WORDS)

        # 匹配子镜头
        sub_blocks = re.split(r"### 子镜头", block)
        for i, sub in enumerate(sub_blocks):
            if i == 0:
                continue  # 跳过母镜头头部信息
            sub_match = re.match(r"(\d+)", sub)
            sub_id = sub_match.group(1) if sub_match else "?"

            # 提取【画面】字段
            pic_match = re.search(r"【画面】(.*?)(?=\n【|\n###|\n---)", sub, re.DOTALL)
            if pic_match:
                pic_text = pic_match.group(1).strip()
                # 找出画面字段中出现的人物引用
                person_refs = sorted(
                    ref for ref in re.findall(r"@[\u4e00-\u9fffA-Za-z0-9]+", pic_text)
                    if ref in all_person_refs
                )
                results.append({
                    "mother_id": m_id,
                    "sub_id": sub_id,
                    "text": pic_text,
                    "person_refs": person_refs,
                    "is_night": is_night,
                })

    return results


def extract_person_refs(filepath: str) -> set:
    """从素材对应表提取人物引用名集合（@角色名）"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    person_refs = set()
    in_table = False
    for line in content.splitlines():
        if line.startswith("## 素材对应表"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            in_table = False
        if in_table and line.startswith("|") and "@" in line:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0].startswith("@"):
                if parts[1] in PERSON_TYPES:
                    person_refs.add(parts[0])
    return person_refs


def posture_hit(text: str) -> str | None:
    """检查文本是否命中姿态词，返回命中的词或None"""
    for w in POSTURE_STATIC:
        if w in text:
            return w
    for w in POSTURE_DYNAMIC:
        if w in text:
            return w
    return None


def check_picture(pic: dict) -> list[dict]:
    """检查单个画面字段，返回违规列表"""
    violations = []
    text = pic["text"]
    label = f"母镜头{pic['mother_id']} 子镜头{pic['sub_id']}"

    # 1. 禁写词检查
    for category, patterns in BANNED_PATTERNS.items():
        for pat in patterns:
            matches = re.findall(pat, text)
            for m in matches:
                violations.append({
                    "label": label,
                    "type": f"禁写词({category})",
                    "detail": f"包含「{m}」",
                })

    # 2. 长度检查（超过150字符警告）
    if len(text) > 150:
        violations.append({
            "label": label,
            "type": "长度超标",
            "detail": f"{len(text)}字符（上限150）",
        })

    # 3. 句子数检查（超过2句警告）
    sentences = SENTENCE_SEP.split(text)
    effective_sentences = [s.strip() for s in sentences if s.strip()]
    if len(effective_sentences) > 2:
        violations.append({
            "label": label,
            "type": "句数超标",
            "detail": f"{len(effective_sentences)}句（上限2句）",
        })

    # 4. 同词重复检查
    word_count = {}
    chinese_words = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
    for w in chinese_words:
        word_count[w] = word_count.get(w, 0) + 1
    for word, count in word_count.items():
        if count >= 3:
            violations.append({
                "label": label,
                "type": "同词重复",
                "detail": f"「{word}」出现{count}次",
            })

    # 5. 姿态状态检查（人物出现时必须描述站/坐/蹲等身体状态）
    if pic.get("person_refs"):
        hit = posture_hit(text)
        if not hit:
            refs_str = "、".join(pic["person_refs"])
            violations.append({
                "label": label,
                "type": "姿态缺失",
                "detail": f"人物({refs_str})无站/坐/蹲/躺等身体状态描述",
            })

    # 6. 夜戏暖黄禁写检查
    if pic.get("is_night"):
        for w in WARM_YELLOW_WORDS:
            if w in text:
                violations.append({
                    "label": label,
                    "type": "夜戏暖黄",
                    "detail": f"夜戏画面包含「{w}」，应改为昏黄灯光/油灯昏光/冷暗局部照明",
                })

    return violations


def main():
    if len(sys.argv) < 2:
        print("用法: python check_picture_field.py <分镜文件路径>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        sys.exit(1)

    pictures = extract_picture_fields(filepath, extract_person_refs(filepath))
    if not pictures:
        print("未找到任何【画面】字段，检查文件格式。")
        sys.exit(1)

    all_violations = []
    for pic in pictures:
        all_violations.extend(check_picture(pic))

    print("=" * 70)
    print("【画面】字段质量校验报告")
    print("=" * 70)
    print(f"文件: {filepath}")
    print(f"扫描字段数: {len(pictures)}")
    print(f"发现问题数: {len(all_violations)}")
    print()

    if not all_violations:
        print("✓ 所有画面字段通过检查！")
    else:
        # 按类型分组输出
        by_type = {}
        for v in all_violations:
            t = v["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(v)

        for t, items in by_type.items():
            print(f"[{t}] ({len(items)}处)")
            for item in items:
                print(f"  {item['label']}: {item['detail']}")
            print()

        print(f"⚠ 共发现 {len(all_violations)} 个问题，请修正后重新校验。")

    sys.exit(0 if not all_violations else 1)


if __name__ == "__main__":
    main()

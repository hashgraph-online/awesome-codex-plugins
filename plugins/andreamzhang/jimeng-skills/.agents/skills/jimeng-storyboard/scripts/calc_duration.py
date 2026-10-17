"""
台词时长计算器 v2.0
支持两种模式：

模式一（导演分析台词清单 → 整句时长）：
  python calc_duration.py <输入JSON> <输出JSON>
  输入格式: [{dialogue_id, text, speed, ...}]
  用于阶段一导演分析后，为整句台词计算宏观参考时长。

模式二（分镜文件 → 子镜头级时长校验）：
  python calc_duration.py --from-storyboard <02-jimeng-prompts.md路径>
  从分镜文件直接解析每个子镜头的实际台词文本和语速，计算精确时长，
  对比母镜头声明总时长和子镜头时长之和，输出修正建议。
"""
import json
import re
import math
import sys
import os

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免 ✓/✗/⚠ 触发 UnicodeEncodeError 崩溃
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ── 加载规则 ──
RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'duration-rules.json')
with open(RULES_PATH, 'r', encoding='utf-8') as f:
    rules = json.load(f)

BASE_SPEED = rules['base_speed']['chars_per_second']
COEFFICIENTS = {k: v['coefficient'] for k, v in rules['speed_coefficients'].items()}

# 语速物理上限（字/秒）：超过即不可执行。极快系数 0.7 → 5/0.7≈7字/秒；上限取 11 字/秒（评审基准），
# 用于拦截"长台词塞进短子镜头、靠标‘极快’蒙混"的伪修复（如 49字/3s=16.3字/秒 物理不可能）。
SPEED_CEILING = 11.0


def count_chars(text: str) -> int:
    """计算有效字数（去标点和非汉字，只计中文字符）"""
    cleaned = re.sub(r'[^\u4e00-\u9fff]', '', text)
    return len(cleaned)




def extract_speed(dialogue_line: str) -> str:
    """从台词行中提取语速"""
    # 匹配 "语速XX" 后面跟逗号、顿号或右括号
    match = re.search(r'语速([^,）\)、]+)', dialogue_line)
    if match:
        speed = match.group(1).strip()
        # 处理复合语速如 "中等→快"，取第一个
        if '→' in speed:
            speed = speed.split('→')[0]
        if speed in COEFFICIENTS:
            return speed
    return '中等'


def compute_duration(text: str, speed: str) -> dict:
    """计算单条台词时长（纯字数×语速，零符号依赖）"""
    char_count = count_chars(text)
    base_duration = char_count / BASE_SPEED
    coefficient = COEFFICIENTS.get(speed, 1.0)
    adjusted = base_duration * coefficient
    rounded = math.ceil(adjusted * 2) / 2
    rounded = max(rounded, 1.0)
    return {
        "char_count": char_count,
        "base_duration": round(base_duration, 2),
        "speed": speed,
        "coefficient": coefficient,
        "adjusted_duration": round(adjusted, 2),
        "rounded_duration": rounded
    }


# ── 模式一：JSON 输入 ──
def mode_json(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        dialogues = json.load(f)

    results = []
    total_duration = 0
    for d in dialogues:
        text = d.get('text', '')
        speed = d.get('speed', '中等')
        duration = compute_duration(text, speed)
        result = {
            "dialogue_id": d.get('dialogue_id', ''),
            "scene_id": d.get('scene_id', ''),
            "character": d.get('character', ''),
            "text": text,
            "emotion": d.get('emotion', ''),
            "tone": d.get('tone', ''),
            **duration
        }
        results.append(result)
        total_duration += duration['rounded_duration']

    output = {
        "meta": {
            "rules_version": rules['version'],
            "base_speed": f"{BASE_SPEED}字/秒",
            "total_dialogues": len(results),
            "total_duration": round(total_duration, 1),
            "source": os.path.basename(input_path)
        },
        "dialogues": results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"模式一：计算完成。{len(results)} 条台词，总时长 {round(total_duration, 1)} 秒")
    print(f"结果已写入：{output_path}")


# ── 模式二：从分镜文件解析 ──
def mode_storyboard(prompts_path: str):
    with open(prompts_path, 'r', encoding='utf8') as f:
        content = f.read()

    # 提取集数信息
    ep_match = re.search(r'第(\d+)集', content)
    ep_num = ep_match.group(1) if ep_match else '?'

    # 分割母镜头
    blocks = content.split('## 母镜头')[1:]  # 跳过文件头部

    mother_header_re = re.compile(r'^(\d+)（总时长：([\d.]+)秒）')
    sub_shot_re = re.compile(r'### 子镜头(\d+)（时长：⏱([\d.]+)s 秒）：')
    dialogue_re = re.compile(r'【台词】(.*?)(?=\n【|\n###|\n---)', re.DOTALL)

    all_mothers = []
    total_prompts_dur = 0
    total_computed_dialogue = 0
    errors_found = 0

    for block in blocks:
        lines = block.strip().split('\n')
        first_line = lines[0].strip()

        m_match = mother_header_re.search(first_line)
        if not m_match:
            continue

        m_id = m_match.group(1)
        m_declared = float(m_match.group(2))

        sub_matches = list(sub_shot_re.finditer(block))
        sub_parts = re.split(r'### 子镜头\d+', block)

        sub_shots = []
        sub_allocated_sum = 0

        for i, s_match in enumerate(sub_matches):
            s_id = int(s_match.group(1))
            s_allocated = float(s_match.group(2))
            sub_allocated_sum += s_allocated

            # 获取子镜头文本块
            s_block = sub_parts[i + 1] if i + 1 < len(sub_parts) else ""

            d_match = dialogue_re.search(s_block)
            dialogue_text = None
            dialogue_speed = None
            computed = None

            if d_match:
                d_raw = d_match.group(1).strip()
                # 跳过"无"、"无（接...）"、"接子镜头..."等
                if d_raw not in ('无', '', '-') and '无（' not in d_raw and not d_raw.startswith('接'):
                    # 提取所有「...」内容（支持"句子1」和「句子2」"多句格式）
                    text_matches = re.findall(r'「(.+?)」', d_raw)
                    if text_matches:
                        dialogue_text = ''.join(text_matches)
                        dialogue_speed = extract_speed(d_raw)
                        computed = compute_duration(dialogue_text, dialogue_speed)

            sub_shots.append({
                "sub_shot_id": s_id,
                "allocated_duration": s_allocated,
                "has_dialogue": dialogue_text is not None,
                "dialogue_text": dialogue_text,
                "dialogue_speed": dialogue_speed,
                "computed": computed
            })

        # 汇总
        sub_allocated_r = round(sub_allocated_sum, 1)
        sub_computed_dialogue = sum(
            s['computed']['rounded_duration']
            for s in sub_shots if s['computed']
        )
        total_computed_dialogue += sub_computed_dialogue

        # 检查问题（区分硬错误与软提示：硬错误=必须修复；软提示=预算紧的正常现象，不判失败）
        issues = []
        for s in sub_shots:
            if s['computed']:
                comp = s['computed']
                allocated = s['allocated_duration']
                eff_speed = round(comp['char_count'] / allocated, 1) if allocated > 0 else float('inf')
                # ① 物理语速上限：即使标"极快"也无法压缩，硬错误（拦截 ep53 M6/M9 类伪修复）
                if eff_speed > SPEED_CEILING:
                    issues.append({
                        "sub_shot_id": s['sub_shot_id'],
                        "type": "语速超物理上限（不可执行）",
                        "allocated": allocated,
                        "computed": comp['rounded_duration'],
                        "gap": round(allocated - comp['rounded_duration'], 1),
                        "severity": "硬错误",
                        "detail": f"{comp['char_count']}字 / {allocated}s = {eff_speed}字/秒 > 上限 {SPEED_CEILING}字/秒，物理不可执行（极快也不可）"
                    })
                    errors_found += 1
                elif allocated < comp['rounded_duration']:
                    issues.append({
                        "sub_shot_id": s['sub_shot_id'],
                        "type": "台词时长不足",
                        "allocated": allocated,
                        "computed": comp['rounded_duration'],
                        "gap": round(allocated - comp['rounded_duration'], 1),
                        "severity": "硬错误",
                        "detail": f"台词需 {comp['rounded_duration']}s, 实际分配 {allocated}s (差 {round(comp['rounded_duration'] - allocated, 1)}s) | {comp['char_count']}字, 语速{comp['speed']}"
                    })
                    errors_found += 1
                elif allocated < comp['rounded_duration'] + 0.3:
                    issues.append({
                        "sub_shot_id": s['sub_shot_id'],
                        "type": "动作余量不足",
                        "allocated": allocated,
                        "computed": comp['rounded_duration'],
                        "gap": round(allocated - comp['rounded_duration'], 1),
                        "severity": "软提示",
                        "detail": f"台词 {comp['rounded_duration']}s + 动作余量仅 {round(allocated - comp['rounded_duration'], 1)}s（预算紧的正常现象，不判失败）"
                    })

        if abs(sub_allocated_r - m_declared) > 0.05:
            issues.append({
                "sub_shot_id": None,
                "type": "母镜头总时长不等",
                "allocated": m_declared,
                "computed": sub_allocated_r,
                "gap": round(sub_allocated_r - m_declared, 1),
                "severity": "硬错误",
                "detail": f"声明 {m_declared}s, 子镜头之和 {sub_allocated_r}s (差 {round(sub_allocated_r - m_declared, 1)}s)"
            })
            errors_found += 1

        mother = {
            "mother_id": m_id,
            "declared_duration": m_declared,
            "sub_shot_sum": sub_allocated_r,
            "sub_shot_computed_dialogue": round(sub_computed_dialogue, 1),
            "sub_shots": [
                {
                    "sub_shot_id": s['sub_shot_id'],
                    "allocated_duration": s['allocated_duration'],
                    "dialogue_text": s['dialogue_text'],
                    "dialogue_speed": s['dialogue_speed'],
                    "computed_dialogue_duration": s['computed']['rounded_duration'] if s['computed'] else None,
                    "char_count": s['computed']['char_count'] if s['computed'] else None,
                }
                for s in sub_shots
            ],
            "issues": issues
        }
        all_mothers.append(mother)
        total_prompts_dur += sub_allocated_r

    # ── 输出 ──
    print("=" * 80)
    print(f"即梦分镜时长校验报告 —— 第{ep_num}集")
    print("=" * 80)
    print(f"规则版本: {rules['version']} | 基准语速: {BASE_SPEED}字/秒")
    print()

    for m in all_mothers:
        hard_here = sum(1 for i in m['issues'] if i.get('severity') == '硬错误')
        soft_here = len(m['issues']) - hard_here
        if not m['issues']:
            status = "✓"
        elif hard_here == 0:
            status = f"✓（{soft_here}个软提示）"
        else:
            status = f"✗ {hard_here}个硬错误" + (f" + {soft_here}软提示" if soft_here else "")
        print(f"母镜头{m['mother_id']} (声明{m['declared_duration']}s, 子镜头和={m['sub_shot_sum']}s) [{status}]")
        for s in m['sub_shots']:
            if s['computed_dialogue_duration'] is not None:
                ok = "✓" if s['allocated_duration'] >= s['computed_dialogue_duration'] else "✗"
                print(f"  子镜头{s['sub_shot_id']}: 分配{s['allocated_duration']}s | 台词需{s['computed_dialogue_duration']}s | {s['char_count']}字 语速{s['dialogue_speed']} [{ok}]")
                print(f"    「{s['dialogue_text'][:60]}{'...' if len(s['dialogue_text'] or '') > 60 else ''}」")
            else:
                purpose = ''
                if s['allocated_duration'] <= 1.0 and s['sub_shot_id'] != 1:
                    purpose = ' [反应]'
                elif s['sub_shot_id'] == 1:
                    purpose = ' [定场/过渡]'
                else:
                    purpose = ' [动作/无台词]'
                print(f"  子镜头{s['sub_shot_id']}: 分配{s['allocated_duration']}s{purpose}")
        if m['issues']:
            for iss in m['issues']:
                print(f"  ⚠ {iss['detail']}")
        print()

    print("=" * 80)
    print("汇总")
    print("=" * 80)
    soft_total = sum(1 for m in all_mothers for i in m['issues'] if i.get('severity') == '软提示')
    print(f"母镜头: {len(all_mothers)} 个")
    print(f"分镜总时长: {round(total_prompts_dur, 1)} 秒")
    print(f"台词计算总时长: {round(total_computed_dialogue, 1)} 秒")
    print(f"硬错误（必须修复）: {errors_found} 个")
    print(f"软提示（参考，不判失败）: {soft_total} 个")
    print()

    # ── 保存 JSON ──
    output_dir = os.path.dirname(prompts_path)
    base_name = os.path.splitext(os.path.basename(prompts_path))[0]
    # 提取 epXX
    ep_match2 = re.search(r'(ep\d+)', output_dir)
    ep_dir = ep_match2.group(1) if ep_match2 else 'epXX'
    output_path = os.path.join(output_dir, f'{ep_dir}-sub-durations.json')

    output_data = {
        "meta": {
            "rules_version": rules['version'],
            "base_speed": f"{BASE_SPEED}字/秒",
            "source": os.path.basename(prompts_path),
            "total_mothers": len(all_mothers),
            "total_storyboard_duration": round(total_prompts_dur, 1),
            "total_computed_dialogue": round(total_computed_dialogue, 1),
            "errors_found": errors_found,
            "soft_warnings": sum(1 for m in all_mothers for i in m['issues'] if i.get('severity') == '软提示')
        },
        "mothers": all_mothers
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"详细 JSON 已写入：{output_path}")
    if errors_found > 0:
        print(f"\n✗ 发现 {errors_found} 个硬错误（必须修复），请在第二遍修正中调整！")


# ── 入口 ──
def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  模式一（JSON输入）: python calc_duration.py <输入JSON> <输出JSON>")
        print("  模式二（分镜解析）: python calc_duration.py --from-storyboard <02-jimeng-prompts.md路径>")
        sys.exit(1)

    if sys.argv[1] == '--from-storyboard':
        if len(sys.argv) < 3:
            print("错误：--from-storyboard 需要指定分镜文件路径")
            sys.exit(1)
        mode_storyboard(sys.argv[2])
    else:
        if len(sys.argv) < 3:
            print("错误：JSON 模式需要输入和输出两个路径")
            sys.exit(1)
        mode_json(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()

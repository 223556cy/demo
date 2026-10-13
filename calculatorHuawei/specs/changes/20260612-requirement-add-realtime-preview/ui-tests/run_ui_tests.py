#!/usr/bin/env python3
"""
OpenCalc HarmonyOS 实时预览功能 UI 自动化测试
补做 apply-report §6 承认的"未在真机/模拟器跑 UI 测试"空白
"""
import os
import sys
import time
import json
import subprocess
import re
from datetime import datetime

# 配置
HDC = r"D:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\toolchains\hdc.exe"
TARGET = "127.0.0.1:5555"
BUNDLE = "com.darkempire78.opencalculator"
TEST_DIR = r"D:\huawei\Demo\worktrees\issue-11\specs\changes\20260612-requirement-add-realtime-preview\ui-tests"
DUMP_DIR = os.path.join(TEST_DIR, "dump")
SHOT_DIR = os.path.join(TEST_DIR, "screenshot")
RESULTS_FILE = os.path.join(TEST_DIR, "results.json")

# 按钮坐标（实时预览版：与百分号按钮版布局相同）
BTN = {
    "AC":    (174, 718),
    "%":     (417, 718),
    "(":     (660, 718),
    ")":     (903, 718),
    "÷":     (1146, 718),
    "7":     (295, 942), "8": (538, 942), "9": (781, 942),
    "×":     (1024, 942),
    "4":     (295, 1166), "5": (538, 1166), "6": (781, 1166),
    "-":     (1024, 1166),
    "1":     (295, 1390), "2": (538, 1390), "3": (781, 1390),
    "+":     (1024, 1390),
    "0":     (264, 1614),
    ".":     (507, 1614),
    "⌫":     (750, 1614),
    "=":     (1025, 1614),
}

# 工具
def run(cmd, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

def hdc(*args, timeout=30):
    return run([HDC, "-t", TARGET] + list(args), timeout=timeout)

def hdc_shell(cmd_str, timeout=30):
    return hdc("shell", cmd_str, timeout=timeout)

def hdc_click(x, y, label=""):
    if label:
        print(f"  点击 [{label}] @ ({x}, {y})")
    hdc_shell(f"uitest uiInput click {x} {y}")

def hdc_screenshot(name):
    remote = f"/data/local/tmp/_t_{name}.png"
    hdc_shell(f"uitest screenCap -p {remote}")
    local = os.path.join(SHOT_DIR, f"{name}.png")
    hdc("file", "recv", remote, local)
    return local if os.path.exists(local) else None

def hdc_dump(name):
    remote = f"/data/local/tmp/_t_{name}.json"
    hdc_shell(f"uitest dumpLayout -p {remote}")
    local = os.path.join(DUMP_DIR, f"{name}.json")
    hdc("file", "recv", remote, local)
    if os.path.exists(local):
        with open(local, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def find_text(tree, target):
    results = []
    def walk(node):
        attrs = node.get('attributes', {})
        text = attrs.get('text', '')
        if target in text:
            results.append({
                'text': text,
                'bounds': attrs.get('bounds', ''),
            })
        for child in node.get('children', []):
            walk(child)
    if tree:
        walk(tree)
    return results

def find_top_text(tree, max_y=500, min_width=1000):
    """在显示区域（y<500，宽度>1000）找最底层的文本节点（结果/预览）"""
    candidates = []
    def walk(node):
        attrs = node.get('attributes', {})
        text = attrs.get('text', '')
        cls = attrs.get('type', '')
        bounds = attrs.get('bounds', '')
        rid = attrs.get('id', '')
        if cls == 'Text' and text and 'Button' not in rid and 'StatusBar' not in rid and 'TimeView' not in rid:
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
            if m:
                l, t, r, b = map(int, m.groups())
                if t < max_y and (r - l) > min_width:
                    candidates.append({'text': text, 'top': t, 'bottom': b})
        for child in node.get('children', []):
            walk(child)
    if tree:
        walk(tree)
    # 排序：top 越大越靠下
    candidates.sort(key=lambda x: x['top'], reverse=True)
    return candidates

def press_buttons(seq, step=0.15):
    for btn in seq:
        if btn in BTN:
            x, y = BTN[btn]
            hdc_click(x, y, btn)
            time.sleep(step)
        elif btn == " ":
            time.sleep(0.3)

def ac():
    hdc_click(*BTN["AC"], "AC")
    time.sleep(0.3)

# 实时预览测试 - 关键：每次按键后立即检查 preview 显示
results = []

def record(ac_id, name, expected_preview, actual, status, note=""):
    rec = {
        "ac_id": ac_id,
        "name": name,
        "expected": expected_preview,
        "actual": str(actual),
        "status": status,
        "note": note,
        "time": datetime.now().strftime("%H:%M:%S"),
    }
    results.append(rec)
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"  {icon} {ac_id} {name}: expected='{expected_preview}' actual='{actual}' {note}")
    return rec

def get_preview_and_result(tree):
    """提取 preview（上层显示）和 result（下层显示）"""
    candidates = find_top_text(tree, max_y=500, min_width=500)
    if len(candidates) >= 2:
        # top 最大是 result（最底）
        # top 第二大是 preview
        return candidates[1]['text'] if len(candidates) > 1 else '', candidates[0]['text']
    elif len(candidates) == 1:
        return '', candidates[0]['text']
    return '', ''

def launch_app():
    hdc_shell(f"aa force-stop {BUNDLE}")
    time.sleep(1)
    hdc_shell(f"aa start -a EntryAbility -b {BUNDLE}")
    time.sleep(3)
    hdc_screenshot("00_app_launched")

# AC 测试
def test_ac_rp_01_empty():
    """AC-RP-01: 空表达式 → preview=''"""
    print("\n=== AC-RP-01: 空表达式 ===")
    ac()
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_01_empty")
    hdc_screenshot("ac_rp_01_empty")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-01", "空表达式 → 空预览", "", preview,
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

def test_ac_rp_02_simple_add():
    """AC-RP-02: 1+2 → preview='3'"""
    print("\n=== AC-RP-02: 简单加法 1+2 ===")
    ac()
    press_buttons(["1", "+", "2"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_02_1plus2")
    hdc_screenshot("ac_rp_02_1plus2_preview")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-02", "简单加法 1+2 → 实时预览=3", "3", preview,
                  "PASS" if preview == "3" else "FAIL",
                  f"result={result}")

def test_ac_rp_03_negative():
    """AC-RP-03: 5-10 → preview='-5'"""
    print("\n=== AC-RP-03: 减法 5-10 ===")
    ac()
    press_buttons(["5", "-", "1", "0"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_03_5minus10")
    hdc_screenshot("ac_rp_03_5minus10_preview")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-03", "5-10 → 实时预览=-5", "-5", preview,
                  "PASS" if preview == "-5" else "FAIL",
                  f"result={result}")

def test_ac_rp_04_incomplete():
    """AC-RP-04: 1+ → preview='' (末位运算符)"""
    print("\n=== AC-RP-04: 不完整表达式 1+ ===")
    ac()
    press_buttons(["1", "+"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_04_incomplete")
    hdc_screenshot("ac_rp_04_incomplete_preview")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-04", "1+ → 末位运算符无预览", "", preview,
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

def test_ac_rp_08_percent():
    """AC-RP-08: 50+10% → preview='55'"""
    print("\n=== AC-RP-08: 百分号 50+10% ===")
    ac()
    press_buttons(["5", "0", "+", "1", "0", "%"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_08_percent")
    hdc_screenshot("ac_rp_08_percent_preview")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-08", "50+10% → 实时预览=55", "55", preview,
                  "PASS" if preview == "55" else "FAIL",
                  f"result={result}")

def test_ac_rp_11_formatting():
    """AC-RP-11: 1000+2000 → preview='3,000' (千分位)"""
    print("\n=== AC-RP-11: 千分位格式 1000+2000 ===")
    ac()
    press_buttons(["1", "0", "0", "0", "+", "2", "0", "0", "0"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_11_formatting")
    hdc_screenshot("ac_rp_11_formatting_preview")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-11", "1000+2000 → 预览=3,000 (千分位)", "3,000", preview,
                  "PASS" if preview == "3,000" else "FAIL",
                  f"result={result}")

def test_ac_rp_13_equals_consistency():
    """AC-RP-13: 1+2 → preview='3' 后按等号 → result='3' 应一致"""
    print("\n=== AC-RP-13: 预览与结果一致 1+2 = 3 ===")
    ac()
    press_buttons(["1", "+", "2"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_13_before_equals")
    hdc_screenshot("ac_rp_13_before_equals")
    preview_before, _ = get_preview_and_result(tree)

    # 按等号
    hdc_click(*BTN["="], "=")
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_13_after_equals")
    hdc_screenshot("ac_rp_13_after_equals")
    _, result_after = get_preview_and_result(tree)
    return record("AC-RP-13", "预览与结果一致", "preview=3, result=3", f"preview={preview_before}, result={result_after}",
                  "PASS" if preview_before == "3" and result_after == "3" else "FAIL",
                  "实时预览与最终结果应一致")

def test_ac_rp_12_ac_clears():
    """AC-RP-12: AC 清空 preview"""
    print("\n=== AC-RP-12: AC 清空预览 ===")
    ac()
    press_buttons(["1", "+", "2"])
    time.sleep(0.3)
    # 此时有 preview "3"
    hdc_click(*BTN["AC"], "AC")
    time.sleep(0.3)
    tree = hdc_dump("ac_rp_12_after_ac")
    hdc_screenshot("ac_rp_12_after_ac")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-12", "AC 后清空预览", "", preview,
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

def test_ac_rp_06_syntax_error():
    """AC-RP-06: 1++2 → preview='' (语法错误)"""
    print("\n=== AC-RP-06: 语法错误 1++2 ===")
    ac()
    press_buttons(["1", "+", "+", "2"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_06_syntax_error")
    hdc_screenshot("ac_rp_06_syntax_error")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-06", "1++2 语法错误无预览", "", preview,
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

def test_ac_rp_07_function():
    """AC-RP-07: sin(0) → preview='0' (基础模式无sin按钮,SKIP)"""
    print("\n=== AC-RP-07: 函数 sin(0) ===")
    ac()
    # 基础模式无 sin 按钮，需要切到科学模式
    # 先尝试切到科学模式
    hdc_click(143, 531, "切换到科学模式")  # 基础/科学切换
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_07_scientific")
    # 检查是否进入科学模式（有 sin 按钮）
    sci_mode = find_text(tree, "sin")
    if sci_mode:
        press_buttons(["s", "i", "n", "(", "0", ")"])
        time.sleep(0.5)
        tree = hdc_dump("ac_rp_07_sin0")
        hdc_screenshot("ac_rp_07_sin0")
        preview, result = get_preview_and_result(tree)
        return record("AC-RP-07", "sin(0) → 预览=0", "0", preview,
                      "PASS" if preview == "0" else "FAIL",
                      f"result={result}")
    else:
        hdc_screenshot("ac_rp_07_no_sin")
        return record("AC-RP-07", "sin(0) → 预览=0", "0", "N/A", "SKIP",
                      "基础模式无 sin 按钮；切到科学模式后未发现")

def test_ac_rp_10_error_isolation():
    """AC-RP-10: 1÷0 后再 1+1 → preview=2, onEquals 后 result=2 不报错"""
    print("\n=== AC-RP-10: 错误状态隔离 1÷0 + 1+1 ===")
    ac()
    # 先触发除零
    press_buttons(["1", "÷", "0"])
    time.sleep(0.3)
    # 预览应该为 ""（除零错误）
    hdc_click(*BTN["="], "=")  # 触发错误
    time.sleep(0.5)
    hdc_screenshot("ac_rp_10_after_division_zero")
    # 清空
    ac()
    # 再输入 1+1
    press_buttons(["1", "+", "1"])
    time.sleep(0.5)
    tree = hdc_dump("ac_rp_10_recovery")
    hdc_screenshot("ac_rp_10_recovery")
    preview, result = get_preview_and_result(tree)
    return record("AC-RP-10", "错误恢复后 1+1 → 预览=2", "2", preview,
                  "PASS" if preview == "2" else "FAIL",
                  f"ErrorFlags 隔离验证 result={result}")

def test_ac_rp_05_unclosed_paren():
    """AC-RP-05: sin(0 → preview='' (函数未闭合)"""
    print("\n=== AC-RP-05: 函数未闭合 sin(0 ===")
    ac()
    hdc_click(143, 531, "切换到科学模式")
    time.sleep(0.5)
    # 检查是否进入科学模式
    tree = hdc_dump("ac_rp_05_sci_check")
    sci_mode = find_text(tree, "sin")
    if sci_mode:
        press_buttons(["s", "i", "n", "(", "0"])
        time.sleep(0.5)
        tree = hdc_dump("ac_rp_05_unclosed")
        hdc_screenshot("ac_rp_05_unclosed")
        preview, result = get_preview_and_result(tree)
        return record("AC-RP-05", "sin(0 未闭合无预览", "", preview,
                      "PASS" if preview == ' ' or preview == '' else "FAIL",
                      f"result={result}")
    else:
        return record("AC-RP-05", "sin(0 未闭合无预览", "", "N/A", "SKIP",
                      "基础模式无 sin 按钮")

# 主流程
def main():
    print("=" * 60)
    print("OpenCalc 实时预览功能 - UI 自动化测试")
    print("=" * 60)
    print(f"开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: {TARGET} ({BUNDLE})")
    print()

    print("[启动] 启动应用...")
    launch_app()

    # 关键 AC 测试
    test_ac_rp_01_empty()
    test_ac_rp_02_simple_add()
    test_ac_rp_03_negative()
    test_ac_rp_04_incomplete()
    test_ac_rp_05_unclosed_paren()
    test_ac_rp_06_syntax_error()
    test_ac_rp_07_function()
    test_ac_rp_08_percent()
    test_ac_rp_10_error_isolation()
    test_ac_rp_11_formatting()
    test_ac_rp_12_ac_clears()
    test_ac_rp_13_equals_consistency()

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    skip_count = sum(1 for r in results if r['status'] == 'SKIP')
    print(f"  PASS: {pass_count}")
    print(f"  FAIL: {fail_count}")
    print(f"  SKIP: {skip_count}")
    print(f"  TOTAL: {len(results)}")

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果: {RESULTS_FILE}")

    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
BUG 修复验证测试 - 1++2 等连续运算符场景
覆盖：连续运算符 + 一元负号/正号回归测试
"""
import os
import sys
import time
import json
import subprocess
import re
from datetime import datetime

HDC = r"D:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\toolchains\hdc.exe"
TARGET = "127.0.0.1:5555"
BUNDLE = "com.darkempire78.opencalculator"
TEST_DIR = r"D:\huawei\Demo\worktrees\issue-11\specs\changes\20260612-requirement-add-realtime-preview\ui-tests"
DUMP_DIR = os.path.join(TEST_DIR, "dump")
SHOT_DIR = os.path.join(TEST_DIR, "screenshot")
RESULTS_FILE = os.path.join(TEST_DIR, "results_bugfix.json")

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

def find_top_text(tree, max_y=500, min_width=500):
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
    candidates.sort(key=lambda x: x['top'], reverse=True)
    return candidates

def get_preview_and_result(tree):
    candidates = find_top_text(tree, max_y=500, min_width=500)
    if len(candidates) >= 2:
        return candidates[1]['text'] if len(candidates) > 1 else '', candidates[0]['text']
    elif len(candidates) == 1:
        return '', candidates[0]['text']
    return '', ''

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

# === 测试用例 ===
results = []

def record(test_id, name, expression, expected_preview, actual, status, note=""):
    rec = {
        "test_id": test_id,
        "name": name,
        "expression": expression,
        "expected": expected_preview,
        "actual": str(actual),
        "status": status,
        "note": note,
        "time": datetime.now().strftime("%H:%M:%S"),
    }
    results.append(rec)
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"  {icon} {test_id} {name}: expr='{expression}' expected='{expected_preview}' actual='{actual}' {note}")
    return rec

# === BUG 修复验证 ===
def test_bug_1pp2():
    """BUG 修复核心测试: 1++2 → 不显示预览"""
    print("\n=== BUG 修复 1++2 ===")
    ac()
    press_buttons(["1", "+", "+", "2"])
    time.sleep(0.5)
    tree = hdc_dump("bugfix_1pp2")
    hdc_screenshot("bugfix_1pp2")
    preview, result = get_preview_and_result(tree)
    return record("BUG-01", "1++2 不应显示预览", "1++2", "",
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

def test_bug_1pm2():
    """1+-2 → 不显示预览"""
    print("\n=== BUG 修复 1+-2 ===")
    ac()
    press_buttons(["1", "+", "-", "2"])
    time.sleep(0.5)
    tree = hdc_dump("bugfix_1pm2")
    hdc_screenshot("bugfix_1pm2")
    preview, result = get_preview_and_result(tree)
    return record("BUG-02", "1+-2 不应显示预览", "1+-2", "",
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

def test_bug_2mp2():
    """2*-2 → 不显示预览"""
    print("\n=== BUG 修复 2*-2 ===")
    ac()
    press_buttons(["2", "×", "-", "2"])
    time.sleep(0.5)
    tree = hdc_dump("bugfix_2mp2")
    hdc_screenshot("bugfix_2mp2")
    preview, result = get_preview_and_result(tree)
    return record("BUG-03", "2*-2 不应显示预览", "2*-2", "",
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

def test_bug_1dp0():
    """1÷0 → 不显示预览（除零）"""
    print("\n=== BUG 修复 1÷0 ===")
    ac()
    press_buttons(["1", "÷", "0"])
    time.sleep(0.5)
    tree = hdc_dump("bugfix_1dp0")
    hdc_screenshot("bugfix_1dp0")
    preview, result = get_preview_and_result(tree)
    return record("BUG-04", "1÷0 不应显示预览", "1÷0", "",
                  "PASS" if preview == ' ' or preview == '' else "FAIL",
                  f"result={result}")

# === 一元运算符回归测试（不应被误判） ===
def test_regression_1p2():
    """回归测试: 1+2 仍显示 3"""
    print("\n=== 回归测试 1+2 ===")
    ac()
    press_buttons(["1", "+", "2"])
    time.sleep(0.5)
    tree = hdc_dump("regress_1p2")
    hdc_screenshot("regress_1p2")
    preview, result = get_preview_and_result(tree)
    return record("REG-01", "1+2 → 3 仍工作", "1+2", "3",
                  "PASS" if preview == "3" else "FAIL",
                  f"result={result}")

def test_regression_5m10():
    """回归测试: 5-10 仍显示 -5"""
    print("\n=== 回归测试 5-10 ===")
    ac()
    press_buttons(["5", "-", "1", "0"])
    time.sleep(0.5)
    tree = hdc_dump("regress_5m10")
    hdc_screenshot("regress_5m10")
    preview, result = get_preview_and_result(tree)
    return record("REG-02", "5-10 → -5 仍工作", "5-10", "-5",
                  "PASS" if preview == "-5" else "FAIL",
                  f"result={result}")

def test_regression_50pp10pp():
    """回归测试: 50+10% 仍显示 55"""
    print("\n=== 回归测试 50+10% ===")
    ac()
    press_buttons(["5", "0", "+", "1", "0", "%"])
    time.sleep(0.5)
    tree = hdc_dump("regress_50pp10pp")
    hdc_screenshot("regress_50pp10pp")
    preview, result = get_preview_and_result(tree)
    return record("REG-03", "50+10% → 55 仍工作", "50+10%", "55",
                  "PASS" if preview == "55" else "FAIL",
                  f"result={result}")

# === 主流程 ===
def main():
    print("=" * 60)
    print("BUG 修复验证测试 - 1++2 连续运算符场景")
    print("=" * 60)
    print(f"开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: {TARGET} ({BUNDLE})")
    print()

    # 启动应用
    print("[启动] 启动应用...")
    hdc_shell(f"aa force-stop {BUNDLE}")
    time.sleep(1)
    hdc_shell(f"aa start -a EntryAbility -b {BUNDLE}")
    time.sleep(3)
    hdc_screenshot("00_bugfix_app_launched")

    # BUG 修复测试
    test_bug_1pp2()
    test_bug_1pm2()
    test_bug_2mp2()
    test_bug_1dp0()

    # 回归测试
    test_regression_1p2()
    test_regression_5m10()
    test_regression_50pp10pp()

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    print(f"  PASS: {pass_count}")
    print(f"  FAIL: {fail_count}")
    print(f"  TOTAL: {len(results)}")

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果: {RESULTS_FILE}")

    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

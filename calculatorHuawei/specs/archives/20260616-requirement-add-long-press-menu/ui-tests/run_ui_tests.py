#!/usr/bin/env python3
"""
OpenCalc HarmonyOS 长按弹出选择菜单 - UI 自动化测试
Re-dispatch v2 补做 (rev-01 反馈 ui-tests/ 目录为空)

关键发现:
- uitest uiInput longClick 不稳定 (有时只触发 onClick 不触发 onAction)
- uitest uiInput swipe X Y X Y 200 也不触发长按
- **uitest uiInput drag X Y X+1 Y+1 200** 稳定触发 LongPressGesture 500ms+
- 弹出菜单显示完整 "arcsin/arccos/arctan", 永久按钮显示截断 "arcsi/arcco/arcta"
"""
import os
import sys
import time
import json
import re
import base64
import subprocess
from datetime import datetime

# ===== 配置 =====
HDC = r"D:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\toolchains\hdc.exe"
TARGET = "127.0.0.1:5555"
BUNDLE = "com.darkempire78.opencalculator"

ROOT = r"D:\huawei\Demo\worktrees\issue-16\specs\changes\20260616-requirement-add-long-press-menu\ui-tests"
DUMP_DIR = os.path.join(ROOT, "dump")
SHOT_DIR = os.path.join(ROOT, "screenshot")
RESULTS_FILE = os.path.join(ROOT, "results.json")

# 科学模式按钮坐标 (来自 dump/01_scientific.json)
BTN = {
    "AC":         (174, 1151),    # 科学模式 AC
    "科学":       (143, 602),
    "sin":        (165, 767),     # bounds [51,687][279,848]
    "cos":        (413, 767),
    "tan":        (660, 767),
    "ln":         (908, 767),
    "log":        (1155, 767),
    "7":          (295, 1375),
    "arcsi":      (165, 948),     # 永久 arcsin 按钮 (truncated)
    "arcco":      (413, 948),
    "arcta":      (660, 948),
}

# ===== 工具 =====
def run(cmd, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

def hdc(*args, timeout=30):
    return run([HDC, "-t", TARGET] + list(args), timeout=timeout)

def hdc_shell(cmd_str, timeout=30):
    return hdc("shell", cmd_str, timeout=timeout)

def hdc_click(x, y, label=""):
    if label:
        print(f"  click [{label}] @ ({x}, {y})")
    hdc_shell(f"uitest uiInput click {x} {y}")

def hdc_long_press(x, y, label=""):
    """用 drag 模拟长按: 微小位移 (1px) + 最低速度 (200) = 实际 500ms+ 持续时间, 触发 LongPressGesture"""
    if label:
        print(f"  longPress [{label}] @ ({x}, {y})")
    hdc_shell(f"uitest uiInput drag {x} {y} {x+1} {y+1} 200")

def hdc_screenshot(name):
    """通过 base64 把 PNG 字节流拉回本地 (规避 hdc file recv 在 Windows 的路径解析问题)"""
    remote = f"/data/local/tmp/_lp_{name}.png"
    hdc_shell(f"uitest screenCap -p {remote}")
    rc, out, err = hdc_shell(f"base64 {remote}")
    png_bytes = base64.b64decode(out.strip())
    local = os.path.join(SHOT_DIR, f"{name}.png")
    with open(local, "wb") as f:
        f.write(png_bytes)
    hdc_shell(f"rm -f {remote}")
    return local

def hdc_dump(name):
    """用 cat 把 dumpLayout JSON 拉回本地"""
    remote = f"/data/local/tmp/_lp_{name}.json"
    hdc_shell(f"uitest dumpLayout -p {remote}")
    rc, out, err = hdc_shell(f"cat {remote}")
    local = os.path.join(DUMP_DIR, f"{name}.json")
    with open(local, "w", encoding="utf-8") as f:
        f.write(out)
    hdc_shell(f"rm -f {remote}")
    try:
        with open(local, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def find_text(tree, target):
    """在 dump 树里找包含 target 的 Text 节点"""
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

def find_exact_text(tree, target):
    """严格匹配完整 text 字符串"""
    results = []
    def walk(node):
        attrs = node.get('attributes', {})
        text = attrs.get('text', '')
        if text == target:
            results.append({
                'text': text,
                'bounds': attrs.get('bounds', ''),
            })
        for child in node.get('children', []):
            walk(child)
    if tree:
        walk(tree)
    return results

def parse_bounds(bounds):
    """[x1,y1][x2,y2] -> (cx, cy)"""
    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
    if m:
        x1, y1, x2, y2 = map(int, m.groups())
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    return None

def find_expression_text(tree):
    """找显示区域(屏幕顶部 y<320)的宽 Text 节点 → 表达式 (y=220-294)。
    结果显示在 y=365-513, 不能混淆。"""
    cands = []
    def walk(node):
        a = node.get('attributes', {})
        text = a.get('text', '')
        cls = a.get('type', '')
        rid = a.get('id', '')
        bounds = a.get('bounds', '')
        if cls == 'Text' and text and 'Button' not in rid and 'StatusBar' not in rid and 'TimeView' not in rid:
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
            if m:
                l, t, r, b = map(int, m.groups())
                if t < 320 and (r - l) > 800:  # 表达式在屏幕 y<320 区域
                    cands.append({'text': text, 'top': t, 'bottom': b})
        for c in node.get('children', []):
            walk(c)
    if tree:
        walk(tree)
    cands.sort(key=lambda x: x['top'])  # 顶部的 (最上) 是表达式
    return cands[0]['text'] if cands else ''

def menu_is_open(tree):
    """菜单是否打开: 查找完整 arcsin/arccos/arctan 文本 (永久按钮只显示截断 arcsi/arcco/arcta)"""
    full_arcsin = find_exact_text(tree, "arcsin")
    full_arccos = find_exact_text(tree, "arccos")
    full_arctan = find_exact_text(tree, "arctan")
    return bool(full_arcsin) and bool(full_arccos) and bool(full_arctan)

def launch_app_scientific():
    """force-stop + start + 切到科学模式"""
    hdc_shell(f"aa force-stop {BUNDLE}")
    time.sleep(1)
    hdc_shell(f"aa start -a EntryAbility -b {BUNDLE}")
    time.sleep(3)
    tree = hdc_dump("00_app_launched")
    if tree and not find_text(tree, "sin"):
        hdc_click(*BTN["科学"], "切到科学模式")
        time.sleep(1)
    hdc_screenshot("00_app_launched_scientific")

def record(ac_id, name, expected, actual, status, note=""):
    rec = {
        "ac_id": ac_id,
        "name": name,
        "expected": expected,
        "actual": str(actual),
        "status": status,
        "note": note,
        "time": datetime.now().strftime("%H:%M:%S"),
    }
    results.append(rec)
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"  {icon} {ac_id} {name}: expected='{expected}' actual='{actual}' {note}")
    return rec

results = []

# ===== AC 测试 =====

def test_ac1_long_press_sin():
    """AC-1: 长按 sin ≥500ms 弹出 [arcsin, arccos, arctan]"""
    print("\n=== AC-1: 长按 sin 弹出候选 ===")
    hdc_click(*BTN["AC"], "AC 清空")
    time.sleep(0.5)
    hdc_long_press(*BTN["sin"], label="长按 sin")
    time.sleep(1.0)
    tree = hdc_dump("01_long_press_sin")
    hdc_screenshot("01_long_press_sin_menu_opened")
    return record("AC-1", "长按 sin 弹出 3 个候选",
                  "arcsin + arccos + arctan (menu open)",
                  f"menu_open={menu_is_open(tree)}",
                  "PASS" if menu_is_open(tree) else "FAIL",
                  f"look at 01_long_press_sin_menu_opened.png")

def test_ac2_click_arcsin():
    """AC-2: 点击 arcsin → 表达式末尾 arcsin("""
    print("\n=== AC-2: 点击 arcsin 插入表达式 ===")
    tree = hdc_dump("02_pre_click")
    # 菜单应该还在(上一动作留下)
    arcsin = find_exact_text(tree, "arcsin")
    if not arcsin:
        return record("AC-2", "点击 arcsin 插入表达式", "arcsin(", "N/A", "FAIL",
                      "菜单未打开, 找不到 arcsin 节点")
    # 第一个 arcsin 必然是菜单中的 (位置在屏幕中部)
    x, y = parse_bounds(arcsin[0]['bounds'])
    print(f"  click arcsin @ ({x}, {y}) bounds={arcsin[0]['bounds']}")
    hdc_shell(f"uitest uiInput click {x} {y}")
    time.sleep(0.5)
    tree = hdc_dump("02_after_arcsin_click")
    hdc_screenshot("02_after_arcsin_click")
    expr = find_expression_text(tree)
    return record("AC-2", "点击 arcsin 插入表达式", "ends with 'arcsin('",
                  f"expr={expr!r}",
                  "PASS" if expr.rstrip().endswith("arcsin(") else "FAIL",
                  f"arcsin 坐标=({x}, {y})")

def test_ac4_mask_close():
    """AC-4: 点击菜单外关闭菜单, 表达式不变"""
    print("\n=== AC-4: 点遮罩关闭菜单 ===")
    # 重新打开菜单
    hdc_long_press(*BTN["sin"], label="重新长按 sin 打开菜单")
    time.sleep(1.0)
    tree = hdc_dump("03_menu_reopen_for_mask")
    if not menu_is_open(tree):
        return record("AC-4", "点遮罩关闭菜单", "menu closed, expr unchanged", "N/A", "FAIL",
                      "菜单未打开, 无法测试遮罩关闭")
    expr_before = find_expression_text(tree)
    hdc_screenshot("03_menu_open_for_mask_test")
    # 点遮罩 (上方空白区, y<500)
    hdc_click(200, 400, "点击遮罩区(顶部)")
    time.sleep(0.5)
    tree = hdc_dump("03_after_mask_click")
    hdc_screenshot("03_after_mask_click")
    expr_after = find_expression_text(tree)
    menu_gone = not menu_is_open(tree)
    return record("AC-4", "点遮罩关闭菜单,表达式不变",
                  f"menu=closed, expr={expr_before!r}",
                  f"menu_gone={menu_gone}, expr={expr_after!r}",
                  "PASS" if (menu_gone and expr_after == expr_before) else "FAIL",
                  "AC-4 遮罩点击关闭 + 表达式保持")

def test_ac3_short_press_sin():
    """AC-3: 短按 sin 仍插入 sin(, 不弹菜单"""
    print("\n=== AC-3: 短按 sin 插入 sin( ===")
    hdc_click(*BTN["AC"], "AC 清空")
    time.sleep(0.5)
    hdc_click(*BTN["sin"], "短按 sin")
    time.sleep(0.5)
    tree = hdc_dump("04_after_short_press_sin")
    hdc_screenshot("04_after_short_press_sin")
    expr = find_expression_text(tree)
    menu_appeared = menu_is_open(tree)
    return record("AC-3", "短按 sin 插入 sin(",
                  f"expr ends with 'sin(', no menu",
                  f"expr={expr!r}, menu_open={menu_appeared}",
                  "PASS" if (expr.rstrip().endswith("sin(") and not menu_appeared) else "FAIL",
                  "短按只插入 sin(, 不弹菜单")

def test_ac5_long_press_number():
    """AC-5: 长按数字无菜单 (端口测试已覆盖,这里附加 UI 验证)"""
    print("\n=== AC-5: 长按数字 7 无菜单 ===")
    hdc_click(*BTN["AC"], "AC 清空")
    time.sleep(0.5)
    hdc_long_press(*BTN["7"], label="长按数字 7")
    time.sleep(1.0)
    tree = hdc_dump("05_after_long_press_7")
    hdc_screenshot("05_after_long_press_7")
    menu_appeared = menu_is_open(tree)
    return record("AC-5", "长按数字无菜单", "no menu opened",
                  f"menu_open={menu_appeared}",
                  "PASS" if not menu_appeared else "FAIL",
                  "FMEA C4 验证 (hasCandidates('7') === false)")

def test_ac6_long_press_cos():
    """AC-6 扩展: 长按 cos 也弹出候选"""
    print("\n=== AC-6 扩展: 长按 cos 弹出候选 ===")
    hdc_click(*BTN["AC"], "AC 清空")
    time.sleep(0.5)
    hdc_long_press(*BTN["cos"], label="长按 cos")
    time.sleep(1.0)
    tree = hdc_dump("06_long_press_cos")
    hdc_screenshot("06_long_press_cos")
    return record("AC-6", "长按 cos 弹出 3 个候选",
                  "arcsin+arccos+arctan (menu open)",
                  f"menu_open={menu_is_open(tree)}",
                  "PASS" if menu_is_open(tree) else "FAIL",
                  "扩展验证 cos 同样工作")

# ===== Main =====
def main():
    os.makedirs(DUMP_DIR, exist_ok=True)
    os.makedirs(SHOT_DIR, exist_ok=True)
    print("=" * 60)
    print("OpenCalc 长按弹出选择菜单 - UI 自动化测试 (re-dispatch v2)")
    print("=" * 60)
    print(f"开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: {TARGET} ({BUNDLE})")
    print(f"截图: {SHOT_DIR}")
    print(f"Dump : {DUMP_DIR}")
    print()

    print("[启动] 启动应用 + 切到科学模式")
    launch_app_scientific()

    test_ac1_long_press_sin()
    test_ac2_click_arcsin()
    test_ac4_mask_close()
    test_ac3_short_press_sin()
    test_ac5_long_press_number()
    test_ac6_long_press_cos()

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    p = sum(1 for r in results if r['status'] == 'PASS')
    f = sum(1 for r in results if r['status'] == 'FAIL')
    s = sum(1 for r in results if r['status'] == 'SKIP')
    print(f"  PASS: {p}")
    print(f"  FAIL: {f}")
    print(f"  SKIP: {s}")
    print(f"  TOTAL: {len(results)}")

    summary = {
        "issue": "#16 长按弹出选择菜单",
        "test_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": TARGET,
        "bundle": BUNDLE,
        "total": len(results),
        "pass": p,
        "fail": f,
        "skip": s,
        "results": results,
    }
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f_out:
        json.dump(summary, f_out, ensure_ascii=False, indent=2)
    print(f"\n结果汇总: {RESULTS_FILE}")

    print(f"\n截图清单:")
    for fn in sorted(os.listdir(SHOT_DIR)):
        fp = os.path.join(SHOT_DIR, fn)
        sz = os.path.getsize(fp)
        print(f"  {fn} ({sz} bytes)")

    return 0 if f == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

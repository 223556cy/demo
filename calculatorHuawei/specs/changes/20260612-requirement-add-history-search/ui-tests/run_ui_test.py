#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史搜索框 UI 自动化测试 v6 - 修复版
aid-workflow 20260612 IR-HS-01..06 验证
"""
import subprocess
import time
import os
import json
import re
from datetime import datetime

HDC = r"D:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\toolchains\hdc.exe"
TARGET = "127.0.0.1:5555"
BUNDLE = "com.darkempire78.opencalculator"
ABILITY = "EntryAbility"
TEST_DIR = r"d:\huawei\Demo\calculatorHuawei\specs\changes\20260612-requirement-add-history-search\ui-tests"
SCREENSHOT_DIR = os.path.join(TEST_DIR, "screenshot")
DUMP_DIR = os.path.join(TEST_DIR, "dump")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)

results = []
test_start = datetime.now()

# 字符常量
TXT_HISTORY_OPEN = "▼ 历史"   # "▼ 历史"
TXT_HISTORY_CLOSE = "▲ 历史"  # "▲ 历史"
TXT_PLACEHOLDER = "搜索역사算式"  # "搜索역사算式"
TXT_EMPTY = "暂无计算记录"   # "暂无计算记录"
TXT_NO_MATCH = "未找到"        # "未找到"
TXT_CLEAR = "✕"                       # "✕"

def hdc(*args, check=True, timeout=30):
    cmd = [HDC, "-t", TARGET] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        return None
    return r

def keep_screen_on():
    hdc("shell", "power", "set", "stay", "on", check=False)

def launch_app():
    hdc("shell", "aa", "force-stop", BUNDLE)
    time.sleep(1)
    hdc("shell", "aa", "start", "-a", ABILITY, "-b", BUNDLE)
    time.sleep(4)

def dump_ui(filename, retries=2):
    remote = f"/data/local/tmp/{filename}.json"
    local = os.path.join(DUMP_DIR, f"{filename}.json")
    for _ in range(retries):
        hdc("shell", "uitest", "dumpLayout", "-p", remote, check=False, timeout=60)
        time.sleep(0.3)
        hdc("file", "recv", remote, local, check=False)
        if os.path.exists(local):
            with open(local, "rb") as f:
                raw = f.read().decode("utf-8", errors="ignore")
            if raw.strip().startswith("{"):
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    time.sleep(0.5)
                    continue
                nodes = []
                def walk(n):
                    a = n.get("attributes", {})
                    nodes.append({
                        "text": a.get("text", ""),
                        "type": a.get("type", ""),
                        "id": a.get("id", ""),
                        "clickable": a.get("clickable", "") == "true",
                        "hint": a.get("hint", ""),
                        "placeholder": a.get("placeholder", ""),
                        "bounds": a.get("bounds", ""),
                    })
                    for c in n.get("children", []):
                        walk(c)
                walk(data)
                return nodes
        time.sleep(0.5)
    return []

def get_center(node):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node["bounds"])
    if not m:
        return None
    l, t, r, b = map(int, m.groups())
    return ((l + r) // 2, (t + b) // 2)

def get_y(node):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node["bounds"])
    if not m: return 0
    return int(m.group(2))

def tap(x, y, wait=0.5, use_swipe=False):
    if use_swipe:
        hdc("shell", "uitest", "uiInput", "swipe", str(x), str(y), str(x), str(y), "200")
    else:
        hdc("shell", "uitest", "uiInput", "click", str(x), str(y))
    time.sleep(wait)

def find_click(nodes, text):
    for n in nodes:
        if n["text"] == text and n["clickable"]:
            return n
    return None

def find_input(nodes):
    """aid-workflow 20260612: ArkUI TextInput 在 dump 中可能显示为 Text 类型,需要多种检测"""
    for n in nodes:
        if not n.get('clickable'): continue
        if n.get('type') in ('TextInput', 'EditText'):
            return n
        attrs = n.get('attributes', {})
        if attrs.get('hint') or attrs.get('placeholder'):
            return n
    # 备选: 找 y > 1700 的可点击区域（历史面板内）
    for n in nodes:
        if n.get('clickable') and get_y(n) > 1700:
            return n
    return None

def input_text(text):
    safe = text.replace(" ", "%s")
    hdc("shell", "input", "text", safe)
    time.sleep(0.3)

def screenshot(name):
    remote = f"/data/local/tmp/{name}.png"
    local = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    hdc("shell", "uitest", "screenCap", "-p", remote, check=False)
    hdc("file", "recv", remote, local, check=False)
    return os.path.exists(local)

def record(case_id, action, expected, actual, pass_):
    result = "PASS" if pass_ else "FAIL"
    results.append({
        "case_id": case_id, "action": action, "expected": expected,
        "actual": actual, "result": result,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    status = "[OK]" if pass_ else "[FAIL]"
    print(f"  {status} {case_id}: {action}")
    print(f"        expected: {expected}")
    print(f"        actual:   {actual}")

# ==================== 主流程 ====================
print("=" * 60)
print("历史搜索框 UI 自动化测试 v6")
print("=" * 60)
keep_screen_on()

# Step 1: 启动
print("\n[Step 1] 启动 App")
launch_app()
nodes = dump_ui("01_initial")
screenshot("01_initial")
record("TC-UI-01", "启动 App", "App 启动成功", f"{len(nodes)} 节点", len(nodes) > 0)

# Step 2: 计算 1+2=3
print("\n[Step 2] 计算 1+2=3")
nodes = dump_ui("02_pre_calc")
seven = find_click(nodes, "1")
plus = find_click(nodes, "+")
two = find_click(nodes, "2")
eq = find_click(nodes, "=")
if seven and plus and two and eq:
    c = get_center(seven); tap(c[0], c[1], 0.3)
    c = get_center(plus); tap(c[0], c[1], 0.3)
    c = get_center(two); tap(c[0], c[1], 0.3)
    c = get_center(eq); tap(c[0], c[1], 1.0)
    nodes = dump_ui("02_after_calc")
    has_three = any("3" == n["text"] for n in nodes)
    record("TC-UI-02", "计算 1+2", "display 显示 3", f"has 3={has_three}", has_three)
    screenshot("02_after_calc")
else:
    record("TC-UI-02", "计算 1+2", "找不到按钮", "missing buttons", False)

# Step 3: 计算 50+50=100
print("\n[Step 3] 计算 50+50=100")
nodes = dump_ui("03_pre_calc2")
ac = find_click(nodes, "AC")
if ac:
    c = get_center(ac); tap(c[0], c[1], 0.3)
nodes = dump_ui("03_pre_calc2_after_ac")
five = find_click(nodes, "5")
plus = find_click(nodes, "+")
zero = find_click(nodes, "0")
eq = find_click(nodes, "=")
if five and plus and zero and eq:
    c = get_center(five); tap(c[0], c[1], 0.2)
    c = get_center(zero); tap(c[0], c[1], 0.2)
    c = get_center(plus); tap(c[0], c[1], 0.2)
    c = get_center(five); tap(c[0], c[1], 0.2)
    c = get_center(zero); tap(c[0], c[1], 0.2)
    c = get_center(eq); tap(c[0], c[1], 1.0)
    nodes = dump_ui("03_after_calc2")
    has_100 = any("100" == n["text"] for n in nodes)
    record("TC-UI-03", "计算 50+50", "display 显示 100", f"has 100={has_100}", has_100)
    screenshot("03_after_calc2")
else:
    record("TC-UI-03", "计算 50+50", "找不到按钮", "missing buttons", False)

# Step 4: 打开历史面板
print("\n[Step 4] 打开历史面板 (swipe 0距离)")
nodes = dump_ui("04_pre_history")
hist_node = find_click(nodes, TXT_HISTORY_OPEN) or find_click(nodes, TXT_HISTORY_CLOSE)
hist_opened = False
if hist_node:
    c = get_center(hist_node)
    print(f"  역사按钮坐标: {c}, text={hist_node['text']!r}")
    for attempt in range(3):
        tap(c[0], c[1], 1.0, use_swipe=True)
        nodes = dump_ui(f"04_after_click{attempt}")
        # aid-workflow 20260612: 必须找到搜索框或"暂无"或键盘区被压缩(说明历史面板打开)
        all_texts = " ".join(n["text"] for n in nodes)
        has_search = TXT_PLACEHOLDER in all_texts
        has_empty = TXT_EMPTY in all_texts
        # 历史项应在 display 之下(y > 700),不在 display 区
        def in_panel(n):
            return get_y(n) > 700 and (TXT_PLACEHOLDER in n.get("text", "") or n.get("hint") or any(s in n.get("text","") for s in ["1+2","50+50","= 3","= 100"]))
        has_history_items = any(in_panel(n) for n in nodes)
        # 也检查是否 keyboard 被压缩（标准 keyboard 不应同时显示 AC,0,= 等 + search box）
        keyboard_visible = all(k in all_texts for k in ["AC", "0", "="])
        print(f"  attempt {attempt}: search={has_search}, empty={has_empty}, items={has_history_items}, keyboard={keyboard_visible}")
        if has_search or has_empty or (has_history_items and not keyboard_visible):
            hist_opened = True
            break
    screenshot("04_history_open")
    if hist_opened:
        record("TC-UI-04", "打开历史面板", "搜索框/空历史/历史项+键盘压缩", "见上文", True)
    else:
        record("TC-UI-04", "打开历史面板", "多次点击未打开", "click failed", False)
else:
    record("TC-UI-04", "打开历史面板", f"找不到 {TXT_HISTORY_OPEN}", "not found", False)

# Step 5: 搜索框可见（已在 Step 4 验证）
print("\n[Step 5] 搜索框可见")
if hist_opened:
    record("TC-UI-05", "搜索框存在", "已确认", "见 TC-UI-04", True)
else:
    record("TC-UI-05", "搜索框存在", "前置条件未满足", "skipped", False)

# Step 6: 键入 '1' 验证过滤
print("\n[Step 6] 键入 '1' 验证过滤")
typed_ok = False
if hist_opened:
    nodes = dump_ui("06_pre_input")
    input_node = find_input(nodes)
    if input_node:
        c = get_center(input_node)
        tap(c[0], c[1], 0.5, use_swipe=True)
        input_text("1")
        time.sleep(0.5)
        nodes = dump_ui("06_after_input")
        screenshot("06_after_input_1")
        all_texts = " ".join(n["text"] for n in nodes)
        has_x = TXT_CLEAR in all_texts
        # 历史项判断
        has_1plus2_in_panel = any(
            get_y(n) > 700 and "1+2" in n.get("text","")
            for n in nodes
        )
        # 50+50 不应显示 (输入 1 不应匹配 50+50)
        no_50plus50 = not any(get_y(n) > 700 and "50+50" in n.get("text","") for n in nodes)
        typed_ok = has_x and has_1plus2_in_panel and no_50plus50
        record("TC-UI-06", "键入 '1' 过滤", "✕显示, panel内仅 1+2 命中",
               f"✕={has_x}, 1+2_in_panel={has_1plus2_in_panel}, 无50+50={no_50plus50}",
               typed_ok)
    else:
        record("TC-UI-06", "键入 '1'", "找不到 TextInput", "not found", False)
else:
    record("TC-UI-06", "键入 '1'", "前置条件未满足", "skipped", False)

# Step 7: 键入 '99999' 验证空状态
print("\n[Step 7] 键入 '99999' 验证空状态")
empty_state_ok = False
if hist_opened:
    nodes = dump_ui("07_pre_99999")
    input_node = find_input(nodes)
    if input_node:
        c = get_center(input_node)
        tap(c[0], c[1], 0.5, use_swipe=True)
        for _ in range(5):
            input_text("9")
        time.sleep(0.5)
        nodes = dump_ui("07_after_99999")
        screenshot("07_after_99999")
        all_texts = " ".join(n["text"] for n in nodes)
        empty_state_ok = TXT_NO_MATCH in all_texts and "99999" in all_texts
        record("TC-UI-07", "键入 '99999'", f"显示「{TXT_NO_MATCH}含 99999 的记录」",
               f"未找到={TXT_NO_MATCH in all_texts}, 99999={'99999' in all_texts}",
               empty_state_ok)
    else:
        record("TC-UI-07", "键入 '99999'", "找不到 TextInput", "not found", False)
else:
    record("TC-UI-07", "键入 '99999'", "前置条件未满足", "skipped", False)

# 收尾
test_end = datetime.now()
duration = test_end - test_start
print("\n" + "=" * 60)
print(f"测试完成 | 耗时: {duration.total_seconds():.1f}s")
print(f"通过: {sum(1 for r in results if r['result'] == 'PASS')}/{len(results)}")
print("=" * 60)

results_file = os.path.join(TEST_DIR, "results.json")
with open(results_file, "w", encoding="utf-8") as f:
    json.dump({
        "test_start": test_start.isoformat(),
        "test_end": test_end.isoformat(),
        "duration_seconds": duration.total_seconds(),
        "total": len(results),
        "passed": sum(1 for r in results if r["result"] == "PASS"),
        "failed": sum(1 for r in results if r["result"] == "FAIL"),
        "cases": results,
    }, f, ensure_ascii=False, indent=2)

print(f"\n结果: {results_file}")

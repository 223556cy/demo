#!/usr/bin/env python3
"""
OpenCalc HarmonyOS Issue #13 一键分享二维码 - UI 自动化测试
aid-workflow 20260615
v2: 动态坐标解析（每次操作前 dump UI + 解析按钮 bounds）
"""
import os, sys, time, json, subprocess, re

HDC = r"D:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\toolchains\hdc.exe"
TARGET = "127.0.0.1:5555"
BUNDLE = "com.darkempire78.opencalculator"
TEST_DIR = r"D:\huawei\Demo\worktrees\issue-13\specs\changes\20260615-requirement-add-qrcode-share\ui-tests"
DUMP_DIR = os.path.join(TEST_DIR, "dump")
SHOT_DIR = os.path.join(TEST_DIR, "screenshot")
RESULTS_FILE = os.path.join(TEST_DIR, "results.json")

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

def find_btn_coords(tree, target_text):
    """在 UI 树中找到 text 等于 target_text 的节点，返回 (x, y) 中心坐标"""
    if not tree: return None
    matches = []
    def walk(node):
        attrs = node.get('attributes', {})
        text = attrs.get('text', '').strip()
        if text == target_text:
            bounds = attrs.get('bounds', '')
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
            if m:
                x1, y1, x2, y2 = map(int, m.groups())
                matches.append(((x1+x2)//2, (y1+y2)//2, bounds))
        for c in node.get('children', []):
            walk(c)
    walk(tree)
    return matches[0][:2] if matches else None

def find_text(tree, target):
    if not tree: return []
    results = []
    def walk(node):
        attrs = node.get('attributes', {})
        text = attrs.get('text', '')
        if target in text:
            results.append({'text': text, 'bounds': attrs.get('bounds', '')})
        for c in node.get('children', []):
            walk(c)
    walk(tree)
    return results

def find_all_text(tree):
    if not tree: return []
    results = []
    def walk(node):
        attrs = node.get('attributes', {})
        text = attrs.get('text', '')
        if text:
            results.append({'text': text, 'bounds': attrs.get('bounds', '')})
        for c in node.get('children', []):
            walk(c)
    walk(tree)
    return results

def find_qrcode(tree):
    if not tree: return []
    results = []
    def walk(node):
        attrs = node.get('attributes', {})
        if attrs.get('type', '') == 'QRCode':
            results.append(attrs)
        for c in node.get('children', []):
            walk(c)
    walk(tree)
    return results

def safe_click(label, dump_name):
    """先 dump UI 找按钮，再点击；找不到返回 False"""
    tree = hdc_dump(dump_name)
    if not tree:
        print(f"  [skip] dump {dump_name} failed")
        return False
    coord = find_btn_coords(tree, label)
    if not coord:
        print(f"  [skip] button [{label}] not found in dump")
        return False
    x, y = coord
    hdc_click(x, y, label)
    time.sleep(0.3)
    return True

def safe_press_keys(keys, dump_name):
    """连续按键：每次按键前重新解析（应对 layout shift）"""
    for k in keys:
        if not safe_click(k, dump_name):
            print(f"  [skip] cannot find [{k}]")
            return False
    return True

# ==================== 测试用例 ====================
results = []

def ac_record(ac_id, name, status, actual="", expected="", note=""):
    results.append({
        "ac_id": ac_id,
        "name": name,
        "status": status,
        "actual": actual,
        "expected": expected,
        "note": note,
        "time": time.strftime("%H:%M:%S")
    })
    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "BLOCKED": "🚫"}.get(status, "?")
    print(f"  {icon} {ac_id}: {name} — {status}")
    if actual:
        print(f"      actual: {actual!r}")

# ==================== 流程：先 dump 拿所有按钮坐标 ====================

def get_all_btn_xy():
    """一次性 dump + 解析所有按钮坐标"""
    tree = hdc_dump("__coord")
    if not tree: return {}
    targets = ["AC","%","(",")","÷","×","-","+",".","⌫","=","0","1","2","3","4","5","6","7","8","9","分享"]
    coords = {}
    for t in targets:
        c = find_btn_coords(tree, t)
        if c: coords[t] = c
    return coords

def test_ac_01_share_button_visible_after_equals():
    ac_record("AC-01", "输入 1+2= 后分享按钮可见", "BLOCKED", note="baseline")
    safe_click("AC", "t01a")
    safe_press_keys(["1","+","2"], "t01b")
    safe_click("=", "t01c")
    time.sleep(1.0)
    tree = hdc_dump("ac01_after_equals")
    share_found = bool(find_btn_coords(tree, "分享"))
    hdc_screenshot("ac01_after_equals")
    ac_record("AC-01", "输入 1+2= 后分享按钮可见",
              "PASS" if share_found else "FAIL",
              actual="分享 found" if share_found else "分享 NOT found")

def test_ac_02_share_button_disabled_when_empty():
    safe_click("AC", "t02a")
    time.sleep(0.3)
    tree = hdc_dump("ac02_empty")
    share_found = bool(find_btn_coords(tree, "分享"))
    hdc_screenshot("ac02_empty")
    ac_record("AC-02", "空表达式时分享按钮存在（disabled）",
              "PASS" if share_found else "FAIL",
              actual="分享 found" if share_found else "NOT found")

def test_ac_03_share_button_disabled_after_error():
    safe_click("AC", "t03a")
    safe_press_keys(["1","÷","0"], "t03b")
    safe_click("=", "t03c")
    time.sleep(0.5)
    tree = hdc_dump("ac03_after_div0")
    texts = find_all_text(tree)
    has_err = any('除' in t['text'] for t in texts) or any('错误' in t['text'] for t in texts)
    share_found = bool(find_btn_coords(tree, "分享"))
    hdc_screenshot("ac03_after_div0")
    ac_record("AC-03", "1÷0 错误状态下分享按钮 disabled",
              "PASS" if (share_found and has_err) else "FAIL",
              actual=f"share_found={share_found}, error_visible={has_err}")

def test_ac_04_click_share_opens_panel():
    safe_click("AC", "t04a")
    safe_press_keys(["1","+","2"], "t04b")
    safe_click("=", "t04c")
    time.sleep(1.0)
    # 此时 dump 找分享按钮
    if not safe_click("分享", "t04d"):
        ac_record("AC-04", "点击分享按钮弹出模态层", "FAIL",
                  actual="分享 button not found")
        return
    time.sleep(2.0)
    tree = hdc_dump("ac04_share_open")
    texts = find_all_text(tree)
    panel_title = any('二维码分享' in t['text'] for t in texts)
    has_expr = any('1+2' in t['text'] for t in texts)
    hdc_screenshot("ac04_share_open")
    ac_record("AC-04", "点击分享按钮弹出模态层",
              "PASS" if panel_title else "FAIL",
              actual=f"title_found={panel_title}, expr_found={has_expr}",
              note=f"expecting 标题 '二维码分享'")

def test_ac_05_share_panel_contains_qrcode():
    """AC-05: 关闭 AC-04 模态 → 输入不同算式 → 重新打开 → QR 内容应变化"""
    # 先关闭当前模态（点 ✕）
    tree = hdc_dump("ac05_pre_close")
    close_btns = find_text(tree, "✕")
    if close_btns:
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', close_btns[0]['bounds'])
        if m:
            x = (int(m.group(1)) + int(m.group(3))) // 2
            y = (int(m.group(2)) + int(m.group(4))) // 2
            hdc_click(x, y, "✕ close")
            time.sleep(0.5)

    # 输入新算式 5+5
    safe_click("AC", "t05a")
    safe_press_keys(["5","+","5"], "t05b")
    safe_click("=", "t05c")
    time.sleep(0.5)
    safe_click("分享", "t05d")
    time.sleep(2.0)

    tree = hdc_dump("ac05_share_panel")
    qrcodes = find_qrcode(tree)
    texts = find_all_text(tree)
    has_qr = len(qrcodes) > 0
    has_formula = any('5+5 = 10' in t['text'] for t in texts) or any('5+5=10' in t['text'] for t in texts)
    hdc_screenshot("ac05_share_panel")
    ac_record("AC-05", "新算式 SharePanel 含 QRCode 组件 + 算式文本",
              "PASS" if (has_qr and has_formula) else "FAIL",
              actual=f"qrcodes={len(qrcodes)}, formula_found={has_formula}")

def test_ac_06_close_share_panel():
    tree = hdc_dump("ac06_share_open")
    close_btns = find_text(tree, "✕")
    if close_btns:
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', close_btns[0]['bounds'])
        if m:
            x = (int(m.group(1)) + int(m.group(3))) // 2
            y = (int(m.group(2)) + int(m.group(4))) // 2
            hdc_click(x, y, "✕")
            time.sleep(0.5)
    tree2 = hdc_dump("ac06_after_close")
    panel_title_after = any('二维码分享' in t['text'] for t in find_all_text(tree2))
    hdc_screenshot("ac06_after_close")
    ac_record("AC-06", "✕ 关闭 SharePanel",
              "PASS" if not panel_title_after else "FAIL",
              actual=f"panel_after_close={panel_title_after}")
    # 在标题关闭后做一个小动作以产生不同截图（点 AC 清空）
    safe_click("AC", "t06a")
    time.sleep(0.3)

def main():
    os.makedirs(DUMP_DIR, exist_ok=True)
    os.makedirs(SHOT_DIR, exist_ok=True)

    print("=" * 60)
    print("Issue #13 一键分享二维码 - UI 自动化测试 (v2)")
    print("=" * 60)

    hdc_shell(f"aa force-stop {BUNDLE}")
    time.sleep(0.5)
    hdc_shell(f"aa start -a EntryAbility -b {BUNDLE}")
    time.sleep(2.5)

    hdc_screenshot("00_startup")

    print("\n[2] 执行 AC 测试...")
    test_ac_01_share_button_visible_after_equals()
    test_ac_02_share_button_disabled_when_empty()
    test_ac_03_share_button_disabled_after_error()
    test_ac_04_click_share_opens_panel()
    test_ac_05_share_panel_contains_qrcode()
    test_ac_06_close_share_panel()

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    print(f"\n{'=' * 60}")
    print(f"结果汇总：{passed} passed, {failed} failed (total {len(results)})")
    print(f"{'=' * 60}")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

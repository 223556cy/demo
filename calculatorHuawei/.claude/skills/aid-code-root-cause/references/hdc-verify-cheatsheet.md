# hdc 验证速查表(aid-code-root-cause 专用)

> **本文件是 `harmonyos-ui-test` skill 中 hdc 命令的精简摘录**,专门服务本 skill 的根因验证场景(单次 dump / 截图 / 重放操作),不替代完整的 UI 测试套件维护。
>
> 完整内容(测试用例格式、状态机、重试机制、报告模板)见 [../../harmonyos-ui-test/SKILL.md](../../harmonyos-ui-test/SKILL.md)。

## 何时用

在做 6 角度分析时,**静态读代码不确定某个假设**,主动跑一次 hdc 验证。本 skill 范围内最高频的 4 个用法:

1. **UI 树 dump** — 看控件的 text / bounds / clickable / id,验证"控件存在 / 状态值对 / 可点击区在哪"
2. **截图** — 验证视觉(颜色、布局、像素),screenshot 像素采样或颜色直方图
3. **重放操作** — click / input / swipe / keyevent,触发代码路径后再 dump 对比
4. **前后对比** — 操作前 dump → 操作 → 操作后 dump,看哪些节点变了

## 何时不用

要"维护并跑完整 UI 测试套件"(测例、回归、覆盖)→ 调 `harmonyos-ui-test` skill。
本 cheatsheet 只够做**单次验证**,不是测例。

---

## 0. hdc 版本检测(必须首先执行一次)

hdc 3.x 和 2.x 的子命令名不同,**不检测就报错**。一次性脚本:

```python
import subprocess, json

def detect_hdc_api():
    """检测 hdc 版本,返回 API 配置。"""
    r = subprocess.run(['hdc', 'version'], capture_output=True, text=True)
    help_out = subprocess.run(['hdc', 'shell', 'uitest', 'help'],
                              capture_output=True, text=True).stdout
    cfg = {
        'version': r.stdout.strip(),
        'dump_cmd': None, 'dump_format': None,
        'screenshot_cmd': None, 'screenshot_suffix': None,
    }
    if 'dumpLayout' in help_out:
        cfg.update(dump_cmd='dumpLayout', dump_format='json')
    elif 'dump ' in help_out:
        cfg.update(dump_cmd='dump', dump_format='xml')
    if 'screenCap' in help_out:
        cfg.update(screenshot_cmd='uitest_screenCap', screenshot_suffix='.png')
    else:
        if subprocess.run(['hdc', 'shell', 'snapshot_display', '-h'],
                          capture_output=True).returncode == 0:
            cfg.update(screenshot_cmd='snapshot_display', screenshot_suffix='.jpeg')
    if not cfg['dump_cmd'] or not cfg['screenshot_cmd']:
        raise RuntimeError(f"Unsupported hdc version: {cfg['version']}")
    return cfg

hdc_api = detect_hdc_api()
print(f"hdc {hdc_api['version']}: dump={hdc_api['dump_cmd']}({hdc_api['dump_format']})")
```

---

## 1. UI 树 dump + 解析(最常用)

### 命令

```bash
# hdc 3.x (JSON 输出)
hdc shell uitest dumpLayout -p /data/local/tmp/uidump.xml

# hdc 2.x (XML 输出)
hdc shell uitest dump -p /data/local/tmp/uidump.xml

# 拉取到本地(Windows 注意 MSYS_NO_PATHCONV / 用绝对路径)
hdc file recv /data/local/tmp/uidump.xml /d/<你的绝对路径>/uidump.xml
```

### 解析(自动适配 JSON/XML)

```python
import xml.etree.ElementTree as ET
import json, re

def parse_ui_tree(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read().decode('utf-8')
    return _parse_json_tree(raw) if raw.strip().startswith('{') else _parse_xml_tree(filepath)

def _parse_xml_tree(xml_path):
    tree = ET.parse(xml_path); root = tree.getroot(); nodes = []
    for elem in root.iter():
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', elem.get('bounds', ''))
        if not m: continue
        l, t, r, b = map(int, m.groups())
        nodes.append({
            'text': elem.get('text', ''), 'class': elem.get('class', ''),
            'resource_id': elem.get('resource-id', ''),
            'clickable': elem.get('clickable', '') == 'true',
            'bounds': (l, t, r, b),
            'center': ((l+r)//2, (t+b)//2),
            'width': r-l, 'height': b-t,
        })
    return nodes

def _parse_json_tree(raw):
    data = json.loads(raw); nodes = []
    def walk(node):
        a = node.get('attributes', {})
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', a.get('bounds', ''))
        if m:
            l, t, r, b = map(int, m.groups())
            cx, cy = (l+r)//2, (t+b)//2
        else: l=t=r=b=cx=cy=0
        nodes.append({
            'text': a.get('text', ''), 'class': a.get('type', ''),
            'resource_id': a.get('id', ''),
            'clickable': a.get('clickable', '') == 'true',
            'bounds': (l, t, r, b), 'center': (cx, cy),
            'width': r-l, 'height': b-t,
        })
        for c in node.get('children', []): walk(c)
    walk(data); return nodes

def find_by_text(nodes, text, exact=True):
    return [n for n in nodes if (n['text'] == text) if exact else (text in n['text'])]
```

### 典型用法(给 6 角度对应)

| 角度 | dump 验证什么 |
|---|---|
| State consistency | 找同名字段在 2 个 dump 里值是否一致 |
| Timing | 操作前后 100ms 内连 dump 2 次,看异步字段填充 |
| Defaults | 启动后立即 dump,看默认值字段(`@State xMin` 的 text 节点) |
| Verification | 触发功能后 dump,看输出控件的 text / 节点存在性 |
| Errors | 异常路径下 dump,看是否弹出错误提示节点 |
| Resources | 多次进入/退出同一 page,看资源是否堆积(节点数趋势) |

---

## 2. 截图(视觉验证)

```bash
# hdc 3.x
hdc shell uitest screenCap -p /data/local/tmp/shot.png

# hdc 2.x
hdc shell snapshot_display -f /data/local/tmp/shot.jpeg

# 拉取
hdc file recv /data/local/tmp/shot.png /d/<绝对路径>/shot.png
```

### Python 封装

```python
import subprocess, os, time

def hdc_screenshot(local_path, hdc_api):
    """截图,自动适配 hdc 2.x / 3.x,文件名后缀要匹配。"""
    suffix = hdc_api['screenshot_suffix']
    remote = f"/data/local/tmp/shot_{int(time.time()*1000)}{suffix}"
    cmd_map = {
        'uitest_screenCap': ['hdc', 'shell', 'uitest', 'screenCap', '-p', remote],
        'snapshot_display': ['hdc', 'shell', 'snapshot_display', '-f', remote],
    }
    subprocess.run(cmd_map[hdc_api['screenshot_cmd']], check=True)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    subprocess.run(['hdc', 'file', 'recv', remote, local_path], check=True)
    subprocess.run(['hdc', 'shell', 'rm', remote], capture_output=True)
    return local_path
```

### 典型用法

- **像素采样**:验证颜色 / 位置 / 大小 — `PIL.Image.open(path).getpixel((x, y))`
- **颜色直方图**:对比前后两张图的直方图,看 UI 是否真的变化
- **OCR**(可选):用 tesseract 读截图文字,验证 label 文字内容

---

## 3. 重放操作(触发代码路径)

```bash
# 点击坐标(推荐)
hdc shell uitest uiInput click <x> <y>

# 输入文本到当前焦点
hdc shell input text "<text>"

# 滑动 (x1,y1) → (x2,y2)
hdc shell uitest uiInput swipe <x1> <y1> <x2> <y2>

# 按键
hdc shell input keyevent KEYCODE_BACK    # 返回
hdc shell input keyevent KEYCODE_HOME    # Home
hdc shell input keyevent KEYCODE_APP_SWITCH  # 最近任务
```

### Python 封装

```python
import subprocess, time

def hdc_click(x, y):
    subprocess.run(['hdc', 'shell', 'uitest', 'uiInput', 'click', str(x), str(y)],
                   check=True, capture_output=True)

def hdc_click_node(node):
    hdc_click(*node['center'])

def hdc_input_text(text):
    import shlex
    subprocess.run(['hdc', 'shell', 'input', 'text', shlex.quote(text)], check=True)

def hdc_type_in_field(node, text):
    hdc_click_node(node); time.sleep(0.5); hdc_input_text(text)

def hdc_swipe(x1, y1, x2, y2):
    subprocess.run(['hdc', 'shell', 'uitest', 'uiInput', 'swipe',
                    str(x1), str(y1), str(x2), str(y2)], check=True)

def hdc_scroll_up():    hdc_swipe(630, 1800, 630, 900)   # 假设屏 1260x2720
def hdc_scroll_down():  hdc_swipe(630, 900, 630, 1800)
def hdc_press_back():   subprocess.run(['hdc', 'shell', 'input', 'keyevent', 'KEYCODE_BACK'], check=True)
```

---

## 4. 验证 workflow(给 6 角度用)

**典型模式:操作前 dump → 操作 → 操作后 dump → diff**

```python
def verify_state_change(before_action, action_fn, after_action_check, hdc_api):
    """
    before_action:  None 或 callable → 准备态
    action_fn:      callable(hdc_api) → 触发动作(click / swipe / ...)
    after_action_check: callable(nodes_after) → 验证变更
    """
    if before_action: before_action()
    dump_before = parse_ui_tree(dump_ui(hdc_api))   # 见 §1
    action_fn(hdc_api)
    time.sleep(0.5)  # 给 UI 渲染时间,异步路径可能要更长
    dump_after = parse_ui_tree(dump_ui(hdc_api))

    before_texts = {n['resource_id']: n['text'] for n in dump_before if n['resource_id']}
    after_texts  = {n['resource_id']: n['text'] for n in dump_after  if n['resource_id']}
    diff = {rid: (before_texts[rid], after_texts[rid])
            for rid in before_texts.keys() & after_texts.keys()
            if before_texts[rid] != after_texts[rid]}

    return after_action_check(dump_after), diff
```

### 配合 6 角度的 3 个常用 pattern

| 角度 | 验证 pattern |
|---|---|
| **State consistency** | 操作前 dump → onChange 触发 → 操作后 dump,看 `@State` 字段对应的 text 节点是否更新 |
| **Timing** | `setTimeout`/`Promise` 路径:操作 → **立即 dump (0ms)** + **100ms dump** + **500ms dump**,看哪一刻字段就位 |
| **Errors** | 故意触发错误路径(输错密码、传非法参数)→ dump,看是否出现 toast / 错误提示节点 |

---

## 5. 输出约定(给 aid-code-root-cause 用)

跑完验证后,验证结果写到 `report.md` 的 finding 条目里(参考 templates/llm-prompt-template.md):

```markdown
### [major] Timing
- **位置**: GraphPage.ets:54-56
- **角度**: Timing
- **类型**: prefs.init vs setTimeout 竞态
- **代码 diff**: ...
- **验证**(可选,但强烈推荐):
  - 操作:打开 GraphPage
  - 验证命令:`hdc shell uitest dumpLayout -p /data/local/tmp/dump.xml && hdc file recv ...`
  - dump 对比:操作前 `radianMode=false` 节点 → 操作后仍 `radianMode=false`(预期应为 true)
  - 结论:验证假设成立,setTimeout 抢在 prefs.init 完成前跑完
- **修复建议**: ...
```

---

## 6. 局限 / 不做

本 cheatsheet **不够**做:

- **测例维护** → 调 `harmonyos-ui-test` skill
- **测试报告生成**(03_测试报告.md 模板)→ 同上
- **状态机 / 阻塞链 / 重试** → 同上
- **Excel / Markdown 用例管理** → 同上

要把验证做成"可重复回归套件"而非"单次确认",**调 harmonyos-ui-test**,不是本 cheatsheet。

---

## 参考

- [harmonyos-ui-test SKILL.md §核心测试工具:hdc 命令](../../harmonyos-ui-test/SKILL.md)(完整 1456 行版本)
- [harmonyos-ui-test ui_test_skill_flow.md](../../harmonyos-ui-test/ui_test_skill_flow.md)(执行流程图)

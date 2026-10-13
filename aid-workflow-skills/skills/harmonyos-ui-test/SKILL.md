---
name: harmonyos-ui-test
description: 使用 hdc (HarmonyOS Device Connector) 和 hvigorw 等通用命令行工具对 HarmonyOS 应用进行自动化 UI 测试。当用户需要在 HarmonyOS 应用上执行 UI 测试、从 Excel 或 Markdown 文件执行测试用例、截图取证、通过无障碍树验证 UI 状态或生成测试报告时使用此 skill。触发词包括："run tests"、"test the app"、"execute test cases"、"UI testing"、"automated testing"、"test on emulator/device"、"验证"、"测试"、"跑测试用例"、"自动化测试"，即使用户没有明确提到此 skill 也应触发。
---

# HarmonyOS UI 自动化测试

基于 hdc (HarmonyOS Device Connector)、hvigorw 等通用命令行工具的 HarmonyOS (ArkTS) 应用自动化 UI 测试工作流，支持模拟器和真机。不依赖 DevEco Studio 或任何 MCP 工具。

## 参数

用户通过自然语言传入测试场景参数，Skill 自动解析。

### 测试场景参数

Excel B 列或 Markdown 用例的前置条件定义了用例的执行前提。分析前置条件可提取出以下场景维度：

| 维度 | 可选值 | B列关键词 | 说明 |
|------|--------|-----------|------|
| 账户类型 | `VIP` / `非VIP` | `是会员`、`不是会员` | 会员状态影响功能可用性、UI显示 |
| 存储权限 | `有权限` / `无权限` | `已获取存储权限`、`没有获取存储权限` | 影响文件保存流程 |
| 生成状态 | `生成中` / `生成完成` / `生成后` | `生成中`、`生成完成`、`生成后` | 大纲/PPT生成的不同阶段 |

**默认使用 VIP 账户测试**。除非用户明确指定非VIP，否则一律用 VIP 账户执行。

用户传入示例：
- "跑测试" / "测试一下" → `account_type=VIP`（默认）
- "用 VIP 账户跑测试" → `account_type=VIP`
- "非VIP测试" / "用非会员测试" → `account_type=非VIP`

**存储权限和生成状态不需要用户传入**——它们是测试流程中自然到达的状态，由测试执行过程自动满足。只有账户类型需要用户指定（且默认VIP），因为它决定了登录的账户。

### 用例筛选与状态依赖规则

阶段零分析时，根据 B 列前置条件和当前参数决定每条用例的处理方式：

```python
def classify_case(precondition, account_type):
    """
    返回: 'execute' | 'skip' | 'state_dependent'
    - execute: 本次立即执行
    - skip: 本次跳过（前置条件不匹配当前账户）
    - state_dependent: 依赖运行时状态（需要在特定状态下执行）
    
    用例分配规则（VIP 为默认测试账户）：
    - VIP测试（默认）：测试所有通用用例 + VIP专属用例
    - 非VIP测试：只测试明确标注"非会员"的用例
    """
    p = precondition.strip() if precondition else ''
    
    # VIP 专属用例
    if p in ['是会员', 'VIP', '已开通']:
        return 'execute' if account_type == 'VIP' else 'skip'
    
    # 非VIP 专属用例
    if p in ['不是会员', '非会员', '非VIP']:
        return 'execute' if account_type == '非VIP' else 'skip'
    
    # 状态依赖（测试流程自动到达）
    if p in ['生成中', '生成完成', '生成后', '已获取存储权限', '没有获取存储权限']:
        return 'state_dependent'
    
    # 无前置条件 → 通用用例
    # 规则：通用用例在VIP测试（默认）中执行，非VIP测试跳过
    if not p:
        return 'execute' if account_type == 'VIP' else 'skip'
    
    # 其他前置条件 → 通用，两种账户都执行
    return 'execute'
```

**跳过的用例**：本次跳过的行在 F 列留空，等对应账户测试时再填写。不写"跳过"文案——空值本身就表示"本次未测"。

### 状态依赖用例的执行策略

**关键状态节点**（从 B 列前置条件提取）：
- `生成中`：大纲/PPT 正在生成的过程中
- `生成完成`：大纲/PPT 生成完毕
- `生成后`：生成完成后的页面状态
- `已获取存储权限` / `没有获取存储权限`：权限申请前后

**执行策略**：
1. **阶段零识别状态转换链**：
   - 分析 Excel 找出状态依赖用例的分布
   - 识别关键依赖节点（如"大纲生成"是后续 100 个用例的前置）
   - 在 `01_用例分析.md` 中绘制状态转换图

2. **阶段二动态状态检测**：
   - 执行到触发状态转换的操作时（如"点击立即生成"），**不要立即跳到下一行**
   - 而是：
     a. 执行操作（点击生成按钮）
     b. 循环 dump UI 树，检测状态变化（如出现"正在生成"文案 → 进入"生成中"状态）
     c. **立即执行所有 B 列为"生成中"的用例**（验证 loading、停止按钮等）
     d. 继续等待状态转换（"生成中" → "生成完成"）
     e. **立即执行所有 B 列为"生成完成"的用例**（验证大纲内容、重新生成按钮等）
     f. 然后继续线性执行后续用例

3. **阻塞链识别与快速失败**：
   - 如果关键依赖节点失败（如大纲生成失败），**立即标记所有依赖该状态的用例为"阻塞"**
   - 不要逐个执行后发现都失败，而是批量标记：
     ```python
     if outline_generation_failed:
         for row in dependent_rows:
             ws.cell(row, 6, '阻塞: 大纲生成失败，无法执行')
             ws.cell(row, 8, time_str)
     ```

**状态转换示例**（大纲生成流程）：

```
[输入主题] → 点击"立即生成" → [生成中] → [生成完成] → 点击"选择模板" → [模板选择页]
                                  ↓              ↓
                            执行行123-130    执行行136-158
                            (验证loading)   (验证大纲内容)
```

**在 01_用例分析.md 中记录**：
- 状态依赖用例的行号范围
- 状态转换触发条件（哪个操作触发状态变化）
- 阻塞链（哪些用例依赖哪个关键节点）

### 隐含的账户差异

即使 B 列未标注，以下功能在 VIP/非VIP 下表现不同，测试时需注意：
- **VIP**: 无水印、无免费次数限制、全部模板可用、会员标显示"已是会员"
- **非VIP**: 有水印、有免费次数限制、部分模板锁定、会员标显示"开通会员"
- 在 `01_用例分析.md` 中标注这些隐含差异

## 测试用例格式

支持三种用例输入格式。Skill 根据文件扩展名自动识别。

### 格式一：Markdown Checkbox List（.md）— 推荐快速/临时测试

最简格式：一个 checkbox list 文件。适合快速编写、版本控制友好。

**语法规则：**

```markdown
# 测试用例标题

## 模块名
- [ ] **(前置条件) 操作步骤描述** → 预期: 预期结果描述
- [ ] **操作步骤描述** → 预期: 预期结果描述
```

| 语法元素 | 说明 | 示例 |
|----------|------|------|
| `- [ ]` | 待测试用例（测试后变为 `- [x]`） | |
| `**粗体**` | 操作步骤（必填） | `**点击"立即生成"按钮**` |
| `→ 预期:` | 预期结果标记（必填） | `→ 预期: 跳转到生成页面` |
| `(VIP)` / `(是会员)` | VIP 专属前置条件 | `**(VIP) 点击会员功能**` |
| `(非会员)` | 非VIP 专属前置条件 | `**(非会员) 验证水印显示**` |
| `[生成中]` / `[生成完成]` / `[生成后]` | 状态依赖标记 | `**[生成中] 验证loading**` |
| `[已获取存储权限]` / `[没有获取存储权限]` | 权限状态标记 | `**[已获取存储权限] 验证保存**` |

**完整示例**（见 `examples/TestCase.example.md`）：

```markdown
# AI PPT 生成器 测试用例

> 应用: com.example.aippt | 默认账户: VIP

## 首页
- [ ] **(VIP) 点击"立即生成"按钮** → 预期: 跳转到大纲生成页面
- [ ] **点击"设置"图标** → 预期: 弹出设置菜单
- [ ] **(非会员) 验证水印显示** → 预期: 页面底部显示"Powered by AI"水印

## 大纲生成
- [ ] **输入主题"AI的未来"** → 预期: 输入框显示完整文本
- [ ] **[生成中] 验证loading动画** → 预期: 显示旋转loading图标
- [ ] **[生成完成] 验证大纲内容** → 预期: 显示3个以上章节标题
```

### 格式二：Markdown 表格（.md）— 兼容 Excel 列结构

与 Excel 列结构一致的 Markdown 表格，方便在 GitHub/GitLab 上直接查看和编辑。

```markdown
| # | 模块 | 前置条件 | 操作步骤 | 预期结果 | 结果 | 时间 |
|---|------|----------|----------|----------|------|------|
| 1 | 首页 | 是会员 | 点击"立即生成" | 进入大纲生成页面 | | |
```

### 格式三：Excel（.xlsx）— 推荐正式/大规模测试

适合 100+ 用例的正式测试，支持行着色、截图嵌入、富文本格式。

### 格式自动识别

```python
def detect_format(test_file):
    """根据文件扩展名返回 'xlsx' | 'md_list' | 'md_table'"""
    ext = os.path.splitext(test_file)[1].lower()
    if ext == '.xlsx':
        return 'xlsx'
    if ext == '.md':
        with open(test_file, 'r') as f:
            content = f.read()
        if '|' in content and '---' in content:
            return 'md_table'
        return 'md_list'
    raise ValueError(f'Unsupported format: {ext}')
```

---

## 前置条件

- hdc (HarmonyOS Device Connector) 已安装且在 PATH 中（随 HarmonyOS SDK 提供）
- hvigorw 已安装（随 HarmonyOS SDK 提供，用于构建 HAP）
- 应用已安装并在模拟器或真机上运行
- Python 3 已安装 `openpyxl` 和 `Pillow` (`pip3 install openpyxl Pillow`)
- **测试用例文件**（项目根目录，以下三种之一）：
  - **Excel (.xlsx)**：A=模块, B=前置条件, C=操作步骤, D=预期结果, E=备注（可选）。结果写入 F/G/H 列。
  - **Markdown Checkbox List (.md)**：checkbox list 格式，操作步骤用 `**粗体**`，预期结果用 `→ 预期:`。结果直接更新 checkbox + 追加到行尾。
  - **Markdown 表格 (.md)**：列结构同 Excel，结果写入"结果"和"时间"列。
- **直接在源文件上操作**，不复制副本。
- VIP 测试（默认）执行通用用例 + VIP专属用例，非VIP 测试只执行非VIP专属用例。

## 核心测试工具：hdc 命令

> **不依赖 DevEco Studio 或 codegenie-mcp MCP**。所有 UI 操作通过 hdc（HarmonyOS Device Connector）命令行工具完成。
>
> **⚠️ hdc 版本差异**：不同 hdc 版本的子命令名称不同。Skill 使用 `detect_hdc_api()` 自动适配。

### 0. hdc 版本检测（必须首先执行）

```python
import subprocess, json

def detect_hdc_api():
    """检测 hdc 版本及可用 API，返回 API 配置字典。
    
    hdc 3.x 和 2.x 的命令名不同：
    - 3.x: uitest dumpLayout (JSON), uitest screenCap (PNG)
    - 2.x: uitest dump (XML), snapshot_display (JPEG)
    """
    r = subprocess.run(['hdc', 'version'], capture_output=True, text=True)
    ver_str = r.stdout.strip()
    
    # 检测可用命令
    help_out = subprocess.run(['hdc', 'shell', 'uitest', 'help'], 
                              capture_output=True, text=True).stdout
    
    config = {
        'version': ver_str,
        'dump_cmd': None,        # UI 树 dump 子命令
        'dump_format': None,     # 'json' | 'xml'
        'screenshot_cmd': None,  # 截图命令
        'screenshot_suffix': None,  # 截图文件后缀
    }
    
    # 检测 UI dump 命令
    if 'dumpLayout' in help_out:
        config['dump_cmd'] = 'dumpLayout'
        config['dump_format'] = 'json'
    elif ' dump ' in help_out or 'dump ' in help_out:
        config['dump_cmd'] = 'dump'
        config['dump_format'] = 'xml'
    
    # 检测截图命令（优先 uitest screenCap）
    if 'screenCap' in help_out:
        config['screenshot_cmd'] = 'uitest_screenCap'
        config['screenshot_suffix'] = '.png'
    else:
        # fallback: snapshot_display (需要 .jpeg 后缀)
        r2 = subprocess.run(['hdc', 'shell', 'snapshot_display', '-h'],
                           capture_output=True, text=True)
        if r2.returncode == 0:
            config['screenshot_cmd'] = 'snapshot_display'
            config['screenshot_suffix'] = '.jpeg'
    
    if not config['dump_cmd'] or not config['screenshot_cmd']:
        raise RuntimeError(f'Unsupported hdc version: {ver_str}. Cannot detect UI dump or screenshot commands.')
    
    return config

# 在阶段一开始时调用
hdc_api = detect_hdc_api()
print(f'hdc {hdc_api["version"]}: dump={hdc_api["dump_cmd"]}({hdc_api["dump_format"]}), '
      f'screenshot={hdc_api["screenshot_cmd"]}({hdc_api["screenshot_suffix"]})')
```

### 1. UI 树检查 (UITest Dump)

```bash
# hdc 3.x (JSON 输出)
hdc shell uitest dumpLayout -p /data/local/tmp/uidump.xml

# hdc 2.x (XML 输出)
hdc shell uitest dump -p /data/local/tmp/uidump.xml

# 拉取到本地（两种版本通用）
# 注意：hdc file recv 需要绝对路径。Windows 上使用 /d/work/... 或 $(pwd)/ai_auto_test/...
hdc file recv /data/local/tmp/uidump.xml {absolute_test_dir}/dump/uidump_{step}.xml
```

**统一解析函数**（自动适配 JSON/XML）：

```python
import xml.etree.ElementTree as ET
import json, re

def parse_ui_tree(filepath):
    """解析 UI 树文件，自动检测 JSON (hdc 3.x) 或 XML (hdc 2.x) 格式。"""
    with open(filepath, 'rb') as f:
        raw = f.read().decode('utf-8')
    
    if raw.strip().startswith('{'):
        return _parse_json_tree(raw)
    else:
        return _parse_xml_tree(filepath)

def _parse_xml_tree(xml_path):
    """解析 UITest XML 文件 (hdc 2.x)"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    nodes = []
    for elem in root.iter():
        bounds = elem.get('bounds', '')
        text = elem.get('text', '')
        cls = elem.get('class', '')
        rid = elem.get('resource-id', '')
        clickable = elem.get('clickable', 'false') == 'true'
        checked = elem.get('checked', 'false') == 'true'
        enabled = elem.get('enabled', 'false') == 'true'
        
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        if match:
            left, top, right, bottom = map(int, match.groups())
        else:
            continue
        
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        nodes.append({
            'text': text, 'class': cls, 'resource_id': rid,
            'clickable': clickable, 'checked': checked, 'enabled': enabled,
            'bounds': (left, top, right, bottom),
            'center': (center_x, center_y),
            'width': right - left, 'height': bottom - top
        })
    return nodes

def _parse_json_tree(raw_json):
    """解析 dumpLayout JSON 格式 (hdc 3.x)"""
    data = json.loads(raw_json)
    nodes = []
    
    def walk(node):
        attrs = node.get('attributes', {})
        bounds_str = attrs.get('bounds', '')
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if m:
            l, t, r, b = map(int, m.groups())
            cx, cy = (l + r) // 2, (t + b) // 2
        else:
            l = t = r = b = cx = cy = 0
        
        nodes.append({
            'text': attrs.get('text', ''),
            'description': attrs.get('description', ''),
            'class': attrs.get('type', ''),
            'resource_id': attrs.get('id', ''),
            'clickable': attrs.get('clickable', '') == 'true',
            'checked': attrs.get('checked', '') == 'true',
            'enabled': attrs.get('enabled', '') == 'true',
            'scrollable': attrs.get('scrollable', '') == 'true',
            'bounds': (l, t, r, b),
            'center': (cx, cy),
            'width': r - l,
            'height': b - t
        })
        
        for child in node.get('children', []):
            walk(child)
    
    walk(data)
    return nodes
```

**UI 树的 JSON 格式说明 (hdc 3.x / dumpLayout)**：

每个节点的 `attributes` 字典包含以下关键属性：

| 属性 | 说明 | 示例 |
|------|------|------|
| `text` | 显示文本 | `"text": "7"` |
| `type` | 控件类型 | `"type": "Text"` |
| `id` | 资源 ID | `"id": "btn_calc"` |
| `bounds` | 边界坐标 | `"bounds": "[190,942][482,1166]"` |
| `clickable` | 是否可点击 | `"clickable": "true"` |
| `checked` | 是否选中 | `"checked": "true"` |
| `scrollable` | 是否可滚动 | `"scrollable": "true"` |
| `enabled` | 是否可用 | `"enabled": "true"` |
| `description` | 无障碍描述 | `"description": "等于"` |

**UI 树的 XML 格式说明 (hdc 2.x / uitest dump)**：

每个节点的关键属性：

| 属性 | 说明 | 示例 |
|------|------|------|
| `text` | 显示文本 | `text="立即生成"` |
| `resource-id` | 资源 ID | `resource-id="com.example:id/btn_create"` |
| `class` | 控件类名 | `class="android.widget.Button"` |
| `bounds` | 边界坐标 | `bounds="[52,2501][1204,2676]"` |
| `clickable` | 是否可点击 | `clickable="true"` |
| `checked` | 是否选中 | `checked="true"` |
| `scrollable` | 是否可滚动 | `scrollable="true"` |
| `enabled` | 是否可用 | `enabled="true"` |

**统一查询函数**（不区分 JSON/XML）：

```python
def find_by_text(nodes, text, exact=True):
    """查找包含指定文本的节点"""
    if exact:
        return [n for n in nodes if n['text'] == text]
    return [n for n in nodes if text in n['text']]

def find_clickable_with_text(nodes, text):
    """查找可点击且包含指定文本的节点（最常用）"""
    return [n for n in nodes if n['clickable'] and text in (n['text'] or '')]
```

### 2. UI 操作

#### 2.1 点击

```bash
# 方式一：点击坐标（推荐）
hdc shell uitest uiInput click <x> <y>

# 方式二：触摸屏点击（备选）
hdc shell mouse click <x> <y>
```

**Python 封装：**
```python
import subprocess

def hdc_click(x, y):
    """在指定坐标点击"""
    subprocess.run(['hdc', 'shell', 'uitest', 'uiInput', 'click', str(x), str(y)], 
                   check=True, capture_output=True, text=True)

def hdc_click_node(node):
    """点击 UI 树节点的中心"""
    x, y = node['center']
    hdc_click(x, y)
```

#### 2.2 输入文本

```bash
# 输入文本到当前焦点输入框
hdc shell input text "<your_text>"

# 备选：先点击输入框获取焦点，再输入
hdc shell uitest uiInput click <x> <y>
hdc shell input text "<your_text>"
```

**Python 封装：**
```python
def hdc_input_text(text):
    """输入文本（需要输入框已获取焦点）"""
    import shlex
    escaped = shlex.quote(text)
    subprocess.run(['hdc', 'shell', 'input', 'text', escaped], 
                   check=True, capture_output=True, text=True)

def hdc_type_in_field(node, text):
    """点击输入框后输入文本"""
    hdc_click_node(node)
    import time
    time.sleep(0.5)
    hdc_input_text(text)
```

#### 2.3 滑动

```bash
# 从 (x1, y1) 滑动到 (x2, y2)
hdc shell uitest uiInput swipe <x1> <y1> <x2> <y2>

# 方向滑动常量：
# 向上: y1 > y2（从屏幕下方滑到上方）
# 向下: y1 < y2
# 向左: x1 > x2
# 向右: x1 < x2
```

**Python 封装：**
```python
def hdc_swipe(x1, y1, x2, y2):
    """从 (x1,y1) 滑动到 (x2,y2)"""
    subprocess.run(['hdc', 'shell', 'uitest', 'uiInput', 'swipe',
                    str(x1), str(y1), str(x2), str(y2)],
                   check=True, capture_output=True, text=True)

def hdc_scroll_up():
    """向上滚动半个屏幕"""
    # 假设屏幕 1260x2720，从屏幕 2/3 滑到 1/3
    hdc_swipe(630, 1800, 630, 900)

def hdc_scroll_down():
    """向下滚动半个屏幕"""
    hdc_swipe(630, 900, 630, 1800)
```

#### 2.4 按键事件

```bash
# Back 键
hdc shell input keyevent KEYCODE_BACK

# Home 键
hdc shell input keyevent KEYCODE_HOME

# Recent Apps
hdc shell input keyevent KEYCODE_APP_SWITCH
```

**Python 封装：**
```python
def hdc_press_back():
    """按返回键"""
    subprocess.run(['hdc', 'shell', 'input', 'keyevent', 'KEYCODE_BACK'],
                   check=True, capture_output=True, text=True)

def hdc_press_home():
    """按 Home 键"""
    subprocess.run(['hdc', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                   check=True, capture_output=True, text=True)
```

#### 2.5 截图

```bash
# hdc 3.x: uitest screenCap (推荐，支持 PNG)
hdc shell uitest screenCap -p /data/local/tmp/screenshot.png

# hdc 2.x: snapshot_display (需要 .jpeg 后缀)
hdc shell snapshot_display -f /data/local/tmp/screenshot.jpeg

# 拉取到本地
# 注意：hdc file recv 需要绝对路径。Windows 上使用 /d/work/... 或 $(pwd)/ai_auto_test/...
hdc file recv /data/local/tmp/screenshot.png {absolute_test_dir}/screenshot/<filename>.png
```

**Python 封装（自动适配 hdc 版本）**：
```python
import os

def hdc_screenshot(local_path, hdc_api):
    """截图并拉取到本地，自动适配 hdc 2.x / 3.x"""
    suffix = hdc_api['screenshot_suffix']
    remote_name = f'_test_screenshot{suffix}'
    remote_path = f'/data/local/tmp/{remote_name}'
    
    if hdc_api['screenshot_cmd'] == 'uitest_screenCap':
        subprocess.run(['hdc', 'shell', 'uitest', 'screenCap', '-p', remote_path],
                       check=True, capture_output=True, text=True)
    else:
        subprocess.run(['hdc', 'shell', 'snapshot_display', '-f', remote_path],
                       check=True, capture_output=True, text=True)
    
    local_path = os.path.abspath(local_path)
    subprocess.run(['hdc', 'file', 'recv', remote_path, local_path],
                   check=True, capture_output=True, text=True)
    return os.path.exists(local_path)
```

### 3. 应用启动与管理

```bash
# 启动应用（需要知道 bundleName 和 abilityName）
hdc shell aa start -a <AbilityName> -b <bundleName>

# 强制停止应用
hdc shell aa force-stop <bundleName>

# 列出运行中的应用
hdc shell aa dump -l
```

**Python 封装：**
```python
def hdc_start_app(bundle_name, ability_name='EntryAbility'):
    """启动或重启应用"""
    # 先停止再启动 = 冷启动
    subprocess.run(['hdc', 'shell', 'aa', 'force-stop', bundle_name],
                   capture_output=True, text=True)
    import time
    time.sleep(1)
    result = subprocess.run(
        ['hdc', 'shell', 'aa', 'start', '-a', ability_name, '-b', bundle_name],
        check=True, capture_output=True, text=True
    )
    return 'success' in result.stdout.lower() or result.returncode == 0
```

### 4. 重试机制

对关键操作（点击后验证页面跳转、网络请求等）实施重试：

```python
import time

MAX_ATTEMPTS = 3
RETRY_DELAY = 10  # 秒

def retry_action(action_fn, verify_fn, description=""):
    """
    重试机制：最多尝试3次，任一次成功即通过。
    - action_fn: 执行操作的函数
    - verify_fn: 验证操作结果的函数，返回 True/False
    - description: 操作描述（用于日志）
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        action_fn()
        time.sleep(2)  # 等待UI响应
        if verify_fn():
            return True
        if attempt < MAX_ATTEMPTS:
            print(f'  [RETRY] {description} 第{attempt}次失败，{RETRY_DELAY}秒后重试...')
            time.sleep(RETRY_DELAY)
    return False
```

适用场景：
- 点击按钮后验证页面跳转（网络延迟可能导致首次失败）
- 等待异步加载完成
- 模拟器偶发的点击无响应

---

## Excel 列规范

### 统一结果列（F/G/H）

VIP 和非VIP 测试共用 F/G/H 三列。每次测试只填写本次负责的行：
- **VIP 测试（默认）**：填写通用用例行 + VIP专属行
- **非VIP 测试**：只填写非VIP专属行（B列为"不是会员"等）

已有结果的行不覆盖——如果 F 列已有值，说明另一次测试已填写，跳过该行。

### 行样式：区分用例类型

在阶段零分析后，通过**背景色 + 字体粗细**两个维度区分用例类型：

**维度一：字体粗细（区分账户归属）**
- **VIP 专属行**：B 列（前置条件列）字体加粗，一眼识别哪些是 VIP 用例
- **其他行**：正常字体

**维度二：背景色（区分前置条件/状态）**

```python
from openpyxl.styles import PatternFill, Font

# 背景色 - 按前置条件状态细分
FILL_NORMAL = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')           # 白色 - 无前置条件/通用
FILL_GENERATING = PatternFill(start_color='FFF9C4', end_color='FFF9C4', fill_type='solid')       # 浅黄 - 生成中
FILL_GENERATED = PatternFill(start_color='C8E6C9', end_color='C8E6C9', fill_type='solid')        # 浅绿 - 生成完成/生成后
FILL_HAS_PERMISSION = PatternFill(start_color='E1F5FE', end_color='E1F5FE', fill_type='solid')   # 浅蓝 - 已获取存储权限
FILL_NO_PERMISSION = PatternFill(start_color='FCE4EC', end_color='FCE4EC', fill_type='solid')    # 浅粉 - 没有获取存储权限
FILL_NON_VIP = PatternFill(start_color='FFF3E0', end_color='FFF3E0', fill_type='solid')          # 浅橙 - 非VIP专属
FILL_VIP = PatternFill(start_color='E8EAF6', end_color='E8EAF6', fill_type='solid')             # 浅靛蓝 - VIP专属

# VIP 行 B 列加粗字体
FONT_VIP_BOLD = Font(bold=True)
FONT_NORMAL = Font(bold=False)

def get_row_fill(precondition):
    """根据 B 列前置条件返回行背景色"""
    p = precondition.strip() if precondition else ''
    if p in ['生成中']:
        return FILL_GENERATING
    elif p in ['生成完成', '生成后']:
        return FILL_GENERATED
    elif p in ['已获取存储权限']:
        return FILL_HAS_PERMISSION
    elif p in ['没有获取存储权限']:
        return FILL_NO_PERMISSION
    elif p in ['是会员', 'VIP', '已开通']:
        return FILL_VIP
    elif p in ['不是会员', '非会员', '非VIP']:
        return FILL_NON_VIP
    return FILL_NORMAL

for row in range(2, ws.max_row + 1):
    precondition = str(ws.cell(row, 2).value or '').strip()
    
    # 设置背景色
    fill = get_row_fill(precondition)
    for col in range(1, 9):  # A-H列
        ws.cell(row, col).fill = fill
    
    # VIP 专属行 B 列加粗
    if precondition in ['是会员', 'VIP', '已开通']:
        ws.cell(row, 2).font = FONT_VIP_BOLD
```

### 结果列字体色：区分测试结果

```python
from openpyxl.styles import Font

FONT_PASS = Font(color='2E7D32', bold=True)      # 深绿 - 通过
FONT_BUG = Font(color='C62828', bold=True)        # 深红 - BUG
FONT_BLOCKED = Font(color='F57C00', bold=False)   # 橙色 - 阻塞
FONT_SKIP = Font(color='9E9E9E', bold=False)      # 灰色 - 跳过/N/A
FONT_REF = Font(color='1565C0', bold=False)       # 蓝色 - 引用

def get_result_font(result_text):
    """根据结果文本返回对应字体样式"""
    if result_text.startswith('通过'):
        return FONT_PASS
    elif result_text.startswith('BUG'):
        return FONT_BUG
    elif result_text.startswith('阻塞'):
        return FONT_BLOCKED
    elif result_text.startswith('跳过') or result_text.startswith('N/A'):
        return FONT_SKIP
    elif result_text.startswith('引用'):
        return FONT_REF
    return Font()

def write_result(ws, row, result_text, time_str):
    """写入测试结果到 F/G/H 列（统一，不区分账户类型）"""
    ws.cell(row, 6, result_text)
    ws.cell(row, 6).font = get_result_font(result_text)
    ws.cell(row, 8, time_str)
```

### 表头样式

```python
from openpyxl.styles import Font, PatternFill, Alignment

HEADER_FILL = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
HEADER_FONT = Font(color='FFFFFF', bold=True, size=11)

headers = [(6, '测试结果'), (7, '截图'), (8, '测试时间')]
for col, title in headers:
    cell = ws.cell(1, col)
    cell.value = title
    cell.fill = HEADER_FILL
    cell.font = HEADER_FONT
    cell.alignment = Alignment(horizontal='center')
```

### 样式图例（在 01_用例分析.md 中说明）

**行背景色（按前置条件区分）：**

| 背景色 | 色值 | 含义 |
|--------|------|------|
| 白色 | `FFFFFF` | 无前置条件 / 通用用例 |
| 浅靛蓝 | `E8EAF6` | VIP 专属（B列加粗） |
| 浅橙 | `FFF3E0` | 非VIP 专属 |
| 浅黄 | `FFF9C4` | 前置条件：生成中 |
| 浅绿 | `C8E6C9` | 前置条件：生成完成 / 生成后 |
| 浅蓝 | `E1F5FE` | 前置条件：已获取存储权限 |
| 浅粉 | `FCE4EC` | 前置条件：没有获取存储权限 |

**字体粗细（区分账户归属）：**

| 样式 | 含义 |
|------|------|
| B列加粗 | VIP 专属用例 |
| B列正常 | 其他用例 |

**F列结果字体色：**

| 字体色 | 含义 |
|--------|------|
| 深绿加粗 | 测试通过 |
| 深红加粗 | BUG |
| 橙色 | 阻塞 |
| 灰色字体 | 跳过/N/A |
| 蓝色字体 | 引用其他模块结果 |

---

## 输出文件规范

测试产物分两部分存放：

1. **用例源文件结果**：直接更新项目根目录的测试用例文件（Excel 的 F/G/H 列 或 Markdown 的 checkbox + 行尾结果）
2. **辅助文件**：存放在 `ai_auto_test/{YYYY-MM-DD_HHmm}_{account_type}/` 子目录中

```
项目根目录/
├── TestCase.xlsx  或  TestCase.md     # 直接更新，结果写回源文件
└── ai_auto_test/
    └── 2026-05-05_2046_vip/           # 本次测试目录
        ├── 01_用例分析.md
        ├── 02_测试执行计划.md
        ├── 03_测试报告.md
        ├── screenshot/
        └── dump/
```

在阶段零开始时创建本次测试目录及子目录：
```python
from datetime import datetime
import os

def normalize_local_path(path):
    """将相对路径转换为绝对路径，确保 hdc file recv 在 Windows/Mac 上正常工作。
    
    hdc file recv 不支持相对路径，必须使用绝对路径。
    """
    return os.path.abspath(path)

account_suffix = 'vip' if account_type == 'VIP' else 'nonvip'
test_dir = normalize_local_path(f'ai_auto_test/{datetime.now().strftime("%Y-%m-%d_%H%M")}_{account_suffix}')
os.makedirs(f'{test_dir}/screenshot', exist_ok=True)
os.makedirs(f'{test_dir}/dump', exist_ok=True)

test_start_time = datetime.now()
```

### 文件说明

| 文件 | 定位 | 何时写 | 内容特点 |
|------|------|--------|----------|
| `TestCase.xlsx` 或 `TestCase.md` | 测试结果记录 | 执行中持续更新（直接修改源文件） | Excel: F列结果+颜色、G列截图、H列时间。Markdown: checkbox打勾+行尾结果+截图链接 |
| `01_用例分析.md` | 测试前的分析思考 | 阶段零完成时 | 用例分类、优化策略、依赖关系、风险识别 |
| `02_测试执行计划.md` | 执行中的进度跟踪 | 阶段零创建，执行中持续更新 | todolist 打勾样式，实时反映完成状态 |
| `03_测试报告.md` | 测试后的统计总结 | 全部测试完成后 | 数据统计、BUG汇总、**开始/结束/耗时** |

---

## 测试方法论

### 五大核心原则

1. **先观察再操作**：每次操作前先 dump UI 树，确认目标元素存在且可交互。盲目点击坐标是最常见的失败原因。
2. **截图即证据（必须嵌入图片）**：每个测试步骤完成后截图。Excel 格式用 `embed_screenshot()` 将图片嵌入 G 列。Markdown 格式将截图链接写入行尾。**禁止将截图路径作为纯文本写入结果列**。
3. **逐行推进**：按用例顺序执行。Excel 格式每完成一行立即写入 F/H 列；Markdown 格式每完成一步立即更新 checkbox 和行尾结果。不要攒到最后批量写入——中途崩溃会丢失所有进度。
4. **状态感知**：测试不是无状态的。前一个用例的操作会改变 app 状态，影响后续用例。规划执行顺序时要考虑状态流转。
5. **失败不阻塞**：单个用例失败后，评估是否影响后续用例。如果不影响，继续执行；如果阻塞，标记后续依赖用例为"阻塞"并说明原因。

### 判定标准

| 结果 | 判定条件 | 结果列写法 |
|------|----------|---------|
| 通过 | UI 树验证与预期完全一致 | `通过` 或 `通过(补充说明)` |
| BUG | 实际行为与预期不符 | `BUG: <具体描述>` |
| 阻塞 | 前置条件未满足或依赖功能异常 | `阻塞: <原因>` |
| 跳过 | 账户类型不匹配或环境限制 | `跳过(<原因>)` |
| N/A | 用例不适用于当前环境 | `N/A: <原因>` |
| 引用 | 结果与其他用例相同 | `引用: 同行XX` |

---

## 测试工作流（六阶段）

### 阶段零：用例分析与规划

**输入**：测试用例文件（`TestCase.xlsx` 或 `TestCase.md`）+ 用户参数（账户类型）+ **bundleName**
**输出**：`01_用例分析.md`、`02_测试执行计划.md`、源文件格式化（Excel 行背景色 / Markdown 分组标注）

#### 步骤 1：检测格式并读取

```python
import os, re, openpyxl
from datetime import datetime

test_file = None
for f in ['TestCase.xlsx', 'TestCase.md', 'test_cases.md', 'test_case.md']:
    if os.path.exists(f):
        test_file = f
        break
if not test_file:
    raise FileNotFoundError('No test case file found. Expected: TestCase.xlsx or TestCase.md')

fmt = detect_format(test_file)
```

#### 步骤 1a：读取 Markdown Checkbox List

```python
def parse_md_list(filepath):
    """解析 checkbox list 格式的 Markdown 测试用例。
    
    返回: list[dict], 每条用例含 module, precondition, action, expected, line_number
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    cases = []
    current_module = ''
    
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 跟踪模块标题 (## xxx)
        if stripped.startswith('## '):
            current_module = stripped[3:].strip()
            continue
        
        # 解析 checkbox 行: - [ ] **操作** → 预期: xxx
        if not stripped.startswith('- [ ]') and not stripped.startswith('- [x]'):
            continue
        
        # 提取操作步骤（**粗体** 内的文本）
        action_match = re.search(r'\*\*(.+?)\*\*', stripped)
        if not action_match:
            continue
        action_raw = action_match.group(1)
        
        # 提取预期结果
        expected_match = re.search(r'→\s*预期:\s*(.+?)$', stripped)
        expected = expected_match.group(1).strip() if expected_match else ''
        
        # 提取前置条件（粗体开头的 (VIP)/[生成中] 等标记）
        precondition = ''
        prefix_match = re.match(r'\(([^)]+)\)\s*', action_raw)
        bracket_match = re.match(r'\[([^\]]+)\]\s*', action_raw)
        
        if prefix_match:
            precondition = prefix_match.group(1)
            action = action_raw[prefix_match.end():].strip()
        elif bracket_match:
            precondition = bracket_match.group(1)
            action = action_raw[bracket_match.end():].strip()
        else:
            action = action_raw
            precondition = ''
        
        cases.append({
            'module': current_module,
            'precondition': precondition,
            'action': action,
            'expected': expected,
            'line_number': lineno,
            'raw_line': stripped,
        })
    
    return cases
```

#### 步骤 1b：读取 Excel

```python
def parse_xlsx(filepath):
    """解析 Excel 测试用例。返回: list[dict]"""
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active
    cases = []
    for row in range(2, ws.max_row + 1):
        a = str(ws.cell(row, 1).value or '').strip()  # 模块
        b = str(ws.cell(row, 2).value or '').strip()  # 前置条件
        c = str(ws.cell(row, 3).value or '').strip()  # 操作步骤
        d = str(ws.cell(row, 4).value or '').strip()  # 预期结果
        if not c:  # 跳过空行
            continue
        cases.append({
            'module': a,
            'precondition': b,
            'action': c,
            'expected': d,
            'row': row,
        })
    return cases, wb, ws
```

#### 步骤 2-4：分类、状态依赖、格式化（通用）

```python
# 分类（Excel 和 Markdown 共用）
for case in cases:
    case['decision'] = classify_case(case['precondition'], account_type)

# 识别状态依赖链
state_dependent = {}
for case in cases:
    if case['decision'] == 'state_dependent':
        state = case['precondition']
        state_dependent.setdefault(state, []).append(case)
```

#### 步骤 5：格式化源文件

**Excel**：设置行背景色、确保 F/G/H 表头、B 列加粗（同原规范）

**Markdown**：在模块标题下添加统计注释，标记依赖关系

```python
def format_md_source(filepath, cases):
    """在 Markdown 源文件中添加模块统计注释和依赖标记。"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    module_stats = {}
    for c in cases:
        m = c['module']
        module_stats.setdefault(m, {'total': 0, 'vip': 0, 'state': []})
        module_stats[m]['total'] += 1
        if c['precondition'] in ['是会员', 'VIP', '已开通']:
            module_stats[m]['vip'] += 1
        if c['decision'] == 'state_dependent':
            module_stats[m]['state'].append(c['precondition'])
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## '):
            mod = stripped[3:].strip()
            output_lines.append(line.rstrip())
            if mod in module_stats:
                s = module_stats[mod]
                parts = [f'<!-- {s["total"]} cases']
                if s['vip']:
                    parts.append(f'{s["vip"]} VIP-only')
                if s['state']:
                    parts.append(f'state: {", ".join(s["state"])}')
                parts.append('-->')
                output_lines.append(' '.join(parts))
        else:
            output_lines.append(line.rstrip())
    
    with open(filepath, 'w') as f:
        f.write('\n'.join(output_lines) + '\n')
```

#### 步骤 6-8：同原规范（01_用例分析.md、02_测试执行计划.md）

### 阶段一：环境准备

0. **检测 hdc API**：`hdc_api = detect_hdc_api()` — 必须首先执行，确定命令名和数据格式
1. **确认 hdc 连接**：`hdc list targets` — 确认设备已连接
2. **确认应用已安装**：`hdc shell bm dump -a | grep <bundleName>` — 检查应用是否已安装
3. **确认应用运行**：
   ```python
   # dump UI 树检查应用是否在前台（使用检测到的 dump 命令）
   dump_cmd = hdc_api['dump_cmd']
   remote = '/data/local/tmp/_check.xml'
   subprocess.run(['hdc', 'shell', 'uitest', dump_cmd, '-p', remote], check=True)
   subprocess.run(['hdc', 'file', 'recv', remote, f'{test_dir}/dump/00_check_app.xml'], check=True)
   nodes = parse_ui_tree(f'{test_dir}/dump/00_check_app.xml')
   ```
4. **如果不在前台**：用 `hdc_start_app()` 启动应用
5. **确认初始页面**：验证当前页面是否为预期的起始页面（通常是首页/闪屏页）
6. **截图记录初始状态**：`hdc_screenshot(f'{test_dir}/screenshot/00_initial_state.png', hdc_api)`

### 阶段二：逐行执行测试

对每个 execute/state_dependent 用例：

```
循环: case = 当前用例
  1. 读取操作步骤和预期结果
  2. 检查是否已有结果 → 有则跳过
  3. dump UI 树 → 确认当前页面状态
  4. 解析操作步骤，拆分为原子操作序列
  5. 逐步执行操作：
     a. 点击 → hdc_click(x, y) 或 hdc_click_node(node)
     b. 输入 → hdc_click_node(field) + hdc_input_text("...")
     c. 滑动 → hdc_swipe(x1, y1, x2, y2)
     d. 返回 → hdc_press_back()
  6. 操作完成后 dump UI 树
  7. 对比 UI 树与预期结果
  8. 截图（必须）
  9. 判定结果（通过/BUG/阻塞）
  10. 立即写回源文件，记录时间
  11. 更新 02_测试执行计划.md 中对应 checkbox
```

**Excel 写回**（F/G/H 列 + 截图嵌入，同原规范）：

```python
# 检查是否已有结果
if ws.cell(row, 6).value:
    pass  # 跳过，不覆盖

ws.cell(row, 6, result)
ws.cell(row, 6).font = get_result_font(result)
ws.cell(row, 8, time_str)
embed_screenshot(ws, row, screenshot_path)
wb.save('TestCase.xlsx')
```

**Markdown 写回**（更新 checkbox + 追加结果到行尾）：

```python
def write_md_result(filepath, case, result, time_str, screenshot_path):
    """更新 Markdown 文件中指定行的测试结果。
    
    将 - [ ] 改为 - [x]，行尾追加结果标记和截图链接。
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    ln = case['line_number'] - 1  # 0-indexed
    old_line = lines[ln]
    
    # 构建结果标记
    if result.startswith('通过'):
        emoji = '✅'
    elif result.startswith('BUG'):
        emoji = '❌'
    elif result.startswith('阻塞'):
        emoji = '🚫'
    elif result.startswith('跳过'):
        emoji = '⏭️'
    else:
        emoji = '📌'
    
    # 截图链接（相对于项目根目录）
    img_rel = f'ai_auto_test/{os.path.basename(os.path.dirname(os.path.dirname(screenshot_path)))}/screenshot/{os.path.basename(screenshot_path)}'
    img_md = f'[截图]({img_rel})' if os.path.exists(screenshot_path) else ''
    
    # 替换 checkbox 并追加结果
    new_line = old_line.replace('- [ ]', '- [x]', 1).rstrip()
    new_line += f' {emoji} {result} ({time_str}) {img_md}\n'
    
    lines[ln] = new_line
    
    with open(filepath, 'w') as f:
        f.writelines(lines)
```

**Markdown 批量阻塞标记**（状态依赖链失败时使用）：

```python
def write_md_blocked_batch(filepath, blocked_cases, reason, time_str):
    """批量标记阻塞用例。"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for case in blocked_cases:
        ln = case['line_number'] - 1
        old_line = lines[ln]
        new_line = old_line.replace('- [ ]', '- [x]', 1).rstrip()
        new_line += f' 🚫 阻塞: {reason} ({time_str})\n'
        lines[ln] = new_line
    
    with open(filepath, 'w') as f:
        f.writelines(lines)
```

**注意**：`get_pil_resample()` 已处理 Pillow 版本兼容性（LANCZOS → ANTIALIAS → BILINEAR 三级回退），无需手动替换。

### 阶段三：截图处理（Excel / Markdown）

**Excel 格式**：截图必须嵌入为图片对象（同原规范）。

> **核心规则：G 列只能包含嵌入的图片对象，绝不能是文件路径文本。**
> 用户打开 Excel 时必须直接看到截图缩略图，而不是一串路径字符串。

每个测试步骤完成后，**必须**将截图作为图片嵌入对应行的 G 列。

**Markdown 格式**：截图通过 Markdown 图片链接 `[截图](相对路径)` 嵌入到行尾结果中（由 `write_md_result()` 自动处理）。

---
### Excel 截图嵌入

**正确做法** — 用 `ws.add_image()` 嵌入图片：
```python
from openpyxl.drawing.image import Image as XlImage
from PIL import Image as PILImage
import os

def get_pil_resample():
    """PIL 兼容性：优先 LANCZOS，回退 ANTIALIAS/BILINEAR"""
    for attr in ['LANCZOS', 'ANTIALIAS', 'BILINEAR']:
        if hasattr(PILImage, attr):
            return getattr(PILImage, attr)
    return 0  # NEAREST as last resort

def embed_screenshot(ws, row, screenshot_path, thumb_width=150):
    """将截图缩放后作为图片对象嵌入 Excel G 列，并调整行高"""
    if not os.path.exists(screenshot_path):
        return

    try:
        img = PILImage.open(screenshot_path)
        ratio = thumb_width / img.width
        new_size = (thumb_width, int(img.height * ratio))
        resample = get_pil_resample()
        img_resized = img.resize(new_size, resample)

        thumb_path = screenshot_path.replace('.png', '_thumb.png')
        img_resized.save(thumb_path)

        xl_img = XlImage(thumb_path)
        ws.add_image(xl_img, f'G{row}')
        ws.row_dimensions[row].height = new_size[1] * 0.75
    except Exception as e:
        print(f'  [WARN] Failed to embed screenshot: {e}')
```

**错误做法（禁止）**：
```python
# ❌ 绝对不要这样做！这只会在单元格里显示一串文字路径
ws.cell(row, 7, screenshot_path)
ws.cell(row, 7, '{test_dir}/screenshot/row15_xxx.png')
```

**执行顺序（必须先截图再写回）**：
1. 执行 UI 操作并验证结果
2. 调用 `hdc screenshot` 保存截图文件到本地
3. 调用写回函数（Excel: `embed_screenshot()` + 写 F/H 列；Markdown: `write_md_result()`）
4. 保存（Excel: `wb.save()`；Markdown: 自动保存）

**关键：步骤 2 必须在步骤 3 之前完成**，确保截图文件已存在。

**截图文件名规范**：
- Excel：`{test_dir}/screenshot/row{行号}_{操作描述}.png`
- Markdown：`{test_dir}/screenshot/case{序号}_{操作描述}.png`

**设置 G 列宽度**（在阶段零执行一次）：
```python
ws.column_dimensions['G'].width = 22
```

**批量写入场景的处理**：当需要批量标记多行结果（如阻塞链）时，如果多行共用同一张截图，每行都要嵌入该截图的图片对象：
```python
for row in blocked_rows:
    ws.cell(row, 6, '阻塞: 大纲生成失败')
    ws.cell(row, 6).font = FONT_BLOCKED
    ws.cell(row, 8, time_str)
    embed_screenshot(ws, row, shared_screenshot_path)  # 每行都嵌入
wb.save('TestCase.xlsx')
```

### 阶段四：持续保存

测试过程中定期保存 Excel，避免数据丢失：
- 每完成一个模块（一组相关用例）后保存一次
- 遇到异常或阻塞时立即保存
- 保存前不需要关闭文件，openpyxl 的 `wb.save()` 是覆盖写入

### 阶段五：生成测试报告

全部用例执行完成后，生成 `03_测试报告.md`。

**报告必须包含时间统计**：

```python
from datetime import datetime

test_end_time = datetime.now()
duration = test_end_time - test_start_time

hours, remainder = divmod(int(duration.total_seconds()), 3600)
minutes, seconds = divmod(remainder, 60)
duration_str = f'{hours}小时{minutes}分钟' if hours > 0 else f'{minutes}分钟'
```

**报告模板**：

```markdown
# {应用名} 自动化UI测试报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 应用名称 | {app_name} |
| 平台 | HarmonyOS (ArkTS) |
| 测试设备 | {device_name} |
| 测试账号 | {account_type}账号 |
| 测试日期 | {date} |
| 测试开始时间 | {start_time} |
| 测试结束时间 | {end_time} |
| 总耗时 | {duration_str} |
| 测试工具 | hdc (HarmonyOS Device Connector) |
| 测试用例文件 | TestCase.xlsx |

## 测试结果总览

| 状态 | 数量 | 占比 |
|------|------|------|
| PASS (通过) | {pass_count} | {pass_pct}% |
| BUG (缺陷) | {bug_count} | {bug_pct}% |
| Blocked (阻塞) | {blocked_count} | {blocked_pct}% |
| Skip (跳过) | {skip_count} | {skip_pct}% |
| **总计** | **{total}** | **100%** |

通过率(PASS/可执行): {pass_count}/{executable} = **{pass_rate}%**

## 关键BUG清单

### P0 - 严重缺陷
{p0_bugs}

### P1 - 重要缺陷
{p1_bugs}

### P2 - 一般缺陷
{p2_bugs}

## Blocked项说明
{blocked_details}

## 建议
{recommendations}
```

---

## 关键技巧

### 1. 坐标计算

从 UI 树节点 bounds 属性计算点击坐标：
```
bounds="[52,2501][1204,2676]"
→ center_x = (52 + 1204) / 2 = 628
→ center_y = (2501 + 2676) / 2 = 2589
```

### 2. 系统弹窗处理

权限弹窗、确认弹窗等系统级对话框：
- 先 dump UI 树确认弹窗内容
- 查找"允许"/"确认"/"取消"按钮的坐标
- 点击对应按钮
- 再次 dump 确认弹窗已消失

### 3. 滚动查找元素

当目标元素不在当前可视区域时：
1. dump UI 树确认元素不存在
2. 执行 hdc_swipe 滑动（向上或向下滑半个屏幕）
3. 等待 1 秒
4. 再次 dump UI 树查找目标元素
5. 重复直到找到或达到滚动边界（连续两次 dump 内容相同）

### 4. 等待异步操作

网络请求、动画、页面切换等异步操作：
- 操作后等待 2-3 秒再 dump UI 树
- 如果页面仍在加载（有 loading 指示器），继续等待
- 最多等待 30 秒，超时则标记为阻塞

### 5. 状态恢复

测试完一个模块后，需要回到初始状态再测下一个模块：
- 多次按 Back 键回到首页
- 或者用 `hdc_start_app()` 重启应用
- dump UI 树确认回到预期页面

### 6. 文本验证技巧

UI 树中的 `text` 属性用于验证显示内容：
- 精确匹配：`node['text'] == expected`
- 包含匹配：`expected in node['text']`（用于动态内容如时间、数量）
- 存在性检查：确认某个文本节点存在即可（不关心具体值）

---

## 常见问题

### Q0: hdc 版本差异导致命令不存在？
```bash
# hdc 3.x 和 2.x 子命令不同，Skill 通过 detect_hdc_api() 自动检测：
# 3.x: uitest dumpLayout (JSON 输出), uitest screenCap (PNG)
# 2.x: uitest dump (XML 输出), snapshot_display (JPEG)

# 手动检查可用命令：
hdc shell uitest help
```

### Q1: hdc 连接不上设备？
```bash
# 检查 hdc 版本
hdc version

# 列出已连接设备
hdc list targets

# 如果是模拟器，重启 hdc 服务
hdc kill
hdc start
```

### Q2: UI 树 dump 返回空或格式不对？
- **命令不存在**：hdc 3.x 用 `dumpLayout`，不是 `dump`。运行 `hdc shell uitest help` 确认可用命令。
- **JSON 格式**：`dumpLayout` 输出 JSON（不是 XML），`parse_ui_tree()` 已自动处理。
- **空文件**：先截图确认应用状态。可能原因：应用崩溃、页面正在切换、弹窗遮挡。等待 2 秒后重新 dump。

### Q3: 点击坐标无响应？
确认：(1) 元素 `clickable="true"`；(2) 元素 `enabled="true"`；(3) 坐标计算正确（使用中心点）；(4) 没有其他元素遮挡。

### Q4: 截图是黑屏？
设备可能未完全渲染。等待 1-2 秒后重新截图。如果持续黑屏，检查设备状态。

### Q5: Excel 保存报错 "file is locked"？
确保 Excel 文件未在其他程序（如 WPS、Excel）中打开。关闭后重试。

### Q6: 如何处理需要登录的场景？
应用应已处于登录状态。如果 token 过期，需要用户手动重新登录后再继续测试。

### Q7: 模拟器上无法测试的功能？
微信/QQ 分享、相机、NFC 等硬件相关功能在模拟器上无法测试。标记为 `跳过(模拟器不支持)` 或 `N/A: 需真机测试`。

### Q8: 如何处理动态内容（时间戳、随机ID）？
使用包含匹配而非精确匹配。验证关键文本存在即可，忽略动态部分。

### Q9: 测试中途应用崩溃怎么办？
1. 截图记录崩溃状态
2. 当前用例标记为 `BUG: 应用崩溃`
3. 用 `hdc_start_app()` 重启应用
4. 继续后续用例

### Q10: 如何处理多步骤用例？
C 列可能包含多个步骤（用序号或换行分隔）。拆分为原子操作，逐步执行，每步之间 dump UI 树确认状态。

### Q11: 行高/列宽不合适？
```python
ws.column_dimensions['F'].width = 35  # 测试结果列
ws.column_dimensions['G'].width = 22  # 截图列
ws.column_dimensions['H'].width = 18  # 测试时间列
```

### Q12: 如何断点续测？
读取 F 列，找到第一个空值的行号（且该行属于本次测试范围），从该行继续执行。已有结果的行跳过。

### Q13: 测试报告中的通过率如何计算？
通过率 = PASS数 / (总数 - Blocked数 - Skip数 - N/A数)。被阻塞和跳过的用例不计入分母。

### Q14: 如何处理相同操作不同预期的用例？
有些用例操作步骤相同但预期结果因账户类型不同而不同。根据当前账户类型选择对应的预期结果进行验证。

### Q15: 如何获取应用的 bundleName？
```bash
# 从代码仓获取
grep -r "bundleName" src/main/module.json5 | head -1

# 从已安装应用获取
hdc shell bm dump -a | grep -A5 <部分包名>
```

---

## hdc 踩坑记录

| 问题 | 现象 | 解决 |
|------|------|------|
| **hdc 3.x dumpLayout 输出 JSON** | `uitest dump` 不存在，`dumpLayout` 输出的是 JSON 而非 XML | 使用 `parse_ui_tree()` 自动检测 JSON/XML 格式 |
| **snapshot_display 只接受 .jpeg** | hdc 3.x 的 `snapshot_display` 后缀必须是 `.jpeg` | 优先使用 `uitest screenCap`（支持 PNG），或文件命名为 `.jpeg` |
| **坐标偏移** | 点击位置偏差，dumpLayout 的坐标与 uiInput click 坐标系有偏移 | 检查是否有状态栏/导航栏高度偏移，考虑加偏移量校准 |
| 中文文本输入乱码 | `hdc shell input text` 输入中文显示乱码 | 先设置输入法为英文，或使用剪贴板粘贴 |
| UI 树过大 | dump 超时 | 尝试截断页面或只 dump 可见区域 |
| swipe 无效 | 滑动无响应 | 检查目标区域是否可滚动（scrollable="true"），调整滑动距离 |
| 截图尺寸异常 | 截图比实际屏幕小 | 使用 `uitest screenCap` 替代 `snapshot_display` |

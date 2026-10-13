# harmonyos-ui-test Skill 验证报告

## 基本信息

| 项目 | 内容 |
|------|------|
| Skill 名称 | harmonyos-ui-test |
| Skill 路径 | `skills/others/defensive_architecture/harmonyos-ui-test/SKILL.md` |
| 来源仓库 | sdd-group2026/skill_bank |
| 验证日期 | 2026-05-20 (静态审查) + 2026-05-21 (真机实测) |
| 验证人 | IntelliJungle |
| Skill 长度 | ~1070 行 Markdown + Python 代码块 |

## 验证范围

对 SKILL.md 的以下维度进行了逐项审查：

- **正确性** — Python 代码逻辑、hdc 命令语法、Excel 操作 API
- **安全性** — 命令注入风险、文件操作安全
- **完整性** — 工作流覆盖、边界情况处理
- **可用性** — 文档清晰度、代码可执行性
- **鲁棒性** — 错误处理、并发场景、兼容性

---

## 1. 正确性审查

### 1.1 classify_case() 逻辑

| 测试用例 | 输入 (precondition, account_type) | 预期输出 | 判定 |
|----------|----------------------------------|----------|------|
| VIP 专属行 + VIP 账户 | `("是会员", "VIP")` | `execute` | [PASS] |
| VIP 专属行 + 非VIP 账户 | `("是会员", "非VIP")` | `skip` | [PASS] |
| 非VIP 行 + VIP 账户 | `("不是会员", "VIP")` | `skip` | [PASS] |
| 非VIP 行 + 非VIP 账户 | `("不是会员", "非VIP")` | `execute` | [PASS] |
| 空前置条件 + VIP | `("", "VIP")` | `execute` | [PASS] |
| 空前置条件 + 非VIP | `("", "非VIP")` | `skip` | [PASS] |
| 状态依赖（生成中） | `("生成中", "VIP")` | `state_dependent` | [PASS] |
| 未知前置条件 | `("其他条件", "VIP")` | `execute` (兜底) | [PASS] |

**判决：PASS** — 分类逻辑完备，有安全的兜底策略，边界条件覆盖完整。

### 1.2 parse_ui_tree() XML 解析

- 使用 Python 标准库 `xml.etree.ElementTree` — 零依赖，正确
- 坐标解析使用正则 `r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]'` — 正确
- 返回扁平化字典列表，包含 `center` 预计算 — 实用设计

**判决：PASS**

### 1.3 embed_screenshot() 截图嵌入

- 使用 PIL 缩放 + openpyxl `add_image()` — 正确
- 禁止路径文本写入 G 列 — 多处强调，设计正确
- 缩略图文件 (`_thumb.png`) 未清理 — 轻微问题，不影响功能

**判决：PASS**（PIL 兼容性见鲁棒性章节）

### 1.4 Excel 行样式着色

- `get_row_fill()` 按前置条件映射 7 种背景色 — 覆盖完整
- VIP 行 B 列加粗 + 行背景色双维度区分 — 设计合理
- `get_result_font()` 按结果类型映射字体色 — 覆盖完整

**判决：PASS**

---

## 2. 安全性审查

### 2.1 hdc_input_text() 命令注入 [FAIL]

**位置**：SKILL.md 第 278 行

```python
def hdc_input_text(text):
    escaped = text.replace('"', '\\"').replace('$', '\\$')
    subprocess.run(['hdc', 'shell', 'input', 'text', escaped], ...)
```

**问题**：`hdc shell input text` 将文本传递给设备端 shell 执行。当前的转义只覆盖了 `"` 和 `$`，但以下字符未被处理：

| 未转义字符 | 风险 |
|-----------|------|
| `` ` `` (backtick) | 命令替换：`` `rm -rf /` `` |
| `;` | 命令分隔：`hello; malicious_command` |
| `\|` | 管道 |
| `$(...)` | 命令替换（`$` 已被部分处理但 `$(cmd)` 未必被阻止） |
| `\n` | 换行注入 |

**风险等级**：中等。攻击者需要在测试文本中注入（测试用例来自 Excel，通常是可信来源），但仍应防御。

**修复建议**：
```python
import shlex
def hdc_input_text(text):
    escaped = shlex.quote(text)  # 更安全的转义
    subprocess.run(['hdc', 'shell', 'input', 'text', escaped], ...)
```
或使用 `subprocess` 的 list 形式配合 `input` 参数（如果 hdc 支持 stdin）。

**判决：FAIL** — 需要在生产使用前修复。

### 2.2 其他命令调用

- `hdc_click()` / `hdc_swipe()` — 参数为整数坐标，无注入风险 [PASS]
- `hdc_start_app()` — args 来自配置/代码，非用户输入 [PASS]
- `hdc_screenshot()` — 本地路径由代码控制 [PASS]

---

## 3. 完整性审查

### 3.1 覆盖的工作流阶段

| 阶段 | 覆盖率 | 说明 |
|------|--------|------|
| 阶段零：用例分析 | 完整 | Excel 读取、分类、着色、分析文档 |
| 阶段一：环境准备 | 完整 | hdc 连接、应用检查、启动 |
| 阶段二：逐行执行 | 完整 | 操作序列、验证、写入 |
| 阶段三：截图嵌入 | 完整 | PIL 缩放、openpyxl 嵌入 |
| 阶段四：持续保存 | 完整 | 模块级保存策略 |
| 阶段五：生成报告 | 完整 | 报告模板含时间统计 |

**判决：PASS** — 六阶段覆盖完整。

### 3.2 边界情况覆盖

| 边界情况 | 是否覆盖 | 说明 |
|----------|----------|------|
| 应用崩溃恢复 | 是 | Q9：截图→标记BUG→重启→继续 |
| 断点续测 | 是 | Q12：读取F列首个空值继续 |
| 模拟器限制 | 是 | Q7：微信/相机等标记为跳过 |
| 动态内容验证 | 是 | Q8：包含匹配替代精确匹配 |
| 多步骤用例 | 是 | Q10：拆分为原子操作 |
| Excel 文件锁定 | 是 | Q5：关闭外部程序 |
| UI 树过大/超时 | 是 | hdc 踩坑记录表 |
| 中文输入乱码 | 是 | hdc 踩坑记录表 |
| 坐标偏移 | 是 | hdc 踩坑记录表 |
| 系统弹窗处理 | 是 | 技巧 2 |
| 滚动查找元素 | 是 | 技巧 3 |
| 并发测试运行 | **否** | 硬编码的远程截图文件名会冲突 |
| 网络断开恢复 | **否** | 无自动重连逻辑 |
| Excel 编码问题 | **否** | 未提及 CSV/编码回退 |

**判决：PASS**（主要边界情况已覆盖。缺失项为边缘场景）

### 3.3 测试结果类型覆盖

| 结果类型 | F 列文案格式 | 字体色 |
|----------|-------------|--------|
| 通过 | `通过` / `通过(补充)` | 深绿加粗 |
| BUG | `BUG: <描述>` | 深红加粗 |
| 阻塞 | `阻塞: <原因>` | 橙色 |
| 跳过 | `跳过(<原因>)` | 灰色 |
| N/A | `N/A: <原因>` | 灰色 |
| 引用 | `引用: 同行XX` | 蓝色 |

**判决：PASS** — 六种结果类型覆盖全面。

---

## 4. 鲁棒性审查

### 4.1 PIL 兼容性 [NEEDS FIX]

```python
img.resize(new_size, PILImage.LANCZOS)
```

- Pillow >= 10.0.0：`LANCZOS` 存在，正常
- Pillow < 10.0.0：`LANCZOS` 不存在 → **AttributeError 崩溃**
- 文档中已有备注说明此问题，但代码未实现 fallback

**修复建议**：
```python
try:
    resample = PILImage.LANCZOS
except AttributeError:
    try:
        resample = PILImage.ANTIALIAS
    except AttributeError:
        resample = PILImage.BILINEAR
img_resized = img.resize(new_size, resample)
```

**判决：NEEDS FIX**

### 4.2 硬编码常量

| 常量 | 位置 | 影响 |
|------|------|------|
| `MAX_ATTEMPTS = 3` | retry_action | 固定重试次数，不同场景可能需要不同值 |
| `RETRY_DELAY = 10` | retry_action | 固定延迟，LAN 和 4G 差异大 |
| `thumb_width = 150` | embed_screenshot | 缩略图尺寸固定 |
| `/data/local/tmp/_test_screenshot.png` | hdc_screenshot | 并发冲突（已记录为 eval-09） |

**判决：PASS**（合理的默认值。建议后续版本支持配置覆盖）

### 4.3 状态转换等待

状态依赖用例的执行策略中，循环 dump UI 树等待状态变化。缺少：
- 最大等待超时（如等待 120 秒后超时）
- 超时后的处理策略（标记为阻塞？还是重试？）

**判决：NEEDS ATTENTION** — 建议添加超时参数。

---

## 5. 可用性审查

### 5.1 文档质量

| 维度 | 评分 | 说明 |
|------|------|------|
| 结构清晰度 | ★★★★★ | Markdown 层级分明，六阶段用 ### 区分 |
| 代码示例完整性 | ★★★★★ | 每个函数都有完整实现 + import 语句 |
| 常见问题覆盖 | ★★★★★ | 15 个 FAQ 覆盖主要痛点 |
| 踩坑记录 | ★★★★★ | hdc 踩坑表非常实用 |
| 参数说明 | ★★★★☆ | 详细但入口略显复杂 |

**判决：PASS** — 文档质量高，可作为同类 skill 的参考模板。

### 5.2 依赖项

| 依赖 | 版本 | 安装方式 |
|------|------|----------|
| hdc | HarmonyOS SDK 自带 | PATH 配置 |
| hvigorw | HarmonyOS SDK 自带 | PATH 配置 |
| openpyxl | ≥ 3.0 | `pip3 install openpyxl` |
| Pillow | ≥ 9.0（推荐 ≥ 10.0） | `pip3 install Pillow` |

**判决：PASS** — 依赖项精简且明确。

---

## 6. 判决

| 维度 | 结果 |
|------|------|
| 正确性 | [PASS] — 核心逻辑正确，分类函数、XML 解析、Excel 操作均无误 |
| 安全性 | [FAIL] — `hdc_input_text()` 存在命令注入风险，需修复 shell 转义 |
| 完整性 | [PASS] — 六阶段覆盖完整，15 个 FAQ + 踩坑记录 |
| 鲁棒性 | [NEEDS FIX] — PIL 兼容性 fallback 缺失 |
| 可用性 | [PASS] — 文档结构清晰，代码可直接执行 |

**总体判决：[CONDITIONAL PASS]**

该 skill 设计质量高，工作流完整，文档优秀。在修复以下 2 个问题后可以安全使用：

1. **[P0] 安全修复** — `hdc_input_text()` 的 shell 转义增强（使用 `shlex.quote()`）✅ 已修复
2. **[P1] 兼容性修复** — `embed_screenshot()` 添加 PIL resample 方法 fallback ✅ 已修复

## 7. 真机实测（2026-05-21）

### 测试环境

| 项目 | 内容 |
|------|------|
| hdc 版本 | 3.2.0c |
| 设备 | 模拟器 (127.0.0.1:5555) |
| 测试应用 | OpenCalculator (com.darkempire78.opencalculator) |
| 屏幕分辨率 | 1256 × 2760 |

### 实测结果

| 阶段 | 测试项 | 结果 | 关键发现 |
|------|--------|------|----------|
| 阶段零 | Markdown parse + classify (25 cases) | ✅ PASS | 14 execute / 4 skip / 7 state_dependent，分类准确 |
| 阶段零 | Excel parse (25 cases) | ✅ PASS | 与 Markdown 完全对应 |
| 阶段一 | hdc 连接 | ✅ PASS | `hdc list targets` 正常 |
| 阶段一 | UI dump | ⚠️ **hdc 3.x 用 `dumpLayout` 输出 JSON** | SKILL.md 原假设 XML 格式有误，已修复 |
| 阶段一 | 截图 | ⚠️ **`snapshot_display` 需 `.jpeg` 后缀** | 改用 `uitest screenCap`（支持 PNG），已修复 |
| 阶段二 | Markdown writeback | ✅ PASS | `- [ ]` → `- [x]` + emoji + result + timestamp |
| 阶段二 | Batch blocking | ✅ PASS | 4 个 `生成完成` 用例被正确批量标记为阻塞 |
| 阶段二 | UI 树解析 | ✅ PASS | JSON 格式解析正常，73 nodes / 25 clickable |
| 阶段二 | 点击操作 | ⚠️ 坐标偏移 | dumpLayout 坐标与 uiInput click 坐标系可能不一致 |

### 修复记录

| 问题 | 严重度 | 修复 |
|------|--------|------|
| hdc 3.x `dumpLayout` 输出 JSON 而非 XML | P0 | 新增 `detect_hdc_api()` + `_parse_json_tree()` |
| `snapshot_display` 需要 .jpeg 后缀 | P1 | 优先使用 `uitest screenCap`，添加 hdc API 检测 |
| 坐标偏移 | P2 | 踩坑记录已更新，建议后续版本添加校准逻辑 |
| `hdc_input_text` shell 注入 | P0 | 改用 `shlex.quote()` ✅ |
| PIL LANCZOS 兼容性 | P1 | 添加三级 fallback `get_pil_resample()` ✅ |

## 8. Evals

详细评估用例见 `evals.json`（18 个 eval case：15 pass / 1 fail / 2 needs_attention，含 4 个真机实测 case）。

# 需求提案 — Issue #17 粘贴即计算

## 1. 原始需求

> 支持从剪贴板粘贴数学表达式，粘贴后自动计算 | 粘贴计算 | ⭐ | 零操作体验

**Issue 来源**：Issue #17
**类型**：新增功能（Design/Development - New Requirement）
**变更名称**：paste-and-calculate

## 2. 需求理解

### 2.1 意图分类
- **类型**：新增功能
- **一句话概括**：用户从其他 App 复制数学表达式后，回到本应用时自动检测到剪贴板新内容、填入表达式输入框、并立即触发等号计算，整个流程用户无需任何额外点击。

### 2.2 领域映射
- **UI/交互**：在 CalculatorPage 新增「粘贴」工具栏按钮（与「科学/基础」切换同一行），同时页面挂载/恢复时自动尝试读取剪贴板
- **状态管理**：新增 `@State lastPastedHash: number = 0` 用于去重
- **计算引擎**：复用现有 `computePreview` + `onEquals`（不新增任何计算逻辑）
- **剪贴板服务**：使用 `@kit.BasicServicesKit` 的 `pasteboard.getSystemPasteboard().getData()`

### 2.3 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | extend | ToggleRow 新增「📋粘贴」按钮；DisplayPanel 可选挂 TapGesture 触发粘贴 |
| ViewModel | extend | CalculatorPage 新增 onPaste() / onPageShow() / computeHash() 方法；新增 @State lastPastedHash |
| Model | 无 | 不需新增模型，复用 Expression + CalcEngine + NumberFormatter |
| 数据层 | 无 | 无持久化需求（lastPastedHash 是会话内状态） |
| 基础设施 | 无 | 复用已导入的 `pasteboard` + `promptAction` |

### 2.4 关键实体
- **数据实体**：无新增
- **页面实体**：
  - CalculatorPage.ToggleRow（竖屏工具栏）
  - CalculatorPage.DisplayPanel（显示屏，可选 TapGesture 挂载点）
- **接口实体**：
  - `pasteboard.getSystemPasteboard().getData()`（已存在 API，本次新增调用方）
  - `CalcEngine.evaluate(clean, radians)`（复用）
  - `Expression.getCleanExpression(str, '.', ',')`（复用）
  - `NumberFormatter.format(raw, '.', ',', INTERNATIONAL)`（复用）
- **事件实体**：
  - `onPageShow` 触发 → 读剪贴板 → 校验 → 计算
  - 用户点击「📋粘贴」按钮 → onPaste() → 读剪贴板 → 校验 → 计算
  - expression 变化 → @Watch('onExpressionChange') → preview 重算（自动）
  - onEquals 完成 → push HistoryItem（自动）

### 2.5 模糊点（已在 todo.md 自动拍板）
- **触发机制**（blocker → 决定）：**双触发**（onPageShow 自动 + 工具栏按钮显式）
- **表达式识别**（important → 决定）：**仅支持纯数学**（不包 NL 单位换算）
- **历史记录**（important → 决定）：**粘贴计算结果进历史**
- **重复粘贴**（important → 决定）：**静默去重**（hash 比对）
- **错误处理**（important → 决定）：**Toast 静默提示**「非数学表达式」
- **空白字符**（nice-to-have → 决定）：**trim 后投递**
- **重复 expression**（nice-to-have → 决定）：**不替换未变化**表达式

### 2.6 复杂度评估
- **等级**：S（简单）
- **理由**：
  - 复用 `onEquals` + `computePreview` + `Expression.getCleanExpression` 三件套，**零新增计算逻辑**
  - 复用 `pasteboard` + `promptAction` 已导入的 Kit，**零新增依赖**
  - 复用 `@Watch` 自动联动机制，**零新增状态机**
  - 单页面 UI 增强 + 1 个 @State 字段 + 1 个工具栏按钮 + 2 个回调方法，约 60 行代码改动
- **影响模块数**：1（CalculatorPage.ets）
- **架构变更**：否
- **数据模型变更**：否

## 3. 验收标准

### 3.1 功能验收（必过）
- **AC-1** 复制 `2+3` 后回到应用 → expression 自动填入 `2+3` → result 自动显示 `5`
- **AC-2** 复制 `10*20%` 后回到应用 → expression 自动填入 `10*20%` → result 自动显示 `2`（百分号语义同手动输入）
- **AC-3** 复制 `sin(45)` 后回到应用 → expression 自动填入 → result 自动显示 `0.7071...`（按当前 radianMode）
- **AC-4** 复制 `  3.14*2  `（含前后空白）→ 粘贴后 expression 为 `3.14*2` → result `6.28`
- **AC-5** 复制非数学 `Hello World` → Toast 提示「非数学表达式」→ expression 不变
- **AC-6** 连续触发 onPageShow 两次（hash 相同）→ 第二次不重复计算 / 不重复 push 历史
- **AC-7** 用户在 expression 已有值时粘贴新内容 → 旧 expression 被覆盖 → 新 result 计算
- **AC-8** 用户在 expression 已有值时粘贴完全相同内容 → 静默忽略（不覆盖 / 不重算）

### 3.2 UI 验收
- **UI-1** ToggleRow 在「科学/基础」按钮与「▼历史」之间出现「📋粘贴」按钮（12pt 字号 + T2 灰色 + 8px padding）
- **UI-2** 横屏布局：工具栏被裁切，按钮放在 DisplayPanel 右上角折叠菜单内（**暂不实现**）
- **UI-3** 粘贴成功后无 Toast 噪音（仅无效时 Toast）

### 3.3 可靠性验收（FMEA 消减措施）
- **FMEA-1** 剪贴板无文本内容 → 不触发，return early
- **FMEA-2** 剪贴板内容超长（>200 字符）→ 截断到 200 字符后校验
- **FMEA-3** 剪贴板内容校验通过但 evaluate 抛异常 → catch 块设置 errorMsg，expression 仍保留
- **FMEA-4** 重复粘贴 hash 一致 → 静默 return（避免历史污染 + 计算浪费）
- **FMEA-5** getData 系统 API 抛异常 → try/catch 静默吞（不崩溃）
- **FMEA-6** 粘贴空字符串 / 纯空白 → return early

## 4. 风险与依赖

| 风险 | 等级 | 缓解 |
|------|------|------|
| HarmonyOS 模拟器剪贴板互通性 | 中 | 单元测试用 mock pasteboard 验证逻辑；UI 自动化用 `hdc shell input text` 模拟 |
| onPageShow 触发时机不稳定 | 低 | 配合工具栏按钮双保险 |
| `pasteboard.getData` 在某些设备需权限 | 低 | 文档已说明为 public API，无额外权限申请 |
| 表达式识别误判（"123" 既可是数字也可是表达式） | 低 | 接受 "123" 直接当数学表达式处理（求值仍合法） |

## 5. 不在范围

- ❌ 撤销粘贴（Cmd+Z 等价）
- ❌ 批量粘贴多条历史
- ❌ 富文本/HTML 剪贴板内容
- ❌ 跨设备剪贴板同步
- ❌ 粘贴时携带源应用名称
- ❌ 单位换算（Issue #14 范围）
- ❌ 复杂语法高亮

## 6. 后续可优化

- 长按结果区唤起「复制 / 粘贴 / 清空」三选一 ActionSheet
- 识别剪贴板内容为"上次计算结果"时直接累加
- 监听系统级剪贴板变化

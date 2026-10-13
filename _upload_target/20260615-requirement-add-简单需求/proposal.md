# 程序员模式 需求提案 — Issue #12

## 1. 原始需求

> 支持二进制、八进制、十六进制转换，加一个程序员模式切换 | 程序员模式 | ⭐⭐ | 模式切换动画+进制转换

**Issue 来源**：Issue #12
**类型**：新增功能（Design/Development - New Requirement）
**变更名称**：简单需求（programmer-mode）
**关联特性**：feat-programmer-mode

## 2. 需求理解

### 2.1 意图分类
- **类型**：新增功能
- **一句话概括**：在计算器中新增"程序员模式"，允许在 DEC/BIN/OCT/HEX 之间切换实时查看当前结果的多种进制表示，并支持模式切换时的过渡动画。

### 2.2 领域映射
- **UI/交互**：CalculatorPage 新增模式切换器（基础/科学/程序员 三选一），程序员模式下按钮键盘切换为 0/1 + HEX 字母，结果区下方增加多进制实时显示条。
- **状态管理**：当前显示进制（activeBase）、当前模式（mode = basic/scientific/programmer），均需响应式联动。
- **数据管理**：用户偏好（默认模式、上次使用的进制）持久化到 PreferencesStore。

### 2.3 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | extend | CalculatorPage 新增 mode 状态、activeBase 状态、BaseConverterView @Builder、模式切换 Row |
| ViewModel | extend | 新增 mode 切换函数、activeBase 切换函数、convertToBase 函数；联动 preview/result/多进制显示 |
| Model | extend | Models.ets 新增 CalculatorMode 枚举、NumberBase 枚举；PreferencesStore 扩展 mode/activeBase 读写 |
| 数据层 | extend | PreferencesStore 新增 getMode()/setMode()/getActiveBase()/setActiveBase() |
| 基础设施 | 无 | 无新依赖 |

### 2.4 关键实体
- **数据实体**：`CalculatorMode` 枚举（BASIC/SCIENTIFIC/PROGRAMMER），`NumberBase` 枚举（DEC/BIN/OCT/HEX），`BaseConversions` 接口
- **页面实体**：`CalculatorPage.ModeToggleRow`（基础/科学/程序员三选切换），`CalculatorPage.BaseConverterPanel`（多进制显示行），`CalculatorPage.ProgrammerKeypad`（0/1/HEX字母 键盘）
- **接口实体**：`BaseConverter.convert(value: number, base: NumberBase): string`，`NumberFormatter` 扩展支持大整数无千分位
- **事件实体**：`onModeChange(mode)`、`onActiveBaseChange(base)`、`onProgrammerDigit(d)`、`onProgrammerOp(op)`

### 2.5 模糊点（已在 step3 自动决定 — 方案C）
| # | 类别 | 描述 | 严重程度 | 自动决定（方案C） |
|---|------|------|---------|------------------|
| 1 | 行为模糊 | 程序员模式输入策略 | blocker | **DEC 主输入**：用户始终输入十进制，切换 activeBase 仅影响"主结果显示"进制；另以 4 行实时显示 BIN/OCT/HEX |
| 2 | 行为模糊 | 与科学模式关系 | blocker | **互斥三选一**：基础 / 科学 / 程序员三者单选，使用顶部 SegmentedControl |
| 3 | 交互模糊 | 模式切换动画类型 | important | **fade + slide**：新模式 fade-in 200ms，从右侧 slide-in 8px |
| 4 | 行为模糊 | BIN/OCT/HEX 是否支持小数 | important | **截断为整数**：BIN/OCT/HEX 只显示整数部分（toString(0)），DEC 显示完整浮点 |
| 5 | 行为模糊 | 负数表示 | important | **- 前缀**：BIN/OCT/HEX 用 `-` 前缀表示负数（不采用补码） |
| 6 | 行为模糊 | 位宽限制 | important | **不限制**：按需显示结果位数（JS number 安全整数范围内 15-16 位） |
| 7 | 行为模糊 | 程序员模式按键布局 | important | **简化版**：A-F HEX 字母 + 0/1 BIN 按钮 + DEC 数字键，运算符保留 + - × ÷ |
| 8 | 数据模糊 | 偏好持久化 | nice-to-have | **持久化**：模式与上次 activeBase 保存到 PreferencesStore |
| 9 | 范围模糊 | 输入 BIN 数字？ | important | **不支持**：程序员模式只接受 DEC 输入，BIN 仅作为显示进制 |

### 2.6 复杂度评估
- **等级**：M（中等）
- **理由**：跨 View/ViewModel/Model/数据层 4 层；新增 2 个枚举、1 个转换工具类、1 个视图组件、1 组键盘切换；UI 改动较大（顶部模式切换 + 多进制显示行 + 键盘切换）；约 200-300 行新增代码 + 单元测试
- **影响模块数**：3（CalculatorPage.ets, Models.ets, PreferencesStore.ets），新增 1 个（BaseConverter.ets）
- **架构变更**：否（沿用现有 MVVM 分层）
- **数据模型变更**：是（扩展 CalculatorPreferences 增加 mode / activeBase 字段）

## 3. 需求澄清

> **方案 C（自动答）**：用户已授权对模糊点做合理默认决定，以下记录所有决定及理由。

### 3.1 已澄清的关键决策

| # | 问题 | 决策 | 来源 |
|---|------|------|------|
| 1 | 输入进制 vs 显示进制 | DEC 主输入 + BIN/OCT/HEX 多行实时显示 | 用户未指定，参考 iOS Calculator / Android OpenCalc 程序员模式 |
| 2 | 与科学模式关系 | 互斥三选一切换（SegmentedControl） | 与现有 ToggleRow 二选一不一致，统一为 SegmentedControl 提升 UX |
| 3 | 模式切换动画 | fade-in 200ms + slide-from-right 8px | ArkUI 内置 transition API，无第三方依赖 |
| 4 | BIN/OCT/HEX 小数处理 | 截断为整数 | IEEE 754 整数部分；浮点部分用户可见 DEC 主结果 |
| 5 | 负数表示 | `-` 前缀 | 实现简单、用户友好；专业用户可后续升级为补码 |
| 6 | 位宽限制 | 不限制（JS number 安全整数） | HarmonyOS ArkTS Number 与 IEEE 754 double 一致 |
| 7 | 程序员键盘 | 0/1 BIN 按钮 + A-F HEX 字母 + 数字 + 运算符 | 简化版，覆盖 80% 使用场景 |
| 8 | 偏好持久化 | mode + activeBase 写入 PreferencesStore | 与现有模式开关一致 |
| 9 | 输入 BIN 数字 | 不支持 | DEC 主输入已覆盖所有计算场景；专业级后续扩展 |

### 3.2 待定假设
- 假设 1：DEC 显示完整结果（包括小数），BIN/OCT/HEX 显示整数部分（截断）；这是大多数计算器的标准做法。
- 假设 2：模式切换后，当前表达式保留（不重置）；用户可在 DEC 模式计算表达式再切到程序员查看多种进制。
- 假设 3：BIN/OCT/HEX 切换只影响"主结果"显示进制（同时也同步刷新多进制显示行）。
- 假设 4：AC 操作清空 expression 和所有结果，但保持当前 mode 和 activeBase。

### 3.3 功能边界
**包含**：
- 顶部 SegmentedControl 三选一切换（基础/科学/程序员）
- 程序员模式下的键盘布局（BIN 0/1 + HEX A-F + 数字 2-9 + 运算符 + - × ÷）
- 主结果下方 4 行 BIN/OCT/HEX/DEC 多进制实时显示
- 主结果"主进制"切换按钮（程序员模式下，DEC/BIN/OCT/HEX 四选一）
- 模式切换动画（fade + slide）
- mode 与 activeBase 偏好持久化
- 单元测试覆盖 BaseConverter 全部转换场景

**不包含**：
- 任意进制间直接输入（如直接键入 "FF" 表示 HEX 255）
- 位运算（AND/OR/XOR/NOT/SHL/SHR）
- 补码显示
- 大数（> 2^53）支持
- 自定义进制（base-36 之外的任意 base）

## 4. 需求详述

### 4.1 功能需求

#### FR-1: 模式切换
**描述**：顶部 SegmentedControl 切换 BASIC / SCIENTIFIC / PROGRAMMER 模式
**验收条件**：
- 三选一，点击立即切换
- 切换时键盘区域 fade + slide 动画
- 切换后 mode 写入偏好
- 默认 mode = BASIC

#### FR-2: 程序员键盘
**描述**：PROGRAMMER 模式下，键盘切换为 BIN 0/1 + HEX A-F + 数字 2-9 + 运算符
**验收条件**：
- BIN 0/1 按钮各占 1 个槽位
- HEX A-F 字母按钮 6 个
- 数字 2-9 按钮 8 个
- 运算符 + - × ÷ 保留
- AC/退格/等号 保留
- 科学函数 sin/cos/tan/ln/log 隐藏

#### FR-3: 多进制显示
**描述**：PROGRAMMER 模式下，主结果下方 4 行 BIN/OCT/HEX/DEC 实时显示
**验收条件**：
- 4 行格式：DEC: xxx / HEX: 0xFF / DEC: 255 / OCT: 0o377 / BIN: 0b11111111
- 计算时实时刷新
- BIN/OCT/HEX 仅显示整数部分（截断小数）
- DEC 行显示完整值
- 错误状态时多进制行显示 `-`

#### FR-4: 主进制切换
**描述**：PROGRAMMER 模式下，主结果"主进制"四选一按钮（DEC/BIN/OCT/HEX）
**验收条件**：
- 4 个 SegmentedControl 按钮，位于多进制显示行下方
- 切换 activeBase 仅影响主结果"标签"和数值进制
- activeBase = DEC 时主结果 = `255`；BIN 时 `0b11111111`；OCT 时 `0o377`；HEX 时 `0xFF`
- activeBase 写入偏好

#### FR-5: 模式切换动画
**描述**：键盘区域 fade + slide 过渡
**验收条件**：
- fade 200ms
- slide-from-right 8px
- 仅键盘区域动画，显示屏与顶部不动画

### 4.2 可靠性需求

#### REQ-DFR-001: 进制转换稳定性
**描述**：BaseConverter 在边界值上的行为可预测
**关注点**：
- 故障检测：NaN/Infinity 输入返回 `-`
- 故障恢复：所有 API 返回 string，永不抛异常
- 降级策略：非安全整数返回截断后的字符串

## 5. 影响范围分析

### 5.1 涉及的模块

| 模块 | 现有功能 | 新增/修改 |
|------|---------|-----------|
| CalculatorPage.ets | 二选一模式切换 | 改三选一 SegmentedControl；新增 mode 状态、activeBase 状态、BaseConverterPanel、ProgrammerKeypad；onModeChange/onActiveBaseChange 回调 |
| Models.ets | CalculatorPreferences | 新增 CalculatorMode 枚举、NumberBase 枚举；CalculatorPreferences 增加 mode/activeBase 字段 |
| PreferencesStore.ets | 8 类偏好读写 | 新增 getMode/setMode/getActiveBase/setActiveBase |
| BaseConverter.ets | 不存在 | **新建**：纯函数工具类 convert(value: number, base: NumberBase): string + 单元测试 |
| NumberFormatter.ets | 千分位/精度 | 不修改（BaseConverter 自处理大整数无千分位） |
| Calculator.ets | BigDecimal 解析器 | 不修改 |
| Expression.ets | 表达式预处理 | 不修改 |

### 5.2 代码依赖分析
- `BaseConverter` → 无外部依赖（纯函数）
- `CalculatorPage.onEquals()` → 增加多进制显示行刷新
- `CalculatorPage.onExpressionChange()` → 增加多进制显示行刷新（程序员模式时）
- `PreferencesStore.getMode()` → 返回 CalculatorMode；未设置时返回 BASIC
- `PreferencesStore.getActiveBase()` → 返回 NumberBase；未设置时返回 DEC

## 6. 复杂度评估

### 6.1 评估结果
- **复杂度等级**：M（中等）
- **影响模块数**：4（CalculatorPage, Models, PreferencesStore, BaseConverter 新建）
- **架构变更**：否
- **数据模型变更**：是（扩展 CalculatorPreferences）

### 6.2 跳过策略

| 制品 | 是否产出 |
|------|---------|
| proposal.md | ✅ 必须 |
| delta-spec.md | ✅ 必须 |
| info.md | ✅ 必须 |
| new-arch.md | ❌ 跳过（无架构变更） |
| delta-design.md | ✅ 必须 |
| tasks.md | ✅ 必须 |

## 7. 待解决问题

无。所有模糊点已在 step3 通过方案 C 自动决定。
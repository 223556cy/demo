# Proposal: 程序员模式 — 支持二进制/八进制/十六进制转换

> **Date**: 2026-06-12
> **Type**: requirement-add（新功能）
> **Category**: 计算引擎增强
> **Priority**: ⭐⭐ (P1 - 进阶刚需)
> **Issue**: 支持二进制、八进制、十六进制转换，加一个程序员模式切换

---

## 1. 业务背景

OpenCalc 是一款从 Android 迁移到 HarmonyOS 的科学计算器，定位是"日常 + 学生 + 工程师"。当前已实现基础算术 + 科学函数，但缺少**程序员计算器**的进制转换能力。

程序员/学生/硬件调试场景中，需要在 DEC/BIN/OCT/HEX 之间快速切换查看同一数值的不同表示。这是 Android 版 OpenCalc、macOS Calculator、Windows Calculator 程序员模式、Linux `bc` 都具备的基础能力，缺失会导致专业用户流失到第三方 App。

```
255  (DEC)  =  0xFF   =  0377   =  0b11111111
-1  (DEC, signed 8-bit)  =  0xFF   =  0b11111111
```

## 2. 目标

| # | 目标 | 验收标准 |
|---|------|----------|
| G1 | 提供"程序员模式"独立键盘 | 在主页面可通过切换控件进入，进入后键盘为程序员布局 |
| G2 | 支持 4 种进制显示 | DEC / BIN / OCT / HEX 可一键切换，结果区同步刷新 |
| G3 | 进制间正确转换 | 输入 255，切换到 BIN 显示 11111111；切换到 HEX 显示 FF；切换到 OCT 显示 377 |
| G4 | 支持位宽与有符号/无符号 | 8/16/32/64 位可选，signed/unsigned 切换对负数正确显示 |
| G5 | 保留基本算术能力 | 程序员模式下 +、-、×、÷、mod 仍可用，表达式引擎可复用 |
| G6 | 模式状态持久化 | 重启 App 后保留上次使用的模式与位宽 |
| G7 | 有可重复执行的回归测试 | `hvigorw test` 跑通，所有 base-conversion 用例 PASS |

## 3. 非目标 (Non-Goals)

- 不做浮点数的二进制 IEEE 754 位级查看
- 不做 BCD / 格雷码 / 二补码可视化（除默认 signed 行为外）
- 不做 ASCII 字符编码转换
- 不做任意进制（base 2-36）转换，仅支持 2/8/10/16
- 不替换现有科学模式，两者并列存在

## 4. 范围

### In Scope
- 新增 `BaseConverter.ets` 工具模块（纯函数，无副作用）
- 新增 `ProgrammerKeypad.ets` 组件（A-F 字符按钮、AND/OR/XOR/NOT、<<、>>）
- 扩展 `CalculatorPreferences` 新增 `programmerMode`、`activeBase`、`bitWidth`、`signedness` 字段
- 在 `CalculatorPage.ets` 顶部增加模式切换 Tab（基础 / 科学 / 程序员）
- `PreferencesStore` 持久化新字段
- 单元测试：`BaseConverter.test.ets` 覆盖全部基础用例

### Out of Scope
- 不改 `CalcEngine` 表达式引擎（复用现有 parseExpression，但仅支持整数表达式）
- 不改 `Expression.ets` 表达式预处理
- 不改历史记录存储结构（可记录模式，但保持简单）
- 不改主题颜色

## 5. 风险与约束

| 风险 | 等级 | 缓解 |
|------|------|------|
| 浮点数在程序员模式下可能产生非预期行为 | 中 | 明确"输入先 `Math.trunc` 截断"行为，并在 UI 提示 |
| 位宽与有符号切换时，结果需重新格式化（避免半截刷新） | 中 | 单一 `BaseConverter.format()` 函数统管 |
| 模式切换后现有表达式残留在输入框 | 低 | 切换时清空 expression 缓存，提示用户 |
| `Preferences` JSON 字段扩展，需向后兼容 | 中 | 使用可选字段 + 默认值，老配置无 programmerMode 时降级为 false |
| `<<` `>>` 位移运算可能与现有 `<<` `<=` 字符冲突 | 低 | 在程序员模式下独占解释，标准模式不启用 |

## 6. 价值与优先级

- **用户感知**：覆盖硬件/学生/CS 用户群，提升专业感
- **实现成本**：中等（新增 1 个工具模块 + 1 个组件 + 1 个 Tab 切换）
- **回归保护**：高（BaseConverter 纯函数 + 全单元测试）

## 7. 里程碑

| Milestone | 产出 | 估时 |
|-----------|------|------|
| M1 PLANNING | 4 份设计文档 | 已开始 |
| M2 IMPLEMENTING | tasks.md（TDD 任务清单） | 紧随 M1 |
| M3 APPLYING | RED 测试 + GREEN 实现 + REFACTOR + 构建/测试报告 | 紧随 M2 |

## 8. 关联文档

- `delta-spec.md` — 增量需求规格
- `info.md` — 代码仓上下文
- `new-arch.md` — 架构影响（如需）
- `delta-design.md` — 增量设计
- `tasks.md` — 任务分解
- `apply-report.md` — 应用报告

---

## 9. 澄清后需求摘要（rq-clarify 产物）

### 已澄清的关键决策
| # | 问题 | 决策 | 来源 |
|---|------|------|------|
| 1 | 是否保留科学计算 | 纯整数模式（不保留 sin/cos/√/!） | 用户选择 |
| 2 | 位运算支持 | 需要（AND/OR/XOR/NOT、<<、>>） | 用户选择 |
| 3 | 位宽与符号 | 全部纳入（4 种位宽 + signed/unsigned） | 用户选择 |
| 4 | 进制切换控件 | 顶部 Tab（DEC/BIN/OCT/HEX） | 用户选择 |
| 5 | 浮点处理 | Math.trunc 截断 | 用户选择 |
| 6 | 模式入口 | 顶部 Tab（基础/科学/程序员） | 用户选择 |

### 待定假设（实现阶段可调整）
- 小数点按钮在程序员模式下隐藏（截断行为可能造成用户困惑）
- 历史记录只存 DEC 值，避免多进制冗余
- 位宽溢出静默截断，不抛错

### 功能边界
- **包含**：4 种进制切换、4 种位宽、signed/unsigned 切换、位运算（&、\|、^、~、<<、>>）、基本四则 + mod、模式持久化
- **不包含**：浮点函数、BCD/格雷码、ASCII 转换、任意进制（仅 2/8/10/16）

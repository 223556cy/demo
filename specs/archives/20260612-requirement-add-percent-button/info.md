# 代码仓理解：百分号按钮功能

> 变更 ID: 20260612-requirement-add-percent-button
> 分析时间: 2026-06-12
> 分析工具: rq-codebase

## 基本信息

- **需求类别**：新增功能
- **需求名称**：百分号按钮
- **分析范围**：
  - `entry/src/main/ets/pages/CalculatorPage.ets` — UI 键盘
  - `entry/src/main/ets/calculator/Expression.ets` — 表达式解析器
  - `entry/src/main/ets/calculator/Calculator.ets` — 计算引擎
  - `entry/src/main/ets/model/ErrorFlags.ets` — 错误状态
  - `entry/src/main/ets/model/Models.ets` — 数据模型
  - `entry/src/main/ets/preferences/PreferencesStore.ets` — 偏好持久化
  - `entry/src/test/` — 测试套件（hypium 框架）

## ⚠️ 重要发现：已存在的实现

经过分析 worktree 当前已提交代码（最近一次 commit `59218f0 feat(percent): 添加百分号按钮功能及测试`）：

| 模块 | 当前状态 |
| --- | --- |
| `Expression.ets` | ✅ 已有 `getPercentString` 方法（line 169-260）实现了 Windows 风格 % 语义 |
| `CalculatorPage.ets` | ✅ 键盘辅助区已有 `%` 按钮（line 278, `BtnOpPct` builder line 306） |
| `Calculator.ets` | ✅ 通过 `getCleanExpression` → `evaluate` 链支持 % 求值 |
| `ErrorFlags.ets` | ✅ 支持 `syntax_error` 检测 |
| 测试框架 | ✅ hypium 1.0.15 + hamock 1.0.0（依赖已配置） |

**注意**：worktree 还有未提交的变更（`Expression.test.ets` 修改、`List.test.ets` 新增、`build-profile.json5` 修改、`.test/` 目录新增），按 AID 规范**不检查其内容**。

**建议**：本次 PLANNING 应假设从零设计。后续 IMPLEMENTING/APPLYING 阶段需对比：
- 若本次设计与已提交实现**完全一致**：可视为回归测试场景
- 若本次设计**改进/扩展**：在已提交实现基础上增量开发
- 若本次设计**完全不同**：覆盖现有实现（需用户确认）

## 架构分析

### 整体架构

OpenCalc 采用 ArkTS 单页应用架构，UI 与逻辑解耦方式如下：

```
┌─────────────────────────────────────────────────────────┐
│  View 层 (CalculatorPage.ets)                            │
│  - @Entry 装饰的 struct                                  │
│  - @State 状态（expression, result, errorMsg）          │
│  - @Builder 拆分 UI 组件（DisplayPanel, ButtonGrid）    │
│  - 业务事件方法（onDigit, onOp, onEquals, onAC）        │
├─────────────────────────────────────────────────────────┤
│  Model 层 (Expression.ets + Calculator.ets)              │
│  - Expression: 表达式预处理（getCleanExpression）       │
│  - CalcEngine: 递归下降解析器（evaluate）               │
├─────────────────────────────────────────────────────────┤
│  共享状态 (ErrorFlags.ets)                               │
│  - 静态类，所有错误标志位                                │
├─────────────────────────────────────────────────────────┤
│  数据持久化 (PreferencesStore.ets)                       │
│  - 历史记录、偏好设置                                    │
└─────────────────────────────────────────────────────────┘
```

### 核心模块职责

| 模块 | 职责 | 关键方法 |
| --- | --- | --- |
| `CalculatorPage` | UI 渲染、用户事件处理、状态管理 | `onDigit`, `onOp`, `onEquals`, `onAC`, `onBS`, `onCopy`, `onHistoryTap` |
| `Expression` | 表达式字符串预处理（符号替换、隐式乘法、% 转换、! 转换、括号补全） | `getCleanExpression`, `replaceSymbols`, `addMultiply`, `getPercentString`, `formatFactorial`, `addParenthesis` |
| `CalcEngine` | 表达式解析与求值（递归下降） | `evaluate`, `parseExpression`, `parseTerm`, `parseFactor`, `fact`, `powx` |
| `ErrorFlags` | 全局错误状态（静态字段） | `reset`, `syntax_error`, `division_by_0`, `domain_error`, `is_infinity`, `require_real_number` |

### 模块依赖关系

```
CalculatorPage
  ├── Expression (onEquals 调用 getCleanExpression)
  ├── CalcEngine (onEquals 调用 evaluate)
  ├── NumberFormatter (onEquals 调用 format)
  ├── ErrorFlags (错误状态读取/重置)
  ├── Models (HistoryItem, NumberingSystem 类型)
  └── PreferencesStore (历史/偏好持久化)

Expression
  └── ErrorFlags (错误状态写入)

CalcEngine
  └── ErrorFlags (错误状态写入)
```

### 扩展点位置

- **UI 扩展**：`CalculatorPage.ets` 的 `ButtonGrid` @Builder 中（line 272-285），通过 `Row` + `Btn*` 模式添加按钮
- **解析扩展**：`Expression.ets` 的 `getCleanExpression` 方法（line 8-23），通过 if/else if 链处理新字符
- **按钮事件**：`CalculatorPage.ets` 中已有的 `on*` 方法模式（line 70-105），添加 `onPercent` 等新方法
- **测试扩展**：`entry/src/test/ets/calculator/Expression.test.ets` 已有文件

## 接口/契约识别

### 关键接口清单

| 接口 | 模块 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- | --- |
| `Expression.getCleanExpression(calculation, decimalSep, groupingSep)` | Expression | 原始表达式字符串 + 分隔符 | 清理后的表达式字符串 | UI → Model 的入口；所有表达式必须经过此方法 |
| `CalcEngine.evaluate(equation, isDegree)` | CalcEngine | 数学表达式字符串 + 角度/弧度模式 | 求值结果（number） | 接受 getCleanExpression 输出 |
| `ErrorFlags.reset()` | ErrorFlags | — | — | 每次计算前必须调用 |
| `CalculatorPage.onOp(op)` | CalculatorPage | 运算符字符串 | — | UI 事件：将运算符追加到 expression 字符串 |

### 错误传播契约

```
Expression 写入 ErrorFlags
    ↓
CalculatorPage.onEquals() 读取 ErrorFlags
    ↓
根据 ErrorFlags 类型显示对应错误消息
    ↓
不抛异常（ArkTS 限制）
```

### ArkTS 特殊约束

- **没有 try-catch 优化**：ArkTS 鼓励减少异常处理，错误用 `ErrorFlags` 标志位传播
- **无函数类型**：`getCleanExpression` 内部使用类方法而非局部函数（ArkTS 限制）
- **静态可变状态**：`ErrorFlags` 用静态字段模拟全局可变状态（ArkTS 导入变量只读）

## 公共组件或函数识别

### 可复用组件/函数

| 组件/函数 | 位置 | 复用方式 |
| --- | --- | --- |
| `replaceAll(str, from, to)` | `Expression.ets` line 285 | 字符串批量替换 |
| `insertChar(str, ch, idx)` | `Expression.ets` line 277 | 在指定位置插入字符 |
| `lastIndexOfAny(str, chars[])` | `Expression.ets` line 295 | 查找多个字符中的最后位置 |
| `isDigit(ch)` | `Expression.ets` line 281 | 数字字符判断 |
| `NumberFormatter.format(raw, decimal, grouping, system)` | `NumberFormatter.ets` | 数字格式化 |
| `BtnDig`, `BtnOp`, `BtnFunc`, `BtnConst`, `BtnAct`, `BtnEq` | `CalculatorPage.ets` | UI 按钮 @Builder 模板 |

### UI 按钮模板特征

```typescript
@Builder BtnOpPct(l: string) {
  Text(l)
    .fontSize(...)
    .width('17%')  // 5列布局：17% 宽度
    .height(...)
    .textAlign(TextAlign.Center)
    .backgroundColor(this.getOp())
    .borderRadius(50)
    .margin(...)
    .onClick((): void => { this.onOp(l) })  // 触发事件
}
```

`%` 按钮可复用 `BtnOpPct` 模板（5列布局版本）。

## 影响范围分析

### 直接影响模块

| 模块 | 影响 | 详情 |
| --- | --- | --- |
| `Expression.ets` | 扩展 `getPercentString` | 现有实现已存在，需对照本次设计决定保留/覆盖 |
| `CalculatorPage.ets` | 新增/确认 % 按钮 | `ButtonGrid` 第 1 行第 2 列；事件方法 `onOp('%')` |
| `entry/src/test/` | 扩展测试用例 | 8 个 AC 案例 |

### 调用链分析

```
用户点击 % 按钮
    ↓
onOp('%') 被调用
    ↓
expression 字符串追加 '%'
    ↓
用户点击 =
    ↓
onEquals()
    ↓
ErrorFlags.reset()
    ↓
Expression.getCleanExpression(expression, '.', ',')
    ├── replaceSymbols: ×→*, ÷→/, E→*10^, log₂→logtwo, etc.
    ├── addMultiply: 隐式乘法
    ├── formatSquare (if √ 存在)
    ├── getPercentString (if % 存在)  ← 关键点
    ├── replaceAll('%', '/100')  ← 注意：getPercentString 后还会有这一步
    ├── formatFactorial (if ! 存在)
    └── addParenthesis
    ↓
CalcEngine.evaluate(cleaned, !radianMode)
    ↓
根据 ErrorFlags 显示结果或错误
```

### 现有 % 解析逻辑（已提交代码）

经过代码分析（line 169-260 of `Expression.ets`），现有实现已覆盖以下场景：

| 场景 | 实现位置 | 行为 |
| --- | --- | --- |
| `a+b%` | line 246-251 | 重写为 `(a)+(a)*(b/100)`（Windows 风格） |
| `a-b%` | line 246-251 | 重写为 `(a)-(a)*(b/100)`（Windows 风格） |
| `a*b%` | line 242-245 | 重写为 `a*(b/100)` |
| `a/b%` | line 242-245 | 重写为 `a/(b/100)` |
| 嵌套括号 + % | line 184-198 | 递归处理 |
| 阶乘后 + % | line 201-207 | `a!%` → `((a)!)/100)` |
| 负数 + % | （依赖 + 重写时的括号保留） | `-a+b%` 依赖 `addMultiply` 和 `getCleanExpression` 的处理 |

**与本次需求的语义对比**：

| 本次需求澄清结果 | 现有实现 | 一致？ |
| --- | --- | --- |
| 加法：a+b% = a+a*b/100 | ✅ 一致 | 是 |
| 减法：a-b% = a-a*b/100 | ✅ 一致 | 是 |
| 乘法：a*b% = a*b/100 | ✅ 一致（实现为 a*(b/100)） | 是 |
| 除法：a/b% = a/b/100 | ✅ 一致（实现为 a/(b/100)） | 是 |
| 负数：沿用 Windows 规则 | ✅ 一致（依赖括号保留） | 是 |
| 函数内 %：报错 | ❓ 需验证 | 待定 |
| 重复 %：报错 | ❓ 现有 `done[]` 数组防止重复处理同一位置 | 部分 |
| 错误恢复：清错注入 | ⚠️ 现有 `onOp('%')` 不主动清错，依赖 `onEquals` 调用 `reset()` | 部分 |
| 连续运算：% 应用到刚输入的操作数 | ✅ 通过状态机自然实现 | 是 |

**结论**：本次需求的核心语义与现有已提交实现**高度一致**。差异点主要在：
1. 函数内 % 错误检测
2. 重复 % 错误检测
3. 错误状态下 % 按钮行为

## 现有代码分析

### Expression.ets 中的 % 处理（已提交实现）

**关键代码段**（line 14-17）：

```typescript
if (cleanCalculation.indexOf('%') !== -1) {
  cleanCalculation = this.getPercentString(cleanCalculation)
  cleanCalculation = this.replaceAll(cleanCalculation, '%', '/100')
}
```

**注意**：现有的两步处理（先 `getPercentString` 重写表达式，再 `replaceAll('%', '/100')` 兜底）是一个"双保险"机制：前者处理 `a+b%` 模式，后者处理遗漏的 `%`。

**Issue #9 注释**（line 227-230）表明曾修复过操作符优先级 bug（`100+10%+5%` 的展开问题），通过给 base 加括号解决。

### CalculatorPage.ets 中的 % 按钮（已提交实现）

**按钮位置**（line 278）：

```typescript
Row() { this.BtnActPct('AC'); this.BtnOpPct('%'); this.BtnOpPct('('); this.BtnOpPct(')'); this.BtnOpPct('÷') }
```

按钮在第 1 行第 2 列（与用户澄清的"主键盘底部辅助区"一致）。

**按钮事件**（line 306）：

```typescript
@Builder BtnOpPct(l: string) { ... .onClick((): void => { this.onOp(l) }) }
```

通过 `onOp('%')` 触发，简单的字符串追加。

### 关键变量和状态

| 变量 | 类型 | 作用 |
| --- | --- | --- |
| `expression` | `@State string` | 当前表达式字符串 |
| `result` | `@State string` | 计算结果（格式化后） |
| `errorMsg` | `@State string` | 错误消息 |
| `ErrorFlags.syntax_error` 等 | 静态字段 | 错误状态传播 |

## 风险识别

| 风险 | 严重程度 | 说明 | 缓解建议 |
| --- | --- | --- | --- |
| 现有实现与本次设计冲突 | 中 | 已提交的 % 实现可能与本次 PLANNING 输出有差异 | IMPLEMENTING 阶段需对比设计；如有冲突，由用户决定 |
| 工作树有未提交变更 | 中 | `Expression.test.ets` 已修改，测试可能影响 | IMPLEMENTING 阶段需谨慎合并 |
| `getPercentString` 已包含 Issue #9 修复 | 低 | 操作符优先级 bug 已被加括号修复 | 保持现有实现 |
| ArkTS 静态字段导致 `done[500]` 数组 | 低 | line 175 硬编码 500 长度，理论上可能不够 | 监控；如有问题改用 Map |
| `%` 按钮的视觉位置 | 低 | 当前在第 1 行第 2 列（与用户澄清"主键盘底部辅助区"一致） | 已一致 |
| 错误状态下的 % 行为 | 中 | 现有 `onOp('%')` 不主动清错，依赖下次 `onEquals` | 需在 IMPLEMENTING 阶段确认 |
| 重复 % 错误处理 | 中 | 现有 `done[]` 数组防止重复，但用户期望"错误提示" | 可能需在 `onEquals` 时检测 `expression.indexOf('%%')` |
| 函数内 % 错误处理 | 中 | 现有 `getPercentString` 不检查函数上下文 | 需添加函数上下文检测 |

## 测试验证策略

### 现有测试框架

- **Framework**: `@ohos/hypium@1.0.15` + `@ohos/hamock@1.0.0`
- **位置**: `entry/src/test/ets/calculator/`
- **入口**: `entry/src/test/List.test.ets`
- **风格**: `describe`, `it`, `expect` (BDD-like)

### 本次需求测试场景（与 delta-spec.md 对齐）

| AC | 场景 | 测试位置 | 预期 |
| --- | --- | --- | --- |
| AC-001-01 | `50+10%=55` | Expression.test.ets | 展开为 `(50)+(50)*(10/100)` |
| AC-001-02 | `200-15%=170` | Expression.test.ets | 展开为 `(200)-(200)*(15/100)` |
| AC-001-03 | `8×5%=0.4` | Expression.test.ets | 展开为 `8*5/100` 或 `8*(5/100)` |
| AC-001-04 | `100÷10%=0.1` | Expression.test.ets | 展开为 `100/10/100` |
| AC-001-05 | `-50+10%=-55` | Expression.test.ets | 展开为 `(-50)+(-50)*(10/100)` |
| AC-001-06 | `50+10%=55 → +5%=57.75` | 集成测试 | 状态机正确 |
| AC-001-07 | `sin(30%)` 报错 | Expression.test.ets | ErrorFlags.syntax_error = true |
| AC-001-08 | `50%%` 报错 | Expression.test.ets | ErrorFlags.syntax_error = true |
| AC-001-09 | 错误状态 + % → 清错 | 集成测试 | ErrorFlags 清除 |

### 测试运行命令

```bash
# Windows 必须用 --no-daemon 标志
hvigorw --no-daemon test
```

## 监控运维支持

本次需求不涉及新增监控点、配置项、日志记录。错误处理统一通过 `ErrorFlags` 状态传播。

## 关键发现

### 可复用组件或函数

- `Expression.replaceAll` — 字符串批量替换
- `Expression.insertChar` — 位置插入
- `Expression.lastIndexOfAny` — 多字符查找
- `CalculatorPage.BtnOpPct` — UI 按钮模板

### 风险提示

1. **已提交代码已实现 %**：需在 IMPLEMENTING 阶段对比决策（保留/覆盖/扩展）
2. **未提交变更可能影响测试**：未检查其内容，需谨慎合并
3. **Issue #9 注释表明已修复操作符优先级 bug**：本次设计应保持现有修复

### 建议事项

1. **PLANNING 阶段**：本次需求核心语义与现有实现高度一致，可视为"回归测试"或"完善边缘场景"
2. **IMPLEMENTING 阶段**：
   - 任务 1：对比本次 delta-spec.md 与现有 `getPercentString` 实现，识别差异点
   - 任务 2：补充缺失的边缘场景（函数内 % 错误、重复 % 错误、错误恢复）
   - 任务 3：添加/更新 8 个 AC 测试用例
3. **APPLYING 阶段**：
   - 如差异点已由现有实现覆盖：跳过实现，仅跑测试验证
   - 如有缺失：在现有实现上增量修改
   - 如需重写：保留现有 `Issue #9` 修复

## 与 spec 系统的关联

- **SPECS_FEATURE_ROOT**: `D:/huawei/Demo/specs/specs`（当前为空，无既有 feature spec）
- **CHANGES_ROOT**: `D:/huawei/Demo/specs/changes/20260612-requirement-add-percent-button/`
- **本次 delta-spec.md 是该特性的首次规格说明**

# 需求SPEC v1.0 — Issue #11 实时预览功能（增量）

---

## 系统背景

### 目的

> 为 OpenCalc HarmonyOS 移植版的计算器主页面增加"实时预览"能力：用户在按键输入表达式过程中，无需按等号即在显示屏上看到当前表达式的计算结果。目标提升"所见即所得"的科技感与日常使用流畅度，让用户在敲完等号之前就能验证结果正确性。

### 术语与缩写

| 术语/缩写 | 定义 |
| ----- | --- |
| 实时预览（Realtime Preview） | 用户输入表达式时，结果同步显示在显示屏上，无需触发等号按钮 |
| 表达式（Expression） | CalculatorPage.expression 状态变量，存储用户当前输入的字符串 |
| 预览值（Preview） | 本变更新增的 CalculatorPage.preview 状态变量，存储当前表达式的实时计算结果 |
| 降级（Fallback） | 当表达式不完整/语法错误时，预览区显示空字符串或占位符（不报错） |
| 显示屏（Display Panel） | CalculatorPage.DisplayPanel() 区域，位于页面顶部 |

---

## 系统上下文

### 目标系统

| 字段 | 内容 |
| ----------------- | --- |
| 系统名称 | OpenCalc HarmonyOS 移植版（计算器 App） |
| 系统边界说明 | 内部为 OpenCalc 主页面 UI + 表达式计算；外部无新依赖；复用现有 CalcEngine、Expression、NumberFormatter |

### 周边交互方清单

| 编号    | 外部系统名称 | 类型 | 交互接口类型 | 交互接口主要功能 |
| ----- | ------ | ------------------ | ------------------------------------ | -------- |
| ES-01 | 用户 | 人 | UI 触摸 | 按下数字/运算符/功能按钮，触发 expression 变化 |
| ES-02 | CalcEngine | 内部模块 | ArkTS 类方法 | 调用 evaluate(clean, radians) 获取数值结果 |
| ES-03 | Expression | 内部模块 | ArkTS 类方法 | 调用 getCleanExpression(raw, dec, grp) 预处理表达式 |

---

## 需求描述

| 需求编号 | 需求名称 | 需求描述 | 设计人员 |
| -------- | -------- | -------- | -------- |
| SR-RP-01 | 实时预览显示 | 用户输入合法完整表达式时，显示屏等号上方实时显示计算结果 | AID 自动化 |
| SR-RP-02 | 降级占位 | 表达式为空、不完整、含语法错误时，预览区显示空字符串 | AID 自动化 |
| SR-RP-03 | 表达式变化触发 | expression 状态变化（数字/运算符/AC/BS）后立即重算预览 | AID 自动化 |
| SR-RP-04 | 等号后一致性 | 按等号后预览值与主结果区内容相同（覆盖式） | AID 自动化 |
| SR-RP-05 | 横竖屏兼容 | 竖屏和横屏布局都正确显示预览行 | AID 自动化 |
| SR-RP-06 | 错误隔离 | 预览计算过程中产生的错误不污染主结果区与历史记录 | AID 自动化 |
| SR-RP-07 | 长按复制 | 长按预览文本/显示屏区域时复制主结果（与现有行为一致） | AID 自动化 |

### 用户旅程

**主路径 — 实时预览生效**：
1. 用户启动 OpenCalc
2. 用户按数字 `1` → expression = "1"，preview = "1"
3. 用户按 `+` → expression = "1+"，preview = ""（不完整）
4. 用户按数字 `2` → expression = "1+2"，preview = "3"
5. 用户按等号 → result = "3"，preview = "3"（一致）
6. 用户按 AC → expression = ""，preview = ""，result = ""

**异常路径 — 错误表达式**：
1. 用户输入 `1++2` → expression = "1++2"，preview = ""（语法错误，不报错）
2. 用户输入 `1÷0` → expression = "1÷0"，preview = "∞"（或空，需在 IMPLEMENTING 阶段决定）

**性能路径 — 复杂表达式**：
1. 用户输入 `sin(0)+cos(0)` → preview = "1"
2. 用户输入 `1+2*3/4-5` → preview = "-2.5"

---

## 需求分解

### 5.1 功能性需求

#### 5.1.1 实时计算（FR-RP-01）
- **触发**：`@Watch('expression')` 或在 onDigit/onOp/onBS/onAC 后调用
- **输入**：当前 expression 字符串
- **输出**：preview 字符串（已格式化的数值结果）或空字符串
- **算法**：
  1. expression 为空 → preview = ""
  2. expression 末字符为运算符/左括号/小数点/函数名前缀 → preview = ""
  3. 调用 `expr.getCleanExpression(expression, '.', ',')` 预处理
  4. 若 `ErrorFlags.syntax_error` 触发 → preview = ""
  5. 调用 `engine.evaluate(clean, !this.radianMode)` 计算
  6. 若 `ErrorFlags.*` 任一错误位 → preview = ""
  7. 否则 `NumberFormatter.format(raw.toString(), '.', ',', NumberingSystem.INTERNATIONAL)` → preview
  8. 整个 try/catch 包裹，异常 → preview = ""

#### 5.1.2 UI 展示（FR-RP-02）
- 在 DisplayPanel 中 result 行上方新增 preview 行
- 样式：fontSize 14（竖屏）/ 12（横屏）、fontColor getT2()（次要色）、textAlign End、右对齐
- 当 preview 为空时显示空字符串（不显示占位符，避免干扰）

#### 5.1.3 状态隔离（FR-RP-03）
- 预览计算独立调用 `Expression.getCleanExpression` 临时实例或清理 ErrorFlags
- 计算完毕后恢复 ErrorFlags 状态，避免污染后续 onEquals

### 5.2 可靠性需求（DFX）

#### 5.2.1 FMEA 故障模式分析

| 故障模式 | 严重度 | 原因 | 影响 | 消减措施（纳入需求） |
| --- | --- | --- | --- | --- |
| 预览计算抛异常 | 中 | 表达式长度异常/特殊字符 | 主页面崩溃 | try/catch 包裹 computePreview 整个函数（FR-RP-01-8） |
| ErrorFlags 状态污染 | 高 | 预览计算后未清理 | onEquals 时错误状态被错误继承 | 预览计算前 snapshot + 复原 ErrorFlags（FR-RP-03） |
| 不完整表达式导致 result 异常 | 中 | 末位是运算符时 evaluate 行为不可预期 | preview 显示乱码 | 末字符白名单过滤（FR-RP-01-2） |
| 连续按键导致频繁重算 | 低 | 每次按键都同步计算 | 性能下降 | 计算成本低（< 1ms），无需 debounce；若后期性能问题再加 |
| 预览值与主结果不一致 | 中 | 格式化参数不同步 | 用户困惑 | 复用 NumberFormatter.format 同一参数（FR-RP-01-7） |
| %% 等百分号边缘导致 syntax_error | 低 | 上一变更引入的 SR-08 检测 | 预览区闪烁 | 捕获 ErrorFlags.syntax_error 后清空 preview（FR-RP-01-4） |

#### 5.2.2 可靠性消减措施清单

| 编号 | 消减措施 | 关联需求 | 验收测试 |
| --- | --- | --- | --- |
| MTG-RP-01 | computePreview 整体 try/catch | FR-RP-01-8 | AC-RP-09 |
| MTG-RP-02 | 预览计算前后 snapshot/restore ErrorFlags | FR-RP-03 | AC-RP-10 |
| MTG-RP-03 | 末字符白名单过滤 | FR-RP-01-2 | AC-RP-04, AC-RP-05 |
| MTG-RP-04 | 复用相同 NumberFormatter 格式化 | FR-RP-01-7 | AC-RP-11 |
| MTG-RP-05 | 捕获 ErrorFlags 后清空 preview | FR-RP-01-4 | AC-RP-06 |

### 5.3 接口需求

#### 5.3.1 内部接口

```typescript
// CalculatorPage 新增
@State preview: string = ''

@Watch('expression')
onExpressionChange(): void {
  this.preview = this.computePreview(this.expression)
}

private computePreview(exprStr: string): string {
  // 见 5.1.1 算法
}
```

#### 5.3.2 复用接口
- `Expression.getCleanExpression(calculation, dec, grp): string`
- `CalcEngine.evaluate(clean: string, degreeMode: boolean): number`
- `NumberFormatter.format(raw: string, dec, grp, sys): string`

### 5.4 数据需求

无新增数据模型。

### 5.5 性能需求
- 预览计算延迟：< 100ms（同步，< 50 字符表达式）
- 状态更新频次：每次 expression 变化触发 1 次

### 5.6 兼容性需求
- 不破坏现有 onEquals、onCopy、onHistoryTap 等流程
- 不修改 CalcEngine/Expression/NumberFormatter 公共接口
- 竖屏和横屏都正确显示

---

## 验收用例

| 用例编号 | 用例描述 | 输入 | 预期 preview | 关联需求 |
| --- | --- | --- | --- | --- |
| AC-RP-01 | 空表达式 | "" | "" | SR-RP-02 |
| AC-RP-02 | 简单加法 | "1+2" | "3" | SR-RP-01 |
| AC-RP-03 | 减法含负数 | "5-10" | "-5" | SR-RP-01 |
| AC-RP-04 | 不完整加法 | "1+" | "" | SR-RP-02, MTG-RP-03 |
| AC-RP-05 | 函数未闭合 | "sin(0" | "" | SR-RP-02, MTG-RP-03 |
| AC-RP-06 | 语法错误 | "1++2" | "" | SR-RP-02, MTG-RP-05 |
| AC-RP-07 | 函数 | "sin(0)" | "0" | SR-RP-01 |
| AC-RP-08 | 百分号 | "50+10%" | "55" | SR-RP-01 |
| AC-RP-09 | 异常输入 | "1+(" | "" | MTG-RP-01 |
| AC-RP-10 | 错误状态隔离 | 先 "1÷0" 再 "1+1" | preview=2, onEquals 后 result=2 不报错 | MTG-RP-02 |
| AC-RP-11 | 格式一致 | "1000+2000" | "3,000" | MTG-RP-04 |
| AC-RP-12 | AC 清空 | "1+2"→AC | "" | SR-RP-03 |
| AC-RP-13 | 等号后一致 | "1+2"→等号 | preview="3" 与 result="3" 一致 | SR-RP-04 |
| AC-RP-14 | 长表达式 | "1+2*3/4-5" | "-2.5" | SR-RP-01 |
| AC-RP-15 | 嵌套括号 | "(1+2)*(3+4)" | "21" | SR-RP-01 |

---

## 风险与约束

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| ErrorFlags 静态状态污染 | 高 | snapshot + restore（已纳入 MTG-RP-02） |
| 极长表达式性能 | 低 | < 50 字符可接受；超长可后期加 debounce |
| 横屏布局溢出 | 低 | preview 行 maxLines=1 限制 |
| ArkTS 静态属性限制 | 中 | ErrorFlags 为对象属性（已验证可读写） |

---

## 不涉及

- 表达式自动补全（括号/函数名）
- 预览动画/过渡效果
- 主题色定制预览样式
- 历史记录实时更新
- 复制预览内容（仍复制主结果）

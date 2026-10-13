# Issue #14 单位换算 — 代码仓理解

## 基本信息

- **需求类别**:新增功能(New Requirement)
- **需求名称**:unit-conversion
- **分析时间**:2026-06-15
- **分析范围**:
  - `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`(主计算器页面)
  - `opencalc/entry/src/main/ets/calculator/Expression.ets`(表达式预处理)
  - `opencalc/entry/src/main/ets/calculator/Calculator.ets`(计算引擎)
  - `opencalc/entry/src/main/ets/calculator/NumberFormatter.ets`(数字格式化)
  - `opencalc/entry/src/main/ets/model/ErrorFlags.ets`(错误标志)
  - `opencalc/entry/src/main/ets/model/Models.ets`(类型定义)
  - `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets`(持久化)
  - `opencalc/entry/src/test/ets/calculator/Expression.test.ets`(现有测试)

## 架构分析

### 模块结构图

```
opencalc/entry/src/main/ets/
├── pages/
│   ├── Index.ets                    # 启动页
│   └── CalculatorPage.ets           # 主计算器页面(543行)  ← 集成 NL 解析层
├── calculator/
│   ├── Expression.ets               # 表达式预处理(314行)
│   ├── Calculator.ets               # 计算引擎(180行)
│   └── NumberFormatter.ets          # 数字格式化
├── common/                          # ← 新建目录
│   ├── UnitConverter.ets            # 【NEW】单位换算核心
│   ├── UnitConverter.test.ets       # 【NEW】单元测试
│   ├── NaturalLanguageParser.ets    # 【NEW】NL 模式识别
│   └── NaturalLanguageParser.test.ets # 【NEW】单元测试
├── model/
│   ├── Models.ets                   # HistoryItem / NumberingSystem
│   └── ErrorFlags.ets               # 静态错误标志
├── entryability/
└── preferences/
    └── PreferencesStore.ets
```

### 核心模块职责

| 模块 | 职责 | 关键导出 |
|------|------|----------|
| CalculatorPage.ets | UI 渲染、按钮事件、状态管理 | `@Component CalculatorPage` |
| Expression.ets | 表达式字符串预处理 | `getCleanExpression(input, dec, grp): string` |
| Calculator.ets (CalcEngine) | 表达式求值 | `evaluate(eq, isDegree): number` |
| NumberFormatter.ets | 数值显示格式化 | `static format(text, dec, grp, sys): string` |
| ErrorFlags.ets | 错误标志(静态共享) | 5 个 static boolean + reset() / snapshot() / restore() |
| **UnitConverter.ets** 【NEW】 | 单位换算核心 | `static convert(value, from, to, category): number \| null` |
| **NaturalLanguageParser.ets** 【NEW】 | NL 模式识别 | `static parse(input): ParseResult \| null` |

### 依赖关系

```
CalculatorPage
  ├─→ NaturalLanguageParser.parse  【NEW】(在 expression 变化时调用)
  │     └─→ 命中 → UnitConverter.convert 【NEW】
  │     └─→ 未命中 → 降级为 CalcEngine.evaluate
  ├─→ Expression.getCleanExpression  (无修改)
  ├─→ CalcEngine.evaluate  (无修改)
  ├─→ NumberFormatter.format  (无修改)
  ├─→ ErrorFlags  (无修改,仅扩展可读性)
  └─→ PreferencesStore  (无修改)
```

## 接口/契约识别

### 复用接口(无修改)

#### `Expression.getCleanExpression`
- **签名**:`getCleanExpression(calculation: string, decimalSeparatorSymbol: string, groupingSeparatorSymbol: string): string`
- **副作用**:可能设置 `ErrorFlags.syntax_error = true`(如遇到 `%%`)
- **返回值**:清洗后的数学表达式
- **使用约束**:输入必须是合法的"显示表达式",不要求完全可求值
- **本变更影响**:不修改;NL 解析失败时仍走此流程

#### `CalcEngine.evaluate`
- **签名**:`evaluate(equation: string, isDegree: boolean): number`
- **副作用**:可能设置 5 个 `ErrorFlags.*` 之一
- **返回值**:数值结果
- **使用约束**:输入必须是 `getCleanExpression` 处理后的字符串
- **本变更影响**:不修改;NL 解析失败时仍走此流程

#### `NumberFormatter.format`
- **签名**:`static format(text: string, dec: string, grp: string, sys: NumberingSystem): string`
- **副作用**:无
- **返回值**:带千分位的显示字符串
- **本变更影响**:复用,用于格式化单位换算结果

#### `ErrorFlags` 静态字段
- **本变更影响**:不修改;NL 解析失败时降级,CalcEngine 调用仍使用 ErrorFlags

### 新增接口

#### `UnitConverter.convert` 【NEW】
```typescript
/**
 * 单位换算核心函数
 * @param value 输入数值
 * @param from 源单位(canonical key,如 "cm" / "C" / "kg")
 * @param to 目标单位(canonical key)
 * @param category 单位类别("length" | "temperature" | "mass" | "volume")
 * @returns 换算结果;若 from/to 类别不匹配或单位未注册,返回 null
 */
static convert(value: number, from: string, to: string, category: string): number | null
```

**数据结构**:
```typescript
// 长度:以"米"为基准的换算因子
private static lengthFactors: Map<string, number> = new Map([
  ['m', 1.0], ['cm', 0.01], ['mm', 0.001], ['km', 1000.0],
  ['inch', 0.0254], ['ft', 0.3048], ['yd', 0.9144], ['mi', 1609.344]
])

// 温度:非线性换算,使用专门函数
private static convertTemperature(value: number, from: string, to: string): number

// 质量:以"千克"为基准
private static massFactors: Map<string, number> = new Map([
  ['kg', 1.0], ['g', 0.001], ['lb', 0.45359237], ['oz', 0.028349523125]
])

// 体积:以"升"为基准
private static volumeFactors: Map<string, number> = new Map([
  ['L', 1.0], ['mL', 0.001], ['gal', 3.785411784], ['fl_oz', 0.0295735295625]
])
```

#### `NaturalLanguageParser.parse` 【NEW】
```typescript
/**
 * 解析自然语言单位换算查询
 * @param input 用户输入字符串
 * @returns ParseResult {value, from, to, category};若不匹配 NL 模式,返回 null
 */
static parse(input: string): ParseResult | null

interface ParseResult {
  value: number
  from: string       // canonical key (lowercase, 如 "cm")
  to: string         // canonical key
  category: 'length' | 'temperature' | 'mass' | 'volume'
}
```

**实现思路**:
1. 尝试匹配中文模式正则:`^(\d+(?:\.\d+)?)\s*([一-龥]+|cm|mm|...)\s*(转|到|...)\s*([一-龥]+|cm|mm|...)$`
2. 尝试匹配英文模式正则:`^(\d+(?:\.\d+)?)\s*([a-zA-Z°]+)\s*(to|in|->|=>)\s*([a-zA-Z°]+)$`
3. 单位别名查表(中英文 → canonical key)
4. 通过 canonical key 前缀/Map 查询确定 category
5. 返回 ParseResult

**别名表**:
```typescript
private static aliases: Map<string, {key: string, category: string}> = new Map([
  // length
  ['米', {key: 'm', category: 'length'}],
  ['厘米', {key: 'cm', category: 'length'}],
  ['公分', {key: 'cm', category: 'length'}],
  ['cm', {key: 'cm', category: 'length'}],
  ['centimeter', {key: 'cm', category: 'length'}],
  // ... 20+ 个别名
  // temperature
  ['摄氏度', {key: 'C', category: 'temperature'}],
  ['℃', {key: 'C', category: 'temperature'}],
  // ... 10+ 个别名
])
```

## 现有功能影响分析

| 现有功能 | 变更影响 | 优先级 |
|---------|---------|--------|
| `onEquals` 主计算流程 | 不改;NL 解析在 expression 变化时(onWatch)触发,与 onEquals 并行 | 必查 |
| `onDigit / onOp` 等按钮事件 | 不改;只是 expression 字符串变化 | 必查 |
| `@State expression` | 不改;NL 解析读取 expression 但不修改 | 必查 |
| `@State result` | 不改;NL 解析成功时通过 onEquals 路径写入 result | 必查 |
| `@State preview` 实时预览(Issue #11) | 不改;preview 仍走原 computePreview 逻辑;NL 不在 preview 范围 | 必查 |
| 百分号按钮(Issue #9) | 不改;百分号与 NL 模式互斥(百分号走 Expression 预处理,NL 走正则) | 必查 |
| `@State history` 历史记录 | 不改;onEquals 仍触发 history.add | 必查 |
| `getCleanExpression` 表达式预处理 | 不改;NL 解析失败时仍调用 | 必查 |
| `CalcEngine.evaluate` | 不改 | 必查 |
| 横竖屏布局 | 不改;NL 输入仍走 expression 输入层 | 必查 |
| 主题切换 | 不改 | 可选 |
| 偏好设置 | 不改 | 可选 |

## 集成点

### CalculatorPage.ets 集成位置

```typescript
// 现有 @State
@State @Watch('onExpressionChange') expression: string = ''
@State preview: string = ''

// 新增 @State
@State nlConversionResult: string = ''   // NL 换算结果显示

// 在 onExpressionChange() 中,在 computePreview 之前:
onExpressionChange(): void {
  // 1. 尝试 NL 解析
  const nlResult = NaturalLanguageParser.parse(this.expression)
  if (nlResult !== null) {
    const converted = UnitConverter.convert(nlResult.value, nlResult.from, nlResult.to, nlResult.category)
    if (converted !== null) {
      this.nlConversionResult = NumberFormatter.format(converted.toString(), '.', ',', NumberingSystem.INTERNATIONAL)
    } else {
      this.nlConversionResult = ''
    }
  } else {
    this.nlConversionResult = ''
  }
  // 2. 原有 preview 计算
  this.preview = this.computePreview(this.expression, this.radianMode)
}

// onEquals() 中,在执行前先检查 NL 解析结果:
onEquals(): void {
  if (this.nlConversionResult.length > 0) {
    // NL 已识别,直接采用 nlConversionResult
    this.result = this.nlConversionResult
    // ... 写入 history
    return
  }
  // 原计算流程
  // ...
}
```

**关键决策点**:
- **触发时机**:NL 解析在 `onExpressionChange`(expression 变化时,与 preview 并行)
- **结果展示**:NL 解析结果在按 = 时直接写入 result(因为 preview 模式已存在,需在按 = 时确认)
- **不修改 expression**:保留 NL 原文,用户可继续编辑
- **降级透明**:NL 解析失败时,nlConversionResult 为空,走原计算

## 测试策略

### 单元测试(Node 端口 + ArkTS 端)
- **UnitConverter.test.ets / .mjs**:覆盖每个单位对(4 类别 × ~15 转换对 = ~60 用例)
- **NaturalLanguageParser.test.ets / .mjs**:覆盖中英文 NL 模式、别名、错误输入(~30 用例)
- **回归测试**:不破坏现有 17 个 preview 用例 + 8 个百分号用例

### UI 自动化测试(harmonyos-ui-test)
- 在 HarmonyOS 模拟器上跑:
  - AC-UC-01: 输入 "100厘米转英寸" → 截图 result=39.3700787
  - AC-UC-02: 输入 "30摄氏度转华氏度" → 截图 result=86
  - AC-UC-06: 输入 "100cm to inch" → 截图 result=39.3700787
  - 回归:输入 "1+2" → result=3(不触发 NL)
- 产物:截图 + uiautomator dump + results.json

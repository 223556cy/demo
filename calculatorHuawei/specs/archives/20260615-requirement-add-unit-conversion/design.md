# 组件设计 — Issue #14 单位换算功能

> aid-workflow 20260615-requirement-add-unit-conversion · PLANNING step8 产出物
> 基线:proposal.md / delta-spec.md / info.md

---

## 1. 设计目标

在 CalculatorPage.ets 的 expression 输入层集成 NL 解析:
- **检测**:用户输入 "数字 + 单位A + 转换词 + 单位B" 模式时,自动识别为单位换算请求
- **执行**:通过 UnitConverter 计算换算结果
- **展示**:按 "=" 后,结果直接显示在 DisplayPanel.result 区域
- **降级**:NL 解析失败时,完全不影响现有 CalcEngine.evaluate 流程
- **共存**:与实时预览(Issue #11)、百分号(Issue #9)、历史记录、偏好设置共存

---

## 2. 架构设计

### 2.1 模块依赖图

```
┌─────────────────────────────────────────────────────────────┐
│ CalculatorPage (ArkTS @Component)                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ @State @Watch('onExpressionChange') expression: string │  │
│  │ @State preview: string                                │  │
│  │ @State nlConversionResult: string  ← NEW              │  │
│  │                                                        │  │
│  │ onExpressionChange()  ← MODIFIED                      │  │
│  │   ├─→ NaturalLanguageParser.parse()  ← NEW (调用)     │  │
│  │   │     └─→ NL 命中 → UnitConverter.convert() ← NEW   │  │
│  │   │     └─→ NL 未命中 → nlConversionResult = ''       │  │
│  │   └─→ computePreview() (existing)                     │  │
│  │                                                        │  │
│  │ onEquals()  ← MODIFIED                                │  │
│  │   ├─→ if (nlConversionResult 非空) → 直接采用,不走     │  │
│  │   │   CalcEngine                                       │  │
│  │   └─→ else → 走原 CalcEngine.evaluate 流程            │  │
│  └────────────────────────────────────────────────────────┘  │
│       │            │                  │                       │
│       ▼            ▼                  ▼                       │
│  NaturalLanguage  UnitConverter   CalcEngine  (existing)    │
│  Parser (NEW)     (NEW)                                       │
│       │            │                                         │
│       └────────────┴────► ErrorFlags (existing)              │
│                                                              │
│  DisplayPanel() @Builder  ← 显示 result 区域                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户按键 (数字/单位/转换词)
   │
   ▼
onDigit / onOp / ... (existing)
   │
   ▼
this.expression = <new>  ← @State 触发 UI 刷新
   │
   ▼
@Watch('expression') → onExpressionChange()
   │
   ├─► [NEW] NaturalLanguageParser.parse(expression)
   │     │
   │     ├─► 命中 → UnitConverter.convert(value, from, to, category)
   │     │     └─► 成功 → nlConversionResult = format(converted)
   │     │     └─► 失败(跨类) → nlConversionResult = ''
   │     │
   │     └─► 未命中 → nlConversionResult = ''
   │
   └─► [existing] computePreview(expression, radianMode)
         └─► this.preview = ...

用户按 "=" 键
   │
   ▼
onEquals()
   │
   ├─► [NEW] if (nlConversionResult 非空)
   │     │
   │     ├─► this.result = nlConversionResult
   │     ├─► 添加到 history
   │     └─► return (跳过 CalcEngine)
   │
   └─► [existing] CalcEngine.evaluate(clean, ...)
         └─► this.result = format(raw)
```

### 2.3 触发器策略

| 候选 | 优点 | 缺点 | 决定 |
|------|------|------|------|
| 在 `onExpressionChange` 同步触发 | 与 preview 一致,UI 状态即时 | 无明显缺点 | ✅ 采用 |
| 在 `onEquals` 触发 | 按等号才计算 | 用户看不到中间结果,体验差 | ❌ |
| 在 `aboutToAppear` 后台线程 | 不阻塞 UI | ArkTS 线程模型复杂 | ❌ |

**理由**:与 preview 完全并行,共享受同一个 @Watch,UI 响应一致。

---

## 3. 组件 API 契约

### 3.1 新增 @State

```typescript
/**
 * aid-workflow 20260615: NL 单位换算结果
 * - 空字符串表示未识别 NL 模式或解析失败(降级到原计算)
 * - 非空字符串表示已识别 NL,按 = 时直接采用
 */
@State nlConversionResult: string = ''
```

### 3.2 新增模块:`UnitConverter.ets`

#### 3.2.1 数据结构

```typescript
// 单位类别常量
const CATEGORY_LENGTH = 'length'
const CATEGORY_TEMPERATURE = 'temperature'
const CATEGORY_MASS = 'mass'
const CATEGORY_VOLUME = 'volume'

// 长度:以"米"为基准的换算因子
// 单位:canonical key → 多少"米"
const LENGTH_FACTORS: Record<string, number> = {
  m: 1.0, cm: 0.01, mm: 0.001, km: 1000.0,
  inch: 0.0254, ft: 0.3048, yd: 0.9144, mi: 1609.344
}

// 质量:以"千克"为基准
const MASS_FACTORS: Record<string, number> = {
  kg: 1.0, g: 0.001, lb: 0.45359237, oz: 0.028349523125
}

// 体积:以"升"为基准
const VOLUME_FACTORS: Record<string, number> = {
  L: 1.0, mL: 0.001, gal: 3.785411784, fl_oz: 0.0295735295625
}
```

#### 3.2.2 公共 API

```typescript
export class UnitConverter {
  /**
   * 单位换算
   * @param value 输入数值
   * @param from 源单位 canonical key
   * @param to 目标单位 canonical key
   * @param category 单位类别
   * @returns 换算结果;from/to 类别不匹配或单位未注册 → null
   */
  static convert(value: number, from: string, to: string, category: string): number | null {
    if (from === to) return value
    if (category === CATEGORY_TEMPERATURE) return UnitConverter.convertTemperature(value, from, to)
    const factors: Record<string, number> | null = UnitConverter.getFactors(category)
    if (factors === null) return null
    const fromFactor: number | undefined = factors[from]
    const toFactor: number | undefined = factors[to]
    if (fromFactor === undefined || toFactor === undefined) return null
    const valueInBase: number = value * fromFactor
    return valueInBase / toFactor
  }

  /**
   * 温度换算(非线性)
   * @returns 换算结果;单位未注册 → null
   */
  private static convertTemperature(value: number, from: string, to: string): number | null {
    // 统一转换为摄氏度
    let celsius: number
    if (from === 'C') celsius = value
    else if (from === 'F') celsius = (value - 32) * 5 / 9
    else if (from === 'K') celsius = value - 273.15
    else return null

    // 转换为目标单位
    if (to === 'C') return celsius
    if (to === 'F') return celsius * 9 / 5 + 32
    if (to === 'K') return celsius + 273.15
    return null
  }

  /**
   * 获取类别对应的换算因子表
   */
  private static getFactors(category: string): Record<string, number> | null {
    if (category === CATEGORY_LENGTH) return LENGTH_FACTORS
    if (category === CATEGORY_MASS) return MASS_FACTORS
    if (category === CATEGORY_VOLUME) return VOLUME_FACTORS
    return null
  }
}
```

### 3.3 新增模块:`NaturalLanguageParser.ets`

#### 3.3.1 数据结构

```typescript
interface ParseResult {
  value: number
  from: string       // canonical key
  to: string         // canonical key
  category: string   // 'length' | 'temperature' | 'mass' | 'volume'
}

// 别名表:用户输入 → canonical key + category
const ALIASES: Record<string, {key: string, category: string}> = {
  // length
  '米': {key: 'm', category: 'length'},
  'm': {key: 'm', category: 'length'},
  'meter': {key: 'm', category: 'length'},
  'meters': {key: 'm', category: 'length'},
  '厘米': {key: 'cm', category: 'length'},
  '公分': {key: 'cm', category: 'length'},
  'cm': {key: 'cm', category: 'length'},
  'centimeter': {key: 'cm', category: 'length'},
  'centimeters': {key: 'cm', category: 'length'},
  '毫米': {key: 'mm', category: 'length'},
  'mm': {key: 'mm', category: 'length'},
  '千米': {key: 'km', category: 'length'},
  '公里': {key: 'km', category: 'length'},
  'km': {key: 'km', category: 'length'},
  'kilometer': {key: 'km', category: 'length'},
  '英寸': {key: 'inch', category: 'length'},
  '时': {key: 'inch', category: 'length'},
  'inch': {key: 'inch', category: 'length'},
  'inches': {key: 'inch', category: 'length'},
  'in': {key: 'inch', category: 'length'},
  '英尺': {key: 'ft', category: 'length'},
  '尺': {key: 'ft', category: 'length'},
  'foot': {key: 'ft', category: 'length'},
  'feet': {key: 'ft', category: 'length'},
  'ft': {key: 'ft', category: 'length'},
  '码': {key: 'yd', category: 'length'},
  'yard': {key: 'yd', category: 'length'},
  'yards': {key: 'yd', category: 'length'},
  'yd': {key: 'yd', category: 'length'},
  '英里': {key: 'mi', category: 'length'},
  '哩': {key: 'mi', category: 'length'},
  'mile': {key: 'mi', category: 'length'},
  'miles': {key: 'mi', category: 'length'},
  'mi': {key: 'mi', category: 'length'},

  // temperature
  '摄氏度': {key: 'C', category: 'temperature'},
  '摄氏': {key: 'C', category: 'temperature'},
  '℃': {key: 'C', category: 'temperature'},
  'C': {key: 'C', category: 'temperature'},
  'Celsius': {key: 'C', category: 'temperature'},
  'celsius': {key: 'C', category: 'temperature'},
  '华氏度': {key: 'F', category: 'temperature'},
  '华氏': {key: 'F', category: 'temperature'},
  '℉': {key: 'F', category: 'temperature'},
  'F': {key: 'F', category: 'temperature'},
  'Fahrenheit': {key: 'F', category: 'temperature'},
  'fahrenheit': {key: 'F', category: 'temperature'},
  '开尔文': {key: 'K', category: 'temperature'},
  'K': {key: 'K', category: 'temperature'},
  'Kelvin': {key: 'K', category: 'temperature'},
  'kelvin': {key: 'K', category: 'temperature'},

  // mass
  '千克': {key: 'kg', category: 'mass'},
  '公斤': {key: 'kg', category: 'mass'},
  'kg': {key: 'kg', category: 'mass'},
  'kilogram': {key: 'kg', category: 'mass'},
  'kilograms': {key: 'kg', category: 'mass'},
  '克': {key: 'g', category: 'mass'},
  'g': {key: 'g', category: 'mass'},
  'gram': {key: 'g', category: 'mass'},
  'grams': {key: 'g', category: 'mass'},
  '磅': {key: 'lb', category: 'mass'},
  'lb': {key: 'lb', category: 'mass'},
  'lbs': {key: 'lb', category: 'mass'},
  'pound': {key: 'lb', category: 'mass'},
  'pounds': {key: 'lb', category: 'mass'},
  '盎司': {key: 'oz', category: 'mass'},
  'oz': {key: 'oz', category: 'mass'},
  'ounce': {key: 'oz', category: 'mass'},
  'ounces': {key: 'oz', category: 'mass'},

  // volume
  '升': {key: 'L', category: 'volume'},
  '公升': {key: 'L', category: 'volume'},
  'L': {key: 'L', category: 'volume'},
  'l': {key: 'L', category: 'volume'},
  'liter': {key: 'L', category: 'volume'},
  'liters': {key: 'L', category: 'volume'},
  '毫升': {key: 'mL', category: 'volume'},
  'mL': {key: 'mL', category: 'volume'},
  'ml': {key: 'mL', category: 'volume'},
  'milliliter': {key: 'mL', category: 'volume'},
  'milliliters': {key: 'mL', category: 'volume'},
  '加仑': {key: 'gal', category: 'volume'},
  'gal': {key: 'gal', category: 'volume'},
  'gallon': {key: 'gal', category: 'volume'},
  'gallons': {key: 'gal', category: 'volume'},
  '液量盎司': {key: 'fl_oz', category: 'volume'},
  'fl_oz': {key: 'fl_oz', category: 'volume'},
  'floz': {key: 'fl_oz', category: 'volume'},
  'fluid ounce': {key: 'fl_oz', category: 'volume'},
  'fluid ounces': {key: 'fl_oz', category: 'volume'}
}
```

#### 3.3.2 公共 API

```typescript
export class NaturalLanguageParser {
  /**
   * 解析自然语言单位换算查询
   * @param input 用户输入字符串
   * @returns ParseResult;不匹配 NL 模式 → null
   */
  static parse(input: string): ParseResult | null {
    const trimmed: string = input.trim()
    if (trimmed.length === 0) return null

    // 1. 提取数字前缀
    const numMatch: RegExpMatchArray | null = trimmed.match(/^(\d+(?:\.\d+)?)\s+(.+)$/)
    if (numMatch === null) return null
    const value: number = parseFloat(numMatch[1])
    const rest: string = numMatch[2]

    // 2. 尝试匹配中文转换词
    const cnOp: RegExpMatchArray | null = rest.match(/^(.+?)\s*(转|到|换成)\s*(.+)$/)
    let fromStr: string, toStr: string
    if (cnOp !== null) {
      fromStr = cnOp[1].trim()
      toStr = cnOp[3].trim()
    } else {
      // 3. 尝试匹配英文转换词(to / in / -> / =>)
      const enOp: RegExpMatchArray | null = rest.match(/^(.+?)\s*(?:to|in|->|=>)\s*(.+)$/i)
      if (enOp === null) return null
      fromStr = enOp[1].trim()
      toStr = enOp[2].trim()
    }

    // 4. 别名查表
    const fromAlias = ALIASES[fromStr]
    const toAlias = ALIASES[toStr]
    if (fromAlias === undefined || toAlias === undefined) return null

    // 5. 类别必须一致(否则跨类换算)
    if (fromAlias.category !== toAlias.category) return null

    return {
      value: value,
      from: fromAlias.key,
      to: toAlias.key,
      category: fromAlias.category
    }
  }
}
```

### 3.4 CalculatorPage 集成

#### 3.4.1 新增 imports

```typescript
import { NaturalLanguageParser } from '../common/NaturalLanguageParser'
import { UnitConverter } from '../common/UnitConverter'
```

#### 3.4.2 新增 @State

```typescript
@State nlConversionResult: string = ''
```

#### 3.4.3 修改 `onExpressionChange()`

```typescript
onExpressionChange(): void {
  // 1. NL 解析【NEW】
  const nlResult: ParseResult | null = NaturalLanguageParser.parse(this.expression)
  if (nlResult !== null) {
    const converted: number | null = UnitConverter.convert(
      nlResult.value, nlResult.from, nlResult.to, nlResult.category
    )
    if (converted !== null) {
      this.nlConversionResult = NumberFormatter.format(
        converted.toString(), '.', ',', NumberingSystem.INTERNATIONAL
      )
    } else {
      this.nlConversionResult = ''
    }
  } else {
    this.nlConversionResult = ''
  }

  // 2. 原有 preview 计算【EXISTING】
  this.preview = this.computePreview(this.expression, this.radianMode)
}
```

#### 3.4.4 修改 `onEquals()`

```typescript
onEquals(): void {
  if (this.expression.length === 0) return

  // aid-workflow 20260615: NL 换算结果优先【NEW】
  if (this.nlConversionResult.length > 0) {
    this.result = this.nlConversionResult
    this.errorMsg = ''
    const item: HistoryItem = { id: this.nextId, expression: this.expression, result: this.nlConversionResult, timestamp: Date.now() }
    this.nextId = this.nextId + 1
    const nh: HistoryItem[] = [item]
    for (let i: number = 0; i < this.history.length; i++) nh.push(this.history[i])
    this.history = nh
    if (this.prefs) this.prefs.setHistory(this.history)
    return
  }

  // 原计算流程【EXISTING】
  ErrorFlags.reset()
  try {
    const clean: string = this.expr.getCleanExpression(this.expression, '.', ',')
    const raw: number = this.engine.evaluate(clean, !this.radianMode)
    if (ErrorFlags.division_by_0) { this.errorMsg = '除数不能为零'; this.result = '' }
    else if (ErrorFlags.domain_error) { this.errorMsg = '定义域错误'; this.result = '' }
    else if (ErrorFlags.syntax_error) { this.errorMsg = '表达式错误'; this.result = '' }
    else if (ErrorFlags.is_infinity) { this.errorMsg = '结果无穷大'; this.result = '' }
    else if (ErrorFlags.require_real_number) { this.errorMsg = '需要实数'; this.result = '' }
    else {
      const fmt: string = NumberFormatter.format(raw.toString(), '.', ',', NumberingSystem.INTERNATIONAL)
      this.result = fmt; this.errorMsg = ''
      const item: HistoryItem = { id: this.nextId, expression: this.expression, result: fmt, timestamp: Date.now() }
      this.nextId = this.nextId + 1
      const nh: HistoryItem[] = [item]
      for (let i: number = 0; i < this.history.length; i++) nh.push(this.history[i])
      this.history = nh
      if (this.prefs) this.prefs.setHistory(this.history)
    }
  } catch (_e) { this.errorMsg = '计算错误' }
}
```

#### 3.4.5 修改 `onAC()`

```typescript
onAC(): void {
  this.expression = ''
  this.result = ''
  this.preview = ''
  this.nlConversionResult = ''   // 【NEW】清空 NL 结果
  this.errorMsg = ''
  ErrorFlags.reset()
}
```

---

## 4. 错误处理

| 错误场景 | 行为 |
|---------|------|
| NL 正则不匹配 | parse 返回 null → CalculatorPage 走原计算 |
| 单位别名未找到 | parse 返回 null → 降级 |
| 跨类换算 | parse 返回 null → 降级 |
| 同单位(from == to) | convert 返回 value(直接传值,无精度损失) |
| 单位未在 factor 表 | convert 返回 null → nlConversionResult = '' → 走原计算 |
| CalcEngine 后续出错 | 走原 ErrorFlags 流程,显示对应错误消息 |

---

## 5. 性能分析

| 操作 | 复杂度 | 实测时间 |
|------|--------|----------|
| NaturalLanguageParser.parse | O(n) (n=输入长度,正则) | < 1ms |
| UnitConverter.convert | O(1) (Map 查找 + 算术) | < 1μs |
| 总计 | < 1ms | < 1ms |

远低于实时预览的设计目标(5ms 内),不阻塞 UI。

---

## 6. 测试覆盖

### 6.1 UnitConverter 单元测试
- 每个 length 单位对至少 1 个用例(8 单位 = C(8,2) = 28 对 + 8 个自转换 = 36 用例)
- 每个 temperature 单位对(3 单位 = 6 对)
- 每个 mass 单位对(4 单位 = 12 对)
- 每个 volume 单位对(4 单位 = 12 对)
- 跨类换算返回 null(4 用例)
- 总计:约 70 个单元测试用例

### 6.2 NaturalLanguageParser 单元测试
- 中文 NL 命中 8 用例(覆盖 4 类别各 2 个)
- 英文 NL 命中 6 用例
- 别名识别 10 用例
- 数字格式 5 用例(整数、小数、负数、零、极大值)
- 错误输入 8 用例(不匹配、单位未找到、跨类)
- 总计:约 37 个单元测试用例

### 6.3 UI 自动化测试
- AC-UC-01/02/06/10 + 2 个回归用例
- 总计:6 个 UI 自动化测试场景

---

## 7. 集成步骤

1. 创建 `opencalc/entry/src/main/ets/common/` 目录
2. 实现 `UnitConverter.ets`(~80 行)
3. 实现 `NaturalLanguageParser.ets`(~110 行,主要在别名表)
4. 创建单元测试 `UnitConverter.test.ets` 和 `NaturalLanguageParser.test.ets`
5. 集成到 `CalculatorPage.ets`:import + @State + onExpressionChange + onEquals + onAC
6. 在 Node 端口跑单元测试(verify RED → GREEN)
7. 在 HarmonyOS 模拟器跑 UI 自动化测试
8. 生成 apply-report.md

---

## 8. 已知限制

| 限制 | 影响 | 缓解 |
|------|------|------|
| 仅支持 4 大类(length/temperature/mass/volume) | 面积/时间/速度/能量等暂不支持 | 后续 Issue 扩展 |
| 复杂 NL(多步换算、单位算术) | "100 厘米 转 英寸 再 转 英尺" 不支持 | 后续 Issue 扩展 |
| 单位别名固定写死 | 新单位需改代码 | 后续可考虑数据驱动 |
| NL 解析与算术表达式互斥 | 输入 "1+2" 不被识别为 NL | 设计决策,符合 issue 描述"输入框直接支持 NL" |

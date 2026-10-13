# Issue #18 单位换算 - 组件设计 (delta-design)

## 1. 概述

- **设计范围**：新增 `UnitConverter` + `NaturalLanguageParser` 两个纯函数模块，修改 `CalculatorPage.onEquals` 增加 NL 分支
- **设计原则**：
  - 解析与换算严格分层（parser 不查单位表，converter 不解析字符串）
  - 单位表声明式（Map + 简单函数），新增维度零算法改动
  - 错误隔离：NL 路径失败不污染 CalcEngine 路径
- **架构影响**：**无架构变更**（不创建新 layer，仅在 common/ 下新增工具类）

## 2. 模块设计

### 2.1 NaturalLanguageParser（新增）

**位置**：`opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets`

**职责**：识别输入字符串是否为 NL 单位换算模式，抽取 value/from/to 三元组

**公开 API**：
```ts
export interface NLParseResult {
  isUnitConversion: boolean
  value: number
  fromUnit: string
  toUnit: string
}

export class NaturalLanguageParser {
  // 输入：原始 expression 字符串
  // 输出：null = 不是 NL；NLParseResult = 识别成功
  public static parse(input: string): NLParseResult | null
}
```

**算法**：
1. `input.trim()` 后检查是否含分隔关键字（`转` / `to` / `in` / `为` / `→`）
2. 用第一个匹配的关键字 split 为 [head, tail] 两部分
3. head 必须是 `\d+(\.\d+)?`（科学计数法可选支持）
4. tail 去掉前后空白
5. tail 中含第二个关键字（同一关键字）时，按第二关键字 split 出 from / to
6. tail 中无第二关键字时，按 `\s+`（空白）或**位置优先级**（已知单位 token 表）切分
7. 若 head 数字合法且 from/to 都非空 → 返回 NLParseResult
8. 否则返回 null

**支持的格式**（按优先级）：
- `X+空格+单位1+空格+keyword+空格+单位2`（含空格）
- `X+单位1+keyword+单位2`（紧凑无空格）
- `X+keyword+单位1+keyword+单位2`（双 keyword）

**测试用例**：
```
"100厘米转英寸"  → {isUnitConversion:true, value:100, fromUnit:'厘米', toUnit:'英寸'}
"30摄氏度转华氏度" → ...
"5ft in cm"      → {value:5, fromUnit:'ft', toUnit:'cm'}
"5 m to ft"      → ...
"1+2"           → null
"sin(0)"        → null
"5米转千克"      → {value:5, fromUnit:'米', toUnit:'千克'}  ← 错误留给 converter
"5xyz转米"      → {value:5, fromUnit:'xyz', toUnit:'米'}   ← 错误留给 converter
```

### 2.2 UnitConverter（新增）

**位置**：`opencalc/entry/src/main/ets/common/UnitConverter.ets`

**职责**：维护维度表 + 基准单位换算函数

**数据模型**：
```ts
interface UnitDef {
  dimension: string           // 'length' | 'mass' | 'temperature' | 'time'
  aliases: string[]           // ['米', 'm', 'meter']
  toBase: (v: number) => number
  fromBase: (v: number) => number
}
```

**单位表**（声明式，私有 const）：
```ts
// 长度 (base: m)
{ dim:'length', a:['毫米','mm'], toBase: v=>v/1000, fromBase: v=>v*1000 }
{ dim:'length', a:['厘米','cm'], toBase: v=>v/100,  fromBase: v=>v*100 }
{ dim:'length', a:['分米','dm'], toBase: v=>v/10,   fromBase: v=>v*10 }
{ dim:'length', a:['米','m'],    toBase: v=>v,      fromBase: v=>v }
{ dim:'length', a:['千米','km'], toBase: v=>v*1000, fromBase: v=>v/1000 }
{ dim:'length', a:['英寸','in'], toBase: v=>v*0.0254, fromBase: v=>v/0.0254 }
{ dim:'length', a:['英尺','ft'], toBase: v=>v*0.3048, fromBase: v=>v/0.3048 }
{ dim:'length', a:['码','yd'],   toBase: v=>v*0.9144, fromBase: v=>v/0.9144 }
{ dim:'length', a:['英里','mi'],toBase: v=>v*1609.344, fromBase: v=>v/1609.344 }

// 质量 (base: g)
{ dim:'mass', a:['毫克','mg'], toBase: v=>v/1000, fromBase: v=>v*1000 }
{ dim:'mass', a:['克','g'],    toBase: v=>v,      fromBase: v=>v }
{ dim:'mass', a:['千克','kg'], toBase: v=>v*1000, fromBase: v=>v/1000 }
{ dim:'mass', a:['吨','t'],    toBase: v=>v*1e6,  fromBase: v=>v/1e6 }
{ dim:'mass', a:['磅','lb'],   toBase: v=>v*453.592, fromBase: v=>v/453.592 }
{ dim:'mass', a:['盎司','oz'], toBase: v=>v*28.3495, fromBase: v=>v/28.3495 }

// 时间 (base: s)
{ dim:'time', a:['秒','s'],   toBase: v=>v,        fromBase: v=>v }
{ dim:'time', a:['分钟','min'],toBase: v=>v*60,    fromBase: v=>v/60 }
{ dim:'time', a:['小时','h'], toBase: v=>v*3600,   fromBase: v=>v/3600 }
{ dim:'time', a:['天','day','d'], toBase: v=>v*86400, fromBase: v=>v/86400 }

// 温度 (base: K) — 特殊 affine
{ dim:'temperature', a:['摄氏度','°C','C'], toBase: v=>v+273.15, fromBase: v=>v-273.15 }
{ dim:'temperature', a:['华氏度','°F','F'], toBase: v=>(v-32)*5/9+273.15, fromBase: v=>(v-273.15)*9/5+32 }
{ dim:'temperature', a:['开尔文','K'],      toBase: v=>v,                 fromBase: v=>v }
```

**公开 API**：
```ts
export class UnitConverter {
  public static convert(value: number, from: string, to: string): number
  // 成功 → 换算后数值
  // 失败（跨维度 / 未知单位）→ NaN（调用方需检查 isNaN）
  
  public static listDimensions(): string[]
  public static listUnits(dimension: string): string[]
}
```

**算法**（convert）：
1. 遍历单位表，按 alias 找 `from` → 得到 fromDef
2. 遍历单位表，按 alias 找 `to` → 得到 toDef
3. 任一找不到 → 返回 NaN
4. 维度不匹配 → 返回 NaN
5. 维度为 'temperature' → 走 affine 公式（直接 toBase→fromBase）
6. 其他维度 → `fromDef.fromBase(toDef.toBase(value))`

**别名匹配策略**：
- 精确匹配（case-sensitive）
- 别名去前后空白
- 不做模糊匹配（"centermeter" 不会被识别成"厘米"）

### 2.3 CalculatorPage 改造

**位置**：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`

**改动点**：
1. 顶部 `import` 增加：
   ```ts
   import { NaturalLanguageParser } from '../common/NaturalLanguageParser'
   import { UnitConverter } from '../common/UnitConverter'
   ```
2. 新增私有方法 `tryUnitConversion(expr: string): { ok: boolean, value: number, error?: string }`：
   - 调 `NaturalLanguageParser.parse(expr)`，null → `{ok:false}`
   - 调 `UnitConverter.convert(...)`，NaN → `{ok:false, error:'单位不匹配或未知单位'}`
   - 成功 → `{ok:true, value:r}`
3. 修改 `onEquals`：
   ```ts
   onEquals(): void {
     if (this.expression.length === 0) return
     ErrorFlags.reset()
     // === 新增 NL 优先分支 ===
     const uc = this.tryUnitConversion(this.expression)
     if (uc.ok) {
       const fmt: string = NumberFormatter.format(uc.value.toString(), '.', ',', NumberingSystem.INTERNATIONAL)
       this.result = fmt
       this.errorMsg = ''
       // 写入历史
       const item: HistoryItem = { id: this.nextId, expression: this.expression, result: fmt, timestamp: Date.now() }
       this.nextId = this.nextId + 1
       const nh: HistoryItem[] = [item]
       for (let i: number = 0; i < this.history.length; i++) nh.push(this.history[i])
       this.history = nh
       if (this.prefs) this.prefs.setHistory(this.history)
       return
     }
     // === NL 失败但 parser 仍识别为换算 → 直接报错，不走 CalcEngine ===
     if (uc.error !== undefined) {
       this.errorMsg = uc.error
       this.result = ''
       return
     }
     // === 原有 CalcEngine 路径 ===
     try {
       const clean: string = this.expr.getCleanExpression(this.expression, '.', ',')
       const raw: number = this.engine.evaluate(clean, !this.radianMode)
       ... // 原逻辑不变
     } catch (_e) { this.errorMsg = '计算错误' }
   }
   ```

**computePreview 不动**（预览只针对 CalcEngine 路径，NL 换算等号才出结果）

## 3. 数据流

```
用户键入 "100厘米转英寸"
   ↓ CalculatorPage.onEquals
   ↓ NaturalLanguageParser.parse → {value:100, from:'厘米', to:'英寸'}
   ↓ UnitConverter.convert(100,'厘米','英寸') → 39.3700787
   ↓ NumberFormatter.format → "39.3701"
   ↓ result = "39.3701" + history.push
```

```
用户键入 "5米转千克"
   ↓ NL parse → {value:5, from:'米', to:'千克'}
   ↓ UnitConverter.convert → NaN (length vs mass)
   ↓ errorMsg = "单位不匹配"
```

```
用户键入 "1+2"
   ↓ NL parse → null
   ↓ 走原 CalcEngine
   ↓ result = "3"
```

## 4. 测试设计

### 4.1 单元测试文件

**UnitConverter.test.ets**：
```ts
// 长度
assertEqual(100, UnitConverter.convert(1, '米', '厘米'))         // 100
assertApprox(39.3701, UnitConverter.convert(100, '厘米', '英寸'), 1e-4)
assertApprox(0.621371, UnitConverter.convert(1, '千米', '英里'), 1e-4)
// 质量
assertEqual(1000, UnitConverter.convert(1, '千克', '克'))
assertApprox(2.20462, UnitConverter.convert(1, '千克', '磅'), 1e-4)
// 时间
assertEqual(3600, UnitConverter.convert(1, '小时', '秒'))
assertEqual(24, UnitConverter.convert(1, '天', '小时'))
// 温度
assertEqual(86, UnitConverter.convert(30, '摄氏度', '华氏度'))
assertEqual(0, UnitConverter.convert(32, '华氏度', '摄氏度'))
assertEqual(273.15, UnitConverter.convert(0, '摄氏度', '开尔文'))
// 错误
assertNaN(UnitConverter.convert(1, '米', '千克'))      // 跨维度
assertNaN(UnitConverter.convert(1, '米', 'xyz'))      // 未知单位
```

**NaturalLanguageParser.test.ets**：
```ts
const r1 = NaturalLanguageParser.parse('100厘米转英寸')
assertTrue(r1 != null && r1.value === 100 && r1.fromUnit === '厘米' && r1.toUnit === '英寸')

const r2 = NaturalLanguageParser.parse('30摄氏度转华氏度')
assertTrue(r2.value === 30 && r2.fromUnit === '摄氏度' && r2.toUnit === '华氏度')

const r3 = NaturalLanguageParser.parse('5ft in cm')
assertTrue(r3.value === 5 && r3.fromUnit === 'ft' && r3.toUnit === 'cm')

const r4 = NaturalLanguageParser.parse('5 m to ft')
assertTrue(r4 != null && r4.value === 5)

assertNull(NaturalLanguageParser.parse('1+2'))      // 表达式
assertNull(NaturalLanguageParser.parse('sin(0)'))   // 表达式
assertNull(NaturalLanguageParser.parse(''))         // 空
```

### 4.2 UI 自动化测试（可选,harmonyos-ui-test skill）

场景 1：成功换算
```
1. hdc shell aa start -b com.darkempire78.opencalculator
2. uitest uiInput text "100厘米转英寸"
3. uitest uiInput key 61    (回车/等号)
4. 读取 result Text 控件 → 断言 ≈ "39.3701"
```

场景 2：跨维度
```
1. uitest uiInput text "5米转千克"
2. uitest uiInput key 61
3. 读取 errorMsg Text 控件 → 断言 ≈ "单位不匹配"
```

## 5. 错误处理

| 失败点 | 处理 | 用户感知 |
|--------|------|---------|
| NL parse 抛异常 | 内部 try-catch，返回 null | 走 CalcEngine 降级 |
| 单位 alias 未找到 | convert 返回 NaN | errorMsg = "未知单位" |
| 跨维度 | convert 返回 NaN | errorMsg = "单位不匹配" |
| CalcEngine 路径原有错误 | 不变 | 不变 |

## 6. 兼容性

- **向前兼容**：所有原有计算路径（CalcEngine）行为不变
- **API 稳定**：UnitConverter / NaturalLanguageParser 公开 API 仅为 static 方法，无状态
- **i18n**：MVP 支持中英（厘米/cm 互译），全语种不在 MVP

## 7. 实施顺序

1. RED：写 UnitConverter.test.ets + NaturalLanguageParser.test.ets（断言失败）
2. GREEN：实现两个 .ets 模块
3. RED：写 CalculatorPage.test.ets 集成测试（如果框架支持）或记录阻塞
4. GREEN：修改 CalculatorPage.onEquals
5. 编译：`hvigorw --no-daemon assembleHap`
6. 单元测试：`hvigorw --no-daemon test`
7. UI 自动化：harmonyos-ui-test（如果 hdc 可用）
8. 提交 + push

## 8. 复杂度评估

- **等级**：M（参考 PLANNING step6）
- **影响模块数**：3（新增 common/ 下 2 文件 + 修改 pages/CalculatorPage.ets）
- **架构变更**：否
- **数据模型变更**：是（新增 UnitDef 常量表，不修改现有数据模型）
- **可跳过制品**：new-arch.md（无架构变更）

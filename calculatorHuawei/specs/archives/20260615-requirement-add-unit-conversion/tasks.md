# IMPLEMENTING — Issue #14 单位换算功能

> aid-workflow 20260615-requirement-add-unit-conversion · IMPLEMENTING 阶段任务分解
> 基线:proposal.md / delta-spec.md / info.md / design.md
> 强制约束:TDD RED-GREEN-REFACTOR + 真实跑测(铁律 7)

---

## 任务总览

| ID | 阶段 | 任务 | 估时 | 状态 |
|----|------|------|------|------|
| T1 | RED | 创建 Node 端口 `UnitConverter.port.mjs` + `UnitConverter.test.mjs`,写 50+ 失败用例 | 25min | ⏳ |
| T2 | RED | 跑 `node --test` 确认用例 RED(全部失败) | 2min | ⏳ |
| T3 | GREEN | 在 `opencalc/entry/src/main/ets/common/UnitConverter.ets` 实现 convert/convertTemperature | 15min | ⏳ |
| T4 | RED | 创建 Node 端口 `NaturalLanguageParser.port.mjs` + `NaturalLanguageParser.test.mjs`,写 30+ 失败用例 | 20min | ⏳ |
| T5 | RED | 跑 `node --test` 确认 NL 解析 RED | 2min | ⏳ |
| T6 | GREEN | 在 `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets` 实现 parse + 别名表 | 25min | ⏳ |
| T7 | GREEN | 跑 `node --test` 确认 UnitConverter + NL 解析全 GREEN | 2min | ⏳ |
| T8 | GREEN | 在 `CalculatorPage.ets` 集成:import + @State nlConversionResult + 修改 onExpressionChange/onEquals/onAC | 15min | ⏳ |
| T9 | GREEN | 跑 Node 端口回归测试(不破坏现有 preview/百分号) | 2min | ⏳ |
| T10 | GREEN | 真实跑 hvigorw test(或 Node 端口代替) | 5min | ⏳ |
| T11 | UI TEST | 在 HarmonyOS 模拟器跑 harmonyos-ui-test,产出 截图+dump+results.json | 30min | ⏳ |
| T12 | REFACTOR | 提取常量(ALIASES_MAP、FACTOR_KEYS)+ JSDoc 注释 | 10min | ⏳ |
| T13 | REFACTOR | 跑 `node --test` 确认 GREEN 仍稳定 | 2min | ⏳ |
| T14 | VERIFY | git diff --stat + git status | 2min | ⏳ |
| T15 | DOC | 生成 `apply-report.md`(TDD 证据、AC 矩阵、diff stat、UI 结果) | 15min | ⏳ |
| T16 | DOC | 补 `todo.md`(本任务的阶段状态、决策点) | 5min | ⏳ |
| T17 | COMMIT | git add + git commit -s --signoff(每个 AID 文档 + 代码 + 测试分多个 commit) | 5min | ⏳ |
| T18 | PUSH | git push --force-with-lease origin feat/issue-14-中等模糊 | 1min | ⏳ |

**总耗时估算**:~180 分钟(~3 小时)

---

## T1 — RED:UnitConverter 失败测试(Node 端口)

### T1.1 创建 `tests/UnitConverter.port.mjs`

```javascript
// specs/changes/20260615-requirement-add-unit-conversion/tests/UnitConverter.port.mjs
// 1:1 端口:与 ArkTS UnitConverter.ets 一一对应
// RED 阶段:先放空实现(返回 null),让测试失败

class UnitConverter {
  static convert(value, from, to, category) { return null }
  static convertTemperature(value, from, to) { return null }
  static getFactors(category) { return null }
}

export { UnitConverter }
```

### T1.2 创建 `tests/UnitConverter.test.mjs`

写 50+ 用例(每个支持单位对至少 1 个):

**Length 类别(8 单位)**:
- TC-UC-L01: 100 cm → inch ≈ 39.3700787
- TC-UC-L02: 1 km → mi ≈ 0.621371192
- TC-UC-L03: 1 mi → km = 1.609344
- TC-UC-L04: 1 m → cm = 100
- TC-UC-L05: 1 m → mm = 1000
- TC-UC-L06: 1 ft → m = 0.3048
- TC-UC-L07: 1 yd → m = 0.9144
- TC-UC-L08: 1 inch → mm = 25.4
- TC-UC-L09: 0 m → cm = 0
- TC-UC-L10: 1 m → m = 1(自转换)
- TC-UC-L11: 1 mile → ft = 5280
- TC-UC-L12: 1000 mm → m = 1

**Temperature 类别(3 单位)**:
- TC-UC-T01: 0°C → K = 273.15
- TC-UC-T02: 0°C → °F = 32
- TC-UC-T03: 100°C → °F = 212
- TC-UC-T04: 32°F → °C = 0
- TC-UC-T05: 100°F → °C ≈ 37.7777777
- TC-UC-T06: 273.15 K → °C = 0
- TC-UC-T07: -40°C → °F = -40(著名恒等式)
- TC-UC-T08: 0 K → °C = -273.15(绝对零度)

**Mass 类别(4 单位)**:
- TC-UC-M01: 1 kg → g = 1000
- TC-UC-M02: 1 lb → kg ≈ 0.45359237
- TC-UC-M03: 5 lb → kg ≈ 2.26796185
- TC-UC-M04: 16 oz → lb = 1
- TC-UC-M05: 1 kg → oz ≈ 35.27396
- TC-UC-M06: 1 g → mg(无 mg 单位,应返回 null)
- TC-UC-M07: 1 kg → kg = 1(自转换)

**Volume 类别(4 单位)**:
- TC-UC-V01: 1 L → mL = 1000
- TC-UC-V02: 1 gal → L ≈ 3.785411784
- TC-UC-V03: 128 fl_oz → gal = 1
- TC-UC-V04: 1000 mL → L = 1
- TC-UC-V05: 1 L → fl_oz ≈ 33.814
- TC-UC-V06: 1 L → L = 1(自转换)

**跨类 / 错误**:
- TC-UC-ERR01: 1 m → kg → null(跨类)
- TC-UC-ERR02: 1 C → cm → null(跨类)
- TC-UC-ERR03: 1 m → xyz → null(单位未注册)
- TC-UC-ERR04: 1 xyz → m → null(单位未注册)
- TC-UC-ERR05: convert(1, 'm', 'kg', 'invalid') → null(类别无效)

**总计**:约 38 个测试用例(TC-UC-L01 ~ L12 + T01 ~ T08 + M01 ~ M07 + V01 ~ V06 + ERR01 ~ ERR05 = 12+8+7+6+5 = 38)

### T1.3 容差
- 使用 `Math.abs(got - expected) < 1e-6` 验证

### T1.4 RED 输出预期
- 跑 `node --test tests/UnitConverter.test.mjs`
- 38 用例全部 FAIL(因为 stub 返回 null)
- 至少 1 个用例通过(无,因 stub 总是返回 null)

---

## T2 — RED:跑 `node --test` 确认 RED

```bash
cd specs/changes/20260615-requirement-add-unit-conversion/tests
node --test UnitConverter.test.mjs 2>&1 | tee test-output-red.txt
```

**预期**:
- ℹ tests 38
- ℹ pass 0
- ℹ fail 38

将输出保存为 `test-output-red.txt`,作为 RED 证据。

---

## T3 — GREEN:实现 UnitConverter.ets

### T3.1 新建 `opencalc/entry/src/main/ets/common/UnitConverter.ets`

```typescript
// opencalc/entry/src/main/ets/common/UnitConverter.ets
// aid-workflow 20260615: Issue #14 单位换算核心
// 支持 length / temperature / mass / volume 4 大类,共 19 个基准单位

const CATEGORY_LENGTH = 'length'
const CATEGORY_TEMPERATURE = 'temperature'
const CATEGORY_MASS = 'mass'
const CATEGORY_VOLUME = 'volume'

// 长度:以"米"为基准的换算因子(1 单位 = ? 米)
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

export class UnitConverter {
  /**
   * aid-workflow 20260615: 单位换算
   * @param value 输入数值
   * @param from 源单位 canonical key(如 "cm" / "C" / "kg" / "L")
   * @param to 目标单位 canonical key
   * @param category 单位类别("length" | "temperature" | "mass" | "volume")
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
   * aid-workflow 20260615: 温度换算(非线性,通过摄氏度中转)
   */
  private static convertTemperature(value: number, from: string, to: string): number | null {
    let celsius: number
    if (from === 'C') celsius = value
    else if (from === 'F') celsius = (value - 32) * 5 / 9
    else if (from === 'K') celsius = value - 273.15
    else return null

    if (to === 'C') return celsius
    if (to === 'F') return celsius * 9 / 5 + 32
    if (to === 'K') return celsius + 273.15
    return null
  }

  /**
   * aid-workflow 20260615: 获取类别对应的换算因子表
   */
  private static getFactors(category: string): Record<string, number> | null {
    if (category === CATEGORY_LENGTH) return LENGTH_FACTORS
    if (category === CATEGORY_MASS) return MASS_FACTORS
    if (category === CATEGORY_VOLUME) return VOLUME_FACTORS
    return null
  }
}
```

### T3.2 GREEN 验证
跑 `node --test tests/UnitConverter.test.mjs`:
- 38/38 PASS

---

## T4 — RED:NaturalLanguageParser 失败测试

### T4.1 创建 `tests/NaturalLanguageParser.port.mjs`

```javascript
// specs/changes/20260615-requirement-add-unit-conversion/tests/NaturalLanguageParser.port.mjs
// 1:1 端口:与 ArkTS NaturalLanguageParser.ets 一一对应
// RED 阶段:stub 返回 null

class NaturalLanguageParser {
  static parse(input) { return null }
}

export { NaturalLanguageParser }
```

### T4.2 创建 `tests/NaturalLanguageParser.test.mjs`

写 30+ 用例:

**中文 NL 命中**:
- TC-NL-CN-L01: "100厘米转英寸" → {value:100, from:'cm', to:'inch', category:'length'}
- TC-NL-CN-L02: "1英里转千米" → {value:1, from:'mi', to:'km', category:'length'}
- TC-NL-CN-T01: "30摄氏度转华氏度" → {value:30, from:'C', to:'F', category:'temperature'}
- TC-NL-CN-T02: "0摄氏度转开尔文" → {value:0, from:'C', to:'K', category:'temperature'}
- TC-NL-CN-M01: "5磅转千克" → {value:5, from:'lb', to:'kg', category:'mass'}
- TC-NL-CN-M02: "1公斤转克" → {value:1, from:'kg', to:'g', category:'mass'}
- TC-NL-CN-V01: "1加仑转升" → {value:1, from:'gal', to:'L', category:'volume'}
- TC-NL-CN-V02: "1000毫升转升" → {value:1000, from:'mL', to:'L', category:'volume'}

**英文 NL 命中**:
- TC-NL-EN-L01: "100cm to inch" → {value:100, from:'cm', to:'inch', category:'length'}
- TC-NL-EN-L02: "1 mile in km" → {value:1, from:'mi', to:'km', category:'length'}
- TC-NL-EN-T01: "100F to C" → {value:100, from:'F', to:'C', category:'temperature'}
- TC-NL-EN-M01: "1 kg to g" → {value:1, from:'kg', to:'g', category:'mass'}
- TC-NL-EN-V01: "128 fl oz to gal" → {value:128, from:'fl_oz', to:'gal', category:'volume'}
- TC-NL-EN-V02: "1L->mL" → {value:1, from:'L', to:'mL', category:'volume'}

**别名识别**:
- TC-NL-AL-L01: "100公分转英寸" → cm(别名"公分")
- TC-NL-AL-L02: "1公里转英里" → km(别名"公里")
- TC-NL-AL-L03: "1公尺转米" → m(别名"公尺")
- TC-NL-AL-L04: "1尺转英尺" → ft(别名"尺")
- TC-NL-AL-L05: "1哩转英里" → mi(别名"哩")
- TC-NL-AL-T01: "100华氏转摄氏" → F(别名"华氏")
- TC-NL-AL-M01: "1公斤转克" → kg(别名"公斤")
- TC-NL-AL-V01: "1公升转毫升" → L(别名"公升")

**数字格式**:
- TC-NL-NUM-01: "0.5公里转米" → value:0.5
- TC-NL-NUM-02: "1 转 1"(无单位) → null
- TC-NL-NUM-03: "100.5厘米转英寸" → value:100.5
- TC-NL-NUM-04: ".5厘米转英寸"(无整数部分) → null
- TC-NL-NUM-05: "0厘米转英寸" → value:0

**错误输入**:
- TC-NL-ERR-01: "1米转千克" → null(跨类)
- TC-NL-ERR-02: "abc 厘米 转 英寸" → null(无数字)
- TC-NL-ERR-03: "1 未知单位 转 米" → null(别名未找到)
- TC-NL-ERR-04: "100cm" → null(无转换词)
- TC-NL-ERR-05: "1+2" → null(普通表达式)
- TC-NL-ERR-06: "" → null(空字符串)
- TC-NL-ERR-07: "  " → null(纯空格)
- TC-NL-ERR-08: "1米→千克"(中文箭头) → 看实现;若支持则 PASS,否则 null(用 -> 替代)

**总计**:约 32 个测试用例

### T4.3 RED 验证
```bash
node --test tests/NaturalLanguageParser.test.mjs 2>&1 | tee test-output-nl-red.txt
```
- 32/32 FAIL

---

## T5 — RED:跑 `node --test` 确认 NL 解析 RED

(同 T4 步骤,记录输出)

---

## T6 — GREEN:实现 NaturalLanguageParser.ets

### T6.1 新建 `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets`

```typescript
// opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets
// aid-workflow 20260615: Issue #14 自然语言单位换算查询解析
// 支持中文/英文 NL 模式,识别 ~20 个单位别名

interface ParseResult {
  value: number
  from: string
  to: string
  category: string
}

// 别名表:用户输入 → canonical key + category
const ALIASES: Record<string, {key: string, category: string}> = {
  // length
  '米': {key: 'm', category: 'length'},
  '公尺': {key: 'm', category: 'length'},
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
  'millimeter': {key: 'mm', category: 'length'},
  'millimeters': {key: 'mm', category: 'length'},
  '千米': {key: 'km', category: 'length'},
  '公里': {key: 'km', category: 'km'},
  'km': {key: 'km', category: 'length'},
  'kilometer': {key: 'km', category: 'length'},
  'kilometers': {key: 'km', category: 'length'},
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

export class NaturalLanguageParser {
  /**
   * aid-workflow 20260615: 解析自然语言单位换算查询
   * @param input 用户输入字符串
   * @returns ParseResult {value, from, to, category};不匹配 NL 模式 → null
   */
  static parse(input: string): ParseResult | null {
    const trimmed: string = input.trim()
    if (trimmed.length === 0) return null

    // 1. 提取数字前缀(支持小数)
    const numMatch: RegExpMatchArray | null = trimmed.match(/^(\d+(?:\.\d+)?)\s+(.+)$/)
    if (numMatch === null) return null
    const value: number = parseFloat(numMatch[1])
    const rest: string = numMatch[2]

    // 2. 尝试中文转换词
    const cnOp: RegExpMatchArray | null = rest.match(/^(.+?)\s*(转|到|换成)\s*(.+)$/)
    let fromStr: string
    let toStr: string
    if (cnOp !== null) {
      fromStr = cnOp[1].trim()
      toStr = cnOp[3].trim()
    } else {
      // 3. 尝试英文转换词(to / in / -> / =>)
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

### T6.2 GREEN 验证
- 32/32 PASS

---

## T7 — GREEN:跑全部 Node 端口测试

```bash
cd specs/changes/20260615-requirement-add-unit-conversion/tests
node --test UnitConverter.test.mjs NaturalLanguageParser.test.mjs 2>&1 | tee test-output-green.txt
```

**预期**:
- UnitConverter: 38/38 PASS
- NaturalLanguageParser: 32/32 PASS
- 总计: 70/70 PASS

---

## T8 — GREEN:CalculatorPage 集成

### T8.1 新增 import

```typescript
// CalculatorPage.ets line 12 附近
import { NaturalLanguageParser, ParseResult } from '../common/NaturalLanguageParser'
import { UnitConverter } from '../common/UnitConverter'
```

### T8.2 新增 @State

```typescript
// CalculatorPage.ets @State 段(line 17 附近)
@State nlConversionResult: string = ''
```

### T8.3 修改 onExpressionChange()

在 `computePreview` 调用前插入 NL 解析逻辑(详见 design.md §3.4.3)。

### T8.4 修改 onEquals()

在 `ErrorFlags.reset()` 前插入 NL 优先级检查(详见 design.md §3.4.4)。

### T8.5 修改 onAC()

增 `this.nlConversionResult = ''`(详见 design.md §3.4.5)。

---

## T9 — GREEN:Node 端口回归测试

不写新测试,但跑 `tests/RealtimePreview.test.mjs` 验证不破坏 Issue #11 实时预览。

```bash
cd specs/changes/20260612-requirement-add-realtime-preview/tests
node --test RealtimePreview.test.mjs
```

**预期**:17/17 PASS(无回归)

---

## T10 — GREEN:真实跑 hvigorw test

按 capabilities.json 真实跑:
```bash
hvigorw --no-daemon test
```

**预期**:UnitConverter.test.ets + NaturalLanguageParser.test.ets 全部 PASS(若 hvigorw 不可用,降级为 Node 端口)

---

## T11 — UI TEST:harmonyos-ui-test

### T11.1 准备

```bash
hdc -s 127.0.0.1:5555 shell
# 安装最新 HAP
hdc -s 127.0.0.1:5555 install -r opencalc/build/default/outputs/default/entry-default-signed.hap
```

### T11.2 编写测试脚本 `ui-tests/run_ui_tests.py`

```python
# 6 个测试场景:
# 1. AC-UC-01: 输入"100厘米转英寸" → 截图 result=39.3700787
# 2. AC-UC-02: 输入"30摄氏度转华氏度" → 截图 result=86
# 3. AC-UC-06: 输入"100cm to inch" → 截图 result=39.3700787
# 4. AC-UC-09: 输入"1米转千克" → 截图 错误提示
# 5. AC-UC-10: 输入"1+2" → 截图 result=3(原计算,不触发 NL)
# 6. AC-UC-13: 输入"1 kg to g" → 截图 result=1000
```

### T11.3 产出物

```
ui-tests/
├── run_ui_tests.py
├── results.json
├── dump/
│   ├── 00_app_launched.json
│   ├── ac_uc_01_100cm_to_inch.json
│   ├── ac_uc_02_30c_to_f.json
│   ├── ...
└── screenshot/
    ├── 00_app_launched.png
    ├── ac_uc_01_100cm_to_inch.png
    └── ...
```

---

## T12 — REFACTOR:代码质量改进

- 提取常量:`CATEGORY_*` 移至 UnitConverter 顶部
- JSDoc 注释:每个 public method + 关键 helper
- 简化 `getFactors`:使用单一对象 + 类别作为 key

---

## T13 — REFACTOR:跑测试验证无回归

```bash
node --test tests/UnitConverter.test.mjs tests/NaturalLanguageParser.test.mjs
```

**预期**:70/70 PASS

---

## T14 — VERIFY:git diff 检查

```bash
git diff --stat
git status
```

**预期**:
- Modified: 0 files
- New: UnitConverter.ets, UnitConverter.test.ets, NaturalLanguageParser.ets, NaturalLanguageParser.test.ets, CalculatorPage.ets
- New: specs/changes/20260615-requirement-add-unit-conversion/* (AID 文档 + tests + ui-tests)

---

## T15 — DOC:apply-report.md

参考 issue-11 的 `apply-report.md` 格式,产出:
- 任务摘要
- TDD 红绿循环证据
- AC 验收矩阵(15 个 AC)
- 实际代码改动
- git diff --stat
- UI 自动化测试结果
- 已知限制
- 回归保护清单
- 状态总结

---

## T16 — DOC:todo.md

```markdown
# Issue #14 AID 任务状态

## 阶段
- PLANNING: ✅ DONE (2026-06-15)
- IMPLEMENTING: ✅ DONE (2026-06-15)
- APPLYING: ✅ DONE (2026-06-15)

## 用户确认点处理
- 阶段间确认:全部自动同意
- 编译环境检查:Node 24.16.0 可用;hvigorw 未在 PATH,降级为 Node 端口
- 高风险点:无
```

---

## T17 — COMMIT:git commit -s(分多个 commit)

```bash
# Commit 1: AID 文档
git add specs/changes/20260615-requirement-add-unit-conversion/{proposal,delta-spec,info,design}.md
git commit -s -m "docs(aid-planning): Issue #14 单位换算 AID 文档"

# Commit 2: TDD RED 测试
git add specs/changes/20260615-requirement-add-unit-conversion/tests/
git commit -s -m "test(issue-14): RED UnitConverter + NaturalLanguageParser 测试用例"

# Commit 3: GREEN 实现
git add opencalc/entry/src/main/ets/common/UnitConverter.ets opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets
git commit -s -m "feat(unit-conversion): 实现 UnitConverter + NaturalLanguageParser"

# Commit 4: CalculatorPage 集成
git add opencalc/entry/src/main/ets/pages/CalculatorPage.ets
git commit -s -m "feat(issue-14): CalculatorPage 集成 NL 解析层"

# Commit 5: UI 测试产物
git add specs/changes/20260615-requirement-add-unit-conversion/ui-tests/
git commit -s -m "test(issue-14): UI 自动化测试产物(截图+dump+results.json)"

# Commit 6: apply-report.md
git add specs/changes/20260615-requirement-add-unit-conversion/apply-report.md specs/changes/20260615-requirement-add-unit-conversion/todo.md
git commit -s -m "docs(issue-14): apply-report.md + todo.md"

# Commit 7: 修订 955eab5 的 signoff
git rebase --signoff HEAD~6  # 在 955eab5 上加 signoff
```

---

## T18 — PUSH:force-push

```bash
git push --force-with-lease origin feat/issue-14-中等模糊
```

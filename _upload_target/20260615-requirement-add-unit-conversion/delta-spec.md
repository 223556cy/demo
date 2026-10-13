# 需求SPEC v1.0 — Issue #14 单位换算功能(增量)

---

## 系统背景

### 目的

> 在 OpenCalc HarmonyOS 移植版的计算器主页面增加"单位换算"能力:用户在输入框中输入自然语言查询(如 "100厘米转英寸"、"30摄氏度转华氏度"),系统自动识别 NL 模式,直接给出换算结果,无需按等号。目标是让 OpenCalc 超越纯数学计算,覆盖日常生活与工程中常见的单位换算需求,提升用户黏性。

### 术语与缩写

| 术语/缩写 | 定义 |
| ----- | --- |
| 单位换算(Unit Conversion) | 将一种物理量单位的数值转换为另一种等价的数值(如 100 cm = 39.37 inch) |
| 自然语言(NL) | 中文/英文短句,如 "100 厘米 转 英寸"、"100cm to inch" |
| NL 模式 | 满足"数字 + 单位A + 转换词 + 单位B"模式的输入 |
| 单位类别(UnitCategory) | length / temperature / mass / volume 4 大类 |
| 转换词 | 中文:"转"、"到"、"换成" / 英文:"to"、"in"、"->"、"=>" |
| 降级(Fallback) | NL 解析失败时,降级为现有 CalcEngine 求值流程 |

---

## 系统上下文

### 目标系统

| 字段 | 内容 |
| ----------------- | --- |
| 系统名称 | OpenCalc HarmonyOS 移植版(计算器 App) |
| 系统边界说明 | 内部新增 UnitConverter + NaturalLanguageParser;UI 集成在 CalculatorPage.expression 输入层;复用现有 CalcEngine / NumberFormatter / ErrorFlags |

### 周边交互方清单

| 编号    | 外部系统名称 | 类型 | 交互接口类型 | 交互接口主要功能 |
| ----- | ------ | ------------------ | ------------------------------------ | -------- |
| ES-01 | 用户 | 人 | UI 触摸 | 在输入框输入 NL 查询或普通表达式 |
| ES-02 | NaturalLanguageParser | 内部模块 | ArkTS 类方法 | `parse(input): ParseResult \| null` |
| ES-03 | UnitConverter | 内部模块 | ArkTS 类方法 | `convert(value, from, to, category): number` |
| ES-04 | CalcEngine | 内部模块 | ArkTS 类方法 | 复用 evaluate(clean, radians) |
| ES-05 | NumberFormatter | 内部模块 | ArkTS 静态方法 | 复用 format(raw, dec, grp, sys) |

---

## 需求描述

| 需求编号 | 需求名称 | 需求描述 | 设计人员 |
| -------- | -------- | -------- | -------- |
| SR-UC-01 | 长度换算 | 支持米/厘米/毫米/千米/英寸/英尺/码/英里 8 个长度单位互转 | AID 自动化 |
| SR-UC-02 | 温度换算 | 支持摄氏度/华氏度/开尔文 3 个温度单位互转(含非线性转换) | AID 自动化 |
| SR-UC-03 | 质量换算 | 支持千克/克/磅/盎司 4 个质量单位互转 | AID 自动化 |
| SR-UC-04 | 体积换算 | 支持升/毫升/加仑(美)/液量盎司(美)4 个体积单位互转 | AID 自动化 |
| SR-UC-05 | NL 中文模式 | 识别 "数字+中文单位+转/到/换成+中文单位" 模式 | AID 自动化 |
| SR-UC-06 | NL 英文模式 | 识别 "数字+英文单位+to/in/->/=>+英文单位" 模式 | AID 自动化 |
| SR-UC-07 | NL 别名支持 | 支持 ~20 个单位别名(cm/厘米/centimeter 等) | AID 自动化 |
| SR-UC-08 | 跨类降级 | 跨类换算(如"米转千克")返回 null,降级为原计算 | AID 自动化 |
| SR-UC-09 | 普通表达式降级 | 纯数学表达式(如"1+2")不被 NL 解析拦截,走原流程 | AID 自动化 |
| SR-UC-10 | 结果展示 | 换算结果直接显示在 result 区(主结果),expression 保留 NL 原文 | AID 自动化 |
| SR-UC-11 | 不破坏现有功能 | 不影响实时预览(Issue #11)/百分号(Issue #9)/历史/偏好 | AID 自动化 |
| SR-UC-12 | 浮点精度 | 容差 1e-6,符合 SI 国际标准常量 | AID 自动化 |

### 用户旅程

**主路径 — 中文 NL 换算**:
1. 用户启动 OpenCalc
2. 用户键入 "100厘米转英寸" → expression = "100厘米转英寸"
3. 系统检测到 NL 模式 → 解析为 {value: 100, from: "cm", to: "inch", category: "length"}
4. UnitConverter.convert(100, "cm", "inch", "length") → 39.3700787...
5. DisplayPanel.result 显示 "39.3700787"
6. 用户按 AC 清空 → expression = ""，result = ""

**主路径 — 温度换算(非线性)**:
1. 用户键入 "30摄氏度转华氏度"
2. 解析为 {value: 30, from: "°C", to: "°F", category: "temperature"}
3. UnitConverter.convert(30, "°C", "°F", "temperature") = 30 × 9/5 + 32 = 86
4. DisplayPanel.result 显示 "86"

**主路径 — 英文 NL 换算**:
1. 用户键入 "100cm to inch"
2. 解析为 {value: 100, from: "cm", to: "inch", category: "length"}
3. result 显示 "39.3700787"

**异常路径 — 跨类换算**:
1. 用户键入 "1米转千克" → 解析为 {value: 1, from: "m", to: "kg"}
2. 检测 category 不匹配(m=length, kg=mass)→ 返回 null
3. 降级为 CalcEngine.evaluate("1米转千克") → 语法错误 → result 空 + 错误提示

**异常路径 — 无法识别 NL**:
1. 用户键入 "abc 厘米 转 英寸" → 正则不匹配数字
2. 返回 null → 降级为原计算 → 错误

**降级路径 — 普通表达式**:
1. 用户键入 "1+2" → NL 解析返回 null
2. 走 CalcEngine.evaluate → 3
3. result 显示 "3"

**性能路径 — 复杂 NL**:
1. 用户键入 "1000米转千米" → length 换算 → 1 km
2. 用户键入 "0摄氏度转开尔文" → temperature 换算 → 273.15 K
3. 单次 NL 解析 < 1ms,总响应 < 5ms

---

## 需求分解

### 5.1 功能性需求

#### 5.1.1 长度换算(FR-UC-01)
- **支持单位**:m, cm, mm, km, inch(in), foot(ft), yard(yd), mile(mi)
- **基准**:以"米"为基准
  - 1 m = 100 cm = 1000 mm = 0.001 km
  - 1 inch = 0.0254 m
  - 1 foot = 0.3048 m
  - 1 yard = 0.9144 m
  - 1 mile = 1609.344 m
- **算法**:value_in_meters = value × factor[from]; result = value_in_meters / factor[to]
- **验收**:100 cm → inch = 39.3700787; 1 km → mile = 0.621371192; 1 mile → km = 1.609344

#### 5.1.2 温度换算(FR-UC-02)
- **支持单位**:°C(Celsius), °F(Fahrenheit), K(Kelvin)
- **算法**(非线性):
  - °C → °F: F = C × 9/5 + 32
  - °C → K: K = C + 273.15
  - °F → °C: C = (F - 32) × 5/9
  - °F → K: K = (F - 32) × 5/9 + 273.15
  - K → °C: C = K - 273.15
  - K → °F: F = (K - 273.15) × 9/5 + 32
- **验收**:30°C → 86°F; 0°C → 273.15K; 100°F → 37.7777°C

#### 5.1.3 质量换算(FR-UC-03)
- **支持单位**:kg, g, lb(pound), oz(ounce)
- **基准**:以"千克"为基准
  - 1 kg = 1000 g
  - 1 lb = 0.45359237 kg
  - 1 oz = 0.028349523125 kg
- **验收**:5 lb → kg = 2.26796185; 1 kg → g = 1000; 16 oz → lb = 1

#### 5.1.4 体积换算(FR-UC-04)
- **支持单位**:L(liter), mL, gal(US gallon), fl oz(US fluid ounce)
- **基准**:以"升"为基准
  - 1 L = 1000 mL
  - 1 US gal = 3.785411784 L
  - 1 US fl oz = 0.0295735295625 L
- **验收**:1 gal → L = 3.785411784; 128 fl oz → gal = 1; 1000 mL → L = 1

#### 5.1.5 NL 中文模式(FR-UC-05)
- **正则**:`^(\d+(?:\.\d+)?)\s*([一-龥]+|cm|mm|km|inch|ft|yd|mi|kg|g|lb|oz|L|mL|gal)\s*(转|到|换成|to|in|->|=>)\s*([一-龥]+|cm|mm|km|inch|ft|yd|mi|kg|g|lb|oz|L|mL|gal)$`
- **大小写不敏感**:"CM" / "cm" / "Cm" 均接受
- **空格容忍**:数字与单位之间可省略空格

#### 5.1.6 NL 英文模式(FR-UC-06)
- **正则**:`^(\d+(?:\.\d+)?)\s*([a-zA-Z°]+)\s*(to|in|->|=>)\s*([a-zA-Z°]+)$`
- **大小写不敏感**

#### 5.1.7 单位别名(FR-UC-07)
- **length 类别**(8 基准单位):
  - 米:m, meter, meters, 米, 公尺
  - 厘米:cm, centimeter, centimeters, 厘米, 公分
  - 毫米:mm, millimeter, 毫米
  - 千米:km, kilometer, 千米, 公里
  - 英寸:inch, inches, in, 英寸, 时
  - 英尺:foot, feet, ft, 英尺, 尺
  - 码:yard, yards, yd, 码
  - 英里:mile, miles, mi, 英里, 哩
- **temperature 类别**(3 基准单位):
  - 摄氏度:C, °C, Celsius, 摄氏度, 摄氏
  - 华氏度:F, °F, Fahrenheit, 华氏度, 华氏
  - 开尔文:K, Kelvin, 开尔文
- **mass 类别**(4 基准单位):
  - 千克:kg, kilogram, kilograms, 千克, 公斤
  - 克:g, gram, grams, 克
  - 磅:lb, lbs, pound, pounds, 磅
  - 盎司:oz, ounce, ounces, 盎司
- **volume 类别**(4 基准单位):
  - 升:L, l, liter, liters, 升, 公升
  - 毫升:mL, ml, mL, milliliter, 毫升
  - 加仑:gal, gallon, gallons, 加仑
  - 液量盎司:fl oz, fluid ounce, 液量盎司

#### 5.1.8 跨类降级(FR-UC-08)
- **检测**:UnitConverter 接受 category 参数;若 from 和 to 的 canonical 单位类别不一致,返回 null
- **错误传播**:NL 解析器检测到 null → 返回 null → CalculatorPage 降级为原计算
- **错误提示**:"不支持的换算:从 X 到 Y"

#### 5.1.9 结果展示(FR-UC-10)
- **位置**:DisplayPanel.result 区域(主结果)
- **格式**:通过 NumberFormatter 格式化(支持千分位、小数)
- **精度**:默认 6 位小数 + 末尾去零

### 5.2 非功能性需求

#### 5.2.1 性能(NFR-UC-01)
- NL 解析 < 1ms(正则 + 字典查找)
- 单位换算 < 1ms(纯算术)
- 总响应 < 5ms(对用户按键响应无影响)

#### 5.2.2 浮点精度(NFR-UC-02)
- 容差:1e-6
- 已知参考值:
  - 100 cm → inch ≈ 39.3700787
  - 1 mile → km = 1.609344
  - 0°C → K = 273.15
  - 100°F → °C ≈ 37.7777777...
  - 1 US gal → L ≈ 3.785411784

#### 5.2.3 可维护性(NFR-UC-03)
- 单位字典数据结构清晰(便于扩展)
- 测试覆盖率 100%(每个支持单位对至少 1 个用例)
- 文档:每个单位类别有 JSDoc 说明基准和换算公式

### 5.3 验收用例矩阵

| 用例编号 | 输入 | 期望 result | 关联 SR |
|---------|------|-------------|---------|
| AC-UC-01 | "100厘米转英寸" | 39.3700787 | SR-UC-01/05/07 |
| AC-UC-02 | "30摄氏度转华氏度" | 86 | SR-UC-02/05/07 |
| AC-UC-03 | "1英里转千米" | 1.609344 | SR-UC-01/05/07 |
| AC-UC-04 | "5磅转千克" | 2.26796185 | SR-UC-03/05/07 |
| AC-UC-05 | "1加仑转升" | 3.785411784 | SR-UC-04/05/07 |
| AC-UC-06 | "100cm to inch" | 39.3700787 | SR-UC-01/06/07 |
| AC-UC-07 | "0摄氏度转开尔文" | 273.15 | SR-UC-02/05/07 |
| AC-UC-08 | "100华氏度转摄氏度" | 37.7777777 | SR-UC-02/05/07 |
| AC-UC-09 | "1米转千克" | 错误/降级 | SR-UC-08 |
| AC-UC-10 | "1+2" | 3(原计算) | SR-UC-09 |
| AC-UC-11 | "abc 厘米 转 英寸" | 错误/降级 | SR-UC-05 |
| AC-UC-12 | "1000米转千米" | 1 | SR-UC-01/05/07 |
| AC-UC-13 | "1 kg to g" | 1000 | SR-UC-03/06/07 |
| AC-UC-14 | "128 fl oz to gal" | 1 | SR-UC-04/06/07 |
| AC-UC-15 | "0.5 公里 转 米" | 500 | SR-UC-01/05/07 |

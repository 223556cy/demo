# Issue #25 单位换算扩展 — 增量设计文档（Delta）

> 本文件为 Issue #25 的增量设计，仅描述相对 `feat-unit-conversion`（Issue #18）的新增/变更内容。
> 已存在的功能与章节通过引用 `#18 archives` 或 `feat-unit-conversion` 设计实现。
> 关联制品：`proposal.md` / `delta-spec.md` / `info.md`

---

## 1. 概述

### 1.1 应用定位
OpenCalc（HarmonyOS 计算器）的单位换算扩展：在 #18 已实现的 4 大类（length/temperature/mass/volume）基础上，新增 3 大类（area/time/speed），覆盖工程/学习/出行的常见换算需求。

### 1.2 核心交互
用户复用 #18 的 NL 入口（CalculatorPage.expression 输入框），输入"100亩转平方米"等表达式，预览区实时显示换算结果。

```
用户键入 NL
    ↓
CalculatorPage.expression @Watch 触发 onExpressionChange
    ↓
NaturalLanguageParser.parse(expr) → ParseResult | null
    ↓  (匹配)
UnitConverter.convert(value, from, to, category) → number | null
    ↓
NumberFormatter.format → nlConversionResult
    ↓
UI 预览区显示
```

### 1.3 技术栈概览
- 框架：ArkTS 声明式 UI（沿用 #18，零修改）
- 状态管理：V1（@State，#18 已用）
- 模块：entry HAP（单模块应用，#18 已用）
- 公共模块：`common/UnitConverter.ets` + `common/NaturalLanguageParser.ets`（本次扩展）

## 2. 功能清单

| 功能名 | 说明 | 入口 | 优先级 |
| --- | --- | --- | --- |
| F-25-001 面积换算 | 9 个基准单位（m²/cm²/km²/ft²/in²/yd²/acre/hectare/亩） | CalculatorPage 输入框 | P0 |
| F-25-002 时间换算 | 8 个基准单位（ms/s/min/h/d/wk/mo/yr） | CalculatorPage 输入框 | P0 |
| F-25-003 速度换算 | 5 个基准单位（m/s/km/h/mph/knot/mach） | CalculatorPage 输入框 | P0 |
| F-25-004 NL 别名扩展 | 新增 ~50 个中英文别名（area/time/speed） | NaturalLanguageParser | P0 |
| F-25-005 别名冲突检测 | 单元测试用 Set 校验所有别名唯一 | test suite | P1 |
| F-25-006 跨类别拒绝 | from/to 类别不一致返回 null（#18 行为） | UnitConverter | P0 |
| F-25-007 零回归 | #18 4 大类测试 100% 通过 | test suite | P0 |

## 3. 实现模型

### 3.1 上下文视图
```
@startuml
actor User
boundary CalculatorPage
control NaturalLanguageParser
control UnitConverter
database "静态因子表" as Factors
@enduml
```
沿用 #18 上下文视图，无新增外部实体。

### 3.2 总体架构
沿用 #18 的 4 层单向数据流：
```
View（CalculatorPage）
  ↓ @State expression
ViewModel（@Watch onExpressionChange）
  ↓ ParseResult
Service（NaturalLanguageParser + UnitConverter）
  ↓ number | null
Platform-Kit（NumberFormatter）
  ↓ string
View（nlConversionResult 预览）
```
**#25 变更点**：仅 Service 层内部 Map 扩展，零侵入。

### 3.3 HAP/HAR/HSP 模块划分
沿用 #18。entry HAP 单模块，无 HAR/HSP 划分。

### 3.4 设计系统规格
不涉及（#18 已定义完整主题/间距/字号；#25 无 UI 变更）。

### 3.5 UnitConverter 模块增量设计

#### 3.5.1 模块介绍
- 路径：`opencalc/entry/src/main/ets/common/UnitConverter.ets`
- 身份：entry HAP 内 common 模块，纯函数式类
- 范围：单位换算核心，不涉及 UI/状态/持久化

#### 3.5.2 功能描述
| 功能 | 来源 |
| --- | --- |
| `convert(value, from, to, category)` | 沿用 #18，本期扩展 category 取值 |
| `getFactors(category)` | 沿用 #18，本期追加 3 个 if 分支 |
| `buildLengthFactors()` / `buildMassFactors()` / `buildVolumeFactors()` | 沿用 #18，**不改** |
| `buildAreaFactors()` / `buildTimeFactors()` / `buildSpeedFactors()` | **#25 新增** |
| `convertTemperature()` | 沿用 #18，**不改** |

#### 3.5.3 目录结构
```
ets/common/
├── UnitConverter.ets       # 本次扩展
└── NaturalLanguageParser.ets  # 本次扩展
```

#### 3.5.4 架构图谱（类图）
```
@startuml
class UnitConverter {
  +static convert(value, from, to, category): number | null
  -static convertTemperature(value, from, to): number | null
  -static getFactors(category): Map | null
  -static buildLengthFactors(): Map
  -static buildMassFactors(): Map
  -static buildVolumeFactors(): Map
  -static buildAreaFactors(): Map  ' #25 新增
  -static buildTimeFactors(): Map  ' #25 新增
  -static buildSpeedFactors(): Map  ' #25 新增
}

note right of UnitConverter
  #25 扩展：
  - 3 个新因子表
  - getFactors 末尾 +3 if 分支
  - convert 不变（通用因子表查找）
end note
@enduml
```

#### 3.5.5 功能与用例分析
```
用例 UC-A-01：面积换算
前置条件：NL 解析器识别到 area 类别
步骤：
  1. 输入 "100亩转平方米"
  2. NL 解析返回 {value:100, from:"mu", to:"m2", category:"area"}
  3. UnitConverter.convert(100, "mu", "m2", "area")
  4. = 100 * (2000/3) / 1.0 = 66666.6667
后置条件：预览区显示 "66666.67 m²"
```

#### 3.5.6 接口设计
**新增/修改的接口签名**：
```typescript
// 沿用 #18，仅扩展 category 取值
static convert(
  value: number,
  from: string,   // canonical key 如 "mu" / "m2" / "h" / "kmh"
  to: string,
  category: string  // 新增取值 'area' | 'time' | 'speed'
): number | null

// 沿用 #18，仅扩展分支
private static getFactors(category: string): Map<string, number> | null

// #25 新增 3 个私有工厂函数
private static buildAreaFactors(): Map<string, number>
private static buildTimeFactors(): Map<string, number>
private static buildSpeedFactors(): Map<string, number>
```

**接口约束**：
- `category` 新增字符串取值 `'area'` / `'time'` / `'speed'`
- 所有返回值类型不变（`number | null`）
- 不破坏向后兼容（#18 调用方传固定字符串）

#### 3.5.7 状态管理设计
不涉及（纯函数式模块，无状态）。

#### 3.5.8 核心算法

##### 因子表设计（#25 新增）

```typescript
// 面积（基准 m²）
private static buildAreaFactors(): Map<string, number> {
  const m = new Map<string, number>()
  m.set('m2', 1.0)              // 平方米
  m.set('cm2', 0.0001)          // 平方厘米
  m.set('km2', 1_000_000.0)     // 平方千米
  m.set('ft2', 0.09290304)      // 平方英尺
  m.set('in2', 0.00064516)      // 平方英寸
  m.set('yd2', 0.83612736)      // 平方码
  m.set('acre', 4046.8564224)   // 英亩
  m.set('hectare', 10000.0)     // 公顷
  m.set('mu', 2000.0 / 3.0)     // 亩（中国市制）
  return m
}

// 时间（基准 s）
private static buildTimeFactors(): Map<string, number> {
  const m = new Map<string, number>()
  m.set('ms', 0.001)
  m.set('s', 1.0)
  m.set('min', 60.0)
  m.set('h', 3600.0)
  m.set('d', 86400.0)
  m.set('wk', 604800.0)         // 7 × 86400
  m.set('mo', 2592000.0)        // 30 × 86400 (工程近似)
  m.set('yr', 31536000.0)       // 365 × 86400 (工程近似)
  return m
}

// 速度（基准 m/s）
private static buildSpeedFactors(): Map<string, number> {
  const m = new Map<string, number>()
  m.set('m_s', 1.0)
  m.set('kmh', 1000.0 / 3600.0)
  m.set('mph', 1609.344 / 3600.0)
  m.set('knot', 1852.0 / 3600.0)
  m.set('mach', 340.29)          // 海平面 15°C 标况声速
  return m
}
```

##### 换算公式（沿用 #18）
```
valueInBase = value × fromFactor
result = valueInBase / toFactor
```

##### 复杂度
- 时间复杂度：O(1)（Map.get/set）
- 空间复杂度：O(1)（固定大小因子表）

#### 3.5.9 错误处理
沿用 #18：未知单位 / 跨类别 / 无效 category → 返回 `null`，不抛异常。

#25 新增失败场景：
- area/time/speed 任一类别内部 from/to 不在因子表 → null
- from/to 类别不一致（如 area ↔ time） → null（与 #18 一致）

#### 3.5.10 依赖关系
- 内部：无（无 import）
- 外部：无（无 @ohos / @kit）
- 被依赖：CalculatorPage（via `nlConversionResult`）、UnitConverter.test.ets

### 3.6 NaturalLanguageParser 模块增量设计

#### 3.6.1 模块介绍
- 路径：`opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets`
- 身份：entry HAP 内 common 模块
- 范围：NL 字符串解析为 ParseResult，不涉及换算

#### 3.6.2 功能描述
| 功能 | 来源 |
| --- | --- |
| `parse(input)` | 沿用 #18，**逻辑不变**，仅扩展别名表 |
| `buildAliases()` | 沿用 #18 工厂模式，**#25 追加 ~50 行** |

#### 3.6.3 目录结构
沿用 §3.5.3。

#### 3.6.4 架构图谱
```
@startuml
interface ParseResult {
  value: number
  from: string
  to: string
  category: string
}

interface AliasEntry {
  key: string
  category: string
}

class NaturalLanguageParser {
  +static parse(input): ParseResult | null
  -static buildAliases(): Map<string, AliasEntry>
}

NaturalLanguageParser ..> ParseResult : returns
NaturalLanguageParser ..> AliasEntry : uses
note right of NaturalLanguageParser
  #25 扩展：
  buildAliases 末尾追加：
  - ~15 area 别名
  - ~15 time 别名
  - ~15 speed 别名
end note
@enduml
```

#### 3.6.5 功能与用例分析
```
用例 UC-NL-A-01：面积中文 NL
前置条件：用户输入 "100亩转平方米"
步骤：
  1. 正则提取数字 100 → value=100
  2. 中文转换词 "转" → fromStr="亩", toStr="平方米"
  3. ALIASES.get("亩") = {key:"mu", category:"area"}
  4. ALIASES.get("平方米") = {key:"m2", category:"area"}
  5. 类别一致 → 返回 ParseResult
后置条件：返回 {value:100, from:"mu", to:"m2", category:"area"}
```

#### 3.6.6 接口设计
```typescript
// 沿用 #18，零修改
static parse(input: string): ParseResult | null

// 沿用 #18 工厂模式，#25 追加 m.set(...)
private static buildAliases(): Map<string, AliasEntry>
```

#### 3.6.7 状态管理设计
不涉及（纯函数）。

#### 3.6.8 核心算法 — 别名表（#25 新增）

```typescript
// area（~15 别名）
m.set('亩', { key: 'mu', category: 'area' })
m.set('平方米', { key: 'm2', category: 'area' })
m.set('平方千米', { key: 'km2', category: 'area' })
m.set('平方厘米', { key: 'cm2', category: 'area' })
m.set('平方英尺', { key: 'ft2', category: 'area' })
m.set('平方英寸', { key: 'in2', category: 'area' })
m.set('平方码', { key: 'yd2', category: 'area' })
m.set('英亩', { key: 'acre', category: 'area' })
m.set('公顷', { key: 'hectare', category: 'area' })
m.set('m2', { key: 'm2', category: 'area' })
m.set('km2', { key: 'km2', category: 'area' })
m.set('ft2', { key: 'ft2', category: 'area' })
m.set('acre', { key: 'acre', category: 'area' })
m.set('hectare', { key: 'hectare', category: 'area' })
m.set('ha', { key: 'hectare', category: 'area' })

// time（~15 别名）
m.set('秒', { key: 's', category: 'time' })
m.set('毫秒', { key: 'ms', category: 'time' })
m.set('分钟', { key: 'min', category: 'time' })
m.set('小时', { key: 'h', category: 'time' })
m.set('天', { key: 'd', category: 'time' })
m.set('周', { key: 'wk', category: 'time' })
m.set('月', { key: 'mo', category: 'time' })
m.set('年', { key: 'yr', category: 'time' })
m.set('s', { key: 's', category: 'time' })
m.set('ms', { key: 'ms', category: 'time' })
m.set('min', { key: 'min', category: 'time' })
m.set('h', { key: 'h', category: 'time' })
m.set('hour', { key: 'h', category: 'time' })
m.set('day', { key: 'd', category: 'time' })
m.set('week', { key: 'wk', category: 'time' })
m.set('month', { key: 'mo', category: 'time' })
m.set('year', { key: 'yr', category: 'time' })

// speed（~15 别名）
m.set('米每秒', { key: 'm_s', category: 'speed' })
m.set('千米每小时', { key: 'kmh', category: 'speed' })
m.set('公里每小时', { key: 'kmh', category: 'speed' })
m.set('英里每小时', { key: 'mph', category: 'speed' })
m.set('节', { key: 'knot', category: 'speed' })
m.set('马赫', { key: 'mach', category: 'speed' })
m.set('m/s', { key: 'm_s', category: 'speed' })
m.set('km/h', { key: 'kmh', category: 'speed' })
m.set('kph', { key: 'kmh', category: 'speed' })
m.set('mph', { key: 'mph', category: 'speed' })
m.set('knot', { key: 'knot', category: 'speed' })
m.set('mach', { key: 'mach', category: 'speed' })
```

#### 3.6.9 错误处理
沿用 #18 别名未找到返回 null；#25 无新增错误处理。

#### 3.6.10 依赖关系
- 内部：无
- 外部：无
- 被依赖：CalculatorPage、NaturalLanguageParser.test.ets

### 3.7 测试套件增量设计

#### 3.7.1 单元测试

| 测试文件 | #18 已有 | #25 新增 |
| --- | --- | --- |
| `UnitConverter.test.ets` | 4 describe（length/temperature/mass/volume/errors） | +3 describe（area/time/speed）+1 describe（cross-category） |
| `NaturalLanguageParser.test.ets` | 2 describe（chinese/english）+ 1 describe（errors） | +3 describe（area/time/speed） |

#### 3.7.2 测试用例设计（#25 新增）
详见 `info.md` §测试验证策略（共 ~30 个新用例）。

#### 3.7.3 UI 测试
沿用 #18 的 `ui-tests/UnitConverter.ui.ts` 模式，本期新增 3 个用例：
- "100亩转平方米" → 预览 "66666.67 m²"
- "2小时转分钟" → 预览 "120 min"
- "60英里每小时转千米每小时" → 预览 "96.56 km/h"

## 4. 接口设计

### 4.1 内部数据访问 API
沿用 #18，无新增。

### 4.2 业务抽象接口
- **UnitConverter**：`static convert(value: number, from: string, to: string, category: string): number | null`
- **NaturalLanguageParser**：`static parse(input: string): ParseResult | null`

#25 扩展点：category 字符串新增 3 个取值，接口签名零修改。

### 4.3 后台任务与 ExtensionAbility 接口
不涉及。

### 4.4 Want / Action 协议
不涉及。

### 4.5 URI / Deep Link / AppLinking 协议
不涉及。

### 4.6 IPC 与 RPC 接口
不涉及。

### 4.7 Native（C/C++）接口
不涉及。

### 4.8 文件交换接口
不涉及。

## 5. 数据模型

### 5.1 关系型数据库模型
不涉及。

### 5.2 领域模型
```typescript
// 沿用 #18 ParseResult
interface ParseResult {
  value: number      // 输入数值
  from: string       // 源 canonical key
  to: string         // 目标 canonical key
  category: string   // 'length' | 'temperature' | 'mass' | 'volume' | 'area' | 'time' | 'speed'
}

// 沿用 #18 AliasEntry
interface AliasEntry {
  key: string        // canonical key
  category: string   // 类别
}
```

### 5.3 Preferences 结构
不涉及。

### 5.4 分布式数据对象模型
不涉及。

### 5.5 文件格式 Schema
不涉及。

## 6. UI 设计系统

### 6.1-6.7
沿用 #18，零修改。

## 7. 页面清单与导航

### 7.1 页面清单
沿用 #18：`CalculatorPage`（唯一页面）。

### 7.2 全局导航图
不涉及（单页面应用）。

### 7.3 Deep Link / AppLinking
不涉及。

### 7.4 Want 跳转矩阵
不涉及。

## 8. 用户交互规格

### 8.1 手势交互
沿用 #18，零修改。

### 8.2 弹窗/Sheet/Menu
沿用 #18，零修改。

### 8.3 剪贴板与反馈
沿用 #18，零修改。

### 8.4 卡片交互
不涉及。

## 9. 平台集成

### 9.1 构建配置与依赖
零修改。

### 9.2 权限与运行时请求
零新增权限。

### 9.3 系统能力（Kits）清单
沿用 #18（仅 @ohos.hypium 测试框架）。

### 9.4 后台与 Extension
不涉及。

### 9.5 备份与恢复
不涉及。

### 9.6 分布式与跨端
不涉及。

## 10. 偏好设置目录

不涉及（#18 未引入换算相关偏好；#25 同样不引入）。

---

## 附录 A：实施清单（IMPLEMENTING 输入）

| 任务编号 | 任务 | 输入 | 输出 |
| --- | --- | --- | --- |
| T-01 | 扩展 UnitConverter 因子表 | delta-spec §因子表附录 | UnitConverter.ets +3 函数 |
| T-02 | 扩展 UnitConverter.getFactors | delta-spec §SR-001/003/005 | UnitConverter.ets +3 if |
| T-03 | 扩展 NaturalLanguageParser 别名 | delta-spec §SR-002/004/006 | NaturalLanguageParser.ets +50 m.set |
| T-04 | 新增 UnitConverter 测试 | delta-design §3.7.2 | UnitConverter.test.ets +4 describe |
| T-05 | 新增 NaturalLanguageParser 测试 | delta-design §3.7.2 | NaturalLanguageParser.test.ets +3 describe |
| T-06 | 别名冲突检测测试 | delta-spec §SR-007 | 测试套件 |
| T-07 | 跑回归（全量） | T-01..T-06 完成 | 100% 绿 |

## 附录 B：可追溯性矩阵

| 需求 (delta-spec) | 设计章节 | 实现任务 |
| --- | --- | --- |
| REQ-25-001 | §3.5 + §3.6.8 | T-01/02/03 |
| REQ-25-002 | §3.5 + §3.6.8 | T-01/02/03 |
| REQ-25-003 | §3.5 + §3.6.8 | T-01/02/03 |
| REQ-25-004 | §3.6.8 | T-03 |
| REQ-25-005 | §3.7.3 + §附录 A T-07 | T-04/05/07 |
| REQ-25-006 | §3.5.9 + §3.7.2 | T-04 |

---
> 本文档由 mod-design skill 生成。
> 标记 [推断] 的内容为基于设计推断，非确定性事实。
> 生成时间: 2026-06-17

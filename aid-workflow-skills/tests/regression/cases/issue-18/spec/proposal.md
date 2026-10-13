# Issue #25 单位换算扩展 需求提案

> ⚠️ 重叠说明：Issue #18 已经实现 length/temperature/mass/volume 4 大类 19 个基准单位 + NL 解析。
> Issue #25 沿用同一入口("100厘米转英寸"、"30摄氏度转华氏度"),本次在 #18 基础上扩展到 7 大类,新增 area / time / speed 3 类。
> 用户授权：全自动模式(方案 C),自动接受默认值。

## 1. 需求概述

### 1.1 功能名称
单位换算扩展（Extended Unit Conversion）

### 1.2 需求类型
新增功能（requirement-add）

### 1.3 关联特性
feat-unit-conversion（在 Issue #18 feat-unit-conversion 基础上扩展）

### 1.4 需求描述
在 Issue #18 已实现的 length / temperature / mass / volume 4 大类基础上，扩展支持：
- **面积 (area)**：平方米 / 平方厘米 / 平方英尺 / 平方英寸 / 平方码 / 英亩 / 公顷 / 亩
- **时间 (time)**：秒 / 毫秒 / 分钟 / 小时 / 天 / 周 / 月(30天) / 年(365天)
- **速度 (speed)**：米每秒 / 千米每小时 / 英里每小时 / 节 / 马赫

输入框直接接受自然语言查询（沿用 #18 的 NL 解析器），例如：
- "100亩转平方米"
- "2小时转分钟"
- "60英里每小时转千米每小时"
- "500英亩转公顷"

### 1.5 使用场景
- 工程师/学生在手机上快速换算面积、时间、速度
- 不需要切换到专门的换算 App
- 输入框直接识别 NL，无需选择模式

### 1.6 预期效果
- 沿用 #18 的 UX：在输入框输入 NL 表达式 → 实时预览换算结果
- 7 大类总计覆盖 ~32 个基准单位,~120+ 别名（中英文）
- 现有 length / temperature / mass / volume 测试 100% 通过
- 新增类别的单元测试 100% 覆盖

## 2. 需求解析报告

### 2.1 意图分类
- **类型**：新增功能（基于现有功能扩展）
- **一句话概括**：在 Issue #18 已实现的 4 大类单位换算基础上，新增 area / time / speed 3 大类，覆盖工程/学习/出行场景

### 2.2 领域映射
- **UI/交互**：复用 CalculatorPage 现有 NL 实时预览逻辑（已由 #18 完成，本期不修改）
- **状态管理**：无新状态（沿用 #18 的 `nlConversionResult`）
- **数据管理**：仅扩展 `UnitConverter` 因子表和 `NaturalLanguageParser` 别名表（Map 扩展）
- **国际化**：新增中文别名（如"亩"、"节"、"马赫"）和英文别名

### 2.3 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | 不变 | CalculatorPage 不动；NL 预览机制已由 #18 接入 |
| ViewModel | 不变 | 计算逻辑沿用 #18 |
| Model | extend | UnitConverter 增加 area/time/speed 因子表和 convert 方法分支 |
| 基础设施 | extend | NaturalLanguageParser 增加 ~50 个别名 |

### 2.4 关键实体
- **数据实体**：
  - `UnitConverter` 类：新增 `convertArea` / `convertTime` / `convertSpeed` 三个分支（或统一因子表方案）
  - 因子表：`AREA_FACTORS` / `TIME_FACTORS` / `SPEED_FACTORS`
- **接口实体**：
  - `UnitConverter.convert(value, from, to, category)` — 新增 category 取值 `'area' | 'time' | 'speed'`
  - `NaturalLanguageParser.parse(input)` — 自动识别新增类别的别名
- **事件实体**：无

### 2.5 模糊点
| # | 类别 | 描述 | 严重程度 | 决策（方案C） |
|---|------|------|---------|---------------|
| 1 | 范围模糊 | 是否要货币换算？ | blocker-已回避 | 货币汇率随时间变化，#25 不做；属于未来 issue |
| 2 | 范围模糊 | 时间和速度的精度（月=30天 vs 实际月份） | important | 默认 1 月=30 天、1 年=365 天；非闰年近似 |
| 3 | 行为模糊 | "亩"是中国市制单位，是否保留？ | important | 保留；中国用户常用 |
| 4 | 行为模糊 | "马赫"用什么声速值？ | important | 默认 340.29 m/s（海平面 15°C 标况声速） |
| 5 | 交互模糊 | 是否需要在 UI 显示新增类别标识？ | nice-to-have | 不显示；现有 UI 仅显示结果 |

> 决策依据：dev-01 全自动授权（方案 C）；上述默认值均为国际标准或工程常用近似。

### 2.6 复杂度评估
- **等级**：M（中等）
- **理由**：
  - 影响 2 个文件（UnitConverter.ets、NaturalLanguageParser.ets）
  - 新增 ~13 个基准单位 + ~50 个别名
  - 沿用 #18 因子表 + 别名表 Map 模式
  - 不改 UI / 不改数据模型 / 不改架构
  - 新增测试 3 套 + 现有 2 套测试回归

## 3. 需求澄清

### 3.1 已澄清的关键决策
| # | 问题 | 决策 | 来源 |
|---|------|------|------|
| 1 | 是否要做货币换算 | 不做 | 方案C默认，汇率动态不适合内嵌静态因子 |
| 2 | 月/年定义 | 1月=30天、1年=365天 | 方案C默认，工程标准近似 |
| 3 | 马赫声速值 | 340.29 m/s | 方案C默认，海平面 15°C 标况 |
| 4 | "亩"是否保留 | 保留 | 方案C默认，中国用户常用 |

### 3.2 待定假设
- 月=30天、年=365天是工程近似；不区分闰年/平年
- 马赫 = 340.29 m/s（海平面 15°C）；高空/水下不使用
- 不引入配置项（用户无法切换月=30 vs 月=实际天数）
- 不修改 #18 的现有 length/temperature/mass/volume 行为（零回归）

### 3.3 功能边界
- **包含**：
  - 3 个新类别：area / time / speed
  - 对应的中文/英文别名
  - 单元测试覆盖所有新组合
  - 现有 4 大类测试 100% 回归
- **不包含**：
  - 货币换算（动态数据，超出 #25 范围）
  - UI 改造（沿用 #18 UX）
  - 配置项（精度/默认值切换）
  - 数据存储（无持久化需求）

## 4. 需求详述

### 4.1 功能需求

#### FR-1: 面积换算（area）
**描述**：在输入框输入"100亩转平方米"等表达式，实时预览结果。
**验收条件**：
- 支持单位：m² / cm² / km² / ft² / in² / yd² / acre / hectare / 亩
- 1 acre = 4046.8564224 m²
- 1 公顷(hectare) = 10000 m²
- 1 亩 = 666.666... m²（2000/3）
- 现有 length 测试不受影响

#### FR-2: 时间换算（time）
**描述**：在输入框输入"2小时转分钟"等表达式，实时预览结果。
**验收条件**：
- 支持单位：秒(s) / 毫秒(ms) / 分钟(min) / 小时(h) / 天(d) / 周(wk) / 月(mo) / 年(yr)
- 1 mo = 30 × 86400 s
- 1 yr = 365 × 86400 s
- 现有 mass 测试不受影响

#### FR-3: 速度换算（speed）
**描述**：在输入框输入"60英里每小时转千米每小时"等表达式，实时预览结果。
**验收条件**：
- 支持单位：m/s / km/h / mph / knot / mach
- 1 km/h = 1000/3600 m/s ≈ 0.27778 m/s
- 1 mph = 1609.344/3600 m/s ≈ 0.44704 m/s
- 1 knot = 1852/3600 m/s ≈ 0.51444 m/s
- 1 mach = 340.29 m/s（标况声速）
- 现有 volume 测试不受影响

#### FR-4: NL 别名扩展
**描述**：新增类别的中英文别名必须能被 NL 解析器识别。
**验收条件**：
- 中文："亩"/"公顷"/"英亩"/"秒"/"分钟"/"小时"/"天"/"周"/"月"/"年"/"米每秒"/"千米每小时"/"英里每小时"/"节"/"马赫"
- 英文：acre/hectare/ha/sqm/sqft/sqin/sqyd/sqmi/second/minute/hour/day/week/month/year/meter per second/kmh/mph/knot/mach
- 跨类别（如"100亩转分钟"）必须返回 null（同 #18 行为）

### 4.2 可靠性需求

#### REQ-DFR-001: 零回归（#18 全功能保持）
**描述**：新增类别不得影响 #18 已实现的 4 大类。
**关注点**：
- 故障检测：跑全量回归（length/temperature/mass/volume + 新增 area/time/speed）
- 故障恢复：失败用例必须 100% 修复后才可合并
- 降级策略：若新增类别因子表加载失败，#18 的 4 大类仍可独立工作（拆 Map 函数保证）

#### REQ-DFR-002: 别名冲突检测
**描述**：新增别名不得与 #18 现有别名冲突（如某个串同时映射到两个不同类别）。
**关注点**：
- 故障检测：单元测试覆盖所有别名构建后用 Set 校验唯一性
- 故障恢复：冲突时 Map.set 覆盖（最后写入胜出）；测试必须先检测冲突
- 降级策略：别名解析失败返回 null，不抛异常

#### REQ-DFR-003: 跨类别拒绝
**描述**：from 和 to 类别不一致时返回 null（与 #18 行为一致）。
**关注点**：
- 故障检测：每个类别组合的"应当成功"和"应当失败"用例各 1 个
- 故障恢复：直接返回 null，不抛异常
- 降级策略：UI 沿用 #18 的"识别失败则按普通表达式计算"

## 5. 影响范围分析

### 5.1 涉及的模块
| 模块 | 现有功能 | 新增/修改 |
|------|---------|-----------|
| `common/UnitConverter.ets` | 4 大类因子表 + convert 方法 | **新增** 3 大类因子表 + getFactors 新分支 |
| `common/NaturalLanguageParser.ets` | ~70 个别名（4 大类） | **新增** ~50 个别名（3 大类） |
| `entry/src/test/ets/common/UnitConverter.test.ets` | #18 测试用例 | **新增** 3 套测试 |
| `entry/src/test/ets/common/NaturalLanguageParser.test.ets` | #18 测试用例 | **新增** 3 套测试 |
| `pages/CalculatorPage.ets` | NL 预览接入 | **不变**（自动支持） |

### 5.2 代码依赖分析
- `UnitConverter.convert(value, from, to, category)` 增加 category 取值 `'area' | 'time' | 'speed'`
- `getFactors(category)` 增加 3 个 if 分支（保持线性，无 switch）
- `NaturalLanguageParser` 仅扩展 `buildAliases()` 函数末尾的 `m.set(...)` 调用
- `CalculatorPage` 通过现有 `nlConversionResult` 状态自动展示新结果（无需修改）

## 6. 复杂度评估

### 6.1 评估结果
- **复杂度等级**：简单需求（M 体量但纯加法）
- **影响模块数**：2（UnitConverter + NaturalLanguageParser）
- **架构变更**：否
- **数据模型变更**：否（仅 Map 扩展）

### 6.2 跳过策略
| 制品 | 是否产出 |
|------|---------|
| proposal.md | ✅ 必须 |
| delta-spec.md | ✅ 必须 |
| info.md | ✅ 必须 |
| new-arch.md | ❌ 跳过（无架构变更） |
| delta-design.md | ✅ 必须（mod-design 产出） |
| design-review.md | ✅ 必须 |
| tasks.md | ✅ 必须（aid-implementing 产出） |

## 7. 待解决问题
无（方案C全自动接受所有默认值）

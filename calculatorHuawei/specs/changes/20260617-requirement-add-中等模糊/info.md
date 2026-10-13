# Issue #25 单位换算扩展 — 代码仓理解

## 基本信息

- **需求类别**：新增功能（基于 Issue #18 已实现的 4 大类扩展 3 大类）
- **需求名称**：单位换算扩展 (Extended Unit Conversion)
- **分析时间**：2026-06-17
- **分析范围**：`opencalc/entry/src/main/ets/common/UnitConverter.ets`、`opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets`、`opencalc/entry/src/test/ets/common/{UnitConverter,NaturalLanguageParser}.test.ets`
- **关联分支**：`feat/issue-25-中等模糊`（基于已合并 #18 / #17 / #16 / #15 / #13 的 main）
- **重叠说明**：Issue #18 已完整实现 length/temperature/mass/volume 4 大类 NL 单位换算；Issue #25 在此基础上扩展 area/time/speed 3 大类

## 环境能力（来自 .claude/capabilities.json）

- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- 单元测试框架: hypium+hamock
- 测试根: opencalc/entry/src/test
- UI 自动化测试能力: ✅ 可用 (hdc + 模拟器,harmonyos-ui-test skill)
- 模拟器: 127.0.0.1:5555 (running)
- hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- hdc 版本: 3.2.0d
- Java: openjdk 21.0.8

## 架构分析

### 系统模块结构（与 #18 增量相关的部分）
```
opencalc/entry/src/main/ets/
├── common/
│   ├── UnitConverter.ets       # 本次扩展（新增 area/time/speed 因子表）
│   └── NaturalLanguageParser.ets  # 本次扩展（新增 ~50 别名）
├── pages/
│   └── CalculatorPage.ets      # 不变（自动支持新类别，nlConversionResult 已接入）
└── ...（其他模块不变）

opencalc/entry/src/test/ets/
└── common/
    ├── UnitConverter.test.ets       # 本次扩展（新增 3 套 describe）
    └── NaturalLanguageParser.test.ets # 本次扩展（新增 3 套 describe）
```

### 模块职责
- **UnitConverter**：纯函数式换算器，接收 `(value, from, to, category)`，返回 `number | null`
  - 线性因子表模式（一个类别一张因子表，通过 getFactors(category) 选择）
  - 温度走专门 convertTemperature 分支（非线性）
- **NaturalLanguageParser**：基于正则的 NL 解析器，识别"数字+单位A+转/到/to+单位B"模式
  - 别名查表（Map<alias, {key, category}>）
  - 跨类别返回 null
- **CalculatorPage**：ArkTS View，通过 `nlConversionResult` 状态字段接入 NL 预览

### 模块间依赖
```
CalculatorPage ──import──> NaturalLanguageParser ──(无依赖)
                  ──import──> UnitConverter        ──(无依赖)
```
两者无相互依赖，可独立测试/替换。

## 接口/契约识别

### UnitConverter.convert
- **签名**：`static convert(value: number, from: string, to: string, category: string): number | null`
- **输入**：
  - `value`：数值（number，非 NaN/Infinity）
  - `from`：源单位 canonical key（如 `'cm'` / `'C'` / `'kg'`）
  - `to`：目标单位 canonical key
  - `category`：类别字符串（如 `'length'` / `'temperature'`）
- **输出**：
  - 成功：换算结果 number
  - 失败（单位未注册 / 类别无效 / 跨类别）：`null`
- **约束**：`from === to` 时直接返回 `value`（不变性优化）
- **扩展点**：`category` 接受新值；`getFactors` 接受新分支
- **向后兼容**：✅ 新增 category 取值不破坏现有调用方（现有调用方传固定字符串）

### NaturalLanguageParser.parse
- **签名**：`static parse(input: string): ParseResult | null`
- **输入**：用户原始输入字符串
- **输出**：`{value: number, from: string, to: string, category: string} | null`
- **约束**：
  - 输入必须以数字开头（支持小数 `\d+(?:\.\d+)?`）
  - 中间必须含转换词（中文"转/到/换成" 或 英文"to/in/->/=>"，不区分大小写）
  - from/to 必须在别名表中找到且类别一致
- **扩展点**：`buildAliases()` 函数末尾追加 `m.set(...)`
- **向后兼容**：✅ 仅追加别名，不修改解析逻辑

## 公共组件或函数识别

### 可复用组件或函数（来自 #18，可直接复用）
- **`UnitConverter.convertTemperature`**：温度换算模板（基准中转法），但 #25 不直接复用（因为温度不是非线性，不会用此模式）
- **`buildAliases()` Map 工厂模式**：必须沿用（满足 ArkTS `arkts-no-untyped-obj-literals`）
- **`buildXxxFactors()` Map 工厂模式**：必须沿用（同上）
- **`NaturalLanguageParser.parse` 正则链**：必须沿用（不要破坏现有正则）
- **hypium 测试模式 `describe/it/expect`**：必须沿用
- **1:1 Node 端口测试 `.port.mjs`**：可选用作 fallback（hdc 不可用时跑 Node 测试）

### 测试相关工具
- `harmonyos-ui-test` skill：用于 UI 自动化（hdc + emulator 可用时）
- `tests/*.port.mjs`：纯 Node 测试，可在本地快速跑通

## 影响范围分析

### 需要修改的模块/文件
| 文件 | 变更类型 | 行数估算 |
| --- | --- | --- |
| `opencalc/entry/src/main/ets/common/UnitConverter.ets` | extend（+3 因子表函数、+3 if 分支、+3 常量） | +50 ~ +70 行 |
| `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets` | extend（+~50 个 `m.set(...)`） | +50 ~ +60 行 |
| `opencalc/entry/src/test/ets/common/UnitConverter.test.ets` | extend（+3 describe） | +60 ~ +80 行 |
| `opencalc/entry/src/test/ets/common/NaturalLanguageParser.test.ets` | extend（+3 describe） | +60 ~ +80 行 |

### 调用链分析
```
用户输入 NL → CalculatorPage.onExpressionChange
  → NaturalLanguageParser.parse(input)
  → 返回 {value, from, to, category}
  → UnitConverter.convert(value, from, to, category)
  → 返回 number
  → NumberFormatter.format → nlConversionResult
  → UI 显示
```
新类别扩展点：`category` 是字符串，新增取值对调用链零侵入。

### 影响评估
- ✅ 不破坏 #18 已通过的测试（不修改任何现有逻辑）
- ✅ 不修改 CalculatorPage（nlConversionResult 自动覆盖）
- ⚠️ 别名表可能产生冲突（必须用 Set 测试覆盖）

### 修复/扩展方案
1. UnitConverter.ets：在文件末尾追加 3 个 `buildXxxFactors` 函数 + 3 个 `CATEGORY_XXX` 常量
2. UnitConverter.ets：在 `getFactors()` 方法末尾追加 3 个 `if` 分支
3. NaturalLanguageParser.ets：在 `buildAliases()` 末尾追加 ~50 个 `m.set(...)`
4. 测试文件：追加 3 个 `describe()` 块覆盖新类别

## 现有代码分析

### UnitConverter 关键逻辑（#18 实现，#25 不变）
- `convert(value, from, to, category)`：4 个 if 分支（temperature / length / mass / volume / fallback）
- `convertTemperature(value, from, to)`：6 个 if 分支（C/F/K 互相转换）
- `getFactors(category)`：4 个 if 分支选择因子表
- **#25 扩展**：在 getFactors 末尾追加 area/time/speed 3 个分支；convertTemperature 不变

### NaturalLanguageParser 关键逻辑（#18 实现，#25 不变）
- `parse(input)`：正则链提取 value + from + to + category
- `buildAliases()`：~70 个 `m.set(...)`（4 大类）
- **#25 扩展**：在 buildAliases 末尾追加 ~50 个 `m.set(...)`（3 大类）

### 边界条件（#25 必须保留）
- from === to 直接返回 value（避免除零）
- 因子表函数化（buildXxxFactors）— ArkTS 不支持 switch 语法糖 + 必须在模块顶层初始化 Map
- 跨类别返回 null（不抛异常）

## 风险识别

### 风险清单
| # | 风险 | 影响 | 缓解 |
| --- | --- | --- | --- |
| R-01 | 别名冲突：新增别名与 #18 现有别名冲突 | Map.set 后者覆盖前者，导致某些 NL 误识别 | 单元测试用 Set 校验所有别名唯一 |
| R-02 | 因子精度误差：mach=340.29 是近似值 | 速度换算有微小误差 | 测试 EPS=1e-3 容忍 mach |
| R-03 | 月/年定义模糊 | 用户期望与实现不符 | 提案/SPEC 文档化说明；不提供切换 |
| R-04 | NL 复合单位歧义："英里每小时"中间空格 | parser 正则贪婪匹配可能失败 | 测试用例必须覆盖复合单位 |
| R-05 | 因子表过大导致模块加载慢 | 启动性能 | 当前 ~70+ 别名不影响；扩展到 ~120 仍 < 1ms |
| R-06 | #18 测试在 #25 后回归失败 | 严重 | **不修改 #18 任何已有函数**，只追加 |

### 测试能力评估
- 单元测试能力: ✅（hypium+hamock）
- UI 自动化测试能力: ✅（harmonyos-ui-test skill，模拟器运行中）
- 端到端集成测试能力: ✅（沿用 #18 的 ui-tests/ 模式）
- 不能跑的实际原因: 无（hvigorw + hdc + 模拟器均可用）

## 测试验证策略

### 测试用例（必须新增）
- **UnitConverter area**：
  - `UC_A_01_1m2_to_cm2` → 10000
  - `UC_A_02_1acre_to_m2` → 4046.8564224
  - `UC_A_03_1hectare_to_m2` → 10000
  - `UC_A_04_1mu_to_m2` → 666.6666666666666
  - `UC_A_05_100mu_to_m2` → 66666.666...
  - `UC_A_06_1km2_to_m2` → 1000000
- **UnitConverter time**：
  - `UC_Ti_01_1h_to_min` → 60
  - `UC_Ti_02_2h_to_min` → 120
  - `UC_Ti_03_1d_to_h` → 24
  - `UC_Ti_04_1wk_to_d` → 7
  - `UC_Ti_05_1mo_to_d` → 30
  - `UC_Ti_06_1yr_to_d` → 365
- **UnitConverter speed**：
  - `UC_S_01_60mph_to_kmh` → 96.56064
  - `UC_S_02_100kmh_to_mph` → 62.13727...
  - `UC_S_03_1knot_to_kmh` → 1.852
  - `UC_S_04_1mach_to_mps` → 340.29
- **NL 别名**（每类至少 5 个中英文用例）
- **跨类别拒绝**：新增 3 个用例（area↔time↔speed 两两拒绝）

### 回归测试
- 跑全量套件：`hvigorw --no-daemon test`
- 必须 100% 通过 #18 已通过的测试

### UI 测试（沿用 #18）
- 模拟器跑 `ui-tests/UnitConverter.ui.ts`（若 hdc 可用）
- 至少 3 个用例：输入 NL → 验证预览显示

## 监控运维支持

### 不涉及
- 本次不引入新配置项
- 不修改历史记录格式
- 不持久化换算结果（仅会话内）
- 无新增日志点（保持 #18 行为）

## 关键发现

### 可复用组件或函数
- ✅ `UnitConverter.convert` 框架（4 大类已实现，#25 沿用相同 pattern）
- ✅ `NaturalLanguageParser.parse` 框架（正则 + 别名表，#25 仅追加别名）
- ✅ `CalculatorPage.nlConversionResult` 状态（自动支持新类别）
- ✅ hypium 测试模式 + Node 端口测试机制

### 风险提示
- ⚠️ 别名冲突：必须用 `new Set(allAliases).size === allAliases.length` 校验
- ⚠️ mach 值是工程近似，需在 SPEC/注释中说明
- ⚠️ 月/年是工程近似，需文档化

### 建议事项
1. 因子值精度：NIST 标准 8 位有效数字
2. 别名表去重：用 Set 校验 + 单元测试强制
3. 测试 EPS：常规 1e-6，mach 用 1e-3
4. UI 端不需要修改（自动支持）

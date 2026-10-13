# 程序员模式 — 代码仓理解

## 基本信息

- **需求类别**：新增功能（New Requirement）
- **需求名称**：programmer-mode（程序员模式）
- **分析时间**：2026-06-12
- **分析范围**：OpenCalc HarmonyOS 主计算器、计算引擎、表达式预处理、偏好存储

## 架构分析

### 模块结构
```
entry/src/main/ets/
├── pages/
│   ├── CalculatorPage.ets        ← @Entry 主页面（包含 DisplayPanel / ButtonGrid / ToggleRow）
│   └── Index.ets
├── calculator/
│   ├── Calculator.ets            ← CalcEngine：递归下降解析器（不支持 << >>）
│   ├── Expression.ets            ← 表达式预处理：%、!、√、隐式乘号
│   └── NumberFormatter.ets       ← 千分位/小数分隔符格式化
├── model/
│   ├── Models.ets                ← CalculatorError, ScientificModeType, HistoryItem, CalculatorPreferences
│   └── ErrorFlags.ets            ← 全局错误标志位
├── preferences/
│   └── PreferencesStore.ets      ← @ohos.data.preferences 封装
└── entryability/
    └── EntryAbility.ets
```

### 模块依赖关系
```
CalculatorPage
  ├─→ Expression (calculator/Expression)
  ├─→ CalcEngine (calculator/Calculator)
  ├─→ NumberFormatter (calculator/NumberFormatter)
  ├─→ ErrorFlags (model/ErrorFlags)
  ├─→ HistoryItem (model/Models)
  └─→ PreferencesStore (preferences/PreferencesStore)
       └─→ CalculatorPreferences, ScientificModeType (model/Models)
```

### 扩展点
- `CalculatorPage.ButtonGrid()` — 条件渲染 `this.scientific` 切换键盘行；可扩展为 `this.programmerMode` 渲染程序员键盘
- `CalculatorPage.ToggleRow()` — 顶部"基础 / 科学"切换器，可扩展为 3 选项
- `CalculatorPreferences` — 接口扩展字段并加默认值（**已确认**是 interface，可加可选字段）
- `PreferencesStore` — 加 getter/setter 与批量读取字段
- `Expression.replaceSymbols()` — 增加 `&` `|` `^` `~` `<<` `>>` 替换映射
- `CalcEngine.parseFactor()` — 增加 `&` `|` `^` 解析（按位运算）

## 接口/契约识别

### 关键接口

| 接口 | 文件 | 行 | 用途 |
| --- | --- | --- | --- |
| `CalcEngine.evaluate(eq, isDegree)` | Calculator.ets | 28 | 主入口 |
| `Expression.getCleanExpression(calc, dec, grp)` | Expression.ets | 8 | 表达式预处理 |
| `PreferencesStore.getAllPreferences()` | PreferencesStore.ets | 211 | 批量读 |
| `PreferencesStore.getScientificModeDefault()` | PreferencesStore.ets | 138 | 现有科学模式持久化模式 |
| `NumberFormatter.format(text, dec, grp, ns)` | NumberFormatter.ets | 21 | 显示格式化 |

### 重要约束
- `CalcEngine` 解析器**不支持**以下符号：`&` `|` `^` `~` `<<` `>>`。需要在 Expression 层先替换为 CalcEngine 能识别的函数式表达（如 `band(x,y)` `bor(x,y)` `bxor(x,y)` `bnot(x)` `shl(x,n)` `shr(x,n)`）或扩展 CalcEngine。
- 现有 `getPercentString` 已对 `%` 做括号保护，本次不冲突。
- `CalculatorPreferences` 是 interface，可平滑加字段；`DEFAULT_PREFERENCES` 必须同步加。

## 公共组件或函数识别

### 可复用
- `ErrorFlags.reset()` — 错误状态机，可在 BaseConverter 出错时使用
- `NumberFormatter.format()` — 结果区数字格式化（HEX 输出可直接用）
- `NumberFormatter.isDigit()` — 数字字符判断（可扩展判断 HEX 字符）
- `PreferencesStore.getAllPreferences()` — 批量读模式可复用，加新字段后只动 `getAllPreferences`
- `Expression.replaceSymbols()` — 字符映射机制，新增位运算可在此处替换

### 不能直接复用（需扩展）
- `CalcEngine.evaluate()` — 需扩展支持位运算（`band/bor/bxor/bnot/shl/shr` 函数语法）
- `CalculatorPage.ButtonGrid()` — 需新增 `programmerMode` 分支

## 影响范围分析

### 需要新增的模块
| 文件 | 类型 | 说明 |
| --- | --- | --- |
| `calculator/BaseConverter.ets` | 新增 | 纯函数：toBase/fromBase/format |
| `calculator/BaseConverter.test.ets` | 新增 | 单元测试（hypium 框架） |
| `components/ProgrammerKeypad.ets`（或内联到 CalculatorPage） | 新增 | 程序员键盘布局 |

### 需要修改的模块
| 文件 | 改动 | 影响范围 |
| --- | --- | --- |
| `model/Models.ets` | 加 `CalculatorMode` 枚举、`Base` 枚举、`BitWidth` 枚举、`Signedness` 枚举、扩展 `CalculatorPreferences` 4 字段 | 全局 |
| `preferences/PreferencesStore.ets` | 加 4 个 getter/setter、扩展 `getAllPreferences` | 全局 |
| `pages/CalculatorPage.ets` | 加 mode state、Tab 切换、4 进制结果显示、键盘分支 | 主页 |
| `calculator/Expression.ets` | `replaceSymbols` 增加位运算符号替换 | 仅表达式路径 |
| `calculator/Calculator.ets` | `parseFactor` 增加 `band/bor/bxor/bnot/shl/shr` 函数解析 | 仅表达式路径 |

### 不影响
- `entryability/EntryAbility.ets`
- `pages/Index.ets`
- `model/ErrorFlags.ets`
- `calculator/NumberFormatter.ets`（HEX 输出 `0xFF` 借用，但需兼容 `0b` `0o` 前缀）
- 历史记录存储结构

## 现有代码分析

### `CalculatorPage.build()` (行 200-234)
- 顶层 `Stack`，含横竖屏分支
- 已通过 `onAreaChange` 自动判断 `isLandscape`
- `ToggleRow` 已有"科学/基础"切换按钮和"历史"、"⚙ 设置"按钮
- `scientific: boolean` 是 @State，单一模式开关

### `CalculatorPage.ButtonGrid()` (行 284-297)
- 已是 `if (this.scientific)` 条件渲染科学行
- 5 列网格：sin/cos/tan/ln/log、arcsi/arcco/arcta/π/e
- 普通行：AC/%/(/)/÷、789×、456-、123+、0./⌫=

### `CalcEngine` 解析器
- 支持：+、-、×、÷、mod（#）、!、^、sin/cos/tan/ln/log、arcsi/arcco/arcta、√、π、e、阶乘（通过 `factorial` 函数）
- **不支持**：`&` `|` `^` `~` `<<` `>>`（这 6 个符号会触发 syntax_error）
- ASCII 字符码解析：43=`+`、45=`-`、42=`*`、35=`#`、47=`/`

### `Expression.replaceSymbols()` 字符映射
现有：×→*、÷→/、log₂(→logtwo(、log(→logten(、E→*10^、exp→xp、cos⁻¹→arcco、sin⁻¹→arcsi、tan⁻¹→arcta

扩展点：可加
- `&` → `band(` （左操作符方式不便，预处理为函数调用语法）
- `|` → `bor(`
- `^` → `bxor(`
- `~x` → `bnot(x)`（一元）
- `<<` → `shl(`
- `>>` → `shr(`

**注意**：CalcEngine 当前是 parseExpression→parseTerm→parseFactor→parsePrimary，无法直接处理函数式二元运算符 `band(a,b)`。需要：
- 方案 A：在 Expression 预处理层把 `a & b` 替换成 `band(a,b)`，再让 CalcEngine 扩展识别 band/bor/bxor 等函数
- 方案 B：在 CalcEngine.parseFactor 增加 `&` `|` `^` 解析

**推荐方案 A**：保持 CalcEngine 单一职责，预处理层做语法糖转换。

## 风险识别

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| ArkTS 不支持原生 `BigInt`（部分 API 版本） | 中 | 8/16/32 位用 number；64 位用 BigInt 但带 typeof 检测；不满足时降级 number 截断到 ±2^53 |
| `&` `|` `^` `~` 与现有 `^`（幂）冲突 | 高 | `^` 当前是幂运算；位运算的 `^` 需在程序员模式**独占**使用，基础/科学模式不变 |
| 现有 CalcEngine 解析器修改波及面大 | 中 | 不改 CalcEngine，全部在 Expression 预处理层做转换 |
| Preferences 字段扩展破坏老 JSON | 中 | 加新字段为可选，老 Preferences JSON 不带新字段时用默认值 |
| `&` `\|` 等在基础/科学模式误输入 | 低 | 在基础/科学模式不显示位运算按钮；且 Expression 替换仅在程序员模式生效 |
| 浮点数截断后 `1.7 → 1` 造成用户困惑 | 低 | UI 提示"程序员模式自动取整"或在键入小数点时 toast |
| 位宽溢出（256 → 0）| 低 | BaseConverter 静默截断并格式化显示，用户可从结果位数判断 |
| `<<` `>>` 占用 2 个字符，预处理要处理字符序 | 中 | 在 replaceSymbols 用 `replaceAll` 顺序处理，<< 优先于 < |
| 主题色与现有 `getOp/getEq/getClr` 风格不统一 | 低 | 复用现有色彩 API |

## 测试验证策略

### 单元测试（BaseConverter.test.ets）
1. **DEC→BIN**：0, 1, 10, 255, -1
2. **DEC→OCT**：0, 8, 64, 511
3. **DEC→HEX**：0, 16, 255, 4096
4. **8 位截断**：256 → 0, 257 → 1, 255 → 255
5. **8 位 unsigned/signed 切换**：-1 unsigned 8 位 → 255；-1 signed 8 位 → -1
6. **位宽 16/32/64**：32768, 4294967296, 2^53
7. **HEX 解析**：`"FF"` → 255；`"0xFF"` → 255；`"1A2b"` → 0x1A2B
8. **空字符串、null/NaN、负数边界**

### 单元测试（Expression.test.ets，扩展）
- `band(5,3)` → 1
- `bor(5,3)` → 7
- `bxor(5,3)` → 6
- `bnot(0)` → -1
- `shl(1,3)` → 8
- `shr(8,3)` → 1
- `5 & 3` → 1（预处理路径）
- `0xFF & 0x0F` → 15

### UI 测试（手动）
- 顶部 Tab 切换流畅
- HEX 模式下 A-F 按钮可点
- 4 进制同步显示
- 位宽与符号切换立即生效
- 模式重启后保留

### 回归测试
- 现有 20+ 测试用例（来自 Issue #9 percent 按钮）必须全部通过
- 基础/科学模式键盘布局不变

## 监控运维支持

### 配置项
- `programmerMode` (boolean, default false)
- `activeBase` (number, 2/8/10/16, default 10)
- `bitWidth` (number, 8/16/32/64, default 32)
- `signedness` (string, "signed"/"unsigned", default "signed")

### 关键日志点
- `PreferencesStore.loadAll` 失败 → console.warn
- `BaseConverter.format` NaN 输入 → console.warn
- `CalcEngine.evaluate` 64 位 BigInt 降级 → console.warn

## 关键发现

### 可复用组件或函数
- `NumberFormatter.format()` — 可复用但需扩展支持 `0x` `0b` `0o` 前缀
- `ErrorFlags` 错误状态机 — 可复用
- `Expression.replaceSymbols()` — 字符映射扩展点
- `PreferencesStore.getAllPreferences()` — 模式可扩展

### 风险提示
- `^` 在 CalcEngine 已被定义为幂运算；`^` 也是位运算 XOR。**程序员模式下** `^` 必须重定义为 XOR，基础/科学模式保持幂
- `&` `|` 在 JSON 序列化无影响，但 ArkTS 模板字符串中 `&` 需转义为 `&amp;`（如果用于 UI Label）

### 建议事项
- **强烈建议**：BaseConverter 保持为**纯函数模块**，便于 100% 单元测试覆盖
- **强烈建议**：CalcEngine 表达式解析**不修改**，所有位运算通过 Expression 预处理为 `band/bor/bxor/bnot/shl/shr` 函数调用
- **强烈建议**：4 进制显示区在基础/科学模式下不渲染（避免视觉噪声）
- **建议**：HEX 输出加 `0x` 前缀，BIN 加 `0b`，OCT 加 `0o`，DEC 不加前缀（与主流程序员计算器一致）
- **建议**：Preferences 字段命名清晰：`programmerModeEnabled` / `programmerActiveBase` / `programmerBitWidth` / `programmerSignedness`

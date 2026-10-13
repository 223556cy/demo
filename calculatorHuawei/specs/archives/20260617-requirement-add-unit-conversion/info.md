# Issue #18 单位换算 - 代码仓理解

## 基本信息

- **需求类别**：新增功能（requirement-add）
- **需求名称**：计算器支持自然语言单位换算
- **分析时间**：2026-06-17
- **分析范围**：opencalc/entry/src/main/ets/{pages,calculator,model,preferences} + opencalc/entry/src/test/

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- 编译命令: `hvigorw --no-daemon assembleHap`
- 单元测试命令: `hvigorw --no-daemon test`
- UI 测试能力: ✅ true
- 模拟器列表: ["127.0.0.1:5555"]
- hdc 路径: `D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe`
- bundleName: `com.darkempire78.opencalculator`

## 架构分析

### 模块结构
```
opencalc/entry/src/main/ets/
├── calculator/      ← 计算引擎层
│   ├── Calculator.ets        (CalcEngine: evaluate(clean, deg))
│   ├── Expression.ets        (getCleanExpression: 字符串预处理)
│   └── NumberFormatter.ets   (format: 千分位/小数位)
├── model/
│   ├── Models.ets            (HistoryItem, NumberingSystem)
│   └── ErrorFlags.ets        (全局错误标志位)
├── pages/
│   ├── CalculatorPage.ets    (主入口 View，@Entry @Component)
│   └── Index.ets             (ability 容器)
├── preferences/
│   └── PreferencesStore.ets  (kv 持久化)
├── entryability/             (UIAbility)
└── common/                   ← 🚨 不存在，需要新建
    ├── UnitConverter.ets        (本次新增)
    └── NaturalLanguageParser.ets (本次新增)
```

### 依赖关系
- `CalculatorPage` 依赖 `Expression` + `CalcEngine` + `NumberFormatter` + `Models` + `ErrorFlags` + `PreferencesStore`
- `Expression` / `CalcEngine` / `NumberFormatter` 是无状态工具类（所有方法 static 或 new 后 mutate 内部状态）
- `ErrorFlags` 是**全局静态错误标志**（Boolean 数组），调用 evaluate 后检查标志位
- 本次新增 `UnitConverter` + `NaturalLanguageParser` 都将设计为**纯函数静态类**，不引入新状态

## 接口/契约识别

### 现有可复用接口
| 接口 | 位置 | 用途 |
|------|------|------|
| `Expression.getCleanExpression(raw, dec, grp)` | calculator/Expression.ets | 字符串预处理（替换运算符/去除空 token） |
| `CalcEngine.evaluate(clean, degreeMode)` | calculator/Calculator.ets | 数值求值，副作用：可能设置 ErrorFlags |
| `NumberFormatter.format(value, dec, grp, sys)` | calculator/NumberFormatter.ets | 数字→展示字符串 |
| `ErrorFlags.syntax_error` 等 | model/ErrorFlags.ets | 5 个全局 boolean 错误位 |

### 新增接口契约
```ts
// common/UnitConverter.ets
class UnitConverter {
  static convert(value: number, from: string, to: string): number
  // 跨维度 / 未知单位 → 返回 NaN；调用方需检查 isNaN
  static listDimensions(): string[]
  static listUnits(dimension: string): string[]
}

// common/NaturalLanguageParser.ets
interface NLParseResult {
  isUnitConversion: boolean
  value: number
  fromUnit: string
  toUnit: string
}
class NaturalLanguageParser {
  static parse(input: string): NLParseResult | null
  // 不是 NL 模式 → 返回 null；NL 模式但单位不合法 → 仍返回结构，由 UnitConverter 校验
}
```

## 公共组件或函数识别

### 可复用
- **`NumberFormatter.format`**：换算结果出来后统一走该方法，输出与原计算结果一致
- **`ErrorFlags` 模式**：UnitConverter 可选地复用 ErrorFlags（添加 `unit_mismatch` / `unknown_unit` 两个新位），保持错误处理一致性
- **`@Watch('expression')` 模式**：View 层已有的"expression 变化触发计算"模式
- **`@kit.ArkUI.promptAction.showToast`**：用于"已复制"等提示，可扩展到"换算成功"提示

### 测试能力
- **单元测试能力**: ✅（hypium + hamock，运行 `hvigorw --no-daemon test`）
- **UI 自动化测试能力**: ✅（harmonyos-ui-test skill + hdc + 模拟器 127.0.0.1:5555）
- **端到端集成测试能力**: ✅（可真实点开 app + 键入 NL + 验证 result）
- 不能跑的实际原因: N/A

## 影响范围分析

### 需要修改的模块/文件
| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` | modify | onEquals 增加 NL 分支；新增 tryUnitConversion 私有方法 |
| `opencalc/entry/src/main/ets/common/UnitConverter.ets` | **new** | 单位换算引擎 |
| `opencalc/entry/src/main/ets/common/NaturalLanguageParser.ets` | **new** | NL 模式识别 |
| `opencalc/entry/src/test/ets/common/UnitConverter.test.ets` | **new** | 单元测试 |
| `opencalc/entry/src/test/ets/common/NaturalLanguageParser.test.ets` | **new** | 单元测试 |
| `opencalc/entry/src/main/ets/model/ErrorFlags.ets` | modify | 可选增加 unit_mismatch / unknown_unit 标志位 |

### 调用链
```
用户按等号
  → CalculatorPage.onEquals()
    → if NaturalLanguageParser.parse(expr) != null
      → if !isNaN(UnitConverter.convert(v, from, to))
        → result = NumberFormatter.format(...)
        → history.push(...)
      → else (unit mismatch / unknown)
        → errorMsg = '单位不匹配' or '未知单位'
    → else (不是 NL)
      → 走原 CalcEngine.evaluate 降级
```

### 影响评估
- **破坏性**：零（新增分支，原路径不动）
- **回归风险**：低（onEquals 入口加 if 守卫，不命中时与原逻辑一致）
- **性能**：单次字符串扫描+查表，< 1ms

## 现有代码分析

### onEquals 关键代码（CalculatorPage.ets:198-220）
```ts
onEquals(): void {
  if (this.expression.length === 0) return
  ErrorFlags.reset()
  try {
    const clean: string = this.expr.getCleanExpression(this.expression, '.', ',')
    const raw: number = this.engine.evaluate(clean, !this.radianMode)
    if (ErrorFlags.division_by_0) { this.errorMsg = '除数不能为零'; ... }
    else if (ErrorFlags.domain_error) { ... }
    else if (ErrorFlags.syntax_error) { ... }
    else if (ErrorFlags.is_infinity) { ... }
    else if (ErrorFlags.require_real_number) { ... }
    else { this.result = fmt; ... history.push(item) ... }
  } catch (_e) { this.errorMsg = '计算错误' }
}
```

**改造点**：在 `try` 块开头增加：
```ts
const nl = NaturalLanguageParser.parse(this.expression)
if (nl != null && nl.isUnitConversion) {
  const r = UnitConverter.convert(nl.value, nl.fromUnit, nl.toUnit)
  if (!isNaN(r)) { result + history; return }
  // 失败 → 设 errorMsg 后 return，不走 CalcEngine
}
```

### 边界条件
- expression 为空 → 已有 `if (length === 0) return` 守卫
- expression 含 "1+2" → NL parse 返回 null → 走 CalcEngine
- expression 含 "100厘米转英寸" → NL parse 成功 → 走 UnitConverter
- expression 含 "5米转千克" → NL parse 成功 → UnitConverter 返回 NaN → errorMsg
- 浮点精度 → `100厘米转英寸` 应得 39.3700787...，测试允许 1e-4 误差

## 风险识别

| # | 风险 | 严重度 | 缓解措施 |
|---|------|-------|---------|
| 1 | 中文 token 与 ASCII 数字混合解析歧义 | 中 | NL parser 用 regex 严格模式，匹配失败即返回 null |
| 2 | 温度维度用通用 toBase/fromBase 错误 | 高 | UnitConverter 内部对 'temperature' 维度独立分支（affine） |
| 3 | NL parse 误判（如 `1+2转3`） | 中 | 测试覆盖：含 `+` `-` `*` `/` 表达式不会被误判为 NL |
| 4 | 单位别名冲突（`m` = 米 = 分钟） | 中 | 不同维度优先级: 在 `dimensions` Map 中按精确度匹配 + 上下文（出现在 to/前还是后） |
| 5 | 浮点精度（摄氏度→华氏度） | 低 | 测试用 1e-4 容差 |
| 6 | 真实 hdc 不可用阻塞 UI 验证 | 中 | 记录阻塞到 todo.md；fallback 到单元测试 + 代码 review |

### 测试能力评估
- 单元测试能力: ✅
- UI 自动化测试能力: ✅（harmonyos-ui-test skill + hdc + 模拟器 127.0.0.1:5555）
- 端到端集成测试能力: ✅

## 测试验证策略

### 单元测试
- `UnitConverter.test.ets`：
  - 长度：米→厘米 (100), 厘米→英寸 (100→39.37), 千米→英里 (1→0.621)
  - 质量：千克→磅 (1→2.205), 克→盎司 (28.35→1)
  - 时间：小时→秒 (1→3600), 天→小时 (1→24)
  - 温度：摄氏度→华氏度 (30→86), 华氏度→摄氏度 (32→0), 开尔文→摄氏度 (273.15→0)
  - 跨维度：米→千克 → NaN
  - 未知单位：米→xyz → NaN
- `NaturalLanguageParser.test.ets`：
  - "100厘米转英寸" → isUnitConversion=true, v=100, from='厘米', to='英寸'
  - "30摄氏度转华氏度" → ...
  - "5ft in cm" → ...
  - "5 m to ft" → ...
  - "1+2" → null（不是 NL）
  - "sin(0)" → null
  - "5xyz转米" → isUnitConversion=true（错误留给 UnitConverter）

### UI 自动化测试
- 启动 app → 进入 CalculatorPage
- 用 hdc 命令输入 `100厘米转英寸`（用 `uitest uiInput text`）
- 点击等号按钮
- 读取显示屏 result 文本，断言 ≈ "39.37"

## 监控运维支持
- 不涉及新增监控（日志）
- 单位表是常量（`dimensions: Map`），无配置项
- 错误提示复用现有 errorMsg 字段

## 关键发现

### 可复用组件或函数
- `NumberFormatter.format`（结果格式化）
- `ErrorFlags`（错误标志模式，可扩展）
- `Expression.getCleanExpression`（字符串预处理，可选）
- `@Watch('expression')` 模式（View 入口）
- `harmonyos-ui-test` skill（UI 自动化测试）

### 风险提示
- **单位别名冲突**（`m`=米=分钟、`s`=秒=南无）需在 NL parser 中按"出现位置+to 关键字前后"消歧
- **温度特殊处理**必须独立分支，不能用通用 toBase/fromBase
- **跨 worktree 复用**: 之前 issue-14 已实现类似功能但未合入 main，本次实现是独立 PR；可参考 issue-14 思路但不应 merge 它的代码（避免被 dev-01 标记"reuse 未授权"）

### 建议事项
- NL parser 与 UnitConverter 严格分层（parser 不查单位表，converter 不解析字符串）
- 单元表声明式（`Map<string, UnitDef[]>`），新增维度零算法改动
- onEquals 入口加守卫而非改 try-catch（保持错误隔离）
- UI 自动化测试若 hdc 阻塞，记录阻塞到 todo.md 不阻塞 commit

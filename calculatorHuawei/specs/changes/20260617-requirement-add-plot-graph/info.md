# Issue #26 代码仓理解 - 函数图像绘制

## 基本信息

- **需求类别**: 新增功能 (requirement-add)
- **需求名称**: 进阶 — 函数图像绘制 (function-graph-plot)
- **分析时间**: 2026-06-17
- **分析范围**: `opencalc/entry/src/main/ets/`(calculator, pages, model, common, preferences) + 资源 + 测试

## 环境能力(来自 .claude/capabilities.json)

- 项目类型: **HarmonyOS**
- 平台: Windows
- bundleName: `com.darkempire78.opencalculator`
- 编译命令: `hvigorw --no-daemon assembleHap`
- 单元测试命令: `hvigorw --no-daemon test`
- 单元测试框架: hypium + hamock
- 测试根目录: `opencalc/entry/src/test`
- **UI 自动化测试能力: ✅ 可用 (hdc + 模拟器)**
- 模拟器: `127.0.0.1:5555` (running)
- hdc 路径: `D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe`
- hvigorw 路径: `D:/Program Files/Huawei/DevEco Studio/tools/hvigor/bin/hvigorw.bat`
- Java: openjdk 21.0.8

## 架构分析

### 整体结构

```
opencalc/entry/src/main/ets/
├── calculator/        # 计算引擎(纯逻辑,无 UI)
│   ├── Expression.ets    # 表达式预处理(预处理符号、%、阶乘等)
│   ├── Calculator.ets    # CalcEngine: 递归下降解析器 + 数学函数
│   └── NumberFormatter.ets
├── pages/             # 页面
│   ├── Index.ets         # 入口(aboutToAppear 中 router.replaceUrl 到 CalculatorPage)
│   ├── CalculatorPage.ets  # 主计算器页(796行,含横竖屏自适应)
│   └── LongPressMenu.ets   # Issue #16 长按菜单
├── common/            # 通用工具
│   ├── NaturalLanguageParser.ets  # Issue #18 NL 解析
│   └── UnitConverter.ets          # Issue #18 单位换算
├── qrcode/            # Issue #13 二维码生成
│   └── QrCodeBuilder.ets   # 纯函数模块,100% 单元测试覆盖
├── history/           # 历史分组
├── model/             # 数据模型
│   ├── ErrorFlags.ets   # 全局错误标志(syntax_error, domain_error, division_by_0 ...)
│   └── Models.ets       # 数据类型(HistoryItem, NumberingSystem, CalculatorPreferences ...)
├── preferences/       # 偏好设置
│   └── PreferencesStore.ets  # 包装 @ohos.data.preferences
└── entryability/
    └── EntryAbility.ets
```

### 模块依赖

```
pages/CalculatorPage ──> calculator/Expression + Calculator + NumberFormatter
                       ──> model/ErrorFlags + Models
                       ──> preferences/PreferencesStore
                       ──> common/NaturalLanguageParser + UnitConverter
                       ──> qrcode/QrCodeBuilder
                       ──> history/HistoryGroup
                       ──> pages/LongPressMenu
```

### 关键模块职责

- **calculator/Calculator.ets** (`CalcEngine`): 核心求值器, `evaluate(equation: string, isDegree: boolean): number`, 解析表达式并返回数值。函数: sin/cos/tan/arcsi/arcco/arcta/ln/log/logtwo/factorial/sqrt/xp (e^x),常量 π (ASCII 960) 和 e (ASCII 101)。错误通过 `ErrorFlags` 全局标志传递。
- **calculator/Expression.ets** (`Expression`): 预处理: `getCleanExpression(calculation, dec, grp)` 把用户输入的显示字符串(`×`, `÷`, `√`, `π`, `e`, `sin⁻¹` 等) 转换为 ASCII 内部表示。
- **model/ErrorFlags.ets**: 共享可变状态,静态字段。提供 `reset()`, `snapshot()`, `restore()`。
- **qrcode/QrCodeBuilder.ets**: Issue #13 模式 — 纯函数模块, 单一职责 (`buildSharePayload`),便于 100% 单元测试。**新模块应遵循此模式。**

## 接口/契约识别

### 现有核心接口(可复用)

```typescript
// calculator/Calculator.ets
class CalcEngine {
  evaluate(equation: string, isDegree: boolean): number
  // equation 必须是 ASCII 内部表示(已通过 Expression.getCleanExpression 转换)
  // isDegree: true=角度模式(默认), false=弧度模式
}

// calculator/Expression.ets
class Expression {
  getCleanExpression(calculation: string, decimalSep: string, groupingSep: string): string
  // 输入: 用户显示字符串(如 "sin⁻¹(0.5)+π")
  // 输出: ASCII 内部表示(如 "arcsi(0.5)+960")
}

// model/ErrorFlags.ets
class ErrorFlags {
  static syntax_error: boolean
  static division_by_0: boolean
  static domain_error: boolean
  static is_infinity: boolean
  static require_real_number: boolean
  static reset(): void
}
```

### 需要扩展的接口

```typescript
// calculator/Calculator.ets (扩展)
class CalcEngine {
  // 已有
  evaluate(equation: string, isDegree: boolean): number
  // 新增:x 变量值(默认 0)
  private xValue: number = 0
  // 新增: 单点求值,失败返回 null
  evaluateAt(expr: string, x: number, isDegree: boolean): number | null
}
```

### ArkUI Canvas API(将使用)

```typescript
Canvas(context: CanvasRenderingContext2D)
  .onReady(() => { /* 拿到 context,调用绘制方法 */ })
  .width('100%').height('100%')

CanvasRenderingContext2D 方法:
- beginPath() / closePath()
- moveTo(x, y) / lineTo(x, y)
- stroke() / fill()
- fillText(text, x, y)
- set strokeStyle / fillStyle / lineWidth / font
- measureText(text) → TextMetrics
```

### 路由方式

- `main_pages.json` 中注册页面
- `router.pushUrl({ url: 'pages/GraphPage', params: {...} })`
- `router.back()` 返回

## 公共组件或函数识别(可复用)

### 测试可复用工具

- `harmonyos-ui-test` skill — UI 自动化测试(基于 hdc + uitest)
- `dfr-fmea-harmony` skill — FMEA 可靠性分析(本需求已使用其结构)

### 代码层可复用

- **`CalcEngine.evaluate()`** — 直接复用作为 `evaluateAt` 的求值后端
- **`Expression.getCleanExpression()`** — 直接复用做表达式预处理
- **`ErrorFlags.reset() / snapshot() / restore()`** — 用于 evaluateAt 隔离错误状态
- **`PreferencesStore.getTheme()`** — 读取主色 (themeIdx → 主色映射在 CalculatorPage.getOp())
- **路由模式** — 参考 `qrcode/QrCodeBuilder` 纯函数模块设计 `PlotUtils`

### 不可复用

- 现有 `pages/CalculatorPage.ets` 包含大量计算器 UI 代码,绘图页是独立页面,不复用其布局
- 现有按钮/输入框样式可参考色调,但不复用具体组件(布局差异大)

## 影响范围分析

### 需要修改/新建的文件

| 文件 | 类型 | 改动概要 |
|------|------|---------|
| `pages/CalculatorPage.ets` | modify | `ToggleRow()` 中加 "📈 绘图" 按钮 + `onGraphClick()` 跳转到 GraphPage |
| `pages/GraphPage.ets` | **new** | 全新绘图页(画布 + 工具栏 + 输入栏 + 错误提示) |
| `pages/Index.ets` | (无改动) | 入口仍 replaceUrl 到 CalculatorPage |
| `resources/base/profile/main_pages.json` | modify | 注册 `pages/GraphPage` |
| `resources/base/element/string.json` | modify | 新增字符串(graph_title, draw_btn, error_*, etc.) |
| `calculator/Calculator.ets` | extend | `CalcEngine` 加 `xValue` 字段 + `evaluateAt(expr, x, isDegree)` 方法 + `parseFactor` 中识别 `x` |
| `common/PlotUtils.ets` | **new** | 纯函数: 采样 `sampleSeries`、坐标变换 `mapToCanvas`、Y 轴范围 `computeYRange`、常量解析 `parseRange` |
| `viewmodels/GraphViewModel.ets` | **new** | 状态管理: 表达式、范围、采样数、series、错误 |
| `test/ets/common/PlotUtils.test.ets` | **new** | 单元测试 PlotUtils(100% 覆盖) |
| `test/ets/calculator/Calculator.test.ets` | **new 或 extend** | 单元测试 `evaluateAt` 各种 x 值 |
| `test/List.test.ets` | modify | 注册新 test suite |

### 调用链

```
CalculatorPage.onGraphClick()
  → router.pushUrl('pages/GraphPage', { expression: currentInput })
    → GraphPage 初始化 GraphViewModel
      → 用户点"绘制"
        → GraphViewModel.compute()
          → for x in [xMin..xMax]:
              engine.evaluateAt(cleanExpr, x, isDegree)
          → PlotUtils.sampleSeries / computeYRange
          → 触发 onReady 重绘 Canvas
```

## 现有代码分析

### `CalcEngine.evaluate()` 当前限制

- 表达式必须先经 `Expression.getCleanExpression()` 预处理
- ASCII 960 (π) 和 101 (e) 是常量
- 小写字母开头被当作函数名,未知函数名 → `ErrorFlags.syntax_error = true`
- **当前不支持单字母变量 `x`** ← 需要扩展

### `Expression.getCleanExpression()` 关键行为

- 自动插入隐式乘号(`2x` → `2*x`,`(a)(b)` → `(a)*(b)`)
- `π` (希腊字母) 在内部仍识别为 ASCII 960
- 用户输入 `pi` (英文) **不识别**(无法解析为 π)

### 当前 Canvas 使用情况

- `grep -l "Canvas" opencalc/entry/src/main/ets/` **无结果** — 全新引入,需自己写绘制逻辑

### 主题色获取方式

- `PreferencesStore.getTheme()` 返回 0/1/2
- `CalculatorPage.getOp()` 根据 themeIdx 映射颜色字符串(如 `#B4D2E4`)
- 颜色是组件属性,绘图页需读 themeIdx 后自己写 `getCurveColor()` 函数

## 风险识别

### 技术难点

1. **`x` 变量支持** — 需要在 `CalcEngine.parseFactor` 中识别单字母 `x` 并使用 `xValue` 字段值,改动核心求值逻辑。**风险**: 需谨慎避免破坏现有 `sin`/`cos` 等函数解析。**缓解**: 在字母分支的开头特判 `x`(char 120),优先于函数名循环。

2. **大数值下 Y 轴溢出** — `exp(700)` 接近 `Infinity`, 会让 Canvas 绘制失败。**缓解**: `computeYRange` 中限幅 `[-1e10, 1e10]`,超出按 1e10 处理。

3. **除零/`log(0)` 等 NaN** — `evaluateAt` 必须捕获并返回 `null`,不能让异常抛出。**缓解**: 在调用 `evaluate` 前 `ErrorFlags.reset()`,调用后检查 `is_infinity`/`domain_error`/`syntax_error` 任一为真 → 返回 null。

4. **路由参数上限** — ArkUI router params 有 4KB 限制。表达式一般 < 200 字符,远超安全范围,但加 `FMEA-6` 长度校验。

5. **绘制时主线程卡顿** — 200 点求值 < 50ms,但 Canvas 重绘可能在低端设备上 100-200ms。**缓解**: 采样/计算放异步,绘制完成后才 setState 触发 UI 刷新。MVP 范围内可同步。

6. **角度/弧度模式** — Calculator 有 radianMode 偏好,绘图也需支持。**决策**: 默认跟随 radianMode,绘图页不单独设置。

### 与现有功能的兼容性

- **历史记录**: 绘图结果不入历史(单独模块)
- **NL 单位换算**: 绘图表达式不参与 NL 解析
- **长按菜单**: 不影响
- **二维码分享**: 不影响

## 测试验证策略

### 单元测试 (hypium + hamock)

| Suite | 覆盖 |
|-------|------|
| `PlotUtils.test.ets` | sampleSeries(线性函数、定义域外、空)、mapToCanvas(边界、零)、computeYRange(全零、含 null)、parseRange(pi, e, 数字) |
| `Calculator.test.ets` (扩展) | evaluateAt: `sin(0)=0`, `sin(pi)=0`, `2x` 在 x=3 → 6, 错误表达式 → null |

### UI 自动化测试 (harmonyos-ui-test)

| 场景 | 验证 |
|------|------|
| AC-1: 打开绘图页 | uitest: 点 "📈" 按钮 → GraphPage Canvas 节点存在 |
| AC-2: 修改表达式 | 改 `x^2`, 点"绘制" → Canvas 重绘 |
| AC-3: 错误处理 | 输入 `sin(x` → 错误提示 Text 出现 |
| AC-6: 定义域外 | `log(x)`, x ∈ [-5,5] → 曲线在 x≤0 区域断开(可用 pixel 密度粗略验证) |

### 回归测试

- 现有 `Expression.test.ets` / `Calculator.test.ets` 必须全过(确保 `x` 改动不破坏现有解析)
- `List.test.ets` 整体跑通

## 监控运维支持

- 不涉及新监控/日志
- 不涉及新设置项
- 路由跳转失败 → router 自带错误处理

## 关键发现

### 可复用组件或函数

- `CalcEngine.evaluate()` — 求值后端,扩展加 x 变量支持
- `Expression.getCleanExpression()` — 表达式预处理
- `ErrorFlags` 的 `reset/snapshot/restore` — 错误状态隔离
- `qrcode/QrCodeBuilder` 模式 — 纯函数模块,单一职责
- `harmonyos-ui-test` skill — UI 自动化测试
- `dfr-fmea-harmony` skill — FMEA 分析

### 测试能力评估

- 单元测试能力: ✅ (`hypium + hamock` 已配置)
- **UI 自动化测试能力: ✅** (hdc 可用, 模拟器 running, `harmonyos-ui-test` skill)
- 端到端集成测试能力: ✅(通过 UI 自动化)
- 不能跑的实际原因: 无(全部能力可用)

### 风险提示

1. `CalcEngine.parseFactor` 改动需谨慎,回归测试必须全过
2. 路由参数长度限制(FMEA-6)需在 `GraphPage.aboutToAppear` 校验
3. `2x` 隐式乘号需 `addMultiply` 已支持(已确认支持)

### 建议事项

- `PlotUtils` 拆为独立文件,纯函数,100% 单元测试覆盖
- `GraphViewModel` 使用 `@Observed` 装饰器,支持 ArkTS 响应式
- 颜色用 themeIdx 映射,默认蓝色 `#4684E3`
- 表达式含 `x` 校验在 `GraphViewModel.compute()` 入口处做
- 暂时不引入异步/MultiTask,200 点同步足够

## 不涉及章节

- 平台迁移: 不涉及
- 后台任务: 不涉及
- 数据持久化: 不涉及(状态仅内存)
- 国际化: MVP 范围内仅中文,预留资源化字符串
- 权限: 不涉及

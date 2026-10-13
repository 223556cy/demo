# OpenCalc — Android → HarmonyOS 架构分析

> **Date:** 2026-05-07
> **Android source:** [github.com/clementwzk/OpenCalc](https://github.com/clementwzk/OpenCalc)
> **Version:** 3.2.1 (versionCode 54)
> **Source:** 12 Kotlin files, 4,255 lines

---

## 1. 项目概览

OpenCalc 是一个开源科学计算器，支持 BigDecimal 高精度运算、历史记录、多主题、科学模式。

| 指标 | 值 |
|------|-----|
| 源文件 | 12 (.kt, 不含测试) |
| 总行数 | 4,255 |
| Activity | 3 (MainActivity, SettingsActivity, AboutActivity) |
| 第三方库 | **0** (仅 AndroidX + Material + Gson) |
| 架构模式 | 无形式架构（单 Activity + 工具类） |
| UI 框架 | ViewBinding (XML layout) |
| 语言支持 | 35 种语言 |
| 迁移难度 | 🟢 Easy |

## 2. 文件清单

| # | 文件 | 行数 | 类型 | 职责 | 迁移难度 |
|---|------|:---:|------|------|:---:|
| 1 | `activities/MainActivity.kt` | 1,447 | 🟡 View | 主界面 + 按钮绑定 + 计算触发 + 历史交互 | 🟡 |
| 2 | `calculator/Calculator.kt` | 417 | 🟢 Logic | 表达式解析器（递归下降）+ BigDecimal 运算 | 🟢 |
| 3 | `calculator/parser/Expression.kt` | 396 | 🟢 Logic | 输入预处理（%/√/!/隐式乘/括号补齐） | 🟢 |
| 4 | `calculator/parser/NumberFormatter.kt` | ~80 | 🟢 Logic | 数字格式化（千分位、精度） | 🟢 |
| 5 | `history/History.kt` | ~50 | 🟢 Logic | 历史记录数据类 + 持久化 | 🟢 |
| 6 | `history/HistoryAdapter.kt` | ~80 | 🟡 View | RecyclerView Adapter | 🟡 |
| 7 | `MyPreferences.kt` | 123 | 🟢 Logic | SharedPreferences 封装 | 🟡 |
| 8 | `Themes.kt` | 132 | 🟡 View | 主题管理（3 种主题 + 日夜模式） | 🟡 |
| 9 | `activities/SettingsActivity.kt` | 235 | 🟡 View | 设置页面 | 🟡 |
| 10 | `activities/AboutActivity.kt` | ~60 | 🟡 View | 关于页面 | 🟢 |
| 11 | `OpenCalcApp.kt` | 15 | 🔴 Platform | Application 入口 | 🔴 |
| 12 | `util/ScientificMode.kt` | ~30 | 🟢 Logic | 科学模式数据 | 🟢 |

**测试文件：**
| # | 文件 | 行数 | 类型 |
|---|------|:---:|------|
| 13 | `NumberFormatterTest.kt` | ~50 | Unit Test |
| 14 | `ExpressionUnitTest.kt` | ~80 | Unit Test |
| 15 | `MainActivityTests.kt` | ~30 | Instrumentation Test |

## 3. 架构分析

### 3.1 架构模式：无形式架构

```
┌────────────────────────────────────┐
│         MainActivity (1447行)       │
│  ┌──────────────────────────────┐  │
│  │  UI 绑定 (ViewBinding)        │  │
│  │  - 80+ 按钮 onClick           │  │
│  │  - TextWatcher                │  │
│  │  - RecyclerView + Adapter     │  │
│  ├──────────────────────────────┤  │
│  │  计算逻辑（内联调用）          │  │
│  │  - Expression.getCleanExpr()  │  │
│  │  - Calculator.evaluate()      │  │
│  │  - NumberFormatter.format()   │  │
│  ├──────────────────────────────┤  │
│  │  历史管理                      │  │
│  │  - HistoryAdapter             │  │
│  │  - ItemTouchHelper (滑动删除)  │  │
│  │  - 剪贴板                     │  │
│  └──────────────────────────────┘  │
│                                     │
│  依赖：                              │
│  MyPreferences, Themes,              │
│  Calculator, Expression,             │
│  HistoryAdapter, ScientificMode      │
└────────────────────────────────────┘
```

MainActivity 是典型的 "God Activity"——1447 行包含了 UI 初始化、按钮事件、计算流程、历史交互、剪贴板、触觉反馈、弹出菜单、生命周期管理。Android 小项目常见模式。

### 3.2 核心计算引擎

```
用户输入: "sin(30)+5!"
     │
     ▼
Expression.getCleanExpression()
  ├── replaceSymbolsFromCalculation()  → 替换 ×÷√log 等符号
  ├── addMultiply()                    → 补隐式乘号
  ├── formatSquare()                   → √5 → sqrt(5)
  ├── getPercentString()               → % → /100
  ├── formatFactorial()                → 5! → factorial(5)
  └── addParenthesis()                 → 补缺失 )
     │
     ▼
Calculator.evaluate(equation, isDegreeMode)
  ├── 递归下降解析器
  │   parseExpression → +/-
  │   parseTerm       → */# /  (multiply/divide/modulo)
  │   parseFactor     → unary +/-/()/数字/函数/^
  └── BigDecimal 高精度运算
      ├── sqrt (Newton's method / API 33+)
      ├── factorial (Lanczos approximation for non-int)
      ├── sin/cos/tan/arcsin/arccos/arctan
      ├── ln/log2/log10/exp
      └── exponentiation (支持小数指数)
     │
     ▼
NumberFormatter.format(result, precision, grouping, decimal)
  → "1,234.567"
```

### 3.3 数据流

```
用户点击按钮
  │
  ▼
MainActivity.onClick(Button)
  ├── 普通输入: 追加到 EditText
  ├── 退格: 删除最后一个字符
  ├── "=": Expression → Calculator → NumberFormatter → 显示结果
  │           └→ 添加到 HistoryAdapter
  ├── "AC": 清空
  └── 科学函数: 切换科学面板
```

### 3.4 持久化

| 数据 | 存储方式 | 键 |
|------|---------|-----|
| 计算历史 | Gson JSON → SharedPreferences | `KEY_HISTORY` |
| 主题选择 | SharedPreferences int | `THEME`, `FORCE_DAY_NIGHT` |
| 振动开关 | SharedPreferences bool | `KEY_VIBRATION_STATUS` |
| 防休眠 | SharedPreferences bool | `KEY_PREVENT_PHONE_FROM_SLEEPING` |
| 历史数量 | SharedPreferences int | `KEY_HISTORY_SIZE` |
| 科学模式 | SharedPreferences bool | `KEY_SCIENTIFIC_MODE_ENABLED_BY_DEFAULT` |
| 角度/弧度 | SharedPreferences bool | `KEY_RADIANS_INSTEAD_OF_DEGREES_BY_DEFAULT` |
| 数字精度 | SharedPreferences int | `KEY_NUMBER_PRECISION` |

## 4. 迁移策略

### 4.1 迁移层序（深度优先）

```
Phase 1: 纯逻辑层（Calculator + Expression + NumberFormatter + ScientificMode）
  → 直接语法翻译 Kotlin → ArkTS，零 Android 依赖
  → 验证：单元测试通过（移植 Android 测试用例）

Phase 2: 数据层（History model + preferences）
  → History 数据类 → ArkTS interface
  → SharedPreferences → @ohos.data.preferences

Phase 3: UI 层（MainActivity → CalculatorPage）
  → ViewBinding XML → ArkUI 声明式
  → Button onClick → @State + 事件绑定
  → RecyclerView + HistoryAdapter → List + ForEach
  → 主题 → @StorageLink + AppStorage

Phase 4: 辅助页面（Settings + About）
  → SettingsActivity → SettingsPage
  → AboutActivity → AboutPage

Phase 5: 打磨
  → 触觉反馈 → vibrator
  → 多语言 → resource string.json（35 语言）
  → 编译 → BUILD SUCCESSFUL
  → 5 项验收标准
```

### 4.2 关键映射

| Android | HarmonyOS |
|---------|-----------|
| `BigDecimal` | `BigDecimal` (ArkTS 无原生支持，需手动实现或用 number) |
| `Math.sin/cos/tan...` | `Math.sin/cos/tan...` (ArkTS 标准库有) |
| `SharedPreferences` | `@ohos.data.preferences` |
| `RecyclerView + Adapter` | `List + ForEach` |
| `ViewBinding` | ArkUI 声明式 |
| `PopupMenu` | `Menu` 组件 或自定义 |
| `ItemTouchHelper` | `ListItem.swipeAction()` |
| `ClipboardManager` | `@ohos.pasteboard` |
| `HapticFeedback` | `@ohos.vibrator` |
| `WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON` | `window.setWindowKeepScreenOn(true)` |
| `Activity` lifecycle | `@Entry` page lifecycle |
| `AlertDialog` | `AlertDialog` 或 `CustomDialog` |
| `Toast` | `promptAction.showToast()` |
| `Gson` | 手动 JSON 序列化 (简单数据) |

### 4.3 关键决策

| ADR | 决策 | 理由 |
|-----|------|------|
| ADR-001 | BigDecimal 精度方案 | ArkTS number 为 IEEE 754 double，精度足够计算器场景（15-17位有效数字）。不实现完整 BigDecimal，用 number 替代。 |
| ADR-002 | 单页面架构 | 用 Tabs 或条件渲染替代 Settings/About 独立页面，减少路由复杂度 |
| ADR-003 | 表达式解析器直接移植 | Calculator.evaluate() 的递归下降解析器是纯算法，逐行翻译即可 |

---

## 5. 模块分解（TASK_BOARD）

见 [TASK_BOARD.md](TASK_BOARD.md)

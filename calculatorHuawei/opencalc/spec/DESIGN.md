# OpenCalc HarmonyOS Migration — Design

> **Date:** 2026-05-07
> **Android:** OpenCalc 3.2.1 (12 files, 4,255 lines Kotlin)
> **Target:** HarmonyOS ArkTS, single-HAP

---

## 1. 架构设计

```
entry/src/main/ets/
├── pages/
│   └── CalculatorPage.ets        ← @Entry 主页面（替代 MainActivity 1447行）
├── components/
│   ├── DisplayPanel.ets          ← 显示屏（表达式+结果双行）
│   ├── ButtonGrid.ets            ← 按钮网格
│   ├── HistoryPanel.ets          ← 历史列表面板
│   └── SettingsPanel.ets         ← 设置面板
├── calculator/
│   ├── Calculator.ets            ← 表达式解析器 + 运算（移植自 Calculator.kt）
│   ├── Expression.ets            ← 输入预处理（移植自 Expression.kt）
│   └── NumberFormatter.ets       ← 数字格式化（移植自 NumberFormatter.kt）
├── model/
│   └── Models.ets                ← CalculatorError, HistoryItem, Preferences, Themes
├── preferences/
│   └── PreferencesStore.ets      ← 偏好存储封装（替代 MyPreferences.kt）
└── entryability/
    └── EntryAbility.ets          ← UIAbility 入口
```

## 2. 数据模型

```typescript
// 计算错误类型
enum CalculatorError {
  NONE = 'none',
  DIVISION_BY_ZERO = 'division_by_zero',
  DOMAIN_ERROR = 'domain_error',
  SYNTAX_ERROR = 'syntax_error',
  INFINITY = 'infinity',
  REQUIRE_REAL = 'require_real_number'
}

// 历史记录
interface HistoryItem {
  id: number
  expression: string   // "sin(30)+5!"
  result: string        // "120.5"
  timestamp: number
}

// 偏好设置
interface CalculatorPreferences {
  theme: number              // 0=默认 1=AMOLED 2=MaterialYou
  forceDayNight: number      // 0=系统 1=浅色 2=深色 3=AMOLED
  vibrationEnabled: boolean
  preventSleep: boolean
  historySize: number        // 默认 100
  scientificModeDefault: boolean
  radiansDefault: boolean
  numberPrecision: number    // 默认 12
  decimalSeparator: string   // 小数点符号
  groupingSeparator: string  // 千分位符号
}
```

## 3. 核心计算引擎移植

### BigDecimal → number

Android 使用 `java.math.BigDecimal` 实现高精度。ArkTS 无此类型，使用 `number`（IEEE 754 double，15-17 位有效数字）。对于计算器场景足够。

### sqrt 实现

Android 有 Newton's method 实现（API < 33）。ArkTS 用 `Math.sqrt()` 替代。

### 递归下降解析器

逐行翻译 Kotlin → ArkTS，保留完全相同的算法结构：
```
parseExpression() → parseTerm() → parseFactor() → 递归
```

## 4. UI 设计

计算器主页面采用单页面 + 面板切换：

```
┌─────────────────────┐
│     DisplayPanel     │  ← 表达式行（小字）
│                      │  ← 结果行（大字）
├─────────────────────┤
│                     │
│    ButtonGrid       │  ← 5列按钮网格
│                     │  ← 基础模式 / 科学模式切换
│                     │
├─────────────────────┤
│    HistoryPanel      │  ← 历史列表（底部滑动面板）
│   (可折叠)           │
└─────────────────────┘
```

设置 + 关于 → 使用底部弹出 `CustomDialog`，不单独路由页面。

## 5. 关键技术映射

| Android | HarmonyOS | 备注 |
|---------|-----------|------|
| `BigDecimal` 运算 | `number` 运算 | 精度差异 < 1e-10，计算器可接受 |
| `kotlin.math.*` | `Math.*` | ArkTS 标准库有全套 |
| `SharedPreferences` | `@ohos.data.preferences` | async API |
| `Gson.toJson/fromJson` | 手动 `JSON.stringify/parse` | 数据简单 |
| `RecyclerView` | `List` + `ForEach` | 更简洁 |
| `ItemTouchHelper` | `ListItem.swipeAction()` | 原生支持 |
| `ClipboardManager` | `@ohos.pasteboard` | systemPasteboard |
| `HapticFeedback` | `@ohos.vibrator` | startVibration |
| `ViewBinding` | ArkUI 声明式 | 完全不同的范式 |
| `AlertDialog` | `AlertDialog` / `CustomDialog` | 有对应组件 |
| `Toast` | `promptAction.showToast()` | 有对应 API |
| `PopupMenu` | 自定义 `Menu` 或 `ActionSheet` | |

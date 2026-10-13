# Issue #11 实时预览 — 代码仓理解

## 基本信息

- **需求类别**：新增功能（New Requirement）
- **需求名称**：realtime-preview
- **分析时间**：2026-06-12
- **分析范围**：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`、`calculator/Expression.ets`、`calculator/Calculator.ets`、`calculator/NumberFormatter.ets`、`model/ErrorFlags.ets`、`model/Models.ets`

## 架构分析

### 模块结构图

```
opencalc/entry/src/main/ets/
├── pages/
│   ├── Index.ets                    # 启动页（router.replaceUrl → CalculatorPage）
│   └── CalculatorPage.ets           # 主计算器页面 (427行)  ← 核心改动目标
├── calculator/
│   ├── Expression.ets               # 表达式预处理（百分号、阶乘、隐式乘等）
│   ├── Calculator.ets               # 计算引擎（递归下降解析器）
│   └── NumberFormatter.ets          # 数字格式化（千分位/小数）
├── model/
│   ├── Models.ets                   # HistoryItem / NumberingSystem 类型定义
│   └── ErrorFlags.ets               # 静态错误标志（共享可变状态）
├── entryability/                    # Ability 入口
└── preferences/
    └── PreferencesStore.ets         # 持久化偏好/历史
```

### 核心模块职责

| 模块 | 职责 | 关键导出 |
|------|------|----------|
| CalculatorPage.ets | UI 渲染、按钮事件、状态管理 | `@Component CalculatorPage` |
| Expression.ets | 表达式字符串预处理 | `getCleanExpression(input, dec, grp): string` |
| Calculator.ets (CalcEngine) | 表达式求值 | `evaluate(eq, isDegree): number` |
| NumberFormatter.ets | 数值显示格式化 | `static format(text, dec, grp, sys): string` |
| ErrorFlags.ets | 错误标志（静态共享） | 5 个 static boolean + reset() |

### 依赖关系

```
CalculatorPage
  ├─→ Expression.getCleanExpression     (无副作用，纯函数)
  ├─→ CalcEngine.evaluate               (无副作用，每次创建新实例)
  ├─→ NumberFormatter.format            (static，无副作用)
  ├─→ ErrorFlags                        (静态可变状态，副作用点 ⚠️)
  └─→ PreferencesStore                  (异步持久化)
```

## 接口/契约识别

### 复用接口（无修改）

#### `Expression.getCleanExpression`
```typescript
getCleanExpression(calculation: string, decimalSeparatorSymbol: string, groupingSeparatorSymbol: string): string
```
- **副作用**：可能设置 `ErrorFlags.syntax_error = true`（如遇到 `%%`）
- **返回值**：清洗后的数学表达式（已替换 ×→*, ÷→/, 处理百分号等）
- **使用约束**：输入必须是合法的"显示表达式"，不要求完全可求值

#### `CalcEngine.evaluate`
```typescript
evaluate(equation: string, isDegree: boolean): number
```
- **副作用**：可能设置 5 个 `ErrorFlags.*` 之一
- **返回值**：数值结果
- **使用约束**：输入必须是 `getCleanExpression` 处理后的字符串

#### `NumberFormatter.format`
```typescript
static format(text: string, dec: string, grp: string, sys: NumberingSystem): string
```
- **副作用**：无
- **返回值**：带千分位的显示字符串
- **使用约束**：输入应是数字字符串（含小数点、负号、e 记数法）

#### `ErrorFlags` 静态字段
- `syntax_error` / `division_by_0` / `domain_error` / `is_infinity` / `require_real_number`
- `reset()` 方法

## 公共组件或函数识别

### 可复用组件
- `BtnOpPct` / `BtnDigit` / `BtnFn` / `BtnActAC` / `BtnActBS` / `BtnEq` — 已在 CalculatorPage.ets 中实现的按钮 builder 模式
- `DisplayPanel` — 显示屏区域（核心修改点）
- `getBg/getBtnBg/getOp/getT1/getT2` 等主题相关 getter

### 可复用函数
- `NumberFormatter.format` — 格式化预览结果
- `Expression.getCleanExpression` — 预处理表达式
- `CalcEngine.evaluate` — 计算结果

## 影响范围分析

### 需修改的文件
| 文件 | 改动 | 估行数 |
|------|------|--------|
| CalculatorPage.ets | 新增 @State preview + computePreview + @Watch + UI 行 | +20 行 |
| (test) Expression.test.ets / 新增 RealtimePreview.test.ets | 新增 computePreview 单元测试 | +100 行 |

### 复用关系图（实时预览调用链）
```
用户按键 → onDigit/onOp/onBS/onAC
  → expression @State 变化
  → @Watch('expression') 触发 onExpressionChange()
  → computePreview(expression)
    ├─ ErrorFlags.snapshot()  保存现场
    ├─ 末字符白名单过滤
    ├─ expr.getCleanExpression(input, '.', ',')  // 可能 syntax_error
    ├─ engine.evaluate(clean, !radianMode)        // 可能任一 ErrorFlags
    ├─ NumberFormatter.format(raw, ...)
    └─ ErrorFlags.restore()  恢复现场
  → preview @State 更新
  → DisplayPanel 重新渲染（preview Text）
```

### 影响评估
- **现有功能影响**：onEquals 流程不变；computePreview 在 expression 变化时副作用隔离
- **风险点**：ErrorFlags 静态共享状态（已有上一变更 SR-09 处理）
- **回归范围**：onEquals、onCopy、onHistoryTap、HistoryPanel 渲染

## 现有代码分析

### DisplayPanel 当前结构（CalculatorPage.ets:237-265）
```typescript
@Builder DisplayPanel() {
  Column() {
    // 第一行：expression（用户输入）
    Text(this.expression.length > 0 ? this.expression : ' ')
      .fontSize(14 或 18)
      .fontColor(this.getT2())   // 次要色
      .textAlign(TextAlign.End)  // 右对齐
      .maxLines(3)

    // 第二行：result 或 errorMsg
    if (this.errorMsg.length > 0) {
      Text(this.errorMsg)  // 错误样式
    } else {
      Text(this.result.length > 0 ? this.result : '0')
        .fontSize(28 或 36)
        .fontWeight(FontWeight.Bold)
        .fontColor(this.getT1())  // 主色
    }
  }
}
```

### onEquals 当前逻辑（CalculatorPage.ets:89-111）
- ErrorFlags.reset() → expr.getCleanExpression → engine.evaluate → 检查 5 种 ErrorFlags → 格式化 → 存历史

### 关键变量
| 变量 | 类型 | 当前值 | 变化时机 |
|------|------|--------|----------|
| expression | @State string | '' | 数字/运算符/AC/BS 时变化 |
| result | @State string | '' | 仅 onEquals 后更新 |
| errorMsg | @State string | '' | onEquals 后或异常时更新 |
| radianMode | @State boolean | false | 偏好设置影响 |

## 风险识别

| 风险 | 等级 | 缓解 |
|------|------|------|
| ErrorFlags 静态污染预览计算 | 高 | snapshot + restore 模式（与上一变更一致） |
| 末位运算符导致 evaluate 异常 | 中 | 白名单过滤（末位必须是数字/右括号/数字常量/百分号） |
| 性能问题（每次按键同步计算） | 低 | 表达式 < 50 字符 + 单次 evaluate < 1ms |
| 横屏布局溢出 | 低 | preview 行 maxLines=1，fontSize 缩小 |
| ArkTS @Watch 触发时机 | 中 | 经验证：@State 赋值后下一帧触发；同步 set 不会无限递归 |
| 测试环境无 hvigorw | 中 | 复用上一变更的 Node 端口测试方案（.test.mjs + .port.mjs） |

## 测试验证策略

### 测试场景
1. **基础计算**：`1+2` → `3`、`5*6` → `30`、`100/4` → `25`
2. **不完整表达式**：`1+`、`sin(`、`(1+2` → 空
3. **错误表达式**：`1++2`、`1÷0` → 空
4. **百分号**：`50+10%` → `55`（与上一变更协同）
5. **函数**：`sin(0)` → `0`、`cos(0)` → `1`
6. **格式一致**：`1000+2000` → `3,000`
7. **嵌套括号**：`(1+2)*(3+4)` → `21`
8. **错误隔离**：先 `1÷0`（不更新 preview）再 `1+1`（preview=2）→ onEquals 不受影响
9. **AC 清空**：任意表达式 → AC → preview=""

### 验证方法
- 单元测试：computePreview 函数（Node 端口测试 + ArkTS 测试并行）
- 端到端：构建 hvigorw + 真机/模拟器观察 UI（铁律 7 需真实跑测）

### 回归范围
- onEquals 流程
- 百分号按钮（上一变更）
- 历史记录持久化

## 监控运维支持

不涉及（本地计算 App，无远程监控需求）

## 关键发现

### 可复用资源
- `Expression.getCleanExpression` 完整可复用
- `CalcEngine.evaluate` 完整可复用
- `NumberFormatter.format` 完整可复用
- `ErrorFlags.reset` 完整可复用
- 上一变更（percent-button）的 Node 端口测试基础设施可复用

### 风险提示
- ErrorFlags 静态状态是关键风险点，必须 snapshot+restore
- 测试需双轨（Node 端口 + ArkTS），铁律 7 要求真实跑测

### 建议事项
1. computePreview 实现为纯函数（接收 expression、radianMode，返回 preview），便于单元测试
2. 错误状态处理：捕获 ErrorFlags.* 任何一位为 true → preview = ""
3. UI 行 maxLines=1，避免长表达式换行
4. 实时预览触发器使用 @Watch('expression')，与手动调用兼容
5. 测试环境无 hvigorw：使用上一变更的 .test.mjs + .port.mjs 方案

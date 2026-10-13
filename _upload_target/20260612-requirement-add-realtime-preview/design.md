# 组件设计 — Issue #11 实时预览功能

> aid-workflow 20260612-requirement-add-realtime-preview · PLANNING step8 产出物
> 基线：proposal.md / delta-spec.md / info.md

---

## 1. 设计目标

在 CalculatorPage.ets 的 DisplayPanel 中，**expression 行下方、result 行上方**新增一行 `preview`，实现：
- 每次 expression 变化时同步计算预览值（无需按等号）
- 不完整 / 错误表达式显示空字符串（不报错）
- 等号按下后 preview 与 result 一致
- 与现有 5 列布局、横竖屏切换、主题切换、错误恢复共存

---

## 2. 架构设计

### 2.1 模块依赖图

```
┌─────────────────────────────────────────────────────────┐
│ CalculatorPage (ArkTS @Component)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ @State expression: string                        │   │
│  │ @State preview: string        ← NEW              │   │
│  │ @State result: string                            │   │
│  │ @Watch('expression')                              │   │
│  │   onExpressionChange()  ← NEW                     │   │
│  │   private computePreview(expr, radianMode) NEW    │   │
│  └──────────────────────────────────────────────────┘   │
│       │            │                  │                  │
│       ▼            ▼                  ▼                  │
│  Expression    CalcEngine       NumberFormatter         │
│  (existing)    (existing)       (existing)              │
│       │            │                                     │
│       └────────────┴────► ErrorFlags (static, shared)   │
│                                                          │
│  DisplayPanel() @Builder  ← add Text(this.preview)     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户按键
   │
   ▼
onDigit / onOp / onFunc / onConst / onBS / onAC
   │
   ▼
this.expression = <new>     ← @State 触发 UI 刷新
   │
   ▼
@Watch('expression') 回调 → onExpressionChange()
   │
   ▼
this.preview = computePreview(this.expression, this.radianMode)
   │
   ├─► snapshot ErrorFlags
   ├─► Expression.getCleanExpression(input, '.', ',')
   ├─► 检查 ErrorFlags.syntax_error → snapshot/restore
   ├─► CalcEngine.evaluate(clean, !radianMode)
   ├─► 检查 ErrorFlags 任一位 → snapshot/restore
   ├─► NumberFormatter.format(raw, '.', ',', INTERNATIONAL)
   └─► restore ErrorFlags（无论异常与否）
   │
   ▼
preview @State 更新 → DisplayPanel 重新渲染
```

### 2.3 触发器策略

| 候选 | 优点 | 缺点 | 决定 |
|------|------|------|------|
| `@Watch('expression')` | 声明式、自动触发 | ArkTS 装饰器，需语法正确 | ✅ 采用 |
| 手动在每个 onXxx 末尾调用 `onExpressionChange()` | 显式 | 易遗漏、需改 6 处 | ❌ |
| `aboutToAppear` 监听 expression getter | 无 | 不符合 ArkTS 数据流 | ❌ |

**理由**：`@Watch` 是 ArkTS 推荐的副作用触发模式，与现有 `onEquals()` / `onHistoryTap()` 等命令式方法形成清晰分层：状态变更 → UI 重算。

---

## 3. 组件 API 契约

### 3.1 新增 @State

```typescript
/** 实时预览值：当前 expression 的实时计算结果（已格式化），空字符串表示无预览 */
@State preview: string = ''
```

### 3.2 新增 @Watch

```typescript
@Watch('expression')
onExpressionChange(): void {
  this.preview = this.computePreview(this.expression, this.radianMode)
}
```

> 注：ArkTS 装饰器顺序：@Component → @Entry → 字段；@Watch 装饰器紧贴方法，**不能用于构造方法**。本设计按官方规则排列。

### 3.3 新增私有方法

```typescript
/**
 * 计算表达式实时预览（纯函数，副作用隔离）
 * @param exprStr 用户当前输入的表达式字符串
 * @param radianMode true=弧度模式，false=角度模式
 * @returns 格式化后的预览字符串，错误/不完整时返回空字符串
 */
private computePreview(exprStr: string, radianMode: boolean): string {
  // 1. 空表达式 → ""
  if (exprStr.length === 0) return ''

  // 2. 末字符白名单：必须是数字 / 右括号 / 百分号 / 阶乘结尾
  const lastChar: string = exprStr.charAt(exprStr.length - 1)
  if (!this.isLastCharComputable(lastChar, exprStr)) return ''

  // 3. ErrorFlags 快照（避免污染主流程）
  const snap = ErrorFlags.snapshot()

  try {
    // 4. 预处理
    const clean: string = this.expr.getCleanExpression(exprStr, '.', ',')
    if (ErrorFlags.syntax_error) {
      ErrorFlags.restore(snap)
      return ''
    }

    // 5. 求值
    const raw: number = this.engine.evaluate(clean, !radianMode)
    if (ErrorFlags.division_by_0 || ErrorFlags.domain_error ||
        ErrorFlags.syntax_error || ErrorFlags.is_infinity ||
        ErrorFlags.require_real_number) {
      ErrorFlags.restore(snap)
      return ''
    }

    // 6. 格式化
    const formatted: string = NumberFormatter.format(raw.toString(), '.', ',', NumberingSystem.INTERNATIONAL)
    ErrorFlags.restore(snap)
    return formatted
  } catch (_e) {
    ErrorFlags.restore(snap)
    return ''
  }
}

/**
 * 末字符是否可参与求值
 */
private isLastCharComputable(lastChar: string, exprStr: string): boolean {
  // 数字、小数点 → OK
  if ((lastChar >= '0' && lastChar <= '9') || lastChar === '.') return true
  // 右括号 → OK
  if (lastChar === ')') return true
  // 百分号 → OK（"10%"可求值为 0.1）
  if (lastChar === '%') return true
  // 阶乘结尾 → OK
  if (lastChar === '!') return true
  // 常量结尾（π、e）→ OK
  if (lastChar === 'π' || lastChar === 'e') return true
  // 闭合右括号 + 阶乘/百分号组合（"5)!"、"5)%"）→ OK
  // 函数名结尾（sin/cos/... 等小写字母结尾）→ 不可直接求值
  // 运算符 (+-×÷%) 或左括号 → 不可
  return false
}
```

### 3.4 ErrorFlags 快照辅助

为支持 computePreview 的副作用隔离，ErrorFlags 需要增加两个静态方法：

```typescript
// opencalc/entry/src/main/ets/model/ErrorFlags.ets （扩展）
export class ErrorFlags {
  static syntax_error: boolean = false
  static division_by_0: boolean = false
  static domain_error: boolean = false
  static is_infinity: boolean = false
  static require_real_number: boolean = false

  static reset(): void { /* existing */ }

  /** 快照当前所有错误标志（用于预览计算前保存现场） */
  static snapshot(): boolean[] {
    return [
      ErrorFlags.syntax_error,
      ErrorFlags.division_by_0,
      ErrorFlags.domain_error,
      ErrorFlags.is_infinity,
      ErrorFlags.require_real_number
    ]
  }

  /** 从快照恢复错误标志（用于预览计算后恢复现场） */
  static restore(snap: boolean[]): void {
    ErrorFlags.syntax_error = snap[0]
    ErrorFlags.division_by_0 = snap[1]
    ErrorFlags.domain_error = snap[2]
    ErrorFlags.is_infinity = snap[3]
    ErrorFlags.require_real_number = snap[4]
  }
}
```

> **与现有 SR-09 的协同**：`ErrorFlags.snapshot/restore` 是无副作用的读写快照，与现有 `onOp` 中的 `ErrorFlags.reset()` 完全兼容——reset 清零，snapshot/restore 保存/恢复。

### 3.5 UI 插入点

DisplayPanel 当前结构（CalculatorPage.ets:237-265）：

```typescript
@Builder DisplayPanel() {
  Column() {
    // 现有：expression 行（横屏带历史切换）
    if (this.isLandscape) { /* 横屏 expression + ▶ */ }
    else { Text(this.expression) }

    // 【NEW】preview 行
    Text(this.preview.length > 0 ? this.preview : ' ')
      .fontSize(this.isLandscape ? 12 : 14)
      .fontColor(this.getT2())
      .width('100%')
      .textAlign(TextAlign.End)
      .padding({ right: 12, left: 12, top: 2, bottom: 2 })
      .maxLines(1)

    // 现有：result / errorMsg 行
    if (this.errorMsg.length > 0) { Text(this.errorMsg) }
    else { Text(this.result) }
  }
}
```

> 视觉层级：preview 比 result 字号小（14 vs 36）、同色（getT2 次要灰），作为"提示行"存在。

---

## 4. 状态机

```
                   expression 变化
                        │
                        ▼
              ┌──────────────────┐
              │ computePreview() │
              └──────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   expr 为空       末字符不合法      预处理/求值
        │               │               │
        ▼               ▼               ▼
    preview=""      preview=""        ┌────────────┐
                                      │ 无错误？   │
                                      └────────────┘
                                       │        │
                                       ▼        ▼
                                  preview=fmt  ErrorFlags→true
                                               │
                                               ▼
                                            preview=""
```

---

## 5. 性能分析

| 操作 | 耗时（估） | 频次 | 风险 |
|------|----------|------|------|
| `Expression.getCleanExpression` | < 1ms (50 字符) | 每次按键 | 低 |
| `CalcEngine.evaluate` | < 1ms (50 字符) | 每次按键 | 低 |
| `NumberFormatter.format` | < 0.1ms | 每次按键 | 低 |
| `ErrorFlags.snapshot/restore` | < 0.01ms | 每次按键 | 无 |
| **合计** | **< 3ms** | **每次按键** | **< 100ms 目标** |

ArkUI 帧间隔为 16ms（60fps），3ms 同步计算不影响 UI 流畅度。无需 debounce。

---

## 6. 测试矩阵（对接 delta-spec.md 的 AC 验收用例）

| 用例 | 输入 expression | 末字符检查 | 预期 preview | 关联 AC |
|------|----------------|-----------|-------------|---------|
| TC-RP-01 | "" | - | "" | AC-RP-01 |
| TC-RP-02 | "1" | 数字 OK | "1" | AC-RP-01（隐式） |
| TC-RP-03 | "1+2" | 数字 OK | "3" | AC-RP-02 |
| TC-RP-04 | "5-10" | 数字 OK | "-5" | AC-RP-03 |
| TC-RP-05 | "1+" | 运算符 NO | "" | AC-RP-04 |
| TC-RP-06 | "sin(0" | 左括号 NO | "" | AC-RP-05 |
| TC-RP-07 | "1++2" | 数字 OK（eval 失败） | "" | AC-RP-06 |
| TC-RP-08 | "sin(0)" | 右括号 OK | "0" | AC-RP-07 |
| TC-RP-09 | "50+10%" | 百分号 OK | "55" | AC-RP-08 |
| TC-RP-10 | "1+(" | 左括号 NO | "" | AC-RP-09 |
| TC-RP-11 | "1000+2000" | 数字 OK | "3,000" | AC-RP-11 |
| TC-RP-12 | "(1+2)*(3+4)" | 右括号 OK | "21" | AC-RP-15 |
| TC-RP-13 | "1+2*3/4-5" | 数字 OK | "-2.5" | AC-RP-14 |
| TC-RP-14 | "1÷0" | 数字 OK（division_by_0） | "" | (降级) |
| TC-RP-15 | AC 流程 | - | "" | AC-RP-12 |

### 测试基础设施

| 文件 | 角色 |
|------|------|
| `tests/RealtimePreview.port.mjs` | ComputePreview 的 Node 端口（独立类） |
| `tests/RealtimePreview.test.mjs` | node:test 用例，验证 TC-RP-01 ~ TC-RP-15 |

> 与 Issue #9 的 Expression 单元测试模式一致（已有 `Expression.port.mjs` + `Expression.test.mjs` 在 `specs/changes/20260611-requirement-add-percent-button/tests/`）。本次复用 expression-eval.mjs 作为 safeEval。

---

## 7. 风险与缓解

| 风险 | 等级 | 缓解 | 状态 |
|------|------|------|------|
| ErrorFlags 静态污染 | 高 | snapshot + restore（在 ErrorFlags 增加方法） | ✅ 设计已纳入 |
| 末位运算符导致 evaluate 行为不可预期 | 中 | 末字符白名单过滤（isLastCharComputable） | ✅ 设计已纳入 |
| 横屏布局溢出 | 低 | preview 行 maxLines=1 + fontSize 12 | ✅ 设计已纳入 |
| @Watch 触发时机不确定 | 中 | 测试验证：通过 `tests/RealtimePreview.test.mjs` 模拟状态变化 | ✅ 测试已规划 |
| 测试环境无 hvigorw | 中 | 复用上一变更的 Node 端口测试方案 | ✅ 测试基础设施已就绪 |

---

## 8. 设计决策记录

| 决策 | 选项 | 理由 |
|------|------|------|
| 触发方式 | @Watch('expression') vs 手动调用 | @Watch 声明式、不易遗漏 |
| 末字符白名单 | 实现 isLastCharComputable | 简单高效，避免 eval 副作用 |
| 错误隔离 | snapshot/restore vs try/catch | snapshot/restore 在外层 try/catch 内部，保证异常也恢复 |
| ErrorFlags 扩展 | 增加 snapshot/restore vs 复用 reset | reset 清零会破坏主流程状态；snapshot/restore 是无损保存/恢复 |
| Preview 行位置 | expression 下方 vs result 上方 vs 顶部 | expression 下方 + result 上方（用户决策） |
| Preview 行样式 | 同 result vs 区分 | 区分：fontSize 14/36、getT2/getT1；视觉层级清晰 |
| 测试方案 | node:test vs ArkTS hypium | 复用上一变更基础设施，**真实跑测**满足铁律 7 |

---

## 9. 实施顺序（IMPLEMENTING 阶段入口）

1. **ErrorFlags 扩展**（增加 snapshot/restore） — 无破坏性
2. **CalculatorPage 新增 @State preview** — 无副作用
3. **CalculatorPage 新增 computePreview + onExpressionChange + @Watch** — 核心逻辑
4. **DisplayPanel 新增 preview Text 行** — UI 渲染
5. **单元测试**：
   - `RealtimePreview.port.mjs`：JS 端口（含完整 Eval/Format 模拟）
   - `RealtimePreview.test.mjs`：node:test 用例覆盖 TC-RP-01~15

---

## 10. 文件清单

| 文件 | 类型 | 状态 |
|------|------|------|
| `opencalc/entry/src/main/ets/model/ErrorFlags.ets` | 修改 | +15 行（snapshot/restore） |
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` | 修改 | +40 行（preview/computePreview/@Watch/UI 行） |
| `specs/changes/20260612-requirement-add-realtime-preview/tests/RealtimePreview.port.mjs` | 新增 | ~250 行 |
| `specs/changes/20260612-requirement-add-realtime-preview/tests/RealtimePreview.test.mjs` | 新增 | ~80 行 |

**总改动估算**：~50 行 ArkTS 修改 + ~330 行测试代码
**复杂度**：S（与 proposal.md 一致）
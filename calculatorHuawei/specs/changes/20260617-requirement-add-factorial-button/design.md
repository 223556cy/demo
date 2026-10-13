# Design: 阶乘按钮 (!) — Issue #21

> **Date**: 2026-06-17
> **Style**: 增量设计(基于现有 `Expression.formatFactorial` + `CalcEngine.fact`)
> **Methodology**: TDD (RED → GREEN → REFACTOR)

---

## 1. 架构概览

阶乘链路已存在,本次只补 UI 入口 + 测试。

```
┌─────────────────────────────────────────────────────────────┐
│  CalculatorPage (UI)                                          │
│  ┌──────────┐   onOp('!')  ┌──────────┐                       │
│  │  ! 按钮   │ ──────────→ │ expression│ ←── 实时预览触发       │
│  └──────────┘             └─────┬────┘                       │
│                                  │ onEquals()                 │
│                                  ▼                            │
│                          Expression.getCleanExpression       │
│                                  │ formatFactorial 改写        │
│                                  ▼                            │
│                            CalcEngine.evaluate                │
│                                  │ fn==='factorial' → fact(x) │
│                                  ▼                            │
│                              result 字符串                    │
└─────────────────────────────────────────────────────────────┘
```

## 2. 组件设计

### 2.1 UI 组件(新增)

**文件**: `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`

**改动**: 在 `scientific=true` 第 2 行末尾插入 `!` 按钮。

**方案 A — 5+1 列(改宽度 18%→16%)**:
```ets
Row() { this.BtnFunc('arcsi'); this.BtnFunc('arcco'); this.BtnFunc('arcta'); this.BtnConst('π'); this.BtnConst('e'); this.BtnOpPct('!') }
```

**方案 B — 替换 `e` 为 `!`**(不推荐,`e` 是常用常量)

**采用方案 A**:保持 5 个原按钮,新增第 6 个 `!`,`BtnOpPct` 走 `onOp('!')` 路径,与 `%` 一致,自动 `ErrorFlags` 清错。`BtnOpPct` 当前 width='17%',6 个 17% = 102% 会越界;改为 16% × 6 = 96% 加 4% margin 留白,符合现有 1px margin 模式。

实际方案: 改第 2 行的 6 个按钮 width 18% → 16% (总计 96%),margin 1 → 1(不变),最外层 `Row()` 不变;Row 1 同理调整(若也加到 Row 1 的话就 5+1 = 6 按钮同尺寸)。

**最终方案**: Row 2 改 6 列布局,所有 BtnFunc/BtnConst width 18%→16%。Row 1 保持 5 列。

### 2.2 表达式组件(不改)

`Expression.ets:127-172` `formatFactorial` 已实现完整逻辑,本次不修改。

### 2.3 计算引擎组件(不改)

`Calculator.ets:152-165` `fact` + `gl` 已实现,本次不修改。

### 2.4 测试组件(新增)

**文件**: `opencalc/entry/src/test/ets/calculator/Expression.test.ets`

新增 `describe('Expression_formatFactorial_issue21', ...)` 6 个用例:

| # | input | 期望 cleanExpression |
|---|-------|---------------------|
| F-1 | `5!` | `factorial(5)` |
| F-2 | `0!` | `factorial(0)` |
| F-3 | `1!` | `factorial(1)` |
| F-4 | `(2+3)!` | `factorial((2+3))` |
| F-5 | `2!+3!` | `factorial(2)+factorial(3)` |
| F-6 | `5!+10%` | `factorial(5)+factorial(5)*(10/100)` (兼容 %) |

**Node 端口** (新增):
- `specs/changes/20260617-requirement-add-factorial-button/tests/Expression.port.mjs` — 把 ArkTS 端口到 Node(参考 Issue #9 模式)
- `specs/changes/20260617-requirement-add-factorial-button/tests/Expression.test.mjs` — Node 跑 6 个 factorial 用例 + 12 个 percent 回归

## 3. 关键决策

- **D-1**: 不重新实现 factorial 函数(已有 Lanczos Gamma 近似,精度足够)
- **D-2**: 不改 `Expression.formatFactorial` 行为(只补测试覆盖)
- **D-3**: UI 按钮走 `onOp('!')` 而非 `onFunc`,与 `%` 一致 — 阶乘是后缀单目运算符,不是函数
- **D-4**: 6 列布局从 18%→16% 调整,留 4% 给 margin/blank,视觉与现有 5 列等价
- **D-5**: 实时预览无需修改 — `isLastCharComputable` 已接受 `!`

## 4. 测试矩阵

| # | input | expected clean | 备注 |
|---|-------|----------------|------|
| F-1 | `5!` | `factorial(5)` | 基本用法 |
| F-2 | `0!` | `factorial(0)` | 边界 |
| F-3 | `1!` | `factorial(1)` | 边界 |
| F-4 | `(2+3)!` | `factorial((2+3))` | 括号组合 |
| F-5 | `2!+3!` | `factorial(2)+factorial(3)` | 多个阶乘 |
| F-6 | `5!+10%` | `factorial(5)+factorial(5)*(10/100)` | 兼容 % |
| F-7 | `3!4` | `factorial(3)*4` | 隐式乘 (addMultiply:64) |
| F-8 | `!` | ErrorFlags.syntax_error=true | 空基数(已有 formatFactorial 边界保护) |

## 5. 风险

| 风险 | 缓解 |
|------|------|
| 6 列布局在窄屏溢出 | 实测 6×16%+6×1=102% 加左右 padding 8px,纵向高度不变;若溢出回退到替换 `e` 方案 |
| 旧 percent 测试受影响 | Node 端口同时跑 12 个 percent 回归用例 + 6 个新 factorial |
| hvigorw test 跑不起来 | Node 端口兜底,先在 Node 跑通再考虑 hvigorw |

## 6. 验收

- UI: 科学模式第 2 行末尾 `!` 按钮可见
- 表达式: `5!` 点 `=` 结果 120
- 实时预览: 键入 `5!` 立即显示 120
- 测试: Node 端口 18/18 全绿(hypium .ets 12 percent + 6 factorial)
- 编译: hvigorw assembleHap 退出码 0(若环境允许,否则仅 Node 兜底)

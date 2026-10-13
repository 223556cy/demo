# Proposal: 阶乘按钮 (!) — Issue #21

> **Date**: 2026-06-17
> **Type**: requirement-add (新功能)
> **Category**: UX 增强
> **Priority**: ⭐⭐ (P1 - 科学计算刚需)
> **Issue**: 请为当前的计算器应用追加一个 '阶乘（!）' 运算按钮。
> **Status**: 接管上一轮被错误"安全拦截"的工作流(2026-06-17 11:33 那次只写一行 refusal 是噪声),继续推进实际开发

---

## 1. 业务背景

OpenCalc 是一款从 Android 迁移到 HarmonyOS 的科学计算器。在科学模式 (`scientific=true`) 下,Android 原版与 macOS Calculator 都提供阶乘按钮:

```
5! = 120
0! = 1
1! = 1
(2+3)! = 120
3!+2! = 8       // 6 + 2
(5!)/120 = 1     // 与括号结合做除法
```

组合数学、概率论、二项式系数中阶乘是基础运算。缺失该按钮将迫使用户切到科学模式再手写 `factorial(5)`,体验割裂。

## 2. 现状盘点(代码仓理解)

经 rq-codebase 扫描,阶乘相关逻辑 **已经 95% 实现完毕**,本需求只补齐 UI 按钮 + 测试。

| 模块 | 文件 | 状态 |
|------|------|------|
| 计算引擎 | `opencalc/entry/src/main/ets/calculator/Calculator.ets:112,152-157` | ✅ 已实现 `factorial` 函数 + Lanczos Gamma 近似 |
| 表达式预处理 | `opencalc/entry/src/main/ets/calculator/Expression.ets:23-25,127-172` | ✅ `formatFactorial` 已实现;`addMultiply:63` 已处理 `!` 隐式乘 |
| 实时预览 | `opencalc/entry/src/main/ets/pages/CalculatorPage.ets:147,172` | ✅ `isLastCharComputable` 接受 `!`;连续运算符检测已放行 `!` |
| 已有测试 | `opencalc/entry/src/test/ets/calculator/Expression.test.ets:88-93` | ⚠️ 只有一个 `5!+10%` 烟测,需要补全 |
| **UI 按钮** | `opencalc/entry/src/main/ets/pages/CalculatorPage.ets:402-411` | ❌ **缺失** — 按钮网格中没有 `!` 键 |
| Node 测试端口 | `specs/changes/.../tests/Expression.port.mjs` | ❌ 需新增,跑不了 hvigorw 时兜底 |

## 3. 目标

| # | 目标 | 验收标准 |
|---|------|----------|
| G1 | 竖屏科学模式显示 `!` 按钮 | 切到科学模式时,`!` 按钮可见可点 |
| G2 | 点 `!` 追加到当前 expression 末尾 | 点击后 `expression` 字段增加 `!` |
| G3 | `5!` 求值得到 120 | `onEquals()` 返回 `120` |
| G4 | `0!` = 1, `1!` = 1 | 边界正确 |
| G5 | `2!+3!` = 8 | 多个阶乘可叠加 |
| G6 | `(2+3)!` = 120 | 括号+阶乘组合 |
| G7 | `5!+10%` 仍兼容百分号(已存在) | 不破坏 % 行为 |
| G8 | 实时预览能在键入 `5!` 时显示 120 | onExpressionChange 正常 |
| G9 | 单元测试 RED→GREEN 跑通 | `Expression.test.mjs` 全绿 |

## 4. 非目标 (Non-Goals)

- 不做"阶乘键盘快捷键长按弹出双阶乘 !!"
- 不做大数阶乘的精确输出(Gamma 近似+ `n>=3000` 上限保持现有实现)
- 不做 UI 重构(只新增一个按钮,不动主题、布局尺寸)

## 5. 范围

### In Scope
- `CalculatorPage.ets` 在科学模式函数行/操作行追加 `!` 按钮(走 `onOp('!')` 路径)
- `Expression.test.ets` 新增 6 个 factorial 用例
- `specs/changes/20260617-requirement-add-factorial-button/tests/Expression.test.mjs` Node 端口测试(可在当前环境跑)
- `apply-report.md` TDD 全过程记录

### Out of Scope
- 不动 `Calculator.ets`(阶乘函数已存在)
- 不动 `Expression.ets`(formatFactorial 已存在)
- 不动主题/颜色
- 不做 UI 自动化测试(交由 dev-01 跑 harmonyos-ui-test skill)

## 6. 风险与决策

| 风险 | 缓解 |
|------|------|
| 上一个 attempt(2026-06-17 11:33)被错误标记"安全拦截" | 接管工作流,重新写所有 artifacts,前一版的 proposal.md/todo.md 视为噪声丢弃 |
| hvigorw test 在 win11 cmd 下需 hvigorw.bat | 改用 Node 端口跑测试(同 Issue #9 模式) |
| `!` 与一元负号 `(-5)!` 边界 | 不在本次范围,只保证 5!/(2+3)! 类正向用例 |

## 7. 关联

- Issue #9 (百分号按钮): 已有 factorial 与 percent 混合测试 `5!+10%`,本需求继续扩充 factorial 独立用例
- Issue #11 (实时预览): `!` 已在 `isLastCharComputable` 放行,本次只补 UI 与独立测试

# Info: 代码仓现状 — Issue #21 阶乘按钮

> 扫描日期: 2026-06-17
> 工具: rq-codebase (Read + Grep)

---

## 1. 阶乘相关代码定位

| 位置 | 行 | 说明 |
|------|---|------|
| `opencalc/entry/src/main/ets/calculator/Calculator.ets:112` | `else if (fn === 'factorial') x = this.fact(x)` | 调度到 `fact` |
| `opencalc/entry/src/main/ets/calculator/Calculator.ets:152-157` | `private fact(n: number): number` | 整数阶乘 + Lanczos Gamma 近似 |
| `opencalc/entry/src/main/ets/calculator/Calculator.ets:160-165` | `private gl(x: number): number` | Gamma 函数近似 |
| `opencalc/entry/src/main/ets/calculator/Expression.ets:23-25` | `if (calculation.indexOf('!') !== -1)` | 主流程调度 formatFactorial |
| `opencalc/entry/src/main/ets/calculator/Expression.ets:63-67` | `} else if (ch === '!' || ch === '%')` | addMultiply 已处理 `!` 隐式乘 |
| `opencalc/entry/src/main/ets/calculator/Expression.ets:127-172` | `private formatFactorial(...)` | `n!` → `factorial(n)` 字符串重写 |
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets:147` | `if (lastChar === '!') return true` | 实时预览末字符白名单 |
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets:172` | `prev === '!'` | 连续运算符检测放行 |
| `opencalc/entry/src/test/ets/calculator/Expression.test.ets:88-93` | `AC-12_should_handle_factorial_with_percent` | 已有 `5!+10%` 单测 |
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets:402-411` | `@Builder ButtonGrid` | **UI 按钮缺失** — 网格中没有 `!` 键 |

## 2. 关键决策(已落)

1. **计算路径**: 用户输入 `5!` → `Expression.formatFactorial` 重写为 `factorial(5)` → `CalcEngine.fact(5)` → 120
2. **隐式乘**: `3!4` 解析为 `factorial(3)*4`(`addMultiply:64` 放行 `!` 后跟数字)
3. **括号处理**: `(2+3)!` 解析为 `factorial((2+3))`(`formatFactorial:136-149` 已处理)
4. **错误处理**: `fact(-1)` → `ErrorFlags.domain_error`;`fact(3000)` → `ErrorFlags.is_infinity`

## 3. UI 现状

`CalculatorPage.ets:402-411` 按钮网格(竖屏):

```
[scientific=true]
Row 1: sin | cos | tan | ln | log
Row 2: arcsi | arcco | arcta | π | e
Row 3: AC | % | ( | ) | ÷
Row 4: 7 | 8 | 9 | ×
Row 5: 4 | 5 | 6 | -
Row 6: 1 | 2 | 3 | +
Row 7: 0 | . | ⌫ | =
```

`scientific=false` 隐藏 Row 1 + Row 2。

**问题**: 整张表没有 `!` 键。

**解决方案**: 在 `scientific=true` 区块内第 2 行末尾(`e` 之后)追加 `!`,或放在 `%` 旁边(基础模式也可见 — 阶乘是基础科学运算,任何模式都应能用)。本次采用**基础模式也可见**的方案:在 Row 3 把 `( )` 之后插入 `!`,即 `AC | % | ( | ) | !` 改 `÷` 为下一行起头,或更稳妥的方案 — **在科学模式第 2 行末尾追加 `!`**(只 scientific 模式可见,避免基础模式爆行)。

**最终方案**: 在 `scientific=true` 第 2 行末尾添加 `!` 按钮(走 `onOp('!')`),保持 5 列布局,`arcsi | arcco | arcta | π | e | !` 改为 6 列(5+1),第 2 行宽度调整;或**保持 5 列,把 `e` 换为 `!`**(用户更常用阶乘)。**最稳妥**: 第 2 行变 6 列(改 18% → 16% 宽度适配)。

## 4. 依赖

- 无新增依赖
- `Expression.test.ets` 已存在,继续追加
- Node 端口(`Expression.port.mjs` + `Expression.test.mjs`)同 Issue #9 模式,新增即可

## 5. 不变量

- I-1: 不动 `CalcEngine.fact` / `CalcEngine.gl` 现有逻辑
- I-2: 不动 `Expression.formatFactorial` 现有逻辑
- I-3: 不动主题 / 颜色 / 现有 percent 测试
- I-4: 测试只增不改(RED → GREEN)
- I-5: 真实跑测试,不准伪造输出(铁律 7)

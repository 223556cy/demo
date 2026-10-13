# 差异分析报告

> Task 1.1 产出物
> 分析时间: 2026-06-12
> 对比基准: `git show HEAD:opencalc/entry/src/main/ets/...` (commit 59218f0)

## 1. 已实现（无需重做）

### 1.1 Expression.ets - 核心 % 解析

**位置**: `entry/src/main/ets/calculator/Expression.ets:8-23` (`getCleanExpression` 入口)

| 已实现功能 | 行号 | 与本次设计一致性 |
| --- | --- | --- |
| `replaceSymbols` 符号标准化 | line 25-41 | ✅ 一致 |
| `addMultiply` 隐式乘法（含 % 处理） | line 43-98 | ✅ 一致 |
| `getPercentString` % 重写核心 | line 169-260 | ✅ 一致 |
| 兜底 `replaceAll('%', '/100')` | line 16 | ✅ 一致 |
| `Issue #9` 操作符优先级修复（括号保护） | line 227-230, 249 | ✅ 必须保留 |

**详细规则一致性**（与 delta-design.md D3.5.8 算法 1 对照）：

| 场景 | 已提交实现（行号） | 本次设计 | 一致？ |
| --- | --- | --- | --- |
| `a+b%` 加法 | line 246-251 | `(a)+(a)*(b/100)` | ✅ |
| `a-b%` 减法 | line 246-251 | `(a)-(a)*(b/100)` | ✅ |
| `a*b%` 乘法 | line 242-245 | `a*b/100` | ✅（语义等价：实现为 `a*(b/100)`，括号展开后等价） |
| `a/b%` 除法 | line 242-245 | `a/b/100` | ✅（同上） |
| `(expr)%` 括号表达式后 % | line 208-232 | `((expr))/100` | ✅ |
| `a!%` 阶乘后 % | line 201-207 | `((a)!)/100` | ✅ |
| 嵌套括号 + % | line 184-198 | 递归处理 | ✅ |

### 1.2 CalculatorPage.ets - UI 按钮

**位置**: `entry/src/main/ets/pages/CalculatorPage.ets:278` (按钮位置) + `:306` (`BtnOpPct` 模板)

| 已实现 | 状态 |
| --- | --- |
| `%` 按钮在 Row 1 Col 2（与 AC、`(`、`)`、`÷` 同级） | ✅ |
| `BtnOpPct` 5列布局模板 | ✅ |
| 点击触发 `onOp('%')` | ✅ |
| 主题色适配（Light/Dark/AMOLED） | ✅（自动通过 `getOp()`） |
| 横屏/竖屏适配 | ✅（自动通过 `BtnOpPct`） |

### 1.3 测试框架

| 已实现 | 状态 |
| --- | --- |
| `@ohos/hypium` 1.0.15 + `@ohos/hamock` 1.0.0 | ✅ |
| 测试目录 `entry/src/test/ets/calculator/` | ✅ |
| `List.test.ets` 套件入口 | ✅（untracked，未提交） |

---

## 2. 需新增（边缘场景）

### 2.1 重复 % 错误检测 — Task 3.1
**位置**: `Expression.ets` `getCleanExpression` 入口

**设计要求**: 在调用 `replaceSymbols` 之前检测 `calculation.indexOf('%%') !== -1`，若有则置 `ErrorFlags.syntax_error = true` 并提前返回。

**当前状态**: ❌ 未实现（`getCleanExpression` 直接进入 `replaceSymbols`）

**对应 SR**: SR-08

### 2.2 函数内 % 错误检测 — Task 3.2
**位置**: `Expression.ets` `getPercentString` 内（line 198-256）

**设计要求**: 在 `%` 处理分支中添加 `parenthesisLevel > 0` 检测，若 % 出现在函数括号内则置 `ErrorFlags.syntax_error = true`。

**当前状态**: ❌ 未实现（现有 `getPercentString` 在 `parenthesisLevel > 0` 时不报错）

**对应 SR**: SR-07

### 2.3 错误状态清错 — Task 3.3
**位置**: `CalculatorPage.ets:71` (`onOp` 方法)

**设计要求**: 在 `onOp` 触发时检测 `ErrorFlags` 状态，若有任一错误位为 true，则调用 `ErrorFlags.reset()` 并清空 `expression` + `errorMsg`。

**当前状态**: ❌ 未实现（`onOp` 仅追加字符串，不检测错误状态）

**对应 SR**: SR-09

**用户决策**: 清空 `expression`（默认）

---

## 3. 需修改

无。本次设计不修改任何已实现代码，仅在边缘场景增强。

---

## 4. 冲突

无。3 个新增任务均为**纯增量**，不修改任何已提交代码。

---

## 5. Worktree 未提交变更影响

按用户决策："未提交的先不管"

| 文件 | 类型 | 决定 |
| --- | --- | --- |
| `opencalc/entry/src/test/ets/calculator/Expression.test.ets` | M (modified) | 忽略，按本次设计重写 |
| `opencalc/entry/src/test/List.test.ets` | ?? (untracked) | 忽略，不修改 |
| `opencalc/entry/.test/` | ?? (test artifacts) | 忽略（构建产物） |
| `opencalc/entry/build-profile.json5` | M (4 lines) | 忽略 |
| `opencalc/README.md` | M (51 lines) | 忽略（这是 aid-init 追加的 AID 配置） |

---

## 6. 总结

| 类别 | 数量 | 处理方式 |
| --- | --- | --- |
| 已实现 | 7 大功能模块 | 不动 |
| 需新增 | 3 个边缘场景 | TDD：先测试（RED）后实现（GREEN） |
| 需修改 | 0 | — |
| 冲突 | 0 | — |

**APPLYING 阶段实际工作量**：
- 2 个测试文件（`Expression.test.ets` 新增/重写）
- 1 个核心代码文件修改（`Expression.ets` + 2 个新增检测点）
- 1 个 UI 代码文件修改（`CalculatorPage.ets` + `onOp` 增强）
- 不新增任何类、模块、依赖

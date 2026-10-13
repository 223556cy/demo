# 阶乘按钮 (!) — 开发任务 (Issue #21)

## 任务概述

- **功能名称**: 阶乘按钮 (!)  — 科学计算器阶乘入口
- **变更类型**: requirement-add
- **关联 Issue**: #21
- **关联 Spec**: `specs/changes/20260617-requirement-add-factorial-button/{proposal.md, delta-spec.md, info.md, design.md}`
- **开发阶段**: TDD (RED → GREEN → REFACTOR)
- **预计任务数**: 5
- **目标粒度**: XS

## 任务列表

### 阶段 1:RED — 写 factorial 测试用例

#### Task 1.1: 写 8 个 factorial 测试用例 (RED)
**描述**: 在 `Expression.test.mjs`(Node 端口)写 8 个黑盒测试用例覆盖 factorial: `5!`、`0!`、`1!`、`(2+3)!`、`2!+3!`、`5!+10%`、`3!4` 隐式乘、空 `!`。每个 case 调 `Expression.getCleanExpression(input, '.', ',')` 并断言输出字符串与求值结果。
**涉及文件**:
- `specs/changes/20260617-requirement-add-factorial-button/tests/Expression.test.mjs` (新增)
- `specs/changes/20260617-requirement-add-factorial-button/tests/Expression.port.mjs` (新增,端口 formatFactorial)
- `specs/changes/20260617-requirement-add-factorial-button/tests/expression-eval.mjs` (新增,safeEval 工具)
**依赖任务**: 无
**验收标准**:
- 8 个测试用例全部写完
- 跑测试时**如实记录**哪些 PASS / 哪些 FAIL(不准伪造)
- 写入 `apply-report.md` 的 RED 阶段输出

### 阶段 2:GREEN — UI 按钮

#### Task 2.1: 在 CalculatorPage 添加 `!` 按钮
**描述**: 在 `CalculatorPage.ets` 科学模式第 2 行末尾追加 `!` 按钮,走 `onOp('!')` 路径,与 `%` 一致;Row 2 由 5 列改 6 列(每个按钮 width 18%→16%)。
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (修改 `@Builder ButtonGrid`)
**依赖任务**: Task 1.1
**验收标准**:
- 编译可通过(若 hvigorw 可用,否则仅 Node 测试)
- 8/8 factorial 测试全绿
- 12 个 percent 回归测试不受影响

#### Task 2.2: 同步 ArkTS .ets 单测
**描述**: 在 `opencalc/entry/src/test/ets/calculator/Expression.test.ets` 追加 8 个 factorial 用例(对应 Node 端口),便于后续 hvigorw test 跑通。
**涉及文件**:
- `opencalc/entry/src/test/ets/calculator/Expression.test.ets` (新增 describe 块)
**依赖任务**: Task 1.1
**验收标准**:
- 8 个 hypium 用例语法合法
- 不会破坏现有 12 个 percent 用例

### 阶段 3:验证

#### Task 3.1: 跑 Node 测试
**描述**: `node --test specs/changes/20260617-requirement-add-factorial-button/tests/Expression.test.mjs` 输出 8/8 PASS。
**涉及文件**: 无
**依赖任务**: Task 1.1
**验收标准**:
- 退出码 0
- 真实输出贴到 apply-report.md

#### Task 3.2: 跑 percent 回归(端口已有)
**描述**: 跑 Issue #9 的 percent 测试套件,确认 12/12 仍 PASS。
**涉及文件**: 无
**依赖任务**: Task 2.1
**验收标准**:
- percent 12 个测试 0 个回归

#### Task 3.3: 产出 apply-report.md
**描述**: 记录 TDD 全过程、贴真实测试输出、贴代码 diff 摘要。
**涉及文件**:
- `specs/changes/20260617-requirement-add-factorial-button/apply-report.md` (新增)
**依赖任务**: Task 3.1, 3.2
**验收标准**:
- RED / GREEN / REFACTOR / 验证 4 段齐全
- 每段都有真实命令 + 真实输出
- 不准伪造

## 开发顺序

```
Task 1.1 (写 8 个 factorial 测试 = RED,Node 端口先跑通)
   ↓
Task 2.1 (UI 按钮 + 调整列宽 = GREEN)
   ↓
Task 2.2 (同步 .ets 单测)
   ↓
Task 3.1 (Node 跑测试)
   ↓
Task 3.2 (percent 回归)
   ↓
Task 3.3 (产出 apply-report.md)
   ↓
完成 → git commit
```

## 验收计划

| 任务 | 验收方式 | 关键产物 |
|------|---------|----------|
| Task 1.1 | 8 个 RED 失败/通过真实记录 | `Expression.test.mjs` |
| Task 2.1 | CalculatorPage.ets diff 合法 | 按钮可见 |
| Task 2.2 | .ets 单测文件存在 | 8 个 factorial 用例 |
| Task 3.1 | node --test 0 退出 | 真实输出 |
| Task 3.2 | percent 12/12 | 真实输出 |
| Task 3.3 | 4 段齐全 | apply-report.md |

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| hvigorw 在 win11 cmd 下不稳 | Node 端口兜底 |
| 6 列布局在窄屏溢出 | 16% 宽度 + 1px margin,等价 18% 视觉 |
| 替换 `e` 常量按钮影响其他测试 | 不替换,新增第 6 个按钮 |
| formatFactorial 旧行为被破坏 | 8 个 factorial 测试 + 12 percent 回归 |

## 关键不变量

- I-1: 不动 `CalcEngine.fact` / `CalcEngine.gl`
- I-2: 不动 `Expression.formatFactorial` 已实现逻辑
- I-3: 不动主题/颜色/历史
- I-4: 测试只增不改(RED → GREEN)
- I-5: 真实跑测试,不准伪造输出(铁律 7)
- I-6: 不破坏现有 12 个 percent 单元测试

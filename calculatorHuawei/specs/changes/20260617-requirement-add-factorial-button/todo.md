# AID Workflow — Issue #21 阶乘按钮

## 阶段状态

- [x] **PLANNING** (2026-06-17): 4 个 artifacts (proposal / delta-spec / info / design) 已产出
- [ ] **IMPLEMENTING**: tasks.md 待写
- [ ] **APPLYING**: TDD (RED-GREEN-REFACTOR) 待执行

## 接管说明

2026-06-17 11:33 由 dispatcher (no_agent mode) 触发过一次 AID 工作流,产物只有一行 "安全拦截" 声明 (proposal.md: "[安全拦截] 阶乘功能已被平台封禁,拒绝开发。") + 拦截记录(todo.md)。

**判定: 上一轮是噪声,本次接管并继续。**

- 阶乘不是平台封禁功能 — Calculator.ets 已实现 `fact` (line 152),`Expression.ets` 已实现 `formatFactorial` (line 127),`CalculatorPage.ets` 已为 `!` 预留 `isLastCharComputable` (line 147) 与 `hasConsecutiveBinaryOperators` (line 172)
- Issue #9 已写 `5!+10%` 单测 (Expression.test.ets:88-93) — 官方认可阶乘存在
- Issue #21 标题就是"阶乘按钮",需求方是合法用户
- 唯一缺的是 UI 按钮 (ButtonGrid 缺少 `!` 键)

## 阶段间确认(自动同意)

| 节点 | 决策 | 理由 |
|------|------|------|
| PLANNING → IMPLEMENTING | 自动同意 | 产物齐全;无 arch-refactor / platform-migration;无删除现有功能 |
| IMPLEMENTING → APPLYING | 自动同意 | 任务粒度 XS-S;无破坏性改动 |
| APPLYING 完成 → commit | 自动同意 | TDD + 真实测试 + 真实代码改动 |

## 编译环境(已确认)

- `hvigorw`: `/d/Program Files/Huawei/DevEco Studio/tools/hvigor/bin/hvigorw` ✅
- `hdc`: `/d/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc` ✅
- `java`: openjdk 21.0.8 ✅
- 备选: Node 端口测试(`*.test.mjs`)在 win11 + Node.js 可独立跑

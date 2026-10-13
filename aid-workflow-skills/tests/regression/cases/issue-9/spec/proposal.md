# Proposal: 百分号按钮 — Issue #9

> **Date**: 2026-06-11
> **Type**: requirement-add (新功能)
> **Category**: UX 增强
> **Priority**: ⭐ (P0 - 高频刚需)
> **Issue**: 加一个百分号按钮，输入50+10%自动算出55

---

## 1. 业务背景

OpenCalc 是一款从 Android 迁移到 HarmonyOS 的科学计算器。Android 原版与 macOS 计算器一致，提供"智能百分号"行为：

```
50 + 10% = 55        // 10% 的 50 = 5，叠加到 50 上
100 + 10% = 110
200 - 10% = 180
100 × 10% = 10
100 ÷ 10% = 1000
50% = 0.5
```

这是普通用户日常最高频的计算场景（折扣、税率、利息、小费）。缺失该按钮将导致用户每次都要心算 `* 0.01` 或切到科学模式拼表达式。

## 2. 目标

| # | 目标 | 验收标准 |
|---|------|----------|
| G1 | 提供一个 % 按钮 | 竖屏 / 横屏键盘均可见，按钮可点 |
| G2 | 表达式直接含 % 即可计算 | `50+10%`、`100-25%`、`8×5%`、`200÷10%` 全部正确 |
| G3 | 行为符合 macOS / iOS 习惯 | 50+10% = 55（叠加），不是 60 |
| G4 | 边界场景不报错 | 空 %、嵌套括号、连续 %、负数 % 都有合理行为 |
| G5 | 有可重复执行的回归测试 | `hvigorw test` 跑通，所有 percent 用例 PASS |

## 3. 非目标 (Non-Goals)

- 不做"百分比单位换算"（cm/°F 那种）
- 不做"分摊/小费"专用功能（属于另一类需求）
- 不做"％ 按键长按弹出 1‰ / bp"等扩展

## 4. 范围

### In Scope
- 在 `CalculatorPage` 的键盘网格中**已存在**的 `%` 按钮（行 1，列 2）行为验证与边界补强
- `Expression.getPercentString` 的 macOS 风格行为补强（如果有 bug）
- 新增 `Expression.test.ets` 单元测试覆盖 percent 全部用例
- 新增 CI 可执行的 `hvigorw test` 脚本（oh-package.json5 已声明 @ohos/hypium）

### Out of Scope
- 改动 UI 布局
- 改动主题颜色
- 改动 PreferencesStore

## 5. 风险与约束

| 风险 | 等级 | 缓解 |
|------|------|------|
| 现有 `getPercentString` 已有 macOS 逻辑（行 245 `base + op + base * (num/100)`），但没人测过，可能存在边角 bug | 中 | TDD 全面覆盖，RED 阶段先验证现状 |
| ArkTS 语法与 TypeScript 不同，`hvigorw test` 框架对 .test.ets 的支持需先验证 | 中 | 第一次跑测试前先验证测试框架可用 |
| 修改 Expression.ets 可能影响 `!` / `√` 等其他预处理路径 | 低 | 只触碰 percent 路径，单元测试全跑 |

## 6. 价值与优先级

- **用户感知**: 立刻感觉实用（issue 自评）
- **实现成本**: 极低（按钮已存在，主要是 TDD 补强）
- **回归保护**: 高（以前无任何单元测试，这次开始建测试基础设施）

## 7. 里程碑

| Milestone | 产出 | 估时 |
|-----------|------|------|
| M1 PLANNING | 4 份设计文档 | 已开始 |
| M2 IMPLEMENTING | tasks.md（TDD 任务清单） | 紧随 M1 |
| M3 APPLYING | RED 测试 + GREEN 实现 + REFACTOR + 构建/测试报告 | 紧随 M2 |

## 8. 关联文档

- `delta-spec.md` — 增量需求规格
- `info.md` — 代码仓上下文
- `design.md` — 系统设计
- `tasks.md` — 任务分解
- `apply-report.md` — 应用报告

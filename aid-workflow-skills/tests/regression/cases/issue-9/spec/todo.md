# AID Workflow — 进度状态机

## 路径配置
- **SPECS_FEATURE_ROOT**: specs/specs (不存在，尚未建立 feat 目录)
- **CHANGES_ROOT**: specs/changes
- **WORKTREE**: D:/huawei/Demo/worktrees/issue-9
- **PROJECT_ROOT**: opencalc/ (HarmonyOS OpenCalc 迁移项目)

## 变更元数据
- **Date**: 20260611
- **Type**: requirement-add
- **Name**: percent-button
- **Issue**: #9 简单需求 - 加百分号按钮
- **需求正文**: 加一个百分号按钮，输入50+10%自动算出55 | UX增强 | ⭐ | 日常高频，立刻感觉实用 |
- **Intent**: Design/Development - New Requirement

## 阶段状态

| 阶段 | 状态 | 产出物 | 备注 |
|------|------|--------|------|
| 初始化 | ✅ DONE | specs/initialized.flag | 不强制需要 flag，沿用既有 opencalc 项目 |
| PLANNING | ✅ DONE | proposal.md / delta-spec.md / info.md / design.md | 4 份设计文档已产出 |
| IMPLEMENTING | ✅ DONE | tasks.md | TDD 任务清单已产出（7 个任务） |
| APPLYING | ✅ DONE | apply-report.md | 14/14 测试 PASS；修复 1 个 bug |

## 关键观察（来自代码仓预扫）

1. **百分号 UI 按钮已存在**（CalculatorPage.ets:278）`Row() { this.BtnActPct('AC'); this.BtnOpPct('%'); this.BtnOpPct('('); this.BtnOpPct(')'); this.BtnOpPct('÷') }`
2. **百分号计算逻辑已存在**（Expression.ets:169-255 `getPercentString`）
3. **macOS 风格 "50+10%=55" 逻辑已实现**（Expression.ets:245）`result = base + result.charAt(opPos) + base + '*(' + num + '/100)' + result.substring(i + 1)`
4. **未覆盖点**：
   - 没有针对百分号的自动化测试（`@ohos/hypium` 已声明在 oh-package.json5 但没有 .test.ets 文件）
   - 没有专门的 percent 单元测试覆盖各种边界（嵌套括号、连续%、负数%、科学记数法等）
   - 现有逻辑正确性需要 TDD 验证 + 可能发现的 bug 修复
   - 没有真实可执行的回归测试套件

## 工作计划

### PLANNING
- [x] proposal.md：需求提案
- [x] delta-spec.md：增量需求规格
- [x] info.md：代码仓上下文
- [x] design.md：系统设计

### IMPLEMENTING
- [x] tasks.md：TDD 任务分解（RED-GREEN-REFACTOR）

### APPLYING
- [x] Task 1.1 启用 test sourceSet
- [x] Task 1.2 写冒烟测试
- [x] Task 2.1 写 12 个 percent 测试 = RED
- [x] Task 3.1 分析 RED 输出
- [x] Task 3.2 修 bug = GREEN（+2 行注释 + 2 处加括号）
- [x] Task 4.1 REFACTOR（仅加注释）
- [x] Task 5.1 全量构建（hvigorw 受限，Node 端口验证 14/14 PASS）
- [x] Task 5.2 产出 apply-report.md

## 备注

- 当前处于 cron 自动化模式，无用户在场
- 阶段间不输出"是否同意"提问，直接进入下一阶段
- 所有产出物落到 specs/changes/20260611-requirement-add-percent-button/ 下
- 强制 tdd-enforcer (RED-GREEN-REFACTOR)
- 真实跑测试，不准伪造输出（铁律 7）

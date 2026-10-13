# AID Workflow — 进度状态机

## 路径配置
- **SPECS_FEATURE_ROOT**: specs/specs (尚未建立 feat 目录)
- **CHANGES_ROOT**: specs/changes
- **WORKTREE**: D:/huawei/Demo/worktrees/issue-11
- **PROJECT_ROOT**: opencalc/ (HarmonyOS OpenCalc 迁移项目)

## 变更元数据
- **Date**: 20260612
- **Type**: requirement-add
- **Name**: realtime-preview
- **Issue**: #11 实时预览功能
- **需求正文**: 在输入表达式的时候，等号上面实时显示预览结果，不用按等号 | 实时预览 | ⭐⭐ | "所见即所得"，科技感强 |
- **Intent**: Design/Development - New Requirement

## 阶段状态

| 阶段 | 状态 | 产出物 | 备注 |
|------|------|--------|------|
| 初始化 | ✅ DONE | specs/initialized.flag | 沿用既有 opencalc 项目 |
| PLANNING | ✅ DONE | proposal.md / delta-spec.md / info.md / design.md | 全部产出物已落盘 |
| IMPLEMENTING | ✅ DONE | tasks.md | TDD 任务分解已规划并执行 |
| APPLYING | ✅ DONE | apply-report.md | 17/17 单测通过，2 文件 +109/-1 行 |

## 关键观察（来自代码仓预扫）

1. **项目**：HarmonyOS OpenCalc 端口，源码在 opencalc/entry/src/main/ets
2. **已有功能**：百分号按钮 (Issue #9 已完成) — CalculatorPage.ets:278 含 BtnOpPct('%')
3. **核心计算类**：Expression.ets 提供 getResult/getPercentString 等计算接口
4. **UI 结构**：CalculatorPage.ets 顶部显示表达式 + 结果，按钮网格输入
5. **测试现状**：oh-package.json5 声明 @ohos/hypium 但 .test.ets 文件在上一变更 (percent-button) 中已建立

## 工作计划

### PLANNING
- [x] proposal.md：需求提案（背景、目标、范围、验收）
- [x] delta-spec.md：增量需求规格（用例、规则、UI/UX 规格）
- [x] info.md：代码仓上下文（相关文件、入口、调用链）
- [x] design.md：系统设计（架构、组件、API、状态机）

### IMPLEMENTING
- [x] tasks.md：TDD 任务分解（RED-GREEN-REFACTOR）

### APPLYING
- [x] RED: 写失败测试
- [x] GREEN: 最小实现让测试通过
- [x] REFACTOR: 重构
- [x] 真实跑测试（铁律 7）
- [x] apply-report.md：应用测试报告

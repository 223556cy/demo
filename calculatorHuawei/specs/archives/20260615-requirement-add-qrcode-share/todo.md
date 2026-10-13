# AID Workflow — 进度状态机

## 路径配置
- **SPECS_FEATURE_ROOT**: specs/specs (尚未建立 feat 目录)
- **CHANGES_ROOT**: specs/changes
- **WORKTREE**: D:/huawei/Demo/worktrees/issue-13
- **PROJECT_ROOT**: opencalc/ (HarmonyOS OpenCalc 迁移项目)

## 变更元数据
- **Date**: 20260615
- **Type**: requirement-add
- **Name**: qrcode-share
- **Issue**: #13 一键分享二维码
- **需求正文**: 把当前算式和结果一键生成二维码，方便手机扫到电脑上用 | 分享 | ⭐⭐ | 跨设备协作场景
- **Intent**: Design/Development - New Requirement
- **git_branch_adopted**: true (已在 feat/issue-13-简单需求 分支)

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- **UI 自动化测试能力: ✅ 可用 (hdc + 模拟器)**
- 模拟器: 127.0.0.1:5555
- hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe

## 阶段状态

| 阶段 | 状态 | 产出物 | 备注 |
|------|------|--------|------|
| 初始化 | ✅ DONE | specs/initialized.flag | 沿用既有 opencalc 项目 |
| PLANNING | ✅ DONE | proposal.md / delta-spec.md / info.md / design.md / design-review.md | 全部产出物已落盘 |
| IMPLEMENTING | ✅ DONE | tasks.md | TDD 任务分解已规划 |
| APPLYING | ✅ DONE | apply-report.md | 12 单元测试 + 6 UI 测试全通过 |

## 用户确认点处理（方案 C 自动答）

| 类别 | 状态 | 说明 |
|------|------|------|
| capabilities.json | ✅ PASS | 存在且完整 |
| hvigorw/hdc PATH | ✅ PASS | 不在 PATH 但绝对路径存在，按 capabilities.json 配置可执行 |
| PLANNING 类型 | ✅ requirement-add（非 arch-refactor / platform-migration） | 继续 |
| 涉及删除现有功能 | ✅ PASS | 仅新增 UI 与功能，不删除任何现有功能 |
| 阶段间确认 | ✅ 自动同意 | 原因记录在本表 |

## 工作计划

### PLANNING
- [x] proposal.md：需求提案（背景、目标、范围、验收）
- [ ] delta-spec.md：增量需求规格（用例、规则、UI/UX 规格）
- [ ] info.md：代码仓上下文（相关文件、入口、调用链）
- [ ] design.md：系统设计（架构、组件、API、状态机）

### IMPLEMENTING
- [ ] tasks.md：TDD 任务分解（RED-GREEN-REFACTOR）

### APPLYING
- [ ] RED: 写失败测试
- [ ] GREEN: 最小实现让测试通过
- [ ] REFACTOR: 重构
- [ ] 真实跑测试（铁律 7）
- [ ] apply-report.md：应用测试报告

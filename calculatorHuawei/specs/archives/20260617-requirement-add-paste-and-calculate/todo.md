# AID Workflow — 进度状态机

## 路径配置
- **SPECS_FEATURE_ROOT**: specs/specs (尚未建立 feat 目录)
- **CHANGES_ROOT**: specs/changes
- **WORKTREE**: D:/huawei/Demo/worktrees/issue-17
- **PROJECT_ROOT**: opencalc/ (HarmonyOS OpenCalc 迁移项目)
- **MAIN_REPO**: D:/huawei/Demo/calculatorHuawei

## 变更元数据
- **Date**: 20260617
- **Type**: requirement-add
- **Name**: paste-and-calculate
- **Issue**: #17 粘贴即计算
- **需求正文**: 支持从剪贴板粘贴数学表达式，粘贴后自动计算 | 粘贴计算 | ⭐ | 零操作体验
- **Intent**: Design/Development - New Requirement

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- **UI 自动化测试能力: ✅ 可用 (hdc + 模拟器 127.0.0.1:5555)**
- hdc: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- 模拟器状态: running

## 阶段状态

| 阶段 | 状态 | 产出物 | 备注 |
|------|------|--------|------|
| 初始化 | ✅ DONE | specs/initialized.flag | 沿用既有 opencalc 项目 |
| PLANNING | ✅ DONE | proposal.md / delta-spec.md / info.md / design.md / design-review.md | 全部产出物已落盘 |
| IMPLEMENTING | ✅ DONE | tasks.md | TDD 任务分解已规划 |
| APPLYING | ✅ DONE | apply-report.md | Node mock 12/12 PASS; CalculatorPage +61 行 |
| commit | 🔄 IN_PROGRESS | git commit (不 push) | dev-01 负责 push |

## 关键观察

1. **现有 paste 能力**：`CalculatorPage.ets:4` 已 `import { pasteboard }`，`onCopy()` 已实现 `setData`，需新增 `getData` 反向
2. **expression 自动联动**：`@State @Watch('onExpressionChange') expression` 已被监听，赋值自动触发 preview
3. **预览引擎**：复用 `computePreview()` 即可做"剪贴板内容校验"
4. **等号引擎**：复用 `onEquals()` 即可做"自动计算"
5. **错误反馈**：已有 `promptAction.showToast()`
6. **历史记录**：`onEquals()` 内自动 push HistoryItem

## 工作计划

### PLANNING
- [x] proposal.md / delta-spec.md / info.md / design.md / design-review.md / todo.md

### IMPLEMENTING
- [x] tasks.md

### APPLYING
- [x] T1.1 CalculatorPage 集成 (lastPastedHash + onPaste + onPageShow + computeHash) — +61 行
- [x] T2.1 ToggleRow 新增「📋粘贴」按钮 — +3 行
- [x] T3.1 Node mock 测试 — 12/12 PASS
- [ ] T3.2 真实 hvigorw 跑测 — ⏭️ Deferred (worktree 缺 resources/)
- [x] T4.1 UI 自动化脚本 — run_paste_tests.py + parse_ui.py
- [ ] T4.2 UI 自动化真跑 — ⏭️ Deferred (依赖 T3.2 编译产物)
- [x] apply-report.md — 12/12 PASS + 风险诚实披露

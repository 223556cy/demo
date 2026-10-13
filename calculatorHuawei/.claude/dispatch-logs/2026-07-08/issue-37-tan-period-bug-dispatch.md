# Issue #37 后续 (tan 周期) Dispatch Started (rev-01 → dev-01)

- **Time**: 2026-07-08 12:00
- **Title**: [bug] tan(x) 多周期 Y 轴被奇点污染 (issue #37 后续)
- **Type**: bugfix
- **Severity**: P1 — 用户在 GraphPage 选 tan(x) 看到的曲线"高度不一致",直接回归
- **Reporter**: rev-01 (littleleafbbbbb)
- **Worktree**: `D:\huawei\Demo\worktrees\issue-37` (复用)
- **Branch**: `fix/issue-37-tan-period-render` (从 `feat/issue-37-bug-sin-x-在-graphpa` 拉)
- **Spec 目录**: `specs/changes/20260708-bug-tan-period-render/`
- **Related**: Issue #37 (上游 sin 修复), Issue #26 (plot-graph 主线)
- **Root cause files**:
  - `worktrees/issue-37/opencalc/entry/src/main/ets/common/PlotUtils.ets:69-88` (`sampleSeries` 均匀采样)
  - `worktrees/issue-37/opencalc/entry/src/main/ets/common/PlotUtils.ets:127-152` (`computeYRange` min/max + clamp 被奇点污染)
- **Rev-01 comment file**: `.claude/dispatch-logs/2026-07-08/rev01_tan_period_bug.md`
- **Dispatch prompt file**: `.claude/dispatch-logs/2026-07-08/issue-37-tan-period-bug-prompt.txt`
- **Rev-01 fix strategy**: 方案 B (百分位 + 渐进限幅) + 方案 A (渐近线处 y=null 断线),不引入新依赖
- **TDD AC**: AC-22 (tan 多周期 yRange 有界) + AC-23 (sin/cos 无回归)

# todo.md — Issue #37 followup: tan(x) 多周期 Y 轴被奇点污染

## 任务进度

| # | 任务 | 状态 | 时间 | 备注 |
|---|------|------|------|------|
| 1 | 拉最新 + 读 worktree 状态 | ✅ | 15:00 | Issue #37 已处理于 365e189,新分支 fix/issue-37-tan-period-render |
| 2 | 读 PlotUtils.ets + 测试文件 | ✅ | 15:01 | 找到 sampleSeries:69-88 和 computeYRange:127-152 |
| 3 | 写 RED 测试 (AC-22 + AC-23) | ✅ | 15:02 | 7 个新测试,RED 阶段 AC-22.2/22.3 fail |
| 4 | 应用 B+A 修复到 .ets | ✅ | 15:03 | B: 百分位 + |y|>1e6 过滤;A: 值式 null |
| 5 | 同步测试 mock | ✅ | 15:04 | mock 镜像 .ets 逻辑 |
| 6 | 跑 GREEN 测试 | ✅ | 15:05 | 48/48 PASS,零回归 |
| 7 | 写 apply-report.md | ✅ | 15:06 | specs/changes/20260708-bug-tan-period-render/apply-report.md |
| 8 | git commit + force-push | ⏳ | 下一步 | 含 signoff |
| 9 | gh_helper.py comment | ⏳ | 下一步 | @littleleafccccc 转交 rev-01 v5 |

## 关键决策记录

- **方案 A 偏差**: rev-01 推荐位置式渐近线检测 (`|x - (π/2 + kπ)| < step * 0.5`),但这在 AC-2 大步长测试下回归 (x=2 时 0.43 < 0.5 → y 被 null 化)。改用**值式检测** (|y|>1e6 或非有限) 同时满足 AC-22 + AC-23 + AC-2.4
- **测试 mock 调整**: tan mock evaluator 从 `|cosx|<1e-12` 改为 `|tan|>5` 模拟真实数学引擎在渐近线附近返回 null 的行为
- **分支策略**: 新分支 `fix/issue-37-tan-period-render` 从 `feat/issue-37-bug-sin-x-在-graphpa` 拉,不修改 #37 的 commit history

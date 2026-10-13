# todo.md — Issue #37 任务进度

## 阶段状态
- [x] PLANNING (产出 5 个制品)
- [x] IMPLEMENTING (aid-implementing → tasks.md)
- [x] APPLYING (aid-applying + tdd-enforcer)

## 实际产物清单

| step | 制品 | 状态 |
|------|------|------|
| step1 | 用户意图识别 (bugfix) | ✅ |
| step2 | rq-parse → proposal.md | ✅ |
| step3 | rq-clarify (跳过,无 blocker) | ✅ 跳过 |
| step4 | delta-spec.md | ✅ |
| step5 | rq-codebase → info.md | ✅ |
| step6 | 复杂度评估 S 级 | ✅ |
| step7 | 架构设计 (跳过) | ✅ 跳过 |
| step8 | mod-design → delta-design.md | ✅ |
| step9 | design-review.md | ✅ |
| 实施 | opencalc/entry/src/main/ets/pages/GraphPage.ets | ✅ (双修复) |
| 测试 | tests/GraphPageLifecycle.test.mjs (10/10 PASS) | ✅ |
| 测试 | tests/GraphPageLifecycle.source.mjs (更新到 Task 5.3) | ✅ |
| 基线 | Calculator.test.mjs (13/13 PASS) | ✅ |
| 基线 | GraphViewModel.test.mjs (23/23 PASS) | ✅ |
| 编译 | hvigorw assembleHap (BUILD SUCCESSFUL) | ✅ |
| E2E | hdc install + start + 截图 graph_sin_rad_fixed.png | ✅ |
| 调试 | 无 console.log / debugger / hilog 调试 | ✅ |
| 报告 | apply-report.md | ✅ (下一步) |
| 提交 | git commit (no push) | ⏳ (下一步) |
| 通知 | gh_helper.py comment @littleleafccccc | ⏳ (下一步) |

## ⚠️ 实际执行发现:需要双修复

Issue #37 body 仅提出"时序竞态"修复 (方案 A),但实际验证发现:
**时序修复不足以解决问题**,因为:
- 时序修复后,`loadPrefs` 仍然在 `compute` 之前跑
- `loadPrefs` 调 `setRadianMode(!radianMode)` = `setRadianMode(true)` (用户默认 radiansDefault=false=角度)
- `compute` 用 isDegree=true → sin 当成角度算 → x∈[-6.28, 6.28]° → 小角近似 → 直线

**真正的根因有两层**:
1. 时序竞态 (issue body 指出的)
2. 语义错误 (用户默认角度 + GraphPage 跟随用户偏好 → 直线)

**应用两层修复 (Task 3.1 + Task 5.3)**:
- Task 3.1: 移动 `vm.compute()` 到 `loadPrefs().then()` 闭包
- Task 5.3: `setRadianMode(!radianMode)` → `setRadianMode(false)` 强制 GraphPage 用 radian

**第一轮截图失败 (graph_after_fix.png) → 第二轮截图成功 (graph_sin_rad_fixed.png)**
第一次只做时序修复,截图仍为直线。
应用 Task 5.3 后,截图显示完整正弦波 (2 个可见波峰 + 2 个可见波谷,在 [-2π, 2π] 范围内)。

## 决策记录

### git_branch_adopted
- true (已在 feat/issue-37-bug-sin-x-在-graphpa 分支)

### 用户确认点处理
- 阶段间确认: 自动同意 (方案 C)
- 编译环境检查: `run-build-wt.bat` 创建并跑通 (含 DEVECO_SDK_HOME + JAVA_HOME)
- 高风险点暂停:
  - capabilities.json 缺失 → 已存在 ✅
  - hvigorw/hdc 不在 PATH → hdc 直接调用, hvigorw 走 .bat ✅
  - arch-refactor/platform-migration → 否 (本次 bugfix)
  - delta-spec/delta-design 涉及删除现有功能 → 否 (仅修改一处方法)
  - SKILL 安全拦截 → 无拦截

### ⚠️ 设计审视警告的实际应用
- 语义翻转问题 → 实际验证发现确实需要 Task 5.3 扩展修复
- todo.md 警告的"先做时序修复, hilog + 截图验证"流程执行了
- 第一轮截图证明时序修复不够,立即应用 Task 5.3

## 下一阶段
git commit → gh_helper.py 通知 dev-01

# tasks.md — Issue #37 开发任务

## 任务概述

- **功能名称**：sin(x) 在 GraphPage 渲染成直线 — isDegree 时序竞态修复
- **变更类型**：bugfix
- **关联特性**：Issue #26 plot-graph
- **开发阶段**：单文件修改 + 新增 1 个测试 + 端到端验证
- **预计任务数**：6

## 任务列表

### 阶段 1：环境与基线

#### Task 1.1: 环境检查
**描述**：验证 hvigorw / hdc 在 PATH 中可用
**涉及文件**: 无
**依赖任务**：无
**验收标准**：
- `which hvigorw` 输出路径
- `which hdc` 输出路径 (或 DevEco SDK hdc.exe 路径)
- hdc 能列出至少 1 个 device (127.0.0.1:5555)

#### Task 1.2: 基线测试
**描述**：跑 Calculator.test.mjs + GraphViewModel.test.mjs 确认无回归基线
**涉及文件**：
- `specs/changes/20260617-requirement-add-plot-graph/tests/Calculator.test.mjs`
- `specs/changes/20260617-requirement-add-plot-graph/tests/GraphViewModel.test.mjs`
**依赖任务**：无
**验收标准**：
- Calculator.test.mjs: 13/13 PASS
- GraphViewModel.test.mjs: 23/23 PASS

### 阶段 2：RED 测试 (TDD 第一步)

#### Task 2.1: 新增 GraphPageLifecycle.test.mjs (RED)
**描述**：写一个 Node 端测试,模拟 aboutToAppear 时序,断言 `vm.compute()` 必须在 `loadPrefs()` 完成 `.then()` 后才触发
**涉及文件**：
- `specs/changes/20260708-bugfix-sin-straight-line/tests/GraphPageLifecycle.test.mjs` (新增)
- `specs/changes/20260708-bugfix-sin-straight-line/tests/GraphPageLifecycle.source.mjs` (新增 - mock 组件)
**依赖任务**：Task 1.2
**验收标准**：
- 测试断言:`compute` 调用次数 ≥ 1
- 测试断言:`compute` 调用时 `loadPrefs` 已 resolve (isDegree 已设置)
- 测试断言:`setTimeout` 不被使用 (或被替换为微任务)
- 当前测试在 BUG 状态下应 **FAIL** (RED 状态)
- 测试覆盖方案 A (issue #37 body 推荐): 仅修时序,保留 `setRadianMode(!radianMode)` 语义翻转

### 阶段 3：GREEN 修复 (TDD 第二步)

#### Task 3.1: 修复 GraphPage.ets:46-62 aboutToAppear()
**描述**：删除 `setTimeout(() => vm.compute(), 0)`,把 `vm.compute()` 移入 `prefs.init().then()` 闭包
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/GraphPage.ets` (修改)
**依赖任务**：Task 2.1
**修复代码**：
```typescript
aboutToAppear(): void {
    // 路由参数处理 (不变)
    const params = router.getParams() as Record<string, Object> | undefined
    if (params !== undefined && params !== null) {
      const expr = params['expression'] as string | undefined
      if (expr !== undefined && expr.length > 0 && expr.length <= MAX_INPUT_LENGTH) {
        this.vm.expression = expr
        this.expressionInput = expr
      }
    }
    // 读取偏好 + 首次计算 (修复时序)
    const ctx: common.UIAbilityContext = getContext(this) as common.UIAbilityContext
    this.prefs = new PreferencesStore(ctx)
    this.prefs.init()
      .then((): void => {
        this.loadPrefs()
        this.vm.compute()
      })
      .catch((): void => {
        // 降级: VM 默认 isDegree=false,直接计算
        this.vm.compute()
      })
}
```
**验收标准**：
- GraphPageLifecycle.test.mjs: PASS (GREEN 状态)
- Calculator.test.mjs: 13/13 PASS (无回归)
- GraphViewModel.test.mjs: 23/23 PASS (无回归)
- 代码改动 ≤ 8 行 (含 `.catch()` 降级)

#### Task 3.2: 验证编译
**描述**：跑 `hvigorw --no-daemon assembleHap` 确认编译通过
**涉及文件**：无
**依赖任务**：Task 3.1
**验收标准**：
- hvigorw 退出码 0
- 生成 `entry/build/default/outputs/default/entry-default-signed.hap`

### 阶段 4：REFACTOR 清理 (TDD 第三步)

#### Task 4.1: 清理调试代码
**描述**：检查并删除任何遗留的 `console.log` 调试输出
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/GraphPage.ets`
- `opencalc/entry/src/main/ets/viewmodels/GraphViewModel.ets`
- `opencalc/entry/src/main/ets/calculator/Calculator.ets`
**依赖任务**：Task 3.2
**验收标准**：
- 无新增 `console.log` / `console.error`
- 无新增 `hilog` 调试标记

### 阶段 5：端到端验证

#### Task 5.1: 部署到模拟器
**描述**：装 HAP 到 127.0.0.1:5555,启动 OpenCalc,切到程序员模式,进入 GraphPage
**涉及文件**：无
**依赖任务**：Task 4.1
**验收标准**：
- hdc install 成功
- 应用启动无崩溃

#### Task 5.2: hilog + 截图取证
**描述**：抓 hilog 日志确认 `deg=false`,截图确认曲线有 3 波峰 + 3 波谷
**涉及文件**：
- `specs/changes/20260708-bugfix-sin-straight-line/screenshots/sin-after-fix.png` (截图)
**依赖任务**：Task 5.1
**验收标准**：
- hilog 显示 `evalAt_in ... deg=false`
- x=π/2 ≈ 1.57 时 y ≈ 1.0
- x=π ≈ 3.14 时 y ≈ 0.0
- x=3π/2 ≈ 4.71 时 y ≈ -1.0
- y_min < -0.9 且 y_max > 0.9
- 截图:曲线有 3 个波峰 + 3 个波谷

#### Task 5.3: ⚠️ 语义翻转验证 (扩展修复)
**描述**：如果 Task 5.2 截图显示 sin 仍为直线 (因为 `setRadianMode(!radianMode)` 语义翻转),需扩展修复为去掉 `!`
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/GraphPage.ets` (修改 loadPrefs)
**依赖任务**：Task 5.2
**判定标准**：
- 若 hilog 显示 `deg=false` 但 sin 仍为直线 → 是 isDegree 实际被错设为 true,需去掉 `!`
- 若 hilog 显示 `deg=false` 且 sin 正确 → 完成,无需扩展

**修复代码 (若需)**:
```typescript
async loadPrefs(): Promise<void> {
    if (!this.prefs) return
    const radianMode = await this.prefs.getRadiansDefault()
    // radianMode=true → 弧度制 → isDegree=false
    // radianMode=false → 角度制 → isDegree=true
    // 即 isDegree = !radianMode (保持现状)
    this.vm.setRadianMode(!radianMode)
    // ...
}
```
⚠️ **注意**: 如果去掉 `!`,需在 PR 描述中说明这是 issue #37 的扩展修复,与时序修复一起提交,留给 rev-01 评审。
**验收标准**：
- 扩展修复后 sin 正确显示
- 重新跑 hilog + 截图

### 阶段 6：交付

#### Task 6.1: 写 apply-report.md
**描述**：产出 apply-report.md 记录完整过程
**涉及文件**：
- `specs/changes/20260708-bugfix-sin-straight-line/apply-report.md`
**依赖任务**：Task 5.2 (或 Task 5.3)
**验收标准**：
- 包含 RED/GREEN/REFACTOR 三阶段记录
- 包含测试结果 (含回归)
- 包含 hilog 证据 + 截图路径
- 包含代码 diff 摘要

#### Task 6.2: git commit
**描述**：提交所有改动到 feat/issue-37-bug-sin-x-在-graphpa 分支
**涉及文件**：
- 所有修改 + 新增文件
**依赖任务**：Task 6.1
**验收标准**：
- 1 个 commit,message 遵循 Conventional Commits
- commit message:`fix(graph): move vm.compute() into loadPrefs().then() to fix sin(x) straight-line bug (Closes #37)`
- **不 push** (dev-01 负责 push)

#### Task 6.3: 通知 dev-01
**描述**：用 gh_helper.py 在 Issue #37 评论 @littleleafccccc 转交评审
**涉及文件**：无
**依赖任务**：Task 6.2
**验收标准**：
- gh_helper.py comment 37 "@littleleafccccc claude -p 跑完,worktree 在 D:/huawei/Demo/worktrees/issue-37 等 push"

## 开发顺序

```
Task 1.1 → Task 1.2 → Task 2.1 (RED) → Task 3.1 (GREEN) → Task 3.2 → Task 4.1 → Task 5.1 → Task 5.2 → [Task 5.3 (条件性)] → Task 6.1 → Task 6.2 → Task 6.3
```

## 验收计划

| 任务 | 验收方式 | 备注 |
|------|---------|------|
| Task 1.1 | which / hdc list targets | 环境就绪 |
| Task 1.2 | node test/*.mjs | 基线通过 |
| Task 2.1 | node test/GraphPageLifecycle.test.mjs | RED 状态 (测试失败) |
| Task 3.1 | node test/*.mjs | GREEN 状态 (测试通过) |
| Task 3.2 | hvigorw assembleHap | 编译成功 |
| Task 4.1 | grep console.log | 无调试代码 |
| Task 5.1 | hdc install + start | 应用运行 |
| Task 5.2 | hilog + screenshot | hilog deg=false, 截图正确 |
| Task 5.3 | hilog + screenshot (条件性) | 仅当 Task 5.2 显示仍为直线时执行 |
| Task 6.1 | apply-report.md | 报告完整 |
| Task 6.2 | git log | commit 已落地 |
| Task 6.3 | gh_helper.py | 评论已发 |

## 风险预案

| 风险 | 触发条件 | 应对 |
|------|---------|------|
| hvigorw 编译失败 | Task 3.2 退出码非 0 | 检查 ArkTS 语法,确认 .then().catch() 链语法正确 |
| 模拟器未运行 | hdc list targets 空 | 启动 DevEco Studio 模拟器 |
| 时序修复后仍为直线 | Task 5.2 截图失败 | 触发 Task 5.3 扩展修复 |
| Calculator/GraphViewModel 测试回归 | Task 3.1 测试失败 | 修复后跑基线对比,确保无回归 |

---
> 生成时间: 2026-07-08
> 生成人: aid-implementing skill
> 下一阶段: aid-applying (+ tdd-enforcer)
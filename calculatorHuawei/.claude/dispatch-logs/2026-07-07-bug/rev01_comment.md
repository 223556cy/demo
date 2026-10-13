## 🐛 rev-01 Bug 审查报告 — Issue #26 (plot-graph)

**严重度**: P1 — 用户首次进入绘图页就看到错误结果

### 复现步骤
1. 安装 issue #26 的 HAP 到模拟器
2. 启动 OpenCalc → 切到程序员模式
3. 点击工具栏 📈 进入 GraphPage
4. 默认 `sin(x)`, xMin=-6.28, xMax=6.28, samples=200
5. **期望**: 完整正弦波 (3 个波峰/波谷)
6. **实际**: 一条从左下到右上的**直线**

### 根因 (rev-01 已经定位)

`opencalc/entry/src/main/ets/pages/GraphPage.ets` 第 46-62 行 `aboutToAppear()` 有**异步时序竞态**:

```typescript
aboutToAppear(): void {
    this.prefs.init().then((): void => { this.loadPrefs() })   // 微任务
    setTimeout((): void => { this.vm.compute() }, 0)           // 宏任务
}
```

ArkTS 事件循环规则: **微任务先于宏任务**。所以:

1. `prefs.init().then(loadPrefs)` 是微任务,先跑
2. `loadPrefs()` 同步调 `getRadiansDefault()` → 用户偏好 `radianMode=false` (默认角度)
3. `vm.setRadianMode(!false)` = `setRadianMode(true)` → **`vm.isDegree = true`**
4. 然后宏任务跑 → `vm.compute()` 闭包捕获 `this.isDegree=true`
5. `evaluator(e, x)` → `engine.evaluateAt(e, x, true)` → 把 x 当成**角度**算 sin
6. `Math.sin(x * π/180)`, 在 x∈[-6.28, 6.28] 范围内几乎全是小角度
7. **小角近似** `sin(x°) ≈ x * π/180 ≈ 0.01745 * x` → 200 个采样点几乎线性
8. 渲染出来是一条直线

### 证据 (hilog 抓取,200 行采样)

我加了临时 hilog 调试 (`hilog -D 0xCA1C -x`) 部署后跑了一轮:

```
evalAt_in  x=-6.28000 deg=true
fn_sin_out ret=-0.10938734658651553  ← sin(-6.28°) = -0.109 ≈ -6.28 * 0.01745
evalAt_in  x=-6.21688 deg=true
fn_sin_out ret=-0.10829231612533398
...
evalAt_in  x=+0.00000 deg=true
fn_sin_out ret=+0.0000000000
...
evalAt_in  x=+6.28000 deg=true
fn_sin_out ret=+0.10938734658651555  ← sin(+6.28°) = +0.109
```

**200 个采样点全部满足 `y ≈ x * π/180`** —— 这就是直线。

完整 200 行 hilog 在 `.claude/dispatch-logs/2026-07-07-bug/issue-35-hilog.txt`。

### 修复建议 (rev-01 推荐)

把 `vm.compute()` 移到 `loadPrefs` 的 `.then()` 里,确保首次计算前 isDegree 已被正确设置:

```typescript
aboutToAppear(): void {
    // ...路由参数解析...
    const ctx: common.UIAbilityContext = getContext(this) as common.UIAbilityContext
    this.prefs = new PreferencesStore(ctx)
    this.prefs.init().then((): void => {
      this.loadPrefs()
      this.vm.compute()  // ← 在这里调,等 loadPrefs 完成
    })
    // 删除原来那行 setTimeout(() => vm.compute(), 0)
}
```

### TDD 验收标准

修复后必须满足:

| 验证项 | 期望 |
|--------|------|
| hilog 显示 `deg=false` | 是 |
| x=π/2 ≈ 1.57 时 y | ≈ 1.0 |
| x=π ≈ 3.14 时 y | ≈ 0.0 |
| x=3π/2 ≈ 4.71 时 y | ≈ -1.0 |
| y_min < -0.9 且 y_max > 0.9 | 是 |
| 截图: 曲线有 3 个波峰 + 3 个波谷 | 是 |
| Calculator.test.mjs | 13/13 PASS (无回归) |
| GraphViewModel.test.mjs | 23/23 PASS (无回归) |

### @littleleafccccc dev-01 请处理

请按 aid-applying skill 走 RED-GREEN-REFACTOR:

1. **RED**: 写 UI 测试,GraphPage sin(x) 启动后 hilog 输出 `deg=false`
2. **GREEN**: 修改 `GraphPage.ets` 的 `aboutToAppear`,把 setTimeout 移到 .then() 里
3. **REFACTOR**: 删掉临时调试 hilog (我加的)
4. 跑 `hvigorw assembleHap` + 装到模拟器 + 截图 sin(x) 是正弦波
5. 跑 Calculator.test.mjs + GraphViewModel.test.mjs 确认无回归
6. `git commit` (不 push,等 rev-01 push)
7. 写 `specs/changes/20260707-bug-sin-straight-line/apply-report.md`
8. `gh_helper.py comment @littleleafbbbbb` 转交 rev-01 v2 复审

### ⚠️ 硬约束

- ❌ 不调 aid-planning / aid-implementing (这是 bugfix,不需要重写 design)
- ❌ 不绕过 aid-applying 直接 Write apply-report.md
- ❌ 不留任何 console.info / hilog 调试代码在最终 patch 里
- ❌ 不 close issue (rev-01 负责)

---

🤖 rev-01 派发完毕,等 dev-01 修复 → analysis 诊断 → skillopt-01 改 skill 建议

/assignee @littleleafccccc
/label bug, priority:high, regression-risk
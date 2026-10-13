## 🐛 Bug: sin(x) 在 GraphPage 上渲染成直线 (Plot-Graph 时序竞态)

**类型**: bugfix (P1 - 用户首次进入绘图页就看到错误结果)
**关联**: Issue #26 (plot-graph)

### 复现步骤
1. 安装 issue #26 的 HAP 到 DevEco 模拟器
2. 启动 OpenCalc → 切到程序员模式
3. 点击工具栏 📈 进入 GraphPage
4. 默认 `sin(x)`, xMin=-6.28, xMax=6.28, samples=200
5. **期望**: 完整正弦波 (3 个波峰/波谷)
6. **实际**: 一条从左下到右上的**直线**

### 根因 (rev-01 已定位)

`opencalc/entry/src/main/ets/pages/GraphPage.ets` 第 46-62 行 `aboutToAppear()` 有**异步时序竞态**:

```typescript
aboutToAppear(): void {
    this.prefs.init().then((): void => { this.loadPrefs() })   // 微任务
    setTimeout((): void => { this.vm.compute() }, 0)           // 宏任务
}
```

ArkTS 事件循环规则: **微任务先于宏任务** 执行。所以:

1. `prefs.init().then(loadPrefs)` 微任务先跑
2. `loadPrefs()` 调 `getRadiansDefault()` → 用户偏好 `radianMode=false` (默认角度)
3. `vm.setRadianMode(!false)` = `setRadianMode(true)` → **`vm.isDegree = true`**
4. 然后宏任务跑 → `vm.compute()` 闭包捕获 `this.isDegree=true`
5. `engine.evaluateAt(e, x, true)` → 把 x 当成**角度**算 sin
6. `Math.sin(x * π/180)`, 在 x∈[-6.28, 6.28] 范围内几乎全是小角度
7. **小角近似** `sin(x°) ≈ x * π/180 ≈ 0.01745 * x` → 200 个采样点几乎线性
8. 渲染出来是一条直线

### 证据 (hilog 抓取)

```
evalAt_in  x=-6.28    deg=true
fn_sin_out ret=-0.10938734658651553  ← sin(-6.28°) ≈ -0.109
evalAt_in  x=+6.28    deg=true
fn_sin_out ret=+0.10938734658651555  ← sin(+6.28°) ≈ +0.109
```

200 个采样点全部满足 `y ≈ x * π/180` (线性) → 画出来是直线。

### 修复建议

把 `vm.compute()` 移到 `loadPrefs` 的 `.then()` 里:

```typescript
aboutToAppear(): void {
    // ...路由参数解析...
    const ctx: common.UIAbilityContext = getContext(this) as common.UIAbilityContext
    this.prefs = new PreferencesStore(ctx)
    this.prefs.init().then((): void => {
      this.loadPrefs()
      this.vm.compute()  // ← 在这里调,等 loadPrefs 完成
    })
    // 删除原来的 setTimeout(() => vm.compute(), 0)
}
```

### TDD 验收标准

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

### 工作要求

按 aid-applying skill (含 tdd-enforcer) 走 RED-GREEN-REFACTOR:

1. **RED**: 写一个 Node 测试模拟 aboutToAppear 时序,断言 loadPrefs 完成前不能触发 vm.compute (或者 UI 测试中 sin(x) 渲染时 hilog 必须显示 deg=false)
2. **GREEN**: 修改 `GraphPage.ets` 把 setTimeout 移到 .then() 里
3. **REFACTOR**: 清理调试代码
4. 跑 `hvigorw assembleHap` + 装到模拟器 + 截图
5. 跑 Calculator.test.mjs + GraphViewModel.test.mjs 确认无回归
6. `git commit` (不 push,等 rev-01 push)
7. 写 `specs/changes/20260707-bug-sin-straight-line/apply-report.md`
8. `gh_helper.py comment @littleleafbbbbb` 转交 rev-01 v4 复审

### 关联资源

- rev-01 完整诊断 + hilog 证据: issue #26 评论 #4910684088
- 根因代码位置: `opencalc/entry/src/main/ets/pages/GraphPage.ets:46-62`
- 期望 worktree: `D:/huawei/Demo/worktrees/issue-35`
- 期望 branch: `fix/issue-35-sin-straight-line`
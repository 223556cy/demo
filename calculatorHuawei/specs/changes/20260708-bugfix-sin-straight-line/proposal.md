# 需求提案 (proposal.md) — Issue #37

## 需求解析报告

### 原始需求
> [bug] sin(x) 在 GraphPage 渲染成直线 — isDegree 时序竞态 (issue #26 回归)

### 意图分类
- **类型**：缺陷修复 (bugfix)
- **一句话概括**：修复 `GraphPage.ets` 中 `aboutToAppear()` 内 `vm.compute()` 与 `loadPrefs()` 的微任务/宏任务执行顺序竞态,导致 `isDegree` 被错误地从用户偏好 (`radianMode=false` 默认) 翻转为 `true`,进而 `engine.evaluateAt` 把 x 当作角度计算,小角近似下 200 个采样点几乎线性,sin 曲线渲染为直线。

### 领域映射
- **UI/交互**：GraphPage 页面初始化流程 (ArkTS 生命周期 `aboutToAppear`)
- **状态管理**：`GraphViewModel.isDegree` 状态初始化时序
- **数据管理**：`PreferencesStore.getRadiansDefault()` 异步持久化读取

### 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View (pages/GraphPage.ets) | modify | 调整 `aboutToAppear` 中 `setTimeout` 调用顺序,确保 `vm.compute()` 在 `loadPrefs().then()` 内执行 |
| ViewModel (viewmodels/GraphViewModel.ets) | modify (potential) | 需检查 `compute()` 是否依赖 `isDegree` 完成设置 |
| 数据层 (PreferencesStore) | 不变 | 读取逻辑正常,问题在调用顺序 |

### 关键实体
- **页面实体**：`GraphPage` (`opencalc/entry/src/main/ets/pages/GraphPage.ets:46-62`)
- **接口实体**：`PreferencesStore.init()` / `loadPrefs()` / `getRadiansDefault()`,`GraphViewModel.compute()`
- **事件实体**：`aboutToAppear` 生命周期事件,Promise 微任务 vs setTimeout 宏任务
- **数据实体**：`isDegree` (GraphViewModel 状态字段)

### 模糊点
| # | 类别 | 描述 | 严重程度 |
|---|------|------|----------|
| 1 | 行为模糊 | 是否需要在 loadPrefs 失败时设置默认值? | nice-to-have |
| 2 | 范围模糊 | 其他 ViewModel 字段(如 `xMin`/`xMax`/`samples`)是否也需在 loadPrefs 后才设置? | nice-to-have |

### 复杂度评估
- **等级**：S (简单)
- **理由**：单文件改动,核心修复是 1-3 行代码调整;根因明确且已被 rev-01 定位;无新数据模型、无架构变更。

### 备注
- 需求已足够清晰,无需 `rq-clarify` 澄清。
- 这是 issue #26 的回归问题,优先级 P1 (用户首次进入绘图页即看到错误结果)。
- 修复方案已由 issue body 提供,只需按方案执行并 TDD 验收。

## 修复方案

### 根因分析

`aboutToAppear()` 当前实现:
```typescript
aboutToAppear(): void {
    this.prefs.init().then((): void => { this.loadPrefs() })   // 微任务
    setTimeout((): void => { this.vm.compute() }, 0)           // 宏任务
}
```

ArkTS 事件循环规则: **微任务先于宏任务** 执行。

执行序列:
1. `prefs.init().then(loadPrefs)` 入队微任务
2. `setTimeout(compute, 0)` 入队宏任务
3. 微任务执行 → `loadPrefs()` → `getRadiansDefault()` 返回 `false` → `setRadianMode(!false) = setRadianMode(true)` → `vm.isDegree = true`
4. 宏任务执行 → `vm.compute()` 使用 `isDegree=true` 计算
5. `engine.evaluateAt(e, x, true)` 把 x 当作角度 → `Math.sin(x * π/180)` 在 x∈[-6.28, 6.28] 内小角近似为线性 → 直线

### 修复代码

```typescript
aboutToAppear(): void {
    const ctx: common.UIAbilityContext = getContext(this) as common.UIAbilityContext
    this.prefs = new PreferencesStore(ctx)
    this.prefs.init().then((): void => {
        this.loadPrefs()      // 先加载偏好
        this.vm.compute()     // 等 loadPrefs 完成再 compute
    })
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
| Calculator.test.mjs | 13/13 PASS |
| GraphViewModel.test.mjs | 23/23 PASS |

## 后续流程

1. **step3 (需求澄清)**: 无 blocker/important 级模糊点,跳过。
2. **step4 (delta-spec)**: 输出 delta-spec.md
3. **step5 (info.md)**: 通过 rq-codebase 产出
4. **step6 (复杂度评估)**: S 级,见上
5. **step7 (new-arch)**: 简单需求无架构变更,跳过
6. **step8 (delta-design)**: 通过 mod-design 产出
7. **step9 (design-review)**: 输出 design-review.md
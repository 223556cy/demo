# info.md — Issue #37 代码仓理解

## 基本信息
- **需求类别**：缺陷修复 (bugfix)
- **需求名称**：sin(x) 在 GraphPage 渲染成直线 — isDegree 时序竞态
- **分析时间**：2026-07-08
- **分析范围**：GraphPage 初始化时序 + GraphViewModel.compute() + PreferencesStore.getRadiansDefault() + Calculator.evaluateAt()

## 架构分析

### 模块依赖
```
GraphPage.ets (View)
    ↓ 调用
GraphViewModel.ets (ViewModel)
    ↓ 持有 CalcEngine 实例
Calculator.ets (Calculator)
    ↓ 使用
PreferencesStore.ets (数据层)
```

### 关键调用链 (aboutToAppear)
```
GraphPage.aboutToAppear()
  ├── router.getParams()                      // 同步读取路由参数
  ├── new PreferencesStore(ctx)               // 同步构造
  ├── prefs.init().then(loadPrefs)            // 微任务: 异步初始化 + 加载偏好
  └── setTimeout(vm.compute, 0)               // 宏任务: 首次计算 ❌ BUG 触发点
```

## 接口/契约识别

### GraphPage.aboutToAppear()
- **签名**：`(): void`
- **调用约束**：ArkTS 生命周期钩子,页面显示前同步执行
- **副作用**：发起异步操作 `prefs.init()`,并将 `vm.compute()` 排队到下一个宏任务

### PreferencesStore.init()
- **签名**：`async init(): Promise<void>`
- **实现**：调用 `preferences.getPreferences(this.context, PREF_NAME)` 异步获取存储实例
- **约束**：必须在调用任何 getter 前完成

### PreferencesStore.getRadiansDefault()
- **签名**：`async getRadiansDefault(): Promise<boolean>`
- **实现**：返回 `this.store.get('radiansDefault', DEFAULT_PREFERENCES.radiansDefault)`
- **默认值**：`DEFAULT_PREFERENCES.radiansDefault = false` (即默认弧度制)

### GraphPage.loadPrefs()
- **签名**：`async loadPrefs(): Promise<void>`
- **实现**：
  ```typescript
  const radianMode = await this.prefs.getRadiansDefault()
  this.vm.setRadianMode(!radianMode)  // radianMode=true → 弧度 → isDegree=false
  ```
- **关键逻辑**：`setRadianMode(!radianMode)` — 偏好 `radianMode=false` → `isDegree=true`(BUG!) 应改为 `isDegree=false`

### GraphViewModel.setRadianMode(isDeg)
- **签名**：`(isDeg: boolean): void`
- **实现**：`this.isDegree = isDeg`
- **关键**：`isDeg` 为 `true` 表示**角度制**;`false` 表示**弧度制**

### GraphViewModel.compute()
- **签名**：`() => void`
- **实现**：校验 → 预处理 → 采样求值 → 错误处理
- **采样求值**：`this.engine.evaluateAt(e, x, this.isDegree)` — 使用 `this.isDegree` 决定是否把 x 当作角度
- **关键**：`this.isDegree` 在 compute() 调用瞬间必须是正确值

### Calculator.evaluateAt(expr, x, isDegree)
- **签名**：`(expr: string, x: number, isDegree: boolean): number | null`
- **实现**：当 `isDegree=true` 时,三角函数把 x 当作角度 (`Math.sin(x * π/180)`)
- **关键**：sin 在 x∈[-6.28, 6.28] 且 isDegree=true 时,`sin(x°) ≈ x * π/180 ≈ 0.01745x` → 近似线性

## 公共组件或函数识别

| 名称 | 位置 | 复用价值 |
|------|------|---------|
| `PreferencesStore` | `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets` | 已有,无需复用 |
| `GraphViewModel.compute()` | `opencalc/entry/src/main/ets/viewmodels/GraphViewModel.ets:55` | 已有,无需修改 |

## 影响范围分析

### 需要修改的模块/文件清单
| 文件 | 行号 | 变更类型 | 说明 |
|------|------|---------|------|
| `opencalc/entry/src/main/ets/pages/GraphPage.ets` | 46-62 | modify | 删除 `setTimeout`,把 `vm.compute()` 移入 `loadPrefs().then()` |

### 调用链上下游
```
GraphPage (修改) → GraphViewModel.compute (不变) → Calculator.evaluateAt (不变)
                  → PreferencesStore.getRadiansDefault (不变)
```

### 影响评估
- **行为变化**：仅在用户偏好 `radiansDefault=false` (默认弧度) 时,`vm.isDegree` 从 `true` 改为 `false` → sin/cos/tan 在 x∈[-6.28, 6.28] 渲染为完整周期曲线(修复)。
- **兼容性**：`radiansDefault=true` (用户切换为角度) 时,行为不变,无回归。
- **风险等级**：低 — 单文件、单方法、3-5 行修改。

## 现有代码分析

### 当前 GraphPage.ets:46-62
```typescript
aboutToAppear(): void {
    // 读取路由参数(可选)
    const params = router.getParams() as Record<string, Object> | undefined
    if (params !== undefined && params !== null) {
      const expr = params['expression'] as string | undefined
      if (expr !== undefined && expr.length > 0 && expr.length <= MAX_INPUT_LENGTH) {
        this.vm.expression = expr
        this.expressionInput = expr
      }
    }
    // 读取偏好
    const ctx: common.UIAbilityContext = getContext(this) as common.UIAbilityContext
    this.prefs = new PreferencesStore(ctx)
    this.prefs.init().then((): void => { this.loadPrefs() })  // ← 微任务
    // 首次计算
    setTimeout((): void => { this.vm.compute() }, 0)          // ← 宏任务,先于微任务执行 ❌
}
```

### GraphViewModel 默认值
```typescript
isDegree: boolean = false  // 弧度制 (符合用户偏好默认值)
```

### 默认值反差
- GraphViewModel 默认 `isDegree = false` (弧度) ✅
- PreferencesStore 默认 `radiansDefault = false` → loadPrefs 中 `setRadianMode(!false) = setRadianMode(true)` → 翻转成角度 ❌

这是另一个潜在的语义混淆点:
- **偏好字段命名**: `radiansDefault` 是"是否使用弧度制"
- **VM 字段命名**: `isDegree` 是"是否为角度制"
- 转换逻辑: `isDegree = !radiansDefault`

用户偏好 `radiansDefault=false`(默认弧度) → `isDegree = true`(角度) — 这是一个 **意外的语义翻转**!

### 修复目标
将 `vm.compute()` 移入 `loadPrefs().then()`,确保 `isDegree` 已被正确设置后再计算。

## 风险识别

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| 其他 ViewModel 字段(如 `xMin/xMax`)也未在 compute 前读取 | 中 | 仅 `isDegree` 来自偏好,`xMin/xMax/samples` 由 `@State` 默认值提供,无需处理 |
| `loadPrefs()` 失败时 `compute()` 永不被调用 | 中 | 单元测试验证:模拟 init 失败应不调用 compute 或 vm 已有合理默认值 |
| `setRadianMode` 的语义混淆 (`!radiansDefault`) | 低 | 不在本修复范围,但记录为 P2 后续改进 |
| 开发者误改回 `setTimeout` 引入回归 | 中 | TDD 测试 AC-9: 断言 compute 必须在 loadPrefs 后触发 |

## 测试验证策略

### 测试场景
1. **AC-1 ~ AC-6** (hilog + 截图 + 数值): 通过 `harmonyos-ui-test` 跑 `GraphPage` 端到端
2. **AC-7 ~ AC-8** (回归): 跑现有 `Calculator.test.mjs` 和 `GraphViewModel.test.mjs`
3. **AC-9** (时序 RED 测试): Node 端 mock 测试 `aboutToAppear` 时序,断言 `compute` 必须在 `loadPrefs` 完成 `.then()` 后执行

### 回归测试范围
- `Calculator.test.mjs` — 13 测试 (CalcEngine.evaluateAt 角度/弧度)
- `GraphViewModel.test.mjs` — 23 测试 (compute 流程)
- `PlotUtils.test.mjs` — 间接相关 (sampleSeries)

## 监控运维支持

### 日志要点
- `engine.evaluateAt` 现有 `evalAt_in / fn_*_out` hilog 标记,可用于验证 `deg=true/false`
- 修复后 hilog 应显示 `deg=false`

### 配置项
- 偏好键 `radiansDefault` (boolean, 默认 `false`)

## 关键发现

### 可复用组件或函数
- 无新增;复用现有的 `PreferencesStore.loadPrefs()` + `GraphViewModel.compute()` 调用即可

### 风险提示
- ⚠️ `setRadianMode(!radiansDefault)` 的语义翻转是潜在的 UX 陷阱,本次修复仅解决时序竞态,语义问题作为后续 P2 改进

### 建议事项
1. **修复时序竞态**(本 Issue): 把 `vm.compute()` 移入 `loadPrefs().then()`
2. **保留现有逻辑**: `setRadianMode(!radiansDefault)` 维持现状(避免扩大本 Issue 范围)
3. **新增 TDD 测试**: 模拟 aboutToAppear 时序,断言 `compute` 必须在 `loadPrefs` 完成后才触发
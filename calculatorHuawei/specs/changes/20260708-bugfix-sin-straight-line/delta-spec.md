# delta-spec.md — Issue #37 增量规格

> 关联 Issue: #37 [bug] sin(x) 在 GraphPage 渲染成直线 — isDegree 时序竞态 (issue #26 回归)
> 关联特性: Issue #26 函数图像 (plot-graph)

## 1. 变更概述

修复 `GraphPage.ets:aboutToAppear()` 内 `vm.compute()` 与 `loadPrefs()` 的微任务/宏任务执行顺序竞态,确保 `vm.compute()` 仅在 `PreferencesStore.loadPrefs()` 完成、`vm.isDegree` 等偏好字段正确设置后再触发。

## 2. 需求分解

### 2.1 功能需求

| ID | 描述 | 优先级 |
|----|------|--------|
| FR-1 | `GraphPage.aboutToAppear()` 中 `vm.compute()` 必须在 `loadPrefs().then()` 内部调用,而非 `setTimeout` 宏任务 | P0 |
| FR-2 | 修复后,默认 sin(x)、xMin=-6.28、xMax=6.28、samples=200 的渲染结果必须是完整正弦波(3 个波峰 + 3 个波谷) | P0 |
| FR-3 | 修复后,`vm.isDegree` 默认值应为 `false`(与 `radianMode` 默认值 `false` 一致) | P0 |

### 2.2 非功能需求

| ID | 描述 |
|----|------|
| NFR-1 | 现有 Calculator.test.mjs 13/13 必须保持通过(无回归) |
| NFR-2 | 现有 GraphViewModel.test.mjs 23/23 必须保持通过(无回归) |
| NFR-3 | 修复代码量 ≤ 5 行 |

## 3. 可靠性分析 (FMEA 消减措施清单)

| 故障模式 | 严重度 | 发生率 | 风险等级 | 改进措施 |
|---------|--------|--------|---------|----------|
| 微任务/宏任务执行顺序违反 ArkTS 事件循环规则 | 高 | 高 | **极高** | 删除 `setTimeout` 包装,将 `vm.compute()` 移入 `loadPrefs().then()` 闭包 |
| `loadPrefs()` 失败时 `vm.compute()` 仍执行 | 中 | 低 | 中 | 在 `loadPrefs()` 末尾同步调用 `vm.compute()`,确保错误/默认路径均触发 |
| 其他偏好字段(如 xMin/xMax 默认值)未在 loadPrefs 前读取 | 中 | 中 | 中 | 保持现有逻辑,`xMin/xMax` 默认值由 `@State` 初始化提供,仅 `isDegree` 来自偏好 |
| 用户偏好损坏导致 `isDegree` 始终为 true | 中 | 低 | 中 | 不在本修复范围,记录为后续 P2 改进 |

## 4. DFX 分析

### 4.1 性能
- 无影响。删除 `setTimeout(0)` 反而减少一次宏任务调度开销。

### 4.2 安全
- 不涉及。

### 4.3 兼容性
- 行为修复后,用户偏好 `radianMode=false` (默认) 时,GraphPage 使用弧度制,与 `Math.sin` 在 x∈[-6.28, 6.28] 的预期输出一致。
- 用户偏好 `radianMode=true` 时,GraphPage 使用角度制,行为与之前相同(无回归)。

### 4.4 可维护性
- 修复后 `aboutToAppear()` 内无 `setTimeout` 黑魔法,代码意图清晰:"先加载偏好 → 再首次计算"。

### 4.5 可测试性
- 修复后,`vm.compute()` 调用顺序由同步代码控制,可在 Node 测试中精确模拟 aboutToAppear 时序并断言。

## 5. 验收标准 (TDD)

| ID | 验证项 | 期望 |
|----|--------|------|
| AC-1 | hilog 显示 `deg=false` | 是 |
| AC-2 | x=π/2 ≈ 1.57 时 sin(π/2) | ≈ 1.0 |
| AC-3 | x=π ≈ 3.14 时 sin(π) | ≈ 0.0 |
| AC-4 | x=3π/2 ≈ 4.71 时 sin(3π/2) | ≈ -1.0 |
| AC-5 | y_min < -0.9 且 y_max > 0.9 | 是 |
| AC-6 | 截图:曲线有 3 个波峰 + 3 个波谷 | 是 |
| AC-7 | Calculator.test.mjs | 13/13 PASS |
| AC-8 | GraphViewModel.test.mjs | 23/23 PASS |
| AC-9 | 新增 RED 测试: 模拟 aboutToAppear 时序,断言 `vm.compute()` 在 `loadPrefs()` 完成后才触发 | PASS |

## 6. 不涉及

- 架构变更 (无)
- 数据模型变更 (无)
- 新增模块 (无)
- 跨平台适配 (无)
- 其他页面 (仅 GraphPage)
# Design: 百分号按钮 — Issue #9

> **Date**: 2026-06-11
> **Style**: 增量设计（基于现有 `Expression.getPercentString`）
> **Methodology**: TDD (RED → GREEN → REFACTOR)

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│  CalculatorPage (UI)                                          │
│  ┌──────────┐   onOp('%')  ┌──────────┐                       │
│  │  % 按钮   │ ──────────→ │ expression│                      │
│  └──────────┘             └─────┬────┘                       │
│                                  │                            │
│                                  ▼ onEquals()                 │
│                          Expression.getCleanExpression       │
│                                  │                            │
│                                  ▼                            │
│                            CalcEngine.evaluate                │
│                                  │                            │
│                                  ▼                            │
│                              result 字符串                    │
└─────────────────────────────────────────────────────────────┘
```

## 2. 组件设计

### 2.1 测试组件（新增）

**文件**: `entry/src/test/ets/calculator/Expression.test.ets`

```typescript
import { describe, it, expect } from '@ohos/hypium'
import { Expression } from '../../../main/ets/calculator/Expression'
import { ErrorFlags } from '../../../main/ets/model/ErrorFlags'

export default function expressionPercentTest() {
  describe('Expression_getPercentString_macOS', () => {

    it('should_compute_50_plus_10_percent_as_55', 0, () => {
      const e = new Expression()
      const got = e.getCleanExpression('50+10%', '.', ',')
      // 期望: 50+50*10/100
      expect(got).assertEqual('50+50*(10/100)')
    })
    // ... 更多用例
  })
}
```

**关键决策**:
- **不**调用 `engine.evaluate`（黑盒独立测试 `getCleanExpression` 字符串输出）
- 这样测试不依赖计算引擎，定位 bug 更容易
- 数值测试单独写一个 `expressionPercentEvaluate` 集成测试

### 2.2 UI 组件（不改）

`CalculatorPage.ets:278` `%` 按钮已存在，本次无 UI 改动。

### 2.3 表达式组件（可能小改）

`Expression.ets:169-255` `getPercentString`：
- 仅当 RED 测试发现 bug 时改
- 改完后必须**只让新测试从 RED 变 GREEN**，不能让任何旧测试从 GREEN 变 RED
- 不重写整个方法，只做最小修复

## 3. 测试用例矩阵

| # | 用例 | input | 期望 cleanExpression | 类型 |
|---|------|-------|----------------------|------|
| 1 | 纯百分号 | `50%` | `50/100` | RED 新 |
| 2 | 加+百分号（核心） | `50+10%` | `50+50*(10/100)` | RED 新 |
| 3 | 减+百分号 | `200-15%` | `200-200*(15/100)` | RED 新 |
| 4 | 乘+百分号 | `8×5%` | `8*(5/100)` | RED 新 |
| 5 | 除+百分号 | `100÷10%` | `100/(10/100)` | RED 新 |
| 6 | 括号内百分号 | `(2+3)×10%` | `(2+3)*(10/100)` | RED 新 |
| 7 | 连续百分号 | `100+10%+5%` | `100+100*(10/100)+100*(5/100)` | RED 新 |
| 8 | 负数基 | `-50+10%` | `-50+(-50)*(10/100)` | RED 新 |
| 9 | 零基 | `0+10%` | `0+0*(10/100)` | RED 新 |
| 10 | 嵌套括号百分号 | `100+(200×50%)` | `100+200*(50/100)` | RED 新 |
| 11 | 阶乘+百分号 | `5!+10%` | `factorial(5)+factorial(5)*(10/100)` | RED 新 |
| 12 | 空百分号（语法错） | `%` | ErrorFlags.syntax_error | RED 新 |

## 4. TDD 工作流

### 4.1 RED 阶段
1. 写 `Expression.test.ets`，所有 12 个用例
2. 配 `entry/build-profile.json5` 启用 test sourceSet
3. 跑 `hvigorw test` 或 `ohpm test` 或 `node` 等价物
4. **如实记录**：哪些 PASS、哪些 FAIL
5. 不修改实现代码

### 4.2 GREEN 阶段
1. 逐个修 RED 中 FAIL 的用例
2. 优先修逻辑错误（不改 API）
3. 每次改后重跑全部测试，确认无回退

### 4.3 REFACTOR 阶段
1. 提取公共模式（如果有）
2. 改命名
3. 跑全部测试确认绿
4. 跑 `hvigorw build` 确认编译

## 5. 关键不变量

- I-1：`Expression.getCleanExpression` 签名不变
- I-2：`ErrorFlags` 用法不变
- I-3：测试只增不改（覆盖旧行为也只增不删）
- I-4：UI 布局零改动
- I-5：每次提交前 `hvigorw test` 必须通过

## 6. 不做什么

- 不引入新三方库
- 不改 `CalcEngine`
- 不改 UI 颜色 / 主题
- 不改 `PreferencesStore`
- 不加科学模式的额外百分号行为

## 7. 文件改动清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `entry/src/test/ets/calculator/Expression.test.ets` | **新增** | 12 个百分号测试 |
| `entry/src/main/ets/calculator/Expression.ets` | **可能微改** | 仅修 RED 暴露的 bug |
| `entry/build-profile.json5` | **可能改** | 启用 test sourceSet |
| 其他 | **不改** | - |

## 8. 度量

- 测试用例数：12（百分号专项）
- 通过率：100%
- 编译错误：0
- 新增代码行：~150（测试）+ ~0-30（实现）
- 删除代码行：0

## 9. 决策记录

| 决策 | 选择 | 替代方案 | 理由 |
|------|------|----------|------|
| 测试粒度 | 黑盒测 `getCleanExpression` 输出字符串 | 集成到 UI 跑 | 黑盒定位 bug 快，无 UI 依赖 |
| 字符串断言 vs 数值断言 | 字符串断言优先 | 数值断言 | 字符串能精确定位预处理 bug |
| 是否 mock | 不需要 | - | `getCleanExpression` 是纯函数 |
| 测试目录 | `entry/src/test/ets/...` 镜像 main | `entry/src/test/` 平铺 | 镜像便于查找 |

## 10. 时间盒

- RED：≤ 30 min（写 12 个用例 + 跑通框架）
- GREEN：≤ 30 min（修可能 1-2 个 bug）
- REFACTOR：≤ 10 min
- 验证：≤ 10 min（hvigorw 编译）

总计 ≤ 80 min。

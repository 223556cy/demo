# delta-spec — Issue #16 长按弹出选择菜单

> aid-workflow 20260616-requirement-add-long-press-menu
> 基于 proposal.md 增量规格

## 1 需求概述

### 1.1 背景
OpenCalc HarmonyOS 端口当前科学模式提供 sin/cos/tan/ln/log/arcsi/arcco/arcta 等独立按钮。用户使用反三角函数时需要切换行才能找到对应按钮,体验碎片化。

### 1.2 目标
为科学函数按钮增加长按手势,长按时弹出**相关反函数候选菜单**,点选后插入对应函数到表达式。短按维持原行为不变。

### 1.3 范围
**包含**:
- 长按 `sin` 弹出 [arcsin, arccos, arctan] 候选菜单
- 长按 `cos` 弹出 [arcsin, arccos, arctan] 候选菜单
- 长按 `tan` 弹出 [arcsin, arccos, arctan] 候选菜单
- 长按 `ln` 弹出 [log₂x, log₁₀x(已是 log 按钮)] — 注: log 已是独立按钮,首版可只放 logₙx 占位,后续 issue 扩展
- 长按 `arcsi/arcco/arcta` **不**弹菜单(已是反函数,无下层)
- 长按 `π/e/数字/运算符` **不**弹菜单

**不包含**(首版外):
- 振动反馈 (已有 `vibrateOn` 偏好,可后续 issue 接入)
- 长按阈值可配置
- 自定义候选顺序(用户拖拽)
- 多级菜单(嵌套)

## 2 功能需求 (FR)

| ID | 标题 | 描述 | 优先级 |
|----|------|------|--------|
| FR-1 | 长按触发菜单 | 用户长按 sin/cos/tan/ln 按钮 ≥500ms 后,在屏幕中央弹出候选菜单 | P0 |
| FR-2 | 候选菜单显示 | 菜单按列表垂直排列,每项格式为按钮文本(如 `arcsin`),字号 16 | P0 |
| FR-3 | 点选候选 | 点击菜单项后,关闭菜单,执行 `onFunc(item)`,将 `<item>(` 插入表达式末尾 | P0 |
| FR-4 | 点外面关闭 | 点击菜单**外部**区域(半透明遮罩)关闭菜单,不修改表达式 | P0 |
| FR-5 | 短按不变 | 短按 sin/cos/tan/ln 维持原行为(`onFunc(label)`),不弹菜单 | P0 |
| FR-6 | 静态注册表 | 长按映射通过 `LONG_PRESS_REGISTRY: Map<string, string[]>` 静态定义,首版包含 sin/cos/tan → [arcsin, arccos, arctan],ln → [log₂x] | P0 |
| FR-7 | 可扩展 | 添加新长按映射只需修改 `LONG_PRESS_REGISTRY` 一处,无需改 UI 代码 | P0 |

## 3 非功能需求 (NFR)

### 3.1 性能
- 长按检测到菜单弹出延迟 < 100ms
- 菜单关闭 < 50ms

### 3.2 可用性
- 菜单字号 ≥ 16pt,触摸目标 ≥ 44pt 高(HarmonyOS 规范)
- 半透明遮罩 `backgroundColor: '#000000'` + `opacity: 0.4`

### 3.3 可测试性
- 核心逻辑(`LongPressMenu.hasCandidates(label)`, `getCandidates(label)`)写成**纯函数**,可通过 `LongPressMenu.port.mjs` 在 Node.js 单测,无需模拟器

### 3.4 兼容性
- 不修改短按行为,所有现有测试保持 GREEN
- 不修改 `Expression.ets` / `Calculator.ets` / `ErrorFlags.ets`
- 仅修改 `CalculatorPage.ets` + 新增 `LongPressMenu.ets`

## 4 可靠性分析 (FMEA)

| 故障模式 | 原因 | 影响 | RPN | 改进措施 | 残留风险 |
|---------|------|------|-----|---------|---------|
| 长按被误识别为短按(快速双击)| 用户操作习惯 | 菜单未弹出 | 3 | 使用系统 `LongPressGesture` 默认 500ms 阈值,不修改 | 双击场景不弹菜单(可接受) |
| 菜单弹出后卡死 | 状态机错误 | UI 无法操作 | 5 | 菜单状态独立 `@State showLongPressMenu: boolean`,onCandidateTap/点外面都重置为 false | 极低 |
| 候选点击后表达式错误 | 插入逻辑错误 | 计算结果错误 | 4 | 复用现有 `onFunc(f)` 已验证逻辑,新增 `onLongPressCandidate(item)` 调用 `onFunc(item)` | 极低 |
| 长按 ln 弹菜单但 logₙx 占位无功能 | 占位内容 | 用户困惑 | 2 | **首版 ln 长按不弹菜单**,避免半成品体验(FR-6 改为 sin/cos/tan 三个映射)| 已规避 |
| 菜单遮罩点击和按钮点击冲突 | 事件冒泡 | 点击外部可能误触发底部按钮 | 6 | 遮罩用 `Stack` 顶层,菜单层在遮罩之上,事件 stopPropagation 通过层级自然隔离 | 极低 |

**FMEA 消减清单** (必须作为需求约束):
- C1: 长按阈值使用系统默认 500ms,不要在代码里魔改
- C2: 菜单状态独立 `@State`,任何关闭路径必须置 false
- C3: 候选点击必须复用 `onFunc()`,禁止另写插入逻辑
- C4: 首版仅 sin/cos/tan 三个映射,ln 留待后续 issue
- C5: 菜单遮罩 + 菜单容器采用 `Stack` 叠层,菜单在上,点击遮罩区才关闭

## 5 接口需求

### 5.1 用户交互接口

| 入口 | 手势 | 行为 |
|------|------|------|
| `BtnFunc('sin')` 短按 | onClick | 维持原 `onFunc('sin')` → 表达式追加 `sin(` |
| `BtnFunc('sin')` 长按 | LongPressGesture.onAction | 弹出菜单 [arcsin, arccos, arctan] |
| `BtnFunc('cos')` 长按 | LongPressGesture.onAction | 弹出菜单 [arcsin, arccos, arctan] |
| `BtnFunc('tan')` 长按 | LongPressGesture.onAction | 弹出菜单 [arcsin, arccos, arctan] |
| 菜单项点击 | onClick | 执行 `onFunc(item)`, 关闭菜单 |
| 菜单外部点击 | onClick | 关闭菜单,不修改表达式 |

### 5.2 内部接口 (ArkTS)

```typescript
// 新文件 opencalc/entry/src/main/ets/pages/LongPressMenu.ets
export class LongPressMenu {
  static REGISTRY: Map<string, string[]> = new Map([
    ['sin', ['arcsin', 'arccos', 'arctan']],
    ['cos', ['arcsin', 'arccos', 'arctan']],
    ['tan', ['arcsin', 'arccos', 'arctan']],
  ])

  static hasCandidates(label: string): boolean
  static getCandidates(label: string): string[]
}
```

### 5.3 端口文件 (Node.js 测试用)

```javascript
// specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.port.mjs
export const LONG_PRESS_REGISTRY = new Map([
  ['sin', ['arcsin', 'arccos', 'arctan']],
  ['cos', ['arcsin', 'arccos', 'arctan']],
 ['tan', ['arcsin', 'arccos', 'arctan']],
])

export function hasCandidates(label) { ... }
export function getCandidates(label) { ... }
```

## 6 数据需求

无新增持久化数据。无新增状态字段,仅 `@State showLongPressMenu: boolean` 和 `@State longPressSource: string` 在 `CalculatorPage` 内部使用。

## 7 验收标准 (AC)

| AC-ID | 描述 | 验证方法 |
|-------|------|---------|
| AC-1 | 长按 sin ≥500ms 弹出菜单包含 3 项: arcsin, arccos, arctan | UI 手动 + 单元测试 `getCandidates('sin')` 返回 3 项 |
| AC-2 | 点击 arcsin 候选后,表达式末尾变为 `arcsin(` | UI 手动 + 单元测试 onLongPressCandidate 调用 onFunc |
| AC-3 | 短按 sin 仍然插入 `sin(`,**不**弹菜单 | UI 手动 + 单元测试 |
| AC-4 | 点击菜单外区域关闭菜单,表达式不变 | UI 手动 |
| AC-5 | 长按数字/运算符/常量按钮**不**弹菜单 | UI 手动 + 单元测试 `hasCandidates('1')` 返回 false |
| AC-6 | 单元测试 `LongPressMenu.port.mjs` 覆盖 ≥ 6 个用例,全 GREEN | `node --test` |
| AC-7 | 现有 `Expression.test.ets` 等所有单测保持 GREEN | `hvigorw --no-daemon test` |

## 8 不涉及
- 国际化 (i18n): 不涉及,中文按钮文本不变
- 网络通信: 不涉及
- 数据持久化: 不涉及
- 权限: 不涉及
- 性能优化 (DFX): 不涉及(NFR §3.1 是验收基线,非优化目标)
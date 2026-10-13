# Issue #16 — 代码仓理解

> aid-workflow 20260616-requirement-add-long-press-menu
> 基于 rq-codebase 系统分析

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: HarmonyOS
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test (framework: hypium + hamock)
- **UI 自动化测试能力: ✅ 可用 (hdc + 模拟器 127.0.0.1:5555)**
- hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- 端口文件可独立 Node.js 跑测 (`node --test`)

## 基本信息
- **需求类别**: 新增功能 (requirement-add)
- **需求名称**: 长按弹出选择菜单
- **分析时间**: 2026-06-16
- **分析范围**: `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (543行)

## 架构分析

### 模块结构
```
opencalc/entry/src/main/ets/
├── calculator/           # 纯计算引擎（不涉及 UI）
│   ├── Calculator.ets    # CalcEngine — 表达式求值
│   ├── Expression.ets    # 表达式预处理
│   └── NumberFormatter.ets
├── model/                # 数据模型
│   ├── ErrorFlags.ets
│   └── Models.ets        # 包含 HistoryItem 等
├── pages/                # View 层
│   ├── CalculatorPage.ets  # ← 唯一修改点
│   └── Index.ets
├── preferences/          # 持久化
└── entryability/
```

### 依赖关系
- `CalculatorPage` 依赖 `Expression`、`CalcEngine`、`ErrorFlags`、`Models`、`PreferencesStore`、`@kit.ArkUI`、`@kit.BasicServicesKit`
- 新增 `LongPressMenu.ets` 将被 `CalculatorPage` 引用,**不**引入新的外部依赖

### 扩展机制
- HarmonyOS `LongPressGesture` 系统组件,默认 500ms 阈值
- `Stack` 容器支持层叠布局,适合做遮罩+菜单
- 已用 `.gesture(...)` 修饰: DisplayPanel 上挂长按复制(参考点)

## 接口/契约识别

### 现有按钮接口 (待扩展)

| Builder | 输入 | onClick 行为 | 当前用途 |
|---------|------|--------------|---------|
| `BtnDig(l)` | 数字字符 | `onDigit(l)` | 数字 |
| `BtnOp(l)` | 运算符 | `onOp(l)` | +-×÷ |
| `BtnFunc(l)` | 函数名 | `onFunc(l)` | sin/cos/tan/ln/log/arcsi/arcco/arcta |
| `BtnConst(l)` | 常量名 | `onConst(l)` | π/e |
| `BtnAct(l)` | 动作名 | `onAC()` / `onBS()` | AC/⌫ |
| `BtnEq()` | - | `onEquals()` | = |

### 待新增的内部接口

```typescript
// 新文件 opencalc/entry/src/main/ets/pages/LongPressMenu.ets
export class LongPressMenu {
  static REGISTRY: Map<string, string[]>     // 标签 → 候选列表
  static hasCandidates(label: string): boolean
  static getCandidates(label: string): string[]
}
```

## 公共组件或函数识别

### 可复用
- **`onFunc(f: string)`** (CalculatorPage.ets:193): 已实现 `expression += f + '('`,候选点击直接复用,**禁止另写插入逻辑** (FMEA C3)
- **`LongPressGesture()`**: DisplayPanel.ets:380 已有 `.gesture(LongPressGesture().onAction(...))` 实例,Button 上挂法可参考 ArkTS 文档
- **`promptAction.showToast`** (`@kit.ArkUI`): 可选用于关闭菜单的 toast 反馈

### 新建
- **`LongPressMenu.ets`**: 纯逻辑类,无 UI 依赖,完全可测

## 影响范围分析

### 需要修改的模块/文件清单
1. **修改**: `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
   - 引入 `LongPressMenu`
   - 新增 `@State showLongPressMenu: boolean` 和 `@State longPressSource: string`
   - `BtnFunc` Builder 改为接收 `label: string`,增加 `.gesture(LongPressGesture().onAction((): void => { this.onLongPress(label) }))`
   - 新增 `LongPressMenuPanel()` @Builder (遮罩+候选列表)
   - 新增 `onLongPress(label: string)` 和 `onLongPressCandidate(item: string)` 方法
   - `build()` 中 `Stack` 顶层增加 `if (this.showLongPressMenu) this.LongPressMenuPanel()`

2. **新增**: `opencalc/entry/src/main/ets/pages/LongPressMenu.ets` (纯逻辑)
3. **新增**: `specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.port.mjs` (Node.js TDD 端口)
4. **新增**: `specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs` (Node.js 单测)

### 调用链分析
```
用户长按 sin
  ↓
BtnFunc 的 .gesture(LongPressGesture().onAction)
  ↓
this.onLongPress('sin')
  ↓
LongPressMenu.hasCandidates('sin') → true
this.showLongPressMenu = true; this.longPressSource = 'sin'
  ↓
LongPressMenuPanel 渲染,显示 LongPressMenu.getCandidates('sin') = ['arcsin','arccos','arctan']
  ↓
用户点击 'arcsin'
  ↓
this.onLongPressCandidate('arcsin')
  ↓
this.onFunc('arcsin')  // 复用,expression += 'arcsin('
this.showLongPressMenu = false
```

### 影响评估
- **不影响**: Expression.ets、Calculator.ets、ErrorFlags.ets、Models.ets、PreferencesStore.ets
- **不影响**: 现有 BtnDig/BtnOp/BtnConst/BtnAct/BtnEq Builder
- **不影响**: DisplayPanel 长按复制(已有 longpress)
- **回归风险**: 极低(仅扩展,不修改既有行为)

## 现有代码分析

### CalculatorPage.ets 关键代码 (L416-425)
```typescript
@Builder BtnFunc(l: string) {
  Text(l).fontSize(...).fontColor(this.getT1()).width('18%').height(...)
    .textAlign(TextAlign.Center).backgroundColor(this.getFuncBg()).borderRadius(50)
    .margin(...).onClick((): void => { this.onFunc(l) })
}
```
**改造方案**: 在 `.onClick(...)` 后链上 `.gesture(LongPressGesture().onAction((): void => { this.onLongPress(l) }))`。`onClick` 和长按在 HarmonyOS 中互斥(系统保证:短按触发 onClick,长按触发 gesture.onAction),无需手动去抖。

### DisplayPanel.ets:380 长按参考
```typescript
.gesture(LongPressGesture().onAction((): void => { this.onCopy() }))
```
说明 `Text` 组件已成功挂长按,`Text` (按钮文字) 同样适用。

## 风险识别

| 风险 | 等级 | 缓解 |
|------|------|------|
| 长按和点击冲突 | 低 | HarmonyOS 系统保证互斥 |
| 菜单遮罩事件穿透 | 低 | `Stack` 层级隔离,菜单在上 |
| 单元测试环境缺 hvigorw | 中 | Node.js 端口文件 (`.port.mjs`) 离线跑 `node --test` |
| 真实 UI 测试能力未跑通 | 中 | UI 自动化能力 ✅ 可用,但首版依赖端口单测,UI 自动化作为可选任务 |

### 测试能力评估
- 单元测试能力: ✅ (Node.js 端口方式,与 issue #11/#9 一致)
- UI 自动化测试能力: ✅ (hdc + 模拟器 127.0.0.1:5555)
- 端到端集成测试能力: ✅ (同上)
- **不能跑的实际原因**: 无（环境就绪,但首版以端口单测验证逻辑,UI 自动化作为可选 acceptance 测试）

## 测试验证策略

### 测试场景清单
- `LongPressMenu.hasCandidates('sin')` → true
- `LongPressMenu.hasCandidates('1')` → false (数字无候选)
- `LongPressMenu.hasCandidates('arcsi')` → false (反函数无下层)
- `LongPressMenu.hasCandidates('+')` → false (运算符无候选)
- `LongPressMenu.getCandidates('sin')` → ['arcsin', 'arccos', 'arctan']
- `LongPressMenu.getCandidates('cos')` → ['arcsin', 'arccos', 'arctan']
- `LongPressMenu.getCandidates('tan')` → ['arcsin', 'arccos', 'arctan']
- `LongPressMenu.getCandidates('ln')` → [] (首版不映射 ln)
- `LongPressMenu.getCandidates('1')` → []
- 边界: 未知 label → []

### 验收方法
1. `node --test specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs` 全 GREEN
2. (可选) UI 自动化: 启动模拟器 + 长按 sin → 截图确认菜单弹出 (skill: harmonyos-ui-test)
3. 手动验证: 短按 sin 仍然插入 `sin(`,长按弹出菜单

### 回归范围
- `Expression.test.ets` 等所有现有 hvigorw 测试保持 GREEN(本次不改表达式引擎)

## 监控运维支持

不涉及 (UI 层增强,无后端/网络/持久化)。

## 关键发现

### 可复用组件或函数
- `onFunc()` (CalculatorPage:193) — 候选点击后**必须**复用此入口
- `LongPressGesture()` 系统组件 — 直接用
- issue #11 的"端口文件 `.port.mjs`" 模式 — 复用,本 issue 同样建立 `LongPressMenu.port.mjs`

### 风险提示
- ⚠️ 不要修改 `Expression.ets`/`Calculator.ets`/`ErrorFlags.ets`,本期 UI 增强不涉及计算引擎
- ⚠️ 不要重写 onFunc 插入逻辑,必须复用

### 建议事项
- 采用"静态注册表 + 纯函数 `hasCandidates`/`getCandidates`"模式,后续 issue 扩展只需改 `LongPressMenu.REGISTRY` 一行
- 长按 `ln` 首版不映射,避免半成品体验(在 delta-spec §4 FMEA C4 已固化)
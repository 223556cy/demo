# Issue #28 (M1-M6 + MR) — 代码仓理解

## 基本信息

- **需求类别**: 新增功能 (requirement-add)
- **需求名称**: memory-slots
- **分析时间**: 2026-06-17
- **分析范围**: `D:\huawei\Demo\calculatorHuawei\opencalc\entry\src\main\ets\`（calculator / pages / model / preferences / history / qrcode / common）

## 环境能力（来自 .claude/capabilities.json）

- 项目类型: HarmonyOS（ArkTS 6.0.2，V1 state 管理）
- 平台: Windows
- bundleName: com.darkempire78.opencalculator
- 编译命令: hvigorw --no-daemon assembleHap
- 单元测试命令: hvigorw --no-daemon test
- **UI 测试能力: ✅ 可用** (harmonyos-ui-test skill)
- 模拟器列表: 127.0.0.1:5555 (running)
- hdc 路径: D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe
- 单元测试框架: @ohos/hypium 1.0.15 + @ohos/hamock 1.0.0
- 单元测试根: `opencalc/entry/src/test`

## 架构分析

### 关键模块 / 文件

| 模块 | 路径 | 职责 |
| --- | --- | --- |
| **CalculatorPage** | `pages/CalculatorPage.ets` (796 行) | 唯一 `@Entry` 页面，承载所有 UI 与状态 |
| CalcEngine | `calculator/Calculator.ets` | 表达式求值引擎 |
| Expression | `calculator/Expression.ets` | tokenizer / cleaner |
| NumberFormatter | `calculator/NumberFormatter.ets` | 数字格式化 |
| Models | `model/Models.ets` | 数据模型（HistoryItem, CalculatorPreferences 等） |
| ErrorFlags | `model/ErrorFlags.ets` | 错误标志静态方法 |
| PreferencesStore | `preferences/PreferencesStore.ets` | @kit.ArkData preferences 封装 |
| LongPressMenu | `pages/LongPressMenu.ets` | 长按弹出菜单（sin→arcsin 之类）的 registry 与样式常量 |
| QrCodeBuilder | `qrcode/QrCodeBuilder.ets` | 二维码分享 |
| HistoryGroup | `history/HistoryGroup.ets` | 历史分组 |
| NaturalLanguageParser / UnitConverter | `common/` | NL 解析与单位换算 |

### 状态管理模式（重要）

- 项目 **没有** viewmodel 层。`@Observed` / `@ObservedV2` / `@ObjectLink` / `@Trace` 在整个 `entry/src/main/ets/` 0 匹配。
- 所有状态都用 `@State` 直接挂在 `CalculatorPage` struct 上（line 23-47 共 16+ 个 @State）。
- 因此 Issue #28 的状态应该直接挂在 `CalculatorPage` 上作为 `@State`，不需要新建 viewmodel 类；store/类可以放在 `calculator/MemorySlots.ets`（纯逻辑类），但实例化时只暴露给 `CalculatorPage` 当 `@State` 用。

### 模块依赖图（简化）

```
CalculatorPage (@Entry @Component @State 持有者)
   ├── calculator/Calculator.ets   (engine)
   ├── calculator/Expression.ets
   ├── model/Models.ets            (HistoryItem, prefs 等)
   ├── model/ErrorFlags.ets
   ├── preferences/PreferencesStore.ets
   ├── pages/LongPressMenu.ets     (LongPressMenuPanel 渲染源)
   ├── history/HistoryGroup.ets
   └── calculator/MemorySlots.ets  ← 新增
```

## 接口/契约识别

### 既有手势用法（建立模式参考）

| 位置 | 用法 | 文件:行 |
| --- | --- | --- |
| DisplayPanel 长按复制 | `.gesture(LongPressGesture().onAction((): void => { this.onCopy() }))` | `pages/CalculatorPage.ets:565` |
| BtnFunc（sin/cos/tan/ln/log）长按弹菜单 | `.gesture(LongPressGesture().onAction((): void => { this.onLongPress(l) }))` | `pages/CalculatorPage.ets:656` |
| LongPressMenu.REGISTRY | `Map<string, string[]>`，key = 按钮 label，value = 候选 | `pages/LongPressMenu.ets:10-14` |
| LongPressMenuPanel 渲染 | `@Builder LongPressMenuPanel()` + `if (this.showLongPressMenu) this.LongPressMenuPanel()` | `pages/CalculatorPage.ets:463-486, 516` |

> **结论**: 长按弹窗是项目已建立的 pattern，Issue #28 的"MR 弹菜单"应**复用** `LongPressMenu` 系列的 Column-mask + overlay 风格，但 `LongPressMenu.REGISTRY` 是静态 Map（label → string[]），不适合存动态数值。建议新增一个 `MemoryPickerPanel`（同样放在 `pages/`，复用 mask 样式常量 `MENU_*`），独立维护。

### 既有 Toast 用法

- `import { promptAction } from '@kit.ArkUI'` — `pages/CalculatorPage.ets:3`
- `promptAction.showToast({ message: '已复制' })` — `CalculatorPage.ets:271`
- `promptAction.showToast({ message: '非数学表达式', duration: 1500 })` — `CalculatorPage.ets:355`
- 模式：`promptAction.showToast({ message: string, duration?: number })`

> **结论**: "已存入 Mx" toast 直接复用此模式即可。

### ActionSheet / BottomSheet

- 项目 **无** `bindSheet` / `ActionSheet` / `BottomSheet` 用法（grep 0 匹配）。
- 弹窗/面板都是手写 `@Builder` + `Stack` mask 的模式（参考 SettingsPanel、HistoryPanel、AboutPanel、SharePanel、LongPressMenuPanel）。

### Memory 相关代码

- grep `memory|Memory|M1|MR|MemorySlot|memorySlot` 在 `entry/src/main/ets/` **零匹配**。
- 含义: 完全新增，无既有约束。

## 公共组件或函数识别

| 可复用 | 位置 | 复用方式 |
| --- | --- | --- |
| LongPressMenu UI 常量 | `pages/LongPressMenu.ets:18-26` | `MENU_WIDTH_RATIO`, `MENU_MAX_WIDTH`, `MENU_ITEM_HEIGHT`, `MENU_FONT_SIZE`, `MENU_BORDER_RADIUS`, `MENU_MASK_COLOR`, `MENU_MASK_OPACITY`, `MENU_PADDING` 直接 import 复用 |
| LongPressMenuPanel 渲染模板 | `pages/CalculatorPage.ets:463-486` | 复制改造成 `MemoryPickerPanel`（数据驱动而非字符串驱动） |
| `promptAction.showToast` | `@kit.ArkUI` | 已 import；toast 反馈 |
| `@Builder` 数字键 | `pages/CalculatorPage.ets:646` | **需扩展**：在原 Text 后追加 `.gesture(...)` 用于 1-6 数字键 |
| hypium 测试基线 | `entry/src/test/ets/history/HistoryGroup.test.ets` | 复制结构写 MemorySlots.test.ets |

> `LongPressMenu.REGISTRY` 不能直接复用：它是 string→string[] 静态映射，不适合存数值。需要新增 `MemoryPicker` 类持有 6 个 slot。

## 影响范围分析

### 需要修改的文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `pages/CalculatorPage.ets` | modify | 在 ButtonGrid 前插入一行（MR + 记忆指示）；在数字键 builder (line 646) 增加 LongPressGesture 绑定 1-6；新增 @State memorySlots + showMemoryPicker；新增 @Builder MemoryPickerPanel + 触发/关闭函数 |
| `calculator/MemorySlots.ets` | **new** | 新增 MemorySlot 数据类（6 槽）+ 操作函数（save / recall / clear / anyHasValue / lastUsedLabel） |
| `entry/src/test/List.test.ets` | modify | 注册新 test suite |
| `entry/src/test/ets/calculator/MemorySlots.test.ets` | **new** | hypium 单元测试 |

### 调用链（MR 调出路径）

```
用户点击 MR 按钮
   → CalculatorPage.onMRClick()
       → 若 !anySlotHasValue → 早退（按钮已 disabled）
       → this.showMemoryPicker = true
           → @Builder MemoryPickerPanel() 渲染
               → 用户点击 M(N)
                   → CalculatorPage.onPickSlot(N)
                       → MemorySlots.recall(N) → 写入 this.expression (作为输入流值)
                       → this.showMemoryPicker = false
```

### 调用链（长按存槽路径）

```
用户长按数字键 N (1≤N≤6)
   → LongPressGesture.onAction()
       → CalculatorPage.onLongPressDigit(N)
           → MemorySlots.save(N, parseDisplay(this.result))
           → this.memorySlots = MemorySlots.snapshot()
           → promptAction.showToast({ message: '已存入 M' + N })
           → this.memoryActiveLabel 重算
```

### 兼容性影响

- 数字键单击行为不变（`onDigit(l)` 仍生效）；LongPressGesture 与 onClick 在 HarmonyOS ArkTS 是可以共存的（onClick 触发 tap，longPress 触发 longPress；项目 line 565/656 已证实）。
- 新增的 MR 按钮占一格 ButtonGrid → 现有 5×4/5 网格需扩展为多一行（参考 line 630-643，ButtonGrid 是单 Column 内的若干 Row，可在底部加一行，或在科学函数行旁加）。
- 不影响 calc engine / expression / preferences。

## 现有代码分析

### 关键代码片段

`pages/CalculatorPage.ets:18-53`（struct 头）：
```ts
@Entry
@Component
struct CalculatorPage {
  @State @Watch('onExpressionChange') expression: string = ''
  @State preview: string = ''
  @State result: string = ''
  @State errorMsg: string = ''
  // ... 16 个 @State 全部展开
  private nextId: number = 0
  private engine: CalcEngine = new CalcEngine()
  private expr: Expression = new Expression()
  private prefs: PreferencesStore | null = null
}
```

`pages/CalculatorPage.ets:646`（数字键 builder）：
```ts
Text(l).fontSize(...).fontColor(...).width('17%').height(...).textAlign(TextAlign.Center)
  .backgroundColor(this.getBtnBg()).borderRadius(50).margin(...)
  .onClick((): void => { this.onDigit(l) })
```
需要在 `.onClick(...)` 后追加（仅当 l ∈ {'1','2','3','4','5','6'}）：
```ts
.gesture(LongPressGesture().onAction((): void => { this.onLongPressDigit(l) }))
```

`pages/CalculatorPage.ets:656`（BtnFunc 长按弹菜单参考实现）：
```ts
Text(l).fontSize(28).fontColor(this.getOpFg()).width('20%').height(btnH).textAlign(TextAlign.Center)
  .backgroundColor(this.getBtnBg()).borderRadius(50).margin(2)
  .onClick((): void => { this.onOp(l) })
  .gesture(LongPressGesture().onAction((): void => { this.onLongPress(l) }))
```

### 关键变量

- `this.expression` (string): 当前输入流；recall 写入它
- `this.result` (string): 当前结果区显示；长按存的是它（去逗号格式化后 parseFloat）
- `this.preview` (string): 实时预览
- `private engine`: CalcEngine 实例，负责 `=` 计算

### 边界条件

- `this.result` 可能为 `'0'` / `''` / 含逗号千分位 / `'Error'`
- `Number.parseFloat('1,234')` → 1（截断），存槽会丢精度 → 需先 `replace(/,/g, '')`
- 非有限值（NaN / Infinity）应拒绝存入（FMEA-FM-01/FM-05）

## 风险识别

### 技术难点

1. **数字键 builder 改造**: line 646 数字键 builder 是单行 arrow，扩展长按手势需要条件判断 l ∈ 1..6；如果逻辑写在 builder 内会增加复杂度。**缓解**: 在 builder 内做三元判断 `l >= '1' && l <= '6'`，简洁可读。
2. **MR 按钮位置**: 现有 5×5 ButtonGrid 没有空格位；插入会改变布局。**缓解**: 在 AC 旁放 MR（替换一个现有空隙/或新增 1 行）。
3. **长按冲突**: `onClick` + `.gesture(LongPressGesture)` 在 HarmonyOS 中：tap 走 onClick，hold ≥500ms 走 gesture 不会触发 onClick（项目 line 656 已证明）。
4. **MR 菜单 vs LongPressMenu**: 两者 pattern 一致但数据不同；新增 `MemoryPickerPanel` 不影响 `LongPressMenuPanel`。

### 问题区域 / 技术债

- 项目无 viewmodel 概念，单文件 796 行；若继续堆叠会变 900+。**缓解**: MemorySlots 逻辑放到 `calculator/MemorySlots.ets` 保持 CalculatorPage 增量 ≤80 行。

### 风险缓解

| 风险 | 缓解 |
| --- | --- |
| 长按 0/7/8/9 误触发存槽 | builder 内条件 `l >= '1' && l <= '6'` 才挂 gesture |
| 存 NaN/Infinity 破坏状态 | MemorySlots.save 用 Number.isFinite 校验，非有限拒绝 |
| 弹窗状态泄漏 | showMemoryPicker 在 onPageHide / 弹窗外部点击时统一关闭 |
| 菜单与 LongPressMenu 同时打开 | 互斥：打开 MemoryPicker 时关闭 LongPressMenu（设 showLongPressMenu = false） |

## 测试验证策略

### 测试场景

| 场景 | 验证方法 | 文件 |
| --- | --- | --- |
| MemorySlots.save 写入 1..6 | 单元测试 | `MemorySlots.test.ets` |
| MemorySlots.save 覆盖已有 | 单元测试 | 同上 |
| MemorySlots.save 拒绝 NaN/Infinity | 单元测试 | 同上 |
| MemorySlots.recall 空槽返回 null | 单元测试 | 同上 |
| MemorySlots.recall 非空槽返回 value | 单元测试 | 同上 |
| MemorySlots.anyHasValue | 单元测试 | 同上 |
| MemorySlots.lastUsedLabel | 单元测试 | 同上 |
| UI：长按 1 → toast + M1 标签 | UI 自动化 (harmonyos-ui-test) | CI |
| UI：MR 弹出菜单 + 调出到输入流 | UI 自动化 | CI |
| UI：MR 全空态禁用 | UI 自动化 | CI |

### 验证方法

- 单元测试：`hvigorw --no-daemon test`（已在 capabilities.json 配置）
- UI 自动化：harmonyos-ui-test skill（已可用）；用 `uitest uiInput drag X Y X+1 Y+1 200`（memory: [[harmonyos-uitest-longpress]]）稳定触发 LongPressGesture

### 回归范围

- 数字键单击输入（onDigit）：长按 1-6 不应改变单击输入行为；长按 ≥500ms 才走 longPress 分支
- 科学函数按钮长按弹菜单（onLongPress）：不受数字键长按影响
- AC / ⌫ / % / 等按钮：不受影响

## 监控运维支持

- 不涉及（首版不持久化；不写日志；不上报）
- 不涉及配置项

## 关键发现

### 可复用组件或函数

- `LongPressMenu.ets` 的 `MENU_*` 样式常量（MENU_WIDTH_RATIO / MENU_MAX_WIDTH / MENU_ITEM_HEIGHT / MENU_FONT_SIZE / MENU_BORDER_RADIUS / MENU_MASK_COLOR / MENU_MASK_OPACITY / MENU_PADDING）
- `LongPressMenuPanel` @Builder 作为 MemoryPickerPanel 的渲染参考（`pages/CalculatorPage.ets:463-486`）
- `promptAction.showToast` 已 import
- `@ohos/hypium` 测试模板（参考 `entry/src/test/ets/history/HistoryGroup.test.ets`）
- `harmonyos-ui-test` skill — UI 自动化测试标准工具

### 风险提示

- 项目无 viewmodel，所有 @State 挂在 796 行的 `@Entry` struct 上；继续叠加会突破 900 行，需要将 MemorySlots 逻辑下沉到 `calculator/MemorySlots.ets` 控制文件大小
- 数字键 builder line 646 是单行 arrow，扩展 gesture 需要条件判断；务必保持单行可读性
- 长按手势 vs onClick 互斥性已在 line 565/656 验证，无新风险
- **测试能力评估**: 单元测试 ✅ + UI 自动化 ✅（hdc + 模拟器运行中） + 端到端集成测试 ✅
- 不能跑的实际原因: 无

### 建议事项

1. **新增文件** `entry/src/main/ets/calculator/MemorySlots.ets`：6 槽数据类 + 操作函数（纯逻辑，便于单测）
2. **扩展** `pages/CalculatorPage.ets`：
   - 新增 3 个 `@State`：`memorySlots: MemorySlotsState`、`showMemoryPicker: boolean`、`memoryActiveLabel: string`（用 getter 派生）
   - 数字键 builder (line 646) 增加条件 gesture 绑定
   - ButtonGrid 顶部或底部插入 MR 按钮行
   - 新增 `@Builder MemoryPickerPanel()`
   - 新增方法：`onLongPressDigit(d: string)`、`onMRClick()`、`onPickSlot(idx: number)`、`onMemoryMaskClick()`
3. **新增测试** `entry/src/test/ets/calculator/MemorySlots.test.ets` + 在 `entry/src/test/List.test.ets` 注册
4. UI 自动化用例：长按 1 存值 → MR 调出 → 验证 display 等于存入值

# Issue #12 程序员模式 - 开发任务 (tasks.md)

## 任务概述

- **功能名称**：程序员模式（DEC/BIN/OCT/HEX 切换 + 模式切换动画）
- **变更类型**：requirement-add
- **关联特性**：feat-programmer-mode
- **开发阶段**：IMPLEMENTING
- **预计任务数**：10
- **基于**：delta-design.md + delta-spec.md

## 任务列表

### 阶段 1：基础设施（数据层 + 工具类）

#### Task 1.1: 新建 BaseConverter.ets（纯函数工具类）
**描述**：实现 DEC ↔ BIN/OCT/HEX 转换，处理 NaN/Infinity/小数/负数边界。
**涉及文件**：
- 新建 `opencalc/entry/src/main/ets/calculator/BaseConverter.ets`
**依赖任务**：无
**验收标准**：
- [ ] 导出 `class BaseConverter`，含 `static convert(value, base)` 与 `static withPrefix(value, base)`
- [ ] NaN/Infinity 返回 `"-"`，0 返回 `"0"`
- [ ] BIN/OCT/HEX 用 `Math.trunc` 截断小数，负数加 `-` 前缀
- [ ] HEX 输出 uppercase（A-F 大写）
- [ ] DEC 保留原始值（含小数）
**TDD**：RED → GREEN → REFACTOR

#### Task 1.2: 单元测试 BaseConverter.test.ets
**描述**：覆盖 BaseConverter 全部转换场景 + 边界值。
**涉及文件**：
- 新建 `opencalc/entry/src/test/ets/calculator/BaseConverter.test.ets`
**依赖任务**：Task 1.1
**验收标准**：
- [ ] 用例：255→BIN=`11111111`, 255→OCT=`377`, 255→HEX=`FF`
- [ ] 用例：-1→BIN=`-1`, -255→HEX=`-FF`
- [ ] 用例：3.14→BIN=`11`, 3.99→BIN=`11`（截断）
- [ ] 用例：0→BIN=`0`
- [ ] 用例：NaN→BIN=`-`, Infinity→BIN=`-`
- [ ] 用例：withPrefix 255→HEX=`0xFF`, 255→OCT=`0o377`, 255→BIN=`0b11111111`
**TDD**：RED → GREEN

#### Task 1.3: 扩展 Models.ets 增加 CalculatorMode/NumberBase 枚举
**描述**：在 model/Models.ets 增加枚举与 BaseConversions 接口，扩展 CalculatorPreferences。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/model/Models.ets`
**依赖任务**：无
**验收标准**：
- [ ] 新增 `export enum CalculatorMode { BASIC=0, SCIENTIFIC=1, PROGRAMMER=2 }`
- [ ] 新增 `export enum NumberBase { DEC=0, BIN=1, OCT=2, HEX=3 }`
- [ ] 新增 `export interface BaseConversions { dec, hex, oct, bin }`
- [ ] CalculatorPreferences 增加 `mode: CalculatorMode` 和 `activeBase: NumberBase`
- [ ] DEFAULT_PREFERENCES 同步扩展
**TDD**：N/A（类型定义）

### 阶段 2：数据层扩展

#### Task 2.1: 扩展 PreferencesStore.ets 增加 getMode/setMode/getActiveBase/setActiveBase
**描述**：在 preferences/PreferencesStore.ets 增加 4 个新方法 + getAllPreferences 扩展。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets`
**依赖任务**：Task 1.3
**验收标准**：
- [ ] `getMode(): Promise<CalculatorMode>` 默认 BASIC
- [ ] `setMode(mode): Promise<void>` try-catch 写入
- [ ] `getActiveBase(): Promise<NumberBase>` 默认 DEC
- [ ] `setActiveBase(base): Promise<void>` try-catch 写入
- [ ] 保留旧 `getScientificModeDefault/setScientificModeDefault`（不删除）
**TDD**：N/A（持久化层集成测试由应用层覆盖）

### 阶段 3：视图层重构（CalculatorPage）

#### Task 3.1: 重构 CalculatorPage.ets 状态变量
**描述**：将 `@State scientific: boolean` 重构为 `@State mode: CalculatorMode`，新增 activeBase/baseConversions。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 1.3, Task 2.1
**验收标准**：
- [ ] 移除 `@State scientific: boolean`
- [ ] 新增 `@State mode: CalculatorMode = CalculatorMode.BASIC`
- [ ] 新增 `@State activeBase: NumberBase = NumberBase.DEC`
- [ ] 新增 `@State baseConversions: BaseConversions = { dec:'', hex:'', oct:'', bin:'' }`
- [ ] loadPrefs 优先读 mode 字段，无 mode 时回退 scientificModeDefault
- [ ] savePref 支持 `mode` 与 `activeBase` 键
**TDD**：N/A

#### Task 3.2: 重构 ToggleRow → ModeToggleRow（三选一 SegmentedControl）
**描述**：原 ToggleRow 替换为 ModeToggleRow，三选一按钮。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.1
**验收标准**：
- [ ] 新增 `@Builder ModeToggleRow()`
- [ ] 三个按钮：基础 / 科学 / 程序员
- [ ] 当前 mode 高亮
- [ ] onClick 调用 onModeChange(target)
- [ ] 历史/设置按钮保留在 Row 右侧
**TDD**：N/A

#### Task 3.3: 拆分 ButtonGrid 为 BasicKeypad/ScientificKeypad/ProgrammerKeypad
**描述**：原 ButtonGrid 内部按 mode 条件渲染，拆为三个独立的 @Builder。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.1
**验收标准**：
- [ ] `@Builder BasicKeypad()`：5 列 × 6 行数字键盘
- [ ] `@Builder ScientificKeypad()`：5 列 × 7 行（含 sin/cos/tan/ln/log + 常量）
- [ ] `@Builder ProgrammerKeypad()`：5 列 × 6 行（含 BIN 0/1 + HEX A-F + 数字 2-9 + 运算符）
- [ ] build() 根据 mode 条件渲染对应 keypad
- [ ] 三个 keypad 使用相同按钮样式（复用 BtnFunc/BtnConst 或新增 BtnHexLetter/BtnBin）
**TDD**：N/A

#### Task 3.4: 新增 BaseConverterPanel 与 ActiveBaseToggle
**描述**：PROGRAMMER 模式下显示 4 行多进制 + 主进制切换按钮。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.1
**验收标准**：
- [ ] `@Builder BaseConverterPanel()`：4 行 DEC/HEX/OCT/BIN 显示，含 0x/0o/0b 前缀
- [ ] `@Builder ActiveBaseToggle()`：4 个按钮 DEC/BIN/OCT/HEX，当前 activeBase 高亮
- [ ] build() 中仅在 mode === PROGRAMMER 时显示这两个组件
**TDD**：N/A

#### Task 3.5: 实现 onModeChange/onActiveBaseChange 与 refreshBaseConversions
**描述**：状态变更回调，刷新多进制行 + 持久化。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.1, Task 1.1
**验收标准**：
- [ ] `async onModeChange(newMode)`：更新 mode，调用 setMode，触发 @Watch 持久化
- [ ] `async onActiveBaseChange(newBase)`：更新 activeBase，调用 setActiveBase
- [ ] `private refreshBaseConversions(value)`：调用 BaseConverter.convert 四次，更新 baseConversions
- [ ] onEquals() 触发 refreshBaseConversions(result)
- [ ] @Watch('onExpressionChange') 程序员模式下也触发 refresh
- [ ] onActiveBaseChange 也触发 refresh（主结果标签同步）
**TDD**：N/A（调用层）

#### Task 3.6: 主结果格式化支持 activeBase
**描述**：主结果显示按 activeBase 格式化（带前缀）。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.1, Task 1.1
**验收标准**：
- [ ] 程序员模式下主结果 = BaseConverter.withPrefix(result, activeBase)
- [ ] 基础/科学模式下主结果保持 NumberFormatter.format 不变
- [ ] activeBase=DEC 时主结果 = `255`，HEX 时 `0xFF`，BIN 时 `0b11111111`，OCT 时 `0o377`
**TDD**：N/A

#### Task 3.7: 键盘区域 transition 动画
**描述**：给 keypad 容器添加 .transition() 修饰符，fade + slide 200ms。
**涉及文件**：
- 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.3
**验收标准**：
- [ ] keypad Row/Column 应用 `.transition(TransitionEffect.OPACITY.combine(TransitionEffect.translate(...)).animation({ duration: 200, curve: Curve.EaseInOut }))`
- [ ] 仅键盘区域动画；显示屏与顶部不动画
- [ ] enter: opacity 0→1, translate x: 8→0
**TDD**：N/A（视觉验证）

### 阶段 4：测试与验证

#### Task 4.1: 单元测试运行
**描述**：运行 `hvigorw --no-daemon test` 确保 BaseConverter 测试通过 + 不破坏现有测试。
**涉及文件**：
- 运行命令：`hvigorw --no-daemon test`
**依赖任务**：Task 1.2, Task 3.1-3.7
**验收标准**：
- [ ] BaseConverter.test.ets 全部通过
- [ ] 现有 Expression.test.ets 全部通过（不破坏）
- [ ] 现有 NumberFormatter.test.ets 全部通过（不破坏）
**TDD**：GREEN 验证

#### Task 4.2: UI 自动化测试（hdc + harmonyos-ui-test）
**描述**：使用 hdc + harmonyos-ui-test skill 在模拟器执行 AC 验证。
**涉及文件**：
- 新建 `specs/changes/20260615-requirement-add-简单需求/ui-tests/run_tests.py`
- 新建 `specs/changes/20260615-requirement-add-简单需求/ui-tests/parse_ui.py`
- 输出 `specs/changes/20260615-requirement-add-简单需求/ui-tests/results.json`
- 截图目录 `specs/changes/20260615-requirement-add-简单需求/ui-tests/screenshot/`
**依赖任务**：Task 4.1
**验收标准**：
- [ ] hdc 设备已连接（hdc list targets 有输出）
- [ ] 应用已安装到设备（hdc install -r 成功）
- [ ] 应用已启动（aa start 成功）
- [ ] AC-1.1~1.5 模式切换验证（dump UI 树 + 截图）
- [ ] AC-2.1~2.6 程序员键盘验证
- [ ] AC-3.1~3.6 多进制显示验证
- [ ] AC-4.1~4.5 主进制切换验证
- [ ] AC-5.1~5.4 切换动画验证（截图对比）
- [ ] results.json 包含每个 AC 的 pass/fail/skip
**TDD**：UI 自动化（capabilities.json 中 ui_test.available=true）

## 开发顺序

```
Task 1.1 (BaseConverter.ets)
    ↓
Task 1.2 (BaseConverter.test.ets)
    ↓
Task 1.3 (Models.ets 扩展) ← 并行
Task 2.1 (PreferencesStore.ets) ← 依赖 1.3
Task 3.1 (CalculatorPage 状态变量) ← 依赖 1.3
    ↓
Task 3.2 (ModeToggleRow)
Task 3.3 (Keypad 拆分)
Task 3.4 (BaseConverterPanel + ActiveBaseToggle)
Task 3.5 (onModeChange/onActiveBaseChange + refresh)
Task 3.6 (主结果格式化)
Task 3.7 (transition 动画)
    ↓
Task 4.1 (单元测试运行)
Task 4.2 (UI 自动化测试)
```

## 验收计划

| 任务 | 验收方式 | 验收时间 |
|------|---------|----------|
| Task 1.1 | 代码审查 + 编译 | 实现完成后 |
| Task 1.2 | 单元测试通过 | Task 1.2 完成 |
| Task 1.3 | TypeScript 编译通过 | Task 1.3 完成 |
| Task 2.1 | TypeScript 编译通过 + Preferences 读写验证 | Task 2.1 完成 |
| Task 3.1-3.7 | 编译通过 + UI 自动化测试通过 | 阶段 4 |
| Task 4.1 | hvigorw test 全通过 | 阶段 4 |
| Task 4.2 | UI 测试 results.json 全部 pass | 阶段 4 |

## IMPLEMENTING 阶段完成

- **产出物位置**：`specs/changes/20260615-requirement-add-简单需求/tasks.md`
- **任务总数**：10
- **关键路径**：1.1 → 1.2 → 1.3 → 2.1 → 3.1 → 3.2-3.7 → 4.1 → 4.2
- **下一步**：进入 APPLYING 阶段（TDD RED-GREEN-REFACTOR + 真实代码改动）
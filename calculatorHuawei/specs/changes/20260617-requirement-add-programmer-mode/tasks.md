# 程序员模式 (Issue #22) 开发任务

## 任务概述

- 功能名称：程序员模式（BIN/OCT/DEC/HEX 实时转换 + 模式切换动画）
- 变更类型：requirement-add
- 关联特性：feat-programmer-mode
- 开发阶段：IMPLEMENTING（任务分解）
- 预计任务数：9
- 关联 AID Change: 20260617-requirement-add-programmer-mode

## 环境能力（强制 — 来自 .claude/capabilities.json）

| 维度 | 值 | 影响 |
| --- | --- | --- |
| 项目类型 | HarmonyOS | ArkTS / Stage 模型 |
| 平台 | Windows | hdc + DevEco SDK |
| 编译命令 | `hvigorw --no-daemon assembleHap` | Task 5.1 验证 |
| 单元测试命令 | `hvigorw --no-daemon test` | Task 5.2 验证 |
| 单元测试框架 | hypium + hamock | BaseConverter.test.ets |
| **UI 自动化测试能力** | **true** | **Task 5.3 强制使用 hdc + harmonyos-ui-test** |
| 模拟器 | 127.0.0.1:5555 | UI 测试目标 |
| hdc 路径 | D:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe | 已验证 |
| bundleName | com.darkempire78.opencalculator | hdc install / aa start |

**Task 5.3 选型**：ui_test.available=true → **必须**为 UI 自动化测试（hdc + harmonyos-ui-test skill）。

## 任务列表

### 阶段 1：基础设施（数据模型 + 工具类）

#### Task 1.1: 新增数据模型（NumberBase / CalculatorMode / ProgrammerDisplayState）
**描述**：在 `opencalc/entry/src/main/ets/model/ModeModel.ets` 中定义：
- `enum NumberBase { BIN=2, OCT=8, DEC=10, HEX=16 }` 含 `radix` 字段
- `enum CalculatorMode { STANDARD, PROGRAMMER }`
- `class ProgrammerDisplayState` 含 `bin/oct/dec/hex/hasOverflow`
- `static fromValue(n: number): ProgrammerDisplayState` 委托给 BaseConverter
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/model/ModeModel.ets`（新建）
- 测试：（不需独立测试，作为 Task 1.2 的依赖）
**依赖任务**：无
**验收标准**：
- [ ] 枚举与类符合 delta-design §3.8
- [ ] 纯 ArkTS 类型，无 ArkUI 依赖
- [ ] TS 编译通过（Task 5.1 验证）
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR
> RED: 写空壳枚举 + class；GREEN: 加 fromValue；REFACTOR: 命名优化

#### Task 1.2: 实现 BaseConverter 工具类 + 单元测试
**描述**：在 `opencalc/entry/src/main/ets/calculator/BaseConverter.ets` 实现：
- `toBase(n: number, base: NumberBase): string` — 0 边界/负数/取整/溢出标志
- `fromBase(s: string, base: NumberBase): number` — 解析为 number，NaN 表示非法
- `getRepresentations(n: number): ProgrammerDisplayState`
- `isValidChar(ch: string, base: NumberBase): boolean`
- `maxCharsFor(base: NumberBase): number` — 64-bit 数字最大长度
- 字符表常量 BIN_CHARS = '01', OCT_CHARS = '01234567', DEC_CHARS = '0123456789', HEX_CHARS = '0123456789ABCDEF'

单元测试覆盖 12 个 AC（见 delta-spec §7.1）。
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/calculator/BaseConverter.ets`（新建）
- 测试：`opencalc/entry/src/test/ets/calculator/BaseConverter.test.ets`（新建）
**依赖任务**：Task 1.1
**验收标准**：
- [ ] 12 个 AC 全部通过
- [ ] 边界覆盖：0、负数、小数、2^53、2^60、NaN、非法字符
- [ ] `hvigorw test` 套件 BaseConverter 通过
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR
> RED: 写 12 个测试用例到 .test.ets，预期失败；GREEN: 逐方法实现至通过；REFACTOR: 提取共同字符表

#### Task 1.3: 扩展 PreferencesStore（getProgrammerModeDefault / setProgrammerModeDefault）
**描述**：在 `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets` 末尾追加 2 个方法，模式同 `getVibrationEnabled`：
- `async getProgrammerModeDefault(): Promise<boolean>` — key=`programmerModeDefault`, default `false`
- `async setProgrammerModeDefault(value: boolean): Promise<void>` — `put` + `flush`
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/preferences/PreferencesStore.ets`（修改）
- 测试：与 Task 1.2 合并测试
**依赖任务**：无（独立模块）
**验收标准**：
- [ ] 新增方法签名与 delta-design §3.9.1 一致
- [ ] 不修改现有 `CalculatorPreferences` 接口字段
- [ ] TS 编译通过
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR
> 注：preferences 持久化通过现有 7 个测试覆盖回归；本 Task 主要是接口扩展

### 阶段 2：表现层（组件 + 页面扩展）

#### Task 2.1: 新增 ProgrammerPanel 组件
**描述**：在 `opencalc/entry/src/main/ets/pages/ProgrammerPanel.ets` 实现 `@Component`：
- `@Prop decimalValue: number`
- `@Prop activeBase: NumberBase`
- `onBaseTap: (b: NumberBase) => void` 回调
- 内部 4 行：BIN / OCT / DEC / HEX，每行 [label + value]
- activeBase 行加 2vp 边框
- 字号：DEC 16、BIN/OCT/HEX 13
- NaN/Infinity → 4 行显示 "—"
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/ProgrammerPanel.ets`（新建）
- 测试：UI 自动化覆盖（Task 5.3）
**依赖任务**：Task 1.1, Task 1.2
**验收标准**：
- [ ] 组件独立可渲染（被 Page 嵌入后 4 行可见）
- [ ] 点击行触发 `onBaseTap`
- [ ] activeBase 行视觉高亮
- [ ] 主题色继承（getBtnBg / getT1 / getOp）
**TDD**：[x] RED / [ ] GREEN / [x] REFACTOR
> 组件 UI 难以纯单测，UI 自动化在 Task 5.3 验证；REFACTOR 关注视觉一致

#### Task 2.2: CalculatorPage 集成 mode/activeBase 状态 + 模式入口按钮
**描述**：在 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` 中：
- 新增 `@State mode: CalculatorMode = STANDARD`
- 新增 `@State activeBase: NumberBase = DEC`
- 新增 `@State showModeSheet: boolean = false`
- 新增 `@State programmerDisplay: ProgrammerDisplayState = new ProgrammerDisplayState()`
- `aboutToAppear` 中读 `getProgrammerModeDefault()` 赋给 `mode`
- `loadPrefs()` 同样读
- `ToggleRow` 中新增"模式"按钮（在"基础/科学"按钮旁），点击弹 `promptAction.showActionSheet`
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 1.1, Task 1.3
**验收标准**：
- [ ] 启动后 mode 默认为 STANDARD
- [ ] ToggleRow 出现"模式"按钮且可点
- [ ] ActionSheet 弹出含"标准/程序员"两项
- [ ] 选中后 ActionSheet 关闭
**TDD**：[x] RED / [x] GREEN / [x] REFACTOR
> RED: 加 @State + 空 onModeToggle；GREEN: 接 ActionSheet；REFACTOR: 提取常量

#### Task 2.3: CalculatorPage 实现 setMode + 动画 + onProgrammerRecompute
**描述**：
- 实现 `setMode(m: CalculatorMode)`：包在 `animateTo({ duration: 220, curve: Curve.EaseInOut })` 内，赋新 mode；调用 `setProgrammerModeDefault(m === PROGRAMMER)`
- 实现 `onProgrammerRecompute()`：从 `result` 字符串解析出 number，调用 `BaseConverter.getRepresentations(n)` 赋给 `programmerDisplay`
- 在 `onExpressionChange()` 末尾追加 `this.onProgrammerRecompute()` 调用
- 在 `onEquals()` 末尾追加 `this.onProgrammerRecompute()` 调用
- `build()` 中 `mode === PROGRAMMER` 时条件渲染程序员分支（详见 Task 2.4）
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 1.2, Task 2.2
**验收标准**：
- [ ] setMode 切换有 220ms 动画
- [ ] 重启 App 保留上次 mode
- [ ] expression 变化触发 programmerDisplay 更新
- [ ] 计算完成触发 programmerDisplay 更新
**TDD**：[x] RED / [x] GREEN / [x] REFACTOR

#### Task 2.4: CalculatorPage 条件渲染程序员面板 + 程序员键盘
**描述**：
- 抽出 `@Builder ProgrammerSection()` 内部用 `<ProgrammerPanel .../>` + 4 行（BIN/OCT/HEX/DEC）
- 抽出 `@Builder ProgrammerKeyboard()` 5×4 网格：0-9 + A-F + 加减乘除 + AC/= / 退格
- 修改 `build()`：当 `mode === PROGRAMMER` 时显示 `ProgrammerSection()` + `ProgrammerKeyboard()`，否则显示原 `ButtonGrid()`
- `onDigit(d)` 改造：程序员模式下若 `!isValidChar(d, activeBase)` → `showToast("BIN 不支持字符 X")` 并 return
- `onEquals()` 程序员模式下：把 expression 按 activeBase 解析为 number → CalcEngine 算 → 写回 expression
- `onAC()` 程序员模式下：清空 expression + activeBase=DEC
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 1.2, Task 2.1, Task 2.3
**验收标准**：
- [ ] 程序员模式显示 4 行 + 5×4 键盘
- [ ] 标准模式显示原键盘（0 回归）
- [ ] HEX activeBase 下按 'A'-'F' 生效，按 'G' 弹 Toast
- [ ] BIN activeBase 下按 '2' 弹 Toast
**TDD**：[x] RED / [x] GREEN / [x] REFACTOR

#### Task 2.5: CalculatorPage 实现 onProgrammerBaseTap（跨进制接续）
**描述**：
- `onProgrammerBaseTap(b: NumberBase)`：
  - `activeBase = b`
  - 从 `programmerDisplay` 读对应字符串 `s`（如 hex='FF'）
  - `fromBase(s, b)` 得到 number n
  - `expression = n.toString()`（不带千分位，纯数字）
  - 触发 onProgrammerRecompute 重算
- 在 ProgrammerPanel 调用处传 `onBaseTap: (b) => this.onProgrammerBaseTap(b)`
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖文件**：无新增
**依赖任务**：Task 2.1, Task 2.3
**验收标准**：
- [ ] 点击 HEX 行后 activeBase=HEX，expression='FF' 等价 255
- [ ] 继续按 '+1' 计算得 256，HEX 显示 '100'
- [ ] activeBase 行有视觉高亮
**TDD**：[x] RED / [x] GREEN / [x] REFACTOR

### 阶段 5：验证

#### Task 5.1: 编译验证
**描述**：在 `opencalc/` 目录运行 `hvigorw --no-daemon assembleHap`
**涉及文件**：无
**依赖任务**：Task 1.1..2.5 全部
**验收标准**：
- [ ] 退出码 0
- [ ] 输出包含 "BUILD SUCCESSFUL"
- [ ] 产出 `entry/build/default/outputs/default/entry-default-signed.hap`
**TDD**：N/A（验证任务）

#### Task 5.2: 单元测试
**描述**：运行 `hvigorw --no-daemon test`
**涉及文件**：无
**依赖任务**：Task 5.1
**验收标准**：
- [ ] BaseConverter.test.ets 12 个 AC 通过
- [ ] 现有 7 套测试套件全部通过（0 回归）
- [ ] 测试报告输出 PASS
**TDD**：N/A

#### Task 5.3: UI 自动化测试（强制 — capabilities.json ui_test.available=true）

> **强制规则**：capabilities.json 中 `ui_test.available=true`，**必须**使用 hdc + harmonyos-ui-test skill。
> **禁止**改写为"手动集成验证"或"Deferred"。

**描述**：在模拟器 127.0.0.1:5555 上执行 8 个 AC 验证
**涉及文件**：
- 测试脚本：`specs/changes/20260617-requirement-add-programmer-mode/ui-tests/run_tests.py`
- 解析工具：`specs/changes/20260617-requirement-add-programmer-mode/ui-tests/parse_ui.py`
- 截图：`specs/changes/20260617-requirement-add-programmer-mode/ui-tests/screenshot/`
- 结果：`specs/changes/20260617-requirement-add-programmer-mode/ui-tests/results.json`
**依赖任务**：Task 5.1, Task 5.2
**验收标准**：
- [ ] `hdc list targets` 输出 127.0.0.1:5555
- [ ] `hdc install -r` HAP 成功
- [ ] `aa start -a EntryAbility -b com.darkempire78.opencalculator` 成功
- [ ] AC-U1 默认进入标准模式通过
- [ ] AC-U2 点击"模式"按钮 → ActionSheet 弹窗通过
- [ ] AC-U3 切到程序员模式后 220±50ms 内动画完成通过
- [ ] AC-U4 输入 "10" 后 BIN='1010' OCT='12' DEC='10' HEX='A' 通过
- [ ] AC-U5 点击 HEX 行 → activeBase 切换 通过
- [ ] AC-U6 HEX 模式按 'F' 正确追加 通过
- [ ] AC-U7 BIN 模式按 '2' → Toast 提示 通过
- [ ] AC-U8 重启 App 默认进入程序员模式通过
- [ ] screenshot/ 至少 10 张关键步骤截图
- [ ] results.json 含 8 个 AC 的 pass/fail 状态
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR

## 开发顺序

```
Task 1.1 (ModeModel)
   │
   ├─→ Task 1.2 (BaseConverter + 单测)
   │      │
   │      └─→ Task 2.1 (ProgrammerPanel 组件)
   │             │
   │             └─→ Task 2.4 (Page 条件渲染程序员面板+键盘)
   │
   ├─→ Task 1.3 (PreferencesStore 扩展)
   │
   └─→ Task 2.2 (Page 模式入口 + @State)
          │
          └─→ Task 2.3 (setMode + 动画 + onProgrammerRecompute)
                 │
                 └─→ Task 2.5 (onProgrammerBaseTap 跨进制接续)
                        │
                        ▼
                  Task 5.1 (编译)
                        │
                        ▼
                  Task 5.2 (单元测试)
                        │
                        ▼
                  Task 5.3 (UI 自动化) → 完成
```

## 验收计划

| 任务 | 验收方式 | 关键产出 |
| --- | --- | --- |
| Task 1.1 | TS 编译 | model/ModeModel.ets |
| Task 1.2 | 单元测试 | BaseConverter.test.ets 12/12 PASS |
| Task 1.3 | TS 编译 | PreferencesStore 2 方法 |
| Task 2.1 | UI 集成 | ProgrammerPanel.ets 渲染 |
| Task 2.2 | UI 集成 | ToggleRow 模式入口可见 |
| Task 2.3 | 编译 + 视觉 | animateTo 220ms 可见 |
| Task 2.4 | UI 自动化 | 程序员键盘可见 + 0 回归 |
| Task 2.5 | UI 自动化 | 跨进制接续 AC 通过 |
| Task 5.1 | 编译命令 | BUILD SUCCESSFUL |
| Task 5.2 | 单元测试 | 19/19 PASS（12 新 + 7 旧） |
| Task 5.3 | **UI 自动化** | 8/9 PASS + 10 截图 + results.json |

## 风险与回退

| 风险 | 回退策略 |
|------|---------|
| 模拟器 127.0.0.1:5555 未启动 | hdc kill / hdc start；启动模拟器后再跑 |
| animateTo 编译不通过 | 改为 `transition` 属性 + opacity 切换 |
| BIN/OCT/HEX 行在横屏被历史面板挤压 | 缩短历史面板 maxWidth；优先保证主区可见 |
| 启动时 mode 读取有闪烁 | 用 `aboutToAppear` 内同步读 + 默认值兜底 |

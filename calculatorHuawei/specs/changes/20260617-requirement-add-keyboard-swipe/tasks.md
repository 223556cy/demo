# Issue #29 — 竖屏手势滑动切换三种键盘模式 (开发任务)

## 任务概述

- 功能名称：竖屏左右滑动切换基础/科学/程序员三种键盘模式
- 变更类型：requirement-add
- 关联特性：feat-issue-29-keyboard-swipe
- 关联 Issue：#29
- 关联设计：`./delta-design.md`
- 关联 SPEC：`./delta-spec.md`
- 开发阶段：单页 Swiper 改造 + 模式状态机 + 程序员键盘 + UI 自动化
- 预计任务数：9 个最小可开发单元

## 任务列表

### 阶段 1：基础设施（Model / Preferences / Resources）

#### Task 1.1: 扩展 Models.ets — 新增 KeyboardMode 枚举 + programmerModeDefault 字段
**描述**：在 `opencalc/entry/src/main/ets/model/Models.ets` 中：
- 新增 `KeyboardMode` 枚举：`BASIC = 0 / SCIENTIFIC = 1 / PROGRAMMER = 2`
- 在 `CalculatorPreferences` interface 末尾新增 `programmerModeDefault: number`
- 在 `DEFAULT_PREFERENCES` 中新增 `programmerModeDefault: ScientificModeType.NOT_ACTIVE` 默认值
**涉及文件**：
- `opencalc/entry/src/main/ets/model/Models.ets`（修改）
**依赖任务**：无
**验收标准**：
- [ ] `KeyboardMode` 枚举导出 3 个值
- [ ] `CalculatorPreferences` 接口包含 `programmerModeDefault: number`
- [ ] `DEFAULT_PREFERENCES` 默认值 = `ScientificModeType.NOT_ACTIVE` (0)
- [ ] 现有 `scientificModeDefault` 字段语义不变
**TDD**：N/A（纯类型定义）

#### Task 1.2: 扩展 PreferencesStore.ets — 新增 programmerModeDefault 读写
**描述**：在 `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets` 中：
- 新增 `async getProgrammerModeDefault(): Promise<number>`（与 `getScientificModeDefault` 同模式）
- 新增 `async setProgrammerModeDefault(value: number): Promise<void>`（与 `setScientificModeDefault` 同模式）
- 在 `getAllPreferences()` 返回值中包含 `programmerModeDefault: await this.getProgrammerModeDefault()`
**涉及文件**：
- `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets`（修改）
**依赖任务**：Task 1.1
**验收标准**：
- [ ] `getProgrammerModeDefault()` 读取 `programmerModeDefault` key，默认 `ScientificModeType.NOT_ACTIVE`
- [ ] `setProgrammerModeDefault(v)` 写入后 `flush()`
- [ ] `getAllPreferences()` 返回对象包含 `programmerModeDefault` 字段
- [ ] 错误处理风格与现有方法一致
**TDD**：[x] RED（先写单元测试覆盖 set/get）
**为什么 TDD**：纯数据访问逻辑，可在测试中直接验证；为后续 Task 5.1 单元测试做基础

#### Task 1.3: 扩展 string.json — 新增程序员键盘字符串
**描述**：在 `opencalc/entry/src/main/element/string.json` 中新增：
- `"mode_basic"` = "基础"
- `"mode_scientific"` = "科学"
- `"mode_programmer"` = "程序员"
- `"base_hex"` / `"base_dec"` / `"base_oct"` / `"base_bin"` = "HEX" / "DEC" / "OCT" / "BIN"
- `"op_and"` / `"op_or"` / `"op_not"` / `"op_xor"` = "AND" / "OR" / "NOT" / "XOR"
- `"op_shl"` / `"op_shr"` = "<<" / ">>"
**涉及文件**：
- `opencalc/entry/src/main/element/string.json`（修改）
**依赖任务**：无
**验收标准**：
- [ ] 所有新 key/value 写入 string.json
- [ ] 不删除任何已有 key
**TDD**：N/A（资源文件）

### 阶段 2：UI 重构（CalculatorPage）

#### Task 2.1: CalculatorPage.ets — 新增 currentMode 状态与控制器
**描述**：在 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` 顶部 @State 段：
- 引入 `KeyboardMode` 枚举
- 新增 `@State currentMode: KeyboardMode = KeyboardMode.BASIC`
- 新增 `private swpController: SwiperController = new SwiperController()`
- 保留 `@State scientific: boolean = false` 作为派生兼容字段
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 1.1
**验收标准**：
- [ ] 顶部 @State 段增加 `currentMode`
- [ ] `swpController` 初始化
- [ ] `scientific` 保留
- [ ] 编译通过
**TDD**：N/A（状态声明）

#### Task 2.2: CalculatorPage.ets — 实现 modeController (cycleMode + onSwiperChange)
**描述**：在 CalculatorPage 类内新增两个方法：
- `modeController_cycleMode()`：`newIdx = (this.currentMode + 1) % 3`；调用 `this.swpController.changeIndex(newIdx, false)`；注释说明单向数据流（实际状态由 onChange 触发）
- `modeController_onSwiperChange(idx: number)`：
  - 边界检查 `if (idx < 0 || idx > 2) { console.warn(...); return }`
  - `this.currentMode = idx as KeyboardMode`
  - `this.scientific = (idx === KeyboardMode.SCIENTIFIC)`
  - `void this.savePref('scientific', idx === KeyboardMode.SCIENTIFIC ? 1 : 0)`
  - `void this.savePref('programmer', idx === KeyboardMode.PROGRAMMER ? 1 : 0)`
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 2.1
**验收标准**：
- [ ] `cycleMode()` 调用 `swpController.changeIndex`
- [ ] `onSwiperChange(idx)` 正确同步 currentMode / scientific / preferences
- [ ] 非法 idx 触发 console.warn 并 return
- [ ] 编译通过
**TDD**：[x] RED（单元测试覆盖 cycleMode 三态循环 + onSwiperChange 三态切换）

#### Task 2.3: CalculatorPage.ets — 改造 ToggleRow 三态循环
**描述**：修改 `ToggleRow()` @Builder：
- label 由 `this.scientific ? '科学' : '基础'` 改为跟随 `this.currentMode`：
  - BASIC → "基础"
  - SCIENTIFIC → "科学"
  - PROGRAMMER → "程序员"
- onClick 由 `toggle` 改为 `modeController_cycleMode()`
- 仅在 `!this.isLandscape` 时渲染（横屏不显示模式按钮）
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 2.2
**验收标准**：
- [ ] ToggleRow label 跟随 currentMode 三态变化
- [ ] onClick 调用 `modeController_cycleMode()`
- [ ] 横屏 (isLandscape=true) 不渲染 ToggleRow
- [ ] 编译通过
**TDD**：N/A（UI 绑定）

#### Task 2.4: CalculatorPage.ets — Swiper 包裹 ButtonGrid + 新增 ProgrammerGrid
**描述**：在 CalculatorPage build 段：
- 新增 `@Builder ProgrammerGrid()`：实现最简程序员键盘布局
  - 第 1 行：HEX / DEC / OCT / BIN（基数切换按钮，本期点击显示提示 toast 或仅记录点击）
  - 第 2 行：AND / OR / NOT / XOR
  - 第 3 行：<< / >> / 退格 / AC
  - 复用 `BtnFunc / BtnOp / BtnDig` 等已有 @Builder，颜色复用 `getOp/getBtnBg/getFuncBg`
- 修改 `ButtonGrid()` 内部：
  - 竖屏 (`!this.isLandscape`)：外层包 `Swiper(this.swpController) { BasicGrid(); ScientificGrid(); ProgrammerGrid() }` + `indicator: new DotIndicator()` + `index: this.currentMode` + `onChange: modeController_onSwiperChange` + `loop: false`
  - 横屏 (`this.isLandscape`)：保留原 `if (this.scientific) { 科学键 } else { 基础键 }` 单页
- 拆出 `BasicGrid()` / `ScientificGrid()` @Builder 作为 Swiper 子项的复用
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 2.2, Task 2.3
**验收标准**：
- [ ] `Swiper` 包裹三页键盘，索引与 currentMode 同步
- [ ] `DotIndicator` 渲染
- [ ] `onChange` 触发 `modeController_onSwiperChange`
- [ ] `loop: false`
- [ ] `ProgrammerGrid` 提供 HEX/DEC/OCT/BIN + AND/OR/NOT/XOR + <</>> 共 ≥ 10 个按键
- [ ] 横屏不渲染 Swiper
- [ ] 编译通过
**TDD**：[x] GREEN（构建产出后用 UI 自动化验证）

#### Task 2.5: CalculatorPage.ets — loadPrefs 读取 programmerModeDefault
**描述**：修改 `loadPrefs()` / `aboutToAppear`：
- 启动优先级：SCIENTIFIC > PROGRAMMER > BASIC
- 读取 `await this.prefs.getProgrammerModeDefault()`
- 决定初始 `currentMode`：
  - `scientific === 1` → SCIENTIFIC
  - else `programmer === 1` → PROGRAMMER
  - else BASIC
- 同步设置 `this.scientific` 兼容字段
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 1.2, Task 2.1
**验收标准**：
- [ ] 启动时正确读取 `programmerModeDefault`
- [ ] 优先级 SCIENTIFIC > PROGRAMMER > BASIC
- [ ] 首次渲染 currentMode 与 prefs 一致
- [ ] 编译通过
**TDD**：[x] RED（单元测试覆盖启动优先级）

### 阶段 3：测试与验证

#### Task 5.1: 单元测试 — 模式状态机 + PreferencesStore
**描述**：在 `opencalc/entry/src/test/...` 下新增或修改测试文件：
- 覆盖 `KeyboardMode` 枚举值（0/1/2）
- 覆盖 `cycleMode` 三态循环：BASIC → SCIENTIFIC → PROGRAMMER → BASIC
- 覆盖 `onSwiperChange(0/1/2)` 正确更新 currentMode + scientific + 调 savePref
- 覆盖 `onSwiperChange(-1)` / `onSwiperChange(3)` 触发 console.warn 并 return
- 覆盖 `PreferencesStore.getProgrammerModeDefault / setProgrammerModeDefault`（mock preferences）
- 覆盖启动优先级：scientific=1 → SCIENTIFIC；programmer=1 → PROGRAMMER；都=0 → BASIC
**涉及文件**：
- `opencalc/entry/src/test/.../*mode*.test.ets`（新增）
- `opencalc/entry/src/test/.../PreferencesStore.test.ets`（修改）
**依赖任务**：Task 1.1, Task 1.2, Task 2.1, Task 2.2, Task 2.5
**验收标准**：
- [ ] `hvigorw --no-daemon test` 全部 PASS
- [ ] cycleMode / onSwiperChange / 启动优先级 全部覆盖
**TDD**：[x] RED（先于 Task 2.2 / Task 2.5 写）→ [x] GREEN（实现后通过）

#### Task 5.2: 编译验证 — hvigorw assembleHap
**描述**：执行 `hvigorw --no-daemon assembleHap` 验证编译通过。
**涉及文件**：N/A
**依赖任务**：Task 1.1, Task 1.2, Task 1.3, Task 2.1, Task 2.2, Task 2.3, Task 2.4, Task 2.5
**验收标准**：
- [ ] 退出码 0
- [ ] 产物 `entry/build/default/outputs/.../*.hap` 存在
**TDD**：N/A

#### Task 5.3: UI 自动化测试 — 滑动手势 + 模式循环 + 重启恢复
**描述**：基于 `capabilities.json` 中 `ui_test.available=true`，使用 hdc + harmonyos-ui-test skill：
- UI-01 竖屏左滑 BASIC → SCIENTIFIC，圆点指示器更新
- UI-02 竖屏右滑 SCIENTIFIC → BASIC
- UI-03 竖屏左滑 SCIENTIFIC → PROGRAMMER，程序员键盘可见（包含 HEX/DEC/OCT/BIN/AND/OR/NOT/XOR/<<//>>）
- UI-04 点击模式按钮 label 三态循环：基础 → 科学 → 程序员 → 基础
- UI-05 重启 App，模式恢复
- UI-06 横屏不显示 Swiper，继续只显示科学模式
**涉及文件**：
- 测试脚本：`specs/changes/20260617-requirement-add-keyboard-swipe/ui-tests/run_tests.py`
- 截图：`specs/changes/20260617-requirement-add-keyboard-swipe/ui-tests/screenshot/`
- 结果：`specs/changes/20260617-requirement-add-keyboard-swipe/ui-tests/results.json`
- 解析工具：`specs/changes/20260617-requirement-add-keyboard-swipe/ui-tests/parse_ui.py`
**依赖任务**：Task 2.4, Task 5.2
**验收标准**：
- [ ] hdc 设备已连接（hdc list targets 有输出）
- [ ] 应用已安装到设备（hdc install -r 成功）
- [ ] 应用已启动（aa start 成功）
- [ ] UI-01 ~ UI-06 全部通过 dump UI 树 + 截图验证
- [ ] screenshot/ 目录包含每步操作截图
- [ ] results.json 包含每个 AC 的 pass/fail/skip 状态
**TDD**：[x] RED / [x] GREEN（端到端验证）

### 阶段 4：提交

#### Task 6.1: git commit
**描述**：将所有 AID 产物 + 真实代码改动 + 测试 commit 到当前分支 `feat/issue-29-中等模糊`。
**涉及文件**：所有变更
**依赖任务**：Task 5.1, Task 5.2, Task 5.3
**验收标准**：
- [ ] `git status` 干净
- [ ] commit message 包含 `feat(swipe):` 前缀 + Issue #29 关联
- [ ] 不 push（dev-01 负责）
**TDD**：N/A

#### Task 6.2: gh_helper.py comment
**描述**：在 Issue #29 下发评论通知 dev-01 已完成。
**涉及文件**：N/A
**依赖任务**：Task 6.1
**验收标准**：
- [ ] gh_helper.py comment 29 "@littleleafccccc claude -p 跑完,worktree 在 <wt_path> 等 push"
**TDD**：N/A

## 开发顺序

```
Task 1.1 (Models)
  ├── Task 1.2 (PreferencesStore)
  │     └── Task 5.1 (单测 RED 部分 — 覆盖 PreferencesStore)
  ├── Task 1.3 (string.json)
  └── Task 2.1 (CalculatorPage @State)
        ├── Task 2.2 (modeController)
        │     └── Task 5.1 (单测 RED 部分 — 覆盖 cycleMode / onSwiperChange)
        ├── Task 2.3 (ToggleRow)
        │     └── Task 2.4 (Swiper + ProgrammerGrid)
        │           ├── Task 5.1 (单测 GREEN — 全部通过)
        │           ├── Task 5.2 (hvigorw assembleHap)
        │           └── Task 5.3 (UI 自动化 — 需 Task 5.2 先过)
        │                 └── Task 2.5 (loadPrefs)
        │                       └── Task 5.1 (启动优先级测试)
        └── Task 6.1 (commit)
              └── Task 6.2 (gh comment)
```

## 验收计划

| 任务 | 验收方式 | 验收时间 |
|------|---------|----------|
| Task 1.1 | 代码审查 | 实现后立即 |
| Task 1.2 | 单元测试 RED | 实现后立即 |
| Task 1.3 | 代码审查 | 实现后立即 |
| Task 2.1 | 编译验证 | Task 5.2 |
| Task 2.2 | 单元测试 RED/GREEN | Task 5.1 |
| Task 2.3 | UI 测试 UI-04 | Task 5.3 |
| Task 2.4 | UI 测试 UI-01/02/03/06 | Task 5.3 |
| Task 2.5 | 单元测试启动优先级 | Task 5.1 |
| Task 5.1 | `hvigorw --no-daemon test` | 实现后 |
| Task 5.2 | 退出码 0 + .hap 产物 | Task 2.4 后 |
| Task 5.3 | results.json 全 pass | Task 5.2 后 |
| Task 6.1 | `git log` 显示 commit | 实现后 |
| Task 6.2 | GitHub issue 评论出现 | 实现后 |

## 风险点

- **R1 (手势冲突)**：TextArea 不放入 Swiper 内 (Task 2.4 拆分 BasicGrid/ScientificGrid/ProgrammerGrid)
- **R2 (双向绑定循环)**：onChange 单点入口，按钮通过 swpController.changeIndex + onChange 触发 (Task 2.2)
- **R3 (横屏 Swiper 浪费)**：横屏不渲染 Swiper (Task 2.3 / 2.4 分支)
- **R7 (CalcEngine 不支持位运算)**：程序员键盘本期仅作 UI 展示，按键点击不强制接入 CalcEngine (Task 2.4)
- **FM-01 (非法 index)**：onSwiperChange 内 if/else 严格枚举 (Task 2.2)
- **FM-02 (prefs 写入失败)**：savePref 已 try-catch 包装 (Task 2.2 沿用)

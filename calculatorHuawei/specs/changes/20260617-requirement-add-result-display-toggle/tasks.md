# Issue #27 计算结果支持小数和分数两种显示 - 开发任务

## 任务概述

- 功能名称：结果小数/分数显示切换
- 变更类型：requirement-add
- 关联特性：feat-calculator-result-display
- 关联 Issue：#27
- 开发阶段：PLANNING ✅ → IMPLEMENTING ⏳ → APPLYING
- 预计任务数：8

## 任务列表

### 阶段 1：基础设施（数据 + 工具）

#### Task 1.1: 新增 `DisplayMode` 枚举
**描述**：在 `model/Models.ets` 中新增 `DisplayMode` 枚举，包含 `DECIMAL = 'decimal'` 与 `FRACTION = 'fraction'` 两个值。
**涉及文件**：
- `opencalc/entry/src/main/ets/model/Models.ets` (modify)
**依赖任务**：无
**验收标准**：
- [ ] `DisplayMode` 枚举可在 `Models.ets` 顶部导入
- [ ] 编译通过（`hvigorw --no-daemon assembleHap`）
**TDD**：N/A（数据模型，无可测行为）

#### Task 1.2: 新增 `FractionResult` 接口
**描述**：在 `model/Models.ets` 中新增 `FractionResult` 接口，含 `numerator: number` 与 `denominator: number` 字段。
**涉及文件**：
- `opencalc/entry/src/main/ets/model/Models.ets` (modify)
**依赖任务**：Task 1.1
**验收标准**：
- [ ] 接口可在其他模块导入使用
- [ ] 编译通过
**TDD**：N/A

#### Task 1.3: 新增 `FractionUtil` 工具类
**描述**：在 `common/FractionUtil.ets` 新建纯函数工具类，实现：
- `gcd(a, b): number` 欧几里得算法
- `toFraction(value, maxDenominator=9999): FractionResult | null`
- `format(numerator, denominator): string` 输出 `a/b` 或整数
**涉及文件**：
- `opencalc/entry/src/main/ets/common/FractionUtil.ets` (new)
**依赖任务**：Task 1.2
**验收标准**：
- [ ] `toFraction(0.5) === {numerator: 1, denominator: 2}`
- [ ] `toFraction(0.25) === {numerator: 1, denominator: 4}`
- [ ] `toFraction(-0.5) === {numerator: -1, denominator: 2}`
- [ ] `toFraction(0.3333)` 返回 null（分母 10000 > 9999）
- [ ] `toFraction(0) === {numerator: 0, denominator: 1}`
- [ ] `toFraction(NaN/Infinity)` 返回 null
- [ ] `format(1, 2) === "1/2"`
- [ ] `format(4, 2) === "2"`
- [ ] `format(0, 1) === "0"`
- [ ] `format(-1, 2) === "-1/2"`
- [ ] `gcd(12, 8) === 4`
**TDD**：先 RED（写测试，断言失败），再 GREEN（实现），最后 REFACTOR

#### Task 1.4: 扩展 `CalculatorPreferences`
**描述**：在 `model/Models.ets` 中：
- `CalculatorPreferences` 接口增加 `resultDisplayMode: DisplayMode` 字段
- `DEFAULT_PREFERENCES` 增加 `resultDisplayMode: 'decimal'` 默认值
**涉及文件**：
- `opencalc/entry/src/main/ets/model/Models.ets` (modify)
**依赖任务**：Task 1.1
**验收标准**：
- [ ] `getAllPreferences()` 返回对象含 `resultDisplayMode` 字段
- [ ] 现有调用方（如设置面板）不破坏
**TDD**：N/A

### 阶段 2：持久化层

#### Task 2.1: 扩展 `PreferencesStore`
**描述**：在 `preferences/PreferencesStore.ets` 中：
- 新增 `getResultDisplayMode(): Promise<DisplayMode>`
- 新增 `setResultDisplayMode(mode: DisplayMode): Promise<void>`
- 修改 `getAllPreferences()` 返回对象含 `resultDisplayMode` 字段
- key: `'resultDisplayMode'`
**涉及文件**：
- `opencalc/entry/src/main/ets/preferences/PreferencesStore.ets` (modify)
**依赖任务**：Task 1.4
**验收标准**：
- [ ] `getResultDisplayMode()` 默认返回 `DisplayMode.DECIMAL`
- [ ] `setResultDisplayMode(FRACTION)` 持久化
- [ ] 下次启动 `getResultDisplayMode()` 返回 `FRACTION`
- [ ] 编译通过
**TDD**：RED（mock preferences）→ GREEN → REFACTOR

### 阶段 3：UI 表现层

#### Task 3.1: CalculatorPage 状态扩展
**描述**：在 `pages/CalculatorPage.ets` 中：
- 新增 `@State displayMode: DisplayMode = DisplayMode.DECIMAL`
- 新增 `@State lastRawResult: number = 0`（缓存用于分数重格式化）
- `loadPrefs()` 加载 `displayMode`
- `savePref()` 增加 `resultDisplayMode` case
- `onAC()` 增加 `lastRawResult = 0` 清空
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (modify)
**依赖任务**：Task 2.1
**验收标准**：
- [ ] 编译通过
- [ ] 启动后 `displayMode` 反映上次保存值
- [ ] 切换后 `savePref` 写回 Preferences
**TDD**：N/A（state wiring）

#### Task 3.2: CalculatorPage onEquals 缓存 raw
**描述**：在 `pages/CalculatorPage.ets` 的 `onEquals()` 中：
- `this.result = fmt` 之后，添加 `this.lastRawResult = raw`
- 包含 NL 换算路径与正常求值路径两条
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (modify)
**依赖任务**：Task 3.1
**验收标准**：
- [ ] 正常计算后 `this.lastRawResult` 持有 raw 数值
- [ ] NL 换算路径不破坏（如适用，NL 仍用 nlConversionResult）
**TDD**：N/A

#### Task 3.3: CalculatorPage 结果区切换按钮 + 重格式化
**描述**：在 `pages/CalculatorPage.ets` 的结果显示区：
- 用 `Stack({ alignContent: Alignment.TopEnd })` 包裹 `Text(this.result)`
- 右上角加切换按钮（Text 风格），点击调用 `onToggleDisplayMode()`
- 新增 `onToggleDisplayMode()`：翻转 displayMode + 持久化
- 新增 `formatResultForDisplay()`：根据 displayMode 调用 FractionUtil 或 NumberFormatter
- 错误状态下不渲染按钮
- 横屏模式（`isLandscape=true`）不渲染按钮
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (modify)
**依赖任务**：Task 3.2
**验收标准**：
- [ ] 计算 `1÷2`，显示 `0.5`
- [ ] 点击切换按钮，显示 `1/2`
- [ ] 再点击切换，显示回 `0.5`
- [ ] 计算 `1÷3`（无理），显示 `0.33333...`
- [ ] 切换按钮在错误状态不可见
- [ ] 切换按钮在横屏不可见
- [ ] 编译通过
**TDD**：N/A（UI，需 UI 自动化测试覆盖）

### 阶段 4：测试

#### Task 4.1: 单元测试 - FractionUtil
**描述**：在 `opencalc/entry/src/test/common/FractionUtil.test.ets` 新建单元测试，覆盖：
- `gcd` 多组数据
- `toFraction` 正/负/零/NaN/Inf/超分母回退
- `format` 整数/真分数/负数/零
使用 hypium + hamock 框架。
**涉及文件**：
- `opencalc/entry/src/test/common/FractionUtil.test.ets` (new)
**依赖任务**：Task 1.3
**验收标准**：
- [ ] `hvigorw --no-daemon test` 全部通过
- [ ] 覆盖率 ≥ 90% of FractionUtil
**TDD**：RED → GREEN → REFACTOR

#### Task 4.2: 单元测试 - PreferencesStore (DisplayMode)
**描述**：在 `opencalc/entry/src/test/preferences/PreferencesStore.test.ets` 增加 DisplayMode 读写测试（如果测试文件不存在则新建）。
**涉及文件**：
- `opencalc/entry/src/test/preferences/PreferencesStore.test.ets` (new or modify)
**依赖任务**：Task 2.1
**验收标准**：
- [ ] `hvigorw --no-daemon test` 全部通过
**TDD**：RED → GREEN → REFACTOR

#### Task 5.3: UI 自动化测试（基于 capabilities.json: ui_test.available=true）
**描述**：使用 hdc + harmonyos-ui-test skill 在模拟器（127.0.0.1:5555）上执行 AC 验证。
**涉及文件**：
- 测试脚本：`specs/changes/20260617-requirement-add-result-display-toggle/ui-tests/run_tests.py`
- 截图：`specs/changes/20260617-requirement-add-result-display-toggle/ui-tests/screenshot/`
- 结果：`specs/changes/20260617-requirement-add-result-display-toggle/ui-tests/results.json`
- 解析工具：`specs/changes/20260617-requirement-add-result-display-toggle/ui-tests/parse_ui.py`
**依赖任务**：Task 3.3, Task 4.1
**验收标准**：
- [ ] hdc 设备已连接（hdc list targets 有输出）
- [ ] 应用已安装到设备（hdc install -r 成功）
- [ ] 应用已启动（aa start 成功）
- [ ] AC-1: 计算 `1÷2` 默认显示 `0.5`
- [ ] AC-2: 点击切换后显示 `1/2`
- [ ] AC-3: 再次点击显示回 `0.5`
- [ ] AC-4: 重启 App 后模式保留
- [ ] AC-5: 历史记录仍以小数显示
- [ ] screenshot/ 目录包含每步操作截图
- [ ] results.json 包含每个 AC 的 pass/fail/skip 状态
**TDD**：UI 自动化作为 RED → 修复 → GREEN

## 开发顺序

```
Task 1.1 (DisplayMode enum)
   ↓
Task 1.2 (FractionResult interface)
   ↓
Task 1.3 (FractionUtil - RED 写测试 → GREEN 实现 → REFACTOR)
   ↓
Task 1.4 (CalculatorPreferences 扩展)
   ↓
Task 2.1 (PreferencesStore - RED → GREEN → REFACTOR)
   ↓
Task 3.1 (CalculatorPage state 扩展)
   ↓
Task 3.2 (onEquals 缓存 raw)
   ↓
Task 3.3 (切换按钮 + 重格式化)
   ↓
Task 4.1 (FractionUtil 单元测试 - 已在 Task 1.3 期间完成)
   ↓
Task 4.2 (PreferencesStore 单元测试)
   ↓
Task 5.3 (UI 自动化测试)
   ↓
完成
```

## 验收计划

| 任务 | 验收方式 | 工具/命令 |
|------|---------|-----------|
| Task 1.1-1.4 | 编译 | `hvigorw --no-daemon assembleHap` |
| Task 1.3 | 单元测试 | `hvigorw --no-daemon test` |
| Task 2.1 | 单元测试 | `hvigorw --no-daemon test` |
| Task 3.1-3.3 | 编译 + UI 自动化 | `hvigorw --no-daemon assembleHap` + hdc |
| Task 4.1-4.2 | 单元测试 | `hvigorw --no-daemon test` |
| Task 5.3 | UI 自动化 | hdc + harmonyos-ui-test skill |

## 风险与回滚

- 风险：CalculatorPage 改动可能影响其他功能 → 缓解：尽量局部修改，复用现有 NumberFormatter
- 风险：持久化失败 → 缓解：try-catch + 默认 DECIMAL
- 回滚：删除 DisplayMode/FractionUtil 相关代码，恢复 CalculatorPage 原始状态

## IMPLEMENTING 阶段完成确认

- [x] 任务分解完成（8 个任务）
- [x] 任务依赖关系明确
- [x] 验收标准可度量
- [x] 测试任务基于 capabilities.json 硬性选择（ui_test.available=true → Task 5.3 = UI 自动化）

**进入 APPLYING 阶段**（自动同意，方案 C）。

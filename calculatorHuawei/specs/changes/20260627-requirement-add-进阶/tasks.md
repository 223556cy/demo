# Issue #27 分数/小数结果显示切换 — 开发任务

## 任务概述

- 功能名称：计算结果支持小数和分数两种显示，自由切换
- 变更类型：requirement-add
- 关联特性：feat-result-display-toggle
- 开发阶段：代码已存在于 feat/issue-27 分支，本次 AID 以验证、测试、补全产物为主
- 预计任务数：5

## 任务列表

### 阶段 1：基础设施验证

#### Task 1.1: 验证 Model 与 PreferencesStore 扩展
**描述**：确认 DisplayMode 枚举已在 model/Models.ets 中定义，PreferencesStore 已新增 getResultDisplayMode / setResultDisplayMode 方法。
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/model/Models.ets`
- 实现：`opencalc/entry/src/main/ets/preferences/PreferencesStore.ets`
**依赖任务**：无
**验收标准**：
- [ ] Models.ets 中存在 `DisplayMode.DECIMAL` 和 `DisplayMode.FRACTION`
- [ ] PreferencesStore 中存在 `getResultDisplayMode()` 和 `setResultDisplayMode()`
- [ ] 编译通过，无类型错误
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR

#### Task 1.2: 验证 FractionUtil 核心算法
**描述**：确认 FractionUtil 已实现 toFraction、format、gcd 方法，且算法符合设计。
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/common/FractionUtil.ets`
- 测试：`opencalc/entry/src/test/ets/common/FractionUtil.test.ets`
**依赖任务**：Task 1.1
**验收标准**：
- [ ] toFraction 能将 0.5 转为 {1, 2}
- [ ] toFraction 对 1/3 返回 null（无法精确表示）
- [ ] format 能正确输出 "1/2"、"2"、"-1/2"
- [ ] 单元测试已注册在 List.test.ets 中
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR

### 阶段 2：核心功能验证

#### Task 2.1: 验证 CalculatorPage 状态与交互
**描述**：确认 CalculatorPage 已新增 displayMode、lastRawResult 状态，onToggleDisplayMode 和 formatResultForDisplay 方法已实现，DisplayPanel 包含切换按钮。
**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 1.2
**验收标准**：
- [ ] CalculatorPage 中存在 `@State displayMode: DisplayMode`
- [ ] 存在 `onToggleDisplayMode()` 方法
- [ ] 存在 `formatResultForDisplay()` 方法
- [ ] DisplayPanel 中包含切换按钮且绑定点击事件
- [ ] 编译通过，无类型错误
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR

### 阶段 3：测试执行

#### Task 3.1: 单元测试执行
**描述**：运行 hvigorw test，确认 FractionUtil 单元测试全部通过。
**涉及文件**：
- 测试：`opencalc/entry/src/test/ets/common/FractionUtil.test.ets`
- 测试入口：`opencalc/entry/src/test/List.test.ets`
**依赖任务**：Task 2.1
**验收标准**：
- [ ] `hvigorw --no-daemon test` 执行成功
- [ ] FractionUtil 相关用例全部 PASS
- [ ] 无 regression（其他已有用例仍通过）
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR

#### Task 3.2: UI 自动化测试
**描述**：使用 hdc + harmonyos-ui-test skill 在模拟器上验证切换按钮可见、可点击、切换后结果正确。
**涉及文件**：
- 测试脚本：`specs/changes/20260627-requirement-add-进阶/ui-tests/run_tests.py`
- 截图：`specs/changes/20260627-requirement-add-进阶/ui-tests/screenshot/`
- 结果：`specs/changes/20260627-requirement-add-进阶/ui-tests/results.json`
**依赖任务**：Task 3.1
**验收标准**：
- [ ] hdc 设备已连接（hdc list targets 有输出）
- [ ] 应用已安装到设备（hvigorw assembleHap + hdc install 成功）
- [ ] 应用已启动
- [ ] 截图验证切换按钮存在于结果区
- [ ] 操作后截图验证结果在分数/小数间切换
- [ ] results.json 包含每个 AC 的 pass/fail 状态
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR

## 开发顺序

```
Task 1.1 → Task 1.2 → Task 2.1 → Task 3.1 → Task 3.2 → 完成
```

## 验收计划

| 任务 | 验收方式 | 验收时间 |
|------|---------|----------|
| Task 1.1 | 代码审查 + 编译 | 2026-06-27 |
| Task 1.2 | 代码审查 + 编译 | 2026-06-27 |
| Task 2.1 | 代码审查 + 编译 | 2026-06-27 |
| Task 3.1 | 单元测试（hvigorw test） | 2026-06-27 |
| Task 3.2 | UI 自动化测试（hdc + 模拟器） | 2026-06-27 |

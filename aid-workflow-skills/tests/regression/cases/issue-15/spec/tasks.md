# 历史日期分组 — 开发任务

> AID IMPLEMENTING step2-3 产出 · TDD 节奏
> 基础: `delta-design.md` §3.5 + §3.6
>
> **注**: 本次提交**不**包含 `capabilities.json` 变更。`capabilities.json` 由 `aid-init` 维护 (PR #14), 关联 commit `5215449 fix(aid-init): update capabilities.json to point to main repo`, 与本 issue 功能无关。本 PR 范围 = `HistoryGroup.ets` + UI 接入 + 测试。

## 任务概述

- **功能名称**：历史列表按日期分组 (今天/昨天/更早)
- **变更类型**：requirement-add
- **关联特性**：feat-history-grouping
- **开发阶段**：APPLYING 前置规划
- **预计任务数**：6 (含 TDD 拆分)
- **re-dispatch**: 2026-06-16 补 2 个 it 块 (TC-10/11), 实际 11 个 it() 块; 含闭区间注释; 详见 apply-report §0
- **ui_test.available**: ✅ true → Task 5.3 强制 UI 自动化测试

## 任务列表

### 阶段 1：纯函数模块 (TDD)

#### Task 1.1: [RED] 写 `HistoryGroup.test.ets` 失败用例
**描述**：先写 7 个单元测试,期望失败 (模块尚未实现)。每个用例对应一个边界场景。
**涉及文件**：
- `entry/src/test/ets/history/HistoryGroup.test.ets` (新建)
**依赖任务**：无
**验收标准**：
- [ ] 包含 7 个测试用例:
  - TC-01: 空数组 → 3 个空段
  - TC-02: 全部今天 (3 条) → 仅今天段有数据
  - TC-03: 全部昨天 (2 条) → 仅昨天段有数据
  - TC-04: 全部更早 (5 条) → 仅更早段有数据
  - TC-05: 跨三天混合 → 三段均有数据
  - TC-06: 边界 00:00:00 → 跨日正确分组
  - TC-07: 段内顺序保持 newest-first
- [ ] 用 hypium `describe` + `it` 结构
- [ ] 编译通过 (有 import 报错可以,但 .test.ets 不能导致整个 build 失败)
- [ ] 跑测试应报"module not found"或类似失败

#### Task 1.2: [GREEN] 实现 `HistoryGroup.ets` 让测试通过
**描述**：按 delta-design.md §3.5.6 + §3.5.8 实现纯函数模块。
**涉及文件**：
- `entry/src/main/ets/history/HistoryGroup.ets` (新建)
**依赖任务**：Task 1.1
**验收标准**：
- [ ] 导出 `HistoryGroupKey` 枚举 (TODAY/YESTERDAY/EARLIER)
- [ ] 导出 `HistorySection` interface (key/title/items)
- [ ] 导出 `groupHistoryByDate(items, now)` 纯函数
- [ ] 导出 `startOfLocalDay(d)` 工具函数
- [ ] 跑 `hvigorw --no-daemon test` → 7 个用例全部通过
- [ ] 测试输出包含 "Tests: 7 passed"

#### Task 1.3: [REFACTOR] 边界场景加固 + 鲁棒性
**描述**：在已有 GREEN 用例基础上,补 2 个 nice-to-have 测试,并在生产代码加 defensive null check。
**涉及文件**：
- `entry/src/main/ets/history/HistoryGroup.ets` (修改)
- `entry/src/test/ets/history/HistoryGroup.test.ets` (修改)
**依赖任务**：Task 1.2
**验收标准**：
- [ ] 新增 TC-08: `items=null` → 返回 3 段均空 (不抛异常)
- [ ] 新增 TC-09: `items=undefined` → 同上
- [ ] 生产代码 `groupHistoryByDate` 首行加 `if (!items) return [...]` 守卫
- [ ] 跑测试 → 9 个用例全部通过

### 阶段 2：UI 集成 (TDD 风格 — 集成测试)

#### Task 2.1: [INTEGRATE] 接入 CalculatorPage.HistoryPanel
**描述**：修改 CalculatorPage.ets 集成 HistoryGroup,渲染三段分组列表。
**涉及文件**：
- `entry/src/main/ets/pages/CalculatorPage.ets` (修改 lines 9, 441-479)
**依赖任务**：Task 1.3
**验收标准**：
- [ ] 新增 import `groupHistoryByDate, HistorySection, HistoryGroupKey`
- [ ] 新增 `getHistorySections()` 方法
- [ ] HistoryPanel @Builder 改为遍历 sections
- [ ] 新增 `SectionHeader` @Builder
- [ ] 空段不渲染标题
- [ ] 滑删/点击行为不变 (代码逻辑保持)
- [ ] ArkTS 编译通过 (`hvigorw --no-daemon assembleHap --dry-run` 或 hvigorw build)

### 阶段 3：单元测试验证

#### Task 3.1: 跑全量单元测试
**描述**：执行 `hvigorw --no-daemon test`,确保 HistoryGroup 9 用例通过,且不影响现有 Expression.test.ets。
**涉及文件**：无 (验证)
**依赖任务**：Task 2.1
**验收标准**：
- [ ] 退出码 0
- [ ] stdout 含 "Tests: 9 passed" (HistoryGroup)
- [ ] stdout 含 "Tests: <N> passed" (Expression, N=既有)
- [ ] 测试日志保存到 `apply-report.md`

### 阶段 5：UI 自动化测试 (强制 — capabilities.json 显示 ui_test.available=true)

#### Task 5.3: UI 自动化测试 (harmonyos-ui-test)
**描述**：使用 hdc + harmonyos-ui-test skill 在模拟器上验证三段分组在真实 HarmonyOS 渲染管线中正确显示。
**涉及文件**：
- 测试脚本: `ui-tests/run_tests.py`
- 截图: `ui-tests/screenshot/`
- 结果: `ui-tests/results.json`
- 解析工具: `ui-tests/parse_ui.py`
**依赖任务**：Task 3.1
**验收标准**：
- [ ] `hdc list targets` 有输出 (设备已连接)
- [ ] 应用已安装 (`hdc install -r` 成功)
- [ ] 应用已启动 (`aa start -b com.darkempire78.opencalculator -a EntryAbility` 成功)
- [ ] 注入测试数据: 通过 preferences 或多次等号操作构造今天/昨天/更早三条记录
- [ ] 打开历史面板 → 三个标题 "今天" / "昨天" / "更早" 都在 uiautomator dump 中可见
- [ ] 截图存档到 `ui-tests/screenshot/history-grouped.png`
- [ ] `results.json` 包含每个 AC 的 pass/fail 状态
- [ ] **TDD**: ✅ 测试在生产代码完成 (Task 2.1) 之后跑 → 真实验证 AC
**禁止**: ⏭️ Deferred (capabilities.json 明确 ui_test.available=true 且模拟器 running)

### 阶段 6：报告 + Commit

#### Task 6.1: 产出 `apply-report.md`
**描述**：记录测试日志、截图引用、commit 信息。
**涉及文件**：
- `apply-report.md` (新建)
**依赖任务**：Task 5.3
**验收标准**:
- [ ] 含单元测试日志 (hvigorw test 完整输出)
- [ ] 含 UI 测试截图引用 (`ui-tests/screenshot/history-grouped.png`)
- [ ] 含 uiautomator dump 文本 (三个标题可见)
- [ ] 含 commit SHA (Task 6.2 完成后回填)
- [ ] 含 `Signed-off-by:` 行验证 (铁律 7)

#### Task 6.2: `git commit -s` (满足铁律 7)
**描述**:提交所有改动,带 Signed-off-by。
**涉及文件**: git staging
**依赖任务**: Task 6.1
**验收标准**:
- [ ] `git status` 干净 (除 specs/initialized.flag 外)
- [ ] 提交信息含 `feat(history): 按日期分组 (今天/昨天/更早)`
- [ ] 含 `Signed-off-by: Claude <noreply@anthropic.com>` (或用户实际邮箱)
- [ ] `git log --pretty=fuller -1` 显示 Signed-off-by

## 开发顺序

```
Task 1.1 (RED) → Task 1.2 (GREEN) → Task 1.3 (REFACTOR)
       ↓
Task 2.1 (UI INTEGRATE)
       ↓
Task 3.1 (全量单元测试)
       ↓
Task 5.3 (UI 自动化测试 - 强制)
       ↓
Task 6.1 (apply-report) → Task 6.2 (commit -s)
       ↓
完成
```

## 验收计划

| 任务 | 验收方式 | 备注 |
|------|---------|------|
| Task 1.1 | `hvigorw test` 失败日志 | RED 状态证明 |
| Task 1.2 | `hvigorw test` 7 passed | GREEN 状态证明 |
| Task 1.3 | `hvigorw test` 9 passed | REFACTOR 完成 |
| Task 2.1 | `hvigorw build` 0 error | 集成编译通过 |
| Task 3.1 | 全量测试 0 失败 | 不影响现有用例 |
| Task 5.3 | harmonyos-ui-test 三段可见 | 真实渲染验证 |
| Task 6.2 | `git log --pretty=fuller` 显示 Signed-off-by | 铁律 7 |

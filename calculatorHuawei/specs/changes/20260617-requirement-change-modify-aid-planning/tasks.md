# Tasks — 历史搜索框 (Issue #24)

> AID IMPLEMENTING step2-3 产出 · 开发任务分解
> 关联: proposal.md / delta-spec.md / delta-design.md / design-review.md
> TDD 模式: RED → GREEN → REFACTOR

## 1. 任务概述

- **功能名称**: 历史搜索框
- **变更类型**: requirement-change (实质: 新增功能 View 增量)
- **关联特性**: feat-history-search (#24)
- **开发阶段**: 增量开发 (依赖 #15 groupHistoryByDate)
- **预计任务数**: 7

## 2. 任务列表

### 阶段 1：基础设施 (TDD RED)

#### Task 1.1: 写 HistorySearch 单元测试 (RED)
- **描述**: 在 `entry/src/test/ets/history/HistorySearch.test.ets` 写 hypium 测试用例,覆盖 filterHistoryByQuery 的所有契约。**先写测试,让它们失败** (因为 HistorySearch.ets 还不存在)。
- **涉及文件**:
  - `opencalc/entry/src/test/ets/history/HistorySearch.test.ets` (新)
- **依赖任务**: 无
- **验收标准**:
  - 测试文件存在且导入 `filterHistoryByQuery` (会编译失败 → RED)
  - 至少 6 个测试用例:
    - TC-01: 空 query → 返回原 items
    - TC-02: query="12" → 匹配 expression 或 result 含 "12"
    - TC-03: query="SIN" (大写) → 匹配 "sin" (大小写不敏感)
    - TC-04: query="xyz" (无匹配) → 返回 []
    - TC-05: expression 含特殊字符 (π, e) → 正常匹配
    - TC-06: result 含数字/逗号 → 正常匹配
    - TC-07: query="   " (全空格) → trim 后视为空, 透传
- **TDD**: [x] RED (测试在生产代码之前写)
- **状态**: 第一个任务,运行 `hvigorw test` 应失败 (找不到模块)

#### Task 1.2: 创建 history 目录占位 (新模块骨架)
- **描述**: 创建 `entry/src/main/ets/history/HistorySearch.ets` 骨架文件,只声明 `filterHistoryByQuery` 函数签名,不实现 (或实现空 `return []`),让 Task 1.1 的测试能编译。
- **涉及文件**:
  - `opencalc/entry/src/main/ets/history/HistorySearch.ets` (新)
- **依赖任务**: Task 1.1
- **验收标准**:
  - 文件存在,导出 `filterHistoryByQuery` 函数
  - 函数签名: `function filterHistoryByQuery(items: HistoryItem[] | null | undefined, query: string): HistoryItem[]`
  - 返回 `[]` (占位,让测试可编译运行,部分测试会失败)
- **TDD**: [x] RED (骨架,让 RED 阶段可见)

### 阶段 2：核心功能 (TDD GREEN)

#### Task 2.1: 实现 filterHistoryByQuery (GREEN)
- **描述**: 实现 `filterHistoryByQuery` 纯函数。规则: query.trim().toLowerCase() 后空 → 返回原 items;否则遍历 items 匹配 expression 或 result 的 toLowerCase().includes(q)。
- **涉及文件**:
  - `opencalc/entry/src/main/ets/history/HistorySearch.ets` (改)
- **依赖任务**: Task 1.2
- **验收标准**:
  - TC-01 ~ TC-07 全部通过
  - 不修改入参 items
  - 空 items / null / undefined → 返回 []
  - 无异常抛出
- **TDD**: [x] GREEN
- **验证命令**: `cd opencalc && hvigorw --no-daemon test`

#### Task 2.2: CalculatorPage 集成 - 状态 + 数据流
- **描述**: 修改 `pages/CalculatorPage.ets`:
  1. 新增 `@State searchQuery: string = ''`
  2. 修改 `getHistorySections()` → 先 filter 再 group
  3. 关闭面板时清空 searchQuery
- **涉及文件**:
  - `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (改)
- **依赖任务**: Task 2.1
- **验收标准**:
  - 编译通过
  - 空 query 行为与 #15 完全一致 (HistoryGroup.test.ets 全绿)
- **TDD**: [ ] (不涉及新单测, 由 UI 测试覆盖)

#### Task 2.3: CalculatorPage 集成 - SearchBox 子组件
- **描述**: 在 `HistoryPanel()` 内,手柄下方、List 上方插入 `@Builder SearchBox()`:
  - TextInput (placeholder='搜索算式或结果', text=this.searchQuery, onChange → searchQuery)
  - ✕ 按钮 (仅 searchQuery.length > 0 时显示, onClick → searchQuery='')
  - 背景色 getPanelBg, 文字色 getT1, ✕ 色 getT2
- **涉及文件**:
  - `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (改)
- **依赖任务**: Task 2.2
- **验收标准**:
  - 编译通过
  - 搜索框渲染 (横屏 + 竖屏)

#### Task 2.4: CalculatorPage 集成 - 无结果占位
- **描述**: 修改 `HistoryPanel()` 渲染逻辑:
  - `history.length === 0` → "暂无计算记录" (不变)
  - `searchQuery.length > 0 && sections.every(empty)` → "无匹配记录"
  - 否则 → List (不变)
- **涉及文件**:
  - `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (改)
- **依赖任务**: Task 2.3
- **验收标准**:
  - 无匹配时显示"无匹配记录"
  - 有匹配时正常显示 List + 分组

### 阶段 3：验证 (TDD REFACTOR + 集成)

#### Task 3.1: 单元测试全部通过
- **描述**: 运行 `hvigorw --no-daemon test`,验证:
  - HistorySearch.test.ets 7/7 通过
  - HistoryGroup.test.ets (回归) 全绿
  - 其他测试不受影响
- **涉及文件**: 无
- **依赖任务**: Task 2.4
- **验收标准**:
  - 测试输出含 "Test results: ok"
  - 无 FAIL
- **TDD**: [x] REFACTOR (验证)

#### Task 3.2: 编译验证
- **描述**: 运行 `hvigorw --no-daemon assembleHap`,验证编译通过。
- **涉及文件**: 无
- **依赖任务**: Task 3.1
- **验收标准**:
  - 编译成功
  - 产物 HAP 生成
  - 无 ArkTS 编译错误

#### Task 3.3: UI 自动化测试
- **描述**: 使用 hdc + harmonyos-ui-test skill 在模拟器 (127.0.0.1:5555) 上验证 AC_HS_01 ~ AC_HS_10。
- **涉及文件**:
  - `specs/changes/20260617-requirement-change-modify-aid-planning/ui-tests/run_tests.py` (新)
  - `specs/changes/20260617-requirement-change-modify-aid-planning/ui-tests/parse_ui.py` (新)
  - `specs/changes/20260617-requirement-change-modify-aid-planning/ui-tests/screenshot/` (新目录)
  - `specs/changes/20260617-requirement-change-modify-aid-planning/ui-tests/results.json` (新)
- **依赖任务**: Task 3.2
- **验收标准**:
  - hdc list targets 显示 127.0.0.1:5555
  - 应用安装成功 (hdc install -r)
  - 应用启动成功 (aa start)
  - AC_HS_01 ~ AC_HS_10 全部通过 dump UI 树 + 截图验证
  - screenshot/ 包含每步操作截图
  - results.json 包含每个 AC 的 pass/fail 状态
- **TDD**: [x] RED / [x] GREEN / [ ] REFACTOR
- **强制声明**: capabilities.json 显示 `ui_test.available=true`, hdc 已就绪, 模拟器 127.0.0.1:5555, **禁止** 标为 Deferred。

#### Task 3.4: 回归测试 - HistoryGroup 仍通过
- **描述**: 重新运行 HistoryGroup.test.ets,确认 #15 分组功能未被 #24 破坏。
- **涉及文件**: 无
- **依赖任务**: Task 3.3
- **验收标准**:
  - HistoryGroup.test.ets 全绿
  - 空 query 时 groupHistoryByDate 行为不变

## 3. 开发顺序

```
Task 1.1 (RED test)
    ↓
Task 1.2 (skeleton)
    ↓
Task 2.1 (GREEN impl)
    ↓
Task 2.2 (state + data flow)
    ↓
Task 2.3 (SearchBox UI)
    ↓
Task 2.4 (no-result placeholder)
    ↓
Task 3.1 (unit test pass)
    ↓
Task 3.2 (compile)
    ↓
Task 3.3 (UI automation)
    ↓
Task 3.4 (regression)
    ↓
完成 → commit
```

## 4. 验收计划

| 任务 | 验收方式 | 验证命令 |
|------|---------|----------|
| Task 1.1 | 文件检查 + 编译失败 | `hvigorw test` (应报错) |
| Task 1.2 | 文件检查 + 部分测试失败 | `hvigorw test` |
| Task 2.1 | 单元测试全绿 | `hvigorw test` |
| Task 2.2 | 编译通过 | `hvigorw assembleHap` |
| Task 2.3 | 编译通过 | `hvigorw assembleHap` |
| Task 2.4 | 编译通过 + UI dump | `hdc shell uiautomator dump` |
| Task 3.1 | 测试报告 | `hvigorw test` 输出 |
| Task 3.2 | HAP 生成 | `ls opencalc/entry/build/default/outputs/default/opencalc.hap` |
| Task 3.3 | UI 测试 + 截图 | `python ui-tests/run_tests.py` |
| Task 3.4 | 回归测试通过 | `hvigorw test` |

## 5. 风险与依赖

| 风险 | 缓解 |
|------|------|
| 模拟器未运行 | Task 3.3 启动前先 `hdc list targets` 检查 |
| hvigorw 编译慢 | 使用 --no-daemon 避免残留进程 |
| TextInput onChange 性能 | 输入即过滤, n≤100 性能充足, 无需防抖 |
| 搜索框 keyboard 遮挡 | 搜索框固定顶部, List 内容可滚 |

## 6. IMPLEMENTING 阶段完成

- **产出物**: `specs/changes/20260617-requirement-change-modify-aid-planning/tasks.md`
- **任务数**: 7 (1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 3.1+3.2+3.3+3.4)
- **下一步**: 进入 APPLYING 阶段 (aid-applying + tdd-enforcer)

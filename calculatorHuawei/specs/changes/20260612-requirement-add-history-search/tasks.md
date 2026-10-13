# 历史搜索框 — 开发任务

## 任务概述

- **功能名称**: 历史搜索框（子串+大小写不敏感实时过滤）
- **变更类型**: requirement-add
- **关联变更**: specs/changes/20260612-requirement-add-history-search/
- **关联 Spec**: proposal.md / delta-spec.md / info.md / delta-design.md
- **开发阶段**: TDD (RED → GREEN → REFACTOR)
- **预计任务数**: 4
- **目标粒度**: XS-S
- **复杂度**: S（简单）

## 任务列表

### 阶段 1：filterHistory 纯函数（TDD）

#### Task 1.1: 写 12 个 filterHistory 单元测试 (RED)
**描述**: 在 `tests/HistoryFilter.test.mjs` 写 12 个黑盒测试用例（见 delta-design.md §11.2），先不实现 filterHistory
**涉及文件**:
- `specs/changes/20260612-requirement-add-history-search/tests/HistoryFilter.test.mjs`（新增）
- `specs/changes/20260612-requirement-add-history-search/tests/HistoryFilter.port.mjs`（新增，先不实现 filterHistory）
**依赖任务**: 无
**验收标准**:
- 测试文件语法合法
- 跑测试时**如实记录**全部 FAIL（因 filterHistory 不存在）
- 写入 apply-report.md RED 阶段

#### Task 1.2: 实现 filterHistory (GREEN)
**描述**: 在 `tests/HistoryFilter.port.mjs` 中实现 `filterHistory(history, query): HistoryItem[]`
- 子串匹配（query 与 expression 均 toLowerCase + indexOf）
- query.trim() 处理
- 空 query 返回 history 全部
**涉及文件**:
- `specs/changes/20260612-requirement-add-history-search/tests/HistoryFilter.port.mjs`（修改）
**依赖任务**: Task 1.1
**验收标准**:
- 12 个测试用例全部 PASS
- 边界用例：空查询、特殊字符、表情、大小写、空格 trim 全部正确

### 阶段 2：UI 集成

#### Task 2.1: CalculatorPage.HistoryPanel 扩展
**描述**: 修改 `pages/CalculatorPage.ets`：
1. 新增 `@State searchQuery: string = ''`
2. 新增 `get filteredHistory()` 派生 getter（调用 filterHistory）
3. HistoryPanel 顶部新增 SearchInput（TextInput + X 按钮）
4. List 渲染源改用 `this.filteredHistory`
5. 加空状态文案「未找到含 "xxx" 的记录」
6. 加 onSearchChange / onSearchClear 事件处理
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**: Task 1.2
**验收标准**:
- 顶部 SearchInput 可见
- 键入实时过滤
- X 按钮一键清空
- 空状态文案带搜索词
- 现有 onHistoryTap / swipeAction 行为不变
- 编译通过（Node.js 端口不覆盖此 ETS，但保持算法一致）

#### Task 2.2: REFACTOR（可选）
**描述**: 检查 SearchInput 是否有可抽取的公共模式；命名/注释改善
**涉及文件**:
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（可能微调）
**依赖任务**: Task 2.1
**验收标准**:
- 12 个测试仍 PASS
- 无新行为
- 命名/注释改善

### 阶段 3：验证

#### Task 3.1: 全量单元测试
**描述**: 跑 `node --test HistoryFilter.test.mjs` 确认所有用例 PASS
**涉及文件**: 无
**依赖任务**: Task 2.1
**验收标准**:
- 12/12 PASS
- 退出码 0

#### Task 3.2: 手动集成验证
**描述**: 用户在 HarmonyOS 设备/模拟器上验证：
- 打开历史面板
- 看到搜索框
- 键入 "sin" 看到过滤结果
- 点 X 清空
- 看到空状态
- 点击命中项恢复 expression
- 滑动删除仍可用
**涉及文件**:
- `specs/changes/20260612-requirement-add-history-search/ui-tests/screenshot/`（用户截图）
**依赖任务**: Task 3.1
**验收标准**:
- 所有手动 AC 通过
- 截图存档

**原因说明**（必填）：capabilities.json 不存在（.claude/capabilities.json 缺失），无法确认 ui_test.available。环境受限（hvigorw 不可用、无模拟器），采用手动验证。

#### Task 3.3: 产出 apply-report.md
**描述**: 记录 TDD 全过程、贴真实测试输出
**涉及文件**:
- `specs/changes/20260612-requirement-add-history-search/apply-report.md`（新增）
**依赖任务**: Task 3.2
**验收标准**:
- RED / GREEN / 构建 / 测试 4 段齐全
- 每段都有真实命令 + 真实输出

---

## 开发顺序

```
Task 1.1 (RED 测试)
   ↓
Task 1.2 (GREEN 实现)
   ↓
Task 2.1 (UI 集成)
   ↓
Task 2.2 (REFACTOR, 可选)
   ↓
Task 3.1 (单测) → Task 3.2 (手动验证) → Task 3.3 (apply-report)
```

**关键路径**：1.1 → 1.2 → 2.1 → 3.1 → 3.2 → 3.3
**并行机会**：无
**风险点**：Task 2.1 UI 改动可能影响 HistoryPanel 现有渲染（已规避：仅增量，不改 List 内部）

---

## 验收计划

| 任务 | 验收方式 | 验收时间 |
| --- | --- | --- |
| Task 1.1 | 测试输出（FAIL） | 阶段 1 起步 |
| Task 1.2 | 测试输出（PASS） | 阶段 1 完成 |
| Task 2.1 | 代码审查 + 编译 | 阶段 2 完成 |
| Task 3.1 | node --test 退出码 0 | 阶段 3 起步 |
| Task 3.2 | 用户手动 AC | 阶段 3 中段 |
| Task 3.3 | apply-report 完整 | 阶段 3 末 |

---

## 依赖关系图

```
1.1 (RED) → 1.2 (GREEN)
                ↓
            2.1 (UI 集成) → 2.2 (REFACTOR)
                ↓
            3.1 (单测) → 3.2 (手动) → 3.3 (报告)
```

---

> 本文档由 aid-implementing skill 生成。
> 生成时间：2026-06-12

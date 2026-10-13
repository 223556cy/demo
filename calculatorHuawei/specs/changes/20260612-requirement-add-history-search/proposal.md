# Proposal: 历史搜索框

> **Date**: 2026-06-12
> **Type**: requirement-add (新功能)
> **Category**: 历史增强（搜索交互，数据管理）
> **Priority**: ⭐ (P1)
> **Issue**: 计算历史列表上加一个搜索框，能搜之前的算式

---

## 1. 业务背景

OpenCalc 已有历史记录功能（`@ohos.data.preferences` 存储，最多 100 条），用户在 `HistoryPanel` 中可点击历史项恢复 expression。但当历史较长时（接近上限 100 条），查找特定算式非常困难——必须手动滚动浏览。

macOS / iOS Calculator 的"Show History"窗口、Windows Calculator 历史侧栏、Android OpenCalc 3.x 均有搜索/过滤能力。本次新增是标准 UX 增强。

## 2. 目标

| # | 目标 | 验收标准 |
|---|------|----------|
| G1 | 提供一个搜索框 | HistoryPanel 顶部一直显示文本输入框 |
| G2 | 输入即过滤 | 用户键入字符时实时过滤历史列表 |
| G3 | 匹配 expression 字段 | 子串匹配、大小写不敏感 |
| G4 | 空结果有提示 | 搜索无匹配时显示"无匹配记录" |
| G5 | 一键清空 | 搜索框右侧 X 按钮一键清空 |
| G6 | 不影响其他功能 | 现有历史点击恢复、滑动删除仍可用 |

## 3. 非目标 (Non-Goals)

- 不做正则表达式搜索
- 不做按时间/结果排序
- 不做高亮匹配子串
- 不做搜索历史记录

## 4. 范围

### In Scope
- HistoryPanel 顶部增加 SearchInput 组件
- 实时过滤逻辑（@State searchQuery + 派生 filteredHistory）
- 空状态文案
- 清空按钮

### Out of Scope
- 改动 HistoryItem 数据模型
- 改动 PreferencesStore 存储结构
- 改动 calc engine

## 5. 风险与约束

| 风险 | 等级 | 缓解 |
|------|------|------|
| 100 条历史 + 实时过滤性能 | 低 | 100 条数据量很小，每条 substring 检查 O(n*m) < 1ms |
| 搜索框与折叠手势冲突 | 低 | 搜索框在 List 上方独立区域，不影响折叠 |
| 暗色主题下搜索框可读性 | 低 | 复用现有 getT1/getT2 主题色 API |
| 横屏窄空间搜索框挤压历史 | 中 | 搜索框 width: 100% 自适应 |

## 6. 价值与优先级

- **用户感知**：历史 20+ 条时显著提升
- **实现成本**：极低（< 80 行）
- **回归保护**：高（仅 UI 增量）

## 7. 里程碑

| Milestone | 产出 | 估时 |
|-----------|------|------|
| M1 PLANNING | 4 份设计文档 | 已开始 |
| M2 IMPLEMENTING | tasks.md | 紧随 M1 |
| M3 APPLYING | RED + GREEN + REFACTOR + apply-report | 紧随 M2 |

## 8. 关联文档

- `delta-spec.md` — 增量需求规格
- `info.md` — 代码仓上下文
- `delta-design.md` — 系统设计
- `tasks.md` — 任务分解
- `apply-report.md` — 应用报告

---

## 9. 澄清后需求摘要（rq-clarify 产物）

### 已澄清的关键决策
| # | 问题 | 决策 | 来源 |
|---|------|------|------|
| 1 | 搜索范围 | 仅 expression 字段（不匹配 result） | 用户选择 |
| 2 | 匹配方式 | 子串 + 大小写不敏感 | 用户选择 |
| 3 | UI 布局 | 顶部一直可见 | 用户选择 |
| 4 | 空状态 | 显示「无匹配记录」文案（带搜索词） | 用户选择 |

### 待定假设（实现阶段可调整）
- 清空按钮（X）显示在搜索词非空时
- 历史过滤在内存中完成，不重新触发 PreferencesStore 读取

### 功能边界
- **包含**：搜索框输入、实时过滤、清空按钮、空状态文案
- **不包含**：正则、高亮、结果匹配、排序变化

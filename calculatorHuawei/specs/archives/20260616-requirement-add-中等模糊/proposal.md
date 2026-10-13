# Proposal — 历史列表支持按日期分组

> AID PLANNING step2-3 产出 · 自动模式 (claude -p 非交互)

## 1. 原始需求

> **历史列表支持按日期分组，显示"今天""昨天""更早"**
> 类别：历史分组 · ⭐ · 时间分组，信息层级清晰

**来源**：GitHub Issue #15
**类型**：`requirement-add` (新增功能)
**复杂度**：S-M (单一 UI 模块增量，跨 View + Model + 纯函数分组逻辑)
**自动决策理由**：需求标题已明确三段分组 ("今天 / 昨天 / 更早") 与目的 ("信息层级清晰"),无需澄清。

## 2. 需求解析报告 (rq-parse 风格)

### 意图分类
- **类型**：新增功能 (`requirement-add`)
- **一句话**：在历史记录面板中按"今天 / 昨天 / 更早"三段聚合展示计算历史,每段以分组标题分隔。

### 领域映射
- **UI/交互**：HistoryPanel 列表渲染,需插入 ListItem 分组标题 (Section Header)
- **数据管理**：读取已有 HistoryItem.timestamp 字段,不新增数据模型

### 影响层次

| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View (HistoryPanel) | modify | 现有 `ForEach(this.history, ...)` 改为先分组再渲染,组间插入标题 |
| ViewModel (分组逻辑) | new | 新增 `HistoryGroup.ets` 纯函数模块,提供 `groupHistoryByDate(items, now)` |
| Model | extend (复用) | 复用现有 `HistoryItem.timestamp: number` 字段,无新增模型 |

### 关键实体
- **数据实体**：复用 `HistoryItem` (已含 timestamp)
- **页面实体**：CalculatorPage.HistoryPanel
- **新增组件**：HistoryGroup (纯函数 ets 模块,导出 `groupHistoryByDate()` + `HistorySection` 类型)
- **事件实体**：无新增

### 模糊点

| # | 类别 | 描述 | 严重程度 | 自动决策 |
|---|------|------|---------|---------|
| 1 | 边界定义 | "今天" 的边界是 00:00:00 还是滚动 24 小时? | nice-to-have | 用本地时区 00:00:00 (符合 Android 原版 DateUtils 判断,日历感更强) |
| 2 | 分组顺序 | 三段的固定顺序? | nice-to-have | 今天 → 昨天 → 更早 (按时间倒序) |
| 3 | 单组为空 | 只有 1-2 段有时是否隐藏空标题? | important | 空组不渲染标题 (避免"今天"(空) 等视觉噪音) |
| 4 | 跨午夜 | 用户在使用过程中跨过午夜如何处理? | nice-to-have | 不特殊处理 (分组基于渲染瞬间的 now;若需重排可下次迭代) |
| 5 | 更早内部排序 | "更早" 组内是否再按日期细分? | nice-to-have | 不再细分,保持现有插入顺序 (newest-first) |

无 `blocker` 模糊点,可直接进入 spec 设计。

### 复杂度评估
- **等级**：S
- **理由**：单一 UI 组件渲染调整 + 一个纯函数模块;< 150 行代码;不涉及数据模型新增,无架构变更。

## 3. 验收标准

### 功能验收
- [ ] 历史面板中,记录按"今天 / 昨天 / 更早"三段聚合
- [ ] 每段顶部显示中文标题 "今天" / "昨天" / "更早"
- [ ] 仅当某段至少含 1 条记录时才渲染标题
- [ ] 段内仍保持现有 newest-first 排序
- [ ] 滑删/点击/复制行为不变 (回归测试)

### 技术验收
- [ ] 新增 `entry/src/main/ets/history/HistoryGroup.ets` 纯函数模块,导出 `groupHistoryByDate`
- [ ] 单元测试: `entry/src/test/ets/history/HistoryGroup.test.ets`,覆盖空数组/单日/跨日/边界 (00:00:00) / 全部今天 / 全部更早
- [ ] `hvigorw --no-daemon test` 通过
- [ ] `harmonyos-ui-test` 真实截图覆盖: 三个段都含记录的场景
- [ ] commit 包含 `Signed-off-by:` (满足铁律 7)

## 4. 范围外 (Out of Scope)

- 按月份/年份进一步分组 (后续可扩展)
- 时间戳格式本地化显示 (后续可扩展)
- 分组折叠/展开 (非当前需求)

## 5. 风险与缓解

| 风险 | 等级 | 缓解 |
|------|------|------|
| 时区差异导致分组错位 | 低 | 使用本地日历日 (Date.getFullYear/Month/Date),与 Android 原版对齐 |
| 大量历史记录性能 | 低 | 仅遍历一次 items (O(n)),无额外开销 |
| 与现有滑删/点击交互冲突 | 低 | 标题为 ListItem.Group 风格,不可点击;回归测试覆盖 |

## 6. 自动决策日志 (无交互模式记录)

| 问题 | 决策 | 理由 |
|------|------|------|
| 阶段间确认 | 全部自动同意 | dev-01 已授权 "全自动,不允许问问题" |
| 分组边界 | 本地时区 00:00:00 | 与 Android DateUtils 行为一致,日历感明确 |
| 空段处理 | 不渲染标题 | UI 更整洁,避免无意义空标题 |
| 段内排序 | 保持 newest-first | 与现有 HistoryPanel 一致 |

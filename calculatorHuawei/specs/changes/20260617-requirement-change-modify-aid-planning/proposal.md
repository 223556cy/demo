# Proposal — 历史搜索框 (Issue #24)

> AID PLANNING step2-3 产出 · 需求提案
> 工作目录: `D:/huawei/Demo/worktrees/issue-24`
> 变更类型: requirement-change · 名称: modify-aid-planning

## 1. 原始需求

> 计算历史列表上加一个搜索框，能搜之前的算式

## 2. 需求解析 (rq-parse 输出)

### 2.1 意图分类
- **类型**: 新增功能 (本质为 View 增量)
- **类型标签**: requirement-change (用户指定)
- **一句话概括**: 在历史面板顶部加一个搜索输入框,实时按关键字过滤已保存的计算历史

### 2.2 领域映射
- **UI/交互**: 在 HistoryPanel 顶部加 TextInput + 清除按钮,过滤 List 渲染
- **数据管理**: 无 (过滤是内存操作,不改动 PreferencesStore 持久化格式)
- **状态管理**: 搜索关键字为组件内 @State,过滤结果为派生值

### 2.3 影响层次

| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | modify | CalculatorPage.ets 的 HistoryPanel 增加 SearchBox 子组件 |
| ViewModel | new | history/HistorySearch.ets 纯函数模块(过滤逻辑) |
| Model | none | 复用 HistoryItem |
| 数据层 | none | 不修改持久化格式 |
| 基础设施 | none | 不引入新依赖 |

### 2.4 关键实体
- **数据实体**: 复用 `HistoryItem` (id / expression / result / timestamp)
- **页面实体**: `HistoryPanel.SearchBox()`(新) — 搜索输入框 + 清除按钮
- **接口实体**: `filterHistoryByQuery(items, query): HistoryItem[]`(新) — 纯函数
- **事件实体**: 用户输入 → 触发过滤 → List 重渲染

### 2.5 模糊点列表(已自动决策)

| # | 类别 | 描述 | 严重程度 | 自动决策 |
|---|------|------|---------|---------|
| 1 | 行为模糊 | 搜索什么字段? expression / result / 两者? | important | **两者** (用户说"算式",但 result 也是算式结果,一并搜) |
| 2 | 行为模糊 | 实时过滤还是提交过滤? | nice-to-have | **实时** (输入即过滤,无防抖) |
| 3 | 行为模糊 | 大小写敏感? | nice-to-have | **不敏感** (小写后 contains) |
| 4 | 交互模糊 | 有清除按钮吗? | nice-to-have | **有** (右侧 ✕ 图标) |
| 5 | 交互模糊 | 无结果时显示什么? | nice-to-have | **"无匹配记录"** (居中灰色字) |
| 6 | 范围模糊 | 搜索时是否仍按日期分组? | important | **是** (保留 #15 分组结构,段内按过滤结果渲染) |
| 7 | 范围模糊 | 空查询时是否还原所有历史? | important | **是** (空字符串 → 不过滤) |

无 blocker 级模糊点,跳过 rq-clarify。

### 2.6 复杂度评估
- **等级**: S (简单)
- **理由**:
  - 单个 View 子组件 + 单个纯函数模块
  - 1-2 个文件改动
  - 无新数据模型
  - 无架构变更
  - 无接口变更
  - 与 #15 分组可叠加(分组模块不变,在其结果上再过滤)

## 3. 风险与约束

| 风险 | 缓解 |
|------|------|
| 过滤逻辑放页面层会污染 CalculatorPage | 抽到 history/HistorySearch.ets 纯函数模块(对齐 #15 风格) |
| 输入框抢焦点影响 List 滚动 | 输入框 focus/blur 事件不阻止 List 滚动;搜索时 List 内容区不变 |
| 横屏布局狭窄 | 搜索框宽度 = 100% - 24px padding |
| 输入框导致键盘弹起遮挡历史 | 搜索框放 HistoryPanel 顶部,内容区自动滚动 |

## 4. 验收要点

- [ ] 历史面板顶部出现搜索框(空查询时显示提示"搜索算式或结果")
- [ ] 输入"12"时,只显示 expression 或 result 包含"12"的历史项
- [ ] 大小写不敏感(输入"sin"匹配"SIN(30)")
- [ ] 输入框右侧有 ✕ 清除按钮(有内容时才显示)
- [ ] 点击 ✕ 清空输入,显示全部历史
- [ ] 无匹配时显示"无匹配记录"占位
- [ ] 过滤后仍按"今天/昨天/更早"分组
- [ ] 横竖屏搜索框均可用
- [ ] 主题色(浅色/暗色/AMOLED)兼容

## 5. 决策记录

- 阶段间确认: 自动同意(用户授权 dev-01)
- 搜索范围: expression + result(大小写不敏感)
- 实时性: 实时过滤
- 清除按钮: 有
- 无结果状态: "无匹配记录"
- 跳过: rq-clarify(无 blocker 模糊点)
- 跳过: new-arch.md(无架构变更)

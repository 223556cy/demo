# 历史搜索框 — 代码仓理解

## 基本信息

- **需求类别**：新增功能（New Requirement）
- **需求名称**：history-search（历史搜索框）
- **分析时间**：2026-06-12
- **分析范围**：CalculatorPage.HistoryPanel、HistoryItem 模型

## 环境能力（来自 .claude/capabilities.json）
- 项目类型: 未知（capabilities.json 缺失）
- 平台: HarmonyOS
- 编译命令: hvigorw（当前环境不可用）
- 单元测试命令: Node.js `node:test` 端口模式（基线已建立）
- UI 测试能力: ❌ 不可用
- 模拟器列表: 空
- bundleName: opencalc

## 架构分析

### 模块结构
```
entry/src/main/ets/
├── pages/
│   └── CalculatorPage.ets        ← @Entry（含 HistoryPanel @Builder）
├── model/
│   └── Models.ets                ← HistoryItem { id, expression, result, timestamp }
└── preferences/
    └── PreferencesStore.ets      ← getHistory/setHistory (JSON 数组，最大 100 条)
```

### 关键依赖
- HistoryPanel 在 `CalculatorPage.build()` 中根据 `this.showHistory` 条件渲染
- 数据流：`onEquals()` 写入 `this.history[0]`（最新在前）→ `PreferencesStore.setHistory`

## 接口/契约识别

### 关键接口
- `HistoryItem { id, expression, result, timestamp }` —— 已定义
- `onHistoryTap(item)` —— 选中后恢复 expression 到输入框
- `onHistoryDelete(item)` —— 滑动删除

### 重要约束
- 搜索在内存中完成（100 条上限，无 IO 压力）
- 必须保持 List 的 swipeAction 滑动删除功能

## 公共组件或函数识别

### 可复用
- `TextInput` 组件 —— ArkTS 原生
- `getT1/getT2/getBtnBg/getPanelBg` 主题色 API
- `HistoryItem.expression` 字段已包含用户输入（可匹配）

### 不能直接复用
- 现有 `ForEach(this.history, ...)` —— 需改为 `ForEach(this.filteredHistory, ...)`

## 影响范围分析

### 需要修改的模块
| 文件 | 改动 | 影响范围 |
| --- | --- | --- |
| `pages/CalculatorPage.ets` | +@State searchQuery、+filterHistory()、HistoryPanel 顶部加 SearchInput、列表源改 filteredHistory | 主页 |

### 不影响
- `model/Models.ets`
- `preferences/PreferencesStore.ets`
- `calculator/*`

## 现有代码分析

### `HistoryPanel` @Builder（行 441-474）
- 现有结构：手柄 → 条件渲染（空态 vs List）
- 列表源：`this.history`
- 滑动删除：`swipeAction({ end: { builder: DelBtn } })`
- 点击：`onClick → onHistoryTap`

### `history` 数据流
- `loadHistory()` 从 Preferences 读取
- `onEquals()` 写入最新到 `this.history[0]`

## 风险识别

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| 100 条历史 + 实时过滤性能 | 低 | 内存 O(n*m) < 1ms |
| 搜索框与折叠手势冲突 | 低 | 搜索框在 List 上方独立区域 |
| 暗色主题可读性 | 低 | 复用主题色 API |
| 横屏窄空间 | 中 | 搜索框 width: 100% 自适应 |

## 测试验证策略

### 单元测试（filterHistory 纯函数）
- 子串匹配
- 大小写不敏感
- 空查询返回全部
- 特殊字符（+、×、÷）字面量匹配
- 前后空格 trim
- 表情符号降级

### UI 测试（手动）
- 顶部搜索框可见
- 键入实时过滤
- X 按钮清空
- 空状态文案
- 点击命中项恢复 expression
- 滑动删除仍可用

### 回归测试
- 现有历史功能 100% 正常

## 监控运维支持

### 配置项
- 无新增配置

### 关键日志点
- 无（纯 UI 内存操作）

## 关键发现

### 可复用组件或函数
- `TextInput` 原生组件
- 主题色 API

### 风险提示
- 搜索过滤是同步操作，100 条 history 单次过滤 < 1ms
- 不需要 Preferences 重新读取

### 建议事项
- **强烈建议**：filterHistory 写成 `@Builder` 之外的纯函数，便于单测
- **建议**：SearchInput placeholder 用"搜索历史算式"
- **建议**：X 按钮仅在 searchQuery 非空时显示

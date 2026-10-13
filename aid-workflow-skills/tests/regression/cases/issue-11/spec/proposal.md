# 需求提案 — Issue #11 实时预览功能

## 1. 原始需求

> 在输入表达式的时候，等号上面实时显示预览结果，不用按等号 | 实时预览 | ⭐⭐ | "所见即所得"，科技感强

**Issue 来源**：Issue #11
**类型**：新增功能（Design/Development - New Requirement）
**变更名称**：realtime-preview

## 2. 需求理解

### 2.1 意图分类
- **类型**：新增功能
- **一句话概括**：在用户输入表达式过程中，等号按钮上方实时显示当前表达式的计算结果预览，无需按等号即可看到结果。

### 2.2 领域映射
- **UI/交互**：在 CalculatorPage DisplayPanel 中新增预览行（位于 result 与 等号按钮之间）
- **状态管理**：实时计算的状态需要在 expression 变化时同步更新
- **计算引擎**：复用现有 CalcEngine.evaluate，但需要降级处理不完整表达式

### 2.3 影响层次
| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | modify | CalculatorPage.ets: DisplayPanel 新增 preview 文本；ButtonGrid 在竖屏下顶部增加 preview 区域 |
| ViewModel | extend | CalculatorPage 新增 onExpressionChange() / computePreview() 方法；新增 @State preview: string |
| Model | 无 | 不需新增模型，复用 Expression + CalcEngine + NumberFormatter |
| 数据层 | 无 | 无持久化需求 |
| 基础设施 | 无 | 无新依赖 |

### 2.4 关键实体
- **数据实体**：无（复用 HistoryItem? 不需要）
- **页面实体**：CalculatorPage.DisplayPanel（显示屏）
- **接口实体**：CalcEngine.evaluate(clean, radians)、Expression.getCleanExpression(...)（已存在）
- **事件实体**：expression 变化 → computePreview 触发；onEquals 触发 → preview 与 result 一致

### 2.5 模糊点（已在 step3 澄清）
- **触发时机**（blocker → 决定）：每次 expression 变化后立即计算（onChange / @Watch）
- **降级处理**（important → 决定）：当 expression 为空/不完整/语法错误时显示空字符串或占位符
- **样式**（important → 决定）：与 result 样式区分，灰度更轻、字号更小、右对齐
- **等号取消预览**（nice-to-have → 决定）：按等号后 preview 与 result 内容相同（保持一致即可）

### 2.6 复杂度评估
- **等级**：S（简单）
- **理由**：单页面 UI 增强 + 1 个 @State 字段 + 1 个计算函数，< 100 行代码改动
- **影响模块数**：1（CalculatorPage.ets），1 个调用方（Expression/CalcEngine 已存在）
- **架构变更**：否
- **数据模型变更**：否

## 3. 验收标准

### 3.1 功能验收
- [ ] 用户输入合法表达式（如 `1+2`）时，等号上方实时显示 `3`
- [ ] 用户输入不完整表达式（如 `1+`）时，预览区为空/占位符
- [ ] 用户输入语法错误表达式（如 `1++`）时，预览区为空
- [ ] 用户输入包含函数的表达式（如 `sin(0)`）时，预览区显示 `0`
- [ ] 用户清除输入（AC）时，预览区清空
- [ ] 按等号后，预览区与主结果区内容一致
- [ ] 横屏和竖屏下，预览区都正确显示

### 3.2 性能验收
- [ ] 每次按键后预览更新延迟 < 100ms
- [ ] 不阻塞主线程（同步计算，表达式长度 < 50 字符时无明显卡顿）

### 3.3 兼容性验收
- [ ] 不破坏现有"按等号"流程
- [ ] 不影响历史记录功能
- [ ] 不影响偏好设置
- [ ] 错误状态处理保持一致

## 4. 范围边界

### 范围内
- 在 DisplayPanel 顶部增加 preview 行
- 在 expression 变化时实时计算并显示
- 处理不完整/错误表达式的降级
- 竖屏和横屏都支持
- 单元测试覆盖 computePreview 函数

### 范围外
- 复杂表达式解析中间态的智能提示（如自动补全括号）
- 历史记录的实时更新（仍由 onEquals 触发）
- 实时预览的颜色/动画定制（保持简单样式）

## 5. 相关文件

| 文件 | 角色 | 预计改动 |
|------|------|----------|
| `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` | 主页面 | 新增 preview 状态 + computePreview 方法 + UI 行 |
| `opencalc/entry/src/main/ets/calculator/Expression.ets` | 表达式预处理 | 复用 getCleanExpression |
| `opencalc/entry/src/main/ets/calculator/Calculator.ets` | 计算引擎 | 复用 evaluate |
| `opencalc/entry/src/test/ets/...` | 单元测试 | 新增 computePreview 测试用例 |

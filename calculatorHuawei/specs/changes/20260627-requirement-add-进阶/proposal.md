# 需求提案 — Issue #27

## 原始需求
> 计算结果支持小数和分数两种显示，自由切换。学生用户强需求。需要在计算器结果区域支持小数和分数两种显示模式的自由切换。

## 意图分类
- **类型**：新增功能
- **一句话概括**：在计算器结果展示区增加小数/分数显示模式切换能力，满足学生群体对分数表达的需求。

## 领域映射
- UI/交互：结果展示区需新增切换按钮/交互入口
- 状态管理：显示模式需要全局状态管理并持久化
- 数据管理：分数转换算法与格式化输出

## 影响层次

| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | modify | CalculatorPage 结果展示区新增切换按钮与模式状态联动 |
| ViewModel | modify | 新增 displayMode 状态、toggle 逻辑、formatResultForDisplay 格式化路由 |
| Model | extend | 新增 DisplayMode 枚举（DECIMAL / FRACTION） |
| 数据层 | extend | PreferencesStore 新增 getResultDisplayMode / setResultDisplayMode |
| 基础设施 | new | 新增 FractionUtil 工具类（浮点转最简分数） |

## 关键实体
- 数据实体：`DisplayMode` 枚举、`CalculatorPreferences` 扩展字段
- 页面实体：`CalculatorPage` 结果展示区（`DisplayPanel`）
- 接口实体：`FractionUtil.toFraction()`、`PreferencesStore` 显示模式读写接口
- 事件实体：用户点击切换按钮事件、`onExpressionChange` 后重新格式化事件

## 模糊点

| # | 类别 | 描述 | 严重程度 |
|---|------|------|---------|
| 1 | 行为模糊 | 切换模式后是否立即作用于当前结果还是仅下次计算？ | important |
| 2 | 行为模糊 | 分数显示的最大分母限制是多少？（精度与可读性平衡） | important |
| 3 | 交互模糊 | 切换按钮的位置与视觉样式（是否常驻、是否占用额外空间） | nice-to-have |

> 注：经代码仓调研，上述模糊点已在现有实现中明确——切换立即作用于当前结果；最大分母限制通过 `1e15` 缩放+GCD实现；切换按钮位于结果文本右上角小图标。

## 复杂度评估
- **等级**：M（中等）
- **理由**：涉及 UI 交互、状态管理、持久化、分数算法四个小模块，但改动量可控（~100 行），无架构变更。

## 备注
- 代码仓已存在初步实现，本提案用于补全 AID 规划产物。

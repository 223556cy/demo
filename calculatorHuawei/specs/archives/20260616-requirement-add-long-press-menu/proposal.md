# Proposal — Issue #16 长按弹出选择菜单

> aid-workflow 20260616-requirement-add-long-press-menu
> 基于 rq-parse 结构化分析
> 基线:opencalc/entry/src/main/ets/pages/CalculatorPage.ets

## 原始需求
> 给按钮加上长按功能，比如长按 sin 弹出 arcsin/arccos/arctan 选择 | 手势增强 | ⭐⭐ | 按钮弹出菜单，交互丰富

## 意图分类
- **类型**: 新增功能 (requirement-add)
- **一句话概括**: 给科学函数按钮加上长按手势,长按时弹出候选函数列表（如长按 sin 弹出 arcsin/arccos/arctan），点击候选后插入对应函数到表达式;短按维持原行为。

## 领域映射
- UI/交互: 按钮长按手势检测、弹窗菜单 UI
- 状态管理: 弹窗可见状态、长按源按钮记录、候选选项状态

## 影响层次

| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | modify | `CalculatorPage.ets` 中 `BtnFunc` 按钮增加 `.gesture(LongPressGesture().onAction(...))`, 新增 `LongPressMenuPanel` @Builder |
| ViewModel | new | 新建 `LongPressMenu.ets`(纯逻辑模型)：长按映射表 + 候选列表解析器 |
| Model | new | 新建 `LongPressMenu.port.mjs`(1:1 端口便于 Node.js TDD 测试) |

## 关键实体
- **数据实体**:
  - `LongPressEntry`: `{ label: string, candidates: string[] }` — 一个按钮的长按候选
  - `LONG_PRESS_REGISTRY: Map<string, string[]>` — 按钮标签 → 候选列表 静态映射表
- **页面实体**: `LongPressMenuPanel()` @Builder — 半透明遮罩 + 居中候选菜单
- **接口实体**: 无外部接口
- **事件实体**:
  - `onLongPress(label: string)` — 长按触发,打开菜单
  - `onCandidateTap(candidate: string)` — 选择候选,插入表达式并关闭菜单

## 模糊点

| # | 类别 | 描述 | 严重程度 | 处理 |
|---|------|------|---------|------|
| 1 | 行为模糊 | 长按 vs 短按的判定时机？HarmonyOS `LongPressGesture` 默认 500ms | nice-to-have | 采用系统默认 500ms,不暴露阈值配置 |
| 2 | 范围模糊 | "未来长按其他按钮可注册更多映射" → 是否需要完整配置系统？ | nice-to-have | 采用**代码内静态映射表**模式 (`LONG_PRESS_REGISTRY`),后续添加只需改一个 Map,无需运行时配置 |
| 3 | 交互模糊 | 菜单关闭方式？点外面关闭？ESC？ | nice-to-have | 默认**点外面关闭**（半透明全屏遮罩),简化首版 |
| 4 | 行为模糊 | 长按时是否需要视觉反馈（如按钮变色)? | nice-to-have | **不加**视觉反馈,避免和短按点击视觉冲突；菜单弹出本身即反馈 |
| 5 | 行为模糊 | 候选菜单是中文还是英文显示? | nice-to-have | **保持中文功能名**(arcsin/arccos/arctan 等沿用按钮文本风格) |

无 blocker/important 级别模糊点,需求足够清晰。

## 复杂度评估
- **等级**: S (简单) — 单一 UI/交互领域,2 个文件改动
- **理由**: 仅影响 CalculatorPage.ets (View) + 新增 LongPressMenu.ets 逻辑,纯前端,不涉及数据模型/网络/持久化

## 备注
- 需求清晰,可以直接生成 delta-spec.md
- 复用 issue #11 的"纯逻辑类 + port.mjs"模式,实现 Node.js 离线 TDD
- 长按 `sin` 弹菜单的设计属于"渐进式增强"——短按 sin 仍然有效,长按只是多一个入口
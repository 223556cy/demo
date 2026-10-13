# 需求提案 — Issue #29: 竖屏手势滑动切换三种键盘模式

## 1. 原始需求

> 支持在竖屏时左右滑动切换基础/科学/程序员三种键盘模式 | 手势导航 | ⭐⭐ | 三页滑动，像桌面切换

**Issue 元数据**: 中等模糊, requirement-add, issue #29

## 2. 意图分类

- **类型**：新增功能
- **一句话概括**：在竖屏 CalculatorPage 添加水平滑动手势，使用 Swiper 组件实现三种键盘模式（基础/科学/程序员）的桌面式页面切换。

## 3. 领域映射

- **UI/交互**：使用 `Swiper` 组件 + `PanGesture`/`SwipeGesture` 实现桌面式页面切换动画
- **导航路由**：模式切换从"按钮点击"扩展为"按钮 + 手势"双通道
- **状态管理**：`@State scientific: boolean` 扩展为 `currentMode: KeyboardMode`（基础/科学/程序员三态）

## 4. 影响层次

| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | modify | CalculatorPage.ets: Swiper 包裹键盘布局，添加页面指示器 |
| ViewModel | modify | CalculatorPage.ets: `scientific: boolean` → `currentMode: KeyboardMode` |
| Model | extend | Models.ets: 新增 `KeyboardMode` 枚举 (BASIC/SCIENTIFIC/PROGRAMMER) |
| Model | extend | CalculatorPreferences: 新增 `programmerModeDefault: number` |
| 偏好 | extend | PreferencesStore.ets: 新增程序员模式默认值持久化 |
| Resources | new | string.json: 新增 "程序员" 中文标签 |
| Resources | new | 新增程序员键盘布局字符串数组 (string.json) |

## 5. 关键实体

- **数据实体**：
  - `KeyboardMode` (枚举, NEW): BASIC=0 / SCIENTIFIC=1 / PROGRAMMER=2
  - `CalculatorPreferences.programmerModeDefault` (NEW): 默认程序员模式状态
- **页面实体**：
  - `CalculatorPage.ets`: 整体结构改造，外层加 Swiper
  - 程序员键盘布局 (NEW): 和科学键并列的第二扩展页
- **接口实体**：
  - `PreferencesStore.getProgrammerModeDefault() / setProgrammerModeDefault()` (NEW)
- **事件实体**：
  - 模式切换事件: `onChange` (Swiper index 变化 → 更新 currentMode)
  - 旧事件保留: 模式按钮的 `onClick` 仍可触发 mode 切换

## 6. 模糊点

| # | 类别 | 描述 | 严重程度 | 决策 |
|---|------|------|---------|------|
| 1 | 范围模糊 | 项目当前只有"基础"和"科学"两种模式,程序员模式不存在。issue 提到"程序员"模式,需要从零实现。 | important | **自动决策**: 实现最简版程序员键盘(HEX/DEC/OCT/BIN + AND/OR/NOT/XOR + 位移),对齐 issue 文本需求。 |
| 2 | 行为模糊 | 滑动切换的指示器/动画风格未指定("像桌面切换") | important | **自动决策**: 使用 HarmonyOS `Swiper` 组件 (DotIndicator),禁用纵向循环,横向循环关闭 (3 页固定),切换动画 duration 默认。 |
| 3 | 行为模糊 | 是否保留原"模式切换按钮" | important | **自动决策**: 保留原有按钮点击切换 (在三个 mode 之间循环),与滑动手势并存,按钮 label 跟随当前 mode。 |
| 4 | 行为模糊 | 横屏时是否支持滑动 | nice-to-have | **自动决策**: 横屏布局 (`isLandscape`) 不变,继续只显示科学模式,Swiper 仅竖屏生效 (即隐藏 Swiper 用 Grid/Column)。 |
| 5 | 兼容模糊 | 持久化的旧 `scientificModeDefault` 字段如何处理 | important | **自动决策**: 保留字段语义不变,新增 `programmerModeDefault` 字段,首启动 priority: BASIC < PROGRAMMER < SCIENTIFIC (按 preferences 值)。 |
| 6 | 行为模糊 | 滑动冲突: 输入框 TextArea 已有手势,是否会拦截? | blocker | **自动决策**: Swiper 包裹整个键盘区域,TextArea 在 Swiper 上方独立;键盘区域手势优先级高,文本框的横滑(选中)可能被拦截,可通过 Swiper 的 disableSwipe 区域控制(默认在文本框附近小范围禁用 swipe)。 |

## 7. 复杂度评估

- **等级**：M (中等)
- **理由**：
  - 影响模块数: 4 (CalculatorPage, Models, PreferencesStore, resources)
  - 代码改动: ~200-400 行 (新增程序员键盘 ~100 行 + Swiper 改造 ~100 行 + 模式状态机重构 ~50 行)
  - 数据模型变更: 是 (新增 KeyboardMode 枚举 + preferences 字段)
  - 架构变更: 否 (仍然是单页 + 条件渲染模式)

## 8. 备注

- 用户处于非交互模式,上述模糊点全部按"自动决策"采纳,理由已写入表格。
- 本需求属"中等模糊",最复杂的部分(程序员键盘内容)采取最简实现策略——保证可演示、可测试、可扩展。
- 已确认 capabilities.json 中 ui_test.available=true, APPLYING 阶段需要做 UI 自动化测试。
- 已确认本需求不是 arch-refactor 也不是 platform-migration,不会触发高风险暂停。

## 9. 用户确认策略

- 用户授权: dev-01 已授权 "全自动,不允许问问题"。
- 阶段间确认: 自动同意。
- 高风险点: 全部已检查,无暂停需求。
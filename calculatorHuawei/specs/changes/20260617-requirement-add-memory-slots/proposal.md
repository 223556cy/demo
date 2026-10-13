# 需求提案 — Issue #28 记忆槽 (M1-M6 + MR)

> 由 rq-parse 生成的初始提案（AID 非交互模式自动补全决策，详见 todo.md 决策记录）。

## 原始需求

> 长按数字按钮可以把它存到M1-M6六个记忆槽里，点MR调出来
> 类型: 简单需求 | 名称: memory-slots | 分类: 记忆功能 ⭐

## 意图分类

- **类型**: 新增功能 (`requirement-add`)
- **一句话概括**: 为计算器增加经典六槽记忆功能，长按数字键 1-6 可将当前数值存入对应 M1-M6 槽位，点击 MR（Memory Recall）调出最近一次存入或当前选中槽位的值。

## 领域映射

- **UI/交互**: 数字按钮（0-9）的长按手势识别（LongPressGesture），MR 按钮的点击行为
- **状态管理**: 6 个记忆槽状态的运行时维护；当前显示值与记忆值的合成
- **数据管理**: 持久化（可选）— 跨会话保留记忆值（参见下方模糊点决策）

## 影响层次

| 层次 | 变更类型 | 说明 |
|------|---------|------|
| View | new + modify | 新增 MR 按钮布局；现有数字按钮增加 LongPressGesture 绑定 |
| ViewModel | new + extend | 新增 MemorySlotsStore（@State/@Observed）；扩展 CalculatorViewModel 暴露 saveToSlot/recallFromSlot |
| Model | new | MemorySlot 数据模型（slotIndex: 1-6, value: number, updatedAt: number） |
| 数据层 | new (optional) | 持久化（首版可仅内存态；持久化由模糊点 #4 决策） |

## 关键实体

- **数据实体**:
  - `MemorySlot { slotIndex: 1..6, value: number, updatedAt: number, isEmpty: boolean }`
  - `MemoryState { slots: MemorySlot[6], lastUsedSlotIndex: 1..6 | null }`
- **页面实体**:
  - `CalculatorPage`（主计算页面）— 增加 MR 按钮 + 数字键长按绑定
  - 顶部结果区增加记忆激活指示（M / M1-M6 标签）
- **接口实体**:
  - `MemorySlotsStore` 公开方法：`saveToSlot(idx, value)` / `recallFromSlot(idx)` / `getLastUsed()` / `clear()`
- **事件实体**:
  - `onLongPressDigit(slotIndex)` — 数字键长按时触发存槽
  - `onMRTap()` — MR 按钮点击时触发调出

## 模糊点

| # | 类别 | 描述 | 严重程度 | 自动决策（dev-01 已授权） |
|---|------|------|----------|--------------------------|
| 1 | 行为模糊 | 长按数字键时，存哪个值？当前显示值 / 当前输入流 / 最近一次计算结果？ | important | **当前显示值**（display）— 与经典计算器一致，存用户能直接看到的数 |
| 2 | 交互模糊 | 长按数字键 1-6 — 是按下哪个数字就存到对应 M 槽（长按 1→M1）？还是任意数字键长按都循环/弹出选择？ | important | **按下哪个数字→对应 M 槽**（长按 1→M1, 长按 2→M2, ... 长按 6→M6）— 数字 0/7/8/9 不参与，避免歧义；与"6 个槽"语义最直接 |
| 3 | 交互模糊 | MR 行为 — 调出最后一个使用槽 / 弹菜单让用户选 / 默认调出 M1？ | important | **弹菜单**（ActionSheet / 自定义 BottomSheet）让用户选 M1-M6 任一槽位，空槽显示"—"并禁用；菜单关闭后默认高亮 lastUsedSlotIndex |
| 4 | 数据模糊 | 记忆值是否需要持久化（app 关闭后保留）？ | nice-to-have | **首版仅运行时内存态**，简化交付；持久化作为 future work；这一决策是项目级功能权衡，不构成 blocker |
| 5 | 行为模糊 | 长按时是否覆盖已存在槽位？ | nice-to-have | **直接覆盖** + 短暂 toast 提示"已存入 Mx"；这是经典计算器行为 |
| 6 | 交互模糊 | MR 按钮在所有槽位为空时是否禁用？ | nice-to-have | **是**（视觉灰显 + disabled）— 避免无效操作 |

> 没有 `blocker` 级别模糊点，可以进入 step3 → step4。

## 复杂度评估

- **等级**: **M（中等）**
- **理由**:
  - 涉及 View / ViewModel / Model 三层（UI 长按 + 状态管理 + 数据模型）
  - 涉及 UI/交互 + 状态管理两个领域
  - 需要新增 MemorySlot/MemoryState 模型 + MemorySlotsStore + 数字键长按绑定 + MR 弹菜单
  - 估计代码量 100-200 行（含单元测试），属于"中等"区间

## 备注

- 与既有 `feat-memory` 模块关系：需在 step5 (rq-codebase) 验证当前项目是否已有 memory 相关代码，避免重复造轮子
- Issue 描述虽称"简单需求（⭐）"，但实际涉及长按手势 + 弹菜单 + 状态模型，工作量偏 M 而非 S，但低于 L
- **无安全拦截**（无阶乘/! 关键字）

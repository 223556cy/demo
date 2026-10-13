# 设计审视报告 — Issue #16

> aid-workflow 20260616-requirement-add-long-press-menu
> step9 设计审视

## 1. 完整性评估

### 制品齐全性
- [x] proposal.md ✅
- [x] delta-spec.md ✅
- [x] info.md ✅
- [x] design.md ✅
- [x] todo.md ✅
- [x] design-review.md ✅ (本文档)

**复杂度**: S (简单)
**new-arch.md**: 不需要 (无架构变更,纯 UI 增强)

### 需求覆盖度
- [x] FR-1 长按触发菜单 → design.md §3.5.5 + §8.1
- [x] FR-2 候选菜单显示 → design.md §3.4 + §6.3
- [x] FR-3 点选候选 → design.md §3.5.5 + §3.5.6
- [x] FR-4 点外面关闭 → design.md §3.5.5 + §8.1
- [x] FR-5 短按不变 → design.md §3.5.5 (用例: 短按 sin 不弹菜单)
- [x] FR-6 静态注册表 → design.md §3.5.6 + §3.6
- [x] FR-7 可扩展 → design.md §3.5.6 (注释 + REGISTRY Map)

**覆盖度**: 100%

## 2. 一致性评估

### proposal → delta-spec
- [x] FR-1~FR-7 在 delta-spec.md §2 完整呈现
- [x] 模糊点处理在 delta-spec §4 (FMEA) 中体现
- [x] AC 矩阵 (delta-spec §7) 与 FR 一一对应

### delta-spec → design
- [x] FR-1~FR-7 在 design.md §2 功能清单覆盖
- [x] 接口需求 (delta-spec §5.2) ↔ design.md §3.5.6 (LongPressMenu 类)
- [x] FMEA 消减清单 (delta-spec §4 C1-C5) ↔ design.md 各章节:
  - C1 (500ms 默认) → §1.3 技术栈 + §8.1 手势
  - C2 (菜单状态独立) → §3.5.7 @State 设计
  - C3 (复用 onFunc) → §3.5.5 + §3.5.6 注释
  - C4 (ln 不映射) → §3.5.6 REGISTRY (ln 不在表内) + §3.6.6 端口
  - C5 (Stack 叠层) → §3.5.7 数据流 + §8.2 弹窗决策

### info → design
- [x] 模块结构 (info.md 架构分析) ↔ design.md §3.2 总体架构
- [x] 接口契约 (info.md 接口识别) ↔ design.md §3.5.6
- [x] 风险 (info.md 风险识别) ↔ design.md 各 FMEA 对应章节

## 3. 规范性评估

### 格式规范
- [x] 章节结构 D1-D10 完整
- [x] 表格化数据 (功能清单、规格表)
- [x] PlantUML 图表 (上下文图、类图、数据流)
- [x] 命名规范 (LongPressMenu 类名 / REGISTRY 常量名 / hasCandidates 函数名)

### 命名规范
- [x] ArkTS: PascalCase 类, camelCase 方法, UPPER_SNAKE 常量
- [x] Node.js 端口: 1:1 对应 ArkTS API
- [x] 文件名: `LongPressMenu.ets` / `LongPressMenu.port.mjs` / `LongPressMenu.test.mjs`

### 描述清晰度
- [x] 每个 FR 在 design.md 有对应实现位置
- [x] 用例分析覆盖正常/边界路径
- [x] 错误处理 (getCandidates 未知 label → []) 已明确

## 4. 遗留问题

无遗留问题。所有模糊点已在 proposal.md §"模糊点"中给出处理方案,FMEA 改进措施已固化为需求约束。

## 5. 阶段结论

**PLANNING 阶段完成** ✅
- 制品齐全:proposal.md / delta-spec.md / info.md / design.md / todo.md / design-review.md
- 一致性:proposal ↔ delta-spec ↔ design 三角校验通过
- 复杂度:S (简单),架构无需变更
- 进入下一阶段:IMPLEMENTING (产出 tasks.md)

## 6. 决策记录 (自动授权模式)

| 决策点 | 自动决策 | 理由 |
|--------|---------|------|
| 是否分模块 | 不分模块 | UI 增强,单文件改动 |
| 是否需 new-arch.md | 否 | 无架构变更 |
| 测试策略 | Node.js 端口 + node --test | 与 issue #11/#9 模式一致,无需 hvigorw |
| UI 自动化测试 | 可选(非强制) | 端口单测已覆盖逻辑,UI 自动化作为后续 acceptance |
| ln 长按是否首版支持 | 否 | FMEA C4: 避免半成品体验 |
| 菜单实现方式 | 自定义 @Builder (Stack 遮罩 + Column 菜单) | bindMenu 样式受限,CustomDialog 过重 |
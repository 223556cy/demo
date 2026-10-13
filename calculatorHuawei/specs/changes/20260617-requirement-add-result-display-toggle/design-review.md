# 设计审视报告 - Issue #27 计算结果支持小数和分数两种显示

> 变更目录: `specs/changes/20260617-requirement-add-result-display-toggle/`
> 关联 Issue: #27
> 审视时间: 2026-06-17

## 1. 完整性评估

### 1.1 制品齐全性
- [x] `proposal.md` - 需求提案 ✅
- [x] `delta-spec.md` - 增量规格 ✅
- [x] `info.md` - 代码仓理解 ✅
- [x] `delta-design.md` - 增量设计 ✅
- [x] `todo.md` - 任务进度 ✅
- [x] `design-review.md` - 设计审视报告 ✅（本文件）

**结论**：通过

### 1.2 需求覆盖度
| 需求点 | 覆盖制品 | 状态 |
|--------|---------|------|
| 小数/分数切换 | proposal.md §1, delta-spec.md §3.1, delta-design.md §3.8 | ✅ |
| 分数格式化 (GCD) | delta-spec.md §3.2, delta-design.md §3.5 | ✅ |
| 持久化 | delta-spec.md §3.3, delta-design.md §3.7 | ✅ |
| 错误状态禁用 | delta-spec.md FR-15, delta-design.md §3.8.3 | ✅ |
| 启动恢复 | delta-spec.md FR-11, delta-design.md §3.8.2 | ✅ |
| 历史记录保持小数 | delta-spec.md §1.3 范围说明, delta-design.md §3.8.6 | ✅ |
| FMEA 可靠性分析 | delta-spec.md §4 | ✅ |
| 验收标准 | delta-spec.md §7 | ✅ |

**覆盖度**：100%

## 2. 一致性评估

### 2.1 proposal → delta-spec
- [x] 意图分类一致：requirement-add
- [x] 范围一致：分数/小数显示切换 + 持久化
- [x] 模糊点处理一致：精度策略、横竖屏布局

**结论**：通过

### 2.2 delta-spec → delta-design
- [x] 功能点对应：所有 FR 在 delta-design 中有对应实现设计
- [x] 接口对应：DisplayMode/FractionUtil/PreferencesStore 扩展均在设计文档
- [x] FMEA 措施对应：分母阈值 → delta-design §3.5.8 算法
- [x] 验收标准可测：AC-1~8 均有对应测试路径

**结论**：通过

### 2.3 delta-design 自洽性
- [x] 修改文件清单完整
- [x] 状态变更明确（@State displayMode/lastRawResult）
- [x] UI 改造有具体代码片段
- [x] 时序图覆盖切换流程

**结论**：通过

## 3. 规范性评估

### 3.1 格式规范
- [x] 章节编号完整（D1-D10）
- [x] 表格结构化
- [x] PlantUML 图使用 `@startuml/@enduml`
- [x] 引用现有文件路径准确

### 3.2 命名规范
- [x] `DisplayMode` 枚举 ✅
- [x] `FractionUtil` 工具类 ✅
- [x] `FractionResult` 接口 ✅
- [x] `resultDisplayMode` key 一致 ✅

### 3.3 描述清晰度
- [x] 每个修改点有具体代码示例
- [x] 横屏/竖屏布局有明确规则
- [x] 错误/异常处理有边界条件说明

**结论**：通过

## 4. 关键设计决策

| 决策 | 理由 |
|------|------|
| 缓存 `lastRawResult: number` 而非用 `result` 反解 | result 是格式化后字符串（带千分位），反解会丢精度 |
| 切换按钮用字符 `1/2`/`0.5` 而非图片资源 | 减少 media 资源新增，与现有 emoji 风格一致 |
| 横屏隐藏切换按钮 | 横屏空间紧张，沿用 ToggleRow 的竖屏策略 |
| 历史记录不跟随模式切换 | 避免切换模式时历史区视觉闪烁，符合 FMEA 风险缓解 |
| `maxDenominator = 9999` | 经验值，覆盖学生常见分数（如 1/3、1/7、5/8 等），同时避免浮点精度爆炸 |
| 负数 sign 存在 numerator | 减少 format 复杂度，与 GCD 数学定义一致 |

## 5. 风险与遗留问题

### 5.1 已识别风险
| 风险 | 缓解 |
|------|------|
| 浮点精度导致分数化简异常 | maxDenominator=9999 + 化简后分母判断 |
| 横屏布局冲突 | 切换按钮仅竖屏显示 |
| 持久化失败 | try-catch + 默认 DECIMAL |
| GCD 大数溢出 | ArkTS Number 双精度，分母 ≤ 9999 安全 |

### 5.2 待解决问题
无 blocker 问题。后续可优化（不在本次范围）：
- 混合分数显示（`1 1/2`）
- 历史记录条目也支持分数显示
- 自定义分母阈值

## 6. 实施建议

1. **优先级**：
   - P0: FractionUtil + DisplayMode + CalculatorPage 状态 + 切换按钮
   - P1: 错误状态禁用 + 启动恢复
   - P2: 单元测试 + UI 自动化

2. **测试粒度**：
   - 单元测试覆盖 FractionUtil 全部分支（GCD、化简、负数、零、NaN/Inf、回退）
   - UI 自动化覆盖切换按钮存在性 + 点击响应
   - 手动验证持久化

3. **回滚点**：
   - 移除 `resultDisplayMode` 字段
   - 移除切换按钮 UI
   - 恢复 `onEquals` 内的 `lastRawResult` 缓存

## 7. 总结

| 维度 | 评级 |
|------|------|
| 完整性 | ✅ 通过 |
| 一致性 | ✅ 通过 |
| 规范性 | ✅ 通过 |
| 可实施性 | ✅ 通过 |

**PLANNING 阶段结论**：设计完整、规范、可实施，进入 IMPLEMENTING 阶段。

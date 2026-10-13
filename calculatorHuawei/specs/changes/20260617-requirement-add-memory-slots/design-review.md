# 设计审视报告 — Issue #28 记忆槽 (M1-M6 + MR)

> AID PLANNING step9 产物。本报告对变更目录下的设计制品进行完整性、一致性、规范性检查。

---

## 1. 完整性评估

### 1.1 制品齐全性

| 制品 | 是否存在 | 路径 | 备注 |
| --- | --- | --- | --- |
| `proposal.md` | ✅ | `specs/changes/20260617-requirement-add-memory-slots/proposal.md` | 4.5 KB，意图+领域+层次+实体+模糊点+复杂度 |
| `delta-spec.md` | ✅ | `.../delta-spec.md` | 17.7 KB，模板全部章节齐全；SR × 8；FMEA × 7 |
| `info.md` | ✅ | `.../info.md` | 14.6 KB，含 capabilities.json 环境能力章节 |
| `delta-design.md` | ✅ | `.../delta-design.md` | 19.1 KB，D1-D10 全 + PlantUML × 4 + 自验证表 |
| `new-arch.md` | ⏭️ | - | 跳过（架构无变更，step6 决策） |
| `todo.md` | ✅ | `.../todo.md` | 已记录 step1-step9 进度 |
| **`design-review.md`** | ✅ | `.../design-review.md` | 本文件 |

**结论**: 通过。所有 PLANNING 必交制品齐全；`new-arch.md` 已在 step6 评估为可跳过（M 级但无架构变更），理由记录在 todo.md。

### 1.2 需求覆盖度

| 需求 (proposal.md) | delta-spec.md | delta-design.md |
| --- | --- | --- |
| 长按数字键存 M1-M6 | IR-MEM-01 + UC-001-01 | §3.5.5 + §3.6.5 onLongPressDigit |
| MR 弹菜单调出 | IR-MEM-02 + UC-002-01 | §3.6.5 onMRClick/onPickSlot + MemoryPickerPanel §3.6.10 |
| 记忆激活指示 | IR-MEM-03 + UC-003-01 | §3.5.6 lastUsedLabel + §3.6.5 getMemoryActiveLabel |
| 状态生命周期（不持久化） | IR-MEM-04 + SR-MEM-08 | §3.5.6 无 IO 接口；§10 不写偏好 |
| 边界空态 | IR-MEM-05 + UC-002-01 | §3.5.6 anyHasValue + §3.6.5 getMRButtonEnabled |
| 6 个模糊点自动决策 | 全部记录在 proposal.md 表格 | 决策一致性已交叉校验 |

**覆盖率**: 100%。所有 proposal.md 中的 IR 都在 delta-spec.md 中展开为 SR/UC，并在 delta-design.md 中有对应设计章节。

---

## 2. 一致性评估

### 2.1 proposal.md → delta-spec.md

| 检查项 | 结果 |
| --- | --- |
| 意图分类一致 | ✅ both: 新增功能 / requirement-add |
| 领域映射一致 | ✅ both: UI/交互 + 状态管理 (+ 数据管理可选) |
| 复杂度一致 | ✅ both: M（中等） |
| 模糊点 6 项全部进入 spec 约束或决策 | ✅ FMEA FM-01..07 对应 proposal 模糊点 #1..6 |
| 实体列表对齐 | ✅ MemorySlot、MemorySlotsState、MR 按钮、LongPressGesture 全部入 spec SR |

**结果**: 通过。

### 2.2 delta-spec.md → delta-design.md

| 检查项 | 结果 |
| --- | --- |
| 8 个 SR 全部进入 design | ✅ SR-MEM-01..08 ↔ §3.5.6 + §3.6 + §D5 + §D8 |
| FMEA 消减措施全部映射到 design 错误处理 | ✅ FM-01..07 ↔ §3.5.9 + §3.6.8 |
| UC-001-01/UC-002-01/UC-003-01 都有实现设计 | ✅ §3.5.5 + §3.6.4 时序图 + §3.6.10 UI 渲染 |
| KEI 指标（识别准确率/响应时延） | ✅ info.md §测试策略覆盖；design §D8 含手势 + 反馈时延 |
| 假设约束 C-01..C-07 | ✅ C-01（hdc/hvigorw 在 PATH）→ info.md 环境能力；C-04/C-05/C-06 "不涉及"在 spec/design 一致 |

**结果**: 通过。

### 2.3 delta-design.md 内部一致性

| 检查项 | 结果 |
| --- | --- |
| D2 功能清单 ↔ D8 交互目录 | ✅ 7 项功能 ↔ 6 个手势/弹窗 |
| D3.5 接口设计 ↔ D5 数据模型 | ✅ MemorySlotsState.slots 长度 = 6 ↔ §3.5.6 静态方法签名 |
| D6 见 §3.4 一致声明 | ✅ |
| D9.3 Kits 清单 ↔ §3.5.10 依赖 | ✅ 仅 @kit.ArkUI |
| D10 不写偏好 ↔ §3.5.6 无 IO ↔ SR-MEM-08 | ✅ 三处一致 |

**结果**: 通过。

---

## 3. 规范性评估

### 3.1 格式规范

| 检查项 | 结果 |
| --- | --- |
| proposal.md 包含意图/领域/层次/实体/模糊点/复杂度 | ✅ |
| delta-spec.md 模板章节齐全（不涉及的写"不涉及"） | ✅ 系统背景/上下文/需求描述/场景用例/SR 表齐全 |
| delta-design.md 章节 D1-D10 全部存在 | ✅ D1..D10 + 自验证表 + 生成标记 |
| 表格结构清晰 | ✅ |
| PlantUML 图表正确闭合（@startuml/@enduml） | ✅ 4 处 |

### 3.2 命名规范

| 检查项 | 结果 |
| --- | --- |
| 文件命名 `{YYYYMMDD}-{type}-{name}` | ✅ `20260617-requirement-add-memory-slots` |
| 文件名全部小写连字符 | ✅ |
| 标识符 camelCase | ✅ MemorySlot、MemorySlotsState、showMemoryPicker |
| 类名 PascalCase | ✅ |
| 静态方法名 camelCase | ✅ save / recall / anyHasValue / lastUsedLabel |

### 3.3 描述清晰度

| 检查项 | 结果 |
| --- | --- |
| 每个 SR 含 What/关联用例/可验证达成标准/优先级 | ✅ |
| 每个 UC 含主成功路径 + 扩展路径 + 验收 | ✅ |
| delta-design.md 每个接口签名明确参数与返回值 | ✅ |
| 模糊点自动决策含"为什么这样选" | ✅ proposal.md 表格"自动决策"列已说明 |

---

## 4. 设计决策合理性

### 4.1 复用而非新建

| 既有资产 | 复用方式 | 决策依据 |
| --- | --- | --- |
| `pages/LongPressMenu.ets` 的 MENU_* 样式常量 | 直接 import 复用 MemoryPickerPanel 样式 | info.md §5 公共组件识别 |
| `LongPressMenuPanel` Column-mask 渲染模式 | 复制改造成 MemoryPickerPanel | 同上；数据驱动而非字符串驱动 |
| `promptAction.showToast` | 已 import | info.md §6 Toast 模式 |
| `@ohos/hypium` 测试模板 | 复制 HistoryGroup.test.ets 结构 | info.md §8 |

✅ 充分复用既有 pattern，未引入新框架/新 Kit/新依赖。

### 4.2 无架构变更的合理性

- 项目无 viewmodel 概念，V1 @State 直接挂在 `@Entry` 上
- MemorySlots 设计为纯函数式逻辑类（immutable update），不引入 @Observed，保持 V1 一致性
- 不写 Preferences，不引入新文件类型（HAP/HAR/HSP）
- 影响范围：1 个新增文件 + 1 个扩展文件 + 1 个测试文件

✅ 架构决策与项目既有一致，无过度工程。

### 4.3 边界与错误处理完备性

- 非有限值拒绝（FM-01/FM-05）
- 越界抛 Error（仅程序错误路径）
- 空槽返回 null（业务正确）
- 弹窗去重（FM-06）
- 全部空时 MR 禁用（FM-04）

✅ 7 个 FMEA 异常全部有对应消减措施。

### 4.4 测试策略完整性

- 单元测试：MemorySlots 7 个核心方法（含边界）
- UI 自动化：长按 1 存 → MR 调出 → display 验证
- 能力评估：单元 ✅ + UI 自动化 ✅（hdc + 模拟器 127.0.0.1:5555）

✅ 测试链路完整，无盲点。

---

## 5. 风险与遗留问题

### 5.1 实施阶段可能遇到的小风险

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| 数字键 builder 改造引入 lint 警告（单行过长） | 低 | 多行换行 builder 写法 |
| LongPressGesture 与 onClick 互斥未在数字键上验证 | 低 | 项目 line 656 已有同 pattern；可视为已验证 |
| UI 自动化 drag 200ms 在某些模拟器上识别不出 longPress | 低 | memory 中已有 `uitest uiInput drag X Y X+1 Y+1 200` 稳定方案（[[harmonyos-uitest-longpress]]） |
| `parseFloat('1,234')` 截断为 1 风险 | 低 | spec 已要求先 `replace(/,/g, '')`；FMEA 已覆盖 |
| CalculatorPage 突破 900 行 | 低 | 业务逻辑下沉到 MemorySlots.ets；预期 +60 行 |

### 5.2 待 IMPLEMENTING 阶段澄清（无 blocker）

- 无。proposal.md 的 6 个模糊点已全部自动决策并写明理由。
- IMPLEMENTING 阶段直接进入任务分解。

### 5.3 待 APPLYING 阶段验证

- UI 自动化跑通：长按 1 存 → MR 调出 → display 验证
- 单元测试覆盖率 ≥80%（7 个核心方法）
- 编译 hvigorw --no-daemon assembleHap 通过
- Lint 检查通过

---

## 6. 总体结论

| 评估维度 | 结果 |
| --- | --- |
| 完整性 | ✅ 通过 |
| 一致性（proposal ↔ spec ↔ design） | ✅ 通过 |
| 规范性（格式/命名/描述） | ✅ 通过 |
| 决策合理性（复用/架构/边界/测试） | ✅ 通过 |
| 无 blocker 遗留 | ✅ 通过 |

**PLANNING 阶段结论**: ✅ 完成。可进入 IMPLEMENTING 阶段（aid-implementing）。

---

> AID PLANNING step9 设计审视完成。
> 生成时间: 2026-06-17

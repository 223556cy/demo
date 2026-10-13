# 设计审视报告 — 程序员模式

> **变更**：`specs/changes/20260612-requirement-programmer-mode/`
> **审视时间**：2026-06-12

---

## 1. 完整性评估

### 1.1 制品齐全性
- [x] `proposal.md` — 需求提案（含澄清后需求摘要 §9）
- [x] `delta-spec.md` — 增量需求规格（8 个 IR + 15 个 SR + 1 个用例）
- [x] `delta-design.md` — 增量设计（D1-D12 全章节）
- [x] `info.md` — 代码仓理解
- [x] `todo.md` — 任务进度
- [x] `design-review.md` — 本文件

### 1.2 需求覆盖度
- IR-PM-01（模式入口）→ SR-PM-01/02 → F-PM-01 ✓
- IR-PM-02（4 进制显示）→ SR-PM-03 → F-PM-03 ✓
- IR-PM-03（当前进制输入）→ SR-PM-04/05 → F-PM-02/07 ✓
- IR-PM-04（位宽与符号）→ SR-PM-06/07/08 → F-PM-08 ✓
- IR-PM-05（整数四则 + mod）→ SR-PM-09/10 → F-PM-09 ✓
- IR-PM-06（位运算）→ SR-PM-11/12 → F-PM-06 ✓
- IR-PM-07（持久化）→ SR-PM-13 → F-PM-11 ✓
- IR-PM-08（错误处理）→ SR-PM-14/15 → F-PM-12 ✓

**覆盖率 100%**（8/8 IR，15/15 SR，12/12 F）。

---

## 2. 一致性评估

### 2.1 proposal → delta-spec
- [x] proposal.md §2 目标 G1-G7 全部映射到 delta-spec SR-PM-01..15
- [x] proposal.md §3 非目标 在 delta-spec 中均不涉及
- [x] proposal.md §4 范围 与 delta-spec §功能影响列表 一致
- [x] 澄清后决策（§9 6 项）全部反映在 SR 中

### 2.2 delta-spec → delta-design
- [x] SR-PM-01..02 → F-PM-01（Tab 切换）
- [x] SR-PM-03 → F-PM-03（4 进制显示）
- [x] SR-PM-04 → F-PM-02 + A-F 按钮
- [x] SR-PM-06/07/08 → F-PM-08
- [x] SR-PM-09 → F-PM-09（Math.trunc）
- [x] SR-PM-11/12 → F-PM-06 + F-PM-02
- [x] SR-PM-13 → F-PM-05 + F-PM-11
- [x] SR-PM-14/15 → F-PM-12

**一致性：通过**。

### 2.3 delta-design → info
- [x] info.md §"需要新增的模块" 全部覆盖于 delta-design §3.5.3
- [x] info.md §"需要修改的模块" 全部覆盖于 delta-design §3.5.3
- [x] info.md §"风险识别" 5 项均在 delta-design §3.5.9 给出处理

**一致性：通过**。

---

## 3. 规范性评估

### 3.1 格式规范
- [x] delta-spec.md 遵循 delta-spec-template.md 章节结构
- [x] delta-design.md 遵循 mod-design D1-D12 章节结构
- [x] 所有制品含 frontmatter 或开头元数据
- [x] PlantUML 图使用 `@startuml/@enduml` 包裹

### 3.2 命名规范
- [x] 路径：`specs/changes/{date}-{type}-{name}/` 符合规范
- [x] 枚举：`CalculatorMode / Base / BitWidth / Signedness` PascalCase 一致
- [x] 字段：`programmerModeEnabled / programmerActiveBase / programmerBitWidth / programmerSignedness` camelCase 一致
- [x] 函数：`toBase / fromBase / format4Bases / isValidCharForBase` camelCase 动词性

### 3.3 描述清晰度
- [x] FMEA 5 项异常均有 Actor/影响/消减措施/触发检测/恢复兜底
- [x] SR 描述均为 "What"，未越界到 "How"
- [x] delta-design §3.5.6 接口设计有完整签名

---

## 4. 遗留问题

| 编号 | 问题 | 严重程度 | 处理建议 |
| --- | --- | --- | --- |
| Q-01 | `^` 在 CalcEngine 已是幂运算，与 XOR 冲突 | 已处理 | 程序员模式下 `replaceSymbols` 将 `^` 改为 `bxor`，基础/科学模式不变 |
| Q-02 | BigInt 在 API < 12 不可用 | 已处理 | typeof 检测 + 降级 number（±2^53） |
| Q-03 | 64 位位宽显示位数（16 位 HEX） | 已处理 | 显示 16 字符 + 前缀 `0x` 共 18 字符 |
| Q-04 | 历史记录只存 DEC 是否够用 | 已处理 | 假设项（proposal §9）已声明 |
| Q-05 | 横屏 4 列键盘是否够放 A-F + 位运算 | 待 UI 验证 | 程序员模式横屏可能需要 6 列扩展，在 IMPLEMENTING 阶段确认 |
| Q-06 | 浮点截断是否在 onEquals 时统一处理 | 已设计 | 在 input 层 `Math.trunc`，对每个 digit 输入即时生效 |
| Q-07 | `~` 一元运算 Expression 预处理 | 已设计 | 见 §3.5.8 |

---

## 5. 综合结论

| 维度 | 结果 |
| --- | --- |
| 完整性 | 通过 |
| 一致性 | 通过 |
| 规范性 | 通过 |
| 风险覆盖 | 通过 |

**总体评估：可进入 IMPLEMENTING 阶段**。

---

> 本文档由 aid-planning step9 自动生成。
> 生成时间：2026-06-12

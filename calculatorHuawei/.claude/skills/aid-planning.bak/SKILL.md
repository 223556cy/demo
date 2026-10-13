---
name: aid-planning
description: |
  AID PLANNING 阶段 skill，用于需求分析与系统设计规划。
  当用户说"执行 aid-planning"、"开始规划xxx"、"需求分析与设计"或类似表述时触发。
  本 skill 负责 PLANNING 阶段的所有工作：step1（用户意图理解）→ step2（需求理解）→ step3（需求澄清）→ step4（需求spec设计）→ step5（针对需求的代码仓理解）→ step6（需求复杂度评估）→ step7（架构设计）→ step8（组件设计）→ step9（设计审视）
compatible: ["{项目名}-main"]
---

# AID-Planning Skill

## 1 概述

本 skill 实现 AID PLANNING 阶段，负责从需求理解到设计完成的完整规划流程。

```
PLANNING 阶段流程：
step1（用户意图理解）→ step2（需求理解）→ step3（需求澄清）→ step4（需求spec设计）→ step5（针对需求的代码仓理解）→ step6（需求复杂度评估）→ step7（架构设计）→ step8（组件设计）→ step9（设计审视）
```

**8个核心步骤说明**：

| 步骤 | 名称 | 主要产出 | 必须使用的 Skill |
|------|------|---------|-----------------|
| step1 | 用户意图理解 | 识别变更类型 | - |
| step2 | 需求理解 | 结构化解析需求，输出结构化分析结果 | `rq-parse` |
| step3 | 需求澄清 | 澄清模糊需求（当存在 blocker/important 级别模糊点时） | `rq-clarify` |
| step4 | 需求spec设计 | 产出 delta-spec.md | - |
| step5 | 项目和代码仓理解 | 理解现有项目结构和代码，产出 info.md | `rq-codebase` |
| step6 | 需求复杂度评估 | 评估复杂度，决定跳过策略 | - |
| step7 | 架构设计 | 分析架构影响，产出 new-arch.md（如需） | - |
| step8 | 组件设计 | 产出 delta-design.md | `mod-design` |

**方法论说明**
- step1~step4本质是在做需求分析，只需要将需求识别清晰、需求规格明确即可，不应与代码实现绑定。
- step5~step8本质是做系统设计，需要结合具体的系统方案和代码基础，明确实现架构、实现设计。

## 2 执行步骤

### step1 用户意图理解

**主要目标**：理解用户的变更意图，若符合项目开发，则推荐Git分支检查，并初始化specs/changes/*目录。如果前置步骤已经明确，则可以跳过。

**操作步骤**：
划分用户变更意图为五个子意图。

| 子意图  | 类别 | 触发词举例 | 目录管理 |
|------|------|------------|----------|
| 新增功能 | 新增业务需求 | `add`, `new`, `新增`, `增加`, `开发`, `我要`, `我想`, `需要`, `希望` | `./specs/changes/<YYYYMMDD>-requirement-add-<name>` |
| 功能变更 | 对现有需求进行修改 | `change`, `变更`, `修改`, `改动`, `调整`, `优化` | `./specs/changes/<YYYYMMDD>-requirement-change-<name>` |
| 缺陷修复 | 修复缺陷问题 | `fix`, `bugfix`, `修复`, `解决`, `bug`, `问题`, `错误` | `./specs/changes/<YYYYMMDD>-bugfix-<name>` |
| 优化或重构 | 架构优化、性能优化、DFX等 | `重构`, `refactor`, `优化架构`, `架构调整`, `重写`, `性能优化`, `DFX` | `./specs/changes/<YYYYMMDD>-arch-refactor-<name>` |
| 平台迁移 | 将系统移植到新平台 | `migration`, `迁移`, `移植`, `跨平台`, `安卓转鸿蒙` | `./specs/changes/<YYYYMMDD>-platform-migration-<name>` |

### step1.1 Git 分支检查（推荐）

**主要目标**：建议用户在独立分支上进行变更，避免直接修改 main 分支。

**操作步骤**：
1. 执行 `git branch --show-current` 检查当前分支
2. 如果当前在 `main` 或 `master` 分支：
   - 向用户推荐：「建议为本次变更创建独立分支：`feat/{YYYYMMDD}-{type}-{name}`，是否采纳？」
   - 用户接受 → 执行 `git checkout -b feat/{YYYYMMDD}-{type}-{name}`
   - 用户拒绝 → 继续在当前分支工作，后续不再提示
3. 如果已在非 main 分支 → 跳过，直接进入 step2

**约束**：
- 这是软推荐，不阻塞流程
- 分支名复用 step1 确定的 `{YYYYMMDD}-{type}-{name}`
- 记录用户选择到 `todo.md`（字段：`git_branch_adopted: true/false`）

---

### step2 需求理解

**主要目标**：结构化解析需求（使用 rq-parse），产出proposal.md（参考proposal-template.md模板）。

**参考模板**：`aid-planning/templates/proposal-template.md`，或按照使用的skill要求进行输出。

**约束**：必须使用 `skill('rq-parse')`

**操作步骤**：
1. 执行 `skill('rq-parse')` 加载需求解析能力
2. 将用户原始需求作为输入传递给 rq-parse
3. 等待 rq-parse 输出完整的结构化分析

**rq-parse 输出包含**：
- 意图分类（新增功能 / 功能变更 / 缺陷修复 / 优化或重构 / 平台迁移）
- 领域映射（UI/交互、数据管理、网络通信、媒体播放等）
- 影响层次（View/ViewModel/Model/数据层/基础设施）
- 关键实体（数据实体/页面实体/接口实体/事件实体）
- 模糊点列表（blocker/important/nice-to-have）
- 复杂度评估（S/M/L/XL）

### step3 需求澄清

**主要目标**：澄清模糊需求（使用 rq-clarify），产出proposal.md。

**参考模板**：`aid-planning/templates/proposal-template.md`，或按照使用的skill要求进行输出。

**约束**：如果 rq-parse 输出了 `blocker` 或 `important` 级别的模糊点，必须使用 `skill('rq-clarify')`

**操作步骤**：
1. 检查 rq-parse 输出的模糊点列表
2. 如果存在 `blocker` 或 `important` 级别的模糊点：
   - 执行 `skill('rq-clarify')` 加载需求澄清能力
   - 将 rq-parse 的模糊点列表输入给 rq-clarify
   - 按照 rq-clarify 的交互流程进行提问和收集回答
   - rq-clarify 会输出"澄清后需求摘要"
3. 如果没有 blocker/important 级别的模糊点，标记"无需澄清"

### step4 需求spec设计

**主要目标**：产出 delta-spec.md

**参考模板**：`aid-planning/templates/delta-spec-template.md`

**操作步骤**：
1. 阅读 proposal.md
2. 分析新增功能对关联的 `{SPECS_FEATURE_ROOT}/feat-{特性}/spec.md` 的影响
3. 确定需要新增或修改的 spec 章节
4. 在 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/delta-spec.md` 中输出增量 spec

**delta-spec.md 包含内容**：
- 必须根据**参考模板**的要求输出内容，对于分析后确定不需要的内容，必须在对应章节使用“不涉及”表达，禁止修改模板结构。
- 生成内容要严谨合理，宁缺毋滥。
- **参考模板**中的可靠性内容的分析要相对细致、严格，其他DFX可适当简略。
- 在需求分解章节，可靠性分析（FMEA）的故障模式/改进措施等内容（可靠性分析结果（FMEA 消减措施清单）章节的内容），必须作为需求的约束或者独立的需求体现出来，禁止有遗漏。

**文件拆分**：如果 delta-spec.md 超过 2000 行，需要按章节拆分为多个md文件

### step5 针对需求的代码仓理解

**主要目标**：根据用户需求，理解现有项目结构和代码

**约束**：必须使用 `skill('rq-codebase')`

**操作步骤**：
1. 执行 `skill('rq-codebase')` 加载代码仓理解能力
2. 分析 `{项目名}-main/entry/src/main/ets/` 目录下的代码结构
3. 识别关键模块、接口依赖、数据模型
4. 产出 `info.md` 到 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/info.md`

**rq-codebase 输出包含**：
- 项目结构概览
- 关键模块列表
- 接口依赖关系
- 数据模型说明

### step6 需求复杂度评估

**主要目标**：评估复杂度，决定跳过策略

**操作步骤**：
1. 阅读前面步骤生成的内容，理解当前需求和项目
2.  评估需求复杂度

**复杂度评估标准**：

| 维度 | 简单需求 | 复杂需求 |
|------|---------|---------|
| 功能范围 | 单个功能点，影响 1-2 个模块 | 多个功能点，涉及 3+ 模块 |
| 代码改动 | < 100 行 | ≥ 100 行 |
| 数据模型 | 无需新增/修改模型 | 需要新增/修改数据模型 |
| 架构影响 | 无需变更架构 | 需要变更架构 |
| 接口变更 | 现有接口扩展 | 需要新增/修改接口 |
| 依赖关系 | 单一模块依赖 | 多模块交叉依赖 |

**复杂度判定规则**：
- **简单需求**：满足以下条件之一
  - 影响模块数 ≤ 2
  - 无需新增数据模型
  - 无需变更架构
  - 代码改动量小

- **复杂需求**：满足以下条件之一
  - 影响模块数 > 2
  - 需要新增/修改数据模型
  - 需要变更架构
  - 涉及多模块交叉依赖
  - 用户明确说明是大需求

**产出复杂度评估结果**：

```markdown
## 复杂度评估

### 评估结果
- **复杂度等级**：简单 / 复杂
- **影响模块数**：{数量}
- **架构变更**：是 / 否
- **数据模型变更**：是 / 否

### 跳过策略
根据复杂度评估结果，决定需要产出的制品：

| 制品 | 简单需求 | 复杂需求 |
|------|---------|---------|
| new-arch.md | 可跳过（架构无变更时） | 必须（架构变更时） |
| delta-design.md | 必须 | 必须 |
| tasks.md | 必须 | 必须 |
```

### step7 架构设计

**主要目标**：分析架构影响，产出 new-arch.md（如需）

**原则**：非必要情况下不要变更架构

**复杂度判定**：
- **简单需求**（无需架构变更）：跳过此步骤
- **简单需求**（需架构变更）：产出 new-arch.md
- **复杂需求**：执行完整架构分析，产出 new-arch.md（如需要）

**操作步骤**：
1. 阅读 proposal.md、delta-spec.md和info.md等前置输出件
2. 分析新增功能对关联的arch.md的影响
3. 判断是否需要架构变更

**需要架构变更的判断条件**：
- 新增核心模块
- 改变模块间主要交互关系
- 新增外部依赖
- 改变数据流

**不需要架构变更的情况**：
- 纯 UI 变更
- 现有模块内的功能扩展
- 现有接口的简单调用

**产出 new-arch.md（如需要）**：

**参考模板**：`aid-planning/templates/new-arch-template.md`

**new-arch.md 包含内容**：
- 变更概述（变更类型、变更日期、变更人）
- 变更原因
- 变更点（具体变更内容）
- 变更后架构（整体分层图、表现层、业务逻辑层、数据访问层、内部接口、数据模型）
- 兼容性说明
- 迁移方案

### step8 组件设计

**主要目标**：产出 delta-design.md

**约束**：必须使用 `skill('mod-design')`

**操作步骤**：
1. 执行 `skill('mod-design')` 加载组件设计能力
2. 将以下输入文件路径传递给 mod-design：
   - `info.md` - 代码仓理解
   - `proposal.md` - 需求提案
   - `delta-spec.md` - 需求规格说明
3. 要求 mod-design 输出到 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/delta-design.md`

**mod-design skill 说明**：
- mod-design 是正向设计（根据需求产出设计文档）
- 输出类型由 mod-design 根据目录结构自动判断（delta-design.md）
- 设计文档遵循 D1-D10 章节结构

### step9 设计审视

**主要目标**：对变更文件夹下的设计制品进行检查

**操作步骤**：

#### step9-1 完整性检查

检查以下制品是否齐全：
- [ ] `proposal.md` - 需求提案
- [ ] `delta-spec.md` - 增量规格
- [ ] `delta-design.md` - 增量设计
- [ ] `new-arch.md`（如需要架构变更）

#### step9-2 一致性检查

检查制品之间的一致性：
- proposal.md 中的需求是否在 delta-spec.md 中完整呈现
- delta-spec.md 中的功能是否在 delta-design.md 中有对应设计
- delta-design.md 中的设计是否能满足 delta-spec.md 中的要求

#### step9-3 规范性检查

检查制品格式是否符合模板要求：
- 章节结构是否完整
- 命名是否规范
- 描述是否清晰

#### step9-4 产出审视报告

变更文件夹 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/` 下应包含：

- [ ] `info.md` - 代码仓理解
- [ ] `proposal.md` - 需求提案
- [ ] `delta-spec.md` - 增量规格
- [ ] `new-arch.md` - 新架构（如需）
- [ ] `delta-design.md` - 增量设计
- [ ] `design-review.md` - 设计审视报告
- [ ] `todo.md` - 任务进度

在 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/design-review.md` 中输出审视结果：
```markdown
# 设计审视报告

## 1. 完整性评估
- [ ] 制品齐全性：{通过/不通过}
- [ ] 需求覆盖度：{X%}

## 2. 一致性评估
- [ ] proposal → delta-spec：{通过/不通过}
- [ ] delta-spec → delta-design：{通过/不通过}

## 3. 规范性评估
- [ ] 格式规范：{通过/不通过}
- [ ] 命名规范：{通过/不通过}

## 4. 遗留问题
{列出待解决问题}
```

## 3 全局约束

### 3.1 Skill 调用规则

**强制要求**：
- 必须严格按照步骤的顺序执行，不要自行调整顺序。
- 所有步骤都不可以跳过，必须显示的执行步骤，并产出执行效果。
- 只要步骤中要求使用其他 skill 的，必须使用对应的 skill，不能跳过或自行实现。
- 整个过程中，需要询问用户的问题必须询问用户，不允许任何默认的假设。

### 3.2 todo.md 文件同步

在每个 step 完成后，同步更新 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/todo.md` 文件，记录当前进度，便于任务中断恢复。

### 3.3 子任务拆解

在每个 step 中，还需要按照章节进行子任务拆解，保证任务的小颗粒度执行。

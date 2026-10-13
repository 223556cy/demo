# AID Workflow 全流程 Skill 依赖关系 & 测试用例/验收标准生成链路

> **生成时间**: 2026-08-25
> **数据来源**: 实际读取 `calculatorHuawei/.claude/skills/` 下 16 个 SKILL.md + 编排器 `aid-workflow.md` 原文
> **目的**: 回答你提出的 3 件事 —— (1) 整体执行链路 (2) skill 间调用/依赖 (3) 验收标准/测试样例/测试执行由谁生成
>
> ⚠️ 本文档只描述**正常流程下的设计意图**，实际调用次数 / 失职点见 `根因分析-测试用例生成问题.md` 和 `根因分析-OHOS相关根因案例汇总.md`。

---

## 0. 目录

1. 整体执行链路（一图 + 表）
2. Skill 全景清单（按角色分类）
3. 顶层编排器 `aid-workflow` 的阶段划分
4. 各阶段 Skill 调用关系（含 `skill('xxx')` 触发点）
5. 产物（artifact）流向与消费关系
6. 测试用例/验收标准/测试执行的归属（你最关心的部分）
7. 任务分解链路
8. 阶段间硬门禁 & 铁律
9. 关键文件路径模板
10. 横向 skill（不参与主流程但会旁路调用）

---

## 1. 整体执行链路

```
aid-init → aid-planning → aid-implementing → aid-applying → aid-archiving → aid-monitor
   ↓              ↓                ↓                 ↓
 一次性       9 个 step          3 个 step          5 个 step
 环境检查    (产 spec/design)   (产 tasks.md)     (产 apply-report)
```

| 阶段 | Skill | step 数 | 入口命令 | 主要产出物 |
|---|---|---|---|---|
| 初始化 | `aid-init` | 8 | `/aid-init` | `specs/initialized.flag` |
| 需求规划 | `aid-planning` | 9 | `/aid-workflow` step1-9 | `proposal.md` `delta-spec.md` `info.md` `new-arch.md` `delta-design.md` `design-review.md` |
| 任务分解 | `aid-implementing` | 3 | `/aid-workflow` step2-1~3 | `tasks.md` |
| 代码应用+测试 | `aid-applying` | 5 | `/aid-workflow` step3-0~4 | `apply-report.md` |
| 归档 | `aid-archiving` | 4 | `/aid-archiving` | `specs/archives/{change_name}/` |
| 知识库同步 | `aid-monitor` | 7 | `/aid-monitor` | `incident-report.md` `specs/guidelines/{domain}.md` |

> 顶层编排器 `calculatorHuawei/.claude/commands/aid-workflow.md` 通过 TodoWrite 统一管理整个流程的进度（PLANNING/IMPLEMENTING/APPLYING/ARCHIVE 四阶段开关）。

---

## 2. Skill 全景清单（按角色分类）

### 2.1 主流程 skill（aid-workflow 编排器会依次调用）

| Skill | 文件 | 阶段 | 触发命令 | 角色 |
|---|---|---|---|---|
| `aid-init` | `aid-init/SKILL.md` | 初始化 | `/aid-init` | 环境/目录/git 检查 |
| `aid-planning` | `aid-planning/SKILL.md` | PLANNING | `/aid-workflow` step1-9 | 需求+设计 |
| `aid-implementing` | `aid-implementing/SKILL.md` | IMPLEMENTING | `/aid-workflow` step2-1~3 | 任务分解 |
| `aid-applying` | `aid-applying/SKILL.md` | APPLYING | `/aid-workflow` step3-0~4 | 代码应用+测试 |
| `aid-archiving` | `aid-archiving/SKILL.md` | ARCHIVE | `/aid-archiving` | 归档 |
| `aid-monitor` | `aid-monitor/SKILL.md` | 监控 | `/aid-monitor` | 知识库维护 |

### 2.2 aid-planning 内部 sub-skill（在 step2/3/5/8 内被 `skill()` 调用）

| Sub-skill | 在哪个 step 被调 | 产出 | 角色 |
|---|---|---|---|
| `rq-parse` | aid-planning step2 | 结构化需求解析（意图/领域/层次/实体/模糊点） | 需求解析 |
| `rq-clarify` | aid-planning step3（条件触发） | 澄清后需求摘要 | 交互式澄清 |
| `rq-codebase` | aid-planning step5 | `info.md` | 代码仓理解 |
| `mod-design` | aid-planning step8 | `delta-design.md` | 组件设计（D1-D10） |
| `dfr-fmea-harmony` | aid-planning step4（写入 delta-spec.md） | 可靠性分析 + NFSR | 可靠性/FMEA（嵌入 spec） |

### 2.3 aid-applying 内部 sub-skill（在 step3-2 内被调）

| Sub-skill | 在哪个 step 被调 | 角色 |
|---|---|---|
| `tdd-enforcer` | aid-applying step3-2-1 | 强制 RED→GREEN→REFACTOR，每个 task 一次 |
| `harmonyos-ui-test` | aid-applying step3-2-2b | hdc 真机/模拟器 UI 自动化 |

### 2.4 横向 skill（不参与主流程，按需旁路调用）

| Skill | 角色 | 触发场景 |
|---|---|---|
| `aid-reviewing` | SDD/Spec/Design 文档审阅（轻量/audit） | 用户要求"审阅 spec.md" |
| `aid-code-root-cause` | 7 角度扫代码 bug，定位 file:line | 用户报告 bug，需根因分析 |
| `aid-analysis-*` (6 个) | 分析流水线（phenomenon → log-scan → spec-code-map → locate-bug → root-cause → output） | issue 首席诊断任务 |
| `prd-generator` | PRD 文档生成（独立流程） | 用户要写 PRD，不是 aid-workflow |

---

## 3. 顶层编排器 `aid-workflow` 的阶段划分

**文件**: `calculatorHuawei/.claude/commands/aid-workflow.md`（319 行）

**步骤 0**：aid-init（一次性检查 `specs/initialized.flag`）
**步骤 1**：意图识别（5 类意图 → 5 类目录）
**步骤 2**：分阶段串行执行

```
PLANNING (9 step)
  ↓
IMPLEMENTING (3 step)
  ↓
APPLYING (5 step)
  ↓
ARCHIVING (aid-archiving)
```

**每阶段后必须询问用户确认**（不能跳步）。TodoWrite 由编排器统一管理，各 skill 不再用 TodoWrite。

---

## 4. 各阶段 Skill 调用关系（含 `skill('xxx')` 触发点）

### 4.1 aid-planning（9 个 step 的内部调用链）

来源：`aid-planning/SKILL.md` 表 §1

```
step1 用户意图理解            → 无 skill 调用（仅目录初始化）
step2 需求理解                → skill('rq-parse')             [必须]
step3 需求澄清                → skill('rq-clarify')           [条件: blocker/important 模糊点]
step4 需求spec设计             → 无 skill 调用（直接写 delta-spec.md，
                                 含 FMEA 章节 ← 嵌入 dfr-fmea-harmony 流程）
step5 代码仓理解              → skill('rq-codebase')          [必须]
step6 需求复杂度评估          → 无 skill 调用
step7 架构设计                → 无 skill 调用（如需 new-arch.md）
step8 组件设计                → skill('mod-design')           [必须]
step9 设计审视                → 无 skill 调用（自评 design-review.md）
```

**输出文件链路**：
```
step2 → proposal.md
step3 → proposal.md (更新)
step4 → delta-spec.md
step5 → info.md
step7 → new-arch.md (条件)
step8 → delta-design.md
step9 → design-review.md
```

### 4.2 aid-implementing（3 个 step）

来源：`aid-implementing/SKILL.md`

```
step2-1 任务分解
  ├─ 阅读 delta-design.md + proposal.md
  └─ 拆分为最小可开发 task（每个 1-2h、有验收标准）
step2-2 任务排序
  ├─ 基础设施 → 核心业务 → UI 表现层
  └─ 标依赖关系（依赖任务 / 无）
step2-3 产出 tasks.md
```

**输出文件**：`tasks.md`（含任务清单 + 验收标准 + 开发顺序）

> ⚠️ **aid-implementing 内部不调用任何 sub-skill**——它消费 aid-planning 的产物，自己生成 tasks.md。

### 4.3 aid-applying（5 个 step，含 2 个强制 sub-skill）

来源：`aid-applying/SKILL.md`

```
step3-0 环境检查
  ├─ 检测项目类型（hvigorw / package.json / gradlew / ...）
  ├─ 编译 + 测试环境检查
  └─ ⚠️ HarmonyOS 必须用 worktree 里的 opencalc/build_hap.bat（铁律）
step3-1 确认应用条件
  ├─ 检查 tasks.md 全部 completed
  └─ lint 检查
step3-2 代码应用 + 测试
  ├─ step3-2-1 → skill('tdd-enforcer')        [必须, 每个 task 走 RED-GREEN-REFACTOR]
  ├─ step3-2-2   → hvigorw test@entry         [全量单测回归]
  └─ step3-2-2b → skill('harmonyos-ui-test')  [铁律 7: HarmonyOS UI 任务必跑真机/模拟器]
step3-3 更新任务状态（todo.md）
step3-4 产出 apply-report.md
```

**apply-report.md 包含**：AC 覆盖表（每个 AC 行有"主观描述"+"客观证据"两列）

---

## 5. 产物（artifact）流向与消费关系

### 5.1 文件消费矩阵

| 产物 | 由谁产出 | 在哪一步 | 被谁消费 |
|---|---|---|---|
| `proposal.md` | aid-planning step2/3 | rq-parse + rq-clarify 完成后 | ↓ aid-implementing step2-1 (读)<br>↓ aid-planning step7 (读)<br>↓ aid-planning step9 (审) |
| `delta-spec.md` | aid-planning step4 | 直接写（含 FMEA） | ↓ aid-implementing step2-1 (读)<br>↓ mod-design (读)<br>↓ aid-planning step7 (读) |
| `info.md` | aid-planning step5 | rq-codebase 产出 | ↓ mod-design (读)<br>↓ aid-planning step7 (读) |
| `new-arch.md` | aid-planning step7 | 条件产出 | ↓ mod-design (读)<br>↓ aid-implementing step2-1 (读) |
| `delta-design.md` | aid-planning step8 | mod-design 产出 | ↓ aid-implementing step2-1 (读)<br>↓ aid-applying step3-0/1 (前置检查) |
| `design-review.md` | aid-planning step9 | 自评 | ↓ 归档时作为制品 |
| `tasks.md` | aid-implementing step2-3 | 直接产出 | ↓ aid-applying step3-1/2 (执行)<br>↓ aid-applying step3-4 (写 apply-report) |
| `apply-report.md` | aid-applying step3-4 | 直接产出 | ↓ aid-archiving (作为归档制品) |
| `todo.md` | 每个 step 末尾 | 进度同步 | ↓ 阶段间恢复 / 编排器读取 |
| `archive-report.md` | aid-archiving step3-5 | 归档完成报告 | ↓ 最终交付物 |

### 5.2 数据流图（顶层）

```
                ┌─────────────────────────────┐
                │     aid-planning step1       │
                │     (用户意图 + 目录初始化)    │
                └──────────────┬────────────────┘
                               ↓
   ┌────────────┐  ┌──────────────────────────┐
   │ rq-parse   │→ │ aid-planning step2         │
   └────────────┘  │   → proposal.md            │
                   ├──────────────────────────┤
                   │ step3 + rq-clarify (条件)   │
                   │   → proposal.md 更新        │
                   ├──────────────────────────┤
                   │ step4 (FMEA 内嵌)            │
                   │   → delta-spec.md           │
                   ├──────────────────────────┤
                   │ step5 + rq-codebase         │
                   │   → info.md                 │
                   ├──────────────────────────┤
                   │ step7 (条件)                │
                   │   → new-arch.md             │
                   ├──────────────────────────┤
                   │ step8 + mod-design          │
                   │   → delta-design.md         │
                   ├──────────────────────────┤
                   │ step9 (自评)                │
                   │   → design-review.md        │
                   └──────────────┬─────────────┘
                                  ↓ 消费全部 6 个产物
                   ┌──────────────────────────────┐
                   │  aid-implementing step2-1~3   │
                   │    → tasks.md                 │
                   │    (含每个 task 的验收标准)      │
                   └──────────────┬───────────────┘
                                  ↓
                   ┌──────────────────────────────┐
                   │  aid-applying step3-2-1       │
                   │    → skill('tdd-enforcer')     │
                   │    每个 task 走 RED→GREEN→REFACTOR│
                   ├──────────────────────────────┤
                   │  step3-2-2 全量单测             │
                   ├──────────────────────────────┤
                   │  step3-2-2b                   │
                   │    → skill('harmonyos-ui-test')│
                   │    UI 任务必须真机/模拟器验证      │
                   ├──────────────────────────────┤
                   │  step3-4                      │
                   │    → apply-report.md          │
                   └──────────────┬───────────────┘
                                  ↓
                   ┌──────────────────────────────┐
                   │  aid-archiving                 │
                   │    → specs/archives/{name}/    │
                   └──────────────┬───────────────┘
                                  ↓
                   ┌──────────────────────────────┐
                   │  aid-monitor                  │
                   │    → incident-report.md       │
                   │    → specs/guidelines/{domain}.md│
                   └──────────────────────────────┘
```

---

## 6. 测试用例 / 验收标准 / 测试执行 的归属（你最关心的部分）

### 6.1 验收标准（Acceptance Criteria, AC）—— **3 个层次**

| 层次 | 在哪里 | 由谁生成 | 模板 | 示例 |
|---|---|---|---|---|
| **需求层 AC** | `delta-spec.md` 的 `### AC-N` 段 | aid-planning step4 | `aid-planning/templates/delta-spec-template.md` | `### AC-2: 默认 sin(x) 渲染曲线` |
| **任务层 AC** | `tasks.md` 每个 Task 的"验收标准"段 | aid-implementing step2-1 | `aid-implementing/templates/tasks-template.md` | `**验收标准**: sampleSeries 覆盖线性/null/除零` |
| **应用层 AC 验证表** | `apply-report.md` 的"测试结果"表 | aid-applying step3-4 | `aid-applying/templates/apply-report-template.md` | `| AC-2 | sin 渲染 | Calculator.test.mjs AC-2.2 PASS |` |

### 6.2 测试样例（Test Cases）—— **2 个层级**

| 层级 | 在哪里 | 由谁生成 | 形式 | 触发 |
|---|---|---|---|---|
| **单元测试代码** | `tests/*.test.ets` / `*.test.mjs` | aid-applying step3-2-1 通过 `skill('tdd-enforcer')` 强制 | RED → 失败测试代码 | 每个 task 一次 |
| **UI 测试用例** | `ai_auto_test/{date}_{account}/` 下 + 测试源文件 (`TestCase.xlsx` / `.md`) | aid-applying step3-2-2b 通过 `skill('harmonyos-ui-test')` 维护 | Excel/Markdown checkbox list | UI 任务一次 |

> ⚠️ **设计意图**：需求层 AC 在 step4 种下种子；任务层 AC 在 step2-1 继承；测试代码由 tdd-enforcer 在 step3-2-1 "针对任务验收标准写测试"。但**没有任何 skill 强制"边界枚举"**——参见 `根因分析-测试用例生成问题.md:181-189`。

### 6.3 测试执行 —— **3 步走**

| 测试类型 | 命令 | 触发位置 | 强制？ |
|---|---|---|---|
| **单元测试** | `hvigorw test@entry` | aid-applying step3-2-2 | ✅ 必跑 |
| **全量回归** | `hvigorw test@entry`（全量） | aid-applying step3-2-2 | ✅ 必跑 |
| **UI 测试** | hdc 真机/模拟器 + uitest dumpLayout + screenCap | aid-applying step3-2-2b 通过 `skill('harmonyos-ui-test')` | ✅ **铁律 7**：UI 任务必须跑，禁 Node.js mock 替代 |
| **Lint** | `hvigorw lint` | aid-applying step3-2-3 | ✅ 必跑 |
| **集成测试** | （项目自带） | aid-applying step3-2-4 | 条件 |

### 6.4 测试样例生成链路（一张图）

```
delta-spec.md (AC-1, AC-2, ...)                ← aid-planning step4
       │
       │  aid-implementing step2-1 继承 + 拆解
       ↓
tasks.md (Task 1.1, 1.2, ...)
       │ 每个 task 有"验收标准"段
       │
       │  aid-applying step3-2-1 调用 skill('tdd-enforcer')
       ↓
tests/*.test.mjs (RED 失败测试代码)              ← 每个 task 一次 RED-GREEN-REFACTOR
       │
       │  aid-applying step3-2-2 跑 hvigorw test@entry
       ↓
全量单测结果 → 写回 apply-report.md 的 AC 覆盖表
       │
       │  UI 任务 → aid-applying step3-2-2b → skill('harmonyos-ui-test')
       ↓
ai_auto_test/{date}/  +  截图 + dump → 写回 apply-report.md
```

---

## 7. 任务分解链路

### 7.1 拆解步骤

```
aid-planning.step8 (mod-design)
  └─ 生成 delta-design.md（D3.X 模块实现设计）
       │
       │  aid-implementing.step2-1
       │  ├─ 读 delta-design.md 识别代码组件
       │  │  ├─ 数据访问层（DAO / 数据库表）
       │  │  ├─ 业务逻辑层（Service / ViewModel）
       │  │  ├─ 表现层（Component / 页面）
       │  │  └─ 基础设施（EventBus / 常量 / 工具类）
       │  └─ 拆为最小 task（每个 1-2h）
       ↓
tasks.md
  ├─ Task 1.1: {名称}
  │   ├─ 描述
  │   ├─ 涉及文件
  │   ├─ 依赖任务
  │   └─ 验收标准 ←【关键：测试依据】
  ├─ Task 1.2 ...
  └─ ...
```

### 7.2 排序规则（aid-implementing step2-2）

```
基础设施任务（DAO / 常量 / 工具类）
    ↓
核心业务逻辑（Service / ViewModel）
    ↓
UI 表现层（Component / 页面）
```

每个 task 都标 `依赖任务`（无/Task 1.x），形成 DAG。

### 7.3 tasks.md 验收计划段

```markdown
| 任务 | 验收方式 | 验收时间 |
|------|---------|----------|
| Task 1.1 | 代码审查 | {日期} |
| Task 2.1 | 单元测试 | {日期} |
```

---

## 8. 阶段间硬门禁 & 铁律

### 8.1 aid-applying 铁律清单（来自 SKILL.md 原文）

| 编号 | 铁律 | 含义 |
|---|---|---|
| 1 | 用 `build_hap.bat` | 不用裸 `hvigorw`（env 缺失） |
| 2 | TDD 不能跳过 | `skill('tdd-enforcer')` 必调 |
| 3 | **铁律 7**：UI 必真机/模拟器 | 禁 Node.js mock + 源码 grep 替代 |
| 4 | apply-report 数据真实 | 不准捏造 |
| 5 | **Deferred 硬门禁**：UI 任务标 ⏭️ 必须走 4 步降级 | 用户书面同意 + todo.md ⏳+责任人+日期 + capabilities.json 落盘 + hdc 原始输出 |

### 8.2 aid-implementing 约束

- 每个 task 1-2h 内可完成
- 每个 task 有明确验收标准
- 每个 task 有明确输入/输出

### 8.3 aid-planning 全局约束

- step 顺序不可调整
- step 不可跳过
- sub-skill 调用不可绕过
- 必须询问用户的问题不准默认假设

### 8.4 tdd-enforcer 铁律

> **没有失败的测试 → 不写生产代码**

bugfix / 新增 / 重构都强制 RED→GREEN→REFACTOR，无例外。

---

## 9. 关键文件路径模板

| 文件 | 路径模板 | 阶段 |
|---|---|---|
| 变更根目录 | `specs/changes/{YYYYMMDD}-{type}-{name}/` | aid-planning step1 |
| 初始化标记 | `specs/initialized.flag` | aid-init |
| 归档目录 | `specs/archives/{change_name}/` | aid-archiving |
| 知识库（中央） | `skills/monitoring/knowledge-base/{domain}.md` | aid-monitor |
| 知识库（本地） | `specs/guidelines/{domain}.md` | aid-monitor |
| 测试产物（每次） | `ai_auto_test/{YYYY-MM-DD_HHmm}_{account_type}/` | harmonyos-ui-test |
| 单元测试代码 | `entry/src/test/` 或 `tests/` | tdd-enforcer |
| 事件报告 | `specs/changes/{session}/incident-report.md` 或 `specs/guidelines/incidents/{desc}-{YYYYMMDD}.md` | aid-monitor |

---

## 10. 横向 skill（不参与主流程但会旁路调用）

### 10.1 `aid-reviewing`（文档审阅）

- 默认走 **轻量模式**：`concise-dimensions-guide.md` 8 个 D 维度检测
- 用户明确要求才进 **audit mode**：评分 + Critic + 全链路追溯
- 用于：审阅 `delta-spec.md` / `delta-design.md` / `info.md` 等产物
- **与 aid-planning.step9 的关系**：step9 是作者自评；aid-reviewing 是独立审阅

### 10.2 `aid-code-root-cause`（代码层根因）

- 7 个抽象角度：State / Timing / Defaults / Verification / Errors / Resources / Build routing
- 4 层输入：L1 JSONL + L2 worktree + L3 hdc + L4 apply-report
- 与 `aid-analysis-*` 6-skill pipeline 互补（分析流水线）

### 10.3 `aid-analysis-*`（首席诊断 6-skill pipeline）

```
phenomenon → log-scan → spec-code-map → locate-bug → root-cause → output
```

- 用于 issue 诊断（不是开发流程）
- 最终输出 `.claude/analysis-logs/<日期>/issue-<N>-diagnosis.json`

### 10.4 `prd-generator`（独立 PRD 流程）

- 与 aid-workflow 主流程**无依赖**
- 单独用于写 PRD 文档（终端 V2.1 模板）

---

## 附录：跳过的坑（已知失职点，详见根因分析文档）

⚠️ **以下为流程设计** ≠ **实际执行情况**。以下失职点已在 `根因分析-测试用例生成问题.md` 实证：

1. aid-planning step4 的 AC 模板**边界/异常是可选段**（治本需改模板）
2. aid-implementing step2-1 的任务验收标准**无等价类划分**模板
3. tdd-enforcer 只"读取任务验收标准"，**不主动补全边界用例**
4. aid-reviewing 是**死 skill**（0 次被调）—— AC ↔ test 一致性无人审
5. aid-applying 缺**铁律 8**（AC 客观证据硬门禁）—— allow "⏭️ 由 X 覆盖" 虚假 PASS

详见 [根因分析-测试用例生成问题.md](../根因分析-测试用例生成问题.md) § 4-6。

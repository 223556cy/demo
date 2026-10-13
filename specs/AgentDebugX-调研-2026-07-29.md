# AgentDebugX 调研报告

> **调研日期**：2026-07-29
> **调研人**：claude（基于 `https://github.com/AgentDebugX/AgentDebugX` 全量克隆 + 源码阅读）
> **目标仓库**：`https://github.com/AgentDebugX/AgentDebugX/tree/main`
> **本地副本**：`D:\tmp_agentdebugx\AgentDebugX\`
> **关联本地项目**：[d:\huawei\Demo](..) — 1+N 数字员工团队 + AID-Workflow
> **关联文件**：[trace_board_v2.py](..\trace_board_v2.py)、[agents-triggers-and-handoffs.md](..\agents-triggers-and-handoffs.md)、[现有Skill的OHOS能力改进建议.md](..\现有Skill的OHOS能力改进建议.md)

---

## 1. 一句话定位

> **AgentDebugX** 是一个**本地优先（local-first）的 agentic AI 调试框架**，核心做四件事：
>
> **诊断（Diagnose）失败 → 归因（Attribute）到根因 → 恢复（Recover）建议 → 复跑（Rerun）验证修复效果**。

- 主页：<https://www.agentdebugx.com>
- 论文：`arXiv:2607.18754`（2026）— *AgentDebugX: An Open-Source Toolkit for Failure Observability, Attribution, and Recovery in LLM Agents*
- 配套论文：`arXiv:2509.25370`（2025）— *Where LLM Agents Fail and How They Can Learn From Failures*
- 作者机构：**ULab @ UIUC**（Kunlun Zhu 等）
- 协议：MIT，当前版本 **0.3.1（Beta）**，要求 Python ≥3.9
- 包名 `agentdebugx`，导入名 `agentdebug`

---

## 2. 核心范式

两阶段循环，**论文 §4 + README 顶部都强调**：

```text
Diagnose = Detect  →  Attribute  →  Recover
Rerun    = checkpoint  →  retry directive  →  branch execution  →  evaluation
```

| 阶段 | 职责 | 实现位置 |
|---|---|---|
| **Detect** | 从 trajectory 中识别**可见失败信号**（错误、循环、超时、模式违规等） | `src/agentdebug/diagnose/detect/`（deterministic detectors、rule packs、LLM judge、GUI-aware signals、taxonomy induction） |
| **Attribute** | 把失败归因到**具体哪一步 / 哪个 agent / 哪个 tool call** | `src/agentdebug/diagnose/attribute/`（heuristic / all-at-once / step-by-step / bisect / counterfactual / MOE / DeepDebug） |
| **Recover** | 提出**带证据**的修复建议 | `src/agentdebug/diagnose/recover/`（Reflexion / CRITIC / Self-Refine / AutoManual / DeepDebug recovery / saga rollback） |
| **Rerun** | **从某个事件 checkpoint** 重新执行，验证修复是否真有效 | `src/agentdebug/rerun/`（plan / request / branch comparison / HttpLiveExecutor / ProcessLiveExecutor） |

论文里专门强调了一个**很容易踩坑**的点：

> **"Tracing tools show what happened. AgentDebugX focuses on the debugging step that usually comes next"**
>
> 也就是：trace 工具告诉你发生了什么，AgentDebugX 关注**下一步该问什么、谁来负责、怎么验证**。

---

## 3. 仓库结构（实测）

```
AgentDebugX/
├── pyproject.toml                          # Poetry, v0.3.1, Pydantic v1/v2 双兼容
├── README.md                               # 583 行，CLI/Python/UI 全演示
├── docs/
│   ├── ARCHITECTURE.md                     # DeepDebug 内部设计（v1.0, 2026-07-08）
│   ├── TRACE_SCHEMA.md                     # 标准化轨迹/事件/报告契约
│   └── assets/                             # logo / overview 图
├── src/agentdebug/
│   ├── schema/                             # 框架无关的 AgentTrajectory / AgentEvent / DiagnosticReport
│   ├── runtime/                            # 存储、LLM 客户端、事件总线、插件注册
│   ├── ingest/                             # 实时捕获 + 离线导入器
│   │   └── adapters/                       # LangGraph / CrewAI / OpenAI Agents SDK / OTel /
│   │                                       #   Claude Code JSONL / **Hermes** / OpenClaw / GAIA / OSWorld
│   ├── diagnose/
│   │   ├── detect/                         # detectors + rule packs + taxonomy induction
│   │   ├── attribute/                      # heuristic/AAO/step/BS/CF/MOE/DeepDebug
│   │   ├── recover/                        # Reflexion/CRITIC/Self-Refine/AutoManual/...
│   │   ├── profiles/                       # DeepDebug（multi-turn 智能体）
│   │   ├── gui_rca.py                      # CUA / OSWorld GUI 通道
│   │   └── deep_memory.py                  # 长期记忆（基于 SQLite / embedding-cosine）
│   ├── rerun/                              # plan / request / branch / executors
│   │   ├── http_service.py                 # 持久化 HTTP runner（idempotent + 取消 + 重试）
│   │   ├── actor_task.py                   # 导出为待执行 actor 任务（jsonl/parquet）
│   │   └── RUNNER_SPEC.md / SIMULATION_SPEC.md / ACTOR_TASK_SPEC.md
│   ├── inspect/                            # 本地 FastAPI + 无构建 HTML dashboard（端口 7777）
│   ├── hub/                                # 脱敏后可共享的 Error Hub bundle
│   └── integrations/                       # 给宿主 runtime 生成调试 skill（claude / openhands）
├── cua_debugger/                           # 计算机使用 / OSWorld GUI 根因专用工具（独立子项目）
├── examples/
│   ├── basic_usage.py                      # 最小可跑示例（35 行）
│   ├── multi_agent_cascade.py              # 多 agent 级联失败
│   ├── autogen_roundrobin_deepdebug.py
│   ├── taxonomy_induction_demo.py          # 自动归纳失败分类
│   ├── http_agent_runner.py                # live rerun runner 模板
│   ├── live_rerun_runner.py
│   ├── live_use_case_matrix.py
│   ├── llm_judge_demo.py
│   ├── langgraph/  crewai/                 # 各框架适配器示例
│   ├── claude_skill_integration/           # **给 Claude Code 生成调试 skill 的模板**
│   └── debug_skills/                       # Hermes GAIA 真实 trace + 失败案例
└── tests/                                  # 19 个测试模块，pytest + 强制 ≥40% branch coverage
```

---

## 4. 标准化 schema（最值得借鉴的部分）

详见 [docs/TRACE_SCHEMA.md](..\..\tmp_agentdebugx\AgentDebugX\docs\TRACE_SCHEMA.md)。**框架无关的中间表示（IR）** 是整个项目的根基：

```text
AgentTrajectory                     # 一次 agent 运行
└── events: list[AgentEvent]        # 按时间顺序
    └── artifacts: list[Artifact]   # 文件 / 截图 / 状态等非内联证据

DiagnosticReport                    # 与 trajectory 通过 trace_id 关联
├── findings: list[FailureFinding]  # 失败模式 + 证据 + 恢复建议
├── attribution: dict | null        # 归因方法 + 假设 + 主结果
├── recovery: dict | null           # 恢复方法 + 提案
└── audit: list[DiagnosticAuditEntry]  # 4 阶段审计轨迹（DeepDebug 写入）
```

**EventType 标准集合**（17 个，覆盖主流 agent 行为）：
```
run.start / run.end / agent.step / llm.call / llm.response /
tool.call / tool.result / memory.read / memory.write / reflection /
plan / handoff / guardrail / observation / error / human.feedback
```

**关键设计**：每个事件用 `event_id`（不是 `step_index`）做主键。`step_index` 可重复（多 agent / 思考-行动-观察），所以归因和复跑都优先按 `event_id` 解析。

**Artifact 与轨迹解耦**：截图 / 文件 / UI 状态只保留 URI / modality / media_type，**不把字节塞进 JSON**。这对本地大 trace 场景是必要设计。

**报告输出对外过滤 confidence**：Heuristic / DeepDebug 不输出未校准的 confidence，只 LLM Judge 报告保留模型自报值。避免把"看起来很自信"误当成"很对"。

---

## 5. Ingest 适配器矩阵（**和本项目最相关**）

| 适配器 | 来源 | 状态 | 本地相关？ |
|---|---|---|---|
| `messages` / `auto` | 通用 JSON | ✅ | — |
| `openai_agents_spans` | OpenAI Agents SDK | ✅ | — |
| `crewai_events` | CrewAI | ✅ | — |
| `langgraph_callbacks` | LangGraph | ✅ | — |
| `claude_code` | **Claude Code session JSONL** | ✅ | **🟢 完全对应你 264c5a16-*.jsonl 格式** |
| `hermes` | **Hermes session exports** | ✅ | **🟢 直接对应你的 1+N 团队** |
| `openclaw` | OpenClaw session / trajectory | ✅ | — |
| OSWorld / GUI | 计算机使用轨迹 | ✅ | — |
| GAIA / Open Deep Research | 基准 | ✅ | — |
| OpenTelemetry | 通用 OTel | 适配（导出，不是导入） | — |

**直接启示**：本地 [trace_board_v2.py](..\trace_board_v2.py) 当前的轨迹解析是手撸的（见文件头 `TraceNode` / `TraceEdge` / `TraceGraph` dataclass），且本地的 `264c5a16-f4f1-48ff-9f40-d215e1cc2567.jsonl` 没有任何适配逻辑。**AgentDebugX 的 `claude_code` + `hermes` 两个适配器直接覆盖了本项目最常见的两类源**。

---

## 6. DeepDebug：最重磅的组件（设计很值得学）

[docs/ARCHITECTURE.md](..\..\tmp_agentdebugx\AgentDebugX\docs\ARCHITECTURE.md) 是单源真理文档，里面给了一个很清晰的"harness contract"五条款：

> 1. **多轮（Multi-turn）** — 4 macro-turn + conditional arbitration
> 2. **可用工具（Tool-using）** — 统一注册表，文本/ GUI 两通道共享能力
> 3. **环境探测（Env-diving）** — 可以打开 OSWorld 截图 / GAIA 附件，不只是复读 trace
> 4. **知识增强（Knowledge-augmented）** — deep memory + lessons + Error Hub（planned）
> 5. **可审计、类型化的 verdict** — 每个 turn 落审计，最终输出 `DiagnosticReport`

**文本通道**（默认）：固定 4 轮 macro-turn（**经过消融验证** — 自由探索比固定顺序在 Who&When 上低 4.8 严格点）：

| Turn | 名 | 干什么 |
|---|---|---|
| 1 | **Global read** | 整 trace 一遍，命名候选关键步 |
| 2 | **Structure-guided investigation** | 多 agent → 沿 handoff 级联往上；单 agent → 二分 + 重读存活段 |
| 3 | **Cross-examination**（条件） | 若 Turn 1–2 一致 → 接受；否则两侧 ±k 窗口细查仲裁 |
| 4 | **Diagnose & suggest** | 步已定，写 summary + quoted evidence + **一个具体 fix**；verdict 不能再挪步 |

**GUI 通道**（OSWorld）：自由 ReAct 循环，turn 上限，**自动压缩旧截图**避免上下文爆炸。

**评估基线**（仓库自报）：
- **Who&When（n=184，agent + step 定位）**：在 qwen3.5-9b 上**每个指标都赢**（agent 56.0 / 严格 28.8 vs 最佳单基线 47.8 / 21.7）；>40 event 长 trace 的严格定位从 0% → 8%
- **AgentErrorBench**：qwen3.5-9b 上 exact-step 0.170
- **GAIA recovery（n=165）**：诊断 + CRITIC 修复 → 30/61 失败被恢复（81.2%）
- 验收铁律：**任何重做都不许在已汇报单元上回归**（not ship a worse number for narrative reasons）

**对本项目最有价值的部分**：
1. **强制多轮 + 强制审计**：每一步有 `request_summary` + `response_summary` + `duration_ms` + `payload`。本地的 analysis JSON 单子其实只记了"最终结论"，没有过程——这正是 skillopt-01 改不动根因的关键盲区。
2. **"fixed, then verify" 的 Rerun 闭环**：Rerun 必须真跑一遍 actor（不是 simulate 也不是 plan-only），把"修复建议"和"实际效果"绑死。本地 dev-02 跑 12 issue 回归其实已经是这个模式，但**比较机制是 ad-hoc 的**——AgentDebugX 把"原始 trajectory vs rerun branch"做成了显式 `branch comparison`。
3. **Deep memory**：诊断前先 retrieve 相似 past case，写回新案例。完全对应 [agents-triggers-and-handoffs.md](..\agents-triggers-and-handoffs.md) §3.4 里的 `.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-diagnosis.json`，但本地目前是**人写而不是自动 retrieve**。

---

## 7. Rerun 三模式 + 强边界

[src/agentdebug/rerun/README.md](..\..\tmp_agentdebugx\AgentDebugX\src\agentdebug\rerun\README.md) 把"复跑"分成三个有明确边界的模式：

| 模式 | 触发 | 真实执行？ | 适合场景 |
|---|---|---|---|
| `plan-only` | `--plan-only` | ❌ 仅写 workflow JSON / actor-task | 上传轨迹、交给外部 runtime |
| `simulate` | `--simulate` | ❌ LLM 生成 hypothetical trajectory | 纯 prompt 实验，**不证明任务被修复** |
| **live** | `--runner NAME` 或 `--runner-command` | ✅ 真跑框架 | 唯一能"验证修复"的方式 |

**强约束**（本地特别要注意）：
- `HttpLiveExecutor`：**idempotent**（防止重试生成重复 actor）、transient failure 有界 backoff、超时 / 网络失败后 best-effort cancel、要求提交后做 capability handshake
- `ProcessLiveExecutor`：兼容性后路，本地脚本和 CI 还能用
- 一个 chat-completions URL **不等于** Agent environment —— runner 必须拥有 framework、real model、tools、credentials、job 生命周期
- Browser **不接收** runner command / bearer token（防止前端误用）
- `from_event` checkpoint 需要 runner 显式支持"从事件 N 继续"语义

**对本地的直接价值**：dev-02 的"12 issue 回归"目前是脚本式触发（[agents-triggers-and-handoffs.md](..\agents-triggers-and-handoffs.md) §5.5 4 步工作流）。如果用 AgentDebugX 的 `HttpLiveExecutor`，能拿到：

- **真正的 branch comparison**：原 trajectory vs 新 trajectory，自动 diff 失败模式 / 步数 / 终止事件
- **能力握手**：dev-02 runner 必须声明"我有 OTel / 我有 hdc / 我有 hermes profile"，缺哪个直接报错
- **失败任务的 actor-task dataset 导出**：jsonl / parquet，方便喂给 Langfuse 之类的评测平台（与 [langfuse-upload-classifier-policy.md](..\.claude\projects\d--huawei-Demo\memory\langfuse-upload-classifier-policy.md) 联动）

---

## 8. Inspect / Hub / Integrations 三个周边

### 8.1 本地 Inspect UI
- 无构建 FastAPI + HTML/CSS/JS
- 端口 7777（默认）
- 路由 / 视图 / 服务三层分离：`inspect/ui/{routes,views,services,branch_store}.py`
- 浏览器**不持久化** LLM key / runner token（tab 关闭即丢）
- 故意做成"薄壳"，业务逻辑留在 `diagnose/`

### 8.2 Error Hub
- bundle = `BundleManifest` + `AgentTrajectory` + 可选 `DiagnosticReport` + 可选 artifact 路径
- schema_version = `1.0.0`（**只覆盖 manifest 和目录布局，不覆盖 record schema**）
- 默认对 goal / metadata / event.input-output-error 做密钥 + PII 脱敏，**不**扫描 artifact 文件内容
- 本地 trace 存储**不会**自动脱敏——发布前必须主动 scrub

### 8.3 Integrations
最惊艳的一条 CLI：

```bash
agentdebug integrations skill --platform claude --target .claude/skills
```

**直接给 Claude Code 生成调试 skill**。结合 [examples/claude_skill_integration/](..\..\tmp_agentdebugx\AgentDebugX\examples\claude_skill_integration) 看，生成产物是：

- `SKILL.md` — 按 setup / CLI / format / analysis / recovery / safety 拆分，**不**让 host agent 加载一个巨型 instruction
- `artifacts/`、`scenarios.json` — 用来测试 skill 是否真的被触发、是否真的调对了 `agentdebug` 命令、答案是否被正确 hedge

这正好覆盖你团队当前的痛点：[现有Skill的OHOS能力改进建议.md](..\现有Skill的OHOS能力改进建议.md) §2.6 说"aid-reviewing 默认是轻量模式，不强制核验 OHOS 事实"——如果给 skillopt-01 配一个 AgentDebugX 生成的 Claude skill，**对 issue → diagnosis JSON 的桥接就可以标准化**。

---

## 9. 与本地项目对比

### 9.1 维度矩阵

| 维度 | 本地（[d:\huawei\Demo](..)） | AgentDebugX |
|---|---|---|
| **标准化 schema** | [trace_board_v2.py](..\trace_board_v2.py) 自定义 `TraceNode` / `TraceEdge` / `TraceGraph` / `ArtifactVersion` / `BashClassification` | 工业级 `AgentTrajectory` + `AgentEvent` + `Artifact` + `DiagnosticReport` + 17 个 `EventType` |
| **Ingest 适配器** | 仅手写解析 Claude Code JSONL | 8 类源（claude_code / hermes / openclaw / langgraph / crewai / openai-agents / otel / osworld）+ `auto` 自动检测 |
| **归因算法** | 人写 7+ 篇 [根因分析-*.md](..) 文档 + analysis agent | heuristic / all-at-once / step-by-step / bisect / counterfactual / MOE / DeepDebug |
| **恢复策略** | analysis JSON 单子里的 `optimization_direction` 字段 | Reflexion / CRITIC / Self-Refine / AutoManual / DeepDebug recovery / saga rollback |
| **闭环验证** | dev-02 跑 12 issue 回归（脚本） | HttpLiveExecutor + ProcessLiveExecutor + 三模式边界 + branch comparison |
| **长期记忆** | [agents-triggers-and-handoffs.md](..\agents-triggers-and-handoffs.md) §3.4 写 JSON 到 `.claude/analysis-logs/`，但**没有人 retrieve** | Deep memory（SQLite + embedding-cosine）+ Error Hub retrieval |
| **失败分类法** | A/B/C/D 四类（agents-triggers-and-handoffs.md §3.4） | `SEED_FAILURE_MODES` 内置 + taxonomy induction（自动归纳） |
| **审查 UI** | Streamlit `trace_board_v2.py` | FastAPI no-build（端口 7777）+ 浏览器不持久化敏感数据 |
| **错误共享** | GitHub issue / PR（强耦合到组织） | Error Hub bundle（脱敏、可导入本地） |
| **Skill 生成** | skillopt-01 手工改 + CP .bak | `agentdebug integrations skill --platform claude` 一键生成 |
| **隐私模型** | 本地 + GitHub（强耦合） | 本地优先 + opt-in sharing + scrubber |

### 9.2 范式同构点（**巧合得令人发指**）

| AgentDebugX | 本地 1+N 团队 |
|---|---|
| Detect（找失败信号） | analysis 接 `analysis:pending` 标签 / 任何 closed issue |
| Attribute（归因） | analysis 写 `issue-<N>-diagnosis.json` |
| Recover（修复建议） | analysis 的 `optimization_direction` 字段 |
| Rerun（验证修复） | dev-02 跑 12 issue 回归 |
| Skill（产物） | skillopt-01 改 AID-Workflow skill |
| Error Hub | `.claude/analysis-logs/` + GitHub issues |
| Deep memory retrieval | **❌ 当前缺失**，analysis 单子之间互不引用 |

**这不是同义词巧合，是 AgentDebugX 的论文团队显然也是同样的工程师。** 你的本地系统在**流程骨架上**已经做对了，**只是缺失了它的算法、标准化和闭环比较机制**。

### 9.3 本地有但 AgentDebugX 没有的（**别被它替换掉**）

| 维度 | 本地专长 |
|---|---|
| **OHOS / ArkUI 事实核验** | [现有Skill的OHOS能力改进建议.md](..\现有Skill的OHOS能力改进建议.md) 整套 API 证据矩阵 + UNCERTAIN 门禁 + ArkUI 状态传播图 + 布局约束表 |
| **设备真机验证** | hdc dump + 截图 + bounds 断言 + 媒体解码 |
| **AC 完备性** | aid-planning 的 delta-spec AC 模板 + tdd-enforcer 强制 RED-GREEN |
| **跨阶段门禁** | rq-codebase / aid-applying 的"实施期 API 偏离 → design-amendment" |
| **Cron + 多 Profile 编排** | 1+N 团队的 hermes profile + cron 注册 + GitHub PAT 隔离 |

**AgentDebugX 是 agent 的医生，不是 ArkUI 的医生。** 它帮你回答"为什么这个 agent 跑挂了"，但不回答"为什么 @State 变了 ForEach 没刷新"。

---

## 10. 集成建议（按优先级）

### P0 — 单点替换，立刻受益

| 改造 | 现状 | 改造后 | 工作量 |
|---|---|---|---|
| **Claude Code trace 解析** | [trace_board_v2.py](..\trace_board_v2.py) 手撸 dataclass | `agentdebug ingest --format claude_code --out trace.json` 输出 `AgentTrajectory` | 半天 |
| **analysis 的 RCA 输出** | 手写 `phenomenon` / `root_cause_analysis` / `optimization_direction` | `agentdebug diagnose --mode deepdebug --attributor moe --recovery deepdebug --out diag.json` 输出 `DiagnosticReport`（带 4 阶段审计 + 证据引用 + 修复指令） | 1 天 |
| **Skill 生成** | skillopt-01 手工改 + CP .bak | 至少用 `agentdebug integrations skill --platform claude --target .claude/skills/agentdebugx` 生成一个**标准化的 Claude Code debugging skill**，作为 skillopt-01 的参考实现 | 半天 |

### P1 — 闭环升级

| 改造 | 改造后 |
|---|---|
| **dev-02 跑 12 issue 回归** | dev-02 runner 用 AgentDebugX 的 `HttpLiveExecutor` 协议，提供 `/runs` `/runs/{id}` `/runs/{id}/events` 三个端点；agentdebug rerun 自动做 branch comparison，输出"原始 vs 新 trajectory"的 diff JSON |
| **analysis 单子间 retrieval** | 用 `DeepMemoryStore`（`deep_memory.py`）把 `.claude/analysis-logs/` 里的诊断 JSON 当 past case，diagnose 前先 retrieve top-k 相似案例，写回时通过 `MemoryReference` |
| **Error Hub 作为 fixture corpus** | 把 12 issue 里的失败案例打包成 `BundleManifest` + 脱敏轨迹 → `agentdebug hub push --to local:./fixtures`；analysis / dev-02 都从这个 hub 取 |

### P2 — 长期

| 改造 | 说明 |
|---|---|
| **失败分类法合并** | 本地 A/B/C/D 与 `SEED_FAILURE_MODES` 做映射；用 `taxonomy_induction` 自动从历史 根因分析-*.md 里归纳新分类 |
| **Taxonomy → Skill hint** | 把 OHOS 失败模式（如"ArkUI 状态未传播"）注册成新的 `failure_mode`，让 DeepDebug 在文本通道里也能识别 OHOS 失败 |
| **本地 trace UI 升级** | 把 [trace_board_v2.py](..\trace_board_v2.py) 的 Streamlit 拆成两层：解析用 AgentDebugX schema，可视化仍保留 Streamlit；最终目标是 `agentdebug serve` 直接出图 |

---

## 11. 风险与注意事项

1. **网络与 PyPI**：当前环境被企业策略拦截 pypi.org / npmjs.com。`pip install agentdebugx` 必须在能访问外网的机器或代理下跑。**先在能联网的沙箱试通，不要直接装生产环境**。
2. **Pydantic 双兼容**：项目同时跑 v1 / v2（`pydantic = ">=1.10,<3.0"`），所以 `model_to_json` / `model_to_dict` 都要走公共 helper，不能直接调 Pydantic 方法。本地如要嵌入，先确认 Python 环境是哪个版本。
3. **schema 没有 record-level version**（[TRACE_SCHEMA.md](..\..\tmp_agentdebugx\AgentDebugX\docs\TRACE_SCHEMA.md) §12）：破坏性字段改名**不会**自动迁移。本地要**只加字段、加默认值**，不要删。
4. **Confidence 公开过滤**：本地如果把 `DiagnosticReport` 直接喂给 [现有Skill的OHOS能力改进建议.md](..\现有Skill的OHOS能力改进建议.md) 那种自动评审，要记得 Heuristic / DeepDebug 报告**不带 confidence**——评审脚本不能假设一定有 confidence 字段。
5. **Rerun 必须真跑 framework**：本地 dev-02 的"模拟器不可用 → skipped"逻辑（[agents-triggers-and-handoffs.md](..\agents-triggers-and-handoffs.md) §10）和 AgentDebugX 的"plan-only 模式"语义**接近但不等价**——AgentDebugX 的 plan-only 是"上传 + 等外部 runtime"，skipped 是"压根没上传"。要明确区分。
6. **Skill 集成不是 demo**：仓库 README §"Current Findings" 明确说"agent-invoked root-cause analysis over trajectories, not a live tracing UI"——它**不是 trace 工具**，别误用成 observability 平台。
7. **CUA / OSWorld 子项目独立**：`cua_debugger/` 是 AgentDebugX 内部为 GUI 失败做的额外工具，对本地 OHOS 调试**没有直接用处**，但 `gui_rca.py` 的 ReAct loop 设计值得借鉴到鸿蒙的 hdc dump 上。

---

## 12. 参考资源

| 资源 | 链接 |
|---|---|
| GitHub | <https://github.com/AgentDebugX/AgentDebugX> |
| 主页 | <https://www.agentdebugx.com> |
| 论文（toolkit） | <https://arxiv.org/abs/2607.18754> |
| 论文（agent failure） | <https://arxiv.org/abs/2509.25370> |
| Demo 视频 | <https://youtu.be/ztni6w0o_l8> |
| 本地克隆 | `D:\tmp_agentdebugx\AgentDebugX\` |
| README | [README.md](..\..\tmp_agentdebugx\AgentDebugX\README.md)（583 行） |
| Architecture | [docs/ARCHITECTURE.md](..\..\tmp_agentdebugx\AgentDebugX\docs\ARCHITECTURE.md) |
| Trace Schema | [docs/TRACE_SCHEMA.md](..\..\tmp_agentdebugx\AgentDebugX\docs\TRACE_SCHEMA.md) |
| Ingest 工作流 | [src/agentdebug/ingest/README.md](..\..\tmp_agentdebugx\AgentDebugX\src\agentdebug\ingest\README.md) |
| Rerun 工作流 | [src/agentdebug/rerun/README.md](..\..\tmp_agentdebugx\AgentDebugX\src\agentdebug\rerun\README.md) |
| Runner 协议 | [src/agentdebug/rerun/RUNNER_SPEC.md](..\..\tmp_agentdebugx\AgentDebugX\src\agentdebug rerun\RUNNER_SPEC.md) |
| Simulation 协议 | [src/agentdebug/rerun/SIMULATION_SPEC.md](..\..\tmp_agentdebugx\AgentDebugX\src\agentdebug rerun\SIMULATION_SPEC.md) |
| Actor Task 协议 | [src/agentdebug/rerun/ACTOR_TASK_SPEC.md](..\..\tmp_agentdebugx\AgentDebugX\src\agentdebug rerun\ACTOR_TASK_SPEC.md) |
| Claude Skill 集成示例 | [examples/claude_skill_integration/README.md](..\..\tmp_agentdebugx\AgentDebugX\examples\claude_skill_integration\README.md) |
| Debug Skills 案例 | [examples/debug_skills/README.md](..\..\tmp_agentdebugx\AgentDebugX\examples\debug_skills\README.md) |

---

## 13. 一句话总结

> **AgentDebugX 是本地 1+N 团队在 agent 层做的事的工业化版本**——你的 `analysis → skillopt-01 → dev-02` 闭环在**算法和协议层**就是 AgentDebugX 的 Detect → Attribute → Recover → Rerun。
>
> 短期把它当**标准化 ingest + 归因算法 + Skill 生成器**用，长期用它做**闭环 branch comparison 和 past-case retrieval**，但**别替换 OHOS / ArkUI / hdc 这一层**——这是 AgentDebugX 完全不覆盖的领域。
>
> 推荐优先级：**P0 三个单点替换（半天到一天）** → **P1 闭环升级（1 周）** → **P2 与 OHOS 失败分类法合并**。
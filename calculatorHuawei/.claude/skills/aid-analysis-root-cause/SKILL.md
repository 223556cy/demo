---
name: aid-analysis-root-cause
description: |
  根因推理 + 靶点定位 + 修复设计 (analysis pipeline 步骤 5/6): 在首席诊断任务中执行
  11 步推理方法论 (B-0 方法选择 / B-1 事实抽取 / B-2 因果链 / B-3 so why 穿透 / B-4 A/B/C/D 归类 /
  B-5 反事实 / B-6 备选链 / B-7 证据强度 / B-8 anti-bias / B-9 多 bug 穷尽 / B-10 运行时证据 /
  B-11 零状态) + 4 步靶点定位 (C-0 精确定位 / C-1 通用性 / C-2 结构化修复 / C-2.1 覆盖矩阵) + 优先级判定,
  含**修复路径判定**: 改现有 skill (modify-existing) vs 创建新 skill (create-new) vs N/A。
  引用 10 个 problem_signature 签名库和 5 个锚点案例。
  当用户说"根因"、"推理方法"、"靶点"、"签名"、"因果链"、"修复路径"或类似表述时触发。
compatible: ["calculatorHuawei-main"]
---

# aid-analysis-root-cause Skill

## 概述

本 skill 是 analysis 6-skill pipeline 的**第 5 步**,负责**从"哪里有错"→"为什么错"→"怎么修"**。

**核心约束**:
- **必带因果链**: `root_cause_analysis` 必须含 `fact → [机制: ...] → fact` 的箭头链(铁律 #14)
- **必填结构化修复**: `optimization_direction` 是 6 字段 dict,不是字符串(铁律 #11)
- **必填修复路径**: `fix_path` 3 选 1(`modify-existing` / `create-new` / `N/A`)
- **必填覆盖矩阵**: `fix_coverage_matrix` 覆盖主链 L3 + 所有 additional L3(铁律 #18)

```
Pipeline 顺序:
1. aid-analysis-phenomenon
2. aid-analysis-log-scan
3. aid-analysis-spec-code-map
4. aid-analysis-locate-bug
5. aid-analysis-root-cause  ← 本 skill
6. aid-analysis-output
```

## 输入(从前置 skill)

- `phenomenon` + `phenomenon_sources`: 来自 `aid-analysis-phenomenon`
- `log_anchors[]` + `error_summary`: 来自 `aid-analysis-log-scan`
- `spec_to_code_mapping[]` + `coverage_pct`: 来自 `aid-analysis-spec-code-map`
- `bug_location` + `signals[]`: 来自 `aid-analysis-locate-bug`

## 工作流(15 步)

### 步骤 B-0. 推理方法选择

诊断前先**选方法**,不要拿到现象就直接推理。同一现象用错方法 = 推理力量下降 50%。

5 种方法(详见 [references/reasoning-methods.md](references/reasoning-methods.md)):

| 方法 | 适用 | 推理方向 | 锚点 issue |
|------|------|----------|-----------|
| **演绎 (deductive)** | 现象有 SKILL.md 显式规则可对照 | 规则 → 检查应用情况 | **#25** (signoff/4 要素/checkbox 都有规则但漏跳) **#29** (降级强制块存在但被跳过) |
| **归纳 (inductive)** | 多现象 / 多失败指向同一处 | 失败清单 → 抽象共同缺失 | **#27** (整套环境探测失败 → 抽象到"缺 tconn") |
| **溯因 (abductive)** | 现象无明确规则, 多个解释都合理 | 现象 → 最可能根因 (奥卡姆) | **#26** (单测全过 UI PASS 还出 fix commit → 抽象到"等价类指标模糊") |
| **类比 (analogical)** | 现象与历史案例相似 | 历史根因 → 当前套用 → 验差异 | 跨 issue 共性识别 (见 [references/case-library.md](references/case-library.md)) |
| **反证 (counterfactual)** | 现象需排除其他解释 | 假设 → 反驳/确认 (other things didn't happen) | **#27** (rev-01 反证: 跑通 → 环境实际可用) |

**铁律**: B-0 必须先**列 ≥ 2 个候选方法**,用不同方法攻击同一现象,看哪个站得更稳。单方法 = 推理脆弱。

写入 JSON `reasoning_method` 字段 (primary + secondary, 例 `["abductive", "analogical"]`)。

### 步骤 B-1. 提取客观事实(5 类来源,3-7 条)

| 来源 | 何时必须读 | 例 |
|------|-----------|------|
| **session jsonl** | 默认, 永远要读 | `jsonl#3 assistant#L420 - 调 Skill aid-applying, 产物未生成` |
| **SKILL.md 静态规则** | 涉及 skill 行为时必读 | `aid-applying/SKILL.md#L555 commit 命令模板缺 --signoff` |
| **源码** | 涉及 default value / magic number / 命名语义时必读 | `PreferencesStore.ets#L65 DEFAULT_PREFERENCES.radiansDefault = false` |
| **config 文件** | 涉及配置驱动的行为时必读 | `.claude/capabilities.json ui_test.emulator_status = 'running' (stale)` |
| **运行时证据** | 涉及行为/时序/状态机时必读 (见 B-10) | `hilog: evalAt_in deg=true (运行时实际按角度算)` |

> **覆盖要求**: 至少覆盖 2 类来源。如果只读 jsonl 找不到 ≥ 3 条事实, 必须扩到 SKILL.md / 源码 / 运行时。
> **严禁把"推断"当"事实"**。助手说"应该是这样"不算事实, 必须有 tool 调用 / 文件内容 / 运行时输出的字面证据。

### 步骤 B-2. 构造因果链(强制 `[机制: ...]`)

用箭头把事实串成一条链,**严格格式**:
```
fact_a ([源]L#) → [机制: ...] → fact_b ([源]L#) → [机制: ...] → root_cause_layer
```

**关键升级**: 每环箭头之间必须有 **机制说明**(一句话解释为什么 fact_a 必然导致 fact_b),不允许裸箭头 `→`。

**机制说明硬要求**:
- 必须能说出 **物理/逻辑机制**(e.g. "因为 setTimeout 异步, 回调在 loadPrefs 完成前已经触发 compute")
- 不准用同义反复(e.g. "因为 X 发生 → 所以 X 发生" = 废)
- 不准用时间先后代替因果(e.g. "A 在 B 之前 → A 导致 B" 不算, 还需机制)

**反事实强化**:
- 不仅验证"补上根因层 → 现象消失"
- 还要预测"如果根因是真,**还应该有 Y 现象/还应该解释 Z 现象**",验证 Y/Z 是否真观察到
- 例: 根因="radiansDefault=false 默认值错", 预测="新装用户必现 + 改过偏好的用户绕开", 验证 ✅

如果存在另一条也能解释的链 → 列出备选链,用反证 (other things didn't happen) 排除。链条最后一环必须是 **可干预的根因层**(即改了 SKILL.md / 源码 / config 就能破的层)。

### 步骤 B-3. so why 穿透验证(≥ 3 层)

| 层 | 描述 | 例子 (错误 → 正确) |
|----|------|--------------------|
| L1 现象层 | 表面征兆 | "apply-report.md 缺失" |
| L2 流程层 | 流程哪一步没强制 | "step 5 没 imperative 验证产物存在" |
| L3 根因层 | skill 的根本假设漏洞 | "skill 假设子 agent 跑完产物就一定落盘, **没有自我审计步骤**" |

**只把 L3 写入 root_cause_analysis**。L1/L2 是过程,不进 JSON。

### 步骤 B-4. A/B/C/D 归类

链条建好后才允许归 A/B/C/D:
- **A. 幻觉乱写** — skill 没要求, claude 自己加了(改 claude 行为要靠 prompt 显式约束)
- **B. 漏掉步骤** — skill 流程里缺一步(要加 imperative 规则)
- **C. 理解偏差** — skill 规则存在但措辞歧义(要改写措辞)
- **D. 外部因素** — 不是 skill 的问题(e.g. 网络、SDK 缺失、用户描述不清)
  - 此时 `target_skill_filename = 'N/A'`, `fix_path = 'N/A'`

> 注意: A/B/C 是 skill 缺陷的 3 种形态,但优化手段不同 — A 要"加禁止", B 要"加强制", C 要"加精确"。

### 步骤 B-5. 反事实验证

对根因层做反事实: "**如果把根因层这一步补上**, 现象(步骤 A)还会发生吗?"
- **补上 → 现象消失** ✓ 真因(链条成立)
- **补上 → 现象还在** ✗ 链条漏环, 回 B-1 补事实

例: 根因 = "skill 缺自我审计步骤" → 反事实 = 加上 step 5.5"验证产物落盘" → apply-report.md 就能生成 → 现象消失 ✓

### 步骤 B-6. 备选链与排除理由(≥ 1 条)

⚠️ **单一链条 = 推理脆弱**。必须列出 **≥ 1 条** 备选根因解释,用**反证**说明排除原因:
- "备选 X 不成立, 因为 [事实 Y 直接反驳] / [关键现象 Z 没观察到]"
- 如果排除理由是"没证据"或"听起来不太可能", 说明链条没穿透够 — 回 B-1 补事实

写入 JSON 的 `alternative_branches_excluded` 字段。

### 步骤 B-7. 证据强度评级

| 强度 | 含义 | 例子 |
|------|------|------|
| `literal` | 字面引用(tool_result stdout / 评论原话 / 产物内容) | "jsonl#3#L420 tool_result: 'apply-report.md created'" |
| `inferred` | 从字面合理推断(1 步逻辑) | "jsonl#3#L420 调了 Skill aid-applying → 推断进入它的 step 5" |
| `speculated` | 仅推测, 无直接证据 | "claude 可能漏读了 X" |

> **铁律**: `speculated` 不准作为根因层 (L3) 的唯一支撑。写出来行, 但不能当证据。

### 步骤 B-8. Anti-Bias 自检

| 偏差 | 自问 | 修正动作 |
|------|------|----------|
| **Confirmation bias** | 是否只找了支持预设根因的证据? | 强制写 B-6 备选链 + 反证 |
| **Anchoring** | 是否被第一个观察牵着走, 没考虑其他解释? | 重读 phenomenon, 列 ≥ 2 个独立解释 |
| **Premature closure** | 看到第一个合理解释就停了吗? | 强制 so why ≥ 3 层 |
| **Recency bias** | 是否被最后一个证据带偏? | 按时间线重排所有证据 |

√ 4 项全部通过才能写 JSON;任一不通过 → 回 B-2 重建链条。

### 步骤 B-9. 多 bug 穷尽探测

**穷尽检查 3 问**:
1. **同现象双解**: 这个现象如果剥离"机制上独立的因素"还能不能复现?
2. **同路径双因**: 同一代码路径上, 还有哪个"看起来对但其实错"的分支未审计?
3. **同上下文双陷阱**: 同一概念/命名/字段上, 还有没有第二个 silent 默认 / 反向映射?

**穷尽通过判定**:
- 3 问都明确"否"(此现象已被完整解释) → 主链单一, 写 `root_cause_analysis` 单链
- 任意一问答"是 / 不确定" → 触发**多 bug** 模式:
  - 主链写 `root_cause_analysis` (字符串)
  - 其他链写 **`additional_root_causes`** JSON 数组
  - `problem_signature` 升级为 **`multi-bug-discovered`**

### 步骤 B-10. 运行时证据强制(行为类 bug 必填)

**哪些 bug 必须有 runtime 证据**(强制):
- ✅ 状态机切换 / 模式翻转(e.g. 角度↔弧度、登录态、深浅色)
- ✅ 时序竞态 / 异步回调顺序(e.g. setTimeout / Promise / 事件循环)
- ✅ 跨进程通信(e.g. hdc shell、await preload)
- ✅ 计算结果偏差(e.g. evaluateAt 数值、序列化反序列化)
- ✅ UI 渲染(e.g. 控件显示、动画、布局)

**哪些 bug 静态证据就够**: API 拼写错误 / 类型不匹配 / 缺导入 / SyntaxError / 类型签名错 / 静态常量定义错。

**runtime 证据要求**(写入 JSON `runtime_evidence` 数组):
```json
{
  "evidence_type": "<hilog | screenshot | dump | logcat | trace | replay>",
  "source_path": "<绝对路径 / 设备 ID>",
  "key_observation": "<一句话指出证明什么>",
  "interpretation": "<怎么读这个 runtime 输出>"
}
```

### 步骤 B-11. 零状态 / 默认路径(3 个零状态)

| 零状态 | 检查方式 | 案例 |
|--------|---------|------|
| 🔵 **零数据** | 新装 / 空数据库 / 第一次启动 后行为 | rev01_second_bug: 新装用户 PreferencesStore 没 key → 走默认 → 触发 bug |
| 🔵 **默认配置** | config default values 是不是"对的方向" | rev01_second_bug: `radiansDefault=false` 默认值反向, 改过偏好的用户反而绕开 |
| 🔵 **冷启动** | 重启 / 杀进程后第一次调用 | 时序竞态类 bug 常在冷启动必现, 热路径不现 |

**写入 JSON `zero_states_checked`** (3 个):
```json
{"state": "<zero-data | default-config | cold-start>", "finding": "<必现 / 绕开 / 未测>"}
```

未测 = 必须测, 不准写"not-applicable"(除非真的不适配)。

### 步骤 C-0. 精确定位(skill + section + 行号)

候选 skill 花名册(从以下**唯一**选一个):
- `aid-planning` / `aid-implementing` / `aid-applying` / `tdd-enforcer`
- `rq-parse` / `rq-clarify` / `rq-codebase`
- `mod-design` / `aid-init` / `aid-archiving` / `aid-monitor` / `aid-reviewing`
- `dfr-fmea-harmony` / `harmonyos-ui-test` / `prd-generator`

> 注意: `aid-analysis-*` 6 个新 skill **不在此花名册**(它们是 analysis 的辅助,不是 dev-01/rev-01 用的 skill,不会成为 target_skill)。

**唯一性铁律**: 同时指责多个 skill = 失职。选**最直接**造成失败的那一个。

定位到 skill 后, 必须再往下钻 2 层:
1. `target_skill_section`: SKILL.md 内的具体 section / step 编号或标题
2. `target_line_range`: 该 section 在 SKILL.md 中的行号范围(**必须用 Read 工具实际查过** SKILL.md, 不允许估算)

**验证铁律**: dispatch 用 Read 验证 section 标题/行号是否真的存在于对应 SKILL.md, 不存在则拒收。

### 步骤 C-1. 通用性体检(3 问)

⚠️ **致命陷阱**: 只针对本次 issue 修 → 后续 N 个 issue 还会犯同样的错。

定位靶点后, **必须**问自己 3 个问题:
1. **横向覆盖**: 这个 skill 还被哪些其他 issue 场景调用过?(扫最近 10 个 dev-01 session)
2. **纵向延伸**: 这个 skill 在 AID 主链中, 上游/下游还有谁依赖它的产物/契约?
3. **未来场景**: 这个根因是否会在**新功能开发**(而不是修 bug)中也触发?

只有 ≥ 2 个"是" → 才是**通用性问题**, priority 至少 MEDIUM。三问都"否" → 才允许归 D 类外部因素。

### 步骤 C-2. 结构化修复(6 字段对象)

把 `optimization_direction` 从**字符串**升级成**结构化对象**(必须 dict, 铁律 #11):

| 字段 | 必填内容 |
|------|----------|
| `fix_action` | 动词开头, 精确到 step + 行号的修改动作, **多 bug 时用 #1, #2 编号** |
| `fix_rationale` | 为什么这么改, 引回逻辑链 L3 根因 |
| `future_scenarios_covered` | 覆盖的未来场景 **≥ 2 类** |
| `related_skills_to_sync` | 需要联动改的其他 skill(空数组 = 不需要) |
| `acceptance_criteria` | 怎么验证改对了(具体可执行, 非"观察") |
| `revert_plan` | 改坏了怎么回滚(一行, 含具体动作) |

A/B/C 三类缺固定范式:
- A 类(幻觉乱写)fix_action 通常是"加禁止 (must not)"在 prompt 显式约束
- B 类(漏掉步骤)fix_action 通常是"加强制 (must)"加 imperative 规则
- C 类(理解偏差)fix_action 通常是"加精确"重写歧义措辞
- D 类(外部因素)fix_action 通常是"升级降级流程"或"记入 aid-monitor 监控"

### 步骤 C-2.1. 修复覆盖矩阵(闭环铁律)

⚠️ **多 bug 场景**: B-9 探测到 N 个根因 → 必须有 N 个 fix_action, 每个 fix_action 必须**显式映射**到对应根因。

**矩阵字段**(写入 JSON `fix_coverage_matrix` 数组):
```json
{
  "l3_anchor_id": "<对应主链或 additional_root_causes 的根因 ID>",
  "covered_by": "<fix_action#1 | fix_action#2 | ... | N/A>",
  "covered": <true | false>,
  "evidence": "<一句话说明 fix 怎么破这个根因>"
}
```

**铁律**:
- 每个 L3 根因(主 + 副)**必须**有一行 coverage 记录
- 任一 `covered: false` → dispatch 拒收(修不全不准 merge)
- `N/A` 仅用于"故意不修"且写了原因

### 步骤 C-3. 修复不完整时的处置

- **人为明知不全**: 故意不修某 L3 → 写 `N/A` + 在 `fix_rationale` 写原因
- **遗漏未知不全**: 写到 JSON 时漏行 → dispatch 拒收 + 报错回分析员重写
- **跨 issue 修复**: 当前 issue 修一部分 + 开新 issue 修另一部分 → 在 fix_action 注明 "(剩余部分由 issue#M 处理)"

### 步骤 D. 优先级判定

- **HIGH** — 阻塞发布 / 影响 30% 以上 issue / 安全相关 / 通用性 ≥ 3 类未来场景
- **MEDIUM** — 影响 10-30% issue / 体验问题 / 通用性 = 2 类未来场景
- **LOW** — 偶发 / 边缘场景 / 仅本次 issue 特发 / 文档改进

> 通用性是 priority 的**强加分项**(C-1 通过 → 至少 MEDIUM)

### 步骤 E. 修复路径判定(关键: fix_path)

**3 选 1**:

| 场景 | `fix_path` | `target_skill` | `proposed_skill_*` |
|------|------------|----------------|-------------------|
| 现有 15 个 skill 中有 skill 流程能涵盖此根因 | `modify-existing` | **必填**(从 C-0 花名册选) | — |
| 根因落在两个 skill 边界处,都不完全负责 / 现有 skill 责任不重叠 | `create-new` | — | **必填**(`proposed_skill_name` + `proposed_skill_purpose`) |
| 根因是"用户描述不清" / "环境问题" / "工具链缺失" | `N/A` | `"N/A"` | — |
| 根因是"现有 skill 都对但用户没调用"(流程问题) | `N/A` | `"N/A"` | 建议给老板"加提示"而非"建 skill" |

**create-new 判定启发**:
- 现有 15 个 skill 中,**没有任何**一个能涵盖此根因的流程
- 根因属于"跨 skill 边界" / "全新工作流"(如本次拆分出的 6 个 aid-analysis-* 就是 create-new 范本)
- 给出 `proposed_skill_name`(沿用命名族)+ `proposed_skill_purpose`(一句话描述职责)

**铁律**:
- `fix_path` 必填, 3 选 1
- `modify-existing` 时 `target_skill_filename` 必须从 C-0 花名册选(不存在的 skill 名 dispatch 拒收)
- `create-new` 时 `proposed_skill_name` 必填且不含空格 / 特殊字符
- `N/A` 时 `target_skill_filename = "N/A"`, `optimization_direction` 允许空 dict

### 步骤 F. 多维度分类(4 字段)

写入 JSON:
- `defect_dimension`: `planning-stage` / `implementing-stage` / `applying-stage` / `archiving-stage` / `cross-stage`
- `discovery_timing`: `review` / `integration` / `production` / `self-found` / `regression`
- `reasoning_method`: 见 B-0(数组, primary + secondary)
- `problem_signature`: **必须从签名库的 10 个里选, 不准自创**(详见 [references/signature-library.md](references/signature-library.md))

## 输出字段(供 `aid-analysis-output` 序列化)

```json
{
  "root_cause_analysis": "fact_a → [机制: ...] → fact_b → [机制: ...] → L3 根因 (归类 X)",
  "additional_root_causes": [
    {
      "l3_anchor_id": "L3-2",
      "chain_str": "x → [机制:...] → y → L3 根因 (归类 X)",
      "category": "<A | B | C | D>",
      "signature": "<此根因自己的签名>",
      "reasoning_method": "<该根因用什么方法发现的>"
    }
  ],
  "exhaustion_check": {
    "method": "<B-9 三问答案>",
    "passed": <bool>,
    "multi_bug_confirmed": <bool>,
    "explanation": "<一句话>"
  },
  "runtime_evidence": [
    {
      "evidence_type": "<hilog | screenshot | dump | logcat | trace | replay>",
      "source_path": "<绝对路径 / 设备 ID>",
      "key_observation": "<一句话>",
      "interpretation": "<怎么读>"
    }
  ],
  "zero_states_checked": [
    {"state": "<zero-data | default-config | cold-start>", "finding": "<必现 / 绕开 / 未测>"}
  ],
  "evidence_strength": {
    "<anchor_id>": "<literal | inferred | speculated>"
  },
  "alternative_branches_excluded": [
    {"branch": "<备选根因解释>", "reason": "<反证 [事实Y/Z] 排除>"}
  ],
  "optimization_direction": {
    "fix_action": "<动词开头, 精确到 step + 行号, 多 bug 用 #1, #2>",
    "fix_rationale": "<引回主链 L3 + B-5>",
    "future_scenarios_covered": ["<场景1>", "<场景2>"],
    "related_skills_to_sync": ["<skill-a>"],
    "acceptance_criteria": "<具体可执行>",
    "revert_plan": "<一行含具体动作>"
  },
  "fix_coverage_matrix": [
    {
      "l3_anchor_id": "<L3-1 | L3-2>",
      "covered_by": "<fix_action#1 | N/A + 原因>",
      "covered": <bool>,
      "evidence": "<一句话>"
    }
  ],
  "target_skill_filename": "<花名册中或 'N/A'>",
  "target_skill_path": "<绝对路径 或 'N/A'>",
  "target_skill_section": "<step X.Y 或 'N/A'>",
  "target_line_range": "<L100-L130 或 'N/A'>",
  "defect_dimension": "<AID 阶段>",
  "discovery_timing": "<何时发现>",
  "reasoning_method": ["<primary>", "<secondary>"],
  "problem_signature": "<签名库 10 选 1>",
  "priority": "<HIGH | MEDIUM | LOW>",
  "fix_path": "modify-existing" | "create-new" | "N/A",
  "proposed_skill_name": "<create-new 时必填>",
  "proposed_skill_purpose": "<create-new 时必填, 一句话>"
}
```

## 18 条铁律(写入输出前自检)

1. **target_skill_filename** 必须是花名册中确切存在, 不带 .md
2. D 类 → `target_skill_filename='N/A'`, `target_skill_section` / `target_line_range` / `optimization_direction` 置 N/A
3. 字段不允许缺失
4. ~~optimization_direction 是字符串~~ → 已升级为 6 字段 dict(铁律 #11)
5. **逻辑链铁律**: root_cause_analysis 必须能拆出 `fact → fact → 推断 → L3` 箭头链
6. **通用性铁律**: C-1 三问都"否"才允许归 D 类
7. **证据铁律**: 每个 fact 必须有 `jsonl#L#` 行号引用
8. **精确定位铁律**: target_skill_section + target_line_range 必须真实存在
9. **证据强度铁律**: evidence_strength 覆盖所有 anchors; `speculated` 不准作为 L3 唯一支撑
10. **备选链铁律**: alternative_branches_excluded 至少 1 条, 每条含反证
11. **结构化修复铁律**: optimization_direction 必须是 6 字段 dict
12. **多维度分类铁律**: defect_dimension + discovery_timing + reasoning_method + problem_signature 4 字段必填
13. **多源证据铁律**: B-1 必须覆盖 ≥ 2 类来源
14. **因果机制铁律**: B-2 每环必须有 `[机制: ...]`
15. **运行时证据铁律**: B-10 圈定的 bug 必须有 runtime_evidence ≥ 1 条
16. **零状态穷尽铁律**: zero_states_checked 必须 3 条
17. **多 bug 穷尽铁律**: B-9 三问答"是/不确定" → 必填 additional_root_causes + multi_bug_confirmed=true + signature 升 multi-bug-discovered
18. **修复覆盖闭环铁律**: fix_coverage_matrix 覆盖主链 L3 + 所有 additional L3
19. **修复路径铁律**(新增 v2.1): fix_path 必填 3 选 1; `modify-existing` 时 target_skill 必填; `create-new` 时 proposed_skill_name + proposed_skill_purpose 必填

## 失败处理

- **B-1 抽不到 ≥ 3 条事实** → 扩源(SKILL.md / 源码 / 运行时),仍不够 → 标 `insufficient_evidence: true`,回 D 类
- **B-9 三问都答"否"但客观有多个 bug** → 触发多 bug 模式
- **B-10 必须 runtime 但没采到** → 按 aid-applying step3-2-2b 走降级四要素,不能假装有证据
- **fix_path=create-new 但 15 个 skill 都能覆盖** → 强制改回 `modify-existing`,dispatch 拒收 create-new 滥用

## 复用与子文件

- **推理方法详表**:[references/reasoning-methods.md](references/reasoning-methods.md)
- **签名库**(10 个 problem_signature):[references/signature-library.md](references/signature-library.md)
- **锚点案例库**(5 个 issue 经验):[references/case-library.md](references/case-library.md)

## 中间产物写盘(v2.2 升级)

**写盘路径**:
```
D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-root_cause.json
```

**写盘时机**: B-11 完成后(零状态检查完),**必须** 立即 Write(下游 output skill 必读此文件)。

**写盘内容**(完整 v2.0 13 字段 + v2.1 7 字段 + v2.2 2 字段 = 22 字段):
```json
{
  "issue_number": <num>,
  "stage": "root_cause",
  "stage_status": "success" | "no-input" | "partial" | "failed",
  "timestamp": "<ISO8601>",
  "root_cause_analysis": "fact_a → [机制: ...] → fact_b → ... → L3 根因 (归类 X)",
  "additional_root_causes": [...],
  "exhaustion_check": {...},
  "runtime_evidence": [...],
  "zero_states_checked": [...],
  "evidence_strength": {...},
  "alternative_branches_excluded": [...],
  "optimization_direction": {...},
  "fix_coverage_matrix": [...],
  "fix_path": "modify-existing | create-new | N/A",
  "proposed_skill_name": "...",
  "proposed_skill_purpose": "...",
  "target_skill_filename": "...",
  "target_skill_section": "...",
  "target_line_range": "...",
  "defect_dimension": "...",
  "discovery_timing": "...",
  "reasoning_method": [...],
  "problem_signature": "...",
  "priority": "HIGH | MEDIUM | LOW",
  "stage_metadata": {
    "reasoning_method_primary": "...",
    "multi_bug_confirmed": <bool>,
    "iron_laws_passed": [<int>, <int>, ...],
    "evidence_anchors_count": <int>,
    "B1_sources_count": <int>
  }
}
```

**写盘失败处理**: 重试 3 次,失败 → 标 `root_cause_write_failed: true`, 整体 `stage_status="failed"`,output 标 partial。

**v2.2 新增约束**:
- `proposed_skill_purpose` 必填键(create-new 时非空,其他时可空字符串但键必须存在)
- `stage_status` 必含本 step 状态

## 硬约束

1. **不下结论缺机制**: `root_cause_analysis` 每环必须有 `[机制: ...]`
2. **optimization_direction 必 dict**: 不允许字符串
3. **fix_path 必填**: 3 选 1,缺 dispatch 拒收
4. **签名库强制**: problem_signature 必须从 10 个里选,自创 dispatch 拒收
5. **不重写 skill**: 这是 analysis 的工作流,修是 skillopt-01 的工作

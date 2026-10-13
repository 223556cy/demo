---
name: aid-analysis-output
description: |
  诊断 JSON 输出 (analysis pipeline 步骤 6/6): 在首席诊断任务中把根因 + 推理产物序列化为
  issue_ticket JSON, 写至 .claude/analysis-logs/<日期>/issue-<N>-diagnosis.json。
  **v2.2 升级(2026-07-16)**: 强制输出 v2.0 全部 13 字段 + v2.1 扩展 7 字段 + v2.2 修复路径 2 字段 = 22 字段零容忍;
  集成 validate_diagnosis_v2.py 自动校验,FAIL 直接拒收(防止 v1 11 字段旧 JSON 漏检);
  集成中间产物写盘(读 5 个 stage JSON 拼装,而不是从 LLM context 重组);
  5 条铁律 + 6 个 v2.2 新增铁律,共 11 条不可绕过。
  当用户说"输出 JSON"、"diagnosis.json"、"13 字段"、"零容忍"、"自检 6 问"或类似表述时触发。
compatible: ["calculatorHuawei-main"]
---

# aid-analysis-output Skill (v2.2 升级版)

## 概述

本 skill 是 analysis 6-skill pipeline 的**第 6 步**(最后一步),负责**把根因 + 推理产物序列化为 issue_ticket JSON**,写至磁盘。

**v2.2 关键升级**(2026-07-16):
1. **强制输出 22 字段**(v1 11 → v2.0 13 → v2.1 +7 → v2.2 +2)
2. **集成 validator**: `validate_diagnosis_v2.py` 自动校验,FAIL 拒收
3. **中间产物读盘**: 从 5 个 stage JSON 拼装,而不是从 LLM context 重组
4. **修复路径强制**: fix_path 3 选 1,create-new 时 proposed_skill_name + purpose 必填
5. **新增 6 条铁律**: 在 v2.0 5 条基础上 +6,共 11 条硬约束

```
Pipeline 顺序:
1. aid-analysis-phenomenon    → 写盘 phenomenon.json
2. aid-analysis-log-scan      → 写盘 log_scan.json
3. aid-analysis-spec-code-map → 写盘 spec_code_map.json
4. aid-analysis-locate-bug    → 写盘 locate_bug.json
5. aid-analysis-root-cause    → 写盘 root_cause.json
6. aid-analysis-output        → 写盘 diagnosis.json ← 本 skill
```

## 输出路径

```
D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/issue-<num>-diagnosis.json
```

**所有中间产物路径**(v2.2 新增):
```
analysis-logs/<date>/issue-<N>-phenomenon.json      (step 1 产物)
analysis-logs/<date>/issue-<N>-log_scan.json        (step 2 产物)
analysis-logs/<date>/issue-<N>-spec_code_map.json   (step 3 产物)
analysis-logs/<date>/issue-<N>-locate_bug.json      (step 4 产物)
analysis-logs/<date>/issue-<N>-root_cause.json      (step 5 产物)
analysis-logs/<date>/issue-<N>-diagnosis.json       (step 6 最终产物)
```

**注意**: `analysis-logs/` (本 skill 的输出) ≠ `dispatch-logs/` (dev-01 的输出)。

## 完整 JSON Schema(22 字段)

### 13 个 v2.0 必填字段

| # | 字段 | 类型 | fallback | 铁律 |
|---|------|------|---------|------|
| 1 | `target_skill_section` | string | `"N/A"` (D 类) | #8 |
| 2 | `target_line_range` | string | `"N/A"` | #8 |
| 3 | `additional_root_causes` | array | `[]` | #17 |
| 4 | `exhaustion_check` | object | `{"method":"...","passed":bool,"multi_bug_confirmed":bool,"explanation":"..."}` | #17 |
| 5 | `runtime_evidence` | array | `[]` (静态够的 bug 不需要) | #15 |
| 6 | `zero_states_checked` | array, length ≥ 3 | `[{...},{...},{...}]` | #16 |
| 7 | `fix_coverage_matrix` | array | 每个 L3 一行 | #18 |
| 8 | `defect_dimension` | string | `"planning-stage"` 等枚举 | #12 |
| 9 | `discovery_timing` | string | `"review"` 等枚举 | #12 |
| 10 | `reasoning_method` | array | `["abductive","analogical"]` | #12 |
| 11 | `problem_signature` | string | **必须从 10 个签名库选** | #12 |
| 12 | `evidence_strength` | object | `{<anchor_id>: "literal\|inferred\|speculated"}` | #9 |
| 13 | `alternative_branches_excluded` | array, length ≥ 1 | `[{...}]` | #10 |

### 7 个 v2.1 扩展字段

| # | 字段 | 类型 | 必填条件 | 来源 skill |
|---|------|------|---------|-----------|
| 14 | `error_log_paths` | array | 必有(允许 `[]`) | `aid-analysis-log-scan` |
| 15 | `error_summary` | string | 必有(允许 `"无错误日志"`) | `aid-analysis-log-scan` |
| 16 | `log_anchors` | array | 必有(允许 `[]`) | `aid-analysis-log-scan` |
| 17 | `spec_to_code_mapping` | array | 必有(允许 `[]`) | `aid-analysis-spec-code-map` |
| 18 | `bug_location` | object / null | 必有(允许 `null`) | `aid-analysis-locate-bug` |
| 19 | `fix_path` | enum | **必填**(`"modify-existing"` / `"create-new"` / `"N/A"`) | `aid-analysis-root-cause` |
| 20 | `proposed_skill_name` | string | `fix_path="create-new"` 时必填 | `aid-analysis-root-cause` |

### 2 个 v2.2 新增字段(修复路径完整化)

| # | 字段 | 类型 | 必填条件 | 铁律 |
|---|------|------|---------|------|
| 21 | `proposed_skill_purpose` | string | `fix_path="create-new"` 时必填, 一句话 | #19 |
| 22 | `stage_status` | object | 必有(6 个 step 状态汇总) | #21 |

`stage_status` 字段格式:
```json
{
  "phenomenon": "success" | "no-input" | "partial" | "failed",
  "log_scan": "...",
  "spec_code_map": "...",
  "locate_bug": "...",
  "root_cause": "...",
  "output": "..."
}
```

## 完整 JSON 模板(v2.2 升级)

```json
{
  "issue_ticket": {
    "issue_number": <num>,
    "title": "<一句话总结 Bug>",
    "verdict": "<APPROVE | REQUEST_CHANGES>",
    "priority": "<HIGH | MEDIUM | LOW>",

    "target_skill_filename": "<花名册中或 'N/A'>",
    "target_skill_path": "<绝对路径 或 'N/A'>",
    "target_skill_section": "<step X.Y 或 'N/A'>",
    "target_line_range": "<L100-L130 或 'N/A'>",

    "phenomenon": "<50-150 字, 客观描述>",

    "defect_dimension": "<planning-stage | implementing-stage | applying-stage | archiving-stage | cross-stage>",
    "discovery_timing": "<review | integration | production | self-found | regression>",
    "reasoning_method": ["<primary>", "<secondary>"],
    "problem_signature": "<签名库 10 选 1>",

    "root_cause_analysis": "fact_a ([源]L#) → [机制: ...] → fact_b ([源]L#) → [机制: ...] → L3 根因 (归类 X)",

    "additional_root_causes": [
      {
        "l3_anchor_id": "L3-2",
        "chain_str": "x → [机制:...] → y → L3 根因 (归类 X)",
        "category": "<A | B | C | D>",
        "signature": "<签名库 10 选 1>",
        "reasoning_method": "<该根因用什么方法发现的>"
      }
    ],

    "exhaustion_check": {
      "method": "<B-9 三问答案>",
      "passed": <true | false>,
      "multi_bug_confirmed": <true | false>,
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
      {"branch": "<备选根因解释>", "reason": "<反证>"}
    ],

    "optimization_direction": {
      "fix_action": "<动词开头, 多 bug 用 #1, #2 编号>",
      "fix_rationale": "<引回 L3 + B-5>",
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

    "fix_path": "modify-existing | create-new | N/A",
    "proposed_skill_name": "<create-new 时必填>",
    "proposed_skill_purpose": "<create-new 时必填, 一句话>",

    "error_log_paths": ["<绝对路径>"],
    "error_summary": "<一句话总结关键错误>",
    "log_anchors": [
      {
        "log_path": "<绝对路径>",
        "line_range": "L120-L150",
        "error_type": "<hilog | stderr | ide | build | runtime | coverage>",
        "severity": "<HIGH | MEDIUM | LOW>",
        "key_observation": "<一句话>",
        "stack_trace": "<堆栈片段 或 null>"
      }
    ],

    "spec_to_code_mapping": [
      {
        "req_id": "FR-001",
        "requirement_text": "<spec 原文>",
        "code_locations": [{"file": "<路径>", "line_range": "L100-L120", "function": "<func>"}],
        "status": "<implemented | partially-implemented | not-implemented | diverged>",
        "gap_description": "<diverged 时必填>"
      }
    ],

    "bug_location": {
      "file": "<相对 worktree 路径>",
      "absolute_path": "<绝对路径>",
      "line_range": "L100-L130",
      "function": "<func 或类.方法>",
      "error_msg": "<错误原文>",
      "context_before": "<前 5 行>",
      "context_after": "<后 5 行>",
      "confidence": "<HIGH | MEDIUM | LOW>",
      "signals": [{"type": "...", "source": "...", "observation": "..."}]
    },

    "stage_status": {
      "phenomenon": "success",
      "log_scan": "success",
      "spec_code_map": "success",
      "locate_bug": "success",
      "root_cause": "success",
      "output": "success"
    },

    "session_files_analyzed": ["<jsonl 路径>"],
    "evidence_anchors": ["<[源]L# 引用>"]
  }
}
```

## 工作流(5 步,v2.2 升级)

### 步骤 1: 读 5 个 stage JSON 产物

从磁盘读:
- `phenomenon.json` (step 1 写盘)
- `log_scan.json` (step 2 写盘)
- `spec_code_map.json` (step 3 写盘)
- `locate_bug.json` (step 4 写盘)
- `root_cause.json` (step 5 写盘)

### 步骤 2: 拼装 v2.2 22 字段 JSON

按 v2.2 schema 拼装(对照表见上),从 5 个 stage 读字段填充:
- 13 个 v2.0 字段从 root_cause.json 读
- 7 个 v2.1 扩展字段从 log_scan / spec_code_map / locate_bug 读
- 2 个 v2.2 字段(proposed_skill_purpose + stage_status)从 root_cause / 自身状态读

### 步骤 3: 跑 validate_diagnosis_v2.py 自动校验

```bash
python .claude/skills/aid-analysis-output/validate_diagnosis_v2.py \
  .claude/analysis-logs/<date>/issue-<N>-diagnosis.json
```

**退出码 0 → 进入步骤 4**
**退出码 1 → 校验失败,本 skill 自己修复(补 fallback),再跑一次,直到 PASS 为止**

### 步骤 4: 写 diagnosis.json

把拼装好的 22 字段 JSON 写到 `analysis-logs/<date>/issue-<N>-diagnosis.json`

### 步骤 5: 报告产出

向用户/上游报告:
- verdict(APPROVE / REQUEST_CHANGES)
- priority(HIGH / MEDIUM / LOW)
- target_skill_filename
- problem_signature
- 修复路径(fix_path)
- 阶段状态(stage_status)

## 11 条铁律(v2.2 升级,validator 自动校验)

5 条 v2.0 铁律(继承自 SOUL.md v2.0 trial):
- **铁律 #11**: `optimization_direction` 必须是 6 字段 dict(不是 str)
- **铁律 #14**: `root_cause_analysis` 必须含 ≥1 个 `[机制: ...]` 标记
- **铁律 #16**: `zero_states_checked` ≥3 条
- **铁律 #17**: `multi_bug_confirmed=true` 时 `additional_root_causes` 必须非空
- **铁律 #18**: `fix_coverage_matrix` 每行 `covered=true` 或 `covered_by` 开头 `N/A`

6 条 v2.2 新增铁律:
- **铁律 #19**: `fix_path` 必填 3 选 1; `create-new` 时 `proposed_skill_name` + `proposed_skill_purpose` 必填
- **铁律 #20**: 7 个 v2.1 扩展字段(14-20)键必须存在(允许空值/空数组/null)
- **铁律 #21**: `stage_status` 必须含 6 个 step 状态(每个 ∈ success/no-input/partial/failed)
- **铁律 #22**: v2.2 `proposed_skill_purpose` 键必须存在(允许 N/A 时为 null)
- **铁律 #23**: 22 字段总数校验(`len(ticket) >= 22`)
- **铁律 #24**: 任何字段值不能是裸 `None`(必须显式 `"N/A"` 或结构化对象)

## 写完前自检 6 问(v2.2 升级,5 → 6)

1. 我的 issue_ticket 是否有 **22 个字段全部键存在**(允许 N/A / null / [])?
2. 我的 optimization_direction 是 **dict** 而非 str?
3. 我的 root_cause_analysis 含 ≥1 个 `[机制:` 标记?
4. 我的 fix_path 是 3 选 1, 且 create-new 时 proposed_skill_name + purpose 都有?
5. 我的 fix_coverage_matrix 覆盖了主链 L3 + 所有 additional L3?
6. 我的 stage_status 6 个 step 都有状态字段?

**任一不满足** → 跑 `validate_diagnosis_v2.py` 看具体失败铁律,回 `aid-analysis-root-cause` 重写, 不准提交。

## 失败处理

- **步骤 1 读不到 stage JSON** → 标注 `stage_status.<step>="failed"`, 整体判 partial,verdict=REQUEST_CHANGES
- **步骤 3 校验 FAIL** → 自动尝试补 fallback(N/A 填缺失字段),最多 3 次;3 次还失败 → 标 `output_validation_failed: true`,整体判 partial
- **步骤 4 写盘失败** → 重试 3 次,失败则报 `output_write_failed: true`

## 与其他 skill 的接力

- **上游 `aid-analysis-root-cause`**: 写 `root_cause.json` 供本 skill 读
- **下游 `aid-analysis-report`(v2.3 新增)**: 读本 skill 写的 `diagnosis.json` 生成给人读的 Markdown 报告
- **不修改源码**: 只读,修是 dev-01 / dev-02 的工作
- **不重写 skill**: 这是 analysis 的工作流

## 硬约束

1. **不 print 到 stdout**: 写到指定 JSON 文件, **不**额外输出到控制台(除了步骤 5 的最终报告)
2. **不发 GitHub 评论**: dispatch 会基于 JSON 自动生成
3. **不 close / reopen / assign**: 留给 dispatch 收尾
4. **不 commit / push**: 留给 skillopt-01 / dev-02
5. **不重写 skill**: 修是 skillopt-01 的工作
6. **不改 worktree / AID 产物**: 只读
7. **22 字段零容忍**: 任一字段键缺失 → validator FAIL → 整 issue 拒收
8. **validator 必跑**: 不跑 validator 写盘 = 违规,dispatch 不收

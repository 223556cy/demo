---
name: aid-analysis-spec-code-map
description: |
  spec ↔ code 对应性检查 / spec-code-map (analysis pipeline 步骤 3/6): 在首席诊断任务中读
  specs/changes/<dir>/ 下的 spec / design / proposal, 逐条提取需求 (FR / NFR), 对照 worktree 内源码的
  实现状态 — 完整实现 / 部分实现 / 未实现 / 偏离 spec。输出 `spec_to_code_mapping` 数组
  (每条 {req_id, requirement_text, code_locations, status, gap_description})。
  当用户说"spec 对应性"、"代码对照"、"实现状态"、"traceability"、"FR 对应"或类似表述时触发。
  本 skill 是纯人工对照 (Claude 读 spec + 源码语义理解, 无自动化工具)。
compatible: ["calculatorHuawei-main"]
---

# aid-analysis-spec-code-map Skill

## 概述

本 skill 是 analysis 6-skill pipeline 的**第 3 步**,负责**逐条 spec 需求 → 源码实现状态**对照。

**核心约束**: 这是**纯人工 + LLM 语义理解**,无自动化工具。spec 抽取靠 Claude 读,代码定位靠 Claude grep + Read + 语义理解。

```
Pipeline 顺序:
1. aid-analysis-phenomenon
2. aid-analysis-log-scan
3. aid-analysis-spec-code-map  ← 本 skill
4. aid-analysis-locate-bug
5. aid-analysis-root-cause
6. aid-analysis-output
```

## 数据源

| 源 | 路径 | 用途 |
|---|------|------|
| **spec 源** | `D:/huawei/Demo/calculatorHuawei/specs/changes/<change-id>/delta-spec.md` | 主要 FR / NFR |
| **design** | `specs/changes/<change-id>/delta-design.md` 或 `design.md` | 架构级需求 |
| **proposal** | `specs/changes/<change-id>/proposal.md` | 用户原始诉求 |
| **代码源** | `D:/huawei/Demo/worktrees/issue-{N}/opencalc/entry/src/main/...` | 实现对照 |
| **辅助 checklist** | `aid-applying/SKILL.md` + `aid-reviewing/SKILL.md` 内的 check-items-*.md | 人工评审参考 |

## 工作流(4 步)

### 步骤 1: 定位 change-id + 读 spec

从 `phenomenon_sources.aid_files` 找 `delta-spec.md` 路径, 提取:
- `## 需求` / `## FR` / `## NFR` / `## Acceptance Criteria` 段
- 每条需求给一个 `req_id`(FR-001 / NFR-001 / AC-001 / 自行编号)
- **上限 ≤ 20 条 / issue**(超出归类为"广义覆盖",不逐条对照)

如果 spec 文件缺失 → 输出空 mapping + `spec_unavailable: true`, 跳过本 skill。

### 步骤 2: 抽取需求文本(20-100 字 / 条)

对每条需求, 摘录原文(不重写、不归一化)。

### 步骤 3: 源码定位(Grep + Read + 语义理解)

对每条 spec 需求, 在 `opencalc/entry/src/main/` 下:
1. **Grep 关键词**: 提取 spec 里的功能名 / 函数名 / 字段名 → 找候选实现
2. **Read 候选代码**: 判断是否真实现
3. **语义对照**: 实现是否满足 spec?(不只看存在, 看正确性)

每个实现记录 `code_locations: [{file, line_range, function}]`, 多个文件实现就列多个。

### 步骤 4: 判定 status

| status | 判定标准 |
|--------|---------|
| `implemented` | 找到完整实现, 行为与 spec 一致 |
| `partially-implemented` | 找到部分实现, 缺少边界场景 / 默认值 / 错误处理 |
| `not-implemented` | Grep 无命中, spec 该条无对应代码 |
| `diverged` | 找到实现, 但行为与 spec 偏离(参数名反向 / 默认值错 / 逻辑相反) |

**`diverged` 必填 `gap_description`**: 一句话说清"spec 说 X, 代码做 Y"。

## 输入字段(从前置 skill)

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| `phenomenon_sources.aid_files` | object(7 个 bool) | ✅ | `aid-analysis-phenomenon` |
| `phenomenon_sources.worktree_path` | string | ❌(用于定位 worktree 代码) | `aid-analysis-phenomenon` |

> 备注: 通过 `aid_files.delta-spec.md = true` 决定本 skill 是否执行;若 `delta-spec.md` 缺失,标 `spec_unavailable: true` 跳过。

## 输出字段(供后续 skill 引用 + 写盘)

| 字段 | 类型 | 必填 | 写盘路径 | 下游消费方 |
|------|------|------|---------|-----------|
| `spec_to_code_mapping` | array(≤20) | ✅(允许空) | `spec_code_map.json.spec_to_code_mapping` | `locate-bug`, `root-cause`, `output` |
| `spec_to_code_mapping[].req_id` | string | ✅(单条内) | 同上 | `root-cause` |
| `spec_to_code_mapping[].requirement_text` | string(20-100字) | ✅ | 同上 | `root-cause`(B-1 事实) |
| `spec_to_code_mapping[].code_locations` | array | ✅(允许 `[]` if not-implemented) | 同上 | `locate-bug` |
| `spec_to_code_mapping[].status` | enum(`implemented`/`partially-implemented`/`not-implemented`/`diverged`) | ✅ | 同上 | `root-cause`(判根因维度) |
| `spec_to_code_mapping[].gap_description` | string | ⚠️(`diverged` 时必填) | 同上 | `root-cause` |
| `coverage_pct` | float(0-1) | ✅ | `spec_code_map.json.coverage_pct` | `output` |
| `diverged_count` | int | ✅ | `spec_code_map.json.diverged_count` | `root-cause`, `output` |
| `missing_count` | int | ✅ | `spec_code_map.json.missing_count` | `root-cause`, `output` |
| `spec_unavailable` | bool | ✅ | `spec_code_map.json.spec_unavailable` | `output` |
| `mapping_strategy` | enum(`full`/`truncated-at-20`) | ✅ | `spec_code_map.json.mapping_strategy` | `output` |

**JSON 完整 schema**(v2.2 沿用,字段顺序同上):
```json
{
  "spec_to_code_mapping": [
    {
      "req_id": "FR-001",
      "requirement_text": "<spec 里的需求原文, 20-100 字>",
      "code_locations": [
        {
          "file": "<相对 worktree 路径>",
          "line_range": "L100-L120",
          "function": "<函数名或类.方法名>"
        }
      ],
      "status": "<implemented | partially-implemented | not-implemented | diverged>",
      "gap_description": "<diverged 时必填, 一句话说明差异>"
    }
  ],
  "coverage_pct": 0.85,
  "diverged_count": 0,
  "missing_count": 0,
  "spec_unavailable": false,
  "mapping_strategy": "<full | truncated-at-20>"
}
```

**计算规则**:
- `coverage_pct` = (implemented + partially-implemented) / total
- `diverged_count` = status=diverged 的条数
- `missing_count` = status=not-implemented 的条数

**计算**:
- `coverage_pct` = (implemented + partially-implemented) / total
- `diverged_count` = status=diverged 的条数
- `missing_count` = status=not-implemented 的条数

## 失败处理

- **spec 文件缺失** → `spec_to_code_mapping: []` + `spec_unavailable: true` + `coverage_pct: 0`
- **超过 20 条** → 取前 20 条 + `mapping_strategy: "truncated-at-20"`, 总条数记在 `phenomenon_sources.aid_files`
- **代码全空** → 全部填 `not-implemented`, coverage_pct=0
- **Grep 命中率 0 但有源码** → 可能是命名差异, 改用类名 / 字段名再 grep 一次

## 与其他 skill 的接力

- **下游 `aid-analysis-locate-bug`**: 读 `spec_to_code_mapping[].code_locations[].file + line_range` 找具体错位置
- **下游 `aid-analysis-root-cause`**: 读 `diverged_count` / `missing_count` + `gap_description` 判根因维度
- **不修改 spec / code**: 只读, 写不写是 dev-01 的工作

## 中间产物写盘(v2.2 升级)

**写盘路径**:
```
D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-spec_code_map.json
```

**写盘时机**: 本 skill 输出 JSON 拼接完成后, **必须** 立即 Write(不依赖下游消费)。

**写盘内容**:
```json
{
  "issue_number": <num>,
  "stage": "spec_code_map",
  "stage_status": "success" | "no-input" | "partial" | "failed",
  "timestamp": "<ISO8601>",
  "spec_to_code_mapping": [...],
  "coverage_pct": <float>,
  "diverged_count": <int>,
  "missing_count": <int>,
  "spec_unavailable": <bool>,
  "mapping_strategy": "<full | truncated-at-20>",
  "stage_metadata": {
    "total_requirements": <int>,
    "implemented": <int>,
    "partially_implemented": <int>,
    "not_implemented": <int>,
    "diverged": <int>
  }
}
```

**写盘失败处理**: 重试 3 次,失败 → 标 `spec_code_map_write_failed: true`, 整体 `stage_status="failed"`。

## 硬约束

1. **≤ 20 条上限**: 超长 spec 走"广义覆盖", 不逐条对照
2. **必引代码位置**: `code_locations` 不能空(就算 not-implemented 也写 `[]` + 注明原因)
3. **diverged 必填 gap**: 不写 gap_description 直接拒收
4. **不归因**: 找代码是事实, "为什么这样写" 留给 root-cause
5. **不重写 skill**: 这是 analysis 的工作流

---
name: aid-analysis-phenomenon
description: |
  现象还原 / 信息收集 (analysis pipeline 步骤 1/6): 在首席诊断任务中读 GitHub issue
  详情 + rev-01 完整审查评论 + AID 三阶段产物 (proposal / spec / design / tasks / apply-report)
  + 定位 dev-01 session 对话 jsonl, 提取 50-150 字的现象描述。
  当用户说"现象还原"、"读 issue"、"读 session"、"phenomenon"、"信息收集"或类似表述时触发。
  本 skill 是 analysis 6-skill pipeline 的第 1 步, 输出 `phenomenon` 字段供后续 skill 引用。
compatible: ["calculatorHuawei-main"]
---

# aid-analysis-phenomenon Skill

## 概述

本 skill 是 analysis 数字员工 6-skill pipeline 的**第 1 步**,负责**信息收集**而非推理分析。

**核心约束**: 现象描述 = 客观事实(看到了什么), 不下结论(为什么)。结论留给 `aid-analysis-root-cause`。

```
Pipeline 顺序:
1. aid-analysis-phenomenon  ← 本 skill
2. aid-analysis-log-scan
3. aid-analysis-spec-code-map
4. aid-analysis-locate-bug
5. aid-analysis-root-cause
6. aid-analysis-output
```

## 收集源(5 类)

| 源 | 路径 | 必读 |
|---|------|------|
| **GitHub issue** | `gh_helper.py read <num>` | 是 |
| **rev-01 评论** | issue 评论(尤其 `finalize_review` 写的 APPROVE / REQUEST_CHANGES) | 是 |
| **AID 产物** | `specs/changes/<dir>/{proposal,delta-spec,info,delta-design,design-review,tasks,apply-report}.md` | 是 |
| **dev-01 session** | `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-<N>/<YYYY-MM-DD>/*.jsonl` | 是(若有) |
| **Worktree 路径** | `D:/huawei/Demo/worktrees/issue-<N>`(git log + diff) | 是 |

## 工作流(4 步)

### 步骤 1: 读 issue 详情

```bash
python "C:/Users/26909/AppData/Local/hermes/profiles/analysis/bin/gh_helper.py" read <num>
```

收集: 标题、正文、所有评论、标签、状态、assignee。

### 步骤 2: 定位 session 对话文件

按时间排序读所有 jsonl,关注:
- user 给 claude 的原始 prompt
- claude 调用的 Skill tool(哪些 aid-* skill 被加载)
- tool_use / tool_result(实际命令、读的文件、写的产物)
- 错误 / 重试 / 跳过步骤的痕迹

如果 session 不存在 → 标注 `session_available: false`, 基于 AID 产物和评论做诊断。

### 步骤 3: 对比 AID 产物齐全度

检查清单(写进现象描述):
- `proposal.md` ✓/✗
- `delta-spec.md` ✓/✗
- `info.md` ✓/✗
- `delta-design.md` ✓/✗
- `design-review.md` ✓/✗
- `tasks.md` ✓/✗
- `apply-report.md` ✓/✗

### 步骤 4: 提取现象(50-150 字, 1 句话)

**格式要求**:
- **客观**: 只描述看到了什么(产物缺失 / 测试失败 / commit 异常 / UI 报错)
- **不下结论**: 不写"是因为 XXX 步骤缺失" — 留给根因
- **具体**: 引用文件路径 / 行号 / commit hash

**反例**(❌ 写成了结论):
> "因为 dev-01 跳过了 signoff 步骤,导致 commit 不合规"

**正例**(✓ 客观事实):
> "apply-report.md 缺失; commit 8e6555c 缺 Sign-off 字段; 4 要素全跳; checkboxes 未勾选"

## 输入字段(从前置 skill)

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| (无前置 skill — pipeline 第 1 步) | — | — | — |

## 输出字段(供后续 skill 引用 + 写盘)

| 字段 | 类型 | 必填 | 写盘路径 | 下游消费方 |
|------|------|------|---------|-----------|
| `phenomenon` | string(50-150字) | ✅ | `phenomenon.json.phenomenon` | `root-cause`, `output` |
| `phenomenon_sources.issue_url` | string | ✅ | `phenomenon.json.phenomenon_sources.issue_url` | `output` |
| `phenomenon_sources.rev01_verdict` | enum(`APPROVE`/`REQUEST_CHANGES`/`UNKNOWN`) | ✅ | `phenomenon.json.phenomenon_sources.rev01_verdict` | `root-cause`, `output` |
| `phenomenon_sources.aid_files` | object(7 个 bool) | ✅ | `phenomenon.json.phenomenon_sources.aid_files` | `spec-code-map`, `output` |
| `phenomenon_sources.session_jsonls` | array\<string\> | ❌(若无则空) | `phenomenon.json.phenomenon_sources.session_jsonls` | `log-scan` |
| `phenomenon_sources.worktree_path` | string | ❌(若无则 N/A) | `phenomenon.json.phenomenon_sources.worktree_path` | `log-scan`, `locate-bug`, `spec-code-map` |

**JSON 完整 schema**(v2.2 沿用,字段顺序同上):
```json
{
  "phenomenon": "<50-150 字, 客观描述>",
  "phenomenon_sources": {
    "issue_url": "https://github.com/calculatorHuawei/agent_workflow/issues/<N>",
    "rev01_verdict": "<APPROVE | REQUEST_CHANGES | UNKNOWN>",
    "aid_files": {
      "proposal.md": true,
      "delta-spec.md": true,
      "info.md": false,
      "delta-design.md": true,
      "design-review.md": false,
      "tasks.md": true,
      "apply-report.md": false
    },
    "session_jsonls": ["<绝对路径>", ...],
    "worktree_path": "D:/huawei/Demo/worktrees/issue-<N>"
  }
}
```

## 失败处理

- **issue 读失败** → 标注 `issue_read_failed: true`, 跳过 Step 1
- **session 不存在** → 标注 `session_available: false`, 基于产物+评论做
- **产物全缺失** → phenomenon 写"`specs/changes/<dir>/` 目录不存在, dev-01 完全没跑 AID"
- **现象超过 200 字** → 浓缩到核心 1 句话, 详情放 `phenomenon_sources`

## 与其他 skill 的接力

- **下游 `aid-analysis-log-scan`**: 读 `phenomenon_sources.session_jsonls` + `worktree_path` 扫日志
- **下游 `aid-analysis-spec-code-map`**: 读 `phenomenon_sources.aid_files` 找 spec 源
- **下游 `aid-analysis-locate-bug`**: 不直接读本 skill, 但读 `aid-analysis-log-scan` 的 log_anchors

## 中间产物写盘(v2.2 升级)

**写盘路径**:
```
D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-phenomenon.json
```

**写盘时机**: 本 skill 输出 JSON 字段拼接完成后, **必须** 立即 Write 到上述路径(不等下游)。

**写盘内容**:
```json
{
  "issue_number": <num>,
  "stage": "phenomenon",
  "stage_status": "success" | "no-input" | "partial" | "failed",
  "timestamp": "<ISO8601>",
  "phenomenon": "<50-150 字>",
  "phenomenon_sources": { ... },
  "stage_metadata": {
    "phenomenon_length": <int>,
    "files_present": <int>,
    "files_missing": <int>
  }
}
```

**写盘失败处理**:
- 重试 3 次,失败 → 标 `phenomenon_write_failed: true`, 整体 `stage_status="failed"`, 但不抛异常(后续 skill 仍可从 LLM context 接力)
- v2.2 之前的诊断报告缺失中间产物 = 无法独立审计每步,本升级修复此问题

## 硬约束

1. **不下结论**: phenomenon 只描述"看到了什么", 原因 / 机制留给 `aid-analysis-root-cause`
2. **必须客观**: 不写"因为" / "由于" / "根因" 等归因词
3. **必引证据**: 每条现象要带 `jsonl#L#` 或 `commit <hash>` 或 `<file>:<line>` 引用
4. **长度控制**: 50-150 字(超出压缩到核心句)
5. **不重写 skill 文件**: 这是 analysis 的工作流, 不要改 SKILL.md

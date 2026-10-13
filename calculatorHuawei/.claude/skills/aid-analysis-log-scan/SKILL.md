---
name: aid-analysis-log-scan
description: |
  日志分析 / log-scan (analysis pipeline 步骤 2/6): 在首席诊断任务中扫三类日志 —
  (1) .claude/analysis-logs/ 与 .claude/dispatch-logs/ 下的 stderr.log / stdout.log / run-log;
  (2) worktree 内 HarmonyOS 编译日志 (.hvigor/outputs/build-logs/build.log) + JVM 崩溃 (hs_err_pid*.log);
  (3) 鸿蒙应用运行时 hilog (specs/changes/<change>/screenshots/hilog*.log)。
  提取关键 error 摘要 + 堆栈 + 行号, 输出 `log_anchors` 数组供后续 `aid-analysis-locate-bug` 引用。
  当用户说"日志分析"、"扫日志"、"error.log"、"hilog"、"logcat"、"stderr"或类似表述时触发。
compatible: ["calculatorHuawei-main"]
---

# aid-analysis-log-scan Skill

## 概述

本 skill 是 analysis 6-skill pipeline 的**第 2 步**,负责**从多源日志中提取关键错误信号**。

**核心约束**: 只做"提取", 不做"归因"。堆栈行号是事实, 为什么这个错是根因 — 留给 `aid-analysis-root-cause`。

```
Pipeline 顺序:
1. aid-analysis-phenomenon
2. aid-analysis-log-scan  ← 本 skill
3. aid-analysis-spec-code-map
4. aid-analysis-locate-bug
5. aid-analysis-root-cause
6. aid-analysis-output
```

## 收集源(9 类)

| 类别 | 路径 / 模式 | 用途 |
|------|------------|------|
| **analysis 自身 stderr** | `D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<date>/issue-{N}-stderr.log` | claude -p 子进程崩溃/异常 |
| **analysis 自身 stdout** | `.claude/analysis-logs/<date>/issue-{N}-stdout.log` | 进程最终输出(诊断摘要) |
| **analysis run log** | `.claude/analysis-logs/<date>/analysis.log` | `[ERR]` 行 = 业务错误信号 |
| **dev-01 dispatch stderr** | `.claude/dispatch-logs/<date>/issue-{N}-stderr.log` | dev-01 进程错误 |
| **dev-01 dispatch run log** | `.claude/dispatch-logs/<date>/dispatch.log` | `[ERR]` 行 |
| **HarmonyOS 编译日志** | `D:/huawei/Demo/worktrees/issue-{N}/.hvigor/outputs/build-logs/build.log` | hvigorw 编译输出 |
| **JVM HotSpot 崩溃** | `D:/huawei/Demo/worktrees/issue-{N}/opencalc/hs_err_pid*.log` | IDE / 模拟器崩溃 |
| **HarmonyOS 运行时 hilog** | `D:/huawei/Demo/worktrees/issue-{N}/specs/changes/<change-id>/screenshots/hilog*.log` | UI 测试 agent 手动抓取 |
| **测试覆盖率日志** | `D:/huawei/Demo/worktrees/issue-{N}/opencalc/entry/.test/default/intermediates/test/coverage_data/coverage.log` | 单元测试覆盖 |

**glob 模式**:
```python
# 进程级 stderr
.claude/analysis-logs/<date>/issue-{N}-stderr.log
.claude/dispatch-logs/<date>/issue-{N}-stderr.log

# run-level ERR
.claude/analysis-logs/<date>/analysis.log    # grep '\[ERR\]'
.claude/dispatch-logs/<date>/dispatch.log     # grep '\[ERR\]'

# worktree 内
worktrees/issue-{N}/.hvigor/outputs/build-logs/build.log
worktrees/issue-{N}/opencalc/hs_err_pid*.log
worktrees/issue-{N}/specs/changes/*/screenshots/hilog*.log
```

## 工作流(3 步)

### 步骤 1: Glob 扫描 + 文件存在性检查

```python
# 给定 issue number N
log_paths = []
log_paths += glob(f".claude/analysis-logs/{today}/issue-{N}-stderr.log")
log_paths += glob(f".claude/dispatch-logs/{today}/issue-{N}-stderr.log")
log_paths += glob(f"worktrees/issue-{N}/.hvigor/outputs/build-logs/build.log")
log_paths += glob(f"worktrees/issue-{N}/opencalc/hs_err_pid*.log")
log_paths += glob(f"worktrees/issue-{N}/specs/changes/*/screenshots/hilog*.log")
```

如果**全部不命中** → 输出 `error_log_paths: []` + `error_summary: "无错误日志"`, 跳过本 skill。

### 步骤 2: 提取错误信号

对每个文件:
1. **Read 全文**(用 Read 工具)
2. 扫关键词: `Error` / `Exception` / `FATAL` / `CRASH` / `failed` / `cannot` / `undefined` / `null` / `panic` / `Assert`
3. 对每个命中, 提取:
   - `line_range`: 错误行 + 前后 3-5 行
   - `error_type`: 分类(hilog / stderr / ide / build / runtime / coverage)
   - `key_observation`: 一句话指出"证明什么"
   - `stack_trace`: 堆栈片段(若有)

### 步骤 3: 排序 + 优先级

按严重度排序:
- **HIGH**: JVM crash (hs_err_pid*.log) / FATAL / panic
- **MEDIUM**: Exception / Build failure / hilog 报错
- **LOW**: warning / deprecated / coverage gap

**保留前 5 条**, 超过 5 条放 `additional_log_anchors` 数组。

## 输入字段(从前置 skill)

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| `phenomenon_sources.session_jsonls` | array\<string\> | ❌(允许空) | `aid-analysis-phenomenon` |
| `phenomenon_sources.worktree_path` | string | ❌(允许 N/A) | `aid-analysis-phenomenon` |
| `phenomenon_sources.aid_files` | object | ❌(用于定位 specs/changes/ 目录) | `aid-analysis-phenomenon` |

> 备注: session_jsonls 主要用于定位 .claude/dispatch-logs/ 错误;若为空,跳过 dev-01 进程错误扫描。

## 输出字段(供后续 skill 引用 + 写盘)

| 字段 | 类型 | 必填 | 写盘路径 | 下游消费方 |
|------|------|------|---------|-----------|
| `error_log_paths` | array\<string\> | ✅(允许空) | `log_scan.json.error_log_paths` | `output` |
| `error_summary` | string(30-80字) | ✅(允许 `"无错误日志"`) | `log_scan.json.error_summary` | `output`, `root-cause` |
| `log_anchors` | array(≤5 条) | ✅(允许空) | `log_scan.json.log_anchors` | `locate-bug`, `root-cause`, `output` |
| `log_anchors[].log_path` | string | ✅(单条内) | 同上 | `locate-bug`(解析 stack_trace) |
| `log_anchors[].line_range` | string | ✅ | 同上 | `locate-bug` |
| `log_anchors[].error_type` | enum(`hilog`/`stderr`/`ide`/`build`/`runtime`/`coverage`) | ✅ | 同上 | `root-cause` |
| `log_anchors[].severity` | enum(`HIGH`/`MEDIUM`/`LOW`) | ✅ | 同上 | `root-cause` |
| `log_anchors[].key_observation` | string | ✅ | 同上 | `root-cause`(B-1 事实源) |
| `log_anchors[].stack_trace` | string/null | ❌ | 同上 | `locate-bug`(解析文件:行号) |
| `additional_log_anchors` | array(超过 5 条的次要) | ❌ | `log_scan.json.additional_log_anchors` | `root-cause`(参考) |
| `harmony_runtime_logs` | array\<string\> | ❌ | `log_scan.json.harmony_runtime_logs` | `output` |

**JSON 完整 schema**(v2.2 沿用,字段顺序同上):
```json
{
  "error_log_paths": ["<绝对路径>", ...],
  "error_summary": "<一句话总结关键错误, 30-80 字>",
  "log_anchors": [
    {
      "log_path": "<绝对路径>",
      "line_range": "L120-L150",
      "error_type": "<hilog | stderr | ide | build | runtime | coverage>",
      "severity": "<HIGH | MEDIUM | LOW>",
      "key_observation": "<一句话证明什么>",
      "stack_trace": "<关键堆栈片段 或 null>"
    }
  ],
  "additional_log_anchors": [
    /* 超过 5 条的次要错误, 同样结构 */
  ],
  "harmony_runtime_logs": [
    "<hilog 路径 或 'device: 127.0.0.1:5555'>"
  ]
}
```

## 失败处理

- **文件全部不存在** → 输出空数组, 标注 `log_scan: "no-logs-found"`
- **Read 失败** → 跳过该文件, 在 `error_summary` 里标注 "<file> 读失败"
- **文件过大(>10MB)** → 只读前 1000 行 + 末尾 100 行(头尾最可能有关键错)
- **无错误信号** → 输出 `error_summary: "<file> 存在但无错误"`, log_anchors 仍可空

## 与其他 skill 的接力

- **下游 `aid-analysis-locate-bug`**: 读 `log_anchors[].stack_trace` 解析文件+行号
- **下游 `aid-analysis-root-cause`**: 读 `log_anchors[].key_observation` + `error_summary` 做事实链
- **不修改 worktree**: 只读, 不动 hilog 抓取逻辑(那是 rev-01 / dev-02 的工作)

## 中间产物写盘(v2.2 升级)

**写盘路径**:
```
D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-log_scan.json
```

**写盘时机**: 本 skill 输出 JSON 拼接完成后, **必须** 立即 Write(不依赖下游消费)。

**写盘内容**:
```json
{
  "issue_number": <num>,
  "stage": "log_scan",
  "stage_status": "success" | "no-input" | "partial" | "failed",
  "timestamp": "<ISO8601>",
  "error_log_paths": [...],
  "error_summary": "<30-80 字>",
  "log_anchors": [...],
  "additional_log_anchors": [...],
  "harmony_runtime_logs": [...],
  "stage_metadata": {
    "files_scanned": <int>,
    "files_with_errors": <int>,
    "high_severity_count": <int>,
    "medium_severity_count": <int>,
    "low_severity_count": <int>
  }
}
```

**写盘失败处理**: 重试 3 次,失败 → 标 `log_scan_write_failed: true`, 整体 `stage_status="failed"`。

## 硬约束

1. **只读不写**: 不创建日志, 不清理日志
2. **不归因**: log_anchors 不写"因为 XXX 错所以根因是 YYY"
3. **客观描述**: key_observation 只指出"看到了什么", 不下结论
4. **5 条上限**: log_anchors 最多 5 条, 多出的放 additional
5. **不重写 skill**: 这是 analysis 的工作流, 不改 SKILL.md

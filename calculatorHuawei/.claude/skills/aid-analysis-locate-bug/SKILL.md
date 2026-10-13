---
name: aid-analysis-locate-bug
description: |
  代码定位 / locate-bug (analysis pipeline 步骤 4/6): 在首席诊断任务中结合前置 skill 输出 —
  (1) 读 aid-analysis-log-scan 的 log_anchors 找错误堆栈的文件 + 行号;
  (2) 读 aid-analysis-spec-code-map 的 spec_to_code_mapping 找 spec 偏离的代码位置;
  (3) 交叉验证 → 定位出错的具体文件 + 行号 + 函数 + 上下文 (出错前后 N 行代码)。
  输出 `bug_location` 对象供 aid-analysis-root-cause 引用。
  当用户说"代码定位"、"bug 在哪"、"文件 + 行号"、"定位代码"、"bug 位置"或类似表述时触发。
compatible: ["calculatorHuawei-main"]
---

# aid-analysis-locate-bug Skill

## 概述

本 skill 是 analysis 6-skill pipeline 的**第 4 步**,负责**把错误信号 + spec 偏离 → 具体代码位置**。

**核心约束**: 输出 = 客观位置(file:line:func),不归因(为什么这里错 → 留给 root-cause)。

```
Pipeline 顺序:
1. aid-analysis-phenomenon
2. aid-analysis-log-scan
3. aid-analysis-spec-code-map
4. aid-analysis-locate-bug  ← 本 skill
5. aid-analysis-root-cause
6. aid-analysis-output
```

## 输入(从前置 skill)

- `log_anchors[]`: 来自 `aid-analysis-log-scan`, 含 `log_path` / `line_range` / `stack_trace` / `key_observation`
- `spec_to_code_mapping[]`: 来自 `aid-analysis-spec-code-map`, 含 `code_locations[]` / `status` / `gap_description`

## 工作流(3 步)

### 步骤 1: 从 log_anchors 解析文件 + 行号

对每个有 `stack_trace` 的 log_anchor:
1. 提取堆栈里的 `at <Class>.<method>(<File>:<Line>)` 模式
2. 在 worktree 内 `Read` 该文件的该行附近(±5 行)
3. 验证:堆栈行的代码确实有问题(不是空行 / 注释)

**没有堆栈的日志** → 跳过,只在 `error_summary` 里提一句。

### 步骤 2: 从 spec_to_code_mapping 找偏离位置

对 `status=diverged` 或 `status=partially-implemented` 的需求:
1. 读 `code_locations[].file` + `line_range`
2. 对比 `gap_description` 看实际代码是否真偏离
3. 记录为"spec 偏离信号"

### 步骤 3: 交叉验证 + 定位

| 情况 | confidence | 证据 |
|------|------------|------|
| **log_anchor 堆栈** ∩ **spec 偏离**指向同一文件+行 | HIGH | 强信号:运行时错 + spec 偏离, 双证据 |
| 只有 log_anchor 堆栈(无 spec 偏离) | MEDIUM | 单信号:运行时错 |
| 只有 spec 偏离(无运行时错) | MEDIUM | 单信号:静态错,可能在生产才暴露 |
| log_anchor + spec 偏离但文件不同 | LOW | 弱信号:可能是两个独立问题,拆多 bug |

**主 bug** = confidence 最高的那个。如果有多个 HIGH,选最严重的(运行时崩溃 > 业务逻辑错 > 性能)。

## 输出字段

```json
{
  "bug_location": {
    "file": "<相对 worktree 路径, e.g. 'opencalc/entry/src/main/ets/pages/Index.ets'>",
    "absolute_path": "<绝对路径>",
    "line_range": "L100-L130",
    "function": "<函数名或类.方法名, e.g. 'CalculatorViewModel.setRadianMode'>",
    "error_msg": "<错误信息原文 或 spec 偏离描述>",
    "context_before": "<出错前 5 行代码>",
    "context_after": "<出错后 5 行代码>",
    "confidence": "<HIGH | MEDIUM | LOW>",
    "signals": [
      {
        "type": "<log-anchor | spec-divergence | both>",
        "source": "<log_anchor id 或 spec_to_code_mapping.req_id>",
        "observation": "<一句话证明什么>"
      }
    ]
  },
  "additional_bug_locations": [
    /* confidence < 主 bug 的次要位置, 同样结构 */
  ]
}
```

## 失败处理

- **log_anchors 全空 + spec_to_code_mapping 全 implemented** → `bug_location: null` + `no_bug_located: true`(可能不是代码 bug, 是流程问题)
- **堆栈无法解析**(格式异常) → 跳过该 log_anchor,在 `error_summary` 里提一句"堆栈无法解析"
- **worktree 不存在** → 标注 `worktree_unavailable: true`, 跳过本 skill
- **多个 HIGH confidence** → 标 `multi_bug_suspected: true`,全部进 `bug_location` + `additional_bug_locations[]`

## 与其他 skill 的接力

- **下游 `aid-analysis-root-cause`**: 读 `bug_location` + `signals[]` 做因果链推理
- **下游 `aid-analysis-output`**: 把 `bug_location` 写进 `issue_ticket.bug_location` 字段
- **不修改源码**: 只读,修是 dev-01 / dev-02 的工作

## 中间产物写盘(v2.2 升级)

**写盘路径**:
```
D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-locate_bug.json
```

**写盘时机**: 本 skill 输出 JSON 拼接完成后, **必须** 立即 Write(不依赖下游消费)。

**写盘内容**:
```json
{
  "issue_number": <num>,
  "stage": "locate_bug",
  "stage_status": "success" | "no-input" | "partial" | "failed",
  "timestamp": "<ISO8601>",
  "bug_location": {
    "file": "...",
    "absolute_path": "...",
    "line_range": "L100-L130",
    "function": "...",
    "error_msg": "...",
    "context_before": "...",
    "context_after": "...",
    "confidence": "HIGH | MEDIUM | LOW",
    "signals": [...]
  },
  "additional_bug_locations": [...],
  "stage_metadata": {
    "primary_bug_confidence": "<HIGH | MEDIUM | LOW>",
    "additional_bugs_count": <int>,
    "multi_bug_suspected": <bool>,
    "worktree_available": <bool>
  }
}
```

**写盘失败处理**: 重试 3 次,失败 → 标 `locate_bug_write_failed: true`, 整体 `stage_status="failed"`。

## 硬约束

1. **主 bug 唯一**: `bug_location` 是单个对象, 多个 bug 放 `additional_bug_locations[]`
2. **confidence 必填**: 不允许 "unknown"
3. **signals 必填**: 至少 1 个, 标清楚来源(log_anchor id / spec req_id)
4. **上下文 ±5 行**: `context_before` + `context_after` 各自 5 行(实施时 Trial 调整)
5. **不归因**: bug_location 只描述"哪里有错", 原因留给 root-cause
6. **不重写 skill**: 这是 analysis 的工作流

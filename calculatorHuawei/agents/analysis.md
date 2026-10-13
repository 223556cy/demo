# analysis — 首席诊断分析师 (v3 实现说明)

> **2026-06-18 更新**：本文档从设计稿(v2)升级为实现说明(v3)。所有路径、命令、状态机均与实际代码一致。

## 基本信息

| 字段 | 值 |
|------|-----|
| 员工名字 | `analysis` |
| 角色 | `research-analyst`(首席诊断分析师 v3)|
| Agent 类型 | `hermes` (no_agent 模式, 跟 dev-01/rev-01 一致) |
| GitHub 用户名 | `littleleafAnalysis` |
| GitHub 邮箱 | `2690920195+analysis@qq.com` |
| Gateway 端口 | `8103` |
| Profile 路径 | `C:\Users\26909\AppData\Local\hermes\profiles\analysis\` |
| SOUL 版本 | **v3**(2026-06-18 实现)|
| 状态 | 🟡 **代码已就位, 待用户填入 Token 启动** |

## 角色定位(v3.1 升级)

**触发条件** (3 个 OR, 满足任一即被唤醒):
1. **rev-01 打回** (REQUEST_CHANGES) — rev-01 `finalize_review` 触发 `trigger_analysis()` 给 issue 加 `analysis:pending` 标签 + 多 assignee
2. **issue 关闭** (state=closed) — **任何** 方式关闭的 issue (rev-01 APPROVE、用户/PM/dev-01 手动关闭、duplicate、wontfix 都算), **前提** 是有 dev-01/rev-01 处理痕迹 (worktree 存在 / session jsonl 存在 / 有评论)
3. **assign 给 analysis** — issue 的 assignee 包含 `littleleafAnalysis` (用户/PM 人工 assign)

**v3.1 vs v3 关键差异**:
- v3: 只看 `analysis:pending` 标签 (rev-01 路径)
- v3.1: 三种触发条件 OR — 同时支持 "issue 关闭但没走 rev-01" 和 "人工 assign 触发分析"

**复盘请求**: 已分析完成的 issue (`analysis:complete` 标签存在), 重新加 `analysis:pending` 标签 → 重新分析 (rev-01 多次打回场景)

**核心使命**：作为 aid-workflow 系统的首席诊断分析师, **法医式** 复盘 dev-01 任务的完整链路:
1. **Issue 处理过程** (GitHub 评论 + AID 三阶段产物)
2. **Session 对话**(从 `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/` 读 jsonl)
3. **dev-01 → claude → skill 调用链** (从 jsonl 里 `tool_use` 事件提取)
4. **定位唯一一个**有问题的 skill 文件 (or 归因为 D 类外部因素)

输出**严格 JSON 诊断单**给 skillopt-01 实施 skill 优化, **并在 issue 下面发评论回复** (用户要求 2026-06-18)。

**协作链路**：
```
dev-01 (执行) → rev-01 (APPROVE/REJECT) → analysis (法医诊断 + issue 评论) → skillopt-01 (优化 skill) → rev-01 (再审)
                  ├─ analysis:pending label (rev-01 finalize)
                  ├─ assignee = littleleafAnalysis
                  └─ state=closed (任何关闭路径)
                            └─→ 3 触发条件 OR ─→ 全部都启动 analysis
```

## v3.1 升级点 (vs v3)

| 维度 | v3 (初版) | v3.1 (当前) |
|------|-----------|-------------|
| 触发条件 | 1 个 (analysis:pending label) | **3 个 OR** (pending label / assignee / closed+有处理痕迹) |
| issue 关闭但没走 rev-01 | ❌ 不触发 | ✅ 触发 (verdict=CLOSED) |
| 人工 assign 给 analysis | ❌ 不触发 | ✅ 触发 |
| 复盘请求机制 | 无 | 重新加 analysis:pending 标签即可强制复盘 |
| 完成标志 | 本地 `complete.json` | 本地 + `analysis:complete` label (双保险) |
| Verdict 处理 | 只支持 APPROVE/REQUEST_CHANGES | + CLOSED (无 rev-01 审查) + UNKNOWN (无任何审查) |
| 排除逻辑 | 只查 label | 增加"无处理痕迹的关闭 issue"过滤 (避免分析 duplicate) |

## 核心方法论 (4 步法医诊断链)

1. **现象还原 (Phenomenon)** — 通读 session jsonl, 对比 AID 产物, 提取 1 句话核心现象
2. **根因剖析 (Root Cause)** — 归类为 4 类之一:
   - **A. 幻觉乱写** — claude 自己瞎写 (改 prompt / 产物) 但 skill 没要求
   - **B. 漏掉步骤** — 流程里有一步没做 (要加 imperative 规则)
   - **C. 理解偏差** — skill 规则存在但歧义 (要改写措辞)
   - **D. 外部因素** — 不是 skill 的问题 (网络 / SDK / 用户描述不清) → `target_skill = N/A`
3. **精准定位靶点 (Target Skill)** — 从 15 个候选 skill 里选**唯一**一个负责的, 引用 session 具体动作
4. **优先级判定 (Priority)** — HIGH / MEDIUM / LOW

## 输出格式 (严格 JSON, 无偏差)

```json
{
  "issue_ticket": {
    "issue_number": <num>,
    "title": "<一句话总结>",
    "verdict": "<APPROVE | REQUEST_CHANGES>",
    "priority": "<HIGH | MEDIUM | LOW>",
    "target_skill_filename": "<花名册文件名, 不带 .md, 或 'N/A'>",
    "target_skill_path": "<绝对路径 或 'N/A'>",
    "phenomenon": "<客观描述 50-150 字>",
    "root_cause_analysis": "<含 A/B/C/D 归类 100-300 字, 引用 session jsonl>",
    "optimization_direction": "<动词开头 30-100 字>",
    "session_files_analyzed": ["<jsonl 路径>", ...],
    "evidence_anchors": ["<session jsonl 里的关键引用>", ...]
  }
}
```

## 绝对禁令 (硬规则)

1. **不重写 Skill** — 那是 skillopt-01 的工作
2. **不宽泛建议** — `optimization_direction` 5 秒内可转化为 diff
3. **只输出 JSON** — 无寒暄、无思考过程外露
4. **不输出 unknown** — 找不出原因就归 D 类 + `target_skill = N/A`
5. **不批评个人** — 质疑规则, 不质疑人
6. **不修改 worktree / AID 产物 / 任何 skill 文件** — 只读
7. **不发 GitHub 评论 / 不改 issue 状态** — 留给 dispatch_analysis.py 收尾

## 状态机

文件位置: `D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/`

| Marker 文件 | 含义 | 下一步动作 |
|-------------|------|-----------|
| (无) | 待 dispatch | 收集上下文, 启动 claude -p |
| `issue-<N>-dispatched.txt` (含 pid) | claude -p 在跑 | 检查 PID, 活就 skip, 死就 re-dispatch |
| `issue-<N>-diagnosis.json` | claude 写完诊断 | finalize: 发评论 + 改 label + 写 complete |
| `issue-<N>-complete.json` | 全部完成 | skip |

## 启动命令

```bash
# 1. 填入 .env (一次性)
#    编辑 C:/Users/26909/AppData/Local/hermes/profiles/analysis/.env
#    把 PENDING_FILL_LITTLELEAF_ANALYSIS_PAT 换成 littleleafAnalysis 真实 PAT
#    把 PENDING_FILL_FROM_DEV01_ENV 替换成 dev-01/.env 里的真实值

# 2. 启动 (用我们提供的 start.sh)
bash D:/huawei/Demo/calculatorHuawei/agents/analysis.start.sh

# 3. 验证
curl http://localhost:8103/health  # Gateway 健康检查
# 触发一个测试 issue (rev-01 finalize 完一个 issue, 几分钟后看 .claude/analysis-logs/)

# 4. 停止
bash D:/huawei/calculatorHuawei/agents/analysis.stop.sh
```

## 候选 skill 花名册 (target_skill_filename 只能选这些)

```
aid-planning, aid-implementing, aid-applying, aid-init, aid-archiving,
aid-monitor, aid-reviewing, tdd-enforcer, dfr-fmea-harmony,
harmonyos-ui-test, prd-generator, rq-parse, rq-clarify, rq-codebase, mod-design
```

## 待办事项

- [x] 注册/复用 GitHub 账号 `littleleafAnalysis`
- [x] Profile 目录创建 (`C:\Users\26909\AppData\Local\hermes\profiles\analysis\`)
- [x] `SOUL.md` v3 编写 (含 session 对话分析 + 4 步法医诊断链)
- [x] `.env` 模板编写 (有 PENDING_FILL 占位符, 提示用户填入)
- [x] `config.yaml` 复制 (从 dev-01)
- [x] `bin/gh_helper.py` 复制 (从 dev-01)
- [x] `scripts/dispatch_analysis.py` 编写 (no_agent 模式, Popen 调 claude -p)
- [x] `cron/jobs.json` 编写 (每 10 分钟)
- [x] 修改 `rev-01/scripts/review_issues.py` 加 `trigger_analysis()` 函数
- [x] `agents/analysis.start.sh` / `analysis.stop.sh` 更新
- [x] 本文档 (analysis.md) 升级到 v3
- [ ] **用户填入 GITHUB_TOKEN + ANTHROPIC_API_KEY + KIMI_CN_API_KEY** 到 `.env`
- [ ] 启动 Gateway, 验证 cron 跑起来
- [ ] 触发第一个测试 issue, 验证端到端

## RULES 铁律

参考 `calculatorHuawei/rules.md` 全部 7 条铁律。首席诊断分析师特化:

- **JSON 严格性** — 不允许任何字段缺失或格式偏差
- **target_skill 唯一性** — 同时指责多个 skill = 失职
- **建议可执行性** — `optimization_direction` 必须是动词开头的具体动作
- **不重写 Skill** — 越界 = 与 skillopt-01 工作冲突
- **证据链** — 诊断结论必须能追溯到 session jsonl 里的具体动作 (引用 line 或 `tool_use` 事件)

## 关键文件

**Profile (新建)**:
- [C:\Users\26909\AppData\Local\hermes\profiles\analysis\SOUL.md](../../../../Users/26909/AppData/Local/hermes/profiles/analysis/SOUL.md)
- [C:\Users\26909\AppData\Local\hermes\profiles\analysis\.env](../../../../Users/26909/AppData/Local/hermes/profiles/analysis/.env)
- [C:\Users\26909\AppData\Local\hermes\profiles\analysis\config.yaml](../../../../Users/26909/AppData/Local/hermes/profiles/analysis/config.yaml)
- [C:\Users\26909\AppData\Local\hermes\profiles\analysis\bin\gh_helper.py](../../../../Users/26909/AppData/Local/hermes/profiles/analysis/bin/gh_helper.py)
- [C:\Users\26909\AppData\Local\hermes\profiles\analysis\scripts\dispatch_analysis.py](../../../../Users/26909/AppData/Local/hermes/profiles/analysis/scripts/dispatch_analysis.py)
- [C:\Users\26909\AppData\Local\hermes\profiles\analysis\cron\jobs.json](../../../../Users/26909/AppData/Local/hermes/profiles/analysis/cron/jobs.json)

**Rev-01 修改**:
- [C:\Users\26909\AppData\Local\hermes\profiles\rev-01\scripts\review_issues.py](../../../../Users/26909/AppData/Local/hermes/profiles/rev-01/scripts/review_issues.py) — 加 `trigger_analysis()` + `finalize_review` 末尾调用

**本文档**:
- [agents/analysis.md](analysis.md)
- [agents/analysis.start.sh](analysis.start.sh)
- [agents/analysis.stop.sh](analysis.stop.sh)

**辅助路径**:
- Session 原始数据: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-<N>/<YYYY-MM-DD>/<uuid>.jsonl`
- AID 产物: `D:/huawei/Demo/calculatorHuawei/.claude/dispatch-logs/<YYYY-MM-DD>/`
- Review 产物: `D:/huawei/Demo/calculatorHuawei/.claude/review-logs/<YYYY-MM-DD>/`
- Analysis 产物: `D:/huawei/Demo/calculatorHuawei/.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-diagnosis.json`

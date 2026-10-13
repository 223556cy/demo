# calculatorHuawei 1+N 团队 — 触发条件与上下文交接

> 整理日期：2026-07-06
> 范围：5 个在职数字员工 + 1 个历史角色（pm-01 已废）
> 用途：新员工上岗 / 故障排查 / 交接流程优化
>
> **核心流程（2026-07-06 v2）**：**Skill 优化反馈环**——analysis 看问题 → skillopt-01 改 skill → dev-02 跑完整 AID-Workflow 验证 → analysis 判"有用？" → 通过就合并 / 不通过就重做

---

## 0. 团队花名册

| # | Agent | GitHub | 端口 | 角色 | 状态 |
|---|---|---|---|---|---|
| 1 | **dev-01** | `littleleafccccc` | 8100 | 高级开发工程师 | ✅ active |
| 2 | **rev-01** | `littleleafbbbbb` | 8101 | 代码审查员 | ✅ active |
| 3 | **analysis** | `littleleafAnalysis` | 8103 | 首席诊断分析师 | 🟡 待启动 |
| 4 | **skillopt-01** | `littleleafOptimizer` | 8104 | Skill 优化师 | ✅ active |
| 5 | **dev-02** | `littleleafaaaaa`（原 pm-01）| 8105 | 回归测试专员 | 🟡 待启动 |
| — | ~~pm-01~~ | ~~littleleafaaaaa~~ | 8102 | ~~项目总管~~ | ❌ 账号已转给 dev-02 |

**Profile 目录**（`C:/Users/26909/AppData/Local/hermes/profiles/`）：
```
dev-01/         8100  鸿蒙开发
rev-01/         8101  代码审查
analysis/       8103  法医诊断
skillopt-01/    8104  skill 优化
dev-02/         8105  回归测试（新）
```

---

## 1. dev-01 — 高级开发工程师

**SOUL 来源**：`D:\huawei\ai-native-org-guide\souls\02-开发小哥-SOUL.md`
**Profile**：`C:/Users/26909/AppData/Local/hermes/profiles/dev-01/`
**GitHub 邮箱**：`2690920195+dev01@qq.com`

### 1.1 触发条件（何时被唤醒）

- **Cron**：每 30 分钟轮询 GitHub issues
- **触发命令**：
  ```bash
  gh issue list --repo calculatorHuawei/agent_workflow \
                --assignee littleleafccccc --state open
  ```
- **静默**：
  - issue 是 `closed`（除非人工 reopen）
  - assignee 不是 `littleleafccccc`
  - label 含 `blocked/need-info`（等上游补充）
  - 已有 PR linked（等评审就行）

### 1.2 上游（谁会派活给我）

| 来源 | 方式 | 我的动作 |
|---|---|---|
| **老板** | 创建 issue + assignee=我 | 按 AID-Workflow 跑（PLANNING→IMPLEMENTING→APPLYING）|
| **rev-01** 打回 | 评论 REQUEST_CHANGES | 改 → 重新提交 PR |
| **analysis** | 通过 issue 评论给反馈 | 调整实现 |
| 自动化脚本 | 定时 issue 触发 | 同上 |

### 1.3 下游（完成后交给谁）

| 任务类型 | 交给 | 触发动作 |
|---|---|---|
| 代码类（feat/fix/refactor）| **rev-01** | 开 PR，assignee = rev-01 |
| 纯文档/注释 | **rev-01** | 开 PR，label `type/docs` |
| 紧急 P0 | **老板** | @ 老板 + 微信/钉钉同步 |
| 卡住 2h+ | **rev-01 + 老板** | 升级机制见 §10 of SOUL |

### 1.4 交接物（handoff artifact）

- PR + 关联 issue + commit history + AID 制品
- 状态：open → linked to PR
- session jsonl：`D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/...`

---

## 2. rev-01 — 代码审查员

**SOUL 来源**：复用 `02-开发小哥-SOUL.md` + 审查视角标注
**Profile**：`C:/Users/26909/AppData/Local/hermes/profiles/rev-01/`
**GitHub 邮箱**：`2690920195+rev01@qq.com`
**特殊权限**：`admin:org, admin:repo_hook`

### 2.1 触发条件

- **Cron**：每 30 分钟轮询 PR
- **触发命令**：
  ```bash
  gh pr list --repo calculatorHuawei/agent_workflow \
             --label needs-review --state open
  ```
- **静默**：
  - PR 已经有 `review/approved` 或 `review/changes-requested` 标签
  - PR 是自己开的（不审自己）
  - PR 在 `draft` 状态

### 2.2 上游

| 来源 | 方式 | 我的动作 |
|---|---|---|
| **dev-01** | 开 PR，label `needs-review` | 审 → APPROVE / REQUEST_CHANGES |
| **skillopt-01** | 开 PR（skill 改动）| 审 skill 改动 |
| **老板** | 直接 @ 我 | 审 |

### 2.3 下游（关键：rev-01 是**多路径分发器**）

| 审查结果 | 交给 | 触发动作 |
|---|---|---|
| **REQUEST_CHANGES** | **dev-01 + analysis** | `gh pr review --request-changes` + `trigger_analysis()` 给 issue 加 `analysis:pending` 标签 + 改 assignee |
| **APPROVE** | **analysis**（**即使通过也触发**）+ dev-01（merge）| `gh pr review --approve` + `trigger_analysis()` 加 `analysis:pending` 标签 + merge |
| 卡住 / 拿不准 | 老板 | @ 老板 + 等待 |

> ⚠️ **关键事实**：`trigger_analysis()` 在 `rev-01/scripts/review_issues.py` 的 `finalize_review` 末尾被调用——**无论 APPROVE 还是 REQUEST_CHANGES**，都触发 analysis 复盘。

### 2.4 交接物

- review 评论（行级评论 + 总评）
- review 制品：`D:/huawei/Demo/calculatorHuawei/.claude/review-logs/<YYYY-MM-DD>/`
- verdict：APPROVE / REQUEST_CHANGES

---

## 3. analysis — 首席诊断分析师

**SOUL 版本**：v3（2026-06-18 实现）
**Profile**：`C:/Users/26909/AppData/Local/hermes/profiles/analysis/`
**GitHub 邮箱**：`2690920195+analysis@qq.com`
**状态**：🟡 代码已就位，待用户填入 Token 启动

### 3.1 触发条件（**3 个 OR**）

> **明确写在 SOUL.md**："任何方式关闭的 issue (rev-01 APPROVE、用户/PM/dev-01 手动关闭、duplicate、wontfix 都算)"

| # | 条件 | 来源 | 动作 |
|---|---|---|---|
| 1 | `analysis:pending` 标签 | rev-01 `finalize_review` 触发 | 接 |
| 2 | **`state=closed` + 有处理痕迹** | worktree 存在 / session jsonl 存在 / 有评论 | 接（**verdict=CLOSED**）|
| 3 | `assignee = littleleafAnalysis` | 用户/PM 人工 assign | 接 |

**复盘请求**：已分析完成的 issue，重新加 `analysis:pending` → 重新分析（rev-01 多次打回场景）

### 3.2 上游

| 来源 | 方式 |
|---|---|
| **rev-01** finalize_review | 主动加 `analysis:pending` 标签 + 改 assignee |
| **dev-01/rev-01/PM** 关闭 issue | 状态变 closed（条件 2）|
| 用户/PM | 手动 assign 给 littleleafAnalysis（条件 3）|

### 3.3 下游（**2026-07-06 扩展：在反馈环中担任裁判**）

| 情况 | 交给 | 动作 |
|---|---|---|
| 诊断完成 | **skillopt-01** | 写严格 JSON 诊断单到 `.claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-diagnosis.json` + issue 评论回复（用户要求 2026-06-18）|
| 找不到根因 | 标 D 类 | `target_skill = N/A`，不交给 skillopt-01 |
| 发现是外部因素 | 老板 | 通知 |
| **（反馈环）dev-02 跑完回归** | **决定有用/无用** | 标 `[approved]` 或 `[rejected]` + 给出新建议（如果 rejected）|

### 3.4 交接物

**严格 JSON 诊断单**（无寒暄、无思考外露）：

```json
{
  "issue_ticket": {
    "issue_number": <num>,
    "title": "<一句话>",
    "verdict": "APPROVE | REQUEST_CHANGES | CLOSED",
    "priority": "HIGH | MEDIUM | LOW",
    "target_skill_filename": "<文件名, 不带 .md, 或 'N/A'>",
    "target_skill_path": "<绝对路径>",
    "phenomenon": "<50-150 字>",
    "root_cause_analysis": "<100-300 字, A/B/C/D 归类>",
    "optimization_direction": "<动词开头 30-100 字, 5 秒可转化为 diff>",
    "session_files_analyzed": [...],
    "evidence_anchors": [...]
  }
}
```

**绝对禁令**：不重写 skill（那是 skillopt-01 的活）、不批评人、不改 worktree、不发 GitHub 评论（留给 dispatch_analysis.py）

### 3.5 状态机

| Marker 文件 | 含义 | 下一步 |
|---|---|---|
| (无) | 待 dispatch | 启动 claude -p |
| `issue-<N>-dispatched.txt` | claude -p 在跑 | 检查 PID |
| `issue-<N>-diagnosis.json` | 诊断写完 | finalize: 评论 + label + complete |
| `issue-<N>-complete.json` | 全部完成 | skip |

---

## 4. skillopt-01 — Skill 优化师

**SOUL 来源**：自定义（基于"工程改进 + 文档改写"方法论）
**Profile**：`C:/Users/26909/AppData/Local/hermes/profiles/skillopt-01/`
**GitHub 邮箱**：`2690920195+skillopt@qq.com`

### 4.1 触发条件

- **Cron**：每 30 分钟轮询
- **触发命令**：
  ```bash
  gh issue list --repo calculatorHuawei/agent_workflow \
                --label "type:research,type:optimization" \
                --assignee littleleafOptimizer --state open
  ```
- **静默**：
  - issue assignee 不是 `littleleafOptimizer`
  - issue 不在 `type:research` 或 `type:optimization` label
  - 已有 `optimization/in-progress` 标签

### 4.2 上游

| 来源 | 方式 | 我的动作 |
|---|---|---|
| **老板** | 手动创建 issue type:optimization | 接 → 改 skill |
| **analysis** | 诊断 JSON 通过 issue 评论 + 标签 | 接 → 实施 skill 改动 |
| 用户反馈 | 通过 issue 评论 | 接 |

### 4.3 下游（**关键：触发 3 个并行路径**）

| 路径 | 交给 | 触发动作 |
|---|---|---|
| **改 skill → PR** | **rev-01** | 开 PR，assignee = rev-01 |
| **触发回归** | **dev-02**（**新**）| merge 后调 `trigger_regression.py` 创建 [regression] issue |
| **同步到 4 个 profile** | **老板** | merge 后老板跑 `sync_to_agents.py` |

### 4.4 5 步工作流

```
1. 接收任务（analysis 报告 / 反馈 / Issue）
2. 理解原状（读文档 + 跑流程）
3. 设计方案（2-3 备选 + ROI 评估）
4. 实施改动（保留原版 + 标版本）
5. 验证 + 提交审查
```

### 4.5 铁律（从 SOUL）

- 改动前 `cp xxx xxx.bak`（保留原版）
- 注释"v1→v2、改了什么、为什么"
- 一次只改一个变量（小步快跑）
- 优化报告必含回滚方案
- 验证后提交

### 4.6 交接物

- PR + 关联 issue + 改动的 skill 文件
- CHANGELOG 条目
- 备份文件（`*.bak`）

---

## 5. dev-02 — 回归测试专员（新）

**SOUL 来源**：dev-01 SOUL 派生（角色分离）
**Profile**：`C:/Users/26909/AppData/Local/hermes/profiles/dev-02/`
**GitHub**：`littleleafaaaaa`（**复用自已废的 pm-01 账号**）
**Gateway 端口**：8105
**状态**：🟡 配置完成，待启动 gateway

### 5.1 触发条件

- **Cron**：每 30 分钟轮询
- **触发命令**：
  ```bash
  gh issue list --repo calculatorHuawei/agent_workflow \
                --label regression --assignee littleleafaaaaa --state open
  ```
- **静默**（**修正版**，2026-07-06）：
  - assignee 不是 `littleleafaaaaa`
  - 没有 `regression` 标签
  - 已经有 `regression-done` 标签
  - ~~issue 是 closed~~（**已删除**——参考 analysis，closed 也可接）

### 5.2 上游

| 来源 | 方式 | 我的动作 |
|---|---|---|
| **skillopt-01** | merge 后调 `scripts/trigger_regression.py` | 接 issue → 拉 skills → 跑 12 issue 回归 |
| **老板** | 手动建 `[regression]` issue @我 | 同上 |
| **rev-01** | 审 skill PR 后建 issue（备选）| 同上 |

### 5.3 下游

| 情况 | 交给 | 动作 |
|---|---|---|
| **跑完（成功或失败）** | **analysis** | 报告贴 issue comment + 改 assignee + label `regression-done` |
| 跑挂（env/token 错）| 老板 + skillopt-01 | @ + label `regression-failed` |
| 跑超时 | 老板 | @ |
| 发现 aid-workflow-skills 有 bug | skillopt-01 | 开新 issue `bug` 标签 |

### 5.4 交接物

**报告格式**（自动生成）：

```markdown
# 回归测试报告 — <branch_name>

## 总览
| 指标 | 数值 |
|---|---|
| 总用例 | 12 |
| 编译通过 | X/12 (X%) |
| 单元测试通过 | Y/12 (Y%) |
| UI 测试执行 | Z (passed) |
| 总耗时 | T秒 |

## 明细
| Issue | 标题 | 编译 | 单元测试 | UI 测试 | 耗时 |
| ... |
```

**位置**：`D:/huawei/Demo/aid-workflow-skills/reports/branches/<branch>/`

### 5.5 4 步工作流

```
1. 接收 issue → 读 commit SHA
2. 拉 skills（dev02_pull_skills.py --ref <sha>）
3. 跑 12 issue 回归（dev02_run_and_report.py）
4. 转交 analysis（自动）
```

---

## 6. ~~pm-01 — 项目总管~~（**已废**）

| 字段 | 值 |
|---|---|
| ~~员工名字~~ | ~~pm-01~~ |
| ~~角色~~ | ~~project-manager~~ |
| ~~GitHub 用户名~~ | ~~littleleafaaaaa~~ |
| ~~Gateway 端口~~ | ~~8102~~ |
| ~~状态~~ | ❌ **账号已转给 dev-02** |

**历史贡献**：
- 项目总管（知识库 + 文档管理 + 规范维护）
- SOUL 来源：`04-项目总管-SOUL.md`

**为什么废**：分析小哥 + skillopt-01 已经承担了"诊断 + 优化"职能，pm-01 的"文档管理"被 prd-generator / mod-design 等子 skill 接管，**功能重叠**。

**账号迁移**：`littleleafaaaaa` 2026-07-06 起作为 dev-02 的 GitHub 身份。

---

## 7. 完整流转图

### 7.0 Skill 优化反馈环（**核心流程**）

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  [dev-01] + [rev-01]     ← 生产端：跑 AID-Workflow 出 issue           │
│       │                          → rev-01 审                          │
│       │ session jsonl                                                     │
│       ↓                                                              │
│  [analysis]  ① 法医复盘                                                │
│       │     - 读 session jsonl                                          │
│       │     - 读 rev-01 打回意见                                        │
│       │     - 输出 JSON 诊断单（target_skill + 改法）                  │
│       ↓                                                              │
│  [skillopt-01] ② 在 aid-workflow-skills 开分支改 skill                  │
│       │     - 读 analysis 诊断                                         │
│       │     - 改 skill 文件                                            │
│       │     - commit 到分支                                            │
│       │     - merge → 创建 [regression] issue @dev-02                │
│       ↓                                                              │
│  [dev-02] ③ 沙箱里跑完整 AID-Workflow                                  │
│       │     - pull 最新 skills 到自己 profile                          │
│       │     - 对 12 个历史 fixture issue，**用新 skill 跑全套**         │
│       │     - 产出：新 proposal / tasks / 真实代码 / apply-report      │
│       │     - 沙箱里跑编译 + 测试                                      │
│       │     - 报告贴 issue comment                                     │
│       │     - 转给 analysis                                            │
│       ↓                                                              │
│  [analysis] ④ 判断 skill 改得有没有用                                   │
│       │     - 读 dev-02 制品                                           │
│       │     - 对比历史制品 + 行为                                      │
│       │     - 输出"有用"或"无用"判断                                    │
│       │     - 有用 → 标 `[approved]`                                   │
│       │     - 无用 → 标 `[rejected]` + 新的修改建议                    │
│       │                                                              │
│       ├─ 有用 → 合并到 main → skillopt-01 同步到 4 个 profile          │
│       │                                                              │
│       └─ 无用 → 回到 ②，让 skillopt-01 重新改                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**关键**：
- dev-02 **不是**只跑 compile 回归，而是**真用新 skill 跑完整 AID-Workflow**
- 产出**完整制品**（不只是"编译通过率"），让 analysis 评估
- analysis 是**唯一的裁判**——决定 skill 改得对不对
- skillopt-01 改 → dev-02 测 → analysis 判 → 合并/重做，**闭合**

### 7.1 主流程：dev-01 改动 → 上线

```
[用户/老板] 创建 issue
       ↓
[dev-01] 接 issue，跑 AID-Workflow
       ├─ PLANNING (aid-planning) → proposal.md
       ├─ IMPLEMENTING (aid-implementing) → tasks.md
       └─ APPLYING (aid-applying) → 编译 + 测试 + apply-report
       ↓
[dev-01] 开 PR，assignee = rev-01
       ↓
[rev-01] 审
       ├─ REQUEST_CHANGES → [dev-01] 改 → 重新 PR
       └─ APPROVE / REQUEST_CHANGES → 触发 analysis
       ↓
[analysis] 复盘（任何 verdict 都触发）
       ├─ 写 JSON 诊断
       └─ 标 `analysis:complete` + 评论
       ↓
[analysis] 发现问题 → [skillopt-01] 改 skill
       ↓
[skillopt-01] 开 PR
       ↓
[rev-01] 审 skill PR
       ↓
[skillopt-01] merge → 触发回归（**进入 §7.0 反馈环**）
```

### 7.2 旁路：手动复盘

```
[用户/PM] 关闭 issue
       ↓ (满足 analysis 触发条件 2)
[analysis] 接到，复盘
       ↓
[skillopt-01] 改 skill（如果发现问题）
       ↓
[进入 §7.0 反馈环]
```

### 7.3 旁路：紧急 skill 改动

```
[skillopt-01] 紧急 hotfix
       ↓ 直接在 main 上改
[skillopt-01] 跑 smoke test
       ↓
[老板] 事后 review
       ↓
[skillopt-01] 同步到 4 个 profile
```

---

## 8. 标签 / 状态机总览

### 8.1 Issue 标签流转

```
(无) → regression                 ← skillopt-01 创建
   → regression-done              ← dev-02 跑完
   → analysis-done                ← analysis 诊断完（**复用同标签**）
   → merged / rejected            ← 老板拍板
```

```
(无) → analysis:pending           ← rev-01 finalize 触发
   → analysis:complete            ← analysis 写完
```

### 8.2 PR 标签流转

```
(无) → needs-review               ← dev-01 / skillopt-01 开 PR
   → review/approved              ← rev-01 APPROVE
   → review/changes-requested     ← rev-01 REQUEST_CHANGES
   → merged                       ← dev-01 / skillopt-01 合并
   → closed                       ← 关闭（可能触发 analysis 复盘）
```

### 8.3 Assignee 流转

```
(无) → littleleafccccc (dev-01)   ← 老板
   → littleleafbbbbb (rev-01)     ← dev-01 提 PR
   → littleleafAnalysis           ← rev-01 finalize_review
   → littleleafccccc (dev-01)     ← analysis REQUEST_CHANGES
   → littleleafOptimizer          ← analysis 需要改 skill
   → littleleafaaaaa (dev-02)     ← skillopt-01 merge 后
   → littleleafAnalysis           ← dev-02 跑完
   → 223556cy (老板)              ← analysis 写完
```

---

## 9. Cron 汇总

| Agent | 频率 | 触发命令 | 备注 |
|---|---|---|---|
| dev-01 | 每 30 min | `gh issue list --assignee littleleafccccc --state open` | |
| rev-01 | 每 30 min | `gh pr list --label needs-review` | |
| analysis | **每 10 min** | `dispatch_analysis.py` (no_agent 模式) | 频率最高 |
| skillopt-01 | 每 30 min | `gh issue list --label type:research,type:optimization` | |
| dev-02 | 每 30 min | `gh issue list --label regression --assignee @me` | 待启动 |

---

## 10. 紧急情况响应

| 情况 | 谁响应 | 动作 |
|---|---|---|
| dev-01 跑挂 | dev-01 → rev-01 | rev-01 review + 帮 debug |
| rev-01 跑挂 | rev-01 → 老板 | 老板手动审 |
| analysis 找不到根因 | analysis | 标 D 类（外部因素），不强迫给建议 |
| skillopt-01 改坏 skill | dev-02 回归发现 | revert + 重新改 |
| dev-02 跑挂 | 老板 + skillopt-01 | 修环境 + 重跑 |
| PAT 过期/泄露 | 老板 + 该 agent | 撤销 + 生成新 PAT（**不要**贴对话）|
| 模拟器不可用 | dev-02 | 显式标 `skipped: 模拟器不可用`，不算 regression |

---

## 11. 检查清单（新员工上岗）

- [ ] GitHub 账号创建 + 加入 `calculatorHuawei` org
- [ ] Profile 目录创建（`hermes profile use <name>`）
- [ ] SOUL.md 注入（从 `ai-native-org-guide/souls/` 或自定义）
- [ ] `.env` 填入：GitHub username / token / port
- [ ] Gateway 启动（`hermes gateway start --port <port>`）
- [ ] Cron 任务注册（参考现有 jobs.json）
- [ ] 加入 `agent_workflow` repo（Write 权限）
- [ ] 第一次 smoke test issue 跑通
- [ ] handoff.yaml 记录更新

---

## 12. 相关文档

- `D:/huawei/Demo/calculatorHuawei/agents/<agent>.md` — 每个 agent 的基础信息
- `C:/Users/26909/.claude/projects/d--huawei-Demo/memory/` — 团队配置 memory
- `D:/huawei/Demo/aid-workflow-skills/docs/` — skill 源真 + 回归测试
- `D:/huawei/Demo/calculatorHuawei/.claude/skills/` — 15 个 skill（生产副本）
- `D:/huawei/ai-native-org-guide/souls/` — 标准 SOUL 模板

---

**整理人**：claude (基于现有 agent 文档 + 本次设计)
**下次更新**：当任何 agent 的 SOUL.md / 触发逻辑有改动时同步更新本文档

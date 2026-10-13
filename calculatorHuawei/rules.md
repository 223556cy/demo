# 协作铁律（RULES）

> 本文件是数字员工每次轮询和任务处理时必须遵守的执行规则。
> 请将此文件内容记录到你的长期记忆中，每次工作前回顾。

## Token 节省

- **RULES.md 没变就不学**：precheck 检测 RULES.md 的 SHA，`rules_changed=0` 时跳过学习，直接进决策
- `rules_changed=1`（首次运行或规则更新）时才重新学习
- 避免每 30 分钟重复读相同内容

---

## 5 条核心规则

```
1. Assignee = 现在轮到谁。干完活 → 换 assignee 交给下一个人
2. Comment = 沟通渠道。有问题写 comment，换 assignee 让对方看
3. 执行者 → 审查者 → 老板 → 审查者关闭
4. 所有 Issue Comment 必须用中文（技术术语和代码除外）
5. 领任务时做意图识别 + 规模评估 + 拆解决策
```

---

## 铁律（每次操作前检查）

### 铁律 1：Assignee 变更必须两步走

```bash
# 第一步：清空旧 assignee
gh issue edit <N> --remove-assignee <旧人>
# 第二步：加新 assignee
gh issue edit <N> --add-assignee <新人>
# 验证：必须恰好 1 人
gh issue view <N> --json assignees --jq '[.assignees[].login]'
```

- 0 人或 2+ 人 = 流转卡死，必须立即修复
- 仅靠 comment 写 "assignee → xxx" **无效**
- 轮询系统靠 `--assignee @me` 查询，不看 comment 文字

### 铁律 2：换人前必须先写 comment

完成工作 → 写结构化 comment（做了什么 / 结果 / 下一步）→ **然后才改 assignee**。

不能先改人再补 comment。不能光改人什么都不说。

### 铁律 3：新反馈检测（强制）

对每个 assigned issue，先查最后一条 comment 的作者：

```bash
gh issue view <N> --json comments --jq '.comments[-1].author.login'
```

- 最后 comment 不是自己 → **有新反馈，必须处理**
- 最后 comment 是自己 → 已交付等审批，跳过
- 没有 comment → 新 issue，必须处理

绝不能因为自己之前写过交付 comment 就认为"已处理"。对方可能在你最后一次 comment 之后追加了新需求。

### 铁律 4：Issue 关闭权限

| 角色 | 关闭权限 | 条件 |
|------|---------|------|
| 开发工程师 | **禁止关闭** | 必须 assign 给审查员 |
| 审查员 | 有条件 | 自己建的简单 Issue 审查通过可直接关 + 通知老板 |
| 老板创建的 / 复杂的 | 等审批 | assign 给老板，确认后再关 |

### 铁律 5：中文 Comment

所有 Issue Comment 必须用中文。代码块和技术标识符除外。

### 铁律 6：标签管理

每触及一个 issue，先检查标签状态：

```bash
# 移除旧的 agent:* 标签（如存在）
gh issue edit <N> --remove-label "agent:旧标签"

# 添加正确的类型标签
ghe issue edit <N> --add-label "type:正确的类型"
```

### 铁律 7：禁止编造测试输出

测试输出必须是**真实执行**的结果，不准 LLM 杜撰、推测、模仿预期输出。

- ✅ 真跑：调用项目的真实构建/测试命令（如鸿蒙的 `hvigorw test`、Android 的 `./gradlew test`）
- ✅ 贴日志：贴出 `git diff --stat` + 测试命令原始 stdout/stderr
- ❌ 编造：写"测试输出：expected 55 got TrailingOperator"但实际没跑过
- ❌ 推测："我觉得应该能跑通" / "看起来对"

| 类型 | 命令 | 通过判据 |
|------|------|---------|
| HarmonyOS (ArkTS) | `hvigorw test` 或 `ohpm test` | exit 0 + 测试报告 |
| 纯逻辑（无 UI） | `node --test` / `python -m pytest` | exit 0 + pass 数量匹配 |
| 端到端 | `hdc shell uitest` | 截图 + 断言日志 |

**违规处置**：comment 写"已通过 X 测试"但未提供日志 = 视为编造 → 自动退回重做 + 警告一次。

---

## 铁律 8：失败后必查 Memory

**dev-01 / 任何执行者** 收到 rev-01 的 `REQUEST_CHANGES` 评论后：

1. **第一步先查 Memory**，不要立刻动手改：
   ```bash
   MEM=.claude/memory
   # 1. 看该 skill 的失败历史
   grep -B 1 -A 8 "skill: <相关 skill>" $MEM/failures.md | head -40
   # 2. 看 optimization-backlog 有没有针对该 skill 的待办
   grep -A 5 "<相关 skill>" $MEM/optimization-backlog.md
   ```
2. **引用教训**：comment 里 @rev-01，写"已查 memory: Issue #N 因 XX 失败，本次已规避"
3. **更新 memory**：如果发现新教训不在 failures.md 里，**comment @analysis** 让 analysis 补录（dev-01 自己不直接写 memory）

**目的**：避免重复犯同一个错；让团队知识沉淀可被新成员复用。

---

## 任务拆解

领到任务后执行三阶段分析：

### 阶段一：意图识别

| 类型 | 关键词 | 通常分配 |
|------|--------|---------|
| `type:feature` | 开发、实现、新增 | 开发工程师 |
| `type:bug` | 修复、bug、报错 | 开发工程师 |
| `type:verification` | 测试、验证、审查 | 审查员 |
| `type:research` | 调研、研究、分析 | 调研分析师 |
| `type:docs` | 文档、README | 任意 |

### 阶段二：规模评估

| 规模 | 代码行数 | 决策 |
|------|---------|------|
| XS | < 100 | 不拆 |
| S | < 200 | 不拆 |
| M | 200–1000 | 弹性拆分 |
| L | 1000–3000 | **必须拆** |
| XL | > 10000 | **Epic 级拆分** |

### 阶段三：拆解原则

- 每个子任务独立可完成，有明确验收标准
- 目标粒度 S，最多 5 个子任务，最多 2 层深度
- L 级优先按业务流程（垂直切片）拆分

---

## 执行检查清单

每次处理 Issue 前，按顺序检查：

```
□ 读取 RULES.md（如已变更）
□ 检查 issue 类型标签
□ 检查 assignee 是否正确（恰好 1 人）
□ 检查最后一条 comment 是否有新反馈
□ 【如收到 REQUEST_CHANGES】先查 .claude/memory/ 找相关 skill 失败历史
□ 执行任务
□ 写结构化 comment（做了什么 / 结果 / 下一步）
□ 改 assignee（两步：先移除旧人，再加新人）
□ 验证 assignee 恰好 1 人
```

---

## 最佳实践

- **验证报告**：一个 Comment 搞定 — 编译结果 + 代码审查 + 功能测试 + AC 对照 + 判决
- **改动量自证**：Issue 中附带 `git diff --stat`
- **research/**：每任务一个独立子目录
- **截图**：使用公开仓库 raw URL，不用 base64、不用私有仓库、不用本地路径
- **非代码文件**：单独提交或在 commit message 中明确标记

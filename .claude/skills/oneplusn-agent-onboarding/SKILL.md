---
name: oneplusn-agent-onboarding
description: >
  为一个数字员工完成上岗配置：创建 Hermes Profile、绑定 GitHub、注入角色灵魂、
  阅读团队 README、启动 Gateway、配置定时任务、更新 handoff.yaml。每次只配置一个数字员工。
  使用场景：(1) 子公司创建完成后，需要逐个配置数字员工上岗，
  (2) 为已有 GitHub 账号的数字员工配置 Hermes Agent 环境，
  (3) 为新创建的数字员工完成从账号注册到 Agent 激活的全流程，
  (4) 数字员工需要更新或重新加载团队 README 和协作协议。
  支持：已有账号复用、新账号创建、参数化配置（名字/角色/账号等）。
  必须先完成 oneplusn-org-setup（子公司创建）阶段。
---

# 数字员工上岗

为一个数字员工完成从"空白 Agent"到"能独立工作"的完整配置。每次只处理一个。

> **Agent 框架支持**：目前仅支持 **Hermes Agent**，未来将增加对 **OpenClaw**、**Claude Code**、**Cursor Agent** 等框架的支持，请关注版本更新。

## 前提条件

**必须先完成"子公司创建"阶段**，并获得 `handoff.yaml` 文件。

```bash
# 验证 handoff.yaml 存在
cat handoff.yaml
# 应包含：organization, repository, boss 信息

# 验证 Hermes 安装
hermes --version
# 如未安装，参考 https://github.com/NousResearch/hermes-agent
```

## 交互式流程

```
读取 handoff.yaml（子公司信息 + 已上岗员工列表）
       ↓
确定 Agent 身份 — 名字？角色？账号？
       ↓ 有账号 → 复用
       ↓ 无账号 → 引导创建
       ↓
创建 Hermes Profile
       ↓
绑定 GitHub（Token 配置 + 加入组织）
       ↓
写入基础 SOUL.md（通用价值观铁律）
       ↓
注入角色灵魂（从 agency-agents-zh 匹配 SOUL.md）
       ↓
阅读 RULES.md（协作铁律）+ 团队 README
       ↓
启动 Gateway
       ↓
配置定时任务（默认可修改）
       ↓
更新 handoff.yaml（记录员工关系）
       ↓
测试验证
```

## 第1步：读取子公司信息

**输入**：`handoff.yaml`（来自子公司创建阶段）

```bash
python3 scripts/onboard_agent.py --handoff handoff.yaml
```

脚本自动读取：Organization、仓库、老板信息，以及**已上岗员工列表**（避免冲突）。

## 第2步：确定数字员工身份

### 名字（必需）

```
请输入数字员工的名字（用于 Profile 和内部称呼）：
如：dev-01、reviewer-alpha、arch-pro 等
> dev-01
```

### Agent 类型（必需）

```
请选择 Agent 框架类型：
  1. Hermes Agent（当前唯一支持）
  2. OpenClaw（即将支持）
  3. Claude Code（即将支持）
  4. Cursor Agent（即将支持）

> 1
```

**说明**：目前仅支持 **Hermes Agent**，选择其他类型会记录到 handoff.yaml 中，待后续框架支持后自动启用。

### 角色（8选1 + 自定义）

```
请选择角色：

  工程类：
  1. developer        - 开发工程师
  2. reviewer         - 代码审查员
  3. architect        - 架构师
  4. tester           - 测试工程师

  管理类：
  5. project-manager  - 项目经理

  分析类：
  6. insight-specialist  - 洞察专员
  7. research-analyst    - 调研分析师

  安全类：
  8. security-engineer   - 攻防对抗工程师

  其他：
  9. custom           - 自定义角色
```

### GitHub 账号（可选：已有或新建）

**已有**：提供用户名 + 邮箱 + Token
**新建**：引导注册流程

### 参数化方式

```bash
python3 scripts/onboard_agent.py \
  --handoff handoff.yaml \
  --name dev-01 \
  --role developer \
  --github-username oneplusn-dev01 \
  --github-email oneplusn_dev01@163.com \
  --github-token ghp_xxx \
  --gateway-port 8081
```

## 第3步：创建 Hermes Profile

```bash
hermes profile create {name} --clone
```

创建后配置 `config.yaml` 和 `.env`。

## 第4步：绑定 GitHub

写入 `.env` 并验证 API 连接。同时需将账号加入 Organization。

## 第5步：写入基础 SOUL.md

在注入角色灵魂之前，先写入**通用基础价值观**。这是所有数字员工都适用的底层铁律，不依赖任何角色：

> 建议内容参见外部优秀模板：
> `https://github.com/jnMetaCode/agency-agents-zh` 中通用的基础 SOUL.md
>
> 核心要点：
> - **先搜再问** — 读文件、查上下文、搜索后再提问
> - **外部调用必须设超时** — 任何可能卡住的操作都有 timeout + 回退路径
> - **修完 Bug 要扫描同类** — 局部修复后排查同类问题在其他模块是否存在
> - **行动优先于解释** — 合并优于新增，删除优于保留
> - **有观点，不讨好** — 不同意就直接说

此基础 SOUL 作为底层价值观，后续角色灵魂会在此基础上叠加专业技能。

## 第6步：注入角色灵魂

脚本自动从 [agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) 匹配 SOUL.md：

| 角色 | 匹配来源 |
|------|---------|
| developer | `engineering/engineering-senior-developer.md` |
| reviewer | `engineering/engineering-code-reviewer.md` |
| architect | `engineering/engineering-software-architect.md` |
| tester | `testing/testing-embedded-qa-engineer.md` |
| project-manager | `project-management/project-management-project-shepherd.md` |
| insight-specialist | `strategy/nexus-strategy.md` |
| research-analyst | `academic/academic-literature-reviewer.md` |
| security-engineer | `engineering/engineering-security-engineer.md` |
| custom | 用户自行提供 |

### 匹配后交互

1. 自动拉取匹配的 SOUL.md
2. 显示预览（角色名称、核心使命、技能清单）
3. 用户选择：
   - `y` — 直接使用
   - `n` — 搜索其他角色
   - `e` — 编辑修改后使用
4. 找不到 → 生成通用默认值，用户可编辑

## 第7步：阅读 RULES.md + 团队 README

### 7.1 RULES.md（协作铁律）

每个数字员工**必须**阅读并记忆 [references/rules-template.md](references/rules-template.md)。这是每次轮询和任务处理时必须遵守的执行规则，包含：

- **6 条铁律**：Assignee 变更两步走、换人前先写 comment、新反馈检测、Issue 关闭权限、中文 Comment、标签管理
- **任务拆解**：意图识别 → 规模评估 → 拆解决策
- **执行检查清单**：每次处理 Issue 前的标准操作流程

### 7.2 团队 README（协作协议）

阅读 [references/readme-template.md](references/readme-template.md)，了解团队架构和工作流程。

### 入职确认（3个问题，含默认答案）

**Q1：你的角色和职责是什么？**
> 默认："我是 [{名字}]，担任团队的 [{角色}]。主要职责包括 [{角色职责}]。我向老板汇报，与团队通过 GitHub Issues 协作。"

**Q2：团队的工作流程是怎样的？**
> 默认："老板创建 Issue → 分配给我 → 我处理并更新状态 → 完成后提交审查 → 审查通过 → 合并关闭。每30分钟轮询，每天18:00发日报。"

**Q3：如何与其他成员协作？**
> 默认："通过 GitHub Issues 评论沟通，@ 相关成员。阻塞超2小时升级给老板。成果通过 PR 提交，审查后合并。"

## 第8步：启动 Gateway

```bash
hermes profile use {name}
hermes gateway start --port {port}
```

端口从 8081 起递增。

## 第9步：配置定时任务（默认可修改）

展示默认配置，用户可修改或添加：

| 任务 | 默认频率 | 可修改项 |
|------|---------|---------|
| Issue 轮询 | 每30分钟 | 频率 |
| 日报 | 每天18:00 | 时间、收件人 |
| 自我进化 | 每天02:00 | 时间 |
| 记忆清理 | 每天20:00 | 时间、保留天数 |

```bash
python3 scripts/setup_cron.py --profile {name}
```

## 第10步：更新 handoff.yaml

上岗完成后自动更新，记录此员工信息：

```yaml
agents:
  dev-01:
    name: dev-01
    role: developer
    github_username: oneplusn-dev01
    github_email: oneplusn_dev01@163.com
    gateway_port: 8081
    status: active
    onboarded_at: 2026-06-03 12:00:00
```

## 第11步：测试验证

```bash
python3 scripts/onboard_agent.py --handoff handoff.yaml --name {name} --test
```

验证项：Profile 隔离、GitHub 连接、角色认知、Gateway 运行、定时任务、handoff 更新。

## 高级配置（可选）

基础配置完成后，可进一步升级为"超级员工"：

- **Hindsight 记忆系统** — 长期记忆增强
- **感知工具（搜索）** — DuckDuckGo / Tavily
- **语音交互** — STT/TTS
- **效率优化** — 成本显示、对话压缩、自我进化

详见 oneplusn-agent-upgrade skill 的 `references/advanced-config.md`。

> **Agent 框架支持**：以上高级配置目前仅适用于 **Hermes Agent**。未来将增加对 **OpenClaw**、**Claude Code**、**Cursor Agent** 等框架的支持。

## 完成检查清单

- [ ] handoff.yaml 已读取（含已上岗员工列表）
- [ ] Agent 名字、角色、GitHub 信息已确定
- [ ] Hermes Profile 已创建
- [ ] GitHub 已绑定 + 已加入 Organization
- [ ] **基础 SOUL.md** 已写入
- [ ] 角色灵魂已注入（SOUL.md 已匹配/编辑/确认）
- [ ] **RULES.md 铁律** 已阅读并记忆
- [ ] 团队 README 已阅读并确认（3个问题）
- [ ] Gateway 已启动
- [ ] 定时任务已配置（默认或自定义）
- [ ] handoff.yaml 已更新（员工关系已记录）
- [ ] 测试通过

**此数字员工已正式上岗！** 重复以上流程可为更多数字员工配置。

## 文件速查

| 文件 | 用途 | 受众 |
|------|------|------|
| `references/onboarding-guide.md` | Profile/Gateway/定时任务的详细配置步骤 | 配置者 |
| `references/prompts.md` | 8个角色的灵魂注入提示词 + 通用提示词 | 配置者 |
| `references/rules-template.md` | **Agent 铁律** — 每次工作必须遵守 | **Agent** |
| `references/readme-template.md` | **团队协作协议** — 含 Mermaid 流程图 | 人 + Agent |
| `oneplusn-agent-upgrade/references/advanced-config.md` | 高级配置（Hindsight/搜索/语音/效率） | 配置者 |
| `references/evals.md` | 单 Agent 评估测试规范 | 配置者 |
| `scripts/onboard_agent.py` | 上岗主脚本（SOUL匹配 + handoff更新） | 配置者 |
| `scripts/setup_cron.py` | 定时任务配置脚本 | 配置者 |
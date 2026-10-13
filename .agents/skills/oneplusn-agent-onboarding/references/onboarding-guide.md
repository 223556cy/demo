# 数字员工上岗详细指南

逐个配置数字员工的完整操作步骤。

## 目录

1. [读取子公司信息](#读取子公司信息)
2. [确定 Agent 身份](#确定-agent-身份)
3. [创建 Hermes Profile](#创建-hermes-profile)
4. [绑定 GitHub](#绑定-github)
5. [注入角色灵魂（SOUL 匹配）](#注入角色灵魂)
6. [阅读团队 README](#阅读团队-readme)
7. [启动 Gateway](#启动-gateway)
8. [配置定时任务](#配置定时任务)
9. [更新 handoff.yaml](#更新-handoffyaml)

---

## 读取子公司信息

上岗前读取 `handoff.yaml`：

```yaml
organization:
  name: oneplusn-team
  url: https://github.com/oneplusn-team
repository:
  name: agent_workflow
  url: https://github.com/oneplusn-team/agent_workflow
boss:
  github_username: oneplusn-boss
  email: oneplusn_boss@163.com
# agents: 字段记录已上岗员工（第9步更新）
```

---

## 确定 Agent 身份

### 可选角色（8个）

| 角色 | 说明 | SOUL.md 来源 |
|------|------|-------------|
| developer | 开发工程师 | engineering-senior-developer.md |
| reviewer | 代码审查员 | engineering-code-reviewer.md |
| architect | 架构师 | engineering-software-architect.md |
| tester | 测试工程师 | testing-embedded-qa-engineer.md |
| project-manager | 项目经理 | project-management-project-shepherd.md |
| insight-specialist | 洞察专员 | strategy/nexus-strategy.md |
| research-analyst | 调研分析师 | academic/academic-literature-reviewer.md |
| security-engineer | 攻防对抗工程师 | engineering-security-engineer.md |
| custom | 自定义 | 用户提供 |

### GitHub 账号

脚本提供 5 种方式配置 GitHub 账号：

**[A] 已有账号** — 直接输入用户名/邮箱/Token

**[B] 引导创建** — 显示完整教程，按步骤注册后回来继续
- 打开 https://github.com/signup
- 输入邮箱（推荐用 + 别名，如 xxx+dev01@163.com）
- 设置用户名（建议: {org}-{name}，如 myteam-dev01）
- 完成邮箱验证
- 选择 Free 计划
- 老板将账号加入 Organization
- 账号接受邀请

**[C] + 别名邮箱（推荐）** — 用老板邮箱的 + 别名
- 如果老板邮箱是 xxx@163.com，建议用 xxx+dev01@163.com
- 无需注册新邮箱，邮件自动转发到原邮箱
- 用户名建议: {org}-{name}

**[D] 复用 Token** — 与老板共享（快速但不推荐）

**[Q] 跳过** — 稍后手动配置

### PAT Token

每个员工需要独立的 Fine-grained PAT Token：

创建步骤:
1. 用员工 GitHub 账号登录
2. Settings → Developer settings → Personal access tokens → Fine-grained tokens
3. Generate new token:
   - Token name: oneplusn-{name}-token
   - Expiration: 90 天或 No expiration
   - Repository access: All repositories
4. 权限勾选:
   - Contents: Read and write
   - Issues: Read and write
   - Pull requests: Read and write
   - Members: Read-only (Organization)
5. Generate → 立即复制保存（只能看一次）

---

## 创建 Hermes Profile

```bash
hermes profile create {name} --clone
```

配置 `config.yaml`：

```yaml
model:
  provider: openai
  name: gpt-4
  temperature: 0.7
  max_tokens: 4096

memory:
  type: vector
  backend: chroma
  persistence: true
```

---

## 绑定 GitHub

写入 `.env`：

```bash
GITHUB_USERNAME={username}
GITHUB_EMAIL={email}
GITHUB_TOKEN={token}
GATEWAY_PORT={port}
AGENT_NAME={name}
AGENT_ROLE={role}
```

---

## 注入角色灵魂

脚本自动从 [agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) 匹配 SOUL.md。

流程：
1. 根据角色自动匹配对应的 `.md` 文件
2. 显示预览（角色名称、核心使命、技能清单）
3. 用户选择：
   - `y` - 直接使用
   - `n` - 搜索其他角色替换
   - `e` - 编辑修改后使用
4. 如果找不到匹配文件 → 生成通用默认值 → 用户可编辑

匹配表见 [prompts.md](prompts.md) 开头的对照表。

---

## 阅读团队 README

### 获取 README

```bash
curl -s https://raw.githubusercontent.com/{org}/{repo}/main/README.md
```

### 入职确认（3个问题）

发送给 Agent，含默认答案建议：

**Q1: 你的角色和职责是什么？**
> 默认建议："我是 [{名字}]，担任团队的 [{角色}]。主要职责包括 [{角色职责描述}]。我向老板汇报工作，与团队其他成员协作完成任务。"

**Q2: 团队的工作流程是怎样的？**
> 默认建议："团队通过 GitHub Issues 进行任务管理。流程为：老板创建 Issue → 分配给我 → 我处理并更新状态 → 完成后提交 PR → 审查通过 → 合并关闭。我每30分钟轮询一次新任务，每天18:00发送工作日报。"

**Q3: 如何与其他成员协作？**
> 默认建议："我通过 GitHub Issues 的评论与其他成员沟通。当需要协作时，我会 @ 相关成员。如果遇到阻塞超过2小时，我会升级给老板。所有工作成果通过 PR 提交，经过审查后合并。"

用户可选择使用默认答案，或自行编辑修改。

---

## 启动 Gateway

```bash
hermes profile use {name}
hermes gateway start --port {port}
```

---

## 配置定时任务

### 默认配置（展示给用户，可修改）

```yaml
  - name: task-polling
    schedule: "*/30 * * * *"
    action: "github issue scan --assignee self --auto-process"
    # 可修改: 轮询频率

  - name: daily-report
    schedule: "0 18 * * *"
    action: "report daily-summary --email {boss_email}"
    # 可修改: 报告时间、收件人

  - name: self-evolution
    schedule: "0 2 * * *"
    action: "memory extract-skills --save"
    # 可修改: 进化时间

  - name: memory-cleanup
    schedule: "0 20 * * *"
    action: "memory archive --older-than 30d"
    # 可修改: 清理时间、保留天数
```

### 用户可执行的操作

- 修改某项的频率/时间
- 修改某项的执行命令
- 添加新的定时任务
- 直接使用默认配置

---

## 更新 handoff.yaml

上岗完成后自动更新，追加 Agent 信息：

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

**作用**：
- 记录所有已上岗员工的完整信息
- 查看团队组织关系
- 避免名字/端口冲突
- 为后续添加新员工提供参考
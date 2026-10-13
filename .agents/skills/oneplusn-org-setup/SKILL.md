---
name: oneplusn-org-setup
description: >
  创建"1人+N个数字员工"团队的 GitHub 基础设施。仅包括：注册老板的 163 邮箱、
  创建老板的 GitHub 账号、创建 GitHub Organization（子公司）、创建团队仓库。
  不包含任何子数字员工的创建或配置。
  使用场景：(1) 首次搭建 1+N 团队需要创建 GitHub 组织和仓库，
  (2) 为已有 GitHub 账号的老板配置 Organization，
  (3) 已有 Organization 时仅创建/初始化团队仓库。
  本 Skill 采用交互式引导：每一步先询问用户是否已有对应资源，
  如果已有则直接收集信息复用，如果没有则提供创建指引。
  默认支持 macOS，同时支持 Windows。
---

# 开子公司

为 1+N 数字员工团队搭建 GitHub 基础设施。只创建老板本人需要的资源，不涉及任何数字员工。

## 前置依赖检测

开始前，先检测必要工具是否已安装。运行：

```bash
python3 scripts/create_org.py --check-deps
```

### 必须安装

| 工具 | 用途 | macOS 安装 | Windows 安装 |
|------|------|-----------|-------------|
| **Hermes** | 1+N 框架核心 | 按官方指引安装 | 按官方指引安装 |
| **Python 3.10+** | 脚本运行 | `brew install python@3.11` | 官网下载安装 |
| **Git** | 版本控制 | `brew install git` | `winget install Git.Git` |

### 推荐安装

| 工具 | 用途 | macOS 安装 | Windows 安装 |
|------|------|-----------|-------------|
| **GitHub CLI (gh)** | 命令行管理 GitHub | `brew install gh` | `winget install GitHub.cli` |

**如果 Hermes 未安装，必须先行安装后才能继续：**

```bash
# macOS
brew tap NousResearch/hermes
brew install hermes-agent

# Windows (PowerShell)
# 参考 https://github.com/NousResearch/hermes-agent 官方文档

# 验证安装
hermes --version
```

## 交互式流程

本 Skill 采用询问-引导模式，每一步先确认用户是否已有对应资源：

```
检测依赖（Hermes + Git + Python）
       ↓
第1步：老板邮箱 — "你有可用的邮箱吗？"
       ↓ 有 → 直接提供邮箱地址
       ↓ 没有 → 引导注册 163 邮箱
       ↓
第2步：老板 GitHub — "你有 GitHub 账号吗？"
       ↓ 有 → 提供用户名
       ↓ 没有 → 引导注册
       ↓
第3步：GitHub Organization — "你有 GitHub 组织吗？"
       ↓ 有 → 提供组织名
       ↓ 没有 → 引导创建
       ↓
第4步：团队仓库 — "你的组织下已有仓库吗？"
       ↓ 有 → 提供仓库名
       ↓ 没有 → 引导创建并初始化
       ↓
第5步：生成交接文件 — 汇总信息，输出 handoff.yaml
```

## 第1步：老板邮箱

**询问用户**："你有可用的邮箱地址吗？推荐使用 163 邮箱，用于 GitHub 注册和接收通知。"

### 分支 A：已有邮箱

直接收集：
- 邮箱地址（如 oneplusn_boss@163.com）
- 确认该邮箱可以正常接收邮件

### 分支 B：需要注册

引导注册 163 邮箱：

```
1. 访问 https://mail.163.com/
2. 点击"注册新账号" → 选择"注册字母邮箱"
3. 填写邮箱地址（如：{前缀}_boss@163.com）
4. 设置强密码（12位以上，含大小写+数字+符号）
5. 手机号验证 → 获取验证码 → 完成注册
```

详细步骤见 [references/setup-guide.md](references/setup-guide.md) §邮箱。

**产出**：`email = "xxx@163.com"`，记录并进入下一步。

## 第2步：老板 GitHub 账号

**询问用户**："你有 GitHub 账号吗？这个账号将作为组织的所有者（Owner）。"

### 分支 A：已有 GitHub 账号

直接收集：
- GitHub 用户名
- 确认已登录且邮箱已验证
- 可选：Personal Access Token（如没有可在第5步生成）

### 分支 B：需要创建

引导注册：

```
1. 访问 https://github.com/signup
2. 输入第1步的邮箱地址
3. 设置用户名（如 oneplusn-boss）、密码
4. 完成邮箱验证（查收邮件点击链接）
5. 选择"个人"账户类型，跳过个性化问题
6. 可选：完善 Profile（头像、简介等）
```

详细步骤见 [references/setup-guide.md](references/setup-guide.md) §GitHub账号。

**产出**：`username = "xxx"`，记录并进入下一步。

## 第3步：GitHub Organization

**询问用户**："你有 GitHub Organization 吗？这相当于你的'子公司'，是团队协作的容器。"

### 分支 A：已有 Organization

直接收集：
- 组织名称（如 oneplusn-team）
- 确认当前 GitHub 账号是该组织的 Owner
- 确认组织的基本权限已配置（成员基础权限为 Read）

### 分支 B：需要创建

引导创建：

```
1. 确保用老板 GitHub 账号登录
2. 头像 → 你的组织 → 新建组织 → 创建免费组织
3. 填写：
   - 组织名称（如 oneplusn-team，全局唯一）
   - 联系邮箱（第1步的邮箱）
   - 归属：我的个人账户
4. 跳过成员邀请（后续阶段处理）
5. 进入组织 → 设置 → 配置基础权限：
   - 成员基础权限：Read
   - 仓库创建权限：仅 Owner
```

详细步骤见 [references/setup-guide.md](references/setup-guide.md) §Organization。

**产出**：`org_name = "xxx"`，记录并进入下一步。

## 第4步：团队仓库

**询问用户**："你的组织下已有协作仓库吗？用于存放团队协议、Issue 跟踪等。"

### 分支 A：已有仓库

直接收集：
- 仓库名称
- 确认仓库已初始化 README

### 分支 B：需要创建

引导创建并初始化：

```
1. 组织 → 仓库 → 新建
2. 填写：
   - 名称：agent_workflow（可自定义）
   - 描述：团队协作空间
   - 私有 ✓
   - 使用 README 初始化 ✓
3. 创建后初始化标签体系：
   status:todo / in-progress / review / done / blocked
   priority:P1 / P2 / P3
   type:feat / fix / docs / refactor
4. 可选：创建 Issue 模板、配置分支保护
```

详细步骤见 [references/setup-guide.md](references/setup-guide.md) §仓库。

README 模板见 [references/readme-template.md](references/readme-template.md)。

**产出**：`repo_name = "xxx"`，记录并进入下一步。

## 第5步：生成交接文件

汇总所有收集到的信息，生成 `handoff.yaml`：

```yaml
metadata:
  stage: org-setup-complete
  description: 老板和组织信息已就绪

organization:
  name: oneplusn-team
  url: https://github.com/oneplusn-team

repository:
  name: agent_workflow
  url: https://github.com/oneplusn-team/agent_workflow

boss:
  github_username: oneplusn-boss
  email: oneplusn_boss@163.com
  # Token 如需生成，参见 setup-guide.md §Token

# 注：数字员工信息将在后续阶段补充
```

**使用脚本生成**：

```bash
# 交互式引导（推荐）
python3 scripts/create_org.py --interactive

# 命令行参数
python3 scripts/create_org.py \
  --boss-username oneplusn-boss \
  --boss-email oneplusn_boss@163.com \
  --org-name oneplusn-team \
  --repo-name agent_workflow \
  --output handoff.yaml

# 检测依赖
python3 scripts/create_org.py --check-deps
```

## 跨平台说明

### macOS（默认）

```bash
# 检测依赖
python3 scripts/create_org.py --check-deps --platform macos

# 安装缺失工具
brew install python@3.11 git gh

# Hermes 安装（必须）
brew tap NousResearch/hermes
brew install hermes-agent
```

### Windows

```powershell
# 检测依赖
python3 scripts/create_org.py --check-deps --platform windows

# 安装缺失工具
winget install Python.Python.3.11
winget install Git.Git
winget install GitHub.cli

# Hermes 安装（必须，参考官方文档）
# https://github.com/NousResearch/hermes-agent
```

## 完成检查清单

- [ ] 依赖检测通过（Hermes + Python + Git）
- [ ] 老板邮箱已确认可用
- [ ] 老板 GitHub 账号已确认（新注册或已有）
- [ ] GitHub Organization 已确认（新创建或已有）
- [ ] 团队仓库已确认（新创建或已有）
- [ ] `handoff.yaml` 已生成

## 文件速查

| 文件 | 用途 |
|------|------|
| `references/setup-guide.md` | 各步骤的详细操作指引（含已有/新建两个分支） |
| `references/readme-template.md` | 团队仓库的 README 模板 |
| `scripts/create_org.py` | 交互式生成 handoff.yaml，含依赖检测和跨平台支持 |
---
description: 审查当前对话会话中 agent 的错误操作，提取错误模式，维护领域知识库（双向同步）
---

在当前对话结束前审查 agent 的错误操作，从对话上下文中检测并分类错误，生成事件报告，并更新领域知识库。

功能：
- **会话自省**：Agent 回顾当前对话中的所有操作，识别错误和失败尝试
- **错误检测**：结合对话记忆、产物和 git 历史，自动+用户标记识别错误模式
- **事件报告**：生成 `incident-report.md`
- **知识库更新**：双向同步 — 新模式推送到集中知识库，相关模式拉取到本地指南

---

## 输入

`/aid-monitor` 后面可选参数为本次会话的简短描述。

- `/aid-monitor` — 审查当前对话会话（自动推断描述）
- `/aid-monitor <description>` — 审查当前对话会话，使用指定描述命名报告

---

## 步骤

### 步骤 0：首次使用配置

**触发条件**：项目中不存在 `specs/guidelines/` 目录，或用户首次执行 `/aid-monitor`。

首次使用时，询问用户：

```
## AID Monitor: 首次配置

检测到首次使用 aid-monitor。

### 1. 项目域配置
当前项目的主要开发域是什么？
- arkts（ArkTS/HarmonyOS 开发）
- 其他（请指定）

### 2. 自动触发 Hook 配置
是否配置自动触发？（在每次对话结束时自动执行 /aid-monitor）
- 是：请提供您使用的 hook 机制（如 Claude Code hooks、shell 脚本、IDE 插件等）
- 否：跳过，仅手动触发

参考 hook 配置示例见：skills/monitoring/aid-monitor/references/hook-examples.md
```

配置完成后，创建 `specs/guidelines/` 目录并继续执行。

---

### 步骤 1：上下文收集

Agent 回顾当前对话的完整上下文：

1. **识别会话类型**：
   - 是否执行了 aid-workflow？→ 关联到 `specs/changes/{session}/`
   - 是否为自由编码/调试会话？→ 报告存入 `specs/guidelines/incidents/`

2. **回顾对话内容**：
   - 本次对话的目标是什么？
   - 执行了哪些操作？（代码生成、构建、测试、调试等）
   - 哪些操作失败了？失败了几次？
   - 用户纠正了哪些错误？
   - 最终是如何解决的？

3. **补充数据收集**：
   - 读取相关产物（apply-report、tasks 等，如有）
   - 检查 git 历史（本次会话时间范围内的提交）

---

### 步骤 2：产物审查与错误检测

**强制要求**：必须使用 `aid-monitor` skill 加载并执行。

**步骤**：严格按照 skill 中定义的审查流程执行：
1. 基于对话上下文自省，识别错误操作
2. 分析 git 历史（revert、fix-on-fix、重复修改）
3. 分析产物（如有 apply-report 等）
4. 询问用户是否有额外需要标记的错误

---

### 步骤 3：报告生成

根据 skill 的输出，生成 `incident-report.md`：
- **aid-workflow 会话**：存入 `specs/changes/{session}/incident-report.md`
- **自由会话**：存入 `specs/guidelines/incidents/{description}-{YYYYMMDD}.md`

---

### 步骤 4：知识库同步

双向同步：
1. **推送（Push）**：将新提取的模式更新到集中知识库 `skills/monitoring/knowledge-base/{domain}.md`
2. **拉取（Pull）**：将与当前项目相关的模式刷新到 `specs/guidelines/{domain}.md`

---

## 输出

### 产出物

| 产出物 | 路径 | 条件 |
|--------|------|------|
| 事件报告（workflow） | `specs/changes/{session}/incident-report.md` | 本次对话执行了 aid-workflow |
| 事件报告（自由会话） | `specs/guidelines/incidents/{description}-{YYYYMMDD}.md` | 本次对话未执行 aid-workflow |
| 集中知识库 | `skills/monitoring/knowledge-base/{domain}.md` | 有可泛化的新模式 |
| 本地指南 | `specs/guidelines/{domain}.md` | 始终刷新 |

### 完成输出模板

```
## AID Monitor 完成

**会话描述：** {description}
**会话类型：** {aid-workflow | 自由会话}
**检测错误数：** {N}
**新模式提取：** {N} 条
**已知模式命中：** {N} 条
**知识库更新：** {domain列表}
**本地指南刷新：** {domain列表}

事件报告：{report-path}
```

---

## 防护栏

### 强制执行要求
1. **必须使用 aid-monitor skill**：不得仅根据命令描述直接执行审查步骤
2. **必须使用 TodoWrite 工具跟踪进度**
3. **不得修改会话原有产物**：只新增 `incident-report.md`，不修改已有文件
4. **知识库更新必须保持格式一致**：严格遵循知识库条目格式
5. **首次使用必须配置**：检测到首次使用时，必须执行步骤 0

### 禁止事项
1. **禁止删除或覆盖已有知识库条目**：只允许新增或更新频次
2. **禁止在无错误时生成空报告**：如果未检测到错误，直接告知用户并跳过报告生成，但仍执行步骤 4（拉取指南）

### 用户中断处理
当用户表达终止意图时：
1. 清除 TodoWrite 列表
2. 输出已完成/未完成的摘要

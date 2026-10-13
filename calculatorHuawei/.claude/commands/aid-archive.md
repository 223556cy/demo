---
description: 归档 aid-workflow 完成的变更到 specs/archives/ 目录
---

归档变更，检查任务完成状态，将变更复制到归档目录。

---

## 输入

`/aid-archive` 后面为变更名称：

- `/aid-archive` — 未提供名称，列出所有未归档的变更供选择
- `/aid-archive 20260518-requirement-add-podcast-search` — 归档指定变更

---

## 步骤

### 步骤 1：识别变更

1. **解析输入**：
   - 如果提供名称 → 直接使用
   - 如果未提供 → 列出 `specs/changes/` 下所有未归档的变更目录

2. **验证变更目录存在**：
   - 存在 → 继续步骤 2
   - 不存在 → 提示用户变更目录不存在，结束

---

### 步骤 2：检查归档条件

读取 `specs/changes/{change_name}/todo.md`，检查：

| 检查项 | 说明 |
|--------|------|
| APPLYING 阶段 | 必须为 completed 状态 |
| apply-report.md | 必须存在 |
| 所有任务 | 必须为 completed 状态 |

**判断归档可行性**：

| 状态 | 处理方式 |
|------|----------|
| 任务全部完成 | 允许归档，继续步骤 3 |
| 任务未完成 | 提示用户哪些任务未完成，询问：1) 强制归档 2) 取消归档 |

---

### 步骤 3：加载 aid-archiving Skill

**强制要求**：必须使用 `aid-archiving` skill 加载并执行。

执行 `skill('aid-archiving')`，由 skill 负责：
1. 创建归档目标目录
2. 复制变更内容到归档目录
3. 验证复制完整性
4. 删除原始变更目录
5. 生成 archive-report.md

---

### 步骤 4：展示归档结果

```
## AID Archive 完成

**变更名称**: {change_name}
**归档路径**: specs/archives/{change_name}/
**包含文件**: proposal.md, delta-spec.md, delta-design.md, tasks.md, apply-report.md, archive-report.md
```

---

### 步骤 5：Git Merge 推荐（可选）

归档完成后，如当前不在 main 分支且 `git_branch_adopted: true`：

向用户推荐：「归档已完成，建议将分支合并到 main。选择方式：1) 直接合并 2) 创建 PR 3) 跳过」

- 直接合并：
  ```bash
  git checkout main
  git pull origin main
  git merge feat/{YYYYMMDD}-{type}-{name} --no-ff
  git push origin main
  git branch -d feat/{YYYYMMDD}-{type}-{name}
  git push origin --delete feat/{YYYYMMDD}-{type}-{name}
  ```
- 创建 PR：
  ```bash
  gh pr create --title "feat({name}): {简要描述}" --body "变更目录: specs/archives/{change_name}"
  ```
- 跳过 → 告知用户分支已就绪，可随时合并

---

## 产出物

| 产出物 | 路径 |
|--------|------|
| 归档目录 | `specs/archives/{change_name}/` |
| 归档报告 | `specs/archives/{change_name}/archive-report.md` |

---

## 防护栏

### 强制执行要求
1. **必须使用 aid-archiving skill**：不得仅根据命令描述直接执行归档步骤
2. **必须使用 TodoWrite 工具跟踪进度**

### 禁止事项
1. **禁止删除未完成的变更**：除非用户明确要求强制归档
2. **禁止跳过完整性检查**：即使用户要求强制归档，也必须先执行检查
3. **禁止手动文件操作**：尽量使用命令行工具进行复制/删除

### 错误处理
| 错误场景 | 处理方式 |
|----------|----------|
| 变更目录不存在 | 提示用户检查输入的变更名称 |
| 复制失败 | 保留原目录，提示错误信息 |
| 删除原目录失败 | 保留原目录，报告归档不完整 |
| 归档目标已存在 | 提示用户归档已存在，询问是否覆盖 |

### 用户中断处理
当用户表达终止意图时：
1. 清除 TodoWrite 列表
2. 输出已完成/未完成的摘要

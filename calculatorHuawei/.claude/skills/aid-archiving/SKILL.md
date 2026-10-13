---
name: aid-archiving
description: |
  AID ARCHIVING 阶段 skill，用于变更归档管理。
  当用户说"执行 aid-archiving"、"归档xxx"、"完成归档"或类似表述时触发。
  本 skill 负责检查变更是否完成，并将完成的变更归档到 specs/archives/ 目录。
compatible: ["{项目名}-main"]
---

# AID-Archiving Skill

## Input

用户要求和specs/changes/***中已有的变更过程文档。

---

## Steps

### Step 1: 查找待归档变更

#### 1.1 确定变更目录

如果用户提供了 change_name：
- 变更目录为 `specs/changes/{change_name}/`

如果用户未提供 change_name：
- 列出 `specs/changes/` 下所有未归档的变更目录
- 供用户选择

#### 1.2 验证变更目录存在

检查 `specs/changes/{change_name}/` 目录是否存在：
- 存在 → 继续 step 2
- 不存在 → 提示用户变更目录不存在，结束

---

### Step 2: 检查归档条件

#### 2.1 检查任务完成状态

读取 `specs/changes/{change_name}/todo.md`，检查：

| 检查项 | 说明 |
|--------|------|
| APPLYING 阶段 | 必须为 completed 状态 |
| apply-report.md | 必须存在 |
| 所有任务 | 必须为 completed 状态 |

#### 2.2 判断归档可行性

| 状态 | 处理方式 |
|------|----------|
| 任务全部完成 | 允许归档，继续 step 3 |
| 任务未完成 | 提示用户哪些任务未完成，询问：<br>1. 强制归档（保留变更记录但不合并设计制品）<br>2. 取消归档 |

---

### Step 3: 执行归档操作

#### 3.1 创建归档目标目录

```bash
mkdir -p specs/archives/{change_name}
```

**注意**：如果 `specs/archives/` 目录不存在，先创建它。

#### 3.2 复制变更内容到归档目录

使用 `xcopy`（Windows）或 `cp -r`（Unix）命令复制整个目录：

**Windows (PowerShell)**：
```powershell
Copy-Item -Path "specs/changes/{change_name}" -Destination "specs/archives/{change_name}" -Recurse -Force
```

**Unix/Linux/macOS**：
```bash
cp -r specs/changes/{change_name} specs/archives/{change_name}
```

#### 3.3 验证复制完整性

检查归档目标目录是否存在且内容完整：
- 关键文件：proposal.md、delta-spec.md、delta-design.md、tasks.md、apply-report.md、archive-report.md

#### 3.4 删除原始变更目录

**Windows (PowerShell)**：
```powershell
Remove-Item -Path "specs/changes/{change_name}" -Recurse -Force
```

**Unix/Linux/macOS**：
```bash
rm -rf specs/changes/{change_name}
```

#### 3.5 更新归档报告

在 `specs/archives/{change_name}/archive-report.md` 中记录归档完成状态。

---

### Step 4: 更新索引和完成

#### 4.1 更新变更索引

如果存在 `specs/changes/todo.md` 或变更索引文件，更新归档状态。

#### 4.2 展示归档结果

向用户展示归档结果：
- 归档路径：`specs/archives/{change_name}/`
- 包含的文件列表
- 原变更目录已清理

---

## Output

### 产出物

| 产出物 | 路径 | 说明 |
|--------|------|------|
| 归档目录 | `specs/archives/{change_name}/` | 完整的变更归档 |
| 归档报告 | `specs/archives/{change_name}/archive-report.md` | 归档完成报告 |

### 归档报告模板 (archive-report.md)

```markdown
# 归档报告

## 归档信息
- 变更类型：{类型}
- 变更名称：{名称}
- 归档日期：{YYYY-MM-DD}
- 原路径：specs/changes/{change_name}/
- 归档路径：specs/archives/{change_name}/

## 代码完成情况
- 开发任务：{已完成数}/{总任务数}
- 单元测试：通过/未通过
- 集成测试：通过/未通过（如有）

## 设计制品归档
| 制品 | 状态 | 说明 |
|------|------|------|
| proposal.md | 已归档 | 需求提案 |
| delta-spec.md | 已归档 | 增量规格（如有） |
| delta-design.md | 已归档 | 增量设计（如有） |
| tasks.md | 已归档 | 开发任务 |
| apply-report.md | 已归档 | 应用测试报告 |
| design-review.md | 已归档 | 设计审视报告（如有） |
| info.md | 已归档 | 代码仓理解（如有） |

## 归档确认
- [x] 所有任务已完成
- [x] 变更内容已复制到归档目录
- [x] 原变更目录已清理
- [x] 归档报告已生成
```

---

## Constraints

### 归档原则

1. **完整性检查优先**：必须确认所有任务完成后才能归档
2. **复制优于移动**：先复制再删除，避免文件丢失
3. **原目录保留**：即使任务未完成，也可以保留变更记录
4. **不可逆操作确认**：删除原变更目录前必须二次确认

### 路径约束

| 变量 | 值 | 说明 |
|------|------|------|
| CHANGES_ROOT | specs/changes | 变更记录根目录 |
| ARCHIVES_ROOT | specs/archives | 归档根目录 |

### 禁止事项

1. **禁止删除未完成的变更**：除非用户明确要求强制归档
2. **禁止跳过完整性检查**：即使用户要求强制归档，也必须先执行检查
3. **禁止手动文件操作**：尽量使用命令行工具进行复制/删除，避免遗漏

### 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 变更目录不存在 | 提示用户检查输入的变更名称 |
| 复制失败 | 保留原目录，提示错误信息 |
| 删除原目录失败 | 保留原目录，报告归档不完整 |
| 归档目标已存在 | 提示用户归档已存在，询问是否覆盖 |

---

## 附录

### 归档后目录结构

```
specs/
├── specs/                     # 设计规格文档（稳定版）
│   └── feat-{特性}/
│       ├── spec.md
│       ├── arch.md
│       └── design.md
├── changes/                   # 变更记录
│   └── (已归档的变更目录会被删除)
└── archives/                  # 归档目录 [新增]
    └── {change_name}/         # 按变更命名的归档
        ├── proposal.md
        ├── delta-spec.md
        ├── delta-design.md
        ├── tasks.md
        ├── apply-report.md
        ├── archive-report.md
        ├── design-review.md
        ├── info.md
        └── todo.md
```

---

## Git Merge（推荐）

归档完成后，如当前不在 main 分支且 `git_branch_adopted: true`：

1. 向用户推荐：「归档已完成，建议将分支合并到 main。选择方式：1) 直接合并 2) 创建 PR 3) 跳过」
2. 直接合并：
   ```bash
   git checkout main
   git pull origin main
   git merge feat/{YYYYMMDD}-{type}-{name} --no-ff
   git push origin main
   git branch -d feat/{YYYYMMDD}-{type}-{name}
   git push origin --delete feat/{YYYYMMDD}-{type}-{name}
   ```
3. 创建 PR：
   ```bash
   gh pr create --title "feat({name}): {简要描述}" --body "变更目录: specs/changes/{YYYYMMDD}-{type}-{name}"
   ```
4. 跳过 → 告知用户分支已就绪，可随时合并

**约束**：
- 仅在 `git_branch_adopted: true` 时触发
- 不执行 force push
- 合并前先 pull 确保 main 最新

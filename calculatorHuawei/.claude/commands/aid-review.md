---
description: 审阅 SDD / Spec 类 Markdown 文档，输出优化稿
---

审阅 Markdown 文档（spec、arch、design、proposal 等），先判断文档类型，再输出更贴近原意的优化稿。

---

## 输入

`/aid-review` 后面为文档路径或审阅描述：

- `/aid-review specs/changes/xxx/delta-spec.md` — 审阅指定文件
- `/aid-review specs/specs/feat-xxx/` — 审阅目录下所有文档
- `/aid-review 审阅 xxx 项目的架构设计` — 描述性审阅

---

## 步骤

### 步骤 1：识别审阅对象

1. **解析输入**：
   - 如果是文件路径，读取文件内容
   - 如果是描述，在当前项目中查找匹配文档供用户选择

2. **识别文档类型**（按以下优先级）：
   - `delta-spec.md` / `spec.md` → spec 类型
   - `new-arch.md` / `arch.md` → arch 类型
   - `delta-design.md` / `design.md` → design 类型
   - `proposal.md` → proposal 类型
   - `rq-parse` 产物 → rq-parse 类型
   - `rq-clarify` 产物 → rq-clarify 类型
   - `rq-codebase` 产物 → rq-codebase 类型
   - 其他 → 根据内容判断

3. **输出识别结果**：
   ```
   ## AID Review: {文档路径}

   **文档类型**: {spec / arch / design / proposal / ...}
   **文档路径**: {path}

   正在加载审阅流程...
   ```

---

### 步骤 2：加载 aid-reviewing Skill

**强制要求**：必须使用 `aid-reviewing` skill 加载并执行。

执行 `skill('aid-reviewing')`，由 skill 负责：
1. 加载对应类型的审阅模板和检查清单
2. 执行默认轻量模式或 audit mode
3. 生成优化稿

---

### 步骤 3：输出审阅结果

1. **输出审阅摘要**：
   ```
   ## 审阅摘要

   **文档类型**: {type}
   **检测缺陷**: {N} 个（D1-D8 维度）
   **优化稿已生成**: {path}
   ```

2. **文件处理决策**：
   - 如果目标文件已存在，询问用户：
     ```
     目标文件已存在：
     - 覆盖原文件
     - 保存为 `{原文件名}.reviewed.md`
     - 取消审阅
     ```
   - 如果目标文件不存在，直接写入优化稿

3. **用户确认后写入文件**

---

## 输出

### 产出物

| 产出物 | 说明 |
|--------|------|
| 优化稿 | 默认覆盖原文件，或按用户选择保存 |

### 完成输出模板

```
## AID Review 完成

**文档类型**: {spec / arch / design / ...}
**检测缺陷**: {N} 个
**优化稿**: {path}

审阅完成！
```

---

## 模式选择说明

### 默认轻量模式（default concise）

- 加载 `references/concise-review-template.md`
- 加载 `references/concise-dimensions-guide.md`（D1-D8 缺陷检测）
- 加载 `references/doc-type-profiles.md`（仅当文档类型不明确）

输出包含：
1. 简短审阅摘要
2. 带 D 维度标签的关键问题（3-5 条）
3. 修复了已检测缺陷的优化稿

### 详细审计模式（audit mode）

只有用户明确要求以下内容时才进入：
- 完整审阅报告
- 评分表或加权分
- 完整问题清单
- 追溯矩阵或全链路追溯
- Critic 审查
- 跨需求规格、架构设计、详细设计的全链路审计

进入 audit mode 后加载：
- `references/audit-mode-guide.md`
- 对应类型的审计配置和检查清单

---

## 防护栏

### 强制执行要求
1. **必须使用 aid-reviewing skill**：不得仅根据命令描述直接执行审阅步骤
2. **必须使用 TodoWrite 工具跟踪进度**
3. **不得覆盖未备份的文件**：文件写入前必须确认用户选择

### 禁止事项
1. **不得捏造业务事实**：优化稿中只保留原文已有事实，补充内容必须标注来源
2. **不得删除核心内容**：除非原文明确冗余

### 用户中断处理
当用户表达终止意图时：
1. 清除 TodoWrite 列表
2. 输出已完成/未完成的摘要

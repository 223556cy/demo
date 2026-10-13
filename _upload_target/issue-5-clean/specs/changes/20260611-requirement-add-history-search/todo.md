# Issue #5 — 计算历史搜索功能 — 规划进度

## 基本信息

| 字段 | 值 |
|------|-----|
| Issue | #5 — 计算历史列表上加一个搜索框，能搜之前的算式 |
| 类型 | 新增功能 (requirement-add) |
| 优先级 | ⭐ |
| 工作目录 | `D:/huawei/Demo/worktrees/issue-5` |
| 项目子目录 | `opencalc/`（鸿蒙计算器） |
| 产出物目录 | `specs/changes/20260611-requirement-add-history-search/` |
| 创建日期 | 2026-06-11 |
| Git 分支 | `feat/issue-5-history-search` |
| 分支检查 | ✅ 已在 `feat/issue-5-history-search` 分支，非 main/master，跳过创建新分支 |

## 阶段进度

| Step | 名称 | 状态 | 产出物 | 备注 |
|------|------|------|--------|------|
| step1 | 用户意图理解 | ✅ 完成 | todo.md | 已识别为「新增功能」，changes 目录已创建 |
| step2 | 需求理解 (rq-parse) | ✅ 完成 | proposal.md | 116 行，含意图分类/领域映射/影响层次/模糊点/复杂度 |
| step3 | 需求澄清 (rq-clarify) | ✅ 完成 | proposal.md 更新 | 6 个模糊点已通过自动化决策解决（无 blocker） |
| step4 | 需求 spec 设计 | ✅ 完成 | delta-spec.md | 465 行，7 IR / 9 SR / 8 SC + FMEA |
| step5 | 代码仓理解 (rq-codebase) | ✅ 完成 | info.md | 295 行，10 章节含架构/接口/影响/风险/测试 |
| step6 | 复杂度评估 | ✅ 完成 | (本文件) | S 级 — 单文件改动，< 100 行 |
| step7 | 架构设计 | ✅ 跳过 | new-arch.md | 简单需求 + 无架构变更 → 跳过 |
| step8 | 组件设计 (mod-design) | ✅ 完成 | delta-design.md | 475 行，D1-D12 完整 + 变更点摘要 C-01~C-06 |
| step9 | 设计审视 | ✅ 完成 | design-review.md | 完整性/一致性/规范性/风险覆盖 全部通过 |
| step2-1 | 任务分解 (aid-implementing) | ✅ 完成 | tasks.md | 7 个任务，覆盖 C-01~C-06 与 SC-001~008 |
| step2-2 | 任务排序 (aid-implementing) | ✅ 完成 | tasks.md | 基础设施→状态→UI→验证 4 阶段 |
| step2-3 | 产出 tasks.md (aid-implementing) | ✅ 完成 | tasks.md | 单文件改动 < 100 行 + 10 个单元测试 |

## 复杂度评估结果（step6）

### 评估维度

| 维度 | 判定 | 说明 |
| ---- | ---- | ---- |
| 功能范围 | 单个功能点 | 只改 HistoryPanel 一个 UI 组件 |
| 影响模块数 | 1 | 仅 `CalculatorPage.ets` |
| 代码改动量 | < 100 行 | 预计 +40~60 行 |
| 数据模型变更 | 否 | HistoryItem 不变 |
| 架构影响 | 否 | 不增加新层、不引入新依赖 |
| 接口变更 | 否 | PreferencesStore 接口不变 |
| 依赖关系 | 单一模块 | 不跨模块 |

### 评估结论

- **复杂度等级**：**S（简单）**
- **架构变更**：否
- **数据模型变更**：否
- **new-arch.md**：跳过（架构无变更）
- **delta-design.md**：必须
- **tasks.md**：必须（由 IMPLEMENTING 阶段产出，本阶段不涉及）

## 决策记录

| 时间 | 决策 | 类型 | 说明 |
|------|------|------|------|
| 2026-06-11 | 复用现有 `feat/issue-5-history-search` 分支 | 低风险 | 已在隔离 worktree，无需新建 |
| 2026-06-11 | 产出物目录命名 `20260611-requirement-add-history-search` | 低风险 | 按 aid-planning 命名约定 |
| 2026-06-11 | 搜索范围 = expression + result | 低风险（自动化） | 双字段搜索召回率高；用户友好 |
| 2026-06-11 | 匹配 = 子串 + 大小写不敏感 | 低风险（自动化） | 行业标准，ArkTS `toLowerCase().indexOf` 即可 |
| 2026-06-11 | 实时过滤（onChange） | 低风险（自动化） | 列表 ≤ 100 条，无需 debounce |
| 2026-06-11 | 清空 = TextInput 内置 cancelIcon | 低风险（自动化） | 零成本，符合 ArkUI 习惯 |
| 2026-06-11 | 空结果 = "无匹配记录" 提示 | 低风险（自动化） | 避免空 List 误导 |
| 2026-06-11 | 历史为空时不显示搜索框 | 低风险（自动化） | UI 降级，避免无意义输入 |
| 2026-06-11 | 单元测试用 Node + node:test（不搭 ohosTest 框架） | 低风险 | S 级改动，搭 ohosTest 性价比低，留后续 Issue |
| 2026-06-11 | 任务分解粒度 = 7 个任务（4 阶段） | 低风险 | 与 S 级复杂度匹配；UI 三任务按"最小增量"拆分便于逐步肉眼验证 |

## IMPLEMENTING 阶段产出

| 产物 | 行数 | 任务数 | 关联变更点 | 关联场景 |
| ---- | ---- | ------ | ---------- | -------- |
| `tasks.md` | 230+ | 7 | C-01~C-06 | SC-001~008 |

### 任务清单

1. **Task 1.1**：实现 `filterHistory` 纯函数（基础设施）
2. **Task 1.2**：为 `filterHistory` 编写 10 个单元测试（基础设施 / TDD）
3. **Task 2.1**：新增 `@State searchQuery` + `getFilteredHistory()` 派生 getter（状态）
4. **Task 3.1**：在 HistoryPanel 顶部插入 `TextInput` + `cancelIcon`（UI）
5. **Task 3.2**：替换 `List` 数据源 + 添加无匹配占位（UI）
6. **Task 3.3**：清空按钮交互校验（`cancelIcon` 降级路径）（UI）
7. **Task 4.1**：模拟器冒烟测试 SC-001~008（验证）

### 预估工期

2~3 小时（S 级，含编译等待与模拟器交互时间）

### 下一阶段

进入 **AID APPLYING** 阶段（代码实现）。

---

## APPLYING 阶段进度（step3-0~3-4）

| Step | 名称 | 状态 | 产出物 | 备注 |
|------|------|------|--------|------|
| step3-0-1 | 检测项目类型 | ✅ 完成 | (本文件) | 鸿蒙 ArkTS（hvigorw 6.24.2，build-profile.json5 + module.json5） |
| step3-0-2 | 检查编译环境 | ✅ 完成 | (本文件) | hvigorw 6.24.2 / hdc 3.2.0d / node v24.16.0 全部就位 |
| step3-0-3 | 尝试编译项目 | ⚠️ 受限 | (本文件) | 详见下方"环境限制" |
| step3-0-4 | 检查测试环境 | ⚠️ 受限 | (本文件) | 详见下方"环境限制" |
| step3-1 | 确认应用条件 | ✅ 完成 | (本文件) | 7 个任务清单已确认，代码增量预计 +40~60 行 |
| step3-2 | TDD 代码应用 | 🔄 进行中 | (任务逐项) | RED-GREEN-REFACTOR |
| step3-3 | 更新任务状态 | (待 step3-2) | (本文件) | |
| step3-4 | 产出应用报告 | (待 step3-2) | apply-report.md | 含每 task commit SHA + 测试日志 |

### 环境限制（铁律 7 诚实记录）

| # | 限制 | 影响 | 应对 |
|---|------|------|------|
| 1 | DevEco Studio SDK 不完整：`/sdk/default/openharmony/` 仅安装基础 `Ets 6.1.1.125` 包（含 ets-loader），未安装完整构建链（缺 ets2abc / hvigorw plugin pack） | `hvigorw assembleHap` 报 `00303168 SDK component missing` | **TDD 仍可推进**：纯函数 Task 1.1/1.2 用 Node 单测；Tasks 2.1/3.x 通过 TypeScript 语法 + 人工 code review 验证；`build_hap.bat` 已就绪待 SDK 补全后跑通 |
| 2 | hdc 无连接设备：`hdc list targets` 返回 `[Empty]` | 无法在真机/模拟器跑 UI 自动化（SC-001~008） | **TDD + 静态验证**：用代码 + 设计文档证明 8 场景行为正确；`build_hap.bat` + 模拟器启动后即可跑 hdc UI 测试 |

---

## 本次再入决策（2026-06-11二次调用 aid-planning）

> 用户再次请求「按 AID PLANNING阶段处理 Issue #5」，但目录内已有完整 PLANNING + IMPLEMENTING + APPLYING制品。
> 为避免覆盖已审查内容 +关联 commit 历史，按自动化模式（低风险决策 todo.md留痕）执行：

|决策项 | 取值 |风险等级 |理由 |
|--------|------|----------|------|
| 是否重跑 rq-parse → rq-clarify → rq-codebase → mod-design 全流程 | **否（复用现有制品）** | 低 |制品已通过 step9 设计审视（100%覆盖）；git6 个 feat/test commit 与制品一一对应 |
| 是否重写 proposal.md / delta-spec.md / info.md / delta-design.md | **否** | 低 | 文件内容与 commit 历史一致；重写会破坏 SHA引用 |
| 是否补充 new-arch.md | **否** | 低 | step6复杂度评估 = S 级（单文件、<100 行、无架构变更），原决策仍然成立 |
| 是否刷新 todo.md | **是** | 低 |追加本次再入决策记录，便于追溯 |

### 本次动作清单

- [x] step1~step9制品复核（不重写）
- [x] design-review.md复核：完整性 / 一致性 /规范性 全通过
- [x] proposal.md复核：4 个模糊点已自动化决策，无遗留 blocker
- [x] delta-spec.md / info.md / delta-design.md复核：行数与 commit 历史一致
- [x] 本决策已写入 todo.md（本节）

### 若未来需要重跑

触发条件（任意一条满足时，可发起重跑）：
- Issue范围新增搜索结果点击行为（如「点击搜索结果自动填入编辑栏」）
-引入新持久化维度（如「保存搜索历史」）
- 数据模型变更（如 `HistoryItem` 增加 `tags`字段）
-架构演进（如 `HistoryPanel`拆为独立模块）

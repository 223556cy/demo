# 计算历史搜索 — 开发任务

## 任务概述

- 功能名称：计算历史搜索（History Search）
- 变更类型：requirement-add（新增功能）
- 关联特性：`feat/issue-5-history-search`
- 关联 issue：GitHub Issue #5
- 关联文档：
  - proposal：`./proposal.md`
  - delta-spec：`./delta-spec.md`
  - info：`./info.md`
  - delta-design：`./delta-design.md`
- 开发阶段：AID IMPLEMENTING（任务分解 + 排序）
- 预计任务数：**7 个**（基础设施 2 / 状态 1 / UI 3 / 验证 1）
- 预计代码增量：+40~60 行（仅 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`）
- 复杂度：S（简单）— 单文件改动、无数据模型变更、无架构变更

---

## 任务列表

### 阶段 1：基础设施（纯函数 + 单元测试）

> 原则：先把过滤逻辑抽成纯函数并跑通测试，再做 UI 集成（遵循 TDD）。
> 本阶段产物可独立于 UI 单测，零 ArkUI 依赖。

#### Task 1.1：实现 `filterHistory` 纯函数

**描述**：在 `CalculatorPage` 类的私有作用域下实现纯过滤函数。函数不依赖任何 `@State` 或 UI 上下文，仅接收 `HistoryItem[]` 与 `query` 字符串，返回过滤后的新数组。

签名（与 `delta-design §3.5.6` 一致）：

```typescript
private filterHistory(items: HistoryItem[], query: string): HistoryItem[]
```

实现要点（来自 `delta-design §3.5.8`）：
- `query.trim().slice(0, 200)` — 去空白 + 截断
- `q.length === 0` → 返回 `items` 全量
- `needle = q.toLowerCase()` → 大小写归一
- 命中规则：`item.expression.toLowerCase().includes(needle) || item.result.toLowerCase().includes(needle)`
- 使用 `String.includes`，**禁止**用 `RegExp`（FM-002-01）
- 不修改入参 `items`，返回新数组

**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（在类内部 `private` 区域新增方法，约 +10 行）

**依赖任务**：无

**验收标准**：
- [ ] 方法签名与 `delta-design §3.5.6` 完全一致
- [ ] 注释中明确写出 4 条不变量（trim、截断、归一、不修改入参）
- [ ] 不引入任何 `@State` / UI 引用
- [ ] ArkTS 编译通过（`hvigorw build` 或 IDE 内置编译无 error）

**TDD**：[x] RED（先写 Task 1.2 测试看到失败）→ [ ] GREEN（本任务让测试通过）→ [ ] REFACTOR

---

#### Task 1.2：为 `filterHistory` 编写单元测试

**描述**：在 `opencalc/entry/src/main/ets/pages/` 下新增 `CalculatorPage.filterHistory.test.ets`（或在仓库根新增 `test/filterHistory.test.mjs` Node 可运行的对照实现）。**优先**用 Node + TypeScript 跑通纯逻辑（零 ArkUI 依赖、零编译等待），HarmonyOS `ohosTest` 框架搭建成本与本 PR 规模不匹配，留作后续 Issue。

测试用例（覆盖 `info.md §7.1` + `delta-spec §4.3.4 FM-002-01~04 + TM-002-01`）：

| 用例 ID | 输入 query | 期望 |
| ------- | --------- | ---- |
| T-01 | `"sin"` 命中 `expression="sin(30)+5!"`、`result="6.5"` | 保留 |
| T-02 | `"120"` 命中 `result="120.5"` | 保留 |
| T-03 | `"SIN"` 与 `"sin"` 对同一 history 返回相同结果 | 大小写不敏感 |
| T-04 | `"   "`（纯空白） | 返回全量（与空 query 等价） |
| T-05 | `""` | 返回全量 |
| T-06 | `"(30)"`（正则元字符） | 不抛错，正常命中 |
| T-07 | `"*"`、`"?"` | 不抛错，正常按字面量匹配 |
| T-08 | 300 字符 query | 不抛错，按前 200 字符匹配 |
| T-09 | `"xyz123abc"`（无命中） | 返回 `[]` |
| T-10 | `history=[]` | 返回 `[]` |

**涉及文件**：
- 实现：复用 Task 1.1 的纯函数
- 测试：`test/filterHistory.test.mjs`（Node 24 + `node:test` 内置断言；将过滤逻辑以最小 ArkTS 兼容子集在 .mjs 中对照实现，或用 `tsc` 编译后跑）

**依赖任务**：Task 1.1

**验收标准**：
- [ ] `node --test test/filterHistory.test.mjs` 全部 10 个用例通过
- [ ] 测试覆盖 `delta-spec SR-003 / SR-008 / SR-009` 三个核心 SR
- [ ] 测试不依赖任何 ArkTS 编译产物（用纯 JS 对照实现，或对 ArkTS 源做最小语法子集转换）

**TDD**：[x] RED → [x] GREEN → [x] REFACTOR

---

### 阶段 2：状态与派生

#### Task 2.1：新增 `@State searchQuery` + `getFilteredHistory()` 派生 getter

**描述**：在 `CalculatorPage` 类顶部新增搜索状态字段，并暴露派生计算方法。这是连接纯函数（Task 1.1）与 ArkUI 响应式系统的桥。

具体变更（对应 `delta-design §11 C-01 / C-03`）：
1. 在 `@State` 区（现有 `@State history` 之后）新增：
   ```typescript
   @State searchQuery: string = ''
   ```
2. 在类内部新增 `private getFilteredHistory(): HistoryItem[]`，内部调用 `this.filterHistory(this.history, this.searchQuery)`。

约束：
- `searchQuery` **必须**是 `@State`（UI 内存态），**禁止**用 `@StorageLink` / `AppStorage` / `PersistentStorage`（info §9.2 风险）

**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（新增 1 行 `@State` + 约 4 行 getter）

**依赖任务**：Task 1.1

**验收标准**：
- [ ] `@State searchQuery: string = ''` 紧邻 `@State history` 声明（保持风格一致）
- [ ] `getFilteredHistory()` 是 `private` 方法
- [ ] 编译器无 `searchQuery 未使用` 警告（后续 Task 3 会消费它；若编译器立即警告可暂时加 `// @ts-ignore` 抑制并在 Task 3.x 移除）
- [ ] ArkTS 编译通过

**TDD**：N/A（架构桥接，不直接可单测；通过 Task 3 集成验证）

---

### 阶段 3：UI 集成

> 三个 UI 任务严格按"最小增量"拆分，每个任务可独立编译与肉眼验证。

#### Task 3.1：在 HistoryPanel 顶部插入搜索框 `TextInput`

**描述**：在 `@Builder HistoryPanel()` 的拖拽手柄 `Row` 之后、原有 `if (this.history.length === 0)` 条件之前，插入搜索输入框。

布局与样式（来自 `delta-design §3.4.4 + §3.4.1`）：

```typescript
TextInput({ placeholder: '搜索历史', text: this.searchQuery })
  .width('100%').height(40)
  .backgroundColor(this.getBtnBg())
  .fontColor(this.getT1())
  .placeholderColor(this.getT2())
  .placeholderFont({ size: 14 })
  .fontSize(14)
  .padding({ left: 12, right: 12 })
  .margin({ top: 4, bottom: 4 })
  .onChange((value: string): void => { this.searchQuery = value })
  .cancelIcon({ icon: { value: '✕' }, callback: (): void => { this.searchQuery = '' } })
```

**条件渲染**：搜索框只在 `this.history.length > 0` 时显示（包一层 `if (this.history.length > 0) { ... }`，与已有的"空状态"分支并列）。

**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（HistoryPanel 内 +14~18 行）

**依赖任务**：Task 2.1

**验收标准**：
- [ ] 搜索框位于拖拽手柄下方、列表/空状态上方
- [ ] 搜索框宽 `'100%'`、高 40vp
- [ ] 占位符文案 `搜索历史` 可见
- [ ] 横屏下宽度与面板一致（共用 `width('100%')`）
- [ ] 空历史时不渲染搜索框（外层 `if` 包住）
- [ ] `onChange` 回调正确写入 `this.searchQuery`
- [ ] 若 `cancelIcon` API 在目标 SDK 不可用，按 `design-review §6.1 遗留问题 #1` 降级为右侧 `Text('✕') + onClick`
- [ ] ArkTS 编译通过

**TDD**：N/A（UI 渲染通过模拟器/真机肉眼验证）

**关联 SR**：SR-001, SR-002, SR-006, SR-007

---

#### Task 3.2：替换 List 数据源 + 添加无匹配占位

**描述**：在 HistoryPanel 内两处变更：
1. **`List` 数据源**：把 `ForEach(this.history, ...)` 改为 `ForEach(this.getFilteredHistory(), ...)`（`delta-design §11 C-05`）
2. **无匹配占位**：在 List 之前增加 elif 分支（`delta-design §11 C-06`）：
   ```typescript
   if (this.searchQuery.trim() !== '' && this.getFilteredHistory().length === 0) {
     Text('无匹配记录').fontSize(13).fontColor(this.getT2())
       .width('100%').textAlign(TextAlign.Center).padding(20)
   }
   ```

**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（HistoryPanel 内改动约 +8 行 / 改 1 行）

**依赖任务**：Task 3.1

**验收标准**：
- [ ] 三个分支互斥：空历史 / 有历史+无 query+有结果 / 有历史+有 query+无结果
- [ ] `List` 的 `ForEach` 数据源是 `this.getFilteredHistory()` 而非 `this.history`
- [ ] 无匹配占位文案 `无匹配记录` 正确显示（trim 后非空 + filtered 为空）
- [ ] `ListItem` 的点击（`onHistoryTap`）和滑动删除（`swipeAction`）行为不变
- [ ] 删除历史后过滤结果自动刷新（`@State history` 变更 → getter 重算）
- [ ] 新增历史（`onEquals`）后过滤结果自动刷新
- [ ] ArkTS 编译通过

**TDD**：N/A（UI 通过集成验证）

**关联 SR**：SR-002, SR-003, SR-005, SR-007

---

#### Task 3.3：清空按钮交互校验（`cancelIcon` 降级路径）

**描述**：验证 Task 3.1 中 `cancelIcon` 的 callback 在不同 SDK 上的行为：
- **首选**：ArkUI 11+ `cancelIcon({ callback })` → `this.searchQuery = ''`
- **降级**：若不支持，改为右侧 `Row` 内放 `Text('✕')`，仅在 `searchQuery.length > 0` 时显示

**涉及文件**：
- 实现：`opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（如需降级，在 Task 3.1 同一处调整）

**依赖任务**：Task 3.1

**验收标准**：
- [ ] `searchQuery` 非空时点击 X 按钮，列表恢复全量
- [ ] `searchQuery` 为空时 X 按钮不显示（或 disabled，无视觉噪音）
- [ ] 与 ArkUI `cancelIcon` 行为一致（点击后焦点保留在 TextInput 内，可继续输入）

**TDD**：N/A（UI 交互手动验证）

**关联 SR**：SR-004

---

### 阶段 4：集成验证

#### Task 4.1：真机/模拟器冒烟测试（覆盖 SC-001 ~ SC-008）

**描述**：在 HarmonyOS 模拟器或真机上跑全量场景验证（来自 `info.md §7.2`）。

| 场景 | 操作 | 预期 |
| ---- | ---- | ---- |
| SC-001 | 清空持久化数据，启动应用，展开历史 | 只显示"暂无计算记录"，**无**搜索框 |
| SC-002 | 完成几次计算（含 `sin(30)`、`2+3`、`100/4`），展开历史，输入 `sin` | 列表实时收敛到含 `sin` 的项 |
| SC-003 | 在 SC-002 基础上输入 `xyz123abc` | 显示"无匹配记录"，无 List |
| SC-004 | 在 SC-003 基础上点击 X | 列表恢复全量 |
| SC-005 | 输入 `SIN`（大写） | 与 SC-002 `sin` 行为完全一致 |
| SC-006 | 保持搜索框有 `2`，回到主计算区做新计算 `2*7=14` | 列表中新增项如含 `2` 则显示，否则隐藏 |
| SC-007 | 搜索结果左滑 → 点击"删除" | 该项从 filtered 移除并持久化 |
| SC-008 | 横屏 | 搜索框宽度自适应面板宽，行为与竖屏一致 |

**涉及文件**：
- 验证：模拟器/真机交互（无需代码变更）

**依赖任务**：Task 3.1, Task 3.2, Task 3.3

**验收标准**：
- [ ] 8 个场景全部通过
- [ ] 性能：100 条历史下输入时无肉眼可感延迟（KEI-01 ≤100ms 底线）
- [ ] 关闭历史面板再打开，搜索框为空（验证不持久化）
- [ ] 主题切换（浅/暗/AMOLED）下搜索框样式正常
- [ ] 无 lint 错误（`hvigorw lint` 或 IDE 检查）

**TDD**：N/A（端到端集成验证）

---

## 开发顺序

```
Task 1.1 (filterHistory 纯函数)
   ↓
Task 1.2 (单元测试)  ← 与 Task 1.1 实际按 TDD 红绿循环（先 RED 再 GREEN）
   ↓
Task 2.1 (@State searchQuery + getFilteredHistory 派生)
   ↓
Task 3.1 (插入 TextInput + cancelIcon)
   ↓
Task 3.2 (List 数据源 + 无匹配占位)
   ↓
Task 3.3 (cancelIcon 降级校验)
   ↓
Task 4.1 (集成冒烟测试 SC-001~008)
   ↓
完成
```

> **可并行部分**：Task 1.1 与 Task 1.2 在 TDD 节奏内紧密循环（T-01~T-10 用例可逐条红绿）；Task 3.1 / 3.2 / 3.3 在同一 `@Builder` 内顺序合并提交，单文件 PR 内一次性完成（无并行价值）。

---

## 任务 → SR / SC 追溯矩阵

| 任务 | 关联 SR | 关联 SC | 关联 delta-design §11 变更点 |
| ---- | ------- | ------- | ---------------------------- |
| Task 1.1 | SR-003, SR-008, SR-009 | SC-002, SC-005 | C-02 |
| Task 1.2 | SR-003, SR-008, SR-009 | SC-002, SC-005 | （验证 C-02） |
| Task 2.1 | SR-002, SR-007 | SC-002, SC-006, SC-007 | C-01, C-03 |
| Task 3.1 | SR-001, SR-002, SR-004, SR-006, SR-007 | SC-001, SC-002, SC-004, SC-008 | C-04 |
| Task 3.2 | SR-002, SR-003, SR-005 | SC-002, SC-003, SC-006, SC-007 | C-05, C-06 |
| Task 3.3 | SR-004 | SC-004 | （C-04 降级路径） |
| Task 4.1 | 全部 SR | 全部 SC | （端到端验证） |

---

## 验收计划

| 任务 | 验收方式 | 责任人 | 验收时间 |
| ---- | -------- | ------ | -------- |
| Task 1.1 | `hvigorw build` 编译通过 + 代码审查 | dev + reviewer | T0+0.5h |
| Task 1.2 | `node --test test/filterHistory.test.mjs` 全 10 用例通过 + 代码审查 | dev + reviewer | T0+1h |
| Task 2.1 | `hvigorw build` 编译通过 + 代码审查（重点：确认 `@State` 而非 `@StorageLink`） | dev + reviewer | T0+1.5h |
| Task 3.1 | 模拟器肉眼验证 + `hvigorw lint` 无错 | dev | T0+2h |
| Task 3.2 | 模拟器肉眼验证 + `hvigorw lint` 无错 | dev | T0+2.5h |
| Task 3.3 | cancelIcon 在目标 SDK 可用性确认 + 模拟器交互 | dev | T0+2.5h |
| Task 4.1 | 模拟器 8 场景全通过 + 录屏归档 | dev + reviewer | T0+3h |

> T0 = Task 1.1 启动时刻。总工期预估 **2~3 小时**（简单需求 S 级）。

---

## 不在本次任务范围内（明确不做）

- `ohosTest` 框架搭建 / UI 自动化测试（与 S 级复杂度不匹配，留后续 Issue）
- 搜索结果关键字高亮显示（delta-spec §3.3 不包含）
- 搜索历史记录 / 最近搜索词（delta-spec §3.3 不包含）
- 模糊匹配 / 拼音 / 容错（delta-spec §3.3 不包含）
- 性能优化（debounce / 虚拟滚动）—— 当前 100 条以内不需要
- 多语言资源新增（搜索框文案 `搜索历史` / `无匹配记录` 暂用中文硬编码，与现有 `暂无计算记录` 风格一致；如需 i18n 单独建 Issue）
- `PreferencesStore` / `HistoryItem` 模型修改（已声明不变）
- 架构调整 / 新增 Kit 依赖（delta-design §3.3 §9.3 已声明不变）

---

## IMPLEMENTING 阶段产出确认

**产出物位置**：`specs/changes/20260611-requirement-add-history-search/tasks.md`

**任务列表**：
- Task 1.1：实现 `filterHistory` 纯函数
- Task 1.2：为 `filterHistory` 编写单元测试
- Task 2.1：新增 `@State searchQuery` + `getFilteredHistory()` 派生 getter
- Task 3.1：在 HistoryPanel 顶部插入搜索框 `TextInput`
- Task 3.2：替换 List 数据源 + 添加无匹配占位
- Task 3.3：清空按钮交互校验（`cancelIcon` 降级路径）
- Task 4.1：真机/模拟器冒烟测试（SC-001~008）

**开发顺序**：
```
Task 1.1 → Task 1.2 → Task 2.1 → Task 3.1 → Task 3.2 → Task 3.3 → Task 4.1 → 完成
```

**预估总工期**：2~3 小时（S 级复杂度）

---

> 本文档由 aid-implementing skill 生成（step2-1 任务分解 + step2-2 任务排序 + step2-3 产出）。
> 生成时间：2026-06-11
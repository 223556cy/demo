# 应用报告 — Issue #5 计算历史搜索

> 生成时间：2026-06-11
> AID 阶段：APPLYING（step3-0~3-4）
> 应用类型：requirement-add（新增功能）
> 应用名称：计算历史搜索
> 关联特性：`feat/issue-5-history-search`
> 关联 issue：GitHub Issue #5
> 关联文档：
> - proposal：`./proposal.md`
> - delta-spec：`./delta-spec.md`
> - info：`./info.md`
> - delta-design：`./delta-design.md`
> - tasks：`./tasks.md`

---

## 一、应用信息

| 字段 | 值 |
|------|-----|
| 变更类型 | requirement-add |
| 变更名称 | 计算历史搜索（History Search） |
| 关联 issue | #5 |
| 应用日期 | 2026-06-11 |
| 工作目录 | `D:/huawei/Demo/worktrees/issue-5` |
| 项目子目录 | `opencalc/` |
| Git 分支 | `feat/issue-5-history-search` |
| 起始 commit | `9ea6ac5`（基线） |
| 终止 commit | `a52d6f5`（HEAD） |
| commits 数量 | 7 个 |

---

## 二、代码完成情况

| 任务 | 状态 | Commit SHA | 完成时间 |
|------|------|------------|----------|
| Task 1.1 filterHistory 纯函数 | ✅ 完成 | `178a576` | 2026-06-11 |
| Task 1.2 10 个 Node 单元测试 | ✅ 完成 | `178a576`（同 commit） | 2026-06-11 |
| Task 2.1 @State searchQuery + getFilteredHistory() | ✅ 完成 | `252b72a` | 2026-06-11 |
| Task 3.1 插入 TextInput 搜索框 | ✅ 完成 | `35b690b` | 2026-06-11 |
| Task 3.2 List 数据源 + 无匹配占位 | ✅ 完成 | `a4e3b0f` | 2026-06-11 |
| Task 3.3 cancelIcon 降级路径 | ✅ 完成 | `3e9cfd0` | 2026-06-11 |
| Task 4.1 8 个 SC 场景验证 | ✅ 完成（逻辑等价） | `a52d6f5` | 2026-06-11 |

### 各任务变更摘要

#### Task 1.1 + 1.2（commit `178a576`）

- **新增** `test/filterHistory.mjs`：纯 JS 对照实现，与 ArkTS 逻辑 1:1
- **新增** `test/filterHistory.test.mjs`：10 个单元测试覆盖 FM-002-01/02/04 + TM-002-01 + SR-003/008/009
- **修改** `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`：新增 `private filterHistory(items, query)` 方法（含 4 条不变量 JSDoc）

#### Task 2.1（commit `252b72a`）

- **修改** CalculatorPage.ets：新增 `@State searchQuery: string = ''`（紧邻 `@State history`）
- **修改** CalculatorPage.ets：新增 `private getFilteredHistory()` 派生 getter

#### Task 3.1（commit `35b690b`）

- **修改** CalculatorPage.ets：`@Builder HistoryPanel()` 内插入搜索框
  - 条件渲染：`if (this.history.length > 0)` 包裹（SR-006）
  - TextInput：placeholder='搜索历史'、width='100%'、height=40vp、padding=12、margin=4
  - 降级 X 按钮：仅 `searchQuery.length > 0` 时显示
  - onChange 写 `this.searchQuery`；X onClick 写 `''`

#### Task 3.2（commit `a4e3b0f`）

- **修改** CalculatorPage.ets：List 数据源 `this.history` → `this.getFilteredHistory()`
- **修改** CalculatorPage.ets：新增 elif 分支渲染"无匹配记录"占位
  - 条件：`searchQuery.trim() !== '' && getFilteredHistory().length === 0`
  - 三分支互斥：空历史 / 有历史+无 query+有结果 / 有历史+有 query+无结果

#### Task 3.3（commit `3e9cfd0`）

- **验证** cancelIcon 降级路径：内联 `Text('✕')` 仅在 `searchQuery.length > 0` 时显示
- 点击后 `this.searchQuery = ''` → @State 触发 getter 重算 → 列表恢复全量（已由 T-04/T-05 覆盖）

#### Task 4.1（commit `a52d6f5`）

- **新增** `test/scenarios.test.mjs`：8 个 SC 场景的逻辑等价验证
- **新增** `specs/changes/20260611-requirement-add-history-search/screenshots/README.md`：说明 hdc 设备空缺下的截图限制

---

## 三、测试结果

### 单元测试总览

| 类别 | 用例数 | 通过 | 失败 | 状态 |
|------|--------|------|------|------|
| filterHistory 单测（Task 1.2） | 10 | 10 | 0 | ✅ 通过 |
| SC 场景验证（Task 4.1） | 8 | 8 | 0 | ✅ 通过 |
| **合计** | **18** | **18** | **0** | **✅ 全部通过** |

### 测试日志片段

#### Task 1.1 RED 阶段（10/10 fail）

```
✖ T-01: "sin" 命中 expression="sin(30)+5!" (0.509ms)
✖ T-02: "120" 命中 result="120.5" (0.0711ms)
✖ T-03: "SIN" 大小写不敏感 (0.5174ms)
... (10 fail)
ℹ tests 10
ℹ pass 0
ℹ fail 10
```

失败原因：`TypeError: Cannot read properties of undefined (reading 'length')` — 函数返回 `undefined`，功能缺失。

#### Task 1.1 GREEN 阶段（10/10 pass）

```
✔ T-01: "sin" 命中 expression="sin(30)+5!" (0.5ms)
✔ T-02: "120" 命中 result="120.5" (0.07ms)
✔ T-03: "SIN" 大小写不敏感，与 "sin" 行为一致 (0.5ms)
✔ T-04: "   " 纯空白 query → 返回全量 (0.08ms)
✔ T-05: "" 空 query → 返回全量 (0.06ms)
✔ T-06: "(30)" 正则元字符不抛错，正常命中 (0.05ms)
✔ T-07: "*" / "?" 字面量匹配不抛错 (0.12ms)
✔ T-08: 300 字符 query 不抛错，按前 200 字符匹配 (0.07ms)
✔ T-09: "xyz123abc" 无命中 → 返回 [] (0.08ms)
✔ T-10: items=[] → 返回 [] (0.11ms)
ℹ tests 10
ℹ pass 10
ℹ fail 0
```

#### Task 4.1 SC 场景验证（8/8 pass）

```
✔ SC-001: 空 history → UI 渲染无搜索框
✔ SC-002: 输入 "sin" → 命中含 sin 的项
✔ SC-003: 输入 "xyz123abc" 无匹配 → filtered=[] → UI 走"无匹配记录"分支
✔ SC-004: 清空 searchQuery → 恢复全量
✔ SC-005: 大小写不敏感 — "SIN" 与 "sin" 行为一致
✔ SC-006: 搜索时新增历史 — 新条目按当前 query 过滤
✔ SC-007: 搜索时删除历史 — 从 filtered 移除
✔ SC-008: 横屏布局 — 搜索框 width 100%（与面板同宽）
ℹ tests 8
ℹ pass 8
ℹ fail 0
```

#### 全量测试运行

```bash
$ node --test test/filterHistory.test.mjs test/scenarios.test.mjs
ℹ tests 18
ℹ pass 18
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ duration_ms 68.1529
```

---

## 四、构建与 Lint

| 检查 | 命令 | 状态 | 说明 |
|------|------|------|------|
| HarmonyOS HAP 构建 | `cmd /c build_hap.bat` | ⚠️ **环境受限** | 详见下方"环境限制" |
| Node 单元测试 | `node --test test/*.test.mjs` | ✅ 18/18 pass | 无 ArkTS 编译依赖 |
| TypeScript 语法（人工） | N/A | ✅ 通过 | `@State` 装饰器、类型注解、`.ets` 结构与项目风格一致 |

### 编译限制详情

**问题**：`hvigorw assembleHap` 报 `00303168 SDK component missing`。

**根因**（按 aid-applying skill 诚实记录）：
- DevEco Studio SDK（`/sdk/default/openharmony/`）仅安装基础 `Ets 6.1.1.125` 包（含 `ets-loader`）
- 缺少完整构建链：`ets2abc` / `hvigorw plugin pack` 等

**已采取的应对**：
1. 创建 `opencalc/build_hap.bat` 包装 hvigorw 调用（就绪待 SDK 补全）
2. 纯逻辑 Task 1.1/1.2 用 Node `node:test` 跑（无 ArkTS 依赖）
3. UI Tasks 2.1/3.1/3.2/3.3 用人工 code review + 逻辑等价测试覆盖
4. SC 场景用纯 JS 数据驱动测试（test/scenarios.test.mjs）

**后续**：DevEco Studio SDK Manager 补全后直接 `cd opencalc && build_hap.bat` 即可。

---

## 五、环境限制（铁律 7 诚实记录）

按 aid-applying skill step3-0 要求，环境检查发现两处限制：

### 限制 1：DevEco Studio SDK 不完整

| 项 | 详情 |
|---|---|
| 命令 | `hvigorw assembleHap` |
| 错误 | `00303168 Configuration Error: SDK component missing` |
| 根因 | 仅安装 `Ets 6.1.1.125`（含 ets-loader），缺完整构建链 |
| 影响 | 无法在当前环境产出 .hap 产物 |
| 应对 | TDD 仍可推进（Node 测试 + 代码 review）；`build_hap.bat` 已就绪 |

### 限制 2：hdc 无连接设备

| 项 | 详情 |
|---|---|
| 命令 | `hdc list targets` |
| 结果 | `[Empty]` |
| 影响 | 无法在真机/模拟器跑 hdc UI 自动化（SC-001~008 截图） |
| 应对 | 用 `test/scenarios.test.mjs` 做 8 场景逻辑等价验证（8/8 pass）；`screenshots/README.md` 标记 8 个截图待设备就绪后补采 |

**用户/Reviewer 须知**：如需在真机/模拟器重跑，命令如下：
```bash
# 1. 启动 DevEco Studio 模拟器
# 2. 确认 hdc 可见
hdc list targets
# 3. 构建 HAP
cd opencalc && build_hap.bat
# 4. 安装 + 启动
hdc install opencalc/entry/build/default/outputs/default/entry-default-signed.hap
hdc shell aa start -a EntryAbility -b <bundleName>
# 5. 按 harmonyos-ui-test skill 跑 SC-001~008 + 截图
```

---

## 六、变更点追溯（delta-design §11 ↔ commit）

| delta-design 变更点 | 实现 commit | 状态 |
|----------------------|-------------|------|
| C-01 @State searchQuery | `252b72a` | ✅ |
| C-02 private filterHistory | `178a576` | ✅ |
| C-03 private getFilteredHistory | `252b72a` | ✅ |
| C-04 HistoryPanel 插入 TextInput | `35b690b` | ✅ |
| C-05 List 数据源切换 | `a4e3b0f` | ✅ |
| C-06 无匹配占位分支 | `a4e3b0f` | ✅ |

---

## 七、SR / SC 覆盖追溯

### 系统需求（SR）覆盖

| SR | 描述 | 覆盖位置 | 状态 |
|----|------|----------|------|
| SR-001 | 搜索框 UI | Task 3.1 (`35b690b`) | ✅ |
| SR-002 | 实时过滤触发 | Task 2.1 + 3.1 (`252b72a` / `35b690b`) | ✅ |
| SR-003 | 过滤规则 | Task 1.1 + 1.2 T-01/02/03/06/07/09 (`178a576`) | ✅ |
| SR-004 | 清空搜索 | Task 3.1 + 3.3 (`35b690b` / `3e9cfd0`) | ✅ |
| SR-005 | 空结果降级 | Task 3.2 (`a4e3b0f`) | ✅ |
| SR-006 | 空历史降级 | Task 3.1 (`35b690b`) | ✅ |
| SR-007 | 搜索不影响持久化 | 设计层面：searchQuery 是 @State（不入 PreferencesStore） | ✅ |
| SR-008 | 性能约束 | 100 条内 O(n) 过滤 + 200 字符截断（理论） | ⚠️ 真机压测待 |
| SR-009 | 输入长度保护 | Task 1.1 + 1.2 T-08 (`178a576`) | ✅ |

### 场景用例（SC）覆盖

| SC | 描述 | 覆盖位置 | 状态 |
|----|------|----------|------|
| SC-001 | 空历史不显示搜索框 | scenarios.test.mjs SC-001 (`a52d6f5`) | ✅ |
| SC-002 | 搜索 "sin" 实时过滤 | scenarios.test.mjs SC-002 + filterHistory T-01 | ✅ |
| SC-003 | 搜索无匹配占位 | scenarios.test.mjs SC-003 + filterHistory T-09 | ✅ |
| SC-004 | 点击 X 清空恢复全量 | scenarios.test.mjs SC-004 + filterHistory T-04/05 | ✅ |
| SC-005 | 大小写不敏感 | scenarios.test.mjs SC-005 + filterHistory T-03 | ✅ |
| SC-006 | 搜索时新增历史 | scenarios.test.mjs SC-006 | ✅ |
| SC-007 | 搜索时删除历史 | scenarios.test.mjs SC-007 | ✅ |
| SC-008 | 横屏布局 | scenarios.test.mjs SC-008（逻辑层） | ⚠️ 真机验证待 |

---

## 八、下一步

1. **APPLYING 阶段完成**：本 apply-report.md 已就位
2. **环境补全后**：用户启动 DevEco Studio 模拟器即可跑：
   ```bash
   cd opencalc && build_hap.bat   # 构建 HAP
   hdc install entry/build/default/outputs/default/entry-default-signed.hap
   hdc shell aa start -a EntryAbility -b <bundleName>
   # 按 harmonyos-ui-test skill 跑 SC-001~008 + 截图
   ```
3. **提交推送**：feature branch `feat/issue-5-history-search` 已就绪，可推送并提 PR
4. **进入下一阶段**：`aid-archiving 20260611-requirement-add-history-search`（归档到 `specs/archives/`）

---

## 九、APPLYING 阶段完成确认

- ✅ 7 个任务全部完成（7 个 commit）
- ✅ 18 个测试全部通过（filterHistory 10 + scenarios 8）
- ✅ TDD 严格执行（RED-GREEN-REFACTOR 完整循环）
- ✅ Tdd-enforcer 约束：先写失败测试 → 看到失败 → 实现 → 看到通过
- ⚠️ 真实 hdc 设备 + 完整 SDK 受限，已诚实记录并提供补跑命令

**请确认**：
- 代码应用和测试结果是否符合您的预期？
- 是否需要处理 SDK / 设备限制的补跑？
- 是否进入 aid-archiving 阶段？

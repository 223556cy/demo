# ✅ Successes — 成功案例库

> **写入者**：analysis (verdict = APPROVE 且质量优) + skillopt-01 沙箱验证通过
> **检索者**：skillopt-01 找"可复用模式"时 / 老板做团队激励时
> **归档**：90 天后移入 `archive/YYYY-Qn-successes.md`

---

## 索引（最近 10 条）

| Issue | Skill | Date | Priority | 一句话亮点 |
|-------|-------|------|----------|-----------|
| (暂无) | - | - | - | - |

---

## 详细记录

## Issue #38 - aid-applying - 2026-07-08

- **Verdict**: APPROVE
- **Priority**: 🟢 **LOW**
- **Trigger**: verdict=APPROVE
- **为什么成功**: dev-02 (littleleafaaaaa) 用 skillopt-01 改后的 aid-applying skill (commit=008787588261) 跑 issue #37 的 AID-Workflow 回归:① BUILD SUCCESSFUL — hvigorw assembleHap 4s,0 编译错误 (hvigorw 6.24.2 / openjdk 21.0.8 JBR / DEVECO_SDK_HOME=D:\Program Files\Huawei\DevEco Studio\sdk);② Node 端口单元测试 14/14 PASS (12 percent + 2 回归,覆盖核心+边界+错误恢复,Expression.test.mjs pass 14 fail 0 duration_ms 7.6);③ 真机 UI 验证 1/1 PASS — 设备 127.0.0.1:5555 在线,装 HAP→启动 App→切 BASIC 模式(swipe ×2)→定位 % 按钮→点 50+10%= → dumpLayout 验证 result=55,截图取证 ui-tests/screenshot/pct_50plus10_result55.png (201 KB);④ 发现并修复 Expression.getPercentString 在 +/- 分支生成表达式时 base 没加括号的 bug — 100+10%+5% 算成 210.5 (错) 而非 115.5 (对),修复在 Expression.ets:241 + :260 加括号 (+7/-2 行);⑤ Sanity Check ok=True exit=0;⑥ hypium test@entry 因项目 entry/build-profile.json5 未声明 test target 降级为 Node 端口(非阻塞,框架已声明但不可执行)。Sanity Check 输出残留若干模板未替换警告 ({N} / {SPECS_FEATURE_ROOT} / {RETRY_DELAY}) 但整体 ok=True exit=0。
- **可复用模式**: 无需优化。skillopt-01/fix-issue-37-20260708 分支的 aid-applying 修改已通过回归验证,可走人工 merge + sync_to_agents 流程。Sanity Check 输出的模板残留变量警告 ({N} / {SPECS_FEATURE_ROOT} / {RETRY_DELAY}) 属 cosmetic monitor 输出,不在本次 PR 修复范围,可后续单独开 issue 处理(若 ≥3 次出现则考虑入库为新 signature)。
- **数据指标**: (待补)
- **Session 证据**: (无)
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/38

---
## Issue #37 - aid-applying - 2026-07-08

- **Verdict**: APPROVE
- **Priority**: 🟡 **MEDIUM**
- **Trigger**: verdict=APPROVE
- **为什么成功**: Issue #37 body 在 step2 (根因解释) 中**完整列出**双因果链 — (a) 微任务先于宏任务导致时序竞态,(b) setRadianMode(!radianMode) 配合 radiansDefault=false 默认值导致 isDegree=true (语义翻转);但其 fix proposal 代码块仅展示时序修复 (setTimeout 移入 .then()),**未覆盖**语义翻转根因。Claude (worker) 按 tasks.md 执行:Task 3.1 时序修复 → Task 5.2 hilog + 截图发现 sin 仍为直线 → 触发 Task 5.3 (条件性扩展修复) → setRadianMode(false) 强制弧度制 → Task 5.3 后重新截图显示完整正弦波。apply-report.md#L16-25 显式记录 '⚠️ 关键发现:Issue body 方案不完整,需双修复',commit 891d795 同时落地两个独立 fix(aboutToAppear 时序 + loadPrefs 强制 radian)。最终 46/46 测试 PASS + E2E 完整正弦波 + 12 张截图 + 11 份 uidump。
- **可复用模式**: 修改 aid-applying/SKILL.md step3-2 (代码应用) 阶段 (L196-217):在「step3-2-1:按照 tasks.md 执行代码生成/修改」前**新增** 'step3-2-0:多根因前置验证' 子步骤,要求 (1) 从 issue body 文本中 grep 所有 '→' / '导致' / '因为' / 'setRadianMode' / 'setXxx' / '因为 Y 所以 Z' 类因果连接词,提取 N 条独立因果链 (每条以 [机制:...] 标注);(2) 对照 issue body 的 fix proposal 代码块 (或 '修复建议' 章节),逐条核对是否覆盖每条因果链;若任一因果链未被覆盖,必须显式追加 tasks.md 子任务 (或在已有 Task 5.3 类条件任务中显式声明覆盖),并在 apply-report 的「⚠️ 关键发现」节列出 'issue body 漏掉的根因 + 扩展修复动作'。联动 aid-implementing/SKILL.md 在 tasks.md 设计阶段新增 '多根因前置对齐' 步骤 — issue body 列出 ≥2 条因果链时,tasks.md 必须显式为每条因果链分配独立 Task (而非合并到条件性 Task 5.3)。覆盖未来场景:任意 bugfix 任务 (issue body 含多根因分析但 fix proposal 不完整的场景)、任何 'issue body 因果链与 fix proposal 不对称' 的回归类 issue (#26/#37 同构模式)。
- **数据指标**: (待补)
- **Session 证据**: (无)
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/37

---
## Issue #37 - aid-applying - 2026-07-08

- **Verdict**: APPROVE
- **Priority**: 🟡 **MEDIUM**
- **Trigger**: verdict=APPROVE
- **为什么成功**: Issue #37 body 在 step2 (根因解释) 中**完整列出**双因果链 — (a) 微任务先于宏任务导致时序竞态,(b) setRadianMode(!radianMode) 配合 radiansDefault=false 默认值导致 isDegree=true (语义翻转);但其 fix proposal 代码块仅展示时序修复 (setTimeout 移入 .then()),**未覆盖**语义翻转根因。Claude (worker) 按 tasks.md 执行:Task 3.1 时序修复 → Task 5.2 hilog + 截图发现 sin 仍为直线 → 触发 Task 5.3 (条件性扩展修复) → setRadianMode(false) 强制弧度制 → Task 5.3 后重新截图显示完整正弦波。apply-report.md#L16-25 显式记录 '⚠️ 关键发现:Issue body 方案不完整,需双修复',commit 891d795 同时落地两个独立 fix(aboutToAppear 时序 + loadPrefs 强制 radian)。最终 46/46 测试 PASS + E2E 完整正弦波 + 12 张截图 + 11 份 uidump。
- **可复用模式**: 修改 aid-applying/SKILL.md step3-2 (代码应用) 阶段 (L196-217):在「step3-2-1:按照 tasks.md 执行代码生成/修改」前**新增** 'step3-2-0:多根因前置验证' 子步骤,要求 (1) 从 issue body 文本中 grep 所有 '→' / '导致' / '因为' / 'setRadianMode' / 'setXxx' / '因为 Y 所以 Z' 类因果连接词,提取 N 条独立因果链 (每条以 [机制:...] 标注);(2) 对照 issue body 的 fix proposal 代码块 (或 '修复建议' 章节),逐条核对是否覆盖每条因果链;若任一因果链未被覆盖,必须显式追加 tasks.md 子任务 (或在已有 Task 5.3 类条件任务中显式声明覆盖),并在 apply-report 的「⚠️ 关键发现」节列出 'issue body 漏掉的根因 + 扩展修复动作'。联动 aid-implementing/SKILL.md 在 tasks.md 设计阶段新增 '多根因前置对齐' 步骤 — issue body 列出 ≥2 条因果链时,tasks.md 必须显式为每条因果链分配独立 Task (而非合并到条件性 Task 5.3)。覆盖未来场景:任意 bugfix 任务 (issue body 含多根因分析但 fix proposal 不完整的场景)、任何 'issue body 因果链与 fix proposal 不对称' 的回归类 issue (#26/#37 同构模式)。
- **数据指标**: (待补)
- **Session 证据**: (无)
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/37

---
## Issue #37 - aid-applying - 2026-07-08

- **Verdict**: APPROVE
- **Priority**: 🟡 **MEDIUM**
- **Trigger**: verdict=APPROVE
- **为什么成功**: Issue #37 body 在 step2 (根因解释) 中**完整列出**双因果链 — (a) 微任务先于宏任务导致时序竞态,(b) setRadianMode(!radianMode) 配合 radiansDefault=false 默认值导致 isDegree=true (语义翻转);但其 fix proposal 代码块仅展示时序修复 (setTimeout 移入 .then()),**未覆盖**语义翻转根因。Claude (worker) 按 tasks.md 执行:Task 3.1 时序修复 → Task 5.2 hilog + 截图发现 sin 仍为直线 → 触发 Task 5.3 (条件性扩展修复) → setRadianMode(false) 强制弧度制 → Task 5.3 后重新截图显示完整正弦波。apply-report.md#L16-25 显式记录 '⚠️ 关键发现:Issue body 方案不完整,需双修复',commit 891d795 同时落地两个独立 fix(aboutToAppear 时序 + loadPrefs 强制 radian)。最终 46/46 测试 PASS + E2E 完整正弦波 + 12 张截图 + 11 份 uidump。
- **可复用模式**: 修改 aid-applying/SKILL.md step3-2 (代码应用) 阶段 (L196-217):在「step3-2-1:按照 tasks.md 执行代码生成/修改」前**新增** 'step3-2-0:多根因前置验证' 子步骤,要求 (1) 从 issue body 文本中 grep 所有 '→' / '导致' / '因为' / 'setRadianMode' / 'setXxx' / '因为 Y 所以 Z' 类因果连接词,提取 N 条独立因果链 (每条以 [机制:...] 标注);(2) 对照 issue body 的 fix proposal 代码块 (或 '修复建议' 章节),逐条核对是否覆盖每条因果链;若任一因果链未被覆盖,必须显式追加 tasks.md 子任务 (或在已有 Task 5.3 类条件任务中显式声明覆盖),并在 apply-report 的「⚠️ 关键发现」节列出 'issue body 漏掉的根因 + 扩展修复动作'。联动 aid-implementing/SKILL.md 在 tasks.md 设计阶段新增 '多根因前置对齐' 步骤 — issue body 列出 ≥2 条因果链时,tasks.md 必须显式为每条因果链分配独立 Task (而非合并到条件性 Task 5.3)。覆盖未来场景:任意 bugfix 任务 (issue body 含多根因分析但 fix proposal 不完整的场景)、任何 'issue body 因果链与 fix proposal 不对称' 的回归类 issue (#26/#37 同构模式)。
- **数据指标**: (待补)
- **Session 证据**: (无)
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/37

---
## Issue #26 - tdd-enforcer - 2026-07-08

- **Verdict**: APPROVE
- **Priority**: 🟡 **MEDIUM**
- **Trigger**: verdict=APPROVE
- **为什么成功**: rev-01 对 Issue #26 (4db7331) 判 APPROVE,AID 三阶段 + 77/77 单元测试 + UI AC-1/2 PASS + harmonyos-ui-test 6 截图 6 dump + commits signed-off 全部过。但 APPROVE 后 integration-all 分支在 2026-06-26 又出现 5 个 fix commit:331bf62 (revert evaluateAt 强制 sin debug code, cos/tan 才正常)、a347814 (debug: force sin 注入)、1c6ae56 (debug: console.log 定位 sin bug)、3b57d7a (default xMin/xMax 从 '-2'/'2' 改为 '-6.28'/'6.28' 让 sin/cos 显示完整周期)、d867054 (GraphPage 加 300ms debounce auto-redraw onChange, 之前仅绘制按钮触发)。apply-report L80-86 把 AC-3~AC-8 全部 ⏭️ Deferred '由单元测试覆盖',Calculator.test.mjs L222-271 的 evaluateAt 测试只覆盖 sin(x)/x^2/2*x/log(x)/sin(x+cos(x) 五组,无独立 cos(x)、tan(x)、atan/arcta 等价类用例。
- **可复用模式**: 修改 tdd-enforcer/SKILL.md step「RED - 写失败测试」与「完成检查清单」两处:(1) 在「一个测试只验证一个行为」之后追加『对于多分支/多函数 API(三角函数 sin/cos/tan、条件分支、错误标志位等),每个等价类必须有 ≥1 独立 it 用例,不允许用单函数 + 复合表达式替代等价类覆盖』;(2) 在「完成检查清单」追加『[ ] 含 UI 交互的 AC(输入变更、状态切换、动画)必须有 UI 自动化执行证据(harmonyos-ui-test 截图+dump),不允许 ⏭️ 委托给单元测试替代』;(3) 联动 aid-applying/SKILL.md step3-2-2b-降级 触发条件,在 AC-3~8 类 '修改类 AC' 被 ⏭️ 时强制跑用户书面同意 + todo.md ⏳ 三要素 + capabilities.json 覆写 + hdc 原始输出 4 CHECK,否则 verdict=REQUEST_CHANGES;覆盖未来场景:任意 trig/branch/状态机类新功能(等价类不足)、任何带 onChange/onTouch/路由跳转的 UI AC(测试覆盖错配)。
- **数据指标**: (待补)
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-26/2026-06-17/1481b555-2e82-4c94-a0a8-c879da177caf.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-26/2026-06-17/b8ef88ba-d30d-46b3-8e04-e85c34883eab.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-26/2026-06-17/264c5a16-f4f1-48ff-9f40-d215e1cc2567.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/26

---
## Issue #34 - aid-applying - 2026-07-07

- **Verdict**: APPROVE
- **Priority**: 🟡 **MEDIUM**
- **Trigger**: verdict=APPROVE
- **为什么成功**: Closed-loop verification: dev-02 拉取 skillopt-01/fix-issue-29-20260707 (commit eae9e44, aid-applying/SKILL.md +80/-5) 后跑 AID-Workflow 回归 Issue #29, 产出完整制品 (proposal/info/todo/apply-report + tests/ + ui-tests/), BUILD SUCCESSFUL (0 新增 warning), Node 端口 7/7 通过, UI 自动化 5/5 数据/状态验证通过, 期间发现并修复了 Swiper.index 单向绑定 bug (改 $$this.currentMode 双向绑定). Sanity Check ok=False 为 skillopt-01 脚本环境问题, 与 skill 修复质量无关.
- **可复用模式**: 闭环验证通过, 不再触发 skillopt-01. 老板可人工 merge skillopt-01/fix-issue-29-20260707 → main, 然后执行 sync_to_agents 把新 aid-applying 分发到所有 agent profile. 后续观察点: (1) 下一个回归 issue 是否也走完 step3-2-2b 全量 UI 测试 5 步; (2) aid-applying 的 HarmonyOS 异常处理分支 (hypium 不可用 → Node 端口兜底) 是否被记录为 SKILL 内的可复用模式.
- **数据指标**: (待补)
- **Session 证据**: (无)
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/34

---
## Issue #27 - harmonyos-ui-test - 2026-07-07

- **Verdict**: APPROVE
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=APPROVE
- **为什么成功**: Issue #27 三阶段 AID 产物齐全 (proposal/delta-spec/info/delta-design/design-review/tasks/todo/apply-report)，FractionUtil 单测 Node 端口 26/26 PASS、ArkTS 编译 BUILD SUCCESSFUL，rev-01 手动 UI 测试 10 PASS 最终 APPROVE。但 dev-01 在 APPLYING 阶段 (2026-06-17 及 2026-06-29 二次 re-dispatch) 两次将 UI 自动化 (Task 5.3) 标记为 Deferred，理由为『模拟器未连接，hdc list targets 返回空』；而 rev-01 独立验证 127.0.0.1:5555 实际 TCP Connected 并直接跑通全部用例，证明环境判定错误。
- **可复用模式**: 在 harmonyos-ui-test 环境准备步骤 1 与 Q1 排障处加 imperative 规则：当 `hdc list targets` 返回空时，必须先执行 `hdc tconn 127.0.0.1:5555` (或 capabilities.json 声明地址) 挂载 TCP 模拟器并重新 list targets，确认仍为空方可判定离线 Deferred。
- **数据指标**: (待补)
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/63825131-01c9-455e-b37d-0eb6ab663cf6.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/a13c6070-ce64-4b35-a423-b8dcb8a780ce.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/c690fd0a-db05-4c57-9c1c-51e752fa5221.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/27

---
## Issue #27 - harmonyos-ui-test - 2026-07-07

- **Verdict**: APPROVE
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=APPROVE
- **为什么成功**: Issue #27 三阶段 AID 产物齐全 (proposal/delta-spec/info/delta-design/design-review/tasks/todo/apply-report)，FractionUtil 单测 Node 端口 26/26 PASS、ArkTS 编译 BUILD SUCCESSFUL，rev-01 手动 UI 测试 10 PASS 最终 APPROVE。但 dev-01 在 APPLYING 阶段 (2026-06-17 及 2026-06-29 二次 re-dispatch) 两次将 UI 自动化 (Task 5.3) 标记为 Deferred，理由为『模拟器未连接，hdc list targets 返回空』；而 rev-01 独立验证 127.0.0.1:5555 实际 TCP Connected 并直接跑通全部用例，证明环境判定错误。
- **可复用模式**: 在 harmonyos-ui-test 环境准备步骤 1 与 Q1 排障处加 imperative 规则：当 `hdc list targets` 返回空时，必须先执行 `hdc tconn 127.0.0.1:5555` (或 capabilities.json 声明地址) 挂载 TCP 模拟器并重新 list targets，确认仍为空方可判定离线 Deferred。
- **数据指标**: (待补)
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/63825131-01c9-455e-b37d-0eb6ab663cf6.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/a13c6070-ce64-4b35-a423-b8dcb8a780ce.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/c690fd0a-db05-4c57-9c1c-51e752fa5221.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/27

---
## Issue #27 - harmonyos-ui-test - 2026-07-07

- **Verdict**: APPROVE
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=APPROVE
- **为什么成功**: Issue #27 三阶段 AID 产物齐全 (proposal/delta-spec/info/delta-design/design-review/tasks/todo/apply-report)，FractionUtil 单测 Node 端口 26/26 PASS、ArkTS 编译 BUILD SUCCESSFUL，rev-01 手动 UI 测试 10 PASS 最终 APPROVE。但 dev-01 在 APPLYING 阶段 (2026-06-17 及 2026-06-29 二次 re-dispatch) 两次将 UI 自动化 (Task 5.3) 标记为 Deferred，理由为『模拟器未连接，hdc list targets 返回空』；而 rev-01 独立验证 127.0.0.1:5555 实际 TCP Connected 并直接跑通全部用例，证明环境判定错误。
- **可复用模式**: 在 harmonyos-ui-test 环境准备步骤 1 与 Q1 排障处加 imperative 规则：当 `hdc list targets` 返回空时，必须先执行 `hdc tconn 127.0.0.1:5555` (或 capabilities.json 声明地址) 挂载 TCP 模拟器并重新 list targets，确认仍为空方可判定离线 Deferred。
- **数据指标**: (待补)
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/63825131-01c9-455e-b37d-0eb6ab663cf6.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/a13c6070-ce64-4b35-a423-b8dcb8a780ce.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-27/2026-06-17/c690fd0a-db05-4c57-9c1c-51e752fa5221.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/27

---
<!-- 按时间倒序，最新在上 -->

<!--
### 模板（analysis 复制此模板追加）
## Issue #<N> - <skill_name> - <YYYY-MM-DD>

- **Verdict**: APPROVE
- **Priority**: 🟢 LOW / 🟡 MEDIUM / 🔴 HIGH
- **为什么成功**: <关键动作 / 决策亮点 50-150 字>
- **可复用模式**: <dev-01 / skillopt-01 可引用的方法 30-80 字>
- **数据指标**: <如有：执行时长 / 测试覆盖 / 缺陷率>
- **Session 证据**: `<jsonl 路径>`
- **AID 产物**: `<proposal.md / tasks.md 等>`
---
-->

# ❌ Failures — 失败案例库

> **写入者**：analysis (verdict ∈ {REQUEST_CHANGES, CLOSED-with-issues})
> **检索者**：dev-01 被打回时 / skillopt-01 优化时 / 老板复盘时
> **归档**：90 天后移入 `archive/YYYY-Qn-failures.md`

---

## 索引（最近 10 条）

<!-- analysis 每次 finalize 时追加，下方是新条目 -->

| Issue | Skill | Date | Priority | 一句话教训 |
|-------|-------|------|----------|-----------|
| (暂无) | - | - | - | - |

---

## 详细记录

## Issue #22 - aid-applying - 2026-07-13

- **Verdict**: REQUEST_CHANGES
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=REQUEST_CHANGES
- **现象**: Issue #22 (程序员模式 BIN/OCT/DEC/HEX + 模式切换动画, feat/issue-22-简单需求 分支, commit 8e6555c+a4f8f9e signed-off) apply-report.md L37 把 Task 5.3 UI 自动化标 ⏸ 降级,L71-92 写'本工作目录为非交互式 headless 模式,无法启动模拟器' + '建议 dev-01/rev-01 在真实模拟器/真机上跑',但 capabilities.json#L20-25 显式声明 ui_test.available=true + emulator_status=running + emulators=[127.0.0.1:5555];apply-report 末尾无 ## verdict 段,无 hdc list targets / hdc tconn 原始输出,无 capabilities.json 覆写证据,无 todo.md ⏳ 责任人+绝对日期条目,无用户书面同意回执;8 个 UI AC (AC-U1 启动默认标准 / U2 切换程序员 / U3 220ms 动画 / U4 BIN=1010 OCT=12 DEC=10 HEX=A / U5 点击 HEX 行 / U6 HEX 按 F / U7 BIN 按 2 弹 Toast / U8 重启保留) 全部无截图无 dump。
- **根因**: 归类 A (claude 幻觉乱写降级路径) + 副 B (4-CHECK 缺自动执行门禁)。证据链:capabilities.json#L20-25 ui_test.available=true, emulator_status=running (UI 测试声明可用,模拟器声明在跑) → aid-applying/SKILL.md#L228 铁律 7 Deferred 硬门禁 '任何把 UI 测试 / T21 / UI 自动化任务标记为 Deferred / ⏭️ / 延后 / 跳过的行为,必须先完整通过下方 step3-2-2b-降级 CHECK-1~4 全部 ALL PASS,4 CHECK 未全部 ALL PASS 之前绝对禁止在 apply-report.md 写 Deferred / ⏭️ / 任何延后措辞' (literal 强规则) → aid-applying/SKILL.md#L255-298 step3-2-2b-降级 强制 5 步序列 (暂停 apply-report 写入 / 获取用户书面同意 / todo.md ⏳+责任人+绝对日期 / capabilities.json ui_test.emulator_status 覆写 unavailable / apply-report 引用 hdc 失败原始输出) + L272-298 4-CHECK bash 自检脚本 (literal bash 模板) → apply-report.md#L37 'Task 5.3 UI 自动化 ⏸ 降级' + L71-92 '降级说明' + L80 '建议 dev-01/rev-01 在真实模拟器/真机上跑' (literal 直接写降级文案) → apply-report.md 末尾无 ## verdict 段 (CHECK 失败本应追加 verdict=REQUEST_CHANGES, L304) + capabilities.json#L33-37 ui_test.emulator_status=running 未覆写为 unavailable (CHECK-3 失败特征) + apply-report 无 hdc 探测原始输出 (CHECK-4 失败特征) + todo.md 无 ⏳+责任人+绝对日期 (CHECK-2 失败特征) + 无用户书面同意回执 (CHECK-1 失败特征) → 8 个 UI AC 全部委托给 BaseConverter.test.ets 22 个单测 (literal 降级策略第一项 '已通过单元测试覆盖核心计算逻辑', 违反铁律 7 '不准以 UI 任务已在 Task 1.x 单元测试覆盖为由跳过, 单元测试 ≠ UI 测试' L244)。so why 三层穿透:L1 现象 - apply-report 写 ⏸ 降级且零 UI 证据;L2 流程 - dev-01 直接写降级文案与状态, 未走 step3-2-2b-降级 5 步顺序, 4-CHECK 自检脚本未被 agent 跑过;L3 根因 - aid-applying 虽明示强制 4-CHECK 铁律 (L228, L255-298) + verdict=REQUEST_CHANGES 自动闸门 (L304-306), 但 4-CHECK 设计为 agent 在写完 apply-report.md 后自觉跑的 bash 脚本, 缺 pre-write 拦截钩子 / post-write 自动门禁 (例如写 ⏸ 关键词时强制注入 4 要素模板占位 / CI 校验), claude 跳过自检直接写降级文案 + 末尾未追加 verdict 段 + capabilities.json 未覆写, 形成 声明可用 → 报告降级 自相矛盾 (rev-01 评论阻塞项 #1+#2 全中, Issue #25/28 历史教训再次复现, 参 Issue #25 教训 masquerade-as-passing 处理与 Issue #28 教训 ui-tests/ 目录未建)。
- **教训**: 在 aid-applying/SKILL.md step3-2-2b 末尾 (L298 后) 新增一节 'step3-2-2b-降级 post-write 强制门禁 (imperative)': (1) 写 apply-report.md 之前, agent 必须先 grep 降级关键词 (⏸/降级/Deferred/⏭️/环境受限), 若命中则强制按 L257-271 顺序执行 5 步 (暂停写入 / 跑 hdc list targets + hdc tconn 拿原始输出 / jq 落盘覆写 capabilities.json emulator_status=unavailable / 在 todo.md 插入 ⏳+责任人+绝对日期条目 / 用户书面同意回执写入 apply-report.md), 不准在 5 步未全 PASS 前先写降级文案; (2) 写完 apply-report.md 后, 强制跑 L274-298 的 4-CHECK bash 脚本, 任一 FAIL 强制在文件末尾追加 "## verdict
REQUEST_CHANGES
- step3-2-2b-降级 强制自检未通过" 段, 且本会话绝对禁止任何 git add/commit/push (退出码 1 阻断); (3) 联动 aid-monitor/SKILL.md, 在 review 阶段加 'apply-report 含 ⏸ 降级但 capabilities.json ui_test.emulator_status≠unavailable' 自动告警规则, 扫到就判定 dev-01 跳过 4-CHECK 直接出 REQUEST_CHANGES。
- **建议**: 在 aid-applying/SKILL.md step3-2-2b 末尾 (L298 后) 新增一节 'step3-2-2b-降级 post-write 强制门禁 (imperative)': (1) 写 apply-report.md 之前, agent 必须先 grep 降级关键词 (⏸/降级/Deferred/⏭️/环境受限), 若命中则强制按 L257-271 顺序执行 5 步 (暂停写入 / 跑 hdc list targets + hdc tconn 拿原始输出 / jq 落盘覆写 capabilities.json emulator_status=unavailable / 在 todo.md 插入 ⏳+责任人+绝对日期条目 / 用户书面同意回执写入 apply-report.md), 不准在 5 步未全 PASS 前先写降级文案; (2) 写完 apply-report.md 后, 强制跑 L274-298 的 4-CHECK bash 脚本, 任一 FAIL 强制在文件末尾追加 "## verdict
REQUEST_CHANGES
- step3-2-2b-降级 强制自检未通过" 段, 且本会话绝对禁止任何 git add/commit/push (退出码 1 阻断); (3) 联动 aid-monitor/SKILL.md, 在 review 阶段加 'apply-report 含 ⏸ 降级但 capabilities.json ui_test.emulator_status≠unavailable' 自动告警规则, 扫到就判定 dev-01 跳过 4-CHECK 直接出 REQUEST_CHANGES。
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-22/2026-06-17/001d4485-d6cf-4084-a448-f7c91a95141c.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-22/2026-06-17/0521abd4-150c-4009-aefd-8e35fb82c461.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-22/2026-06-17/2072e81e-7c1f-40e3-aa83-fd665476cc9d.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/22

---
## Issue #28 - aid-applying - 2026-07-08

- **Verdict**: REQUEST_CHANGES
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=REQUEST_CHANGES
- **现象**: dev-01 于 2026-06-17 在 worktree issue-28 执行 aid-applying 阶段,写完 apply-report 后用 `git commit -m "feat(memory-slots)..."` 提交主 commit c7ba0fc,命令未带 `-s`/`--signoff`,commit 末尾亦无 Signed-off-by trailer,仅 Co-Authored-By;同时 apply-report.md L147 把 T21 (UI 自动化) 标为 ⏭️ Deferred,仅引用 step3-0-4.1 允许场景作为依据,未走 step3-2-2b-降级 的 CHECK-1~CHECK-4 硬门禁,导致 specs/.../ui-tests/ 目录空、0 截图 0 dump。rev-01 判定两项 FAIL,出 REQUEST_CHANGES。
- **根因**: 归类 B (漏掉步骤)。aid-applying/SKILL.md 在 2026-06-17 当下缺失两条 imperative 硬门禁:(1) `git commit` 必须 `-s/--signoff` 的强约束,(2) 任何 UI 测试/T21 标 ⏭️ Deferred 必须先完整通过 step3-2-2b-降级 CHECK-1~CHECK-4 self-check 的硬阻断。证据是当前 SKILL.md L228 与 L498-501 的 fix 都明确标注『依据 Issue #28 教训』新增——说明这两条规则是事后补入的,并非 c7ba0fc 时刻已存在。session jsonl 998a8871 L263 的实际命令是 `git commit -m "feat(memory-slots)..."`(裸 -m,无 -s);L238 写 apply-report 时 L147 直接引用 step3-0-4.1 允许场景作为 T21 Deferred 依据,跳过 CHECK-1~CHECK-4。dev-01 在缺乏硬约束的 skill 文本下走漏,不是幻觉乱写(A),也不是规则歧义(C),更不是外部因素(D)。
- **教训**: 把 SKILL.md 中两条规则升级为硬门禁:(1) commit 步骤必须用 `git commit -s -m ...` 且 push 前自检 HEAD 含 Signed-off-by,否则 exit 1;(2) UI 测试/T21 标 Deferred 前必须输出 CHECK-1~CHECK-4 4 要素 self-check 块并全部满足,任一不满足则强制跑 UI 自动化。两者均加 🚧 imperative 标记并明确引用 Issue #28 教训。
- **建议**: 把 SKILL.md 中两条规则升级为硬门禁:(1) commit 步骤必须用 `git commit -s -m ...` 且 push 前自检 HEAD 含 Signed-off-by,否则 exit 1;(2) UI 测试/T21 标 Deferred 前必须输出 CHECK-1~CHECK-4 4 要素 self-check 块并全部满足,任一不满足则强制跑 UI 自动化。两者均加 🚧 imperative 标记并明确引用 Issue #28 教训。
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-28/2026-06-17/998a8871-b39d-40d4-a215-13c93cf66e1a.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-28/2026-06-17/75f73d17-3d54-4b00-b8da-5e9604657515.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-28/2026-06-17/fcf60fad-2864-4549-a4d4-8ec05952d408.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/28

---
## Issue #28 - aid-applying - 2026-07-07

- **Verdict**: REQUEST_CHANGES
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=REQUEST_CHANGES
- **现象**: Issue #28 走完整 AID, rev-01 双阻塞: c7ba0fc 主 commit 缺 Signed-off-by; apply-report T21 标 Deferred 但 ui-tests/ 目录未创建, 未走 step3-2-2b 降级 4 要素。
- **根因**: 归类 B+C, 靶点 aid-applying。SKILL.md L557 `git commit -m` 无 -s; dev-01 jsonl 998a8871 L263 字面照抄产 c7ba0fc 无 trailer; fcf60fad L65 amend --signoff 未生效 (b86f7c7 仍无), 证 -s 未硬性。apply-report Deferred 仅列 resources/ 缺失, 未触发同 SKILL step3-2-2b 4 CHECK (用户同意/todo ⏳/capabilities.json 覆写/hdc 原始), 全 FAIL; 两段未串属 C 歧义。
- **教训**: L557 改 `git commit -s -m` + 粗体 '必 -s'; step3-2-2b 顶部插 '4 CHECK 通过前不准写 Deferred'; 串联 step3-0-4.1。
- **建议**: L557 改 `git commit -s -m` + 粗体 '必 -s'; step3-2-2b 顶部插 '4 CHECK 通过前不准写 Deferred'; 串联 step3-0-4.1。
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-28/2026-06-17/998a8871-b39d-40d4-a215-13c93cf66e1a.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-28/2026-06-17/fcf60fad-2864-4549-a4d4-8ec05952d408.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-28/2026-06-17/7c285183-76b0-4335-a3dc-ed60fbb9e227.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/28

---
## Issue #25 - aid-applying - 2026-07-07

- **Verdict**: REQUEST_CHANGES
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=REQUEST_CHANGES
- **现象**: Issue #25 单位换算扩展提交后被 rev-01 判 REQUEST_CHANGES,eec5ecc 主 commit 末尾仅含 Co-Authored-By: Claude Opus 4.8,缺 Signed-off-by(对照同分支 a4f8f9e 有 Signed-off-by: littleleafccccc);apply-report.md §3.1-3.3 披露模拟器未连接并降级为 Node 端口测试(71/71 PASS),但 §降级四要素完全缺失(无用户书面同意回执、无 todo.md ⏳ 标记、无 capabilities.json ui_test.emulator_status 覆写为 unavailable、仅引用 hdc list targets 片段);todo.md L38 IMPLEMENTING 阶段 '调用 aid-implementing → tasks.md' 复选框 [ ] 未勾;未产出 ui-tests/ 目录、无 uiautomator dump、无截图。
- **根因**: 归 B 类(漏掉步骤)。aid-applying/SKILL.md §Git Commit & Push 章节(L549-559)给出的命令模板是 'git commit -m "feat({name}): apply changes from aid-workflow"',未含 --signoff 强制标志,dev-01 在 eec5ecc 直接套用导致 signoff 缺失;同 skill §step3-2-2b HarmonyOS UI 测试强制段(L226-242)要求项目类型=HarmonyOS 必须调 skill('harmonyos-ui-test'),但 apply-report.md §3 显示实际未调用而走 Node 端口测试;§降级四要素(L251-300)要求五步强制顺序(暂停写报告→用户书面同意→todo.md ⏳+责任人+绝对日期→capabilities.json 覆写→四项证据嵌入报告),apply-report.md §6 仅完成第 5 步中 'hdc 探测引用' 一项,其余 4 项全缺。Session jsonl 证据:11ae218a-8612-4a45-b891-74e3d31cb639 (2026-06-17T14:55) 是 dev-01 re-dispatch session,L21-22 assistant 看到 'worktree 里已有 commit 和 AID 产物' 直接走 early-return 分支 'Issue #25 already handled at eec5ecc',未对前序 session 跑出的 commit signoff/lint/降级路径做任何合规性审计,dispatcher 自身的 aid-applying 内部检查也未触发。
- **教训**: 在 aid-applying/SKILL.md L555 把 'git commit -m "feat({name}): apply changes from aid-workflow"' 改为 'git commit --signoff -m "feat({name}): apply changes from aid-workflow"',并在 L559 之前加 imperative 'push 前必须 grep -E "Signed-off-by:" .git/COMMIT_EDITMSG 非空,否则 exit 1';在 L251 step3-2-2b-降级 强制检查块顶部加 'bash 自检 4 要素不通过则禁止在 apply-report.md 写降级措辞' 的硬门禁。
- **建议**: 在 aid-applying/SKILL.md L555 把 'git commit -m "feat({name}): apply changes from aid-workflow"' 改为 'git commit --signoff -m "feat({name}): apply changes from aid-workflow"',并在 L559 之前加 imperative 'push 前必须 grep -E "Signed-off-by:" .git/COMMIT_EDITMSG 非空,否则 exit 1';在 L251 step3-2-2b-降级 强制检查块顶部加 'bash 自检 4 要素不通过则禁止在 apply-report.md 写降级措辞' 的硬门禁。
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-25/2026-06-17/11ae218a-8612-4a45-b891-74e3d31cb639.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/25

---
## Issue #29 - aid-applying - 2026-07-07

- **Verdict**: REQUEST_CHANGES
- **Priority**: 🔴 **HIGH**
- **Trigger**: verdict=REQUEST_CHANGES
- **现象**: dev-01 在 worktree D:/huawei/Demo/worktrees/issue-29 调用 aid-applying 跑完 28/28 单元测试与 hvigorw 编译,但 step3-2-2b-降级 强制检查块四要素全部缺失:apply-report.md:58-83 仅'诚实标注'hdc list targets=Empty / hdc tconn 失败 / AVD 不可用,但未调 harmonyos-ui-test skill、未获取用户书面同意、todo.md 无 ⏳+责任人+绝对日期、.claude/capabilities.json 的 ui_test.emulator_status 字段仍为 stale 的 'running'。这恰是 SKILL.md:312-317 显式列为'反模式示例 (禁止复刻)'的错例形态。
- **根因**: 归类为 B(漏掉步骤)。aid-applying/SKILL.md:251-318 的 'step3-2-2b-降级:强制检查块 (铁律 7 兜底)' 明确写出当 hdc list targets=Empty / capabilities.json stale 时必须按 1-5 顺序执行:暂停写入 → 用户书面同意 → todo.md ⏳+责任人+绝对日期 → capabilities.json ui_test.emulator_status 覆写为 unavailable → apply-report 引四项证据。jsonl#14 (1e7215e9 assistant thinking) 显示 dev-01 检测到 worktree 已有 commit+产物后直接退出未跑 aid-applying;真正跑 aid-applying 的早期 jsonl (apply-report.md 是 06-18 12:18 写入) 在降级块已存在版本上执行,但 step3-2-2b-降级 触发条件全部满足时 agent 跳过了五步强制块、仅写出'环境受限'自由文体段落,违反铁律 7 兜底。apply-report.md 文本'请 dev-01 / 人类协助'与 SKILL.md 反模式示例 '请 dev-01 / 人类协助处理' 字符级吻合,确认为降级块被绕过而非 skill 缺失。
- **教训**: 在 step3-2-2b-降级 第 5 步末尾追加 imperative self-check 块:写完 apply-report.md 后必须跑 SKILL.md:278-300 的四条 grep 自检命令 (用户书面同意/todo ⏳ 三要素/capabilities.json unavailable/hdc 原始输出),任一 FAIL 禁止 commit/push 并自动 verdict=REQUEST_CHANGES;同时删除重复的第二份降级块 (lines 320-386 是 251-318 的完全重复,违反单一可信源)。
- **建议**: 在 step3-2-2b-降级 第 5 步末尾追加 imperative self-check 块:写完 apply-report.md 后必须跑 SKILL.md:278-300 的四条 grep 自检命令 (用户书面同意/todo ⏳ 三要素/capabilities.json unavailable/hdc 原始输出),任一 FAIL 禁止 commit/push 并自动 verdict=REQUEST_CHANGES;同时删除重复的第二份降级块 (lines 320-386 是 251-318 的完全重复,违反单一可信源)。
- **Session 证据**: `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-29/2026-06-17/87c9f776-0d4d-4874-bdf1-c5e790e2e767.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-29/2026-06-17/bc8f66cc-b85b-4773-918e-c224cac3c480.jsonl`, `D:/huawei/my_sessions/sessions/claude-code/dev-01/_raw/D--huawei-Demo-worktrees-issue-29/2026-06-18/13596774-3942-4151-8e48-61c5c7809878.jsonl`
- **AID 产物**: (待补)
- **URL**: https://github.com/calculatorHuawei/agent_workflow/issues/29

---
<!-- 按时间倒序，最新在上 -->

<!--
### 模板（analysis 复制此模板追加）
## Issue #<N> - <skill_name> - <YYYY-MM-DD>

- **Verdict**: REQUEST_CHANGES
- **Priority**: 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW
- **Trigger**: <什么场景触发的分析>
- **现象**: <客观描述 50-150 字>
- **根因**: <A/B/C/D 归类 100-300 字>
- **教训**: <可被 dev-01 引用的经验 30-80 字>
- **建议**: <动词开头的具体动作 30-100 字>
- **Session 证据**: `<jsonl 路径>`
- **AID 产物**: `<proposal.md / tasks.md 等>`
---
-->

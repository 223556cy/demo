# aid-code-root-cause / LLM 分析 Prompt 模板

LLM 在做代码层根因分析时,使用此模板引导思考。

## 输入(v1.3 分层)

| 层级 | 内容 | 强制? |
|---|---|---|
| L1 (must) | JSONL events.json(events_id + code + thinking + diff) | ✅ 必有 |
| L2 (highly recommended) | worktree 当前代码(`worktree_gap.json` 列未触碰的必须 Read) | ✅ 必有 |
| L3 (when UI / Build) | hdc dump + screenshot | ✅ UI / Build routing 类 finding 必跑 |
| L4 (when needed) | apply-report / delta-spec.md / issue 评论 | 可选,但 critical 必读 |

**重要**:L1 only 的视野恒等于"agent 当天动过的那块代码",**≠** issue 完整 bug 集。
锚点案例:程序员模式 Bug 1(`onClick 写死 DEC`)和 Bug 3(`build() 缺位运算键`)在 worktree 内完整存在,但 agent 当天没改 `onClick` / `build()` 段,JSONL only 看不到。

## 分析 Prompt

```markdown
你是 aid-code-root-cause skill。

# 任务
对给定 JSONL + worktree 代码 + hdc 验证中的 Write/Edit 代码,做代码层根因分析。

# 思考框架(v1.3:6 → 7 个角度)
依次问 7 个角度(必问,防漏):
1. State consistency — 同一概念在多处定义/存储吗?改 A B 知道吗?(含 ArkUI 响应式追踪 / 跨文件 import 污染 / **回调契约错位**)
2. Timing — 操作在什么时候跑,顺序对吗?
3. Defaults — 默认值从哪里来,跟 spec 一致吗?有没有符号/方向反转 / **回调参数硬编码**?
4. Verification — 测试真的在测对的东西吗?
5. Errors — 错误被吞了吗?用户能看到真原因吗?
6. Resources — 创建的资源清理了吗?
7. **Build routing**(v1.3 新增) — build() 中 if/else 分支是否完整?被选中的子组件包含 spec 所有功能项吗?多 row 共享 hot-zone 是否区分 row?

每个角度都要问,**不要跳过**(防漏)。7 角度不是限制 — 看到新类别自由推理(防僵化)。
鸿蒙/ArkTS 实例提示见 references/code-issues-angles.md。

# 输入
- JSONL: <jsonl_path>
- worktree 根: <worktree_root>(若 L2 提供)
- 代码已抽到 events (Write/Edit 的 file + code + line)
- 任务描述: <user_problem_statement>
- hdc dump/screenshot 路径(若 L3 提供)

# 输出格式
写到 <output_dir>/report.md:

## 严重度汇总
| 等级 | 数量 | 说明 |
|---|---|---|
| critical | N | 必然导致 bug |
| major | N | 大概率导致 bug |
| minor | N | 代码异味 |

## JSONL gap 自检(必填)
| 文件路径 | 是否在 events.json | 是否 Read | 状态 |
|---|---|---|---|
| CalculatorPage.ets | yes | yes/no | touched |
| ProgrammerPanel.ets | yes | yes/no | touched |
| LongPressMenu.ets | no(untouched) | yes/no | ⚠️ 应 Read |
| ... | | | |

## Findings(按严重度排序)
### [severity] angle_name
- **位置**: file:line
- **角度**: State consistency / Timing / / Build routing / ...
- **类型**: 一句话描述
- **代码 diff**: Edit 事件必填(unified diff 3-5 行);Write 事件写关键片段(events.json 的 `code_diff` 字段已生成)
- **证据强度**: strong(有 hdc dump 复现)/ medium(静态分析)/ weak(仅 thinking 推测)
- **触发状态**: live(hdc 实测复现) / static-only(代码里有 bug 但未 hdc 验证) / unverified
- **解释**: 为什么这是 bug
- **触发判断**: 在本次 session 实际触发了吗?(避免误报)
- **修复建议**: 1-2 句

## hdc 验证可行性
- 本次有 hdc 实测吗?yes/no
- 每条 finding 的 [UI] / [Build] / [Logic] 标签,标注哪些走了 hdc 验证、哪些只靠静态分析
- [UI] / [Build] 类 finding 没 hdc dump 佐证 → 标 '未验证' + 严重度降一级

## 自我怀疑段(v1.3 必填)
- 本次 skill 仅输入 L1 时,漏掉的最大风险是什么?(对照 worktree_gap.json)
- 我对哪些 finding 自信度 < 50%?为什么?
- agent 的 exploration trail(同一文件被改 ≥ 5 次反复横跳)中,哪些可能不是 live bug?
- 是否需要补充验证手段?

## 未覆盖的潜在新 bug
你看到但 7 角度没列出的 bug,列在这里。

**怎么想**:问自己以下引导问题,任何"是"的回答都要展开看:
- 这 7 个角度有没有覆盖不到的**语义反转 / 边界条件 / 跨进程 / 第三方依赖**类问题?
- 跨多个 angle 的复合 bug(如时序+错误处理)是不是被拆散了?
- 这次 session 的 **thinking 块**有没有透露 agent 误以为对、实际错的推断?
- agent 的 exploration trail 反映的"他当时碰到的错"是不是其实不是 live bug?
- 有没有**新类别 bug 模式**应该被加进 `references/code-issues-angles.md` 的实例提示?

# 约束
- 不输出 regex pattern
- 不只列已知 bug 类型 — 自由推理
- 区分"代码 bug 存在" vs "本次 session 实际触发" vs "hdc 实测复现"
- 不修复部署/工具链问题(那是其他 skill 的事)
```

## 真实调用示例

### A. 264c5a16 — 6 角度时代(老锚点)

**输入**:
- JSONL: `264c5a16-f4f1-48ff-9f40-d215e1cc2567.jsonl`
- 用户问题:"最后 UI 测试时 sin(x) 画成直线"
- L1 only(L2/L3 当时未强制)

**LLM 工作流程**:
1. 抽 42 个 Write/Edit 事件,拿到完整代码
2. 读 `references/code-issues-angles.md` 加载 6 个角度
3. 对每个事件问 6 个角度
4. L260 GraphPage.ets Write 命中:
   - 角度 1: TextInput 默认值 vs vm 默认值 状态脱节
   - 角度 5: onChange 改 vm 没 compute,UI 静默 stale
5. L247 GraphViewModel.ets Write 命中:
   - 角度 3: VM isDegree 默认 vs prefs 默认
6. 测试文件命中:
   - 角度 4: 测试断言太弱,只查 y ~ 0 不查 yMax
7. UI 测试文件命中:
   - 角度 4: UI 测试只查 screenshot 大小

**输出报告**:在 `<output_dir>/report.md` 出 4-6 个 finding,按严重度排序。

### B. 程序员模式 Bug 1/Bug 3 — 7 角度 + L1+L2+L3 新锚点(2026-08 v1.3)

**输入**:
- JSONL: dev-01 session 3c890e61...
- worktree: `D:\huawei\Demo\worktrees\issue-22`
- L3:hdc dump 已抓(`dump/rca_p2_prog.xml` + `screenshot/rca_p2_after_switch.png`)
- 用户问题:"程序员模式用着用着感觉哪里不对"

**LLM 工作流程**:
1. L1:抽 32 个 Write/Edit 事件,events.json 拿到 agent 当天动过的代码(主要是 ProgrammerPanel.ets / CalculatorPage.ets 的 @Builder 部分)
2. **L2 必跑**:worktree_gap.json 列出 62 个未触碰文件 → Read `ProgrammerPanel.ets`(125 行)+ `CalculatorPage.ets` 关键段
3. **L2 发现真 bug**:ProgrammerPanel.ets:106-110 `onClick(() => onBaseTap(NumberBase.DEC))` 写死 — **不在 events.json 内,JSONL only 看不到**
4. **L3 必跑**:hdc 实测复现"输入 1 → HEX 行 → F"流程,dump 确认 expression 不变("1" not "1F")+ screenshot 显示 Toast
5. 7 角度分析:
   - 角度 1(回调契约错位):Bug 1 — 共享 onClick 不区分 row
   - 角度 3(回调参数硬编码):Bug 1 同源 — `NumberBase.DEC` 写死
   - **角度 7(Build routing)(v1.3 新增)**:Bug 3 — build() 走 `ProgrammerKeyboard()` 但该键盘不含 AND/OR/XOR/NOT/<< 键
6. **L4**:读 apply-report 第 4.4 行"位运算 UI-only ✅ DONE" — 标 PASS 实则完全没接入

**输出报告**(v2.0):
- 3 critical findings(Bug 1 / Bug 3 / dev-01 JSONL 修复被还原)
- 1 major(UI 弱断言)
- 1 minor(spec AC 函数级)
- 每条 finding 标 `[evidence: strong]` + `[trigger: live]` 因为有 hdc 复现

## 注意事项

1. **不要列已知 pattern 后就结束** — 7 角度是引导,不是限制
2. **必须读 thinking 块** — agent 的 thinking 透露意图,有助于判断
   - 抽取方法:`extract_code.py` 在 events.json 的 `thinking` 字段一并输出
   - 关键:thinking 块在 Claude Code JSONL 里**几乎从不与 Write/Edit 同条 message**,所以 `thinking_source` 通常是 `prior-N`(前 N 条 message 的思考);看到 `prior-N` 要意识到这是 agent 较早的意图,可能与当前工具调用有偏差
   - 关注 thinking 里 "看起来对 / 应该没问题" 的断言 — 那是高频漏判区
3. **agent 的 exploration trail 不等于 live bug**(v1.3 新增)— 同一文件被改 ≥ 5 次反复横跳的 pattern,**必须**用 git diff 验证当前代码是否含 agent 的 trail
4. **区分触发 vs 存在** — 代码有 bug 不等于本次 session 触发了;触发了不等于 hdc 实测复现了
5. **跨文件关联** — 同一个 bug 可能跨多个文件(如 radian mode 涉及 3 个文件)
6. **不要自动修复** — 本 skill 只出报告,fix 由其他 skill/人做
7. **上下文窗口限制** — 如果 Write/Edit 事件 > 100 个,优先按"代码改动大小 / 是否触发测试 / 是否影响用户行为"排序,先看高优先级事件
8. **强制 L2/L3**(v1.3 新增)— UI / Build routing 类 finding 没 hdc 验证,不报;其他类 finding 没 worktree 代码 Read,不报 critical
9. **严重度 4 维度**(v1.3 新增)— severity(critical/major/minor)+ evidence(strong/medium/weak)+ trigger(live/static-only/unverified)+ scope(global/mode-specific/edge);不要只填 severity

---
name: aid-code-root-cause
description: |
  代码层根因定位 skill。让 LLM 从 **7 个抽象角度**分析 session JSONL + worktree 代码 + hdc 实机验证,
  判断是否有 bug 并定位到 file:line。

  **重要**:bug 现象可以是任何层(UI 显示错、性能差、状态丢、计算错);**验证手段不限**
  (hdc / screenshot / dump 都能用)。根因分析永远在代码层。

  **输入分层**:L1 JSONL events.json (must) + L2 worktree 必读代码 (highly recommended) +
  L3 hdc 实机(UI/Build 类必跑)+ L4 apply-report/spec 评论(可选)。详见正文。

  触发词:"代码层根因" / "扫代码 bug" / "为什么这个 bug 流到用户手里" /
  "JSONL 找代码 bug" / "7 角度分析 session 代码" / "session 代码复盘(代码层)" /
  "UI 现象找代码根因" / "按钮位置/标签大小/坐标轴/状态不刷新等 UI 问题反推代码" /
  "hdc 验证根因" / "dump + 代码反推 bug"。

  与 aid-applying diff_engine(流程层)和 aid-analysis-locate-bug(溯源层)互补:
  - aid-applying diff:查 SKILL.md / spec 是否被遵守(流程层)
  - aid-code-root-cause:**本 skill**,查代码本身有没有 bug(代码层)
  - aid-analysis-locate-bug:综合日志 + spec 反推 bug 位置(溯源层)
  - harmonyos-ui-test:维护并跑 UI 测试套件;本 skill 借其能力验证,但不依赖它做根因分析
compatible: ["calculatorHuawei-main"]
---

# AID-Code-Root-Cause Skill

## 概述

**核心思路**:LLM 用 **7 个抽象角度**思考(JSONL + worktree 代码 + hdc 实机验证),而不是 regex 自动化扫描。

- ❌ 之前思路(已废弃):35 个 regex pattern + 自动匹配 — 过拟合,漏新 bug,误报多
- ✅ 现在思路:**7 个抽象角度**(State/Timing/Defaults/Verification/Errors/Resources/**Build routing**)+ LLM 自由推理

**7 个角度**见 `references/code-issues-angles.md`。每个角度:
- 不规定具体 bug 模式(regex 过拟合)
- 给 LLM 思考方向 + 2-3 个子问题
- 附鸿蒙/ArkTS 实例提示(可选参考)

---

## 输入分层(v1.3 强制)

**核心原则**:**JSONL only 视野恒等于"agent 当天动过的那块代码",**≠** issue 完整 bug 集**。

锚点案例(程序员模式 v1 报告 vs v2 报告对比):
- Bug 1(`ProgrammerPanel.ets:106` onClick 写死 DEC)— 在 worktree 内完整存在,但 agent 当天**没改 onClick 语义**,JSONL only 看不到
- Bug 3(`CalculatorPage.ets:597` build() 路由错位)— 在 worktree 内完整存在,但 dev-01 当天**没动 build() 段**,JSONL only 看不到

**强制 4 层输入**:

| 层级 | 内容 | 强制? | 漏了后果 |
|---|---|---|---|
| L1 (must) | JSONL events.json(events_id + code + thinking + diff) | ✅ 必有 | 没输入 |
| L2 (highly recommended) | worktree 当前代码(`worktree_gap.json` 列未触碰的必 Read) | ✅ 必有 | 漏 agent 没碰过的代码区里的 bug(Bug 1/Bug 3 案例) |
| L3 (when UI / Build) | hdc dump + screenshot | ✅ UI / Build routing 类 finding 必跑 | 静态分析无法验证 UI 显示/行为 |
| L4 (when needed) | apply-report / delta-spec.md / issue 评论 | 可选;critical finding 必读 | 漏 spec 偏离 / 自评 PASS 谎报 |

**`extract_code.py --include-worktree <dir>`**:
- 扫 worktree 根目录的源文件,与 JSONL 触过的对比
- 输出 `worktree_gap.json`(列未触碰的文件 + 大小)
- 跳过的目录:`.git .hvigor node_modules build dist .idea .vscode .claude oh_modules build-profile outputs .test __pycache__ .gradle coverage`

---

## 使用方法

### 工作流(LLM-driven,4 步,Step 2.5 条件必跑)

```
JSONL events.json + worktree 代码 + (hdc 验证)
  ↓
Step 1: 抽代码(脚本自动)
  scripts/extract_code.py --include-worktree <dir> → events.json + worktree_gap.json + summary.md
  ↓
Step 2: LLM 思考(7 角度分析 + L2 工作树代码 Read)
  LLM 读 events.json + worktree_gap.json + references/code-issues-angles.md
  对每个事件 + 每个未触碰的关键文件,问 7 角度,产出"假设清单"
  ↓
Step 2.5: 必跑验证(hdc 主动验证)— 见下方"Step 2.5 必跑条件表"
  LLM 读 references/hdc-verify-cheatsheet.md
  → UI / Build 类 finding 必须 hdc 验证
  → 把验证结果(strong / medium / weak 证据)附到对应 finding
  ↓
Step 3: LLM 出报告(模板化)
  templates/llm-prompt-template.md 引导
  → report.md(按严重度排序 + JSONL gap 自检 + hdc 验证可行性 + 自我怀疑段)
```

**Step 2.5 必跑条件表**(v1.3 强制):

| finding 类型 | hdc 必跑? | 漏了后果 |
|---|---|---|
| UI 状态不一致 / 显示错位 | ✅ 必 | 静态分析无法验证,fallback "未验证" 标弱证据 |
| UI 路由 / 模式分支 / build() 条件分支 | ✅ 必 | dump 列所有可见 clickable,对比 spec 缺则报 routing bug |
| 回调契约错位 / 共享 onClick 不区分 row | ✅ 必 | hdc 重放点不同位置确认实际行为 |
| 纯算法(三角函数、转换、解析) | ❌ 可选 | unit test 即可 |
| 纯模型(class 字段语义) | ❌ 可选 | 读源码即可 |
| 持久化(prefs / settings) | ⚠️ 强烈推荐 | 重启 App 验证 |
| 第三方 SDK 集成 | ⚠️ 看场景 | — |

**Step 2.5 设计原则**:
- **条件必跑**(v1.3 起):UI / Build routing / 回调契约类 finding 没 hdc dump 佐证,不报 critical(降级 major + 标 'unverified')
- **单次验证够用** — dump / 截图 / 重放,3-5 分钟内能跑完即可
- **不替代 harmonyos-ui-test** — 本 cheatsheet 只够单次确认,不是测例维护
  - 详见 [references/hdc-verify-cheatsheet.md](references/hdc-verify-cheatsheet.md) §6 局限

### 命令行(只跑 Step 1 抽代码)

```bash
python ...\scripts\extract_code.py <input.jsonl> [--include-worktree <dir>] [-o output_dir]

# jsonl 路径必传,output_dir 可省(默认基于 jsonl 所在目录派生)
# --include-worktree 强烈推荐:产出 worktree_gap.json
```

### 作为 skill 调用(LLM 流程)

skill 触发后:
1. LLM 读本 SKILL.md(知道流程 + 输入分层)
2. LLM 跑 `extract_code.py --include-worktree`(Step 1)
3. LLM 读 `references/code-issues-angles.md`(Step 2 输入)
4. LLM 按 7 角度分析(Step 2)— 产出假设清单
5. **条件必跑**:LLM 读 `references/hdc-verify-cheatsheet.md` 验证 UI / Build / 回调类 finding(Step 2.5)
6. LLM 按 `templates/llm-prompt-template.md` 引导出报告(Step 3)
7. LLM 写 report.md,必带 JSONL gap 自检 + hdc 验证可行性 + 自我怀疑段

### 与其他 skill 串联(可选 pipeline)

> **关系澄清**:三个 skill 是**互补关系**(查不同层),不强制先后顺序。典型 analysis pipeline
> 中 aid-code-root-cause 可被嵌入 aid-analysis-locate-bug **上游**(给 locate-bug 提供"代码层候选位置")。

| 步骤 | Skill | 用途 |
|---|---|---|
| 1 | aid-applying | 跑完得 annotated.jsonl(可选输入) |
| 2 | **aid-code-root-cause** | 本 skill:从 JSONL + worktree + hdc → LLM 7 角度分析 |
| 3 | aid-analysis-locate-bug | 综合日志 + spec 反推(可消费本 skill 输出) |
| 4 | aid-analysis-root-cause | 11 步推理 |
| 5 | aid-analysis-output | 序列化成 issue_ticket JSON |

---

## 前置条件

- 输入:JSONL 文件路径(annotated.jsonl 或 原始 .jsonl)+ **worktree 根目录**(强烈推荐)
- 必须含 Write/Edit tool_use(input.content / new_string 含完整代码)
- **LLM 必须自己 Read worktree 源码(v1.3 反转原保守原则)**:
  - 默认 events.json 主导,但 worktree_gap.json 列的未触碰文件 **必 Read**
  - 引用 file:line 时按 full_path 定位
  - 这是 v1.3 重大变更 — 早期"LLM 不需要 Read worktree"是导致程序员模式 v1 报告 60% 误诊的元凶
- **输出目录**默认基于 JSONL 所在目录派生(见下方"输出位置")

---

## 全局约束

### 输出位置

- 默认:`<jsonl_dir>/.claude/analysis-reports/code-root-cause/<session_id>/`
  - 其中 `<jsonl_dir>` 是输入 JSONL 的所在目录(通常是 worktree 内的 `.claude/`)
  - `<session_id>` 来自 JSONL 文件名(`<jsonl>.stem`,去掉 `.annotated` 后缀)
- 产物:`events.json`(LLM 输入)+ `summary.md`(脚本产物)+ `report.md`(LLM 产出)
- 可用 `-o <dir>` 覆盖

### 必区分

- **代码 bug 存在** vs **本次 session 实际触发** — 区分清楚避免误报

### 范围与划走原则

**做(本职)**:**用户报告的 bug 现象,反过来找代码层根因**。
**bug 现象可以是任何层**(UI、性能、计算结果、行为不符、状态丢失、显示错位)——
**根因分析永远在代码层**(ArkTS / TS / Python / JSON5 等写下的代码)。

**验证手段不限制** — 静态分析不确定时,**可以主动调用 UI 自动化测试**(hdc / screenshot / accessibility tree / UI test runner)验证根因假设。验证是为了确认根因,不是"做某类事"。

典型 UI 症状 → 代码根因的反向追溯路径(本 skill 应能命中):

| 用户报告的现象(症状层) | 可能的代码层根因(本 skill 找) | 验证手段(可用) |
|---|---|---|
| 按钮位置和结果区重合 | 布局参数(Grid/Stack alignContent、width/height hardcoded)、padding/margin 算错 | hdc screenshot + aapt dump |
| sin(x) 显示成直线 | 弧度/角度模式默认值错(onChange 没 compute) | screenshot 像素采样 |
| X 轴标签太小(10px) | fontSize 硬编码、vp/fp 单位错、缩放函数未生效 | hdc uiautomator dump |
| 坐标轴不显示 | 条件渲染默认 false、画布 size=0、stroke 颜色与背景同色 | screenshot 颜色采样 |
| 搜索输入了不生效 | ArkUI 不追踪 getter 内部 @State 依赖 | hdc uiautomator dump 前后对比 |
| 模式切换后 UI 不刷新 | @State 浅拷贝 / @Link vs @Prop 选错 | 操作后 dump 验证 |
| 列表项不更新 | ForEach keyGenerator 错、id 复用导致 diff 失败 | uiautomator dump 比对 |

**结论:症状在 UI 层 ≠ 划走给 harmonyos-ui-test**;**验证用 UI 测试 ≠ 划走给 harmonyos-ui-test**。
harmonyos-ui-test 的本职是"维护并跑 UI 测试套件"(测例、回归、覆盖),本 skill 是分析过程中**借用测试能力验证假设**,两者非互斥。

**不做(明确划走)**:**只划"做某类事",不划"症状层/验证手段"**。

- ❌ 部署/工具链层 bug(权限、build-profile、hdc 配置错)— aid-init 的事
- ❌ SKILL.md / spec 合规 diff — aid-applying diff 的事
- ❌ 算法逻辑 bug(三角函数公式错、浮点精度)— unit test 触发
- ❌ 性能/数值精度 bug — 没数据
- ❌ **UI 设计改进建议 / 视觉美学评判**(按钮该不该挪、配色好不好看)— 设计层,不是代码 bug
- ❌ 测试覆盖矩阵分析 / AC 粒度评估 — aid-reviewing + design-review 的事

> 这条原则不只适用于本 skill:任何 skill 都只划"做某类事"(设计改进、写 spec diff、写 AC、做部署),症状层与验证手段不限。

---

## 7 个角度(LLM 思考框架)

详见 `references/code-issues-angles.md`。摘要:

| 角度 | 核心问题 |
|---|---|
| State consistency | 同一概念多处定义,改 A B 知不知道?(含 ArkUI 响应式追踪 / 跨文件 import 污染 / **回调契约错位 v1.3**) |
| Timing | 异步顺序对吗?lifecycle 时机对吗? |
| Defaults | 默认值在多个文件/与 spec 一致吗?(含边界/方向/比较反转 — `!` / 三元写反 / 比较运算符错位 / **回调参数硬编码 v1.3**) |
| Verification | 测试断言验证的是真行为吗? |
| Errors | 错误被吞了吗?用户能看到真原因吗?(主动谎报 / 自评 100% PASS 划走) |
| Resources | Canvas/Listener/Timer 创建后清理了吗? |
| **Build routing**(v1.3 新增) | build() 路由分支完整性 + 多 row 共享 hot-zone 是否区分 row? |

每个角度附鸿蒙/ArkTS 实例提示(常见 bug 形态),不是必须命中。

---

## ⚠️ 警告:agent exploration trail ≠ live bug(v1.3 新增)

**问题模式**:agent 在 JSONL 中反复试错同一逻辑区块(同一文件被改 ≥ 5 次,方向反复横跳)。

**示例**:程序员模式 dev-01 在 JSONL L429-L616 反复试 `@Builder BaseRow(...)`、`@State repCache`、`@Watch`、`aboutToAppear`、`method cache` —— 7 种不同改法。

**陷阱**:**LLM 看到这条 trail 容易误以为是"代码 bug 多"**。

**事实**:这条 trail 反映的是 agent 当天碰到的错,**未必是 live bug**。锚点案例验证:
- 当前 worktree 代码 `ProgrammerPanel.ets` **仍是 `@Builder BaseRow` 写法**(agent 最终的 inline Row 修复被还原)
- hdc 实测 "1 0 输入" → BIN=1010 / OCT=12 / DEC=10 / HEX=A **显示正确**
- 说明 `@Builder BaseRow` 在当前代码里**没有缓存 bug**

**规则**:
1. 把 trail 反推成"代码 bug"前,**必须** `git diff worktree HEAD vs JSONL 最后修改状态`
2. 如果 worktree **不含** agent 的 trail → trail 是已废探索,**bug 不存在 / 已被兜底**(build() re-render 等)
3. 如果 worktree **含** trail → 可能是 stale fix / 部分 fix / 真 bug,需进一步 hdc 验证
4. report.md 的"自我怀疑段"必填:**我对哪些 finding 自信度 < 50%?** 哪些可能是 agent trail 误判?

---

## 严重度约定

每条 finding 填 **4 维**:

| 维度 | 取值 | 含义 |
|---|---|---|
| severity | critical / major / minor | 必然 / 大概率 / 代码异味 |
| evidence | strong / medium / weak | hdc 实测 / 静态分析 / 仅 thinking 推测 |
| trigger | live / static-only / unverified | hdc 复现 / 代码里有但未验证 / 完全没验证 |
| scope | global / mode-specific / edge | 全局 / 模式分支 / 边界条件 |

**降级规则**:
- UI / Build routing / 回调契约类 finding,evidence 是 weak 或 trigger 是 unverified → severity 降一级
- 例如:critical + evidence:weak + trigger:unverified → 实际标 **major + 标"未验证"**

---

## 工作流详解

> 4 步总览 + Step 2.5 必跑条件表见上文"工作流(LLM-driven, 4 步)"段;命令行参数见"命令行"段。

### Step 2:LLM 思考 — 假设清单输出格式

每个假设输出 JSON:

```json
{
  "event_id": "call_function_xxx:GraphPage",
  "file": "GraphPage.ets",
  "angle": "State consistency",
  "type": "TextInput 默认值 vs vm 默认值脱节",
  "severity": "critical",
  "triggered_in_session": true,
  "evidence": "@State xMinInput = '-6.28' 但 vm.xMin 默认 -2π",
  "code_diff": "--- old\n+++ new\n@@ -60,3 +60,3 @@\n- @State xMinInput = '-2'\n+ @State xMinInput = '-6.28'",
  "fix_suggestion": "aboutToAppear 里同步 xMinInput → vm.xMin"
}
```

> **event_id 说明**:优先用 `tool_use.id`(跨 export 稳定),fallback 到 `L<jsonl_line>:<file_stem>`。
> `code_diff` 在 Edit 事件上由 `extract_code.py` 自动生成(unified diff 精简版,≤30 行)。

### Step 3:出 report.md — 必带 4 段

模板:`templates/llm-prompt-template.md`。`report.md` 必带:

- **严重度汇总表**(4 维,见"严重度约定"段)
- **按 severity 排序的 findings**:每条含 file:line + 代码 diff + 角度 + 解释 + 证据强度
- **未覆盖的潜在新 bug**(LLM 自由推理段)
- **自我怀疑段**:对每条 finding 标 confidence,标 'unverified' 的明确说,标可能的 agent trail 误判

---

## 输入示例

### JSONL 输入(摘)

```jsonl
{"type":"assistant","message":{"content":[
  {"type":"tool_use","name":"Write","input":{
    "file_path":"D:/.../GraphPage.ets",
    "content":"// 完整 ArkTS 代码..."
  }}
]}}
```

### events.json 输出

```json
[{
  "event_id": "call_function_xxx:GraphPage",
  "tool_use_id": "call_function_xxx",
  "line": 260,
  "file": "GraphPage.ets",
  "tool": "Write",
  "code": "...完整代码...",
  "old_code": "",
  "code_diff": "",
  "code_len": 1234,
  "thinking": "...agent 的思考摘要...",
  "thinking_source": "prior",
  "thinking_offset": 2
}, ...]
```

> `thinking_source`: `"self"` = 同 message 内 thinking;`"prior"` = 前 N 条 message 的 thinking(Claude Code JSONL 里几乎所有 Write/Edit 都是 prior,因为 thinking 和工具调用不在同一条 message);`null` = 向前 5 条 message 内都没有 thinking。

### report.md 输出

```markdown
## 严重度汇总
| critical | major | minor |
|---|---|---|
| 3 | 5 | 8 |

## Findings
### [critical] State consistency
- **位置**: GraphPage.ets:60-78 (Write)
- **角度**: State consistency
- **类型**: TextInput @State vs vm 状态脱节
- **代码 diff**: 
  ```diff
  - @State xMinInput: string = '-2'
  + @State xMinInput: string = '-6.28'
  ```
- **触发**: yes(本次 session 改源码默认值没传播)
- **修复**: ...

## 未覆盖的潜在新 bug
LLM 在 7 角度之外看到的潜在问题...
```

---

## 锚点案例

### A. 264c5a16 — 6 角度时代(老锚点,GraphPage)

> **说明**:完整跑通的 sin(x)→直线 bug 案例,用作 6 角度命中参考。代表"JSONL only + 静态分析"时代的有效范围。

| 角度 | 命中 bug |
|---|---|
| State consistency | TextInput 默认值 vs vm 脱节(GraphPage.ets:60-78)/ 多文件 radian mode 默认冲突(3 文件) |
| Timing | prefs.init().then vs setTimeout 竞态(GraphPage.ets:54-56) |
| Defaults | VM `isDegree=false` vs prefs `radiansDefault=false`(GraphViewModel.ets:247)/ `!radianMode` 符号反转(loadPrefs) |
| Verification | 测试只查 `y < 0.1` 不查 yMax(PlotUtils.test.ets)/ UI 测试只查 screenshot 大小(任意非空都过) |
| Errors | onChange 改 vm 没 compute,UI 静默 stale(GraphPage.ets)— 注:主动谎报 / apply-report 100% PASS 划走,由 aid-applying diff 管 |
| Resources | Canvas state 在 page switch 后 stale(GraphPage.ets) |

### B. 程序员模式 Bug 1/Bug 3 — 7 角度 + L1+L2+L3 新锚点(v1.3)

> **说明**:完整跑通的"JSONL only 视野盲区"案例,用作 L2/L3 + Build routing 角度的命中参考。锚点案例 264c5a16 全在 events.json 内可分析;**本案关键 bug 在 worktree 内但 events.json 外**,必须 L2/L3 才能找到。

**JSONL only(v1)报告**:`@Watch 漏调 onProgrammerRecompute` / `@Builder BaseRow 缓存` / `parseExpressionAsNumber 作 @Prop` / `@Watch 异步 first-frame stale` —— **4 项 critical 全部误诊**(dev-01 exploration trail ≠ live bug,build() re-render 兜底)。

**JSONL + worktree + hdc(v2)真实 finding**:

| 角度 | 命中 bug | 验证 |
|---|---|---|
| **Build routing**(v1.3 新增) | `CalculatorPage.ets:597` build() 走 `ProgrammerKeyboard()` 分支,但该键盘**不含 AND/OR/XOR/NOT/<< 键** | hdc dump `rca_p2_prog.xml` 列所有 clickable 元素 |
| **State consistency:回调契约错位**(v1.3 新增) | `ProgrammerPanel.ets:106-110` `.onClick(() => onBaseTap(NumberBase.DEC))` — 4 行共享 onClick 永远切到 DEC | hdc "1 → HEX 行 → F" 序列,dump 验证 expression 仍 "1"、截图含 Toast |
| **Defaults:回调参数硬编码**(v1.3 新增) | 同上,`NumberBase.DEC` 写死,无 caller-side 上下文 | 同上 |
| **Resources / State(子)** | dev-01 JSONL L307 / L378 / L381 / L384 / L408 修复**全部被还原**到 worktree HEAD | grep 对比 + git diff(待补) |

**结论**:v1.3 的 L1+L2+L3 输入分层 + Build routing / 回调契约错位 / 回调参数硬编码 子角度 **能稳定命中本案**;v1 仅 L1 + 6 角度漏掉 60% 真 bug。

---

## 限制与诚实

### 不适合的场景
- 用户没给 JSONL → 用 aid-analysis-locate-bug(需要 log + spec)
- Bug 在数值/算法层 → unit test 触发
- Bug 在 spec/设计层 → aid-analysis-spec-code-map
- Bug 在部署/工具链 → aid-init

### 已知失败
- 264c5a16 案例:LLM 找全了 6 个角度的 bug,但**没找**出 radian mode 的"语义反"(LLM 没意识到 `!radianMode` 反转)— 这是抽象"符号/方向反转"问题
- 修复方向:Defaults 角度升级为"边界/方向/比较反转",一次性扫 `!` / 三元分支写反 / 比较运算符错位 — 已在 `references/code-issues-angles.md` v1.2 实施
- **程序员模式 v1 报告(2026-08)**:**4 项 critical finding 全部误诊**(`@Watch 漏调`、`@Builder 缓存`、`parseExpressionAsNumber 作 @Prop`、`@Watch 异步 first-frame stale`)—— 这些是 dev-01 在 JSONL 中的 exploration trail 反映,实际 live 代码里因 build() re-render 兜底,bug 根本不显现
- 修复方向(v1.3):
  - **输入分层**:JSONL only 视野恒等于 agent 当天动过的代码, ≠ issue 完整 bug 集 — L1+L2+L3 强制
  - **Build routing 角度**:新增 — 程序员模式 Bug 3(`build()` 走 `ProgrammerKeyboard()` 但缺位运算键)只有这一角度能命中
  - **回调契约错位 / 回调参数硬编码**:State consistency / Defaults 加 sub-question — 程序员模式 Bug 1(`onClick(() => onBaseTap(NumberBase.DEC))` 写死)只有这两个能命中
  - **agent trail ≠ live bug 警告**:同一文件被改 ≥ 5 次反复横跳,trail 反映 agent 当时碰到的错,未必是 live bug — git diff worktree vs JSONL 最后修改状态验证
- **未覆盖类别**(LLM 自由推理段必备):
  - ArkUI 响应式追踪失败(ForEach 调 getter,getter 内部 @State 变更不触发重渲染)— 已在 State consistency 加 sub-question v1.2
  - 跨 worktree 合并时 import 污染(头部多了非本 issue 组件)— 已在 State consistency 加 sub-question v1.2
  - 回调契约错位(共享 onClick 不区分 row)— 已在 State consistency 加 sub-question v1.3
  - 回调参数硬编码(caller 没用 caller-side 上下文)— 已在 Defaults 加 sub-question v1.3
  - build() 路由分支完整性 + 子组件实现完整— 已在 Build routing 加角度 v1.3
  - UI 视觉/布局/坐标轴/标签清晰度 — 划走,显式声明给 harmonyos-ui-test

---

## 参考资料

| 文件 | 用途 |
|---|---|
| `SKILL.md`(本文件) | 流程 + 触发 + 输出格式(v1.3 含输入分层 + 7 角度) |
| `references/code-issues-angles.md` | **7 个角度的详细内容**(LLM 必读,v1.3 新增 Build routing) |
| `references/hdc-verify-cheatsheet.md` | **hdc 验证速查表**(Step 2.5 用,精简版;完整 1456 行见 `harmonyos-ui-test/SKILL.md`) |
| `templates/llm-prompt-template.md` | LLM 分析的 prompt 模板(v1.3 加 JSONL gap 自检 + hdc 验证可行性 + 自我怀疑段) |
| `scripts/extract_code.py` | Step 1 代码抽取工具(v1.3 加 `--include-worktree` flag + 输出 `worktree_gap.json`) |

### 关联 skill

> pipeline 已涉及的 skill(`aid-applying` / `aid-analysis-locate-bug` / `aid-analysis-root-cause` /
> `aid-analysis-output`)见上一节。以下是**不在 pipeline 中、本 skill 配合使用**的 skill:

| Skill | 关系 |
|---|---|
| `aid-analysis-phenomenon` | 读 issue + AID 产物 |
| `aid-analysis-log-scan` | 扫日志 |
| `aid-analysis-spec-code-map` | spec vs code 对照(手工) |
| `harmonyos-ui-test` | **本 skill 借其 hdc 能力做单次验证**(Step 2.5);不替代它维护测试套件(测例/回归/覆盖)— 详见 references/hdc-verify-cheatsheet.md §6 局限 |
| `dfr-fmea-harmony` | FMEA 可靠性分析 |

### 根因分析参考来源

- `D:\Demo\根因分析-sin直线问题.md` — 本 skill 6 角度的直接来源(**外部参考文件**,不在本仓库内,缺失时 6 角度仍可独立工作;v1.3 在此基础上新增第 7 角度 Build routing)
- `D:\Demo\根因分析-程序员模式缺陷.md` — 程序员模式 Bug 1/Bug 3 来源,作为 v1.3 Build routing / 回调契约错位 / 回调参数硬编码 子角度的命中参考

---

## 维护

- **新增角度**:不建议,**先归到现有 6 类**
- **新增实例**:7 角度下加鸿蒙/ArkTS 实例,**鼓励**
- **修改子问题**:如果某类子问题描述模糊,改它
- **新增报告模板**:可改 `templates/llm-prompt-template.md`

---

## 版本

- **v1.3(2026-08)**:
  - **重大:输入分层 L1 → L4 强制**(反 v1.2 "LLM 不需要 Read worktree" 保守原则)
    - L1 (must):JSONL events.json
    - L2 (highly recommended):worktree 当前代码(`worktree_gap.json` 列未触碰的必 Read)
    - L3 (when UI / Build):hdc dump + screenshot
    - L4 (when needed):apply-report / delta-spec.md / issue 评论
  - **新增角度 7 "Build routing"** — 源自程序员模式 Bug 3(build() 路由错位导致用户触不到位运算键)
  - **State consistency 新增"回调契约错位"** sub-question — 源自 Bug 1(`onClick(() => onBaseTap(NumberBase.DEC))` 写死)
  - **Defaults 新增"回调参数硬编码"** sub-question — 同源
  - **Step 2.5 由可选 → 条件必跑**:UI / Build routing / 回调契约类 finding 没 hdc dump 不报 critical(降级 major + 标 'unverified')
  - **严重度由 3 级 → 4 维**:severity + evidence + trigger + scope,见"严重度约定"段
  - **新增"agent exploration trail ≠ live bug"警告段**:同一文件被改 ≥ 5 次反复横跳,trail 反映 agent 当时碰到的错,未必是 live bug(程序员模式案 v1 报告 4 项 critical 误诊全是 trail 误判)
  - **脚本 `extract_code.py` 加 `--include-worktree <dir>` flag**:扫 worktree 源文件,与 JSONL 触过的对比,输出 `worktree_gap.json` 列未触碰文件 + 跳过 `.git .hvigor .test __pycache__ .gradle` 等目录
  - **Windows GBK 兼容**:stdout/stderr reconfigure utf-8 避免 print emoji 报错
  - **新增 anchor 案例 B(程序员模式 Bug 1/Bug 3)**:作为 7 角度 + L2/L3 输入的实际命中参考;原 anchor A(264c5a16 sin(x)→直线)保留作 6 角度时代参考
  - **报告必带 3 段自检**(模板改写):
    - JSONL gap 自检(列出 events.json 没出现的关键文件 + 是否 Read)
    - hdc 验证可行性(每条 finding 标 [UI]/[Build]/[Logic] + 是否走 hdc)
    - 自我怀疑段(对哪些 finding 自信度 < 50% + agent trail 误判风险)
- **v1.2(2026-08)**:
  - 修脚本:`extract_code.py` 改为向前回溯 5 条 message 找 thinking 块(原版 0% 命中,修后 87% 命中)
  - event_id 改用 `tool_use.id`(稳定)+ line fallback
  - Edit 事件输出 `code_diff`(unified diff 精简版)
  - State consistency 加 2 个子问题:ArkUI 响应式追踪 / 跨文件 import 污染
  - Defaults 反转升级为"边界/方向/比较反转",涵盖 `!` / 三元写反 / 比较运算符错位
  - **范围澄清**:
    - bug 症状层不限(UI/性能/计算都可,显式写进 description 和"做的"段)
    - 验证手段不限(hdc / screenshot / dump 都能用,不必外包给 harmonyos-ui-test)
    - UI 症状→代码根因反查表加 7 行,每行带"验证手段"列
  - 划走原则固化:**只划"做某类事"(设计改进/spec diff/AC 评估),不划症状来源、不划验证手段**
  - **新增 Step 2.5(可选验证)**:从 harmonyos-ui-test 抽出 hdc/dump/screenshot 关键命令到 [references/hdc-verify-cheatsheet.md](references/hdc-verify-cheatsheet.md)(约 350 行精简版,完整 1456 行链回 harmonyos-ui-test/SKILL.md);LLM 在静态分析不确定时主动验证假设
  - 加 `compatible: ["calculatorHuawei-main"]` frontmatter(12 个 sibling AID skill 已对齐)
- **v1.1(2026-08)**:Defaults 加"符号/方向反转"sub-question
- **v1.0**:基于 264c5a16 sin(x)→直线 bug 案例提炼,替代之前 35 个 regex pattern

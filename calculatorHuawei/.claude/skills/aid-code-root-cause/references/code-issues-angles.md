# Code-Level Issue Angles (LLM Thinking Framework)

## 简介

本文档是 LLM 在做代码层根因分析时的**思考角度框架**。

**不是 regex 规则库**(那会过拟合),而是 **7 个抽象类别**(v1.3 起 6 → 7,新增 "Build routing"),每个类别附 LLM 应问的子问题和鸿蒙/ArkTS 实例提示。

**用法**:
- LLM 对每个 Write/Edit 事件,逐条问 7 个角度
- 命中子问题 → 标记 finding,记 file:line
- 鸿蒙/ArkTS 实例作为**额外提示**,不是必须查

**关键约束**:
- 7 类是**思考方向**,不是 checklist — LLM 应自由推理
- 子问题是**该问什么**,不是**该查什么** — 答案由代码本身决定
- 实例是**常见形态**,不是**必中形态** — 新 bug 类也可能命中某个角度
- **7 角度都要问**(防漏)+ **自由推理补充**(防僵化) — 两个都要

**输入边界(v1.3 起强制)**:
- L1 must:JSONL events.json
- L2 highly recommended:worktree 当前代码(`worktree_gap.json` 列未触碰的必须 Read)
- L3 when UI:hdcdump + screenshot
- 详见 SKILL.md § "输入分层" 段

---

## 7 个角度

### 1. State consistency(状态一致性)

**核心问题**:同一概念在多处定义/存储时,改了一处其他地方知道不知道?

**LLM 应问的子问题**:
- 多个变量/字段描述**同一个东西**吗?它们之间有没有显式同步?
- 改了来源 A,下游 B/C 会被通知吗?
- 跨文件 / 跨模块的**默认值/单位/方向**一致吗?
- "single source of truth" 是谁?其他副本会 staleness 吗?
- **[ArkUI 响应式追踪]** `@Builder` / `ForEach` 里调用的 getter 或计算属性,ArkUI 能不能追踪到它**内部**对 `@State` 的依赖?要不要 `@Computed` / `@ObjectLink`?返回新对象/数组的 getter 不会自动触发依赖追踪(对应历史搜索不生效 case)
- **[跨文件 import 污染]** 这个文件 import 的依赖里,有没有不属于本 issue 范围、合并时塞进来的?头部 import 列表是否和 spec 列的依赖一致?(对应分数切换 case:worktree 合并后头部多了 4 个其他 issue 的组件)
- **[回调契约错位 / Caller-Callee mismatch]**(v1.3 新增)— 子组件声明 `onX: (data: T) => void`,父组件传 `onX: () => { ... }` 没用 caller-side 上下文(target / coord / state)?多 row 共享 `onClick` 时是否传递了行级信息?(对应程序员模式 Bug 1:`onClick(() => onBaseTap(NumberBase.DEC))` 写死 DEC)

**鸿蒙/ArkTS 实例提示**:
- `@State obj: Class` 改 obj.field — ArkUI 浅拷贝,UI 不更新(只引用替换触发)
- `@ObjectLink` 未在父组件 `@State obj` 初始化 — 编译过运行崩
- TextInput 默认值 vs vm 默认值 — UI 改了 vm 不知道
- PreferencesStore vs vm 默认值 — 跨文件默认值错位
- `@Prop` vs `@Link` 选错 — 单向 vs 双向语义反
- `ForEach(this.getHistorySections(), ...)` 看似对、UI 不刷新 — ArkUI 不追踪 getter 内部 `@State` 依赖(2026-08 历史搜索 case)
- 头部 import 多了 4 个其他 issue 的组件(分数切换 case,worktree 合并副作用)
- **共享 onClick 不区分 row**(2026-08 程序员模式 Bug 1:`onClick(() => onBaseTap(NumberBase.DEC))` 永远 DEC)

### 2. Timing(时序)

**核心问题**:操作在什么时候跑,顺序对不对?

**LLM 应问的子问题**:
- 异步初始化谁先谁后?有 race 吗?
- microtask(Promise.then)vs macrotask(setTimeout)区分了吗?
- lifecycle hook(aboutToAppear / onPageShow / onLoad)触发顺序对吗?
- "我读这个值时,谁填的?" 链路上游先跑了吗?

**鸿蒙/ArkTS 实例提示**:
- `prefs.init().then(loadPrefs)` vs `setTimeout(compute, 0)` 竞态
- aboutToAppear 里 `setTimeout(0)` 在首帧前是否跑完
- onPageShow 没 drawCanvas → canvas state 丢失
- router.getParams() 是 async,漏 await 拿到 undefined
- @Watch 初始值不触发,只在变化时触发

### 3. Defaults(默认值)

**核心问题**:默认值从哪里来,跟 spec/需求一致吗?

**LLM 应问的子问题**:
- 同一个量在多个文件里有默认值吗?一致吗?
- 默认值跟 spec / 需求文档写的一致吗?
- 用户**没显式设值**时,代码行为是预期的吗?
- 默认值改了,谁会注意到?
- **[边界/方向/比较反转]** 下面这一类陷阱都属于"语义反向" — 一次性扫:
  - `!` / `~` / 取反 / 类型转换(防 `!radianMode` / `isDegree = !prefs.radiansDefault` 类陷阱,源自 264c5a16 已知失败)
  - 三元里 `condition ? a : b` 两个分支**写反**(LLM 易漏,看似对称实则错)
  - 比较运算符错位:`>` vs `<`、`>=` vs `<=`、`==` vs `===`(特别在 sort/filter/边界判断里)
- **[回调参数硬编码]**(v1.3 新增)— 共享 onClick 场景下,callback 第一参数是否硬编码而没用 caller-side 上下文?`onClick(() => onX(NumberBase.HARDCODE))` 写死一个枚举值,无法响应坐标 / target / row?
  - 例如程序员模式 `onClick(() => onBaseTap(NumberBase.DEC))` — 应通过 `e.target.bounds` 或 `touchY` 算出点击的是 BIN/OCT/DEC/HEX 哪一行

**鸿蒙/ArkTS 实例提示**:
- VM `isDegree=false` vs prefs `radiansDefault=false` — 3 文件冲突,语义相反
- TextInput 默认 '-6.283185307' vs spec F3.1 [-2π, 2π] — 不一致
- build-profile.json5 改了 → hvigorw 缓存,需 clean
- @State 默认值改源码 vs 用户期望初始就生效 — 没联动
- `!radianMode` / `isDegree = !prefs.radiansDefault` 类符号反转(LLM 易漏,2026-08 锚点)
- 排序条件 `arr.sort((a,b) => a.x - b.x)` vs `b.x - a.x` — 升降序写反,UI 数据反向
- 边界判断 `x >= max` vs `x > max` — 边界点处理不一致(数组越界 / 含端点 vs 不含)
- **共享 onClick 硬编码**(2026-08 程序员模式 Bug 1:`onClick(() => onBaseTap(NumberBase.DEC))`)

### 4. Verification(验证)

**核心问题**:测试真的在测对的东西吗?能保证生产对吗?

**LLM 应问的子问题**:
- 断言验证的是**真行为**还是**副作用**?
- 测试通过能保证生产也对吗?
- 错误能被**检测到**吗,还是默默通过?
- UI 测试读 DOM/pixel,还是只读 screenshot?

**鸿蒙/ArkTS 实例提示**:
- `assertTrue(Math.abs(y) < 0.1)` 不查 yMax ≈ 1 → 漏水平线
- `assert ... getsize(path) > 50000` → 任意非空都过
- Node mock 测试只测 'x' 不测 'sin(x)'
- `assertTrue(errorMessage === '')` ≠ "结果对"
- 测试只跑 happy path,不跑边界

### 5. Errors(错误)

**核心问题**:错误被吞了吗?传到消费者了吗?用户看到真原因了吗?

**LLM 应问的子问题**:
- 异常被 try-catch 吞了?catch 块空吗?
- Promise 漏 catch?
- 错误传到调用方了吗?消费者能知道失败吗?
- 用户看到的失败信息和真原因一致吗?
- silent failure:代码"成功"了但实际是错的

**鸿蒙/ArkTS 实例提示**:
- onChange 改 vm 没 compute → UI 静默 stale(看起来对,实际错)
- try {} catch {} 空块 — 异常被吞
- Promise.then() 缺 .catch() — 异步失败无感
- catch (e) { console.log(e) } — 记了但没传给用户
- async/await 漏 await — 后续代码在 resolve 前跑

**划走(明确不属于 Errors 角度)**:主动谎报 / 自评 100% PASS 的合规层问题(如 apply-report 漏标偏离、design-review 自评全 PASS)由 **aid-applying diff** 管,本 skill 只报代码层的 silent failure。

### 6. Resources(资源)

**核心问题**:资源生命周期对吗?清理/同步做了吗?

**LLM 应问的子问题**:
- Canvas / Listener / Timer 创建了,清理了吗?
- 持久化数据(Preferences / Storage)同步了吗?
- page 切走时状态保存了吗?切回来能恢复了吗?
- aboutToDisappear / onPageHide 触发了?

**鸿蒙/ArkTS 实例提示**:
- Canvas state page switch 后 stale
- aboutToDisappear 没 unsubscribe EventBus → 内存泄漏
- PreferencesStore 多实例数据不同步
- Timer / Animation 未 clearTimeout → 后台继续跑
- @State 持有大对象(Map / Array)不释放

### 7. Build routing(v1.3 新增 — build() 路由完整性)

**核心问题**:`build()` 中的 if/else 分支 / 模式切换 / 子组件 inline 调用 — 是否把 spec 所有需要的东西挂上去?

**LLM 应问的子问题**:
- `build()` 中不同模式分支是否完整?某分支下 spec 列的功能项是否全部接入?
  - 例:`if (mode === PROGRAMMER) { ProgrammerKeyboard() } else { ButtonGrid() }` — `ProgrammerKeyboard` 是否包含 spec 列的所有按键?(程序员模式 Bug 3:`ProgrammerKeyboard` 没挂 AND/OR/XOR/NOT/<<,apply-report 自称"位运算 UI-only" 但实际键盘里没接)
- 多 row 共享 hot-zone 时,事件 router 是否区分了 row?(程序员模式 Bug 1:`Stack.onClick(() => onBaseTap(NumberBase.DEC))` 不区分 BIN/OCT/DEC/HEX 行)
- `if (cond) { A() }` 走的分支是否能满足用户的全部诉求?否则用户切错分支就用不到核心功能
- 横竖屏分支(`isLandscape ? portrait_layout : landscape_layout`)是否两套都完整?
- build() 路由决定后,被选中的子组件**自身**的实现完整性(单独组件视角看不到的洞)

**鸿蒙/ArkTS 实例提示**:
- **程序员模式 Bug 3**(2026-08):`if (mode === PROGRAMMER) { ProgrammerSection() + ProgrammerKeyboard() }`,但 `ProgrammerKeyboard` 不包含 AND/OR/XOR/NOT/<< 键 → 用户切到程序员模式触不到位运算
- **程序员模式 Bug 1**(2026-08):`Stack.onClick(() => onBaseTap(NumberBase.DEC))` 4 行共享同一 onClick → activeBase 永远切到 DEC → 用户在 HEX 行点击没用
- `@if (this.mode === X) { A() } else { B() }` 切换主题/横竖屏时,`B()` 那一支从未跑过 → 缺验证
- build() 末尾 `if (this.showX) this.XPanel()` — `XPanel` 自身有问题时不会触发 build → 仅当 `showX` 切到 true 才发现

**验证手段**:
- 必跑 hdc dump,列出当前屏所有 clickable 元素,对比 spec 列的元素清单
- 缺则报 routing bug
- 详细流程见 SKILL.md § "Step 2.5 必跑条件表"

---

## 不在这 7 类里(明确划走)

**部署/工具链层面** — 不属于 aid-code-root-cause,由 aid-applying / aid-init 管:

| 问题 | 归哪个 skill |
|---|---|
| 权限缺 manifest 声明 | aid-init / 部署 |
| build-profile.json5 配置错 | aid-init / 构建 |
| hdc MSYS_NO_PATHCONV 没设 | 测试工具(脚本侧) |
| oh-package.json5 依赖装错 | aid-init / 包管理 |
| i18n 资源文件缺失 | 资源/构建 |
| hap vs har vs hsp 模块类型选错 | 打包 |
| debug HAP 没签名 | 部署 |

**Spec/SKILL.md 合规层面** — 由 aid-applying diff_engine 管:

| 问题 | 归哪个 skill |
|---|---|
| SKILL.md 写了必须调某 skill,agent 没调 | aid-applying diff |
| spec 写要产出某文件,代码没产出 | aid-applying diff |
| design-review 自评 100% 不可信 | aid-reviewing |

---

## 使用示例(LLM 实际工作方式)

```markdown
# 对每个 Write/Edit 事件,逐条问 6 个角度:

## Event: GraphPage.ets L260 Write
### 1. State consistency?
- TextInput `@State xMinInput = '-6.28'` 与 `vm.xMin = -2*Math.PI` 都是默认值,改了前者 vm 不知道 → 状态脱节
- `PreferencesStore.radiansDefault=false` 与 `vm.isDegree=false` 都是 false,但含义相反
→ **finding**: state-default-mismatch (L247 + L260)

### 2. Timing?
- aboutToAppear 用 setTimeout(compute, 0) vs prefs.init().then(loadPrefs)
→ **finding**: timing-race (L54-56)

### 3. Defaults?
- 同上(也是 defaults 问题)
- agent 改 TextInput 默认值 '-2' 但 vm.xMin 默认 -2π,defaults 不一致

### 4. Verification?
- 测试只查 `Math.abs(y) < 0.1` 不查 yMax
- UI 测试只查 screenshot 文件大小
→ 2 个 finding

### 5. Errors?
- onChange 改 vm.xMin 但没 compute,UI 静默 stale
- 没有任何错误抛出或提示

### 6. Resources?
- Canvas state 在 onPageShow/onPageHide 时机对吗?
```

---

## 维护

**新增角度**:v1.3 起 7 类。**新增到现有 7 类优先,再加第 8 类需评审**。Build routing 是基于程序员模式 Bug 1/Bug 3 提炼,反映"agent 没改过的代码区 + hdc 验证缺失"的盲点。

**新增实例**:7 类下加鸿蒙/ArkTS 实例,**鼓励** — 帮助 LLM 知道该类 bug 在鸿蒙里长什么样。

**修改子问题**:如果某类子问题描述模糊,改它。

**新增子问题**:在某角度下追加 sub-question,**鼓励**。
  - v1.3 新增:
    - State consistency 新增"回调契约错位 / Caller-Callee mismatch"(源自程序员模式 Bug 1)
    - Defaults 新增"回调参数硬编码"(同源)
    - 新增第 7 类 "Build routing"(源自程序员模式 Bug 3)
  - v1.2 新增:
    - State consistency "ArkUI 响应式追踪"(源自历史搜索不生效 case)+ "跨文件 import 污染"(源自分数切换 case)
    - Defaults "边界/方向/比较反转"
  - v1.1 新增:Defaults "符号/方向反转"

---

## 历史

- v1.3(2026-08):
  - **新增第 7 角度 "Build routing"** — 源自程序员模式 Bug 3(`build()` 路由错位导致用户触不到位运算键)
  - **State consistency 新增"回调契约错位"** sub-question — 源自 Bug 1(`onClick(() => onBaseTap(NumberBase.DEC))` 写死)
  - **Defaults 新增"回调参数硬编码"** sub-question — 同源
  - **输入边界 L1 → L4 分层强制**:JSONL events + worktree 代码(必读 worktree_gap.json)+ hdc 验证(UI 类必跑)+ apply-report(可选)
  - **anchor 案例(程序员模式)** 加入:作为 7 角度(尤其 Build routing + 回调契约错位)的典型命中参考
- v1.2(2026-08):
  - State consistency 新增 2 个子问题:"ArkUI 响应式追踪"(getter 内部 @State 不被追踪)+ "跨文件 import 污染"(合并时头部 import 多了非本 issue 组件)
  - Defaults 反转 sub-question 升级为"边界/方向/比较反转",涵盖 `!` / 三元分支写反 / 比较运算符错位
  - Errors 角度加"划走"说明,显式区分 silent failure(本 skill)vs 主动谎报(aid-applying diff)
- v1.1(2026-08):Defaults 角度补"符号/方向反转"sub-question(防 `!radianMode` 类陷阱,源自 264c5a16 已知失败)
- v1.0:基于 264c5a16 sin(x)→直线 bug 案例提炼
- 来源:`D:\Demo\根因分析-sin直线问题.md`
- 替代之前 35 个 regex pattern(过拟合)

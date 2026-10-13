# 现有 Skill 的 OHOS / ArkUI 能力改进建议

> **编写日期**：2026-07-20  
> **适用范围**：当前 AID Workflow 的 PLANNING → IMPLEMENTING → APPLYING → REVIEWING → ARCHIVING 链路  
> **目标**：降低模型因不了解、误记或未验证 OHOS API / ArkUI 运行机制而生成错误 Spec、Design 和实现的概率  
> **关联分析**：[OHOS相关根因案例汇总.md](OHOS相关根因案例汇总.md)

---

## 1. 建议结论

建议优化现有 Skill，但**不建议每个阶段都重复扫描一遍本地 SDK**。

推荐模式：

```text
需求解析与澄清
  ↓
一次集中完成 OHOS 技术事实调查
  ├─ 本地 SDK .d.ts
  ├─ 项目 SDK / API Level 配置
  ├─ 现有项目代码和可复用实现
  ├─ ArkUI 状态、布局和生命周期分析
  └─ 必要时执行最小编译 / 运行 Spike
  ↓
产出唯一技术证据源 info.md
  ↓
Spec / Design 引用证据 ID，不再凭模型记忆写 API
  ↓
IMPLEMENTING 将证据和运行验证拆为 Task
  ↓
APPLYING 检查实际代码是否偏离证据和 Design
  ↓
rev-01 独立核验技术事实
  ↓
dev-02 在真实环境做回归验证
```

核心原则：

> **模型知识只能作为搜索线索，不能作为 OHOS API 事实来源。**

事实来源优先级应固定为：

```text
本地 SDK 声明和项目配置
  > 最小可编译 / 可运行 Spike
  > 与当前 SDK 版本匹配的官方文档
  > 项目内已验证的可运行代码
  > 模型记忆
```

---

## 2. 当前 Skill 的主要结构性问题

### 2.1 aid-planning：Spec 生成早于代码仓和 SDK 理解

当前 [aid-planning/SKILL.md](aid-workflow-skills/skills/aid-planning/SKILL.md) 的执行顺序：

```text
step1 意图
→ step2 需求理解
→ step3 需求澄清
→ step4 需求 Spec
→ step5 代码仓理解
→ step6~8 设计
→ step9 审视
```

主要问题：

- step4 已产出 `delta-spec.md`；
- step5 才调用 `rq-codebase` 产出 `info.md`；
- 全局约束要求严格按顺序执行，不允许自行调整顺序。

模型在生成 Spec 时可能尚未确认：

- 项目实际 compileSdk / compatibleSdk；
- 本地 SDK 是否存在候选 API；
- API 的准确 import 和签名；
- API 返回的是 PixelMap、Promise 还是 UI 组件；
- 权限和 API Level；
- ArkUI V1 还是 V2 状态模型；
- 项目是否已有可复用实现。

二维码案例是该顺序的直接风险表现。

### 2.2 rq-codebase：只理解项目代码，没有强制核验本地 SDK

当前 [rq-codebase/SKILL.md](aid-workflow-skills/skills/rq-codebase/SKILL.md) 已包含：架构分析、接口识别、影响范围、风险、测试策略，但缺少：

- 读取 `build-profile.json5`、`module.json5`、`oh-package.json5` 确认 SDK 环境；
- 搜索本地 SDK `.d.ts`；
- 记录 API 证据路径；
- 区分 VERIFIED / UNCERTAIN / UNAVAILABLE；
- 分析 ArkUI 状态传播和布局契约；
- 对不确定行为执行最小 Spike。

因此 `info.md` 可能仍只是模型根据已有知识总结，而不是技术事实报告。

### 2.3 rq-clarify：ArkUI 行为问题没有进入澄清清单

当前 [rq-clarify/SKILL.md](aid-workflow-skills/skills/rq-clarify/SKILL.md) 在 HarmonyOS ArkTS 专项澄清中只提到：数据存储、离线策略、后台行为、权限。

未涉及：

- UI 状态传播预期；
- 父子组件数据刷新方式；
- 布局关系与可达性；
- ArkUI 状态模型 V1/V2 选择；
- 媒体、分享、保存、显示组件的能力区分。

### 2.4 mod-design：API 决策可以自由选择 OHOS API

当前 [mod-design/SKILL.md](aid-workflow-skills/skills/mod-design/SKILL.md) 已有 D9 平台集成和 D4 接口设计章节，但：

- 不强制引用 `info.md` 中的 API 证据 ID；
- 不要求标注 API Level、权限、返回类型；
- 不要求说明 API 选型背后的能力边界和代价；
- 不要求描述 ArkUI 状态传播图。

### 2.5 aid-applying：实施期 API/组件替换无门禁

当前 [aid-applying/SKILL.md](aid-workflow-skills/skills/aid-applying/SKILL.md) 有 step3-2-2b UI 测试降级门禁，但没有针对以下情况的门禁：

- 实际 import 与 Design 不一致；
- 实际 Kit 与 Design 不一致；
- 实际返回类型与 Design 不一致；
- 新增或删除系统权限；
- 实际 ArkUI 装饰器与 Design 不一致；
- 关键 UI 组件被替换为能力更弱的组件。

这些场景下当前流程没有要求生成 `design-amendment.md`。

### 2.6 aid-reviewing：默认是轻量模式，不强制核验 OHOS 事实

当前 [aid-reviewing/SKILL.md](aid-workflow-skills/skills/aid-reviewing/SKILL.md) 默认是 `default concise` 模式，输出优化稿而不进入 `audit mode`。在大量 issue 中实际被调用的次数很少，且不强制：

- 比对 API 证据与实际 import；
- 验证 OHOS API 真的存在；
- 对照原始需求与设计实现是否一致。

### 2.7 harmonyos-ui-test：缺端到端行为断言

当前 [harmonyos-ui-test/SKILL.md](aid-workflow-skills/skills/harmonyos-ui-test/SKILL.md) 主要解决 hdc 操作、UI 树解析、截图、Excel / Markdown 模板：

- 强项是 hdc 工具和测试结果记录；
- 弱项是没有强制 UI 状态传播、布局 bounds、组件可达性、媒体内容解码等端到端行为断言。

### 2.8 tdd-enforcer：不知道 AC 完备性是否足够

当前 [tdd-enforcer/SKILL.md](aid-workflow-skills/skills/tdd-enforcer/SKILL.md) 的检查清单只验证"每条 AC 都有对应测试"，不验证：

- AC 是否覆盖 ArkUI 集成层；
- AC 是否写成用户可感知的行为；
- AC 是否引用了 OHOS API 证据。

### 2.9 aid-implementing：tasks 模板不要求证据和验证方式

当前 [aid-implementing/SKILL.md](aid-workflow-skills/skills/aid-implementing/SKILL.md) 的任务模板只有描述、文件、依赖、验收标准四段，没有：

- 引用 `info.md` API 证据；
- 引用 `delta-spec` AC；
- 标明 ArkUI 集成 / UI 验证方式；
- 标明端到端行为如何被复测。

### 2.10 aid-archiving：归档条件未做技术事实核查

当前 [aid-archiving/SKILL.md](aid-workflow-skills/skills/aid-archiving/SKILL.md) 的归档判断只检查任务完成状态和制品存在性，不检查：

- `design-amendment.md` 是否存在并被评审；
- 实际 import 是否与 `delta-design` 一致；
- UI 测试是否在真实设备上跑过；
- 是否仍有 UNCERTAIN 状态的核心 API。

---

## 3. 推荐改进方案

## 3.1 改造 aid-planning

### 调整步骤顺序

将代码仓与 SDK 调查移到 Spec 生成之前：

```text
step1 用户意图
step2 需求理解
step3 需求澄清
step3.5 OHOS 技术事实预检（新增）
step4 需求 Spec
step5 已有代码与可复用实现（基于 step3.5）
step6 复杂度评估
step7 架构设计
step8 组件设计
step9 独立设计审视
```

说明：

- `step3.5` 不是新增的独立 Skill，而是 `aid-planning` 内部对 `rq-codebase` 的硬性触发条件；
- 如果需求涉及 HarmonyOS / ArkUI / Kit / 权限 / 状态管理 / 媒体 / 路由 / 共享，则 step3.5 必跑。

### 增加硬门禁

- step4 输出 `delta-spec.md` 时，如果 step3.5 的 `info.md` 中存在 `UNCERTAIN` 状态的核心 API，必须先解决；
- 解决方式：补充本地证据、改为 UNVERIFIED 已有的能力，或在 Spec 中显式声明"降级为不可用能力并补 won't-fix 决策"；
- 未解决禁止进入 step5。

### 推荐证据等级

| 状态 | 含义 | 是否可进入 step4 |
|---|---|---|
| VERIFIED | 已在本地 SDK、最小编译或已有可运行代码中验证 | 是 |
| UNCERTAIN | 仅有模型记忆或一般性文档 | 否，必须先验证 |
| UNAVAILABLE | 已确认当前 SDK / 配置不可用 | 是，但必须显式声明降级 |

---

## 3.2 改造 rq-codebase：增加 OHOS 技术事实调查

### 增加触发条件

当需求类别包含以下关键词时，必须进入 OHOS 技术事实调查：

- HarmonyOS / OpenHarmony / ArkTS / ArkUI / Stage / 模拟器 / 真机；
- 状态管理 / 响应式 / 组件 / 页面 / 渲染；
- 权限 / 后台 / 服务 / 卡片 / 共享 / 传输；
- 媒体 / 相机 / 麦克风 / 文件 / 相册 / 通讯录 / 位置 / 二维码 / 蓝牙 / NFC / 网络。

### 强制的环境核查

读取并记录：

- `build-profile.json5` 中的 `compileSdkVersion`、`compatibleSdkVersion`；
- `oh-package.json5` 中的依赖和版本范围；
- `AppScope/app.json5` 与各模块 `module.json5` 的 `requestPermissions`；
- ArkTS / ArkUI 配置（V1 还是 V2）；
- 模拟器 / 真机的 API Level；
- 现有 `entry/src/main/ets` 结构与可复用模块。

### API 证据矩阵模板

写入 `info.md` 顶部新增章节"OHOS 技术事实"：

```markdown
## OHOS 技术事实

### SDK 环境

| 项 | 值 | 来源 |
|---|---|---|
| compileSdkVersion | {值} | build-profile.json5 |
| compatibleSdkVersion | {值} | build-profile.json5 |
| API Level | {值} | ... |
| ArkUI 状态模型 | V1 / V2 | ... |

### API 证据矩阵

| ID | 需求能力 | 候选 API | 实际 import | 方法签名 | 返回值 | API Level | 权限 | 本地证据 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| API-001 | 生成二维码 | @ohos.arkui.qrcode.QRCode | (待查) | (待查) | UI 组件 | (待查) | 无 | (待查) | UNCERTAIN |
| API-002 | 生成 PixelMap | @kit.QRCodeKit.qrcode.createQrCode | (待查) | (待查) | Promise<PixelMap> | (待查) | 无 | (待查) | UNCERTAIN |
| API-003 | 保存相册 | photoAccessHelper | (待查) | (待查) | (待查) | (待查) | WRITE_IMAGEVIDEO | (待查) | UNCERTAIN |
```

### ArkUI 状态传播分析

为涉及状态的特性增加：

```markdown
## ArkUI 状态传播

| 状态源 | 装饰器 | 修改入口 | 消费组件 | 预期触发 | 验证方式 |
|---|---|---|---|---|---|
| searchQuery | @State | TextInput.onChange | HistoryPanel | 列表重渲染 | dump 节点数对比 |
| expression | @State | onDigit/onEqual | ProgrammerPanel | 四行刷新 | dump 文本对比 |
| activeBase | @State | onBaseTap | 键盘 | 字符集变化 | 输入 F 是否被接受 |
```

并明确检查：

- 普通方法返回值作为 `@Prop` 入参时是否真正能传播；
- `ForEach` 的数据源是否随状态改变；
- 父组件计算值传入子组件是否需要显式缓存；
- 是否错误地使用普通方法代替 `@State` / `@Computed` / `@Watch`。

### 布局关系与可达性

为涉及布局的特性增加：

```markdown
## ArkUI 布局约束

| 元素 A | 元素 B | 容器 | 布局关系 | 允许重叠 | 验证方式 |
|---|---|---|---|---|---|
| 结果文本 | 切换按钮 | Column/Row | 上下排列 | 否 | bounds 交集 = 0 |
| 表达式输入框 | 键盘 | Column | 顺序排列 | 否 | hdc dump bounds |
| ProgrammerSection | ProgrammerKeyboard | if/else | 二选一 | 不适用 | build 分支覆盖 |
```

并明确检查：

- 涉及条件渲染的组件是否被声明在所有可能的 build 分支；
- 不同朝向、横竖屏、字号下布局是否仍然成立；
- 关键节点的可点击区域是否被其他节点遮挡。

### 最小 Spike

如果静态证据不足，应执行 Spike 并把结果写入 `info.md`：

- 状态 Spike：验证 `@State` 变化是否驱动 `ForEach`；
- 布局 Spike：验证 `Stack` 中两个组件是否重叠；
- API Spike：调用 SDK API 得到真实返回值；
- 权限 Spike：验证 `requestPermissions` 是否能在目标 API Level 通过。

推荐位置：

```text
{changes_root}/spikes/<purpose>/
```

不应放在项目根目录或上传目录。

---

## 3.3 改造 rq-clarify：增加 ArkUI 行为澄清规则

### 通用状态澄清

需求描述涉及以下任一场景，必须澄清：

- 文本输入影响列表、表格、树或网格；
- 选项切换影响可见内容；
- 状态变化驱动页面切换或动画；
- 用户操作触发刷新加载。

澄清输出必须包含：

- 状态所有者；
- 修改入口；
- 派生状态计算方式；
- 消费者；
- 期望的响应式传播；
- 降级行为（如状态未及时刷新时的容错）。

### 布局澄清

需求涉及以下任一场景，必须澄清：

- 浮动按钮、徽标、角标；
- 模态层、Drawer、Sheet、Dialog、Menu；
- 同区域多个控件并存；
- 跨屏幕尺寸或横竖屏布局。

澄清输出必须包含：

- 元素之间布局关系；
- 显隐 / 替换条件；
- 是否允许重叠；
- 长文本或旋转下的行为。

### 媒体与显示能力澄清

需求涉及以下任一场景，必须澄清：

- 二维码 / 条码 / 截图 / 拍照；
- 保存到相册 / 共享 / 发送；
- 媒体播放 / 编辑；
- 文件导入导出。

澄清输出必须包含：

- 期望的输出媒体格式；
- 期望的可被消费方（其他 App、扫描器、相册）解码的内容；
- 是否需要保存或分享能力；
- 与现有权限和 Ability 的关系。

---

## 3.4 改造 mod-design：API 决策必须引用证据 ID

### D4 接口设计

API 设计必须为每个关键 API 引用 `info.md` 证据 ID，例如：

```markdown
## 4. 接口设计

### 4.x 二维码生成

- **能力**：将算式文本编码为二维码图像，并允许保存到相册。
- **引用证据**：API-002（@kit.QRCodeKit.qrcode.createQrCode）+ API-003（photoAccessHelper.saveAsset）
- **API 选型理由**：API-001 只能渲染 UI，无法生成可保存图像。
- **能力损失**：若不引入 API-003，则需要降级为“只显示二维码”并显式声明 won't-fix。
- **ArkUI 状态依赖**：见 §3.x 中 ProgrammerSection 状态传播图。
```

### D9 平台集成

每个 Kit 必须注明：

- 证据 ID；
- API Level；
- 权限；
- 返回类型；
- 副作用；
- 与 ArkUI 状态模型的关系。

### D3.5 模块设计

涉及 ArkUI 状态、布局、可达性的模块必须包含：

- 状态传播图；
- 布局约束表；
- 关键 build 分支；
- 端到端验证方式。

---

## 3.5 改造 aid-applying：增加 API/组件偏离门禁

### APPLYING 阶段入口前自检

实际代码与 `delta-design.md` 出现以下任一不一致时，必须暂停并写 `design-amendment.md`：

- import 路径或包名不同；
- Kit / 模块 / 组件不同；
- 函数签名、参数、返回类型不同；
- 新增或删除系统权限；
- ArkUI 装饰器、V1/V2 模型不同；
- 关键 UI 组件从数据生成型变为仅显示型；
- 实际行为导致功能降级。

### design-amendment 模板

```markdown
# Design Amendment

## 变更背景
- 实施期间发现 / 决定变更的内容
## 原 Design
- 引用 delta-design.md 章节
## 新 Design
- 实际采用的方案
## 触发原因
- 本地 SDK 证据
- 最小 Spike 证据
- 风险评估
## 能力损失
- 与原始需求对比的功能差
## 受影响 AC
- delta-spec 中被降级或删除的 AC
## 受影响测试
- 已通过的测试是否仍可证明
## 评审结论
- rev-01 是否同意降级
```

### 与现有的 step3-2-2b 关系

- `step3-2-2b` 仍然负责 UI 测试降级；
- API/组件偏离门禁是新的 `step3-2-x` 段，建议在 `step3-2-1` 之前执行；
- 自检命令通过后方可继续 TDD 循环。

### 与 aid-implementing 联动

- `aid-implementing` 在设计 tasks 时应包含 API 证据和端到端验证两个分类；
- `aid-applying` 实施时若发现证据失效，应回写 `info.md` 并生成 amendment。

---

## 3.6 改造 aid-reviewing：增加 OHOS 事实核验

### audit mode 必须包含 OHOS 证据

如果被审文档是 `info.md`、`delta-spec.md`、`delta-design.md`、QR/媒体类需求，应额外检查：

- `delta-design` 引用的 API 是否在 `info.md` 证据矩阵中；
- `delta-design` 引用的 import 与实际代码是否一致；
- 是否新增或删除权限而未声明；
- 是否对原始需求进行了降级而未声明；
- 是否与 `增强需求-*.md` 或 issue body 描述一致。

### rev-01 角色扩展

- rev-01 应被授权查询本地 SDK；
- rev-01 必须独立比对 `info.md` 与设计文档；
- rev-01 的检查项应包括端到端验证证据。

### 轻量模式不变

为了不增加频繁审计成本，`default concise` 模式保持不变；只对包含 OHOS / ArkUI 关键决策的文档自动提升到 OHOS 事实核验清单。

---

## 3.7 改造 harmonyos-ui-test：增加端到端行为断言

### 增加必填行为断言

涉及以下行为时，TC 必须包含对应断言：

- 状态变化后 UI 重渲染：dump 节点数 / 文本对比；
- 子组件数据同步：dump 子组件参数；
- 布局关系：bounds 交集或中心点距离；
- 组件可达性：触发 build 分支的入口是否真实可达；
- 媒体输出内容：解码或解析真实输出；
- 权限请求：观察弹窗或降级行为。

### bounds 断言示例

```python
def assert_no_overlap(a, b, threshold=4):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    if ax1 < bx2 - threshold and ax2 > bx1 + threshold and \
       ay1 < by2 - threshold and ay2 > by1 + threshold:
        return False, "bounds 重叠"
    return True, "无重叠"
```

### 媒体内容解码示例

```python
def assert_qr_content(screenshot_path, expected):
    import cv2
    img = cv2.imread(screenshot_path)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data == expected, data
```

### 状态传播断言示例

```python
def assert_state_refresh(dump_before, dump_after, expected_delta):
    return expected_delta in set(dump_after) - set(dump_before)
```

---

## 3.8 改造 tdd-enforcer：完成检查清单增加三项

新增项：

- AC 完备性：是否覆盖 ArkUI 集成层、UI 状态传播、用户可感知行为；
- API 证据引用：测试代码中引用的 OHOS API 是否对应 `info.md` 证据 ID；
- 端到端验证：是否有 hdc 真实设备或真实运行验证，而不是只靠单测或源码 grep。

修改原清单的位置在原 6 条之后，不替换原有条目。

---

## 3.9 改造 aid-implementing：tasks 模板要求证据和验证方式

在任务模板中新增"证据引用"和"端到端验证"两列：

```markdown
#### Task 1.1 {任务名}
- 描述：...
- 涉及文件：...
- 依赖任务：...
- 引用证据：API-001 / spec AC-2 / design §3.4
- 单元测试：...
- 端到端验证：hdc dump 验证 / 截图对比 / 媒体解码
- 验收标准：...
```

这样可以保证：

- 每条 Task 都能追溯到技术证据；
- 每条 Task 都明确说明如何被独立验证；
- rev-01 可以按 Task 抽查验证质量。

---

## 3.10 改造 aid-archiving：归档前核验技术事实

归档前必须通过：

- `design-amendment.md` 存在并被评审（如果实施期发生 API 偏离）；
- 实际 import 与 `delta-design` 一致；
- 真实设备或模拟器 UI 测试通过（非空运行）；
- `info.md` 中所有 UNCERTAIN 已关闭；
- 原始需求的能力已逐条对照，没有未声明的降级。

归档时不仅复制制品，还要把 `info.md` API 证据矩阵作为长期可追溯档案。

---

## 4. 跨 Skill 协作流程

推荐流程：

```text
用户需求
  ↓
aid-planning
  ├─ step2 rq-parse
  ├─ step3 rq-clarify（含 ArkUI 行为、布局、媒体能力澄清）
  ├─ step3.5 rq-codebase（OHOS 技术事实调查 + info.md 证据矩阵）
  ├─ step4 delta-spec（引用证据矩阵 ID）
  ├─ step7 架构
  ├─ step8 mod-design（引用证据矩阵 ID + 状态传播图 + 布局约束）
  └─ step9 aid-reviewing（OHOS 事实核验）

aid-implementing
  └─ tasks.md 每条 Task 引用证据 ID + 端到端验证方式

aid-applying
  ├─ step3-2-0 多根因前置验证
  ├─ step3-2-x API/组件偏离门禁（新增）
  ├─ step3-2-1 TDD（含 API 证据引用）
  ├─ step3-2-2 全量测试
  ├─ step3-2-2b UI 测试（端到端行为断言）
  └─ step3-2-3 lint

rev-01（独立 Agent）
  └─ 核验 info.md 证据、delta-design 一致性、原始需求对照

dev-02（独立 Agent）
  └─ 在真实环境做回归验证

aid-archiving
  └─ 归档前技术事实核验
```

---

## 5. 实施优先级

| 优先级 | Skill | 改动 | 工作量预估 | 立即效果 |
|---|---|---|---|---|
| P0 | aid-planning | 调整顺序 + API 状态门禁 | 0.5 天 | 阻止二维码类问题在 Planning 阶段就失控 |
| P0 | rq-codebase | API 证据矩阵 + ArkUI 状态传播 + 布局约束 + Spike | 1-2 天 | 让后续阶段有可引用的事实源 |
| P0 | aid-applying | API/组件偏离门禁 + design-amendment 模板 | 0.5 天 | 阻止实施期越权切换 API |
| P1 | mod-design | D4/D9 强制引用证据 + D3.5 状态传播 + 布局约束 | 0.5 天 | 让 Design 真正反映事实 |
| P1 | aid-reviewing | OHOS 事实核验清单 | 0.5 天 | 让独立评审发挥拦截作用 |
| P1 | harmonyos-ui-test | 端到端行为断言 | 1 天 | 让 UI 测试能抓状态传播、布局、媒体内容 |
| P1 | rq-clarify | ArkUI 行为/布局/媒体澄清规则 | 0.5 天 | 提早补齐关键模糊点 |
| P2 | tdd-enforcer | 完成清单三项 | 0.25 天 | 让 TDD 不只测纯函数 |
| P2 | aid-implementing | tasks 模板补充证据列 | 0.25 天 | 让每条 Task 可追溯 |
| P2 | aid-archiving | 归档前技术事实核验 | 0.25 天 | 防止把不一致的变更归档到 main |

---

## 6. 不建议做的事

- 不建议在 Skill 内硬编码大量 OHOS API 名称。SDK 和 API 会随版本变化，硬编码会快速过期。
- 不建议在每个阶段重复扫描整个本地 SDK。会导致速度变慢，且不同阶段结论可能冲突。
- 不建议让 tdd-enforcer 接管 UI 测试。tdd-enforcer 应该管纯逻辑层，UI 测试应由 harmonyos-ui-test 管。
- 不建议让 harmonyos-ui-test 接管 AC 模板。AC 模板属于需求层，应由 aid-planning 管。
- 不建议把 aid-reviewing 当作万能门禁。reviewing 应当聚焦于文档和事实核验，而不是重复执行或回归测试。
- 不建议把 OHOS 知识汇总成一个超大的新 Skill。应该把 OHOS 技术事实作为 info.md 的标准章节，让现有 rq-codebase 承担该职责。

---

## 7. 立即可执行的小步快跑建议

如果暂时不能全量改造，可以先做两件事：

1. 把 `rq-codebase` 的"分析步骤"中追加一个 OHOS 技术事实段，让 `info.md` 在每条需求上记录 API 证据矩阵（即使是空表）。最低成本先把"是否需要查 API"这件事流程化。
2. 在 `aid-applying` 的 `step3-2-1` 之前加一段"实际 import 偏离检查"，并允许生成 `design-amendment.md`。最低成本先阻止实施期静默换 API。

这两步不依赖大规模 Skill 改写，可以在 1-2 天内落地，但能直接缓解二维码、二维码类需求偏离问题。

---

## 8. 与记忆/Memory 的关系

本次改进建议在执行时，建议把以下事项写入项目记忆：

- API 证据矩阵是唯一技术事实源；
- UNCERTAIN 状态 API 必须关闭才允许进入 step4；
- 实施期 API 替换必须先写 `design-amendment.md`；
- UI 测试必须有端到端行为断言，不能只看节点存在；
- rev-01 必须独立核验 OHOS 事实，不能只看文档格式。

这些是 AID Workflow 在 HarmonyOS 项目上的硬约束，应作为长期规则记录。

---

## 9. 关联文档

- [OHOS相关根因案例汇总.md](OHOS相关根因案例汇总.md)
- 当前 Skill：
  - [aid-planning/SKILL.md](aid-workflow-skills/skills/aid-planning/SKILL.md)
  - [rq-codebase/SKILL.md](aid-workflow-skills/skills/rq-codebase/SKILL.md)
  - [rq-clarify/SKILL.md](aid-workflow-skills/skills/rq-clarify/SKILL.md)
  - [aid-implementing/SKILL.md](aid-workflow-skills/skills/aid-implementing/SKILL.md)
  - [aid-applying/SKILL.md](aid-workflow-skills/skills/aid-applying/SKILL.md)
  - [mod-design/SKILL.md](aid-workflow-skills/skills/mod-design/SKILL.md)
  - [aid-reviewing/SKILL.md](aid-workflow-skills/skills/aid-reviewing/SKILL.md)
  - [aid-archiving/SKILL.md](aid-workflow-skills/skills/aid-archiving/SKILL.md)
  - [harmonyos-ui-test/SKILL.md](aid-workflow-skills/skills/harmonyos-ui-test/SKILL.md)
  - [tdd-enforcer/SKILL.md](aid-workflow-skills/skills/tdd-enforcer/SKILL.md)

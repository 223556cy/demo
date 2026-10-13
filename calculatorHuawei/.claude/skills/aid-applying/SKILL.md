---
name: aid-applying
description: |
  AID APPLYING 阶段 skill，用于代码应用与测试。
  当用户说"执行 aid-applying"、"应用代码"、"测试xxx"或类似表述时触发。
  本 skill 负责 APPLYING 阶段的所有工作：代码应用、单元测试、lint 检查、产出应用报告。
compatible: ["{项目名}-main"]
---

# AID-Applying Skill

## 概述

本 skill 实现 AID APPLYING 阶段，负责将开发完成的代码应用到项目并进行测试验证。

```
APPLYING 阶段流程：
step3-0（环境检查）→ step3-1（确认应用条件）→ step3-2（代码应用）→ step3-3（更新任务状态）→ step3-4（产出应用报告）
```

## 使用方法

```
执行 aid-applying {类型}-{名称}
应用 {功能名称} 的代码
测试 {功能名称} 功能
```

---

## 前置条件

进入 APPLYING 阶段前，确认以下条件已满足：
1. IMPLEMENTING 阶段已完成
2. 代码已完成开发
3. 所有 tasks.md 中的任务已完成

---

## 全局约束

### 1. TodoWrite 管理

**注意**：TodoWrite 由编排层 aid-workflow 统一管理，本 skill 不使用 TodoWrite 工具。

### 2. todo.md 文件同步

在每个 step 完成后，同步更新 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/todo.md` 文件，记录当前进度。

### 3. 测试要求

- 单元测试必须通过
- Lint 检查必须通过
- 如有集成测试，也需要通过

### 4. 代码质量

确保代码符合项目规范：
- 遵循导入顺序规范
- 遵循命名规范
- 无安全隐患

---

## step3-0：环境检查

**目的**：确保编译和测试环境就绪，避免在 APPLYING 过程中因环境问题中断。

**原则**：根据项目类型自适应检查，不硬编码特定工具。

### step3-0-1：检测项目类型

检查项目根目录下存在哪些构建文件来确定项目类型：

| 构建文件 | 项目类型 | 编译命令 | 测试命令 |
|---------|---------|---------|---------|
| `hvigorw` | HarmonyOS | `hvigorw assembleHap` | `hvigorw test@entry` |
| `package.json` | Node/JS/TS | `npm run build` | `npm test` |
| `gradlew` | Gradle/Android | `gradlew assembleDebug` | `gradlew test` |
| `pom.xml` / `build.gradle` | Maven/Java/Kotlin | `mvn compile` / `gradle compileJava` | `mvn test` / `gradle test` |
| `Cargo.toml` | Rust | `cargo build` | `cargo test` |
| `Makefile` | C/C++ | `make` | `make test` |
| 其他 | 未知类型 | 询问用户 | 询问用户 |

**操作**：
1. 检查项目根目录下的构建文件
2. 识别项目类型
3. 记录对应的编译和测试命令
4. 如果无法识别，询问用户使用的构建工具

### step3-0-2：检查编译环境

根据检测到的项目类型，运行对应的版本检查命令：

| 项目类型 | 检查命令 | 成功标准 |
|---------|---------|---------|
| HarmonyOS | `hvigorw --version` | 输出版本号 |
| Node/JS/TS | `node --version && npm --version` | 输出版本号 |
| Gradle | `gradlew --version` | 输出版本号 |
| Maven | `mvn --version` | 输出版本号 |
| Rust | `cargo --version` | 输出版本号 |
| C/C++ | `make --version` | 输出版本号 |
| 未知 | 询问用户 | 用户提供命令 |

**检查项**：
- 命令是否可用
- 版本号是否正常显示

### step3-0-3：尝试编译项目

运行编译命令确认项目可构建：

| 项目类型 | 编译命令 | 成功标准 |
|---------|---------|---------|
| HarmonyOS | `hvigorw assembleHap` | BUILD SUCCESS |
| Node/JS/TS | `npm run build` | 退出码 0 |
| Gradle | `gradlew assembleDebug` | BUILD SUCCESSFUL |
| Maven | `mvn compile` | BUILD SUCCESS |
| Rust | `cargo build` | 退出码 0 |
| C/C++ | `make` | 退出码 0 |
| 未知 | 询问用户 | 用户确认 |

**检查项**：
- 项目能否成功编译
- 是否有编译错误

### step3-0-4：检查测试环境

运行测试命令确认测试框架可用：

| 项目类型 | 测试命令 | 成功标准 |
|---------|---------|---------|
| HarmonyOS | `hvigorw test@entry --help` | 输出帮助信息 |
| Node/JS/TS | `npm test -- --help` 或 `jest --version` | 输出版本或帮助 |
| Gradle | `gradlew test --help` | 输出帮助信息 |
| Maven | `mvn test --help` | 输出帮助信息 |
| Rust | `cargo test --help` | 输出帮助信息 |
| C/C++ | `make test` 或检查 Makefile | 目标存在 |
| 未知 | 询问用户 | 用户提供命令 |

**HarmonyOS 特殊说明**：
- CLI 测试在 Linux 环境下不支持，需使用 Windows/macOS
- **UI 测试必须使用 `skill('harmonyos-ui-test')`**（铁律 7：不准用 Node.js 单元测试或源码 grep 替代鸿蒙真实环境测试）
- **构建必须用 worktree 里的 `opencalc/build_hap.bat`**（已设 `DEVECO_SDK_HOME` + `JAVA_HOME` env），不能用裸 `hvigorw`（必失败因 env 缺失）
- 验证命令：`cmd //c "build_hap.bat assembleHap --no-daemon"` 替代 `hvigorw assembleHap`
- `harmonyos-ui-test` skill 路径：`C:\Users\26909\.claude\skills\harmonyos-ui-test\SKILL.md`（**用户全局 skill，必须显式调用**）

**检查项**：
- 测试命令是否可用
- Linux 环境下 CLI 测试不支持

### step3-0-5：环境问题处理

如果环境检查失败：

**选项 1：用户可解决**
- 提示用户："编译/测试环境未就绪，请先配置"
- 列出需要解决的问题
- 等待用户确认环境就绪后再继续

**选项 2：环境限制**
- 如果项目在 Linux 环境下且 CLI 测试不可用
- 询问用户："是否在 Windows/macOS 环境下进行测试？"
- 或记录为遗留问题

**选项 3：未知项目类型**
- 询问用户使用的构建工具和测试框架
- 记录用户提供的命令
- 根据用户输入执行检查

**重要**：不要跳过环境检查。进入 step3-2（TDD 代码应用）前必须确保环境就绪。

---

## step3-1：确认应用条件

### step3-1-1：检查代码完成状态

确认以下条件已满足：
1. 代码已完成开发
2. 所有 tasks.md 中的任务已完成
3. 代码已按设计文档实现

### step3-1-2：检查代码质量

在应用前，运行以下检查：
1. 代码 lint 检查
2. 语法检查

如果检查未通过，**必须先修复问题**，然后继续。

---

## step3-2：代码应用

### step3-2-1：按照 tasks.md 执行代码生成/修改（TDD 模式）

**约束**：必须使用 `skill('tdd-enforcer')`

按照 tasks.md 中定义的任务顺序，对每个 task 执行 TDD 循环：

```
对每个 task:
  1. RED：根据验收标准写失败测试
  2. 验证测试失败
  3. GREEN：写最小代码使测试通过
  4. 验证测试通过
  5. REFACTOR：重构，保持测试绿色
  6. 进入下一个 task
```

执行顺序仍遵循：
1. 基础设施代码
2. 核心业务逻辑代码
3. UI 表现层代码

### step3-2-2：运行全量测试

所有 task 完成后，运行全量测试确认无回归：

```bash
cd {项目名}-main
hvigorw test@entry
```

### step3-2-2b：HarmonyOS UI 测试（强制）

> 🚧 **Deferred 硬门禁(imperative — 依据 Issue #28 教训)**：任何把 UI 测试 / T21 / UI 自动化任务标记为 `Deferred` / `⏭️` / "延后" / "跳过" 的行为,**必须先完整通过下方 step3-2-2b-降级 的 CHECK-1 ~ CHECK-4**。4 CHECK 未全部 ALL PASS 之前,**绝对禁止**在 `apply-report.md`(含 §测试结果、§HarmonyOS UI 测试、任务状态表 T21 行)写 `Deferred` / `⏭️` / 任何延后措辞,也**绝对禁止**只在报告里标 Deferred 而不创建 `ui-tests/` 目录。只写 Deferred 而未走降级四要素 = rev-01 强制 REQUEST_CHANGES(Issue #28:apply-report T21 标 Deferred 但 ui-tests/ 未建、降级 4 要素全空,双阻塞被打回)。

**触发条件**：项目类型 == HarmonyOS **且** tasks.md 中存在以下任一类型的 task：

- 涉及 `@Builder` / `@Component` / `@Entry` / Page 文件
- 涉及 UI 状态变化（@State / 模式切换 / 路由跳转 / 动画）
- 涉及用户交互（onClick / onTouch / 手势 / 键盘事件）
- 涉及持久化的设置项（@Builder Settings / 偏好开关）

**强制约束**（铁律 7 — 不准用任何形式替代鸿蒙真实环境测试）：

1. **必须**调用 `skill('harmonyos-ui-test')` 在真机或模拟器上执行 UI 自动化测试
2. **不准**用 Node.js vm + .ets transformer 自研 harness 替代（issue#4 曾踩此坑：`tests/loader.mjs` 77/77 PASS 但 0 真机验证）
3. **不准**只做"源代码层断言"（grep 源码 / 正则匹配文件内容）
4. **不准**以"CLI 不可用 / Linux 环境 / 没有 hvigorw"为由跳过 → 必须走 worktree 里的 `opencalc/build_hap.bat`（已设 `DEVECO_SDK_HOME` + `JAVA_HOME` env）
5. **不准**以"UI 任务已在 Task 1.x 单元测试覆盖"为由跳过 — 单元测试 ≠ UI 测试

### step3-2-2b-降级（铁律 7 兜底 — 强制 5 步 + 自检 + 反模式）

**触发条件**（任一满足即必须执行本降级块,缺一不可绕过）:

- `hdc list targets` 返回 Empty（或 `hdc list devices` 无可用设备）
- `hdc tconn <serial>` 失败（连接超时/鉴权失败/serial 不存在）
- `capabilities.json` 的 `ui_test.emulator_status` 字段值与 hdc 实际探测结果冲突（stale）
- 用户/分析层标注 AVD 不可用
- 真机/模拟器截图脚本无设备可连

> ⚠️ **铁律 7 硬门禁(imperative gate)**:在跑完下方「强制自检命令」CHECK-1 ~ CHECK-4 全部 ALL PASS 之前,**绝对禁止**在 `apply-report.md` 写任何"环境受限"/"降级为端口测试"/"AVD 不可用,跳过 UI 测试"/"测试覆盖已在 Task 1.x 完成"等措辞;**绝对禁止**删除已写的「HarmonyOS UI 测试」段模板占位;**绝对禁止**在 apply-report.md 末尾追加 `verdict=PASS`。任一 CHECK FAIL → apply-report.md 必追加 `verdict=REQUEST_CHANGES` 且全流程阻断 git add/commit/push。违者按 masquerade-as-passing 处理(analysis 复审强制升级为 #N+1,参 Issue #25 教训:apply-report §3.1-3.3 走端口测试但 §6 降级 4 要素全缺)。

**强制执行顺序**（严格按下列顺序,不准跳步、并行、合并）:

1. **暂停 apply-report 写入**：在步骤 2-5 全部完成前,**不准**在 `apply-report.md` 的「HarmonyOS UI 测试」段写"环境受限"或任何降级措辞;不准删除已写的模板占位
2. **获取用户书面同意**：在 apply-report.md 或变更会话输出中显式记录 `用户明确书面同意降级 {YYYY-MM-DD HH:MM}` 一行;无用户确认原文则降级路径无效
3. **覆写 todo.md**：在 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/todo.md` 插入 ⏳ 标记条目,**必须同时含**三要素:
   - ⏳ 标记本身（unicode U+23F3）
   - 责任人（dev-01 名字或群组 ID,不准写"待定"）
   - 计划补做时间（**绝对日期**如 2026-07-15,不准写"后续"/"有空再说"/"下次"）
4. **覆写 capabilities.json**：将 `ui_test.emulator_status` 字段从 `running`/`unknown` 改为 `unavailable`;**必须**落盘（apply-report.md 中"自承 stale"但未覆写字段值 = 违规）
5. **apply-report 写入环境受限段**：完成 1-4 后方可写"环境受限,未执行 UI 测试",并显式引用四项证据:
   - 用户书面同意回执（贴原文 + 时间戳）
   - todo.md 含 ⏳ 的行号或 grep 输出
   - capabilities.json `ui_test.emulator_status` 当前值（cat/JQ 输出）
   - hdc list targets / hdc tconn 失败原始输出

**强制自检命令（imperative self-check — 写完 apply-report.md 后,必须逐条执行,任一 FAIL 立即触发 verdict=REQUEST_CHANGES 并封锁 git commit/push）**:

```bash
set -euo pipefail
cd "{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/"

# CHECK-1: 用户书面同意回执
echo "[CHECK-1] 用户书面同意回执:"; \
test -n "$(grep -E '用户明确书面同意降级 [0-9]{4}-[0-9]{2}-[0-9]{2}' apply-report.md)" \
  || { echo "FAIL-1: 缺用户书面同意回执 → verdict=REQUEST_CHANGES + 禁止 git commit/push"; exit 1; }

# CHECK-2: todo.md ⏳ + 责任人 + 绝对日期 三要素
echo "[CHECK-2] todo.md ⏳ + 责任人 + 计划时间:"; \
test -n "$(grep -P '⏳.*责任人.*20[0-9]{2}-[0-9]{2}-[0-9]{2}' todo.md)" \
  || { echo "FAIL-2: todo.md 缺 ⏳+责任人+绝对日期 → verdict=REQUEST_CHANGES + 禁止 git commit/push"; exit 1; }

# CHECK-3: .claude/capabilities.json ui_test.emulator_status='unavailable' 已落盘
echo "[CHECK-3] .claude/capabilities.json ui_test.emulator_status:"; \
test -n "$(grep -E '\"ui_test\":\s*\{[^}]*\"emulator_status\"\s*:\s*\"unavailable\"' .claude/capabilities.json)" \
  || { echo "FAIL-3: capabilities.json ui_test.emulator_status 未覆写 → verdict=REQUEST_CHANGES + 禁止 git commit/push"; exit 1; }

# CHECK-4: apply-report.md 引用 hdc list targets / hdc tconn 原始输出
echo "[CHECK-4] hdc 失败原始输出:"; \
test -n "$(grep -E 'hdc (list targets|tconn)' apply-report.md)" \
  || { echo "FAIL-4: apply-report.md 缺 hdc 探测原始输出 → verdict=REQUEST_CHANGES + 禁止 git commit/push"; exit 1; }

echo "ALL PASS: 降级路径四要素齐备 → verdict=PASS,允许 git commit/push"
```

**自动 verdict 与 commit/push 闸门（imperative）**:

- 上述 4 条 CHECK 必须**在 apply-report.md 写完后、git commit/push 前**顺序执行
- 任一 CHECK 退出码 ≠ 0（FAIL-N）→ **强制**在 apply-report.md 末尾追加 `## verdict\nREQUEST_CHANGES\n- ❌ step3-2-2b-降级 强制自检未通过 (FAIL-N: <错误原因>)` 段,并**绝对禁止**任何 `git add` / `git commit` / `git push` 操作（仅允许修复后重跑自检）
- 全部 CHECK 通过 → 在 apply-report.md 追加 `## verdict\nPASS` 后方可进入「Git Commit & Push」步骤
- **绝对禁止**绕过自检（不退避、不跳过、不手动覆盖 verdict）;analysis 层复审见 masquerade-as-passing（自检未跑但 verdict=PASS）→ 复审强制 REQUEST_CHANGES 并升级为 analysis #N+1

**反模式示例（禁止复刻）**:

```markdown
# ❌ apply-report.md:58-83 — issue#29 错例（仅"诚实标注"但未走降级四要素）
> hdc list targets=Empty,hdc tconn 失败,AVD 不存在。
> 请 dev-01 / 人类协助处理。
# 缺：用户书面同意 + todo.md ⏳ + 责任人 + 时间 + capabilities.json 覆写

# ❌ "环境受限,下次补做" + 空 todo.md
# ❌ "AVD 不可用,跳过 UI 测试"（无 hdc 原始输出引用）
# ❌ "测试覆盖已在 Task 1.x 完成"（单元测试 ≠ UI 测试）
# ❌ capabilities.json 自承 stale 但字段值未改
```

**自检失败时的最小修复路径**:

1. FAIL-1 → 在 apply-report.md 增加 `> 用户明确书面同意降级 {YYYY-MM-DD HH:MM}` 一行,或回到 step3-2 重新询问用户
2. FAIL-2 → 在 todo.md 插入形如 `- ⏳ [责任人 dev-01] 补做 harmonyos-ui-test,截止 2026-07-15` 的条目
3. FAIL-3 → 执行 `jq '.ui_test.emulator_status="unavailable"' .claude/capabilities.json > tmp && mv tmp .claude/capabilities.json` 落盘
4. FAIL-4 → 在 apply-report.md「HarmonyOS UI 测试」段粘贴 `hdc list targets` / `hdc tconn <serial>` 的原始 stdout/stderr 输出 + 失败原因

**产物**：

- `ai_auto_test/{YYYY-MM-DD_HHmm}_{account_type}/03_测试报告.md`
- 真机/模拟器 PASS/BUG 数（必须为整数，不能写"未测"）
- 至少 1 张截图嵌入作为 evidence

### step3-2-3：执行 lint 检查

执行代码 lint 检查：

```bash
cd {项目名}-main
hvigorw lint
```

### step3-2-4：执行集成测试（如有）

如果有集成测试，执行集成测试验证各模块协作正常。

---

## step3-3：更新任务状态

更新 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/todo.md`：
- 标记所有完成的任务
- 记录测试结果
- 记录 lint 检查结果
- 标记 APPLYING 阶段完成

---

## step3-4：产出应用报告

在 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/apply-report.md` 中输出应用报告：

**参考模板**：`aid-applying/templates/apply-report-template.md`

### apply-report.md 结构

```markdown
# 应用报告

## 应用信息
- 变更类型：{类型}
- 变更名称：{名称}
- 关联特性：feat-{特性}
- 应用日期：{YYYY-MM-DD}

## 代码完成情况
| 任务 | 状态 | 完成时间 |
|------|------|----------|
| Task 1.1 | ✅ 完成 | {日期} |
| Task 1.2 | ✅ 完成 | {日期} |
| Task 2.1 | ✅ 完成 | {日期} |

## 测试结果
- 单元测试：{通过/未通过}
- 集成测试：{通过/未通过（如有）}
- Lint 检查：{通过/未通过}

## HarmonyOS UI 测试（若适用）
- UI 测试状态：[✅ 已执行 / ⏭️ Deferred]（**若标 ⏭️ Deferred:必须已通过 step3-2-2b-降级 CHECK-1~4 且 `ui-tests/` 目录已建,否则 rev-01 判 REQUEST_CHANGES,参 Issue #28**）
- `skill('harmonyos-ui-test')` 是否调用：[✅/❌]
- 测试报告路径：`ai_auto_test/{YYYY-MM-DD_HHmm}_{account_type}/03_测试报告.md`
- 真机/模拟器 PASS 数：{n}
- 真机/模拟器 BUG 数：{n}
- 截图 evidence：[链接] 或 N/A（若未调用则此行必填 N/A，并移至下方「风险与遗留问题」详述原因）

## 测试详情
### 单元测试
{测试结果详情}

### Lint 检查
{检查结果详情}

## 下一步
测试通过后，执行归档操作：
执行 aid-archiving {类型}-{名称}
```

---

## APPLYING 阶段完成

**完成条件**：代码通过单元测试和 lint 检查

**完成动作**：
1. 更新 apply-report.md 测试结果
2. 更新 `{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/todo.md` 状态（标记 APPLYING 完成）

**用户确认**：

```
## APPLYING 阶段完成

**产出物位置**：`{CHANGES_ROOT}/{YYYYMMDD}-{类型}-{名称}/apply-report.md`

**测试结果**：
- 单元测试：{通过/未通过}
- 集成测试：{通过/未通过（如有）}
- Lint 检查：{通过/未通过}

**代码完成情况**：
- Task 1.1: ✅ 完成
- Task 1.2: ✅ 完成
- Task 2.1: ✅ 完成

**请确认**：
- 代码应用和测试结果是否符合您的预期？
- 是否需要处理问题？

选项：
1. 接受，继续下一阶段
2. 处理问题（请说明需要处理的内容）
```

### 处理用户反馈

如果用户在确认时反馈问题：
1. 暂停继续执行
2. 听取并记录用户反馈的问题
3. 定位并修复问题
4. 重新运行测试验证
5. 更新 apply-report.md
6. 重新展示测试结果
7. 再次等待用户确认
8. 用户接受后继续执行下一阶段

**提示用户**：测试通过，可以进入achieving阶段进行归档


---

## 附录

### Skill 模板文件

模板文件位于 `aid-applying/templates/` 目录：

| 模板文件 | 用途 |
|----------|------|
| `apply-report-template.md` | 应用报告模板 |
| `todo-template.md` | 任务进度模板 |

### 构建/测试命令

在 `{项目名}-main/` 目录下执行：

```bash
# 构建
hvigorw assembleHap

# 测试
hvigorw test@entry

# Lint 检查
hvigorw lint
```

---

## Git Commit & Push（推荐）

当所有测试通过且 apply-report.md 已生成：

1. 向用户推荐：「建议提交并推送本次变更到远程分支，是否执行？」
2. 用户接受 → 执行：
   ```bash
   git add -A
   git commit -s -m "feat({name}): apply changes from aid-workflow"  # ⚠️ **必 -s/--signoff**（铁律,缺 Signed-off-by 则 rev-01 判 REQUEST_CHANGES,参 Issue #25/#28 教训）
   # ⚠️ 铁律:push 前必须自检 **HEAD 实体 commit** 含 Signed-off-by,否则 exit 1 阻断 push
   # （查 HEAD 而非 .git/COMMIT_EDITMSG:Issue #28 fcf60fad `git commit --amend --signoff` 未生效,b86f7c7 HEAD 仍无 trailer,但 COMMIT_EDITMSG 会误报 PASS）
   git log -1 --format=%B | grep -qE "^Signed-off-by:" || { echo "❌ FAIL: HEAD commit 缺 Signed-off-by → 执行 git commit --amend --signoff --no-edit 后重跑本自检确认生效"; exit 1; }
   git push -u origin $(git branch --show-current)
   ```
3. 用户拒绝 → 跳过

**约束**：
- 仅在 `git_branch_adopted: true`（step1.5 中用户接受了分支推荐）时触发此推荐
- 如果用户在 main 分支上工作，不推荐此步骤

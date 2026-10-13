# Issue #13 一键分享二维码 — 开发任务

## 任务概述

- 功能名称：一键分享二维码
- 变更类型：requirement-add
- 关联特性：feat-qrcode-share
- 开发阶段：IMPLEMENTING
- 预计任务数：9
- TDD 策略：RED → GREEN → REFACTOR（与项目铁律 7 一致）

## 任务列表

### 阶段 1：基础设施（纯函数工具类）

#### Task 1.1: RED — 写 QrCodeBuilder.test.ets 失败测试
**描述**：在 `opencalc/entry/src/test/ets/qrcode/QrCodeBuilder.test.ets` 中编写 10 个失败用例（TC-01 ~ TC-10），覆盖基本格式、特殊字符（π/+//）、空值、超长截断、UTF-8 编码、常量类型等。
**涉及文件**：
- `opencalc/entry/src/test/ets/qrcode/QrCodeBuilder.test.ets`（新增）
**依赖任务**：无
**验收标准**：
- [ ] 文件存在，包含 10 个 `it(...)` 测试用例
- [ ] 全部用例在缺实现时抛 `SyntaxError: Cannot find name 'QrCodeBuilder'` 或类似
- [ ] 命名规范与项目内 `HistoryFilter.test.ets` 对齐
**TDD**：[x] RED

#### Task 1.2: GREEN — 实现 QrCodeBuilder.ets
**描述**：在 `opencalc/entry/src/main/ets/qrcode/QrCodeBuilder.ets` 中实现 `buildSharePayload` 纯函数 + 4 个常量 + 命名空间导出，让 Task 1.1 的全部测试通过。
**涉及文件**：
- `opencalc/entry/src/main/ets/qrcode/QrCodeBuilder.ets`（新增）
**依赖任务**：Task 1.1
**验收标准**：
- [ ] 导出 `buildSharePayload(expr, res): string`、`MAX_PAYLOAD_LENGTH=200`、`PAYLOAD_PREFIX`、`RESULT_PREFIX`、`TRUNCATED_FLAG`、`QrCodeBuilder` 命名空间
- [ ] URL 编码用标准 `encodeURIComponent`
- [ ] 超长截断逻辑保留 result 优先
- [ ] Task 1.1 全部测试通过
**TDD**：[x] GREEN

#### Task 1.3: REFACTOR — QrCodeBuilder 内部清理
**描述**：清理 QrCodeBuilder.ets 的局部变量命名；将 magic number 提取为命名常量；确保纯函数无副作用。
**涉及文件**：
- `opencalc/entry/src/main/ets/qrcode/QrCodeBuilder.ets`
**依赖任务**：Task 1.2
**验收标准**：
- [ ] 测试仍 100% 通过
- [ ] 函数体 ≤ 25 行（可读性）
- [ ] 无未使用 import
**TDD**：[ ] REFACTOR

### 阶段 2：CalculatorPage 集成（State + 方法）

#### Task 2.1: RED — onShareClick 行为测试（合约测试）
**描述**：通过在 CalculatorPage 内添加 `// @ts-ignore` 临时桩，写 onShareClick 单元测试覆盖：启用条件校验、空表达式拒绝、有错误拒绝、无结果拒绝。
**说明**：CalculatorPage 是 ArkTS @Component，难以独立单测。本任务通过"合约级断言"记录行为预期，在 Task 2.2 实现后由 INTEGRATION 测试验证。
**涉及文件**：
- `opencalc/entry/src/test/ets/pages/CalculatorPage.share.test.ets`（新增）
**依赖任务**：Task 1.2
**验收标准**：
- [ ] 存在合约测试桩（如 `// CONTRACT: onShareClick requires expression.length>0 && errorMsg.length===0 && result.length>0`）
- [ ] 测试文件存在并描述行为预期
**TDD**：[x] RED (合约级)

#### Task 2.2: GREEN — CalculatorPage 集成 onShareClick / onShareClose / isShareEnabled
**描述**：在 CalculatorPage.ets 中：
1. 新增 `@State showShare: boolean = false`
2. 新增 `@State qrImage: PixelMap | null = null`
3. 新增 `isShareEnabled` getter（expression+errorMsg+result 三重校验）
4. 新增 `onShareClick()`：异步调用 `qrcode.createQrCode` 生成 QR，弹出模态
5. 新增 `onShareClose()`：release PixelMap + 关闭模态
6. 新增 import `qrcode`, `image`, `QrCodeBuilder`
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
**依赖任务**：Task 2.1
**验收标准**：
- [ ] 文件可编译（无 ArkTS 类型错误）
- [ ] 新增 import 路径正确（`../qrcode/QrCodeBuilder`、`@kit.QRCodeKit`、`@kit.ImageKit`）
- [ ] isShareEnabled getter 逻辑符合合约
**TDD**：[x] GREEN

#### Task 2.3: REFACTOR — 提取 onShareClick 内部逻辑到私有方法
**描述**：把 onShareClick 中的 payload 生成、QR 异步生成、错误处理分别拆为 `buildQrPayload()` / `generateQrImage(payload)` / `showQrErrorToast()` 私有方法。
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 2.2
**验收标准**：
- [ ] onShareClick 函数体 ≤ 15 行
- [ ] 行为不变
**TDD**：[ ] REFACTOR

### 阶段 3：UI 集成（按钮 + 模态层）

#### Task 3.1: DisplayPanel 顶部新增分享按钮
**描述**：在 DisplayPanel 的 expression 行**上方**增加 Row：左 Blank + 右"⎘"分享按钮，使用 isShareEnabled 控制可用性。
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 2.2
**验收标准**：
- [ ] 按钮位置正确（expression 上方，右对齐）
- [ ] disabled 状态下 fontColor 变灰、.enabled(false) 拦截点击
- [ ] 不影响长按显示屏手势（仍触发 onCopy）
**TDD**：N/A（纯 UI）

#### Task 3.2: 新增 SharePanel builder
**描述**：在 CalculatorPage.ets 中新增 `@Builder SharePanel()`，结构：
- 标题栏（"二维码分享" + ✕）
- QR 码 Image（240x240，强制白底）
- 文本副本（expression + " = " + result）
- 截断提示（payload 含 &truncated=1 时显示）
- 操作提示
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.1
**验收标准**：
- [ ] builder 存在，结构与 design §2.2 一致
- [ ] onShareClose 正确绑定到 ✕ 按钮
- [ ] QR 区域 backgroundColor='#FFFFFF'（不受主题影响）
**TDD**：N/A（纯 UI）

#### Task 3.3: build() Stack 中添加 SharePanel 条件渲染
**描述**：在 CalculatorPage.build() 的 Stack 中添加 `if (this.showShare) this.SharePanel()`。
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
**依赖任务**：Task 3.2
**验收标准**：
- [ ] Stack 中存在 SharePanel 渲染分支
- [ ] 不影响 SettingsPanel / AboutPanel 的现有渲染
**TDD**：N/A

### 阶段 4：构建验证 + 集成测试

#### Task 5.1: hvigorw 编译验证
**描述**：在 opencalc/ 目录下执行 `hvigorw --no-daemon assembleHap`，确保代码可编译通过。
**涉及文件**：`opencalc/` 全项目
**依赖任务**：Task 3.3
**验收标准**：
- [ ] 编译无错误（warnings 可接受）
- [ ] 输出 HAP 文件存在
**TDD**：N/A

#### Task 5.2: hvigorw test 单测全跑
**描述**：在 opencalc/ 目录下执行 `hvigorw --no-daemon test`，确认 QrCodeBuilder 单元测试 10 个全部通过 + 不破坏现有测试。
**涉及文件**：测试运行输出
**依赖任务**：Task 5.1
**验收标准**：
- [ ] 10 个 QrCodeBuilder 测试全 pass
- [ ] 现有 Expression.test.ets 测试仍 pass
- [ ] 测试报告 100% 通过
**TDD**：N/A

#### Task 5.3: UI 自动化测试（capabilities.json 显示 ui_test.available=true）
**描述**：使用 hdc + harmonyos-ui-test skill 在模拟器（127.0.0.1:5555）上执行 AC-01 ~ AC-08 验证。
**涉及文件**：
- 测试脚本：`specs/changes/20260615-requirement-add-qrcode-share/ui-tests/run_tests.py`
- 截图：`specs/changes/20260615-requirement-add-qrcode-share/ui-tests/screenshot/`
- 结果：`specs/changes/20260615-requirement-add-qrcode-share/ui-tests/results.json`
- 解析工具：`specs/changes/20260615-requirement-add-qrcode-share/ui-tests/parse_ui.py`
**依赖任务**：Task 5.2
**验收标准**：
- [ ] hdc list targets 有输出（设备连接）
- [ ] 应用已安装到模拟器
- [ ] 应用已启动（aa start 成功）
- [ ] 所有 AC 通过 dump UI 树 + 截图验证
- [ ] screenshot/ 目录包含每步操作截图
- [ ] results.json 包含每个 AC 的 pass/fail/skip 状态
**TDD**：[x] RED / [x] GREEN / [ ] REFACTOR
**禁止**：标为 ⏭️ Deferred 或"手动"

### 阶段 5：APPLYING 收尾

#### Task 6.1: 写 apply-report.md
**描述**：在 `specs/changes/20260615-requirement-add-qrcode-share/apply-report.md` 中产出应用报告，含：
- 完成情况（任务清单 ✓/✗）
- 测试结果（10 个单元测试 + UI 自动化结果）
- 改动文件清单
- 已知限制 / 后续优化
**涉及文件**：
- `specs/changes/20260615-requirement-add-qrcode-share/apply-report.md`
**依赖任务**：Task 5.3
**验收标准**：
- [ ] apply-report.md 存在且结构完整
**TDD**：N/A

#### Task 6.2: 更新 todo.md 状态
**描述**：把 todo.md 的阶段状态全部更新为 ✅ DONE。
**涉及文件**：
- `specs/changes/20260615-requirement-add-qrcode-share/todo.md`
**依赖任务**：Task 6.1
**验收标准**：
- [ ] todo.md 中 PLANNING/IMPLEMENTING/APPLYING 全为 ✅
**TDD**：N/A

## 开发顺序

```
Task 1.1 (RED)
   ↓
Task 1.2 (GREEN)
   ↓
Task 1.3 (REFACTOR)
   ↓
Task 2.1 (RED-合约)
   ↓
Task 2.2 (GREEN)
   ↓
Task 2.3 (REFACTOR)
   ↓
Task 3.1 (DisplayPanel 按钮)
   ↓
Task 3.2 (SharePanel builder)
   ↓
Task 3.3 (Stack 条件渲染)
   ↓
Task 5.1 (hvigorw 编译)
   ↓
Task 5.2 (hvigorw test)
   ↓
Task 5.3 (UI 自动化测试)
   ↓
Task 6.1 (apply-report.md)
   ↓
Task 6.2 (更新 todo.md)
```

## 验收计划

| 任务 | 验收方式 | 验收时间 |
|------|---------|----------|
| Task 1.1 | 单元测试运行失败（预期） | RED 阶段 |
| Task 1.2 | 单元测试 10/10 通过 | GREEN 阶段 |
| Task 1.3 | 单元测试仍 10/10 通过 | REFACTOR 阶段 |
| Task 2.1 | 合约测试桩存在 | RED 阶段 |
| Task 2.2 | hvigorw 编译通过 | GREEN 阶段 |
| Task 2.3 | 编译通过 + 行为不变 | REFACTOR 阶段 |
| Task 3.1 | 视觉检查（UI 测试） | UI 阶段 |
| Task 3.2 | 视觉检查（UI 测试） | UI 阶段 |
| Task 3.3 | 视觉检查（UI 测试） | UI 阶段 |
| Task 5.1 | hvigorw assembleHap 成功 | 构建阶段 |
| Task 5.2 | hvigorw test 全 pass | 测试阶段 |
| Task 5.3 | UI 自动化 8/8 AC 通过 | UI 测试 |
| Task 6.1 | apply-report.md 完整 | 收尾 |
| Task 6.2 | todo.md 全 ✅ | 收尾 |

## IMPLEMENTING 阶段完成

**产出物位置**：`specs/changes/20260615-requirement-add-qrcode-share/tasks.md`

**任务列表**：13 个任务（3 + 3 + 3 + 4）
- 阶段 1: Task 1.1/1.2/1.3 — QrCodeBuilder TDD
- 阶段 2: Task 2.1/2.2/2.3 — CalculatorPage 集成 TDD
- 阶段 3: Task 3.1/3.2/3.3 — UI 集成
- 阶段 4: Task 5.1/5.2/5.3 — 构建 + 单测 + UI 自动化
- 阶段 5: Task 6.1/6.2 — APPLYING 收尾

**开发顺序**：Task 1.1 → 1.2 → 1.3 → 2.1 → 2.2 → 2.3 → 3.1 → 3.2 → 3.3 → 5.1 → 5.2 → 5.3 → 6.1 → 6.2

**自动接受**（方案 C）：claude -p 全自动模式，跳过用户确认，直接进入 APPLYING 阶段。

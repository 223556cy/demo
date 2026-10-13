# 开发任务 — Issue #17 粘贴即计算

## 任务概述

- **功能名称**：粘贴即计算（paste-and-calculate）
- **变更类型**：requirement-add
- **预计任务数**：5 大任务（含 13 子任务）
- **预计工时**：3-4 小时
- **目标代码量**：~60 行生产代码 + ~150 行测试代码

## 任务依赖图

```
T1 (CalculatorPage 集成: lastPastedHash + onPaste + onPageShow + computeHash)
    │
    ├─► T2 (ToggleRow 新增按钮)
    │
    ▼
T3 (Node mock 端到端测试)
    │
    ▼
T4 (hvigorw 真实跑测 — 可选)
    │
    ▼
T5 (UI 自动化 — harmonyos-ui-test)
```

## 任务列表

### 阶段 1：核心功能（CalculatorPage 集成）

#### Task 1.1: CalculatorPage 新增 lastPastedHash + onPaste + onPageShow + computeHash
**描述**：在 CalculatorPage.ets 中实现所有新增字段和方法
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改，新增约 60 行）
**依赖任务**：无
**验收标准**：
- [ ] 新增 `@State lastPastedHash: number = 0`
- [ ] 新增 `onPageShow(): void`（aboutToAppear 之后）
- [ ] 新增 `onPaste(): void`（onCopy 之后）
- [ ] 新增 `computeHash(text: string): number`（私有方法）
- [ ] onPaste 内部 trim + 截断 + hash 比对 + 校验 + 提交
- [ ] onPaste 失败时 `promptAction.showToast({ message: '非数学表达式', duration: 1500 })`
- [ ] onPaste 成功时 `this.expression = text; this.onEquals()`
- [ ] 不修改 computePreview / onEquals / onCopy 任何既有逻辑
- [ ] 不删除任何现有功能
**TDD**：✅ GREEN（无独立单测，靠 T3 Node mock 验证）
**预计时间**：30 分钟
**验证标准**：现有 5/5 (Expression.test.ets) 不回归 + T3 Node mock 全 PASS

#### Task 1.2: CalculatorPage 集成测试 (Node mock)
**描述**：在 specs/changes/.../tests/ 写 Node 端 mock 测试，模拟完整粘贴流程
**涉及文件**：
- `specs/changes/20260617-requirement-add-paste-and-calculate/tests/PasteAndCalculate.test.mjs`（新建）
**依赖任务**：T1.1
**验收标准**：
- [ ] 模拟 pasteboard.getData() 返回 `2+3` → 验证 expression='2+3', result=5
- [ ] 模拟 `Hello` → 验证 toast
- [ ] 模拟重复粘贴 → 验证去重
- [ ] 模拟空白 → 验证 early return
- [ ] 模拟超长 500 字符 → 验证截断到 200
- [ ] 测试通过率 100%
**TDD**：✅ GREEN
**预计时间**：25 分钟
**验证标准**：`node PasteAndCalculate.test.mjs` 输出 6/6 PASS

### 阶段 2：UI 表现层

#### Task 2.1: ToggleRow 新增「📋粘贴」按钮
**描述**：在工具栏添加粘贴按钮，调用 onPaste
**涉及文件**：
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改 ToggleRow @Builder）
**依赖任务**：T1.1
**验收标准**：
- [ ] 位置：「科学/基础」按钮与「▼历史」之间
- [ ] 文字：`📋`（emoji）
- [ ] 样式：12pt + getT2() + 8px padding（与「▼历史」一致）
- [ ] onClick 调用 `this.onPaste()`
- [ ] 不影响 ToggleRow 内其他按钮布局
- [ ] 不影响横屏布局（ToggleRow 在横屏被裁切，已是既有行为）
**TDD**：✅ GREEN（无单测，靠人工/UI 自动化验证）
**预计时间**：10 分钟
**验证标准**：UI 截图显示新按钮存在 + 点击不报错

### 阶段 3：测试验证

#### Task 3.1: Node mock 端到端验证
**描述**：在 specs/changes/.../tests/ 写 Node 端 mock 测试
**涉及文件**：
- `specs/changes/20260617-requirement-add-paste-and-calculate/tests/PasteAndCalculate.test.mjs`（新建）
**依赖任务**：T1.1, T2.1
**验收标准**：
- [ ] 6 个测试场景全 PASS
- [ ] 输出 PASS/FAIL 报告
**TDD**：✅ GREEN
**预计时间**：25 分钟
**验证标准**：`node PasteAndCalculate.test.mjs` 6/6 PASS

#### Task 3.2: 真实 hvigorw 跑测（如果环境允许）
**描述**：在 hvigorw 可用的环境真实跑 hypium 测试
**涉及文件**：无新增
**依赖任务**：T3.1
**验收标准**：
- [ ] 尝试 `hvigorw --no-daemon test`（绝对路径）
- [ ] 如果失败，fallback 到 `node` 跑 mock 测试
- [ ] 把结果记录到 apply-report.md
**TDD**：N/A（验证）
**预计时间**：15 分钟
**验证标准**：测试结果记录到 apply-report.md

### 阶段 4：UI 自动化（基于 capabilities.json ui_test.available=true）

#### Task 4.1: UI 自动化脚本编写
**描述**：用 Python + hdc + harmonyos-ui-test 编写 UI 自动化测试
**涉及文件**：
- `specs/changes/20260617-requirement-add-paste-and-calculate/ui-tests/run_paste_tests.py`（新建）
- `specs/changes/20260617-requirement-add-paste-and-calculate/ui-tests/parse_ui.py`（新建）
**依赖任务**：T2.1
**验收标准**：
- [ ] 脚本可以：启动 App → 模拟粘贴 `2+3` → 截图 → 验证 result=5
- [ ] 至少覆盖 3 个场景：basic paste、invalid paste、duplicate paste
- [ ] 截图存档到 `screenshot/` 目录
- [ ] 结果写入 `results.json`
**TDD**：✅ GREEN
**预计时间**：40 分钟
**验证标准**：脚本能跑（如果环境允许真跑）

#### Task 4.2: UI 自动化真跑验证
**描述**：在模拟器 127.0.0.1:5555 上真实执行自动化脚本
**涉及文件**：无新增
**依赖任务**：T4.1
**验收标准**：
- [ ] hdc list targets 显示模拟器
- [ ] 应用安装成功
- [ ] 至少 3 个场景 PASS
- [ ] 截图存档
**TDD**：N/A（验证）
**预计时间**：20 分钟
**验证标准**：results.json 记录 3/3 PASS

## 开发顺序

```
T1.1 (CalculatorPage 集成)
  └─► T2.1 (ToggleRow 按钮)
        └─► T3.1 (Node mock 测试)
              └─► T3.2 (真实跑测 — 可选)
                    └─► T4.1 (UI 自动化脚本)
                          └─► T4.2 (UI 自动化真跑)
```

## 验收计划

| 任务 | 验收方式 | 工具 | 备注 |
|------|---------|------|------|
| T1.1 | 代码审查 + Node mock | 人工 + node | 现有 5 个测试不回归 |
| T2.1 | 代码审查 | 人工 | UI 样式 |
| T3.1 | Node mock PASS | node test.mjs | 6/6 PASS |
| T3.2 | 真实跑测 | hvigorw test | 结果记录 |
| T4.1 | 脚本语法检查 | python -m py_compile | 语法 OK |
| T4.2 | 真实 UI 跑测 | python run_paste_tests.py | 截图存档 |

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| T1.1 测试需 mock pasteboard Kit | 用 Node mock 模拟系统调用 |
| T3.2 hvigorw 真实跑可能失败 | fallback 到 Node mock |
| ArkTS 类型严格（无 any） | 用 `(s as string).charCodeAt(i)` 显式断言 |
| onPaste 内部 try/catch 嵌套 | 已抽到 computePreview 内置 try/catch |

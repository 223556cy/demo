# 百分号按钮功能 - 开发任务

> 变更 ID: 20260612-requirement-add-percent-button
> 阶段: IMPLEMENTING
> 生成时间: 2026-06-12
> 关联文档: `proposal.md` · `delta-spec.md` · `info.md` · `delta-design.md` · `design-review.md`

## 任务概述

- **功能名称**：百分号按钮（Percent Button）
- **变更类型**：新增功能（New Requirement）
- **关联特性**：feat-percent-button
- **开发阶段**：在已提交实现基础上增量补齐
- **预计任务数**：9 个任务
- **关键发现**：已提交代码（commit 59218f0）已实现 % 核心功能，本次需增量补齐 3 个边缘场景 + 完整测试覆盖

## 上下文

### 已实现（无需重做）
- ✅ `Expression.getPercentString` - Windows 风格 % 语义解析（`Expression.ets:169-260`）
- ✅ `CalculatorPage.ButtonGrid` 第 1 行第 2 列 `%` 按钮
- ✅ `BtnOpPct` 模板（5列布局）
- ✅ `Issue #9` 操作符优先级修复（已含括号保护）

### 需增量补齐（3 个边缘场景）
- 🆕 **重复 % 错误检测**（`50%%` → Error）
- 🆕 **函数内 % 错误检测**（`sin(30%)` → Error）
- 🆕 **错误状态清错**（Error + % → 清错注入新表达式）

### 需测试覆盖
- 8 个 AC（详见 delta-spec.md SR 列表）
- 注意：worktree 中 `Expression.test.ets` 已有未提交变更，需合并而非重写

---

## 任务列表

### 阶段 1：差异分析（Foundation）

#### Task 1.1: 对比设计与已提交实现
**描述**：阅读已提交的 `Expression.ets` 和 `CalculatorPage.ets`，对比本次 `delta-design.md` 中的设计，识别以下内容：
1. 已提交实现与本次设计**完全一致**的功能（无需修改）
2. 本次设计**新增**的边缘场景（需补齐）
3. 本次设计**修改**的逻辑（如有）
4. 任何**冲突**或不兼容点

**涉及文件**：
- 读：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/main/ets/calculator/Expression.ets`
- 读：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/main/ets/pages/CalculatorPage.ets`
- 写：`D:/huawei/Demo/specs/changes/20260612-requirement-add-percent-button/diff-analysis.md`

**依赖任务**：无
**验收标准**：
- diff-analysis.md 包含 4 个章节：已实现 / 需新增 / 需修改 / 冲突
- 每个差异点标注"对应 SR 编号"
- 列出 worktree 中 `Expression.test.ets` 已有的测试用例（从 git diff 可见）

**TDD**：不适用（此任务为分析任务）

---

### 阶段 2：测试先行（RED）- 写失败的测试

#### Task 2.1: 添加 8 个 AC 测试用例（核心语义）
**描述**：在 `Expression.test.ets` 中添加或补齐 8 个 AC 测试用例：
- AC-001-01: 加法 `50+10%` → `(50)+(50)*(10/100)`
- AC-001-02: 减法 `200-15%` → `(200)-(200)*(15/100)`
- AC-001-03: 乘法 `8×5%` → `8*(5/100)` 或 `8*5/100`
- AC-001-04: 除法 `100÷10%` → `100/(10/100)` 或 `100/10/100`
- AC-001-05: 负数 `-50+10%` → `(-50)+(-50)*(10/100)`
- AC-001-06: 连续运算（端到端，可能在 `onEquals` 层级测试）
- AC-001-07: 错误恢复（端到端，可能在 `onOp` 层级测试）

**注意**：先检查 worktree 中 `Expression.test.ets` 的未提交内容，**合并而非覆盖**。

**涉及文件**：
- 写：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/test/ets/calculator/Expression.test.ets`

**依赖任务**：Task 1.1
**验收标准**：
- 至少 5 个核心 % AC 用例在 `Expression.test.ets` 中（AC-001-01~05）
- 端到端测试（AC-001-06, 09）可放在集成测试层
- 单元测试运行后，AC-001-07（重复 %）和 AC-001-08（函数内 %）**失败**（RED 阶段）

**TDD**：[x] RED

---

#### Task 2.2: 添加错误恢复测试（端到端）
**描述**：添加测试验证"错误状态下按 % 自动清错"的行为。这可能需要 mock `ErrorFlags` 或在 `CalculatorPage` 层级测试。

**涉及文件**：
- 写：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/test/ets/calculator/Expression.test.ets`
- 或新建：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/test/ets/pages/CalculatorPage.test.ets`（如需）

**依赖任务**：Task 2.1
**验收标准**：
- 触发除零后调用 `onOp('%')`，`ErrorFlags.reset()` 被调用
- `expression` 不包含残留错误字符

**TDD**：[x] RED

---

### 阶段 3：实现（GREEN）- 让测试通过

#### Task 3.1: 在 `Expression.getCleanExpression` 入口添加重复 % 检测
**描述**：在 `getCleanExpression` 方法的入口（line 8-9 之间）添加 `indexOf('%%')` 检测，若发现连续 `%` 则置 `ErrorFlags.syntax_error = true` 并提前返回。

**代码位置**：`Expression.ets:8-23`

**伪代码**：
```typescript
getCleanExpression(calculation, decimalSep, groupingSep): string {
  if (calculation.indexOf('%%') !== -1) {
    ErrorFlags.syntax_error = true
    return calculation  // 提前返回，不继续解析
  }
  // ... 原有逻辑
}
```

**涉及文件**：
- 改：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/main/ets/calculator/Expression.ets`

**依赖任务**：Task 2.1
**验收标准**：
- AC-001-08 `50%%` 测试通过
- 不影响 AC-001-01~06 已通过的测试
- 保持 `Issue #9` 操作符优先级修复

**TDD**：[x] GREEN

---

#### Task 3.2: 在 `Expression.getPercentString` 中添加函数内 % 检测
**描述**：在 `getPercentString` 方法（line 169-260）的 `%` 处理分支中，添加 `parenthesisLevel > 0` 的检测。若 % 出现在函数括号内（如 `sin(30%)`），置 `ErrorFlags.syntax_error = true` 并返回。

**代码位置**：`Expression.ets:198-256`

**伪代码**：
```typescript
} else if (ch === '%') {
  if (parenthesisLevel > 0) {
    ErrorFlags.syntax_error = true
    return result
  }
  if (parenthesisLevel === 0 && !done[i]) {
    // ... 原有逻辑
  }
}
```

**涉及文件**：
- 改：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/main/ets/calculator/Expression.ets`

**依赖任务**：Task 3.1
**验收标准**：
- AC-001-07 函数内 % 错误测试通过
- 不影响其他 % 场景
- 不影响嵌套括号表达式中的合法 % 转换

**TDD**：[x] GREEN

---

#### Task 3.3: 在 `CalculatorPage.onOp` 中添加错误状态清错
**描述**：修改 `onOp` 方法（line 71），在追加运算符前检测 `ErrorFlags` 状态，若有任一错误标志位为 true，则调用 `ErrorFlags.reset()` 并清空 `expression` 和 `errorMsg`。

**代码位置**：`CalculatorPage.ets:71`

**伪代码**：
```typescript
onOp(op: string): void {
  // 本次新增：错误状态恢复
  if (ErrorFlags.syntax_error || ErrorFlags.division_by_0 ||
      ErrorFlags.domain_error || ErrorFlags.is_infinity ||
      ErrorFlags.require_real_number) {
    ErrorFlags.reset()
    this.errorMsg = ''
    this.expression = ''
  }
  this.expression = this.expression + op
  this.errorMsg = ''
}
```

**涉及文件**：
- 改：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/main/ets/pages/CalculatorPage.ets`

**依赖任务**：Task 3.2
**验收标准**：
- AC-001-09 错误恢复测试通过
- 不影响 `onOp` 其他运算符（`+`、`-`、`×`、`÷`）的正常行为
- [推断] 需用户确认：清空 `expression` vs 保留 `expression`

**TDD**：[x] GREEN

---

### 阶段 4：重构（REFACTOR）

#### Task 4.1: 重构 `getPercentString` 提取共用逻辑
**描述**：检查 `getPercentString` 中是否有可提取的共用逻辑（如括号配对扫描、`subExpr` 提取）。如无明显重复，可跳过此任务。

**代码位置**：`Expression.ets:169-260`

**涉及文件**：
- 改：`D:/huawei/Demo/worktrees/issue-9/opencalc/entry/src/main/ets/calculator/Expression.ets`

**依赖任务**：Task 3.3
**验收标准**：
- 所有 AC 仍通过
- 代码重复消除（如有）
- 函数长度不超过 100 行（当前约 90 行）

**TDD**：[x] REFACTOR

---

### 阶段 5：验证（Verification）

#### Task 5.1: 编译验证
**描述**：使用 hvigorw 编译项目，确保所有变更可成功编译。

**执行命令**：
```powershell
Set-Location 'D:\huawei\Demo\worktrees\issue-9\opencalc'
$env:DEVECO_SDK_HOME='D:\Program Files\Huawei\DevEco Studio\sdk'
$env:JAVA_HOME='D:\Program Files\Huawei\DevEco Studio\jbr'
$env:Path="$env:JAVA_HOME\bin;$env:Path"
& 'D:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat' --no-daemon assembleHap
```

**涉及文件**：无

**依赖任务**：Task 4.1
**验收标准**：
- 退出码 0
- 输出包含 `BUILD SUCCESSFUL`
- 无 ERROR 级别日志

**TDD**：不适用

---

#### Task 5.2: 测试验证
**描述**：使用 hvigorw 运行 hypium 测试套件，确保所有 8 个 AC 测试通过。

**执行命令**：
```powershell
Set-Location 'D:\huawei\Demo\worktrees\issue-9\opencalc'
$env:DEVECO_SDK_HOME='D:\Program Files\Huawei\DevEco Studio\sdk'
$env:JAVA_HOME='D:\Program Files\Huawei\DevEco Studio\jbr'
$env:Path="$env:JAVA_HOME\bin;$env:Path"
& 'D:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat' --no-daemon test
```

**涉及文件**：无

**依赖任务**：Task 5.1
**验收标准**：
- 所有 8 个 AC 测试通过
- 0 个 FAILED
- 测试报告生成在 `entry/build/test-results/` 或类似路径

**TDD**：不适用

---

#### Task 5.3: 集成验证（手动）
**描述**：在真机或模拟器上运行编译后的应用，验证：
1. 输入 `50+10%` 显示 55
2. 输入 `200-15%` 显示 170
3. 输入 `8×5%` 显示 0.4
4. 输入 `100÷10%` 显示 0.1
5. 输入 `50%%` 显示"表达式错误"
6. 输入 `sin(30%)` 显示"表达式错误"
7. 触发除零后按 `%`，能继续输入

**涉及文件**：无

**依赖任务**：Task 5.2
**验收标准**：
- 7 个手动验证场景全部符合预期
- 截图存档（在 docs/ 目录下）

**TDD**：不适用

---

## 开发顺序

```
Task 1.1 (差异分析)
    ↓
Task 2.1 (写失败的测试)
    ↓
Task 2.2 (写错误恢复测试)
    ↓
Task 3.1 (实现重复 % 检测) → 让 Task 2.1 中 AC-001-08 通过
    ↓
Task 3.2 (实现函数内 % 检测) → 让 Task 2.1 中 AC-001-07 通过
    ↓
Task 3.3 (实现错误状态清错) → 让 Task 2.2 通过
    ↓
Task 4.1 (重构，可选)
    ↓
Task 5.1 (编译验证)
    ↓
Task 5.2 (测试验证)
    ↓
Task 5.3 (手动集成验证)
    ↓
完成
```

## 验收计划

| 任务 | 验收方式 | 验收时间 | 关键产出 |
| --- | --- | --- | --- |
| Task 1.1 | 文档审查 | Phase 1 结束 | `diff-analysis.md` |
| Task 2.1 | 测试运行 | Phase 2 结束 | 测试用例新增，AC-001-07, 08 RED |
| Task 2.2 | 测试运行 | Phase 2 结束 | AC-001-09 RED |
| Task 3.1 | 测试运行 | Phase 3 结束 | AC-001-08 GREEN |
| Task 3.2 | 测试运行 | Phase 3 结束 | AC-001-07 GREEN |
| Task 3.3 | 测试运行 | Phase 3 结束 | AC-001-09 GREEN |
| Task 4.1 | 代码审查 | Phase 4 结束 | 代码质量提升 |
| Task 5.1 | 编译命令 | Phase 5 结束 | BUILD SUCCESSFUL |
| Task 5.2 | 测试命令 | Phase 5 结束 | 8/8 AC 通过 |
| Task 5.3 | 手动验证 | Phase 5 结束 | 7/7 场景符合 |

## 风险与注意事项

| 风险 | 缓解 |
| --- | --- |
| worktree 有未提交的 `Expression.test.ets` 变更 | Task 1.1 阶段先确认现有测试用例，Task 2.1 合并而非覆盖 |
| 错误恢复清空 `expression` 可能影响 UX | IMPLEMENTING 前与用户确认：清空 vs 保留 |
| `Issue #9` 操作符优先级修复可能受影响 | Task 3.1/3.2 后必须跑 AC-001-06 等连续运算测试 |
| hvigorw daemon 模式下 Java 路径问题 | 所有 hvigorw 命令加 `--no-daemon` 标志 |
| 已提交实现的语法（如 done[] 数组） | 保留，不重写 |

## 与 APPLYING 阶段的衔接

- APPLYING 阶段将依次执行 Task 1.1 → 5.3
- 每个任务完成后更新 `todo.md` 状态
- 任务阻塞或失败时立即停止并报告
- 测试失败时回到对应实现任务修复

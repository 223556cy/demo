# 百分号按钮 — 开发任务

## 任务概述

- **功能名称**: 百分号按钮 (macOS 风格 + 回归测试)
- **变更类型**: requirement-add
- **关联 Issue**: #9
- **关联 Spec**: specs/changes/20260611-requirement-add-percent-button/{proposal.md, delta-spec.md, info.md, design.md}
- **开发阶段**: TDD (RED → GREEN → REFACTOR)
- **预计任务数**: 7
- **目标粒度**: XS-S

## 任务列表

### 阶段 1：测试基础设施搭建 (RED 前置)

#### Task 1.1: 启用 test sourceSet
**描述**: 在 `entry/build-profile.json5` 中声明 test sourceSet 指向 `entry/src/test`，并在 `entry/src/test/ets` 目录建立 ArkTS 测试入口
**涉及文件**:
- `opencalc/entry/build-profile.json5` （可能新增 src/test 配置）
- `opencalc/entry/src/test/ets/` 新建（占位 .ets）
**依赖任务**: 无
**验收标准**:
- `entry/src/test/ets/` 目录存在
- 不会破坏现有 `hvigorw build`（构建 HAP 仍然成功）

#### Task 1.2: 写最小冒烟测试
**描述**: 写一个最简单的测试 `1+1` 验证 hypium 框架可用
**涉及文件**:
- `opencalc/entry/src/test/ets/Smoke.test.ets`
**依赖任务**: Task 1.1
**验收标准**:
- 测试文件语法合法
- 后续 Task 2.x 中能跑通

### 阶段 2：RED — 写百分号测试用例

#### Task 2.1: 写 12 个 percent 测试用例（RED）
**描述**: 在 `Expression.test.ets` 写 12 个黑盒测试用例（见 design.md 第 3 节），每个 case 调 `Expression.getCleanExpression(input, '.', ',')` 并断言输出字符串
**涉及文件**:
- `opencalc/entry/src/test/ets/calculator/Expression.test.ets` （新增）
**依赖任务**: Task 1.2
**验收标准**:
- 12 个测试用例全部写完
- 跑测试时**如实记录**哪些 PASS / 哪些 FAIL（不准伪造）
- 写入 `apply-report.md` 的 RED 阶段输出

### 阶段 3：GREEN — 修复 RED 暴露的 bug

#### Task 3.1: 分析 RED 输出，识别 bug
**描述**: 阅读 Task 2.1 的测试输出，区分：
- (a) 测试期望值写错（assertion 写错）
- (b) 实现代码 bug
**涉及文件**: 无（仅分析）
**依赖任务**: Task 2.1
**验收标准**:
- 输出"RED 阶段判决表"——逐 case 标注 PASS / FAIL / 期望错 / 实现错

#### Task 3.2: 修复 `Expression.getPercentString` 中的 bug（最小修改）
**描述**: 针对 Task 3.1 识别出的实现 bug，做最小化修改，让 FAIL 用例变 PASS
**涉及文件**:
- `opencalc/entry/src/main/ets/calculator/Expression.ets` （可能小改）
**依赖任务**: Task 3.1
**验收标准**:
- 改完后所有 12 个测试 PASS
- 旧的 factorial / sqrt 测试逻辑未被破坏（读代码确认）
- 不引入新三方库

### 阶段 4：REFACTOR

#### Task 4.1: 重构 + 命名清理（可选）
**描述**: 仅当发现明显可抽取的公共模式或命名异味时做；否则跳过此 task
**涉及文件**: 视情况
**依赖任务**: Task 3.2
**验收标准**:
- 12 个测试仍 PASS
- 没有引入新行为

### 阶段 5：验证

#### Task 5.1: 全量构建
**描述**: 跑 `hvigorw clean && hvigorw build`（或等价物），确认 0 编译错误
**涉及文件**: 无
**依赖任务**: Task 4.1
**验收标准**:
- 编译退出码 0
- 贴出 stdout / stderr 关键片段到 apply-report.md

#### Task 5.2: 产出 apply-report.md
**描述**: 记录 TDD 全过程、贴真实测试输出、贴构建输出
**涉及文件**:
- `specs/changes/20260611-requirement-add-percent-button/apply-report.md` （新增）
**依赖任务**: Task 5.1
**验收标准**:
- RED / GREEN / REFACTOR / 构建 4 段齐全
- 每段都有真实命令 + 真实输出
- 不准伪造

## 开发顺序

```
Task 1.1 (建 test 目录)
   ↓
Task 1.2 (写冒烟测试)
   ↓
Task 2.1 (写 12 个 percent 测试 = RED)
   ↓
Task 3.1 (分析 RED 输出)
   ↓
Task 3.2 (修 bug = GREEN)
   ↓
Task 4.1 (REFACTOR，可选)
   ↓
Task 5.1 (全量构建验证)
   ↓
Task 5.2 (产出 apply-report.md)
   ↓
完成
```

## 验收计划

| 任务 | 验收方式 | 关键产物 |
|------|---------|----------|
| Task 1.1 | 目录存在 + 构建不破 | `entry/src/test/ets/` |
| Task 1.2 | 文件语法合法 | `Smoke.test.ets` |
| Task 2.1 | 12 个测试执行 | `Expression.test.ets` + 真实输出 |
| Task 3.1 | 判决表完整 | 文字判决 |
| Task 3.2 | 12/12 PASS | 真实输出 |
| Task 4.1 | 12/12 仍 PASS | 同上 |
| Task 5.1 | 编译退出码 0 | 真实日志 |
| Task 5.2 | 4 段齐全 | apply-report.md |

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| hvigorw test 在当前 win11 环境跑不起来 | 备选方案：手写最小 ArkTS→JS 转换器 或 用 Node.js 等价测试 `getCleanExpression` 的纯逻辑（前提是 Expression.ets 逻辑可独立于 ArkTS 运行） |
| @ohos/hypium import 失败 | 备选：直接 require / 写最简断言 |
| 测试文件被 .gitignore | 检查 opencalc/.gitignore，需要 `!test/` 规则 |

## 关键不变量

- I-1: 不动 `CalcEngine`
- I-2: 不动 UI 颜色 / 主题 / 布局
- I-3: 不动 `PreferencesStore`
- I-4: 测试只增不改
- I-5: 真实跑测试，不准伪造输出（铁律 7）

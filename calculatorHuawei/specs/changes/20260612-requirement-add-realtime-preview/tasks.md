# IMPLEMENTING — Issue #11 实时预览功能

> aid-workflow 20260612-requirement-add-realtime-preview · IMPLEMENTING 阶段任务分解
> 基线：proposal.md / delta-spec.md / info.md / design.md
> 强制约束：TDD RED-GREEN-REFACTOR + 真实跑测（铁律 7）

---

## 任务总览

| ID | 阶段 | 任务 | 估时 | 状态 |
|----|------|------|------|------|
| T1 | RED | 创建 `RealtimePreview.port.mjs` + `RealtimePreview.test.mjs`，写 15 个失败用例 | 30min | ⏳ |
| T2 | RED | 跑 `node --test` 确认用例 RED（全部失败） | 2min | ⏳ |
| T3 | GREEN | 扩展 `ErrorFlags.ets` 增加 `snapshot/restore` 静态方法 | 5min | ⏳ |
| T4 | GREEN | 在 `CalculatorPage.ets` 新增 `@State preview` + `computePreview` + `@Watch` | 20min | ⏳ |
| T5 | GREEN | 在 `DisplayPanel()` 中插入 preview Text 行 | 10min | ⏳ |
| T6 | GREEN | 跑 `node --test` 确认用例 GREEN（全部通过） | 2min | ⏳ |
| T7 | REFACTOR | 提取常量（`PREVIEW_FONT_SIZE`） / 拆分 `isLastCharComputable` 为可测试 | 10min | ⏳ |
| T8 | REFACTOR | 跑 `node --test` 确认 GREEN（重构不破坏） | 2min | ⏳ |
| T9 | VERIFY | git diff --stat 检查改动量 + `git status` 列出变更文件 | 2min | ⏳ |
| T10 | DOC | 生成 `apply-report.md`（含测试输出、AC 矩阵、git diff） | 10min | ⏳ |

---

## T1 — RED：写失败测试

### T1.1 创建 `RealtimePreview.port.mjs`

```javascript
// specs/changes/20260612-requirement-add-realtime-preview/tests/RealtimePreview.port.mjs
// 1:1 端口：将 CalculatorPage.computePreview 提取为独立类 PreviewCalculator

class ErrorFlags {
  static division_by_0 = false
  static domain_error = false
  static syntax_error = false
  static is_infinity = false
  static require_real_number = false
  static reset() { /* ... */ }
  static snapshot() { return [/* ... */] }
  static restore(snap) { /* ... */ }
}

class PreviewCalculator {
  computePreview(exprStr, radianMode) {
    // 实现见 design.md 第 3.3 节
  }
  isLastCharComputable(lastChar) {
    // 实现见 design.md 第 3.3 节
  }
}

export { ErrorFlags, PreviewCalculator }
```

**注意**：RED 阶段此文件包含 **完整实现**（因为代码与 ArkTS 一一对应），但**测试尚未编写**——RED 阶段的"失败"是测试用例本身不存在/不通过。

### T1.2 创建 `RealtimePreview.test.mjs`

15 个 TC-RP 用例，对应 design.md 第 6 节测试矩阵。每个用例格式：

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { PreviewCalculator, ErrorFlags } from './RealtimePreview.port.mjs'

function freshCalc() {
  ErrorFlags.reset()
  return new PreviewCalculator()
}

test('TC-RP-01: 空表达式 → ""', () => {
  const c = freshCalc()
  assert.equal(c.computePreview('', false), '')
})
// ... 其余 14 个用例
```

### T1.3 关键用例（直接抄自 design.md 测试矩阵）

| ID | 用例名 | 输入 | 预期 |
|----|--------|------|------|
| TC-RP-01 | 空表达式 | "" | "" |
| TC-RP-03 | 简单加法 | "1+2" | "3" |
| TC-RP-04 | 减法负数 | "5-10" | "-5" |
| TC-RP-05 | 不完整加法 | "1+" | "" |
| TC-RP-06 | 函数未闭合 | "sin(0" | "" |
| TC-RP-07 | 语法错误 | "1++2" | "" |
| TC-RP-08 | 函数 | "sin(0)" | "0" |
| TC-RP-09 | 百分号 | "50+10%" | "55" |
| TC-RP-10 | 异常输入 | "1+(" | "" |
| TC-RP-11 | 格式一致 | "1000+2000" | "3,000" |
| TC-RP-12 | 嵌套括号 | "(1+2)*(3+4)" | "21" |
| TC-RP-13 | 长表达式 | "1+2*3/4-5" | "-2.5" |
| TC-RP-14 | 除零 | "1÷0" | "" |
| TC-RP-15 | AC 等价 | ""（调用 reset 后） | "" |

---

## T2 — RED 验证

**验收**：`node --test` 必须输出 RED：

```bash
cd specs/changes/20260612-requirement-add-realtime-preview/tests
node --test RealtimePreview.test.mjs
# 预期：tests 15 fail 15 pass 0（首次）
```

> 若首次全 PASS（说明用例太弱或实现已存在），需补强用例。

---

## T3 — GREEN：错误标志扩展

### T3.1 修改 `ErrorFlags.ets`

在现有 `ErrorFlags` 类中追加：

```typescript
static snapshot(): boolean[] {
  return [
    ErrorFlags.syntax_error,
    ErrorFlags.division_by_0,
    ErrorFlags.domain_error,
    ErrorFlags.is_infinity,
    ErrorFlags.require_real_number
  ]
}

static restore(snap: boolean[]): void {
  ErrorFlags.syntax_error = snap[0]
  ErrorFlags.division_by_0 = snap[1]
  ErrorFlags.domain_error = snap[2]
  ErrorFlags.is_infinity = snap[3]
  ErrorFlags.require_real_number = snap[4]
}
```

**验收**：`ErrorFlags.snapshot()` 返回 5 元素数组；`ErrorFlags.restore(snap)` 恢复所有 5 位。

### T3.2 Node 端口同步

在 `RealtimePreview.port.mjs` 的 `ErrorFlags` 类中追加同样两个方法（确保 Node 测试通过）。

---

## T4 — GREEN：核心逻辑实现

### T4.1 修改 `CalculatorPage.ets`

#### a) 新增 @State（字段块 16-25 行附近）

```typescript
@State preview: string = ''   // 【NEW】实时预览值
```

#### b) 新增 @Watch + computePreview（onEquals 之后，私有方法块）

```typescript
@Watch('expression')
onExpressionChange(): void {
  this.preview = this.computePreview(this.expression, this.radianMode)
}

private computePreview(exprStr: string, radianMode: boolean): string {
  // 见 design.md 第 3.3 节
}
```

#### c) 新增 isLastCharComputable 辅助

```typescript
private isLastCharComputable(lastChar: string): boolean {
  if ((lastChar >= '0' && lastChar <= '9') || lastChar === '.') return true
  if (lastChar === ')') return true
  if (lastChar === '%') return true
  if (lastChar === '!') return true
  if (lastChar === 'π' || lastChar === 'e') return true
  return false
}
```

### T4.2 不修改 `onEquals` / `onOp`

现有 SR-09 错误恢复逻辑保持不变——`computePreview` 通过 snapshot/restore 实现隔离，不污染 onEquals 流程。

---

## T5 — GREEN：UI 行插入

### T5.1 修改 `DisplayPanel()`

在 expression 行后、result 行前插入：

```typescript
// 【NEW】实时预览行
Text(this.preview.length > 0 ? this.preview : ' ')
  .fontSize(this.isLandscape ? 12 : 14)
  .fontColor(this.getT2())
  .width('100%')
  .textAlign(TextAlign.End)
  .padding({ right: 12, left: 12, top: 2, bottom: 2 })
  .maxLines(1)
```

**视觉**：横屏 12pt / 竖屏 14pt，与 expression 同色（getT2），右对齐，maxLines=1 防止溢出。

---

## T6 — GREEN 验证

**验收**：`node --test` 输出 GREEN：

```bash
cd specs/changes/20260612-requirement-add-realtime-preview/tests
node --test RealtimePreview.test.mjs
# 预期：tests 15 pass 15 fail 0
```

> 若失败：检查 isLastCharComputable 白名单是否完备；检查 ErrorFlags.snapshot/restore 是否被调用。

---

## T7 — REFACTOR：清理

### T7.1 提取常量

```typescript
// CalculatorPage.ets 顶部常量区
private static readonly PREVIEW_FONT_PORTRAIT: number = 14
private static readonly PREVIEW_FONT_LANDSCAPE: number = 12
private static readonly PREVIEW_MAX_LINES: number = 1
```

### T7.2 抽取 isLastCharComputable 为可测试函数

为便于单元测试，将 isLastCharComputable 从 CalculatorPage 抽到独立 helper（可选，本变更可保持私有）。

### T7.3 注释规范化

为 computePreview 添加完整 JSDoc。

---

## T8 — REFACTOR 验证

**验收**：`node --test` 仍全 GREEN，且 `git diff --stat` 改动量未异常膨胀（应 < 60 行）。

---

## T9 — VERIFY：改动量自证

```bash
cd D:/huawei/Demo/worktrees/issue-11
git status
git diff --stat
```

**预期文件**：
- `opencalc/entry/src/main/ets/model/ErrorFlags.ets` (modified)
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (modified)
- `specs/changes/20260612-requirement-add-realtime-preview/tests/RealtimePreview.port.mjs` (new)
- `specs/changes/20260612-requirement-add-realtime-preview/tests/RealtimePreview.test.mjs` (new)

---

## T10 — DOC：apply-report.md

按以下结构生成：

1. 任务摘要（10 个任务的实际耗时）
2. 测试输出（原始 stdout，含 tests 数 / pass 数 / duration）
3. AC 验收矩阵（设计 7 个 SR + 15 个 AC 全部对照）
4. git diff --stat（实际改动量）
5. 已知限制（如未在真机跑测，仅 Node 端口验证）
6. 下一步建议（移交审查员 / 进入归档）

---

## 约束与质量门禁

| 约束 | 实施方法 |
|------|----------|
| TDD 强制 | T1 写测试 → T2 验证 RED → T3-T5 实现 → T6 验证 GREEN |
| 真实跑测 | `node --test` 真实执行；贴原始 stdout（铁律 7） |
| 末字符白名单 | isLastCharComputable（design.md 3.3） |
| 错误状态隔离 | ErrorFlags.snapshot/restore（T3） |
| 不破坏现有 | onEquals / onOp / 百分号 / 历史记录 全部不变 |
| 测试独立性 | beforeEach ErrorFlags.reset（每次用例前清零） |

---

## 关联文档

- `proposal.md` — 需求提案（步骤 1-3）
- `delta-spec.md` — 增量规格（步骤 4）
- `info.md` — 代码仓理解（步骤 5）
- `design.md` — 组件设计（本变更步骤 8 产物）
- `todo.md` — 工作流进度状态机
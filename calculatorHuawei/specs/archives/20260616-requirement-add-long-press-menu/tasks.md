# Tasks — Issue #16 长按弹出选择菜单

> aid-workflow 20260616-requirement-add-long-press-menu · IMPLEMENTING 阶段任务分解
> 基线:proposal.md / delta-spec.md / info.md / design.md
> 强制约束:TDD RED-GREEN-REFACTOR + 真实跑测(铁律 7)

---

## 任务总览

| ID | 阶段 | 任务 | 估时 | 状态 |
|----|------|------|------|------|
| T1 | RED | 创建 `LongPressMenu.port.mjs` + `LongPressMenu.test.mjs`,写 6 个失败用例 | 15min | ⏳ |
| T2 | RED | 跑 `node --test` 确认用例 RED(全部失败) | 2min | ⏳ |
| T3 | GREEN | 实现 `LongPressMenu.port.mjs` 让所有用例 GREEN | 5min | ⏳ |
| T4 | GREEN | 跑 `node --test` 确认用例 GREEN(全部通过) | 2min | ⏳ |
| T5 | GREEN | 创建 `opencalc/entry/src/main/ets/pages/LongPressMenu.ets` (ArkTS 实现,与 .port.mjs 1:1 对应) | 5min | ⏳ |
| T6 | GREEN | 修改 `CalculatorPage.ets` 增加 `@State showLongPressMenu/longPressSource` + `onLongPress/onLongPressCandidate` | 15min | ⏳ |
| T7 | GREEN | 修改 `CalculatorPage.ets` 的 `BtnFunc` Builder 增加 `.gesture(LongPressGesture().onAction(...))` | 5min | ⏳ |
| T8 | GREEN | 新增 `LongPressMenuPanel()` @Builder + 在 `build()` Stack 顶层挂载 | 15min | ⏳ |
| T9 | GREEN | 跑 `node --test` 确认 GREEN(端口逻辑仍通过) | 2min | ⏳ |
| T10 | REFACTOR | 端口文件提取常量 `LONG_PRESS_REGISTRY` 命名与 design.md 对齐 | 5min | ⏳ |
| T11 | REFACTOR | `LongPressMenuPanel` 抽出 `MENU_WIDTH_RATIO=0.6`/`MENU_ITEM_HEIGHT=44` 常量 | 5min | ⏳ |
| T12 | REFACTOR | 跑 `node --test` 确认 GREEN(重构不破坏) | 2min | ⏳ |
| T13 | VERIFY | git diff --stat 检查改动量 + `git status` 列出变更文件 | 2min | ⏳ |
| T14 | DOC | 生成 `apply-report.md`(含测试输出、AC 矩阵、git diff) | 10min | ⏳ |
| T15 | UI | UI 自动化测试 (hdc + harmonyos-ui-test skill,capabilities.json ui_test.available=true) | 20min | ⏳ |

---

## T1 — RED:写失败测试

### T1.1 创建 `LongPressMenu.port.mjs`(空实现,导出空 stub)

```javascript
// specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.port.mjs
// 1:1 端口:与 ArkTS LongPressMenu.ets 一一对应
// RED 阶段: 仅导出空 stub,测试用例会全部失败

function hasCandidates(label) {
  return false  // stub - RED
}

function getCandidates(label) {
  return []  // stub - RED
}

export { hasCandidates, getCandidates }
```

### T1.2 创建 `LongPressMenu.test.mjs`(6 个失败用例)

```javascript
// specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs
import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { hasCandidates, getCandidates } from './LongPressMenu.port.mjs'

test('AC-1 hasCandidates sin/cos/tan → true', () => {
  assert.equal(hasCandidates('sin'), true)
  assert.equal(hasCandidates('cos'), true)
  assert.equal(hasCandidates('tan'), true)
})

test('AC-5 hasCandidates 数字/运算符/常量 → false', () => {
  assert.equal(hasCandidates('1'), false)
  assert.equal(hasCandidates('+'), false)
  assert.equal(hasCandidates('π'), false)
})

test('AC-5 hasCandidates arcsi/arcco/arcta → false', () => {
  assert.equal(hasCandidates('arcsi'), false)
  assert.equal(hasCandidates('arcco'), false)
  assert.equal(hasCandidates('arcta'), false)
})

test('AC-5 hasCandidates ln/log 首版无映射 → false', () => {
  assert.equal(hasCandidates('ln'), false)
  assert.equal(hasCandidates('log'), false)
})

test('AC-1 getCandidates sin → 3 项', () => {
  assert.deepEqual(getCandidates('sin'), ['arcsin', 'arccos', 'arctan'])
})

test('getCandidates 边界 - 未知 label → []', () => {
  assert.deepEqual(getCandidates('xxx'), [])
  assert.deepEqual(getCandidates(''), [])
})
```

---

## T2 — RED:确认失败

```bash
node --test specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs
```

**预期**: 6 个 test 全部 FAIL (stub 返回 false/[])

---

## T3 — GREEN:实现端口

### T3.1 完整实现 `LongPressMenu.port.mjs`

```javascript
// specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.port.mjs
// GREEN 阶段: 完整实现

const LONG_PRESS_REGISTRY = new Map([
  ['sin', ['arcsin', 'arccos', 'arctan']],
  ['cos', ['arcsin', 'arccos', 'arctan']],
  ['tan', ['arcsin', 'arccos', 'arctan']],
])

function hasCandidates(label) {
  return LONG_PRESS_REGISTRY.has(label)
}

function getCandidates(label) {
  const v = LONG_PRESS_REGISTRY.get(label)
  return v === undefined ? [] : v
}

export { LONG_PRESS_REGISTRY, hasCandidates, getCandidates }
```

---

## T4 — GREEN:确认通过

```bash
node --test specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs
```

**预期**: 6 个 test 全部 PASS

---

## T5 — GREEN:ArkTS 类

### T5.1 创建 `LongPressMenu.ets`

```typescript
// opencalc/entry/src/main/ets/pages/LongPressMenu.ets
// aid-workflow 20260616: 长按候选菜单逻辑(纯静态类,无 UI 依赖)
// 对应 .port.mjs 与 design.md §3.5.6

export class LongPressMenu {
  /** aid-workflow 20260616: 长按候选注册表,标签 → 候选函数列表 */
  static REGISTRY: Map<string, string[]> = new Map<string, string[]>([
    ['sin', ['arcsin', 'arccos', 'arctan']],
    ['cos', ['arcsin', 'arccos', 'arctan']],
    ['tan', ['arcsin', 'arccos', 'arctan']],
  ])

  /** aid-workflow 20260616: 按钮是否有长按候选 */
  static hasCandidates(label: string): boolean {
    return LongPressMenu.REGISTRY.has(label)
  }

  /** aid-workflow 20260616: 获取按钮的长按候选列表 */
  static getCandidates(label: string): string[] {
    const v = LongPressMenu.REGISTRY.get(label)
    return v === undefined ? [] : v
  }
}
```

---

## T6 — GREEN:CalculatorPage 状态 + 事件

### T6.1 修改 `CalculatorPage.ets`

```typescript
// 在 imports 后追加
import { LongPressMenu } from './LongPressMenu'

// 在 @State 段(约 L18-33) 追加:
@State showLongPressMenu: boolean = false  // aid-workflow 20260616
@State longPressSource: string = ''         // aid-workflow 20260616

// 在 onEquals 之后(约 L221) 追加方法:
onLongPress(label: string): void {
  // aid-workflow 20260616: 长按按钮 → 弹出候选菜单
  if (!LongPressMenu.hasCandidates(label)) return
  this.longPressSource = label
  this.showLongPressMenu = true
}

onLongPressCandidate(item: string): void {
  // aid-workflow 20260616: 点击候选 → 复用 onFunc + 关闭菜单
  this.showLongPressMenu = false
  this.onFunc(item)
}
```

---

## T7 — GREEN:BtnFunc 加长按手势

### T7.1 修改 `BtnFunc` Builder (CalculatorPage.ets L422)

**原代码**:
```typescript
@Builder BtnFunc(l: string) { Text(l).fontSize(...).onClick((): void => { this.onFunc(l) }) }
```

**新代码**:
```typescript
@Builder BtnFunc(l: string) {
  Text(l).fontSize(...).onClick((): void => { this.onFunc(l) })
    .gesture(LongPressGesture().onAction((): void => { this.onLongPress(l) }))
}
```

**FMEA C5**: Stack 层级 + 系统手势互斥保证长按/短按不冲突。

---

## T8 — GREEN:LongPressMenuPanel + Stack 挂载

### T8.1 在 CalculatorPage.ets 增加 LongPressMenuPanel @Builder

```typescript
// aid-workflow 20260616: 长按候选菜单面板(半透明遮罩 + 居中菜单)
@Builder LongPressMenuPanel() {
  Stack() {
    // 1. 遮罩层 (铺满整个 Stack,点击关闭菜单)
    Column().width('100%').height('100%')
      .backgroundColor('#000000').opacity(0.4)
      .onClick((): void => { this.showLongPressMenu = false })

    // 2. 菜单容器(居中)
    Column() {
      ForEach(LongPressMenu.getCandidates(this.longPressSource), (item: string) => {
        Text(item).fontSize(16).fontColor(this.getT1())
          .width('100%').height(44)
          .textAlign(TextAlign.Center)
          .backgroundColor(this.getPanelBg())
          .onClick((): void => { this.onLongPressCandidate(item) })
      })
    }
    .width('60%').constraintSize({ maxWidth: 280 })
    .backgroundColor(this.getPanelBg()).borderRadius(12).padding(4)
  }
  .width('100%').height('100%')
}
```

### T8.2 在 `build()` Stack 顶层追加

**原代码** (CalculatorPage.ets:310-334):
```typescript
Stack() {
  if (this.isLandscape) { ... }
  else { ... }
  if (this.showSettings) this.SettingsPanel()
  if (this.showAbout) this.AboutPanel()
}
```

**新代码** (在 `if (this.showAbout)` 后追加):
```typescript
Stack() {
  if (this.isLandscape) { ... }
  else { ... }
  if (this.showSettings) this.SettingsPanel()
  if (this.showAbout) this.AboutPanel()
  // aid-workflow 20260616: 长按候选菜单(顶层,遮罩盖全屏)
  if (this.showLongPressMenu) this.LongPressMenuPanel()
}
```

---

## T9 — GREEN:回归测试

```bash
node --test specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs
```

**预期**: 6 个 test 仍然 PASS(端口文件未变,ArkTS 代码不影响)

---

## T10 — REFACTOR:端口常量对齐

将 `LONG_PRESS_REGISTRY` 重命名/重组对齐 design.md 命名(若已对齐则跳过)。

---

## T11 — REFACTOR:ArkTS 常量提取

在 `LongPressMenu.ets` 头部增加:
```typescript
// aid-workflow 20260616: UI 规格常量(供 LongPressMenuPanel 引用)
export const MENU_WIDTH_RATIO = '60%'
export const MENU_ITEM_HEIGHT = 44
export const MENU_BORDER_RADIUS = 12
export const MENU_MASK_COLOR = '#000000'
export const MENU_MASK_OPACITY = 0.4
```

在 CalculatorPage 中替换字面量为常量引用。

---

## T12 — REFACTOR:回归

```bash
node --test specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs
```

**预期**: 仍然 PASS

---

## T13 — VERIFY:git 检查

```bash
git status
git diff --stat
```

**预期变更文件清单**:
- `opencalc/entry/src/main/ets/pages/LongPressMenu.ets` (新增)
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets` (修改)
- `specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.port.mjs` (新增)
- `specs/changes/20260616-requirement-add-long-press-menu/tests/LongPressMenu.test.mjs` (新增)

---

## T14 — DOC:apply-report.md

按 aid-applying skill 模板生成,包含:
- 测试输出(node --test 完整结果)
- AC 矩阵(AC-1 ~ AC-7)
- git diff 摘要
- 手动验证步骤

---

## T15 — UI 自动化测试(可选,基于 capabilities.json ui_test.available=true)

### T15.1 创建 UI 测试脚本

```python
# specs/changes/20260616-requirement-add-long-press-menu/ui-tests/run_tests.py
"""长按菜单 UI 自动化测试 (hdc + harmonyos-ui-test)"""
# 1. hdc list targets 验证连接
# 2. hdc install -r 安装新版本 HAP
# 3. aa start 启动应用
# 4. dump UI 树找到 'sin' 按钮
# 5. input longpress 触发
# 6. dump UI 树验证弹出菜单含 arcsin/arccos/arctan
# 7. screenshot 存档
```

**验收标准**:
- [ ] hdc 设备已连接
- [ ] 应用已安装到设备
- [ ] 应用已启动
- [ ] AC-1 通过 dump UI 树 + 截图验证
- [ ] screenshot/ 目录包含每步截图
- [ ] results.json pass

**TDD**: [x] RED / [x] GREEN / [ ] REFACTOR (UI 测试是 acceptance 性质,不是 TDD 强制)

**注意**: UI 自动化作为可选 acceptance 步骤。若 hvigorw 编译失败导致 HAP 无法安装,在 apply-report 中标注 ⏭️ Deferred 并说明(端口单测已 GREEN)。

---

## 开发顺序

```
T1 (RED 写测试)
  ↓
T2 (RED 跑测,确认失败)
  ↓
T3 (GREEN 实现)
  ↓
T4 (GREEN 跑测,确认通过)
  ↓
T5 (ArkTS 类)
  ↓
T6 (CalculatorPage 状态/事件)
  ↓
T7 (BtnFunc 长按手势)
  ↓
T8 (LongPressMenuPanel + 挂载)
  ↓
T9 (回归 GREEN)
  ↓
T10~T11 (REFACTOR)
  ↓
T12 (回归 GREEN)
  ↓
T13 (git 检查)
  ↓
T14 (apply-report.md)
  ↓
T15 (UI 自动化,可选)
  ↓
✅ IMPLEMENTING + APPLYING 完成
```

---

## 验收计划

| 任务 | 验收方式 | 期望结果 |
|------|---------|---------|
| T1 | 文件存在 + 6 个 test 块 | ✅ |
| T2 | `node --test` 全 FAIL | ✅ |
| T4 | `node --test` 全 PASS | ✅ |
| T9 | `node --test` 仍 PASS | ✅ |
| T12 | `node --test` 仍 PASS | ✅ |
| T13 | `git status` 含 4 个变更文件 | ✅ |
| T14 | apply-report.md 生成 | ✅ |
| T15 | UI 测试通过(可选) | ⏭️ Deferred if hvigorw 失败 |
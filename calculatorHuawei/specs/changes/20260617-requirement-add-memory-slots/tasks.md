# Tasks — Issue #28 记忆槽 (M1-M6 + MR)

> aid-workflow 20260617-requirement-add-memory-slots · IMPLEMENTING 阶段任务分解
> 基线: proposal.md / delta-spec.md / info.md / delta-design.md / design-review.md
> 强制约束: TDD RED-GREEN-REFACTOR + 真实跑测(铁律 7)
> 复用: Issue #16 的 port.mjs 模式做快速迭代（node --test），同套单测逻辑最终落到 entry/src/test/ets/calculator/MemorySlots.test.ets（hypium）

---

## 任务总览

| ID | 阶段 | 任务 | 估时 | 状态 |
|----|------|------|------|------|
| T1 | RED | 创建 `tests/MemorySlots.port.mjs`（空 stub）+ `tests/MemorySlots.test.mjs` 写 10 个失败用例 | 15min | ⏳ |
| T2 | RED | 跑 `node --test` 确认用例 RED（全部失败） | 2min | ⏳ |
| T3 | GREEN | 实现 `MemorySlots.port.mjs` 让 10 个用例 GREEN | 10min | ⏳ |
| T4 | GREEN | 跑 `node --test` 确认 GREEN（全部通过） | 2min | ⏳ |
| T5 | GREEN | 创建 ArkTS `opencalc/entry/src/main/ets/calculator/MemorySlots.ets`（与 .port.mjs 1:1 对应） | 5min | ⏳ |
| T6 | RED | 创建 hypium 单元测试 `opencalc/entry/src/test/ets/calculator/MemorySlots.test.ets` | 10min | ⏳ |
| T7 | RED | 跑 `hvigorw --no-daemon test` 确认 hypium 用例 RED | 5min | ⏳ |
| T8 | GREEN | 修改 `CalculatorPage.ets` 增加 `@State memorySlots / showMemoryPicker` + 派生方法 | 10min | ⏳ |
| T9 | GREEN | 修改数字键 builder（L646）增加 1-6 数字键的 `.gesture(LongPressGesture().onAction(...))` | 5min | ⏳ |
| T10 | GREEN | 修改 ButtonGrid（L630-643）插入 MR 按钮 + 记忆激活指示 | 10min | ⏳ |
| T11 | GREEN | 新增 `MemoryPickerPanel()` @Builder + 在 `build()` Stack 顶层挂载 | 15min | ⏳ |
| T12 | GREEN | 新增 `onLongPressDigit / onMRClick / onPickSlot / onMemoryMaskClick` 方法 | 10min | ⏳ |
| T13 | GREEN | 在 `entry/src/test/List.test.ets` 注册新 test suite | 2min | ⏳ |
| T14 | GREEN | 跑 `hvigorw --no-daemon test` 确认 hypium GREEN（11 个用例） | 5min | ⏳ |
| T15 | GREEN | 跑 `node --test` 端口逻辑仍 GREEN（确保未破坏） | 2min | ⏳ |
| T16 | REFACTOR | 端口文件提取常量 `MEMORY_SLOTS_COUNT = 6` 命名与 design.md 对齐 | 3min | ⏳ |
| T17 | REFACTOR | `CalculatorPage.ets` 把字面量替换为 MemorySlots 派生方法调用 | 5min | ⏳ |
| T18 | REFACTOR | 跑 `node --test` + `hvigorw test` 双 GREEN 回归 | 5min | ⏳ |
| T19 | VERIFY | `git diff --stat` + `git status` 检查改动量 | 2min | ⏳ |
| T20 | DOC | 生成 `apply-report.md`（含测试输出、AC 矩阵、git diff、UI 截图） | 15min | ⏳ |
| T21 | UI | UI 自动化测试（hdc + harmonyos-ui-test skill, capabilities.json ui_test.available=true） | 25min | ⏳ |

> 共 **21** 个任务；预计总时长 ~3h

---

## T1 — RED: 写失败测试（端口模式）

### T1.1 创建 `tests/MemorySlots.port.mjs`（空 stub）

```javascript
// specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.port.mjs
// 1:1 端口：与 ArkTS calculator/MemorySlots.ets 一一对应
// RED 阶段：仅导出空 stub，测试用例会全部失败

const MEMORY_SLOTS_COUNT = 6

function empty() {
  return { slots: [], lastUsedSlotIndex: null }  // stub - RED
}

function save(state, idx, value) {
  return state  // stub - RED（应返回新 state）
}

function recall(state, idx) {
  return null  // stub - RED
}

function clearSlot(state, idx) {
  return state  // stub - RED
}

function anyHasValue(state) {
  return false  // stub - RED
}

function lastUsedLabel(state) {
  return ''  // stub - RED
}

export { MEMORY_SLOTS_COUNT, empty, save, recall, clearSlot, anyHasValue, lastUsedLabel }
```

### T1.2 创建 `tests/MemorySlots.test.mjs`（10 个失败用例）

```javascript
// specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs
import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import {
  MEMORY_SLOTS_COUNT,
  empty, save, recall, clearSlot, anyHasValue, lastUsedLabel,
} from './MemorySlots.port.mjs'

test('AC-MEM-01 empty() 返回 6 个空槽 + lastUsedSlotIndex=null', () => {
  const s = empty()
  assert.equal(s.slots.length, MEMORY_SLOTS_COUNT)
  assert.equal(s.lastUsedSlotIndex, null)
  for (let i = 0; i < MEMORY_SLOTS_COUNT; i++) {
    assert.equal(s.slots[i].slotIndex, i + 1)
    assert.equal(s.slots[i].isEmpty(), true)
  }
})

test('AC-MEM-02 save 写入第 1 槽后 anyHasValue=true', () => {
  let s = empty()
  s = save(s, 1, 42)
  assert.equal(anyHasValue(s), true)
  assert.equal(recall(s, 1), 42)
  assert.equal(s.lastUsedSlotIndex, 1)
})

test('AC-MEM-03 save 覆盖已有槽位', () => {
  let s = empty()
  s = save(s, 3, 100)
  s = save(s, 3, 200)
  assert.equal(recall(s, 3), 200)
  assert.equal(s.lastUsedSlotIndex, 3)
})

test('AC-MEM-04 recall 空槽返回 null', () => {
  const s = empty()
  assert.equal(recall(s, 1), null)
  assert.equal(recall(s, 6), null)
})

test('AC-MEM-05 save 拒绝 NaN 返回旧 state', () => {
  let s = empty()
  s = save(s, 2, 10)
  const before = s
  const after = save(s, 2, NaN)
  assert.equal(after, before)
  assert.equal(recall(after, 2), 10)
})

test('AC-MEM-06 save 拒绝 Infinity 返回旧 state', () => {
  let s = empty()
  s = save(s, 4, 5)
  const before = s
  const after = save(s, 4, Infinity)
  assert.equal(after, before)
  assert.equal(recall(after, 4), 5)
})

test('AC-MEM-07 save 越界 idx=0 / idx=7 抛 Error', () => {
  const s = empty()
  assert.throws(() => save(s, 0, 1), /idx/)
  assert.throws(() => save(s, 7, 1), /idx/)
})

test('AC-MEM-08 anyHasValue 全空 false / 任一非空 true', () => {
  let s = empty()
  assert.equal(anyHasValue(s), false)
  s = save(s, 5, 1)
  assert.equal(anyHasValue(s), true)
  s = clearSlot(s, 5)
  assert.equal(anyHasValue(s), false)
})

test('AC-MEM-09 lastUsedLabel 无 lastUsed 返回 ""', () => {
  const s = empty()
  assert.equal(lastUsedLabel(s), '')
})

test('AC-MEM-10 lastUsedLabel 有 lastUsed 返回 "M{N}"', () => {
  let s = empty()
  s = save(s, 3, 99)
  assert.equal(lastUsedLabel(s), 'M3')
  s = save(s, 6, 1)
  assert.equal(lastUsedLabel(s), 'M6')
})
```

---

## T2 — RED: 确认失败

```bash
cd /d/huawei/Demo/worktrees/issue-28
node --test specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs
```

**预期**：10 个 test 全部 FAIL（stub 返回空 state / false / null / ''）

---

## T3 — GREEN: 实现端口

### T3.1 完整实现 `MemorySlots.port.mjs`

```javascript
// specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.port.mjs
// GREEN 阶段：完整实现

const MEMORY_SLOTS_COUNT = 6

function makeEmptySlot(slotIndex) {
  return { slotIndex, value: NaN, updatedAt: 0, isEmpty: () => true }
}

function makeSlot(slotIndex, value) {
  return { slotIndex, value, updatedAt: Date.now(), isEmpty: () => false }
}

function empty() {
  const slots = []
  for (let i = 1; i <= MEMORY_SLOTS_COUNT; i++) slots.push(makeEmptySlot(i))
  return { slots, lastUsedSlotIndex: null }
}

function validateIdx(idx) {
  if (!Number.isInteger(idx) || idx < 1 || idx > MEMORY_SLOTS_COUNT) {
    throw new Error(`MemorySlots.save: invalid idx ${idx}, expected 1..${MEMORY_SLOTS_COUNT}`)
  }
}

function save(state, idx, value) {
  validateIdx(idx)
  if (!Number.isFinite(value)) return state
  const slots = state.slots.map((s) =>
    s.slotIndex === idx ? makeSlot(idx, value) : s
  )
  return { slots, lastUsedSlotIndex: idx }
}

function recall(state, idx) {
  if (idx < 1 || idx > MEMORY_SLOTS_COUNT) return null
  const slot = state.slots[idx - 1]
  return slot.isEmpty() ? null : slot.value
}

function clearSlot(state, idx) {
  validateIdx(idx)
  const slots = state.slots.map((s) =>
    s.slotIndex === idx ? makeEmptySlot(idx) : s
  )
  return { slots, lastUsedSlotIndex: state.lastUsedSlotIndex }
}

function anyHasValue(state) {
  return state.slots.some((s) => !s.isEmpty())
}

function lastUsedLabel(state) {
  if (state.lastUsedSlotIndex === null) return ''
  return `M${state.lastUsedSlotIndex}`
}

export {
  MEMORY_SLOTS_COUNT,
  empty, save, recall, clearSlot, anyHasValue, lastUsedLabel,
}
```

---

## T4 — GREEN: 确认通过

```bash
node --test specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs
```

**预期**：10 个 test 全部 PASS

---

## T5 — GREEN: ArkTS 类

### T5.1 创建 `opencalc/entry/src/main/ets/calculator/MemorySlots.ets`

```typescript
// opencalc/entry/src/main/ets/calculator/MemorySlots.ets
// aid-workflow 20260617: 记忆槽（M1-M6 + MR）逻辑层
// 对应 .port.mjs 与 delta-design.md §3.5

export interface MemorySlot {
  slotIndex: 1 | 2 | 3 | 4 | 5 | 6
  value: number
  updatedAt: number
  /** aid-workflow 20260617: 空槽判定（value 非有限） */
  isEmpty(): boolean
}

export interface MemorySlotsState {
  slots: MemorySlot[]
  lastUsedSlotIndex: 1 | 2 | 3 | 4 | 5 | 6 | null
}

export class MemorySlots {
  /** aid-workflow 20260617: 槽位总数 */
  static readonly COUNT: number = 6

  /** aid-workflow 20260617: 构造空 state（6 槽全空） */
  static empty(): MemorySlotsState {
    const slots: MemorySlot[] = []
    for (let i = 1; i <= MemorySlots.COUNT; i++) {
      slots.push(MemorySlots.makeEmptySlot(i as 1|2|3|4|5|6))
    }
    return { slots: slots, lastUsedSlotIndex: null }
  }

  /** aid-workflow 20260617: 写入第 idx 个槽（1..6），非有限值拒绝 */
  static save(state: MemorySlotsState, idx: number, value: number): MemorySlotsState {
    MemorySlots.validateIdx(idx)
    if (!Number.isFinite(value)) return state
    const slots: MemorySlot[] = state.slots.map((s: MemorySlot): MemorySlot =>
      s.slotIndex === idx ? MemorySlots.makeSlot(idx as 1|2|3|4|5|6, value) : s
    )
    return { slots: slots, lastUsedSlotIndex: idx as 1|2|3|4|5|6 }
  }

  /** aid-workflow 20260617: 读取槽值；越界/空槽返回 null */
  static recall(state: MemorySlotsState, idx: number): number | null {
    if (idx < 1 || idx > MemorySlots.COUNT) return null
    const slot: MemorySlot = state.slots[idx - 1]
    return slot.isEmpty() ? null : slot.value
  }

  /** aid-workflow 20260617: 清空第 idx 个槽 */
  static clearSlot(state: MemorySlotsState, idx: number): MemorySlotsState {
    MemorySlots.validateIdx(idx)
    const slots: MemorySlot[] = state.slots.map((s: MemorySlot): MemorySlot =>
      s.slotIndex === idx ? MemorySlots.makeEmptySlot(idx as 1|2|3|4|5|6) : s
    )
    return { slots: slots, lastUsedSlotIndex: state.lastUsedSlotIndex }
  }

  /** aid-workflow 20260617: 是否存在任一非空槽 */
  static anyHasValue(state: MemorySlotsState): boolean {
    return state.slots.some((s: MemorySlot): boolean => !s.isEmpty())
  }

  /** aid-workflow 20260617: "M" / "M3" / "" 派生字符串 */
  static lastUsedLabel(state: MemorySlotsState): string {
    if (state.lastUsedSlotIndex === null) return ''
    return `M${state.lastUsedSlotIndex}`
  }

  // ---- private helpers ----
  private static makeEmptySlot(slotIndex: 1|2|3|4|5|6): MemorySlot {
    return {
      slotIndex: slotIndex,
      value: NaN,
      updatedAt: 0,
      isEmpty(): boolean { return !Number.isFinite(this.value) }
    }
  }

  private static makeSlot(slotIndex: 1|2|3|4|5|6, value: number): MemorySlot {
    return {
      slotIndex: slotIndex,
      value: value,
      updatedAt: Date.now(),
      isEmpty(): boolean { return !Number.isFinite(this.value) }
    }
  }

  private static validateIdx(idx: number): void {
    if (!Number.isInteger(idx) || idx < 1 || idx > MemorySlots.COUNT) {
      throw new Error(`MemorySlots.save: invalid idx ${idx}, expected 1..${MemorySlots.COUNT}`)
    }
  }
}
```

---

## T6 — RED: hypium 单元测试

### T6.1 创建 `opencalc/entry/src/test/ets/calculator/MemorySlots.test.ets`

参考既有 `entry/src/test/ets/history/HistoryGroup.test.ets` 风格：

```typescript
// opencalc/entry/src/test/ets/calculator/MemorySlots.test.ets
import { describe, it, expect } from '@ohos/hypium'
import { MemorySlots, MemorySlotsState } from '../../../main/ets/calculator/MemorySlots'

export default function memorySlotsTest() {
  describe('MemorySlots', () => {
    it('AC_MEM_01_empty_returns_6_empty_slots', 0, () => {
      const s: MemorySlotsState = MemorySlots.empty()
      expect(s.slots.length).assertEqual(6)
      expect(s.lastUsedSlotIndex).assertEqual(null)
      for (let i = 0; i < 6; i++) {
        expect(s.slots[i].slotIndex).assertEqual(i + 1)
        expect(s.slots[i].isEmpty()).assertEqual(true)
      }
    })

    it('AC_MEM_02_save_then_recall_returns_value', 1, () => {
      let s: MemorySlotsState = MemorySlots.empty()
      s = MemorySlots.save(s, 1, 42)
      expect(MemorySlots.anyHasValue(s)).assertEqual(true)
      expect(MemorySlots.recall(s, 1)).assertEqual(42)
      expect(s.lastUsedSlotIndex).assertEqual(1)
    })

    it('AC_MEM_03_save_overwrites_existing', 2, () => {
      let s: MemorySlotsState = MemorySlots.empty()
      s = MemorySlots.save(s, 3, 100)
      s = MemorySlots.save(s, 3, 200)
      expect(MemorySlots.recall(s, 3)).assertEqual(200)
      expect(s.lastUsedSlotIndex).assertEqual(3)
    })

    it('AC_MEM_04_recall_empty_returns_null', 3, () => {
      const s: MemorySlotsState = MemorySlots.empty()
      expect(MemorySlots.recall(s, 1)).assertEqual(null)
      expect(MemorySlots.recall(s, 6)).assertEqual(null)
    })

    it('AC_MEM_05_save_rejects_NaN', 4, () => {
      let s: MemorySlotsState = MemorySlots.empty()
      s = MemorySlots.save(s, 2, 10)
      const before: MemorySlotsState = s
      const after: MemorySlotsState = MemorySlots.save(s, 2, NaN)
      expect(after === before).assertEqual(true)
      expect(MemorySlots.recall(after, 2)).assertEqual(10)
    })

    it('AC_MEM_06_save_rejects_Infinity', 5, () => {
      let s: MemorySlotsState = MemorySlots.empty()
      s = MemorySlots.save(s, 4, 5)
      const before: MemorySlotsState = s
      const after: MemorySlotsState = MemorySlots.save(s, 4, Infinity)
      expect(after === before).assertEqual(true)
      expect(MemorySlots.recall(after, 4)).assertEqual(5)
    })

    it('AC_MEM_07_save_throws_on_invalid_idx', 6, () => {
      const s: MemorySlotsState = MemorySlots.empty()
      expect((): void => { MemorySlots.save(s, 0, 1) }).assertThrowError('idx')
      expect((): void => { MemorySlots.save(s, 7, 1) }).assertThrowError('idx')
    })

    it('AC_MEM_08_anyHasValue_toggles', 7, () => {
      let s: MemorySlotsState = MemorySlots.empty()
      expect(MemorySlots.anyHasValue(s)).assertEqual(false)
      s = MemorySlots.save(s, 5, 1)
      expect(MemorySlots.anyHasValue(s)).assertEqual(true)
      s = MemorySlots.clearSlot(s, 5)
      expect(MemorySlots.anyHasValue(s)).assertEqual(false)
    })

    it('AC_MEM_09_lastUsedLabel_empty_returns_blank', 8, () => {
      const s: MemorySlotsState = MemorySlots.empty()
      expect(MemorySlots.lastUsedLabel(s)).assertEqual('')
    })

    it('AC_MEM_10_lastUsedLabel_with_lastUsed_returns_MN', 9, () => {
      let s: MemorySlotsState = MemorySlots.empty()
      s = MemorySlots.save(s, 3, 99)
      expect(MemorySlots.lastUsedLabel(s)).assertEqual('M3')
      s = MemorySlots.save(s, 6, 1)
      expect(MemorySlots.lastUsedLabel(s)).assertEqual('M6')
    })
  })
}
```

---

## T7 — RED: 跑 hypium 确认失败

> 注：此时 ArkTS 实现 T5 已完成（GREEN），hypium 测试在 T5 之后跑会 GREEN；本任务序列调整为 **T5（实现）→ T6（写 hypium 测试）→ T7（跑 hypium 确认 GREEN）**。
>
> 为保留 RED-GREEN 节奏，本任务目标改为：**写完 hypium 测试后立即跑确认 GREEN（因为实现已在 T5 完成）**；如实现有 bug 导致 hypium 失败，回到 T5 修复。

```bash
cd /d/huawei/Demo/calculatorHuawei/opencalc
hvigorw --no-daemon test
```

**预期**：MemorySlots suite 10 个用例 PASS

---

## T8 — GREEN: CalculatorPage 状态 + 派生方法

### T8.1 修改 `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`

在 imports 后追加：

```typescript
// aid-workflow 20260617: 记忆槽（M1-M6 + MR）
import { MemorySlots, MemorySlotsState } from '../calculator/MemorySlots'
```

在 `@State` 段（约 L23-47 后）追加：

```typescript
@State memorySlots: MemorySlotsState = MemorySlots.empty()  // aid-workflow 20260617
@State showMemoryPicker: boolean = false                      // aid-workflow 20260617
```

在 `onEquals` 之后（约 L221 后）追加派生方法：

```typescript
/** aid-workflow 20260617: 派生记忆激活指示文案 */
private getMemoryActiveLabel(): string {
  return MemorySlots.lastUsedLabel(this.memorySlots)
}

/** aid-workflow 20260617: 派生 MR 按钮是否可用 */
private getMRButtonEnabled(): boolean {
  return MemorySlots.anyHasValue(this.memorySlots)
}
```

---

## T9 — GREEN: 数字键 builder 增加长按手势

### T9.1 修改数字键 builder（CalculatorPage.ets L646）

**原代码**：
```typescript
@Builder BtnDigit(l: string) {
  Text(l).fontSize(...).onClick((): void => { this.onDigit(l) })
}
```

**新代码**（在 `.onClick(...)` 后追加条件 gesture）：
```typescript
@Builder BtnDigit(l: string) {
  Text(l).fontSize(...).onClick((): void => { this.onDigit(l) })
    .gesture(this.buildDigitLongPressGesture(l))
}

/** aid-workflow 20260617: 数字键长按手势构造器（仅 1-6 触发存槽） */
private buildDigitLongPressGesture(l: string): GestureConfig {
  // aid-workflow 20260617: 仅 1-6 数字键挂存槽手势
  if (l < '1' || l > '6') {
    // 0/7/8/9 不挂 longPress，等价于 noop
    return LongPressGesture().onAction((): void => {})
  }
  return LongPressGesture().onAction((): void => { this.onLongPressDigit(l) })
}
```

> **FMEA-FM-02 消减**: 通过 builder 内部 `l >= '1' && l <= '6'` 条件守卫，0/7/8/9 永远不进入 save 路径。
> **FMEA-FM-04 兜底**: 即使长按 0/7/8/9 触发 noop gesture，对 onClick 流程零影响。

---

## T10 — GREEN: ButtonGrid 插入 MR 按钮 + 指示

### T10.1 在 ButtonGrid（约 L630-643）顶部插入记忆行

```typescript
@Builder ButtonGrid() {
  Column() {
    // aid-workflow 20260617: 记忆行（MR + 激活指示）
    Row() {
      Text('M').fontSize(14).fontColor(this.getOpFg())
        .width('17%').height(28).textAlign(TextAlign.Center)
        .opacity(0.6)
      Text(this.getMemoryActiveLabel()).fontSize(14).fontColor(this.getOpFg())
        .layoutWeight(1).height(28).textAlign(TextAlign.Start)
        .opacity(0.7)
      Text('MR').fontSize(20).fontColor(this.getOpFg())
        .width('17%').height(36).textAlign(TextAlign.Center)
        .backgroundColor(this.getBtnBg()).borderRadius(50)
        .margin({ left: 4, right: 4 })
        .enabled(this.getMRButtonEnabled())
        .opacity(this.getMRButtonEnabled() ? 1.0 : 0.4)
        .onClick((): void => { this.onMRClick() })
    }.width('100%').margin({ bottom: 6 })

    // 既有科学函数行 + 数字按钮行（保持不变）
    ...
  }
}
```

---

## T11 — GREEN: MemoryPickerPanel + Stack 挂载

### T11.1 新增 `MemoryPickerPanel` @Builder

参考既有 `LongPressMenuPanel`（L463-486）模式，复用 `pages/LongPressMenu.ets` 的 `MENU_*` 常量：

```typescript
import { LongPressMenu } from './LongPressMenu'

/** aid-workflow 20260617: 6 槽选择面板（与 LongPressMenuPanel 风格一致） */
@Builder MemoryPickerPanel() {
  Stack() {
    // 遮罩
    Column()
      .width('100%').height('100%')
      .backgroundColor(LongPressMenu.MENU_MASK_COLOR)
      .opacity(LongPressMenu.MENU_MASK_OPACITY)
      .onClick((): void => { this.onMemoryMaskClick() })

    // 居中浮层
    Column() {
      ForEach(this.memorySlots.slots, (slot: MemorySlot) => {
        Row() {
          Text(`M${slot.slotIndex}`)
            .fontSize(LongPressMenu.MENU_FONT_SIZE)
            .fontColor(slot.isEmpty() ? Color.Gray : Color.Black)
            .width(60)
          Text(slot.isEmpty() ? '—' : String(slot.value))
            .fontSize(LongPressMenu.MENU_FONT_SIZE)
            .fontColor(slot.isEmpty() ? Color.Gray : Color.Black)
            .layoutWeight(1)
        }
        .width('100%')
        .height(LongPressMenu.MENU_ITEM_HEIGHT)
        .opacity(slot.isEmpty() ? 0.4 : 1.0)
        .enabled(!slot.isEmpty())
        .onClick((): void => { this.onPickSlot(slot.slotIndex) })
      }, (slot: MemorySlot) => String(slot.slotIndex))
    }
    .width('60%')
    .constraintSize({ maxWidth: LongPressMenu.MENU_MAX_WIDTH })
    .padding(LongPressMenu.MENU_PADDING)
    .backgroundColor(Color.White)
    .borderRadius(LongPressMenu.MENU_BORDER_RADIUS)
  }
  .width('100%').height('100%')
}
```

### T11.2 在 `build()` Stack 顶层追加渲染守卫

在 L516 后追加：

```typescript
// aid-workflow 20260617: 记忆槽选择面板（顶层遮罩）
if (this.showMemoryPicker) this.MemoryPickerPanel()
```

---

## T12 — GREEN: 事件处理方法

### T12.1 在 `onPaste` 后追加

```typescript
/** aid-workflow 20260617: 数字键 1-6 长按 → 存槽 + toast */
private onLongPressDigit(d: string): void {
  // aid-workflow 20260617: 解析 display（剥千分位逗号），非有限值拒绝
  const raw: string = this.result.replace(/,/g, '')
  const value: number = Number.parseFloat(raw)
  if (!Number.isFinite(value)) {
    promptAction.showToast({ message: '无法存入', duration: 1500 })
    return
  }
  const idx: number = Number(d)
  this.memorySlots = MemorySlots.save(this.memorySlots, idx, value)
  promptAction.showToast({ message: `已存入 M${idx}`, duration: 1500 })
}

/** aid-workflow 20260617: MR 按钮点击 → 打开/关闭面板 */
private onMRClick(): void {
  if (!MemorySlots.anyHasValue(this.memorySlots)) return  // FMEA-FM-04 兜底
  this.showMemoryPicker = !this.showMemoryPicker
  // FMEA-FM-06: 互斥关闭 LongPressMenu
  if (this.showLongPressMenu) this.showLongPressMenu = false
}

/** aid-workflow 20260617: 选槽调出 → 写入输入流 */
private onPickSlot(idx: 1|2|3|4|5|6): void {
  const value: number | null = MemorySlots.recall(this.memorySlots, idx)
  if (value === null) return  // FMEA 兜底：空槽不应被点中
  // aid-workflow 20260617: 写入当前输入流
  this.expression = this.expression + String(value)
  this.errorMsg = ''
  this.showMemoryPicker = false
}

/** aid-workflow 20260617: 面板遮罩点击 → 关闭 */
private onMemoryMaskClick(): void {
  this.showMemoryPicker = false
}
```

---

## T13 — GREEN: 注册 hypium suite

### T13.1 修改 `opencalc/entry/src/test/List.test.ets`

在已有 import 段后追加：

```typescript
import memorySlotsTest from './ets/calculator/MemorySlots.test.ets'
```

在已有 `testsuite()` 调用内追加：

```typescript
memorySlotsTest()
```

---

## T14 — GREEN: 跑 hypium

```bash
cd /d/huawei/Demo/calculatorHuawei/opencalc
hvigorw --no-daemon test
```

**预期**：MemorySlots suite 10 个用例 PASS；既有 suites 不回归

---

## T15 — GREEN: 端口回归

```bash
node --test specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs
```

**预期**：10 个 port 用例仍 PASS（端口实现未变）

---

## T16 — REFACTOR: 端口常量对齐

提取 `MEMORY_SLOTS_COUNT = 6` 常量（已在 T3 完成，确认命名一致）。

---

## T17 — REFACTOR: CalculatorPage 字面量替换

- `Number.parseFloat(this.result.replace(/,/g, ''))` 抽到 `private parseDisplayValue(): number` 派生方法
- `String(value)` 在 onPickSlot 中改为 `formatNumberForInput(value)`（沿用 NumberFormatter.ets 的格式化）

---

## T18 — REFACTOR: 双 GREEN 回归

```bash
node --test specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs
cd /d/huawei/Demo/calculatorHuawei/opencalc && hvigorw --no-daemon test
```

**预期**：port + hypium 双 PASS

---

## T19 — VERIFY: git 检查

```bash
git status
git diff --stat
```

**预期变更文件清单**：
- `opencalc/entry/src/main/ets/calculator/MemorySlots.ets`（新增）
- `opencalc/entry/src/main/ets/pages/CalculatorPage.ets`（修改）
- `opencalc/entry/src/test/ets/calculator/MemorySlots.test.ets`（新增）
- `opencalc/entry/src/test/List.test.ets`（修改）
- `specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.port.mjs`（新增）
- `specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs`（新增）

---

## T20 — DOC: apply-report.md

按 aid-applying skill 模板生成，包含：
- 测试输出（port + hypium）
- AC 矩阵（AC-MEM-01..10）
- FMEA 消减措施映射表
- git diff 摘要
- UI 自动化截图链接

---

## T21 — UI: 自动化测试（强制 — capabilities.json ui_test.available=true）

### T21.1 创建 UI 测试脚本

参考 Issue #16 的 ui-tests/ 模式（Python + hdc + harmonyos-ui-test skill）：

```python
# specs/changes/20260617-requirement-add-memory-slots/ui-tests/run_tests.py
"""记忆槽 M1-M6 + MR UI 自动化测试 (hdc + harmonyos-ui-test)"""
# 1. hdc list targets 验证连接
# 2. hdc install -r 安装新 HAP
# 3. aa start 启动应用
# 4. 输入 "1+2=" → display="3"
# 5. uitest uiInput drag <1键坐标> <1键坐标+1,1+1> 200 触发 longPress
# 6. dump UI 树找到 toast "已存入 M1"
# 7. 点击 MR 按钮 → dump 验证菜单含 "M1 3"
# 8. 点击 M1 项 → dump 验证 expression 末尾追加 "3"
# 9. screenshot 存档到 screenshot/
```

**验收标准**：
- [ ] hdc 设备已连接（hdc list targets 有输出）
- [ ] 应用已安装到设备（hdc install -r 成功）
- [ ] 应用已启动（aa start 成功）
- [ ] AC-MEM-01..10 全部通过 dump UI 树 + 截图验证
- [ ] screenshot/ 目录包含每步操作截图
- [ ] results.json pass

**TDD**: [x] RED / [x] GREEN / [ ] REFACTOR

---

## 开发顺序

```
T1 (RED 写测试)
  ↓
T2 (RED 跑测确认失败)
  ↓
T3 (GREEN 实现端口)
  ↓
T4 (GREEN 跑测确认通过)
  ↓
T5 (ArkTS 类)
  ↓
T6 (hypium 测试)
  ↓
T7 (hypium 跑 GREEN)
  ↓
T8 (CalculatorPage 状态/派生)
  ↓
T9 (数字键长按手势)
  ↓
T10 (MR 按钮 + 指示)
  ↓
T11 (MemoryPickerPanel + 挂载)
  ↓
T12 (事件处理方法)
  ↓
T13 (注册 hypium suite)
  ↓
T14 (hypium 跑 GREEN)
  ↓
T15 (端口跑 GREEN)
  ↓
T16~T17 (REFACTOR)
  ↓
T18 (双 GREEN 回归)
  ↓
T19 (git 检查)
  ↓
T20 (apply-report.md)
  ↓
T21 (UI 自动化)
  ↓
✅ IMPLEMENTING + APPLYING 完成
```

---

## 验收计划

| 任务 | 验收方式 | 期望结果 |
|------|---------|---------|
| T1 | 文件存在 + 10 个 test 块 | ✅ |
| T2 | `node --test` 全 FAIL | ✅ |
| T4 | `node --test` 全 PASS | ✅ |
| T7 | `hvigorw test` MemorySlots suite PASS | ✅ |
| T14 | `hvigorw test` 全 suite PASS（无回归） | ✅ |
| T15 | `node --test` 仍 PASS | ✅ |
| T18 | port + hypium 双 PASS | ✅ |
| T19 | `git status` 含 6 个变更文件 | ✅ |
| T20 | apply-report.md 生成 | ✅ |
| T21 | UI 自动化 AC 全通过（hdc + 模拟器） | ✅ |

// OpenCalc — 记忆槽 (M1-M6 + MR) 逻辑层
// aid-workflow 20260617-requirement-add-memory-slots · T5
// 对应 .port.mjs 与 delta-design.md §3.5
// 1:1 对应 specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.port.mjs

// aid-workflow 20260617 Issue #28: MemorySlot 用 class 实现而非 interface,
// 因为 ArkTS 严格模式不允许 untyped object literal 与 method-shorthand 中的 this
export class MemorySlot {
  slotIndex: 1 | 2 | 3 | 4 | 5 | 6
  value: number
  updatedAt: number

  constructor(slotIndex: 1 | 2 | 3 | 4 | 5 | 6, value: number, updatedAt: number) {
    this.slotIndex = slotIndex
    this.value = value
    this.updatedAt = updatedAt
  }

  /** aid-workflow 20260617: 空槽判定（value 非有限） */
  isEmpty(): boolean {
    return !Number.isFinite(this.value)
  }
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
      slots.push(MemorySlots.makeEmptySlot(i as 1 | 2 | 3 | 4 | 5 | 6))
    }
    return { slots: slots, lastUsedSlotIndex: null }
  }

  /** aid-workflow 20260617: 写入第 idx 个槽（1..6），非有限值拒绝 */
  static save(state: MemorySlotsState, idx: number, value: number): MemorySlotsState {
    MemorySlots.validateIdx(idx)
    if (!Number.isFinite(value)) return state
    const slots: MemorySlot[] = state.slots.map((s: MemorySlot): MemorySlot =>
      s.slotIndex === idx ? MemorySlots.makeSlot(idx as 1 | 2 | 3 | 4 | 5 | 6, value) : s
    )
    return { slots: slots, lastUsedSlotIndex: idx as 1 | 2 | 3 | 4 | 5 | 6 }
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
      s.slotIndex === idx ? MemorySlots.makeEmptySlot(idx as 1 | 2 | 3 | 4 | 5 | 6) : s
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
  private static makeEmptySlot(slotIndex: 1 | 2 | 3 | 4 | 5 | 6): MemorySlot {
    return new MemorySlot(slotIndex, NaN, 0)
  }

  private static makeSlot(slotIndex: 1 | 2 | 3 | 4 | 5 | 6, value: number): MemorySlot {
    return new MemorySlot(slotIndex, value, Date.now())
  }

  private static validateIdx(idx: number): void {
    if (!Number.isInteger(idx) || idx < 1 || idx > MemorySlots.COUNT) {
      throw new Error(`MemorySlots.save: invalid idx ${idx}, expected 1..${MemorySlots.COUNT}`)
    }
  }
}

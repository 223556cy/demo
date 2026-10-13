// specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.port.mjs
// 1:1 端口：与 ArkTS calculator/MemorySlots.ets 一一对应
// aid-workflow 20260617-requirement-add-memory-slots · T3 (GREEN)
// 实现：6 槽记忆（不可变更新模式）

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

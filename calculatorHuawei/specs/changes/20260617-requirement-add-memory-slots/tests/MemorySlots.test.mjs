// specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs
// aid-workflow 20260617-requirement-add-memory-slots · T1.2
// 10 个失败用例（RED 阶段）
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

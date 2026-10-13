// OpenCalc — MemorySlots 单元测试 (hypium 风格)
// aid-workflow 20260617-requirement-add-memory-slots · T6
// 1:1 镜像 specs/changes/20260617-requirement-add-memory-slots/tests/MemorySlots.test.mjs

import { describe, it, expect } from '@ohos/hypium'
import { MemorySlots, MemorySlotsState, MemorySlot } from '../../../main/ets/calculator/MemorySlots'

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

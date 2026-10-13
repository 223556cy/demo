// OpenCalc — HistoryGroup 单元测试 (hypium 风格)
// Issue #15 历史按日期分组 (今天/昨天/更早)
// TDD RED 阶段: 模块尚未实现,本文件用于驱动生产代码生成。

import { describe, it, expect } from '@ohos/hypium'
import { HistoryItem } from '../../../main/ets/model/Models'
import {
  groupHistoryByDate,
  startOfLocalDay,
  HistoryGroupKey,
  HistorySection
} from '../../../main/ets/history/HistoryGroup'

// 工具: 构造 HistoryItem
function mkItem(id: number, timestamp: number, expr: string = '1+1', result: string = '2'): HistoryItem {
  return { id, expression: expr, result, timestamp }
}

// 工具: 把 Date 转成 epoch ms (本地时区)
function msOf(year: number, month: number, day: number, hour: number = 12, minute: number = 0, second: number = 0): number {
  return new Date(year, month - 1, day, hour, minute, second).getTime()
}

export default function historyGroupTest() {

  describe('groupHistoryByDate_boundary_cases', () => {

    // TC-01: 空数组 → 3 个空段 (顺序: 今天/昨天/更早)
    it('AC_HG_01_empty_items_should_return_three_empty_sections_in_order', 0, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      const sections = groupHistoryByDate([], now)

      expect(sections.length).assertEqual(3)
      expect(sections[0].key).assertEqual(HistoryGroupKey.TODAY)
      expect(sections[0].title).assertEqual('今天')
      expect(sections[0].items.length).assertEqual(0)
      expect(sections[1].key).assertEqual(HistoryGroupKey.YESTERDAY)
      expect(sections[1].title).assertEqual('昨天')
      expect(sections[1].items.length).assertEqual(0)
      expect(sections[2].key).assertEqual(HistoryGroupKey.EARLIER)
      expect(sections[2].title).assertEqual('更早')
      expect(sections[2].items.length).assertEqual(0)
    })

    // TC-02: 全部今天 (3 条) → 仅今天段有数据
    it('AC_HG_02_all_today_should_only_fill_today_section', 1, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      const items = [
        mkItem(1, msOf(2026, 6, 16, 9, 0, 0)),
        mkItem(2, msOf(2026, 6, 16, 8, 30, 0)),
        mkItem(3, msOf(2026, 6, 16, 0, 0, 1))  // 刚过零点
      ]

      const sections = groupHistoryByDate(items, now)

      expect(sections[0].items.length).assertEqual(3)
      expect(sections[1].items.length).assertEqual(0)
      expect(sections[2].items.length).assertEqual(0)
    })

    // TC-03: 全部昨天 (2 条) → 仅昨天段有数据
    it('AC_HG_03_all_yesterday_should_only_fill_yesterday_section', 2, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      const items = [
        mkItem(1, msOf(2026, 6, 15, 14, 0, 0)),
        mkItem(2, msOf(2026, 6, 15, 0, 0, 1))  // 昨天刚过零点
      ]

      const sections = groupHistoryByDate(items, now)

      expect(sections[0].items.length).assertEqual(0)
      expect(sections[1].items.length).assertEqual(2)
      expect(sections[2].items.length).assertEqual(0)
    })

    // TC-04: 全部更早 (5 条) → 仅更早段有数据
    it('AC_HG_04_all_earlier_should_only_fill_earlier_section', 3, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      const items = [
        mkItem(1, msOf(2026, 6, 14, 12, 0, 0)),  // 前天
        mkItem(2, msOf(2026, 6, 13, 9, 0, 0)),   // 3 天前
        mkItem(3, msOf(2026, 6, 10, 14, 0, 0)),   // 上周
        mkItem(4, msOf(2026, 5, 1, 8, 0, 0)),    // 上个月
        mkItem(5, msOf(2025, 12, 25, 18, 0, 0))  // 去年
      ]

      const sections = groupHistoryByDate(items, now)

      expect(sections[0].items.length).assertEqual(0)
      expect(sections[1].items.length).assertEqual(0)
      expect(sections[2].items.length).assertEqual(5)
    })

    // TC-05: 跨三天混合 → 三段均有数据
    it('AC_HG_05_mixed_three_days_should_fill_all_sections', 4, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      const items = [
        mkItem(1, msOf(2026, 6, 16, 9, 0, 0)),    // 今天
        mkItem(2, msOf(2026, 6, 15, 14, 0, 0)),   // 昨天
        mkItem(3, msOf(2026, 6, 14, 8, 0, 0))     // 前天
      ]

      const sections = groupHistoryByDate(items, now)

      expect(sections[0].items.length).assertEqual(1)
      expect(sections[0].items[0].id).assertEqual(1)
      expect(sections[1].items.length).assertEqual(1)
      expect(sections[1].items[0].id).assertEqual(2)
      expect(sections[2].items.length).assertEqual(1)
      expect(sections[2].items[0].id).assertEqual(3)
    })

    // TC-06: 边界 00:00:00 → 跨日正确分组
    it('AC_HG_06_midnight_boundary_should_group_correctly', 5, () => {
      const now = msOf(2026, 6, 16, 12, 0, 0)
      // 今天 00:00:00.000 严格属于"今天"
      const todayStart = msOf(2026, 6, 16, 0, 0, 0)
      // 昨天 23:59:59.999 严格属于"昨天"
      const yesterdayEnd = msOf(2026, 6, 15, 23, 59, 59)

      const items = [
        mkItem(1, todayStart),     // 今天 00:00:00
        mkItem(2, yesterdayEnd)    // 昨天 23:59:59
      ]

      const sections = groupHistoryByDate(items, now)

      expect(sections[0].items.length).assertEqual(1)
      expect(sections[0].items[0].id).assertEqual(1)  // todayStart 归今天
      expect(sections[1].items.length).assertEqual(1)
      expect(sections[1].items[0].id).assertEqual(2)  // yesterdayEnd 归昨天
      expect(sections[2].items.length).assertEqual(0)
    })

    // TC-07: 段内顺序保持 newest-first
    it('AC_HG_07_within_section_order_should_preserve_input', 6, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      // 输入顺序: 9:00, 8:00, 11:00 (newest-first 由调用方保证, 函数内部不排序)
      const items = [
        mkItem(1, msOf(2026, 6, 16, 9, 0, 0)),
        mkItem(2, msOf(2026, 6, 16, 8, 0, 0)),
        mkItem(3, msOf(2026, 6, 16, 11, 0, 0))
      ]

      const sections = groupHistoryByDate(items, now)

      // 段内顺序应与输入一致 (不排序)
      expect(sections[0].items.length).assertEqual(3)
      expect(sections[0].items[0].id).assertEqual(1)
      expect(sections[0].items[1].id).assertEqual(2)
      expect(sections[0].items[2].id).assertEqual(3)
    })
  })

  describe('startOfLocalDay', () => {

    it('AC_HG_08_start_of_local_day_should_be_zero_hundred', 7, () => {
      const d = new Date(2026, 5, 16, 14, 30, 45)  // 2026-06-16 14:30:45
      const start = startOfLocalDay(d)
      const expected = msOf(2026, 6, 16, 0, 0, 0)

      expect(start).assertEqual(expected)
    })

    it('AC_HG_09_start_of_local_day_midnight_should_equal_itself', 8, () => {
      // 已是 00:00:00 的 Date,startOfLocalDay 应不变
      const d = new Date(2026, 5, 16, 0, 0, 0)
      const start = startOfLocalDay(d)

      expect(start).assertEqual(d.getTime())
    })
  })

  describe('groupHistoryByDate_null_guards', () => {

    // TC-10: items=null → 返回 3 段均空 (不抛异常)
    it('AC_HG_10_null_items_should_return_three_empty_sections', 9, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      const sections = groupHistoryByDate(null, now)

      expect(sections.length).assertEqual(3)
      expect(sections[0].key).assertEqual(HistoryGroupKey.TODAY)
      expect(sections[0].items.length).assertEqual(0)
      expect(sections[1].key).assertEqual(HistoryGroupKey.YESTERDAY)
      expect(sections[1].items.length).assertEqual(0)
      expect(sections[2].key).assertEqual(HistoryGroupKey.EARLIER)
      expect(sections[2].items.length).assertEqual(0)
    })

    // TC-11: items=undefined → 返回 3 段均空 (不抛异常)
    it('AC_HG_11_undefined_items_should_return_three_empty_sections', 10, () => {
      const now = msOf(2026, 6, 16, 10, 0, 0)
      // undefined 是 ArkTS/TS 的合法值,与 null 分别覆盖守卫路径
      const sections = groupHistoryByDate(undefined, now)

      expect(sections.length).assertEqual(3)
      expect(sections[0].key).assertEqual(HistoryGroupKey.TODAY)
      expect(sections[0].items.length).assertEqual(0)
      expect(sections[1].key).assertEqual(HistoryGroupKey.YESTERDAY)
      expect(sections[1].items.length).assertEqual(0)
      expect(sections[2].key).assertEqual(HistoryGroupKey.EARLIER)
      expect(sections[2].items.length).assertEqual(0)
    })
  })
}

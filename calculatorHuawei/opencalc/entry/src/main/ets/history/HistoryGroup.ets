// OpenCalc — HistoryGroup 纯函数模块
// Issue #15 历史按日期分组 (今天/昨天/更早)
// 移植自：delta-design.md §3.5
// 边界：本地时区日历日, 与 Android DateUtils.isToday 行为对齐

import { HistoryItem } from '../model/Models'

/** 分组类型 (按时间倒序固定) */
export enum HistoryGroupKey {
  TODAY = 0,
  YESTERDAY = 1,
  EARLIER = 2
}

/** 单个分组: 标题 + 条目列表 */
export interface HistorySection {
  key: HistoryGroupKey   // TODAY / YESTERDAY / EARLIER
  title: string          // "今天" / "昨天" / "更早"
  items: HistoryItem[]   // 段内条目, 保持输入顺序
}

const MS_PER_DAY: number = 86400000

/**
 * 把 Date 转成 "本地日历日起始 ms" (00:00:00.000)
 */
export function startOfLocalDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0).getTime()
}

/**
 * 把 HistoryItem[] 按 timestamp 分到三段
 * @param items 输入历史 (newest-first, 可为空/null)
 * @param now 参考"当前时间" (ms epoch)
 * @returns 长度固定 3 的 HistorySection[], 顺序: 今天/昨天/更早
 */
export function groupHistoryByDate(items: HistoryItem[] | null | undefined, now: number): HistorySection[] {
  const safeItems: HistoryItem[] = items ? items : []
  const todayStart: number = startOfLocalDay(new Date(now))
  const yesterdayStart: number = todayStart - MS_PER_DAY

  const sections: HistorySection[] = [
    { key: HistoryGroupKey.TODAY, title: '今天', items: [] },
    { key: HistoryGroupKey.YESTERDAY, title: '昨天', items: [] },
    { key: HistoryGroupKey.EARLIER, title: '更早', items: [] }
  ]

  for (let i: number = 0; i < safeItems.length; i++) {
    const item: HistoryItem = safeItems[i]
    // 闭区间判定: `timestamp >= todayStart` 包含今日 00:00:00.000.000 (归今天),
    // `timestamp >= yesterdayStart` 包含昨日 00:00:00.000.000 (归昨天).
    // 不要改成 `>` 否则 00:00:00 整点会落到 "更早" 段 — 与 delta-spec AC_HG_06 不符.
    if (item.timestamp >= todayStart) {
      sections[0].items.push(item)
    } else if (item.timestamp >= yesterdayStart) {
      sections[1].items.push(item)
    } else {
      sections[2].items.push(item)
    }
  }

  return sections
}

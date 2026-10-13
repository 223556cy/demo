// HistoryGroup Node.js 端口 - 用于本地单测验证
// Issue #15 历史按日期分组 (今天/昨天/更早)
// 完整等价于: opencalc/entry/src/main/ets/history/HistoryGroup.ets
// 跑测: node HistoryGroup.test.mjs

export const HistoryGroupKey = {
  TODAY: 0,
  YESTERDAY: 1,
  EARLIER: 2
}

const MS_PER_DAY = 86400000

export function startOfLocalDay(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0).getTime()
}

export function groupHistoryByDate(items, now) {
  const safeItems = items ? items : []
  const todayStart = startOfLocalDay(new Date(now))
  const yesterdayStart = todayStart - MS_PER_DAY

  const sections = [
    { key: HistoryGroupKey.TODAY, title: '今天', items: [] },
    { key: HistoryGroupKey.YESTERDAY, title: '昨天', items: [] },
    { key: HistoryGroupKey.EARLIER, title: '更早', items: [] }
  ]

  for (let i = 0; i < safeItems.length; i++) {
    const item = safeItems[i]
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

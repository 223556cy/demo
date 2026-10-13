// HistorySearch Node.js 端口 - 用于本地单测验证
// Issue #24 历史搜索框
// 完整等价于: opencalc/entry/src/main/ets/history/HistorySearch.ets
// 跑测: node HistorySearch.test.mjs

export function filterHistoryByQuery(items, query) {
  const safeItems = items ? items : []
  const q = (query || '').trim().toLowerCase()
  if (q.length === 0) return safeItems
  const result = []
  for (let i = 0; i < safeItems.length; i++) {
    const item = safeItems[i]
    if (item.expression.toLowerCase().includes(q) ||
        item.result.toLowerCase().includes(q)) {
      result.push(item)
    }
  }
  return result
}

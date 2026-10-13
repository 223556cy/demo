// HistoryFilter Node.js 端口 — 镜像 ETS 实现
// Iron rule 6: 代码与 ETS 源保持一致

/**
 * 历史记录条目（镜像 model/Models.ets HistoryItem）
 */
export class HistoryItem {
  constructor(id, expression, result, timestamp) {
    this.id = id
    this.expression = expression
    this.result = result
    this.timestamp = timestamp
  }
}

/**
 * 过滤历史记录
 * 规则：仅匹配 expression 字段、子串、大小写不敏感
 * @param {HistoryItem[]} history
 * @param {string} query
 * @returns {HistoryItem[]}
 */
export function filterHistory(history, query) {
  const q = (query || '').trim().toLowerCase()
  if (q.length === 0) return history
  return history.filter((it) =>
    it.expression.toLowerCase().indexOf(q) !== -1
  )
}
